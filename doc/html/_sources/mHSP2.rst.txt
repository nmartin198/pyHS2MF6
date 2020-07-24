.. _mHSP2:

mHSP2
=====================

**mHSP2** is the port of `HSPsquared <https://github.com/respec/HSPsquared>`_
created specifically for coupled simulation with MODFLOW 6. *HSPsquared* 
is a HSPF variant which was rewritten in pure Python. **mHSP2** only 
provides the water movement and storage capabilities of *HSPsquared*. 

The main difference between **mHSP2** and *HSPsquared* is that **mHSP2** 
was created with the simulation time loop as the main simulation loop to
facilitate dynamic coupling to MODFLOW 6. HSPF-variants traditionally use
an operating module instance loop that is executed in routing order as
the main simulation loop. This approach requires that the time 
simulation loop be executed for each operating module instance.


.. toctree::
    :maxdepth: 3

    mHSP2_main.rst
    mHSP2_hrchhyd.rst
    mHSP2_hyperwat.rst
    mHSP2_himpwat.rst
    mHSP2_coupling.rst
    mHSP2_HDF5.rst
    mHSP2_logger.rst

