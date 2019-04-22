#!/bin/bash

set -e

algos="merge ssecf sl-wrr wrr"

runsh() {
    # echo $1 $2
    ssh $1 $2
}

runsh mpquic.aliyun "killall -q sim-server iperf3 tcpdump; echo 1"
runsh mpquic.aliyun "rm -fr /tmp/mpquic"

runsh xia.client "killall -q sim-client iperf3 tcpdump; echo 1"
runsh xia.client "rm -fr /tmp/mpquic"

for i in $algos; do
    pushd ~/go/src/github.com/lucas-clemente/quic-go
    git checkout dev-$i
    popd

    make force
    
	rsync -avz --delete ./ mpquic.aliyun:~/sync-$i/
	rsync -avz --delete ./ xia.client:~/sync-$i/
done
