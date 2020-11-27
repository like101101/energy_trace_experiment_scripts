import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import matplotlib
import os
import glob
import multiprocessing as mp

def updateDF(fname, START_RDTSC, END_RDTSC, ebbrt=False):
    df = pd.DataFrame()
    if ebbrt:
        df = pd.read_csv(fname, sep=' ', names=EBBRT_COLS, skiprows=1)
        df['c1'] = 0
        df['c1e'] = 0
        df = df[df['timestamp'] >= START_RDTSC]
        df = df[df['timestamp'] <= END_RDTSC]
        df['timestamp'] = df['timestamp'] - df['timestamp'].min()
        df['timestamp'] = df['timestamp'] * TIME_CONVERSION_khz                
    else:
        df = pd.read_csv(fname, sep=' ', names=LINUX_COLS)
        df = df[df['timestamp'] >= START_RDTSC]
        df['timestamp'] = df['timestamp'] - df['timestamp'].min()
        df['timestamp'] = df['timestamp'] * TIME_CONVERSION_khz
        #df = df[df['timestamp'] <= 20.0]
    ## filter out timestamps    
    #converting timestamps
    df = df.iloc[100:]
    df.drop(df.tail(100).index,
            inplace = True)
    
    # update timestamp_diff
    df['timestamp_diff'] = df['timestamp'].diff()
    df.dropna(inplace=True)
        
    ## convert global_linux_tuned_df_non0j
    df_non0j = df[df['joules'] > 0
                  & (df['instructions'] > 0)
                  & (df['cycles'] > 0)
                  & (df['ref_cycles'] > 0)
                  & (df['llc_miss'] > 0)].copy()
    df_non0j['timestamp_non0'] = df_non0j['timestamp'] - df_non0j['timestamp'].min()
    df_non0j['joules'] = df_non0j['joules'] * JOULE_CONVERSION
    tmp = df_non0j[['instructions', 'ref_cycles', 'cycles', 'joules', 'timestamp_non0', 'llc_miss', 'c1', 'c1e', 'c3', 'c6', 'c7']].diff()
    tmp.columns = [f'{c}_diff' for c in tmp.columns]
    df_non0j = pd.concat([df_non0j, tmp], axis=1)    
    df_non0j['ref_cycles_diff'] = df_non0j['ref_cycles_diff'] * TIME_CONVERSION_khz
    df_non0j.dropna(inplace=True)
    print(df_non0j['ref_cycles_diff'][:10])
    print(df_non0j['timestamp_non0_diff'][:10])
    
    df_non0j['nonidle_frac_diff'] = df_non0j['ref_cycles_diff'] / df_non0j['timestamp_non0_diff']
    
    
    #
    #df['nonidle_timestamp_diff'] = df['refcyc_diff'] * TIME_CONVERSION_khz
    
    
    #df_non0j['nonidle_timestamp_diff'] = df_non0j['ref_cycles_diff'] * TIME_CONVERSION_khz
    #global_linux_tuned_df_non0j['nonidle_frac_diff'] = global_linux_tuned_df_non0j['nonidle_timestamp_diff'] / global_linux_tuned_df_non0j['timestamp_diff']
    #print(global_linux_tuned_df_non0j['nonidle_timestamp_diff'], global_linux_tuned_df_non0j['nonidle_timestamp_diff'].shape[0])
    #print(global_linux_tuned_df_non0j['timestamp_diff'], global_linux_tuned_df_non0j['timestamp_diff'].shape[0])
    return df, df_non0j


plt.rc('axes', labelsize=14)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=14)    # fontsize of the tick labels
plt.rc('ytick', labelsize=14)    # fontsize of the tick labels
plt.rc('legend', fontsize=14)    # legend fontsize

plt.ion()

x_offset, y_offset = 0.01/5, 0.01/5

LINUX_COLS = ['i', 'rx_desc', 'rx_bytes', 'tx_desc', 'tx_bytes', 'instructions', 'cycles', 'ref_cycles', 'llc_miss', 'c1', 'c1e', 'c3', 'c6', 'c7', 'joules', 'timestamp']
EBBRT_COLS = ['i', 'rx_desc', 'rx_bytes', 'tx_desc', 'tx_bytes', 'instructions', 'cycles', 'ref_cycles', 'llc_miss', 'c3', 'c6', 'c7', 'joules', 'timestamp']

JOULE_CONVERSION = 0.00001526 #counter * constant -> JoulesOB
TIME_CONVERSION_khz = 1./(2899999*1000)

workload_loc='/scratch2/mcdsilo/mcdsilo_combined_11_20_2020/mcdsilo_combined.csv'
log_loc='/scratch2/mcdsilo/mcdsilo_combined_11_20_2020/'

COLORS = {'linux_default': 'blue',
          'linux_tuned': 'green',
          'ebbrt_tuned': 'red'}          
