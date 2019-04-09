package main

import (
	"bytes"
	"crypto/tls"
	"io"
	"log"
	"strconv"
	"sync"

	"github.com/CyrusBiotechnology/go-har"
	"github.com/lucas-clemente/quic-go"
	"golang.org/x/net/http2"
	"golang.org/x/net/http2/hpack"
)

func getInitiator(initiator har.Initiator) string {
	switch initiator.Type {
	case "other":
		return ""
	case "parser":
		return initiator.Url
	case "script":
		callFrames := initiator.Stack.CallFrames
		if len(callFrames) == 0 {
			callFrames = initiator.Stack.Parent.CallFrames
		}
		if len(callFrames) == 0 {
			log.Println("stack empty cannot determine initiator")
			return ""
		}
		return callFrames[0].Url
	}
	log.Printf("unknown initiator type %v", initiator.Type)
	return ""
}

type client struct {
	sess      quic.Session
	header    quic.Stream
	dataChans map[int]chan int
	wg        sync.WaitGroup
}

func dial(addr string) (*client, error) {
	sess, err := quic.DialAddr(addr,
		&tls.Config{InsecureSkipVerify: true},
		&quic.Config{CreatePaths: true},
	)
	if err != nil {
		return nil, err
	}

	header, err := sess.OpenStreamSync()
	if err != nil {
		sess.Close(nil)
		return nil, err
	}

	c := &client{
		sess:      sess,
		header:    header,
		dataChans: make(map[int]chan int),
	}
	go c.handleHeader()

	return c, nil
}

func (c *client) close() {
	c.sess.Close(nil)
}

func (c *client) handleHeader() error {
	h2framer := http2.NewFramer(nil, c.header)
	for {
		frame, err := h2framer.ReadFrame()
		if err != nil {
			return err
		}
		headerFrame, ok := frame.(*http2.HeadersFrame)
		if !ok {
			continue
		}

		h2pack := hpack.NewDecoder(4096, nil)
		headers, err := h2pack.DecodeFull(headerFrame.HeaderBlockFragment())
		if err != nil {
			continue
		}

		var size int
		for _, h := range headers {
			if h.Name == "content-length" {
				size, _ = strconv.Atoi(h.Value)
			}
		}
		// default buffer?
		if size <= 0 {
			size = 4096
		}
		if ch, ok := c.dataChans[int(headerFrame.StreamID)]; ok {
			ch <- size
		}
	}
}

func (c *client) getPage(req har.Request) error {
	data, err := c.sess.OpenStreamSync()
	if err != nil {
		return err
	}
	// ignore request data
	data.Close()

	sid := int(data.StreamID())
	c.dataChans[sid] = make(chan int)

	var header bytes.Buffer
	h2pack := hpack.NewEncoder(&header)
	for _, h := range req.Headers {
		err := h2pack.WriteField(hpack.HeaderField{Name: h.Name, Value: h.Value})
		if err != nil {
			return err
		}
	}

	h2framer := http2.NewFramer(c.header, nil)
	err = h2framer.WriteHeaders(http2.HeadersFrameParam{
		StreamID:      uint32(sid),
		BlockFragment: header.Bytes(),
		EndStream:     true,
		EndHeaders:    true,
	})
	if err != nil {
		return err
	}

	size := <-c.dataChans[sid]
	buf := make([]byte, size)
	for n, err := data.Read(buf); n != 0 && err != io.EOF; n, err = data.Read(buf) {
		if err != nil {
			return err
		}
	}

	c.initiate(req.Url)

	return nil
}

func (c *client) doGetPage(req har.Request) {
	err := c.getPage(req)
	if err != nil {
		log.Println(err)
	}
	c.wg.Done()
}

// very slow implementation
func (c *client) initiate(url string) {
	for idx, ent := range db.data {
		if db.vis[idx] {
			continue
		}
		initiator := getInitiator(ent.Initiator)
		if initiator == url {
			db.vis[idx] = true
			c.wg.Add(1)
			log.Println(encodeHeaderHAR(ent.Request.Headers))
			go c.doGetPage(ent.Request)
		}
	}
}
