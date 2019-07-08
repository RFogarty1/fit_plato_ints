#!/usr/bin/python3

from types import SimpleNamespace

import sys
import unittest
import unittest.mock as mock

sys.path.append('..')
import workflow_coordinator as tCode


class TestWorkFlowCoordinatorRaisesErorrsOnDuplications(unittest.TestCase):

	def setUp(self):
		self.workFlowA = createMockWorkFlowA()
		self.workFlowB = createMockWorkFlowB()

	def testRaisesForDuplicatedFolderBetweenWorkflows_Initiation(self):
		self.workFlowB.workFolder = self.workFlowA.workFolder
		workFlows = [self.workFlowA, self.workFlowB]
		with self.assertRaises(ValueError):
			tCode.WorkFlowCoordinator(workFlows)

	def testRaisesForDuplicatedPropertyBetweenWorkflowsInitiation(self):
		self.workFlowB.namespaceAttrs[0] = self.workFlowA.namespaceAttrs[0]
		workFlows = [self.workFlowA, self.workFlowB]
		with self.assertRaises(ValueError):
			tCode.WorkFlowCoordinator(workFlows)

	def testRaisesForDuplicatedFolderBetweenWorkflows_addition(self):
		testCoord = tCode.WorkFlowCoordinator([self.workFlowA])
		with self.assertRaises(ValueError):
			testCoord.addWorkFlow(self.workFlowA)


class TestWorkFlowCoordinatorNamespaceGeneration(unittest.TestCase):

	def setUp(self):
		self.workFlowA = createMockWorkFlowA()
		self.workFlowB = createMockWorkFlowB()

	def testCorrectOutputNamespaceOneWorkFlow(self):
		expNamespace = SimpleNamespace(hcp_v0=1,fcc_v0=2)
		testCoord = tCode.WorkFlowCoordinator([self.workFlowA])
		testCoord.run()
		actNamespace = testCoord.propertyValues
		self.assertEqual(expNamespace,actNamespace)

	def testCorrectOutputNamespaceTwoWorkFlows(self):
		expNamespace = SimpleNamespace(hcp_v0=1,fcc_v0=2,bcc_v0=3)
		testCoord = tCode.WorkFlowCoordinator([self.workFlowA, self.workFlowB])
		testCoord.run()
		actNamespace = testCoord.propertyValues
		self.assertEqual(expNamespace, actNamespace)

def createMockWorkFlowA():
	workFlowA = mock.Mock()
	workFlowA.workFolder = "test_folderA"
	workFlowA.namespaceAttrs = ["hcp_v0", "fcc_v0"]
	workFlowA.run = fakeWorkFlowRunMethod(workFlowA, SimpleNamespace(hcp_v0=1, fcc_v0=2))
	return workFlowA

def createMockWorkFlowB():
	workFlowB = mock.Mock()
	workFlowB.workFolder = "test_folderB"
	workFlowB.namespaceAttrs = ["bcc_v0"]
	workFlowB.run = fakeWorkFlowRunMethod(workFlowB, SimpleNamespace(bcc_v0=3))
	return workFlowB

def fakeWorkFlowRunMethod(workFlowObj,outNamespace):
	def retMethod():
		workFlowObj.output = outNamespace
	return retMethod

if __name__ == '__main__':
	unittest.main()

