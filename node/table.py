import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import matplotlib
import os
import glob
import multiprocessing as mp

JOULE_CONVERSION = 0.00001526 #counter * constant -> JoulesOB
TIME_CONVERSION_khz = 1./(2899999*1000)

workload_loc='/scratch2/node/node_combined_11_17_2020/node_combined.csv'
log_loc='/scratch2/node/node_combined_11_17_2020/'

df = pd.read_csv(workload_loc, sep=' ')
df = df[df['joules'] > 0]
df['edp'] = df['joules'] * df['time']

dld = df[(df['sys']=='linux_default') & (df['itr']==1) & (df['dvfs']=='0xffff')].copy()
dlt = df[(df['sys']=='linux_tuned')].copy()
det = df[(df['sys']=='ebbrt_tuned')].copy()

## prep
bconf={}
wconf={}
for dbest in [dld, dlt, det]:
    b = dbest[dbest.edp==dbest.edp.min()].iloc[0]
    bconf[b['sys']] = [b['i'], b['itr'], b['dvfs'], b['rapl']]
    w = dbest[dbest.edp==dbest.edp.max()].iloc[0]
    wconf[w['sys']] = [w['i'], w['itr'], w['dvfs'], w['rapl']]
#print(bconf)
bconf['ebbrt_tuned'] = [2, 4, '0x1900', 135]

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
