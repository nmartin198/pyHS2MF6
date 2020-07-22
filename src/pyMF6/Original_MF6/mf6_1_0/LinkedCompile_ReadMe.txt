# you can do this all from an Anaconda Prompt or can do
# 1, 2, 3, 6 from standard command prompt and #4 and #7 cd ..\from Anaconda prompt

# 1. make the current working directory mf6_1_0\make 

# 2. mf_f2pyw adjusted to compile all the necessary object files with allobj
mingw32-make.exe --makefile=mf_f2pyw allobj

# 3. these are turned into a DLL with, note that the *.mod files are only used for optimization
#   need to change current directory to build directory mf6_1_0\build\obj_temp  
gfortran -shared -fPIC -mrtd -O2 -o mf6.dll *.o

# 4. copy the file mf_6_1_0\src\f2Py\f2PWrappers.f90 to mf_6_1_0\build\obj_temp 
# then need to use f2Py to compile our remaining files while linking to this
# dll; the *.mod files still need to be accessible until this one is linked
f2py.exe -c -m locamf6 -LC:\Users\nmartin\Documents\LOCA\mf6_1_0\build\obj_temp -lmf6 --verbose f2PWrappers.f90

# 5. copy the files mf6.dll and locamf6.cp37-win_amd64.pyd from mf6_1_0\build\obj_temp to mf6_1_0\build and
#   to mf6_1_0\src\f2Py 

# 6. use mf_f2pyw to remove all of the object and mod files and executables in the build directory 
mingw32-make.exe --makefile=mf_f2pyw cleanobj

# 7. test the modifications on the test model
# 7a. copy mf6.dll, locamf6.cp37-win_amd64.pyd, mf6Loca.py, and custLogger.py to the test model directory
# 7b. run the command below
python mf6Loca.py C:\Users\nmartin\Documents\LOCA\Models\MODFLOW_6\Test_Model1 

