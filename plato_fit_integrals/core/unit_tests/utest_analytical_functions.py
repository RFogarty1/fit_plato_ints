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

	def testErrorThrownIfStartCoeffLengthWrong(self):
		with self.assertRaises(TypeError):
			outObj = tCode.Cawkwell17ModTailRepr( rCut=10, refR0=5 , valAtR0=3.2 , nodePositions=None , startCoeffs=[-0.2,-0.1,-0.5], tailDelta=4.0 ,nPoly=2)


class TestPromoteCawkValsToVariables(unittest.TestCase):

	def setUp(self):
		self.rCut = 10
		self.refR0 = 5
		self.valAtR0 = 3.2
		self.nodePositions = [3.5,5.7]
		self.startCoeffs = [-0.2,-0.1]
		self.tailDelta = 4.0 #To make maths easier
		self.nPoly = 2
		self.currCoeffs = list(self.startCoeffs)

		self.testRVals = [0, 1, 4, 5, 7, 9]

		self.createTestObj()

	def runFunct(self):
		return self.testObj.evalAtListOfXVals(self.testRVals)

	def createTestObj(self):
		self.testObj = tCode.Cawkwell17ModTailRepr( rCut=self.rCut, refR0=self.refR0 , valAtR0=self.valAtR0 , nodePositions=self.nodePositions ,
		                                       startCoeffs=self.startCoeffs, tailDelta=self.tailDelta ,nPoly=self.nPoly)
		self.testObj.promoteValAtR0ToVariable()
		self.testObj.promoteNodePositionsToVariables()
		self.setCoeffs()

	def setCoeffs(self, inclValAtR0=True):
		if inclValAtR0:
			self.testObj.coeffs = self.currCoeffs + [self.valAtR0] + self.nodePositions
		else:
			self.testObj.coeffs = self.currCoeffs + self.nodePositions

	def testCoeffSetterSimpleCase(self):
		self.nodePositions = [0.2,0.4]
		self.valAtR0 = 5.0
		self.setCoeffs()
		self.assertEqual(self.valAtR0,self.testObj.valAtR0)
		[self.assertAlmostEqual(exp,act) for exp,act in it.zip_longest(self.nodePositions,self.testObj.nodePositions)] #TODO: Make nodePositions private

	def testExpValSimpleCaseForValAtR0(self):
		self.valAtR0 = self.valAtR0 + 1.0
		self.setCoeffs()
		expVals = [-11.935575814, -13.540743228, 1.9292064739, 1.8871816493, -2.1556412881, -0.120629058]
		actVals = self.runFunct()
		[self.assertAlmostEqual(exp,act) for exp,act in it.zip_longest(expVals,actVals)]

	def testModdingNodePositionsWorksIfValAtR0Demoted(self):
		self.testObj.demoteValAtR0FromVariable()
		self.nodePositions = [4.0,5.9]
		self.setCoeffs(inclValAtR0=False)
		expVals = [-12.5504690263, -15.0580747387, 0, 1.4378526852, -1.3897174604, -0.0915702675]
		actVals = self.runFunct()
		[self.assertAlmostEqual(exp,act) for exp,act in it.zip_longest(expVals,actVals)]

	def testModifyingNodePositionsGivesExpVal(self):
		self.nodePositions = [4.0,5.9]
		self.setCoeffs()
		expVals = [-12.5504690263, -15.0580747387, 0, 1.4378526852, -1.3897174604, -0.0915702675]
		actVals = self.runFunct()
		[self.assertAlmostEqual(exp,act) for exp,act in it.zip_longest(expVals,actVals)]

	def testRaisesIfSettingWrongNumberOfCoeffs(self):
		self.testObj.demoteValAtR0FromVariable()
		with self.assertRaises(TypeError): #We're now passing the wrong number of arguments (its pretty feasible this could happen)
			self.setCoeffs()



class TestExpDecayFunct(unittest.TestCase):

	def setUp(self):
		self.prefactor = 5
		self.alpha = -2.4
		self.r0 = 1.0
		self.testXVals = [0,1,2]
		self.rCut = None
		self.tailDelta = None

	def runFunct(self):
		outVals = self.testObj.evalAtListOfXVals(self.testXVals)
		return outVals

	def createObj(self):
		self.testObj = tCode.ExpDecayFunct(r0=self.r0,prefactor=self.prefactor,alpha=self.alpha,rCut=self.rCut, tailDelta=self.tailDelta)		

	def testExpValsForSimpleInputs(self):
		self.createObj()
		actVals = self.runFunct()
		expVals = [1586.7416445893, 5, 0.015755558]
		[self.assertAlmostEqual(exp,act) for exp,act in it.zip_longest(expVals,actVals)]

	def testNCoeffsCorrectDefaultBuild(self):
		self.createObj()
		actNumbCoeffs = self.testObj.nCoeffs
		expNumbCoeffs = 2 #prefactor and alpha value should be coeffs
		self.assertEqual(expNumbCoeffs,actNumbCoeffs)

	def testExpCoeffsReturned(self):
		self.createObj()
		expCoeffs = [self.prefactor,self.alpha]
		actCoeffs = self.testObj.coeffs
		[self.assertAlmostEqual(exp,act) for exp,act in it.zip_longest(expCoeffs,actCoeffs)]

	def testExpCoeffsSet(self):
		newPrefactor,newAlpha = 0.5,2.5
		self.createObj()
		self.testObj.coeffs = [newPrefactor, newAlpha]
		self.assertAlmostEqual(newPrefactor, self.testObj._prefactor)
		self.assertAlmostEqual(newAlpha, self.testObj._alpha)

	def testExpValsWithTailFunct(self):
		self.rCut = 5.0
		self.tailDelta = 0.5
		self.createObj()
		self.testXVals = self.testXVals + [self.rCut, 7.0]
		expVals = [1435.7432127803,4.4124845129,0.0133367919,0,0]
		actVals = self.runFunct()
		[self.assertAlmostEqual(exp,act) for exp,act in it.zip_longest(expVals,actVals)]


if __name__ == '__main__':
	unittest.main()


