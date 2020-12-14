import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import matplotlib
import os
import glob
import multiprocessing as mp

def printSorted(d):
    c=0
    for index, b in d.iterrows():
        csum = int(b['c1_mean'])+int(b['c1e_mean'])+int(b['c3_mean'])+int(b['c6_mean'])+int(b['c7_mean'])
        print(f"{c} {b['sys']} {b['itr']} {b['dvfs']} {b['rapl']} {round(b['edp_mean'], 2)} {round(b['edp_std'], 2)} {round(b['joules_mean'], 2)} {round(b['joules_std'], 2)} {round(b['time_mean'], 2)} {round(b['time_std'], 2)} {int(b['lat99_mean'])} {int(b['lat99_std'])} {int(b['num_interrupts_mean'])} {int(b['num_interrupts_std'])} {int(b['instructions_mean'])} {int(b['instructions_std'])} {int(b['ref_cycles_mean'])} {int(b['ref_cycles_std'])} {int(b['llc_miss_mean'])} {int(b['llc_miss_std'])} {int(b['c1_mean'])} {int(b['c1_std'])} {int(b['c1e_mean'])} {int(b['c1e_std'])} {int(b['c3_mean'])} {int(b['c3_std'])} {int(b['c6_mean'])} {int(b['c6_std'])} {int(b['c7_mean'])} {int(b['c7_std'])} {int(csum)} {int(b['rx_bytes_mean'])} {int(b['rx_bytes_std'])} {int(b['tx_bytes_mean'])} {int(b['tx_bytes_std'])}")
        c += 1
        if c > 1:
            break

        
JOULE_CONVERSION = 0.00001526 #counter * constant -> JoulesOB
TIME_CONVERSION_khz = 1./(2899999*1000)

workload_loc='/scratch2/node/node_combined_11_17_2020/node_combined.csv'
#workload_loc='/scratch2/node/node_top10/node_combined.csv'
log_loc='/scratch2/node/node_combined_11_17_2020/'

df = pd.read_csv(workload_loc, sep=' ')
df = df[df['joules'] > 0]
df['edp'] = df['joules'] * df['time']

NCOLS = ['sys', 'itr', 'dvfs', 'rapl']
df_mean = df.groupby(NCOLS).mean()
df_std = df.groupby(NCOLS).std()

df_mean.columns = [f'{c}_mean' for c in df_mean.columns]
df_std.columns = [f'{c}_std' for c in df_std.columns]

df_comb = pd.concat([df_mean, df_std], axis=1)
df_comb.reset_index(inplace=True)

d = df_comb[(df_comb['sys']=='linux_default') & (df_comb['itr']==1) & (df_comb['dvfs']=='0xffff')].copy()
#printSorted(d.sort_values(by='edp_mean', ascending=True).copy())
printSorted(d.sort_values(by='time_mean', ascending=True).copy())

d = df_comb[(df_comb['sys']=='linux_tuned')].copy()
printSorted(d.sort_values(by='time_mean', ascending=True).copy())
#printSorted(d.sort_values(by='edp_mean', ascending=True).copy())

d = df_comb[(df_comb['sys']=='ebbrt_tuned')].copy()
printSorted(d.sort_values(by='time_mean', ascending=True).copy())
#dd = d[d['lat99_mean'] <= 77].copy()
#printSorted(dd.sort_values(by='edp_mean', ascending=True).copy())


#dld = df[(df['sys']=='linux_default') & (df['itr']==1) & (df['dvfs']=='0xffff')].copy()
#dlt = df[(df['sys']=='linux_tuned')].copy()
#det = df[(df['sys']=='ebbrt_tuned')].copy()

## prep
#bconf={}
#wconf={}
#for dbest in [dld, dlt, det]:
#    b = dbest[dbest.edp==dbest.edp.min()].iloc[0]
#    bconf[b['sys']] = [b['i'], b['itr'], b['dvfs'], b['rapl']]
    #w = dbest[dbest.edp==dbest.edp.max()].iloc[0]
    #wconf[w['sys']] = [w['i'], w['itr'], w['dvfs'], w['rapl']]
#print(bconf)
#bconf['ebbrt_tuned'] = [2, 4, '0x1900', 135]

'''
#print(bconf)
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    num = bconf[dsys][0]
    itr = bconf[dsys][1]
    dvfs = bconf[dsys][2]
    rapl = bconf[dsys][3]
    d = df[(df['sys']==dsys) & (df['itr']==itr) & (df['dvfs']==dvfs) & (df['rapl']==rapl)].copy()
    edp_mean = d['edp'].mean()
    edp_std = d['edp'].std()
    joules_mean = d['joules'].mean()
    time_mean = d['time'].mean()    
    print(f"best epp {dsys} {itr},{dvfs},{rapl} {round(edp_mean, 3)} {round(edp_std, 3)} {round(joules_mean, 3)} {round(time_mean, 3)}")

for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    num = wconf[dsys][0]
    itr = wconf[dsys][1]
    dvfs = wconf[dsys][2]
    rapl = wconf[dsys][3]
    d = df[(df['sys']==dsys) & (df['itr']==itr) & (df['dvfs']==dvfs) & (df['rapl']==rapl)].copy()
    edp_mean = d['edp'].mean()
    edp_std = d['edp'].std()
    joules_mean = d['joules'].mean()
    time_mean = d['time'].mean()    
    print(f"worst epp {dsys} {itr},{dvfs},{rapl} {round(edp_mean, 3)} {round(edp_std, 3)} {round(joules_mean, 3)} {round(time_mean, 3)}")
'''    
'''
## tables
for dbest in [dld, dlt, det]:
    b = dbest[dbest.edp==dbest.edp.min()].iloc[0] 
    print('Best EPP')
    ins="{:e}".format(b['instructions'])
    rcyc="{:e}".format(b['ref_cycles'])
    rb="{:e}".format(b['rx_bytes'])
    tb="{:e}".format(b['tx_bytes'])
    numi="{:e}".format(b['num_interrupts'])
    print(f"{b['sys']} {b['itr']},{b['dvfs']},{b['rapl']} {round(b['edp'], 3)} {round(b['time'],3)} {ins} {rcyc} {rb} {tb} {numi}")
    
    b = dbest[dbest.joules==dbest.joules.min()].iloc[0] 
    print('Best Joules')
    ins="{:e}".format(b['instructions'])
    rcyc="{:e}".format(b['ref_cycles'])
    rb="{:e}".format(b['rx_bytes'])
    tb="{:e}".format(b['tx_bytes'])
    numi="{:e}".format(b['num_interrupts'])
    print(f"{b['sys']} {b['itr']},{b['dvfs']},{b['rapl']} {round(b['joules'],3)} {round(b['time'],3)} {ins} {rcyc} {rb} {tb} {numi}")

    b = dbest[dbest.time==dbest.time.min()].iloc[0]
    print('Best Time')
    ins="{:e}".format(b['instructions'])
    rcyc="{:e}".format(b['ref_cycles'])
    rb="{:e}".format(b['rx_bytes'])
    tb="{:e}".format(b['tx_bytes'])
    numi="{:e}".format(b['num_interrupts'])
    print(f"{b['sys']} {b['itr']},{b['dvfs']},{b['rapl']} {round(b['joules'], 3)} {round(b['time'],3)} {ins} {rcyc} {rb} {tb} {numi}") 
'''
