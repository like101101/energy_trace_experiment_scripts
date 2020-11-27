import re
import os
from os import path
import sys
import pandas as pd

print(len(sys.argv), sys.argv)
if len(sys.argv) != 2:
    print("clean_netpipe.py <path>")
    exit()
loc = sys.argv[1]

'''
dvfs = ["0xC00",
        "0xF00",
        "0x1000",
        "0x1100",
        "0x1200",
        "0x1500",
        "0x1600",
        "0x1700",
        "0x1800",
        "0x1900",
        "0x1A00",
        "0x1B00",
        "0x1C00",
        "0x1D00"]

itrs = ["2", "4", "6", "8", "12", "16", "20", "24", "28", "32", "36", "40", "50", "60", "70", "80"]
'''

dvfs=["0xFFFF"]
itrs=["1"]
rapls = ["135"]
msgs = ["524288", "64", "8192", "65536"]
iters = 20

'''
msgs=["524288"]
rapls=["135"]
iters=10
'''
TIME_CONVERSION_khz = 1./(2899999*1000)
JOULE_CONVERSION = 0.00001526
LINUX_COLS = ['i', 'rx_desc', 'rx_bytes', 'tx_desc', 'tx_bytes', 'instructions', 'cycles', 'llc_miss','joules', 'timestamp']
EBBRT_COLS = ['i', 'rx_desc', 'rx_bytes', 'tx_desc', 'tx_bytes', 'instructions', 'cycles', 'ref_cycles', 'llc_miss', 'c3', 'c6', 'c7', 'joules', 'timestamp']

print("sys i msg itr dvfs rapl time tput joule rx_bytes instructions llc_miss num_interrupts")

for msg in msgs:
    for rapl in rapls:
        for itr in itrs:
            for d in reversed(dvfs):
                for i in range(0, iters):
                    fname = f'{loc}/linux.dmesg.{i}_{msg}_5000_{itr}_{d}_{rapl}.csv'
                    #ebbrt.dmesg.0_524288_5000_12_0x1000_135.csv
                    #fname = f'{loc}/ebbrt.dmesg.{i}_{msg}_5000_{itr}_{d}_{rapl}.csv'
                    pname=""
                    if path.exists(fname):
                        df = pd.DataFrame()
                        if itr == "1" and d == "0xFFFF":
                            pname="linux_default"
                            df = pd.read_csv(fname, sep=' ', names=EBBRT_COLS)
                        else:
                            pname="ebbrt_tuned"
                            df = pd.read_csv(fname, sep=' ', names=LINUX_COLS)
                        
                        df['timestamp'] = df['timestamp'] - df['timestamp'].min()
                        df['timestamp'] = df['timestamp'] * TIME_CONVERSION_khz                        
                        df['timestamp_diff'] = df['timestamp'].diff()                        
                        df.dropna(inplace=True)

                        df_non0j = df[(df['joules']>0) & (df['instructions'] > 0) & (df['cycles'] > 0) & (df['llc_miss'] > 0)].copy()
                        df_non0j['joules'] = df_non0j['joules'] * JOULE_CONVERSION
                        df_non0j['joules_diff'] = df_non0j['joules'].diff()
                        df_non0j['instructions_diff'] = df_non0j['instructions'].diff()
                        df_non0j['llc_miss_diff'] = df_non0j['llc_miss'].diff()
                        df_non0j.dropna(inplace=True)
                        df_non0j = df_non0j[df_non0j['joules_diff'] > 0]                        

                        ttime = df['timestamp_diff'].sum()
                        tt = ttime / 5000 / 2                        
                        tput = (int(msg) * 8) / (tt * 1024 * 1024)
                        print(f"{pname} {i} {msg} {itr} {d} {rapl} {round(ttime, 3)} {round(tput, 2)} {round(df_non0j['joules_diff'].sum(), 2)} {int(df['rx_bytes'].sum())} {int(df_non0j['instructions_diff'].sum())} {int(df_non0j['llc_miss_diff'].sum())} {df.shape[0]}")
