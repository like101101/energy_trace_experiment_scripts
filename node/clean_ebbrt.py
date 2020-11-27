import re
import os
from os import path
import sys
import pandas as pd

'''
dvfs = ["0xd00",
        "0xf00",
        "0x1100",
        "0x1300",
        "0x1500",
        "0x1700",
        "0x1900",
        "0x1b00",
        "0x1d00"]

itrs = ["2", "4", "6", "8", "12", "16", "20", "24", "28", "32", "36", "40", "80"]
rapls = ["135", "55"]
iters = 3
'''

dvfs = ["0x1d00"]

itrs = ["2"]
rapls = ["135"]
iters = 3

TIME_CONVERSION_khz = 1./(2899999*1000)
JOULE_CONVERSION = 0.00001526
COLS = ['i', 'rx_desc', 'rx_bytes', 'tx_desc', 'tx_bytes', 'instructions', 'cycles', 'ref_cycles', 'llc_miss', 'c3', 'c6', 'c7', 'joules', 'timestamp']

#print("sys i itr dvfs rapl lat50 lat75 lat90 lat99 requests time joule instructions cycles ref_cycles llc_miss c1 c1e c3 c6 c7 num_interrupts")

for rapl in rapls:
    for itr in itrs:
        for d in reversed(dvfs):
            for i in range(0, iters):
                fname = 'ebbrt_dmesg.'+str(i)+'_1_'+itr+'_'+d+'_'+rapl+'.csv'
                if not path.exists(fname):
                    print(fname, "doesn't exist?")
                else:                    
                    fout = open('ebbrt_out.'+str(i)+'_1_'+itr+'_'+d+'_'+rapl, 'r')
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
                    
                    frtdsc = open('ebbrt_rdtsc.'+str(i)+'_'+itr+'_'+d+'_'+rapl, 'r')
                    START_RDTSC = 0
                    END_RDTSC = 0
                    for line in frtdsc:
                        tmp = line.strip().split(' ')
                        START_RDTSC = int(tmp[0])
                        END_RDTSC = int(tmp[1])
                        tdiff = round(float((END_RDTSC - START_RDTSC) * TIME_CONVERSION_khz), 2)
                        if tdiff > 3 and tdiff < 40:
                            break
                    frtdsc.close()                                                            
            
                    if START_RDTSC == 0 or END_RDTSC == 0 or tdiff < 3:
                        print(f"BUG: {fname} rtdsc == 0")
                        break
                    else:
                        df = pd.read_csv(fname, sep=' ', names=COLS, skiprows=1)
                        df = df[df['timestamp'] >= START_RDTSC]
                        df = df[df['timestamp'] <= END_RDTSC]
                        
                        df_non0j = df[(df['joules']>0) & (df['instructions'] > 0) & (df['cycles'] > 0) & (df['ref_cycles'] > 0) & (df['llc_miss'] > 0)].copy()
                        df_non0j['timestamp'] = df_non0j['timestamp'] - df_non0j['timestamp'].min()
                        df_non0j['timestamp'] = df_non0j['timestamp'] * TIME_CONVERSION_khz
                        df_non0j['joules'] = df_non0j['joules'] * JOULE_CONVERSION
                        
                        tmp = df_non0j[['instructions', 'cycles', 'ref_cycles', 'llc_miss', 'joules']].diff()
                        tmp.columns = [f'{c}_diff' for c in tmp.columns]
                        df_non0j = pd.concat([df_non0j, tmp], axis=1)
                        df_non0j.dropna(inplace=True)
                        df.dropna(inplace=True)
                        df_non0j = df_non0j[df_non0j['joules_diff'] > 0]
                        
                        print(f"ebbrt_tuned {i} {itr} {d} {rapl} {lat_us_50} {lat_us_75} {lat_us_90} {lat_us_99} {total_requests} {tdiff} {round(df_non0j['joules_diff'].sum(), 2)} {int(df['rx_desc'].sum())} {int(df['rx_bytes'].sum())} {int(df['tx_desc'].sum())} {int(df['tx_bytes'].sum())} {int(df_non0j['instructions_diff'].sum())} {int(df_non0j['cycles_diff'].sum())} {int(df_non0j['ref_cycles_diff'].sum())} {int(df_non0j['llc_miss_diff'].sum())} {0} {0} {0} {0} {int(df_non0j['c7'].sum())} {df.shape[0]}")
