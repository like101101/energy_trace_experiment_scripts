	./run_mcd.sh runMCD
	python3 /home/like/like_trace/energy_trace_experiment_scripts/mcd/like/clean_mcd_linux.py /home/like/like_trace/energy_trace_experiment_scripts/mcd/like/current
	rm -r current
	wc -l mcd_symbio.csv
