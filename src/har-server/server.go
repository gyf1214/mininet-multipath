package main

import (
	"bytes"
	"errors"
	"fmt"
	"log"
	"strconv"
	"sync"

	"github.com/lucas-clemente/quic-go"
	"golang.org/x/net/http2"
	"golang.org/x/net/http2/hpack"
)

type server struct {
	sess      quic.Session
	header    quic.Stream
	data      map[int]chan quic.Stream
	dataMutex sync.Mutex

	h2framer *http2.Framer
	h2pack   *hpack.Decoder
}

func newServer(sess quic.Session) (*server, error) {
	header, err := sess.AcceptStream()
	if err != nil {
		return nil, err
	}
	ss := &server{
		sess:     sess,
		header:   header,
		data:     make(map[int]chan quic.Stream),
		h2framer: http2.NewFramer(nil, header),
		h2pack:   hpack.NewDecoder(4096, nil),
	}
	go ss.handleStreams()
	return ss, nil
}

func (s *server) addStream(sid int) {
	s.dataMutex.Lock()
	if _, ok := s.data[sid]; !ok {
		s.data[sid] = make(chan quic.Stream)
	}
	s.dataMutex.Unlock()
}

func (s *server) handleStreams() error {
	for {
		if str, err := s.sess.AcceptStream(); err == nil {
			sid := int(str.StreamID())
			log.Println("accept stream", sid)
			s.addStream(sid)
			go func() {
				s.data[sid] <- str
			}()
		} else {
			log.Println(err)
			return err
		}
	}
}

func encodeHeader(headers []hpack.HeaderField) string {
	var path, authority, method string
	for _, header := range headers {
		switch header.Name {
		case ":path":
			path = header.Value
		case ":authority":
			authority = header.Value
		case ":method":
			method = header.Value
		}
	}
	return fmt.Sprintf("%s %s%s", method, authority, path)
}

func (s *server) handleData(stream quic.Stream, enc string) {
	// get the FIN
	stream.Read([]byte{0})

	if resp, ok := db.data[enc]; ok {
		var headers bytes.Buffer
		enc := hpack.NewEncoder(&headers)
		enc.WriteField(hpack.HeaderField{Name: ":status", Value: strconv.Itoa(resp.Status)})

		var length int
		for _, h := range resp.Headers {
			if h.Name == "content-length" {
				length, _ = strconv.Atoi(h.Value)
			}
			enc.WriteField(hpack.HeaderField{Name: h.Name, Value: h.Value})
		}

		framer := http2.NewFramer(s.header, nil)
		err := framer.WriteHeaders(http2.HeadersFrameParam{
			StreamID:      uint32(stream.StreamID()),
			EndHeaders:    true,
			BlockFragment: headers.Bytes(),
		})
		if err != nil {
			log.Println(err)
		}

		log.Printf("response %v with %v bytes", enc, length)
		if length > 0 {
			buf := make([]byte, length)
			n, err := stream.Write(buf)
			log.Println(n, err)
		}
	} else {
		log.Printf("response %v not found, ignore", enc)
	}

	sid := int(stream.StreamID())
	stream.Close()
	s.dataMutex.Lock()
	delete(s.data, sid)
	s.dataMutex.Unlock()
}

// returns true if close the connection
func (s *server) acceptHeader() (bool, error) {
	frame, err := s.h2framer.ReadFrame()
	if err != nil {
		return false, err
	}
	headerFrame, ok := frame.(*http2.HeadersFrame)
	if !ok || !headerFrame.HeadersEnded() {
		return true, errors.New("not header frame")
	}
	headers, err := s.h2pack.DecodeFull(headerFrame.HeaderBlockFragment())
	if err != nil {
		return true, err
	}

	enc := encodeHeader(headers)
	sid := int(headerFrame.StreamID)
	s.addStream(sid)
	stream := <-s.data[sid]

	log.Printf("stream %v handle %v", sid, enc)
	go s.handleData(stream, enc)
	return true, nil
}
