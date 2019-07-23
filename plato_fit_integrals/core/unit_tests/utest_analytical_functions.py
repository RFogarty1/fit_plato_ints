#!/usr/bin/python3

import itertools as it
import unittest

import plato_fit_integrals.core.create_analytical_reprs as tCode

class TestCawk17ModTailFunctions(unittest.TestCase):

	def setUp(self):
		self.floatTol = 1e-7
		self.noNodesFunctA = self._createNoNodesFunctA()
		self.nodesFunctA = self._createNoNodesFunctA()
		self.nodesFunctA.nodePositions = [3.5,5.7]

	def _createNoNodesFunctA(self):
		outObj = tCode.Cawkwell17ModTailRepr( rCut=10, refR0=5 , valAtR0=3.2 , nodePositions=None , startCoeffs=[-0.2,-0.1], tailDelta=4.0 ,nPoly=2)
		return outObj

	def testNoNodesCaseA(self):
		inpXVals = [0, 1, 4, 5, 7, 9]
		expOutVals = [0.4786195815, 0.9219229432, 1.8157237402, 1.4378526852, 0.3790138528, 0.0053169833]
		actOutVals = self.noNodesFunctA.evalAtListOfXVals(inpXVals)

		for exp,act in it.zip_longest(expOutVals, actOutVals):
			self.assertAlmostEqual(exp,act)

	def testWithNodesCaseA(self):
		inpXVals = [0, 1, 4, 5, 7, 9]
		expOutVals = [-9.0937720487, -10.3167567452, 1.4698715992, 1.4378526852, -1.6423933623, -0.0919078537]
		actOutVals = self.nodesFunctA.evalAtListOfXVals(inpXVals)

		print("actOutVals = {}".format(actOutVals))
		for exp,act in it.zip_longest(expOutVals, actOutVals):
			self.assertAlmostEqual(exp,act)


class TestPromoteCawkValsToVariables(unittest.TestCase):

	def setUp(self):
		self.rCut = 10
		self.refR0 = 5
		self.valAtR0 = 3.2
		self.nodePositions = None
		self.startCoeffs = [-0.2,-0.1]
		self.tailDelta = 0.0 #To make maths easier
		self.nPoly = 2
		self.currCoeffs = list(self.startCoeffs)
		self.applyDecoTwice = False

		self.testRVals = [0,1,4]

	def runFunct(self):
		testObj = tCode.Cawkwell17ModTailRepr( rCut=self.rCut, refR0=self.refR0 , valAtR0=self.valAtR0 , nodePositions=self.nodePositions ,
		                                       startCoeffs=self.startCoeffs, tailDelta=self.tailDelta ,nPoly=self.nPoly)
		testObj.promoteValAtR0ToVariable()
		testObj.coeffs = self.currCoeffs
		return testObj.evalAtListOfXVals(self.testRVals)


	def testExpValSimpleCase(self):
		self.currCoeffs.append(self.valAtR0+1.0)
		expVals = [0.9371466726, 1.8871816493, 4.6417178559]
		actVals = self.runFunct()
		[self.assertAlmostEqual(exp,act) for exp,act in it.zip_longest(expVals,actVals)]



if __name__ == '__main__':
	unittest.main()


