

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
		self.refInts =  np.array(refInts)
		self.refInts = self.refInts[refInts[:,0].argsort()]
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
		assert np.all(np.diff(actInts[:,0]) > 0), "x-values must be increasing"
		for idx,row in enumerate(targInts):
			weightVal = 1.0
			xVal,yVal = row[0],row[1]
			calcYVal = np.interp(xVal, actInts[:,0], actInts[:,1]) #DANGEROUS function; x-vals must be increasing. Much faster than using scipy thoiugh
			sqrDiffs.append( ((yVal-calcYVal)**2)*weightVal )
		sumSqrDev = sum(sqrDiffs)
		rmsd = math.sqrt( sumSqrDev/len(sqrDiffs) )
		return rmsd
	return rmsdFunct


def _createMaeObjFunct():
	def maeFunct(targInts,actInts):
		absDiffs = list()
		assert np.all(np.diff(actInts[:,0]) > 0), "x-values must be increasing"
		for row in targInts:
			xVal,yVal = row[0],row[1]
			calcYVal = np.interp(xVal, actInts[:,0], actInts[:,1]) #DANGEROUS function; x-vals must be increasing. Much faster than using scipy thoiugh
			absDiffs.append( abs(yVal-calcYVal) )
		mae = sum(absDiffs)/len(absDiffs)
		return mae
	return maeFunct


def _calcDistToNearestWeightsSorted1DimArray(inpData:"sorted,ascending 1-dim array"):
	outArray = np.array(inpData)
	outArray[0] = inpData[1]-inpData[0]
	for rIdx in range(1,outArray.shape[0]-1):
		outArray[rIdx] = min( abs(inpData[rIdx]-inpData[rIdx-1]),  abs(inpData[rIdx]-inpData[rIdx+1]) )

	outArray[-1] = inpData[-1] - inpData[-2]
	return outArray
