# -*- coding: utf-8 -*-
"""
Created on 12/19/2022

@author: nmartin
"""

# imports
import os
import shutil
import sys
import subprocess
import pandas as pd
import numpy as np
import pickle
import flopy

# parameters
#    model executables
PYTHON_EXE = r'C:\Users\nmartin\.conda\envs\pyhs2mf6\python.exe'
MF6_EXE = r'C:\MODFLOW\mf6.2.1\bin\mf6.exe'
ZB6_EXE = r'C:\MODFLOW\mf6.2.1\bin\zbud6.exe'
PLPROC_EXE = r'C:\Pest\pest17\plproc.exe'
#PESTPP_CONTROL_ROOT = "s4_bspr"
PESTPP_CONTROL_ROOT = "s4_it2_bspr"
INPUTS_FILE = "Inputs.dat"
OUTPUTS_FILE = "Outputs.dat"
CP_INPUT_FILE = "LOCA_In.dat"
MF6_NAME = "MF6TBraat_cp"
ZBIDs_MAT_FILE = "ZoneBudgetIDs_mat.pkl"
ZBIDs_LIST_FILE = "ZBUniqueZones_List.pkl"
IN_HDF5_DIR = "InputHDF5"
IN_HDF5_NAME = "BRAAT_cp_nr.h5"
OUT_HDF5_NAME = "BRAAT_cp.h5"
# important dates
SimStart = pd.Timestamp( 2015, 1, 1, 0, )
BurnInEnd = pd.Timestamp( 2016, 6, 30, 23, 59, )
CalibStart = pd.Timestamp( 2016, 7, 1, 0, )
CalibEnd = pd.Timestamp( 2019, 12, 31, 23, 59, )
ValidStart = pd.Timestamp( 2020, 1, 1, 0, )
SimEnd = pd.Timestamp( 2021, 12, 31, 23, 59, )
# Pilot points meta data - all the information that need to implement the
#   interpolation
PP_META_DICT = { 1 : ["BFZ_Art", "BFZ_Art_PLPkr_%d_%s.dat", "BFZ_Art_Clist_DF.pkl",
                      "BFZ_Art_PPs_ClistwIn_DF.pkl", "BFZ_Art_Clist.dat",
                      [[31, 51, 53, 71], [32, 41, 42, 52, 61]]],
                 2 : ["BFZ_FBlocks", "BFZ_FBlocks_PLPkr_%d_%s.dat",
                      "BFZ_FBlocks_Clist_DF.pkl",
                      "BFZ_FBlocks_PPs_ClistwIn_DF.pkl", "BFZ_FBlocks_Clist.dat",
                      [[31, 51, 53, 71],[41, 61]]],
                 3 : ["BS_Pool", "BS_Pool_PLPkr_%d_%s.dat", "BS_Pool_Clist_DF.pkl",
                      "BS_Pool_PPs_ClistwIn_DF.pkl", "BS_Pool_Clist.dat",
                      [[31, 51, 53, 71],[32, 41, 42, 52, 61]]],
                 4 : ["Trans_FBlocks", "Trans_FBlocks_PLPkr_%d_%s.dat",
                      "Trans_FBlocks_Clist_DF.pkl",
                      "Trans_FBlocks_PPs_ClistwIn_DF.pkl",
                      "Trans_FBlocks_Clist.dat",
                      [[31, 51, 53, 71],[41, 61]]],
                 5 : ["BS_Contrib", "BS_Contrib_PLPkr_%d_%s.dat",
                      "BS_Contrib_Clist_DF.pkl",
                      "BS_Contrib_PPs_ClistwIn_DF.pkl", "BS_Contrib_Clist.dat",
                      [[51, 53, 71],[41, 42, 52, 61]]],
                 6 : ["Horst", "Horst_PLPkr_%d_%s.dat", "Horst_Clist_DF.pkl",
                      "Horst_PPs_ClistwIn_DF.pkl", "Horst_Clist.dat",
                      [[51, 53, 71],[41, 61]]],
                 7 : ["FWest", "FWest_PLPkr_%d_%s.dat", "FWest_Clist_DF.pkl",
                      "FWest_PPs_ClistwIn_DF.pkl", "FWest_Clist.dat",
                      [[51, 53, 71],[41, 61]]], }
# storage considerations/calculations
Sy_MAX = 0.45
Sy_MIN = 0.12
Sy_RANGE = Sy_MAX - Sy_MIN
Ss_MAX = 0.0001666667
Ss_MIN = 0.00000033333333
Ss_RANGE = Ss_MAX - Ss_MIN
# lambdas
SsCalcFromSy = lambda Sy: max( Ss_MIN, ( ( ( Sy - Sy_MIN ) / Sy_RANGE ) * Ss_RANGE ) + Ss_MIN )
# water level stuff for NRMSE calc
MAX_WL = 417.245774
MIN_WL = 148.899870
WL_RANGE = MAX_WL - MIN_WL
# dictionary identifying drain labels
SPRING_DICT = { "jws" : ["jws", "JWS", ],
                "a15" : ["a-15_hays", "A-15_HAYS", ],
                "ccs" : ["cypress_creek_spring", "CYPRESS_CREEK_SPRING", ],
                "fbs" : ["fern_bank_springs", "FERN_BANK_SPRINGS", ],
                "pvs" : ["pvs", "PVS", ],
                "crb" : ["crabapple_creek_spring", "CRABAPPLE_CREEK_SPRING", ],
                "drp" : ["dripping_springs", "DRIPPING_SPRINGS", ],
                "c3h" : ["c-3_hays", "C-3_HAYS", ],
                "cld" : ["cold_spring", "COLD_SPRING", ],
                "zer" : ["zercher_spring", "ZERCHER_SPRING", ],
                "bar" : ["barton_creek_springs", "BARTON_CREEK_SPRINGS", ],
                "lps" : ["little_park_spring", "LITTLE_PARK_SPRING",],
                "bla" : ["blanco_river_spring", "BLANCO_RIVER_SPRING",],
                "sms" : ["sms", "SMS",],
                "c5h" : ["c-5_hays", "C-5_HAYS",],
                "brf" : ["blanco_river_fb", "BLANCO_RIVER_FB",],
                "par" : ["park_spring", "PARK_SPRING",], }


# Ftable dictionary
FTAB_DICT = { 1 : ["FT001", "R001", "Blanco_01", ],
              2 : ["FT002", "R002", "Blanco_02", ],
              3 : ["FT003", "R003", "Blanco_03", ],
              4 : ["FT004", "R004", "Blanco_04", ],
              5 : ["FT005", "R005", "Blanco_05", ],
              6 : ["FT006", "R006", "Blanco_06", ],
              7 : ["FT007", "R007", "Blanco_07", ],
              8 : ["FT008", "R008", "Blanco_08", ],
              9 : ["FT009", "R009", "Blanco_09", ],
             10 : ["FT010", "R010", "Blanco_10", ],
             20 : ["FT020", "R020", "LBlanco_20", ],
             21 : ["FT021", "R021", "LBlanco_21", ],
             30 : ["FT030", "R030", "Spring_Lake", ],
             31 : ["FT031", "R031", "SanMarcos_31", ],
             40 : ["FT040", "R040", "SouthOnion_40", ],
             41 : ["FT041", "R041", "NorthOnion_41", ],
             42 : ["FT042", "R042", "Onion_42", ],
             43 : ["FT043", "R043", "Onion_43",],
             44 : ["FT044", "R044", "Onion_44", ],
             50 : ["FT050", "R050", "Bear_50", ],
             51 : ["FT051", "R051", "Bear_51", ],
             60 : ["FT060", "R060", "Barton_60", ],
             70 : ["FT070", "R070", "Cypress_70", ],
             71 : ["FT071", "R071", "Cypress_71", ], }
