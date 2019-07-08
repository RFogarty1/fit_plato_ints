

""" Code to actually run the optimisation """

from scipy.optimize import minimize

class ObjectiveFunction:

	def __init__(self, coeffTableConverter, workFlowCoordinator, objFunctCalculator):
		self.coeffTableConverter = coeffTableConverter
		self.workFlowCoordinator = workFlowCoordinator
		self.objFunctCalculator = objFunctCalculator

	def __call__(self, coeffs):
		self.coeffsTableConverter.coeffs = coeffs
		self.coeffsTableConverter.writeTables()
		calcValues = self.workFlowCoordinator.runAndGetPropertyValues()
		objFunctVal = self.objFunctCalculator.calculateObjFunction(calcValues)
		return objFunctVal


#Mainly for initial testing
def carryOutOptimisationBasicOptions(initCoeffs, ObjectiveFunct):	
	fitRes = scipy.minimize(ObjectiveFunct, initCoeffs)
	return fitRes

