import contextlib
import copy
import itertools as it
import os
import pathlib
from types import SimpleNamespace

import plato_pylib.plato.parse_plato_out_files as platoOut
import plato_pylib.plato.mod_plato_inp_files as modInp
import plato_pylib.shared.ucell_class as UCell
import plato_pylib.utils.job_running_functs as jobRun

import plato_fit_integrals.core.obj_funct_calculator as objFunctCalc
import plato_fit_integrals.core.workflow_coordinator as wflowCoord
import plato_fit_integrals.initialise.obj_functs_targ_vals as ObjCmpFuncts
import plato_fit_integrals.shared.workflow_helpers as wFlowHelpers


def createDimerDissocCurveStructs(dists:list, atomA:str, atomB:str):
	""" Creates a set of UnitCell geometries for carrying out dimer-dissociation curve calculations
	
	Args:
		dists (list): List of distances between the two atoms
		atomA (str): Symbol for first atom
		atomB (str): Symbol for second atom

	Returns
		List of UnitCell objects with the specified separations. Ordering same as input dists.
	
	Raises:
		Errors
	"""

	cubeSide = 100
	lattVects = [ [cubeSide, 0.0	 , 0.0	 ],
				  [0.0	 , cubeSide, 0.0	 ],
				  [0.0	 , 0.0	 , cubeSide] ]
	
	outGeoms = list()
	for x in dists:
		zFractDisp = x/cubeSide
		atomACoords = [cubeSide/2 for x in range(3)] + [atomA]
		atomBCoords = list(atomACoords)
		atomBCoords[2] += zFractDisp
		atomBCoords[-1] = atomB
		currFractCoords = [atomACoords, atomBCoords]
		currUCell = UCell.UnitCell.fromLattVects(lattVects,fractCoords=currFractCoords)
		outGeoms.append(currUCell)
		
	return outGeoms
	

def getSepTwoAtomsInUnitCellStruct(uCellStruct, atomAIdx=0, atomBIdx=1):
	""" Finds the distance between two atoms in a unit-cell structure from their indices.
	Original goal is just to use this to get separation for a dimer.
	
	Args:
		uCellStruct: UnitCell object (from plato_pylib.shared.ucell_class) with atomic co-ords set
		atomAIdx: List index (within the UnitCell object) of the first atom
		atomBIdx: List index (within the UnitCell object) of the second atom
	Returns
		Distance between atomA and atomB
	
	"""
	cartGeom = uCellStruct.cartCoords
	atomAPos = cartGeom[atomAIdx][:3]
	atomBPos = cartGeom[atomBIdx][:3]
	distance = _getDistTwoVectors(atomAPos, atomBPos)

	return distance



def _getDistTwoVectors(vectA,vectB):
	sqrDiff = [(b-a)**2 for a,b in it.zip_longest(vectA,vectB)]
	dist = (sum(sqrDiff))**0.5
	return dist


