import re
import os
from os import path
import sys

print(len(sys.argv), sys.argv)
if len(sys.argv) != 5:
    print("clean.py itr dvfs rapl dvfs")
    exit()
'''
dvfs = ["0xd00",
        "0xf00",
        "0x1100",
        "0x1300",
        "0x1500",
        "0x1700",
        "0x1900",
        "0x1b00",
        "0x1d00"]

itrs = ["4", "6", "8", "12", "16", "20", "24", "28", "32", "36", "40", "80"]
rapls = ["135", "95", "55"]
'''
dvfs = []
itrs = []
rapls = []
qpss = []

itrs.append(sys.argv[1])
dvfs.append(sys.argv[2])
rapls.append(sys.argv[3])
qpss.append(sys.argv[4])

iters = 10
TIME_CONVERSION_khz = 1./(2899999*1000)
JOULE_CONVERSION = 0.00001526
    
#fwh = open('linux_nodejs_all.csv', 'a+')
#fwh.write("sys i itr dvfs rapl lat50 lat75 lat90 lat99 Request Time Joule total_ins total_cyc total_refcyc total_llcm c3 c6 c7\n")
#fwh.write("sys i itr dvfs rapl qps time joule ins cyc refcyc llcm c3 c6 c7 total_c_states\n")
print("sys i core itr dvfs rapl qps time joule ins cyc refcyc llcm c3 c6 c7")

