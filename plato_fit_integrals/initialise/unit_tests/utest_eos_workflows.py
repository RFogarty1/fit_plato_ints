#!/usr/bin/python3

import os
import itertools as it
import unittest
import unittest.mock as mock

from types import SimpleNamespace

import plato_pylib.plato.mod_plato_inp_files as modInp

import plato_fit_integrals.initialise.obj_functs_targ_vals as objCmpFuncts
import plato_fit_integrals.initialise.create_eos_workflows as tCode


class TestCreateEosProperties(unittest.TestCase):

	def setUp(self):
		self.structVols = [150,200,250]
		self.structDict = {"hcp":createMockUCellObjListFromVols(self.structVols)}
		self.modOptDicts = {"hcp": {"dataset":"fake_dataset"} }
		self.workFolder = "fake_folder"
		platoCode = "dft2"
		varyType = "pairpot"

		self.factoryA = tCode.CreateEosWorkFlow(self.structDict, self.modOptDicts, self.workFolder,
		                                        platoCode, varyType=varyType)
		self.workFlowA = self.factoryA()

	def testExpectedOutAttrs(self):
		actWorkFlow = self.workFlowA
		expKeys = sorted(["hcp_" + str(x) for x in ["v0","b0"]])
		actKeys = sorted(actWorkFlow.namespaceAttrs)
		[self.assertEqual(exp,act) for exp,act in it.zip_longest(expKeys,actKeys)]

	def testExpectedPreShellComms(self):
		workFolder = os.path.abspath(self.workFolder)
		expFileNames = ["{}_vol_{:.2f}".format( list(self.structDict.keys())[0], vol) for vol in self.structVols]
		expFileNames = [x.replace(".","pt")+".in" for x in expFileNames]
		expRunComms = ["cd {};dft2 {} > outFile".format(workFolder,fName.replace(".in","")) for fName in expFileNames]
		actRunComms = self.workFlowA.preRunShellComms
		[self.assertEqual(exp,act) for exp,act in it.zip_longest(expRunComms,actRunComms)]

	def testModOptsCorrectInOutFile(self):
		inpFilePaths = self.workFlowA._inpFilePaths
		expModdedOpts = self.modOptDicts
		expModdedOpts["hcp"]["addCorrectingPPFromBdt".lower()] = str(1)
		fullInpDict = modInp.tokenizePlatoInpFile(inpFilePaths[0])

		for key in expModdedOpts["hcp"]:
			self.assertEqual( expModdedOpts["hcp"][key], fullInpDict[key] )



def createMockUCellObjListFromVols(volList):
	outObjList = [mock.Mock() for x in volList]
	for x,vol in it.zip_longest(outObjList,volList):
		x.volume = vol
		x.lattVects = [[1.0,0.0,0.0],
		               [0.0,1.0,0.0],
		               [0.0,0.0,1.0]]
		x.fractCoords = [[0.0,0.0,0.0,"X"]]
		x._getMagVector = lambda x: 0.0
	return outObjList



class TestCreateObjFunct(unittest.TestCase):

	def setUp(self):
		self.propList = ["v0","b0"]
		self.structList = ["hcp","hcp"]
		self.targVals = [0.0 for x in range(len(self.propList))]
		self.weightList = [1.0 for x in range(len(self.propList))] #TODO:alter this
		self.objFunctList = [objCmpFuncts.createSimpleTargValObjFunction("blank") for x in range(len(self.propList))]
		self.inpLists = [self.propList, self.structList, self.targVals, self.weightList, self.objFunctList]
		self.testObjA = tCode.EosObjFunctCalculator(self.propList, self.structList, self.targVals,
		                                            self.weightList, self.objFunctList)

	def testCorrectObjFunctionCalculated(self):
		calcVals = SimpleNamespace( **{"hcp_v0":2,
		                               "hcp_b0":7})
		expObjFunctVal = 9 
		actObjFunctVal = self.testObjA.calculateObjFunction(calcVals)
		self.assertEqual(expObjFunctVal, actObjFunctVal)

	def testInitAssertsEqualListsInput(self):
		self.propList.pop()
		with self.assertRaises(AssertionError):
			tCode.EosObjFunctCalculator(self.propList, self.structList, self.targVals,
		                                            self.weightList, self.objFunctList)

	def testExpectedProps(self):
		expProps = ["hcp_v0", "hcp_b0"]
		actualProps = self.testObjA.props
		[self.assertEqual(exp,act) for exp,act in it.zip_longest(expProps,actualProps)]

	def testRaisesForDuplicateProperties_initation(self):
		for currList in self.inpLists:
			currList.append( currList[0] )
		with self.assertRaises(ValueError):
			tCode.EosObjFunctCalculator(*self.inpLists)

	def testAddPropAffectsObjFunct(self):
		targVal=0.0
		extraProp = ("hcp","e0",targVal)
		self.testObjA.addProp(*extraProp,weight=2.0,objFunct=objCmpFuncts.createSimpleTargValObjFunction("blank"))
		calcVals = SimpleNamespace( **{"hcp_v0":2,
		                               "hcp_b0":3,
		                               "hcp_e0":7} )
		expObjFunct = 19
		actObjFunct = self.testObjA.calculateObjFunction(calcVals)
		self.assertEqual(expObjFunct,actObjFunct)

	def testRaisesForDuplicateProperts_addProp(self):
		extraProp = (self.structList[0],self.propList[0],self.targVals[0])
		with self.assertRaises(ValueError):
			self.testObjA.addProp(*extraProp)

if __name__ == '__main__':
	unittest.main()

