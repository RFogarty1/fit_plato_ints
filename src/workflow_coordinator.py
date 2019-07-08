from types import SimpleNamespace

class WorkFlowCoordinator():
	def __init__(self, workFlows:"list of WorkFlow objects"):
		self._workFlows = workFlows
		self._ensureNoDuplicationBetweenWorkFlows()


	def runAndGetPropertyValues(self):
		self.run()
		return self.propertyValues()

	def run(self):
		for x in self._workFlows:
			x.run()

	@property
	def propertyValues(self):
		currNamespace = SimpleNamespace()
		for x in self._workFlows:
			currNamespace = getCombinedNamespaceNoDuplicatedKeys(currNamespace, x.output)
		return currNamespace

	def addWorkFlow(self,wFlow):
		""" Add a workFlow
	
		Args:
			wFlow: WorkFlow object
				
		Returns
			Nothing
		
		Raises:
			ValueError: If new workflow contains duplication(fields or workfolder) with current workflows. The workflow
			            will still be added if you catch this error (not recommended though)
		"""
		self._workFlows.append(wFlow)
		self._ensureNoDuplicationBetweenWorkFlows()
	
	def _ensureNoDuplicationBetweenWorkFlows(self):
		self._ensureWorkFlowsContainNoDuplicatedFields()
		self._ensureWorkFlowsContainNoDuplicateWorkFolders()

	def _ensureWorkFlowsContainNoDuplicatedFields(self):
		allFields = list()
		for x in self._workFlows:
			for field in x.namespaceAttrs:
				if field in allFields:
					raise ValueError("Duplicate field {} found in different workflows".format(field))
				else:
					allFields.append(field)

	def _ensureWorkFlowsContainNoDuplicateWorkFolders(self):
		allWorkFolders = list()
		for x in self._workFlows:
			if x.workFolder in allWorkFolders:
				raise ValueError("Duplicate work folders {} found in different workflows".format(x.WorkFolder))
			else:
				allWorkFolders.append(x.workFolder)


def getCombinedNamespaceNoDuplicatedKeys(nSpaceA:"types.SimpleNamespace", nSpaceB):
	dictA, dictB = vars(nSpaceA), vars(nSpaceB)

	#Check for ducplication
	keysA, keysB = list(dictA.keys()), list(dictB.keys())
	assert len(keysA) + len(keysB) == len( keysA+keysB ), "Duplicate keys not supported"

	dictA.update(dictB)
	return SimpleNamespace(**dictA)


#TODO: May add getPreRunShellCommands - a set of shell cmds that can all be run in parralel before starting
#      This will let me run plato-jobs from any number of workflows all in parralel[this should be the slow step always]
class WorkFlowBase():

	@property
	def preRunShellComms(self):
		""" List of string commands that will get run before run() is called. Higher-level functions can therefore 
		    combine these for a set of WorkFlows, which should lead to more efficient parralelisation. Return None or
		    empty list to not run any of these commands.
		
		"""
		return None

	@property
	def namespaceAttrs(self):
		raise NotImplementedError()

	@property
	def workFolder(self):
		raise NotImplementedError()

	def run(self):
		""" Runs the workflow and returns a Namespace
		    with the calculated properties as fields
				
		Returns
			Namespace containing all fields defined in namespaceAttrs. MUST be lower case
		
		"""
		raise NotImplementedError()


