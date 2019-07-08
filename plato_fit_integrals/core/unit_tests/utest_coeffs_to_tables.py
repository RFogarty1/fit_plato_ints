#!/usr/bin/python3

import copy
import itertools as it
import os
import unittest
import unittest.mock as mock


import plato_pylib.plato.parse_tbint_files as parseTbint
import plato_pylib.plato.private.tbint_test_data as tData
import plato_fit_integrals.core.coeffs_to_tables as tCode

class TestIntegralHolder(unittest.TestCase):
	
	def setUp(self):
		self.atomPairNames = [("Mg","Mg")]
		self.integDicts = [ {k.lower():v for k,v in tData.loadTestBdtFileAExpectedVals_format4().items()} ]
		self.testObjA = tCode.IntegralsHolder(self.atomPairNames, self.integDicts)

		self.expGetPairPot = copy.deepcopy(self.integDicts[0]["pairpot"][0])
		self.expGetPairPot.integrals[:,1] = [6.224678330, -0.010034643, -0.000000300]


	def testGetterForPairPotInclCorrection_singleFile(self):
		atomA, atomB, integStr = "Mg", "Mg", "PAirPOt" #Weird format on integStr since it should be case-insensitive anyway
		actIntegObj = self.testObjA.getIntegTable(integStr, atomA, atomB)
		self.assertEqual( self.expGetPairPot, actIntegObj )


	def testSetterForPairPot_singleFile(self):
		atomA, atomB, integStr = "Mg", "Mg", "Pairpot"
		testSetTable = copy.deepcopy(self.integDicts[0]["pairpot"][0])
		testSetTable.integrals[:,1] *= -1

		#We want the pair-potential to be unchanged internally, only the correction
		#So if the internal PP repr is unchanged AND PP+corr(result of the getter) is what it was set
		#to then the setter has worked correctly
		self.testObjA.setIntegTable(testSetTable, integStr, atomA, atomB)
		actTablePP = self.testObjA.integDicts[0]["pairpot"][0]
		expTablePP = self.integDicts[0]["pairpot"][0]
		actFullPPTable = self.testObjA.getIntegTable(integStr, atomA, atomB)

		self.assertEqual(expTablePP, actTablePP)
		self.assertEqual(testSetTable, self.testObjA.getIntegTable(integStr, atomA, atomB) )
		

class TestCoeffsTableConverterWriteTables(unittest.TestCase):

	def setUp(self):
		self.atomPairNames = [("Xa","Xb")]
		self.integDicts = [ {k.lower():v for k,v in tData.loadTestBdtFileAExpectedVals_format4().items()} ]
		self.integDicts[0]["PairPotCorrection0".lower()][0].integrals[:,1] = 0 #no PP Correction, means it will equal any change i make in total PP

		#Write integrals to file
		self.outFileA = "Xa_Xb.bdt" #Needs to match the atomPairNames
		parseTbint.writeBdtFileFormat4(self.integDicts[0], self.outFileA)
		integHolder = tCode.IntegralsHolder(self.atomPairNames, copy.deepcopy(self.integDicts))

		integInfo = createIntegTableInfoXaXbPairPot( os.getcwd() )
		mockedAnalyticalRepr = mock.Mock()
		mockedAnalyticalRepr.evalAtListOfXVals = lambda x: [0 for a in x]

		self.testObj = tCode.CoeffsTablesConverter([mockedAnalyticalRepr], [integInfo], integHolder)

	def tearDown(self):
		os.remove(self.outFileA)

	def testCorrectlyWritesPairPot_singleFile(self):
		expPPCorr = self.integDicts[0]["pairpot"][0]
		expPPCorr.integrals[:,1] *= -1 #Total PP is zero, so the correction must exactly cancel the initial

		self.testObj.writeTables() #Will always update before writing them
		actualPPCorr = parseTbint.getIntegralsFromBdt(self.outFileA)["PairPotCorrection0"][0]

		self.assertEqual(expPPCorr, actualPPCorr)



class TestCoeffsTableConverterPassCoeffs(unittest.TestCase):
	def setUp(self):
		integHolder = None
		integInfoList = [None]

		mockedAnalyticalReprs = [mock.Mock() for x in range(3)]
		self.nCoeffs = [2,2,1]
		for x,nCoeff in it.zip_longest(mockedAnalyticalReprs, self.nCoeffs):
			x.nCoeffs=nCoeff

		coeffVals = [[0,1],[2,3],[4]]
		self.mergedListCoeffs = [0,1,2,3,4]
		for x,coeffs in it.zip_longest(mockedAnalyticalReprs,coeffVals):
			x.coeffs = coeffs

		self.testObj = tCode.CoeffsTablesConverter( mockedAnalyticalReprs, integInfoList, integHolder )

	def testGetCoeffs(self):
		expCoeffs = self.mergedListCoeffs
		actCoeffs = self.testObj.coeffs
		[self.assertEqual(exp,act) for exp,act in it.zip_longest(expCoeffs,actCoeffs)]

	def testSetCoeffs(self):
		expCoeffs = [9,10,11,12,13]
		self.testObj.coeffs = expCoeffs
		actCoeffs = self.testObj.coeffs
		[self.assertEqual(exp,act) for exp,act in it.zip_longest(expCoeffs,actCoeffs)]

def createIntegTableInfoXaXbPairPot(modelFolder):
	return tCode.IntegralTableInfo(modelFolder, "pairpot", "Xa", "Xb")



if __name__ == '__main__':
	unittest.main()

