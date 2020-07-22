# -*- coding: utf-8 -*-
"""
.. module:: pyHS2MF6_Inputs.py
   :platform: Windows, Linux
   :synopsis: Module containing methods related to input files

.. moduleauthor:: Nick Martin <nmartin@swri.org>

This module provides input file reading methods for a coupled model.
Also provides a module for persistent storage of these input values.

"""
# imports
import datetime as dt

# module wide parameters
DATE_FMT = "%Y-%m-%d"
"""Date format used in the coupled model input file"""
# module wide variables
INPUT_FILE = None
"""Coupled model input file"""
HSP2_DIR = None
"""Directory for HSPsquared input fles"""
HSP2_HDF5 = None
"""Name of HSPsquared HDF5 input file"""
FULL_HSP2_HDF5 = None
"""FQDN pathname for HSPsquared, HDF5 input file. Created from HSP2_HDF5
and HSP2_DIR"""
START_DT = None
"""Simulation start time"""
END_DT = None
"""Simulation end time """
MF6_DIR = None
"""MODFLOW 6 model directory. *.sim file must be here"""
HSP2_NUM_RR = None
"""Total number of RCHRES objects/targets in the HSP2 model"""
HSP2_NUM_PL = None
"""Total number of PERLND objects/targets in the HSP2 model"""
HSP2_NUM_IL = None
"""Total number of IMPLND objects/targets in the HSP2 model"""
MF6_NLAY = None
"""Number of layers in the MODFLOW 6 model"""
MF6_NCPL = None
"""Number of cells per layer in the MODFLOW 6 model"""
MF6_NVERT = None
"""Number of vertices per layer in the MODFLOW 6 model"""
MF6_IUZFN = None
"""Number of UZF cells defined in the MODFLOW 6 model"""
MF6_ROOT = None
"""Root name for the MODFLOW 6 model to run """
RR_MAP_GW_PFILE = None
"""Pickle file with dictionary for mapping RCHRES locations to groundwater
model cells. This dictionary has a required format. The dictionary keys
are the HSPF target Id, i.e., 'R001'. The values are a list, L, with
3 items.
    L[0] (int): HSPF RCHRES exit that goes to groundwater. Must be > 1 and
                <= 5.
    L[1] (float): total UZF cell area in this target ID
    L[2] (pd.DataFrame): DataFrame that describes the UZF cell specifications
                         within this target ID. The DataFrame index is
                         the 2D Cell ID, 1-based. The DataFrame has four
                         columns.
        - "iuzno" (int): UZF cell ID, 1-based
        - "TopActive" (int): the top active layer for this model cell, 
                             1-based
        - "SArea_m2" (float): surface area of this cell within the 
                              HSPF target ID in m2
        - "Weight" (float): dimensionless weight for allocating flows from
                            HSPF to this cell. Should be > 0 and <= 100.0
"""
PL_MAP_GW_PFILE = None
"""Pickle file with dictionary for mapping PERLND areas to groundwater
model cells. This dictionary has a required format. The dictionary keys
are the HSPF target Id, i.e., 'P001'. The values are a list, L, with
2 items.
    L[0] (float): total UZF cell area in this target ID
    L[1] (pd.DataFrame): DataFrame that describes the UZF cell specifications
                         within this target ID. The DataFrame index is
                         the 2D Cell ID, 1-based. The DataFrame has four
                         columns.
        - "iuzno" (int): UZF cell ID, 1-based
        - "TopActive" (int): the top active layer for this model cell, 
                             1-based
        - "SArea_m2" (float): surface area of this cell within the 
                              HSPF target ID in m2
        - "Weight" (float): dimensionless weight for allocating flows from
                            HSPF to this cell. Should be > 0 and <= 100.0
"""
SP_MAP_GW_PFILE = None
"""Pickle file with dictionary for mapping MODFLOW 6 springs that are 
represented as drain boundaries to HSPF targets. This dictionary has
a required format. The dictionary keys are the labels/names for the 
springs as represented in the *.drn and *.drn.obs files. The values
are lists, L, where:
    L[0] (str): target ID for the HSPF location
    L[1] (int): 2D cell Id, 1-based, for the cell where the drain is
                placed
    L[2] (int): top active layer, 1-based, for the cell where the drain
                is placed
    L[3] (float): surface area for the cell where the drain is located

*Note: the combination (top active layer, 2D Cell ID) fully specifies the 
drain location for MODFLOW 6 using DISV
"""
FULL_RR_MAP = None
"""FQDN path and file name for RR mapping - assumes that in same directory 
as input file"""
FULL_PL_MAP = None
"""FQDN path and file name for PL mapping - assumes that in same directory 
as input file"""
FULL_SP_MAP = None
"""FQDN path and file name for SP mapping - assumes that in same directory 
as input file"""


