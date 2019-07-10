
import os

import plato_pylib.plato.parse_tbint_files as parseTbint

import plato_fit_integrals.core.coeffs_to_tables as coeffTableConv


#Creating integral holders

def createIntegHolderFromModelFolderPath(modelFolderPath):
	allBdtPaths = _getAllBdtPathsInAFolder(modelFolderPath)
	atomPairNames = _getAtomPairNamesFromBdtPaths(allBdtPaths)
	integTables = _getAllIntegDictsFromBdtPaths(allBdtPaths)
	outObj = coeffTableConv.IntegralsHolder(atomPairNames, integTables)
	return outObj



def _getAllBdtPathsInAFolder(modelFolderPath):
	fNames = [ x for x in os.listdir(modelFolderPath) if x.endswith(".bdt") ]
	return [os.path.abspath( os.path.join(modelFolderPath, fName) ) for fName in fNames]


def _getAtomPairNamesFromBdtPaths(allPaths):
	allElementPairs = list()
	for currPath in allPaths:
		currFileName = os.path.split(currPath)[1]
		baseFileName = os.path.splitext(currFileName)[0]
		elements = baseFileName.split("_")
		allElementPairs.append(elements)
	return allElementPairs

def _getAllIntegDictsFromBdtPaths(allPaths):
	allIntegDicts = list()
	for currPath in allPaths:
		allIntegDicts.append( parseTbint.getIntegralsFromBdt(currPath) )
	return allIntegDicts



#Creating integral info structs
def getAllIntInfoObjsFromIntegStrAndBdtPath(integStr:"str, e.g. hopping" , bdtPath):
	integDict = parseTbint.getIntegralsFromBdt(bdtPath)
	relevantInts = integDict[integStr]
	modelFolder = os.path.split(bdtPath)[0]
	outputObjs = list()
	for x in relevantInts:
		currObj = coeffTableConv.IntegralTableInfo(modelFolder, integStr, x.atomAName, x.atomBName, x.shellA, x.shellB, x.orbSubIdx)
		outputObjs.append(currObj)

	#Need to filter out axAngMom = 1 (default in parseTbint) for atom-based integrals
	for x in outputObjs:
		if (x.shellA is None):
			x.axAngMom = None

	return outputObjs




