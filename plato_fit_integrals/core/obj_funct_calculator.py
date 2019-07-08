
import itertools as it

#Base class
class ObjectiveFunctCalculator():

	def calculateObjFunction( self, calcValues:"types.SimpleNamespace" ):
		""" Takes a set of values and calculates the objective function value
		
		Args:
			calcValues: SimpleNamespace containing values of all parameters being fit to (e.g. bulk modulii,
			            elastic constants)
				
		Returns
			objVal: Value of the objective function based on the calcValues
		
		Raises:
			AttributeError: If any required calcValues are missing
		"""
		raise NotImplementedError()



class ObjectiveFunctTotal(ObjectiveFunctCalculator):

	def __init__(self, objFuncts:"list", weights:list=None):
		self.objFuncts =  list(objFuncts)
		if weights is None:
			self.weights = [1.0 for x in range(len(self.objFuncts))]
		else:
			self.weights = weights

	def calculateObjFunction( self, calcValues ):
		totVal  = 0.0
		for x,weight in it.zip_longest(self.objFuncts,self.weights):
			totVal += x.calculateObjFunction(calcValues) * weight
		return totVal


class ObjectiveFunctionContrib(ObjectiveFunctCalculator):

	#Note each objective function needs to take (targValue,actValue) as args
	def __init__(self, targValuesWithObjFuncts:"types.SimpleNamespace"): 
		self.targValuesWithObjFuncts = targValuesWithObjFuncts

	def calculateObjFunction(self, calcValues):
		dictRepTargets = vars(self.targValuesWithObjFuncts)
		dictRepValues = vars(calcValues)
		totVal = 0.0

		for currAttr in dictRepTargets.keys():
			targVal = dictRepTargets[currAttr][0]
			objFunct = dictRepTargets[currAttr][1]
			actVal = dictRepValues[currAttr]
			totVal += objFunct(targVal,actVal)
		
		return totVal