def readInputFile( FileName, DirPath ):
    """Read the input file and store to the module-wide globals.
    Reads designated key words from lines that do not start with '#' and that
    have the designated key word separated from its value by and '='
    
    Args:
        FileName (str): name for the input file
        DirPath (str): FQDN filepath for the directory with the input file
        
    Returns:
        retStat (int): return status 0 means success
        
    """
    # imports
    import os
    # global
    global INPUT_FILE, HSP2_DIR, HSP2_HDF5, START_DT, END_DT
    global DATE_FMT, MF6_DIR, HSP2_NUM_RR, HSP2_NUM_PL, HSP2_NUM_IL
    global MF6_NLAY, MF6_NCPL, MF6_NVERT, MF6_ROOT, RR_MAP_GW_PFILE 
    global FULL_HSP2_HDF5, PL_MAP_GW_PFILE, FULL_RR_MAP, FULL_PL_MAP
    global SP_MAP_GW_PFILE, FULL_SP_MAP, MF6_IUZFN
    # parameters
    #    good return
    goodReturn = 0
    #    bad return codes
    noFile = -1
    fileReadError = -2
    #    read keys
    hsp2_dir = "HSP2_DIR"
    hsp2_hdf5 = "HSP2_HDF5"
    start_dt = "START_DT"
    end_dt = "END_DT"
    mf6_dir = "MF6_DIR"
    hsp2_num_rr = "HSP2_NUM_RR"
    hsp2_num_pl = "HSP2_NUM_PL"
    hsp2_num_il = "HSP2_NUM_IL"
    mf6_nlay = "MF6_NLAY"
    mf6_ncpl = "MF6_NCPL"
    mf6_nvert = "MF6_NVERT"
    mf6_iuzfn = "MF6_IUZFN"
    mf6_root = "MF6_ROOT"
    rr_gw_file = "RR_MAP_GW_PFILE"
    pl_gw_file = "PL_MAP_GW_PFILE"
    sp_gw_file = "SP_MAP_GW_PFILE"
    # our key list
    KEY_LIST = sorted( [ hsp2_dir, hsp2_hdf5, start_dt, end_dt, mf6_dir,
                         hsp2_num_rr, hsp2_num_pl, hsp2_num_il, mf6_nlay,
                         mf6_ncpl, mf6_nvert, mf6_root, rr_gw_file, 
                         pl_gw_file, sp_gw_file, mf6_iuzfn ] )
    # locals
    # start
    FilePath = os.path.normpath( os.path.join( DirPath, FileName ) )
    INPUT_FILE = FilePath
    if not os.path.isfile( INPUT_FILE ):
        # this is an error
        print( "Input file %s not found!!!" % INPUT_FILE )
        return noFile
    # now open and read in the entire input file
    with open( FilePath, 'r' ) as InFID:
        AllLines = InFID.readlines()
    # end of with and close the file
    # go through a line at a time and process ..
    for tLine in AllLines:
        # skip blank lines
        if len(tLine) < 3:
            continue
        # skip lines that start with # - comment lines
        if tLine[0] == "#":
            continue
        # now try to process our line. Only process lines that have '='
        if "=" in tLine:
            tLSplit = tLine.split("=")
            tKey = tLSplit[0].strip()
            tValStr = tLSplit[1].strip()
            if not tKey in KEY_LIST:
                continue
            # if made it here need to process this value
            # processing is custom for each defined key
            if tKey.upper() == hsp2_dir:
                try:
                    mtValStr = tValStr.strip('\"')
                    HSP2_DIR = os.path.normpath( mtValStr )
                except:
                    print( "Could not process %s value of %s !!!\n" % 
                                ( hsp2_dir, mtValStr ) )
                    return fileReadError
            elif tKey.upper() == hsp2_hdf5:
                mtValStr = tValStr.strip('\"')
                HSP2_HDF5 = mtValStr
            elif tKey.upper() == start_dt:
                try:
                    START_DT = dt.datetime.strptime( tValStr, DATE_FMT )
                except:
                    print( "Could not parse datetime from %s for %s" % 
                                ( tValStr, start_dt ) )
                    return fileReadError
            elif tKey.upper() == end_dt:
                try:
                    END_DT = dt.datetime.strptime( tValStr, DATE_FMT )
                except:
                    print( "Could not parse datetime from %s for %s" % 
                                ( tValStr, end_dt ) )
                    return fileReadError
            elif tKey.upper() == mf6_dir:
                try:
                    mtValStr = tValStr.strip('\"')
                    MF6_DIR = os.path.normpath( mtValStr )
                except:
                    print( "Could not process %s value of %s !!!\n" % 
                                ( mf6_dir, mtValStr ) )
                    return fileReadError
            elif tKey.upper() == hsp2_num_rr:
                try:
                    HSP2_NUM_RR = int( tValStr )
                except:
                    print( "Could not process %s value of %s !!!!\n" %
                           ( hsp2_num_rr, tValStr ) )
                    return fileReadError
            elif tKey.upper() == hsp2_num_pl:
                try:
                    HSP2_NUM_PL = int( tValStr )
                except:
                    print( "Could not process %s value of %s !!!!\n" %
                           ( hsp2_num_pl, tValStr ) )
                    return fileReadError
            elif tKey.upper() == hsp2_num_il:
                try:
                    HSP2_NUM_IL = int( tValStr )
                except:
                    print( "Could not process %s value of %s !!!!\n" %
                           ( hsp2_num_il, tValStr ) )
                    return fileReadError
            elif tKey.upper() == mf6_nlay:
                try:
                    MF6_NLAY = int( tValStr )
                except:
                    print( "Could not process %s value of %s !!!!\n" %
                           ( mf6_nlay, tValStr ) )
                    return fileReadError
            elif tKey.upper() == mf6_ncpl:
                try:
                    MF6_NCPL = int( tValStr )
                except:
                    print( "Could not process %s value of %s !!!!\n" %
                           ( mf6_ncpl, tValStr ) )
                    return fileReadError
            elif tKey.upper() == mf6_nvert:
                try:
                    MF6_NVERT = int( tValStr )
                except:
                    print( "Could not process %s value of %s !!!!\n" %
                           ( mf6_nvert, tValStr ) )
                    return fileReadError
            elif tKey.upper() == mf6_iuzfn:
                try:
                    MF6_IUZFN = int( tValStr )
                except:
                    print( "Could not process %s value of %s !!!!\n" %
                           ( mf6_iuzfn, tValStr ) )
                    return fileReadError
            elif tKey.upper() == mf6_root:
                try:
                    mtValStr = tValStr.strip('\"')
                    MF6_ROOT = str( mtValStr )
                except:
                    print( "Could not process %s value of %s !!!\n" % 
                                ( mf6_root, mtValStr ) )
                    return fileReadError
            elif tKey.upper() == rr_gw_file:
                mtValStr = tValStr.strip('\"')
                RR_MAP_GW_PFILE = mtValStr
            elif tKey.upper() == pl_gw_file:
                mtValStr = tValStr.strip('\"')
                PL_MAP_GW_PFILE = mtValStr
            elif tKey.upper() == sp_gw_file:
                mtValStr = tValStr.strip('\"')
                SP_MAP_GW_PFILE = mtValStr
            # end of key if
        # end of '=' in
    # end of for AllLines
    # check to make sure that got everything
    for tKey in KEY_LIST:
        if tKey == hsp2_dir:
            if HSP2_DIR is None:
                print( "Did not read a value in the input file for %s" %
                            ( hsp2_dir ) )
                return fileReadError
        elif tKey == hsp2_hdf5:
            if HSP2_HDF5 is None:
                print( "Did not read a value in the input file for %s" %
                            ( hsp2_hdf5 ) )
                return fileReadError
        elif tKey == start_dt:
            if START_DT is None:
                print( "Did not read a value in the input file for %s" %
                            ( start_dt ) )
                return fileReadError
        elif tKey == end_dt:
            if END_DT is None:
                print( "Did not read a value in the input file for %s" %
                            ( end_dt ) )
                return fileReadError
        elif tKey == mf6_dir:
            if MF6_DIR is None:
                print( "Did not read a value in the input file for %s" %
                            ( mf6_dir ) )
                return fileReadError
        elif tKey == hsp2_num_rr:
            if HSP2_NUM_RR is None:
                print( "Did not read a value in the input file for %s" %
                            ( hsp2_num_rr ) )
                return fileReadError
        elif tKey == hsp2_num_pl:
            if HSP2_NUM_PL is None:
                print( "Did not read a value in the input file for %s" %
                            ( hsp2_num_pl ) )
                return fileReadError
        elif tKey == hsp2_num_il:
            if HSP2_NUM_IL is None:
                print( "Did not read a value in the input file for %s" %
                            ( hsp2_num_il ) )
                return fileReadError
        elif tKey == mf6_nlay:
            if MF6_NLAY is None:
                print( "Did not read a value in the input file for %s" %
                            ( mf6_nlay ) )
                return fileReadError
        elif tKey == mf6_ncpl:
            if MF6_NCPL is None:
                print( "Did not read a value in the input file for %s" %
                            ( mf6_ncpl ) )
                return fileReadError
        elif tKey == mf6_nvert:
            if MF6_NVERT is None:
                print( "Did not read a value in the input file for %s" %
                            ( mf6_nvert ) )
                return fileReadError
        elif tKey == mf6_iuzfn:
            if MF6_IUZFN is None:
                print( "Did not read a value in the input file for %s" %
                            ( mf6_iuzfn ) )
                return fileReadError
        elif tKey == mf6_root:
            if MF6_ROOT is None:
                print( "Did not read a value in the input file for %s" %
                            ( mf6_root ) )
                return fileReadError
        elif tKey == rr_gw_file:
            if RR_MAP_GW_PFILE is None:
                print( "Did not read a value in the input file for %s" %
                            ( rr_gw_file ) )
                return fileReadError
        elif tKey == pl_gw_file:
            if PL_MAP_GW_PFILE is None:
                print( "Did not read a value in the input file for %s" %
                            ( pl_gw_file ) )
                return fileReadError
        elif tKey == sp_gw_file:
            if SP_MAP_GW_PFILE is None:
                print( "Did not read a value in the input file for %s" %
                            ( sp_gw_file ) )
                return fileReadError
        # end if
    # end of checking for
    # now process the full file names
    HSP2_DIR = os.path.normpath( HSP2_DIR )
    FULL_HSP2_HDF5 = os.path.normpath( os.path.join( HSP2_DIR, HSP2_HDF5 ) )
    if not os.path.exists( FULL_HSP2_HDF5 ):
        # this is an error
        print( "File %s does not exist !!!\n" % FULL_HSP2_HDF5 )
        return fileReadError
    # return
    # check the MODFLOW model directory
    MF6_DIR = os.path.normpath( MF6_DIR )
    if not os.path.exists( MF6_DIR ):
        # this is an error
        print( "Directory %s does not exist !!!\n" % MF6_DIR )
        return fileReadError
    # mapping dictionary pickle files
    FULL_RR_MAP = os.path.normpath( os.path.join( DirPath, RR_MAP_GW_PFILE ) )
    FULL_PL_MAP = os.path.normpath( os.path.join( DirPath, PL_MAP_GW_PFILE ) )
    FULL_SP_MAP = os.path.normpath( os.path.join( DirPath, SP_MAP_GW_PFILE ) )
    if not os.path.exists( FULL_RR_MAP ):
        # this is an error
        print( "Input file %s does not exist !!!\n" % FULL_RR_MAP )
        return fileReadError
    if not os.path.exists( FULL_PL_MAP ):
        # this is an error
        print( "Input file %s does not exist !!!\n" % FULL_PL_MAP )
        return fileReadError
    if not os.path.exists( FULL_SP_MAP ):
        # this is an error
        print( "Input file %s does not exist !!!\n" % FULL_SP_MAP )
        return fileReadError
    # return
    return goodReturn


