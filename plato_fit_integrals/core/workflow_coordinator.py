
import plato_pylib.utils.job_running_functs as jobRun
from types import SimpleNamespace

class WorkFlowCoordinator():
	def __init__(self, workFlows:"list of WorkFlow objects", nCores=1, quietPreShellComms=True):
		self._workFlows = workFlows
		self._ensureNoDuplicationBetweenWorkFlows()
		self._nCores = nCores
		self.quietPreShellComms = quietPreShellComms

	def runAndGetPropertyValues(self, inclPreRun=True):
		self.run(inclPreRun)
		return self.propertyValues

	def run(self,inclPreRun=True):
		if inclPreRun:
			self._doPreRunComms()
		for x in self._workFlows:
			x.run()

	def _doPreRunComms(self):
		preRunComms = list()
		for x in self._workFlows:
			currShellComms = x.preRunShellComms
			if x.preRunShellComms is not None:
				preRunComms.extend(currShellComms)
	
		jobRun.executeRunCommsParralel(preRunComms,self._nCores,quiet=self.quietPreShellComms)


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
			if (x.workFolder in allWorkFolders) and (x.workFolder is not None):
				raise ValueError("Duplicate work folders {} found in different workflows".format(x.workFolder))
			else:
				allWorkFolders.append(x.workFolder)


def getCombinedNamespaceNoDuplicatedKeys(nSpaceA:"types.SimpleNamespace", nSpaceB):
	dictA, dictB = vars(nSpaceA), vars(nSpaceB)

	#Check for ducplication
	keysA, keysB = list(dictA.keys()), list(dictB.keys())
	assert len(keysA) + len(keysB) == len( keysA+keysB ), "Duplicate keys not supported"

	dictA.update(dictB)
	return SimpleNamespace(**dictA)


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
		""" List of attribute names for the properties this workspace calculates + places in a Namespace. See run()
		
		"""
		raise NotImplementedError()

	@property
	def workFolder(self):
		raise NotImplementedError()

	def run(self):
		""" Runs the workflow and populates the output attr wtih a Namespace
		containing calculated properties/values as fields/values. Field names should match those in namespaceAttrs
				
		
		"""
		raise NotImplementedError()


def decorateWorkFlowWithPrintOutputsEveryNSteps(inpObj,printInterval=5):
    f = inpObj.run
    stepNumb = 0
    def runPlusOutput():
        nonlocal stepNumb
        f()
        if (stepNumb%printInterval)==0:
            print(inpObj.output)
        stepNumb += 1
        return None
    inpObj.run = runPlusOutput
    return None

