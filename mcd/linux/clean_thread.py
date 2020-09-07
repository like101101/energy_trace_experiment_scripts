import re
import os
from os import path
import sys
import time

print(len(sys.argv), sys.argv)
if len(sys.argv) != 5:
    print("clean.py itr dvfs rapl qps")
    exit()

dvfs = []
itrs = []
rapls = []
qpss = []

itrs.append(sys.argv[1])
dvfs.append(sys.argv[2])
rapls.append(sys.argv[3])
qpss.append(sys.argv[4])

iters = 3
TIME_CONVERSION_khz = 1./(2899999*1000)
JOULE_CONVERSION = 0.00001526

read_5th = 0
read_10th = 0
read_50th = 0
read_90th = 0
read_95th = 0
read_99th = 0
START_RDTSC = 0
END_RDTSC = 0
tdiff = 0
mqps = 0
tins = 0
tcyc = 0
trefcyc = 0
tllcm = 0
tc3 = 0
tc6 = 0
tc7 = 0
tjoules = 0.0

#fwh = open('linux_nodejs_all.csv', 'a+')
#fwh.write("\nsys i itr dvfs rapl lat50 lat75 lat90 lat99 Request Time Joule total_ins total_cyc total_refcyc total_llcm c3 c6 c7\n")

def parseOut(i, itr, d, rapl, q):
    global read_5th
    global read_10th
    global read_50th
    global read_90th
    global read_95th
    global read_99th
    global mqps

    f = 'mcd_out.'+str(i)+'_'+itr+'_'+d+'_'+rapl+'_'+q
    #print(f)
    fout = open(f, 'r')
    for line in fout:
        if "Total QPS" in line:
            tmp = str(line.split("=")[1])
            mqps = float(tmp.strip().split(" ")[0])
        if "read" in line:
            alla = list(filter(None, line.strip().split(' ')))
            read_5th = float(alla[4])
            read_10th = float(alla[5])
            read_50th = float(alla[6])
            read_90th = float(alla[7])
            read_95th = float(alla[8])
            read_99th = float(alla[9])
                    
    fout.close()

def parseRdtsc(i, itr, d, rapl, q):
    global START_RDTSC
    global END_RDTSC
    global tdiff

    f = 'mcd_rdtsc.'+str(i)+'_'+itr+'_'+d+'_'+rapl+'_'+q
    #print(f)
    frtdsc = open(f, 'r')
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
                        
