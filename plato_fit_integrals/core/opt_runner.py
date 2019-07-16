

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
def carryOutOptimisationBasicOptions(objectiveFunct,method=None, **kwargs):	
	fitRes = minimize(objectiveFunct, objectiveFunct.coeffTableConverter.coeffs,method=method, **kwargs)
	output = SimpleNamespace(optRes=fitRes, calcVals=objectiveFunct.workFlowCoordinator.propertyValues )
	objectiveFunct.coeffs = fitRes.x #These should be the optimised parameters; if i didnt do this then objFunct would only contain the FINAL parameters
	objectiveFunct.coeffTableConverter.writeTables()
	return output

