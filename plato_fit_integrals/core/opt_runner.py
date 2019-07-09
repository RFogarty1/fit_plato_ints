

""" Code to actually run the optimisation """
from types import SimpleNamespace
from scipy.optimize import minimize

class ObjectiveFunction:

	def __init__(self, coeffTableConverter, workFlowCoordinator, objFunctCalculator):
		self.coeffTableConverter = coeffTableConverter
		self.workFlowCoordinator = workFlowCoordinator
		self.objFunctCalculator = objFunctCalculator

	def __call__(self, coeffs):
		self.coeffTableConverter.coeffs = coeffs
		self.coeffTableConverter.writeTables()
		calcValues = self.workFlowCoordinator.runAndGetPropertyValues()
		objFunctVal = self.objFunctCalculator.calculateObjFunction(calcValues)
		return objFunctVal



#Mainly for initial testing
def carryOutOptimisationBasicOptions(objectiveFunct):	
	fitRes = minimize(objectiveFunct, objectiveFunct.coeffTableConverter.coeffs)
	output = SimpleNamespace(optRes=fitRes, calcVals=objectiveFunct.workFlowCoordinator.propertyValues )
	return output

