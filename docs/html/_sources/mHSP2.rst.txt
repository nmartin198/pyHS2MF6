.. _mHSP2:

mHSP2
=====================

**mHSP2** is the port of `HSPsquared <https://github.com/respec/HSPsquared>`_
created specifically for coupled simulation with MODFLOW 6. 
`HSPsquared <https://github.com/respec/HSPsquared>`_ is a HSPF variant 
which was rewritten in pure Python. **mHSP2** only provides the water 
movement and storage capabilities of 
`HSPsquared <https://github.com/respec/HSPsquared>`_. 

The main difference between **mHSP2** and 
`HSPsquared <https://github.com/respec/HSPsquared>`_ is that **mHSP2** 
was created with the simulation time loop as the main simulation loop to
facilitate dynamic coupling to MODFLOW 6. HSPF-variants traditionally use
an operating module instance loop that is executed in routing order as
the main simulation loop. This approach requires that the time 
simulation loop be executed for each operating module instance. 
**Figure** :ref:`fig_cd_mHSP2_struct_mod` graphically depicts this 
structural modification.


.. _fig_cd_mHSP2_struct_mod:

.. figure:: ./images/Fig_02-mHSP2_Structure_Reorg.png
    :width: 900px
    :align: center
    :alt: mHSP2 Structural Modifications
    :figclass: align-center 

    **mHSP2 structural modifications**

|

|



.. toctree::
    :maxdepth: 3

    mHSP2_main.rst
    mHSP2_hrchhyd.rst
    mHSP2_hyperwat.rst
    mHSP2_himpwat.rst
    mHSP2_coupling.rst
    mHSP2_HDF5.rst
    mHSP2_logger.rst

