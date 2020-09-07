#! /bin/bash
export RXU=${RXU:='8'}

currdate=`date +%m_%d_%Y_%H_%M_%S`

export MRAPL=${MRAPL:-"135 115 95 75 55"}
export NITERS=${NITERS:='9'}
export MDVFS=${MDVFS:="0x1d00 0x1b00 0x1900 0x1700 0x1500 0x1300 0x1100 0xf00 0xd00"}
#export ITRS=${ITRS:-"4 6 8 12 16 20 24 28 32 36 40 80"}
export ITRS=${ITRS:-"4 6 8 12 16 20 24 28 32 36 40 80"}
export RITRS=${RITRS:-"1 2 3 4 6 8 10 12 14 16 18 20 40"}

#set -x
#ghzs="2.9 2.8 2.7 2.6 2.5 2.4 2.3 2.2 2.1 2.0 1.9 1.8 1.7 1.6 1.5 1.4 1.3 1.2"
#coms="com1 com512"
#taskset -c 1 ./wrk -t1 -c1 -d1s -H "Host: example.com \n Host: test.go Host: example.com \n  Host: example.com \n  Host: example.com \n  Host: example.com \n Host: example.com \n Host: example.com Host: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.com Host: example.comHost: example.com Host: example.com \n Host: test.go Host: example.com \n  Host: example.com \n  Host: example.com \n  Host: example.com \n Host: example.com \n Host: example.com Host: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.com Host: example.comHost: " http://192.168.1.230:6666/index.html --latency
#
function reboot
{
    echo "reboot"
    ssh handong@10.255.0.1 hil node power cycle neu-5-9
    sleep 1
    success=1
    for iwait in `seq 0 1 10`;
    do
        echo "reboot waiting ${iwait}"
	if alive; then
	    success=0
	    break	    
        fi
	sleep 60
    done

    return $success
}

function alive
{
    output=$(ping -c 3 192.168.1.200 | grep "3 received")
    if [[ ${#output} -ge 1 ]]; then
	return 0
    else
	return 1
    fi
}

function runEbbRT
{    
    for r in ${MRAPL}; do
	for itr in ${RITRS}; do	    
	    for dvfs in ${MDVFS}; do
		for nrepeat in `seq 0 1 ${NITERS}`; do		    
		    # try two times
			for rerun in `seq 0 1 1`; do
			    sleep 1
			    runBench=1
			    benchSuccess=1
			    
			    if alive; then
				echo "alive"
				runBench=0
			    else
				echo "dead"

				if reboot; then	    
				    runBench=0
				    echo "reboot success"
				fi
			    fi
			    
			    if [[ ${runBench} -eq 0  ]]; then
				echo "timeout 300 python3 -u nodejs_bench.py --os ebbrt --rapl ${r} --dvfs ${dvfs} --itr ${itr} --nrepeat ${i}"
				timeout 300 python3 -u nodejs_bench.py --os ebbrt --rapl ${r} --dvfs ${dvfs} --itr ${itr} --nrepeat ${nrepeat}
				if alive; then
				    benchSuccess=0
				fi
			    fi

			    ritr=$(( ${itr}*2 ))
			    if [[ ${benchSuccess} -eq 0  ]]; then
				echo "ebbrt_dmesg.${nrepeat}_${ritr}_${dvfs}_${r} success"
				echo "rdtsc,0" | socat - TCP4:192.168.1.200:5002 > ebbrt_rdtsc.${nrepeat}_${ritr}_${dvfs}_${r}
				echo ebbrt_rdtsc.${nrepeat}_${itr}_${dvfs}_${r}
				echo "get,1" | socat - TCP4:192.168.1.200:5002 > "ebbrt_dmesg.${nrepeat}_1_${ritr}_${dvfs}_${r}"
				
				if alive; then
				    ./parse_ebbrt_mcd "ebbrt_dmesg.${nrepeat}_1_${ritr}_${dvfs}_${r}" > "ebbrt_dmesg.${nrepeat}_1_${ritr}_${dvfs}_${r}.csv"
				    rm -f "ebbrt_dmesg.${nrepeat}_1_${ritr}_${dvfs}_${r}"
				    break
				else
				    echo "**** ebbrt_dmesg.${nrepeat}_${ritr}_${dvfs}_${r} get log error"
				fi				
			    else
				echo "**** ebbrt_dmesg.${nrepeat}_${ritr}_${dvfs}_${r} ran out of memory error"
			    fi

			    echo "rerun == ${rerun}"
			done
		done
	    done
	done
    done
}

function runASPLOS
{
    echo "DVFS ${MDVFS}"
    echo "ITRS ${ITRS}"
    echo "MRAPL ${MRAPL}"
    echo "NITERS ${NITERS}"
    
    for r in ${MRAPL}; do
	for itr in $ITRS; do	    
	    for dvfs in ${MDVFS}; do
		for i in `seq 0 1 ${NITERS}`; do
		    echo "timeout 300 python3 -u nodejs_bench.py --rapl ${r} --dvfs ${dvfs} --itr ${itr} --nrepeat ${i}"
		    timeout 300 python3 -u nodejs_bench.py --rapl ${r} --dvfs ${dvfs} --itr ${itr} --nrepeat ${i}
		    sleep 1
		done
	    done
	done
    done
}

function runASPLOSgov
{
    echo "MRAPL ${MRAPL}"
    echo "NITERS ${NITERS}"
    
    for r in ${MRAPL}; do
	for i in `seq 0 1 ${NITERS}`; do
	    echo "timeout 300 python3 -u nodejs_bench.py --rapl ${r} --dvfs 0xffff --itr 1 --nrepeat ${i}"
	    timeout 300 python3 -u nodejs_bench.py --rapl ${r} --nrepeat ${i}
	    sleep 1
	done
    done
}


function run
{
    for c in $coms;
    do
	for d in $ghzs;
	do
	    for r in `seq 136 -2 46`;
	    do	    
		timeout 120 python3 -u ./nodejs_bench.py --rapl $r --dvfs $d --com $c
	    done
	done
    done
}

function run2
{
    for i in `seq 10 100 900`; # 8
    do
	for d in $ghzs; # 17
	do
	    for r in `seq 135 -8 46`; # 9
	    do	    
		timeout 120 python3 -u ./nodejs_bench.py --rapl $r --dvfs $d --com "com512" --itr $i
	    done
	done
    done
}


$1
