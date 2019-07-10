#!/usr/bin/python3

import itertools as it
import os
import pathlib
import unittest

import plato_fit_integrals.core.coeffs_to_tables as coeffsToTables

import plato_fit_integrals.initialise.create_coeff_tables_converters as tCode
import plato_pylib.plato.private.tbint_test_data as tData
import plato_pylib.plato.parse_tbint_files as parseTbint

class TestCreateIntegHolderFromModelFolder(unittest.TestCase):

	def setUp(self):
		self.expData = tData.loadTestBdtFileAExpectedVals_format4()
		self.dirPath = os.path.abspath( os.path.join( os.getcwd(), "fake_model_folder") )
		createFakeModelFolderEnvironment(self.dirPath)
		self.createdIntegHolder = tCode.createIntegHolderFromModelFolderPath(self.dirPath)

	def tearDown(self):
		destroyFakeModelFolderEnvironment(self.dirPath)

	def testForPairPotentialSingleElement(self):
		atomA, atomB = "Xa","Xb"
		expPPNoCorr = self.expData["pairPot"][0]
		actPPNoCorr = self.createdIntegHolder.getIntegTable("pairPot", atomA, atomB, inclCorrs=False)
		expPPNoCorr.inpFilePath = actPPNoCorr.inpFilePath 
		self.assertEqual(expPPNoCorr, actPPNoCorr)


class TestIntInfoObjsFromBdtFile(unittest.TestCase):

	def setUp(self):
		self.dirPath = os.path.abspath( os.path.join( os.getcwd(), "fake_model_folder_t2") )
		self.bdtPath = os.path.join(self.dirPath,"Xa_Xb.bdt")
		createFakeModelFolderEnvironment(self.dirPath)
	

	def tearDown(self):
		destroyFakeModelFolderEnvironment(self.dirPath)


	def testForPairPot(self):
		expInfoObjs = self._loadPPExpIntInfo()
		actIntInfoObjs = tCode.getAllIntInfoObjsFromIntegStrAndBdtPath("pairPot", self.bdtPath)
		[self.assertEqual(exp,act) for exp,act in it.zip_longest(expInfoObjs,actIntInfoObjs)]


	def testForHopInts(self):
		expInfoObjs = self._loadHopExpIntInfo()
		actIntInfoObjs = tCode.getAllIntInfoObjsFromIntegStrAndBdtPath("hopping", self.bdtPath)
		[self.assertEqual(exp,act) for exp,act in it.zip_longest(expInfoObjs,actIntInfoObjs)]


	def _loadPPExpIntInfo(self):
		atomA, atomB = "Xa", "Xb"
		ppIntegInfo = coeffsToTables.IntegralTableInfo(self.dirPath, "pairPot", atomA, atomB)
		return [ppIntegInfo]

	def _loadHopExpIntInfo(self):
		atomA, atomB = "Xa", "Xb"
		fixedArgs = [self.dirPath,"hopping",atomA,atomB]

		hopOrbAA        = coeffsToTables.IntegralTableInfo(*fixedArgs, shellA=0, shellB=0, axAngMom=1)
		hopOrbAB        = coeffsToTables.IntegralTableInfo(*fixedArgs, shellA=0, shellB=1, axAngMom=1)
		hopOrbBA        = coeffsToTables.IntegralTableInfo(*fixedArgs, shellA=1, shellB=0, axAngMom=1)
		hopOrbBB_sigma  = coeffsToTables.IntegralTableInfo(*fixedArgs, shellA=1, shellB=1, axAngMom=1)
		hopOrbBB_pi     = coeffsToTables.IntegralTableInfo(*fixedArgs, shellA=1, shellB=1, axAngMom=2)

		allObjs = [hopOrbAA, hopOrbAB, hopOrbBA, hopOrbBB_sigma, hopOrbBB_pi]

		return allObjs

def createFakeModelFolderEnvironment(workFolder):
	pathlib.Path(workFolder).mkdir(exist_ok=True, parents=False)
	allData = tData.loadTestBdtFileAExpectedVals_format4()
	outFilePath = os.path.join( workFolder, "Xa_Xb.bdt" )
	parseTbint.writeBdtFileFormat4( allData ,outFilePath )

def destroyFakeModelFolderEnvironment(workFolder):
	fileNames = [x for x in os.listdir(workFolder)]
	filePaths = [ os.path.abspath(os.path.join(workFolder,x)) for x in fileNames ]
	for fPath in filePaths:
		os.remove(fPath)
	os.rmdir(workFolder)


if __name__ == '__main__':
	unittest.main()


