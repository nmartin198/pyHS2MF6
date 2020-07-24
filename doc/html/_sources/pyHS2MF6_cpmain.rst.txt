.. _cp_coupled:

Main Block for Coupled Mode
-------------------------------

**pyHS2MF6** is designed for coupled mode simulation. This mode is
expected to be the primary use case. For coupled mode simulation,
the *coupledMain* module provides the coupled model controller and queue 
server functionality.

It will start independent **mHSP2** and **pyMF6** processes and will
create, serve, and manage three message passing queues for interprocess
communications.


.. _cp_coupledmain_py:

coupledMain.py
~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: coupledMain
	:members:
