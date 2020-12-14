import re
import os
from os import path
import sys
import time
import numpy as np
import pandas as pd

#print(len(sys.argv), sys.argv)
if len(sys.argv) != 2:
    print("clean_netpipe_linux.py <path>")
    exit()
loc = sys.argv[1]


dvfs = ["0xc00",
        "0xd00",
        "0xe00",
        "0xf00",
        "0x1000",
        "0x1100",
        "0x1200",
        "0x1300",
        "0x1400",
        "0x1500",
        "0x1600",
        "0x1700",
        "0x1800",
        "0x1900",
        "0x1a00",
        "0x1b00",
        "0x1c00",
        "0x1d00",
        "0xffff"]
    
itrs = ["0", "1", "2", "4", "6", "8", "10", "12", "14", "16", "18", "20", "22", "24", "26", "28", "30", "32", "34", "36", "38", "40"]
rapls = ["135", "95", "75", "55"]
msgs = ["64", "8192", "65536", "524288"]

#msgs = ["64"]
#dvfs=["0xffff"]
#itrs=["2", "4", "6"]
#rapls=["135"]
#msgs=["8192"]

iters = 10

COLS = ['i', 'rx_desc', 'rx_bytes', 'tx_desc', 'tx_bytes', 'instructions', 'cycles', 'ref_cycles', 'llc_miss', 'c1', 'c1e', 'c3', 'c6', 'c7', 'joules', 'timestamp']

TIME_CONVERSION_khz = 1./(2899999*1000)
JOULE_CONVERSION = 0.00001526

START_RDTSC = 0
END_RDTSC = 0
tdiff = 0
tput = 0
tins = 0
tcyc = 0
trefcyc = 0
tllcm = 0
tc3 = 0
tc6 = 0
tc7 = 0
tjoules = 0.0

def checkExist(fnclient, fnserver, fnlog):
    if not path.exists(fnclient):
        return False
    if not path.exists(fnlog):
        return False
    if not path.exists(fnserver):
        return False    
    return True

def parseRdtsc(fnserver):
    global START_RDTSC
    global END_RDTSC
    global tdiff
    START_RDTSC = 0
    END_RDTSC = 0    
    f = open(fnserver, 'r')    
    for line in f:
        if 'WORKLOAD' in line.strip():
            tmp = list(filter(None, line.strip().split(' ')))
            START_RDTSC = int(tmp[1])
            END_RDTSC = int(tmp[2])
            break
    f.close()
    tdiff = round(float((END_RDTSC - START_RDTSC) * TIME_CONVERSION_khz), 1)
    
def parseTput(fnclient):
    global tput
    tput = 0.0
    lat = 0.0
    f = open(fnclient, 'r')
    for line in f:
        tmp = list(filter(None, line.strip().split(' ')))
        tput = float(tmp[1])
        break
    f.close()
    
print("sys i msg itr dvfs rapl time tput joules rx_bytes tx_bytes instructions cycles ref_cycles llc_miss c1 c1e c3 c6 c7 num_interrupts")
for d in dvfs:
    for itr in itrs:
        for rapl in rapls:
            for msg in msgs:
                for i in range(0, iters):
                    #linux.np.client.0_1_524288_5000_1_0xffff_135
                    fnlog = f'{loc}/linux.np.log.{i}_1_{msg}_5000_{itr}_{d}_{rapl}'
                    fnserver = f'{loc}/linux.np.server.{i}_1_{msg}_5000_{itr}_{d}_{rapl}'
                    fnclient = f'{loc}/linux.np.client.{i}_1_{msg}_5000_{itr}_{d}_{rapl}'

                    if checkExist(fnclient, fnserver, fnlog) == True:
                        parseTput(fnclient)
                        parseRdtsc(fnserver)
                        
                        df = pd.read_csv(fnlog, sep=' ', names=COLS)
                        df = df[df['timestamp'] >= START_RDTSC]
                        df = df[df['timestamp'] <= END_RDTSC]

                        df['timestamp'] = df['timestamp'] - df['timestamp'].min()
                        df['timestamp'] = df['timestamp'] * TIME_CONVERSION_khz
                        df['timestamp_diff'] = df['timestamp'].diff()
                        df.dropna(inplace=True)

                        df_non0j = df[(df['joules']>0) & (df['instructions'] > 0) & (df['cycles'] > 0) & (df['ref_cycles'] > 0) & (df['llc_miss'] > 0)].copy()                        
                        df_non0j['joules'] = df_non0j['joules'] * JOULE_CONVERSION
                        df_non0j['joules'] = df_non0j['joules'] - df_non0j['joules'].min()
                        
                        tmp = df_non0j[['instructions', 'cycles', 'ref_cycles', 'llc_miss', 'joules', 'c1', 'c1e', 'c3', 'c6', 'c7']].diff()
                        tmp.columns = [f'{c}_diff' for c in tmp.columns]
                        df_non0j = pd.concat([df_non0j, tmp], axis=1)
                        df_non0j.dropna(inplace=True)
                        df.dropna(inplace=True)
                        df_non0j = df_non0j[df_non0j['joules_diff'] > 0]

                        ttime = df['timestamp_diff'].sum()
                        tt = ttime / 5000 / 2
                        tput = (int(msg) * 8) / (tt * 1024 * 1024)

                        pname=''
                        if d == '0xffff':
                            pname='linux_default'
                        else:
                            pname='linux_tuned'
                        #print(f"{pname} {i} {msg} {itr} {d} {rapl} {round(ttime, 3)} {round(tput, 2)} {round(df_non0j['joules_diff'].sum(), 2)} {int(df['rx_bytes'].sum())} {int(df['tx_bytes'].sum())} {int(df_non0j['instructions_diff'].sum())} {int(df_non0j['cycles_diff'].sum())} {int(df_non0j['ref_cycles_diff'].sum())} {int(df_non0j['llc_miss_diff'].sum())} {int(df_non0j['c1_diff'].sum())} {int(df_non0j['c1e_diff'].sum())} {int(df_non0j['c3_diff'].sum())} {int(df_non0j['c6_diff'].sum())} {int(df_non0j['c7_diff'].sum())} {df.shape[0]}")
                        print(f"{pname} {i} {msg} {itr} {d} {rapl} {round(ttime, 3)} {round(tput, 2)} {round(df_non0j['joules_diff'].sum(), 2)} {int(df['rx_bytes'].sum())} {int(df_non0j['instructions_diff'].sum())} {int(df_non0j['llc_miss_diff'].sum())} {df.shape[0]}")
                    
