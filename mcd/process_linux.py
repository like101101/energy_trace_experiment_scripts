import re
import os
from os import path
import sys
import time
import numpy as np
import pandas as pd

print(len(sys.argv), sys.argv)
if len(sys.argv) != 2:
    print("process_linux.py <path>")
    exit()
loc = sys.argv[1]

dvfs = ["0xd00",
        "0xf00",
        "0x1100",
        "0x1200",
        "0x1300",
        "0x1400",
        "0x1500",
        "0x1700",
        "0x1800",
        "0x1900",
        "0x1a00",
        "0x1b00",
        "0x1c00",
        "0x1d00"]

itrs = ["2", "10", "20", "30", "40", "50", "100", "200", "300", "350", "400"]
rapls = ["135"]
qpss = ["200000"]

iters = 10
possible_qps_vals = np.array([200000])
LINUX_COLS = ['i', 'rx_desc', 'rx_bytes', 'tx_desc', 'tx_bytes', 'instructions', 'cycles', 'ref_cycles', 'llc_miss', 'c1', 'c1e', 'c3', 'c6', 'c7', 'joules', 'timestamp']

TIME_CONVERSION_khz = 1./(2899999*1000)
JOULE_CONVERSION = 0.00001526

read_5th = 0
read_10th = 0
read_50th = 0
read_90th = 0
read_95th = 0
read_99th = 0
START_RDTSC = 0
END_RDTSC = 0
tdiff = 0
mqps = 0
cqps = 0
tins = 0
tcyc = 0
trefcyc = 0
tllcm = 0
tc3 = 0
tc6 = 0
tc7 = 0
tc1 = 0
tc1e = 0
trx_desc = 0
trx_bytes = 0
ttx_desc = 0
ttx_bytes = 0
tjoules = 0.0
tnum_interrupts = 0

'''
Parses output file to read tail latency, QPS values
'''
def parseOut(i, itr, d, rapl, q):
    global read_5th
    global read_10th
    global read_50th
    global read_90th
    global read_95th
    global read_99th
    global mqps
    global cqps
    
    f = f'{loc}/linux.mcd.out.'+str(i)+'_'+itr+'_'+d+'_'+rapl+'_'+q
    fout = open(f, 'r')
    for line in fout:
        if "Total QPS" in line:
            tmp = str(line.split("=")[1])
            mqps = float(tmp.strip().split(" ")[0])
            cqps = possible_qps_vals[np.argmin(np.abs((int(mqps) - possible_qps_vals)))]
        if "read" in line:
            alla = list(filter(None, line.strip().split(' ')))
            read_5th = float(alla[4])
            read_10th = float(alla[5])
            read_50th = float(alla[6])
            read_90th = float(alla[7])
            read_95th = float(alla[8])
            read_99th = float(alla[9])
                    
    fout.close()

'''
Parses rdtsc file to get START and END timestamps for each core.
For now, just pick the smallest RDTSC and largest RDTSC to get trim
and save the maximum number of log entries
'''
def parseRdtsc(i, itr, d, rapl, q):
    global START_RDTSC
    global END_RDTSC
    global tdiff

    f = f'{loc}/linux.mcd.rdtsc.'+str(i)+'_'+itr+'_'+d+'_'+rapl+'_'+q
    frtdsc = open(f, 'r')
    START_RDTSC = 0
    END_RDTSC = 0
    for line in frtdsc:
        tmp = line.strip().split(' ')

        ## get largest RDTSC
        if int(tmp[2]) > START_RDTSC:                                
            START_RDTSC = int(tmp[2])

        ## get smallest RDTSC
        if END_RDTSC == 0:                                
            END_RDTSC = int(tmp[3])
        elif END_RDTSC < int(tmp[3]):
            END_RDTSC = int(tmp[3])                                                            
    frtdsc.close()

    ## convert diff to seconds
    tdiff = round(float((END_RDTSC - START_RDTSC) * TIME_CONVERSION_khz), 2)

'''
Checks if all files needed exist, else it is a failed run and ignore data
'''
def exists(i, itr, d, rapl, q):
    outf = f'{loc}/linux.mcd.out.'+str(i)+'_'+itr+'_'+d+'_'+rapl+'_'+q
    if not path.exists(outf):
        #print(outf)
        return False
    
    rf = f'{loc}/linux.mcd.rdtsc.'+str(i)+'_'+itr+'_'+d+'_'+rapl+'_'+q
    if not path.exists(rf):
        #print(rf)
        return False

    for core in range(0, 16):
        fname = f'{loc}/linux.mcd.dmesg.'+str(i)+'_'+str(core)+'_'+itr+'_'+d+'_'+rapl+'_'+qps
        if not path.exists(fname):
            #print(fname)
            return False
    return True                    

