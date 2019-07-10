
import copy
import itertools as it
import os

import plato_pylib.plato.parse_tbint_files as parseTbint

class CoeffsTablesConverter():
	
	def __init__(self, analyticalReprs:list, integInfoTables:list, integHolder:"IntegralsHolder obj"):
		self._analyticalReps = list(analyticalReprs)
		self._integInfo = list(integInfoTables)
		self._integHolder = integHolder


	@property
	def coeffs(self):
		outCoeffs = list()
		for aRep in self._analyticalReps:
			outCoeffs.extend(aRep.coeffs)
		return outCoeffs

	@coeffs.setter
	def coeffs(self,val:list):
		startIdx = 0
		for aRep in self._analyticalReps:
			aRep.coeffs = val[startIdx:startIdx+aRep.nCoeffs]
			startIdx += aRep.nCoeffs

	def writeTables(self):
		self._updateTables()
		self._writeTables()

	def _updateTables(self):
		for x in range(len(self._integInfo)):
			self._updateSingleTable(x)

	def _updateSingleTable(self,idx):
		integStr, atomA, atomB = self._integInfo[idx].integStr, self._integInfo[idx].atomA, self._integInfo[idx].atomB
		shellA, shellB, axAngMom = self._integInfo[idx].shellA, self._integInfo[idx].shellB, self._integInfo[idx].axAngMom

		currTable = self._integHolder.getIntegTable(integStr, atomA, atomB, shellA, shellB, axAngMom)
		currTable.integrals[:,1] = self._analyticalReps[idx].evalAtListOfXVals(currTable.integrals[:,0])
		self._integHolder.setIntegTable(currTable, integStr, atomA, atomB, shellA, shellB, axAngMom)

	def _writeTables(self):
		integDicts = self._integHolder.integDicts
		filePaths = [x.filePath for x in self._integInfo]

		for currDict, currPath in it.zip_longest(integDicts, filePaths):
			parseTbint.writeBdtFileFormat4(currDict, currPath)


class IntegralTableInfo():
	"""Contains all information required to read/write a specific integral table from/to file.

	Attributes (incl. @properties):
		filePath (str): Absolute path to the file containig integrals
		integStr (str): Type of integral, format needs to match (case insensitive) the parsed dictionary keys from plato_pylib:parse_tbint_files
		atomA (str): Chemical symbol for 1st atom
		atomB (str): Chemical symbol for 2nd atom
		shellA (int): Shell index of 1st atom (orbital based integrals only; else None)
		shellB (int): Shell index of 2nd atom (orbital based integrals only; else None)
		axAngMom (int): Axial angular momentum; e.g. sigma=0, pi=1, delta=2 (orbital based integrals only; else None)

	"""

	def __init__(self, modelFolder, integStr, atomA, atomB, shellA=None, shellB=None, axAngMom=None):
		self.integStr = integStr.lower()
		self.atomA = atomA
		self.atomB = atomB
		self.shellA = shellA
		self.shellB = shellB
		self.axAngMom = axAngMom
		self._modelFolder = os.path.abspath(modelFolder)

	@property
	def filePath(self):
		bdtName = "{}_{}.bdt".format(self.atomA,self.atomB)
		return os.path.abspath( os.path.join(self._modelFolder,bdtName) ) 

	def __eq__(self, other):
		return self.__dict__ == other.__dict__


