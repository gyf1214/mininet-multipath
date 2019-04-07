from __future__ import print_function
from time import sleep, time
from network.exe import Exe, kill
from network.topo import MPTopo, PREFIX, log
from settings import SETTINGS, TESTS, SIZE

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

        bd = self.size / st * 8.0 / 1000.0
        print("size: %d, time: %.2fs, bd: %.0fkbps" % (self.size, st, bd))

        sleep(0.1)
        kill(self.topo.server, spid)

        return bd
    
    def runBatch(self, setting, test):
        # line buffer
        fout = open(self.path + "/batch.log", "w", 1)
        for s in setting:
            for i in range(self.topo.paths):
                t = 2 * i
                self.topo.configBothLink(i, int(s[t] * 1000), int(s[t + 1] * 1000))

            for _ in range(test):
                bd = self.run()
                out = " ".join(tuple(str(x) for x in s))
                out = out + " " + str(bd)
                print(out, file=fout)
                log("output:", out)
        
        fout.close()

if __name__ == "__main__":
    topo = MPTopo()
    topo.setupNet()
    topo.testConnection()
    # CLI
    # topo.getCLI()

    # batch test
    exe = MPQuicExe(topo, SIZE)
    exe.runBatch(SETTINGS, TESTS)

    # small test
    # exe = MPQuicExe(topo, SIZE)
    # topo.configBothLink(0, 5000, 20000)
    # topo.configBothLink(1, 10000, 60000)
    # exe.run()

    topo.stopNet()
