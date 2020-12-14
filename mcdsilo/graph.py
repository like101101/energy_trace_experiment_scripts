import pandas as pd
import numpy as np
import matplotlib.pylab as plt
import matplotlib
import os
import glob
import multiprocessing as mp
import sys

if len(sys.argv) != 2:
    print("graph.py <QPS>")
    exit()
QPS = int(sys.argv[1])

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
    #print(df_non0j['ref_cycles_diff'][:10])
    #print(df_non0j['timestamp_non0_diff'][:10])
    
    df_non0j['nonidle_frac_diff'] = df_non0j['ref_cycles_diff'] / df_non0j['timestamp_non0_diff']
    
    
    #
    #df['nonidle_timestamp_diff'] = df['refcyc_diff'] * TIME_CONVERSION_khz
    
    
    #df_non0j['nonidle_timestamp_diff'] = df_non0j['ref_cycles_diff'] * TIME_CONVERSION_khz
    #global_linux_tuned_df_non0j['nonidle_frac_diff'] = global_linux_tuned_df_non0j['nonidle_timestamp_diff'] / global_linux_tuned_df_non0j['timestamp_diff']
    #print(global_linux_tuned_df_non0j['nonidle_timestamp_diff'], global_linux_tuned_df_non0j['nonidle_timestamp_diff'].shape[0])
    #print(global_linux_tuned_df_non0j['timestamp_diff'], global_linux_tuned_df_non0j['timestamp_diff'].shape[0])
    return df, df_non0j


plt.rc('axes', labelsize=20)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=20)    # fontsize of the tick labels
plt.rc('ytick', labelsize=20)    # fontsize of the tick labels
plt.rc('legend', fontsize=20)    # legend fontsize
plt.rcParams['ytick.right'] = plt.rcParams['ytick.labelright'] = True
plt.rcParams['ytick.left'] = plt.rcParams['ytick.labelleft'] = False

plt.ion()

#QPS=200000

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
LINES = {'linux_default': '--',
          'linux_tuned': '-.',
          'ebbrt_tuned': ':'}
HATCHS = {'linux_default': 'o',
          'linux_tuned': '*',
          'ebbrt_tuned': 'x'}

df = pd.read_csv(workload_loc, sep=' ')
df = df[df['joules'] > 0]
df = df[df['read_99th'] < 501]
df['edp'] = df['joules'] * df['read_99th']

print(df.shape[0])
#plot 1: overview
#plt.figure()
fig, ax = plt.subplots(1)
ax.yaxis.set_label_position("right")
dld = df[(df['sys']=='linux_default') & (df['itr']==1) & (df['dvfs']=='0xffff') & (df['target_QPS'] == QPS)].copy()
dlt = df[(df['sys']=='linux_tuned')& (df['target_QPS'] == QPS)].copy()
det = df[(df['sys']=='ebbrt_tuned')& (df['target_QPS'] == QPS)].copy()
#dlt = df[(df['sys']=='linux_tuned') & (df['target_QPS'] == QPS)& (df['itr']!=1) & (df['dvfs']!='0xffff')].copy()
#det = df[(df['sys']=='ebbrt_tuned') & (df['target_QPS'] == QPS)& (df['itr']!=1) & (df['dvfs']!='0xffff')].copy()
#print(dld.shape[0], dlt.shape[0], det.shape[0])
#plt.title('Memcached-Silo 200K QPS')
plt.errorbar(det['joules'], det['read_99th'], fmt='x', label=LABELS[det['sys'].max()], c=COLORS['ebbrt_tuned'], alpha=1)
plt.errorbar(dlt['joules'], dlt['read_99th'], fmt='*', label=LABELS[dlt['sys'].max()], c=COLORS['linux_tuned'], alpha=1)
plt.errorbar(dld['joules'], dld['read_99th'], fmt='o', label=LABELS[dld['sys'].max()], c=COLORS['linux_default'], alpha=1)
for dbest in [dld, dlt, det]:
    b = dbest[dbest.edp==dbest.edp.min()].iloc[0]
    bjoules = b['joules']
    btail = b['read_99th']
    #print(b)
    plt.plot(bjoules,  btail, fillstyle='none', marker='o', markersize=15, c=COLORS[b['sys']])