# stream gauge dictionary
GAUGE_MAP_DICT = { 55200 : [8155200, "R060" ],
                   58700 : [8158700, "R042" ],
                   58810 : [8158810, "NA" ],
                   58813 : [8158813, "R050" ],
                   58827 : [8158827, "R044" ],
                   70500 : [8170500, "R030" ],
                   70890 : [8170890, "R020" ],
                   70950 : [8170950, "R005" ],
                   70990 : [8170990, "R070" ],
                   71000 : [8171000, "R006" ],
                   71290 : [8171290, "R007" ],
                   71300 : [8171300, "R008" ],
                   71350 : [8171350, "R009" ],
                   71400 : [8171400, "R031" ],
                    7817 : [7817, "R002" ],
                    4595 : [4595, "R043" ], }
# "Special" gauge - 8158810 conceptually provides the runoff that enters
#    Reach 50 from Subbasin 21. There is not a RCHRES so it is handled
#    differently.
SPECIAL_GAUGE = { 58810 : [ 8158810, "R050",
                            { "PERLND" : [ 21 ],
                              "IMPLND" : [ 21 ], }, ], }



# functions
def copyHDF5( cDir, inDir, inName, outName ):
    """
    Copies the cleaned and packed HDF5 file to the working directory.

    The HDF5 file provides for simulation inputs and outputs. If the same
    file is used and edited each time, the file size will continue to
    increase. If this 'clean' input file is used each time the file size
    will remain small. Overwrite and then update the file for each automated
    calibration iteration.

    Parameters
    ----------
    cDir : STR
        Current working directory.
    inDir : STR
        Sub-directory name.
    inName : STR
        Clean, input HDF5 file name.
    outName : STR
        Working, output HDF5 file name.

    Returns
    -------
    HDF5_Path : STR
        Fully qualified pathname with filename for the working HDF5 file.

    """
    # start of function
    InFiler = os.path.normpath( os.path.join( cDir, inDir, inName ) )
    if not os.path.isfile( InFiler ):
        print("File %s not found!!!" % InFiler )
        return ""
    # end if
    # if the file exists then copy it
    cpDest = os.path.normpath( os.path.join( cDir, outName ) )
    HDF5_Path = shutil.copy( InFiler, cpDest )
    # return
    return HDF5_Path


def readProcInputFile( CurDir, MF6Dir, mHSP2Dir, HDF5File, InputsFile ):
    """Read and process the inputs file.

    PEST++ will produce the inputs file for each run. This file has more than
    5,000 parameters that are varied. Most of the parameters are pilot
    points. Some are zones and some FTAB discharges for specified levels


    Parameters
    ----------
    CurDir : str
        Path to current directory.
    MF6Dir : str
        Path to MODFLOW 6 directory
    mHSP2Dir : str
        Path to mHSP2 directory
    HDF5File : str
        Path to current HDF5 file
    InputsFile : str
        Inputs file name.

    Returns
    -------
    RetStatus: int
        0 == success; 1 == failure.

    """
    # imports
    # globals
    global MF6_NAME, ZBIDs_MAT_FILE
    # parameters
    uKey = "uzf"
    zKey = "zone"
    pKey = "pp"
    fKey = "ftab"
    dKey = "drn"
    badReturn = 1
    goodReturn = 0
    retStatus = goodReturn
    # start
    # get the parameter assignment dictionary from the input file
    ParAssignDict = readCPInputsFile(CurDir, InputsFile)
    # now process this to assign parameters
    # want to do all of the assignment here so that only need to load the model
    #   1 time.
    # UZF
    UZFDict = ParAssignDict[uKey]
    # load the model
    sim = flopy.mf6.MFSimulation.load( MF6_NAME, 'mf6', 'mf6', MF6Dir,
                                       verbosity_level=0, )
    mf6 = sim.get_model( MF6_NAME.lower() )

    uzf = mf6.get_package( 'uzf' )# get some model dimensions
    disv = mf6.get_package( 'disv' )
    NLAY = disv.nlay.get_data()
    NCPL = disv.ncpl.get_data()
    IDOM = disv.idomain.get_data()
    # send to the helper function to assign new values
    uzf_info_list, uzf_period = assignUZFParams( UZFDict, uzf )
    # now finish processing for output
    NumUZF = len( uzf_info_list )
    # get the boundary names
    UZFBndNames = sorted( set( [ x[10] for x in uzf_info_list ] ) )
    # define the observations
    ObsDefnList = [ ['Recharge', 'uzf-gwrch'], ['Discharge', 'uzf-gwd'],
                    ['Infilt', 'infiltration'], ['RejInfilt', 'rej-inf'],
                    ['Storage', 'storage'], ['NetInfilt', 'net-infiltration'], ]
    ObsLister = list()
    for lList in ObsDefnList:
        for iName in UZFBndNames:
            ObsLister.append( ( "%s_%s" % (lList[0], iName), lList[1], iName ) )
        # end inner for
    # end outer for
    uzf_obs = { ('uzf_obs.bsv', 'binary'): ObsLister , }
    # remove the old UZF and assign this one. Then write out just the package
    mf6.remove_package( 'uzf' )
    uzf = flopy.mf6.ModflowGwfuzf( mf6, pname='uzf', print_input=False,
                                   print_flows=False, save_flows=True,
                                   boundnames=True, mover=False,
                                   simulate_et=False, linear_gwet=False,
                                   square_gwet=False, simulate_gwseep=True,
                                   unsat_etwc=False, unsat_etae=False,
                                   nuzfcells=NumUZF, ntrailwaves=7,
                                   nwavesets=450, packagedata=uzf_info_list,
                                   perioddata=uzf_period, observations=uzf_obs,
                                   filename='{}.uzf'.format(MF6_NAME) )
    uzf.write()
    # done with UZF
    # Next do the pilot point interpolations in preparation for parameter assign
    PPDict = ParAssignDict[pKey]
    PPRegKeys = sorted( PPDict.keys() )
    RegDictDF = ppInterp( MF6Dir, PPDict )
    # now are ready to assign our values
    ZnDict = ParAssignDict[zKey]
    ZnRegKeys = sorted( ZnDict.keys() )
    # now get the overlap keys - these are for z-only pilot points
    OverlapKeys = [ x for x in PPRegKeys if x in ZnRegKeys ]
    # get the Zone Budget Ids
    InFiler = os.path.normpath( os.path.join( MF6Dir, ZBIDs_MAT_FILE ) )
    with open( InFiler, 'rb' ) as IF:
        ZBMatrix = pickle.load( IF )
    # end with
    # this matrix has the full 5 digit IDs
    # Get the parameter packages
    #   NPF
    oldNPF = mf6.get_package( 'npf' )
    ICellType = oldNPF.icelltype.get_data()
    K11 = oldNPF.k.get_data()
    K22 = oldNPF.k22.get_data()
    K33 = oldNPF.k33.get_data()
    #   STO
    oldSTO = mf6.get_package( 'sto' )
    SS = oldSTO.ss.get_data()
    SY = oldSTO.sy.get_data()
    IConv = oldSTO.iconvert.get_data()
    # now go through the entire domain and check out
    for iI in range(NCPL):
        for kK in range(NLAY):
            cZBId = ZBMatrix[kK, iI]
            cIDom = IDOM[kK, iI]
            if (cZBId < 1) or (cIDom < 1):
                if (cZBId >= 1) or (cIDom >= 1):
                    # this is a conceptual error
                    print("Found ZB Id of %d for IDOM of %d at (%d,%d)!!!" %
                          (cZBId, cIDom, kK+1, iI+1))
                    retStatus = badReturn
                # end if
                # then is inactive
                continue
            # end if
            if cZBId < 10000:
                # this is also a conceptual error
                print("Found ZB Id of %d at (%d,%d)!!!" % (cZBId, kK+1, iI+1))
                retStatus = badReturn
                continue
            # end if
            # need to determine the overall region
            baseIder = int( round( cZBId, -4 ) )
            tR = int( baseIder / 10000 )
            # check if round pushed us up instead of down
            if (tR * 10000 ) > cZBId:
                # correct if round pushed up
                tR -= 1
                baseIder = tR * 10000
            # end if
            cUnitId = cZBId - baseIder
            if cUnitId > 100:
                # know it is a zone because it is a fault. Bounding faults have
                #   a region ID of 8 but internal faults don't have a region
                #   ID because can span multiple regions.
                if cZBId >= 80000:
                    if not (tR == 8):
                        # this is a conceptual error check
                        print("Have region %d for ZB Id %d!!!!" % (tR, cZBId))
                        retStatus = badReturn
                    # end if
                    ZnLookupKey = cZBId
                else:
                    ZnLookupKey = cUnitId
                # end if
                if not ZnLookupKey in ZnRegKeys:
                    print("Found unit %d that is not in the zones!!!" % ZnLookupKey )
                    retStatus = badReturn
                    continue
                # end check if
                curSy = float( ZnDict[ZnLookupKey]["s"] )
                curSs = SsCalcFromSy( curSy )
                curParams = [ float( ZnDict[ZnLookupKey]["x"] ),
                              float( ZnDict[ZnLookupKey]["y"] ),
                              float( ZnDict[ZnLookupKey]["z"] ), curSs, curSy ]
            elif (tR == 8) and (cUnitId < 100):
                # in the bounding fault zones there are some karst and HSG AB
                #   in the surficial layers
                # these are zone values
                if not cZBId in ZnRegKeys:
                    # this is a conceptual error
                    print("Found ZB Id %d at (%d,%d) that is not in Zone dict!!!"
                          % (cZBId, kK+1, iI+1) )
                    retStatus = badReturn
                    continue
                # end if
                curKx = float( ZnDict[cZBId]["x"] )
                curKy = float( ZnDict[cZBId]["y"] )
                curKz = float( ZnDict[cZBId]["z"] )
                curSy = float( ZnDict[cZBId]["s"] )
                curSs = SsCalcFromSy( curSy )
                # set the curParams
                curParams = [ curKx, curKy, curKz, curSs, curSy ]
            else:
                # in this case could be a zone or pilot point
                if cZBId in OverlapKeys:
                    # then know it is combined.
                    curKx = float( ZnDict[cZBId]["x"] )
                    curKy = float( ZnDict[cZBId]["y"] )
                    curSy = float( ZnDict[cZBId]["s"] )
                    curSs = SsCalcFromSy( curSy )
                    # have to get the actual location from the PP DF
                    curRegDF = RegDictDF[tR]
                    colHdr = "%d_z" % cUnitId
                    curKz = float( curRegDF.at[iI+1,colHdr])
                    # set the curParams
                    curParams = [ curKx, curKy, curKz, curSs, curSy ]
                elif cZBId in ZnRegKeys:
                    curKx = float( ZnDict[cZBId]["x"] )
                    curKy = float( ZnDict[cZBId]["y"] )
                    curKz = float( ZnDict[cZBId]["z"] )
                    curSy = float( ZnDict[cZBId]["s"] )
                    curSs = SsCalcFromSy( curSy )
                    # set the curParams
                    curParams = [ curKx, curKy, curKz, curSs, curSy ]
                elif cZBId in PPRegKeys:
                    curRegDF = RegDictDF[tR]
                    colHdr = "%d_x" % cUnitId
                    curKx = float( curRegDF.at[iI+1,colHdr])
                    colHdr = "%d_y" % cUnitId
                    curKy = float( curRegDF.at[iI+1,colHdr])
                    colHdr = "%d_z" % cUnitId
                    curKz = float( curRegDF.at[iI+1,colHdr])
                    colHdr = "%d_s" % cUnitId
                    curSy = float( curRegDF.at[iI+1,colHdr])
                    curSs = SsCalcFromSy( curSy )
                    # set the curParams
                    curParams = [ curKx, curKy, curKz, curSs, curSy ]
                else:
                    print("ZB Id %d for (%d,%d) is not in zones or pilot points!!!"
                          % ( cZBId, kK+1, iI+1 ) )
                    retStatus = badReturn
                    continue
                # end inner if
            # end outer if
            # now assign to our parameter matrices
            K11[kK, iI] = curParams[0]
            K22[kK, iI] = curParams[1]
            K33[kK, iI] = curParams[2]
            SS[kK, iI] = curParams[3]
            SY[kK, iI] = curParams[4]
        # end layer for
    # end cell2D for
    # update our parameter packages
    mf6.remove_package('npf')
    npf = flopy.mf6.ModflowGwfnpf( mf6, save_flows=True, icelltype=ICellType,
                                   k=K11, k22=K22, k33=K33, pname="npf",
                                   filename='{}.npf'.format(MF6_NAME) )
    npf.write()
    mf6.remove_package( 'sto' )
    sto = flopy.mf6.ModflowGwfsto( mf6, pname="sto", save_flows=True,
                                   iconvert=IConv, ss=SS, sy=SY,
                                   transient={0:True},
                                   filename='{}.sto'.format(MF6_NAME), )
    sto.write()
    # update our drain package
    DRNDict = ParAssignDict[dKey]
    drn = mf6.get_package( 'drn' )
    DRNBndNames, drn_period = assignDRNCond( DRNDict, drn )
    NumDRN = len( drn_period[0] )
    # make the drn observations
    Obs_List = [ ( x, 'drn', x ) for x in DRNBndNames ]
    drn_obs = { ('drn_obs.bsv', 'binary'): Obs_List , }
    # add to MODFLOW and write out
    mf6.remove_package( 'drn' )
    drn = flopy.mf6.ModflowGwfdrn(mf6, pname='drn', print_input=False,
                                  print_flows=False, save_flows=True,
                                  observations=drn_obs, boundnames=True,
                                  maxbound=NumDRN, stress_period_data=drn_period,
                                  filename='{}.drn'.format(MF6_NAME))
    drn.write()
    # finally update our ftables
    FTABDict = ParAssignDict[fKey]
    # assign the FTable values
    setFTABs( HDF5File, FTABDict )
    # done so return
    return retStatus


