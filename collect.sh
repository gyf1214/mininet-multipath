#!/bin/bash

set -e

runsh() {
    # echo $1 $2
    ssh $1 $2
}

tmp=/tmp/mpquic
output=/home/xia/result/real

t=`runsh xia "ls -1 $output | wc -l"`
out=$output/$t
echo $out
runsh xia "mkdir -p $out"

echo server
runsh mpquic.aliyun "tar czf server.tar.gz -C $tmp ."
runsh xia "scp mpquic.aliyun:server.tar.gz $out/"

echo client
runsh xia.client "tar czf client.tar.gz -C $tmp ."
runsh xia "scp xia.client:client.tar.gz $out/"
