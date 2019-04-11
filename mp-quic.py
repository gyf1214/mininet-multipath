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
        self.port = ":6121"
        self.server = PREFIX + str(self.topo.paths) + ".1" + self.port
    
    def run(self):
        spid = self.logRun(self.topo.server, "server", 'bin/server -size=' + str(self.size) + ' -listen="' + self.port + '"', True)

        st = time()
        self.logRun(self.topo.client, "client", 'bin/client -url="https://' + self.server + '"')
        st = time() - st

        bd = self.size / st * 8.0 / 1000.0
        print("size: %d, time: %.2fs, bd: %.0fkbps" % (self.size, st, bd))

        sleep(0.1)
        kill(self.topo.server, spid)

        return bd

    def runHar(self, harFile):
        fout = open(self.path + "/batch.log", "w", 1)
        spid = self.logRun(self.topo.server, "har-server", 'bin/har-server -har="' + harFile + '" -listen="' + self.port + '"', True)

        # st = time()
        out = self.logRun(self.topo.client, "har-client", 'bin/har-client -har="' + harFile + '" -addr="' + self.server + '"', output=True)
        fout.write(out)
        # st = time() - st

        # print("time: %.2f" % st)

        sleep(0.1)
        kill(self.topo.server, spid)
        fout.close()

    
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

    # har test
    topo.configBothLink(0, 5000, 10000)
    topo.configBothLink(1, 5000, 10000)
    exe = MPQuicExe(topo, SIZE)
    exe.runHar("bin/www.google.com.har")

    # batch test
    # exe = MPQuicExe(topo, SIZE)
    # exe.runBatch(SETTINGS, TESTS)

    # small test
    # exe = MPQuicExe(topo, SIZE)
    # topo.configBothLink(0, 5000, 20000)
    # topo.configBothLink(1, 10000, 60000)
    # exe.run()

    topo.stopNet()
