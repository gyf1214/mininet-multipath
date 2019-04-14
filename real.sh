#!/bin/bash

out=/dev/null
# out=/tmp/1.err

mkdir -p /tmp/mpquic/$3
for i in `seq -w 0 $1`; do
    echo $i
    bin/sim-client -har="bin/$2.json" -addr="47.104.97.160:6121" 2> $out > /tmp/mpquic/$3/$2-$i.log
done
