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
