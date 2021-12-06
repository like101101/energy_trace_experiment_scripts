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
    
def start_counter():
    s = 3
    for i in range(0, 16):
        ITRC.append(int(runRemoteCommandGet(CSERVER2, "cat /proc/interrupts | grep -m 1 enp4s0f1-TxRx-"+str(i)+" | tr -s ' ' | cut -d ' ' -f "+str(s))))
        s += 1
    #print(ITRC)
        
def end_counter(qps, read_avg, read_std, read_min, read_5th, read_50th, read_90th, read_95th, read_99th):
    s = 3
    for i in range(0, 16):
        t = int(runRemoteCommandGet(CSERVER2, "cat /proc/interrupts | grep -m 1 enp4s0f1-TxRx-"+str(i)+" | tr -s ' ' | cut -d ' ' -f "+str(s)))
        ITRC[i] = t - ITRC[i]
        s += 1
        
    output = runRemoteCommandGet(MASTER, "cat perf.out")
    cycles = 0
    instructions = 0
    llc_load = 0
    llc_store = 0
    energy_pkg = 0.0
    energy_ram = 0.0
    ttime = 0.0
    watts = 0.0
    ipc = 0.0
    avg_itr = np.average(ITRC)
    tlist = []

    c1_usage = 0
    c1E_usage = 0
    c3_usage = 0
    c6_usage = 0
    c7_usage = 0
    
    pc1_usage = 0
    pc1E_usage = 0
    pc3_usage = 0
    pc6_usage = 0
    pc7_usage = 0
    
    count = 0    
    for l in str(output).split("\\n"):
        #print(l.strip())
        f = list(filter(None, l.strip().split(' ')))            
        if 'cycles' in l:
            tlist.append(float(f[0].replace(',', '')))
            cycles += int(f[1].replace(',', ''))
        if 'instructions' in l:
            tlist.append(float(f[0].replace(',', '')))
            instructions += int(f[1].replace(',', ''))
        if 'load-misses' in l:
            tlist.append(float(f[0].replace(',', '')))
            llc_load += int(f[1].replace(',', ''))
        if 'store-misses' in l:
            tlist.append(float(f[0].replace(',', '')))
            llc_store += int(f[1].replace(',', ''))
        if 'energy-pkg' in l:
            tlist.append(float(f[0].replace(',', '')))
            energy_pkg += float(f[1].replace(',', ''))
        if 'energy-ram' in l:
            tlist.append(float(f[0].replace(',', '')))
            energy_ram += float(f[1].replace(',', ''))
            #print(tlist)
        if 'C1_usage' in l:
            if count == 1:
                c1_usage += (float(f[1]) - pc1_usage)
            pc1_usage = float(f[1])
        if 'C1E_usage' in l:
            if count == 1:
                c1E_usage += (float(f[1]) - pc1E_usage)
            pc1E_usage = float(f[1])            
        if 'C3_usage' in l:
            if count == 1:
                c3_usage += (float(f[1]) - pc3_usage)
            pc3_usage = float(f[1])            
        if 'C6_usage' in l:
            if count == 1:
                c6_usage += (float(f[1]) - pc6_usage)
            pc6_usage = float(f[1])            
        if 'C7_usage' in l:
            if count == 1:
                c7_usage += (float(f[1]) - pc7_usage)
            pc7_usage = float(f[1])
            if count == 0:
                count = 1
    
    ttime = tlist[len(tlist)-1] - tlist[0]
    #watts = (energy_pkg+energy_ram)/ttime
    watts = energy_pkg/ttime
    ipc = instructions/float(cycles)
 
    print("ITR=%d RAPL=%d QPS=%.2f READ_99TH=%.2f WATTS=%.2f TARGET_QPS=%d QPS/WATT=%.2f C1_usage=%.2f C1E_usage=%.2f C3_usage=%.2f C6_usage=%.2f C7_usage=%.2f LLC_MISSES=%d IPC=%.5f AVG_ITR_PER_CORE=%.2f TIME=%.2f CYCLES=%d INSTRUCTIONS=%d LLC_LOAD_MISSES=%d LLC_STORE_MISSES=%d NRG_PKG=%.2f NRG_RAM=%.2f READ_5TH=%.2f READ_50TH=%.2f READ_90TH=%.2f READ_95TH=%.2f ITR0=%d ITR1=%d ITR2=%d ITR3=%d ITR4=%d ITR5=%d ITR6=%d ITR7=%d ITR8=%d ITR9=%d ITR10=%d ITR11=%d ITR12=%d ITR13=%d ITR14=%d ITR15=%d RXRING=%d TXRING=%d DTXMXSZRQ=%d WTHRESH=%d PTHRESH=%d HTHRESH=%d DCA=%d" % (ITR, RAPL, qps, read_99th, watts, TARGET_QPS, qps/watts, c1_usage, c1E_usage, c3_usage, c6_usage, c7_usage, llc_load+llc_store, ipc, avg_itr, ttime, cycles, instructions, llc_load, llc_store, energy_pkg, energy_ram, read_5th, read_50th, read_90th, read_95th, ITRC[0], ITRC[1], ITRC[2], ITRC[3], ITRC[4], ITRC[5], ITRC[6], ITRC[7], ITRC[8], ITRC[9], ITRC[10], ITRC[11], ITRC[12], ITRC[13], ITRC[14], ITRC[15], RXRING, TXRING, DTXMXSZRQ, WTHRESH, PTHRESH, HTHRESH, DCA))