plt.ylabel("99% Tail Latency (usecs)")
plt.xlabel("Energy Consumed (Joules)")
plt.grid()
plt.show()
plt.tight_layout()
plt.savefig(f'mcdsilo_{QPS}_overview.pdf')

## EDP
x_offset, y_offset = 0.01/5, 0.01/5
#plt.figure()
fig, ax = plt.subplots(1)
ax.yaxis.set_label_position("right")
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
    
    #markevery = range(1, 2)
    xxrange = np.arange(0, int(btime)+1, int(btime/10))
    yyrange = np.arange(0, int(bjoules)+1, int(bjoules/10))
    plt.errorbar(xxrange, yyrange, label=LABELS[dbest['sys'].max()], fmt=FMTS[dbest['sys'].max()], c=COLORS[dbest['sys'].max()])
    #plt.errorbar([0, btime], [0, bjoules], markevery=markevery, label=LABELS[dbest['sys'].max()], fmt=FMTS[dbest['sys'].max()], c=COLORS[dbest['sys'].max()])
    if dsys == 'linux_tuned':
        plt.text(x_offset + btime - 7, y_offset + bjoules + 14, f'({ditr}, {ddvfs}, {drapl})', fontsize=14)
    if dsys == 'ebbrt_tuned':
        plt.text(x_offset + btime - 7, y_offset + bjoules - 500, f'({ditr}, {ddvfs}, {drapl})', fontsize=14)

plt.xlabel("Time (secs)")
plt.ylabel("Energy Consumed (Joules)")
#plt.legend(loc='lower right')
plt.grid()
#99 tail subplot
metric_labels = ['99% Tail (us)']
N_metrics = len(metric_labels) #number of clusters
N_systems = 3 #number of plot loops
idx = np.arange(N_metrics) #one group per metric
width = 0.2

df_dict = {'linux_default': dld,
           'linux_tuned': dlt,
           'ebbrt_tuned': det}

data_dict = {}
a = plt.axes([.05, .6, .3, .3])

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
                 ha='center', va='bottom', size=14)
    counter += 1
    plt.xticks([])
    plt.yticks([])
    plt.xlabel('99% Tail (us)')
plt.show()
plt.tight_layout()
plt.savefig(f'mcdsilo_{QPS}_epp.pdf')

#bar plots
metric_labels = ['CPI', 'Instructions', 'Cycles', 'RxBytes', 'TxBytes', 'Interrupts', 'Halt']
N_metrics = len(metric_labels) #number of clusters
N_systems = 3 #number of plot loops

fig, ax = plt.subplots(1)

idx = np.arange(N_metrics-1) #one group per metric
width = 0.2

df_dict = {'linux_default': dld,
           'linux_tuned': dlt,
           'ebbrt_tuned': det}

data_dict = {}
cstates_all={}

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
    
    if 'ebbrt' in dsys:
        c_all = np.array([0, 0, 0, 0, int(b['c7'])])
    else:
        c_all=np.array([int(b['c1']), int(b['c1e']), int(b['c3']), int(b['c6']), int(b['c7'])])
    cstates_all[dsys]=c_all
    
    data_dict[dsys] = np.array([b['ref_cycles']/b['instructions'],
                                b['instructions'],
                                b['ref_cycles'],
                                b['rx_bytes'],
                                b['tx_bytes'],
                                b['num_interrupts']])

for dsys in ['linux_tuned', 'ebbrt_tuned', 'linux_default']:
    cstates_all[dsys] = cstates_all[dsys]/sum(cstates_all['linux_default'])
    #print(cstates_all[dsys])

counter = 0
last=0
for sys in data_dict: #normalize and plot
    data = data_dict[sys] / data_dict['linux_default']
    last=(idx + counter*width)[len(idx + counter*width)-1]
    ax.bar(idx + counter*width, data, width, label=LABELS[sys], color=COLORS[sys], edgecolor='black', hatch=HATCHS[sys])
    counter += 1

