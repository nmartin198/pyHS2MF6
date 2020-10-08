#!/usr/bin/python3
"""
The main block for mHSP2 which is a replacement for *HSPsquared* main.

*HSPsquared* (HSP2) was completely modified and rearranged to create a 
main time loop with a sub-loop of operations/targets. The original HSPF 
logic is a main-loop of operations/targets and then a sub-loop for each
target that is the time loop. Consequently, the time loop is run 
completely for each operation and target.

To couple HSPF to MODFLOW6, need to be able to break into the time loop
at the beginning of each day. This Python module provides the replacement
for HSP2\main.py for coupling to MODFLOW 6. There are two main time loop
versions within this module. The user controls which version is run by
executing ``..\coupledMain.py`` or ``..\standaloneMain.py.`` Both "mains" 
use functions within this module. Function *salocaMain* is for standalone 
execution, and functions *setUPPreTL* and *mainTL* are for coupled 
(to MODFLOW 6) execution.

The message passing queue functions are only used when coupled mode
execution is requested. Also the main block (``if __name__ == main():``)
in this module is what is launcehd to start the independent process, 
spawned by the coupled controller and queue manager. 

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
# imports for this module
import os
import sys
# code block to make sure that all required modules are in path at
# run time
OUR_MODULE_PATH = os.path.abspath( __file__ )
OUR_PACKAGE_PATH = os.path.abspath( os.path.join( OUR_MODULE_PATH, '..' ) )
PATH_LIST = sys.path
if ( not OUR_PACKAGE_PATH in PATH_LIST ):
    sys.path.append( OUR_PACKAGE_PATH )
# end if
# other imports
import datetime as dt
from collections import defaultdict
import pandas as pd
import numpy as np
from multiprocessing import Queue
from multiprocessing.managers import SyncManager
from queue import Empty
# pyHS2MF6 package imports
import locaLogger as CL
import locaHyperwat as PLD 
import locaHrchhyd as RR
import locaHimpwat as IMP


# globals for this module
# ---------------------------------------------------------------------
# HSPF-related. Generally should not be changed unless are expanding
# the implementation. Most of these are parameters
TARG_PERVLND = "PERLND"
"""Key value for pervious land targets"""
TARG_IMPLND = "IMPLND"
"""Key value for impervious land targets"""
TARG_RCHRES = "RCHRES"
"""Key value for reach/reservoir targets"""
KEY_ACT_PWAT = "PWATFG"
"""Key value for simulating standard pervious water runoff"""
nKEY_ACT_PWAT = "PWATER"
"""New HDF5 format, key value for simulating standard pervious
water runoff"""
KEY_ACT_IWAT = "IWATFG"
"""Key value for simulating standard impervious water runoff"""
nKEY_ACT_IWAT = "IWATER"
"""New HDF5 format, key value for simulating standard impervious 
water runoff"""
KEY_ACT_RRHYD = "HYDRFG"
"""Key value for simulating HYDR portion of reach reservoirs"""
nKEY_ACT_RRHYD = "HYDR"
"""New HDF5 format, key value for simulating HYDR portion of reach 
reservoirs"""
SUPPORTED_ACTIVITIES = { TARG_PERVLND : [ [KEY_ACT_PWAT], [nKEY_ACT_PWAT] ],
                         TARG_IMPLND : [ [KEY_ACT_IWAT], [nKEY_ACT_IWAT] ],
                         TARG_RCHRES : [ [KEY_ACT_RRHYD], [nKEY_ACT_RRHYD] ], }
"""Dictionary of supported activities"""
TARG_DICT = dict()
"""Dictionary with target types as keys and list of target ids as values"""
KEY_TS_PRECIP = "PREC"
"""External time series key for precipitation"""
KEY_TS_PET = "PETINP"
"""External time series key for input PET"""
SIMTIME_INDEXES = dict()
"""Dictionary that holds simulation time indexes in case they happen 
to be different
"""
DAILY_DELT_STR = "1440"
"""DELT string representing daily, 24 hours * 60 minutes """
GFTAB_DICT = dict()
"""Global FTABLE dictionary that stores the FTABLEs by FTABLE number
"""
GTS_DICT = dict()
"""Global time series dictionary that stores the time series by SVOLNO
key
"""
MAP_TS_DICT = dict()
"""Dictionary to map solution structure to time series.

Keys, tuple of (solution type, ID), and values [ SVOLNO, TMEMN, TVOLNO]
"""
SEQUENCE_DICT = { TARG_PERVLND : [ [ 100, "AIRTFG" ], 
                                   [ 200, "SNOWFG" ],
                                   [ 300, [ KEY_ACT_PWAT, nKEY_ACT_PWAT ] ] ], 
                  TARG_IMPLND : [ [ 100, "ATMPFG" ], 
                                   [ 200, "SNOWFG" ],
                                   [ 300, [ KEY_ACT_IWAT, nKEY_ACT_IWAT ] ] ], 
                  TARG_RCHRES : [ [ 100, [ KEY_ACT_RRHYD, nKEY_ACT_RRHYD ] ] ],
}
"""Holds the required calculation sequence by supported target type.

In HSPsquared, this is read in from the HDF5 file. Anyone can change
edit the HDF5 file which opens the possibility of unintentional 
breakage of the program through incorrect editing of a portion of 
the HDF5 file. Consequently, this is hard coded here because to
modify this sequence successfully, the code needs to be modified.
"""


# ---------------------------------------------------------------------
# Queue definition and management items
HOST = 'localhost'
"""Host machine for queue server.

Localhost means that the process are set-up to be on all the same 
machine. The queue server and the clients are in different processes
on the same 'machine'.
"""
CLIENTHOST = '127.0.0.1'
"""Host machine for queue clients.

Clients are on the same 'machine' as the queue server when local 
descriptors like 'localhost' or '127.0.0.1' are used.
"""
PORT0 = 45492
"""Port number for the HSP2 queue.

Port numbers for queues need to be the same for each independent process 
for connection. Additionally, ports need to be opened in any firewall
software even for local simulation.
"""
PORT1 = 45493
"""Port number for the MODFLOW 6 queue.

Port numbers for queues need to be the same for each independent process 
for connection. Additionally, ports need to be opened in any firewall
software even for local simulation.
"""
PORT2 = 45494
"""Port number for global error handling and communications queue.

Port numbers for queues need to be the same for each independent process 
for connection. Additionally, ports need to be opened in any firewall
software even for local simulation.
"""
AUTHKEY = "authkey".encode()
"""Authorization key for queue access.

This is not currently setup in a secure manner. If you plan on using 
pyHS2MF6 across a public or partially public network, then you should
give some thought to the AUTHKEY and a means of securing this value.
AUTHKEY needs to be encoded to a byte string.
"""
QUEUE_TIMEOUT = ( 60.0 * 5.0 )
"""Queue wait timeout before error in seconds.

This is for the from pyMF6 queue and determines the mHSP2 wait time
for receipt from MODFLOW 6.
"""
QUEUE_ERROR = [ "Error" ]
"""Error message to put on queues for program termination """
QINIT_MSG = [ "Hello" ]
"""Queue intialization and checkin message"""
START_QUEUE_TO = ( 60.0 * 5.0 )
"""Queue wait timeout before error in seconds.

