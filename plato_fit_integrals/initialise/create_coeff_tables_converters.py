
import os

import plato_pylib.plato.parse_tbint_files as parseTbint

import plato_fit_integrals.core.coeffs_to_tables as coeffTableConv

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
