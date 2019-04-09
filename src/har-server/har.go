package main

import (
	"encoding/json"
	"fmt"
	"io"

	"github.com/CyrusBiotechnology/go-har"
)

type database struct {
	data map[string]har.Response
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

func checkEnt(ent har.Entry) bool {
	if ent.Request.HttpVersion != "http/2.0" && ent.Request.HttpVersion != "http/2.0+quic/43" {
		return false
	}

	hasLength, hasAuthority := false, false
	for _, header := range ent.Request.Headers {
		if header.Name == ":authority" {
			hasAuthority = true
			break
		}
	}
	for _, header := range ent.Response.Headers {
		if header.Name == "content-length" {
			hasLength = true
			break
		}
	}
	return hasLength && hasAuthority
}

func (d *database) load(r io.Reader) error {
	dec := json.NewDecoder(r)

	var full struct{ Log har.HAR }
	err := dec.Decode(&full)
	if err != nil {
		return err
	}

	d.data = make(map[string]har.Response)
	for _, ent := range full.Log.Entries {
		if !checkEnt(ent) {
			continue
		}
		enc := encodeHeaderHAR(ent.Request.Headers)
		d.data[enc] = ent.Response
	}

	return nil
}
