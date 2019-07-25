
import copy
import itertools as it
import math
import numpy as np


class AnalyticalIntRepr():

	def evalAtListOfXVals(self,xVals:iter):
		""" Evaluate function at list of x-values
		
		Args:
			xVals: Iterable (e.g. list) of float values
				
		Returns
			yVals: Iterable of float values (function values at relevant xVals)
		
		Raises:
			NotImplementedError: If sub-class hasnt overwritten method
		"""
		raise NotImplementedError("evalAtListOfXVals not implemented on child class")

	@property
	def nCoeffs(self):
		raise NotImplementedError("nCoeffs property getter not implemented on child class")

	@property
	def coeffs(self):
		raise NotImplementedError("coeffs property getter not implemented on child class")

	@coeffs.setter
	def coeffs(self,val):
		raise NotImplementedError("coeffs property getter not implemented on child class") #Wont actually get this error if getter is set


def getCombinedAnalyticalReprs(aRepList,copyObjs=True):
	""" Gets an object that represents the additive combination of AnalyticalIntRepr functions
	
	Args:
		aRepList: List of individual objects with AnalyticalIntRepr interface
		copyObjs (Bool): If true the returned object contains deep copies of input objects, else contains references to them
	Returns
		outARep: CompositeAnalyticalRepr(AnalyticalIntRepr) Object. Interface functions use the combination of each input function
	(e.g. outARep.nCoeffs = sum([x.nCoeffs for x in aRepList])
	
	"""
	if copyObjs:
		useList = [copy.deepcopy(x) for x in aRepList]
	else:
		useList = list(aRepList)

	return CompositeAnalyticalRepr(useList)

class CompositeAnalyticalRepr(AnalyticalIntRepr):
	""" Holds multiple AnalyticalIntRepr objects while implementing the AnalyticalIntRepr interface (defined methods are
	a sum of all individual functions contributions
	"""
	def __init__(self, aRepList):
		self._aRepList = aRepList


	@property
	def nCoeffs(self):
		return sum([x.nCoeffs for x in self._aRepList])


	@property
	def coeffs(self):
		outList = list()
		for x in self._aRepList:
			currCoeffs = list(x.coeffs)
			outList.extend(currCoeffs)
		return outList

	#DUPLICATE CODE: essentially same thing is implemented in the coeffsToTables case
	@coeffs.setter
	def coeffs(self,val):
		startIdx = 0
		for aRep in self._aRepList:
			aRep.coeffs = val[startIdx:startIdx+aRep.nCoeffs]
			startIdx += aRep.nCoeffs

	def evalAtListOfXVals(self,xVals:iter):
		outVals = list()
		for x in self._aRepList:
			outVals.append( np.array(x.evalAtListOfXVals(xVals)) )
		return sum(outVals)

