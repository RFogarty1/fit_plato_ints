

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
	return OBJ_FUNCT_DICT[functTypeStr.lower()](catchOverflow=catchOverflow, errorRetVal=errorRetVal)


@registerObjFunctTargVals("msd")
def _createMsdFunct(catchOverflow=True,errorRetVal=1e30):
	def Msd(valA,valB):
		return (valA-valB)**2

	if catchOverflow:
		return catchOverflowDecorator(Msd, errorRetVal)

	return Msd






