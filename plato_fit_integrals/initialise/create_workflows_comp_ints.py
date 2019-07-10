

import functools
import math
import numpy as np

from types import SimpleNamespace

import plato_fit_integrals.core.workflow_coordinator as wFlow
import plato_fit_integrals.initialise.fit_analytic_to_initial_tables as fitInit


class CreateWorkflowActualIntsVsRef:
	""" Factory for creating workflows that simply compare how similar a set of integrals are
	to reference data. Used for example in fitting integrals to inverse-SK results. Object is callable
	and will return a workflow object.
	"""

	def __init__(self, integHolder, refValues, integInfo, objFunct=None, outProp="rmsdIntegs"):
		""" 
		Args:
			integHolder (IntegralsHolder Object) : Reference to the object that holds and updates all the integrals.
			refValues ( 2-d array ): Reference values to fit to. np.array(input) is used, which should produce a 2-column array
			integInfo (class IntegralTableInfo Object): Reference to an object containing all information about the integral 
		                                         (e.g. atomA, shellA)
			objFunct(Optional): Function that calculates the objective function from (targInts,actInts), where both args
			                    are 2-column arrays with equal numbers of rows. (Default=RMSD)
			outProp(Optional): Label for the calculated property on the workflow. Needs to match a property in the objective
			                   function calculator
		"""


		self.refValues = np.array(refValues)
		self.getterFunction = functools.partial( integHolder.getIntegTable, integInfo.integStr, integInfo.atomA, integInfo.atomB,
		                                         integInfo.shellA, integInfo.shellB, integInfo.axAngMom )

		if objFunct is None:
			objFunct = _createRmsdObjFunct() 
		self.objFunct = objFunct

		self.outProp = outProp


	def __call__(self):
		return _WorkFlowCompareIntsVsRef(self.refValues, self.getterFunction, self.outProp, self.objFunct)



class _WorkFlowCompareIntsVsRef(wFlow.WorkFlowBase):

	def __init__(self, refInts, intGetter, propName, objFunct):
		self.refInts = refInts
		self.intGetter = intGetter
		self.propName = propName
		self.objFunct = objFunct


	@property
	def namespaceAttrs(self):
		return [self.propName]

	@property
	def workFolder(self):
		return None

	def run(self):
		newInts = self.intGetter().integrals
		objFunctVal = self.objFunct(self.refInts,newInts)
		self.output = SimpleNamespace( **{self.propName:objFunctVal} )

def _createRmsdObjFunct():
	def rmsdFunct(targInts,actInts):
		sqrDiffs = list()
		for row in targInts:
			xVal,yVal = row[0],row[1]
			calcYVal = fitInit.getInterpYValGivenXValandInpData(xVal,actInts)
			sqrDiffs.append( (yVal-calcYVal)**2 )
		sumSqrDev = sum(sqrDiffs)
		rmsd = math.sqrt( sumSqrDev/len(sqrDiffs) )
		return rmsd
	return rmsdFunct




