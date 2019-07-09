#!/usr/bin/python3

import os
import pathlib
import unittest

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


