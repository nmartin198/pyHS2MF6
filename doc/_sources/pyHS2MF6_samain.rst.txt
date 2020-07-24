.. _cp_standalone:

Main Block for Standalone Mode
-------------------------------

Standalone mode allows the user to confirm that **pyHS2MF6** is reproducing
model output sufficiently from independent standalone models. **pyHS2MF6** 
is specifically formulated to use extend existing **HSPF** and 
**MODFLOW 6** models.

**pyMF6** is the standalone version of **MODFLOW 6** in **pyHS2MF6**. 
**pyMF6** should reproduce previous **MODFLOW 6** results almost exactly 
because all of the source code and calculation logic in **MODFLOW 6** is 
ported intact to **pyMF6**. The reproduction should be almost exact in 
the sense that identical compilers and computers will be required to
be exact.

**mHSP2** is the standalone version of **HSPF** in **pyHS2MF6**. It only
provides the water movement and storage capabilities of **HSPF**. 
Additionally, **mHSP2** is a pure python, rewrite of *HSPsquared*. 
The rewrite was necessary to make the main loop the simulation time
loop to facilitate dynamic coupling. The goal of the rewrite was to
reproduce the calculation logic from *HSPsquared* and **HSPF** but
reorder the calculations into outer time loop order. Because **mHSP2** 
is a complete rewrite using different numpy package components, 
**mHSP2** is not expected to exactly reproduce **HSPF** results. It 
is expected to conceptually and generally reproduce **HSPF** results.


.. _cp_standaloneMain_py:

standaloneMain.py
~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: standaloneMain
	:members:

