# [Practical epidemics](https://gem-epidemics.gitlab.io/practical-epidemics)

This site provides a collection of tutorial material on how to develop and implement infectious disease models in Python code.  In includes a collection of lecture slides and notebooks, together with the material for the IDDinf course at Lancaster University.

Examples are not limited to epidemics, but also include implementations of endemic models.  Although we focus on epidemiology here, the underying models are all flavours of discrete-space state transition models and therefore may be relevant to other applications as well.

## Contributing

[Practical epidemics](https://gem-epidemics.gitlab.io/practical-epidemics) is built using the [Sphinx](https://sphinx-doc.org) documentation system, which allows Jupyter notbooks to be rendered as HTML.  The source code for the site is contained in the `site/source` directory, and is written using [MyST](https://myst-parser.readthedocs.io/) markdown and Jupyter notebooks (which may, of course, be used for standalone presentations).  For more information, please refer to the [Sphinx](https://sphinx-doc.org), [MyST](https://myst-parser.readthedocs.io/), and [Jupyter notebook](https://jupyter.org) documentation.

All contributions are welcome, by the usual process of forking the repository and submitting merge requests, and may be included pending review by the development team.  Comments and suggestions should be submitted to the repository issue tracker in Gitlab.

All contributors must abide by our Code of Conduct, and failure to comply may result in sanctions.


## Building

If you wish to build the Practical Epidemics site locally, you will need to install the Python [poetry](https://python-poetry.org) package first according to its documentation for your platform.  Thereafter, from the top level directory do

```bash
$ poetry install
$ poetry shell
$ cd site
$ make html
```
