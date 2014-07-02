from collections import defaultdict, deque
import random as xxx_random # prevent accidental usage
import numpy as np

from utils import *

## Represents a replica capable of executing (or not) optional code.
# Current implementation simulates processor-sharing with an infinite number of
# concurrent requests and a fixed time-slice.
class Replica:
	class Request(object):
		__slots__ = ('requestId', 'replyTo', 'withOptional', 'arrival', 'departure', 'remainingTime')

	## Constructor.
	# @param sim Simulator to attach the server to
	# @param serviceTimeY time to service one request with optional content
	# @param serviceTimeN time to service one request without optional content
	# @param serviceTimeYVariance varince in service-time with optional content
	# @param serviceTimeNVariance varince in service-time without optional content
	# @param minimumServiceTime minimum service-time (despite variance)
	# @param timeSlice time slice; a request longer that this will observe
	# context-switching
	# @param initialTheta initial dimmer value
	# @param controlPeriod control period of brownout controller (0 = disabled)
	# @note The constructor adds an event into the simulator
	def __init__(self, sim, seed = 1,
			timeSlice = 0.01,
			timeY = (0.07, 0.01),
			timeN = (0.00067, 0.0001),
			replicaId = 0):
		## time slice for scheduling requests (server model parameter)
		self.timeSlice = timeSlice
		## service time (mean and standard deviation) with optional content (server model parameter)
		self.timeY = timeY
		## service time (mean and standard deviation) without optional content (server model parameter)
		self.timeN = timeN
		## how often to report metrics
		self.reportPeriod = 1
		## list of active requests (server model variable)
		self._activeRequests = deque()
		## latencies during the last report interval
		self._latestLatencies = []

		## The amount of time this server is active. Useful to compute utilization
		# Since we are in a simulator, this value is hard to use correctly. Use getActiveTime() instead.
		self._activeTime = 0
		## The time when the server became last active (None, not currently active)
		self._activeTimeStarted = None
		## Value used to compute utilization
		self._lastActiveTime = 0

		## Server ID for pretty-printing
		self.name = 'replica' + str(replicaId)

		## Reference to simulator
		self._sim = sim
		
		## Random number generator
		self._random = xxx_random.Random()
		self._random.seed(seed)

		# Initialize reporting
		self._runReportLoop()

	## Compute the (simulated) amount of time this server has been active.
	# @note In a real OS, the active time would be updated at each context switch.
	# However, this is a simulation, therefore, in order not to waste time on
	# simulating context-switches, we compute this value when requested, as if it
	# were continuously updated.
	def getActiveTime(self):
		ret = self._activeTime
		if self._activeTimeStarted is not None:
			ret += self._sim.now - self._activeTimeStarted
		return ret

	## Runs report loop.
	# Regularly report on the status of the server
	def _runReportLoop(self):
		# Compute utilization
		utilization = (self.getActiveTime() - self._lastActiveTime) / self.reportPeriod
		self._lastActiveTime = self.getActiveTime()

		# Report
		self._sim.report(self,
			( 'avgLatency', 'maxLatency', 'utilization' ),
			( avg(self._latestLatencies), maxOrNan(self._latestLatencies), utilization),
		)

		# Re-run later
		self._latestLatencies = []
		self._sim.add(self.reportPeriod, self._runReportLoop)

	## Serve a request
	# @param requestId An opaque value used to identify this request when replied
	# @param replyTo Call this object's reply() method
	# @param headers Dictionary of values that may influence the replica's behaviour. Currently,
	#	only "withOptional" is taken into account.
	# @note When request completes an event is scheduled to: replyTo.reply(requestId, headers).
	def request(self, requestId, replyTo, headers):
		# Activate scheduler, if its not active
		if len(self._activeRequests) == 0:
			self._sim.add(0, self._onScheduleRequests)
		# Add request to list of active requests
		request = Replica.Request()
		request.arrival = self._sim.now
		request.departure = None
		request.requestId = requestId
		request.replyTo = replyTo
		request.withOptional = headers.get('withOptional', False)
		request.remainingTime = self.drawServiceTime(request.withOptional)
		self._activeRequests.append(request)

	def drawServiceTime(self, withOptional):
		mu, sigma = self.timeY \
			if withOptional else self.timeN

		serviceTime = max(self._random.normalvariate(mu, sigma), 0)
		return serviceTime

	## Event handler for scheduling active requests.
	# This function is the core of the processor-sharing with time-slice model.
	# This function is called when "context-switching" occurs. There must be at
	# most one such event registered in the simulation.
	# This function is invoked in the following cases:
	# <ul>
	#   <li>By request(), when the list of active requests was previously empty.
	#   </li>
	#   <li>By _onCompleted(), to pick a new request to schedule</li>
	#   <li>By itself, when a request is preempted, i.e., context-switched</li>
	# </ul>
	def _onScheduleRequests(self):
		# Select next active request
		activeRequest = self._activeRequests.popleft()
		
		# Track utilization
		if self._activeTimeStarted is None:
			self._activeTimeStarted = self._sim.now

		# Schedule it to run for a bit
		timeToExecuteActiveRequest = min(self.timeSlice, activeRequest.remainingTime)
		activeRequest.remainingTime -= timeToExecuteActiveRequest

		# Will it finish?
		if activeRequest.remainingTime == 0:
			# Leave this request in front (onCompleted will pop it)
			self._activeRequests.appendleft(activeRequest)

			# Run onComplete when done
			self._sim.add(timeToExecuteActiveRequest, \
				self._onCompleted)
		else:
			# Reintroduce it in the active request list at the end for
			# round-robin scheduling
			self._activeRequests.append(activeRequest)

			# Re-run scheduler when time-slice has expired
			self._sim.add(timeToExecuteActiveRequest, self._onScheduleRequests)

	## Event handler for request completion.
	# Marks the request as completed, calls replyTo.reply() and calls
	# _onScheduleRequests() to pick a new request to schedule.
	# @param request request that has received enough service time
	def _onCompleted(self):
		# Track utilization
		self._activeTime += self._sim.now - self._activeTimeStarted
		self._activeTimeStarted = None

		# Remove request from active list
		request = self._activeRequests.popleft()

		# And completed it
		request.departure = self._sim.now
		self._latestLatencies.append(request.departure - request.arrival)
		headers = { 'withOptional' : request.withOptional }
		request.replyTo.reply(request.requestId, headers)

		# Continue with scheduler
		if len(self._activeRequests) > 0:
			self._onScheduleRequests()

	## Pretty-print server's ID
	def __str__(self):
		return str(self.name)

