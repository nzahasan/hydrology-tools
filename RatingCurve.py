# /usr/bin/env python3

from scipy.optimize import minimize
import pylab as pl
import numpy as np
import sys
pl.style.use('ggplot')
np.warnings.filterwarnings('ignore')



class RatingCurve(object):
	
	'''	
							RATING CURVE GENERATION 
		--------------------------------------------------------------
		Generates raging curve for given Waterlevel and Discharge data
		uses scipy's bounded optimization method to determine parameter
		generates 5 set of parameter for best performing rating curves

	'''
	def __init__(self,obs_wl,obs_q,curve_type):
		self.obs_q  = obs_q	
		self.obs_wl = obs_wl


		# execution check
		self.fitExecute = False

		if self.checkData() == 0:
			self.dataOkay = True
		else:
			self.dataOkay = False
			print(f'ERROR: Invalid Data return code {self.checkData()}',)
			return

		self.type   = curve_type

		# multiplier constant
		self.c_min = 0
		self.c_max = 1000

		# water level at 0 discharge
		self.a_min = 0.1
		self.a_max = self.obs_wl.min()

		# exponent
		self.n_min = 0.001
		self.n_max = 10

		# breaking point for segmented rating curve
		self.bp_min = self.obs_wl.min()
		self.bp_max = self.obs_wl.max()

		# save curve detail in this vars
		self.RC = {}
		self.RC['mse']        = []
		self.RC['parameters'] = []

		
		


	def checkData(self):

		if self.obs_wl.shape[0] != self.obs_q.shape[0]:
			return -1
		elif not isinstance(self.obs_q,np.ndarray):
			return -2
		elif not isinstance(self.obs_wl,np.ndarray):
			return -3
		else:
			return 0

	def fit(self):

		if self.dataOkay !=True: 
			print('ERROR: Invalid data')
			return

		if self.type=="continuous":
			
			lower_bound = np.array((self.c_min,self.a_min,self.n_min))
			upper_bound = np.array((self.c_max,self.a_max,self.n_max ))

			p_bounds = np.column_stack((lower_bound,upper_bound))

			for i in range(10):
				initial_parameter = (lower_bound+upper_bound)*(i/10)
				optimizer = minimize(self.cont_rc_mse,
							initial_parameter,
							args=(self.obs_wl,self.obs_q),
							method='L-BFGS-B',
							bounds=p_bounds ,
							)
				self.RC['parameters'].append(optimizer.x)
				self.RC['mse'].append(self.cont_rc_mse(optimizer.x,self.obs_wl,self.obs_q))

			# sort based on mse
			sortedRC =  sorted(zip(self.RC['parameters'],self.RC['mse']),key=lambda pair: pair[1] ) 
			self.RC['parameters'] = [item[0] for item in sortedRC ]
			self.RC['mse']        = [item[1] for item in sortedRC ]

			print('Suggested Rating curves:-')
			for i in range(5):
				print(f'\n{i+1}) MSE: {self.RC["mse"][i]:.2f}')
				print(f'\t {self.RC["parameters"][i][0]:.2f}*(H - {self.RC["parameters"][i][1]:.2f})^{self.RC["parameters"][i][2]:.2f}' )
				
		elif self.type=="segmented":

			# __upper and lower bound for parameter__

			lower_bound = np.array(( 
			self.c_min,self.c_min,
			self.a_min,self.a_min,
			self.n_min,self.n_min,
			self.bp_min ))
		
			upper_bound = np.array(( 
				self.c_max,self.c_max,
				self.a_max,self.a_max,
				self.n_max,self.n_max,
				self.bp_max ))
			
			p_bounds = np.column_stack((lower_bound,upper_bound))
			# run 10 times with different initial guess
			 
			for i in range(10):
				initial_parameter = (lower_bound+upper_bound)*(i/10)
				optimizer = minimize(self.seg_rc_mse,
							initial_parameter,
							args=(self.obs_wl,self.obs_q),
							method='L-BFGS-B',
							bounds=p_bounds ,
							)
				self.RC['parameters'].append(optimizer.x)
				self.RC['mse'].append(self.seg_rc_mse(optimizer.x,self.obs_wl,self.obs_q))

			# sort based on mse
			sortedRC =  sorted(zip(self.RC['parameters'],self.RC['mse']),key=lambda pair: pair[1] ) 
			self.RC['parameters'] = [item[0] for item in sortedRC ]
			self.RC['mse']        = [item[1] for item in sortedRC ]
			
			print('Suggested Rating curves:-')
			for i in range(5):
				print(f'\n{i+1}) MSE: {self.RC["mse"][i]:.2f}')
				print(f'\t[H  < {self.RC["parameters"][i][-1]:.2f}] {self.RC["parameters"][i][0]:.2f}*(H - {self.RC["parameters"][i][2]:.2f})^{self.RC["parameters"][i][4]:.2f}' )
				print(f'\t[H >= {self.RC["parameters"][i][-1]:.2f}] {self.RC["parameters"][i][1]:.2f}*(H - {self.RC["parameters"][i][3]:.2f})^{self.RC["parameters"][i][5]:.2f}' )
			
		self.fitExecute = True

	def showPlot(self,rc_no):
		
		if self.fitExecute == False:
			print('ERROR: fit() has not been executed.')
			return

		pl.figure(figsize=(12,4))
		pl.plot(self.obs_q,label='Observed Q')
		
		if self.type=="continuous" and rc_no>0:
			print('cont capture')
			pl.plot(
				self.cont_rc(self.RC['parameters'][rc_no-1],self.obs_wl),
				label='Rating Q')

		elif self.type =="segmented" and rc_no>0:
			pl.plot(
				self.seg_rc(self.RC['parameters'][rc_no-1],self.obs_wl),
				label='Rating Q')
		elif rc_no <=0:
			print('Error: unable to find this curve no!')

		pl.title(f'Observed and Rating Curve Discharge, MSE {self.RC["mse"][rc_no-1]:.2f}')
		pl.legend() ; pl.axis('off')
		pl.show()
		pl.clf()
		

	def savePlot(self,rc_no,output_location):
		
		if self.fitExecute == False:
			print('ERROR: Execute fit() before saving plot.')
			return

		pl.figure(figsize=(12,4))
		pl.plot(self.obs_q,label='Observed Q')
		
		if self.type=="continuous" and rc_no>0:
			pl.plot(
				self.cont_rc(self.RC['parameters'][rc_no-1],self.obs_wl),
				label='Rating Q')

		elif self.type =="segmented" and rc_no>0:
			pl.plot(
				self.seg_rc(self.RC['parameters'][rc_no-1],self.obs_wl),
				label='Rating Q')

		elif rc_no <=0:
			print('Error: unable to find this curve no!')

		pl.title(f'Observed and Rating Curve Discharge, MSE {self.RC["mse"][rc_no-1]:.2f}')
		pl.legend() ; pl.axis('off')
		pl.savefig(output_location)
		pl.clf()


	def saveRC(self,output_location):
		
		if self.fitExecute == False:
			print('ERROR: Execute fit() before saving RC data.')
			return

		rcDat = 'Suggested Rating curves:-\n\n'

		if self.type=="continuous":
			pass 
		elif self.type=="segmented":
			for i in range(5):
				rcDat += f'{i+1}) MSE: {self.RC["mse"][i]:.2f}\n'
				rcDat += f'\t[H  < {self.RC["parameters"][i][-1]:.2f}] {self.RC["parameters"][i][0]:.2f}*(H - {self.RC["parameters"][i][2]:.2f})^{self.RC["parameters"][i][4]:.2f}\n'
				rcDat += f'\t[H >= {self.RC["parameters"][i][-1]:.2f}] {self.RC["parameters"][i][1]:.2f}*(H - {self.RC["parameters"][i][3]:.2f})^{self.RC["parameters"][i][5]:.2f}\n'
			with open(output_location,'w') as rcfile:
				rcfile.write(rcDat)
		
	def seg_rc(self,params,obs_wl):
		c1 = params[0]
		a1 = params[2]
		n1 = params[4]
		# breaking point
		bp = params[6]
		# segment 2 constants
		c2 = params[1]
		a2 = params[3]
		n2 = params[5]

		RC_Q = np.zeros((obs_wl.shape[0]))

		mask_l  = obs_wl  < bp
		mask_ge = obs_wl >= bp

		RC_Q[mask_l ] = c1 * ( (obs_wl[mask_l ]-a1)**n1 )
		RC_Q[mask_ge] = c2 * ( (obs_wl[mask_ge]-a2)**n2 ) 

		return RC_Q


	def seg_rc_mse(self,params,obs_wl,obs_q):

		c1 = params[0]
		a1 = params[2]
		n1 = params[4]
		# breaking point
		bp = params[6]
		# segment 2 constants
		c2 = params[1]
		a2 = params[3]
		n2 = params[5]

		RC_Q = np.zeros((obs_wl.shape[0]))

		mask_l  = obs_wl  < bp
		mask_ge = obs_wl >= bp

		RC_Q[mask_l ] = c1 * ( (obs_wl[mask_l ]-a1)**n1 )
		RC_Q[mask_ge] = c2 * ( (obs_wl[mask_ge]-a2)**n2 ) 

		# function for mean square error
		mse = np.sqrt ( (( (RC_Q-obs_q)**2 ).sum() ) / RC_Q.shape[0] )

		# if power is too big mse will be np.nan
		if np.isnan(mse):
			mse = obs_q.sum()

		return mse

	def cont_rc_mse(self,params,obs_wl,obs_q):
		c = params[0]
		a = params[1]
		n = params[2]

		RC_Q = c * ( (obs_wl-a)**n )
		
		# function for mean square error
		mse = np.sqrt ( (( (RC_Q-obs_q)**2 ).sum() ) / RC_Q.shape[0] )

		# if power is too big mse will be np.nan
		if np.isnan(mse):
			mse = obs_q.sum()

		return mse


	def cont_rc(self,params,obs_wl):
		c = params[0]
		a = params[1]
		n = params[2]

		RC_Q = c * ( (obs_wl-a)**n )

		return RC_Q

# _end_