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


def createVectorisedTargValObjFunction(functTypeStr:str, averageMethod="mean",catchOverflow=True, errorRetVal=1e30, normToErrorRetVal=False):
	baseFunct = createSimpleTargValObjFunction(functTypeStr, catchOverflow=False)
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

	if catchOverflow:
		outFunct = catchOverflowDecorator(outFunct,errorRetVal)

	#Important this comes after catchOverflow, which essentially caps the value
	if normToErrorRetVal:
		outFunct = applyNormDecorator(outFunct, errorRetVal)

	return outFunct

def createSimpleTargValObjFunction(functTypeStr:str, catchOverflow=True, errorRetVal=1e30):
	""" Creates an objective function that takes input (targetVal, actVal) where both are single numbers
	
	Args:
		functTypeStr: String (Case insensitive) indicating the type of function required. See OBJ_FUNCT_DICT.keys()
		              for available options
			
	Returns
		objFunct: Function with interface (targetVal, actVal)->output value.
	
	Raises:
		KeyError: If functTypeStr is not a valid key for an objective function
	"""

	basicObjFunct = OBJ_FUNCT_DICT[functTypeStr.lower()]()
	if catchOverflow:
		basicObjFunct = catchOverflowDecorator(basicObjFunct, errorRetVal)
	return basicObjFunct


@registerObjFunctTargVals("sqrdev")
def _createSqrDevFunct():
	def sqrDev(valA,valB):
		return (valA-valB)**2
	return sqrDev


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
