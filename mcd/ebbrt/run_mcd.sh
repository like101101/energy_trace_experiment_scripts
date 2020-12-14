#! /bin/bash

export NITERS=${NITERS:='0'}
export SERVER=${SERVER:=192.168.1.230}
export OUTFILE=${OUTFILE:=0}
#export MQPS=${MQPS:='100000 200000 400000 600000 800000 900000'}
#export ITRS=${ITRS:-"100 200 400"}
#export MDVFS=${MDVFS:="0x1d00 0x1c00 0x1b00 0x1a00 0x1900 0x1800 0x1700 0x1600 0x1500 0x1400 0x1300 0x1200 0x1100 0x1000 0xf00 0xe00 0xd00 0xc00"}
#export MDVFS=${MDVFS:="0x1c00 0x1a00 0x1800 0x1600 0x1400 0x1200 0x1000 0xe00 0xc00"}
export MDVFS=${MDVFS:="0x1d00 0x1b00 0x1900 0x1700 0x1500 0x1300 0x1100 0xf00 0xd00"}
export MQPS=${MQPS:='200000 400000 600000'}
export ITRS=${ITRS:-"25 50 100 150 200"}
export MRAPL=${MRAPL:-"135 95 55"}

currdate=`date +%m_%d_%Y_%H_%M_%S`

function runMutilateBench
{
    timeout 300 python3 -u mutilate_bench.py "$@"
}

function reboot
{
    echo "reboot"
    ssh handong@10.255.0.1 hil node power cycle neu-5-9
    ssh 192.168.1.11 pkill mutilate
    ssh 192.168.1.37 pkill mutilate
    ssh 192.168.1.38 pkill mutilate
    ssh 192.168.1.104 pkill mutilate
    ssh 192.168.1.106 pkill mutilate
    ssh 192.168.1.107 pkill mutilate
    sleep 600
    success=1
    if alive; then
	success=0
    fi
    return $success

}