def parseLogs(i, core, itr, d, rapl, fname):
    global START_RDTSC
    global END_RDTSC
    global tdiff
    global read_5th
    global read_10th
    global read_50th
    global read_90th
    global read_95th
    global read_99th
    global mqps
    global tins
    global tcyc
    global trefcyc
    global tllcm
    global tc3
    global tc6
    global tc7
    global tjoules
    
    cc = 0
    startj = 0
    endj = 0
    total_ins = 0
    total_cyc = 0
    total_refcyc = 0
    total_llcm = 0
    prevj = 0
    sumj = 0
    
    ins = 0
    cyc = 0
    refcyc = 0
    llcm = 0
    
    total_c3 = 0
    total_c6 = 0
    total_c7 = 0
    
    c3 = 0
    c6 = 0
    c7 = 0
                    
    f = open(fname)
    for line in f:
        tmp = list(filter(None, line.strip().split(' ')))
        if len(tmp) > 5 and 'i' not in line.strip():
            tmp2 = list(filter(None, line.strip().split(']')))
            tmp3 = list(filter(None, tmp2[1].strip().split(' ')))                            
                            
            if int(tmp3[13]) > START_RDTSC and int(tmp[13]) < END_RDTSC and int(tmp3[5]) > 0 and int(tmp3[6]) > 0 and int(tmp3[7]) > 0 and int(tmp3[8]) > 0:
            #if int(tmp3[5]) > 0 and int(tmp3[6]) > 0 and int(tmp3[7]) > 0 and int(tmp3[8]) > 0:
                joules = int(tmp3[12])
                if joules > 0:
                    if prevj == 0:
                        prevj = joules
                    elif prevj > 0 and joules < prevj:
                        prevj = joules
                    elif prevj > 0 and joules >= prevj:
                        sumj += joules - prevj
                        prevj = joules
                                        
                    if cc == 0 and joules > 0:
                        #startj =  joules
                        ins = int(tmp3[5])
                        cyc = int(tmp3[6])
                        refcyc = int(tmp3[7])
                        llcm = int(tmp3[8])
                        c3 = int(tmp3[9])
                        c6 = int(tmp3[10])
                        c7 = int(tmp3[11])
                        cc = 1                                    
                    #elif cc == 1 and joules > 0:
                    #    endj = joules
                                        
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
    if core == 0 or core == 1: tjoules += (JOULE_CONVERSION * sumj)
    
    tins += total_ins
    tcyc += total_cyc
    trefcyc += total_refcyc
    tllcm += total_llcm
    tc3 += total_c3
    tc6 += total_c6
    tc7 += total_c7
    
    if core == 0 or core == 1:
        print("linux_core "+str(i)+" "+str(core)+" "+str(itr)+" "+str(d)+" "+str(rapl)+" "+str(mqps)+" "+str(tdiff)+" "+str(round(JOULE_CONVERSION * sumj,2))+" "+str(total_ins)+" "+str(total_cyc)+" "+str(total_refcyc)+" "+str(total_llcm)+" "+str(total_c3)+" "+str(total_c6)+" "+str(total_c7)+" "+str(read_5th)+" "+str(read_10th)+" "+str(read_50th)+" "+str(read_90th)+" "+str(read_95th)+" "+str(read_99th)+" "+str(START_RDTSC)+" "+str(END_RDTSC))
    else:
        print("linux_core "+str(i)+" "+str(core)+" "+str(itr)+" "+str(d)+" "+str(rapl)+" "+str(mqps)+" "+str(tdiff)+" "+str(0.0)+" "+str(total_ins)+" "+str(total_cyc)+" "+str(total_refcyc)+" "+str(total_llcm)+" "+str(total_c3)+" "+str(total_c6)+" "+str(total_c7)+" "+str(read_5th)+" "+str(read_10th)+" "+str(read_50th)+" "+str(read_90th)+" "+str(read_95th)+" "+str(read_99th)+" "+str(START_RDTSC)+" "+str(END_RDTSC))
        
    #print("linux "+str(i)+" "+str(core)+" "+str(itr)+" "+str(d)+" "+str(rapl)+" "+str(qps)+" "+str(tdiff)+" "+str(round((JOULE_CONVERSION * (endj-startj)),2))+" "+str(total_ins)+" "+str(total_cyc)+" "+str(total_refcyc)+" "+str(total_llcm)+" "+str(total_c3)+" "+str(total_c6)+" "+str(total_c7)+" "+str(total_c3+total_c6+total_c7))

    
print("sys i core itr dvfs rapl QPS time joule ins cyc refcyc llcm c3 c6 c7 read_5th read_10th read_50th read_90th read_95th read_99th RDTSC_START RDTSC_END")

for d in dvfs:
   for itr in itrs:
      for qps in qpss:
         for rapl in rapls:            
            for i in range(0, iters):
               START_RDTSC = 0
               END_RDTSC = 0
               tdiff = 0
               read_5th = 0
               read_10th = 0
               read_50th = 0
               read_90th = 0
               read_95th = 0
               read_99th = 0
               mqps = 0
               tins = 0
               tcyc = 0
               trefcyc = 0
               tllcm = 0
               tc3 = 0
               tc6 = 0
               tc7 = 0
               tjoules = 0
               
               check_done = True
               while check_done == True:
                  fname = 'mcd_dmesg.'+str(i)+'_'+str(15)+'_'+itr+'_'+d+'_'+rapl+'_'+qps
                  if path.exists(fname):
                     check_done = False
                  else:
                     time.sleep(300)
               
               for core in range(0, 16):
                  fname = 'mcd_dmesg.'+str(i)+'_'+str(core)+'_'+itr+'_'+d+'_'+rapl+'_'+qps
                                      
                  parseOut(i, itr, d, rapl, qps)
                  parseRdtsc(i, itr, d, rapl, qps)
                     
                  if START_RDTSC != 0:
                     parseLogs(i, core, itr, d, rapl, fname)
                  else:
                     print(fname, "RTDSC = 0")
                        
               print("linux "+str(i)+" "+str(itr)+" "+str(d)+" "+str(rapl)+" "+str(mqps)+" "+str(tdiff)+" "+str(round(tjoules,2))+" "+str(tins)+" "+str(tcyc)+" "+str(trefcyc)+" "+str(tllcm)+" "+str(tc3)+" "+str(tc6)+" "+str(tc7)+" "+str(read_5th)+" "+str(read_10th)+" "+str(read_50th)+" "+str(read_90th)+" "+str(read_95th)+" "+str(read_99th)+" "+str(START_RDTSC)+" "+str(END_RDTSC))
                    
                                
                    