def createObjFunctCalculatorFromEcurveWorkflow(inpWorkFlow, targetVals, functTypeStr, averageMethod="mean",catchOverflow=True, errorRetVal=1e30,
 normToErrorRetVal=False, greaterThanIsOk=False, shiftToRefVals=True, **kwargs):
	""" Creates an objective function calculator from an input workflow of class StructEnergiesWorkFlow.
	    Works only because this workflow should only have a single output field.
	
	Args:
		inpWorkFlow: StructEnergiesWorkFlow instance
		targetVals: List of the target energies
		functTypeStr: Type of function to use for objective function - see createSimpleTargValObjFunction in
		              obj_functs_targ_vals for details/options
		shiftToRefVals(bool): Only does anything if dealing with relEnergies. In which case outputValues are made relative to the structure thats 0-energy in targetVals
		                      before calculating errors (i.e. the identity of the 0-energy structure is ALWAYS the same and based on the target structures)
		**kwargs: These are all passed unchanged to createSimpleTargValObjFunction; see that function for details

	Returns
		objFunctCalculator: Object with a calculateObjFunction(calcValues) method, i.e. it returns an objective function when
		                    passed a list of values corresponding to calculated energies for the set of input structures
	
	Raises:
		ValueError: If invalid value of averageMethod is passed (error type may change later)
		ValueError: If relEnergies is set on workflow, but no value near zero is found in targetVals
		KeyError: If invalid value of functTypeStr is passed
		AssertionError: If the input workflow has more than one output attribute
	"""

	objAttrs = inpWorkFlow.namespaceAttrs
	assert len(objAttrs) == 1, "Valid workflow must have only one output attribute"

	#Check we have a near-zero value if fitting to rel-errors
	if inpWorkFlow.relEnergies:
		minAbsEnergies = min([ abs(x) for x in targetVals ])
		assert minAbsEnergies < 1e-5, "At least 1 energy needs to be close to zero when fitting to relative energies curves"


	attrName = objAttrs[0]
	cmpFunct = ObjCmpFuncts.createVectorisedTargValObjFunction(functTypeStr, averageMethod=averageMethod, catchOverflow=catchOverflow, errorRetVal=errorRetVal,normToErrorRetVal=normToErrorRetVal, greaterThanIsOk=greaterThanIsOk, **kwargs)

	if shiftToRefVals and inpWorkFlow.relEnergies:
		equaliseFunct = _getEqualizeZerosForRelEnergiesFunct()
		cmpFunct = _wrapCmpFunctAroundPreProcessFunct(cmpFunct,equaliseFunct)

	objFunct = objFunctCalc.ObjectiveFunctionContrib( SimpleNamespace(**{attrName:(targetVals,cmpFunct)}) ) 
	return objFunct


def _wrapCmpFunctAroundPreProcessFunct(cmpFunct, preProcessFunct):
	def outFunct(targVals, actVals):
		processed = preProcessFunct(targVals, actVals)
		return cmpFunct(*processed)
	return outFunct

def _getEqualizeZerosForRelEnergiesFunct():
	def outFunct(targVals,actVals):
		minIdx = targVals.index( min(targVals) )	#Responsibility of higher level functions to make sure min energy is zero
		refEnergy = actVals[minIdx]
		newActVals = [x-refEnergy for x in actVals]
		return (targVals,newActVals)
	return outFunct

##Used to make sure the same structure is always treated as the zero energy structure
#def _wrapEqualiseZerosForRelEnergies(funct):
#	def outFunct(targVals,actVals):
#		minIdx = targVals.index( min(targVals) )	#Responsibility of higher level functions to make sure min energy is zero
#		refEnergy = actVals[minIdx]
#		newActVals = [x-refEnergy for x in actVals]
#		return (targVals,newActVals)
#	return outFunct


#Factory has as similar as possible an interface with the EOS one at time of writing
class CreateStructEnergiesWorkFlow():
	def __init__(self, structList, modOptsDict, workFolder, platoCode, varyType="pairPot", outAttr="energy_vals", eType="electronicCohesiveE", ePerAtom=False, relEnergies=False):
		""" Create the StructureEnergies Factory instance. Follow initiation straight by a call to just get the relevant workflow
		
		Args:
			structList: List of UnitCell objects containing the structures to run calculations on
			modOptsDict: dict containing any keywords to modify from the defaults of plato_pylib
			             (*.plato.mod_plato_inp_files). Expect to have BlochStates set at miniimum.
			workFolder: Path to folder to carry out calculations in
			platoCode: Str representing command used to call the plato code needed
			varyType: String (case insensitive) denoting which integrals are being fit. Opts={\"pairPot\",\"hopping\",None}
			outAttr: String that will appears in workflows output (i.e. the key to get the set of energies after running the workflow)
			eType: String denoting the type of energy to take from the outfile. See plato_pylib EnergyVals class for options
			ePerAtom: Bool, if True the total energy is divided by number of atoms in the simulation cell
			relEnergies: Bool, if True then try to fit to energies relative to the lowest energy of structList (i.e. absolute values irrelevant)

		Raises:
			Errors
		"""

		self.structList = structList
		self.modOptsDict = {k.lower():v for k,v in modOptsDict.items()}
		self.workFolder = os.path.abspath(workFolder)
		self.platoCode = platoCode
		self.outAttr = outAttr
		self.varyType = varyType
		self.eType = eType
		self.ePerAtom = ePerAtom
		self.relEnergies = relEnergies

	@property
	def optDict(self):
		outDict = {k.lower():v for k,v in modInp.getDefOptDict(self.platoCode).items()}
		wFlowHelpers.modOptDictBasedOnCorrTypeAndPlatoCode(outDict, self.varyType, self.platoCode)
		outDict.update(self.modOptsDict)
		return outDict

	def __call__(self):
		outObj = StructEnergiesWorkFlow(self.structList, self.optDict, self.workFolder, self.platoCode,self.outAttr, self.varyType, eType=self.eType, ePerAtom=self.ePerAtom, relEnergies=self.relEnergies)
		return outObj




