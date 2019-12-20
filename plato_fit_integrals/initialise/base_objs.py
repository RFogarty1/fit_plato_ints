

class PointDefectRunnerBase():

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

