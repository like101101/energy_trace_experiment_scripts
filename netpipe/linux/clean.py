import re
import os
from os import path

my_dict = {
    "0xc00": "0xC00",
    "0xf00" : "0xF00",
    "0x1000": "0x1000", 
    "0x1100": "0x1100",
    "0x1200": "0x1200",
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

dvfs = ["0xc00",
#        "0xd00",
#        "0xe00",
        "0xf00",
        "0x1000",
        "0x1100",
        "0x1200",
#        "0x1300",
#        "0x1400",
        "0x1500",
        "0x1600",
        "0x1700",
        "0x1800",
        "0x1900",
        "0x1a00",
        "0x1b00",
        "0x1c00",
        "0x1d00"]

ebbrt_dvfs = ["0xC00",
#        "0xD00",
#        "0xE00",
        "0xF00",
        "0x1000",
        "0x1100",
        "0x1200",
#        "0x1300",
#        "0x1400",
        "0x1500",
        "0x1600",
        "0x1700",
        "0x1800",
        "0x1900",
        "0x1A00",
        "0x1B00",
        "0x1C00",
        "0x1D00"]

linux_itrs = ["1", "0", "4", "6", "8", "12", "16", "20", "24", "28", "32", "36", "40", "60", "80"]
ebbrt_itrs = ["6", "8", "12", "16", "20", "24", "28", "32", "36", "40", "60", "80"]
msgs = ["64", "8192", "65536", "524288"]
iters = 10

for i in range(0, iters):
    for msg in msgs:
        for itr in linux_itrs:
            for d in reversed(dvfs):
                fname = 'dmesg_devicelog.'+str(i)+'_'+msg+'_5000_'+str(itr)+'_'+d+'_135'
                fnpserver = 'np.server.'+str(i)+'_'+msg+'_5000_'+str(itr)+'_'+d+'_135'
                fnpout = 'np.out.'+str(i)+'_'+msg+'_5000_'+str(itr)+'_'+d+'_135'
                fdmesg = 'linux.dmesg.'+str(i)+'_'+msg+'_5000_'+str(itr)+'_'+my_dict[d]+'_135.csv'
                
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

                fw = open('linux.out.'+str(i)+'_'+msg+'_5000_'+str(itr)+'_'+my_dict[d]+'_135.csv', 'w')
                fw.write(str(tput)+' '+str(pk0j)+' '+str(pk1j)+' '+str(START_RDTSC)+' '+str(END_RDTSC)+'\n')
                fw.close()                                
                
                #print("i rx_desc rx_bytes tx_desc tx_bytes instructions cycles llc_miss joules timestamp")
                print(fdmesg)
                f = open(fname)
                fw = open(fdmesg, 'w')
                for line in f:
                    tmp = line.strip().split(']')
                    tmp2=tmp[1][1:].split(' ')
                    if 'i' not in line.strip():                        
                        if int(tmp2[len(tmp2)-1]) > START_RDTSC and int(tmp2[len(tmp2)-1]) < END_RDTSC:
                            fw.write(tmp[1][1:]+'\n')
                f.close()
	        fw.close()                
