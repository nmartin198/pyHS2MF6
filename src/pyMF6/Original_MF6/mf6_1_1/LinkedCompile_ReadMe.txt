# pyHS2MF6 ReadMe for compiling DLLs
#
# These instructions will work for Windows 10 OS with
# MinGW GFortran.
#
# Open an Anaconda prompt and activate the environment
# (base) conda activate pyhs2mf6 
# (pyhs2mf6) 
#
# Next proceed stepwise through the commands 

# 1. Make a new sub-directory within the "make" subdirectory of the 
#		MODFLOW 6, version 6.1.1 distribution downloaded from the USGS
#	- Name this sub-directory cp_Modules  

# 2. Copy the five, Fortran source code files from pyHS2MF6\src\pyMF6 
#	 	to this new cp_Modules directory.
#	i.   f2PWrappers.f90
#	ii.  cp_SimulationCreate.f90 
#   iii. cp_gwf3.f90 
#   iv.  cp_gwf3uzf8.f90 
#   v.   cp_gwf3drn8.f90

# 3. Copy the file pyHS2MF6\installation\modmakefile to C:\mf6_1_1\make

# 4. Make the current working directory of the Anaconda Prompt the "make" 
# 		subdirectory of the MODFLOW 6 distribution downloaded from the USGS. 
#  (phys2mf6) cd C:\mf6_1_1\make 

# 5. Create DLL file, mf6.dll 
#   (phys2mf6) C:\mf6_1_1\make > mingw32-make.exe --makefile=modmakefile all

# 6. Create the PYD file, pyMF6.cp37-win_amd64.pyd
#   (phys2mf6) C:\mf6_1_1\make > f2py.exe -c -m pyMF6 -L.\ -lmf6 -I.\obj_temp\ --verbose .\cp_Modules\f2PWrappers.f90 

#EOF