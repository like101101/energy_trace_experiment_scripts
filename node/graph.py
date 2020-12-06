import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import matplotlib
import os
import glob
import multiprocessing as mp

LINUX_COLS = ['i', 'rx_desc', 'rx_bytes', 'tx_desc', 'tx_bytes', 'instructions', 'cycles', 'ref_cycles', 'llc_miss', 'c1', 'c1e', 'c3', 'c6', 'c7', 'joules', 'timestamp']
EBBRT_COLS = ['i', 'rx_desc', 'rx_bytes', 'tx_desc', 'tx_bytes', 'instructions', 'cycles', 'ref_cycles', 'llc_miss', 'c3', 'c6', 'c7', 'joules', 'timestamp']

def updateDF(fname, START_RDTSC, END_RDTSC, ebbrt=False):
    df = pd.DataFrame()
    if ebbrt:
        df = pd.read_csv(fname, sep=' ', names=EBBRT_COLS, skiprows=1)
        df['c1'] = 0
        df['c1e'] = 0
    else:
        df = pd.read_csv(fname, sep=' ', names=LINUX_COLS)

    df = df.iloc[100:]
    
    ## filter out timestamps
    df = df[df['timestamp'] >= START_RDTSC]
    df = df[df['timestamp'] <= END_RDTSC]
    #converting timestamps
    df['timestamp'] = df['timestamp'] - df['timestamp'].min()
    df['timestamp'] = df['timestamp'] * TIME_CONVERSION_khz
    df['timestamp_diff'] = df['timestamp'].diff()
    df.dropna(inplace=True)        
    
    ## convert df_non0j
    df_non0j = df[df['joules'] > 0
                  & (df['instructions'] > 0)
                  & (df['cycles'] > 0)
                  & (df['ref_cycles'] > 0)
                  & (df['llc_miss'] > 0)].copy()
    df_non0j['timestamp_non0'] = df_non0j['timestamp'] - df_non0j['timestamp'].min()
    # convert joules
    df_non0j['joules'] = df_non0j['joules'] * JOULE_CONVERSION
    df_non0j['joules'] = df_non0j['joules'] - df_non0j['joules'].min()
    tmp = df_non0j[['instructions', 'ref_cycles', 'cycles', 'joules', 'timestamp_non0', 'llc_miss', 'c1', 'c1e', 'c3', 'c6', 'c7']].diff()
    tmp.columns = [f'{c}_diff' for c in tmp.columns]
    df_non0j = pd.concat([df_non0j, tmp], axis=1)
    df_non0j['ref_cycles_diff'] = df_non0j['ref_cycles_diff'] * TIME_CONVERSION_khz
    df_non0j.dropna(inplace=True)
    df_non0j['nonidle_frac_diff'] = df_non0j['ref_cycles_diff'] / df_non0j['timestamp_non0_diff']

    return df, df_non0j

plt.rc('axes', labelsize=14)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=14)    # fontsize of the tick labels
plt.rc('ytick', labelsize=14)    # fontsize of the tick labels
plt.rc('legend', fontsize=14)    # legend fontsize

#plt.ion()

x_offset, y_offset = 0.01/5, 0.01/5

JOULE_CONVERSION = 0.00001526 #counter * constant -> JoulesOB
TIME_CONVERSION_khz = 1./(2899999*1000)

workload_loc='/scratch2/node/node_combined_11_17_2020/node_combined.csv'
log_loc='/scratch2/node/node_combined_11_17_2020/'

COLORS = {'linux_default': 'blue',
          'linux_tuned': 'green',
          'ebbrt_tuned': 'red'}          
LABELS = {'linux_default': 'Linux Default',
          'linux_tuned': 'Linux Tuned',
          'ebbrt_tuned': 'LibOS Tuned'}
FMTS = {'linux_default': 'o--',
          'linux_tuned': '*-.',
          'ebbrt_tuned': 'x:'}
LINES = {'linux_default': '--',
          'linux_tuned': '-.',
          'ebbrt_tuned': ':'}
HATCHS = {'linux_default': 'o',
          'linux_tuned': '*',
          'ebbrt_tuned': 'x'}

df = pd.read_csv(workload_loc, sep=' ')
df = df[df['joules'] > 0]
df['edp'] = df['joules'] * df['time'] * df['lat99']

dld = df[(df['sys']=='linux_default') & (df['itr']==1) & (df['dvfs']=='0xffff')].copy()
dlt = df[(df['sys']=='linux_tuned')].copy()
det = df[(df['sys']=='ebbrt_tuned')].copy()

'''
## overview
plt.figure()
plt.errorbar(det['joules'], det['time'], fmt='x', label=LABELS[det['sys'].max()], c=COLORS['ebbrt_tuned'], alpha=0.5)
plt.errorbar(dlt['joules'], dlt['time'], fmt='*', label=LABELS[dlt['sys'].max()], c=COLORS['linux_tuned'], alpha=0.5)
plt.errorbar(dld['joules'], dld['time'], fmt='o', label=LABELS[dld['sys'].max()], c=COLORS['linux_default'], alpha=0.5)
plt.ylabel("Time (secs)")
plt.xlabel("Energy Consumed (Joules)")
plt.legend()
plt.grid()
plt.savefig('nodejs_overview.pdf')
'''

## prep
bconf={}
for dbest in [dld, dlt, det]:
    b = dbest[dbest.edp==dbest.edp.min()].iloc[0]
    bconf[b['sys']] = [b['i'], b['itr'], b['dvfs'], b['rapl']]
bconf['ebbrt_tuned'] = [2, 4, '0x1900', 135]
print(bconf)

ddfs = {}
lddf = pd.DataFrame()
lddfn = pd.DataFrame()
ltdf = pd.DataFrame()
ltdfn = pd.DataFrame()
etdf = pd.DataFrame()
etdfn = pd.DataFrame()

for dsys in ['ebbrt_tuned', 'linux_tuned', 'linux_default']:
    fname=''    
    START_RDTSC=0
    END_RDTSC=0
    num = bconf[dsys][0]
    itr = bconf[dsys][1]
    dvfs = bconf[dsys][2]
    rapl = bconf[dsys][3]

    if dsys == 'linux_tuned' or dsys == 'linux_default':        
        frdtscname = f'{log_loc}/linux.node.server.rdtsc.{num}_1_{itr}_{dvfs}_{rapl}'
        frdtsc = open(frdtscname, 'r')
        for line in frdtsc:
            tmp = line.strip().split(' ')
            START_RDTSC = int(tmp[1])
            END_RDTSC = int(tmp[2])
            tdiff = round(float((END_RDTSC - START_RDTSC) * TIME_CONVERSION_khz), 2)
            if tdiff > 3 and tdiff < 40:
                break
        frdtsc.close()

        fname = f'{log_loc}/linux.node.server.log.{num}_1_{itr}_{dvfs}_{rapl}'
        if dsys == 'linux_tuned':
            ltdf, ltdfn = updateDF(fname, START_RDTSC, END_RDTSC)
            ddfs[dsys] = [ltdf, ltdfn]
        elif dsys == 'linux_default':
            lddf, lddfn = updateDF(fname, START_RDTSC, END_RDTSC)
            ddfs[dsys] = [lddf, lddfn]            
    elif dsys == 'ebbrt_tuned':        
        frdtscname = f'{log_loc}/ebbrt_rdtsc.{num}_{itr}_{dvfs}_{rapl}'
        frdtsc = open(frdtscname, 'r')
        for line in frdtsc:
            tmp = line.strip().split(' ')
            START_RDTSC = int(tmp[0])
            END_RDTSC = int(tmp[1])
            tdiff = round(float((END_RDTSC - START_RDTSC) * TIME_CONVERSION_khz), 2)
            if tdiff > 3 and tdiff < 40:
                break
        frdtsc.close()        
        fname = f'{log_loc}/ebbrt_dmesg.{num}_1_{itr}_{dvfs}_{rapl}.csv'
        etdf, etdfn = updateDF(fname, START_RDTSC, END_RDTSC, ebbrt=True)
        ddfs[dsys] = [etdf, etdfn]

