import re
import os
from os import path
import sys
import time
import numpy as np
import pandas as pd

print(len(sys.argv), sys.argv)
if len(sys.argv) != 2:
    print("clean_mcd_ebbrt.py <path>")
    exit()
loc = sys.argv[1]

dvfs = ["0xc00",
        "0xd00",
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
        "0x1d00"]
    
itrs = ["2", "4", "6", "8", "10", "12", "14", "16", "18", "20", "22", "24", "26", "28", "30", "32", "34", "36", "38", "40"]
rapls = ["135", "95", "75", "55"]
msgs = ["64", "8192", "65536", "524288"]

iters = 10

EBBRT_COLS = ['i', 'rx_desc', 'rx_bytes', 'tx_desc', 'tx_bytes', 'instructions', 'cycles', 'ref_cycles', 'llc_miss', 'c3', 'c6', 'c7', 'joules', 'timestamp']

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

def checkExist(fname, fnpout):
    if not path.exists(fname):
        #print(fname, "doesn't exist?")
        return False
    if not path.exists(fnpout):
        #print(fnpout, "doesn't exist?")
        return False
    return True

def parseTput(fnpout):
    global tput
    global START_RDTSC
    global END_RDTSC
    global tdiff
    tput = 0.0
    lat = 0.0
    f = open(fnpout, 'r')
    for line in f:
        tmp = list(filter(None, line.strip().split(' ')))
        tput = float(tmp[8])
        START_RDTSC = int(tmp[10])
        END_RDTSC = int(tmp[11])
        break
    f.close()
    tdiff = round(float((END_RDTSC - START_RDTSC) * TIME_CONVERSION_khz), 1)
    
print("sys i itr dvfs rapl tput time joules rx_bytes tx_bytes instructions cycles ref_cycles llc_miss c1 c1e c3 c6 c7 num_interrupts")
for d in dvfs:
    for itr in itrs:
        for rapl in rapls:
            for msg in msgs:
                for i in range(0, iters):
                    fname = f'{loc}/ebbrt.dmesg.{i}_{msg}_5000_{itr}_{d}_{rapl}'
                    fnpout = f'{loc}/ebbrt.np.out.{i}_{msg}_5000_{itr}_{d}_{rapl}'
                    if checkExist(fname, fnpout) == True:
                        parseTput(fnpout)
                        
                        df = pd.read_csv(fname, sep=' ', names=EBBRT_COLS)
                        df = df[df['timestamp'] >= START_RDTSC]
                        df = df[df['timestamp'] <= END_RDTSC]

                        df['timestamp'] = df['timestamp'] - df['timestamp'].min()
                        df['timestamp'] = df['timestamp'] * TIME_CONVERSION_khz
                        df['timestamp_diff'] = df['timestamp'].diff()
                        df.dropna(inplace=True)

                        df_non0j = df[(df['joules']>0) & (df['instructions'] > 0) & (df['cycles'] > 0) & (df['ref_cycles'] > 0) & (df['llc_miss'] > 0)].copy()
                        df_non0j['joules'] = df_non0j['joules'] * JOULE_CONVERSION
                        df_non0j['joules'] = df_non0j['joules'] - df_non0j['joules'].min()
                        df_non0j['joules_diff'] = df_non0j['joules'].diff()
                        df_non0j['instructions_diff'] = df_non0j['instructions'].diff()
                        df_non0j['ref_cycles_diff'] = df_non0j['ref_cycles'].diff()
                        df_non0j['cycles_diff'] = df_non0j['cycles'].diff()
                        df_non0j['llc_miss_diff'] = df_non0j['llc_miss'].diff()                        
                        df_non0j = df_non0j[df_non0j['joules_diff'] > 0]
                        df_non0j.dropna(inplace=True)

                        ttime = df['timestamp_diff'].sum()
                        tt = ttime / 5000 / 2
                        tput = (int(msg) * 8) / (tt * 1024 * 1024)
                        pname='ebbrt_tuned'
                        print(f"{pname} {i} {msg} {itr} {d} {rapl} {round(ttime, 3)} {round(tput, 2)} {round(df_non0j['joules_diff'].sum(), 2)} {int(df['rx_bytes'].sum())} {int(df['tx_bytes'].sum())} {int(df_non0j['instructions_diff'].sum())} {int(df_non0j['cycles_diff'].sum())} {int(df_non0j['ref_cycles_diff'].sum())} {int(df_non0j['llc_miss_diff'].sum())} 0 0 0 0 {int(df_non0j['c7'].sum())} {df.shape[0]}")
                    
