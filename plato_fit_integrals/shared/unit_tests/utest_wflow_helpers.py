#!/usr/bin/python3
import copy
import unittest

import plato_fit_integrals.shared.workflow_helpers as tCode

class TestModOptDict(unittest.TestCase):

	def setUp(self):
		self.baseOptDict = {"addcorrectingppfrombdt":0,
		                    "addcorrectinghopfrombdt":0}
		self.outDict = copy.deepcopy(self.baseOptDict)
		self.expDict = copy.deepcopy(self.baseOptDict)

		self.progStr = "tb1"
		self.testCorrType = None

	@property
	def inpArgs(self):
		#Property is needed else i cant modify the immutable parts (e.g testCorrType) of this list
		return [self.outDict, self.testCorrType, self.progStr] 

	def runTestFunction(self):
		tCode.modOptDictBasedOnCorrTypeAndPlatoCode(*self.inpArgs)

	def testCorrectingPairPot(self):
		self.testCorrType = "pAirPoT"
		self.expDict["addcorrectingppfrombdt"] = 1
		self.runTestFunction()
		self.assertEqual(self.expDict, self.outDict)

	def testCorrectingPairPotDft2(self):
		self.testCorrType = "pAirPoT"
		self.progStr = "dft2"
		self.expDict["addcorrectingppfrombdt"] = 1
		self.expDict["e0method"] = 1
		self.runTestFunction()
		self.assertEqual(self.expDict, self.outDict)

	def testCorrectingHop(self):
		self.testCorrType ="hopping"
		self.expDict["addcorrectinghopfrombdt"] = 1
		self.runTestFunction()
		self.assertEqual(self.expDict, self.outDict)

	def testRaisesForInvalidCorrType(self):
		self.testCorrType = "whatever"
		with self.assertRaises(ValueError):
			self.runTestFunction()

	def testRaisesForInvalidPlatoStr(self):
		self.progStr = "whatever"
		with self.assertRaises(ValueError):
			self.runTestFunction()

	def testRaisesForInvalidCombination(self):
		self.progStr = "dft2"
		self.testCorrType = "hopping"
		with self.assertRaises(ValueError):
			self.runTestFunction()

if __name__ == '__main__':
	unittest.main()

