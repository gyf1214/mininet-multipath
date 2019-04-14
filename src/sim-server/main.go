package main

import (
	"flag"
	"log"

	"github.com/gyf1214/h2quicsim"
	"github.com/lucas-clemente/quic-go"
)

var (
	addr     = flag.String("listen", ":4443", "listen")
	certFile = flag.String("cert", "bin/fullchain.pem", "cert")
	keyFile  = flag.String("key", "bin/privkey.pem", "key")
	harFile  = flag.String("har", "", "har")
)

func main() {
	flag.Parse()
	log.SetFlags(log.Lmicroseconds | log.LstdFlags)
	quic.SetLogLevel("info")

	lis, err := h2quicsim.NewServer(h2quicsim.LoadObjectsPath(*harFile))
	if err != nil {
		log.Fatal(err)
	}
	log.Fatal(lis.Listen(*addr, *certFile, *keyFile))
}
