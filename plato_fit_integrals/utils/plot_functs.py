

import plato_fit_integrals.initialise.create_ecurve_workflows as ecurves

import matplotlib.pyplot as plt


def plotFittedIntsVsInitial(integInfo,coeffsToTablesObj):
    initInts = coeffsToTablesObj._integHolder.getIntegTableFromInfoObj(integInfo,inclCorrs=False).integrals
    fitInts = coeffsToTablesObj._integHolder.getIntegTableFromInfoObj(integInfo,inclCorrs=True).integrals

    figA = plt.figure()
    axA = figA.add_subplot(1,1,1)
    axA.plot(initInts[:,0],initInts[:,1])
    axA.plot(fitInts[:,0],fitInts[:,1])
    
    return figA


def plotDissocCurvesInitVsFinal(structList, initEnergies, finalEnergies):
    xData = _getDistsFromUCellStructsList(structList)
    figA = plt.figure()
    axA = figA.add_subplot(1,1,1)
    axA.scatter(xData,initEnergies)
    axA.scatter(xData,finalEnergies)
    return figA
    
def _getDistsFromUCellStructsList(structList):
    allDists = list()
    for x in structList:
        assert len(x.cartCoords)==2, "Only dimers are supported"
        currDist = ecurves.getSepTwoAtomsInUnitCellStruct(x)
        allDists.append(currDist)
    return allDists

