
import os

import contextlib
import collections
import copy
import itertools as it
import math
import pathlib
from types import SimpleNamespace, MethodType

import numpy as np

import plato_fit_integrals.core.workflow_coordinator as wflowCoord
import plato_fit_integrals.core.obj_funct_calculator as objFunctCalc
import plato_fit_integrals.initialise.obj_functs_targ_vals as objCmpFuncts

import plato_pylib.plato.mod_plato_inp_files as modInp
import plato_pylib.plato.parse_plato_out_files as parsePlatoOut
import plato_pylib.utils.fit_eos as fitBMod
import plato_pylib.utils.job_running_functs as jobRun

class CreateEosWorkFlow():

	def __init__(self, structDict, modOptDicts, workFolder, platoCode, varyType="pairPot", eosModel="murnaghan", 
	             onlyCalcE0=False, nonE0EnergyDict=None):
		""" Create the EosWorkFlow Factory instance. Follow initiation straight by a call to just get the relevant workflow
		
		Args:
			structDict: keys are structure labels (e.g. hcp, bcc etc.). Values are lists of UnitCell objects
			modOptDicts: keys are struct labels. Values are dicts, each of them containing any keywords to modify from the defaults of plato_pylib
		                 (*.plato.mod_plato_inp_files). Expect to have BlochStates at least in these dicts
			workFolder: Path to folder to carry out calculations in
			platoCode: Str representing command used to call the plato code needed
		    varyType: String denoting which integrals are being fit
			eosModel: The model to use to fit the equation of state. Passed directly to atomic simulation environment (hence see ase.eos for options)
			onlyCalcE0: Optimisation for fitting to pair-pots. If True various run settings that dont affect E0 (e.g. k-points) will be changed for
			            for speed. These Will Overwrite options from modOptDicts.
			nonE0EnergyDict: Only needed when using onlyCalcE0=True. Dict with same structure as structDict, with structures replaced with values of energies
		
		Raises:
			Errors
		"""

		self.structDict = structDict
		self.modOptsDict = modOptDicts
		self.workFolder = os.path.abspath(workFolder)
		self.eosModel = eosModel
		self.varyType = varyType
		self.platoCode = platoCode

		self.nonE0EnergyDict = nonE0EnergyDict
		self.onlyCalcE0 = onlyCalcE0

	@property
	def onlyCalcE0(self):
		return self._onlyCalcE0

	@onlyCalcE0.setter
	def onlyCalcE0(self,val):
		if (val is True) and (self.nonE0EnergyDict is None):
			raise ValueError("onlyCalcE0 cant be used without first setting nonE0EnergyDict")
		self._onlyCalcE0 = val	

	
	@property
	def optDicts(self):
		outDict = dict()
		for key in self.structDict.keys():
			baseDict = {k.lower():v for k,v in modInp.getDefOptDict(self.platoCode).items()}
			currModDict = {k.lower():v for k,v in self.modOptsDict[key].items()}
			self._modDictBasedOnCorrType(currModDict)
			if self.onlyCalcE0:
				self._modDictForE0Only(currModDict)
			baseDict.update(currModDict)
			outDict[key] = baseDict
		return outDict

	def _modDictBasedOnCorrType(self,inpDict):
		if self.varyType.lower() == "pairPot".lower():
			inpDict["addcorrectingppfrombdt".lower()] = 1
			if self.platoCode=="dft2":
				inpDict["e0method"] = 1
		elif self.varyType.lower() == "hopping".lower():
			inpDict["addcorrectinghopfrombdt"] = 1
			if self.platoCode=="dft":
				raise ValueError("varyType = {} is an invalid option for platoCode={}".format(self.varyType,self.platoCode))
		else:
			raise ValueError("varyType = {} is an invalid option".format(self.varyType))

	def _modDictForE0Only(self,inpDict):
		inpDict["blochstates"] = [1,1,1]
		if self.platoCode=="dft2":
			inpDict["xtalxcmethod"] = -1
			inpDict["hopxcmethod"] = -1
			inpDict["xtalVnaMethod".lower()] = 1
			inpDict["hopVnaMethod".lower()] = -1
			inpDict["xtalVnlMethod".lower()] = 1
			inpDict["hopVnlMethod".lower()] = -1

	def __call__(self):
		if self.onlyCalcE0:
			outObj = EosWorkFlow(self.structDict, self.optDicts, self.workFolder, self.platoCode,eosFromOutFilesFunct=getEosOneStructWhenE1Known,energiesMinusE0=self.nonE0EnergyDict)
		else:
			outObj = EosWorkFlow(self.structDict, self.optDicts, self.workFolder, self.platoCode)
		return outObj



