package main

import (
	"crypto/tls"
	"flag"
	"log"
	"os"
	"sync"

	"github.com/lucas-clemente/quic-go"
)

var (
	addr     = flag.String("listen", ":4443", "listen")
	certFile = flag.String("cert", "bin/fullchain.pem", "cert")
	keyFile  = flag.String("key", "bin/privkey.pem", "key")
	harFile  = flag.String("har", "", "har")
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

func workSession(sess quic.Session) error {
	defer sess.Close(nil)

	ss, err := newServer(sess)
	if err != nil {
		return err
	}

	for {
		ct, err := ss.acceptHeader()
		if err != nil {
			log.Println(err)
		}
		if !ct {
			return err
		}
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
			return err
		}
		go workSession(sess)
	}
}

func initDB() error {
	fin, err := os.Open(*harFile)
	if err != nil {
		return err
	}
	defer fin.Close()
	return db.load(fin)
}

func main() {
	flag.Parse()

	err := initDB()
	if err != nil {
		log.Fatal(err)
	}
	log.Fatal(listen())
}
