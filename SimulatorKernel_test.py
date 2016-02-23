from __future__ import print_function

from SimulatorKernel import SimulatorKernel

def assertShouldRunAt(sim, when, eventsExecuted):
	"""
	Helper method to assert that an event was executed at the right time.
	"""
	eventsExecuted.append(sim.now)
	assert sim.now == when

def assertShouldRunPeriodically(sim, period, eventsExecuted):
	"""
	Helper method to assert that an event was executed at the right time.
	The current time needs to be divisible with the period.
	"""
	eventsExecuted.append(sim.now)
	assert sim.now % period == 0

def test_add_events():
	eventsExecuted = []

	sim = SimulatorKernel()
	sim.add(0  , lambda: assertShouldRunAt(sim, 0  , eventsExecuted))
	sim.add(100, lambda: assertShouldRunAt(sim, 100, eventsExecuted))
	sim.add(200, lambda: assertShouldRunAt(sim, 200, eventsExecuted))
	sim.run()

	assert eventsExecuted == [ 0, 100, 200 ], eventsExecuted

def test_run_until():
	def runPeriodically(sim, period, eventsExecuted):
		assertShouldRunPeriodically(sim, period, eventsExecuted)
		sim.add(period, lambda: runPeriodically(sim, period, eventsExecuted))

	eventsExecuted = []
	sim = SimulatorKernel()
	runPeriodically(sim, 100, eventsExecuted)
	sim.run(until = 1000)

	# MUST include time 1000
	assert eventsExecuted == range(0, 1001, 100), eventsExecuted

def test_update_event():
	def toRun():
		assertShouldRunAt(sim, 100, eventsExecuted)

	eventsExecuted = []

	sim = SimulatorKernel()
	sim.add(0, toRun)
	# The above assertion WOULD fail, so add an event to update it
	sim.update(100, toRun)
	sim.run()

	assert eventsExecuted == [ 100 ], eventsExecuted

def test_output():
	import base64
	import os

	issuer = base64.urlsafe_b64encode(os.urandom(16)) 
	sim = SimulatorKernel()
	sim.output(issuer, "hello")
	sim.output(issuer, "world")

	expected = "hello\nworld\n"
	resultFileName = 'sim-' + issuer + '.csv'
	result = open(resultFileName).read()
	os.remove(resultFileName)
	
	assert result == expected