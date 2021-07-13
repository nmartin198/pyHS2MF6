.. _installation:

================
 Installation
================

**pyHS2MF6** installation and configuration includes a number of steps, 
enumerated below.

1. Obtain or download the **pyHS2MF6** directories and files from the GitHub site
   as a zip file archive.

    * Unzip this file to a local directory on the computer where you will 
      run **pyHS2MF6**.

    * In the remainder of these instructions this directory is referred 
      to as the `pyHS2MF6` directory. The `pyHS2MF6` directory should
      have the structure shown below.

.. _fig_dir_struct:
.. figure:: ./images/pyHS2MF6_dir_structure.png 
    :align: center
    :alt: pyHS2MF6 directory structure 

    **pyHS2MF6 GitHub archive directory structure**

|

2. The `pyHS2MF6\\bin` directory contains the executable files or 
   program files that comprise the program. In the `bin` root there
   should be four Python source code files with the extension `.py`.

    * The `pyHS2MF6\\bin\\mHSP2` folder contains the eight Python source
      code files that compose the mHSP2 program.

    * `pyHS2MF6\\bin\\pyMF6` folder contains three Python source code files 
      and two dynamic-link library (DLL) files. One file has a `.dll` 
      extension and the other has a `.pyd` extension.

3. Install and configure the Python 3 interpreter. This iteration of 
   **pyHS2MF6** has only been tested with Python 3.8. The **mHSP2** 
   source has been tested with Python 3.8.5 and 3.8.10. It is recommended 
   to use Python 3.8.10.

    * See :ref:`install_pyint`

4. Recreate the DLL files, if needed. This iteration of **pyHS2MF6**
   is designed to be compiled with MODFLOW 6.2.1.

    * See :ref:`install_dlls`

5. Configure the firewall to allow for message passing between the three
   independent processes used in a coupled mode simulation.

    * `Open firewall ports <https://www.tomshardware.com/news/how-to-open-firewall-ports-in-windows-10,36451.html>`_ 

    * There are three firewall ports that need to be opened. One port 
      for each message passing queue.

        1. To HSPF queue

            * :py:data:`coupledMain.PORT0`
            * :py:data:`locaMain.PORT0`
            * :py:data:`pyMF6py.PORT0`

        2. To MODFLOW 6 queue

            * :py:data:`coupledMain.PORT1`
            * :py:data:`locaMain.PORT1`
            * :py:data:`pyMF6py.PORT1`

        3. Error handling queue

            * :py:data:`coupledMain.PORT2`
            * :py:data:`locaMain.PORT2`
            * :py:data:`pyMF6py.PORT2`

    .. caution:: There is also an authorization key or pass code that 
        is set by the user for queue access.

          * :py:data:`coupledMain.AUTHKEY`
          * :py:data:`locaMain.AUTHKEY`
          * :py:data:`pyMF6py.AUTHKEY`

|


**Section Contents**

.. toctree::
    :maxdepth: 3
    :name: installtoc

    install_pyint.rst
    install_dlls.rst