## timediff timeline
plt.figure()
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    #ddf = ddf[(ddf['timestamp'] > 5.5) & (ddf['timestamp'] < 8)]
    ddf = ddf[ddf['timestamp_diff'] < 0.0005]
    plt.plot(ddf['timestamp'], ddf['timestamp_diff'], FMTS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
plt.xlabel("Time (secs)")
plt.ylabel("Time_diff")
plt.legend()
plt.grid()
plt.savefig(f'nodejs_timediff_timeline.pdf')


'''

## instructions timeline
plt.figure()
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    #ddfn = ddfn[(ddfn['timestamp_non0'] > 3) & (ddfn['timestamp_non0'] < 8)]
    #ddfn = ddfn[(ddfn['timestamp_non0'] > 0.02)
    ddfn = ddfn[ddfn['instructions_diff'] < 2500000]
    plt.plot(ddfn['timestamp_non0'], ddfn['instructions_diff'], FMTS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
plt.xlabel("Time (secs)")
plt.ylabel("Instructions")
plt.legend(loc='upper left')
#plt.xticks(visible=False)
#plt.yticks(visible=False)
plt.grid()
plt.savefig(f'nodejs_instructions_timeline_zoom.pdf')


#bar plots
metric_labels = ['CPI', 'Instructions', 'Cycles', 'Halt', 'RxBytes', 'TxBytes', 'Interrupts']
N_metrics = len(metric_labels) #number of clusters
N_systems = 3 #number of plot loops
fig, ax = plt.subplots(1)
idx = np.arange(N_metrics) #one group per metric
width = 0.2
data_dict = {}

for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]

    if 'ebbrt' in dsys:
        c_all = ddfn['c7'].sum()
        print(f"{dsys} c7={c_all}")
    else:
        c_all = ddfn['c1_diff'].sum() + ddfn['c1e_diff'].sum() + ddfn['c3_diff'].sum() + ddfn['c6_diff'].sum() + ddfn['c7_diff'].sum()
        print(f"{dsys} c1={ddfn['c1_diff'].sum()} c1e={ddfn['c1e_diff'].sum()} c3={ddfn['c3_diff'].sum()} c6={ddfn['c6_diff'].sum()} c7={ddfn['c7_diff'].sum()}")

        
    data_dict[dsys] = np.array([(ddfn['ref_cycles_diff'].sum()/ddfn['instructions_diff'].sum()),
                                ddfn['instructions_diff'].sum(),
                                ddfn['ref_cycles_diff'].sum(),
                                c_all,
                                ddf['rx_bytes'].sum(),
                                ddf['tx_bytes'].sum(),
                                ddf.shape[0]])
counter = 0
for sys in data_dict: #normalize and plot
    data = data_dict[sys] / data_dict['linux_default']    
    ax.bar(idx + counter*width, data, width, label=LABELS[sys], color=COLORS[sys], edgecolor='black', hatch=HATCHS[sys])
    counter += 1    
ax.set_xticks(idx)
ax.set_xticklabels(metric_labels, rotation=15)
plt.legend()
plt.savefig(f'nodejs_barplot.pdf')
'''
'''
## EDP
plt.figure()
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ditr = bconf[dsys][1]
    ddvfs = bconf[dsys][2]
    drapl = bconf[dsys][3]
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    
    plt.plot(ddfn['timestamp_non0'], ddfn['joules'], LINES[dsys], c=COLORS[dsys])
    plt.plot(ddfn['timestamp_non0'].iloc[0], ddfn['joules'].iloc[0], HATCHS[dsys], c=COLORS[dsys])
    plt.plot(ddfn['timestamp_non0'].iloc[-1], ddfn['joules'].iloc[-1], HATCHS[dsys], c=COLORS[dsys])
    plt.plot(ddfn['timestamp_non0'].iloc[::1400], ddfn['joules'].iloc[::1400], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)    
    btime = ddf['timestamp_diff'].sum()
    bjoules = ddfn['joules_diff'].sum()
    if 'tuned' in dsys:
        plt.text(x_offset + btime, y_offset + bjoules, f'({ditr}, {ddvfs}, {drapl})')
plt.xlabel("Time (secs)")
plt.ylabel("Energy Consumed (Joules)")
plt.legend()
plt.grid()
plt.savefig(f'nodejs_edp.pdf')

## joule timeline
plt.figure()
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]    
    plt.plot(ddfn['timestamp_non0'], ddfn['joules_diff'], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
plt.xlabel("Time (secs)")
plt.ylabel("Energy Consumed (Joules)")
plt.legend()
plt.grid()
plt.savefig(f'nodejs_joule_timeline.pdf')

## nonidle timeline
plt.figure()
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]    
    plt.plot(ddfn['timestamp_non0'], ddfn['nonidle_frac_diff'], FMTS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
plt.xlabel("Time (secs)")
plt.ylabel("Nonidle Time (%)")
plt.ylim((0, 1.001))
plt.legend()
plt.grid()
plt.savefig(f'nodejs_nonidle_timeline.pdf')

'''
'''
## rxbytes timeline
plt.figure()
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    ddf = ddf[(ddf['timestamp'] > 5.5) & (ddf['timestamp'] < 8)]
    plt.plot(ddf['timestamp'], ddf['rx_bytes'], FMTS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
plt.xlabel("Time (secs)")
plt.ylabel("RxBytes")
plt.legend()
plt.grid()
plt.savefig(f'nodejs_rxbytes_timeline.pdf')

## txbytes timeline
plt.figure()
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    ddf = ddf[(ddf['timestamp'] > 5.5) & (ddf['timestamp'] < 8)]
    plt.plot(ddf['timestamp'], ddf['tx_bytes'], FMTS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
plt.xlabel("Time (secs)")
plt.ylabel("TxBytes")
plt.legend()
plt.grid()
plt.savefig(f'nodejs_txbytes_timeline.pdf')
'''