class Cawkwell17ModTailRepr(AnalyticalIntRepr):

	def __init__( self, rCut:float=None, refR0:float=None, valAtR0:float=None,
                 nPoly:int=None, startCoeffs:list=None, tailDelta=None,
	             nodePositions=None ):

		if None in [rCut, refR0, valAtR0, tailDelta]:
			raise ValueError("Missing parameter when creating Cawkwell17ModTailRepr Object")

		#Sort out number of polynomials and start coefficients
		if (nPoly is None) and (startCoeffs is None):
			raise ValueError("Either nPoly or startCoeffs needs to be set")
		elif nPoly is None:
			self.nPoly = len(startCoeffs)
			self._coeffs = startCoeffs
		elif startCoeffs is None:
			self._coeffs = [0.0 for x in range(nPoly)]
			self.nPoly = nPoly
		else:
			self.nPoly = nPoly
			self._coeffs = list(startCoeffs)
			if len(self._coeffs) != self.nPoly:
				raise TypeError("nPoly set to {} but {} startCoeffs passed".format(self.nPoly,len(self._coeffs)))

		#Set everything else
		self.rCut = rCut
		self.refR0 = refR0
		self.valAtR0 = valAtR0
		self.tailDelta = tailDelta
		self.nodePositions = list(nodePositions) if nodePositions is not None else []
		self._treatValAtR0AsVariable = False
		self._treatNodePositionsAsVariables = False

	def __repr__( self ):
		return str(self.__dict__)


	def evalAtListOfXVals(self,xVals):
		outArray = np.zeros( (len(xVals)) )
		nodeDenominators = [self.refR0 - nodePos for nodePos in self.nodePositions]
		tailArray = applyTailFunctToListOfXVals(xVals, self.rCut, self.tailDelta)
		for idx,x in enumerate(xVals):
			if x >= self.rCut:
				outArray[idx] = 0.0
			else:
				diffVal = x-self.refR0
	
				#Calc node factor
				nodeFactor = 1.0
				for nodePos,nodeDenom in it.zip_longest(self.nodePositions, nodeDenominators):
					nodeFactor *= ( (x-nodePos) / (nodeDenom) )
	
				try:	
					expTerm = sum([(diffVal**(expIdx+1))*x for expIdx,x in enumerate(self._coeffs)])
					scaleFactor = math.exp(expTerm)
					outArray[idx] = self.valAtR0*scaleFactor*nodeFactor*tailArray[idx]
				except OverflowError:
					outArray[idx] = 1e30
		return outArray

	def promoteValAtR0ToVariable(self):
		self._treatValAtR0AsVariable = True

	def promoteNodePositionsToVariables(self):
		self._treatNodePositionsAsVariables = True

	def demoteValAtR0FromVariable(self):
		self._treatValAtR0AsVariable = False

	@property
	def nCoeffs(self):
		numbCoeffs = self.nPoly
		if self._treatValAtR0AsVariable:
			numbCoeffs += 1
		if self._treatNodePositionsAsVariables:
			numbCoeffs += len(self.nodePositions)
		return numbCoeffs

	@property
	def coeffs(self):
		outCoeffs = list(self._coeffs)
		if self._treatValAtR0AsVariable:
			outCoeffs = outCoeffs + [self.valAtR0]
		if self._treatNodePositionsAsVariables:
			outCoeffs = outCoeffs + self.nodePositions
		return outCoeffs

	@coeffs.setter
	def coeffs(self,val):
		if len(val) != self.nCoeffs:
			raise TypeError("Expected {} coeffs, but {} passed".format(self.nCoeffs,len(val)))

		self._coeffs = list(val[:self.nPoly])
		nextListPos = self.nPoly
		if self._treatValAtR0AsVariable:
			self.valAtR0 = val[nextListPos]
			nextListPos += 1
		if self._treatNodePositionsAsVariables:
			self.nodePositions = list(val[nextListPos:])




class ExpDecayFunct(AnalyticalIntRepr):
	def __init__(self, r0=None,alpha=None,prefactor=None, rCut=None, tailDelta=None):
		reqArgs = [r0,alpha,prefactor]
		if None in reqArgs:
			raise TypeError("Missing parameter when creating ExpDecayFunct")

		self.r0 = r0
		self._alpha = alpha
		self._prefactor = prefactor
		self._rCut = rCut
		self._tailDelta = tailDelta

		if rCut is not None:
			self.applyTail = True
		else:
			self.applyTail = False

	def evalAtListOfXVals(self,xVals:iter):
		outArray = np.zeros( (len(xVals)) )
		alphaSqr = self._alpha*self._alpha

		if self.applyTail:
			tailArray = applyTailFunctToListOfXVals(xVals,self._rCut, self._tailDelta)
		for idx,x in enumerate(xVals):
			rDist = x - self.r0
			outArray[idx] = self._prefactor * math.exp( (-1*alphaSqr*rDist) )
			if self.applyTail:
				outArray[idx] *= tailArray[idx]

		return outArray

	@property
	def nCoeffs(self):
		return len(self.coeffs)

	@property
	def coeffs(self):
		return [self._prefactor,self._alpha]

	@coeffs.setter
	def coeffs(self,val):
		if len(val) != self.nCoeffs:
			raise TypeError("Expected {} coeffs, but {} passed".format(self.nCoeffs,len(val)))
		self._prefactor = val[0]
		self._alpha = val[1]



def applyTailFunctToListOfXVals(xVals,rCut,tailDelta):
	outArray = np.zeros( (len(xVals)) )
	for idx,x in enumerate(xVals):
		if x >= rCut:
			outArray[idx] = 0.0
		else:
			outArray[idx] = math.exp( tailDelta/(x-rCut) ) #Approaches 0 as x approaches rCut
	return outArray
