
import contextlib
import copy
import os
import pathlib
from types import SimpleNamespace

import plato_fit_integrals.core.workflow_coordinator as wFlowCoord
from plato_fit_integrals.shared.workflow_helpers import getCombinedNamespaceNoDuplicatedKeys


import plato_pylib.plato.mod_plato_inp_files as modInp
import plato_pylib.utils.job_running_functs as jobRun
import plato_pylib.plato.parse_plato_out_files as parsePlatoOut
import plato_pylib.utils.defects as defects

class CreateInterstitialWorkFlow():
	def __init__(self, structRef, structInter, startFolder, modOptDict, platoComm, genPreShellComms=True, relaxed="relaxed", interType="generic", cellDims=None, eType="electronicCohesiveE"):
		""" Creates InterstitialWorkFlow Factory instance. Follow initiation straight by a call to just get the relevant workflow 
		
		Args:
			structRef: UnitCell object for the structure with no interstitial
			structInter: UnitCell object for the structure with an interstitial
			startFolder: Base directory to carry out calculations in. Calculations will be done at least ONE directory deeper
			modOptDict: keys are struct labels. Values are dicts, each of them containing any keywords to modify from the defaults of plato_pylib
		                 (*.plato.mod_plato_inp_files). Expect to have BlochStates at least in these dicts
			platoComm: Str, plato program used. tb1/dft2/dft are supported options at time of writing
			genPreShellComms(Optional): Bool, whether the created objects can generate plato-run commands. If False, no plato jobs will be run.
			                            Purpose is to make workFlows easier to use outside fitting code. Default=True
			eType(Optional): str, the energy type to use. See energies object in plato_pylib. One possible option is electronicTotalE

		Optional Args for object labelling:
		These optional arguments are all used to label the created object, such that you calculate multiple
		types of interstitial with the same workFlowCoordinator

			relaxed: str representing relaxation type (recommended are unrelaxed/relaxed_constant_p/relaxed_constant_v). Used to tell
			         the difference between created objects
			cellDims: 3-element iter, the dimensions of the supercell your calculating
			interType: str, label for the type of interstitial being calculated (e.g. octahedral)
 
		Raises:
			Errors

		"""
		self.structRef = structRef
		self.structInter = structInter
		if cellDims is None:
			cellDims = [1,1,1]
		self.cellDims = [int(x) for x in cellDims]
		self.interType = interType
		self.relaxed = relaxed
		self.startFolder = os.path.abspath(startFolder)
		self.modOptDict = modOptDict
		self.platoComm = platoComm
		self.genPreShellComms = genPreShellComms
		self.eType = eType

	def getRunOptsDict(self):
		outDict = modInp.getDefOptDict(self.platoComm)
		outDict.update(self.modOptDict)	
		return outDict

	def __call__(self):
		cellDimStr = "_".join([str(x) for x in self.cellDims])
		outLabel =  "{}_{}_{}".format(self.interType, self.relaxed, cellDimStr)
		workFolder = os.path.abspath( os.path.join(self.startFolder,outLabel) )
		runOptsDict = self.getRunOptsDict()
		return InterstitialWorkFlow(self.structInter, self.structRef, workFolder, self.platoComm, runOptsDict, outLabel, genPreShellComms=self.genPreShellComms, eType=self.eType)


class CompositeInterstitialWorkFlow(wFlowCoord.WorkFlowBase):
	""" Composite of interstitialWorkFlows, same interface as an individual one """
	def __init__(self, interstitWorkFlows):
		""" Create a Composite of interstitial work flows
		
		Args:
			interstitWorkFlows: (iter) of interstitWorkFlow objects
		Raises:
			ValueError: If duplicate attributes or workFolders are found

		Limitations:
			SLIGHT amount of care needed when using multiple composites in a single workFlow co-ordinator. It cant properly ensure there are no overlaps
			between individual workFolders. This shouldnt be a problem if all workFlows are created with the factory method, since the workFolders are based on 
			the namespaceAttrs (which are properly checked for duplication).

		"""
		self._workFlows = interstitWorkFlows
		self._ensureNoDuplicateAttrs()
		self._ensureNoDuplicateWorkFolders() #imperfect implementation for composite of composites

	def _ensureNoDuplicateAttrs(self):
		allAttrs = self.namespaceAttrs
		uniqueAttrs = list(set(allAttrs))
		numbAttrs, numbUnique = len(allAttrs), len(uniqueAttrs)
		numbDuplicateAttrs = numbAttrs - numbUnique
		if numbDuplicateAttrs != 0:
			raise ValueError("{} duplicate attributes found when creating/modifying CompositeInterstitialWorkFlow".format(numbDuplicateAttrs))


	def _ensureNoDuplicateWorkFolders(self):
		allWorkFolders = [x.workFolder for x in self._workFlows if x is not None] #None should only be returned for composite objects
		numbFolders, numbUnique = len(allWorkFolders), len(set(allWorkFolders))
		numbDuplicates = numbFolders - numbUnique
		if numbDuplicates != 0:
			raise ValueError("{} duplicate workFolders found when creating/modifying CompositeInterstitialWorkFlow".format(numbDuplicates))

	@property
	def namespaceAttrs(self):
		outAttrs = list()
		for obj in self._workFlows:
			outAttrs.extend(obj.namespaceAttrs)
		return outAttrs

	@property
	def workFolder(self):
		""" Not meaningful for the case of a composite object """
		return None


	@property
	def preRunShellComms(self):
		allComms = list()
		for obj in self._workFlows:
			currComms = obj.preRunShellComms
			if currComms is not None:
				allComms.extend(currComms)

		if len(allComms)==0:
			allComms = None

		return allComms

	def run(self):
		for obj in self._workFlows:
			obj.run()
	
		#Combine namespace objects, asserting that we dont lose any due to 
		allOutput = [copy.deepcopy(x.output) for x in self._workFlows]
		refNamespace = allOutput[0]
		if len(allOutput) == 1:
			self.output = refNamespace
			return None
	
		for x in allOutput[1:]:
			refNamespace = getCombinedNamespaceNoDuplicatedKeys(refNamespace, x)
		self.output = refNamespace
		
	

