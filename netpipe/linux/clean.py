import re
import os
from os import path

my_dict = {
    "0x1500": "0x1500",
    "0x1600": "0x1600",
    "0x1700": "0x1700",
    "0x1800": "0x1800",
    "0x1900": "0x1900",
    "0x1a00" : "0x1A00",
    "0x1b00" : "0x1B00",
    "0x1c00" : "0x1C00",
    "0x1d00" : "0x1D00"
}

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

dvfs = ["0x1900"]        
linux_itrs = ["2 4 6 8 10 12 14 16 18 20 24 28 30 38 60 80"]
msgs = ["8192"]
iters = 3
core = '1'

for i in range(0, iters):
    for msg in msgs:
        for itr in linux_itrs[0].split(' '):
            for d in reversed(dvfs):
                fname = 'linux.np.log.'+str(i)+'_'+core+'_'+msg+'_5000_'+str(itr)+'_'+d+'_135'
                fnpserver = 'linux.np.server.'+str(i)+'_'+core+'_'+msg+'_5000_'+str(itr)+'_'+d+'_135'
                fnpout = 'linux.np.client.'+str(i)+'_'+core+'_'+msg+'_5000_'+str(itr)+'_'+d+'_135'
                fdmesg = 'linux.np.log.'+str(i)+'_'+core+'_'+msg+'_5000_'+str(itr)+'_'+d+'_135.csv'
                
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
                for line in f:
                    tmp2 = line.strip().split(' ')
                    if 'i' not in line.strip():                        
                        if int(tmp2[len(tmp2)-1]) > START_RDTSC and int(tmp2[len(tmp2)-1]) < END_RDTSC:
                            fw.write(line.strip()+'\n')
                f.close()
                fw.close()
