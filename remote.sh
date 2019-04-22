#!/bin/bash

set -e

addr=47.104.219.159:6121
listen=:6121

times=24
algos="merge ssecf sl-wrr wrr"
hars="google amazon"

# times=0
# algos=wrr
# hars=google

runsh() {
    # echo $1 $2
    ssh $1 $2
}

for i in `seq -w 0 $times`; do
    for algo in $algos; do
        sbin=/root/sync-$algo/bin
        cbin=/home/xia/sync-$algo/bin
        tmp=/tmp/mpquic/$algo

        for har in $hars; do
            echo $i $algo $har

            runsh mpquic.aliyun "mkdir -p $tmp"
            runsh mpquic.aliyun "nohup $sbin/sim-server -har=$sbin/$har.json -cert=$sbin/fullchain.pem -key=$sbin/privkey.pem -listen=$listen < /dev/null 2>$tmp/$har-$i.server >/dev/null &"

            sleep 0.1
            runsh xia.client "mkdir -p $tmp"
            runsh xia.client "$cbin/sim-client -har=$cbin/$har.json -addr=$addr 2>$tmp/$har-$i.client >$tmp/$har-$i.log"

            sleep 0.1
            runsh mpquic.aliyun "killall sim-server"
        done
    done
done

