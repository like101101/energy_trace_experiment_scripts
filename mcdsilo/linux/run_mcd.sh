#! /bin/bash

export RXU=${RXU:='8'}
export RXQ=${RXQ:='512'}
export TXQ=${TXQ:='512'}
export NITERS=${NITERS:='2'}
export SERVER=${SERVER:=192.168.1.230}
export OUTFILE=${OUTFILE:=0}
#export MQPS=${MQPS:='100000 200000 400000 600000 800000 900000'}
#export ITRS=${ITRS:-"100 200 400"}
#export MDVFS=${MDVFS:="0x1c00 0x1a00 0x1800 0x1600 0x1400 0x1200 0x1000 0xe00 0xc00"}
#export MDVFS=${MDVFS:="0x1d00 0x1c00 0x1b00 0x1a00 0x1900 0x1800 0x1700 0x1600 0x1500 0x1400 0x1300 0x1200 0x1100 0x1000 0xf00 0xe00 0xd00 0xc00"}
#export MRAPL=${MRAPL:-"135 125 115 105 95 85 75 65 55 45"}
#export MRAPL=${MRAPL:-"135 105 75 45"}

#export MDVFS=${MDVFS:="0x1d00 0x1b00 0x1900 0x1700 0x1500 0x1300 0x1100 0xf00 0xd00"}
export MDVFS=${MDVFS:="0x1d00 0x1c00 0x1b00 0x1a00 0x1900 0x1800"}
export MQPS=${MQPS:='50000 100000 200000'}
export ITRS=${ITRS:-"50 100 200 300 400"}
export MRAPL=${MRAPL:-"135 95 75 55"}

currdate=`date +%m_%d_%Y_%H_%M_%S`

function runMutilateBench
{
    timeout 600 python3 -u mutilate_bench.py "$@"
}

function runASPLOStest
{
    echo "runASPLOStest"
    
    #warm up
    runMutilateBench --bench mcd --qps 200000 --time 30 --itr 300 --rapl 135 --dvfs 0x1500 --nrepeat 0

    for itr in 300 400; do	    
	for qps in 200000 400000 600000; do	    	    
	    for r in 135 95 55; do	
		for i in `seq 0 1 $NITERS`; do
		    echo "runMutilateBench --bench mcd --qps ${qps} --time 20 --itr ${itr} --rapl ${r} --dvfs 0x1500 --nrepeat ${i}"
		    runMutilateBench --bench mcd --qps ${qps} --time 20 --itr ${itr} --rapl ${r} --dvfs 0x1500 --nrepeat ${i}
		    sleep 1
		done
	    done
	done
    done
    #   done
    
}

function runASPLOS
{
    echo "DVFS ${MDVFS}"
    echo "ITRS ${ITRS}"
    echo "MQPS ${MQPS}"
    echo "MRAPL ${MRAPL}"
    echo "NITERS ${NITERS}"

    #runASPLOStest
    
    for dvfs in ${MDVFS}; do
	for itr in $ITRS; do
	    for r in ${MRAPL}; do				
		for qps in ${MQPS}; do	    	    		
		    for i in `seq 0 1 $NITERS`; do
			echo "runMutilateBench --bench mcd --qps ${qps} --time 20 --itr ${itr} --rapl ${r} --dvfs ${dvfs} --nrepeat ${i}"
		        runMutilateBench --bench mcd --qps ${qps} --time 20 --itr ${itr} --rapl ${r} --dvfs ${dvfs} --nrepeat ${i}
			sleep 1
		    done
		done
	    done
	done
    done
}

function runASPLOSgov
{
    echo "runASPLOSitr"
    #echo "DVFS ${MDVFS}"
    #echo "ITRS ${ITRS}"
    echo "MQPS ${MQPS}"
    echo "MRAPL ${MRAPL}"
    echo "NITERS ${NITERS}"
    
    for qps in ${MQPS}; do	    	    
	for r in ${MRAPL}; do				
	    for i in `seq 0 1 $NITERS`; do
		echo "runMutilateBench --bench mcd --qps ${qps} --time 20 --rapl ${r} --nrepeat ${i}"
		runMutilateBench --bench mcd --qps ${qps} --time 20 --rapl ${r} --nrepeat ${i}
		sleep 1
	    done
	done
    done
}

"$@"