def readCPInputsFile( CurDir, InputsFile ):
    """Read the inputs file generated by PEST++

    Generates ParAssignDict
        Outermost level has keys: 'uzf', 'zone', 'pp', 'ftab', and 'drn'
            * uzf : dictionary, has keys == UZF boundary names - like 'rr_1' or
            'sb_107'
                - values are a dictionary with two keys 'vks', 'thts'
                    - sub dictionary values are floats which are the parameters
            * zones : dictionary, has keys == 5 digit ZB Id (integer) except for
            internal faults which might have only a 3 or 4 digit ZB Id because
            they cross hydrostratigraphic regions.
                - values are dictionary with up to four keys ['x', 'y', 'z', 's']
                    - sub dictionary values are floats which are the zone
                    parameter values.
            * pp : dictionary, has keys == 5 digit ZB Id (integer)
                - values are dictionary with up to four keys ['x', 'y', 'z', 's']
                    - sub dictionary values are another dictionary which has
                    pilot point Ids as keys and the parameter value as values
            * ftab : dictionary, has keys == 2 digit RCHRES Id (integer)
                - values are a dictionary with up to two keys ['ds1', 'ds2']
                that identify the discharge port
                - sub dictionary values are [depth, discharge] pairs
            * drn: dictionary, has keys == 3 digit drn string ID
                - value is a float that is the conductance

    Parameters
    ----------
    CurDir : str
        Path to current directory.
    InputsFile : str
        Inputs file name.

    Returns
    -------
    ParAssignDict : dict
        Dictionary containing parameter values from PEST++ to assign to the
        model.

    """
    # imports
    # globals
    # parameters
    ParAssignDict = dict()
    # start
    InFiler = os.path.normpath( os.path.join( CurDir, InputsFile ) )
    with open(InFiler, 'r') as IF:
        AllLines = IF.readlines()
    # end with and close file
    # now read the file
    iCnt = 0
    for tLine in AllLines:
        if len(tLine) < 3:
            iCnt += 1
            continue
        # end if
        if iCnt == 0:
            iCnt += 1
            continue
        # end if
        # now parse
        tLSplit = tLine.split()
        curVal = float( tLSplit[1] )
        curParam = tLSplit[0].strip()
        cParTypeId = curParam[0]
        cProcParam = curParam[1:]
        if cParTypeId == "u":
            odKey = "uzf"
            cParSplit = cProcParam.split("_")
            cBndName = "%s_%d" % (cParSplit[0], int(cParSplit[1]))
            cPSubTId = cParSplit[2]
            if cPSubTId == "v":
                cPSubParam = "vks"
            elif cPSubTId == "s":
                cPSubParam = "thts"
            else:
                print("Invalid UZF subtype of %s in %s!!!" %
                      (cPSubTId, curParam))
                continue
            # end inner if
            if odKey in ParAssignDict.keys():
                if cBndName in ParAssignDict[odKey].keys():
                    if cPSubParam in ParAssignDict[odKey][cBndName].keys():
                        # this shouldn't happen
                        print( "overwrite parameter for %s with key %s, %s !!!" %
                               (curParam, odKey, cPSubParam))
                        ParAssignDict[odKey][cBndName][cPSubParam] = curVal
                    else:
                        ParAssignDict[odKey][cBndName][cPSubParam] = curVal
                    # end inner if
                else:
                    ParAssignDict[odKey][cBndName] = { cPSubParam : curVal, }
            else:
                ParAssignDict[odKey] = { cBndName : { cPSubParam : curVal, }, }
            # end assign if
        elif cParTypeId == "z":
            odKey = "zone"
            cParSplit = cProcParam.split("_")
            cZBId = int( cParSplit[0] )
            if cZBId < 10000:
                # then is a bounding fault zone. Convert to 5 digit ZB Id
                cSubZoneIder = int( cParSplit[1] )
                if cZBId in [201, 202, 401, 402, 403, 601, 602, 701, 702,
                             801, 802]:
                    cBaseIder = 8 * 10000
                else:
                    cBaseIder = 0
                # end if
                cPSubParam = cParSplit[2].strip()
                curZBFullId = cBaseIder + (cSubZoneIder * 1000) + cZBId
            else:
                curZBFullId = cZBId
                cPSubParam = cParSplit[1].strip()
            # end if
            # now assign
            if odKey in ParAssignDict.keys():
                if curZBFullId in ParAssignDict[odKey].keys():
                    if cPSubParam in ParAssignDict[odKey][curZBFullId].keys():
                        print( "overwrite parameter for %s with key %s, %d, %s !!!"
                              % (curParam, odKey, curZBFullId, cPSubParam))
                        ParAssignDict[odKey][curZBFullId][cPSubParam] = curVal
                    else:
                        ParAssignDict[odKey][curZBFullId][cPSubParam] = curVal
                    # end if
                else:
                    ParAssignDict[odKey][curZBFullId] = { cPSubParam : curVal, }
                # end if
            else:
                ParAssignDict[odKey] = { curZBFullId : { cPSubParam : curVal, }, }
            # end assign if
        elif cParTypeId == "p":
            odKey = "pp"
            cParSplit = cProcParam.split("_")
            cZBId = int( cParSplit[0] )
            if cZBId < 10000:
                # this is an error
                print("Found ZB Id of %d for pp for %s !!!" % (cZBId, curParam))
                continue
            # end if
            cPSubParam = cParSplit[1][0]
            cPPId = int( cParSplit[1][1:] )
            # now assign
            if odKey in ParAssignDict.keys():
                if cZBId in ParAssignDict[odKey].keys():
                    if cPSubParam in ParAssignDict[odKey][cZBId].keys():
                        if cPPId in ParAssignDict[odKey][cZBId][cPSubParam].keys():
                            print( "overwrite parameter for %s with key %s, %d, %s, %d!!!"
                                  % (curParam, odKey, cZBId, cPSubParam, cPPId))
                            ParAssignDict[odKey][cZBId][cPSubParam][cPPId] = curVal
                        else:
                            ParAssignDict[odKey][cZBId][cPSubParam][cPPId] = curVal
                    else:
                        ParAssignDict[odKey][cZBId][cPSubParam] = { cPPId : curVal, }
                else:
                    ParAssignDict[odKey][cZBId] = { cPSubParam : { cPPId : curVal, }, }
            else:
                ParAssignDict[odKey] = { cZBId : { cPSubParam : { cPPId : curVal, }, }, }
        elif cParTypeId == "f":
            odKey = "ftab"
            cParSplit = cProcParam.split("_")
            rrId = int( cParSplit[0] )
            innerKey = cParSplit[1]
            curDepth = int( cParSplit[2] ) / 10.0
            # now assign
            if odKey in ParAssignDict.keys():
                if rrId in ParAssignDict[odKey].keys():
                    if innerKey in ParAssignDict[odKey][rrId].keys():
                        ParAssignDict[odKey][rrId][innerKey].append( [ curDepth, curVal ] )
                    else:
                        ParAssignDict[odKey][rrId][innerKey] = [ [ curDepth, curVal ] ]
                else:
                    ParAssignDict[odKey][rrId] = { innerKey : [ [ curDepth, curVal ], ] }
            else:
                ParAssignDict[odKey] = { rrId : { innerKey : [ [ curDepth, curVal ], ] } }
            # end assign n if
        elif cParTypeId == "d":
            odKey = "drn"
            cParSplit = cProcParam.split("_")
            innerKey = cParSplit[1]
            # now assign
            if odKey in ParAssignDict.keys():
                if innerKey in ParAssignDict[odKey].keys():
                    ParAssignDict[odKey][innerKey] = curVal
                    print( "overwrite parameter for %s with key %s, %s" %
                           ( curParam, odKey, innerKey ) )
                else:
                    ParAssignDict[odKey][innerKey] = curVal
            else:
                ParAssignDict[odKey] = { innerKey : curVal }
            # end assign n if
        else:
            print("Invalid parameter type of %s for %s!!!" %
                  (cParTypeId, curParam))
            continue
        # end if
        iCnt += 1
    # end line for
    # return
    return ParAssignDict


