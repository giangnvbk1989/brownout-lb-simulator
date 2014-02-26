#!/bin/bash

mkdir -p results

algs=( random RR weighted-RR theta-diff theta-diff-plus optimization SQF SQF-plus FRF equal-thetas FRF-EWMA predictive 2RC ctl-simplify equal-thetas-SQF optim-SQF )

for algorithm in "${algs[@]}"
do
    mkdir -p results/${algorithm}
    ./simulator.py --algorithm ${algorithm} --outdir results/${algorithm} $@ &
done
wait

echo
echo "Results sorted by algorithm:"
cat results/*/sim-final-results.csv | sort

echo
echo "Results sorted by performance:"
cat results/*/sim-final-results.csv | sort -t, -k2 -r

echo
echo "Results sorted by number of optional requests:"
(for algo in results/*; do
	printf "%-20s %10d %10d\n" \
		`echo $algo | cut -d/ -f2` \
		`tail -n1 $algo/sim-lb.csv | cut -d, -f22 | cut -d. -f1` \
		`tail -n1 $algo/sim-lb.csv | cut -d, -f23 | cut -d. -f1`;
done) | sort -rnk 3