class StructEnergiesWorkFlow(wflowCoord.WorkFlowBase):
	def __init__(self, structList, runOpts, workFolder, platoCodeStr, outAttr, varyType, eType="electronicCohesiveE", ePerAtom=False, relEnergies=False):
		self.platoCodeStr = platoCodeStr
		self.runOpts = runOpts
		self._workFolder = os.path.abspath(workFolder)
		self.outAttr = outAttr
		self.output = SimpleNamespace()
		self.structList = structList
		self.eType=eType
		self.varyType=varyType
		self.ePerAtom = ePerAtom
		self.relEnergies = relEnergies	
 
		#Need to create input files only once, on initiation
		pathlib.Path(self.workFolder).mkdir(exist_ok=True,parents=True)
		self._writeInpFiles()
		
	@property
	def preRunShellComms(self):
		#Remove any previous jobs to stop the *.out files becoming too long (new jobs append to them)
		with contextlib.suppress(FileNotFoundError):
			[os.remove(x) for x in self.outFilePaths]
		return jobRun.pathListToPlatoRunComms(self.inpFilePaths, self.platoCodeStr)
		
	@property
	def workFolder(self):
		return os.path.abspath(self._workFolder)
	
	@property
	def namespaceAttrs(self):
		return [self.outAttr]
	
	def run(self):
		allEnergies = list()
		for x in self.outFilePaths:
			parsedFile = platoOut.parsePlatoOutFile(x)
			currEnergy = getattr(parsedFile["energies"],self.eType)
			if self.ePerAtom:
				currEnergy = currEnergy / parsedFile["numbAtoms"]
			allEnergies.append(currEnergy)
		if self.relEnergies:
			minE = min(allEnergies)
			allEnergies = [x-minE for x in allEnergies]

		setattr(self.output, self.outAttr, allEnergies)

	def _writeInpFiles(self):
		strDictNoGeom = modInp.getStrDictFromOptDict(self.runOpts,self.platoCodeStr)
		structDicts = [modInp.getPlatoGeomDictFromUnitCell(x) for x in self.structList]
		for fPath,struct in it.zip_longest(self.inpFilePaths, structDicts):
			currOutDict = copy.deepcopy(strDictNoGeom)
			currOutDict.update(struct)
			modInp.writePlatoOutFileFromDict(fPath,currOutDict)

	@property
	def baseFileNames(self):
		outNames = list()
		fileNameFmt = "struct_energies_{}"
		for x in range( len(self.structList) ):
			outNames.append(  fileNameFmt.format(x)  )
		return outNames
	
	@property
	def inpFilePaths(self):
		return [os.path.join(self.workFolder,x)+".in" for x in self.baseFileNames]
	
	@property
	def outFilePaths(self):
		return [os.path.join(self.workFolder,x)+".out" for x in self.baseFileNames]