def updateRING(v):
    global RXRING
    global TXRING
    
    if v == 0:
        RXRING = 512
        TXRING = 512
    else:
        RXRING = 4092
        TXRING = 4092
    #print(RXRING, TXRING)
    # RXRING
    p1 = Popen(["ssh", CSERVER2, "ethtool -G enp4s0f1 rx", str(RXRING)], stdout=PIPE, stderr=PIPE)
    p1.communicate()

    # TXRING
    p1 = Popen(["ssh", CSERVER2, "ethtool -G enp4s0f1 tx", str(TXRING)], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    
def updateTHRESH(v):
    global WTHRESH
    global HTHRESH
    global PTHRESH
    if v == 0:
        PTHRESH = 12
        HTHRESH = 4
        WTHRESH = 4
    elif v == 1:
        PTHRESH = 0
        HTHRESH = 16
        WTHRESH = 16
    elif v == 2:
        PTHRESH = 12
        HTHRESH = 0
        WTHRESH = 0
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 WTHRESH", str(WTHRESH)], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 PTHRESH", str(PTHRESH)], stdout=PIPE, stderr=PIPE)
    p1.communicate()

    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 HTHRESH", str(HTHRESH)], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    
def updateDTXMX(v):
    global DTXMXSZRQ
    if v == 0:
        DTXMXSZRQ = 16
    elif v == 1:
        DTXMXSZRQ = 2046
    elif v == 2:
        DTXMXSZRQ = 4095
    # DTXMXSZRQ 
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 DTXMXSZRQ", str(DTXMXSZRQ)], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    
def updateDCA(v):
    global DCA
    if v == 0:
        DCA = 1
    else:
        DCA = 4
    # DCA
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 DCA", str(DCA)], stdout=PIPE, stderr=PIPE)
    p1.communicate()


