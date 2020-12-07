.. _install_pyint:


Install and Configure a Python Environment
===========================================

A Python environment provides the Python 3 interpreter. The 
`Anaconda Individual Edition <https://www.anaconda.com/products/individual>`_ 
is the recommended distribution to install to provide a Python environment 
and a Python 3 interpreter. Instructions and helper files are provided
for working with this distribution in Section :ref:`install_pyconda`.
 
You can use any Python distribution that is desired as long as you ensure 
the requirements, listed in :ref:`install_pyreqs`, are fulfilled.

|

.. _install_pyreqs:

Python Requirements 
---------------------

**pyHS2MF6** has only been used and tested with Python 3.8.5. Consequently,
it is recommended to use Python 3.8.5.

In addition to Python 3.8.5, a number of add-on Python libraries or 
packages are required by **pyHS2MF6**. These packages are listed below.

    * `NumPy <https://numpy.org/>`_ 19.0.2

    * `pandas <https://pandas.pydata.org/>`_ 1.1.3

    * `h5py <https://www.h5py.org/>`_ 2.10.0

    * `PyTables <https://www.pytables.org/usersguide/tutorials.html>`_ 3.6.1

    * `FloPy <https://modflowpy.github.io/flopydoc/>`_ 3.3.2


The following packages are not strictly required by **pyHS2MF6** but are 
used for pre- and post-processing in the example models.

    * `Jupyter notebooks <https://jupyter.org/>`_ jupyterlab 2.2.6

    * `matplotlib <https://matplotlib.org/>`_ 3.3.2

    * `GeoPandas <https://geopandas.org/>`_ 0.6.1

    * `Shapely <https://pypi.org/project/Shapely/>`_ - installed as part of 
      the GeoPandas installation.


|

.. _install_pyconda:

Anaconda Install Instructions
-------------------------------

1. Download the 
   `Python 3.8 Anaconda Graphical Installer <https://www.anaconda.com/products/individual>`_ 
   and follow the
   `installation instructions <https://docs.anaconda.com/anaconda/install/>`_

2. Open an 
   `Anaconda Prompt <https://docs.anaconda.com/anaconda/user-guide/getting-started/#open-anaconda-prompt>`_.

3. Install a pre-configured virtual environment for use with **pyHS2MF6** 
   using the file `pyHS2MF6_env.yml` in the `installation` directory by running 
   the following command from the `Anaconda Prompt`. ::

    conda env create -f pyHS2MF6_env.yml


4. In the file `pyHS2MF6_env.yml`, the last section is usually the `prefix:` 
   section. You will need to edit this to be the appropriate path on your 
   computer in order to have the virtual environment installation and 
   configuration complete on your computer.

5. When you use **pyHS2MF6** in the future, you will want to run it  
   from the virtual environment that was just created. To use the 
   virtual environment, you need to 
   `activate it <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#activating-an-environment>`_ 
   and when you are done with it,  
   `deactivate it <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#deactivating-an-environment>`_.

    * `Anaconda Virtual Environments <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#managing-environments>`_ 


