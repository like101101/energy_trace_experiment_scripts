import math
import random
import subprocess
from subprocess import Popen, PIPE, call
import time
from datetime import datetime
import sys
import os
import getopt
import numpy as np
import itertools
import argparse

SERVER = "192.168.1.9"

ITR = "1"
RAPL = "135"
NREPEAT = "0"

com_dict = {
    "com1" : 'ssh 192.168.1.11 taskset -c 1 /app/wrk-4.0.2/wrk -t1 -c1 -d30s http://192.168.1.9:6666/index.html --latency',
#    "com512" : "ssh 192.168.1.11 taskset -c 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15 /dev/shm/wrk -t16 -c512 -d30s http://192.168.1.230:6666/index.html --latency",
#    'com1_1024' : 'ssh 192.168.1.11 taskset -c 1 /dev/shm/wrk -t1 -c1 -d30s -H "Host: example.com \n Host: test.go Host: example.com \n  Host: example.com \n  Host: example.com \n  Host: example.com \n Host: example.com \n Host: example.com Host: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.com Host: example.comHost: example.com Host: example.com \n Host: test.go Host: example.com \n  Host: example.com \n  Host: example.com \n  Host: example.com \n Host: example.com \n Host: example.com Host: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.com Host: example.comHost: " http://192.168.1.230:6666/index.html --latency',
#    'com512_1024' : 'ssh 192.168.1.11 taskset -c 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15 /dev/shm/wrk -t16 -c512 -d30s -H "Host: example.com \n Host: test.go Host: example.com \n  Host: example.com \n  Host: example.com \n  Host: example.com \n Host: example.com \n Host: example.com Host: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.com Host: example.comHost: example.com Host: example.com \n Host: test.go Host: example.com \n  Host: example.com \n  Host: example.com \n  Host: example.com \n Host: example.com \n Host: example.com Host: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.com Host: example.comHost: " http://192.168.1.230:6666/index.html --latency'
}

dvfs_dict = {
    "1.2" : "0xC00",
    "1.3" : "0xD00",
    "1.4" : "0xE00",
    "1.5" : "0xF00",
    "1.6" : "0x1000",
    "1.7" : "0x1100",
    "1.8" : "0x1200",
    "1.9" : "0x1300",
    "2.0" : "0x1400",
    "2.1" : "0x1500",
    "2.2" : "0x1600",
    "2.3" : "0x1700",
    "2.4" : "0x1800",
    "2.5" : "0x1900",
    "2.6" : "0x1A00",
    "2.7" : "0x1B00",
    "2.8" : "0x1C00",
    "2.9" : "0x1D00",
}

DVFS = "0xffff" #dvfs_dict["2.9"]
COM = com_dict['com1']

def runLocalCommandOut(com):
    #print(com)
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    p1.communicate()
    #print("\t"+com, "->\n", p1.communicate()[0].strip())
    
def runRemoteCommandOut(com):
    #print(com)
    p1 = Popen(["ssh", SERVER, com], stdout=PIPE)
    p1.communicate()
    #print("\tssh "+SERVER, com, "->\n", p1.communicate()[0].strip())

def runLocalCommand(com):
    #print(com)
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    
def runRemoteCommand(com):
    #print(com)
    p1 = Popen(["ssh", SERVER, com])

def runRemoteCommands(com, server):
    #print(com)
    p1 = Popen(["ssh", server, com])

def runRemoteCommandGet(com):
    #print(com)
    p1 = Popen(["ssh", SERVER, com], stdout=PIPE)
    return p1.communicate()[0].strip()

def init():
    r = runRemoteCommandGet("ls /dev/shm/")
    if len(r) == 0:
        runRemoteCommandOut("cp ~/node /dev/shm/")
        runRemoteCommandOut("cp ~/hello_http.js /dev/shm/")        
    
def setRAPL(v):
    global RAPL
    p1 = Popen(["ssh", SERVER, "/app/uarch-configure/rapl-read/rapl-power-mod", v], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    time.sleep(0.5)
    RAPL = v

def setDVFS(v):
    global DVFS
    p1 = Popen(["ssh", SERVER, "wrmsr -p 1 0x199", v], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    time.sleep(0.5)
    DVFS = v

def setITR(v):
    global ITR
    p1 = Popen(["ssh", SERVER, "/app/ethtool-4.5/ethtool -C eth0 rx-usecs", v], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    time.sleep(0.5)
    ITR = v

def cleanLogs():
    #core 1
    for i in range(1, 17):
        runRemoteCommandGet("/app/ethtool-4.5/ethtool -C eth0 DUMP_DYNAMIC_ITR "+str(i))
        runRemoteCommandGet("dmesg -C")
    runRemoteCommandGet("/app/ethtool-4.5/ethtool -C eth0 DUMP_DYNAMIC_ITR 2")
    runRemoteCommandGet("dmesg -C")

def printLogs():
    #core 1
    runRemoteCommandGet("/app/ethtool-4.5/ethtool -C eth0 DUMP_DYNAMIC_ITR 2")
    runRemoteCommandGet("dmesg -c &> /app/node_dmesg.1")

def getLogs():
    runLocalCommandOut("scp -r 192.168.1.9:/app/node_dmesg.1"+" node_dmesg."+str(NREPEAT)+"_"+"1_"+str(ITR)+"_"+str(DVFS)+"_"+str(RAPL))
    runLocalCommandOut("scp -r 192.168.1.9:/tmp/node.rdtsc node_rdtsc."+str(NREPEAT)+"_"+"1_"+str(ITR)+"_"+str(DVFS)+"_"+str(RAPL))

def runWrk():
    output = runRemoteCommandGet("pgrep node")
    if len(output) == 0:
        runRemoteCommand("taskset -c 1 /app/node-0.10.26/node /app/node-0.10.26/hello_http.js")
        time.sleep(1)
    
    cleanLogs()
    time.sleep(1)

    # run wrk
    p1 = Popen(list(filter(None, COM.strip().split(' '))), stdout=PIPE)
    wrkOut = p1.communicate()[0].strip()
    
    f = open("node_out."+str(NREPEAT)+"_1_"+str(ITR)+"_"+str(DVFS)+"_"+str(RAPL), 'w')
    for l in str(wrkOut).split("\\n"):
        f.write(l.strip()+"\n")
    f.close()

    runRemoteCommandGet("killall -USR2 node")
    printLogs()
    getLogs()
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--rapl", help="Rapl power limit [46, 136]")
    parser.add_argument("--dvfs", help="Cpu frequency [0x1D00 ... 0xC00]")
    parser.add_argument("--com", help="com1 == -t1 -c1, com512 == -t16 -c512, com1_1024 == 1024 bytes")
    parser.add_argument("--itr", help="Static interrupt delay [10, 1000]")
    parser.add_argument("--nrepeat", help="repeat value")
        
    args = parser.parse_args()
    if args.rapl:
        setRAPL(args.rapl)
    if args.dvfs:
        setDVFS(args.dvfs)
    if args.com:
        COM = args.com
    if args.itr:
        setITR(args.itr)        
    if args.nrepeat:
        NREPEAT = args.nrepeat
    
    #init()
    runWrk()
