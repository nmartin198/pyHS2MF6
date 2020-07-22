.. _mHSP2_HDF5:

HDF5 File Methods and Data Structures
--------------------------------------------

**mHSP2** reads the input 
`HDF5 file <https://portal.hdfgroup.org/display/knowledge/What+is+HDF5>`_ and 
stores the pertinent portions in memory before starting the main time 
loop. At the end of simulation time, **mHSP2** reopens this same 
HDF5 file and writes the specified time series outputs.


.. _mHSP2_locaHSP2HDF5_py:

locaHSP2HDF5.py
~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: locaHSP2HDF5
    :members:

