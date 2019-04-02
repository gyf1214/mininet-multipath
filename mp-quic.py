from time import sleep
from network.exe import Exe, kill
from network.topo import MPTopo, PREFIX

class MPQuicExe(Exe):
    def __init__(self, topo):
        Exe.__init__(self, "mpquic")
        self.topo = topo
    
    def run(self):
        port = ":6121"
        server = PREFIX + str(self.topo.paths) + ".1" + port
        spid = self.logRun(self.topo.server, "server", 'bin/server -size=1048576 -listen="' + port + '"', True)
        self.logRun(self.topo.client, "client", 'bin/client -url="https://' + server + '"')
        sleep(1)
        kill(self.topo.server, spid)

if __name__ == "__main__":
    topo = MPTopo()
    topo.setupNet()
    topo.testConnection()
    exe = MPQuicExe(topo)
    exe.run()
    topo.stopNet()
