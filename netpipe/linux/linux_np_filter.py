import re
import os
from os import path
import argparse

'''
dvfs = ["0x1500",
        "0x1600",
        "0x1700",
        "0x1800",
        "0x1900",
        "0x1a00",
        "0x1b00",
        "0x1c00",
        "0x1d00"]
'''

#dvfs = ["0x1900"]        
#linux_itrs = ["2 4 6 8 10 12 14 16 18 20 24 28 30 38 60 80"]
#msgs = ["8192"]
#iters = 3
#core = '1'

parser = argparse.ArgumentParser()
parser.add_argument("--rapl", help="Rapl power limit", required=True)
parser.add_argument("--dvfs", help="Cpu frequency [0x1D00 ... 0xC00]", required=True)
parser.add_argument("--itr", help="Static interrupt delay [10, 1000]", required=True)
parser.add_argument("--msg", help="message sizes [64, 8192, 65536, 524288]", required=True)
parser.add_argument("--core", help="0 to NPROC", type=int, required=True)
parser.add_argument("--iterations", help="repeat value", type=int, required=True)
parser.add_argument("--dir", help="directory to read and put filtered output", required=True)

args = parser.parse_args()

rapl=args.rapl
dvfs=args.dvfs
itrs=args.itr
msgs=args.msg
core=args.core
iters=args.iterations
dir=args.dir

print(args)

for i in range(0, iters):
    for msg in msgs.split(' '):
        for itr in itrs.split(' '):
            for d in dvfs.split(' '):
                for r in rapl.split(' '):
                    fname = dir+'/linux.np.log.'+str(i)+'_'+str(core)+'_'+msg+'_5000_'+str(itr)+'_'+d+'_'+r
                    fnpserver = dir+'/linux.np.server.'+str(i)+'_'+str(core)+'_'+msg+'_5000_'+str(itr)+'_'+d+'_'+r
                    fnpout = dir+'/linux.np.client.'+str(i)+'_'+str(core)+'_'+msg+'_5000_'+str(itr)+'_'+d+'_'+r
                    fdmesg = dir+'/linux.np.log.'+str(i)+'_'+str(core)+'_'+msg+'_5000_'+str(itr)+'_'+d+'_'+r+'.csv'
                    
                    if not path.exists(fname):
                        print(fname, "doesn't exist?")
                        exit()
                    if not path.exists(fnpserver):
                        print(fnpserver, "doesn't exist?")
                        exit()
                    if not path.exists(fnpout):
                        print(fnpout, "doesn't exist?")
                        exit()
                
                    tput = 0.0
                    lat = 0.0
                    f = open(fnpout, 'r')
                    for line in f:
                        tmp = list(filter(None, line.strip().split(' ')))
                        tput = float(tmp[1])
                        break
                    f.close()                

                    f = open(fnpserver, 'r')
                    START_RDTSC = 0
                    END_RDTSC = 0
                    pk0j = 0.0
                    pk1j = 0.0
                    for line in f:
                        if 'WORKLOAD' in line.strip():
                            tmp = list(filter(None, line.strip().split(' ')))
                            START_RDTSC = int(tmp[1])
                            END_RDTSC = int(tmp[2])
                            pk0j = float(tmp[3])
                            pk1j = float(tmp[4])
                            break
                    f.close()

                    #fw = open('linux.out.'+str(i)+'_'+msg+'_5000_'+str(itr)+'_'+my_dict[d]+'_135.csv', 'w')
                    #fw.write(str(tput)+' '+str(pk0j)+' '+str(pk1j)+' '+str(START_RDTSC)+' '+str(END_RDTSC)+'\n')
                    #fw.close()                                
                
                    #print("i rx_desc rx_bytes tx_desc tx_bytes instructions cycles llc_miss joules timestamp")
                    
                    print(fdmesg)             
                    f = open(fname)
                    fw = open(fdmesg, 'w')
                    fw.write('i rx_desc rx_bytes tx_desc tx_bytes instructions cycles ref_cycles llc_miss c3 c6 c7 joules timestamp\n')
                    for line in f:
                        tmp2 = line.strip().split(' ')
                        if 'i' not in line.strip():
                            if int(tmp2[len(tmp2)-1]) > START_RDTSC and int(tmp2[len(tmp2)-1]) < END_RDTSC:
                                fw.write(line.strip()+'\n')
                    f.close()
                    fw.close()

