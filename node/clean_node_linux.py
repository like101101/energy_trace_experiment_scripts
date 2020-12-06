
import re
import os
from os import path
import sys
import pandas as pd

print(len(sys.argv), sys.argv)
if len(sys.argv) != 2:
    print("clean_linux.py <path>")
    exit()
loc = sys.argv[1]

'''
dvfs = ["0xd00",
        "0xf00",
        "0x1100",
        "0x1300",
        "0x1500",
        "0x1700",
        "0x1900",
        "0x1b00",
        "0x1d00",
        "0xffff"]
'''
#itrs = ["1", "2", "4", "6", "8", "12", "16", "20", "24", "28", "32", "36", "40", "50", "60", "70", "80"]

dvfs=["0xffff"]
itrs=["1"]
rapls = ["135", "95", "75", "55"]
iters = 10

#dvfs = ["0x1d00"]
#itrs = ["2"]
#rapls = ["135"]
#iters = 3

TIME_CONVERSION_khz = 1./(2899999*1000)
JOULE_CONVERSION = 0.00001526
COLS = ['i', 'rx_desc', 'rx_bytes', 'tx_desc', 'tx_bytes', 'instructions', 'cycles', 'ref_cycles', 'llc_miss', 'c1', 'c1e', 'c3', 'c6', 'c7', 'joules', 'timestamp']

print("sys i itr dvfs rapl lat50 lat75 lat90 lat99 requests time joule rx_desc rx_bytes tx_desc tx_bytes instructions cycles ref_cycles llc_miss c1 c1e c3 c6 c7 num_interrupts")

for rapl in rapls:
    for itr in itrs:
        for d in reversed(dvfs):
            for i in range(0, iters):
                fname = f'{loc}/linux.node.server.log.'+str(i)+'_1_'+itr+'_'+d+'_'+rapl
                if path.exists(fname):                    
                    fout = open(f'{loc}/linux.node.server.out.'+str(i)+'_1_'+itr+'_'+d+'_'+rapl, 'r')
                    lat_us_50 = 0
                    lat_us_75 = 0
                    lat_us_90 = 0
                    lat_us_99 = 0
                    total_requests= 0
                    for line in fout:
                        if "50%" in line:
                            tmp = list(filter(None, line.strip().split(' ')))
                            lat_us_50 = float(tmp[1][0:len(tmp[1])-2])
                        if "75%" in line:
                            tmp = list(filter(None, line.strip().split(' ')))
                            lat_us_75 = float(tmp[1][0:len(tmp[1])-2])
                        if "90%" in line:
                            tmp = list(filter(None, line.strip().split(' ')))
                            lat_us_90 = float(tmp[1][0:len(tmp[1])-2])
                        if "99%" in line:
                            tmp = list(filter(None, line.strip().split(' ')))
                            lat_us_99 = float(tmp[1][0:len(tmp[1])-2])
                        if "requests in" in line:
                            tmp = list(filter(None, line.strip().split(' ')))
                            total_requests = int(tmp[0])                        
                    fout.close()
                    
                    frtdsc = open(f'{loc}/linux.node.server.rdtsc.'+str(i)+'_1_'+itr+'_'+d+'_'+rapl, 'r')
                    START_RDTSC = 0
                    END_RDTSC = 0
                    for line in frtdsc:
                        tmp = line.strip().split(' ')
                        START_RDTSC = int(tmp[1])
                        END_RDTSC = int(tmp[2])
                        tdiff = round(float((END_RDTSC - START_RDTSC) * TIME_CONVERSION_khz), 2)
                        if tdiff > 3 and tdiff < 40:
                            break
                    frtdsc.close()                                                            
            
                    if START_RDTSC == 0 or END_RDTSC == 0:
                        print(f"{fname} rtdsc == 0 tdiff={tdiff}")
                    else:                        
                        df = pd.read_csv(fname, sep=' ', names=COLS)
                        df = df[df['timestamp'] >= START_RDTSC]
                        df = df[df['timestamp'] <= END_RDTSC]
                        
                        df['timestamp'] = df['timestamp'] - df['timestamp'].min()
                        df['timestamp'] = df['timestamp'] * TIME_CONVERSION_khz
                        
                        df['timestamp_diff'] = df['timestamp'].diff()
                        df['instructions_diff'] = df['instructions'].diff()
                        df['cycles_diff'] = df['cycles'].diff()
                        df['ref_cycles_diff'] = df['ref_cycles'].diff()
                        df['llc_miss_diff'] = df['llc_miss'].diff()
                        df.dropna(inplace=True)

                        df_non0j = df[(df['joules']>0) & (df['instructions'] > 0) & (df['cycles'] > 0) & (df['ref_cycles'] > 0) & (df['llc_miss'] > 0)].copy()
                        df_non0j['joules'] = df_non0j['joules'] * JOULE_CONVERSION
                        tmp = df_non0j[['joules', 'c1', 'c1e', 'c3', 'c6', 'c7']].diff()
                        tmp.columns = [f'{c}_diff' for c in tmp.columns]
                        df_non0j = pd.concat([df_non0j, tmp], axis=1)
                        df_non0j.dropna(inplace=True)
                        df_non0j = df_non0j[df_non0j['joules_diff'] > 0]

                        pname=""
                        if itr == "1" and d == "0xffff":
                            pname="linux_default"
                        else:
                            pname="linux_tuned"
                            
                        print(f"{pname} {i} {itr} {d} {rapl} {lat_us_50} {lat_us_75} {lat_us_90} {lat_us_99} {total_requests} {round(df['timestamp_diff'].sum(), 3)} {round(df_non0j['joules_diff'].sum(), 2)} {int(df['rx_desc'].sum())} {int(df['rx_bytes'].sum())} {int(df['tx_desc'].sum())} {int(df['tx_bytes'].sum())} {int(df['instructions_diff'].sum())} {int(df['cycles_diff'].sum())} {int(df['ref_cycles_diff'].sum())} {int(df['llc_miss_diff'].sum())} {int(df_non0j['c1_diff'].sum())} {int(df_non0j['c1e_diff'].sum())} {int(df_non0j['c3_diff'].sum())} {int(df_non0j['c6_diff'].sum())} {int(df_non0j['c7_diff'].sum())} {df.shape[0]}")                        