def get_HSP2_DIR():
    """Get the HSP2_DIR global
    """
    # globals
    global HSP2_DIR
    return HSP2_DIR


def get_FULL_HSP2_HDF5():
    """Get the FULL_HSP2_HDF5 global
    """
    # globals
    global FULL_HSP2_HDF5
    return FULL_HSP2_HDF5


def get_START_DT():
    """Get the START_DT global
    """
    global START_DT
    return START_DT


def get_END_DT():
    """Get the END_DT global
    """
    global END_DT
    return END_DT


def get_HSP2_NUM_RR():
    """Get the HSP2_NUM_RR global
    """
    global HSP2_NUM_RR
    return HSP2_NUM_RR


def get_HSP2_NUM_PL():
    """Get the HSP2_NUM_PL global
    """
    global HSP2_NUM_PL
    return HSP2_NUM_PL


def get_HSP2_NUM_IL():
    """Get the HSP2_NUM_IL global
    """
    global HSP2_NUM_IL
    return HSP2_NUM_IL


def get_MF6_NLAY():
    """Get the MF6_NLAY global
    """
    global MF6_NLAY
    return MF6_NLAY


def get_MF6_NCPL():
    """Get the MF6_NCPL global
    """
    global MF6_NCPL
    return MF6_NCPL


def get_MF6_NVERT():
    """Get the MF6_NVERT global
    """
    global MF6_NVERT
    return MF6_NVERT


def get_MF6_IUZFN():
    """Get the MF6_IUZFN global
    """
    global MF6_IUZFN
    return MF6_IUZFN


def get_MF6_DIR():
    """Get the MF6_DIR global
    """
    global MF6_DIR
    return MF6_DIR


def get_MF6_ROOT():
    """Get the MF6_ROOT global
    """
    global MF6_ROOT
    return MF6_ROOT


def get_FULL_RR_MAP():
    """Get the FULL_RR_MAP global
    """
    global FULL_RR_MAP
    return FULL_RR_MAP


def get_FULL_PL_MAP():
    """Get the FULL_PL_MAP global
    """
    global FULL_PL_MAP
    return FULL_PL_MAP


def get_FULL_SP_MAP():
    """Get the FULL_SP_MAP global
    """
    global FULL_SP_MAP
    return FULL_SP_MAP


# EOF