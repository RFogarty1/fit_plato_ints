
import types

import plato_fit_integrals.core.workflow_coordinator as wflowCoord


#NOTE: Lots of duplication from surface energies workflow
class VacancyWorkFlow(wflowCoord.WorkFlowBase):

	def __init__(self, vacRunner:"PointDefectRunnerBase", bulkRunner:"PointDefectRunnerBase"):
		self.vacRunner = vacRunner
		self.bulkRunner = bulkRunner

		self._ensureWorkFoldersAreTheSame()
		self._createFilesOnInit()
		self.output = types.SimpleNamespace()


	def _ensureWorkFoldersAreTheSame(self):
		if self.vacRunner.workFolder != self.bulkRunner.workFolder:
			raise ValueError("vacRunner workFolder must be the same as bulk workFolder.\nvacRunner path = {}\nBulk path = {}".format(self.vacRunner.workFolder, self.bulkRunner.workFolder))

	@property
	def preRunShellComms(self):
		runList = list()
		runList.extend( self.vacRunner.runComm )
		runList.extend( self.bulkRunner.runComm )
		runList = [x for x in runList if x is not None]
		return runList

	def _createFilesOnInit(self):
		self.vacRunner.writeFiles()
		self.bulkRunner.writeFiles()

	def run(self):
		vacEnergy = self.vacRunner.nAtoms* (self.vacRunner.ePerAtom - self.bulkRunner.ePerAtom)
		self.output.vacEnergy = vacEnergy

	@property
	def namespaceAttrs(self):
		return ["vacEnergy"]

	@property
	def workFolder(self):
		self._ensureWorkFoldersAreTheSame()
		return self.vacRunner.workFolder