class EosWorkFlow(wflowCoord.WorkFlowBase):

	def __init__(self, structDict, runOptsDicts, workFolder, platoCodeStr, eosModel="murnaghan", eosFromOutFilesFunct=None, energiesMinusE0=None):
		self.structDict = collections.OrderedDict(structDict)
		self.runOptsDicts = runOptsDicts
		self.platoCodeStr = platoCodeStr
		self._workFolder = os.path.abspath(workFolder)
		self._eosModel = eosModel

		self._outVals = ["v0","b0","e0","gof"]

		self.output = SimpleNamespace()

		#This is originally a way to allow us to use ONLY the E0 value from the output files
		if eosFromOutFilesFunct is None:
			eosFromOutFilesFunct = standardGetEosOneStruct 
		self._getEosOneStruct = MethodType(eosFromOutFilesFunct,self)

		self.energiesMinusE0 = energiesMinusE0

		#Only need to create the input files at initiation time
		pathlib.Path(self.workFolder).mkdir(exist_ok=True,parents=False)
		self._writeFiles()

	@property
	def preRunShellComms(self):
		#Need to delete previous out-files, since they get appended to (which slows down the parsing MASSIVELY)
		outPaths = [x.replace(".in",".out") for x in self._inpFilePaths]
		with contextlib.suppress(FileNotFoundError):
			[os.remove(x) for x in outPaths]
		inpPaths = self._inpFilePaths
		runComms = jobRun.pathListToPlatoRunComms(inpPaths, self.platoCodeStr)
		return runComms

	@property
	def workFolder(self):
		return os.path.abspath(self._workFolder)

	@property
	def _baseFileNames(self):
		namesDict = self._baseFileNameDict
		outNames = list()
		for sKey in namesDict.keys():
			for fName in namesDict[sKey]:
				outNames.append( fName )
		return outNames

	@property
	def _inpFilePaths(self):
		inpPaths = list()
		for x in self._baseFileNames:
			currPath = os.path.join(self.workFolder, x+".in") 
			inpPaths.append(currPath)
		return inpPaths


	@property
	def namespaceAttrs(self):
		outAttrs = list()
		for key in self.structDict:
			for outVal in self._outVals:
				outAttrs.append( key + "_" + outVal )
		return outAttrs

	@property
	def _baseFileNameDict(self):
		outDict = collections.OrderedDict()
		for sKey in self.structDict.keys():
			outDict[sKey] = list()
			for struct in self.structDict[sKey]:
				currVol = struct.volume
				currFName = "{}_vol_{:.2f}".format(sKey,currVol).replace(".","pt")
				outDict[sKey].append( currFName )
		return outDict

	@property
	def _inpFilePathsDict(self):
		outDict = self._baseFileNameDict
		for key,val in outDict.items():
			for idx,baseName in enumerate(val):
				val[idx] = os.path.join(self.workFolder,baseName + ".in")
		return outDict
				

	def _writeFiles(self):
		pathDict = self._inpFilePathsDict
		for sKey in self.runOptsDicts.keys():
			for idx,geom in enumerate(self.structDict[sKey]):
				currPath = pathDict[sKey][idx]
				currStrDict = modInp.getStrDictFromOptDict(self.runOptsDicts[sKey], self.platoCodeStr)
				geomSection = modInp.getPlatoGeomDictFromUnitCell(geom)
				currStrDict.update(geomSection)
				modInp.writePlatoOutFileFromDict(currPath,currStrDict)

	def run(self):
		for key in self.structDict.keys():
			try:
				fittedEos = self._getEosOneStruct(key)
			except RuntimeError or ValueError: #ValueError is called in the case of NaN values appearing in ase somewhere
				for attr in self.namespaceAttrs:
					setattr(self.output, attr, np.inf)
				return None
			self._setAttrsFromEosModelOneStruct(key,fittedEos)

#
	def _setAttrsFromEosModelOneStruct(self,structKey, fittedEos):
		setattr(self.output,structKey+"_"+"v0", fittedEos["v0"])
		setattr(self.output,structKey+"_"+"b0", fittedEos["b0"])
		setattr(self.output,structKey+"_"+"e0", fittedEos["e0"])
		gof = getRelRMSDForItersTargVsAct( fittedEos["data"][:,1], fittedEos["fitAtDataPoints".lower()][:,1] )
		setattr(self.output,structKey+"_"+"gof", gof)

def standardGetEosOneStruct(self:"eos WorkFlow class", structKey):
	outFilePaths = [x.replace(".in",".out") for x in self._inpFilePathsDict[structKey]]
	with contextlib.redirect_stdout(None):
		fittedEos = fitBMod.getBulkModFromOutFilesAseWrapper(outFilePaths, eosModel=self._eosModel)
	return fittedEos

