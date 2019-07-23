
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
					expTerm = sum([(diffVal**(expIdx+1))*x for expIdx,x in enumerate(self._coeffs)]) + (self.tailDelta/(x-self.rCut))
					scaleFactor = math.exp(expTerm)
					outArray[idx] = self.valAtR0*scaleFactor*nodeFactor
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

	#TODO: Throw error if wrong number of coefficients passed
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

