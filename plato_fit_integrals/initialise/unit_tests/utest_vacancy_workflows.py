#!/usr/bin/python3

import types
import unittest
import unittest.mock as mock

import plato_fit_integrals.initialise.create_vacancy_workflows as tCode

class TestVacancyWorkFlow(unittest.TestCase):

	def setUp(self):
		self.stubBulk = types.SimpleNamespace(ePerAtom=35, nAtoms=20, workFolder="fake", writeFiles=mock.Mock() )
		self.stubVac = types.SimpleNamespace(ePerAtom=36, nAtoms=19, workFolder="fake", writeFiles=mock.Mock() )
		self.createTestObj()

	def createTestObj(self):
		self.testObj = tCode.VacancyWorkFlow(self.stubVac, self.stubBulk)

	def testExpectedVacancyEnergyObtained(self):
		expVacEnergy = self.stubVac.nAtoms* ( self.stubVac.ePerAtom -  self.stubBulk.ePerAtom )
		self.testObj.run()
		actVacEnergy = self.testObj.output.vacEnergy
		self.assertAlmostEqual(expVacEnergy, actVacEnergy)


if __name__ == '__main__':
	unittest.main()

