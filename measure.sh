#!/bin/bash

set -e

runsh() {
    # echo $1 $2
    ssh $1 $2
}

tmp=/tmp/mpquic
suff="</dev/null 2>/dev/null >/dev/null &"
pp="-p 5001"
addr=47.104.219.159
adds="192.168.1.100 192.168.42.21"

runsh mpquic.aliyun "mkdir -p $tmp"
runsh xia.client "mkdir -p $tmp"

runsh mpquic.aliyun "nohup tcpdump -n -i eth0 -w $tmp/server.pcap port 5001 $suff"
runsh mpquic.aliyun "iperf3 $pp -s -D"

runsh xia.client "nohup tcpdump -n -i enp0s20f0u1 -w $tmp/rmnet.pcap port 5001 $suff"
runsh xia.client "nohup tcpdump -n -i wlp1s0 -w $tmp/wifi.pcap port 5001 $suff"
for add in $adds; do
    runsh xia.client "iperf3 -B $add $pp -c $addr -R"
    runsh xia.client "iperf3 -B $add $pp -c $addr"
done

sleep 0.1

runsh xia.client "killall tcpdump"

runsh mpquic.aliyun "killall iperf3"
runsh mpquic.aliyun "killall tcpdump"
