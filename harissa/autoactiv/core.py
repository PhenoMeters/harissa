### core.py - Core functions for the inference of a positive loop for one gene ###
"""NB: this part is made to deal with a basic (N,2) numpy array where N = number of valid measures:
- the first column stores the time-points,
- the second column stores the expression values.
Moreover, parameters T (time-points), a and theta are assumed to be numpy arrays"""

import numpy as np
import scipy.optimize

### Import useful functions from the package
from autoactiv.utils import binom
from autoactiv.graphics import plotInference

### Import special functions
from numpy import exp, log
from scipy.special import gamma, psi

### Compute the exact log-likelihood
def logLikelihood(X,Timepoints,a,theta,c):
    N = np.size(X[:,0])
    S, B = 0, binom(c)
    z = np.linspace(0,c,c+1)
    lz = a[0] + a[1]*z
    for t, timepoint in enumerate(Timepoints):
        x = X[X[:,0]==timepoint,1]
        Z = np.sum(B*exp(theta[t]*z)*gamma(lz)/(a[2]**lz))
        lu = (a[0]-1)*log(x) - a[2]*x + c*log(1 + exp(theta[t])*(x**a[1]))
        n = np.size(x)
        S += np.sum(lu) - n*log(Z)

    return S/N ### Normalized log-likelihood

### Compute the conditional expectations of Z given X (denoted by Y)
def Expectation(X,Timepoints,a,theta,c):
    N = np.size(X[:,0])
    Y = np.zeros(N)
    # Construct a dict {timepoint: t} to retrieve the array index given a time-point
    T = len(Timepoints)
    timedict = dict(zip(Timepoints,range(0,T)))
    for i in range(0,N):
        t = timedict[X[i,0]]
        x = X[i,1]
        Y[i] = c*exp(theta[t])*(x**a[1])/(1 + exp(theta[t])*(x**a[1]))

    return Y

### Compute the EM objective function Q given Y (up to a useless additive constant)
def objQ(X,Timepoints,a,theta,c,Y):
    S, N = 0, np.size(X[:,0])
    # Construct a dict {timepoint: t} to retrieve the array index given a time-point
    T = len(Timepoints)
    timedict = dict(zip(Timepoints,range(0,T)))
    for i in range(0,N):
        t, x, y = timedict[X[i,0]], X[i,1], Y[i]

        ### Compute the integration constant at time t
        B = binom(c)
        z = np.linspace(0,c,c+1)
        lz = a[0] + a[1]*z
        A = np.sum(B*gamma(lz)*exp(theta[t]*z - log(a[2])*lz))

        ### Compute Q
        S += (theta[t] + a[1]*log(x))*y + a[0]*log(x) - a[2]*x - log(A)

    return S/N

### Compute the gradient of Q given Y
def gradQ(X,Timepoints,a,theta,c,Y):
    Da = np.zeros(3)
    Dtheta = np.zeros(len(Timepoints))
    N = np.size(X[:,0])
    # Construct a dict {timepoint: t} to retrieve the array index given a time-point
    T = len(Timepoints)
    timedict = dict(zip(Timepoints,range(0,T)))
    for i in range(0,N):
        t, x, y = timedict[X[i,0]], X[i,1], Y[i]

        ### Compute the unconditioned expectations
        B = binom(c)
        z = np.linspace(0,c,c+1)
        lz = a[0] + a[1]*z
        wz = B*gamma(lz)*exp(theta[t]*z - log(a[2])*lz)
        wz = wz/np.sum(wz)

        Ez = np.sum(z*wz)
        Elnx = np.sum((psi(lz) - log(a[2]))*wz)
        Ezlnx = np.sum(z*(psi(lz) - log(a[2]))*wz)
        Ex = np.sum((lz/a[2])*wz)

        ### Compute the gradient
        Da[0] += log(x) - Elnx
        Da[1] += log(x)*y - Ezlnx
        Da[2] += -x + Ex
        Dtheta[t] += y - Ez

    return np.append(Da,Dtheta)/N

### Maximization step (using quasi-newton method L-BFGS-B)
def Maximization(X,Timepoints,a,theta,c,Y,**kwargs):
    x0 = np.append(a,theta)
    ### We locally define proper objective and gradient functions
    def f(x):
        return -objQ(X,Timepoints,x[0:3],x[3:],c,Y)
    def Df(x):
        return -gradQ(X,Timepoints,x[0:3],x[3:],c,Y)

    b = [(1e-5,None),(1e-5,None),(1e-5,None)] + [(None,None) for i in Timepoints]
    res = scipy.optimize.minimize(f, x0, method='L-BFGS-B', jac = Df, bounds = b)

    if not res.success:
        print("Warning, Maximization step failed")
    # else:
    #     print("M step done in {} iterations, a = {}".format(res.nit, res.x[0:3]))

    return (res.x[0:3],res.x[3:])

### The EM routine
def inferParamEM(X,Timepoints,a,theta,c,**kwargs):
    monitor_path = kwargs.get('monitor_path', None)
    iter_em = kwargs.get('iter_em', 100) # Number of iterations of the EM
    idgene = kwargs.get('idgene', 0)
    gene = kwargs.get('gene', '[?]')

    T = len(Timepoints)
    Va = np.zeros((iter_em+1,3))
    Vtheta = np.zeros((iter_em+1,T))
    Vl = np.zeros(iter_em+1)

    l = logLikelihood(X,Timepoints,a,theta,c)
    Va[0,:] = a
    Vtheta[0,:] = theta
    Vl[0] = l
    i = 1
    lt = l - 1

    while ((i < iter_em+1) and (l - lt > 1e-5)):
        # print('i = {}'.format(i))
        Y = Expectation(X,Timepoints,a,theta,c)
        (a,theta) = Maximization(X,Timepoints,a,theta,c,Y)
        lt = l
        l = logLikelihood(X,Timepoints,a,theta,c)
        ### Saving the values if needed
        if monitor_path:
            Va[i,:] = a
            Vtheta[i,:] = theta
            Vl[i] = l

        i += 1

    if (i < iter_em+1):
        for k in range(i,iter_em+1):
            Va[k,:] = a
            # Vtheta[k,:] = theta
            Vl[k] = l
    else: print("Warning (c = {}): EM has not converged in {} iterations".format(c,iter_em))

    if monitor_path:
        pathimage = monitor_path + "/Monitoring_{}_{}".format(idgene,c)
        plotInference(Va,Vtheta,Vl,c,gene,pathimage)

    return (a,theta)


