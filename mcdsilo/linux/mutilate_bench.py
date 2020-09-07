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
import shutil

MASTER = "192.168.1.9"
CSERVER = "192.168.1.11"
CSERVER2 = "192.168.1.9"
ITR = 1
WTHRESH = 0
PTHRESH = 0
HTHRESH = 0
THRESHC = 0
DTXMXSZRQ = 0
DCA = 0
RSC_DELAY = 0
MAX_DESC = 0
BSIZEPKT = 0
BSIZEHDR = 0
RXRING = 0
TXRING = 0
RAPL = 135
DVFS = '0xffff'
ITRC = []
TYPE = 'etc'
TIME = 120
SEARCH = 0
VERBOSE = 0
TARGET_QPS=100000
NREPEAT = 0

WORKLOADS = {
    'etc': '--keysize=fb_key --valuesize=fb_value --iadist=fb_ia --update=0.0',
}

'''
MOC NODES:
+-----------+
| Nodes (7) |
+-----------+
|  neu-5-25  | -> Intel(R) Xeon(R) CPU E5-2630L v2 @ 2.40GHz, 126 GB, 12 cores, Ubuntu 18.04, 4.15.1, 82599ES -> 192.168.1.205: mutilate
|  neu-5-24  | -> Intel(R) Xeon(R) CPU E5-2630L v2 @ 2.40GHz, 126 GB, 12 cores, Ubuntu 18.04, 4.15.1, 82599ES -> 192.168.1.204: mutilate
|  neu-5-9   | -> Intel(R) Xeon(R) CPU E5-2690 0 @ 2.90GHz, 126 GB, Ubuntu 18.04, 5.0.0, 82599ES, 192.168.1.20: launcher
|  neu-5-8   | -> Intel(R) Xeon(R) CPU E5-2690 0 @ 2.90GHz, 126 GB, Ubuntu 18.04, 4.15.1, 82599ES, 192.168.1.200: nic server
|  neu-5-11  | -> Intel(R) Xeon(R) CPU E5-2690 0 @ 2.90GHz, 126 GB, RHEL 7.7, 3.10.0, 82599ES -> 192.168.1.202: mutilate
|  neu-3-8   | -> Intel(R) Xeon(R) CPU E5-2690 0 @ 2.90GHz, 126 GB, Ethernet controller: Solarflare Communications SFC9120 10G Ethernet Controller
|  neu-15-8  | -> Intel(R) Xeon(R) CPU E5-2690 0 @ 2.90GHz, 252 GB, Ethernet controller: Intel Corporation 82599ES 10-Gigabit SFI/SFP+

   neu-19-33   -> model name	: Intel(R) Xeon(R) CPU E5-2660 0 @ 2.20GHz

+------------+

 192.168.1.201,192.168.1.202,192.168.1.203,192.168.1.204,192.168.1.205
'''

def runLocalCommandOut(com):
    #print(com)
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    p1.communicate()
    #print("\t"+com, "->\n", p1.communicate()[0].strip())
    
def runRemoteCommandOut(com):
    #print(com)
    p1 = Popen(["ssh", MASTER, com], stdout=PIPE)
    p1.communicate()
    #print("\tssh "+MASTER, com, "->\n", p1.communicate()[0].strip())

def runLocalCommand(com):
    #print(com)
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    
def runRemoteCommand(com):
    #print(com)
    p1 = Popen(["ssh", MASTER, com])

def runRemoteCommands(com, server):
    #print(com)
    p1 = Popen(["ssh", server, com])

def runRemoteCommandGet(com, server):
    #print(com)
    p1 = Popen(["ssh", server, com], stdout=PIPE)
    return p1.communicate()[0].strip()

def setITR(v):
    global ITR
    p1 = Popen(["ssh", CSERVER2, "/app/ethtool-4.5/ethtool -C eth0 rx-usecs", v], stdout=PIPE, stderr=PIPE)
    p1.communicate()    
    time.sleep(0.5)
    ITR = int(v)

