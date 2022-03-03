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
DCA = 0
RAPL = 135
DVFS = '0xffff'
TYPE = 'etc'
TIME = 120
VERBOSE = 0
TARGET_QPS=100000
NREPEAT = 0

WORKLOADS = {
    #ETC = 75% GET, 25% SET
    'etc': '--keysize=fb_key --valuesize=fb_value --iadist=fb_ia --update=0.25',

    #USR = 99% GET, 1% SET
    'usr': '--keysize=19 --valuesize=2 --update=0.01',

    'etc2': '--keysize=fb_key --valuesize=fb_value --iadist=fb_ia --update=0.033'
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

   neu-5-9     -> 192.168.1.9

   neu-3-7     -> 192.168.1.37   Intel(R) Xeon(R) CPU E5-2660 0 @ 2.20GHz        Intel(R) 10 Gigabit PCI Express Network Driver   
   neu-3-8     -> 192.168.1.38   Intel(R) Xeon(R) CPU E5-2690 0 @ 2.90GHz         
   bu-23-104   -> 192.168.1.104   Intel(R) Xeon(R) CPU E5-2650 v2 @ 2.60GHz       Intel(R) 10 Gigabit Network Connection
   bu-23-106   -> 192.168.1.106   Intel(R) Xeon(R) CPU E5-2650 v2 @ 2.60GHz       Intel(R) 10 Gigabit Network Connection
   bu-23-107   -> 192.168.1.107   Intel(R) Xeon(R) CPU E5-2650 v2 @ 2.60GHz       Intel(R) 10 Gigabit Network Connection

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
    
    if ITR != 1:
        p1 = Popen(["ssh", CSERVER2, "/app/uarch-configure/rapl-read/rapl-power-mod", v], stdout=PIPE, stderr=PIPE)
        p1.communicate()
        time.sleep(0.5)
    RAPL = int(v)

def setDVFS(v):
    global DVFS

    if ITR != 1:
        p1 = Popen(["ssh", CSERVER2, "wrmsr -a 0x199", v], stdout=PIPE, stderr=PIPE)
        p1.communicate()
        time.sleep(0.5)
    DVFS = v

def cleanLogs():
    for i in range(0, 16):                    
        runRemoteCommandGet("cat /proc/ixgbe_stats/core/"+str(i)+" &> /dev/null", "192.168.1.9")
        if VERBOSE:
            print("cleanLogs", i)
            
def printLogs():
    for i in range(0, 16):
        runRemoteCommandGet("cat /proc/ixgbe_stats/core/"+str(i)+" &> /app/mcd_dmesg."+str(i), "192.168.1.9")
        if VERBOSE:
            print("printLogs", i)    

def getLogs():
    for i in range(0, 16):
        runLocalCommandOut("scp -r 192.168.1.9:/app/mcd_dmesg."+str(i)+" linux.mcd.dmesg."+str(NREPEAT)+"_"+str(i)+"_"+str(ITR)+"_"+str(DVFS)+"_"+str(RAPL)+"_"+str(TARGET_QPS))        
        if VERBOSE:
            print("getLogs", i)
    runLocalCommandOut("scp -r 192.168.1.9:/tmp/mcd.rdtsc linux.mcd.rdtsc."+str(NREPEAT)+"_"+str(ITR)+"_"+str(DVFS)+"_"+str(RAPL)+"_"+str(TARGET_QPS))

def runBench(mqps):
    runRemoteCommandGet("pkill mutilate", "192.168.1.104")
    runRemoteCommandGet("pkill mutilate", "192.168.1.106")
    runRemoteCommandGet("pkill mutilate", "192.168.1.107")        
    runRemoteCommandGet("pkill mutilate", "192.168.1.38")
    runRemoteCommandGet("pkill mutilate", "192.168.1.37")
    runRemoteCommandGet("pkill mutilate", "192.168.1.11")

    time.sleep(1)

    runRemoteCommands("/app/mutilate/mutilate --agentmode --threads=16", "192.168.1.37")
    runRemoteCommands("/app/mutilate/mutilate --agentmode --threads=16", "192.168.1.38")
    runRemoteCommands("/app/mutilate/mutilate --agentmode --threads=16", "192.168.1.104")
    runRemoteCommands("/app/mutilate/mutilate --agentmode --threads=16", "192.168.1.106")
    runRemoteCommands("/app/mutilate/mutilate --agentmode --threads=16", "192.168.1.107")
    time.sleep(1)

    is_running_mcd = runRemoteCommandGet("pgrep memcached", "192.168.1.9")
    if is_running_mcd:
        print("already running mcd")
    else:
        ## 16 core server or 1 core
        
        runRemoteCommands("taskset -c 0-15 /app/memcached/memcached -u root -t 16 -m 32G -c 8192 -b 8192 -l 192.168.1.9 -B binary", "192.168.1.9")
        #runRemoteCommands("taskset -c 1 /app/memcached/memcached -u root -t 1 -m 16G -c 8192 -b 8192 -l 192.168.1.9 -B binary", "192.168.1.9")
        time.sleep(1)

        ## large key, value stores
        #runRemoteCommandGet("taskset -c 0 /app/mutilate/mutilate --binary -s 192.168.1.9 --loadonly -K normal:200,2 -V normal:2000,2", "192.168.1.11")

        ## place some ETC load
        runRemoteCommandGet("taskset -c 0 /app/mutilate/mutilate --binary -s 192.168.1.9 --loadonly -K fb_key -V fb_value", "192.168.1.11")
    time.sleep(1)

    ## dump logs to /dev/null first
    cleanLogs()

    ## run workload
    output = runRemoteCommandGet("taskset -c 0 /app/mutilate/mutilate --binary -s 192.168.1.9 --noload --agent=192.168.1.104,192.168.1.106,192.168.1.107,192.168.1.37,192.168.1.38 --threads=1 "+WORKLOADS[TYPE]+" --depth=4 --measure_depth=1 --connections=16 --measure_connections=32 --measure_qps=2000 --qps="+str(mqps)+" --time="+str(TIME), "192.168.1.11")
    #output = runRemoteCommandGet("taskset -c 0 /app/mutilate/mutilate --binary -s 192.168.1.9 --noload --agent=192.168.1.106,192.168.1.107,192.168.1.37,192.168.1.38 --threads=1 --keysize=normal:200,2 --valuesize=normal:2000,2 --update=0.25 --depth=4 --measure_depth=1 --connections=16 --measure_connections=32 --measure_qps=2000 --qps="+str(mqps)+" --time="+str(TIME), "192.168.1.11")

    ## trigger signal to dump rdtsc
    runRemoteCommands("killall -USR2 memcached", "192.168.1.9")
    
    if VERBOSE:
        print("Finished executing memcached")
    
    f = open("linux.mcd.out."+str(NREPEAT)+"_"+str(ITR)+"_"+str(DVFS)+"_"+str(RAPL)+"_"+str(TARGET_QPS), "w")
    for line in str(output).strip().split("\\n"):
        f.write(line.strip()+"\n")
    f.close()
    
    printLogs()
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
    parser.add_argument("--type", help="Workload type [etc, usr]")
    parser.add_argument("--verbose", help="Print mcd raw stats")
    
    args = parser.parse_args()

    if args.itr:
        #print("ITR = ", args.itr)
        setITR(args.itr)

    if args.dvfs:
        setDVFS(args.dvfs)
        
    if args.rapl:
        #print("RAPL = ", args.rapl)
        setRAPL(args.rapl)
    
    if args.qps:
        TARGET_QPS = args.qps
        #print("TARGET_QPS = ", TARGET_QPS)
    
    if args.nrepeat:
        NREPEAT = args.nrepeat
        
    if args.time:
        TIME = args.time
        #print("TIME = ", TIME)
        
    if args.type:
        TYPE = args.type
        print("TYPE = ", TYPE)
        
    if args.verbose:
        VERBOSE = 1

    if args.bench == "mcd":
        runBench(TARGET_QPS)
    else:
        print("unknown ", args.bench, " --bench mcd or zygos")
            
