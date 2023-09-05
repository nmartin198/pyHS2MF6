#!/usr/bin/python3
"""
pyHS2MF6 main block for running either pyMF6 or mHSP2 in standalone mode.

Provides standalone access to MODFLOW 6 or HSPF under the assumption that the
user will want to do some pre-coupling, independent model verification prior to
running a coupled model. Uses argparse to accept and parse three command line
arguments.

Command line argument options

    * *modelType* (str): identifier for which model to run in standalone mode;
                         must be HSP2 or MF6
    * *modelDir* (str): path for model directory with input files
    * *inFile* (str): main input file name for the program that was specified
                      modelType

Typical usage examples

    **mHSP2**
        ``python ..\..\LOCA\standaloneMain.py HSP2 C:\\Users\\nmartin\\Documents\\LOCA\\Test_Models\\HSP2 -f DC_Subs.h5``

    **pyMF6**
        ``python ..\..\LOCA\standaloneMain.py MF6 C:\\Users\\nmartin\\Documents\\LOCA\\Test_Models\\MF6 -f mfsim.nam``
 
"""
# Copyright and License
"""
Copyright 2020 Southwest Research Institute

Module Author: Nick Martin <nick.martin@stanfordalumni.org>

This file is part of pyHS2MF6.

pyHS2MF6 is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

pyHS2MF6 is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with pyHS2MF6.  If not, see <https://www.gnu.org/licenses/>.

"""
# imports
import sys
import os
import argparse
# local package imports. Can use the standard import approach because are not
#   run as independent processes
import mHSP2.locaMain as HSP2
import pyMF6.pyMF6py as MF6


# module - wide parameters
MF_SIM_NAME = "mfsim.nam"
"""Standard and fixed MODFLOW 6 simulation name"""

#standalone execution block
# assumes that this module is executed within the same current directory
# as the input file
if __name__ == "__main__":
    # do the argument processing stuff first
    apUsage = "%(prog)s <model> <model directory> -f <HSP2 HDF5 file>"
    apDesc = "Execute standalone HSP2 or MF6 simulation"
    parser = argparse.ArgumentParser( usage=apUsage, description=apDesc )
    parser.add_argument( action='store', choices=["HSP2", "MF6"], type=str, 
                         nargs=1, dest="modelType", 
                         help='Standalone model to run',
                         metavar="model" )
    parser.add_argument( action='store', nargs=1,
                         dest='modelDir', type=str,
                         help='Model directory with input file(s)',
                         metavar="model directory" )
    parser.add_argument( '-f', '--file', action='store', nargs=1, 
                         dest="inFile", type=str, 
                         metavar="Input file",
                         help="Main input file", required=True )
    # parse the command line arguments received and set the simulation directory
    args = parser.parse_args()
    Model_Type = args.modelType[0]
    Sim_Dir = os.path.normpath( args.modelDir[0] )
    # check that our directory exists
    if not os.path.isdir( Sim_Dir ):
        # this is an error
        errMsg = "Model directory %s does not exist!!!" % Sim_Dir
        sys.exit( errMsg )
    # now need to start up our logger
    if not Model_Type in ["HSP2", "MF6"]:
        errMsg = "Invalid model type of %s" % Model_Type
        sys.exit( errMsg )
    # end if
    # get the current directory
    CWD = os.getcwd()
    if CWD != Sim_Dir:
        os.chdir( Sim_Dir )
    # now run the selected model
    if Model_Type == "HSP2":
        hsp5File = args.inFile[0]
        if hsp5File is None:
            errMsg = "No HDF5 file name specified for HSP2 !!!"
            sys.exit( errMsg )
        elif len( hsp5File ) < 4:
            errMsg = "Receivied invalid HDF5 file name of %s" % hsp5File
            sys.exit( errMsg )
        # now can continue
        hsp2InputFile = os.path.normpath( os.path.join( Sim_Dir, hsp5File ) )
        if not os.path.isfile( hsp2InputFile ):
            # this is an error
            errMsg = "HSP2 input file %s does not exist !!!" % hsp2InputFile
            sys.exit( errMsg )
        # end if
        retStat = HSP2.salocaMain( Sim_Dir, hsp2InputFile )
    elif Model_Type == "MF6":
        mf6InputFile = os.path.normpath( os.path.join( Sim_Dir, 
                                                    MF_SIM_NAME ) )
        if not os.path.isfile( mf6InputFile):
            # this is an error
            errMsg = "Main MF6 input file %s does not exist !!!" % \
                        mf6InputFile
            sys.exit( errMsg )
        # end if
        retStat = MF6.saMF6TimeLoop( Sim_Dir )
    # end if
    # check our status
    if retStat != 0:
        if Model_Type == "HSP2":
            errMsg = "Error encountered running HSP2.\n" \
                     "Please check the debug log for more " \
                     "information."
            sys.exit( errMsg )
        elif Model_Type == "MF6":
            errMsg = "Error encountered running MODFLOW 6.\n" \
                     "Please check the MODFLOW listing files for " \
                     "more information."
            sys.exit( errMsg )
        # end if
    # end if
    # return to the current directory
    if CWD != Sim_Dir:
        os.chdir( CWD )
    # end if
    print( "Successful termination of %s" % Model_Type )
    # end


#EOF