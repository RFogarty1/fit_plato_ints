#!/usr/bin/python3

import unittest
import plato_fit_integrals.initialise.obj_functs_targ_vals as tCode 


class TestBasicMSDFunction(unittest.TestCase):

	def setUp(self):
		self.testFunction = tCode.createSimpleTargValObjFunction("SqRDeV") #Weird caps to make sure case-insensitive
		self.testFunctNoOverflowProt = tCode.createSimpleTargValObjFunction("SqRDeV",catchOverflow=False)

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


class TestVectorisedCreator(unittest.TestCase):
	
	def setUp(self):
		self.functTypeStr = "relRootSqrDev".lower()
		self.averageMethod = "mean"
		self.divErrorsByNormFactor = None
		self.createFunction()

	def createFunction(self):
		self.testFunct = tCode.createVectorisedTargValObjFunction(self.functTypeStr, averageMethod=self.averageMethod,divideErrorsByNormFactor=self.divErrorsByNormFactor)

	def testMeanMethodGivesExpOutput(self):
		targVals = [1,3,5]
		inpVals = [2,8,3]
		expAnswer = 1.0222222
		actAnswer = self.testFunct(targVals,inpVals)
		self.assertAlmostEqual(expAnswer, actAnswer)

	def testDivByConstantGivesExpOutput(self):
		targVals = [1,3,5]
		inpVals = [2,8,3]
		normFactor = 2.5
		expAnswer = 1.0222222/normFactor
		self.divErrorsByNormFactor = normFactor
		self.createFunction()
		actAnswer = self.testFunct(targVals,inpVals)
		self.assertAlmostEqual(expAnswer,actAnswer)



class TestVectorisedDecoratorOptions(unittest.TestCase):

	def setUp(self):
		self.functTypeStr = "sqrdev".lower()
		self.averageMethod = "mean"
		self.catchOverflow = True
		self.greaterThanIsOk = False
		self.lessThanIsOk = False
		self.useAbsVals = False
		self.targVals = [2,3,0]
		self.actVals = [1,2,3]

	def runFunct(self):
		currKwargs = {"greaterThanIsOk":self.greaterThanIsOk, "averageMethod":self.averageMethod,
		              "catchOverflow":self.catchOverflow, "lessThanIsOk":self.lessThanIsOk, "useAbsVals":self.useAbsVals}
		cmpFunct = tCode.createVectorisedTargValObjFunction(self.functTypeStr, **currKwargs)
		outVal = cmpFunct(self.targVals, self.actVals)
		return outVal

	def testExpOutputGivenForGreaterThan(self):
		self.greaterThanIsOk = True
		expAnswer = 2/3
		actAnswer = self.runFunct()
		self.assertAlmostEqual(expAnswer, actAnswer)

	def testExpOutputGivenForLessThan(self):
		self.lessThanIsOk = True
		expAnswer = 9/3
		actAnswer = self.runFunct()
		self.assertAlmostEqual(expAnswer, actAnswer)

	def testUseAbsValsGivesExpectedVals(self):
		self.useAbsVals = True
		self.actVals = [-1,-2,-3]
		expVal = 11/3
		actVal = self.runFunct() 
		self.assertAlmostEqual(expVal,actVal)

	def testAbsValsMixedWithLessThan(self):
		""" Demonstrates that abs than is applied before checking less-than """
		self.useAbsVals = True
		self.lessThanIsOk = True
		self.actVals = [-1,-2,-3]
		expVal = 9/3 #Same as the less-than test, since we essentially convert act-vals back to what they were
		actVal = self.runFunct()
		self.assertAlmostEqual(expVal, actVal)

if __name__ == '__main__':
	unittest.main()


