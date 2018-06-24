#! /usr/bin/env python3
# -*- coding: utf-8 -*-

'''			digital filter for baseflow seperation
--------------------------------------------------------------------
	:: q[t] = β*q[t-1] + 0.5*(1 + β)*(Q[t] -Q[t-1])

	:: q[t] = β*q[t-1] + c*(Q[t] -Q[t-1])--------(1)

	:: bf[t] = Q[t] - q[t]-----------------------(2)

c = 0.5*(1 + β)

filter param β = 0.925

initial condition q[0] = 0.5*Q[0]

3 passes, forward pass, backward pass, forward pass

references:
 - J.G. Arnold and P.M Allen. 
Automated methods for estimating baseflow and groundwater recharge 

Nazmul Ahasan
nzahasan@gmail.com
-----------------------------------------------------------------'''

import sys

def read_csv(fname,header=1,date_col=0,flow_col=1):

	dates = []
	Q = []

	with open(fname) as csv_file:
		f_data = csv_file.readlines()[header:]

		# remove tailing line of csv file
		if len(f_data[-1].split(","))<2:
			f_data = f_data[:-1]

		for i in range(len(f_data)):
			if len(f_data[i].split(',')) <2:
				print("Error in csv data at line ",i+2)
				sys.exit(100)

			dates.insert( i, f_data[i].split(',')[date_col] )
			Q.insert(i, float( f_data[i].split(',')[flow_col].replace('\n','').replace('\r','') ) )
		
	return dates,Q

def make_csv(dates,baseq):
	csv = 'Date,First-pass,Second-pass,Third-pass\n'
	
	if len(baseq)<3:
		if len(baseq[0])==0:
			if len(baseq[1])==0:
				if len(baseq[2])==0:
					if len(baseq[0])!= len(baseq[1]) and len(baseq[0])!= len(baseq[2]):
						print('Invalid baseflow data passed to csv maker.')
						sys.exit(200)
	
	for i in range(len(baseq[0])):
		csv += dates[i]+','+str(baseq[0][i])+','+str(baseq[2][i])+','+str(baseq[2][i])+'\n'
	
	return csv

def main():

	if len(sys.argv) < 2:
		print('Provide flow data csv file.')
		sys.exit(300)

	dates,Q = read_csv(str(sys.argv[1]))
	
	b = 0.925
	c = 0.5*(1 + b)

	surfq = [0] * len(Q)
	baseq = [ [0]*len(Q),[0]*len(Q),[0]*len(Q)]


	# first pass: forward 
	
	surfq[0] = 0.5*Q[0]
	baseq[0][0] =Q[0] - surfq[0]
	
	for t in range(1,len(Q),1):

		surfq[t] = b*surfq[t-1] + c*(Q[t] -Q[t-1])
		
		if surfq[t] < 0: surfq[t] = 0
		
		baseq[0][t] = Q[t] - surfq[t]
		
		if baseq[0][t] <0: baseq[0][t] = 0
		if baseq[0][t] > Q[t]: baseq[0][t] = Q[t]
		

	# second pass: backward pass
	
	baseq[1][len(Q)-1] = baseq[0][len(Q)-1]

	for t in range(len(Q)-2,-1,-1):

		surfq[t] = b*surfq[t+1] + c*(baseq[0][t] - baseq[0][t+1])
		
		if surfq[t] < 0: surfq[t]=0
		
		baseq[1][t] = baseq[0][t]-surfq[t]
		
		if baseq[1][t] <0: baseq[1][t]=0
		if baseq[1][t] > baseq[0][t]: baseq[1][t]=baseq[0][t]
		# print(t)

	# third pass: forward

	baseq[2][0] = baseq[1][0]

	for t in range(1,len(Q),1):
		surfq[t] = b*surfq[t-1] + c*( baseq[1][t] - baseq[1][t-1] )

		if surfq[t] < 0: surfq[t]=0

		baseq[2][t] = baseq[1][t] - surfq[t]

		if baseq[2][t] < 0: baseq[2][t]=0
		if baseq[2][t] > baseq[1][t]: baseq[2][t]=baseq[1][t]

	# save data
	with open('Baseflow_Data.csv','w') as csvFile:
		csvFile.write(make_csv(dates,baseq))
	
	return 0

if __name__ == '__main__':
	main()