class IntegralsHolder():

	def __init__(self, atomPairNames:"iter of 2-tuples", integDicts: "list of dicts containing integrals"):
		self.atomPairNames = [tuple(x) for x in atomPairNames]
		self.integDicts = list( [ {k.lower():v for k,v in x.items()} for x in integDicts ] )


	def getIntegTableFromInfoObj(self, integInfo, inclCorrs=True):
		integStr, atomA, atomB = integInfo.integStr, integInfo.atomA, integInfo.atomB
		shellA, shellB, axAngMom = integInfo.shellA, integInfo.shellB, integInfo.axAngMom
		return self.getIntegTable(integStr, atomA, atomB, shellA, shellB, axAngMom, inclCorrs)

	def getIntegTable(self, integStr, atomA, atomB, shellA=None, shellB=None, axAngMom=None, inclCorrs=True):
		integStr, dictIdx = self._getIntegStrAndDictIdxForTable(integStr, atomA, atomB, shellA=None, shellB=None, axAngMom=None)

		if self._weAreLookingForAtomBasedIntTable(shellA,shellB,axAngMom):
			intTable = self.integDicts[dictIdx][integStr][0]
			if _isAtomicIntTable(intTable) and len(self.integDicts[dictIdx][integStr])==1:
				return copy.deepcopy( _getIntegTableCombinedWithCorr(integStr, self.integDicts[dictIdx], 0, inclCorrs) )
			else:
				raise ValueError("shellA/shellB/axAngMom not set despite search for orbital based integrals {}".format(integStr))
		else:
			integIdx = parseTbint._getIdxOfOrbBasedIntInList(shellA,shellB,axAngMom, self.integDicts[dictIdx][integStr])
			if integIdx is not None:
				return copy.deepcopy( _getIntegTableCombinedWithCorr(integStr, self.integDicts[dictIdx], integIdx, inclCorrs) )
			else:
				raise ValueError("Invalid integral requested")


	def setIntegTable(self, newTable, integStr, atomA, atomB, shellA=None, shellB=None, axAngMom=None):
		integStr, dictIdx = self._getIntegStrAndDictIdxForTable(integStr, atomA, atomB, shellA, shellB, axAngMom)
		if self._weAreLookingForAtomBasedIntTable(shellA,shellB,axAngMom):
			integIdx = 0
		else:
			integIdx = parseTbint._getIdxOfOrbBasedIntInList(shellA,shellB,axAngMom, self.integDicts[dictIdx][integStr])

		_setIntegTable(newTable, self.integDicts[dictIdx], integStr, integIdx)

	def getAllIntegsTwoAtoms(self, atomStrA, atomStrB):
		dictIdx = self.atomPairNames.index( (atomA,atomB) )
		return self.integDicts[dictIdx]


	def _getIntegStrAndDictIdxForTable(self, integStr, atomA, atomB, shellA=None, shellB=None, axAngMom=None):
		integStr = integStr.lower()
		dictIdx = self.atomPairNames.index( (atomA,atomB) )
		return integStr, dictIdx

	def _weAreLookingForAtomBasedIntTable(self, shellA, shellB, axAngMom):
		if all( [x is None for x in [shellA,shellB,axAngMom]] ):
			return True
		else:
			return False


def _isAtomicIntTable(intTable):
	if all( [x is None for x in [intTable.shellA, intTable.shellB]] ):
		return True
	else:
		return False


def _getIntegTableCombinedWithCorr(integStr, integDict, integIdx, inclCorr=True):

	corrTable = None
	startTable = integDict[integStr][integIdx]
	if integStr == "pairpot":
		if integDict["PairPotCorrection0".lower()] is not None:
			corrTable = integDict["PairPotCorrection0".lower()][integIdx] #integIdx shouldnt really be needed (only 1 table per dict per pairpot)
		else:
			corrTable = None

	if integStr == "hopping":
		if integDict["HopCorrection0".lower()] is not None:
			corrTable = integDict["HopCorrection0".lower()][integIdx]
		else:
			corrTable = None

	if corrTable is not None and inclCorr:
		return parseTbint.comboSimilarIntegrals(startTable, corrTable)
	else:
		return startTable

def _setIntegTable(intTable, integDict, integStr, integIdx):
	toSetKey = integStr	
	toSetTable = intTable

	if integStr == "pairpot":
		toSetKey = "PairPotCorrection0".lower()
		toSetTable = parseTbint.getIntegralsAMinusBIfTheyAreSimilarIntegrals(intTable, integDict[integStr][integIdx])
	elif integStr == "hopping":
		toSetKey = "HopCorrection0".lower()
		toSetTable = parseTbint.getIntegralsAMinusBIfTheyAreSimilarIntegrals(intTable, integDict[integStr][integIdx])

	if integDict[toSetKey] is not None:
		integDict[toSetKey][integIdx] = toSetTable
	else:
		integDict[toSetKey] = _getInitialiseBlankCorrectionInts( integDict[integStr] ) #Handle case where correction not present in initial file
		integDict[toSetKey][integIdx] = toSetTable


def _getInitialiseBlankCorrectionInts(baseIntTableList):
	outInts = copy.deepcopy(baseIntTableList)
	for x in outInts:
		x.integrals[:,1] = 0.0
	return outInts
		


