Epi in the Valley
======================

IDDinf is a short course run by the University of Melbourne, and held in Mt Macedon,
Victoria, Australia from 23rd -- 27th November, 2026.

These note form the basis of an extended tutorial in practical Bayesian epidemic modelling
using the Python ``gemlib`` library, providing a comprehensive introduction to
likelihood-based statistical inference methods for stochastic infectious disease
models. You will be introduced to stochastic modelling, likelihood theory, and MCMC
methods through a series of lecture-practicals.  On completion, you will have a deeper
understanding of how likelihood-based inference methods work on infectious disease models,
and be able to apply them to your own epidemiological problems.


```{toctree}
:maxdepth: 1
:caption: Thursday -- some theory
:numbered:
	     
gemlib_workshop.ipynb
likelihood_theory.ipynb
bayes_mcmc_workshop.ipynb
```

```{toctree}
:maxdepth: 1
:caption: Friday -- the Hagelloch measles outbreak
:numbered:

Network models in ``gemlib`` <hagelloch_network.ipynb>
Data-augmentation MCMC for individual-level models <hagelloch_inference.ipynb>
```
