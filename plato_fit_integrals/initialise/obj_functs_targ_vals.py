import copy
import itertools as it
import math

OBJ_FUNCT_DICT = dict()


def registerObjFunctTargVals(key):
	def decorate(funct):
		OBJ_FUNCT_DICT[key.lower()] = funct
		return funct
	return decorate


def catchOverflowDecorator(funct, overflowRetVal):
	def overflowSafeFunct(*args,**kwargs):
		try:
			return funct(*args, **kwargs)
		except OverflowError:
			return overflowRetVal
	return overflowSafeFunct

def applyMeanDecorator(funct):
	def getMean(*args, **kwargs):
		outIter = funct(*args, **kwargs)
		mean = sum(outIter)/len(outIter)
		return mean
	return getMean

#TODO:Needs proper testing
def applyNormDecorator(funct, maxVal):
	def getNormd(*args, **kwargs):
		outVal = funct(*args,**kwargs)
		outVal = outVal/maxVal
		if outVal > 1:
			outVal = 1
		return outVal
	return getNormd

def applyGreaterThanIsOkDecorator(funct):
	def outFunct(targVal,actVal):
		if actVal > targVal:
			return 0
		else:
			return funct(targVal,actVal)
	return outFunct

def applyLessThanIsOkDecorator(funct):
	def outFunct(targVal, actVal):
		if actVal < targVal:
			return 0
		else:
			return funct(targVal, actVal)
	return outFunct

def applyAbsValsDecorator(funct):
	def outFunct(targVal,actVal):
		return funct(abs(targVal),abs(actVal))
	return outFunct



def applyDivByConstantDecorator(funct, constant):
	def outFunct(*args,**kwargs):
		outVal = funct(*args,**kwargs)
		return outVal / constant
	return outFunct
	

def createVectorisedTargValObjFunction(functTypeStr:str, averageMethod="mean",catchOverflow=True, errorRetVal=1e30, normToErrorRetVal=False, greaterThanIsOk=False, lessThanIsOk=False, useAbsVals=False,
divideErrorsByNormFactor=None):
	""" Creates a comparison function that operators on (iterA,iterB) and returns a single value representing their similarity
	
	Args:
		functTypeStr(str): Key for selecting a base function for comparing two single numbers. e.g. "absdev" means a function returning the absolute difference.
		                   All possible values can be found in OBJ_FUNCT_DICT. The function this gives has interface cmpFunct(expVal,actVal)->objVal
		averageMethod(str): Determines how we convert an array of errors (obtained by applying functTypeStr function to all pairs of values) to a single error value
		catchOverflow(bool): If True we catch overflow errors when comparing numbers, we replace the (overflowed) error value with errorRetVal
		errorRetVal(float): see catchOverflow
		normToErrorRetVal(bool): If True we ensure that all output values are between - and 1. We do this by divinding values by errorRetVal, and still setting the answer
		                         to 1 even if they go above that value
		greaterThanIsOk(bool): If True then the cmpFunct(expVal,actVal) returns 0 if expVal>=actVal, regardless on the actual type of cmpFunct(which is determined by functTypeStr)
		lessThanIsOk(bool): If True then the cmpFunct(expVal, actVal) returns 0 if expVal<=actVal, regardless on the actual type of cmpFunct(which is determined by functTypeStr)
		useAbsVals(bool): If True then the cmpFunct(expVal,actVal) will use abs(expVal) and abs(actVal) as inputs. Useful if you only care about the magnitude of your errors. Note: This is applied BEFORE less than/greater than functionality; so if mixed the <,> operators are appleid to abs(expVal) and abs(actVal)
		divideErrorsByNormFactor(float): If not None, then we divide the output error by this value. The original purpose is to get a normalised error based on target values;
		                                 this is accomplished by setting this arg to the average expVal, and using the absdev cmp function.

	Returns
		outFunct(targIter,actIter)->error: Single function that works on two input iterators. Order of targIter and actIter probably wont matter.
	
	"""
	baseFunct = createSimpleTargValObjFunction(functTypeStr, catchOverflow=False, greaterThanIsOk=greaterThanIsOk, lessThanIsOk=lessThanIsOk, useAbsVals=useAbsVals)
	def vectorizedFunct(targVals,actVals):
		outVals = list()
		tVals, aVals = copy.deepcopy(targVals), copy.deepcopy(actVals)
		for t,a in it.zip_longest(tVals,aVals):
			outVals.append( baseFunct(t,a) )
		return outVals	

	outFunct = vectorizedFunct #Currently takes in lists, and returns a list
	if averageMethod.lower()=="mean":
		outFunct = applyMeanDecorator(outFunct)
	else:
		raise ValueError("{} is not a supported option for averageMethod".format(averageMethod))

	if divideErrorsByNormFactor is not None:
		outFunct = applyDivByConstantDecorator(outFunct, divideErrorsByNormFactor)

	if catchOverflow:
		outFunct = catchOverflowDecorator(outFunct,errorRetVal)

	#Important this comes after catchOverflow, which essentially caps the value
	if normToErrorRetVal:
		outFunct = applyNormDecorator(outFunct, errorRetVal)

	return outFunct