function alive
{
    output=$(ping -c 3 192.168.1.9 | grep "3 received")
    if [[ ${#output} -ge 1 ]]; then
	return 0
    else
	return 1
    fi
}

function runEbbRT
{
    echo "runEbbRT"
    echo "DVFS ${MDVFS}"
    echo "ITRS ${ITRS}"
    echo "MRAPL ${MRAPL}"
    echo "NITERS ${NITERS}"
    echo "MQPS ${MQPS}"
    echo "mkdir ${currdate}"
    mkdir ${currdate}
    mkdir "${currdate}_sla_violations"
    
    for dvfs in ${MDVFS}; do
	for itr in $ITRS; do
	    for qps in ${MQPS}; do	    
		for r in ${MRAPL}; do
		    for nrepeat in `seq 0 1 $NITERS`; do
			# try two times
			for rerun in `seq 0 1 1`; do
			    sleep 1
			    runBench=1
			    benchSuccess=1
			    
			    if alive; then
				echo "alive ${rerun}"
				runBench=0
			    else
				echo "dead ${rerun}"

				if reboot; then
				    if alive; then
					## preload fb_key and fb_value
					ssh 192.168.1.11 /app/mutilate/mutilate --binary -s 192.168.1.9 --loadonly -K fb_key -V fb_value
					sleep 1
					ssh 192.168.1.11 /app/mutilate/mutilate --binary -s 192.168.1.9 --loadonly -K fb_key -V fb_value
					sleep 1
					ssh 192.168.1.11 /app/mutilate/mutilate --binary -s 192.168.1.9 --loadonly -K fb_key -V fb_value
					sleep 1
					ssh 192.168.1.11 /app/mutilate/mutilate --binary -s 192.168.1.9 --loadonly -K fb_key -V fb_value
					sleep 1
					## warmup run
					runMutilateBench --os ebbrt --bench mcd --qps 50000 --time 10 --itr 50 --rapl 135 --dvfs 0x1d00 --nrepeat 0

					if alive; then
					    ssh 192.168.1.11 pkill mutilate
					    ssh 192.168.1.37 pkill mutilate
					    ssh 192.168.1.38 pkill mutilate
					    ssh 192.168.1.104 pkill mutilate
					    ssh 192.168.1.106 pkill mutilate
					    ssh 192.168.1.107 pkill mutilate
					    runBench=0
					fi
				    fi				    
				    
				    echo "reboot success ${rerun}"
				fi
			    fi
			    
			    if [[ ${runBench} -eq 0  ]]; then		
				echo "runMutilateBench --os ebbrt --bench mcd --qps ${qps} --time 20 --itr ${itr} --rapl ${r} --dvfs ${dvfs} --nrepeat ${nrepeat}"
				runMutilateBench --os ebbrt --bench mcd --qps ${qps} --time 20 --itr ${itr} --rapl ${r} --dvfs ${dvfs} --nrepeat ${nrepeat}
				sleep 1
				if alive; then
				    rritr=$(( ${itr}*2 ))
				    output=$(wc -c "ebbrt_out.${nrepeat}_${rritr}_${dvfs}_${r}_${qps}" | awk '{print $1}')
				    if (( $output > 100)); then
					echo "filesize == ${output} good"
					read_99th=$(sed -n 2p "ebbrt_out.${nrepeat}_${rritr}_${dvfs}_${r}_${qps}" | awk '{ print $10 }')
				        read_99th_int=${read_99th%.*}

					if (( $read_99th_int <= 500 )); then
					    benchSuccess=0
					else
					    echo "ebbrt_out.${nrepeat}_${rritr}_${dvfs}_${r}_${qps} read_99=${read_99th_int} > 500, skipping log data"
					    mv "ebbrt_out.${nrepeat}_${rritr}_${dvfs}_${r}_${qps}" "${currdate}_sla_violations/"
					    pkill socat
					    break
					fi
					
				    else
					echo "filesize == ${output} bad, rebooting"
					rm "ebbrt_out.${nrepeat}_${rritr}_${dvfs}_${r}_${qps}"
					reboot
				    fi
				fi
			    fi

			    ritr=$(( ${itr}*2 ))
			    if [[ ${benchSuccess} -eq 0  ]]; then
				echo "rdtsc,0" | socat - TCP4:192.168.1.9:5002 > ebbrt_rdtsc.${nrepeat}_${ritr}_${dvfs}_${r}_${qps}
				for c in `seq 0 1 15`; do
				    echo "get,$c" | socat - TCP4:192.168.1.9:5002 > ebbrt_dmesg.${nrepeat}_${c}_${ritr}_${dvfs}_${r}_${qps}
				    sleep 1
				    ./parse_ebbrt_mcd ebbrt_dmesg.${nrepeat}_${c}_${ritr}_${dvfs}_${r}_${qps} > "ebbrt_dmesg.${nrepeat}_${c}_${ritr}_${dvfs}_${r}_${qps}.csv"
				    sleep 1
				    rm -f ebbrt_dmesg.${nrepeat}_${c}_${ritr}_${dvfs}_${r}_${qps}
				    mv ebbrt_* ${currdate}/
				    sleep 1
				done
				
				if alive; then
				    echo "FINISHED: ebbrt_out.${nrepeat}_${ritr}_${dvfs}_${r}_${qps}"
				    break
				else
				    echo "**** ebbrt_dmesg.${nrepeat}_${ritr}_${dvfs}_${r}_${qps} get log error"
				fi				
			    else
				echo "**** ebbrt_dmesg.${nrepeat}_${ritr}_${dvfs}_${r}_${qps} ran out of memory error"
			    fi

			    echo "rerun == ${rerun}"
			done
    		    done
		done
	    done
	done

    done
}

function runEbbRTpart
{
    ITRS="1 5 10 15 20" MRAPL="135 75 55" NITERS="0" runEbbRT
    
    #MDVFS="0xd00" ITRS="25" MQPS="200000" MRAPL="55" NITERS="5" runEbbRT
    #MDVFS="0xd00" ITRS="25" MQPS="400000" MRAPL="95" NITERS="5" runEbbRT
    #MDVFS="0xd00" ITRS="25" MQPS="600000" MRAPL="95" NITERS="5" runEbbRT
    
    
    #MDVFS="0x1d00 0x1b00 0x1900 0x1700 0x1500 0x1300 0x1100 0xf00 0xd00" ITRS="25 50 100 150 200" MQPS="200000 400000 600000" MRAPL="135 95 55" NITERS="2" runEbbRT
    #sleep 1
    
    #MDVFS="0x1d00 0x1500 0xd00" ITRS="25 100 200" MQPS="800000 1000000 1200000 1400000 1600000 1800000 20000000 2200000" MRAPL="135" NITERS="2" runEbbRT
    #sleep 1
    
    #MDVFS="0xd00" ITRS="200" MQPS="200000" MRAPL="95" NITERS="2" runEbbRT
    #sleep 1
    
    #1168  ebbrt  0  300   0xd00    55  399808.8  30.0  1471.96  87511310887  ...      72.2       90.8      209.0      321.3      338.8      367.7  2557001490897  2644005645403  400000
   # MDVFS="0xd00" ITRS="150" MQPS="400000" MRAPL="55" NITERS="2" runEbbRT
    
    #1197  ebbrt  0  400   0xd00   135  599700.3  30.00  1536.94   69879283987  ...      85.3      109.1      260.9      403.5      429.9      470.7   924088820357  1011092690510  600000
    #MDVFS="0xd00" ITRS="150" MQPS="600000" MRAPL="95" NITERS="2" runEbbRT
    #sleep 1

    #MDVFS="0x1d00 0x1900 0x1700 0x1300 0xf00 0xd00" ITRS="25 50 100 150 200" MQPS="800000 850000 900000 1000000" MRAPL="135 95 55" NITERS="0" runEbbRT
    #sleep 1

    #MDVFS="0x1d00 0x1700 0xf00" ITRS="2 4" MQPS="200000 400000 600000 800000" MRAPL="135 95 55" NITERS="0" runEbbRT
    #sleep 1    
}

function parseEbbRT
{
    for dvfs in ${MDVFS}; do
	for itr in $ITRS; do
	    for qps in ${MQPS}; do	    
		for r in ${MRAPL}; do
		    for nrepeat in `seq 0 1 $NITERS`; do			
			for c in `seq 0 1 15`; do
			    ritr=$(( ${itr}*2 ))
			    TFILE="ebbrt_dmesg.${nrepeat}_${c}_${ritr}_${dvfs}_${r}_${qps}"
			    if [[ -f ${TFILE} ]]; then				
				./parse_ebbrt_mcd ${TFILE} > "ebbrt_dmesg.${nrepeat}_${c}_${ritr}_${dvfs}_${r}_${qps}.csv"
				rm -f ${TFILE}
				echo "${TFILE} DONE"
			    else
				echo "${TFILE} does not exist"
			    fi
			    
			done				
		    done
		done
	    done
	done
    done

}

"$@"