'''                        
#print("sys i itr dvfs rapl tput time joule ins cyc refcyc llcm c3 c6 c7 RDTSC_START RDTSC_END")    
for i in range(num, num+1):
    fname = 'ebbrt.dmesg.'+str(i)+'_'+msg+'_5000_'+itr+'_'+dvfs+'_135'
    fnpout = 'ebbrt.np.out.'+str(i)+'_'+msg+'_5000_'+itr+'_'+dvfs+'_135'
    #print(fname)

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
    
    checkExist(fname, fnpout)                
    parseTput(fnpout)
    parseLogs(fname)

    print("ebbrt "+str(i)+" "+str(itr)+" "+str(dvfs)+" "+str(rapl)+" "+str(round(tput,2))+" "+str(tdiff)+" "+str(round(tjoules,2))+" "+str(tins)+" "+str(tcyc)+" "+str(trefcyc)+" "+str(tllcm)+" "+str(tc3)+" "+str(tc6)+" "+str(tc7)+" "+str(START_RDTSC)+" "+str(END_RDTSC))
'''
    
'''
def parseLogs(fname):
    global START_RDTSC
    global END_RDTSC
    global tdiff
    global tput
    global tins
    global tcyc
    global trefcyc
    global tllcm
    global tc3
    global tc6
    global tc7
    global tjoules

    cc = 0
    total_ins = 0
    total_cyc = 0
    total_refcyc = 0
    total_llcm = 0
    prevj = 0
    sumj = 0
    
    ins = 0
    cyc = 0
    refcyc = 0
    llcm = 0
    
    total_c3 = 0
    total_c6 = 0
    total_c7 = 0
    
    c3 = 0
    c6 = 0
    c7 = 0

    f = open(fname)
    for line in f:
        tmp3 = list(filter(None, line.strip().split(' ')))
        if len(tmp3) == 14:
            if int(tmp3[13]) > START_RDTSC and int(tmp3[13]) < END_RDTSC and int(tmp3[5]) > 0 and int(tmp3[6]) > 0 and int(tmp3[7]) > 0 and int(tmp3[8]) > 0:
                joules = int(tmp3[12])
                if joules > 0:
                    if prevj == 0:
                        prevj = joules
                    elif prevj > 0 and joules < prevj:
                        prevj = joules
                    elif prevj > 0 and joules >= prevj:
                        sumj += joules - prevj
                        prevj = joules
                                        
                    if cc == 0 and joules > 0:
                        ins = int(tmp3[5])
                        cyc = int(tmp3[6])
                        refcyc = int(tmp3[7])
                        llcm = int(tmp3[8])
                        c3 = int(tmp3[9])
                        c6 = int(tmp3[10])
                        c7 = int(tmp3[11])
                        cc = 1
                                        
                    if ins > 0 and int(tmp3[5]) > ins:
                        total_ins = total_ins + (int(tmp3[5]) - ins)
                        ins = int(tmp3[5])
                    if cyc > 0 and int(tmp3[6]) > cyc:
                        total_cyc = total_cyc + (int(tmp3[6]) - cyc)
                        cyc = int(tmp3[6])
                    if refcyc > 0 and int(tmp3[7]) > refcyc:
                        total_refcyc = total_refcyc + (int(tmp3[7]) - refcyc)
                        refcyc = int(tmp3[7])    
                    if llcm > 0 and int(tmp3[8]) > llcm:
                        total_llcm = total_llcm + (int(tmp3[8]) - llcm)
                        llcm = int(tmp3[8])
                    if c3 > 0 and int(tmp3[9]) > c3:
                        total_c3 = total_c3 + (int(tmp3[9]) - c3)
                        c3 = int(tmp3[9])
                    if c6 > 0 and int(tmp3[10]) > c6:
                        total_c6 = total_c6 + (int(tmp3[10]) - c6)
                        c6 = int(tmp3[10])
                    if c7 > 0:
                        total_c7 = total_c7 + int(c7)
                        #total_c7 = total_c7 + (int(tmp3[11]) - c7)
                        #c7 = int(tmp3[11])

    f.close()
    tjoules += (JOULE_CONVERSION * sumj)        
    tins += total_ins
    tcyc += total_cyc
    trefcyc += total_refcyc
    tllcm += total_llcm
    tc3 += total_c3
    tc6 += total_c6
    tc7 += total_c7        
'''
