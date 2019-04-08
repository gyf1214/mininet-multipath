package main

import (
	"crypto/tls"
	"flag"
	"fmt"
	"log"
	"sync"

	"github.com/lucas-clemente/quic-go"
	"golang.org/x/net/http2"
	"golang.org/x/net/http2/hpack"
)

var (
	addr     = flag.String("listen", ":4443", "listen")
	certFile = flag.String("cert", "bin/fullchain.pem", "cert")
	keyFile  = flag.String("key", "bin/privkey.pem", "key")
)

func handleStreams(sess quic.Session, streams map[int]quic.Stream, streamMutex *sync.Mutex) {
	for {
		if str, err := sess.AcceptStream(); err == nil {
			streamMutex.Lock()
			streams[int(str.StreamID())] = str
			streamMutex.Unlock()
		} else {
			log.Println(err)
			return
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

func workSession(sess quic.Session) {
	defer sess.Close(nil)

	header, err := sess.AcceptStream()
	streams := make(map[int]quic.Stream)
	streamMutex := &sync.Mutex{}
	go handleStreams(sess, streams, streamMutex)

	hpackDecoder := hpack.NewDecoder(4096, nil)
	h2Framer := http2.NewFramer(nil, header)

	for {
		frame, err := h2Framer.ReadFrame()
		if err != nil {
			log.Println(err)
			break
		}
		headerFrame, ok := frame.(*http2.HeadersFrame)
		if !ok || !headerFrame.HeadersEnded() {
			log.Println("get non-header frame, ignore")
			continue
		}
		headers, err := hpackDecoder.DecodeFull(headerFrame.HeaderBlockFragment())
		if err != nil {
			log.Println("cannot decode header frame, ignore")
			continue
		}

		sid := int(headerFrame.StreamID)
		streamMutex.Lock()
		stream := streams[sid]
		streamMutex.Unlock()
	}
}

func listen() error {
	cert, err := tls.LoadX509KeyPair(*certFile, *keyFile)
	if err != nil {
		return err
	}
	listener, err := quic.ListenAddr(*addr, &tls.Config{
		Certificates: []tls.Certificate{cert},
	}, nil)
	if err != nil {
		return err
	}
	defer listener.Close()

	for {
		sess, err := listener.Accept()
		if err != nil {
			log.Println(err)
		}
		go workSession(sess)
	}
}
