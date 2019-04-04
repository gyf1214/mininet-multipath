from __future__ import print_function
from sys import stderr
from math import ceil
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.cli import CLI

DEBUG = True
NETMASK = "255.255.255.0"
PREFIX = "10.1."

# utils functions
def log(*args, **kwargs):
    if DEBUG:
        print(*args, file=stderr, **kwargs)

def cmd(host, c):
    log(host.name, c)
    return host.cmd(c)

def interfaceUp(host, eth, ip, netmask=NETMASK):
    # hardcode 20000 txqueuelen for a BDP of around 100Mbps * 2400ms
    cmd(host, "ifconfig " + host.name + "-eth" + str(eth) + " " + ip + " netmask " + netmask + " txqueuelen 20000")

def tcConfig(host, eth, bd, delay, limit):
    eth = " dev " + host.name + "-eth" + str(eth)
    cmd(host, "tc qdisc del" + eth + " root")
    cmd(host, "tc qdisc add" + eth + " root handle 5:0 htb default 1")
    cmd(host, "tc class add" + eth + " parent 5:0 classid 5:1 htb rate " + str(bd) + "kbit burst 15k")
    cmd(host, "tc qdisc add" + eth + " parent 5:1 handle 10: netem delay " + str(delay) + "us limit " + str(limit))

class BaseTopo(Topo):
    "Basic topo"
    def __init__(self):
        Topo.__init__(self)
        self.net = None
    
    def startNet(self):
        self.net = Mininet(topo=self, link=TCLink)
        self.net.start()

    def getCLI(self):
        CLI(self.net)
    
    def stopNet(self):
        self.net.stop()

class MPTopo(BaseTopo):
    "Multipath"
    def __init__(self):
        BaseTopo.__init__(self)
    
    def configDevice(self, paths=2):
        self.paths = paths
        self.client = self.addHost("client")
        self.server = self.addHost("server")
        self.router = self.addHost("router")
        # self.switches = []
        for _ in range(paths):
            self.addLink(self.client, self.router)
            # self.switches.append(switch)
        self.addLink(self.router, self.server)
    
    def configClient(self, path, subnet):
        table = " table " + str(path + 1)
        eth = " dev " + self.client.name + "-eth" + str(path) + table
        cmd(self.client, "ip rule add from " + subnet + ".1" + table)
        cmd(self.client, "ip route add " + subnet + ".0/24" + eth)
        cmd(self.client, "ip route add default via " + subnet + ".2" + eth)
    
    def configInterface(self):
        self.client = self.net.getNodeByName(self.client)
        self.server = self.net.getNodeByName(self.server)
        self.router = self.net.getNodeByName(self.router)
        for i in range(self.paths):
            subnet = PREFIX + str(i)
            interfaceUp(self.client, i, subnet + ".1")
            interfaceUp(self.router, i, subnet + ".2")
            self.configClient(i, subnet)
        # add default path
        cmd(self.client, "ip route add default via " + PREFIX + "0.2")
        subnet = PREFIX + str(self.paths)
        interfaceUp(self.server, 0, subnet + ".1")
        interfaceUp(self.router, self.paths, subnet + ".2")
        cmd(self.server, "ip route add default via " + subnet + ".2")
    
    def configLink(self, path, bd, delay, limit, uplink=False):
        host = self.client if uplink else self.router
        tcConfig(host, path, bd, delay, limit)
    
    def configBothLink(self, path, bd, rtt, queue_delay):
        "bd in kbps, rtt & queue_delay in us"
        limit = int(ceil(float(rtt + queue_delay) * float(bd) / 12000000.0))
        if limit < 1:
            limit = 1
        # we split rtt on uplink & downlink
        self.configLink(path, bd, rtt / 2, limit, False)
        self.configLink(path, bd, rtt / 2, limit, True)
    
    def testConnection(self):
        print("test connection")
        server = PREFIX + str(self.paths) + ".1"
        for i in range(self.paths):
            print("path " + str(i))
            client = PREFIX + str(i) + ".1"
            tail = " >/dev/null 2> /dev/null || echo 1"
            res = cmd(self.client, "ping -qc 1 -I " + client + " " + server + tail)
            if res != "":
                print("ping failed client -> server")
            res = cmd(self.server, "ping -qc 1 " + client + tail)
            if res != "":
                print("failed server -> client")
    
    def setupNet(self):
        self.configDevice()
        self.startNet()
        self.configInterface()

if __name__ == "__main__":
    topo = MPTopo()
    topo.setupNet()
    topo.testConnection()
    topo.getCLI()
    topo.stopNet()
