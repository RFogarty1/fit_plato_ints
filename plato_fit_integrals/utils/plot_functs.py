
import matplotlib.pyplot as plt


def plotFittedIntsVsInitial(integInfo,coeffsToTablesObj):
    initInts = coeffsToTablesObj._integHolder.getIntegTableFromInfoObj(integInfo,inclCorrs=False).integrals
    fitInts = coeffsToTablesObj._integHolder.getIntegTableFromInfoObj(integInfo,inclCorrs=True).integrals

    figA = plt.figure()
    axA = figA.add_subplot(1,1,1)
    axA.plot(initInts[:,0],initInts[:,1])
    axA.plot(fitInts[:,0],fitInts[:,1])
    
    return figA



