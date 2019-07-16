
import copy
import functools
from types import SimpleNamespace
import numpy as np

from scipy.optimize import brentq
from scipy.interpolate import interp1d


import plato_fit_integrals.core.workflow_coordinator as wFlow
import plato_fit_integrals.core.opt_runner as runOpts
import plato_fit_integrals.core.obj_funct_calculator as objFunctCalc

import plato_fit_integrals.initialise.obj_functs_targ_vals as objFuncts

def fitAnalyticFormToStartIntegrals( coeffTableConverter, intIdx=0, method=None):
	""" Fits the required analytical form directly to a set of tabulated integrals
	
	Args:
		coeffTableConverter: CoeffTableConverter object, this contains all functional forms as well as the current integral tables
		intIdx: The index of the integral table in coeffTableConverter, call a higher level function if you want ALL fitted
			
	Returns
		Nothing. Works in place.

	"""

	#Optimisation Step - we dont need to write the output tables until the end
	origWriteFunct = copy.deepcopy( coeffTableConverter._writeTables )
	copiedTableConv = copy.deepcopy( coeffTableConverter )
	copiedTableConv._writeTables = lambda : None

	workFlow = _createWorkflowCompareTwoSetsTabulatedIntegrals(copiedTableConv, intIdx)
	workFlowCoordinator = wFlow.WorkFlowCoordinator([workFlow])

	objFunctCalcultor = _createObjFunctionCalculator()

	objectiveFunction = runOpts.ObjectiveFunction(copiedTableConv, workFlowCoordinator, objFunctCalcultor)
	fitRes = runOpts.carryOutOptimisationBasicOptions(objectiveFunction,method=method)

	#Write the tables; this would usually be done automatically at each step as part of the update step
	coeffTableConverter.coeffs = copiedTableConv.coeffs
	coeffTableConverter.writeTables()

	return fitRes



def _createWorkflowCompareTwoSetsTabulatedIntegrals( coeffTableConverter, intIdx ):
	#Step 1  = get our reference data
	intInfo = coeffTableConverter._integInfo[intIdx]
	integStr = intInfo.integStr
	atomA, atomB = intInfo.atomA, intInfo.atomB
	shellA, shellB = intInfo.shellA, intInfo.shellB
	axAngMom = intInfo.axAngMom
	startIntegrals = coeffTableConverter._integHolder.getIntegTable(integStr, atomA, atomB, shellA, shellB, axAngMom, inclCorrs=False)

	integralsGetter = functools.partial(coeffTableConverter._integHolder.getIntegTable, integStr, atomA, atomB, shellA, shellB, axAngMom)

	return WorkFlowCompareIntegralTableToReference(startIntegrals, integralsGetter)



def _createObjFunctionCalculator():
	targVal = 0
	blankObjFunct = objFuncts.createSimpleTargValObjFunction("blank") #We effectively calculate the objective function within the workflow, so are basically mocking out the objFuncttion calculator
	propsWithObjFunct = SimpleNamespace( **{"rmsd":(targVal,blankObjFunct)} )
	objFunctCalculator = objFunctCalc.ObjectiveFunctionContrib(propsWithObjFunct)
	return objFunctCalculator


class WorkFlowCompareIntegralTableToReference(wFlow.WorkFlowBase):

	def __init__(self, refValues, newValuesGetter:"function"):
		self.refValues = refValues
		self.getterFunct = newValuesGetter

	@property
	def namespaceAttrs(self):
		return ["rmsd"]

	@property
	def workFolder(self):
		return None

	def run(self):
		newInts = self.getterFunct()
		tableOld, tableNew = np.array(self.refValues.integrals), np.array(newInts.integrals)
		assert np.allclose(tableNew[:,0],tableOld[:,0]), "X-values inconsistent in tables"

		diffArray = np.array(tableNew[:,1] - tableOld[:,1])
		for x in range(diffArray.shape[0]):
			diffArray[x] *= diffArray[x]

		self.output = SimpleNamespace(rmsd=sum(diffArray)/diffArray.shape[0])


def findCrossings(inpArray):
	"""function thet finds positions of the nodes along x axis using linear interpolation between sign changes"""
	x,y = inpArray[:,0], inpArray[:,1]
	zero_crossings = np.where(np.diff(np.signbit(y[:-1])))[0]
	finterp=interp1d(x, y, kind='linear')
	x_nodes= list()
	for cross in zero_crossings:
		x_nodes.append(brentq(finterp,x[cross],x[cross+1]))
	return x_nodes


def getInterpYValGivenXValandInpData(xVal, inpData):
	finterp = interp1d(inpData[:,0],inpData[:,1])
	return finterp(xVal)



