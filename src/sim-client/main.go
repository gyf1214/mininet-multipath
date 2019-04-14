package main

import (
	"flag"
	"log"

	"github.com/gyf1214/h2quicsim"
	"github.com/lucas-clemente/quic-go"
)

var (
	addr    = flag.String("addr", "127.0.0.1:4443", "addr")
	harFile = flag.String("har", "", "har")
)

func main() {
	flag.Parse()
	log.SetFlags(log.Lmicroseconds | log.LstdFlags)
	quic.SetLogLevel("info")

	cl, err := h2quicsim.NewClient(h2quicsim.LoadObjectsPath(*harFile))
	if err != nil {
		log.Fatal(err)
	}

	err = cl.Run(*addr)
	if err != nil {
		log.Fatal(err)
	}
	cl.Wait()
}
