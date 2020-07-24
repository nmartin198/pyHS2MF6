.. _install_dlls:


Install a Compiler and Build DLLs
==================================

Two dynamic-link library (DLL) files are required for pyHS2MF6 operation. 
The installation and compilation discussion is presented for use on 
Windows operating systems. These instructions can easily be adapted 
for use on Linux operating systems. On a Linux system, these two files 
would be dynamic load library (SO) files.

The purpose of the DLL files is two-fold.

1. Make MODFLOW 6 available to Python programs and the Python 3 
    interpreter

2. Incorporate extended types or objects into MODFLOW 6 to enable 
    sharing of information between independent HSPF and MODFLOW 6
    processes, or models.

Two DLL files are in the `pyHS2MF6\\bin\\pyMF6` folder. Both of these 
files were created by compiling Fortran source code. These two DLL 
files were compiled on a system with the following characteristics.

* Windows 10, 64-bit OS, Intel x64-based processor
* Python 3.7, 64-bit 

If your computer has equivalent characteristics and software, you can 
try using the versions of `mf6.dll` and `pyMF6.cp37-win_amd64.pyd` 
that are in the `pyHS2MF6\\bin\\pyMF6` folder. Most likely, you will 
need to recreate these DLL files to work on your particular computer 
system.



.. _install_fortran:

Install a Compiler
--------------------

A Fortran compiler, that supports Fortran 95 and 2008 standards, is 
needed to transform the Fortran source code files into DLL files. The 
`MinGW <http://www.mingw.org/>`_ port of the GNU Compiler Collection (GCC)
Fortran compiler, called `GFortran <https://gcc.gnu.org/fortran/>`_, 
was used to compile `pyHS2MF6\\bin\\pyMF6\\mf6.dll` and 
`pyHS2MF6\\bin\\pyMF6\\pyMF6.cp37-win_amd64.pyd`. Instructions are only 
available here for `MinGW GFortran`; however, any Fortran compiler that
supports the 1995 and 2008 standards and is supported by F2PY could be 
used in place of `MinGW GFortran`. On linux systems, GFortran can 
usually be installed through a customized installation of the GNU 
Compiler Collection (GCC) using the linux distribution package manager.

* `Install 32-bit MinGW <http://www.mingw.org/wiki/Install_MinGW>`_ 

* `Install 64-bit MinGW <http://mingw-w64.org/doku.php/download>`_

    * Be sure to add the `bin` directory from the MinGW installation 
        to your PATH environment variable before continuing to the
        next steps.



.. _install_f2py:

Configure NumPy F2PY
~~~~~~~~~~~~~~~~~~~~~~~~~

:abbr:`F2PY (Fortran to Python interface generator)` provides a connection
between Fortran and Python programming languages. F2PY provides this 
connection by inserting interface information into Fortran source code 
file and then using a Fortran compiler to compile both the source code
and the interface specification to a `PYD` file. A `PYD` is a `DLL` file
that has a special function and some additional declarations so that it 
can be loaded into a Python program or the Python 3 interpreter. 

F2PY was installed with NumPy in :ref:`install_pyconda`. There is one 
configuration item that seems be required to have Python and F2PY use
the MinGW compiler. The user needs to create a 
`pydistutils.cfg <https://www.scivision.dev/f2py-fortran-python-windows/>`_ 
file in their home directory. The contents of the `pydistutils.cfg` file 
should be ::

    [build]
    compiler=mingw32

After installing a Fortran compiler and configuring F2PY, it is best to 
test your installation and configuration before moving on to building 
the DLL files.

* `A simple F2PY test case and tutorial <https://www.numfys.net/howto/F2PY/>`_



.. _install_builddlls:

Build DLL Files 
-------------------------

The following steps are required to build the DLL files from the source 
code files.

1. Obtain the 
`MODFLOW 6, version 6.1.1 distribution <https://water.usgs.gov/water-resources/software/MODFLOW-6/mf6.1.1.zip>`_ 
from the USGS including source code. 

    * Extract `mf6.1.1` from the zip archive and place it at the root 
        of the `C:\\` so that have the MODFLOW 6 root directory of at 
        `C:\\mf6.1.1`. 
    
2. Make a new directory `cp_Modules` within the `make` sub-directory so
that have `C:\\mf6.1.1\\make\\cp_Modules`. 

3. Copy the five Fortran source code files, listed below, from 
`pyHS2MF6\\src\\pyMF6` to `C:\\mf6.1.1\\make\\cp_Modules`

    * f2PWrappers.f90 

    * cp_SimulationCreate.f90

    * cp_gwf3.f90 

    * cp_gwf3uzf8.f90 

    * cp_gwf3drn8.f90 

4. Copy the modified makefile, `modmakefile` from `pyHS2MF6\\installation` 
to `C:\\mf6.1.1\\make`

    * This is a modified version of the file `C:\\mf6.1.1\\make\\makefile`. 
        The modifications are so that the result is a DLL instead of an 
        EXE and so that modified file uses DOS commands instead of 
        UNIX commands.

    * If you would like to make a modified make file for Linux, just 
        compare the `C:\\mf6.1.1\\make\\makefile` and 
        `C:\\mf6.1.1\\make\\modmakefile` and the required modifications 
        should be identifiable.

5. Open an Anaconda Prompt, activate the pyhs2mf6 environment, and make 
the active directory `C:\\mf6.1.1\\make`. ::

    (base) > conda activate pyhs2mf6 
     
    (pyhs2mf6) > cd C:\mf6.1.1\make 
     
    (pyhs2mf6) C:\mf6.1.1\make >

6. Create the DLL file, `C:\\mf6.1.1\\make\\mf6.dll`, using the MODFLOW 6 source 
code, four of source code files in `cp_Modules`, and `modmakefile`. ::

    (pyhs2mf6) C:\mf6.1.1\make > mingw32-make.exe --makefile=modmakefile all 

7. Create the PYD file, `C:\\mf6.1.1\\make\\pyMF6.cp37-win_amd64.pyd`, using F2PY 
by linking to `C:\\mf6.1.1\\make\\mf6.dll` and compiling `cp_Modules\\f2PWrappers.f90`. ::

    (pyhs2mf6) C:\mf6.1.1\make > f2py.exe -c -m pyMF6 -L.\ -lmf6 -I.\obj_temp\ --verbose .\cp_Modules\f2PWrappers.f90 

8. Copy the DLL and PYD files from `C:\\mf6.1.1\\make` to `pyHS2MF6\\bin\\pyMF6`.