def setRAPL(v):
    global RAPL
    p1 = Popen(["ssh", CSERVER2, "/app/uarch-configure/rapl-read/rapl-power-mod", v], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    time.sleep(0.5)
    RAPL = int(v)

def setDVFS(v):
    global DVFS
    p1 = Popen(["ssh", CSERVER2, "wrmsr -a 0x199", v], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    time.sleep(0.5)
    DVFS = v
    
def cleanLogs():
    for i in range(1, 16):                    
        runRemoteCommandGet("/app/ethtool-4.5/ethtool -C eth0 DUMP_DYNAMIC_ITR "+str(i), "192.168.1.9")
        runRemoteCommandGet("dmesg -C", "192.168.1.9")
        if VERBOSE:
            print("cleanLogs", i)
            
def printLogs():
    for i in range(1, 16):
        runRemoteCommandGet("/app/ethtool-4.5/ethtool -C eth0 DUMP_DYNAMIC_ITR "+str(i), "192.168.1.9")
        runRemoteCommandGet("dmesg -c &> /app/mcdsilo_dmesg."+str(i-1), "192.168.1.9")
        if VERBOSE:
            print("printLogs", i)

def getLogs():
    for i in range(1, 16):
        runLocalCommandOut("scp -r 192.168.1.9:/app/mcdsilo_dmesg."+str(i-1)+" mcdsilo_dmesg."+str(NREPEAT)+"_"+str(i-1)+"_"+str(ITR)+"_"+str(DVFS)+"_"+str(RAPL)+"_"+str(TARGET_QPS))       
        if VERBOSE:
            print("getLogs", i)
    runLocalCommandOut("scp -r 192.168.1.9:/tmp/mcdsilo.rdtsc mcdsilo_rdtsc."+str(NREPEAT)+"_"+str(1)+"_"+str(ITR)+"_"+str(DVFS)+"_"+str(RAPL)+"_"+str(TARGET_QPS))        
    
def runBenchASPLOS(mqps):
    runRemoteCommandGet("pkill mutilate", "192.168.1.38")
    runRemoteCommandGet("pkill mutilate", "192.168.1.37")
    time.sleep(1)
    
    runRemoteCommands("/app/mutilate/mutilate --agentmode --threads=16", "192.168.1.37")
    runRemoteCommands("/app/mutilate/mutilate --agentmode --threads=16", "192.168.1.38")
    time.sleep(2)
    
    check_mcd = False
    while check_mcd == False:
        is_running_mcd = runRemoteCommandGet("pgrep silotpcc-linux", "192.168.1.9")
        if is_running_mcd:
            if VERBOSE:
                print("already running silotpcc-linux")
            check_mcd = True
        else:
            if VERBOSE:
                print("launching silotpcc-linux")
            runRemoteCommands("taskset -c 0-15 /app/zygos-bench/servers/silotpcc-linux", "192.168.1.9")
            time.sleep(60)
        
    cleanLogs()
    time.sleep(1)
    
    output = runRemoteCommandGet("taskset -c 0 /app/mutilate/mutilate --binary -s 192.168.1.9 --noload --agent=192.168.1.38,192.168.1.37 --threads=1 "+WORKLOADS[TYPE]+" --depth=4 --measure_depth=1 --connections=16 --measure_connections=32 --measure_qps=2000 --qps="+str(mqps)+" --time="+str(TIME), "192.168.1.11")    
    
    if VERBOSE:
        print("Finished executing memcached")
        
    f = open("mcdsilo_out."+str(NREPEAT)+"_"+str(ITR)+"_"+str(DVFS)+"_"+str(RAPL)+"_"+str(TARGET_QPS), "w")
    for line in str(output).strip().split("\\n"):
        #print(line.strip())
        f.write(line.strip()+"\n")
    f.close()
    
    printLogs()
    runRemoteCommands("killall -USR2 silotpcc-linux", "192.168.1.9")
    time.sleep(1)
    getLogs()    
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--bench", help="Type of benchmark [mcd, zygos]")
    parser.add_argument("--rapl", help="Rapl power limit [35, 135]")
    parser.add_argument("--itr", help="Static interrupt delay [10, 500]")
    parser.add_argument("--dvfs", help="DVFS value [0xc00 - 0x1d00]")
    parser.add_argument("--nrepeat", help="repeat value")
    parser.add_argument("--qps", type=int, help="RPS rate")
    parser.add_argument("--time", type=int, help="Time in seconds to run")
    parser.add_argument("--ring", type=int, help="TX and RX ring")
    parser.add_argument("--dtxmx", type=int, help="DTXMXSZRQ")
    parser.add_argument("--dca", type=int, help="DCA")
    parser.add_argument("--thresh", type=int, help="PTHRESH, HTHRESH, WTHRESH")
    parser.add_argument("--restartnic", type=int, help="restart nic")
    parser.add_argument("--type", help="Workload type [etc, usr]")
    parser.add_argument("--pow_search_enable", help="Limit printf for search power limit")
    parser.add_argument("--verbose", help="Print mcd raw stats")
    
    args = parser.parse_args()
    if args.rapl:
        #print("RAPL = ", args.rapl)
        setRAPL(args.rapl)
    if args.itr:
        #print("ITR = ", args.itr)
        setITR(args.itr)
    if args.qps:
        TARGET_QPS = args.qps
        #print("TARGET_QPS = ", TARGET_QPS)
    if args.dvfs:
        setDVFS(args.dvfs)
    if args.nrepeat:
        NREPEAT = args.nrepeat
    if args.time:
        TIME = args.time
        #print("TIME = ", TIME)
    if args.type:
        TYPE = args.type
        print("TYPE = ", TYPE)
    if args.pow_search_enable:
        SEARCH = 1
    if args.verbose:
        VERBOSE = 1

    runBenchASPLOS(TARGET_QPS)            
