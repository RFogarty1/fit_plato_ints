#!/usr/bin/python3

import unittest
import unittest.mock as mock

from types import SimpleNamespace


import plato_fit_integrals.core.obj_funct_calculator as tCode


class TestTotalObjectiveFunctClass(unittest.TestCase):

	def setUp(self):
		self.testObjContribA = createMockObjFunctContribA()
		self.testObjContribB = createMockObjFunctContribB()

	def testCalcExpObjFunctMultiComponentsUnitWeights(self):
		testTotObj = tCode.ObjectiveFunctTotal( [self.testObjContribA, self.testObjContribB] )
		expObjFunction = 12
		actObjFunct = testTotObj.calculateObjFunction( None ) #Calculate values are irrelevant with the mocking used
		self.assertEqual(expObjFunction, actObjFunct)

	def testMultiComponentsWithWeights(self):
		weightVals = [0.2,2.0]
		expObjFunction = 15
		testTotObj = tCode.ObjectiveFunctTotal( [self.testObjContribA, self.testObjContribB], weights=weightVals )
		actObjFunct = testTotObj.calculateObjFunction( None )
		self.assertEqual(expObjFunction, actObjFunct)


def createMockObjFunctContribA():
	outObj = mock.Mock()
	retVal = 5
	outObj.calculateObjFunction = createCalcObjFunctReturnX(retVal)
	return outObj


def createMockObjFunctContribB():
	outObj = mock.Mock()
	retVal = 7
	outObj.calculateObjFunction = createCalcObjFunctReturnX(retVal)
	return outObj


def createCalcObjFunctReturnX(retVal):
	def outFunct(calcVals):
		return retVal
	return outFunct



class TestContribObjectiveFunctionClass(unittest.TestCase):

	def setUp(self):
		self.testObjFunctContribA = createObjFunctContribObjA()


	def testTwoSimpleProps(self):
		calcVals = SimpleNamespace( hcp_v0=19, hcp_b0=17 )
		expObjFunct = 5
		actObjFunct = self.testObjFunctContribA.calculateObjFunction(calcVals)
		self.assertEqual(expObjFunct, actObjFunct)



def createObjFunctContribObjA():
	objFunctA, objFunctB = createMeanSqrDiffObjFunctOneVal(), createMeanSqrDiffObjFunctOneVal()
	targNamespace = SimpleNamespace( hcp_v0=(20,objFunctA) , hcp_b0=(15,objFunctB) ) 
	return tCode.ObjectiveFunctionContrib(targNamespace)


def createMeanSqrDiffObjFunctOneVal():
	def outFunct(targVal,actVal):
		return (targVal - actVal)**2
	return outFunct







if __name__ == '__main__':
	unittest.main()

