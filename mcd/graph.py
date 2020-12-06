import pandas as pd
import numpy as np
#from mpl_toolkits.axes_grid.inset_locator import inset_axes
import matplotlib.pylab as plt
import matplotlib
import os
import glob
import multiprocessing as mp
import sys
                                
plt.rc('axes', labelsize=14)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=14)    # fontsize of the tick labels
plt.rc('ytick', labelsize=14)    # fontsize of the tick labels
plt.rc('legend', fontsize=14)    # legend fontsize

QPS=600000
#if len(sys.argv) != 2:
#    print("graph.py <QPS>")
#    exit()
#QPS = int(sys.argv[1])

#plt.ion()

x_offset, y_offset = 0.01/5, 0.01/5

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
    ## filter out timestamps
    df = df[df['timestamp'] >= START_RDTSC]
    df = df[df['timestamp'] <= END_RDTSC]
    #converting timestamps
    df['timestamp'] = df['timestamp'] - df['timestamp'].min()
    df['timestamp'] = df['timestamp'] * TIME_CONVERSION_khz
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
    df_non0j['nonidle_frac_diff'] = df_non0j['ref_cycles_diff'] / df_non0j['timestamp_non0_diff']
    return df, df_non0j

JOULE_CONVERSION = 0.00001526 #counter * constant -> JoulesOB
TIME_CONVERSION_khz = 1./(2899999*1000)

workload_loc='/scratch2/mcd/mcd_combined_11_9_2020/mcd_combined.csv'
log_loc='/scratch2/mcd/mcd_combined_11_9_2020/'

COLORS = {'linux_default': 'blue',
          'linux_tuned': 'green',
          'ebbrt_tuned': 'red'}          
LABELS = {'linux_default': 'Linux Default',
          'linux_tuned': 'Linux Tuned',
          'ebbrt_tuned': 'LibOS Tuned'}
FMTS = {'linux_default':   'o--',
          'linux_tuned':   '*-.',
          'ebbrt_tuned':   'x:'}
LINES = {'linux_default':  '--',
          'linux_tuned':   '-.',
          'ebbrt_tuned':   ':'}
HATCHS = {'linux_default': 'o',
          'linux_tuned':   '*',
          'ebbrt_tuned':   'x'}

df = pd.read_csv(workload_loc, sep=' ')
df = df[df['joules'] > 0]
df = df[df['read_99th'] <= 500.0]
#df['edp'] = df['joules'] * df['time']
df['edp'] = df['joules'] * df['read_99th']
dld = df[(df['sys']=='linux_default') & (df['itr']==1) & (df['dvfs']=='0xffff') & (df['target_QPS'] == QPS)].copy()
dlt = df[(df['sys']=='linux_tuned') & (df['target_QPS'] == QPS)].copy()
det = df[(df['sys']=='ebbrt_tuned') & (df['target_QPS'] == QPS)].copy()

#bar plots
metric_labels = ['CPI', 'Ins', 'Cyc', 'C1', 'C1E', 'C3', 'C7', 'C*SUM', 'RxB', 'TxB', 'Interrupts']
N_metrics = len(metric_labels) #number of clusters
N_systems = 3 #number of plot loops

fig, ax = plt.subplots(1)

idx = np.arange(N_metrics) #one group per metric
width = 0.2
data_dict = {}

for dbest in [dld, dlt, det]:
    b = dbest[dbest.edp==dbest.edp.min()].iloc[0]
    dsys = b['sys']
    c_all = 0
    if 'ebbrt' in dsys:
        c_all = b['c7']
        print(f"{dsys} c7={c_all}")
    else:
        c_all = b['c1']+b['c1e']+b['c3']+b['c6']+b['c7']
        print(f"{dsys} c1={b['c1']} c1e={b['c1e']} c3={b['c3']} c6={b['c6']} c7={b['c7']}")
    
        
    data_dict[dsys] = np.array([b['ref_cycles']/b['instructions'],
                                b['instructions'],
                                b['ref_cycles'],
                                b['c1'],
                                b['c1e'],
                                b['c3'],
                                b['c7'],
                                c_all,
                                b['rx_bytes'],
                                b['tx_bytes'],
                                b['num_interrupts']])
counter = 0
for sys in data_dict: #normalize and plot
    data = data_dict[sys] / data_dict['linux_default']    
    ax.bar(idx + counter*width, data, width, label=LABELS[sys], color=COLORS[sys], edgecolor='black', hatch=HATCHS[sys])
    counter += 1
    