def assignUZFParams( UZFDict, UZFPackage ):
    """Assign UZF parameters VKS and THTS from PEST++

    UZF Dictionary:
        * keys == UZF boundary names - like 'rr_1' or 'sb_107'
        * values are a dictionary with two keys 'vks', 'thts'
            - sub dictionary values are floats which are the parameters

    Parameters
    ----------
    UZFDict : dict
        Collated values from the input file.
    UZFPackage : flopy.uzf package structure - existing

    Returns
    -------
    Tuple, T: 0 - uzf_info_list
              1 - uzf_period dictionary with period 0

    """
    # imports
    # globals
    # parameters
    uzf_info_list = list()
    uzf_period = dict()
    uzf_period0_array = list()
    BName_Index = 10
    VKS_Key = "vks"
    THTS_Key = "thts"
    # locals
    # start
    DictBndNames = sorted( UZFDict.keys() )
    # process UZF
    exUZFForcing = UZFPackage.perioddata.get_data()[0]
    exUZF = UZFPackage.packagedata.get_data()
    nOrgUZF = len( exUZF )
    UZFInfoCols = list( exUZF.dtype.names )
    UZFFCols = list( exUZFForcing.dtype.names )
    # need uzf info list - this is for package data
    # now go through and create the new UZF package with modified values
    iCnt = 0
    for iI in range( nOrgUZF ):
        curBndName = exUZF[iI][UZFInfoCols[BName_Index]]
        if curBndName in DictBndNames:
            curVKS = UZFDict[curBndName][VKS_Key]
            curTHTS = UZFDict[curBndName][THTS_Key]
        # end if
        uzf_info_list.append( [ iCnt, exUZF[iI][UZFInfoCols[1]],
                                exUZF[iI][UZFInfoCols[2]],
                                exUZF[iI][UZFInfoCols[3]],
                                exUZF[iI][UZFInfoCols[4]], curVKS,
                                exUZF[iI][UZFInfoCols[6]], curTHTS,
                                exUZF[iI][UZFInfoCols[8]],
                                exUZF[iI][UZFInfoCols[9]], curBndName ] )
        uzf_period0_array.append( [ iCnt, exUZFForcing[iI][UZFFCols[1]],
                                    exUZFForcing[iI][UZFFCols[2]],
                                    exUZFForcing[iI][UZFFCols[3]],
                                    exUZFForcing[iI][UZFFCols[4]],
                                    exUZFForcing[iI][UZFFCols[5]],
                                    exUZFForcing[iI][UZFFCols[6]],
                                    exUZFForcing[iI][UZFFCols[7]] ] )
        iCnt += 1
    # end for
    uzf_period[0] = uzf_period0_array
    # return
    return ( uzf_info_list, uzf_period )