def createSimpleTargValObjFunction(functTypeStr:str, catchOverflow=True, errorRetVal=1e30, greaterThanIsOk=False, lessThanIsOk=False, useAbsVals=False):
	""" Creates an objective function that takes input (targetVal, actVal) where both are single numbers
	
	Args:
		functTypeStr: String (Case insensitive) indicating the type of function required. See OBJ_FUNCT_DICT.keys()
		              for available options
		catchOverflow: Bool. If set to True then whenever an overflow error occurs then errorRetVal is returned by the function
		errorRetVal: Return value if a caught error is thrown (only overflows at the time of writing)
		greaterThanIsOk: Bool, If true then the cmp function is set to zero if actual value>target value.
		lessThanIsOk(bool): If True then the cmpFunct(expVal, actVal) returns 0 if expVal<=actVal, regardless on the actual type of cmpFunct(which is determined by functTypeStr)
		useAbsVals(bool): If True then the cmpFunct(expVal,actVal) will use abs(expVal) and abs(actVal) as inputs. Useful if you only care about the magnitude of your errors. Note: This is applied BEFORE less than/greater than functionality; so if mixed the <,> operators are appleid to abs(expVal) and abs(actVal)

	Returns
		objFunct: Function with interface (targetVal, actVal)->output value.
	
	Raises:
		KeyError: If functTypeStr is not a valid key for an objective function
	"""

	basicObjFunct = OBJ_FUNCT_DICT[functTypeStr.lower()]()

	if greaterThanIsOk:
		basicObjFunct = applyGreaterThanIsOkDecorator(basicObjFunct)

	if lessThanIsOk:
		basicObjFunct = applyLessThanIsOkDecorator(basicObjFunct)

	#NOTE: This needs to be on the outside (after greater/less than but before overflow catching)
	if useAbsVals:
		basicObjFunct = applyAbsValsDecorator(basicObjFunct)

	if catchOverflow:
		basicObjFunct = catchOverflowDecorator(basicObjFunct, errorRetVal)

	return basicObjFunct


@registerObjFunctTargVals("sqrdev")
def _createSqrDevFunct():
	def sqrDev(valA,valB):
		return (valA-valB)**2
	return sqrDev

@registerObjFunctTargVals("absdev")
def _createAbsDevFunct():
	def absDev(valA,valB):
		return abs(valA-valB)
	return absDev

@registerObjFunctTargVals("sqrRootAbsDev".lower())
def _createSqrRootAbsDevFunct():
	def sqrRootAbsDev(valA, valB):
		return math.sqrt( abs(valA-valB) )
	return sqrRootAbsDev

@registerObjFunctTargVals("blank")
def _createBlankObjFunct():
	def blankObjFunct(targVal,actVal):
		return actVal
	return blankObjFunct

@registerObjFunctTargVals("relRootSqrDev".lower())
def _createRelRootSqrDevFunct():
	def relRootSqrDevFunct(targVal,actVal):
		rootSqrDev = math.sqrt( (targVal-actVal)**2 )
		return abs(rootSqrDev/targVal)
	return relRootSqrDevFunct

@registerObjFunctTargVals("actMinusTarg".lower())
def _createActMinusTargFunct():
	def actMinusTargFunct(targVal, actVal):
		outVal = actVal-targVal
		return outVal
	return actMinusTargFunct