LABELS = {'linux_default': 'Linux Default',
          'linux_tuned': 'Linux Tuned',
          'ebbrt_tuned': 'LibOS Tuned'}
FMTS = {'linux_default': 'o--',
          'linux_tuned': '*-.',
          'ebbrt_tuned': 'x:'}
HATCHS = {'linux_default': 'o',
          'linux_tuned': '*',
          'ebbrt_tuned': 'x'}

df = pd.read_csv(workload_loc, sep=' ')
df = df[df['joules'] > 0]
df = df[df['read_99th'] <= 500.0]
df['edp'] = 0.5 * df['joules'] * df['time']

#plot 1: overview
plt.figure()
dld = df[(df['sys']=='linux_default') & (df['itr']==1) & (df['dvfs']=='0xffff') & (df['target_QPS'] == 100000)].copy()
dlt = df[(df['sys']=='linux_tuned') & (df['target_QPS'] == 100000)].copy()
det = df[(df['sys']=='ebbrt_tuned') & (df['target_QPS'] == 100000)].copy()
#plt.title('Memcached-Silo 200K QPS')
plt.errorbar(det['read_99th'], det['joules'], fmt='x', label=LABELS[det['sys'].max()], c=COLORS['ebbrt_tuned'], alpha=1)
plt.errorbar(dlt['read_99th'], dlt['joules'], fmt='*', label=LABELS[dlt['sys'].max()], c=COLORS['linux_tuned'], alpha=1)
plt.errorbar(dld['read_99th'], dld['joules'], fmt='o', label=LABELS[dld['sys'].max()], c=COLORS['linux_default'], alpha=1)
plt.xlabel("99% Tail Latency (usecs)")
plt.ylabel("Energy Consumed (Joules)")
#plt.legend()
plt.grid()
plt.show()
plt.savefig('mcdsilo_100K_overview.pdf')

## EDP
x_offset, y_offset = 0.01/5, 0.01/5
plt.figure()
for dbest in [dld, dlt, det]:
    b = dbest[dbest.edp==dbest.edp.min()].iloc[0]
    #print(b)
    btime = b['time']
    bjoules = b['joules']

    di = b['i']
    ditr = b['itr']
    ddvfs = b['dvfs']
    drapl = b['rapl']
    dqps = b['target_QPS']
    dsys = b['sys']
    
    markevery = range(1, 2)    
    plt.errorbar([0, btime], [0, bjoules], markevery=markevery, label=LABELS[dbest['sys'].max()], fmt=FMTS[dbest['sys'].max()], c=COLORS[dbest['sys'].max()])
    if dsys == 'linux_tuned':
        plt.text(x_offset + btime - 2, y_offset + bjoules + 60, f'({ditr}, {ddvfs}, {drapl})')
    if dsys == 'ebbrt_tuned':
        plt.text(x_offset + btime - 2, y_offset + bjoules - 300, f'({ditr}, {ddvfs}, {drapl})')

plt.xlabel("Time (secs)")
plt.ylabel("Energy Consumed (Joules)")
plt.legend()
plt.grid()
plt.show()
plt.savefig('mcdsilo_200K_edp.pdf')

#bar plots
metric_labels = ['Instructions', 'Energy', 'RefCycles', 'TxBytes', 'Interrupts']
N_metrics = len(metric_labels) #number of clusters
N_systems = 3 #number of plot loops

fig, ax = plt.subplots(1)

idx = np.arange(N_metrics) #one group per metric
width = 0.2

df_dict = {'linux_default': dld,
           'linux_tuned': dlt,
           'ebbrt_tuned': det}

data_dict = {}

for dbest in [dld, dlt, det]:
    b = dbest[dbest.edp==dbest.edp.min()].iloc[0]
    btime = b['time']
    bjoules = b['joules']

    di = b['i']
    ditr = b['itr']
    ddvfs = b['dvfs']
    drapl = b['rapl']
    dqps = b['target_QPS']
    dsys = b['sys']

    data_dict[dsys] = np.array([b['instructions'],
                                b['joules'],
                                b['ref_cycles'],
                                b['tx_bytes'],
                                b['num_interrupts']])
    
counter = 0
for sys in data_dict: #normalize and plot
    data = data_dict[sys] / data_dict['linux_default']    
    ax.bar(idx + counter*width, data, width, label=LABELS[sys], color=COLORS[sys], edgecolor='black', hatch=HATCHS[sys])
    counter += 1
    
ax.set_xticks(idx)
ax.set_xticklabels(metric_labels, rotation=15)
#ax.set_ylabel('Metric / Metric for Linux Default')
plt.legend(loc='lower left')
plt.savefig('mcdsilo_200K_barplot.pdf')


