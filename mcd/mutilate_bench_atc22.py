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
ITR = 333
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
DVFS = '0x1d00'
ITRC = []
TYPE = 'etc'
TIME = 120
SEARCH = 0
VERBOSE = 0
TARGET_QPS=100000
NREPEAT = 0
SLEEP = "c7"
SEND='single'

WORKLOADS = {
    #ETC = 75% GET, 25% SET
    'etc': '--keysize=fb_key --valuesize=fb_value --iadist=fb_ia --update=0.25',

    #USR = 99% GET, 1% SET
    'usr': '--keysize=19 --valuesize=2 --update=0.01',

    'etc2': '--keysize=fb_key --valuesize=fb_value --iadist=fb_ia --update=0.033',

    'large': '--keysize=normal:400,2 -V --valuesize=normal:8000,2 --update=0.25'
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

def runLocalCommandGet(com, sin):
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE, stdin=PIPE)
    sout = p1.communicate(input=sin.encode())[0]
    return sout.decode()

sleep_dict = {
    "c1"  : "0",      # 0x00
    "c1e" : "1",      # 0x01
    "c3"  : "16",     # 0x10
#    "c6"  : "32",     # 0x20
    "c7"  : "48"      # 0x30
}
def setSLEEP(v):
    global SLEEP
    SLEEP = v
    runLocalCommandGet("socat - TCP4:192.168.1.9:5002", "sleep_state,"+sleep_dict[SLEEP])
    
def setITR(v, s):    
    global ITR

    if s == "linux":
        p1 = Popen(["ssh", CSERVER2, "/app/ethtool-4.5/ethtool -C eth0 rx-usecs", v], stdout=PIPE, stderr=PIPE)
        p1.communicate()    
        time.sleep(0.5)
    else:
        runLocalCommandGet("socat - TCP4:192.168.1.9:5002", "rx_usecs,"+v)
    
    ITR = int(v)

def setRAPL(v, s):
    global RAPL

    if s == "linux":
        p1 = Popen(["ssh", CSERVER2, "/app/uarch-configure/rapl-read/rapl-power-mod", v], stdout=PIPE, stderr=PIPE)
        p1.communicate()
        time.sleep(0.5)
    else:
        runLocalCommandGet("socat - TCP4:192.168.1.9:5002", "rapl,"+v)
        
    RAPL = int(v)

def setDVFS(v, s):
    global DVFS

    if s == "linux":
        p1 = Popen(["ssh", CSERVER2, "wrmsr -a 0x199", v], stdout=PIPE, stderr=PIPE)
        p1.communicate()
        time.sleep(0.5)
    else:
        runLocalCommandGet("socat - TCP4:192.168.1.9:5002", "dvfs,"+str(int(v, 0)))

    DVFS = v

def setSend(s):
    global SEND

    ssend = 0
    if s == 'SINGLE':
        ssend = 1
    elif s == 'MULTIPLE':
        ssend = 2
    else:
        print('Unknown SEND type = ', s)
        return
    
    runLocalCommandGet("socat - TCP4:192.168.1.9:5002", "ixgbe_switch_send,"+str(ssend))
    SEND = s
    