class InterstitialWorkFlow(wFlowCoord.WorkFlowBase):

	def __init__(self, interstitStruct, refStruct, workFolder, platoComm, runOptsDict, label, genPreShellComms=True, eType="electronicCohesiveE"):
		""" Dont call directly, see CreateInterstitialWorkFlow factory class """
		self._interstitStruct = interstitStruct
		self._refStruct = refStruct
		self._workFolder = os.path.abspath(workFolder)
		self._platoComm = platoComm
		self._runOptsDict = runOptsDict
		self._eType = eType
		self.label = label
		self.genPreShellComms = genPreShellComms

		#Only need to create the input files at initiation time
		pathlib.Path(self.workFolder).mkdir(exist_ok=True,parents=True)
		self._writeFiles()

	@property
	def preRunShellComms(self):
		if self.genPreShellComms is False:
			return None
		outPaths = [x.replace(".in",".out") for x in self._inpFilePaths]
		with contextlib.suppress(FileNotFoundError):
			[os.remove(x) for x in outPaths]
		runComms = jobRun.pathListToPlatoRunComms(self._inpFilePaths, self._platoComm)
		return runComms

	@property
	def workFolder(self):
		return self._workFolder

	@property
	def namespaceAttrs(self):
		return [self.label + "_interstit_e"]

	@property
	def _inpFilePaths(self):
		return [x+".in" for x in self._baseFilePaths]

	@property
	def _baseFilePaths(self):
		baseNames = self._baseFileNames
		basePaths = [os.path.join(self.workFolder,x) for x in baseNames]
		return basePaths

	@property
	def _baseFileNames(self):
		return ["inter","no_inter"]

	@property
	def _inpFilePathDict(self):
		fileList = self._inpFilePaths
		outDict = {"inter":fileList[0], "no_inter":fileList[1]}
		return outDict

	@property
	def _strOptDict(self):
		return modInp.getStrDictFromOptDict(self._runOptsDict,self._platoComm)

	def _writeFiles(self):
		self._writeNoInterFile()
		self._writeInterFile()

	def _writeNoInterFile(self):
		outPath = self._inpFilePathDict["no_inter"]
		geomSection = modInp.getPlatoGeomDictFromUnitCell(self._refStruct)
		strDict = self._strOptDict
		strDict.update(geomSection)
		modInp.writePlatoOutFileFromDict(outPath,strDict)

	def _writeInterFile(self):
		outPath = self._inpFilePathDict["inter"]
		geomSection = modInp.getPlatoGeomDictFromUnitCell(self._interstitStruct)
		strDict = self._strOptDict
		strDict.update(geomSection)
		modInp.writePlatoOutFileFromDict(outPath,strDict)

	def _parseOutputFiles(self):
		inpPaths = self._inpFilePathDict
		parsedInter = parsePlatoOut.parsePlatoOutFile_energiesInEv(inpPaths["inter"].replace(".in",".out"))
		parsedNoInter = parsePlatoOut.parsePlatoOutFile_energiesInEv(inpPaths["no_inter"].replace(".in",".out"))
		
		parsedEnergies = [getattr(x["energies"], self._eType) for x in [parsedInter,parsedNoInter]]
		parsedNAtoms = [x["numbAtoms"] for x in [parsedInter,parsedNoInter]]

		outObjs = [SimpleNamespace(energy=parsedEnergies[0], nAtoms=parsedNAtoms[0]),
		           SimpleNamespace(energy=parsedEnergies[1], nAtoms=parsedNAtoms[1])]

		assert parsedNAtoms[0]!=parsedNAtoms[1], "Different amount of atoms required for interstitial vs non-interstitial structures"

		return outObjs

	def run(self):
		#Get index for the interstitial
		parsedData = self._parseOutputFiles()
		nAtomsList = [x.nAtoms for x in parsedData]
		interIndex = nAtomsList.index(max(nAtomsList)) #one with more atoms is the interstitial; guarding against user mixing up structs
		refIndex = nAtomsList.index(min(nAtomsList))
		interEnergy, refEnergy = parsedData[interIndex].energy, parsedData[refIndex].energy
		numbInters = parsedData[interIndex].nAtoms - parsedData[refIndex].nAtoms
		interstitEnergy = defects.calcInterstitialE(refEnergy, interEnergy, parsedData[refIndex].nAtoms, nInter=numbInters)

		#Now move the interstitial energy to the ouput	
		self.output = SimpleNamespace( **{self.namespaceAttrs[0]:interstitEnergy} )