This is for program startup communications.
"""
QREADY_MSG = [ "Ready" ]
"""Queue intialization and checkin message"""
QEND_MSG = [ "End" ]
"""End of simulation message"""

# ---------------------------------------------------------------------
# Queue methods

# create the queue manager class
# needs to be at the top level so that is pickleable. Do not need to do
# anything here just subclass SyncManager
class QueueManager(SyncManager):
    """Create the queue manager class.

    Needs to be at top level of the module so that is pickleable. Do not
    need anything here except to subclass SyncManager.

    """
    pass


def QueueServerClient(ThisHost, Porter, CustomAuth):
    """Get a client connection a queue.
    
    The connection is bidirectional and can use this connection for both get 
    and put.
            
    Args:
        ThisHost (str): host name. Should be '127.0.0.1' for the same machine
        Porter (int): the port number to listen on
        CustomAuth (str): the custom authorization string
    
    Returns:
        locaMain.QueueManager: the client connection
        
    """
    QueueManager.register('get_queue')
    QueueManager.register('get_name')
    QueueManager.register('get_description')
    manager = QueueManager(address = (ThisHost, Porter), authkey = CustomAuth)
    manager.connect() # This starts the connected client
    return manager


def WriteQueueCheckToLog( qMF6 ):
    """Write queue checks to log file
    
    Args:
        qMF6 (Queue): the from MODFLOW6 queue
    
    Returns:
        int: function status; 0 == success
    
    """
    # imports
    # globals
    # parameters
    goodReturn = 0
    badReturn = -1
    # do the output
    try:
        MF6QueueSize = str( qMF6.qsize() )
    except:
        # in this case just return
        errMsg = "Exception thrown getting queue size for output.\n" \
                 "Exception info:\n\t%s\n\n" % sys.exc_info()[0]
        CL.LOGR.error( errMsg )
        # return
        return badReturn
    # if made it here then output
    infoMsg = "The from MODFLOW6 queue size is %s\n\n" % MF6QueueSize
    CL.LOGR.info( infoMsg )
    # return
    return goodReturn


# ---------------------------------------------------------------------
# HSPF customized methods
def setSimTimeIndexes( allops, general, hdfType ):
    """Sets the simulation time indexes from operational sequence in the
    hdf5 file.

    At this time are only excepting daily time steps so this is all that
    will be returned. If a daily time step is not specified in the 
    operational sequence, then an error will be thrown.

    Args:
        allops (np.recarray): operations listing from locaHSP2HDF5
        general (dict): GENERAL dictionary from locaHSP2HDF5
        hdfType (int): type of HDF5 file; 0 == original format; 1 == new format

    Returns:
        int: function status; 0 == success

    """
    # imports
    from locaHSP2HDF5 import DFCOL_OPSEQ_SDELT, KEY_GEN_START
    from locaHSP2HDF5 import KEY_GEN_END, HSP2_TIME_FMT, nKEY_START
    from locaHSP2HDF5 import nKEY_END
    # globals
    global SIMTIME_INDEXES, DAILY_DELT_STR
    # parameters
    goodReturn = 0
    badReturn = -1
    # locals
    # start
    # next get the unique values
    unDTVals = list( np.unique( allops[ DFCOL_OPSEQ_SDELT ] ) )
    # check that the supported time step type exists here
    if not DAILY_DELT_STR in unDTVals:
        # this is an error
        errMsg = "Only daily time steps are currently supported.\n" \
                 "No daily time step specifications were made.\n" \
                 "In the input operational sequences, you must use " \
                 "daily time steps!!!"
        CL.LOGR.error( errMsg )
        return badReturn
    # now check the number of time step specifications
    if len( unDTVals ) > 1:
        # this is not currently supported
        warnMsg = "Only daily time steps are currently supported.\n" \
                  "The following time steps are specified:\n %s\n" \
                  "Only %s will be used!!!" % ( unDTVals, DAILY_DELT_STR )
        CL.LOGR.warning( warnMsg )
        print( "%s" % warnMsg )
    # now set our time index ...
    if hdfType == 0:
        startDT = dt.datetime.strptime( 
                    general[ KEY_GEN_START ], HSP2_TIME_FMT )
        endDT = dt.datetime.strptime( 
                    general[ KEY_GEN_END ], HSP2_TIME_FMT )
    else:
        startDT = dt.datetime.strptime( 
                    general['Info'][ nKEY_START ], HSP2_TIME_FMT )
        endDT = dt.datetime.strptime( 
                    general['Info'][ nKEY_END ], HSP2_TIME_FMT )
    # end if
    DailyDTInd = pd.date_range( start=startDT, end=endDT, freq='D' )
    # now assign
    SIMTIME_INDEXES[ DAILY_DELT_STR ] = DailyDTInd
    # now set the DAYFG arrays
    PLD.setupDAYFG( DailyDTInd )
    IMP.setupHR1FG( DailyDTInd )
    # return
    return goodReturn


def getDailySimTimeIndex():
    """Returns the daily simulation time index from the SIMTIME_INDEXES 
    dictionary.

    Must be called after setSimTimeIndexes

    Returns:
        pd.datetimeindex: daily simulation time series index

    """
    # globals
    global SIMTIME_INDEXES, DAILY_DELT_STR
    # 
    tIndex = SIMTIME_INDEXES[ DAILY_DELT_STR ]
    return tIndex 


def checkOpsSpec( allops, ucs, hdfType ):
    """Checks the activities and operations desired and creates lists of
    target types.

    Currently only PWATFG for PERLND, IWATFG for IMPLND, and HYDR
    for RCHRES are supported. Before going through the time and
    operations loops warn the user that only these will be implemented

    Args:
        allops (np.recarray): operations listing from locaHSP2HDF5
        ucs (dict): user control dictionary from locaHSP2HDF5
        hdfType (int): type of HDF5 file; 0 == original format; 1 == new format

    Returns:
        int: function status; 0 == success

    """
    # imports
    from locaHSP2HDF5 import DFCOL_OPSEQ_TARG, DFCOL_OPSEQ_ID
    # globals
    global SUPPORTED_ACTIVITIES, TARG_DICT
    # parameters
    goodReturn = 0
    badReturn = -1
    # locals
    # start
    # get the type keys
    typeKeys = list( SUPPORTED_ACTIVITIES.keys() )
    # get number of operations
    num_ops = len( allops )
    for jJ in range( num_ops ):
        cTarg = allops[ DFCOL_OPSEQ_TARG ][jJ]
        cID = allops[ DFCOL_OPSEQ_ID ][jJ]
        if hdfType == 0:
            cActivity = ucs[ cTarg, "ACTIVITY", cID ]
        elif hdfType == 1:
            cActivity = ucs[(cTarg, 'GENERAL', cID)]['ACTIVITY']
        else:
            errMsg = "Only HDF5 file types of 0 and 1 are supported. " \
                     "Have value of %d!!!" % ( hdfType )
            CL.LOGR.error( errMsg )
            return badReturn
        # end if
        if not cTarg in typeKeys:
            # this is an error
            errMsg = "For operation %d found unsupported target type o" \
                     "f %s!!!!" % ( (jJ + 1), cTarg )
            CL.LOGR.error( errMsg )
            return badReturn
        # now add to our tracking dictionary list
        if cTarg in TARG_DICT.keys():
            TARG_DICT[cTarg].append( cID )
        else:
            TARG_DICT[cTarg] = [ cID ]
        # now check if our supported activity is desired
        totActive = 0
        for checks in SUPPORTED_ACTIVITIES[ cTarg ][ hdfType ]:
            totActive += cActivity[ checks ]
        # end for
        if totActive <= 0:
            # this is an error
            errMsg = "Only activities %s are supported for %s \n" \
                     "None of these are active for operation %d1!!!" % \
                     ( SUPPORTED_ACTIVITIES[ cTarg ][ hdfType ], cTarg, (jJ +1) )
            CL.LOGR.error( errMsg )
            return badReturn
        # next check that nothing is active that not supported and if 
        #   so warn the user
        if hdfType == 0:
            actCols = list( cActivity.index )
        else:
            actCols = list( cActivity.keys() )
        # end if
        for cAct in actCols:
            if cAct in SUPPORTED_ACTIVITIES[ cTarg ][ hdfType ]:
                continue
            # check the value
            if cActivity[cAct] > 0:
                # this is not supported
                warnMsg = "Activity %s is not supported for %s \n" \
                          "This activity will not be simulated!!!" % \
                          ( cAct, cTarg )
                #print( warnMsg )
                CL.LOGR.warning( warnMsg )
            # end if
        # end activity for
    # end operations for
    # return
    return goodReturn


def setParmsFlagsUCS( sim_delt, ucs, hdfType ):
    """Transfer the parameter values and flags from the hdf file to
    our target modules.
    
    Currently only "PWATFG", "IWATFG", and "HYDRFG" are supported. Note 
    that these names have changed slightly under the new HDF5 file format
    and both naming conventions are supported.

    Args:
        sim_delt (float): time step duration 
        ucs (dict): user control dictionary from locaHSP2HDF5
        hdfType (int): type of HDF5 file; 0 == original format; 
                       1 == new format
    
    Returns:
        int: function status; 0 == success

    """
    #imports
    from locaHSP2HDF5 import getMONTHLYs
    # globals
    global TARG_DICT, TARG_PERVLND, TARG_IMPLND, TARG_RCHRES
    global KEY_ACT_PWAT, KEY_ACT_IWAT, KEY_ACT_RRHYD
    global nKEY_ACT_PWAT, nKEY_ACT_IWAT, nKEY_ACT_RRHYD
    # parameters
    goodReturn = 0
    badReturn = -1
    CalMonths = [ 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 
                  'AUG', 'SEP', 'OCT', 'NOV', 'DEC' ]
    # locals
    # start
    targKeys = TARG_DICT.keys()
    for ttKey in targKeys:
        allTargIds = TARG_DICT[ ttKey ]
        for tID in allTargIds:
            if ttKey == TARG_PERVLND:
                # only PWATFG is supported
                if hdfType == 0:
                    cFlagVals = ucs[(ttKey, KEY_ACT_PWAT, tID)]
                    allIndexs = list( cFlagVals.index )
                else:
                    paramsD = ucs[(ttKey, nKEY_ACT_PWAT, tID)]['PARAMETERS']
                    statesD = ucs[(ttKey, nKEY_ACT_PWAT, tID)]['STATES']
                    cFlagVals = { **paramsD, **statesD }
                    allIndexs = list( cFlagVals.keys() )
                # end if
                # call our accessory function
                retStat = PLD.configFlagsParams( tID, cFlagVals, allIndexs )
                if retStat != 0:
                    return badReturn
                # if check
            elif ttKey == TARG_IMPLND:
                # only IWATFG is supported
                if hdfType == 0:
                    cFlagVals = ucs[(ttKey, KEY_ACT_IWAT, tID)]
                    allIndexs = list( cFlagVals.index )
                else:
                    paramsD = ucs[(ttKey, nKEY_ACT_IWAT, tID)]['PARAMETERS']
                    statesD = ucs[(ttKey, nKEY_ACT_IWAT, tID)]['STATES']
                    cFlagVals = { **paramsD, **statesD }
                    allIndexs = list( cFlagVals.keys() )
                # end if
                # call our accessory function
                retStat = IMP.configFlagsParams( tID, cFlagVals, allIndexs )
                if retStat != 0:
                    return badReturn
                # if check
            elif ttKey == TARG_RCHRES:
                # only HYDRFG is supported
                if hdfType == 0:
                    cFlagVals = ucs[(ttKey, KEY_ACT_RRHYD, tID)]
                    allIndexs = list( cFlagVals.index )
                else:
                    paramsD = ucs[(ttKey, nKEY_ACT_RRHYD, tID)]['PARAMETERS']
                    statesD = ucs[(ttKey, nKEY_ACT_RRHYD, tID)]['STATES']
                    cFlagVals = { **paramsD, **statesD }
                    allIndexs = list( cFlagVals.keys() )
                # call our accessory function
                retStat = RR.configFlagsParams( tID, cFlagVals, allIndexs, hdfType )
                if retStat != 0:
                    return badReturn
                # if check
            # end if
        # end for target id
    # end of target key for
    # now can set the parameter values that need to be adjusted for
    #    internal units. Need to make sure that have the operator type
    #    before calling
    for ttKey in targKeys:
        allTargIds = TARG_DICT[ ttKey ]
        if len( allTargIds ) == 0:
            continue
        # end if
        # now call the setup
        if ttKey == TARG_PERVLND:
            PLD.setDelT( sim_delt )
        elif ttKey == TARG_RCHRES:
            RR.setDelT( sim_delt )
        elif ttKey == TARG_IMPLND:
            IMP.setDelT( sim_delt )
        # end if
    # end for
    # also set the number of exits for each RCHRES. This is stored
    #   under GENERAL in UCS
    allTargIds = TARG_DICT[ TARG_RCHRES ]
    for tID in allTargIds:
        if hdfType == 0:
            uci = ucs[ TARG_RCHRES, "GENERAL_INFO", tID ]
        else:
            uci = ucs[ TARG_RCHRES, nKEY_ACT_RRHYD, tID ]['PARAMETERS']
        # end if
        if "NEXITS" in uci.keys():
            nExits = int( uci["NEXITS"] )
            RR.setNExits( tID, nExits )
        else:
            # this is an error
            errMsg = "Keyword 'NEXITS' is not in 'GENERAL_INFO' for %s!!!!" % \
                     tID
            CL.LOGR.error( errMsg )
            return badReturn
        # next do the lake flag
        if "LKFG" in uci.keys():
            lFlag = int( uci["LKFG"] )
            RR.setLakeFlag( tID, lFlag )
        else:
            # this is an error
            errMsg = "Keyword 'LKFG' is not in 'GENERAL_INFO' for %s!!!!" % \
                     tID
            CL.LOGR.error( errMsg )
            return badReturn
    # end of for
    # the final item of business is to transfer monthly values from read-in
    #   structures to the calculation structures. This is done differently
    #   depending on the input HDF5 file format.
    if hdfType == 0:
        simMonthlys = getMONTHLYs()
        if len( simMonthlys ) < 1:
            return goodReturn
        # end if
        # here then have a monthly's dictionary
        mKeys = list( simMonthlys.keys() )
        for tKey in mKeys:
            ttKey = tKey[0]
            tID = tKey[1]
            # get the values dictionary for this key
            tDict = simMonthlys[tKey]
            targKeys = list( tDict.keys() )
            for paramK in targKeys:
                valTup = tDict[paramK]
                if ttKey == TARG_PERVLND:
                    rStat = PLD.setMonthlyParams( tID, paramK, valTup )
                elif ttKey == TARG_IMPLND:
                    rStat = IMP.setMonthlyParams( tID, paramK, valTup )
                else:
                    # this target type not supported
                    warnMsg = "Monthly values only supported for %s and %s. " \
                              "Type %s is not supported and monthly array " \
                              "%s is ignored!!!" % \
                              ( TARG_PERVLND, TARG_IMPLND, ttKey, paramK )
                    CL.LOGR.warning( warnMsg )
                    continue
                # end if
                # check the return status
                if rStat != 0:
                    # then the parameter name was not recognized
                    warnMsg = "Monthly parameter %s for type %s is not " \
                              "supported. These values are ignored!!!" % \
                              ( paramK, ttKey )
                    CL.LOGR.warning( warnMsg )
                    continue
                # end if
            # end parameter for
        # end key for
    else:
        # this is for the new style. Here the monthlys are in the UCS under a 
        # monthly key extension
        allKeys = list( ucs.keys() )
        for tKey in allKeys:
            ttKey = tKey[0]
            tID = tKey[2]
            # get the keys for this outer key
            tDict = ucs[tKey]
            targKeys = list( tDict.keys() )
            for checkP in targKeys:
                if 'MONTHLY_' in checkP:
                    paramK = checkP.strip('MONTHLY_')
                else:
                    continue
                # end if
                # need to add an 'M' to the end of the parameter
                paramK += "M"
                #get the annual dictionary for this parameter
                monDict = tDict[checkP]
                # make a list in calendar year order
                calOList = [ monDict[x] for x in CalMonths ]
                # now are ready to assign
                if ttKey == TARG_PERVLND:
                    rStat = PLD.setMonthlyParams( tID, paramK, calOList )
                elif ttKey == TARG_IMPLND:
                    rStat = IMP.setMonthlyParams( tID, paramK, calOList )
                else:
                    # this target type not supported
                    warnMsg = "Monthly values only supported for %s and %s. " \
                              "Type %s is not supported and monthly array " \
                              "%s is ignored!!!" % \
                              ( TARG_PERVLND, TARG_IMPLND, ttKey, paramK )
                    CL.LOGR.warning( warnMsg )
                    continue
                # end if
                # check the return status
                if rStat != 0:
                    # then the parameter name was not recognized
                    warnMsg = "Monthly parameter %s for type %s is not " \
                              "supported. These values are ignored!!!" % \
                              ( paramK, ttKey )
                    CL.LOGR.warning( warnMsg )
                    continue
                # end if
            # end targ keys for
        # end targets for
    # end if
    # done so return
    return goodReturn


def initAllocTargStructures( sim_len ):
    """Initialize all target structures including time series,
    flags, parameters, and initial values.

    This takes care of initializing or allocating the simulation
    memory by creating np.recarrays of the simulation length.

    Args:
        sim_len (int): number of time steps in the simulation

    Returns:
        int: function status; 0 == success
    
    """
    # imports
    from locaCoupling import setUpRRRecArrays, setUpPLRecArrays
    # globals
    global TARG_DICT, TARG_PERVLND, TARG_IMPLND, TARG_RCHRES
    # parameters
    goodReturn = 0
    #badReturn = -1
    # locals
    # start
    # first go throught the target dictionary and initialize all of
    #   the targets in the model.
    targKeys = TARG_DICT.keys()
    for ttKey in targKeys:
        if ttKey == TARG_PERVLND:
            # run the pervious land initialization
            PLD.setUpRecArrays( TARG_DICT[ ttKey ], sim_len )
            setUpPLRecArrays( TARG_DICT[ ttKey ], sim_len )
        elif ttKey == TARG_IMPLND:
            # run the impervous land initialization
            IMP.setUpRecArrays( TARG_DICT[ ttKey ], sim_len )
        elif ttKey == TARG_RCHRES:
            # run the reaach/reservoir intitialization
            RR.setUpRecArrays( TARG_DICT[ ttKey ], sim_len )
            setUpRRRecArrays( TARG_DICT[ ttKey ], sim_len )
        # end if
    # end of target key for
    # return
    return goodReturn


def setTargDataTS( sim_len ):
    """Set the input time series into the target structures.

    **Note** that this only works with daily simulation time steps
    Time steps are stored in minutes so this should always be
    1440.0 minutes or 1 day.

    Args:
        sim_len (int): number of time steps in the simulation

    Returns:
        int: function status; 0 == success
    
    """
    # imports
    # globals
    global TARG_DICT, TARG_PERVLND, TARG_IMPLND, TARG_RCHRES, GTS_DICT
    global MAP_TS_DICT
    # parameters
    goodReturn = 0
    badReturn = -1
    # locals
    # start
    # go through target dictionary and set all target time series
    targKeys = TARG_DICT.keys()
    mapKeys = MAP_TS_DICT.keys()
    for ttKey in targKeys:
        allTargIds = TARG_DICT[ ttKey ]
        for tID in allTargIds:
            # first check if have external time series
            if not ( ttKey, tID ) in mapKeys:
                continue
            # now get our mapping list
            cTSList = MAP_TS_DICT[ ( ttKey, tID ) ]
            # now check our type and send to our excessory function
            if ttKey == TARG_PERVLND:
                retStat = PLD.configExternalTS( sim_len, cTSList, 
                                                GTS_DICT )
                if retStat != 0:
                    return badReturn
                # end check if
            elif ttKey == TARG_IMPLND:
                # impervious land time series
                retStat = IMP.configExternalTS( sim_len, cTSList, 
                                                GTS_DICT )
                if retStat != 0:
                    return badReturn
                # end check if
            elif ttKey == TARG_RCHRES:
                # rchres time series
                retStat = RR.configExternalTS( sim_len, cTSList, 
                                               GTS_DICT )
                if retStat != 0:
                    return badReturn
                # end check if
            # end outer if
        # end for tID
    # end for ttKey
    # return
    return goodReturn


def setOutputSave( ucs, hdfType ):
    """Extract the save specifications from the hdf5 storage structures
    and send to the target modules.

    Args:
        ucs (dict): user control dictionary from locaHSP2HDF5
        hdfType (int): type of HDF5 file; 0 == original format; 
                       1 == new format
    
    Returns:
        int: function status; 0 == success

    """
    # imports
    # globals
    global TARG_DICT, SUPPORTED_ACTIVITIES, TARG_PERVLND, TARG_IMPLND
    global TARG_RCHRES
    # parameters
    goodReturn = 0
    badReturn = -1
    # locals
    # start
    targKeys = TARG_DICT.keys()
    for ttKey in targKeys:
        allTargIds = TARG_DICT[ ttKey ]
        allActs = SUPPORTED_ACTIVITIES[ ttKey ][ hdfType ]
        for aAct in allActs:
            for tID in allTargIds:
                if hdfType == 0:
                    savetable = ucs[ ttKey, aAct, 'SAVE', tID ]
                    stTypes = list( savetable.index )
                else:
                    savetable = ucs[ ttKey, aAct, tID]['SAVE']
                    stTypes = list( savetable.keys() )
                # end if
                retStat = 1
                if ttKey == TARG_PERVLND:
                    retStat = PLD.setOutputControlFlags( tID, savetable, stTypes )
                elif ttKey == TARG_IMPLND:
                    retStat = IMP.setOutputControlFlags( tID, savetable, stTypes )
                elif ttKey == TARG_RCHRES:
                    retStat = RR.setOutputControlFlags( tID, savetable, stTypes )
                # end if
                if retStat != 0:
                    errMsg = "Issue setting output control for %s, %s, %s!!!" \
                             % ( ttKey, aAct, tID )
                    CL.LOGR.error( errMsg )
                    return badReturn
                # end check if
            # end for tID
        # end for aAct
    # end for ttKey
    # return
    return goodReturn


def writeOutputs( hdfname, tIndex, hdfType, IsCoupled):
    """Write out the outputs at the end of the simulation.

    Args:
        hdfname (str): HDF5 file to output to
        tIndex (pd.DateTimeIndex): time series index for outputs
        hdfType (int): type of HDF5 file; 0 == original format; 
                       1 == new format
        IsCoupled (bool): is a coupled simulation?

    Returns:
        int: function status; success == 0

    """
    # imports
    from locaCoupling import writeOutputs as wCOuts
    # globals
    global TARG_DICT, SUPPORTED_ACTIVITIES, TARG_PERVLND, TARG_IMPLND
    global TARG_RCHRES, KEY_ACT_PWAT, KEY_ACT_IWAT, KEY_ACT_RRHYD
    global nKEY_ACT_PWAT, nKEY_ACT_IWAT, nKEY_ACT_RRHYD
    # parameters
    goodReturn = 0
    badReturn = -1
    # locals
    # start
    targKeys = TARG_DICT.keys()
    # open our store for output
    with pd.HDFStore( hdfname ) as store:
        for ttKey in targKeys:
            allActs = SUPPORTED_ACTIVITIES[ ttKey ][ hdfType ]
            for aAct in allActs:
                if ttKey == TARG_PERVLND:
                    if aAct in [ KEY_ACT_PWAT, nKEY_ACT_PWAT ]:
                        retStat = PLD.writeOutputs( store, tIndex )
                        if retStat != 0:
                            # error
                            errMsg = "Issue writing out %s, %s !!!!" % \
                                     ( ttKey, aAct )
                            CL.LOGR.error( errMsg )
                            return badReturn
                    # end inner if
                elif ttKey == TARG_IMPLND:
                    if aAct in [ KEY_ACT_IWAT, nKEY_ACT_IWAT ]:
                        retStat = IMP.writeOutputs( store, tIndex )
                        if retStat != 0:
                            # error
                            errMsg = "Issue writing out %s, %s !!!!" % \
                                     ( ttKey, aAct )
                            CL.LOGR.error( errMsg )
                            return badReturn
                    # end inner if
                elif ttKey == TARG_RCHRES:
                    if aAct in [ KEY_ACT_RRHYD, nKEY_ACT_RRHYD ]:
                        retStat = RR.writeOutputs( store, tIndex )
                        if retStat != 0:
                            # error
                            errMsg = "Issue writing out %s, %s !!!!" % \
                                     ( ttKey, aAct )
                            CL.LOGR.error( errMsg )
                            return badReturn
                    # end inner if
                # end type if
            # end activity for
        # end type for
        # now do the coupled outputs
        if IsCoupled:
            retStat = wCOuts( store, tIndex )
            if retStat != 0:
                # error
                errMsg = "Issue writing coupled tracking arrays to file !!!"
                CL.LOGR.error( errMsg )
                return badReturn
            # end check if
        # end if coupled
    # end with and store closed
    # return
    return goodReturn


def setHRUAreas( linkdd ):
    """Extract the HRU surface areas and store for post-processing.

    This involves setting the areas for PERLND and IMPLND. These
    are only stored in the SCHEMATIC and LINKS sections of the
    inputs as the area factor or AFACTOR. So have to process through
    this linkdd which is ordered by reach to extract these values

    Args:
        linkdd(dict): dictionary of links with reaches as keys

    Returns:
        int: function status; 0 == success 

    """
    # imports
    # globals
    global TARG_IMPLND, TARG_PERVLND
    # parameters
    goodReturn = 0
    badReturn = -1
    # locals
    GoodTypes = [ TARG_IMPLND, TARG_PERVLND ]
    # start
    PervProcList = list()
    ImpervProcList = list()
    AllLinkKeys = linkdd.keys() 
    for rKey in AllLinkKeys:
        cSchemeLink = linkdd[ rKey ]
        # this is a list of Pandas series objects
        for tLink in cSchemeLink:
            # first get the mass link iD and the source vol
            try:
                sVolType = str( tLink["SVOL"] )
                sVolID = str( tLink["SVOLNO"] )
                aFactor = float( tLink["AFACTR"] )
            except:
                # this is an unrecoverable error
                errMsg = "Issue extracting area from schematic " \
                         "link %s!!!" % str( tLink )
                CL.LOGR.error( errMsg )
                return badReturn
            # now process
            if sVolType in GoodTypes:
                if sVolType == TARG_PERVLND:
                    if sVolID in PervProcList:
                        # already done
                        continue
                    # end if
                    # call function
                    PLD.setWSAreas( sVolID, aFactor )
                    # add to list
                    PervProcList.append( sVolID )
                elif sVolType == TARG_IMPLND:
                    if sVolID in ImpervProcList:
                        # already done
                        continue
                    # end if
                    # call function
                    IMP.setWSAreas( sVolID, aFactor )
                    # add to list
                    ImpervProcList.append( sVolID )
                # end if
            else:
                continue
            # end if
        # end for RCHRES link
    # end for rKey
    # return
    return goodReturn


def setFlowLinks( linkdd, mldd, hdfType ):
    """Setup the link structues, or routing, among targets.

    This requires a combination of the defined mass links 
    and schematic defined in the UCI file and ported to the
    HDF5 file.

    At this point only linkages among "flow" types: PERLND; IMPLAND;
    and RCHRES are supported. Note that only RCHRES is supported as 
    a receiving target - this means that a usable mass link and 
    schematic link can only have RCHRES as the TVOL and that
    PERLND and IMPLAND can never be the TVOL.

    Args:
        linkdd (dict): dictionary with schematic linkage among 
                        targets
        mldd (dict): mass link definitions
        hdfType (int): type of HDF5 file; 0 == original format; 
                       1 == new format
    
     Returns:
        int: function status; success == 0

    """
    # imports
    from locaHrchhyd import RR_TGRPN_SUPP, RR_TMEMN_SUPP
    # globals
    global SUPPORTED_ACTIVITIES, TARG_DICT, TARG_RCHRES
    # parameters
    goodReturn = 0
    badReturn = -1
    # locals
    # start
    # first check our mass link definitions. The only thing that is 
    #  supported is RCHRES as a target
    SuppTargs = list( SUPPORTED_ACTIVITIES.keys() )
    massLinkD = dict()
    mlKeys = mldd.keys()
    for strInd in mlKeys:
        # now look at the entries
        # only support a list length of 1
        bigLList = mldd[strInd]
        numLinks = len( bigLList )
        if numLinks < 1:
            warnMsg = "Mass link %s has no entries and will be " \
                      "skipped!!!" % strInd
            CL.LOGR.warning( warnMsg )
            #print("%s" % warnMsg)
            continue
        elif numLinks > 1:
            warnMsg = "Mass link %s has %d link entries. Only the first " \
                      "one will be parsed!!!" % ( strInd, numLinks )
            CL.LOGR.warning( warnMsg )
            #print("%s" % warnMsg)
        # process the 1 link
        linkList = bigLList[0]
        addLink = True
        cSMLNO = linkList.MLNO 
        cSVol = linkList.SVOL
        cSGrpn = linkList.SGRPN 
        cSMemn = linkList.SMEMN 
        cTVol = linkList.TVOL  
        cTMemn = linkList.TMEMN
        cMFactor = linkList.MFACTOR
        cSMemsb = linkList.SMEMSB
        if hdfType == 0:
            cTGrpn = linkList.TGRPN
            # get the mass link num as an integer
            try:
                intInd = int( cSMLNO )
            except:
                errMsg = "Could not convert mass link id string %s to an " \
                        "integer for mass link dictionary key %s!!!" % \
                        ( cSMLNO, strInd )
                CL.LOGR.error( errMsg )
                return badReturn
        else:
            cTGrpn = RR_TGRPN_SUPP
            # get the mass link num as an integer
            try:
                intInd = int( cSMLNO.strip('ML') )
            except:
                errMsg = "Could not convert mass link id string %s to an " \
                        "integer for mass link dictionary key %s!!!" % \
                        ( cSMLNO, strInd )
                CL.LOGR.error( errMsg )
                return badReturn
        # end if
        # now do our checks
        if not cSVol in SuppTargs:
            # warn that not supported
            warnMsg = "Have target type %s as source for mass link %d. " \
                        "This target type is unsupported and the mass link " \
                        "will be ignored!!!" % ( cSVol, intInd )
            CL.LOGR.warning( warnMsg )
            #print("%s" % warnMsg)
            addLink = False 
        if not ( cTVol == TARG_RCHRES ):
            # warn that not supported
            warnMsg = "Only target type %s is supported for mass link " \
                        "destinations. Mass Link %d has %s for destination " \
                        "type. This mass link will be ignored!!!" % \
                        ( TARG_RCHRES, intInd, cTVol )
            CL.LOGR.warning( warnMsg )
            #print("%s" % warnMsg)
            addLink = False 
        if ( addLink and ( not ( cTGrpn == RR_TGRPN_SUPP ) ) ):
            # warn that not supported
            warnMsg = "Only mass link flow group %s is supported for " \
                        "target type %s. Mass Link %d has %s for group " \
                        "type. This mass link will be ignored!!!" % \
                        ( RR_TGRPN_SUPP, TARG_RCHRES, intInd, cTGrpn )
            CL.LOGR.warning( warnMsg )
            #print("%s" % warnMsg)
            addLink = False 
        if ( addLink and ( cTGrpn == RR_TGRPN_SUPP ) and 
            ( not ( cTMemn == RR_TMEMN_SUPP )  )):
            # warn that not supported
            warnMsg = "Only flow group member %s is supported for " \
                        "target type %s and group %s. Mass Link %d has %s " \
                        "for member type. Member type set to %s!!!" % \
                        ( RR_TMEMN_SUPP, TARG_RCHRES, RR_TGRPN_SUPP, intInd, 
                        cTMemn, RR_TMEMN_SUPP )
            CL.LOGR.warning( warnMsg )
            #print("%s" % warnMsg)
            cTMemn = RR_TMEMN_SUPP
        if ( addLink and ( cSVol == TARG_PERVLND ) and 
                ( not ( cSMemn == "PERO" ) ) ):
            warnMsg = "Only outflow group member PERO is supported for " \
                      "source type %s.\nCurrent outflow is specified as %s." \
                      "\nMass link %d will be ignored!!!" % \
                      ( TARG_PERVLND, cSMemn, intInd )
            CL.LOGR.warning( warnMsg )
            #print("%s" % warnMsg )
            addLink = False
        if ( addLink and ( cSVol == TARG_IMPLND ) and 
                ( not ( cSMemn == "SURO" ) ) ):
            warnMsg = "Only outflow group member SURO is supported for " \
                      "source type %s.\nCurrent outflow is specified as %s." \
                      "\nMass link %d will be ignored!!!" % \
                      ( TARG_IMPLND, cSMemn, intInd )
            CL.LOGR.warning( warnMsg )
            #print("%s" % warnMsg )
            addLink = False
        # if did not make it through the checks then continue
        if not addLink:
            continue
        # done with checks so need to do some additional processing
        try:
            cFFactor = float( cMFactor )
        except:
            errMsg = "Could not convert string factor %s to float!!!" % \
                        cMFactor 
            CL.LOGR.error( errMsg )
            return badReturn
        # finally try to parse the exits and categories
        if cSMemsb:
            exitList = list()
            if len( cSMemsb ) > 0:
                strLister = cSMemsb.split(" ")
                for sL in strLister:
                    try:
                        intSL = int( sL )
                    except:
                        # this is an error
                        errMsg = "Could not convert exit and/or " \
                                    "category string %s to integers!!!" % \
                                    cSMemsb
                        CL.LOGR.error( errMsg )
                        return badReturn
                    # if made it here then add to our list
                    exitList.append( intSL )
                # end for exit and category
            # end if
        else:
            exitList = [ 1 ]
        # end if
        # add our values to our custom list
        massLinkD[intInd] = [ cTVol, cTGrpn, cTMemn, cFFactor, cSVol, 
                              cSGrpn, cSMemn, exitList ]
    # end for mldd
    # currently only supported destination is RCHRES. 
    # check the link dictionary
    lKeyList = list( linkdd.keys() )
    targTList = [ x[0] for x in lKeyList ]
    uniqueLinkTargs = set( targTList )
    if len( uniqueLinkTargs ) > 1:
        warnMsg = "Only %s targets are supported for schematic links.\n" \
                  "The target types of %s are specified. Non %s targets" \
                  " will be ignored!!!" % \
                  ( TARG_RCHRES, str(uniqueLinkTargs), TARG_RCHRES )
        CL.LOGR.warning( warnMsg )
        #print("%s" % warnMsg)
    if not ( TARG_RCHRES in uniqueLinkTargs ):
        warnMsg = "No %s targets are specified for schematic links.\n" \
                  "%s targets are specified and will be ignored!!!" % \
                  ( TARG_RCHRES, str( uniqueLinkTargs ) )
        CL.LOGR.warning( warnMsg )
        #print("%s" % warnMsg)
    # Now go through the link dictionary and call the appropriate method to
    # set up the linkage structures
    mlKeyList = list( massLinkD.keys() )
    allRRs = TARG_DICT[ TARG_RCHRES ]
    for tID in allRRs:
        if not ( TARG_RCHRES, tID ) in lKeyList:
            continue
        # now process
        cSchemeLink = linkdd[ ( TARG_RCHRES, tID ) ]
        # this is a list of Pandas series objects
        for tLink in cSchemeLink:
            # first get the mass link iD and the source vol
            try:
                if hdfType == 0:
                    mlID = int( tLink["MLNO"] )
                else:
                    mlID = int( tLink["MLNO"].strip('ML') )
                # end if
                sVolType = str( tLink["SVOL"] )
                sVolID = str( tLink["SVOLNO"] )
                aFactor = float( tLink["AFACTR"] )
            except:
                # this is an unrecoverable error
                errMsg = "Issue extracting mass link id from schematic " \
                         "link %s!!!" % str( tLink )
                CL.LOGR.error( errMsg )
                return badReturn
            # now check the mass link id
            if not mlID in mlKeyList:
                # this is an error
                errMsg = "Mass Link %d was not in Mass Link dictionary!!!" \
                         % mlID
                CL.LOGR.error( errMsg )
                return badReturn 
            # now send our schematic and mass link information
            cMasslink = massLinkD[ mlID ]
            retStat = RR.addInflowMap( tID, sVolType, sVolID, aFactor, 
                                       cMasslink )
            if retStat != 0:
                # error
                errMsg = "Could not set mass link %d between source %s " \
                         "and target %s!!!!" % ( mlID, sVolID, tID )
                CL.LOGR.error( errMsg )
                return badReturn
            # end if check
        # end for schematic link
    # end for target ID
    # return 
    return goodReturn


def salocaMain(simdir, hdfname, saveall=False, reloadkeys=False):
    """Runs main HSP2 program in standalone mode.

    Rewrite of original to make one main time loop

    Args:
        simdir (str): verified model simulaton directory
        hdfname (str): HDF5 filename used for both input and output.
        saveall (bool): Saves all calculated data ignoring SAVE tables.
        reloadkeys (bool): Regenerates keys, used after adding new modules.
    
    Returns:
        int: function status, 0 == success

    """
    # imports
    from locaHSP2HDF5 import DFCOL_OPSEQ_TARG, DFCOL_OPSEQ_ID
    from locaHSP2HDF5 import initialHDFRead, getALLOPS, getUCS
    from locaHSP2HDF5 import getGENERAL, setGTSDict, setGFTabDict
    from locaHSP2HDF5 import getLINKDD, getMLDD, getnUCI, getHDFFormat
    # globals
    global SIMTIME_INDEXES, DAILY_DELT_STR, SUPPORTED_ACTIVITIES
    global TARG_PERVLND, TARG_IMPLND, TARG_RCHRES, KEY_ACT_PWAT
    global KEY_ACT_IWAT, KEY_ACT_RRHYD, GFTAB_DICT, GTS_DICT
    global MAP_TS_DICT, SEQUENCE_DICT
    # parameters
    goodReturn = 0
    badReturn = -1
    # locals - explicit here in case go to Cython for this routine
    sim_len = 0     # number of time steps
    sim_delt = 0.0  # time step length
    num_ops = 0      # number of operations for each time step
    # start out by opening the log file
    CL.loggerStart( simdir )
    # Rather than keeping the HDF5 file accessible for the entire run,
    #   read the inputs and do setup and then start the time loop.
    retStat = initialHDFRead( hdfname, reloadkeys )
    if retStat != 0:
        # this is an error
        errMsg = "Issue reading inputs from %s !!!" % hdfname
        CL.LOGR.error( errMsg )
        CL.loggerEnd()
        return badReturn
    # check our operations sequences and activities to make sure that are
    # supported
    allops = getALLOPS()
    hdfTyper = getHDFFormat()
    # check here that hdfTyper is 0 or 1. Other values are not supported
    if hdfTyper == 0:
        ucs = getUCS()
    elif hdfTyper == 1:
        ucs = getnUCI()
    else:
        # this is an error
        errMsg = "hdfTyper tells the version of the HDF5 file used in " \
                 "this simulation. Only 0 and 1 are supported values." \
                 " Found a value of %s!!!" % hdfTyper
        CL.LOGR.error( errMsg )
        CL.loggerEnd()
        return badReturn
    # end if
    retStat = checkOpsSpec( allops, ucs, hdfTyper )
    if retStat != 0:
        # this is an error
        errMsg = "Too many unsupported activities are specified !!!"
        CL.LOGR.error( errMsg )
        CL.loggerEnd()
        return badReturn
    # now set up our time index for this simulation
    general = getGENERAL( )
    retStat = setSimTimeIndexes( allops, general, hdfTyper )
    if retStat != 0:
        # this is an error
        errMsg = "Issue setting up simulation time index !!!"
        CL.LOGR.error( errMsg )
        CL.loggerEnd()
        return badReturn
    # now get our number of time steps
    sim_len = len( SIMTIME_INDEXES[ DAILY_DELT_STR ] )
    sim_delt = float( DAILY_DELT_STR )
    # now extract all of our time series to a dictionary.
    retStat = setGTSDict( hdfname, SIMTIME_INDEXES, MAP_TS_DICT,  
                          GTS_DICT )
    if retStat != 0:
        # this is an error
        errMsg = "Issue setting time series and ts mapping !!!"
        CL.LOGR.error( errMsg )
        CL.loggerEnd()
        return badReturn
    # get our FTABLE structures
    retStat = setGFTabDict( hdfname, TARG_DICT, GFTAB_DICT )
    if retStat != 0:
        # this is an error
        errMsg = "Error extracting FTABLES !!!"
        CL.LOGR.error( errMsg )
        CL.loggerEnd()
        return badReturn
    # allocate and initialize all of our target structures
    retStat = initAllocTargStructures( sim_len )
    if retStat != 0:
        # this is an error
        errMsg = "Error allocating target structures !!!"
        CL.LOGR.error( errMsg )
        CL.loggerEnd()
        return badReturn
    # set the flags and parameters to the target structures
    retStat = setParmsFlagsUCS( sim_delt, ucs, hdfTyper )
    if retStat != 0:
        # this is an error
        errMsg = "Issue setting parameters and flags !!!"
        CL.LOGR.error( errMsg )
        CL.loggerEnd()
        return badReturn
    # push the time series to the target calculation structures
    retStat = setTargDataTS( sim_len )
    if retStat != 0:
        # this is an error
        errMsg = "Issue putting time series to targets !!!"
        CL.LOGR.error( errMsg )
        CL.loggerEnd()
        return badReturn
    # create the routing link structures
    linkdd = getLINKDD()
    mldd = getMLDD()
    retStat = setFlowLinks( linkdd, mldd, hdfTyper )
    if retStat != 0:
        # this is an error
        errMsg = "Error setting internal routing !!!"
        CL.LOGR.error( errMsg )
        CL.loggerEnd()
        return badReturn
    # set up the output flags
    retStat = setOutputSave( ucs, hdfTyper )
    if retStat != 0:
        # this is an error
        errMsg = "Error setting output flags !!!"
        CL.LOGR.error( errMsg )
        CL.loggerEnd()
        return badReturn
    else:
        infoMsg = "Finished setup"
        CL.LOGR.info( infoMsg )
    # now are ready for the main time loop
    num_ops = len( allops )
    # get our tIndex
    tIndex = SIMTIME_INDEXES[ DAILY_DELT_STR ]
    # main time loop
    for iI in range( sim_len ):
        # debugging outputs
        if iI == 0:
            print("LOCA HSPF Start")
        elif iI % 365 == 0:
            print("Sim time: %s" % tIndex[iI].strftime( "%Y-%m-%d" ) )
        # get the current month
        cMonth = tIndex[iI].month
        # within each time step need to go through all of the activities or
        #   operations in order from upstream to downstream.
        for jJ in range( num_ops ):
            cTarg = allops[ DFCOL_OPSEQ_TARG ][jJ]
            cID = allops[ DFCOL_OPSEQ_ID ][jJ]
            if hdfTyper == 0:
                cActivity = ucs[ cTarg, "ACTIVITY", cID ]
            else:
                cActivity = ucs[(cTarg, 'GENERAL', cID)]['ACTIVITY']
            # end if
            for seq in SEQUENCE_DICT[cTarg]:
                if len( seq[1] ) > 1:
                    cFlag = seq[1][ hdfTyper ]
                else:
                    cFlag = seq[1]
                # end if
                if not ( ( cFlag in SUPPORTED_ACTIVITIES[cTarg][hdfTyper] ) and
                        ( cActivity[ cFlag ] == 1 ) ):
                    # if this is not true then nothing to do
                    continue
                # end if
                if ( ( cTarg == TARG_PERVLND ) and 
                        ( cFlag in [ KEY_ACT_PWAT, nKEY_ACT_PWAT ] ) ):
                    # then call the appropriate function
                    retStat = PLD.pwater_liftedloop( iI, cMonth, cID )
                elif ( ( cTarg == TARG_IMPLND ) and 
                        ( cFlag in [ KEY_ACT_IWAT, nKEY_ACT_IWAT ] ) ):
                    # call appropriate function
                    retStat = IMP.iwater_liftedloop( iI, cMonth, cID )
                elif ( ( cTarg == TARG_RCHRES ) and 
                        ( cFlag in [ KEY_ACT_RRHYD, nKEY_ACT_RRHYD ] ) ):
                     # call appropriate function
                    retStat = RR.hydr_liftedloop( iI, cID, GFTAB_DICT )
                else:
                    # an error but warn of unsupported
                    warnMsg = "Target type %s and activity %s are unknown " \
                              "and unsupported!!!" % ( cTarg, cFlag )
                    CL.LOGR.warning( warnMsg )
                    continue
                # end if
                # check our retStat
                if retStat != 0:
                    warnMsg = "Issue in %s, %s that written to errorsV.\n" \
                              "Need to add additional error handling " \
                              "functionality." % ( cTarg, cID )
                    CL.LOGR.warning( warnMsg )
            # end sequence for
        # end operation for
    # end time step for
    # now are ready to write out our outputs
    retStat = writeOutputs( hdfname, tIndex, hdfTyper, False )
    if retStat != 0:
        # some sort of error
        errMsg = "Issue writing outputs!!!"
        CL.LOGR.error( errMsg )
        CL.loggerEnd()
        return badReturn
    # end check if
    # close the logger
    CL.loggerEnd()
    # run is done so return
    return goodReturn


def mainTL( sim_len, tIndex, qHSP2, qMF6, hdfTyper ):
    """The main time loop for mHSP2 in the coupled program.

    Currently only 1440.0 minutes, or daily, is supported for 
    sim_delt or a daily time step.

    Args:
        sim_len (int): number of daily time steps in the simulation
        tIndex (pd.datetimeseries): daily time index for simulation
        qHSP2 (Queue client): from HSP2 queue
        qMF6 (Queue client): from MODFLOW 6 queue
        hdfTyper (int): type of HDF5 file; 0 == original format;0 
                        1 == new format
    
    Returns:
        int: function status, 0 == success

    """
    # imports
    from locaHSP2HDF5 import DFCOL_OPSEQ_TARG, DFCOL_OPSEQ_ID
    from locaHSP2HDF5 import getALLOPS, getUCS, getnUCI
    from locaCoupling import calcSendArray, getNUM_UZF
    # globals
    global SUPPORTED_ACTIVITIES, TARG_PERVLND, TARG_IMPLND, TARG_RCHRES
    global KEY_ACT_PWAT, KEY_ACT_IWAT, KEY_ACT_RRHYD, GFTAB_DICT
    global SEQUENCE_DICT, nKEY_ACT_PWAT, nKEY_ACT_IWAT, nKEY_ACT_RRHYD
    # parameters
    goodReturn = 0
    badReturn = -1
    # get the items that need for main time loop
    allops = getALLOPS()
    num_ops = len( allops )
    if hdfTyper == 0:
        ucs = getUCS()
    else:
        ucs = getnUCI()
    # main time loop
    for iI in range( sim_len ):
        # wait for MODFLOW 6 unless is the first time step
        if iI > 0:
            try:
                RecArray = qMF6.get( True, QUEUE_TIMEOUT )
            except Empty:
                # Timeout
                errMsg = "MF6 queue timeout at day %d. Timeout period %g " \
                         "seconds.\n" % ( iI, QUEUE_TIMEOUT )
                CL.LOGR.error( errMsg )
                qHSP2.put( QUEUE_ERROR )
                return badReturn
            except:
                ErrTuple = sys.exc_info()
                errMsg = "Exception thrown getting message from MODFLOW " \
                         "6 queue.\nMessage: Type - %s ; Value - %s \n" \
                         "Traceback - %s \n\n" % \
                         ( ErrTuple[0], ErrTuple[1], ErrTuple[2] )
                CL.LOGR.error( errMsg )
                qHSP2.put( QUEUE_ERROR )
                return badReturn
            # end try block
            # parse the received array
            retStat = processArrayComm( iI, RecArray )
            if retStat != 0:
                qHSP2.put( QUEUE_ERROR )
                return badReturn
            # end inner if
        # end if
        # get the current month
        cMonth = tIndex[iI].month
        # within each time step need to go through all of the activities or
        #   operations in order from upstream to downstream.
        for jJ in range( num_ops ):
            cTarg = allops[ DFCOL_OPSEQ_TARG ][jJ]
            cID = allops[ DFCOL_OPSEQ_ID ][jJ]
            if hdfTyper == 0:
                cActivity = ucs[ cTarg, "ACTIVITY", cID ]
            else:
                cActivity = ucs[(cTarg, 'GENERAL', cID)]['ACTIVITY']
            # end if
            for seq in SEQUENCE_DICT[cTarg]:
                if len( seq[1] ) > 1:
                    cFlag = seq[1][ hdfTyper ]
                else:
                    cFlag = seq[1]
                # end if
                if not ( ( cFlag in SUPPORTED_ACTIVITIES[cTarg][hdfTyper] ) and
                        ( cActivity[ cFlag ] == 1 ) ):
                    # if this is not true then nothing to do
                    continue
                # end if
                if ( ( cTarg == TARG_PERVLND ) and 
                            ( cFlag in [ KEY_ACT_PWAT, nKEY_ACT_PWAT ] ) ):
                    # then call the appropriate function
                    retStat = PLD.pwater_liftedloop( iI, cMonth, cID )
                elif ( ( cTarg == TARG_IMPLND ) and 
                            ( cFlag in [ KEY_ACT_IWAT, nKEY_ACT_IWAT ] ) ):
                    # call appropriate function
                    retStat = IMP.iwater_liftedloop( iI, cMonth, cID )
                elif ( ( cTarg == TARG_RCHRES ) and 
                            ( cFlag in [ KEY_ACT_RRHYD, nKEY_ACT_RRHYD ] ) ):
                     # call appropriate function
                    retStat = RR.hydr_liftedloop( iI, cID, GFTAB_DICT )
                else:
                    # an error but warn of unsupported
                    warnMsg = "Target type %s and activity %s are unknown " \
                              "and unsupported!!!" % ( cTarg, cFlag )
                    CL.LOGR.warning( warnMsg )
                    continue
                # end if
                # check our retStat
                if retStat != 0:
                    warnMsg = "Issue in %s, %s that written to errorsV " \
                              "and HSP2 simulaton log." % ( cTarg, cID )
                    CL.LOGR.warning( warnMsg )
            # end sequence for
        # end operation for
        # now are ready to send our information to MODFLOW. Get our array
        passNPArray = calcSendArray( iI )
        # put the array
        qHSP2.put( passNPArray )
    # end time step for
    # run is done so return
    return goodReturn


def setUPPreTL(hdfname, saveall=False, reloadkeys=False):
    """Does all of the main mHSP2 setup for a coupled simulation.
    
    Called prior to starting the main, time, loop.

    Args:
        hdfname (str): HDF5 filename used for both input and output.
        saveall (bool): Saves all calculated data ignoring SAVE tables.
        reloadkeys (bool): Regenerates keys, used after adding new modules.
    
    Returns:
        int: function status; also needs to be one of the *hdfTyper* 
             supported values, [0,1]; successful execution of this 
             function means that either 0 or 1 is returned.

    """
    # imports
    from locaHSP2HDF5 import initialHDFRead, getALLOPS, getUCS
    from locaHSP2HDF5 import getGENERAL, setGTSDict, setGFTabDict
    from locaHSP2HDF5 import getLINKDD, getMLDD, getUNITS, getnUCI
    from locaHSP2HDF5 import getHDFFormat
    # globals
    global SIMTIME_INDEXES, DAILY_DELT_STR, GFTAB_DICT, GTS_DICT
    global MAP_TS_DICT
    # parameters
    #goodReturn = 0
    badReturn = -1
    # Rather than keeping the HDF5 file accessible for the entire run,
    #   read the inputs and do setup and then start the time loop.
    retStat = initialHDFRead( hdfname, reloadkeys )
    if retStat != 0:
        # this is an error
        errMsg = "Issue reading inputs from %s !!!" % hdfname
        CL.LOGR.error( errMsg )
        return badReturn
    # check our operations sequences and activities to make sure that are
    # supported
    allops = getALLOPS()
    # get the HDF5 file format, check this value, and use it to get the
    #   correct UCS structure
    hdfTyper = getHDFFormat()
    # check here that hdfTyper is 0 or 1. Other values are not supported
    if hdfTyper == 0:
        ucs = getUCS()
    elif hdfTyper == 1:
        ucs = getnUCI()
    else:
        # this is an error
        errMsg = "hdfTyper tells the version of the HDF5 file used in " \
                 "this simulation. Only 0 and 1 are supported values." \
                 " Found a value of %s!!!" % hdfTyper
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    retStat = checkOpsSpec( allops, ucs, hdfTyper )
    if retStat != 0:
        # this is an error
        errMsg = "Too many unsupported activities are specified !!!"
        CL.LOGR.error( errMsg )
        return badReturn
    # now set up our time index for this simulation
    general = getGENERAL( )
    # get and check our units
    unitsInt = getUNITS()
    if unitsInt != 1:
        errMsg = "Only standard units are supported in this version " \
                   "of HSPF. Units are currently specified as %d.\n" \
                   "1 denotes standard units and 2 denotes metric." % \
                   unitsInt
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    retStat = setSimTimeIndexes( allops, general, hdfTyper )
    if retStat != 0:
        # this is an error
        errMsg = "Issue setting up simulation time index !!!"
        CL.LOGR.error( errMsg )
        return badReturn
    # now get our number of time steps
    tIndex = getDailySimTimeIndex()
    sim_len = len( tIndex )
    sim_delt = float( DAILY_DELT_STR )
    # now extract all of our time series to a dictionary.
    retStat = setGTSDict( hdfname, SIMTIME_INDEXES, MAP_TS_DICT,  
                          GTS_DICT )
    if retStat != 0:
        # this is an error
        errMsg = "Issue setting time series and ts mapping !!!"
        CL.LOGR.error( errMsg )
        return badReturn
    # get our FTABLE structures
    retStat = setGFTabDict( hdfname, TARG_DICT, GFTAB_DICT )
    if retStat != 0:
        # this is an error
        errMsg = "Error extracting FTABLES !!!"
        CL.LOGR.error( errMsg )
        return badReturn
    # allocate and initialize all of our target structures
    retStat = initAllocTargStructures( sim_len )
    if retStat != 0:
        # this is an error
        errMsg = "Error allocating target structures !!!"
        CL.LOGR.error( errMsg )
        return badReturn
    # set the flags and parameters to the target structures
    retStat = setParmsFlagsUCS( sim_delt, ucs, hdfTyper )
    if retStat != 0:
        # this is an error
        errMsg = "Issue setting parameters and flags !!!"
        CL.LOGR.error( errMsg )
        return badReturn
    # push the time series to the target calculation structures
    retStat = setTargDataTS( sim_len )
    if retStat != 0:
        # this is an error
        errMsg = "Issue putting time series to targets !!!"
        CL.LOGR.error( errMsg )
        return badReturn
    # create the routing link structures
    linkdd = getLINKDD()
    # set our WS areas
    retStat = setHRUAreas( linkdd )
    if retStat != 0:
        # this is an error
        errMsg = "Error setting watershed areas !!!"
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    mldd = getMLDD()
    retStat = setFlowLinks( linkdd, mldd, hdfTyper )
    if retStat != 0:
        # this is an error
        errMsg = "Error setting internal routing !!!"
        CL.LOGR.error( errMsg )
        return badReturn
    # set up the output flags
    retStat = setOutputSave( ucs, hdfTyper )
    if retStat != 0:
        # this is an error
        errMsg = "Error setting output flags !!!"
        CL.LOGR.error( errMsg )
        return badReturn
    else:
        infoMsg = "Finished setup in setUPPreTL"
        CL.LOGR.info( infoMsg )
    # return
    return hdfTyper


def metaChecks( start_dt, end_dt, num_pl, num_il, num_rr ):
    """Check the remaining meta data items passed from the queue
    server as part of initial setup of a coupled simulation.

    Requires that the input HDF5 file has already been read 
    and processed into program structures.

    Args:
        start_dt (dt.datetime): starting date time
        end_dt (dt.datetime): ending date time
        num_pl (int): number of PERLND
        num_il (int): number of IMPLND
        num_rr (int): number of RCHRES

    Returns:
        int: function status; 0 == success

    """
    # imports
    # globals
    global TARG_DICT, TARG_PERVLND, TARG_IMPLND, TARG_RCHRES
    # parameters
    goodReturn = 0
    badReturn = -1
    # locals
    # start
    tIndex = getDailySimTimeIndex()
    aStart = tIndex[0].to_pydatetime()
    aEnd = tIndex[ ( len(tIndex) - 1) ].to_pydatetime()
    if aStart != start_dt:
        errMsg = "Expected HSP2 sim start is %s and HDF5 start is %s\n" \
                 % ( start_dt.strftime("%Y-%m-%d"), 
                     aStart.strftime("%Y-%m-%d") )
        CL.LOGR.error( errMsg )
        return badReturn
    if aEnd != end_dt:
        errMsg = "Expected HSP2 sim end is %s and HDF5 end is %s\n" \
                 % ( end_dt.strftime("%Y-%m-%d"), 
                     aEnd.strftime("%Y-%m-%d") )
        CL.LOGR.error( errMsg )
        return badReturn
    aNumPL = len( TARG_DICT[TARG_PERVLND] )
    aNumIL = len( TARG_DICT[TARG_IMPLND] )
    aNumRR = len( TARG_DICT[TARG_RCHRES] )
    if ( ( aNumPL != num_pl ) or ( aNumIL != num_il ) or 
                ( aNumRR != num_rr ) ):
        errMsg = "Missmatch in number of HSP2 structures by type!!!\n" \
                 "Expected %d %s; %d %s; %d %s \n" \
                 "Instead found, %d %s; %d %s; %d %s \n" % \
                 ( num_pl, TARG_PERVLND, num_il, TARG_IMPLND, num_rr, 
                   TARG_RCHRES, aNumPL, TARG_PERVLND, aNumIL, TARG_IMPLND,
                   aNumRR, TARG_RCHRES )
        CL.LOGR.error( errMsg )
        return badReturn
    # return
    return goodReturn


def getTARG_DICT():
    """Get the global target dictionary.

    Returns:
        dict: TARG_DICT
    
    """
    global TARG_DICT
    return TARG_DICT


#----------------------------------------------------------------------
# queue processing methods
def processInitMeta( PassList ):
    """Process the initial metadata communication received from the
    queue server.
    
    Call the various routines as required to read in all of the HDF5 
    information as required to completely set up the model and check 
    start time, end time, number of pervious, number of impervious, 
    and number of reach res

    Args:
        PassList (list): list, L, of items - these are pickled and 
        unpickled and following formats are required.

            0. (str): model directory
            1. (str): FQDN pathname for HDF5 input file
            2. (dt.datetime): start time
            3. (dt.datetime): end time
            4. (int): number of PERLND
            5. (int): number of IMPLND
            6. (int): number of RCHRES
            7. (int): number of 2D cells, NCPL in MF6
            8. (str): FQDN pathname for RCHRES mapping dictionary
            9. (str): FQDN pathname for PERLND mapping dictionary
            10. (int): number of UZF cells in MF6
            11. (str): FQDN pathname for SPRING mapping dictionary

    Returns:
        tuple: two items that provide the necessary information for 
        continuing the simulation.

            0. (int): return status; needs to be a member of *hdfTyper* - 
            0 or 1 for a success status

            1. (str): hdfname - FQDN path for simulation HDF5 file. Empty
            string for error.

    """
    # imports
    from locaCoupling import mapSetup
    # globals
    global QUEUE_ERROR, TARG_DICT
    # parameters
    PASS_LEN = 12
    emptyStr = ""
    badReturn = -1
    # use try block and check transmission for basic errors
    try:
        ErrorOccurred = ( PassList == QUEUE_ERROR )
        TooSmall = ( len ( PassList ) < 1 )
    except:
        # catchall exception
        ErrTuple = sys.exc_info()
        errMsg = "Unknown exception in processInitMeta checking of %s" \
                  ".\nType - %s ; Value - %s\nTraceback - %s \n\n" % \
                  ( PassList, ErrTuple[0], ErrTuple[1], ErrTuple[2] )
        with open( "HSP2_QueueInit_Errors.txt", 'w' ) as LogFID:
            LogFID.write("%s" % errMsg )
        # end with block and close file
        return ( badReturn, emptyStr )
    # end try
    if ErrorOccurred or TooSmall:
        # these are also errors
        errMsg = "Either an error occurred in the intitial starutp, %s, " \
                 "or passed list length does not conform with " \
                 "expectations, %s.\n\n" % ( ErrorOccurred, TooSmall )
        with open( "HSP2_QueueInit_Errors.txt", 'w' ) as LogFID:
            LogFID.write("%s" % errMsg )
        # end with block and close file
        return ( badReturn, emptyStr )
    # end if
    # now process our values
    if len( PassList ) != PASS_LEN:
        # this is an error
        errMsg = "Expected a list with %d items in processInitMeta and " \
                 "received a list with %d items.\n" % \
                 ( PASS_LEN, len( PassList ) )
        with open( "HSP2_QueueInit_Errors.txt", 'w' ) as LogFID:
            LogFID.write("%s" % errMsg )
        # end with block and close file
        return ( badReturn, emptyStr )
    # now get our values
    cwd = PassList[0]
    hdfname = PassList[1]
    start_dt = PassList[2]
    end_dt = PassList[3]
    num_pl = PassList[4]
    num_il = PassList[5]
    num_rr = PassList[6]
    num_cpl = PassList[7]
    rr_map_file = PassList[8]
    pl_map_file = PassList[9]
    num_iuzf = PassList[10]
    sp_map_file = PassList[11]
    # now set up our log file
    CL.loggerStart( cwd )
    # now check our values. First check hdfname
    if not os.path.isfile( hdfname ):
        errMsg = "HDF5 file, %s, not found --- EXIT!!! " % hdfname
        CL.LOGR.error( errMsg )
        return ( badReturn, emptyStr )
    # now call the pre time loop setup
    hdfTyper = setUPPreTL( hdfname )
    if hdfTyper < 0:
        errMsg = "Issue in HSP2 setup!!!\n"
        CL.LOGR.error( errMsg )
        return ( badReturn, emptyStr )
    # end if
    # do our remaining checks
    if not type( start_dt ) == dt.datetime:
        # an error
        errMsg = "Expected type %s for start_dt and received %s!!!\n" % \
                 ( type( dt.datetime.now() ), str( start_dt ) )
        CL.LOGR.error( errMsg )
        return ( badReturn, emptyStr )
    if not type( end_dt ) == dt.datetime:
        # an error
        errMsg = "Expected type %s for end_dt and received %s!!!\n" % \
                 ( type( dt.datetime.now() ), str( end_dt ) )
        CL.LOGR.error( errMsg )
        return ( badReturn, emptyStr )
    if not type( num_pl ) == int:
        # an error
        errMsg = "Expected type %s for num_pl and received %s!!!\n" % \
                 ( type( 1 ), str( num_pl ) )
        CL.LOGR.error( errMsg )
        return ( badReturn, emptyStr )
    if not type( num_il ) == int:
        # an error
        errMsg = "Expected type %s for num_il and received %s!!!\n" % \
                 ( type( 1 ), str( num_il ) )
        CL.LOGR.error( errMsg )
        return ( badReturn, emptyStr )
    if not type( num_rr ) == int:
        # an error
        errMsg = "Expected type %s for num_rr and received %s!!!\n" % \
                 ( type( 1 ), str( num_rr ) )
        CL.LOGR.error( errMsg )
        return ( badReturn, emptyStr )
    if not type( num_cpl ) == int:
        # an error
        errMsg = "Expected type %s for num_cpl and received %s!!!\n" % \
                 ( type( 1 ), str( num_cpl ) )
        CL.LOGR.error( errMsg )
        return ( badReturn, emptyStr )
    if not type( num_iuzf ) == int:
        # an error
        errMsg = "Expected type %s for num_iuzf and received %s!!!\n" % \
                 ( type( 1 ), str( num_iuzf ) )
        CL.LOGR.error( errMsg )
        return ( badReturn, emptyStr )
    if not os.path.isfile( rr_map_file ):
        errMsg = "Input RCHRES mapping file %s was not found !!! " % \
                 rr_map_file
        CL.LOGR.error( errMsg )
        return ( badReturn, emptyStr )
    if not os.path.isfile( pl_map_file ):
        errMsg = "Input PERLND mapping file %s was not found !!! " % \
                 pl_map_file
        CL.LOGR.error( errMsg )
        return ( badReturn, emptyStr )
    if not os.path.isfile( sp_map_file ):
        errMsg = "Input SPRING mapping file %s was not found !!! " % \
                 sp_map_file
        CL.LOGR.error( errMsg )
        return ( badReturn, emptyStr )
    # now check the values
    retStat = metaChecks( start_dt, end_dt, num_pl, num_il, num_rr )
    if retStat != 0:
        # then an error
        errMsg = "HSP2 metadata value disagreement in processInitMeta\n"
        CL.LOGR.error( errMsg )
        return ( badReturn, emptyStr )
    # check and assign mapping dictionary values
    retStat = mapSetup( TARG_DICT, num_cpl, num_iuzf, rr_map_file, 
                        pl_map_file, sp_map_file )
    if retStat != 0:
        # then an error
        errMsg = "HSP2 mapping file setup issue in processInitMeta\n"
        CL.LOGR.error( errMsg )
        return ( badReturn, emptyStr )
    # now return
    return ( hdfTyper, hdfname )


def processReadyComm( StringList ):
    """Process the ready communication with external processes.

    Args:
        StringList (list): list of string items

    Returns:
        int: function status; success == 0

    """
    # imports
    # globals
    global QUEUE_ERROR, QREADY_MSG
    # parameters
    goodReturn = 0
    badReturn = -1
    # use try block and check transmission for basic errors
    try:
        GoodValue = ( StringList == QREADY_MSG )
        ErrorOccurred = ( StringList == QUEUE_ERROR )
        TooSmall = ( len ( StringList ) < 1 )
    except:
        # catchall exception
        ErrTuple = sys.exc_info()
        errMsg = "Unknown exception in HSP2 processReadyComm checking of %s" \
                  ".\nType - %s ; Value - %s\nTraceback - %s \n\n" % \
                  ( StringList, ErrTuple[0], ErrTuple[1], ErrTuple[2] )
        CL.LOGR.error( errMsg )
        return badReturn
    # end try
    if ErrorOccurred or TooSmall:
        # these are also errors
        errMsg = "Either an error occurred in the HSP2 processReadyComm, %s, " \
                 "or passed list length does not conform with " \
                 "expectations, %s.\n\n" % ( ErrorOccurred, TooSmall )
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    if GoodValue:
        infoMsg = "Successfully received simulation start message " \
                  "queue client.\n"
        CL.LOGR.info( infoMsg )
        return goodReturn
    # end if
    errMsg = "Unknown message of %s received during processReadyComm!!!\n" \
             % str( StringList )
    CL.LOGR.error( errMsg )
    return badReturn


def processArrayComm( iI, NpArray ):
    """Process the array communication from MODFLOW 6.

    Args:
        iI (int): current day, 0-based in the simulation
        NpArray (np.array): the array of discharge to the surface from 
                            MODFLOW 6

    Return:
        int: function status; success == 0

    """
    # imports
    from locaCoupling import getNUM_CPL, processReceivedArray
    # globals
    global QUEUE_ERROR, TARG_DICT
    # parameters
    goodReturn = 0
    badReturn = -1
    # use try block and check transmission for basic errors
    try:
        ErrorOccurred = ( NpArray[0] == QUEUE_ERROR[0] )
        TooSmall = ( len ( NpArray ) < 1 )
    except:
        # catchall exception
        ErrTuple = sys.exc_info()
        errMsg = "Unknown exception in HSP2 processArrayComm checking of " \
                  "passed array.\nType - %s ; Value - %s\nTraceback - " \
                  "%s \n\n" % \
                  ( ErrTuple[0], ErrTuple[1], ErrTuple[2] )
        CL.LOGR.error( errMsg )
        return badReturn
    # end try
    if ErrorOccurred or TooSmall:
        # these are also errors
        errMsg = "Either an error occurred in the HSP2 processArrayComm, %s, " \
                 "or passed array does not conform with " \
                 "expectations, %s.\n\n" % ( ErrorOccurred, TooSmall )
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    if not type( NpArray ) == np.ndarray:
        # this is an error
        errMsg = "Received MODFLOW 6 transmission that was not a " \
                 "numpy array. Passed type %s !!!!\n"
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    # check the length of the array
    NUM_CPL = getNUM_CPL()
    if NpArray.shape[0] != NUM_CPL:
        # this is an error
        errMsg = "Received numpy array from MODFLOW with dim 0 of " \
                 "%d and expected ncpl of %d!!!!" % \
                 ( NpArray.shape[0], NUM_CPL)
        CL.LOGR.error( errMsg )
        return badReturn
    # add call to function here to process the array
    retStat = processReceivedArray( TARG_DICT, iI, NpArray )
    if retStat != 0:
        # then there is an error
        errMsg = "Error processing array received from MODFLOW 6"
        CL.LOGR.error( errMsg )
        return badReturn
    # return
    return goodReturn


#standalone execution block
if __name__ == "__main__":
    # want to set-up TERM queue first. The TERM queue is first
    # used to ensure communication and to pass some important
    # globals to the child processes.
    try:
        # get the client
        qcTERM = QueueServerClient( CLIENTHOST, PORT2, AUTHKEY )
        # use the client to get the queue
        qTERM = qcTERM.get_queue( )
    except:
        # error - no handling is set up yet so need to write to
        # a temporary file
        ErrTuple = sys.exc_info()
        errMsg = "Exception thrown getting global comms queue access.\n" \
                 "Message: Type - %s ; Value - %s \nTraceback - %s " \
                 "\n\n" % ( ErrTuple[0], ErrTuple[1], ErrTuple[2] )
        with open( "HSP2_QueueInit_Errors.txt", 'w' ) as LogFID:
            LogFID.write("%s" % errMsg )
        # end with block and close file
        sys.exit( errMsg )
    # end try qTERM
    # sent the startup message to the message server
    qTERM.put( QINIT_MSG )
    # now need to wait for the response with our meta info
    try:
        PassList = qTERM.get( True, START_QUEUE_TO )
    except Empty:
        # Timeout
        errMsg = "Error handling queue timeout. Timeout period %g " \
                 "seconds." % START_QUEUE_TO
        with open( "HSP2_QueueInit_Errors.txt", 'w' ) as LogFID:
            LogFID.write("%s" % errMsg )
        # end with block and close file
        sys.exit( errMsg )
        qTERM.put( QUEUE_ERROR )
        sys.exit( errMsg )
    except:
        ErrTuple = sys.exc_info()
        errMsg = "Exception thrown getting message from error " \
                 "handling queue.\nMessage: Type - %s ; Value - %s \n" \
                 "Traceback - %s \n\n" % \
                 ( ErrTuple[0], ErrTuple[1], ErrTuple[2] )
        with open( "HSP2_QueueInit_Errors.txt", 'w' ) as LogFID:
            LogFID.write("%s" % errMsg )
        # end with block and close file
        qTERM.put( QUEUE_ERROR )
        sys.exit( errMsg )
    # now process the pass list
    RetTuple = processInitMeta( PassList )
    hdfTyper = RetTuple[0]
    hdfname = RetTuple[1]
    if ( len( hdfname ) < 3 ) or ( hdfTyper < 0 ):
        # this is an error
        errMsg = "Metadata checking failed for HSP2!!!!"
        qTERM.put( QUEUE_ERROR )
        sys.exit( errMsg )
    # end check if
    # now get our other two queues and wait for the ready message
    try:
        # get the clients
        qcHSP2 = QueueServerClient( CLIENTHOST, PORT0, AUTHKEY )
        qcMF6 = QueueServerClient( CLIENTHOST, PORT1, AUTHKEY )
        # use the clients to get the queue
        qHSP2 = qcHSP2.get_queue()
        qMF6 = qcMF6.get_queue()
    except:
        # error 
        ErrTuple = sys.exc_info()
        errMsg = "Exception thrown getting process comm queue access.\n" \
                 "Message: Type - %s ; Value - %s \nTraceback - %s " \
                 "\n\n" % ( ErrTuple[0], ErrTuple[1], ErrTuple[2] )
        CL.LOGR.error( errMsg )
        qTERM.put( QUEUE_ERROR )
        # end with block and close file
        sys.exit( errMsg )
    # end try
    # send the ready message
    qTERM.put( QREADY_MSG )
    # now wait for receipt of ready
    try:
        PassList = qMF6.get( True, START_QUEUE_TO )
    except Empty:
        # Timeout
        errMsg = "MF6 queue timeout. Timeout period %g " \
                 "seconds.\n" % START_QUEUE_TO
        CL.LOGR.error( errMsg )
        qTERM.put( QUEUE_ERROR )
        sys.exit( errMsg )
    except:
        ErrTuple = sys.exc_info()
        errMsg = "Exception thrown getting message from error " \
                 "handling queue.\nMessage: Type - %s ; Value - %s \n" \
                 "Traceback - %s \n\n" % \
                 ( ErrTuple[0], ErrTuple[1], ErrTuple[2] )
        CL.LOGR.error( errMsg )
        qTERM.put( QUEUE_ERROR )
        sys.exit( errMsg )
    # end try
    # process pass list
    retStat = processReadyComm( PassList )
    if retStat != 0:
        # this is an error
        errMsg = "Invalid ready message received by HSP2!!!"
        CL.LOGR.error( errMsg )
        qTERM.put( QUEUE_ERROR )
        sys.exit( errMsg )
    # end if
    # start the main time loop
    tIndex = getDailySimTimeIndex()
    sim_len = len( tIndex )
    sim_delt = float( DAILY_DELT_STR )
    retStat = mainTL( sim_len, tIndex, qHSP2, qMF6, hdfTyper )
    if retStat != 0:
        errMsg = "Error in main time loop!!!"
        CL.LOGR.error( errMsg )
        qHSP2.put( QUEUE_ERROR )
        qTERM.put( QUEUE_ERROR )
        sys.exit( errMsg )
    # write our outputs
    # now are ready to write out our outputs
    retStat = writeOutputs( hdfname, tIndex, hdfTyper, True )
    if retStat != 0:
        # some sort of error
        errMsg = "Issue writing outputs!!!"
        CL.LOGR.error( errMsg )
        qHSP2.put( QUEUE_ERROR )
        qTERM.put( QUEUE_ERROR )
        sys.exit( errMsg )
    # end check if
    # send some sort of close sign
    qTERM.put( QEND_MSG )
    # close this log
    CL.loggerEnd()
    # end


# EOF