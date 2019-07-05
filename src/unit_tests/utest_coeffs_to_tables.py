#!/usr/bin/python3

import copy
import os
import sys
import unittest
import unittest.mock as mock

sys.path.append('..')

import plato_pylib.plato.parse_tbint_files as parseTbint
import plato_pylib.plato.private.tbint_test_data as tData
import coeffs_to_tables as tCode

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
		

class TestCoeffsTableConverter(unittest.TestCase):

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
		pass
		#TODO: NEED TO REMOVE THE *.bdt file i created

	def testCorrectlyWritesPairPot_singleFile(self):
		expPPCorr = self.integDicts[0]["pairpot"][0]
		expPPCorr.integrals[:,1] *= -1 #Total PP is zero, so the correction must exactly cancel the initial

		self.testObj.writeTables() #Will always update before writing them
		actualPPCorr = parseTbint.getIntegralsFromBdt(self.outFileA)["PairPotCorrection0"][0]

		print("actual PPCorr integrals = {}".format(actualPPCorr.integrals))
		print("expPPCorr integrals = {}".format(expPPCorr.integrals))
#		import pdb
#		pdb.set_trace()
		self.assertEqual(expPPCorr, actualPPCorr)


def createIntegTableInfoXaXbPairPot(modelFolder):
	return tCode.IntegralTableInfo(modelFolder, "pairpot", "Xa", "Xb")



if __name__ == '__main__':
	unittest.main()

