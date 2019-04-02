from __future__ import print_function
from sys import stderr
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
    cmd(host, "ifconfig " + host.name + "-eth" + str(eth) + " " + ip + " netmask " + netmask)

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
    
    def testConnection(self):
        print("test connection")
        server = PREFIX + str(self.paths) + ".1"
        for i in range(self.paths):
            print("path " + str(i))
            client = PREFIX + str(i) + ".1"
            tail = " >/dev/null 2> /dev/null || echo 1"
            res = cmd(self.client, "ping -qc 1 -I " + client + " " + server + tail)
            if res != "":
                print("failed client -> server")
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
