#!/usr/bin/python3

import unittest
import plato_fit_integrals.initialise.obj_functs_targ_vals as tCode 


class TestBasicMSDFunction(unittest.TestCase):

	def setUp(self):
		self.testFunction = tCode.createSimpleTargValObjFunction("MsD") #Weird caps to make sure case-insensitive
		self.testFunctNoOverflowProt = tCode.createSimpleTargValObjFunction("MSD",catchOverflow=False)

	def testForSimpleValues(self):
		testTargVal, testActVal = 5,2
		expOutput = 9
		actOutput = self.testFunction(testTargVal, testActVal)
		self.assertEqual(expOutput,actOutput)


	def testArgOrderIrrelevant(self):
		paramA, paramB = 12,19
		outA,outB = self.testFunction(paramA,paramB), self.testFunction(paramB,paramA)
		self.assertEqual(outA,outB)


	def testForOverflowingValues(self):
		paramA,paramB = 1e199,1e198
		expVal = 1e30
		actVal = self.testFunction(paramA,paramB)
		self.assertEqual(expVal,actVal)




if __name__ == '__main__':
	unittest.main()


