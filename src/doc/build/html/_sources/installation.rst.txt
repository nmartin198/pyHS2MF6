.. _installation:

================
 Installation
================

pyHS2MF6 installation and configuration includes a number of steps, which
are enumerated below.


.. image:: ./images/pyHS2MF6_dir_structure.png 
    :width: 500 px
    :align: center


1. Obtain or download the pyHS2MF6 directories and files from the GitHub site
as a zip file archive.

    * Unzip this file to a local directory on the computer where you will 
        run pyHS2MF6.

    * In the remainder of these instructions this directory is referred 
        to as the `pyHS2MF6` directory. The `pyHS2MF6` directory should
        have the structure shown above.

2. The `pyHS2MF6\bin` directory contains the executable files or 
program files that comprise the program. In the `bin` root there
should be four Python source code files with the extension `.py`.

    * The `pyHS2MF6\bin\mHSP2` folder contains eight Python source code
        files that compose the **mHSP2** program.

    * `pyHS2MF6\bin\pyMF6` folder contains three Python source code files 
        and two dynamic-link library (DLL) files. One file has a `.dll` 
        extension and the other has a `.pyd` extension.

3. Install and configure the Python 3 interpreter

    * See :ref:`install_pyint`

4. Recreate the DLL files, if needed.

    * See :ref:`install_dlls`



**Table of Contents**

.. toctree::
    :maxdepth: 3
    :name: installtoc

    install_pyint.rst
    install_dlls.rst


