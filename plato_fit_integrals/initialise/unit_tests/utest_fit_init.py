#!/usr/bin/python3


import itertools as it
import unittest

import numpy as np

import plato_fit_integrals.initialise.fit_analytic_to_initial_tables as tCode

class TestFindCrossings(unittest.TestCase):

	def setUp(self):
		self.testDataA = loadTestDataA()
		

	def testForDataA(self):
		expNodePos = [1.5, 4+(5/6)]
		actNodePos = tCode.findCrossings(self.testDataA)
		[self.assertAlmostEqual(exp,act) for exp,act in it.zip_longest(expNodePos, actNodePos)]


class TestGetYVal(unittest.TestCase):

	def setUp(self):
		self.testDataA = loadTestDataA()

	def testForDataA(self):
		xVals =     [1.0,  3.5,  2.25]
		expYVals =  [1.0, -4.0, -1.5]

		actVals = list()
		for x in xVals:
			actVals.append( tCode.getInterpYValGivenXValandInpData(x,self.testDataA) )

		for exp,act in it.zip_longest(expYVals, actVals):
			self.assertAlmostEqual(exp,act)


def loadTestDataA():
	xVals = [1,  2,  3,  4,  5,  6]
	yVals = [1, -1, -3, -5,  1,  3]
	testDataA = np.array( [(x,y) for x,y in it.zip_longest(xVals,yVals)] )
	return testDataA


if __name__ == '__main__':
	unittest.main()

