.. _getting_started:

===============================
 Getting Started with pyHS2MF6
===============================

The `py` in **pyHS2MF6** denotes the 
`Python programming language <https://www.python.org>`_. If you are new 
to Python, 

    "Python is a clear and powerful object-oriented programming 
    language, comparable to Perl, Ruby, Scheme, or Java."

    -- `Beginners Guide Overview <https://wiki.python.org/moin/BeginnersGuide/Overview>`_ 

You will not have to program in Python to run a coupled model with 
**pyHS2MF6**. But, because it is primarily written in Python, you will have to 
run **pyHS2MF6** using the Python 3 interpreter. The interpreter 

    "is the program that reads Python programs and carries out their 
    instructions; you need it before you can do any Python programming."

    -- `Beginners Guide <https://wiki.python.org/moin/BeginnersGuide>`_

:ref:`installation` provides a lengthy laundry list of things that 
need to be done before you can use **pyHS2MF6** on your computer. The first 
item on the list is installation of a Python distribution. The 
`Anaconda Individual Edition <https://www.anaconda.com/products/individual>`_ 
is the recommended distribution, but you can use any Python distribution 
under the caveats provided in :ref:`installation`.

|

Python Programming 
=====================

Although you do not need to know how to program in Python to run **pyHS2MF6**, 
you will find rudimentary programming skills helpful for creating model 
inputs and processing model outputs. **pyHS2MF6** was created under the 
assumption that users would employ some combination of the following 
Python-based toolkits for setting up model inputs and processing model 
outputs.

    * `Jupyter notebooks <https://jupyter.org/>`_ 
    * `FloPy <https://modflowpy.github.io/flopydoc/>`_
    * `HSPsquared <https://github.com/respec/HSPsquared>`_

There is no graphical user interface (GUI) for **pyHS2MF6**. For this 
type of an application, a GUI would just lead to a severe case of carpal 
tunnel from the numerous mouse clicks required to parameterize a model based 
on a three-dimensional, computational grid, like MODFLOW 6. And, it would 
likely be seizure inducing from all of the monitor refresh flashes
needed for rendering when zooming with the mouse scroll wheel.

|

Next Steps 
=============

* :ref:`installation`: Install and configure all of the requirements
* :ref:`case_study`: Understand the requirments to go from existing, 
  standalone HSPF and MODFLOW 6 models to a coupled mode **pyHS2MF6** 
  simulation

