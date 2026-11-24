Epi in the Valley
======================

IDDinf is a short course run by the University of Melbourne, and held in Mt Macedon,
Victoria, Australia from 23rd -- 27th November, 2026.

These note form the basis of an extended tutorial in practical Bayesian epidemic modelling
using the Python [``gemlib``](https://gemlib.gem-epidemics.org) library, providing a comprehensive introduction to
likelihood-based statistical inference methods for stochastic infectious disease
models. You will be introduced to stochastic modelling, likelihood theory, and MCMC
methods through a series of lecture-practicals.  On completion, you will have a deeper
understanding of how likelihood-based inference methods work on infectious disease models,
and be able to apply them to your own epidemiological problems.


## Thursday

Thursday's sessions will cover stochastic epidemics, the principles of likelihood theory, and Bayesian statistics.  We'll work in Python (with [``gemlib``](https://gemlib.gem-epidemics.org)), and provide a quick R$\rightarrow$Python conversion tutorial at the beginning. 

```{toctree}
:maxdepth: 1
:numbered:

python_positron_setup.rst
gemlib_workshop.ipynb
likelihood_theory.ipynb
bayes_mcmc_workshop.ipynb
```

## Friday

Friday's morning sessions will be dedicated to building an inference framework around an individual-level model of the 1861 outbreak of meales in Hagelloch, Germany.  We'll cover the basics of stochastic epidemics on networks, as well as how to use ``gemlib`` to perform data augmentation MCMC when infectious times are not observed.

```{toctree}
:maxdepth: 1
:numbered:

hagelloch_network_model.ipynb
data_augmentation_workshop.ipynb
```