def getEosOneStructWhenE1Known(self, structKey):
	outFilePaths = [x.replace(".in",".out") for x in self._inpFilePathsDict[structKey]]
	parsedFiles = [parsePlatoOut.parsePlatoOutFile(x) for x in outFilePaths]
	allE0Vals = [x["energies"].e0Coh for x in parsedFiles]
	allTotalEnergies = [e0+eOther for e0,eOther in it.zip_longest(allE0Vals, self.energiesMinusE0[structKey])] #in Ry
	allTotalEnergiesPerAtom = [x/parsed["numbAtoms"] for x,parsed in it.zip_longest(allTotalEnergies,parsedFiles)]
	allVolumes = [x["unitCell"].volume /x["numbAtoms"] for x in parsedFiles] #in bohr units
	
	#Do the conversions:
	bohrCubedToAngCubed = 1*(1/(fitBMod.ANG_TO_BOHR**3))
	rydToEv = 1/fitBMod.EV_TO_RYD
	volInAng = [bohrCubedToAngCubed*x for x in allVolumes]
	energiesInEv = [rydToEv*x for x in allTotalEnergiesPerAtom]

	#Fit, answers are in bohr^3 and eV
	with contextlib.redirect_stdout(None):
		fittedEos = fitBMod.getBulkModFromVolsAndEnergies(volInAng, energiesInEv)

	return fittedEos

def calcNonE0EnergyDict(structDict, modOptDicts, workFolder, platoCode, nCores=1,quiet=True,varyType="pairpot"):
	eosWorkFlow = CreateEosWorkFlow(structDict, modOptDicts, workFolder, platoCode, varyType=varyType) ()#Note this will write the files and create the folder upon initiation
	inpFilesDict = eosWorkFlow._inpFilePathsDict 
	runComms = eosWorkFlow.preRunShellComms
	jobRun.executeRunCommsParralel(runComms, nCores, quiet=quiet)

	outEnergies = copy.deepcopy(inpFilesDict)
	for key in outEnergies.keys():
		for idx in range(len(outEnergies[key])):
			outPath = outEnergies[key][idx].replace(".in",".out")
			outEnergies[key][idx] = _getNonE0EnergyOneOutFile(outPath)
	return outEnergies


def _getNonE0EnergyOneOutFile(outPath):
	parsedFile = parsePlatoOut.parsePlatoOutFile(outPath)
	return parsedFile["energies"].electronicCohesiveE - parsedFile["energies"].e0Coh

def getRelRMSDForItersTargVsAct(iterTarg,iterAct):
	totVal = 0.0
	for targ,act in it.zip_longest(iterTarg,iterAct):
		totVal += math.sqrt( (targ-act)**2 )
	return totVal/len(iterTarg)


def decorateEosWorkFlowWithPrintOutputsEveryNSteps(inpObj,printInterval=5):
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



class EosObjFunctCalculator(objFunctCalc.ObjectiveFunctCalculator):
	def __init__(self,propList, structList, targVals, weightList, objFunctList):
		self._propList = list(propList)
		self._structList = list(structList)
		self._weightList = list(weightList)
		self._objFunctList = list(objFunctList)
		self._targVals = list(targVals)

		self._checkValidFields()
		self._compositeObjFunctCalc = self._createObjFunctCalculator

	@classmethod
	def createEmptyInstance(cls):
		return cls(list(),list(),list(),list(),list())

	@property
	def props(self):
		propList = list()
		for x,y in it.zip_longest(self._structList,self._propList):
			currProp = "{}_{}".format(x,y)
			propList.append(currProp)
		return propList

	def _checkValidFields(self):
		self._checkAllListsEqualLen()
		self._checkNoDuplicateProperties()


	def _checkAllListsEqualLen(self):
		propLists = [self._propList, self._structList, self._weightList, self._objFunctList, self._targVals]
		lenLists = [len(x) for x in propLists]
		assert all([x==lenLists[0] for x in lenLists]), "inequal lists detected"

	def _checkNoDuplicateProperties(self):
		allProps = self.props
		if len(set(allProps)) != len(allProps):
			raise ValueError("Duplicate properties present in list {}".format(self.props))

	def calculateObjFunction(self, calcVals):
		calculator = self._createObjFunctCalculator()
		return calculator.calculateObjFunction(calcVals)

	def _createObjFunctCalculator(self):
		allContribs = list()
		propList = self.props
		for idx in range(len(self._propList)):
			currPropTargObjFuncts = SimpleNamespace( **{propList[idx]:(self._targVals[idx],self._objFunctList[idx])} )
			currContrib = objFunctCalc.ObjectiveFunctionContrib(currPropTargObjFuncts)
			allContribs.append( currContrib )
		totalCalculator = objFunctCalc.ObjectiveFunctTotal(allContribs, self._weightList)
		return totalCalculator


	def addProp(self, structKey, prop:"v0,e0,b0", targVal, weight=1.0, objFunct=None ):
		if objFunct is None:
			objFunct = objCmpFuncts.createSimpleTargValObjFunction("relRootSqrDev".lower())

		self._propList.append(prop)
		self._structList.append(structKey)
		self._objFunctList.append(objFunct)
		self._weightList.append(weight)
		self._targVals.append(targVal)

		self._checkAllListsEqualLen()
		self._checkNoDuplicateProperties()



