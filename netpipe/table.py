import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import matplotlib
import os
import glob
import multiprocessing as mp

def printdf(d):
    for msg in [64/1000.0, 8192/1000.0, 65536/1000.0, 524288/1000.0]:
        e = d[d['msg']==msg]
        #b = e[e.edp_mean==e.edp_mean.min()].iloc[0]
        #print('Best EPP', msg, b['sys'])
        #print(f"{b['itr']},{b['dvfs']},{b['rapl']} {round(b['edp_mean'], 3)} {round(b['edp_std'], 3)} {round(b['joules_mean'], 3)} {round(b['time_mean'],3)}")
        #print('')
        b = e[e.edp_mean==e.edp_mean.max()].iloc[0]
        print('Worst EPP', msg, b['sys'])
        print(f"{b['itr']},{b['dvfs']},{b['rapl']} {round(b['edp_mean'], 3)} {round(b['edp_std'], 3)} {round(b['joules_mean'], 3)} {round(b['time_mean'],3)}")
        print('')

def printSorted(d, msg):
    #for msg in [64/1000.0, 8192/1000.0, 65536/1000.0, 524288/1000.0]:
    #for msg in [524288/1000.0]:
    e = d[d['msg']==msg]
    c = 0
    for index, b in e.iterrows():
        csum = int(b['c1_mean'])+int(b['c1e_mean'])+int(b['c3_mean'])+int(b['c6_mean'])+int(b['c7_mean'])
        cpi=round(int(b['ref_cycles_mean'])/int(b['instructions_mean']), 2)
        print(f"{c} {int(msg*1000.0)} {b['sys']} {b['itr']} {b['dvfs']} {b['rapl']} {round(b['edp_mean'], 2)} {round(b['edp_std'], 2)} {round(b['joules_mean'], 2)} {round(b['joules_std'], 2)} {round(b['time_mean'], 2)} {round(b['time_std'], 2)} {int(b['num_interrupts_mean'])} {int(b['num_interrupts_std'])} {cpi} {int(b['instructions_mean'])} {int(b['instructions_std'])} {int(b['ref_cycles_mean'])} {int(b['ref_cycles_std'])} {int(b['llc_miss_mean'])} {int(b['llc_miss_std'])} {int(b['c1_mean'])} {int(b['c1_std'])} {int(b['c1e_mean'])} {int(b['c1e_std'])} {int(b['c3_mean'])} {int(b['c3_std'])} {int(b['c6_mean'])} {int(b['c6_std'])} {int(b['c7_mean'])} {int(b['c7_std'])} {int(csum)} {int(b['rx_bytes_mean'])} {int(b['rx_bytes_std'])} {int(b['tx_bytes_mean'])} {int(b['tx_bytes_std'])}")
        #print(f"{c} {int(msg*1000.0)} {b['sys']} {b['itr']} {b['dvfs']} {b['rapl']} {round(b['edp_mean'], 2)} {round(b['edp_std'], 2)} {round(b['joules_mean'], 2)} {round(b['time_mean'], 2)} {int(b['num_interrupts_mean'])} {int(b['instructions_mean'])}")
        c += 1
        if c > 10:
            break
        
JOULE_CONVERSION = 0.00001526 #counter * constant -> JoulesOB
TIME_CONVERSION_khz = 1./(2899999*1000)

#workload_loc='/scratch2/netpipe/11_30_2020_rsc_enabled_test/netpipe_combined.csv'
#workload_loc='/scratch2/netpipe/netpipe_combined/netpipe_combined.csv'
workload_loc='/scratch2/netpipe/11_29_2020/netpipe_combined.csv'

#log_loc='/scratch2/netpipe/netpipe_combined/'

df = pd.read_csv(workload_loc, sep=' ')
df = df[df['joules'] > 0]
df['edp'] = df['joules'] * df['time']
df['tput'] = df['tput']/1000.0
df['msg'] = df['msg']/1000.0

NCOLS = ['sys', 'msg', 'itr', 'dvfs', 'rapl']
df_mean = df.groupby(NCOLS).mean()
df_std = df.groupby(NCOLS).std()

df_mean.columns = [f'{c}_mean' for c in df_mean.columns]
df_std.columns = [f'{c}_std' for c in df_std.columns]

df_comb = pd.concat([df_mean, df_std], axis=1)
df_comb.reset_index(inplace=True)


#for msg in [64/1000.0, 8192/1000.0, 65536/1000.0, 524288/1000.0]:
for msg in [65536/1000.0]:
    #d = df_comb[(df_comb['sys']=='linux_default') & (df_comb['itr']==1) & (df_comb['dvfs']=='0xffff')].copy()
    #printSorted(d.sort_values(by='edp_mean', ascending=True).copy(), msg)
    
    #d = df_comb[(df_comb['sys']=='linux_tuned') & (df_comb['itr']!=1) & (df_comb['dvfs']!='0xffff')].copy()
    #printSorted(d.sort_values(by='edp_mean', ascending=True).copy(), msg)

    d = df_comb[(df_comb['sys']=='ebbrt_tuned') & (df_comb['itr']!=1) & (df_comb['dvfs']!='0xffff')].copy()
    printSorted(d.sort_values(by='edp_mean', ascending=True).copy(), msg)
    #print('')


#d = df_comb[(df_comb['sys']=='linux_default') & (df_comb['itr']==1) & (df_comb['dvfs']=='0xFFFF')].copy()
#printdf(d)

#d = df_comb[(df_comb['sys']=='linux_tuned') & (df_comb['itr']!=1) & (df_comb['dvfs']!='0xFFFF')].copy()
#printdf(d)

#d = df_comb[(df_comb['sys']=='ebbrt_tuned') & (df_comb['itr']!=1) & (df_comb['dvfs']!='0xFFFF')].copy()
#printdf(d)



    
        
'''
det = df[(df['sys']=='ebbrt_tuned')].copy()
dlt = df[(df['sys']=='linux_tuned')].copy()
dld = df[(df['sys']=='linux_default') & (df['itr']==1) & (df['dvfs']=='0xFFFF')].copy()

for d in [dld, dlt, det]:
#    for m in [64/1000.0, 8192/1000.0, 65536/1000.0, 524288/1000.0]:
    for m in [8192/1000.0]:
        dbest = d[d['msg'] == m].copy()
        dbest['edp'] = dbest['joules'] * dbest['time']
        b = dbest[dbest.edp==dbest.edp.min()].iloc[0]
        print('Best EPP', m)
        print(f"{b['sys']} {b['itr']},{b['dvfs']},{b['rapl']} {round(b['edp'], 3)} {round(b['time'],3)}")
    
        b = dbest[dbest.joules==dbest.joules.min()].iloc[0] 
        print('Best Joules', m)
        print(f"{b['sys']} {b['itr']},{b['dvfs']},{b['rapl']} {round(b['joules'],3)} {round(b['time'],3)}")

        b = dbest[dbest.time==dbest.time.min()].iloc[0]
        print('Best Time', m)
        print(f"{b['sys']} {b['itr']},{b['dvfs']},{b['rapl']} {round(b['joules'], 3)} {round(b['time'],3)}")
        print('')
'''
