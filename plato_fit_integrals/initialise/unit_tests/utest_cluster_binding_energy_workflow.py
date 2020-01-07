#!/usr/bin/python3

import types
import unittest
import unittest.mock as mock

import plato_fit_integrals.initialise.create_cluster_binding_energy_workflows as tCode

class TestBindingEnergyClusterWorkFlow(unittest.TestCase):

	def setUp(self):
		self.clusterStub = types.SimpleNamespace(nMolecules=4, totalEnergy=8, writeFiles=mock.Mock())
		self.monomerStub = types.SimpleNamespace(nMolecules=1, totalEnergy=1, writeFiles=mock.Mock())
		self.createTestObj()

	def createTestObj(self):
		self.testObj = tCode.ClusterBindingEnergyWorkFlow(self.clusterStub, self.monomerStub)

	def testErrorRaisedIfMonomerHasMultpipleMolecules(self):
		self.monomerStub.nMolecules = 2
		with self.assertRaises(AssertionError):
			self.createTestObj()

	def testExpectedBindingEnergyObtained(self):
		expBindingEnergy = 4
		self.testObj.run()
		actBindingEnergy = self.testObj.output.bindingEnergy
		self.assertEqual(expBindingEnergy, actBindingEnergy)


if __name__ == '__main__':
	unittest.main()

