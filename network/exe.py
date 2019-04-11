from os import path, makedirs
from time import localtime, strftime
from .topo import cmd, log

PARENT = "/tmp/mininet"

def timeStamp():
    return strftime("%m.%d-%H:%M:%S", localtime())

def kill(host, pid):
    cmd(host, "kill " + str(pid))

class Exe(object):
    def __init__(self, name):
        self.name = name
        self.path = PARENT + "/" + name + "/" + timeStamp()
        log("init exec", self.name, "log path" + self.path)
        if not path.exists(self.path):
            makedirs(self.path)
    
    def logRun(self, host, name, c, bg=False, output=False):
        c = c + " 2> " + self.path + "/" + name + ".log"
        if not output:
            c = c + " >&2"
        if bg:
            c = c + " &"
        std = cmd(host, c)
        if bg:
            return int(cmd(host, "echo $!"))
        if output:
            return std
    
    def run(self):
        raise NotImplementedError