def runBenchATC(mqps):
    runRemoteCommandGet("pkill mutilate", "192.168.1.106")
    runRemoteCommandGet("pkill mutilate", "192.168.1.107")
    
    runRemoteCommandGet("pkill mutilate", "192.168.1.38")
    runRemoteCommandGet("pkill mutilate", "192.168.1.37")
    runRemoteCommandGet("pkill mutilate", "192.168.1.11")
    time.sleep(1)
    print("pkill mutilate done")
    
    runRemoteCommands("/app/mutilate/mutilate --agentmode --threads=16", "192.168.1.37")
    runRemoteCommands("/app/mutilate/mutilate --agentmode --threads=16", "192.168.1.38")
    runRemoteCommands("/app/mutilate/mutilate --agentmode --threads=16", "192.168.1.106")
    runRemoteCommands("/app/mutilate/mutilate --agentmode --threads=16", "192.168.1.107")
    
    time.sleep(5)    
    print("mutilate agentmode done")

    localout = runLocalCommandGet("socat - TCP4:192.168.1.9:5002", "start,0")    
    output = runRemoteCommandGet("taskset -c 0 /app/mutilate/mutilate --binary -s 192.168.1.9 --noload --agent=192.168.1.106,192.168.1.107,192.168.1.37,192.168.1.38 --threads=1 "+WORKLOADS[TYPE]+" --depth=4 --measure_depth=1 --connections=16 --measure_connections=32 --measure_qps=2000 --qps="+str(mqps)+" --time="+str(TIME), "192.168.1.11")
    
    #--keysize=fb_key --valuesize=fb_value
    #normal:400,2 -V normal:8000,2
    #output = runRemoteCommandGet('taskset -c 0 /app/mutilate/mutilate --binary -s 192.168.1.9 --noload --agent=192.168.1.106,192.168.1.107,192.168.1.37,192.168.1.38 --threads=1 --keysize=normal:400,2 -V --valuesize=normal:8000,2 --update=0.25 --depth=4 --measure_depth=1 --connections=16 --measure_connections=32 --measure_qps=2000 --qps='+str(mqps)+' --time='+str(TIME), '192.168.1.11')
    
    localout = runLocalCommandGet("socat - TCP4:192.168.1.9:5002", "stop,0")
    read_5th = ''
    read_10th = ''
    read_50th = ''
    read_90th = ''
    read_95th = ''
    read_99th = ''
    f = open("ebbrt_out."+str(NREPEAT)+"_"+str(int(ITR)*2)+"_"+DVFS+"_"+str(RAPL)+"_"+str(TARGET_QPS)+"_"+str(SLEEP)+"_"+TYPE, "w")
    for line in str(output).strip().split("\\n"):
        if "read" in line:
            alla = list(filter(None, line.strip().split(' ')))
            read_5th = alla[4]
            read_10th = alla[5]
            read_50th = alla[6]
            read_90th = alla[7]
            read_95th = alla[8]
            read_99th = alla[9]
        f.write(line.strip()+"\n")
    f.close()

    countersout = runLocalCommandGet("socat - TCP4:192.168.1.9:5002", "getcounters,0")
    f = open("ebbrt_counters."+str(NREPEAT)+"_"+str(int(ITR)*2)+"_"+DVFS+"_"+str(RAPL)+"_"+str(TARGET_QPS)+"_"+str(SLEEP)+"_"+TYPE, "w")
    f.write(str(countersout))
    f.close()
            
    x1 = np.zeros(72)
    tjoules=0.0
    trdtsc=0.0
    for line in str(countersout).strip().split("\n"):
        alla = list(filter(None, line.strip().split(' ')))
        core = int(alla[0])
        if core < 2:
            ## sum up joules for package 0 & 1
            tjoules += float(alla[10])
            trdtsc += float(alla[11])
        xalla = [float(x) for x in alla]
        x1 = np.add(x1, xalla)
    ## average time
    trdtsc = trdtsc / 2.0

    ## 16 cores
    x1[0] = 16
    x1[10] = tjoules
    x1[11] = trdtsc    
    f = open("ebbrt_mcd_stats."+str(NREPEAT)+"_"+str(int(ITR)*2)+"_"+DVFS+"_"+str(RAPL)+"_"+str(TARGET_QPS)+"_"+str(SLEEP)+"_"+TYPE, "w")
    salla = [str(x) for x in x1]
    f.write('ncores rx_desc rsc_desc rx_bytes tx_desc tx_bytes instructions cycles ref_cycles llc_miss joules time')
    for i in np.arange(40):
        f.write(' tx_desc_'+str(i))
    f.write(' read_5th read_10th read_50th read_90th read_95th read_99th\n')
    f.write((' '.join(salla[:52]))+' '+read_5th+' '+read_10th+' '+read_50th+' '+read_90th+' '+read_95th+' '+read_99th)
    f.close()
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--os", help="linux or ebbrt")
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
    parser.add_argument("--send", help="Send using SINGLE TX descriptor or MULTIPLE [SINGLE, MULTIPLE]")
    parser.add_argument("--pow_search_enable", help="Limit printf for search power limit")
    parser.add_argument("--verbose", help="Print mcd raw stats")
    parser.add_argument("--sleep_state", help="sleep states: c1, c1e, c3, c6, c7")
    
    args = parser.parse_args()
    rb = 1
    if args.rapl:
        #print("RAPL = ", args.rapl)
        setRAPL(args.rapl, args.os)
    if args.itr:
        #print("ITR = ", args.itr)
        setITR(args.itr, args.os)
    if args.qps:
        TARGET_QPS = args.qps
        #print("TARGET_QPS = ", TARGET_QPS)
    if args.dvfs:
        setDVFS(args.dvfs, args.os)
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
    if args.sleep_state:
        setSLEEP(args.sleep_state)
    if args.send:
        setSend(args.send)
        
    if rb:
        if args.bench == "mcd":
            if args.os == "ebbrt":
                runBenchATC(TARGET_QPS)
        elif args.bench == "test":
            test()
        else:
            print("unknown ", args.bench, " --bench mcd or zygos")
            
