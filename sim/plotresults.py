#!/usr/bin/env python
import fnmatch
import os
import numpy as np
from pylab import *

def avg(a):
	if len(a) == 0:
		return float('nan')
	return sum(a) / len(a)

def aggregate(a, interval = 10, func = avg):
	ret = np.zeros(a.shape)
	for i in range(0, a.shape[0]):
		for j in range(0, a.shape[1]):
			ret[i,j] = func(a[i:i+interval,j])
	return ret

def main():
	replicas = 0
	for f in os.listdir('.'):
    		if fnmatch.fnmatch(f, 'sim-lb.csv'):
			data = np.genfromtxt(f, dtype=float, delimiter=',') 
		if fnmatch.fnmatch(f, 'sim-server*.csv'):
        		replicas += 1

	# parse data
	times = data[:,0]
	weights = data[:,1:replicas+1]
	dimmers = data[:,replicas+1:2*replicas+1]
	avg_latencies = data[:,2*replicas+1:3*replicas+1]
	max_latencies = data[:,3*replicas+1:4*replicas+1]
	total_requests = data[:,4*replicas+1]
	optional_requests = data[:,4*replicas+2]
	effective_weights = data[:,4*replicas+3:5*replicas+3]

	# make plots more readable
	max_latencies = aggregate(max_latencies, func = max)
	effective_weights = aggregate(effective_weights)
	
	subplot(3, 2, 1)
	plot(times, weights)
	title("Weights")
	subplot(3, 2, 2)
	plot(times, dimmers)
	title("Dimmers")
	subplot(3, 2, 3)
	plot(times, max_latencies)
	title("Max latencies")
	subplot(3, 2, 4)
	plot(times, optional_requests/total_requests)
	title("Percentage recommendations")
	subplot(3, 2, 5)
	plot(times, effective_weights)
	title("Effective weights")
	show()


if __name__ == "__main__":
	main()

