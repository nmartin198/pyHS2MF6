.. _pyMF6_fortran:

Customized Fortran Modules
------------------------------

One completely new Fortran module, :ref:`pyMF6_f2pwrap_f`, was created 
to complete the Python wrapping. This module provides the link between 
Fortran MODFLOW 6 and Python.

Four MODFLOW 6 Fortran modules were copied, renamed, slightly 
modified, and extended to provide for four new type extensions, as 
discussed in :ref:`pyMF6_m6exts_f`. The modified modules and extended 
types provide dynamic coupling capabilities to pass an array of 
infiltration values into MODFLOW 6 and to create and return an array 
of groundwater discharge to the ground surface.


.. toctree::
    :maxdepth: 3

    pyMF6_f2pwrap.rst
    pyMF6_mf6types.rst