'''
Main Loop: Iterates across DVFS, ITR, QPS, RAPL, and iterations and calculate overall results for each configuration
'''
print("sys i itr dvfs rapl read_5th read_10th read_50th read_90th read_95th read_99th measure_QPS target_QPS time joules rx_desc rx_bytes tx_desc tx_bytes instructions cycles ref_cycles llc_miss c1 c1e c3 c6 c7 num_interrupts")
for d in dvfs:
    for itr in itrs:
        for qps in qpss:
            for rapl in rapls:            
                for i in range(0, iters):
                    if exists(i, itr, d, rapl, qps) == True:
                        START_RDTSC = 0
                        END_RDTSC = 0
                        tdiff = 0
                        read_5th = 0
                        read_10th = 0
                        read_50th = 0
                        read_90th = 0
                        read_95th = 0
                        read_99th = 0
                        mqps = 0
                        cqps = 0
                        tins = 0
                        tcyc = 0
                        trefcyc = 0
                        tllcm = 0                    
                        tc3 = 0
                        tc6 = 0
                        tc7 = 0
                        tjoules = 0
                        tc1 = 0
                        tc1e = 0
                        num_interrupts = 0
                        trx_desc = 0
                        trx_bytes = 0
                        ttx_desc = 0
                        ttx_bytes = 0
                        tnum_interrupts = 0

                        ## parses Memcached output file to get measured tail latencies
                        parseOut(i, itr, d, rapl, qps)

                        ## parses rdtsc files to get start and end rdtsc timers
                        parseRdtsc(i, itr, d, rapl, qps)

                        ## for each core
                        for core in range(0, 16):
                            ## reads log file of each core
                            fname = f'{loc}/linux.mcd.dmesg.'+str(i)+'_'+str(core)+'_'+itr+'_'+d+'_'+rapl+'_'+qps
                            df = pd.read_csv(fname, sep=' ', names=LINUX_COLS)
                            df = df[df['timestamp'] >= START_RDTSC]
                            df = df[df['timestamp'] <= END_RDTSC]

                            df_non0j = df[(df['joules']>0) & (df['instructions'] > 0) & (df['cycles'] > 0) & (df['ref_cycles'] > 0) & (df['llc_miss'] > 0)].copy()
                            df_non0j['timestamp'] = df_non0j['timestamp'] - df_non0j['timestamp'].min()
                            df_non0j['timestamp'] = df_non0j['timestamp'] * TIME_CONVERSION_khz
                            df_non0j['joules'] = df_non0j['joules'] * JOULE_CONVERSION
                                         
                            tmp = df_non0j[['instructions', 'cycles', 'ref_cycles', 'llc_miss', 'joules', 'c1', 'c1e', 'c3', 'c6', 'c7']].diff()
                            tmp.columns = [f'{c}_diff' for c in tmp.columns]
                            df_non0j = pd.concat([df_non0j, tmp], axis=1)
                            df_non0j.dropna(inplace=True)
                            df.dropna(inplace=True)
                            df_non0j = df_non0j[df_non0j['joules_diff'] > 0]

                            cjoules = df_non0j['joules_diff'].sum()

                            ## energy values only on core 0 or 1 because energy is per CPU package
                            if core == 0 or core == 1:
                                tjoules += cjoules
                                
                            trx_desc += df['rx_desc'].sum()
                            trx_bytes += df['rx_bytes'].sum()
                            ttx_desc += df['tx_desc'].sum()
                            ttx_bytes += df['tx_bytes'].sum()
                                         
                            tins += df_non0j['instructions_diff'].sum()
                            tcyc += df_non0j['cycles_diff'].sum()
                            trefcyc += df_non0j['ref_cycles_diff'].sum()
                            tllcm += df_non0j['llc_miss_diff'].sum()
                            tc1 += df_non0j['c1_diff'].sum()
                            tc1e += df_non0j['c1e_diff'].sum()
                            tc3 += df_non0j['c3_diff'].sum()
                            tc6 += df_non0j['c6_diff'].sum()
                            tc7 += df_non0j['c7_diff'].sum()
                            tnum_interrupts += df.shape[0]

                            ## print per core statistics
                            print(f"linux_core_tuned {i} {core} {itr} {d} {rapl} {read_5th} {read_10th} {read_50th} {read_90th} {read_95th} {read_99th} {mqps} {cqps} {tdiff} {round(cjoules, 2)} {df['rx_desc'].sum()} {df['rx_bytes'].sum()} {df['tx_desc'].sum()} {df['tx_bytes'].sum()} {int(df_non0j['instructions_diff'].sum())} {int(df_non0j['cycles_diff'].sum())} {int(df_non0j['ref_cycles_diff'].sum())} {int(df_non0j['llc_miss_diff'].sum())} {int(df_non0j['c1_diff'].sum())} {int(df_non0j['c1e_diff'].sum())} {int(df_non0j['c3_diff'].sum())} {int(df_non0j['c6_diff'].sum())} {int(df_non0j['c7_diff'].sum())} {df.shape[0]}")

                        ## print overall statistics
                        print(f"linux_tuned {i} {itr} {d} {rapl} {read_5th} {read_10th} {read_50th} {read_90th} {read_95th} {read_99th} {mqps} {cqps} {tdiff} {round(tjoules, 2)} {trx_desc} {trx_bytes} {ttx_desc} {ttx_bytes} {tins} {tcyc} {trefcyc} {tllcm} {tc1} {tc1e} {tc3} {tc6} {tc7} {tnum_interrupts}")
                            