def ppInterp( CurDir, PPDict ):
    """Interpolate pilot point values to grid points

    PPDict
        * Keys are 5 digit ZB Ids (integer)
        * Values are dictionary
            - Subdictionary keys - up to four from ['x', 'y', 'z', 's']
            - Subdictionary values are another dictionary
                - Subsubdictionary keys - pilot point Ids
                - Subsubdictionary values - parameter values

    Parameters
    ----------
    CurDir : str
        Current working directory where all the files reside.
    PPDict : dict
        Pilot point dictionary

    Returns
    -------
    RegDictDF: Dictionary of DataFrames with interpolated values for each
               parameter type and unit.

    """
    # imports
    # globals
    global PP_META_DICT, PLPROC_EXE
    # parameters
    # locals
    ppRKeys = sorted( PPDict.keys() )
    RegIds = sorted( PP_META_DICT.keys() )
    RegPPDictDF = dict()
    RegDictDF = dict()
    # do the setup stuff
    for tR in RegIds:
        # get the metadata that need
        curVals = PP_META_DICT[tR]
        # open the DataFrames that form the basis for tracking our values
        InFiler = os.path.normpath( os.path.join( CurDir, curVals[2]))
        cAllPtsDF = pd.read_pickle( InFiler )
        InFiler = os.path.normpath( os.path.join( CurDir, curVals[3]))
        cPPtsDF = pd.read_pickle( InFiler )
        PPAllList = curVals[5][0]
        PPZList = curVals[5][1]
        # use this information to setup all of our data structures
        OutFmtStr = "{0:<7d}    {1:<10.3f}    {2:<11.3f}"
        HdrFmtStr = "{0:>7s}    {1:>10s}    {2:>11s}"
        oCnt = 3
        for zbID in PPAllList:
            cHdrX = "%d_x" % zbID
            cHdrY = "%d_y" % zbID
            cHdrZ = "%d_z" % zbID
            cHdrS = "%d_s" % zbID
            cPPtsDF[cHdrX] = -1.0
            OutFmtStr += "    {%d:<12.6f}" % oCnt
            HdrFmtStr += "    {%d:>12s}" % oCnt
            oCnt += 1
            cPPtsDF[cHdrY] = -1.0
            OutFmtStr += "    {%d:<12.6f}" % oCnt
            HdrFmtStr += "    {%d:>12s}" % oCnt
            oCnt += 1
            cPPtsDF[cHdrZ] = -1.0
            OutFmtStr += "    {%d:<12.6f}" % oCnt
            HdrFmtStr += "    {%d:>12s}" % oCnt
            oCnt += 1
            cPPtsDF[cHdrS] = -1.0
            OutFmtStr += "    {%d:<12.6f}" % oCnt
            HdrFmtStr += "    {%d:>12s}" % oCnt
            oCnt += 1
            cAllPtsDF[cHdrX] = -1.0
            cAllPtsDF[cHdrY] = -1.0
            cAllPtsDF[cHdrZ] = -1.0
            cAllPtsDF[cHdrS] = -1.0
        # end for
        for zbID in PPZList:
            cHdrZ = "%d_z" % zbID
            cPPtsDF[cHdrZ] = -1.0
            OutFmtStr += "    {%d:<12.6f}" % oCnt
            HdrFmtStr += "    {%d:>12s}" % oCnt
            cAllPtsDF[cHdrZ] = -1.0
            oCnt += 1
        # end for
        OutFmtStr += " \n"
        HdrFmtStr += " \n"
        # assign to the tracking dictionaries
        RegPPDictDF[tR] = [ cPPtsDF, HdrFmtStr, OutFmtStr ]
        RegDictDF[tR] = cAllPtsDF
    # end for
    # Next populate the pilot points DFs in RegPPDictDF
    for fullZBId in ppRKeys:
        tR = int( round( fullZBId, -4) / 10000 )
        zbId = fullZBId - ( tR * 10000 )
        typeKeys = list( PPDict[fullZBId].keys() )
        for cTyp in typeKeys:
            cHdr = "%d_%s" % (zbId, cTyp)
            cPPDict = PPDict[fullZBId][cTyp]
            cPPIds = sorted( cPPDict.keys() )
            for cPId in cPPIds:
                RegPPDictDF[tR][0].at[ cPId-1, cHdr ] = cPPDict[cPId]
            # end for
        # end for
    # end for
    # write out these DataFrames to CLists, do the interpolation, and load
    #  back to our full points DataFrame
    for tR in RegIds:
        baseIder = tR * 10000
        # get the metadata that need
        curVals = PP_META_DICT[tR]
        PPAllList = curVals[5][0]
        PPZList = curVals[5][1]
        OutFmtStr = RegPPDictDF[tR][2]
        HdrFmtStr = RegPPDictDF[tR][1]
        # write our CList file for this region
        OutFiler = os.path.normpath( os.path.join( CurDir,
                                     "%s_PPVals_Clist.dat" % curVals[0] ) )
        cModDF = RegPPDictDF[tR][0].copy()
        outHdrList = list( RegPPDictDF[tR][0].columns )
        cModDF.set_index( "Cell2D", inplace=True )
        with open( OutFiler, 'w' ) as OID:
            OID.write( HdrFmtStr.format( *outHdrList ) )
            for indx, row in cModDF.iterrows():
                lineList = [ indx ]
                lineList.extend( list( row ) )
                OID.write( OutFmtStr.format( *lineList ) )
            # end for
        # end with
        # now go through krige/interpolate and put interpolated values in the
        #   all points DF
        for zbId in PPAllList:
            cZBIder = baseIder + zbId
            for cTyp in ["x", "y", "z", "s"]:
                cHdr = "%d_%s" % (zbId, cTyp)
                RunFiler = os.path.normpath( os.path.join( CurDir,
                                             curVals[1] % (zbId, cTyp) ) )
                ReadFiler = os.path.normpath( os.path.join( CurDir,
                                              "%s%d.csv" % (cTyp, cZBIder) ) )
                plProcOut = subprocess.run( [ PLPROC_EXE, RunFiler ], cwd=CurDir,
                                            capture_output=True )
                # check the result
                if ( plProcOut.returncode != 0 ):
                    print("PLPROC issue!!!")
                    print("%s" % plProcOut.stdout.decode('utf-8'))
                # end if
                # now read in the output file
                IntDF = pd.read_csv( ReadFiler, header=0, )
                RegDictDF[tR][cHdr] = IntDF["pm_1"].to_numpy(dtype=np.float64)
            # end for
        # end for Id
        for zbId in PPZList:
            cZBIder = baseIder + zbId
            cHdr = "%d_z" % zbId
            RunFiler = os.path.normpath( os.path.join( CurDir,
                                         curVals[1] % (zbId, "z") ) )
            ReadFiler = os.path.normpath( os.path.join( CurDir,
                                          "z%d.csv" % cZBIder ) )
            plProcOut = subprocess.run( [ PLPROC_EXE, RunFiler ], cwd=CurDir,
                                        capture_output=True )
            # check the result
            if ( plProcOut.returncode != 0 ):
                print("PLPROC issue!!!")
                print("%s" % plProcOut.stdout.decode('utf-8'))
            # end if
            # now read in the output file
            IntDF = pd.read_csv( ReadFiler, header=0, )
            RegDictDF[tR][cHdr] = IntDF["pm_1"].to_numpy(dtype=np.float64)
        # end for
    # end regions for
    # return
    return RegDictDF


