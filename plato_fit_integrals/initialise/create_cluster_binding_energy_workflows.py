


import types

import plato_fit_integrals.core.workflow_coordinator as wflowCoord

class ClusterBindingEnergyWorkFlow(wflowCoord.WorkFlowBase):


	def __init__(self, clusterRunner, monomerRunner):
		""" Initialiser for cluster binding energy workflow
		
		Args:
			clusterRunner: (MolClusterBindingEnergyRunnerBase) Represents the cluster (made of multiple monomers)
			monomerRunner:  (MolClusterBindingEnergyRunnerBase) Represents the single monomer unit
	 
		Raises:
			AssertionError: If monomerRunner is made of multiple units (nMolecules != 1)
		"""
		self.cluster = clusterRunner
		self.monomer = monomerRunner
		self.output = types.SimpleNamespace()
		self._assertMonomerHasSingleMolecule()

	def _assertMonomerHasSingleMolecule(self):
		assert self.monomer.nMolecules == 1, "monomer must be comprised of 1 molecule, not {}".format(self.monomer.nMolecules)

	@property
	def preRunShellComms(self):
		runList = list()
		runList.extend( self.cluster.runComm )
		runList.extend( self.monomer.runComm )
		runList = [x for x in runList if x is not None]
		return runList


	@property
	def namespaceAttrs(self):
		return ["bindingEnergy"]

	@property
	def workFolder(self):
		self._ensureWorkFoldersAreTheSame()
		return self.cluster.workFolder

	def _ensureWorkFoldersAreTheSame(self):
		if self.cluster.workFolder != self.monomer.workFolder:
			raise ValueError("cluster workFolder must be the same as monomer workFolder.\cluster path = {}\monomer path = {}".format(self.cluster.workFolder, self.monomer.workFolder))

	def run(self):
		monomerSumEnergies = self.cluster.nMolecules*self.monomer.totalEnergy
		clusterEnergy = self.cluster.totalEnergy
		self.output.bindingEnergy = clusterEnergy - monomerSumEnergies


