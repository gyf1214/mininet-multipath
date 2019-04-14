#!/bin/bash

bin/sim-server -har="bin/$1.json" -listen=":6121" 2> /dev/null