last = last+width
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    last = last + width
    bars=0
    for i in range(0, len(cstates_all[dsys])):
        llen=len(cstates_all[dsys])
        colors = plt.cm.BuPu(np.linspace(0, 1, llen))
        
        if 'linux_default' == dsys:
            colors = plt.cm.get_cmap('Blues', llen) #plt.cm.Blues(np.linspace(0, 1, len(cstates_all[dsys])))
        elif 'linux_tuned' == dsys:
            colors = plt.cm.get_cmap('Greens', llen) #plt.cm.Greens(np.linspace(0, 1, len(cstates_all[dsys])))
        else:
            colors = plt.cm.get_cmap('Reds', llen) #plt.cm.Reds(np.linspace(0, 1, len(cstates_all[dsys])))
            
        if i == 0:
            ax.bar(last, cstates_all[dsys][i], width=width, color=colors(i/llen), edgecolor='black', hatch=HATCHS[dsys])
        else:
            ax.bar(last, cstates_all[dsys][i], bottom=bars, width=width, color=colors(i/llen), edgecolor='black', hatch=HATCHS[dsys])
        bars = bars + cstates_all[dsys][i]

idx = np.arange(N_metrics) #one group per metric
ax.set_xticks(idx)
ax.set_xticklabels(metric_labels, rotation=15)
#plt.legend(loc='lower left')
plt.tight_layout()
plt.savefig(f'mcdsilo_{QPS}_barplot.pdf')

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
        frdtscname = f'{log_loc}/linux.mcdsilo.rdtsc.{i}_{itr}_{dvfs}_{rapl}_{qps}'
        frdtsc = open(frdtscname, 'r')
        for line in frdtsc:
            tmp = line.strip().split(' ')
            if int(tmp[2]) > START_RDTSC:                                
                START_RDTSC = int(tmp[2])                        
        frdtsc.close()

        fname = f'{log_loc}/linux.mcdsilo.dmesg.{i}_{core}_{itr}_{dvfs}_{rapl}_{qps}'
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

## joule timeline
#plt.figure()
fig, ax = plt.subplots(1)
ax.yaxis.set_label_position("right")
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    ddfn = ddfn[(ddfn['joules_diff'] > 0) & (ddfn['joules_diff'] < 3000)]
    plt.plot(ddfn['timestamp_non0'], ddfn['joules_diff'], HATCHS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
plt.xlabel("Time (secs)")
plt.ylabel("Energy Consumed (Joules)")
#plt.legend(loc='lower right')
plt.grid()
plt.tight_layout()
plt.savefig(f'mcdsilo_{QPS}_joules_timeline.png')

## nonidle timeline
#plt.figure()
fig, ax = plt.subplots(1)
ax.yaxis.set_label_position("right")
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    ddfn = ddfn[(ddfn['nonidle_frac_diff'] > 0) & (ddfn['nonidle_frac_diff'] < 1.1)]
    plt.plot(ddfn['timestamp_non0'], ddfn['nonidle_frac_diff'], FMTS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
plt.xlabel("Time (secs)")
plt.ylabel("Nonidle Time (%)")
plt.ylim((0, 1.01))
#plt.legend()
plt.grid()
plt.tight_layout()
plt.savefig(f'mcdsilo_{QPS}_nonidle_timeline.png')

## instructions timeline
#plt.figure()
fig, ax = plt.subplots(1)
ax.yaxis.set_label_position("right")
for dsys in ['linux_default', 'linux_tuned', 'ebbrt_tuned']:
    ddf = ddfs[dsys][0]
    ddfn = ddfs[dsys][1]
    ddfn = ddfn[(ddfn['instructions_diff'] > 0) & (ddfn['instructions_diff'] < 250000000)]
    plt.plot(ddfn['timestamp_non0'], ddfn['instructions_diff'], FMTS[dsys], label=LABELS[dsys], c=COLORS[dsys], alpha=0.5)
plt.xlabel("Time (secs)")
plt.ylabel("Instructions")
#plt.legend()
plt.grid()
plt.tight_layout()
plt.savefig(f'mcdsilo_{QPS}_instructions_timeline.png')