for rapl in rapls:
    for itr in itrs:
        for d in reversed(dvfs):
            for qps in qpss:
                for i in range(0, iters):
                    fname = 'mcd_dmesg.'+str(i)+'_1_'+itr+'_'+d+'_'+rapl+'_'+qps
                    if not path.exists(fname):
                        print(fname, "doesn't exist?")
                    else:
                        print(fname)
                        frtdsc = open('mcd_rdtsc.'+str(i)+'_'+itr+'_'+d+'_'+rapl+'_'+qps, 'r')
                        START_RDTSC = 0
                        END_RDTSC = 0
                        for line in frtdsc:
                            tmp = line.strip().split(' ')
                            if int(tmp[2]) > START_RDTSC:                                
                                START_RDTSC = int(tmp[2])

                            if END_RDTSC == 0:                                
                                END_RDTSC = int(tmp[3])
                            elif END_RDTSC < int(tmp[3]):
                                END_RDTSC = int(tmp[3])                                                            
                        frtdsc.close()
                        tdiff = round(float((END_RDTSC - START_RDTSC) * TIME_CONVERSION_khz), 2)
                        
                        print(START_RDTSC, END_RDTSC, round(float((END_RDTSC - START_RDTSC) * TIME_CONVERSION_khz), 2))
                        cc = 0
                        startj = 0
                        endj = 0
                        total_ins = 0
                        total_cyc = 0
                        total_refcyc = 0
                        total_llcm = 0
                        prevj = 0
                        
                        ins = 0
                        cyc = 0
                        refcyc = 0
                        llcm = 0
                        
                        eins = 0
                        ecyc = 0
                        erefcyc = 0
                        ellcm = 0
                        ec3 = 0
                        ec6 = 0
                        ec7 = 0
                        
                        total_c3 = 0
                        total_c6 = 0
                        total_c7 = 0
                        
                        c3 = 0
                        c6 = 0
                        c7 = 0
                        
                        f = open(fname)
                        #fname2 = 'linux.dmesg.'+str(i)+'_1_'+itr+'_'+d+'_'+rapl+'_'+qps+'.csv'
                        #fw = open(fname2, 'w')
                        #print("i rxdesc rxbytes txdesc txbytes ins cyc refcyc llcm C3 C6 C7 JOULE TSC")                  
                        #fw.write("i rxdesc rxbytes txdesc txbytes ins cyc refcyc llcm C3 C6 C7 JOULE TSC\n")
                        for line in f:
                            tmp = list(filter(None, line.strip().split(' ')))
                            if len(tmp) > 5 and 'i' not in line.strip():
                                tmp2 = list(filter(None, line.strip().split(']')))
                                tmp3 = list(filter(None, tmp2[1].strip().split(' ')))                            
                            
                                if int(tmp3[13]) > START_RDTSC and int(tmp[13]) < END_RDTSC and int(tmp3[5]) > 0 and int(tmp3[6]) > 0 and int(tmp3[7]) > 0 and int(tmp3[8]) > 0:
                                    joules = int(tmp3[12])
                                    if joules > 0:
                                        fw.write(' '.join(tmp3).strip()+'\n')
                                        if prevj == 0:
                                            prevj = joules
                                        elif prevj > 0 and joules < prevj:
                                            joules = joules + prevj
                                        
                                    if cc == 0 and joules > 0:
                                        startj =  joules
                                        ins = int(tmp3[5])
                                        cyc = int(tmp3[6])
                                        refcyc = int(tmp3[7])
                                        llcm = int(tmp3[8])
                                        c3 = int(tmp3[9])
                                        c6 = int(tmp3[10])
                                        c7 = int(tmp3[11])
                                        cc = 1                                    
                                    elif cc == 1 and joules > 0:
                                        endj = joules
                                        eins = int(tmp3[5])
                                        ecyc = int(tmp3[6])
                                        erefcyc = int(tmp3[7])
                                        ellcm = int(tmp3[8])
                                        ec3 = int(tmp3[9])
                                        ec6 = int(tmp3[10])
                                        ec7 = int(tmp3[11])
                                        
                                    if ins > 0 and int(tmp3[5]) > ins:
                                        total_ins = total_ins + (int(tmp3[5]) - ins)
                                        ins = int(tmp3[5])
                                    if cyc > 0 and int(tmp3[6]) > cyc:
                                        total_cyc = total_cyc + (int(tmp3[6]) - cyc)
                                        cyc = int(tmp3[6])
                                    if refcyc > 0 and int(tmp3[7]) > refcyc:
                                        total_refcyc = total_refcyc + (int(tmp3[7]) - refcyc)
                                        refcyc = int(tmp3[7])    
                                    if llcm > 0 and int(tmp3[8]) > llcm:
                                        total_llcm = total_llcm + (int(tmp3[8]) - llcm)
                                        llcm = int(tmp3[8])
                                    if c3 > 0 and int(tmp3[9]) > c3:
                                        total_c3 = total_c3 + (int(tmp3[9]) - c3)
                                        c3 = int(tmp3[9])
                                    if c6 > 0 and int(tmp3[10]) > c6:
                                        total_c6 = total_c6 + (int(tmp3[10]) - c6)
                                        c6 = int(tmp3[10])
                                    if c7 > 0 and int(tmp3[11]) > c7:
                                        total_c7 = total_c7 + (int(tmp3[11]) - c7)
                                        c7 = int(tmp3[11])
                        f.close()
                        fw.close()
                        print("linux "+str(i)+" "+str(itr)+" "+str(d)+" "+str(rapl)+" "+str(qps)+" "+str(tdiff)+" "+str(round((JOULE_CONVERSION * (endj-startj)),2))+" "+str(total_ins)+" "+str(total_cyc)+" "+str(total_refcyc)+" "+str(total_llcm)+" "+str(total_c3)+" "+str(total_c6)+" "+str(total_c7)+" "+str(total_c3+total_c6+total_c7))
                        #fwh.write("linux "+str(i)+" "+str(itr)+" "+str(d)+" "+str(rapl)+" "+str(qps)+" "+str(tdiff)+" "+str(round((JOULE_CONVERSION * (endj-startj)),2))+" "+str(total_ins)+" "+str(total_cyc)+" "+str(total_refcyc)+" "+str(total_llcm)+" "+str(total_c3)+" "+str(total_c6)+" "+str(total_c7)+" "+str(total_c3+total_c6+total_c7)+"\n")
fwh.close()