ax.set_xticks(idx)
ax.set_xticklabels(metric_labels, rotation=15)
plt.legend()
#plt.legend(loc='lower left')
plt.savefig(f'mcd_{QPS}_barplot.pdf')

## prep
bconf={}
for dbest in [dld, dlt, det]:
    b = dbest[dbest.edp==dbest.edp.min()].iloc[0]
    bconf[b['sys']] = [b['i'], b['itr'], b['dvfs'], b['rapl']]
print(bconf)

ddfs = {}

for dsys in ['ebbrt_tuned', 'linux_tuned', 'linux_default']:
    fname=''    
    START_RDTSC=0
    END_RDTSC=0
    i = bconf[dsys][0]
    itr = bconf[dsys][1]
    dvfs = bconf[dsys][2]
    rapl = bconf[dsys][3]
    qps = QPS
    core=0
    
    if dsys == 'linux_tuned' or dsys == 'linux_default':        
        frdtscname = f'{log_loc}/linux.mcd.rdtsc.{i}_{itr}_{dvfs}_{rapl}_{qps}'
        frdtsc = open(frdtscname, 'r')
        for line in frdtsc:
            tmp = line.strip().split(' ')
            if int(tmp[2]) > START_RDTSC:                                
                START_RDTSC = int(tmp[2])
            
            if END_RDTSC == 0:                                
                END_RDTSC = int(tmp[3])
            elif END_RDTSC < int(tmp[3]):
                END_RDTSC = int(tmp[3])                                                            
        frdtsc.close()

        fname = f'{log_loc}/linux.mcd.dmesg.{i}_{core}_{itr}_{dvfs}_{rapl}_{qps}'
        if dsys == 'linux_tuned':
            ltdf, ltdfn = updateDF(fname, START_RDTSC, END_RDTSC)
            ddfs[dsys] = [ltdf, ltdfn]
        elif dsys == 'linux_default':
            lddf, lddfn = updateDF(fname, START_RDTSC, END_RDTSC)
            ddfs[dsys] = [lddf, lddfn]
    elif dsys == 'ebbrt_tuned':
        frdtscname = f'{log_loc}/ebbrt_rdtsc.{i}_{itr}_{dvfs}_{rapl}_{qps}'
        frdtsc = open(frdtscname, 'r')
        for line in frdtsc:
            tmp = line.strip().split(' ')
            START_RDTSC = int(tmp[0])
            END_RDTSC = int(tmp[1])
            break    
        frdtsc.close()
        fname = f'{log_loc}/ebbrt_dmesg.{i}_{core}_{itr}_{dvfs}_{rapl}_{qps}.csv'
        etdf, etdfn = updateDF(fname, START_RDTSC, END_RDTSC, ebbrt=True)
        ddfs[dsys] = [etdf, etdfn]
    
