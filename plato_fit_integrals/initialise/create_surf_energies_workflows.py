
import types

import plato_fit_integrals.core.workflow_coordinator as wflowCoord


class SurfaceEnergiesWorkFlow(wflowCoord.WorkFlowBase):

	def __init__(self, surfaceObj, bulkObj):
		self.surfObj = surfaceObj
		self.bulkObj = bulkObj

		self._ensureWorkFoldersAreTheSame()

		self._createFilesOnInit()
		self.output = types.SimpleNamespace()


	def _ensureWorkFoldersAreTheSame(self):
		if self.surfObj.workFolder != self.bulkObj.workFolder:
			raise ValueError("surface workFolder must be the same as bulk workFolder.\nSurface path = {}\nBulk path = {}".format(self.surfObj.workFolder, self.bulkObj.workFolder))


	@property
	def preRunShellComms(self):
		runList = list()
		runList.extend( self.surfObj.runComm )
		runList.extend( self.bulkObj.runComm )
		runList = [x for x in runList if x is not None]
		return runList

	def _createFilesOnInit(self):
		self.surfObj.writeFiles()
		self.bulkObj.writeFiles()


	def run(self):
		ePerAtomBulk = self.bulkObj.ePerAtom
		ePerAtomSurf = self.surfObj.ePerAtom
		surfArea = self.surfObj.surfaceArea
		nSurfAtoms = self.surfObj.nAtoms
		surfEnergy = ( nSurfAtoms/(2*surfArea) ) * (ePerAtomSurf - ePerAtomBulk)
		self.output.surfaceEnergy = surfEnergy

#TODO: I want both surfaceObj and bulkObj to have runComm, writeFile() and parseFile methods. The writeFile should use a variable on the object that 
# lets the base folder be set to workFolder. The factory can handle the adapter needed for whatever the easiest to pass input object is

class SurfaceRunnerBase():

	def writeFiles(self):
		raise NotImplementedError()

	@property
	def workFolder(self):
		raise NotImplementedError()

	@workFolder.setter
	def workFolder(self, value):
		raise NotImplementedError()

	@property
	def ePerAtom(self):
		raise NotImplementedError()

	@property
	def nAtoms(self):
		raise NotImplementedError()

	@property
	def runComm(self):
		raise NotImplementedError()

	@property
	def surfaceArea(self):
		raise NotImplementedError()



