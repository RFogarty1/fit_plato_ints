

VALID_PLATO_CODE_STRS = ["dft2","tb1"]
VALID_CORR_TYPES = ["pairPot".lower(),"hopping", None]

def modOptDictBasedOnCorrTypeAndPlatoCode(optDict, corrType:str, platoCode:str):
	""" Modified a dictionary in place based on the plato code used and the integrals we are varying.
	e.g. if we're varying hopping integrals it will 
	
	Args:
		optDict: Dict defining keyword options for plato; with kwargs in the plato_pylib format (usually the same kwarg as plato inp-files)
		corrType: Str (case insensitive) denoting integrals which will be corrected; Valid options={\"pairPot\",\"hopping\",None} [Others throw errors]
		platoCode: Str (case insensitive) used to call the relevant plato program 
	Returns
		None (modifies optDict in place)
	
	Raises:
		ValueError: For invalid combinations. For example dft cannot be used with any varyTypes, while dft2 cant be used with hopping
	"""

	#Check options are valid individually
	if corrType is not None:
		if corrType.lower() not in VALID_CORR_TYPES:
			raise ValueError(_getErrorStrForModOptDict(corrType=corrType))
	if platoCode is not None:
		if platoCode.lower() not in VALID_PLATO_CODE_STRS:
			raise ValueError(_getErrorStrForModOptDict(platoCode=platoCode))

	#Correct the dictionary
	if corrType is None:
		pass
	elif corrType.lower() == "pairPot".lower():
		optDict["addcorrectingppfrombdt"] = 1
		if platoCode.lower() == "dft2":
			optDict["e0method"] = 1
	elif corrType.lower() == "hopping":
		if platoCode.lower() == "tb1":
			optDict["addcorrectinghopfrombdt"] = 1
		else:
			raise ValueError(_getErrorStrForModOptDict(corrType=corrType,platoCode=platoCode))
	else:
		raise ValueError(_getErrorStrForModOptDict(corrType=corrType)) #shouldnt ever be called really


def _getErrorStrForModOptDict(corrType=None,platoCode=None):
	if (corrType is None) and (platoCode is None):
		return None
	elif (corrType is not None) and (platoCode is None):
		return "corrType = {} is an invalid option".format(corrType)
	elif (corrType is None) and (platoCode is not None):
		return "platoCode = {} is an invalid option".format(corrType)
	else:
		return "corrType = {} and platoCode = {} is an invalid combination".format(corrType, platoCode)



#		if self.varyType is None: #Useful if we just want to run the workflow once without using correcting integrals
#			pass
#		elif self.varyType.lower() == "pairPot".lower():
#			inpDict["addcorrectingppfrombdt".lower()] = 1
#			if self.platoCode=="dft2":
#				inpDict["e0method"] = 1
#		elif self.varyType.lower() == "hopping".lower():
#			inpDict["addcorrectinghopfrombdt"] = 1
#			if self.platoCode=="dft":
#				raise ValueError("varyType = {} is an invalid option for platoCode={}".format(self.varyType,self.platoCode))
#		else:
#			raise ValueError("varyType = {} is an invalid option".format(self.varyType))
#