## nonidle timeline
plt.figure()
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    ddfn = ddfn[(ddfn['nonidle_frac_diff'] > 0) & (ddfn['nonidle_frac_diff'] < 1.001)]
    plt.plot(ddfn['timestamp_non0'], ddfn['nonidle_frac_diff'], FMTS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
plt.xlabel("Time (secs)")
plt.ylabel("Nonidle Time (%)")
plt.ylim((0, 1.001))
plt.legend()
plt.grid()
plt.savefig(f'mcd_{QPS}_nonidle_timeline.png')

## joule timeline
plt.figure()
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    ddfn = ddfn[(ddfn['joules_diff'] > 0) & (ddfn['joules_diff'] < 3000)]
    plt.plot(ddfn['timestamp_non0'], ddfn['joules_diff'], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
plt.xlabel("Time (secs)")
plt.ylabel("Energy Consumed (Joules)")
plt.legend()
plt.grid()
plt.savefig(f'mcd_{QPS}_joules_timeline.png')

## instructions timeline
plt.figure()
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    ddfn = ddfn[(ddfn['instructions_diff'] > 0) & (ddfn['instructions_diff'] < 250000000)]
    plt.plot(ddfn['timestamp_non0'], ddfn['instructions_diff'], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
plt.xlabel("Time (secs)")
plt.ylabel("Instructions")
plt.ticklabel_format(axis="y", style="sci", scilimits=(0,0))
plt.legend()
plt.grid()
plt.savefig(f'mcd_{QPS}_instructions_timeline.png')

## timediff timeline
plt.figure()
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]    
    plt.plot(ddf['timestamp'], ddf['timestamp_diff'], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
plt.xlabel("Time (secs)")
plt.ylabel("Time diff (usecs)")
plt.ticklabel_format(axis="y", style="sci", scilimits=(0,0))
plt.legend()
plt.grid()
plt.savefig(f'mcd_{QPS}_timediff_timeline.png')

##rxbyte timeline
plt.figure()
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    ddf = ddf[(ddf['timestamp'] > 10) & (ddf['timestamp'] < 15)]
    plt.plot(ddf['timestamp'], ddf['rx_bytes'], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
plt.xlabel("Time (secs)")
plt.ylabel("RxBytes")
plt.ticklabel_format(axis="y", style="sci", scilimits=(0,0))
#plt.legend()
plt.grid()
plt.savefig(f'mcd_{QPS}_rxbytes_timeline.png')

#plot 1: throughput vs msg size
plt.figure()
plt.errorbar(det['joules'], det['read_99th'], fmt='x', label=LABELS[det['sys'].max()], c=COLORS['ebbrt_tuned'], alpha=1)
plt.errorbar(dlt['joules'], dlt['read_99th'], fmt='*', label=LABELS[dlt['sys'].max()], c=COLORS['linux_tuned'], alpha=1)
plt.errorbar(dld['joules'], dld['read_99th'], fmt='o', label=LABELS[dld['sys'].max()], c=COLORS['linux_default'], alpha=1)

plt.ylabel("99% Tail Latency (usecs)")
plt.xlabel("Energy Consumed (Joules)")
#plt.legend()
plt.grid()
plt.show()
plt.savefig(f'mcd_{QPS}_overview.pdf')

## EPP
x_offset, y_offset = 0.01/5, 0.01/5
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

    xxrange = np.arange(0, int(btime)+1, int(btime/10))
    yyrange = np.arange(0, int(bjoules)+1, int(bjoules/10))
    #print(btime, xxrange)
    #print(bjoules, yyrange)
    plt.errorbar(xxrange, yyrange, label=LABELS[dbest['sys'].max()], fmt=FMTS[dbest['sys'].max()], c=COLORS[dbest['sys'].max()])
    if dsys == 'linux_tuned':
        plt.text(x_offset + btime - 2, y_offset + bjoules + 60, f'({ditr}, {ddvfs}, {drapl})')
    if dsys == 'ebbrt_tuned':
        plt.text(x_offset + btime - 2, y_offset + bjoules - 300, f'({ditr}, {ddvfs}, {drapl})')
    #plt.axis([0, 1, 1.1*np.amin(yyrange), 1.1*np.amax(yyrange)])

plt.xlabel("Time (secs)")
plt.ylabel("Energy Consumed (Joules)")
plt.legend(loc='lower right')
plt.grid()

#99 tail subplot
metric_labels = ['99% Tail (us)']
N_metrics = len(metric_labels) #number of clusters
N_systems = 3 #number of plot loops

#fig, ax = plt.subplots(1)

idx = np.arange(N_metrics) #one group per metric
width = 0.2

df_dict = {'linux_default': dld,
           'linux_tuned': dlt,
           'ebbrt_tuned': det}

data_dict = {}
a = plt.axes([.15, .53, .3, .3])

for dbest in [dld, dlt, det]:
    b = dbest[dbest.edp==dbest.edp.min()].iloc[0]
    dsys = b['sys']
    data_dict[dsys] = np.array([b['read_99th']])    
counter = 0
for sys in data_dict: #normalize and plot
    data = data_dict[sys]
    rect = plt.bar(idx + counter*width, data, width, label=LABELS[sys], color=COLORS[sys], edgecolor='black', hatch=HATCHS[sys])    
    height = int(data)
    plt.annotate('{}'.format(height),
                 xy=(idx + counter*width, height),
                 xytext=(0, 3),  # 3 points vertical offset
                 textcoords="offset points",
                 ha='center', va='bottom')
    counter += 1
    plt.xticks([])
    plt.yticks([])
    plt.xlabel('99% Tail (us)')
plt.show()
plt.savefig(f'mcd_{QPS}_epp.pdf')

## txbyte timeline
plt.figure()
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]    
    plt.plot(ddf['timestamp'], ddf['tx_bytes'], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
plt.xlabel("Time (secs)")
plt.ylabel("TxBytes")
plt.ticklabel_format(axis="y", style="sci", scilimits=(0,0))
#plt.legend()
plt.grid()
plt.savefig(f'mcd_{QPS}_txbytes_timeline.png')
