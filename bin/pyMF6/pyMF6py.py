""".. module:: pyMF6py.py
   :platform: Windows, Linux
   :synopsis: Module containing Python-wrapped, MODFLOW implementation

.. moduleauthor:: Nick Martin <nmartin@swri.org>

This module provides the main entry point for running MODFLOW 6 and the
main time loop through Python.

"""
import os
import sys
OUR_MODULE_PATH = os.path.abspath( __file__ )
"""Current module path"""
OUR_PACKAGE_PATH = os.path.abspath( os.path.join( OUR_MODULE_PATH, '..' ) )
"""Current package path"""
PATH_LIST = sys.path
"""All environment paths"""
if ( not OUR_PACKAGE_PATH in PATH_LIST ):
    sys.path.append( OUR_PACKAGE_PATH )
from multiprocessing import Queue
from multiprocessing.managers import SyncManager
from queue import Empty
import datetime as dt
import numpy as np
# custom package imports 
import pyMF6Logger as CL


# ---------------------------------------------------------------------
# module - wide parameters
MF_SIM_NAME = "mfsim.nam"
"""Standard and fixed MODFLOW 6 simulation name"""
NUM_LAY = 0
"""Number of layers in the MODFLOW 6 model """
NUM_CPL = 0
"""Number of cells per layer in the MODFLOW 6 model """
NUM_UZF = 0
"""Number of UZF cells in the MODFLOW 6 model """
SIM_DAYS = 0
"""Total number of days to be simulated"""
SIM_MONTHS = 0
"""Total number of months to be simulated"""
SIM_DAYS_SERIES = None
"""Pandas date range series of days in date form to be simulated"""
SIM_MONTH_SERIES = None
"""Pandas date range series of months in date form to be simulated"""
TRACK_UZF_IN = None
"""Recarray with dimensions NUM_UZF, SIM_MONTHS for tracking the UZF
inflows passed from HSPF"""
TRACK_DIS_OUT = None
"""Recarray with dimension NUM_CPL, SIM_MONTHS for tracking the 
discharge to ground surface sent to HSPF
"""
TRACK_REJI_OUT = None
"""Recarray with dimension NUM_CPL, SIM_MONTHS for tracking the 
rejected infiltration sent to HSPF
"""
# ---------------------------------------------------------------------
# Queue definition and management items
HOST = 'localhost'
"""Localhost means that the process are set-up to be on all the same 
machine. The queue server and the clients are in different processes
on the same 'machine' """
CLIENTHOST = '127.0.0.1'
"""Clients are on the same 'machine' as the queue server
"""
PORT0 = 45492
"""Port number for the HSP2 queue.  Port numbers for queues
need to be the same for each independent process for connection"""
PORT1 = 45493
"""Port number for the MODFLOW 6 queue. Port numbers for queues
need to be the same for each independent process for connection"""
PORT2 = 45494
"""Port number for global error handling and communications queue"""
AUTHKEY = "authkey".encode()
"""The authorization key for connecting to a queue. This can 
be changed, on the queue server and on each process. It is 
not intended at this point to provide a minimal layer of
security but can be customized for that purpose."""
QUEUE_TIMEOUT = ( 60.0 * 2.0 )
"""Queue wait timeout before error in seconds """
QUEUE_ERROR = [ "Error" ]
"""Error message to put on queues for program termination """
QINIT_MSG = [ "Hello" ]
"""Queue intialization and checkin message"""
START_QUEUE_TO = ( 60.0 * 5.0 )
"""Queue wait timeout before error in seconds. This is for the
startup communications """
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
    """Subclass of multiprocessing.managers.SyncManager. Just sub class
    don't need to add any custom functionality or overloads. The class 
    definition needs to be at the top level of the module so that it is
    pickleable.
    """
    pass


