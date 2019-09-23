#!/usr/bin/python3

import os
import itertools as it
import unittest
import unittest.mock as mock
from types import SimpleNamespace

import plato_pylib.shared.ucell_class as UCell

import plato_fit_integrals.initialise.create_ecurve_workflows as tCode

class TestCreateDimerDissocCurveStructs(unittest.TestCase):

	def setUp(self):
		self.dists = [2,4,6]
		self.testAtomA = "Mg"
		self.testAtomB = "Si"
		

	def testExpectedDistsPresent(self):
		outGeoms = tCode.createDimerDissocCurveStructs(self.dists, self.testAtomA, self.testAtomB)
		expDists = self.dists
		outCartGeoms = [x.cartCoords for x in outGeoms]	
		actDists = list()
		for x in outCartGeoms:
			posA = x[0][:3]
			posB = x[1][:3]
			actDists.append( _getDistTwoVectors(posA, posB) )

		[self.assertAlmostEqual(exp,act) for exp,act in it.zip_longest(expDists,actDists)]

def _getDistTwoVectors(vectA,vectB):
	sqrDiff = [(b-a)**2 for a,b in it.zip_longest(vectA,vectB)]
	dist = (sum(sqrDiff))**0.5
	return dist


class TestGetSepTwoAtomsInUnitCell(unittest.TestCase):

	def setUp(self):
		self.lattVects = [[1.0, 0.0, 0.0],
		                  [0.0, 1.0, 0.0],
		                  [0.0, 0.0, 1.0]]
		self.cartCoords = [[0.0,0.0,0.0],[0.0,0.0,4.0]]
		self.testCellA = UCell.UnitCell.fromLattVects(self.lattVects)
		self.testCellA.cartCoords = self.cartCoords

	def testExpDistanceObtained(self):
		expSep = 4.0
		actSep = tCode.getSepTwoAtomsInUnitCellStruct(self.testCellA)
		self.assertAlmostEqual(expSep,actSep)


class TestCreateObjFunctCalculator(unittest.TestCase):

	def setUp(self):
		self.outAttr = "test_attr"
		self.inpWorkFlow = createMockECurveWorkFlow([self.outAttr])
		self.functTypeStr = "relRootSqrDev"
		self.testCalcVals = SimpleNamespace(**{self.outAttr:[3.0,5.0]})
		self.testTargVals = [6.0,7.0]
		self.avMethod = "mean"
		self.catchOverflow = True
		self.errorRetVal = 1e30
		self.normToErrorRetVal=False

	def runTestFunct(self):
		outVal = tCode.createObjFunctCalculatorFromEcurveWorkflow(self.inpWorkFlow, self.testTargVals, self.functTypeStr, self.avMethod,
		                                                          self.catchOverflow, self.errorRetVal, self.normToErrorRetVal)
		return outVal

	def testExpObjFunctValSetA(self):
		objFunctCalculator = self.runTestFunct()
		expObjFunctVal = 0.5*sum([(3/6),(2/7)])
		actObjFunctVal = objFunctCalculator.calculateObjFunction(self.testCalcVals) 
		self.assertAlmostEqual(expObjFunctVal,actObjFunctVal)


	def testRaisesForWrongWorkFlow(self):
		""" Test we get ValueError if workFlow has more than 1 attribute """
		fakeWorkFlow = mock.Mock()
		fakeWorkFlow.namespaceAttrs = ["fakeA","fakeB"]
		self.inpWorkFlow = fakeWorkFlow
		with self.assertRaises(AssertionError):
			self.runTestFunct()

def createMockECurveWorkFlow(outAttrs:list):
	outObj = mock.Mock()
	outObj.namespaceAttrs = outAttrs
	return outObj



class TestStructEnergiesWorkFlow(unittest.TestCase):

	def setUp(self):
		self.structList = list()
		self.modOptsDict = dict()
		self.workFolder = os.getcwd()
		self.platoCode = "dft2"
		self.outAttr = "energies_per_atom"
		self.varyType = None
		self.eType = "electronicCohesiveE"
		self.ePerAtom = True
		self.createTestObj()

	def createTestObj(self):
		self.testObjA = tCode.CreateStructEnergiesWorkFlow(self.structList, self.modOptsDict, self.workFolder, self.platoCode,
		                                                   varyType=self.varyType, outAttr=self.outAttr, eType=self.eType, ePerAtom=self.ePerAtom) ()

	@mock.patch("plato_fit_integrals.initialise.create_ecurve_workflows.platoOut.parsePlatoOutFile")
	@mock.patch("plato_fit_integrals.initialise.create_ecurve_workflows.StructEnergiesWorkFlow.outFilePaths",new_callable=mock.PropertyMock)
	def testEnergiesPerAtomApplied(self, outPathsMock, parseOutMock):
		outPathsMock.return_value =  ["fake_path"]
		parseOutMock.return_value = getParsePlatoFakeDictA()
		expEnergyVal = 7.1
		self.testObjA.run()
		actEnergyVal = getattr(self.testObjA.output,self.outAttr)[0]
		self.assertAlmostEqual(expEnergyVal,actEnergyVal)


def getParsePlatoFakeDictA():
	outDict = dict()
	outDict["energies"] = SimpleNamespace(electronicCohesiveE=14.2)
	outDict["numbAtoms"] = 2
	return outDict


if __name__ == '__main__':
	unittest.main()

