import re
import os
from os import path
import sys

print(len(sys.argv), sys.argv)
if len(sys.argv) != 4:
    print("clean.py itr dvfs rapl")
    exit()
    
dvfs = []
itrs = []
rapls = []

itrs.append(sys.argv[1])
dvfs.append(sys.argv[2])
rapls.append(sys.argv[3])

iters = 10
TIME_CONVERSION_khz = 1./(2899999*1000)
JOULE_CONVERSION = 0.00001526

#fwh = open('linux_nodejs_all.csv', 'a+')
#fwh.write("\nsys i itr dvfs rapl lat50 lat75 lat90 lat99 Request Time Joule total_ins total_cyc total_refcyc total_llcm c3 c6 c7\n")
print("sys i itr dvfs rapl lat50 lat75 lat90 lat99 requests time joule ins cyc refcyc llcm c3 c6 c7 START_RDTSC END_RDTSC")

for rapl in rapls:
    for itr in itrs:
        for d in reversed(dvfs):
            for i in range(0, iters):
                fname = 'node_dmesg.'+str(i)+'_1_'+itr+'_'+d+'_'+rapl
                if not path.exists(fname):
                    print(fname, "doesn't exist?")
                else:
                    #node_rdtsc.2_1_32_0x1700_135
                    
                    #print(fname)
                    
                    fout = open('node_out.'+str(i)+'_1_'+itr+'_'+d+'_'+rapl, 'r')
                    lat_us_50 = 0
                    lat_us_75 = 0
                    lat_us_90 = 0
                    lat_us_99 = 0
                    total_requests= 0
                    for line in fout:
                        if "50%" in line:
                            tmp = list(filter(None, line.strip().split(' ')))
                            lat_us_50 = float(tmp[1][0:len(tmp[1])-2])
                        if "75%" in line:
                            tmp = list(filter(None, line.strip().split(' ')))
                            lat_us_75 = float(tmp[1][0:len(tmp[1])-2])
                        if "90%" in line:
                            tmp = list(filter(None, line.strip().split(' ')))
                            lat_us_90 = float(tmp[1][0:len(tmp[1])-2])
                        if "99%" in line:
                            tmp = list(filter(None, line.strip().split(' ')))
                            lat_us_99 = float(tmp[1][0:len(tmp[1])-2])
                        if "requests in" in line:
                            tmp = list(filter(None, line.strip().split(' ')))
                            total_requests = int(tmp[0])
                        
                    fout.close()
                    
                    frtdsc = open('node_rdtsc.'+str(i)+'_1_'+itr+'_'+d+'_'+rapl, 'r')
                    START_RDTSC = 0
                    END_RDTSC = 0
                    for line in frtdsc:
                        tmp = line.strip().split(' ')
                        START_RDTSC = int(tmp[1])
                        END_RDTSC = int(tmp[2])
                        tdiff = round(float((END_RDTSC - START_RDTSC) * TIME_CONVERSION_khz), 2)
                        if tdiff > 20 and tdiff < 40:
                            break
                    frtdsc.close()                                                            
            
                    if START_RDTSC == 0 or END_RDTSC == 0:
                        print("rtdsc == 0")
                        break
                    #print(START_RDTSC, END_RDTSC)
                    
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
                    #fname2 = 'linux.dmesg.'+str(i)+'_1_'+itr+'_'+d+'_'+rapl+'.csv'
                    #fw = open(fname2, 'w')
                    #print(fname2)
                    #i rxdesc rxbytes txdesc txbytes ins cyc refcyc llcm C3 C6 C7 JOULE TSC
                    #print("i rxdesc rxbytes txdesc txbytes ins cyc refcyc llcm C3 C6 C7 JOULE TSC")                  
                    #fw.write("i rxdesc rxbytes txdesc txbytes ins cyc refcyc llcm C3 C6 C7 JOULE TSC\n")
                    for line in f:
                        tmp = list(filter(None, line.strip().split(' ')))
                        if len(tmp) > 5 and 'i' not in line.strip():
                            tmp2 = list(filter(None, line.strip().split(']')))
                            tmp3 = list(filter(None, tmp2[1].strip().split(' ')))
                            if int(tmp3[13]) > START_RDTSC and int(tmp3[13]) < END_RDTSC and int(tmp3[5]) > 0 and int(tmp3[6]) > 0 and int(tmp3[7]) > 0 and int(tmp3[8]) > 0:
                                joules = int(tmp3[12])
                                if prevj == 0:
                                    prevj = joules
                                elif prevj > 0 and joules < prevj:
                                    prevj = joules
                                elif prevj > 0 and joules >= prevj:
                                    sumj += joules - prevj
                                    prevj = joules
                                        
                                if cc == 0 and joules > 0:
                                    ins = int(tmp3[5])
                                    cyc = int(tmp3[6])
                                    refcyc = int(tmp3[7])
                                    llcm = int(tmp3[8])
                                    c3 = int(tmp3[9])
                                    c6 = int(tmp3[10])
                                    c7 = int(tmp3[11])
                                    cc = 1
                                    
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
                    #fw.close()
                    
                    #fwh.write("linux "+str(i)+" "+str(itr)+" "+str(d)+" "+str(rapl)+" "+str(lat_us_50)+" "+str(lat_us_75)+" "+str(lat_us_90)+" "+str(lat_us_99)+" "+str(total_requests)+" "+str(tdiff)+" "+str(round((JOULE_CONVERSION * (endj-startj)),2))+" "+str(total_ins)+" "+str(total_cyc)+" "+str(total_refcyc)+" "+str(total_llcm)+" "+str(total_c3)+" "+str(total_c6)+" "+str(total_c7)+" "+str(total_c3/total_refcyc)+" "+str(total_c6/total_refcyc)+" "+str(total_c7/total_refcyc)+"\n")
                    print("linux "+str(i)+" "+str(itr)+" "+str(d)+" "+str(rapl)+" "+str(lat_us_50)+" "+str(lat_us_75)+" "+str(lat_us_90)+" "+str(lat_us_99)+" "+str(total_requests)+" "+str(round(tdiff, 2))+" "+str(round((JOULE_CONVERSION * sumj),2))+" "+str(total_ins)+" "+str(total_cyc)+" "+str(total_refcyc)+" "+str(total_llcm)+" "+str(total_c3)+" "+str(total_c6)+" "+str(total_c7), START_RDTSC, END_RDTSC)
                    #linux 0 4 0x1b00 135 79.0 81.0 84.0 91.0 371595 30.1 930.39 37135291094 81269751160 87290753449 54502371 2182221 0                    
                    #print("%s %2s %3s $4s" % {"linux", str(i), str(itr), str(d), str(rapl), str(lat_us_50), str(lat_us_75), str(lat_us_90), str(lat_us_99), str(total_requests), str(round(tdiff, 2)), str(round((JOULE_CONVERSION * (endj-startj)),2)), str(total_ins), str(total_cyc), str(total_refcyc), str(total_llcm), str(total_c3), str(total_c6), str(total_c7)})
#fwh.close()
            

            