def QueueServerClient(ThisHost, Porter, CustomAuth):
    """Get a client connection to the queue. Can use this connection for
    both get and put.
    
    See:
        https://docs.python.org/2.7/library/multiprocessing.html#using-a-remote-manager
        http://stackoverflow.com/questions/11532654/python-multiprocessing-remotemanager-under-a-multiprocessing-process
        http://stackoverflow.com/questions/25631266/cant-pickle-class-main-jobqueuemanager
        
    Args:
        ThisHost(str): host name. Should be '127.0.0.1' for the same machine
        Porter(int): the port number to listen on
        CustomAuth(str): the custom authorization string
    
    Return:
        manager(QueueManager): the client connection
        
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
        qMF6(Queue): the from MODFLOW6 queue
        
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


#----------------------------------------------------------------------
# MODFLOW 6 functions

def setupRecarrays( ncpl, nuzf, nmonths ):
    """Three recarrays are used to track communications between HSPF and
    MODFLOW on a grid basis. These recarrays are instantiated and 
    initialized here

    Args:
        ncpl (int): number of computational cells in a layer, NCPL
        nuzf (int): number of UZF cells, NUZFCELLS
        nmonths (int): number of months to be simulated

    Returns:
        retStat (int): 0 == success
    """
    # imports
    # globals
    global TRACK_UZF_IN, TRACK_DIS_OUT, TRACK_REJI_OUT 
    # parameters
    goodReturn = 0
    #badReturn = -1
    # locals
    retStat = goodReturn
    # make our dtype
    typeLister = list()
    for iI in range( 1, nmonths + 1 , 1 ):
        typeLister.append( ( '%d' % iI, 'f8') )
    # end for
    # create our type
    DEF_DT = np.dtype( typeLister )
    # now allocate and initialize
    TRACK_UZF_IN = np.rec.array( np.zeros( nuzf, dtype=DEF_DT ) )
    TRACK_DIS_OUT = np.rec.array( np.zeros( ncpl, dtype=DEF_DT ) )
    TRACK_REJI_OUT = np.rec.array( np.zeros( ncpl, dtype=DEF_DT ) )
    # return
    return retStat


def updateUZFRAs( curpTS, rArray ):
    """Update the rec array that tracks inputs from HSPF

    Args:
        curpTS (pd.Timestamp): current simulation time/day
        rArray (np.array, 1D, NUZF): array that passed from HSPF after
                                      checking
    
    Returns:
        retStat (int): 0 == good; currently only 0 returned

    """
    # imports
    # globals
    global TRACK_UZF_IN, SIM_MONTH_SERIES 
    # parameters
    goodReturn = 0
    #badReturn = -1
    # locals
    retStat = goodReturn
    # current current dt.datetime for the beginning of the month
    curDT = dt.datetime( curpTS.year, curpTS.month, 1 )
    curIndex = SIM_MONTH_SERIES.get_loc( curDT )
    # increment from 0-based
    curIndex += 1
    # get the string form
    strIndex = "%d" % curIndex
    # now do our update
    TRACK_UZF_IN[:][ strIndex ] += rArray
    # return
    return retStat


def updateDischargeRAs( curpTS, tArray ):
    """Update the two rec arrays that track discharge to the ground surface

    Args:
        curpTS (pd.Timestamp): current simulation time/day
        tArray (np.array, 2D, (2, NCPL)): array that extracted from MODFLOW
                                            at the end of every time step
    
    Returns:
        retStat (int): 0 == good; currently only 0 returned

    """
    # imports
    # globals
    global TRACK_DIS_OUT, TRACK_REJI_OUT, SIM_MONTH_SERIES 
    # parameters
    goodReturn = 0
    #badReturn = -1
    # locals
    retStat = goodReturn
    # current current dt.datetime for the beginning of the month
    curDT = dt.datetime( curpTS.year, curpTS.month, 1 )
    curIndex = SIM_MONTH_SERIES.get_loc( curDT )
    # increment from 0-based
    curIndex += 1
    # get the string form
    strIndex = "%d" % curIndex
    # now do our updates
    TRACK_DIS_OUT[:][ strIndex ] += tArray[0,:]
    TRACK_REJI_OUT[:][ strIndex ] += tArray[1,:]
    # return
    return retStat


def outputTracking():
    """Output all of our tracking collections so that these can be
    post-processed if desired. Output to four pickle files.

    Pickle file 1 'IndexDict.pickle', dictionary, DI, with indexes
        DI['ncpl'] = NUM_CPL
        DI['nuzf'] = NUM_UZF
        DI['sim_day_index'] = SIM_DAYS_SERIES
        DI['sim_month_index'] = SIM_MONTH_SERIES

    Pickle file 2, 'UZF_from_HSPF.pickle', TRACK_UZF_IN

    Pickle file 3, 'GSURF_from_MF6.pickle', TRACK_DIS_OUT 

    Pickle file 4, 'REJINF_from_MF6.pickle', TRACK_REJI_OUT 

    """
    # imports
    import pickle
    # globals
    global NUM_CPL, NUM_UZF, SIM_DAYS_SERIES, SIM_MONTH_SERIES
    global TRACK_DIS_OUT, TRACK_REJI_OUT, TRACK_UZF_IN 
    # parameters
    goodReturn = 0
    #badReturn = -1
    # locals
    retStat = goodReturn
    # make the dictionary for the indexes
    IndDict = dict()
    IndDict['ncpl'] = NUM_CPL
    IndDict['nuzf'] = NUM_UZF
    IndDict['sim_day_index'] = SIM_DAYS_SERIES
    IndDict['sim_month_index'] = SIM_MONTH_SERIES 
    with open( "IndexDict.pickle", 'wb' ) as OP:
        pickle.dump( IndDict, OP, protocol=pickle.HIGHEST_PROTOCOL )
    # end with
    with open( "UZF_from_HSPF.pickle", 'wb' ) as OP:
        pickle.dump( TRACK_UZF_IN, OP, protocol=pickle.HIGHEST_PROTOCOL )
    # end with
    with open( "GSURF_from_MF6.pickle", 'wb' ) as OP:
        pickle.dump( TRACK_DIS_OUT, OP, protocol=pickle.HIGHEST_PROTOCOL )
    # end with
    with open( "REJINF_from_MF6.pickle", 'wb' ) as OP:
        pickle.dump( TRACK_REJI_OUT, OP, protocol=pickle.HIGHEST_PROTOCOL )
    # end with
    # return
    return retStat


def saMF6TimeLoop( simdir ):
    """Main MODFLOW 6 time loop and all model setup for standalone

    Args:
        simdir(str): directory with simulation inputs

    Returns:
        retStat (int): 0 == success

    """
    # imports
    import pyMF6.pyMF6 as mf6
    # globals
    # parameters
    # locals
    # logic
    # start the logger
    CL.loggerStart( simdir )
    # now are ready to do the MODFLOW stuff
    mf6.f2pwrap.setup()
    # next, need to set-up our simulation objects
    mf6.f2pwrap.objsetup()
    # start the time loop
    totalsimtime = mf6.f2pwrap.gettotalsimtime()
    tottime = mf6.f2pwrap.gettotim()
    iCnt = 0
    while ( tottime < totalsimtime ):
        # run our inner loop stuff
        mf6Stat = mf6.f2pwrap.innertimeloop()
        # check
        if mf6Stat != 0:
            errMsg = "MODFLOW did not converge on time step %d" % iCnt
            CL.LOGR.error(errMsg)
            break
        # end if
        iCnt += 1
        # get the new time
        tottime = mf6.f2pwrap.gettotim()
    # end while
    # done with time loop so deallocate and close up
    # final processing
    retStat = mf6.f2pwrap.finalproc()
    # close the log
    CL.loggerEnd()
    # return
    return retStat + mf6Stat


def MF6TimeLoop( qMF6, qHSP2 ):
    """Main MODFLOW6 time loop and all model setup
    Currently have to run the simulation from the current directory and 
    need to have all of the custom Python files in that directory as well.

    Args:
        qMF6 (Queue client): queue for information from MODFLOW 6
        qHSP2 (Queue client): queue for information from HSP2

    Returns:
        retStat (int): 0 == success

    """
    # imports
    import pyMF6 as mf6
    # globals
    global MF_SIM_NAME, NUM_CPL, NUM_UZF, SIM_DAYS_SERIES
    # parameters
    goodReturn = 0
    badReturn = -1
    # locals
    # logic
    # now are ready to do the MODFLOW stuff
    mf6.f2pwrap.cphsetup()
    # next, need to set-up our simulation objects
    mf6.f2pwrap.objsetup()
    # start the time loop
    # start the time loop
    totalsimtime = mf6.f2pwrap.gettotalsimtime()
    tottime = mf6.f2pwrap.gettotim()
    iCnt = 0
    while ( tottime < totalsimtime ):
        # run our inner loop stuff
        curpTS = SIM_DAYS_SERIES[iCnt]
        # wait for communication from HSP2
        try:
            RecArray = qHSP2.get( True, QUEUE_TIMEOUT )
        except Empty:
            # Timeout
            errMsg = "HSP2 queue timeout at day %d. Timeout period %g " \
                        "seconds.\n" % ( iCnt, QUEUE_TIMEOUT )
            CL.LOGR.error( errMsg )
            qMF6.put( QUEUE_ERROR )
            mf6Stat = badReturn
            break
        except:
            ErrTuple = sys.exc_info()
            errMsg = "Exception thrown getting message from HSP2 " \
                        " queue.\nMessage: Type - %s ; Value - %s \n" \
                        "Traceback - %s \n\n" % \
                        ( ErrTuple[0], ErrTuple[1], ErrTuple[2] )
            CL.LOGR.error( errMsg )
            qMF6.put( QUEUE_ERROR )
            mf6Stat = badReturn
            break
        # end try block
        # parse the received array
        retStat = processArrayComm( RecArray )
        if retStat != 0:
            qMF6.put( QUEUE_ERROR )
            mf6Stat = badReturn
            break
        # end inner if
        # add to our checking rec arrays
        retStat = updateUZFRAs( curpTS, RecArray )
        if retStat != 0:
            mf6Stat = badReturn
            break
        # main part of the loop
        # main part of the loop
        sdisMat = mf6.f2pwrap.cphinnertimeloop( RecArray, NUM_CPL, 
                                                NUM_UZF )
        sdisArray = sdisMat[0,:] + sdisMat[1,:]
        # update our tracking arrays
        retStat = updateDischargeRAs( curpTS, sdisMat )
        if retStat != 0:
            mf6Stat = badReturn
            break
        # now check for convergence
        mf6Stat = mf6.f2pwrap.cphconverge_check()
        if mf6Stat != goodReturn:
            errMsg = "MODFLOW model did not converge at time step %d!!!" % iCnt
            CL.LOGR.error( errMsg )
            break
        # end if
        # send information to HSP2
        qMF6.put( sdisArray )
        # update the counter
        iCnt += 1
        # get the new time
        tottime = mf6.f2pwrap.gettotim()
    # end while
    # done with time loop so deallocate and close up
    # final processing
    logmsg = "Finished main time loop"
    CL.LOGR.info( logmsg )
    retStat1 = mf6.f2pwrap.cphfinalproc()
    logmsg = "Finished cphfinalproc, status %d" % retStat1 
    CL.LOGR.info( logmsg )
    # deallocate
    mf6.f2pwrap.cphdeallocall()
    logmsg = "Finished cphdeallocall"
    CL.LOGR.info( logmsg )
    # output our rec.arrays and indexes to pickle files
    retStat3 = outputTracking( )
    logmsg = "Finished outputTracking, status %d" % retStat3
    CL.LOGR.info( logmsg )
    # get our return value
    retStat = goodReturn + mf6Stat + retStat1 + retStat3
    # return
    return retStat


def metaChecks( mf6root, cwd, start_dt, end_dt, num_lay, num_cpl, 
                num_vert, num_uzf ):
    """Check the remaining meta data items pass from the queue
    server as part of initial setup. Uses flopy to implement
    these checks.

    Args:
        mf6root (str): MODFLOW 6 model root name
        cwd (str): MODFLOW 6 model directory
        start_dt (dt.datetime): starting date time
        end_dt (dt.datetime): ending date time
        num_lay (int): number of layers
        num_cpl (int): number of cells per layer
        num_vert (int): number of vertices per layer
        num_uzf (int): number of UZF cells in the model

    Returns:
        retStat (int): 0 == success

    """
    # imports
    import flopy
    # globals
    # parameters
    goodReturn = 0
    badReturn = -1
    GOOD_TU = "days"
    GOOD_LU = 'meters'
    GOOD_GRID = "DISV"
    UZF_NAME = 'uzf'
    # locals
    # start
    # need to get the simulation object
    mf6_sim = flopy.mf6.MFSimulation.load( mf6root, 'mf6', 'mf6', cwd )
    if mf6_sim is None:
        # did not get the simulation
        errMsg = "Unable to get MODFLOW 6 simulation %s in directory " \
                 "%s!!!" % ( mf6root, cwd )
        CL.LOGR.error( errMsg )
        return badReturn
    # can get the time information from the simulation object
    timeSettings = mf6_sim.get_package( 'tdis' )
    if timeSettings is None:
        # unable to get time settings
        errMsg = "Unable to get MODFLOW 6 simulation %s time settings!!!"
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    # number of stress periods
    nper = timeSettings.nper.get_data()
    # get the time units
    timeU = timeSettings.time_units.get_data()
    if timeU != GOOD_TU:
        # error
        errMsg = "Only MODFLOW6 time units of %s are supported. Model " \
                 "%s has units of %s!!!" % ( GOOD_TU, mf6root, timeU )
        CL.LOGR.error( errMsg )
        return badReturn
    # start date time
    startStr = timeSettings.start_date_time.get_data()
    MStart_DT = dt.datetime.strptime( startStr, "%Y-%m-%d" )
    if MStart_DT != start_dt:
        # this is an error
        errMsg = "MODFLOW 6 start date is %s and HSP2 start date " \
                 "is %s!!!" % ( MStart_DT.strftime( "%Y-%m-%d" ),
                                start_dt.strftime( "%Y-%m-%d") )
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    TotHSP2Days = ( end_dt - start_dt ).days
    # now calculate the total MODFLOW6 simulation days
    timeArray = timeSettings.perioddata.array
    perlen = timeArray['perlen'].view( dtype=np.float64 )
    numts = timeArray['nstp'].view( dtype=np.int32 )
    compPL = np.array( perlen.copy(), dtype=np.int32 )
    # check that the number of time steps is equal to the
    #   the period length in days
    if not np.array_equal( numts, compPL ):
        # this is an array
        errMsg = "The number of time steps per stress period must " \
                 "be equal to the number of days in a stress period " \
                 "so that daily time steps are used!!!"
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    TotMF6Days = perlen.sum()
    if TotMF6Days != TotHSP2Days:
        # this is an error
        errMsg = "Total number of HSP2 simulation days is %g and the " \
                 "total MODFLOW 6 simulation days is %g. These two must " \
                 "be equal!!!" % ( TotHSP2Days, TotMF6Days )
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    # check the number and type of models
    modelDict = mf6_sim.model_dict
    numModels = len( modelDict )
    if numModels != 1:
        # this is an error for our purposes
        errMsg = "Total number of models in MODFLOW 6 simulation is %d.\n" \
                 "Only 1 model is supported." % numModels
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    # check that is a gwf
    OurKey = sorted( modelDict.keys() )[0]
    if not modelDict[OurKey].model_type == "gwf":
        # this is an error
        errMsg = "Only model type gwf is currently supported. Model %s " \
                 "has type of %s" % ( OurKey, modelDict[OurKey].model_type )
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    # Now need to get the model object to check the remaining items
    mf6 = mf6_sim.get_model( mf6root.lower() )
    if mf6 is None:
        # then we didn't get anything
        errMsg = "Unable to get a flopy gwf model object for %s in " \
                 "directory %s!!!" % (mf6root, cwd )
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    gType = mf6.get_grid_type()
    if not gType.name == GOOD_GRID:
        # this is an error
        errMsg = "Only %s MODFLOW 6 grid types are supported. Model %s " \
                 "uses a grid type of %s!!!!" % ( GOOD_GRID, mf6root, 
                 gType.name )
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    # get the DISV package
    Disv = mf6.get_package( GOOD_GRID.lower() )
    if Disv is None:
        errMsg = "Unable to obtain %s grid package from model %s!!!" % \
                 ( GOOD_GRID.lower(), mf6root )
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    MF6LenUnits = Disv.length_units.get_data()
    if MF6LenUnits != GOOD_LU:
        errMsg = "Only length units of %s are supported. Model %s has " \
                 "units of %s!!!" % ( GOOD_LU, mf6root, MF6LenUnits )
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    modNCPL = Disv.ncpl.get_data()
    modNLAY = Disv.nlay.get_data()
    modNVERT = Disv.nvert.get_data()
    # now check
    if ( ( modNCPL != num_cpl ) or ( modNLAY != num_lay ) or 
                ( modNVERT != num_vert ) ):
        errMsg = "Input grid dimensions do not agree with model %s " \
                 "grid dimensions. Input - layers %d, cells per layer " \
                 "%d, vertices per layer %d. Model - layers %d, cells " \
                 "per layer %d, vertices per layer %d." % \
                 ( mf6root, num_lay, num_cpl, num_vert, modNLAY, modNCPL, 
                   modNVERT )
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    # next check the UZF package
    if not UZF_NAME in mf6.package_names:
        # this is an error
        errMsg = "Coupled MODFLOW 6 model is required to use the %s " \
                 "package." % UZF_NAME
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    Uzf = mf6.get_package( UZF_NAME )
    if Uzf is None:
        errMsg = "Unable to obtain %s package from model %s!!!" % \
                 ( UZF_NAME, mf6root )
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    # now check the UZF configuration
    NUZFCELLS = Uzf.nuzfcells.get_data() 
    if NUZFCELLS != num_uzf:
        # this is an error
        errMsg = "Model %s has %d UZF cells and %d were specified in the " \
                 "input file." % ( mf6root, NUZFCELLS, num_uzf )
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    simGWSeep = Uzf.simulate_gwseep.get_data()
    if not simGWSeep:
        # this is an error
        errMsg = "Coupled model requires that UZF GW seepage be turned on " \
                 "in UZF package."
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    simUZFEt = Uzf.simulate_et.get_data()
    if simUZFEt is None:
        simUZFEt = False
    else:
        if simUZFEt:
            # this is an error
            errMsg = "UZF ET simulation must be turned off for coupled models."
            CL.LOGR.error( errMsg )
            return badReturn
        # end inner if
    # end if
    uzfPeriod = Uzf.perioddata.get_data()
    if len( uzfPeriod ) != 1:
        # this is an error
        errMsg = "Coupled model requires that UZF inputs only be provided for " \
                 "the first stress period. %s has inputs for %d stress periods." \
                 % ( mf6root, len( uzfPeriod ) )
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    # end of checks - if made it here then are good
    infoMsg = "Model %s in directory %s has time units of %s and length " \
              "units of %s; %d stress periods and %g total simulation " \
              "days; and, it has %d layers with %d cells per layer and " \
              "a grid type of %s." % ( mf6root, cwd, GOOD_TU, GOOD_LU,
              nper, TotMF6Days, modNLAY, modNCPL, GOOD_GRID )
    CL.LOGR.info( infoMsg )
    infoMsg = "Model %s also uses the UZF package. Only GW seepage is " \
              "simulated and there are %d UZF cells. Additionally inputs " \
              "are only provided for 1 stress period." % ( mf6root, num_uzf )
    CL.LOGR.info( infoMsg )
    # return
    return goodReturn


# ---------------------------------------------------------------------
# Queue processing methods
def processInitMeta( PassList ):
    """Process the initial metadata communication received from the
    queue server. Call the various routines as required to read 
    in all of the HDF5 information as required to completely set
    up the model and check start time, end time, number of 
    pervious, number of impervious, and number of reach res

    Args:
        PassList (list): list, L, of items - these are pickled and 
                                unpickled and following formats are
                                required.
                        L[0] (str): model directory
                        L[1] (dt.datetime): start time
                        L[2] (dt.datetime): end time
                        L[3] (int): number of layers
                        L[4] (int): number of cells per layer
                        L[5] (int): number of vertices per layer
                        L[6] (str): MODFLOW 6 root file name
                        L[7] (int): number of uzf cells

    Return:
        cwd (str): FQDN path for MODFLOW 6 simulation files

    """
    # imports
    import pandas as pd
    # globals
    global QUEUE_ERROR, NUM_LAY, NUM_CPL, NUM_UZF
    global SIM_DAYS, SIM_DAYS_SERIES, SIM_MONTH_SERIES, SIM_MONTHS
    # parameters
    PASS_LEN = 8
    emptyStr = ""
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
        with open( "MF6_QueueInit_Errors.txt", 'w' ) as LogFID:
            LogFID.write("%s" % errMsg )
        # end with block and close file
        return emptyStr
    # end try
    if ErrorOccurred or TooSmall:
        # these are also errors
        errMsg = "Either an error occurred in the intitial starutp, %s, " \
                 "or passed list length does not conform with " \
                 "expectations, %s.\n\n" % ( ErrorOccurred, TooSmall )
        with open( "MF6_QueueInit_Errors.txt", 'w' ) as LogFID:
            LogFID.write("%s" % errMsg )
        # end with block and close file
        return emptyStr
    # end if
    # now process our values
    if len( PassList ) != PASS_LEN:
        # this is an error
        errMsg = "Expected a list with %d items in processInitMeta and " \
                 "received a list with %d items.\n" % \
                 ( PASS_LEN, len( PassList ) )
        with open( "MF6_QueueInit_Errors.txt", 'w' ) as LogFID:
            LogFID.write("%s" % errMsg )
        # end with block and close file
        return emptyStr
    # now get our values
    cwd = PassList[0]
    start_dt = PassList[1]
    end_dt = PassList[2]
    num_lay = PassList[3]
    num_cpl = PassList[4]
    num_vert = PassList[5]
    mod_root = PassList[6]
    num_uzf = PassList[7]
    # now set up our log file
    CL.loggerStart( cwd )
    # do our remaining checks
    if not type( start_dt ) == dt.datetime:
        # an error
        errMsg = "Expected type %s for start_dt and received %s!!!\n" % \
                 ( type( dt.datetime.now() ), str( start_dt ) )
        CL.LOGR.error( errMsg )
        return emptyStr
    if not type( end_dt ) == dt.datetime:
        # an error
        errMsg = "Expected type %s for end_dt and received %s!!!\n" % \
                 ( type( dt.datetime.now() ), str( end_dt ) )
        CL.LOGR.error( errMsg )
        return emptyStr
    if not type( num_lay ) == int:
        # an error
        errMsg = "Expected type %s for num_lay and received %s!!!\n" % \
                 ( type( 1 ), str( num_lay ) )
        CL.LOGR.error( errMsg )
        return emptyStr
    if not type( num_cpl ) == int:
        # an error
        errMsg = "Expected type %s for num_cpl and received %s!!!\n" % \
                 ( type( 1 ), str( num_cpl ) )
        CL.LOGR.error( errMsg )
        return emptyStr
    if not type( num_vert ) == int:
        # an error
        errMsg = "Expected type %s for num_vert and received %s!!!\n" % \
                 ( type( 1 ), str( num_vert ) )
        CL.LOGR.error( errMsg )
        return emptyStr
    if not type( num_uzf ) == int:
        # an error
        errMsg = "Expected type %s for num_uzf and received %s!!!\n" % \
                 ( type( 1 ), str( num_uzf ) )
        CL.LOGR.error( errMsg )
        return emptyStr
    # now check the values
    retStat = metaChecks( mod_root, cwd, start_dt, end_dt, num_lay, 
                          num_cpl, num_vert, num_uzf )
    if retStat != 0:
        # then an error
        errMsg = "MF6 metadata value disagreement in processInitMeta\n"
        CL.LOGR.error( errMsg )
        return emptyStr
    # now do the global assignments
    NUM_LAY = num_lay
    NUM_CPL = num_cpl
    NUM_UZF = num_uzf
    # finally create our simulation time indices
    SIM_DAYS = ( end_dt - start_dt ).days
    SIM_DAYS_SERIES = pd.date_range( start=start_dt, end=end_dt, 
                                     freq='D', closed='left' )
    SIM_MONTH_SERIES = pd.date_range( start=start_dt, end=end_dt,
                                      freq='MS', closed='left' )
    SIM_MONTHS = len( SIM_MONTH_SERIES )
    # set-up the tracking rec.arrays. Not checked at this time but if
    #  run into issues with initialization then will need to add 
    #  checking
    retStat = setupRecarrays( NUM_CPL, NUM_UZF, SIM_MONTHS )
    # now return
    return cwd


def processReadyComm( StringList ):
    """Process the ready communication with external processes

    Args:
        StringList (list): list of string items

    Return:
        retStat (int): success == 0

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
        errMsg = "Unknown exception in MF6 processReadyComm checking of %s" \
                  ".\nType - %s ; Value - %s\nTraceback - %s \n\n" % \
                  ( StringList, ErrTuple[0], ErrTuple[1], ErrTuple[2] )
        CL.LOGR.error( errMsg )
        return badReturn
    # end try
    if ErrorOccurred or TooSmall:
        # these are also errors
        errMsg = "Either an error occurred in the MF6 processReadyComm, %s, " \
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


