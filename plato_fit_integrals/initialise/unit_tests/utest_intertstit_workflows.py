#!/usr/bin/python3

import copy
import os
import unittest
import unittest.mock as mock

from types import MethodType, SimpleNamespace

import plato_pylib.plato.mod_plato_inp_files as modInp
import plato_pylib.shared.ucell_class as UCell

import plato_fit_integrals.initialise.create_interstit_workflows as tCode


class TestCreateInterProperties(unittest.TestCase):

	def setUp(self):
		self.structRef = createUnitCellObjA()
		self.structInter = createUnitCellObjA()
		self.structInter.lattParams ={k:v for k,v in zip(["a","b","c"],[2.0,3.0,4.0])} #Just to make it different from the ref struct
		self.relaxed="relaxed"
		self.startFolder = os.getcwd()
		self.interType = "octa"
		self.cellDims = [2,3,4]
		self.expDefaultLabel = "octa_relaxed_2_3_4"
		self.platoProg = "tb1"
		self.modOptsDict = {"dataset":"fake_dataset"}
		self.expWorkFolder = os.path.join( os.path.abspath(self.startFolder), self.expDefaultLabel)
		self.genPreShellComms = True
		self.origParser = copy.deepcopy(tCode.InterstitialWorkFlow._parseOutputFiles)

		mockedParser = lambda x: [SimpleNamespace(energy=-868.6244182776455,nAtoms=37),
		                          SimpleNamespace(energy=-856.2981592407685,nAtoms=36)]
		tCode.InterstitialWorkFlow._parseOutputFiles = MethodType(mockedParser,tCode.InterstitialWorkFlow)
		self.expInterstitialEnergy = 11.459800942033212
		self.createWorkFlow()

	def tearDown(self):
		tCode.InterstitialWorkFlow._parseOutputFiles = self.origParser
		self.workFlow = None

	def createWorkFlow(self):
		factoryInstance = tCode.CreateInterstitialWorkFlow(self.structRef,self.structInter, self.startFolder, self.modOptsDict, self.platoProg,
		                                                   relaxed=self.relaxed, interType=self.interType, cellDims=self.cellDims, genPreShellComms=self.genPreShellComms)
		self.workFlow = factoryInstance()

	def testWorkfolderDefaults(self):
		absStartFolder = os.path.abspath(self.startFolder)
		expWorkFolder = self.expWorkFolder
		actWorkFolder = self.workFlow.workFolder
		self.assertEqual(expWorkFolder, actWorkFolder)

	def testOutputAttrsDefaults(self):
		expAttrs = [self.expDefaultLabel + "_interstit_e"]
		actAttrs = self.workFlow.namespaceAttrs
		self.assertEqual(expAttrs, actAttrs)

	def testExpectedPreShellRunComms(self):
		runFormat = "cd " + self.expWorkFolder + ";" + self.platoProg + " {} > outFile"
		expPreShellComms = [runFormat.format(x) for x in ["inter","no_inter"]]
		actPreShellComms = self.workFlow.preRunShellComms
		self.assertEqual(expPreShellComms, actPreShellComms)

	def testExpectedModOptsPresent(self):
		#Note - the files are written upon object initiation 
		actStrDict = modInp.tokenizePlatoInpFile( self.workFlow._inpFilePaths[0] ) #The interstitial case (though fake ucell regardless)
		#Note cant test some possible options (e.g. bloch states) this way; only those stored as strings already in the opt dict (conv to str dict if thats needed)
		for key in self.modOptsDict.keys():
			self.assertEqual( self.modOptsDict[key], actStrDict[key])

	def testCalcInterstitEnergy(self):
		self.workFlow.run()
		outputAttr = self.workFlow.namespaceAttrs[0] #Only 1 ouput expected
		actInterstit = getattr(self.workFlow.output,outputAttr)
		self.assertAlmostEqual(self.expInterstitialEnergy,actInterstit)

	def testPreShellCommsCanBeTurnedOff(self):
		self.genPreShellComms = False
		self.createWorkFlow()
		expRunComms = None
		actRunComms = self.workFlow.preRunShellComms
		self.assertTrue(expRunComms == actRunComms)



class TestInterstitCompositeWorkFlow(unittest.TestCase):

	def setUp(self):
		self.mockWorkFlowA = createMockInterstitWorkFlowA()
		self.mockWorkFlowB = createMockInterstitWorkFlowB()
		self.createTestObj()

	def createTestObj(self):
		self.testObj = tCode.CompositeInterstitialWorkFlow([self.mockWorkFlowA, self.mockWorkFlowB])

	def testNamespaceAttrs(self):
		expAttrs = ["mock_a","mock_b"]
		actAttrs = self.testObj.namespaceAttrs
		self.assertEqual(expAttrs,actAttrs)


	def testCompositeRaisesWhenAttributesDuplicated(self):
		self.mockWorkFlowB = self.mockWorkFlowA
		with self.assertRaises(ValueError):
			self.createTestObj()

	def testCompositeRaisesWhenWorkFoldersDuplicated(self):
		self.mockWorkFlowA.workFolder = self.mockWorkFlowB.workFolder
		with self.assertRaises(ValueError):
			self.createTestObj()


	def testRunWithSimpleMocks(self):
		expOutput = SimpleNamespace(**{"inter_energy_a":20,"inter_energy_b":10})
		self.testObj.run()
		self.assertEqual(self.testObj.output, expOutput)

	def testPreShellCommsNoDuplicates(self):
		expOutput = ["mock_a_inter","mock_a_non_inter","mock_b_inter","mock_b_non_inter"]
		actOutput = self.testObj.preRunShellComms
		self.assertEqual(expOutput,actOutput)

	@unittest.skip("")
	def testPreShellDuplicateStrDicts(self):
		pass

	@unittest.skip("")
	def testPreShellDuplicateWithOneTurnedOff(self):
		pass


def createUnitCellObjA():
	lattVects = [[1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0]]
	fractCoords = [ [0.5,0.5,0.5,"Mg"] ]
	outObj = UCell.UnitCell.fromLattVects(lattVects, fractCoords=fractCoords)
	return outObj


def createMockInterstitWorkFlowA():
	def mockRunFunct(self):
		self.output = SimpleNamespace(**{"inter_energy_a":20})

	outObj = SimpleNamespace()
	outObj.namespaceAttrs = ["mock_a"]
	outObj.workFolder = "mockfolder_a"
	outObj.preRunShellComms = ["mock_a_inter","mock_a_non_inter"]
	outObj.run = MethodType(mockRunFunct,outObj)
	return outObj

def createMockInterstitWorkFlowB():
	def mockRunFunct(self):
		self.output = SimpleNamespace(**{"inter_energy_b":10})

	outObj = SimpleNamespace()
	outObj.namespaceAttrs = ["mock_b"]
	outObj.workFolder = "mockfolder_b"
	outObj.preRunShellComms = ["mock_b_inter","mock_b_non_inter"]
	outObj.run = MethodType(mockRunFunct,outObj)
	return outObj


if __name__ == '__main__':
	unittest.main()

