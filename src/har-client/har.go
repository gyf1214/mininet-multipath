package main

import (
	"encoding/json"
	"fmt"
	"io"

	"github.com/CyrusBiotechnology/go-har"
)

type database struct {
	data []har.Entry
	vis  []bool
}

var db database

func encodeHeaderHAR(headers []har.NVP) string {
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

func (d *database) load(r io.Reader) error {
	dec := json.NewDecoder(r)

	var full struct{ log har.HAR }
	err := dec.Decode(&full)
	if err != nil {
		return err
	}

	for _, ent := range full.log.Entries {
		req := ent.Request

		// ignore non-http/2
		if req.HttpVersion != "http/2.0" && req.HttpVersion != "http/2.0+quic/43" {
			continue
		}

		d.data = append(d.data, ent)
	}
	d.vis = make([]bool, len(d.data))

	return nil
}