def processArrayComm( NpArray ):
    """Process the array communication from MODFLOW 6

    Args:
        NpArray (np.array): the array of discharge to the surface from 
                            MODFLOW 6

    Return:
        retStat (int): success == 0

    """
    # imports
    # globals
    global QUEUE_ERROR, NUM_UZF
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
        errMsg = "Unknown exception in MF6 processArrayComm checking of " \
                  "passed array.\nType - %s ; Value - %s\nTraceback - " \
                  "%s \n\n" % \
                  ( ErrTuple[0], ErrTuple[1], ErrTuple[2] )
        CL.LOGR.error( errMsg )
        return badReturn
    # end try
    if ErrorOccurred or TooSmall:
        # these are also errors
        errMsg = "Either an error occurred in the MF6 processArrayComm, %s, " \
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
    # check the array size
    if NpArray.shape[0] != NUM_UZF:
        # this is an error
        errMsg = "Received numpy array from HSP2 with dim 0 of " \
                 "%d and expected ncpl of %d!!!!" % \
                 ( NpArray.shape[0], NUM_UZF)
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    # add call to function here to process the array
    # return
    return goodReturn


# standalone execution block
# assumes that this module is executed within the same current directory
# as the input file
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
        with open( "MF6_QueueInit_Errors.txt", 'w' ) as LogFID:
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
                 "seconds.\n" % START_QUEUE_TO
        with open( "MF6_QueueInit_Errors.txt", 'w' ) as LogFID:
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
        with open( "MF6_QueueInit_Errors.txt", 'w' ) as LogFID:
            LogFID.write("%s" % errMsg )
        # end with block and close file
        qTERM.put( QUEUE_ERROR )
        sys.exit( errMsg )
    # now process the pass list
    CurDir = processInitMeta( PassList )
    if len( CurDir ) < 3:
        # this is an error
        errMsg = "Metadata checking failed for MF6!!!!"
        qTERM.put( QUEUE_ERROR )
        sys.exit( errMsg )
    # end check if
    OrgDir = os.getcwd() 
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
        PassList = qHSP2.get( True, START_QUEUE_TO )
    except Empty:
        # Timeout
        errMsg = "HSP2 queue timeout. Timeout period %g " \
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
        errMsg = "Invalid ready message received by MF6!!!"
        CL.LOGR.error( errMsg )
        qTERM.put( QUEUE_ERROR )
        sys.exit( errMsg )
    # end if
    # start the main time loop
    # change to our model directory
    os.chdir( CurDir )
    # make sure that the simulation name file exists. We no longer use the 
    #   call to GetCommandLineArguments
    if not os.path.isfile( MF_SIM_NAME ):
        # this is an error
        errMsg = "File %s does not exist!!!" % MF_SIM_NAME
        CL.LOGR.error( errMsg )
        qMF6.put( QUEUE_ERROR )
        qTERM.put( QUEUE_ERROR )
        sys.exit( errMsg )
    # end if and ready for main loop
    retStat = MF6TimeLoop( qMF6, qHSP2 )
    if retStat != 0:
        errMsg = "Error in main time loop!!!"
        CL.LOGR.error( errMsg )
        qMF6.put( QUEUE_ERROR )
        qTERM.put( QUEUE_ERROR )
        sys.exit( errMsg )
    else:
        infomsg = "Received success MF6 end"
        CL.LOGR.info( infomsg )
    # end if
    # change back to our directory
    os.chdir( OrgDir )
    CL.LOGR.info( "Changed back to original directory" )
    # send some sort of close sign
    qTERM.put( QEND_MSG )
    # close this log
    CL.loggerEnd()
    # end


#EOF