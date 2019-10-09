#!/usr/bin/python3

import numpy as np
import unittest

import plato_fit_integrals.initialise.create_workflows_comp_ints as tCode

class TestConvertVectorObjFunctFor2dArray(unittest.TestCase):
	""" Test the function that converts objFunct(iterA,iterB) to objFunct(2dArrayA,2dArrayB)
	"""

	def setUp(self):
		self.targValA = np.array( ([1,2], [2,4]) )
		self.actValA = np.array( ([1,4], [2,6]) ) #1st dim is the same (x-values), 2nd dim is different (y-vals)
		self.vectorisedFunct = lambda iterA,iterB: sum(iterA) + sum(iterB)
		self.createFunction()

	def createFunction(self):
		self.testFunct = tCode.getObjFunctForYValsInArraysFromVectorisedFunct(self.vectorisedFunct)

	def testExpForTestArraysA(self):
		expAnswer = 16 #The sum of all y values
		actAnswer = self.testFunct(self.targValA, self.actValA)
		self.assertAlmostEqual(expAnswer, actAnswer)


if __name__ == '__main__':
	unittest.main()

