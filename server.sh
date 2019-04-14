#!/bin/bash

out=/dev/null
# out=/tmp/1.err

bin/sim-server -har="bin/$1.json" -listen=":6121" 2> $out
