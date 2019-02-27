# Harissa

### Tools for mechanistic-based gene network inference

This is a Python package for inferring gene networks from single-cell data.
It consists in:

* *Hartree Approximation* and *Random fields*
* for mechanistic-based gene network *Inference*
* along with a *Stochastic Simulation Algorithm*

#### Important
This repository is still under construction, but will hopefully improve soon. Currently, the `harissa` package consists of 3 independent subpackages:

* `autoactiv` : hyperparameter inference using an auto-activation model
* `automodel` : network inference using a mechanistic-based random field
* `grnsim` : stochastic simulation of the corresponding dynamical model

Please see the [tutorials](https://github.com/ulysseherbach/harissa/tree/master/tutorials) folder for some demos.

#### Dependencies
The package depends on the following standard scientific libraries:

* numpy
* scipy
* matplotlib