def assignDRNCond( DRNDict, drn ):
    """Assign the DRN conductance from input file to model

    Parameters
    ----------
    DRNDict : dict
        dictionary that has the conductance by drain boundary.
    drn : flopy drn package.

    Returns
    -------
    Tuple, T: 0 - drain boundary names
              1 - drn_period dictionary with period 0

    """
    # imports
    # globals
    global SPRING_DICT
    # locals
    bndNameDict = dict()
    drn_period = dict()
    drn_period0_array = list()
    # start
    # preprocess the drain dictionary to be a boundary name dictionary
    for sDName in DRNDict.keys():
        curBndName = SPRING_DICT[sDName][0]
        bndNameDict[curBndName] = DRNDict[sDName]
    # end for
    # now get the drain stuff and process
    exDRN = drn.stress_period_data.get_data()[0]
    nOrgDRN = len( exDRN )
    DrnHdrs = list( exDRN.dtype.names )
    ExBndNames = list( set( list( exDRN[:][DrnHdrs[3]] ) ) )
    for iI in range( nOrgDRN ):
        curBndName = exDRN[iI][DrnHdrs[3]]
        if curBndName in bndNameDict.keys():
            curCond = bndNameDict[curBndName]
        else:
            curCond = exDRN[iI][DrnHdrs[2]]
        # end if
        drn_period0_array.append( [exDRN[iI][DrnHdrs[0]], exDRN[iI][DrnHdrs[1]],
                                   curCond, curBndName] )
    # end for
    drn_period[0] = drn_period0_array
    return ( ExBndNames, drn_period )


def setFTABs( HDF5File, FTABDict ):
    """Update FTAB for new parameterization.

    FTAB curves are parameterized for designated depths/volumes with non-
    overlapping ranges of values.

    * ftab : dictionary, has keys == 2 digit RCHRES Id (integer)
        - values are a dictionary with up to two keys ['ds1', 'ds2']
        that identify the discharge port
        - sub dictionary values are [depth, discharge] pairs

    Parameters
    ----------
    CurDir : STR
        Current working directory.
    HDF5File : STR
        FQDN filename for input HDF5 file.
    FTABDict : DICT
        Discharge values to modify.

    Returns
    -------
    None

    """
    # globals
    global FTAB_DICT
    # parameters
    FTAB_ROOT_KEY = r'/FTABLES/'
    # start
    ftabKeys = sorted( FTABDict.keys() )
    for fKey in ftabKeys:
        curFTId = FTAB_DICT[fKey][0]
        # now get the FTABLE from the HDF5 file
        ftabKey = "%s%s/" % ( FTAB_ROOT_KEY, curFTId )
        with pd.HDFStore( HDF5File ) as store:
            curFTab = store.get( key=ftabKey )
        # end with
        IAdjFTab = curFTab.set_index( "Depth" )
        # get the column keys for this FTABLE
        if "ds1" in FTABDict[fKey].keys():
            ds1ValPairs = FTABDict[fKey]["ds1"]
        else:
            ds1ValPairs = []
        # end if
        if "ds2" in FTABDict[fKey].keys():
            ds2ValPairs = FTABDict[fKey]["ds2"]
        else:
            ds2ValPairs = []
        # end if
        for setVals in ds1ValPairs:
            IAdjFTab.at[ setVals[0], "Disch1" ] = setVals[1]
        # end for
        for setVals in ds2ValPairs:
            IAdjFTab.at[ setVals[0], "Disch2" ] = setVals[1]
        # end for
        curFTab["Disch1"] = IAdjFTab["Disch1"].to_numpy(dtype=np.float64)
        curFTab["Disch2"] = IAdjFTab["Disch2"].to_numpy(dtype=np.float64)
        # write the modified FTAB back to the file
        curFTab.to_hdf( HDF5File, ftabKey, format='table', data_columns=True )
    # end FTABLE for
    # return
    return


def readProcOutputs( CurDir, MF6Dir, mHSP2Dir, HDF5File, OutputsFile ):
    """Read coupled simulation outputs and create the output file for PEST++.

    This function writes the outputs file in the order expected by PEST++ to
    work with the instruction set. A DataFrame is serialized in the current
    directory to provide this format.


    Parameters
    ----------
    CurDir : str
        Path to the current directory.
    MF6Dir : str
        Path to MODFLOW 6 directory
    mHSP2Dir : str
        Path to mHSP2 directory
    HDF5File : str
        Path to current HDF5 file
    OutputsFile : str
        Outputs or targets, collated file.

    Returns
    -------
    NumOut : int
        Number of targets written to the file.

    """
    # imports
    import datetime as dt
    from math import sqrt as msqrt
    # globals
    global WL_RANGE, PESTPP_CONTROL_ROOT, GAUGE_MAP_DICT
    # parameters
    PESTPP_OBS_CSV = "%s.obs_data.csv" % PESTPP_CONTROL_ROOT
    FNAME_OUTPUTS_DF = "ObsTemplateDF.pkl"
    HOBS_FILE = "mwell-hydrographs.csv"
    WELL_LABELS_DICT = { "bp" : "BPGCD",
                         "bs": "BSEACD",
                         "cc" : "CCGCD",
                         "ea" : "EAA",
                         "ht" : "HTGCD",
                         "tb" : "WD_BSEACD",
                         "tc" : "WD_CCGCD",
                         "sw" : "WD_SWTCGCD",
                         "tw" : "WD_TWDB", }
    EAA_ID_DICT = { 1303 : 6701303,
                    1403 : 6701403,
                    9101 : 6709101,
                    9110 : 6709110,
                    6801 : 6816801, }
    HdrFmtStr = "{0:<20s}    {1:>16s} \n"
    AValFmtStr = "{0:<20s}    {1:>16.8E} \n"
    # locals
    totAssign = 0
    WLResidsList = list()
    # first get the daily time index
    DayDTIndex = getDTIndexFromMF6( MF6Dir )
    # load the template DataFrame
    InFiler = os.path.normpath( os.path.join( CurDir, FNAME_OUTPUTS_DF ) )
    AllObsDF = pd.read_pickle( InFiler )
    # load the PEST++ obs to DataFrame
    InFiler = os.path.normpath( os.path.join( CurDir, PESTPP_OBS_CSV ) )
    PPPObsDF = pd.read_csv( InFiler, header=0, index_col=0 )
    # get the dictionary of stream gauge comparison time series
    GCompDict = getGaugeCompDict( HDF5File )
    # get the dictionary of water rights comparison time series
    WRCompDict = getWaterRightsExComp( HDF5File )
    # get the dictionary of water budget records for tracking
    WBTrackDict = getWBTrackingDict( MF6Dir )
    # next load and process the MODFLOW output file that we need
    # head observations
    HDSO_Path = os.path.join( MF6Dir, HOBS_FILE )
    HObs_DF = pd.read_csv(HDSO_Path)
    hhdrs = list( HObs_DF.columns )
    hhdrs.remove('time')
    DataDict = dict()
    for tHdr in hhdrs:
        DataDict[tHdr] = np.array( HObs_DF[tHdr], dtype=np.float64 )
    # end for
    Hds_DF = pd.DataFrame( index=DayDTIndex, data=DataDict )
    MonHds_DF = Hds_DF.resample( 'MS' ).mean()
    # now are ready to process and fill the observations
    AllObsDF["sim values"] = -1.0
    for indx, row in AllObsDF.iterrows():
        if indx[0] in ["l", "g"]:
            continue
        # end if
        if indx[0] == "w":
            # then it well water levels which is what we are currently working
            #   on
            obsTyper = indx[1]
            splitObs = indx.split("_")
            shortGCD = splitObs[1]
            curGCDIder = int( splitObs[2] )
            curDateDT = dt.datetime.strptime( splitObs[3], "%Y%m%d" )
            longGCD = WELL_LABELS_DICT[shortGCD]
            if ( longGCD == "EAA" ) and ( curGCDIder in EAA_ID_DICT.keys() ):
                curGCDIder = EAA_ID_DICT[curGCDIder]
            # end if
            HdrStr = "%s_%d" % ( longGCD, curGCDIder )
            # now extract the value by type
            if obsTyper == "p":
                # then is a daily point observation
                simVal = float( Hds_DF.at[curDateDT, HdrStr] )
                AllObsDF.at[indx, "sim values"] = simVal
                totAssign += 1
                curWeight = float( PPPObsDF.at[indx,"weight"] )
                obsVal = float( PPPObsDF.at[indx,"obsval"] )
                curGrp = PPPObsDF.at[indx,"obgnme"]
                if ( curWeight > 0.0 ) or ( curGrp == "valid" ):
                    WLResidsList.append( obsVal - simVal )
                # end if
            elif obsTyper == "a":
                # then is a monthly average observation
                simVal = float( MonHds_DF.at[curDateDT, HdrStr] )
                AllObsDF.at[indx, "sim values"] = simVal
                totAssign += 1
                curWeight = float( PPPObsDF.at[indx,"weight"] )
                obsVal = float( PPPObsDF.at[indx,"obsval"] )
                curGrp = PPPObsDF.at[indx,"obgnme"]
                if ( curWeight > 0.0 ) or ( curGrp == "valid" ):
                    WLResidsList.append( obsVal - simVal )
                # end if
            elif obsTyper == "o":
                # then is a zero weight observation
                simVal = float( MonHds_DF.at[curDateDT, HdrStr] )
                AllObsDF.at[indx, "sim values"] = simVal
                totAssign += 1
            else:
                print("Invalid observation type of %s for %s !!!" %
                      ( obsTyper, indx))
                continue
            # end inner if
        elif indx[0] == "s":
            # stream gauge
            splitObs = indx.split("_")
            gIder = int( splitObs[1] )
            fYear = int( splitObs[2][:4] )
            fMonth = int( splitObs[2][4:] )
            curTS = pd.Timestamp( fYear, fMonth, 1, )
            simVal = float( GCompDict[gIder].at[curTS, "Simulated"] )
            AllObsDF.at[indx, "sim values"] = simVal
            totAssign += 1
        elif indx[0] == "r":
            # water rights check
            splitObs = indx.split("_")
            rIder = int( splitObs[1][1:] )
            fYear = int( splitObs[2][:4] )
            fMonth = int( splitObs[2][4:] )
            curTS = pd.Timestamp( fYear, fMonth, 1, )
            simVal = float( WRCompDict[rIder].at[curTS, "Simulated"] )
            AllObsDF.at[indx, "sim values"] = simVal
            totAssign += 1
        elif indx[0] == "b":
            # water budget recording
            splitObs = indx.split("_")
            cZn = int( splitObs[1] )
            if not cZn in WBTrackDict.keys():
                # this is an error
                print("Unknown zone of %d for observation %s!!!" % (cZn, indx) )
                continue
            # end if
            simVal = WBTrackDict[cZn]
            AllObsDF.at[indx, "sim values"] = simVal
            totAssign += 1
        else:
            print("Unknown observation of %s!!!" % indx)
            continue
        # end outer if
    # end for row in all observations
    # calculate the NRMSE
    NCObs = len( WLResidsList )
    npResids = np.array( WLResidsList, dtype=np.float64 )
    SSE = np.power( npResids, 2.0 ).sum()
    MSE = SSE / NCObs
    RMSE = msqrt( MSE )
    NRMSE = ( RMSE / WL_RANGE )
    AllObsDF.at["l_nrmse", "sim values"] = NRMSE
    totAssign += 1
    # the last thing to do is the NRMSE calcs for the stream gauges
    AllGKeys = sorted( GCompDict.keys() )
    AllSGObsInd = [ x for x in list( PPPObsDF.index ) if x[:2] == "s_" ]
    for gKey in AllGKeys:
        curDF = GCompDict[gKey]
        curDF = curDF.loc[CalibStart:SimEnd].copy()
        obsList = list()
        simList = list()
        for indx, row in curDF.iterrows():
            curTSStr = indx.strftime( "%Y%m" )
            curObsnme = "s_%d_%s" % ( gKey, curTSStr )
            if curObsnme in AllSGObsInd:
                simList.append( row["Simulated"] )
                obsList.append( float( PPPObsDF.at[curObsnme, "obsval" ] ) )
            # end if
        # end for
        # now calculate the nse
        obs = np.array( obsList, dtype=np.float32 )
        sim = np.array( simList, dtype=np.float32 )
        curNSE = vcalc_nse( obs, sim )
        tObsNme = "g_{0:d}".format( gKey )
        AllObsDF.at[tObsNme, "sim values"] = curNSE
        totAssign += 1
    # end gauge key for
    # now check
    if totAssign != len( AllObsDF ):
        # then missed something
        print( "Did not assign all observations; assigned %d and have %d !!!" %
               ( totAssign, len( AllObsDF ) ) )
    # end if
    # now need to write out the observations file
    OutFiler = os.path.normpath( os.path.join( CurDir, OutputsFile ) )
    with open( OutFiler, 'w' ) as OID:
        lineList = [ "obsnme", "value" ]
        OID.write( HdrFmtStr.format( *lineList ) )
        for indx, row in AllObsDF.iterrows():
            lineList = [ indx, float(row["sim values"]) ]
            OID.write( AValFmtStr.format( *lineList ) )
        # end for
    # end with
    # return
    return totAssign


