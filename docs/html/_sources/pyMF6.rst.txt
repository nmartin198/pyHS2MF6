.. _pyMF6:

pyMF6
=====================

**pyMF6** is a Python-wrapped version of 
`MODFLOW 6 <https://www.usgs.gov/software/modflow-6-usgs-modular-hydrologic-model>`_
created specifically for coupled simulation with HSPF. **pyMF6** provides 
the full functionality of `MODFLOW 6 <https://www.usgs.gov/software/modflow-6-usgs-modular-hydrologic-model>`_ 
because it references all of the 
`MODFLOW 6 <https://www.usgs.gov/software/modflow-6-usgs-modular-hydrologic-model>`_ 
source code.

For coupled simulation with **pyMF6**, four extended types, or objects, are available 
to the coupled program. **Figure** :ref:`fig_cd_pyMF6_new_types` shows the Python-
wrapping methodology along with the extended types added to the source code. The 
purpose of the extended objects or types is to provide for passing an array into 
`MODFLOW 6 <https://www.usgs.gov/software/modflow-6-usgs-modular-hydrologic-model>`_ 
from the independent, external **mHSP2** process and to provide for sending an array 
from **pyMF6** to the **mHSP2** process.

The passing of these arrays provides for the dynamic simulation capabilities 
in **pyHS2MF6**.

|

.. _fig_cd_pyMF6_new_types:

.. figure:: ./images/Fig_05-pyMF6_Structure_Reorg.svg
    :width: 1000px
    :align: left
    :alt: pyMF6 Extended Types
    :figclass: align-left 

    **pyMF6 Python-wrapping and extended types**

**pyMF6** retains all MODFLOW 6 functionality, input structure, and 
output formats. The only changes to MODFLOW 6 in **pyMF6** are wrapping 
of subroutines and modules for access from Python modules and addition 
of four extended types to provide for dynamic information sharing with 
**mHSP2**.

|

|


.. toctree::
    :maxdepth: 3

    pyMF6_python.rst
    pyMF6_fortran.rst

