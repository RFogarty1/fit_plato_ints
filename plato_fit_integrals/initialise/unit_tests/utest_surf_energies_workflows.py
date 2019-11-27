#!/usr/bin/python3

import types
import unittest
import unittest.mock as mock

import plato_fit_integrals.initialise.create_surf_energies_workflows as tCode

class TestWorkFlowExtractingSurfaceEnergies(unittest.TestCase):

	def setUp(self):
		self.surfStub = types.SimpleNamespace( ePerAtom=35, nAtoms=20, surfaceArea=5, runComm=["surfRun"], workFolder="fake", writeFiles=mock.Mock() )
		self.bulkStub = types.SimpleNamespace( ePerAtom=33, runComm = [None], workFolder="fake", writeFiles=mock.Mock() )
		self.createWorkFlow()

	def createWorkFlow(self):
		self.testObj = tCode.SurfaceEnergiesWorkFlow(self.surfStub, self.bulkStub)

	def testExpectedSurfEnergyCalculated(self):
		expSurfaceEnergy = 4
		self.createWorkFlow()
		self.testObj.run()
		actSurfaceEnergy = self.testObj.output.surfaceEnergy
		self.assertAlmostEqual(expSurfaceEnergy, actSurfaceEnergy)

	def testExpectedPreShellRunComms(self):
		expPreShellRunComms =  ["surfRun"]
		actPreShellRunComms = self.testObj.preRunShellComms
		self.assertEqual(expPreShellRunComms, actPreShellRunComms)


	def testRaisesWhenWorkFoldersDifferent(self):
		self.bulkStub.workFolder = "whatever"
		with self.assertRaises(ValueError):
			self.createWorkFlow()


if __name__ == '__main__':
	unittest.main()