def getDTIndexFromMF6( CurDir ):
    """Get the daily DateTimeIndex from the simulation for use in processing
    results.

    Parameters
    ----------
    CurDir : str
        Current working directory.

    Returns
    -------
    DayDTIndex : pd.DatetimeIndex.

    """
    # imports
    import datetime as dt
    # globals
    global MF6_NAME
    # locals
    # start
    #   load the simulation and model
    sim = flopy.mf6.MFSimulation.load( MF6_NAME, 'mf6', 'mf6', CurDir,
                                       verbosity_level=0, )
    # get the start interval
    tdis = sim.get_package('tdis')
    StartDT = dt.datetime.strptime(tdis.start_date_time.get_data(), "%Y-%m-%d" )
    tpRecArray = tdis.perioddata.get_data()
    totDays = tpRecArray[:]['perlen'].sum()
    CEndDT = StartDT + dt.timedelta( days=totDays )
    CEndDT -= dt.timedelta( hours=1 )
    DayDTIndex = pd.date_range( start=StartDT, end=CEndDT, freq='D' )
    # return
    return DayDTIndex


def getGaugeCompDict( HDF5File ):
    """Extracts simulated results at stream gauge locations

    Parameters
    ----------
    HDF5File : str
        Path to HDF5 output file.

    Returns
    -------
    GCompDict : dict
        Dictionary with monthly-averaged, simulated stream gauge discharge.

    """
    # imports
    # globals
    global GAUGE_MAP_DICT, SPECIAL_GAUGE, SimStart, SimEnd
    # parameters
    ConvAFDtoCFS = lambda AFD: ( AFD * ( 43560.0 / 1.0**2 ) ) * ( 1.0 / (24.0 * 60.0 * 60.0 ) )
    RR_RES_KEY = r'/RESULTS/RCHRES_%s/HYDR'
    ExtractCol = "O1"
    # locals
    GCompDict = dict()
    AllGaugeKeys = sorted( GAUGE_MAP_DICT.keys() )
    SpecialKeys = sorted( SPECIAL_GAUGE.keys() )
    # start
    for gKey in AllGaugeKeys:
        if gKey in SpecialKeys:
            continue
        # end if
        TReach = GAUGE_MAP_DICT[gKey][1]
        curRRKey = RR_RES_KEY % TReach
        with pd.HDFStore( HDF5File ) as store:
            cRRes = store.get( key=curRRKey )
        # end with
        cRRes = cRRes[[ExtractCol]].loc[SimStart:SimEnd].copy()
        monRRes = cRRes.resample( 'MS' ).mean()
        monRRes.columns = ["Simulated"]
        GCompDict[gKey] = monRRes
    # end for
    # next do the special gauge
    for gKey in SpecialKeys:
        TReach = SPECIAL_GAUGE[gKey][1]
        curRRKey = RR_RES_KEY % TReach
        with pd.HDFStore( HDF5File ) as store:
            cRRes = store.get( key=curRRKey )
        # end with
        cRRes = cRRes[["IVOL"]].loc[SimStart:SimEnd].copy()
        cRRes["Simulated"] = cRRes.apply( lambda row: ConvAFDtoCFS( row["IVOL"] ), axis=1 )
        monRRes = cRRes.resample( 'MS' ).mean()
        GCompDict[gKey] = monRRes
    # end for
    # return
    return GCompDict


