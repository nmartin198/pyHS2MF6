.. _pyMF6:

pyMF6
=====================

**pyMF6** is a Python-wrapped version of 
`MODFLOW 6 <https://www.usgs.gov/software/modflow-6-usgs-modular-hydrologic-model>`_
created specifically for coupled simulation with HSPF. **pyMF6** provides 
the full functionality of MODFLOW 6 because it references all of the MODFLOW 6
source code.

For coupled simulation with **pyMF6**, four extended types are available 
to the coupled program to provide for passing an array into MODFLOW 6 from 
the independent, external **mHSP2** process and to provide for sending an array 
from **pyMF6** to the **mHSP2** process.

The passing of these arrays provides for the dynamic simulation capabilities 
in **pyHS2MF6**.


.. toctree::
    :maxdepth: 3

    pyMF6_python.rst
    pyMF6_fortran.rst

