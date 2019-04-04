from __future__ import print_function
from time import sleep, time
from network.exe import Exe, kill
from network.topo import MPTopo, PREFIX

class MPQuicExe(Exe):
    def __init__(self, topo, size):
        Exe.__init__(self, "mpquic")
        self.topo = topo
        self.size = size
    
    def run(self):
        port = ":6121"
        server = PREFIX + str(self.topo.paths) + ".1" + port
        spid = self.logRun(self.topo.server, "server", 'bin/server -size=' + str(self.size) + ' -listen="' + port + '"', True)

        st = time()
        self.logRun(self.topo.client, "client", 'bin/client -url="https://' + server + '"')
        st = time() - st
        print("size: %d, time: %.2fs, bd: %.2fMbps" % (self.size, st, self.size / st * 8 / 1000000))

        sleep(1)
        kill(self.topo.server, spid)

if __name__ == "__main__":
    topo = MPTopo()
    topo.setupNet()
    topo.configBothLink(0, "5Mbit", "10ms")
    topo.configBothLink(1, "10Mbit", "30ms")
    topo.testConnection()
    # topo.getCLI()
    # 20MB
    exe = MPQuicExe(topo, 20 * 1024 * 1024)
    exe.run()
    topo.stopNet()