# energy timeline
plt.figure()
for dbest in [dld, dlt, det]:
    b = dbest[dbest.edp==dbest.edp.min()].iloc[0]
    btime = b['time']
    bjoules = b['joules']

    di = b['i']
    ditr = b['itr']
    ddvfs = b['dvfs']
    drapl = b['rapl']
    dqps = b['target_QPS']
    dsys = b['sys']
    print(b)
    
    if dsys == 'ebbrt_tuned':
        frdtscname = f'{log_loc}/ebbrt_rdtsc.{di}_{ditr}_{ddvfs}_{drapl}_{dqps}'
        frdtsc = open(frdtscname, 'r')
        for line in frdtsc:
            tmp = line.strip().split(' ')
            START_RDTSC = int(tmp[0])
            END_RDTSC = int(tmp[1])
            break    
        frdtsc.close()

        fname = f'{log_loc}/ebbrt_dmesg.{di}_{0}_{ditr}_{ddvfs}_{drapl}_{dqps}.csv'        
        det_df, det_non0j = updateDF(fname, START_RDTSC, END_RDTSC, ebbrt=True)
        plt.errorbar(det_non0j['timestamp'], det_non0j['joules_diff'], label=LABELS[dsys], fmt=HATCHS[dsys], c=COLORS[dsys])
    else:
        START_RDTSC=0
        END_RDTSC=0
        frdtscname = f'{log_loc}/linux.mcdsilo.rdtsc.{di}_{ditr}_{ddvfs}_{drapl}_{dqps}'
        frdtsc = open(frdtscname, 'r')
        for line in frdtsc:
            tmp = line.strip().split(' ')
            if int(tmp[2]) > START_RDTSC:                                
                START_RDTSC = int(tmp[2])                        
        frdtsc.close()
        fname = f'{log_loc}/linux.mcdsilo.dmesg.{di}_{0}_{ditr}_{ddvfs}_{drapl}_{dqps}'
        l_df, l_non0j = updateDF(fname, START_RDTSC, END_RDTSC)
        #plt.errorbar(l_non0j['timestamp'], l_non0j['joules_diff'], label=LABELS[dsys], fmt=HATCHS[dsys], c=COLORS[dsys])
        plt.errorbar(l_non0j['timestamp_non0'], l_non0j['nonidle_frac_diff'], label=LABELS[dsys], fmt=HATCHS[dsys], c=COLORS[dsys])        
        
plt.xlabel("Time (secs)")
#plt.ylabel("Energy Consumed (Joules)"
plt.ylabel("Non-idle Time (%)")
plt.legend()
plt.grid()
plt.savefig('mcdsilo_200K_nonidle_timeline.pdf')

dld = df[(df['sys']=='linux_default') & (df['itr']==1) & (df['dvfs']=='0xffff')].copy()
dlt = df[(df['sys']=='linux_tuned')].copy()
det = df[(df['sys']=='ebbrt_tuned')].copy()

for d in [dld, dlt, det]:
    for m in [50000, 100000, 200000]:
        dbest = d[d['target_QPS'] == m].copy()
        dbest['edp'] = dbest['joules'] * dbest['read_99th']
        b = dbest[dbest.edp==dbest.edp.min()].iloc[0] 
        print('Best EPP', m)
        ins="{:e}".format(b['instructions'])
        rcyc="{:e}".format(b['ref_cycles'])
        rb="{:e}".format(b['rx_bytes'])
        tb="{:e}".format(b['tx_bytes'])
        numi="{:e}".format(b['num_interrupts'])
        print(f"{b['sys']} {b['itr']},{b['dvfs']},{b['rapl']} {round(b['edp'], 3)} {round(b['read_99th'],3)} {ins} {rcyc} {rb} {tb} {numi}")
        
        b = dbest[dbest.joules==dbest.joules.min()].iloc[0] 
        print('Best Joules', m)
        ins="{:e}".format(b['instructions'])
        rcyc="{:e}".format(b['ref_cycles'])
        rb="{:e}".format(b['rx_bytes'])
        tb="{:e}".format(b['tx_bytes'])
        numi="{:e}".format(b['num_interrupts'])
        print(f"{b['sys']} {b['itr']},{b['dvfs']},{b['rapl']} {round(b['joules'],3)} {round(b['read_99th'],3)} {ins} {rcyc} {rb} {tb} {numi}")
        
        b = dbest[dbest.read_99th==dbest.read_99th.min()].iloc[0]
        print('Best Tail', m)
        ins="{:e}".format(b['instructions'])
        rcyc="{:e}".format(b['ref_cycles'])
        rb="{:e}".format(b['rx_bytes'])
        tb="{:e}".format(b['tx_bytes'])
        numi="{:e}".format(b['num_interrupts'])
        print(f"{b['sys']} {b['itr']},{b['dvfs']},{b['rapl']} {round(b['joules'], 3)} {round(b['read_99th'],3)} {ins} {rcyc} {rb} {tb} {numi}")

    