def getWaterRightsExComp( HDF5File ):
    """Extract simulated water rights diversion for verification

    Parameters
    ----------
    HDF5File : str
        Path to HDF5 output file.

    Returns
    -------
    WRCompDict : dict
        Dictionary by reach of water rights comparisons.

    """
    # imports
    # globals
    global FTAB_DICT, SimStart, SimEnd
    # parameters
    RR_RES_KEY = r'/RESULTS/RCHRES_%s/HYDR'
    WRCompDict = dict()
    RRIds = sorted( FTAB_DICT.keys() )
    # locals
    # start
    for rId in RRIds:
        TReach = FTAB_DICT[rId][1]
        curRRKey = RR_RES_KEY % TReach
        with pd.HDFStore( HDF5File ) as store:
            cRRes = store.get( key=curRRKey )
        # end with
        cRRes = cRRes[["O3"]].loc[SimStart:SimEnd].copy()
        monRRes = cRRes.resample( 'MS' ).mean()
        monRRes.columns = ["Simulated"]
        WRCompDict[rId] = monRRes
    # end for
    # return
    return WRCompDict


def getWBTrackingDict( CurDir ):
    """Extract the average total water budget

    Parameters
    ----------
    CurDir : str
        Path to MODFLOW 6 directory.

    Returns
    -------
    WBTrackDict : dict
        Water budget tracking dictionary.

    """
    # imports
    # globals
    global ZBIDs_MAT_FILE, ZBIDs_LIST_FILE, MF6_NAME, SimStart
    # parameters
    # locals
    WBTrackDict = dict()
    # start
    # get all of the serialized arrays that need to make this calculation
    #   fairly quick and easy
    InFiler = os.path.normpath( os.path.join( CurDir, ZBIDs_LIST_FILE ) )
    with open( InFiler, 'rb' ) as IF:
        UniqueZones = pickle.load( IF )
    # end with
    InFiler = os.path.normpath( os.path.join( CurDir, ZBIDs_MAT_FILE ) )
    with open( InFiler, 'rb' ) as IF:
        ZBMatrix = pickle.load( IF )
    # end with
    InFiler = os.path.normpath( os.path.join( CurDir, "npAreas.pkl" ) )
    with open( InFiler, 'rb' ) as IF:
        npAreas = pickle.load( IF )
    # end with
    InFiler = os.path.normpath( os.path.join( CurDir, "npZ.pkl" ) )
    with open( InFiler, 'rb' ) as IF:
        npZ = pickle.load( IF )
    # end with
    InFiler = os.path.normpath( os.path.join( CurDir, "npVol.pkl" ) )
    with open( InFiler, 'rb' ) as IF:
        npVol = pickle.load( IF )
    # end with
    InFiler = os.path.normpath( os.path.join( CurDir, "npBotZ.pkl" ) )
    with open( InFiler, 'rb' ) as IF:
        npBotZ = pickle.load( IF )
    # end with
    # need to get storage terms from the MODFLOW model
    sim = flopy.mf6.MFSimulation.load( MF6_NAME, 'mf6', 'mf6', CurDir,
                                       verbosity_level=0, )
    mf6 = sim.get_model( MF6_NAME.lower() )
    # get some model dimensions
    disv = mf6.get_package( 'disv' )
    NLAY = disv.nlay.get_data()
    NCPL = disv.ncpl.get_data()
    IDOM = disv.idomain.get_data()
    # get the storage params
    sto = mf6.get_package( 'sto' )
    SS = sto.ss.get_data()
    SY = sto.sy.get_data()
    # now load the heads file
    headfile = '{}.hds'.format(MF6_NAME)
    HdsFileName = os.path.join( CurDir, headfile )
    HeadsObj = flopy.utils.binaryfile.HeadFile( HdsFileName )
    outSPTimes = HeadsObj.get_times()
    NumOutTimes = len( outSPTimes )
    outTS = [ SimStart + pd.Timedelta(days=x) for x in outSPTimes ]
    AllVolDF = pd.DataFrame( index=outTS, columns=UniqueZones )
    for oInt in range(NumOutTimes):
        curTS = outTS[oInt]
        h = HeadsObj.get_data( totim=outSPTimes[oInt] )
        disvH = np.reshape( h, (NLAY, NCPL) )
        # now get the Z heights for each part of the calc
        npZAbBot = np.where( IDOM > 0, disvH - npBotZ, 0.0 )
        npZAbBot = np.where( npZAbBot >= 0.0, npZAbBot, 0.0 )
        npSYZ = np.where( npZ > npZAbBot, npZAbBot, npZ )
        # calculate the total water volume in each cell
        npWVol = np.zeros( (NLAY, NCPL), dtype=np.float32 )
        for kK in range(NLAY):
            npWVol[kK,:] = ( ( ( SS[kK,:] * npSYZ[kK,:] ) * ( npZAbBot[kK,:] * npAreas ) ) +
                             ( SY[kK,:] * npSYZ[kK,:] * npAreas ) )
        # end for
        for cZn in UniqueZones:
            cZnVol = np.where( ZBMatrix == cZn, npWVol, 0.0 )
            AllVolDF.at[curTS, cZn] = cZnVol.sum()
        # end for zone
    # end for output times
    # now just need go through and get the mean value to return in our dictionary
    for cZn in UniqueZones:
        curVal = AllVolDF[cZn].mean()
        WBTrackDict[cZn] = curVal
    # end for
    # return
    return WBTrackDict


def vcalc_nse( obs, predict ):
    """Calculate NSE from observed, obs, and predicted, predict, arrays.

    Calculates an array of NSE values, one for each output

    Args:
        obs (np.array): observed time series (#Num Time Intervals, #Outputs)
        predict (np.array): predicted, or simulated, time series
                            (#Num Time Intervals, #Outputs)

    Returns:
        NSE (np.array): Nash-Sutcliffe-Efficiency value which can range from
                        negative infinity to 1.0 (#Outputs)
    """
    # now are ready to do our calcs.
    resids = obs - predict
    sq_resids = np.square( resids )
    sum_sqresides =sq_resids.sum( axis=0 )
    obs_mean = obs.mean( axis=0 )
    diff_mean = obs - obs_mean
    sq_diffm = np.square( diff_mean )
    sum_diffsq = sq_diffm.sum( axis=0 )
    denom = np.where( np.abs( sum_diffsq ) < 0.00001, 0.00001, sum_diffsq )
    right_side = sum_sqresides / denom
    # calc
    NSE = 1.0 - right_side
    # return
    return NSE


### standalone execution block
if __name__ == "__main__":
    # first get the current working directory
    CurDir = os.getcwd()
    MF6Dir = os.path.normpath( os.path.join( CurDir, "pyMF6" ) )
    mHSP2Dir = os.path.normpath( os.path.join( CurDir, "mHSP2" ) )
    pyHS2MF6Dir = os.path.normpath( os.path.join( CurDir, "pyHS2MF6" ) )
    # copy the clean HDF5 base file to the designated location for mods
    HDF5File = copyHDF5( mHSP2Dir, IN_HDF5_DIR, IN_HDF5_NAME, OUT_HDF5_NAME )
    if len( HDF5File ) < 5:
        # this is an error
        sys.exit("HDF5 file issue!!!")
    # end if
    # read the input file and update the HDF5 File
    retStatus = readProcInputFile( CurDir, MF6Dir, mHSP2Dir, HDF5File,
                                   INPUTS_FILE )
    # check
    if retStatus != 0:
        # then there was an error
        sys.exit("Input file issue!!!")
    # end if
    # ready to run the simulation
    # run the coupled model
    cpMainPath = os.path.normpath( os.path.join( pyHS2MF6Dir, "coupledMain.py" ) )
    cpMOut = subprocess.run( [ PYTHON_EXE, cpMainPath, CP_INPUT_FILE],
                               cwd=CurDir, capture_output=True )
    # check the result
    if ( cpMOut.returncode != 0 ):
        sys.exit("%s" % cpMOut.stdout.decode('utf-8'))
    # end if
    # now need to run ZoneBudget before process the results for PEST
    #zbOut = subprocess.run( [ ZB6_EXE ], cwd=MF6Dir, capture_output=True )
    # check the result
    #if ( zbOut.returncode != 0 ):
    #    sys.exit("%s" % zbOut.stdout.decode('utf-8'))
    # end if
    # process MF6 outputs to generate easy targets for comparison
    TotOuts = readProcOutputs( CurDir, MF6Dir, mHSP2Dir, HDF5File,
                               OUTPUTS_FILE )
    # done

#EOF