def rebootNIC():
    p1 = Popen(["ssh", CSERVER2, "ifdown enp4s0f1"], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    time.sleep(1)
    
    p1 = Popen(["ssh", CSERVER2, "ifup enp4s0f1"], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    time.sleep(5)

    for i in range(5):
        p1 = Popen(["ping", "-c 3", CSERVER], stdout=PIPE)
        output = p1.communicate()[0]
        if "3 received" in str(output):
            return 1
        time.sleep(1)
    print("enp40sf1 did not restart correctly")
    return 0
        
def updateNIC():
    global ITR
    global WTHRESH
    global HTHRESH
    global PTHRESH
    global DTXMXSZRQ
    global DCA
    global RSC_DELAY
    global MAX_DESC
    global BSIZEPKT
    global BSIZEHDR
    global RXRING
    global TXRING
    global THRESHC
    
    ### fix syntax highlighting in emacs???
    bs = 0
    
    '''
    Receive Side Scaling (RSC)
    '''
    # RSC Delay: The delay = (RSC Delay + 1) x 4 us = 4, 8, 12... 32 us.
    # 3 bits, so [0 - 7]
    # select 4: 4, 8, 16, 32 | 1, 2, 4, 8
    RSC_DELAY = np.random.randint(1, 5)
    if RSC_DELAY == 3:
        RSC_DELAY=4
    elif RSC_DELAY == 4:
        RSC_DELAY = 8
    
    '''
    MAXDESC * SRRCTL.BSIZEPKT must not exceed 64 KB minus one, which is the
    maximum total length in the IP header and must be larger than the expected
    received MSS.

    Maximum descriptors per Large receive as follow:
    00b = Maximum of 1 descriptor per large receive.
    01b = Maximum of 4 descriptors per large receive.
    10b = Maximum of 8 descriptors per large receive.
    11b = Maximum of 16 descriptors per large receive
    '''
    # select 3: 1, 2, 3
    MAX_DESC = np.random.randint(1, 4)

    '''
    SRRCTL.BSIZEPKT
    Receive Buffer Size for Packet Buffer.
    The value is in 1 KB resolution. Value can be from 1 KB to 16 KB. Default buffer size is
    2 KB. This field should not be set to 0x0. This field should be greater or equal to 0x2
    in queues where RSC is enabled.

    *** Linux default is at 3072
    
    MAXDESC * SRRCTL.BSIZEPKT must not exceed 64 KB minus one

    if MAX_DESC == 1:
        BSIZEPKT = 12 * 1024 #np.random.randint(3, 16) * 1024
    elif MAX_DESC == 2:
        BSIZEPKT = 6 * 1024#np.random.randint(3, 8) * 1024
    else:
        BSIZEPKT = 3 * 1024 #np.random.randint(3, 4) * 1024
    '''
    BSIZEPKT = 3 * 1024
    
    '''
    BSIZEHEADER

    Receive Buffer Size for Header Buffer.
    The value is in 64 bytes resolution. Value can be from 64 bytes to 1024 bytes

    *** Linux default is set at 0x4 * 64 Bytes = 256 Bytes
    '''
    # select 3: [4, 8, 12] * 64 Bytes
    BSIZEHDR = np.random.randint(1, 4) * 4 * 64

    '''
    ITR Interval
    '''
    # ITR: (RSC_DELAY+2) us to 200 us in increments of 10
    #ITR = np.random.randint((((RSC_DELAY+1) * 4)/2)+1, 101) * 2
    itr_delay_us = RSC_DELAY*4
    itr_start = (itr_delay_us/10) + 1
    #print("itr_start", itr_start)
    ITR = np.random.randint(itr_start, 16) * 10
    
    '''
    RDLEN
    '''
    c = np.random.randint(0, 2)
    if c == 0:
        RXRING = 512
        TXRING = 512
    else:
        RXRING = 4092
        TXRING = 4092

    '''
    TDLEN
    '''
    #c = np.random.randint(0, 2)
    #if c == 0:
    #    TXRING = 512
    #else:
    #    TXRING = 4092
    
    '''
    ** Linux: PTHRESH=32 HTHRESH=1 WTHRESH=1
    Notes about THRESH, PTHRESH, WTHRESH

    Transmit descriptor fetch setting is programmed in the TXDCTL[n] register per
    In order to reduce transmission latency, it is recommended to set the PTHRESH value
    as high as possible while the HTHRESH and WTHRESH as low as possible (down to
    zero).

    In order to minimize PCIe overhead the PTHRESH should be set as low as possible
    while HTHRESH and WTHRESH should be set as high as possible.

    The sum of PTHRESH plus WTHRESH must not be greater than the onchip descriptor
    buffer size (40)

    When the WTHRESH equals zero, descriptors are written back for those
    descriptors with the RS bit set. When the WTHRESH value is greater than
    zero, descriptors are accumulated until the number of accumulated descriptors equals
    the WTHRESH value, then these descriptors are written back. Accumulated
    descriptor write back enables better use of the PCIe bus and memory bandwidth.

    PTHRESH: Pre Fetch Threshold The on chip descriptor buffer becomes almost empty while there are enough
    descriptors in the host memory.
         - The on-chip descriptor buffer is defined as almost empty if it contains less descriptors
           then the threshold defined by PTHRESH
         - The transmit descriptor contains enough descriptors if it includes more ready
           descriptors than the threshold defined by TXDCTL[n].HTHRESH

    Controls when a prefetch of descriptors is considered. This threshold refers to the
    number of valid, unprocessed transmit descriptors the 82599 has in its on-chip buffer. If
    this number drops below PTHRESH, the algorithm considers pre-fetching descriptors from
    host memory. However, this fetch does not happen unless there are at least HTHRESH
    valid descriptors in host memory to fetch. HTHRESH should be given a non-zero value each time PTHRESH is used.
    '''

    # [2, 40) in increments of 2
    # WTHRESH: Should not be higher than 1 when ITR == 0, else device basically crashes
    '''
    WTHRESH = np.random.randint(1, 20)
    
    #PTHRESH: WTHRESH + PTHRESH < 40
    PTHRESH = np.random.randint(1, (20 - WTHRESH)+1)
    
    # HTHRESH
    HTHRESH = np.random.randint(1, 20)

    WTHRESH *= 2
    PTHRESH *= 2
    HTHRESH *= 2
    '''
    '''
    In order to reduce transmission latency, it is recommended to set the PTHRESH value
    as high as possible while the HTHRESH and WTHRESH as low as possible (down to
    zero).

    In order to minimize PCIe overhead the PTHRESH should be set as low as possible
    while HTHRESH and WTHRESH should be set as high as possible.

    The sum of PTHRESH plus WTHRESH must not be greater than the on chip descriptor
    buffer size (40)
    '''
    THRESHC = np.random.randint(0, 3)

    if THRESHC == 0:
        '''
        CPU cache line optimization Assume  N equals the CPU cache line divided by 16 descriptor size.
        Then in order to align descriptors prefetch to CPU cache line in most cases it is advised to
        set PTHRESH to the onchip descriptor buffer size minus N and HTHRESH to N. In order to align 
        descriptor write back to the CPU cache line it is advised to set WTHRESH to either N or even 2 times N.
        Note that partial cache line writes might significantly degrade performance. Therefore, it is highly recommended to follow this advice.
        
        getconf LEVEL1_DCACHE_LINESIZE == CPU cache line size 64
        on chip descriptor size == 16
        
        N = 64 / 16 = 4
        PTHRESH = 16 4 == 12
        HTHRESH == 4
        WTHRESH == 4 or 8
        '''

        PTHRESH = 12
        HTHRESH = 4
        WTHRESH = 4
    elif THRESHC == 1:
        '''
        Minimizing PCIe overhead: As an example, setting PTHRESH to the on-chip descriptor buffer size minus 16 and HTHRESH to 16 
        minimizes the PCIe request and header overhead to 20% of the bandwidth required for the descriptor fetch.
        '''
        PTHRESH = 0
        HTHRESH = 16
        WTHRESH = 16
    elif THRESHC == 2:
        '''
        Minimizing transmission latency from tail update: Setting PTHRESH to the on chip 
        descriptor buffer size minus N, previously defined, while HTHRESH and WTHRESH to zero.
        '''
        PTHRESH = 12
        HTHRESH = 0
        WTHRESH = 0
    
    '''
    DTXMXSZRQ
    The maximum allowed amount of 256 bytes outstanding requests. If the total
    size request is higher than the amount in the field no arbitration is done and no
    new packet is requested
    
    min: 0x10 * 256 = 4 KB
    max: 0xFFF * 256 = 1 MB
    '''
    c = np.random.randint(0, 3)
    if c == 0:
        # default
        DTXMXSZRQ = 16
    elif c == 1:
        DTXMXSZRQ = 2046
    elif c == 2:
        # 0xFFF
        DTXMXSZRQ = 4095

    '''
    DCA == 1, RX_DCA = OFF, TX_DCA = OFF
    DCA == 2, RX_DCA = ON, TX_DCA = OFF
    DCA == 3, RX_DCA = OFF, TX_DCA = ON
    DCA == 4, RX_DCA = ON, TX_DCA = ON
    '''
    dcac = np.random.randint(0, 2)
    if dcac == 0:
        DCA = 1
    else:
        DCA = 4

    #print("RSC_DELAY=%d MAX_DESC=%d BSIZEPKT=%d BSIZEHDR=%d RXRING=%d TXRING=%d ITR=%d DTXMXSZRQ=%d WTHRESH=%d PTHRESH=%d HTHRESH=%d DCA=%d\n" % (RSC_DELAY, MAX_DESC, BSIZEPKT, BSIZEHDR, RXRING, TXRING, ITR, DTXMXSZRQ, WTHRESH, PTHRESH, HTHRESH, DCA))
    #return

    # RSC_DELAY
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 RSCDELAY", str(RSC_DELAY)], stdout=PIPE, stderr=PIPE)
    p1.communicate()

    # MAXDESC
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 MAXDESC", str(MAX_DESC)], stdout=PIPE, stderr=PIPE)
    p1.communicate()

    # BSIZEPKT
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 BSIZEPACKET", str(BSIZEPKT)], stdout=PIPE, stderr=PIPE)
    p1.communicate()

    # BSIZEHDR
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 BSIZEHEADER", str(BSIZEHDR)], stdout=PIPE, stderr=PIPE)
    p1.communicate()

    # RXRING
    p1 = Popen(["ssh", CSERVER2, "ethtool -G enp4s0f1 rx", str(RXRING)], stdout=PIPE, stderr=PIPE)
    p1.communicate()

    # TXRING
    p1 = Popen(["ssh", CSERVER2, "ethtool -G enp4s0f1 tx", str(TXRING)], stdout=PIPE, stderr=PIPE)
    p1.communicate()

    # ITR
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 rx-usecs", str(ITR)], stdout=PIPE, stderr=PIPE)
    p1.communicate()
        
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 WTHRESH", str(WTHRESH)], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 PTHRESH", str(PTHRESH)], stdout=PIPE, stderr=PIPE)
    p1.communicate()

    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 HTHRESH", str(HTHRESH)], stdout=PIPE, stderr=PIPE)
    p1.communicate()

    # DTXMXSZRQ 
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 DTXMXSZRQ", str(DTXMXSZRQ)], stdout=PIPE, stderr=PIPE)
    p1.communicate()

    # DCA
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 DCA", str(DCA)], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    
    p1 = Popen(["ssh", CSERVER2, "ifdown enp4s0f1"], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    time.sleep(1)
    
    p1 = Popen(["ssh", CSERVER2, "ifup enp4s0f1"], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    time.sleep(1)

    #print("RSC_DELAY=%d MAX_DESC=%d BSIZEPKT=%d BSIZEHDR=%d RXRING=%d TXRING=%d ITR=%d DTXMXSZRQ=%d WTHRESH=%d PTHRESH=%d HTHRESH=%d DCA=%d" % (RSC_DELAY, MAX_DESC, BSIZEPKT, BSIZEHDR, RXRING, TXRING, ITR, DTXMXSZRQ, WTHRESH, PTHRESH, HTHRESH, DCA), end='')
    
    for i in range(5):
        p1 = Popen(["ping", "-c 3", CSERVER], stdout=PIPE)
        output = p1.communicate()[0]
        if "3 received" in str(output):
            #print("3 received")
            return 1
        time.sleep(1)

    #print("ifdown enp4s0f1 && ifup enp4s0f1")
    #p1 = Popen(["ssh", CSERVER2, "ifdown enp4s0f1 && ifup enp4s0f1"], stdout=PIPE, stderr=PIPE)
    #time.sleep(2)
    print("enp40sf1 did not restart correctly")
    return 0

def runScan(com):
    try:
        p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
        output = p1.communicate()[0].strip()
        if len(output) > 10:
            for line in str(output).strip().split("\\n"):
                print(line.strip())
    except Exception as e:
        print("An error occurred in runScan", type(e), e)

def runMutilateStatsAll(com):
    try:
        #print(com)
        ret = -1.0
        p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
        output = p1.communicate()[0].strip()
        read_avg = 0
        read_std = 0
        read_min = 0
        read_5th = 0
        read_10th = 0
        read_50th = 0
        read_90th = 0
        read_95th = 0
        read_99th = 0
        if len(output) > 10:
            for line in str(output).strip().split("\\n"):
                if VERBOSE == 1:
                    print(line.strip())
                if "Total QPS" in line:
                    tmp = str(line.split("=")[1])
                    qps = float(tmp.strip().split(" ")[0])
                    ret = qps
                if "read" in line:
                    all = list(filter(None, line.strip().split(' ')))
                    read_avg = float(all[1])
                    read_std = float(all[2])
                    read_min = float(all[3])
                    read_5th = float(all[4])
                    read_10th = float(all[5])
                    read_50th = float(all[6])
                    read_90th = float(all[7])
                    read_95th = float(all[8])
                    read_99th = float(all[9])
                    
        return ret, read_avg, read_std, read_min, read_5th, read_50th, read_90th, read_95th, read_99th
    except Exception as e:
        print("An error occurred in runMutilateStatsAll ", type(e), e)
        return -1.0, 0, 0, 0, 0, 0, 0, 0, 0

def ebbrtAlive():
    output = runRemoteCommandGet("ping -c 3 192.168.1.9", "192.168.1.11")
    if "3 received" in str(output):
        return True
    else:
        return False

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
    
def runBenchEbbRT(mqps):
    #if not ebbrtAlive():
    #    print("ebbrtAlive == False, exiting ...")
    #    return

    runRemoteCommandGet("pkill mutilate", "192.168.1.104")
    runRemoteCommandGet("pkill mutilate", "192.168.1.106")
    runRemoteCommandGet("pkill mutilate", "192.168.1.107")
    
    runRemoteCommandGet("pkill mutilate", "192.168.1.38")
    runRemoteCommandGet("pkill mutilate", "192.168.1.37")
    runRemoteCommandGet("pkill mutilate", "192.168.1.11")
    time.sleep(1)
    print("pkill mutilate done")
    
    runRemoteCommands("/app/mutilate/mutilate --agentmode --threads=16", "192.168.1.37")
    runRemoteCommands("/app/mutilate/mutilate --agentmode --threads=16", "192.168.1.38")
    runRemoteCommands("/app/mutilate/mutilate --agentmode --threads=16", "192.168.1.104")
    runRemoteCommands("/app/mutilate/mutilate --agentmode --threads=16", "192.168.1.106")
    runRemoteCommands("/app/mutilate/mutilate --agentmode --threads=16", "192.168.1.107")
    
    time.sleep(5)    
    print("mutilate agentmode done")
    
    #for i in range(0, 4):
    #    runRemoteCommandGet("taskset -c 0 /app/mutilate/mutilate --binary -s 192.168.1.9 --loadonly -K fb_key -V fb_value", "192.168.1.11")
    #    time.sleep(1)
    #print("preload done")

    localout = runLocalCommandGet("socat - TCP4:192.168.1.9:5002", "clear,0")
    localout = runLocalCommandGet("socat - TCP4:192.168.1.9:5002", "start,0")
    
    output = runRemoteCommandGet("taskset -c 0 /app/mutilate/mutilate --binary -s 192.168.1.9 --noload --agent=192.168.1.104,192.168.1.106,192.168.1.107,192.168.1.37,192.168.1.38 --threads=1 "+WORKLOADS[TYPE]+" --depth=4 --measure_depth=1 --connections=16 --measure_connections=32 --measure_qps=2000 --qps="+str(mqps)+" --time="+str(TIME), "192.168.1.11")
    localout = runLocalCommandGet("socat - TCP4:192.168.1.9:5002", "stop,0")

    ## normalize settings for retrieving logs
    localout = runLocalCommandGet("socat - TCP4:192.168.1.9:5002", "rx_usecs,10")
    localout = runLocalCommandGet("socat - TCP4:192.168.1.9:5002", "dvfs,"+str(int('0x1d00', 0)))
    localout = runLocalCommandGet("socat - TCP4:192.168.1.9:5002", "rapl,135")
        
    f = open("ebbrt_out."+str(NREPEAT)+"_"+str(int(ITR)*2)+"_"+DVFS+"_"+str(RAPL)+"_"+str(TARGET_QPS)+"_"+str(SLEEP), "w")
    for line in str(output).strip().split("\\n"):
        f.write(line.strip()+"\n")
    f.close()
    
    #ocalout = runLocalCommandGet("socat - TCP4:192.168.1.9:5002", "rdtsc,0")
    # = open("ebbrt_rdtsc."+str(NREPEAT)+"_"+str(ITR)+"_"+DVFS+"_"+str(RAPL)+"_"+str(TARGET_QPS), "w")
    #or line in str(localout).strip().split("\\n"):
    #   f.write(line.strip()+"\n")
    #.close()

    
    #rint(localout)
    
    
def cleanLogs():
    for i in range(1, 17):                    
        runRemoteCommandGet("/app/ethtool-4.5/ethtool -C eth0 DUMP_DYNAMIC_ITR "+str(i), "192.168.1.9")
        runRemoteCommandGet("dmesg -C", "192.168.1.9")
        if VERBOSE:
            print("cleanLogs", i)
        
def printLogs():
    for i in range(1, 17):
        runRemoteCommandGet("/app/ethtool-4.5/ethtool -C eth0 DUMP_DYNAMIC_ITR "+str(i), "192.168.1.9")
        runRemoteCommandGet("dmesg -c &> /app/mcd_dmesg."+str(i-1), "192.168.1.9")
        if VERBOSE:
            print("printLogs", i)

def getLogs():
    for i in range(1, 17):
        runLocalCommandOut("scp -r 192.168.1.9:/app/mcd_dmesg."+str(i-1)+" mcd_dmesg."+str(NREPEAT)+"_"+str(i-1)+"_"+str(ITR)+"_"+str(DVFS)+"_"+str(RAPL)+"_"+str(TARGET_QPS))
        runLocalCommandOut("gzip -f9 mcd_dmesg."+str(NREPEAT)+"_"+str(i-1)+"_"+str(ITR)+"_"+str(DVFS)+"_"+str(RAPL)+"_"+str(TARGET_QPS))
        if VERBOSE:
            print("getLogs", i)
    runLocalCommandOut("scp -r 192.168.1.9:/tmp/mcd.rdtsc mcd_rdtsc."+str(NREPEAT)+"_"+str(i-1)+"_"+str(ITR)+"_"+str(DVFS)+"_"+str(RAPL)+"_"+str(TARGET_QPS))
    
def runBenchASPLOS(mqps):
    runRemoteCommandGet("pkill mutilate", "192.168.1.138")
    runRemoteCommandGet("pkill mutilate", "192.168.1.131")
    runRemoteCommandGet("pkill mutilate", "192.168.1.14")
    runRemoteCommandGet("pkill mutilate", "192.168.1.38")
    runRemoteCommandGet("pkill mutilate", "192.168.1.37")
    runRemoteCommandGet("pkill mutilate", "192.168.1.11")
    time.sleep(1)
    
    runRemoteCommands("/app/mutilate/mutilate --agentmode --threads=16", "192.168.1.14")
    runRemoteCommands("/app/mutilate/mutilate --agentmode --threads=16", "192.168.1.37")
    runRemoteCommands("/app/mutilate/mutilate --agentmode --threads=16", "192.168.1.38")
    runRemoteCommands("/app/mutilate/mutilate --agentmode --threads=16", "192.168.1.138")
    runRemoteCommands("/app/mutilate/mutilate --agentmode --threads=12", "192.168.1.131")
    time.sleep(5)

    is_running_mcd = runRemoteCommandGet("pgrep memcached", "192.168.1.9")
    if is_running_mcd:
        print("already running mcd")
    else:
        runRemoteCommands("taskset -c 0-15 /app/memcached/memcached -u nobody -t 16 -m 16G -c 8192 -b 8192 -l 192.168.1.9 -B binary", "192.168.1.9")
        time.sleep(1)
        runRemoteCommandGet("taskset -c 0 /app/mutilate/mutilate --binary -s 192.168.1.9 --loadonly -K fb_key -V fb_value", "192.168.1.11")    
    cleanLogs()
    time.sleep(1)
    
    output = runRemoteCommandGet("taskset -c 0 /app/mutilate/mutilate --binary -s 192.168.1.9 --noload --agent=192.168.1.138,192.168.1.131,192.168.1.14,192.168.1.38,192.168.1.37 --threads=1 "+WORKLOADS[TYPE]+" --depth=4 --measure_depth=1 --connections=16 --measure_connections=32 --measure_qps=2000 --qps="+str(mqps)+" --time="+str(TIME), "192.168.1.11")
    runRemoteCommands("killall -USR2 memcached", "192.168.1.9")
    
    if VERBOSE:
        print("Finished executing memcached")
        
    f = open("mcd_out."+str(NREPEAT)+"_"+str(ITR)+"_"+str(DVFS)+"_"+str(RAPL)+"_"+str(TARGET_QPS), "w")
    for line in str(output).strip().split("\\n"):
        f.write(line.strip()+"\n")
    f.close()
    
    printLogs()
    getLogs()
    
def runBenchQPS(mqps):
    start_counter()

    time.sleep(1)    
    runRemoteCommands("/root/tmp/zygos_mutilate/mutilate --agentmode --threads=16", "192.168.1.201")
    time.sleep(1)
    runRemoteCommands("/root/tmp/zygos_mutilate/mutilate --agentmode --threads=16", "192.168.1.202")
    time.sleep(1)
    runRemoteCommands("/root/tmp/zygos_mutilate/mutilate --agentmode --threads=16", "192.168.1.203")
    time.sleep(1)
    runRemoteCommands("/root/tmp/zygos_mutilate/mutilate --agentmode --threads=12", "192.168.1.204")
    time.sleep(1)
    runRemoteCommands("/root/tmp/zygos_mutilate/mutilate --agentmode --threads=12", "192.168.1.205")
    time.sleep(1)
 
    #https://elixir.bootlin.com/linux/v4.15/source/arch/x86/events/intel/cstate.c
    runRemoteCommand("perf stat -a -D 4000 -I 1000 -o perf.out -e cycles,instructions,LLC-load-misses,LLC-store-misses,power/energy-pkg/,power/energy-ram/,cstate_core/c3-residency/,cstate_core/c6-residency/,cstate_core/c7-residency/,cstate_pkg/c2-residency/,cstate_pkg/c3-residency/,cstate_pkg/c6-residency/,cstate_pkg/c7-residency/ memcached -u nobody -t 16 -m 16G -c 8192 -b 8192 -l "+MASTER+" -B binary")    
    time.sleep(1)

    runLocalCommandOut("taskset -c 1 /root/tmp/zygos_mutilate/mutilate --binary -s "+MASTER+" --loadonly -K fb_key -V fb_value")    
    time.sleep(1)
    
    qps, read_avg, read_std, read_min, read_5th, read_50th, read_90th, read_95th, read_99th = runMutilateStatsAll("taskset -c 0 /root/tmp/zygos_mutilate/mutilate --binary -s "+MASTER+" --noload --agent=192.168.1.201,192.168.1.202,192.168.1.203,192.168.1.204,192.168.1.205 --threads=1 "+WORKLOADS[TYPE]+" --depth=4 --measure_depth=1 --connections=16 --measure_connections=32 --measure_qps=2000 --qps="+str(mqps)+" --time="+str(TIME))
    
    runRemoteCommandOut("pkill memcached")
    
    if qps > 0.0:
        if SEARCH:
            end_counter(qps, read_avg, read_std, read_min, read_5th, read_50th, read_90th, read_95th, read_99th)
            print(read_99th)
        else:
            end_counter(qps, read_avg, read_std, read_min, read_5th, read_50th, read_90th, read_95th, read_99th)

def runBenchLocalQPS(mqps):
    start_counter()

    time.sleep(1)
    #runLocalCommand("taskset -c 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15 /root/tmp/zygos_mutilate/mutilate --agentmode --threads=15")
    #runLocalCommand("taskset -c 1 /root/tmp/zygos_mutilate/mutilate --agentmode --threads=1")       
    time.sleep(1)
    
    runRemoteCommand("perf stat -a -D 4000 -I 1000 -o perf.out -e cycles,instructions,LLC-load-misses,LLC-store-misses,power/energy-pkg/,power/energy-ram/ memcached -u nobody -t 16 -m 16G -c 8192 -b 8192 -l "+MASTER+" -B binary")
    time.sleep(1)

    runLocalCommandOut("taskset -c 0 /root/tmp/zygos_mutilate/mutilate --binary -s "+MASTER+" --loadonly -K fb_key -V fb_value")
    time.sleep(1)
    
    qps, read_avg, read_std, read_min, read_5th, read_50th, read_90th, read_95th, read_99th = runMutilateStatsAll("taskset -c 0 /root/tmp/zygos_mutilate/mutilate --binary -s "+MASTER+" --agent=localhost --noload --threads=1 "+WORKLOADS[TYPE]+" --depth=1 --measure_depth=1 --connections=16 --measure_connections=32 --measure_qps=2000 --qps="+str(mqps)+" --time="+str(TIME))
    
    runRemoteCommandOut("pkill memcached")
    
    if qps > 0.0:
        if SEARCH:
            end_counter(qps, read_avg, read_std, read_min, read_5th, read_50th, read_90th, read_95th, read_99th)
            print(read_99th)
        else:
            end_counter(qps, read_avg, read_std, read_min, read_5th, read_50th, read_90th, read_95th, read_99th)

            
#####################################################################################################
#
#
# ZYGOS
#
#
####################################################################################################
def runZygos(mqps):
    start_counter()
    #runLocalCommand("taskset -c 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15 /root/tmp/mutilate/mutilate --agentmode --affinity --threads 15")
    time.sleep(1)
    runRemoteCommands("/root/tmp/zygos_mutilate/mutilate --agentmode --threads=16", "192.168.1.201")
    time.sleep(1)
    runRemoteCommands("/root/tmp/zygos_mutilate/mutilate --agentmode --threads=16", "192.168.1.202")
    time.sleep(1)
    runRemoteCommands("/root/tmp/zygos_mutilate/mutilate --agentmode --threads=16", "192.168.1.203")
    time.sleep(1)
    runRemoteCommands("/root/tmp/zygos_mutilate/mutilate --agentmode --threads=12", "192.168.1.204")
    time.sleep(1)
    runRemoteCommands("/root/tmp/zygos_mutilate/mutilate --agentmode --threads=12", "192.168.1.205")
    time.sleep(1)
    
    runRemoteCommand("perf stat -a -D 30000 -I 1000 -o perf.out -e cycles,instructions,LLC-load-misses,LLC-store-misses,power/energy-pkg/,power/energy-ram/ /root/servers/silotpcc-linux")
    time.sleep(29)
    qps, read_avg, read_std, read_min, read_5th, read_50th, read_90th, read_95th, read_99th = runMutilateStatsAll("taskset -c 0 /root/tmp/zygos_mutilate/mutilate --binary -s "+MASTER+" --noload --agent=192.168.1.201,192.168.1.202,192.168.1.203,192.168.1.204,192.168.1.205 --threads=1 --records=1000000 "+WORKLOADS['etc2']+" --depth=4 --measure_depth=1 --connections=16 --measure_connections=16 --measure_qps=2000 --qps="+str(mqps)+" --time="+str(TIME))

    runRemoteCommandOut("pkill silotpcc-linux")
    if qps > 0.0:
        if SEARCH:
            print(read_99th)
        else:
            end_counter(qps, read_avg, read_std, read_min, read_5th, read_50th, read_90th, read_95th, read_99th)

def test():
    output = runRemoteCommandGet(MASTER, "cat perf.out")

    poll_usage = 0
    c1_usage = 0
    c1E_usage = 0
    c3_usage = 0
    c6_usage = 0
    c7_usage = 0

    poll_time = 0
    c1_time = 0
    c1E_time = 0
    c3_time = 0
    c6_time = 0
    c7_time = 0
    
    ppoll_usage = 0
    pc1_usage = 0
    pc1E_usage = 0
    pc3_usage = 0
    pc6_usage = 0
    pc7_usage = 0

    ppoll_time = 0
    pc1_time = 0
    pc1E_time = 0
    pc3_time = 0
    pc6_time = 0
    pc7_time = 0
    
    count = 0
    for l in str(output).split("\\n"):
        f = list(filter(None, l.strip().split(' ')))

        if 'POLL_usage' in l:
            if count == 1:
                poll_usage += (int(f[1]) - ppoll_usage)
            ppoll_usage = int(f[1])
            
        if 'C1_usage' in l:
            if count == 1:
                c1_usage += (int(f[1]) - pc1_usage)
            pc1_usage = int(f[1])
    
        if 'C1E_usage' in l:
            if count == 1:
                c1E_usage += (int(f[1]) - pc1E_usage)
            pc1E_usage = int(f[1])
            
        if 'C3_usage' in l:
            if count == 1:
                c3_usage += (int(f[1]) - pc3_usage)
            pc3_usage = int(f[1])
            
        if 'C6_usage' in l:
            if count == 1:
                c6_usage += (int(f[1]) - pc6_usage)
            pc6_usage = int(f[1])

        if 'POLL_time' in l:
            if count == 1:
                poll_time += (int(f[1]) - ppoll_time)
            ppoll_time = int(f[1])
            
        if 'C1_time' in l:
            if count == 1:
                c1_time += (int(f[1]) - pc1_time)
            pc1_time = int(f[1])
    
        if 'C1E_time' in l:
            if count == 1:
                c1E_time += (int(f[1]) - pc1E_time)
            pc1E_time = int(f[1])
            
        if 'C3_time' in l:
            if count == 1:
                c3_time += (int(f[1]) - pc3_time)
            pc3_time = int(f[1])
            
        if 'C6_time' in l:
            if count == 1:
                c6_time += (int(f[1]) - pc6_time)
            pc6_time = int(f[1])

        if 'C7_time' in l:
            if count == 1:
                c7_time += (int(f[1]) - pc7_time)
            pc7_time = int(f[1])
            
        if 'C7_usage' in l:
            if count == 1:
                c7_usage += (int(f[1]) - pc7_usage)
            pc7_usage = int(f[1])
            if count == 0:
                count = 1

    print("POLL usage", poll_usage)
    print("C1 usage", c1_usage)
    print("C1E usage", c1E_usage)
    print("C3 usage", c3_usage)
    print("C6 usage", c6_usage)
    print("C7 usage", c7_usage)

    print("")
    
    print("POLL time", poll_time)
    print("C1 time", c1_time)
    print("C1E time", c1E_time)
    print("C3 time", c3_time)
    print("C6 time", c6_time)
    print("C7 time", c7_time)
    print("total", poll_time+c1_time+c1E_time+c3_time+c6_time+c7_time)

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
        
    #if args.ring >= 0:
    #    updateRING(args.ring)
    #if args.thresh >= 0:
    #    updateTHRESH(args.thresh)
    #if args.dca >= 0:
    #    updateDCA(args.dca)
    #if args.dtxmx >= 0:
    #    updateDTXMX(args.dtxmx)
    #if args.restartnic >= 0:
    #    rb = rebootNIC()

    if rb:
        if args.bench == "mcd":
            if args.os == "ebbrt":
                #runBenchEbbRT(TARGET_QPS)
                runBenchATC(TARGET_QPS)
        elif args.bench == "test":
            test()
        else:
            print("unknown ", args.bench, " --bench mcd or zygos")
            
