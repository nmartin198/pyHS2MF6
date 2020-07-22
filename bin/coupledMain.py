# -*- coding: utf-8 -*-
"""
.. module:: coupledMain.py
   :platform: Windows, Linux
   :synopsis: pyHS2MF6 main for coupled MODFLOW6 and HSP2

.. moduleauthor:: Nick Martin <nmartin@swri.org>

Purpose:

Provides custom multiprocessing, message passing interface queue manager or
queue server. This needs to be executed as an independent process and then
it will launch a queue server that manages three queues.

1. From mHSP2 queue
2. From pyMF6 queue
3. Program control/termination queue

Each queue is associated with a socket and has an authorization key. The
authorization key and correct socket/port are required for access from
another client.

To run the coupled program, open an Anaconda prompt

1. conda activate py3
2. cd to the model main directory where the coupled input file is located
3. python {path to this file} {coupled input file} 
4. python {path to this file} -h 
    - will provide command line help

python ..\LOCA\coupledMain.py LOCA_In.dat

"""
import sys
import os
OUR_MODULE_PATH = os.path.abspath( __file__ )
"""Current module path"""
OUR_PACKAGE_PATH = os.path.abspath( os.path.join( OUR_MODULE_PATH, '..' ) )
"""Current package path"""
PATH_LIST = sys.path
if ( not OUR_PACKAGE_PATH in PATH_LIST ):
    sys.path.append( OUR_PACKAGE_PATH )
import argparse
from subprocess import Popen, STDOUT
from multiprocessing import Queue
from queue import Empty
from multiprocessing.managers import SyncManager
from functools import partial
import custLogger as CL
import pyHS2MF6_Inputs as LI

# globals
CUR_ENV = os.environ
"""The environment for running the subprocesses"""
mHSP2_MAIN = "locaMain.py"
"""Location of the standalone execution block for HSP2"""
pyMF6_MAIN = "pyMF6py.py"
"""Location of the standalone execution block for MODFLOW 6"""

# -----------------------------------------------------------
# queue definitions. Python multiprocessing queues with remote manager 
# are used to dynamically share information among this main wrapper and
# the DLLs. This facilities setting custom station IDs from the command
# line in this case.
# queue stuff
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
"""Authorization key, needs to be encoded"""
# queue names
NAME_FROM_HSPF = 'qmHSP2'
NAME_FROM_MF6 = 'qmMF6'
NAME_FROM_TERM = 'qmTERM'
# the queue server description
HSP2_DESCRIPTION = 'HSP2 Queue Server'
MF6_DESCRIPTION = 'MODFLOW 6 Queue Server'
TERM_DESCRIPTION = 'Termination Queue Server'
QINIT_MSG = [ "Hello" ]
"""Queue intialization and check in message"""
QUEUE_TIMEOUT = ( 60.0 * ( 1.0 * 60.0 ) )
"""End of simulation wait time in seconds """
START_QUEUE_TO = ( 60.0 * 5.0 )
"""Queue wait timeout before error in seconds. This is for the
startup communications """
QUEUE_ERROR = [ "Error" ]
"""Error message to put on queues for program termination """
QREADY_MSG = [ "Ready" ]
"""Queue ready to start message"""
QEND_MSG = [ "End" ]
"""End of simulation message"""
SHELL_CAPTURE = "MF6_ShellOut.txt"
"""Capture the standard MODFLOW simulation output to text file"""

#---------------------------------------------------------
# Remote queue multi-processing stuff. Much needs to be at the top level
# so that can be pickled for the queues
def get_q(q):
    """Main level definition of the get function for queue definition. This
    needs to be at this level so that pickle can find it.
    
    Args:
        q(Queue): queue to be returned
            
    Return:
        q(Queue): return the queue reference (i.e. return itself)
    """
    return q


# create the queue manager class
# needs to be at the top level so that is pickleable. Do not need to do
# anything here just subclass SyncManager
class QueueManager(SyncManager):
    pass


def CreateQueueServer( ThisHost, Porter, CustomAuth, name = None, 
                       description = None):
    """
    This is where we actually create and start the queues. Needs to be called
    2 times, one for each queue. The "register" settings provide the 
    basic method structure for our queues.
    
    See:
        https://docs.python.org/2.7/library/multiprocessing.html#using-a-remote-manager
        http://stackoverflow.com/questions/11532654/python-multiprocessing-remotemanager-under-a-multiprocessing-process
        http://stackoverflow.com/questions/25631266/cant-pickle-class-main-jobqueuemanager
    
    Args:
        ThisHost(str): host name. Should be 'localhost' for the same machine
        Porter(int): the port number to listen on
        CustomAuth(str): the custom authorization string
        name(str): the queue name
        description(str): the queue description
        
    Return:
        manager(QueueManager): return the reference to the queue manager
        
    """
    name = name
    description = description
    q = Queue()
    # now register our keys
    QueueManager.register('get_queue', callable=partial(get_q, q))
    QueueManager.register('get_name', callable = name)
    QueueManager.register('get_description', callable = description)
    # create an and start the queue manager
    manager = QueueManager(address = (ThisHost, Porter), authkey = CustomAuth)
    manager.start() # This actually starts the server
    # return
    return manager


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


def WriteQueueCheckToLog( qHSP2, qMF6, qTERM ):
    """Write queue checks to log file
    
    Args:
        qHSP2(Queue): the from HSP2 queue
        qMF6(Queue): the from MODFLOW 6 queue
        qTERM(Queue): error handling queue
    
    Return:
        retStat (int): success == 0
    """
    # imports
    from sys import exc_info
    # globals
    # parameters
    goodReturn = 0
    badReturn = -1
    # do the output
    try:
        HSP2QueueSize = str( qHSP2.qsize() )
        MF6QueueSize = str( qMF6.qsize() )
        TERMQueueSize = str( qTERM.qsize() )
    except:
        # in this case just return
        errMsg = "Exception thrown getting queue size for output.\n" \
                 "Exception info:\n\t%s\n\n" % exc_info()[0]
        CL.LOGR.info( errMsg )
        # return
        return badReturn
    # if made it here then output
    infoMsg = "GS queue size is %s, " \
              "FE queue size is %s, " \
              "TERM queue size is %s \n" % \
              ( HSP2QueueSize, MF6QueueSize, TERMQueueSize )
    CL.LOGR.info( infoMsg )
    # end of with block
    return goodReturn


def processInitComm( StringList ):
    """Process the initial communication with external processes

    Args:
        StringList (list): list of string items

    Return:
        retStat (int): success == 0

    """
    # imports
    # globals
    global QUEUE_ERROR, QINIT_MSG
    # parameters
    goodReturn = 0
    badReturn = -1
    # use try block and check transmission for basic errors
    try:
        GoodValue = ( StringList == QINIT_MSG )
        ErrorOccurred = ( StringList == QUEUE_ERROR )
        TooSmall = ( len ( StringList ) < 1 )
    except:
        # catchall exception
        ErrTuple = sys.exc_info()
        errMsg = "Unknown exception in processInitComm checking of %s" \
                  ".\nType - %s ; Value - %s\nTraceback - %s \n\n" % \
                  ( StringList, ErrTuple[0], ErrTuple[1], ErrTuple[2] )
        CL.LOGR.error( errMsg )
        return badReturn
    # end try
    if ErrorOccurred or TooSmall:
        # these are also errors
        errMsg = "Either an error occurred in the intitial startup, %s, " \
                 "or passed list length does not conform with " \
                 "expectations, %s.\n\n" % ( ErrorOccurred, TooSmall )
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    if GoodValue:
        infoMsg = "Successfully initialized and communicated with " \
                  "queue client.\n"
        CL.LOGR.info( infoMsg )
        return goodReturn
    # end if
    errMsg = "Unknown message of %s received during process initial " \
             "startup!!!\n" % str( StringList )
    CL.LOGR.error( errMsg )
    return badReturn


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
        errMsg = "Unknown exception in processReadyComm checking of %s" \
                  ".\nType - %s ; Value - %s\nTraceback - %s \n\n" % \
                  ( StringList, ErrTuple[0], ErrTuple[1], ErrTuple[2] )
        CL.LOGR.error( errMsg )
        return badReturn
    # end try
    if ErrorOccurred or TooSmall:
        # these are also errors
        errMsg = "Either an error occurred in the metadata processing, %s, " \
                 "or passed list length does not conform with " \
                 "expectations, %s.\n\n" % ( ErrorOccurred, TooSmall )
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    if GoodValue:
        infoMsg = "Successfully passed metadata to queue client " \
                  "queue client.\n"
        CL.LOGR.info( infoMsg )
        return goodReturn
    # end if
    errMsg = "Unknown message of %s received during process metadata " \
             "processing!!!\n" % str( StringList )
    CL.LOGR.error( errMsg )
    return badReturn


def processEndComm( StringList ):
    """Process the end simulation communication with external processes

    Args:
        StringList (list): list of string items

    Return:
        retStat (int): success == 0

    """
    # imports
    # globals
    global QUEUE_ERROR, QEND_MSG
    # parameters
    goodReturn = 0
    badReturn = -1
    # use try block and check transmission for basic errors
    try:
        GoodValue = ( StringList == QEND_MSG )
        ErrorOccurred = ( StringList == QUEUE_ERROR )
        TooSmall = ( len ( StringList ) < 1 )
    except:
        # catchall exception
        ErrTuple = sys.exc_info()
        errMsg = "Unknown exception in processEndComm checking of %s" \
                  ".\nType - %s ; Value - %s\nTraceback - %s \n\n" % \
                  ( StringList, ErrTuple[0], ErrTuple[1], ErrTuple[2] )
        CL.LOGR.error( errMsg )
        return badReturn
    # end try
    if ErrorOccurred or TooSmall:
        # these are also errors
        errMsg = "Either an error occurred in processEndComm, %s, " \
                 "or passed list length does not conform with " \
                 "expectations, %s.\n\n" % ( ErrorOccurred, TooSmall )
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    if GoodValue:
        infoMsg = "Successfully received end of simulation message " \
                  "from queue client.\n"
        CL.LOGR.info( infoMsg )
        return goodReturn
    # end if
    errMsg = "Unknown message of %s received during processEndComm" % \
             str( StringList )
    CL.LOGR.error( errMsg )
    # return
    return badReturn


# standalone execution block
# assumes that this module is executed with the current directory the same
# as the input file
if __name__ == "__main__":
    # start our processing
    # do the argument processing stuff first
    apUsage = "%(prog)s <Coupled Input File>"
    apDesc = "Execute coupled mHSP2 and pyMF6 simulation"
    parser = argparse.ArgumentParser( usage=apUsage, description=apDesc )
    parser.add_argument( action='store', type=str, nargs=1, 
                         dest="input_file", 
                         help='Coupled model input file',
                         metavar="input file" )
    # parse the command line arguments received
    args = parser.parse_args()
    # extract our arguments
    InFile = args.input_file[0]
    # get the current working directory
    CWD = os.getcwd()
    # now read the input file
    retStat = LI.readInputFile( InFile, CWD )
    if retStat != 0:
        sys.exit( "Error processing input file!!!" )
    # end if
    # setup log file
    CL.loggerStart( CWD )
    # start all of the queues
    QM_HSP2 = CreateQueueServer( HOST, PORT0, AUTHKEY, NAME_FROM_HSPF, HSP2_DESCRIPTION )
    QM_MF6 = CreateQueueServer( HOST, PORT1, AUTHKEY, NAME_FROM_MF6, MF6_DESCRIPTION )
    QM_TERM = CreateQueueServer( HOST, PORT2, AUTHKEY, NAME_FROM_TERM, TERM_DESCRIPTION )
    # then get clients to put our information into the queues
    qcHSP2 = QueueServerClient( CLIENTHOST, PORT0, AUTHKEY )
    qcMF6 = QueueServerClient( CLIENTHOST, PORT1, AUTHKEY )
    qcTERM = QueueServerClient( CLIENTHOST, PORT2, AUTHKEY )
    # Get the queue objects from the clients
    qHSP2 = qcHSP2.get_queue()
    qMF6 = qcMF6.get_queue()
    qTERM = qcTERM.get_queue()
    # now output some checking stuff to our log file
    retStat = WriteQueueCheckToLog(qHSP2, qMF6, qTERM)
    if retStat != 0:
        # this is an error
        sys.exit( "Could not set up queues!!!" )
    # next start the sub processes
    locaPath = os.path.normpath( os.path.join( OUR_PACKAGE_PATH, "mHSP2", mHSP2_MAIN ) )
    mf6Path = os.path.normpath( os.path.join( OUR_PACKAGE_PATH, "pyMF6", pyMF6_MAIN ) )
    # start HSP2 first
    hspf_proc = Popen( ["python", locaPath ], env=CUR_ENV )
    hspf_pid = hspf_proc.pid
    # now are going to wait for the initial check in message
    try:
        PassList = qTERM.get( True, START_QUEUE_TO )
    except Empty:
        # Timeout
        errMsg = "mHSP2 queue timeout. Timeout period %g seconds.\n" \
                  % START_QUEUE_TO
        CL.LOGR.error( errMsg )
        qTERM.put( QUEUE_ERROR )
        sys.exit( errMsg )
    except:
        ErrTuple = sys.exc_info()
        errMsg = "Exception thrown getting message from mHSP2 " \
                 "queue.\nMessage: Type - %s ; Value - %s \n" \
                 "Traceback - %s \n\n" % \
                 ( ErrTuple[0], ErrTuple[1], ErrTuple[2] )
        CL.LOGR.error( errMsg )
        qTERM.put( QUEUE_ERROR )
        sys.exit( errMsg )
    # now process the pass list
    retStat = processInitComm( PassList )
    if retStat != 0:
        # an error
        errMsg = "Issue with queue or process initialization for mHSP2!!!"
        qTERM.put( QUEUE_ERROR )
        sys.exit( errMsg )
    # end if
    # send the model directory and HDF5 file paths
    SendList = [ LI.get_HSP2_DIR(), 
                 LI.get_FULL_HSP2_HDF5(),
                 LI.get_START_DT(),
                 LI.get_END_DT(),
                 LI.get_HSP2_NUM_PL(),
                 LI.get_HSP2_NUM_IL(),
                 LI.get_HSP2_NUM_RR(),
                 LI.get_MF6_NCPL(), 
                 LI.get_FULL_RR_MAP(),
                 LI.get_FULL_PL_MAP(),
                 LI.get_MF6_IUZFN(),
                 LI.get_FULL_SP_MAP(), ]
    qTERM.put( SendList )
    # now wait for the response
    try:
        PassList = qTERM.get( True, START_QUEUE_TO )
    except Empty:
        # Timeout
        errMsg = "mHSP2 queue timeout. Timeout period %g seconds.\n" \
                 % START_QUEUE_TO
        CL.LOGR.error( errMsg )
        qTERM.put( QUEUE_ERROR )
        sys.exit( errMsg )
    except:
        ErrTuple = sys.exc_info()
        errMsg = "Exception thrown getting message from mHSP2 " \
                 "queue.\nMessage: Type - %s ; Value - %s \n" \
                 "Traceback - %s \n\n" % \
                 ( ErrTuple[0], ErrTuple[1], ErrTuple[2] )
        CL.LOGR.error( errMsg )
        qTERM.put( QUEUE_ERROR )
        sys.exit( errMsg )
    # process the response
    retStat = processReadyComm( PassList )
    if retStat != 0:
        # an error
        errMsg = "Issue with metadata processing for mHSP2!!!"
        qMF6.put( QUEUE_ERROR )
        sys.exit( errMsg )
    # end if
    # ready to start MODFLOW 6
    mCaptID = open( SHELL_CAPTURE, 'w' )
    mf6_proc = Popen( ["python", mf6Path ], env=CUR_ENV, 
                      stdout=mCaptID )
    #mf6_proc = Popen( ["python", mf6Path ], env=CUR_ENV )
    mf6_pid = mf6_proc.pid
    # do init checking and setup
    try:
        PassList = qTERM.get( True, START_QUEUE_TO )
    except Empty:
        # Timeout
        errMsg = "pyMF6 queue timeout. Timeout period %g seconds.\n" % \
                 START_QUEUE_TO
        CL.LOGR.error( errMsg )
        qMF6.put( QUEUE_ERROR )
        mCaptID.close()
        sys.exit( errMsg )
    except:
        ErrTuple = sys.exc_info()
        errMsg = "Exception thrown getting message from mHSP2 " \
                 "queue.\nMessage: Type - %s ; Value - %s \n" \
                 "Traceback - %s \n\n" % \
                 ( ErrTuple[0], ErrTuple[1], ErrTuple[2] )
        CL.LOGR.error( errMsg )
        qMF6.put( QUEUE_ERROR )
        mCaptID.close()
        sys.exit( errMsg )
    # now process the pass list
    retStat = processInitComm( PassList )
    if retStat != 0:
        # an error
        errMsg = "Issue with queue or process initialization for pyMF6!!!"
        qMF6.put( QUEUE_ERROR )
        qTERM.put( QUEUE_ERROR )
        mCaptID.close()
        sys.exit( errMsg )
    # end if
    # send the metadata
    SendList = [ LI.get_MF6_DIR(), 
                 LI.get_START_DT(),
                 LI.get_END_DT(),
                 LI.get_MF6_NLAY(),
                 LI.get_MF6_NCPL(),
                 LI.get_MF6_NVERT(),
                 LI.get_MF6_ROOT(),
                 LI.get_MF6_IUZFN(), ]
    qTERM.put( SendList )
    # wait for MODFLOW 6 response
    # now wait for the response
    try:
        PassList = qTERM.get( True, START_QUEUE_TO )
    except Empty:
        # Timeout
        errMsg = "pyMF6 queue timeout. Timeout period %g seconds.\n" \
                 % START_QUEUE_TO
        CL.LOGR.error( errMsg )
        qMF6.put( QUEUE_ERROR )
        qTERM.put( QUEUE_ERROR )
        mCaptID.close()
        sys.exit( errMsg )
    except:
        ErrTuple = sys.exc_info()
        errMsg = "Exception thrown getting message from pyMF6 " \
                 "queue.\nMessage: Type - %s ; Value - %s \n" \
                 "Traceback - %s \n\n" % \
                 ( ErrTuple[0], ErrTuple[1], ErrTuple[2] )
        CL.LOGR.error( errMsg )
        qMF6.put( QUEUE_ERROR )
        qTERM.put( QUEUE_ERROR )
        mCaptID.close()
        sys.exit( errMsg )
    # process the response
    retStat = processReadyComm( PassList )
    if retStat != 0:
        # an error
        errMsg = "Issue with metadata processing for pyMF6!!!"
        qMF6.put( QUEUE_ERROR )
        qHSP2.put( QUEUE_ERROR )
        mCaptID.close()
        sys.exit( errMsg )
    # end if
    # send start to HSP2
    qMF6.put( QREADY_MSG )
    # send start to MF6
    qHSP2.put( QREADY_MSG) 
    # now all communications except for TERM are between the
    #   two child processes
    # wait for end of simulation or terminaton error.
    #   Expect to receive two of these one for each sub
    try:
        EndList = qTERM.get( True, QUEUE_TIMEOUT )
    except Empty:
        # Timeout
        errMsg = "End of simulation timeout for end 1. Timeout " \
                 "period %g seconds.\n" % QUEUE_TIMEOUT
        CL.LOGR.error( errMsg )
        qMF6.put( QUEUE_ERROR )
        qHSP2.put( QUEUE_ERROR )
        mCaptID.close()
        sys.exit( errMsg )
    except:
        ErrTuple = sys.exc_info()
        errMsg = "Exception thrown getting end of simulation " \
                 "message 1.\nMessage: Type - %s ; Value - %s \n" \
                 "Traceback - %s \n\n" % \
                 ( ErrTuple[0], ErrTuple[1], ErrTuple[2] )
        CL.LOGR.error( errMsg )
        qMF6.put( QUEUE_ERROR )
        qHSP2.put( QUEUE_ERROR )
        mCaptID.close()
        sys.exit( errMsg )
    # process
    retStat = processEndComm( EndList )
    if retStat != 0:
        # an error
        errMsg = "Error received for end message 1!!!"
        qMF6.put( QUEUE_ERROR )
        qHSP2.put( QUEUE_ERROR )
        mCaptID.close()
        sys.exit( errMsg )
    else:
        infoMsg = "Received successful end message 1!!!"
        CL.LOGR.info( infoMsg )
    # end if
    # now wait for message 2
    try:
        EndList = qTERM.get( True, QUEUE_TIMEOUT )
    except Empty:
        # Timeout
        errMsg = "End of simulation timeout for end 2. Timeout " \
                 "period %g seconds.\n" % QUEUE_TIMEOUT
        CL.LOGR.error( errMsg )
        qMF6.put( QUEUE_ERROR )
        qHSP2.put( QUEUE_ERROR )
        mCaptID.close()
        sys.exit( errMsg )
    except:
        ErrTuple = sys.exc_info()
        errMsg = "Exception thrown getting end of simulation " \
                 "message 5.\nMessage: Type - %s ; Value - %s \n" \
                 "Traceback - %s \n\n" % \
                 ( ErrTuple[0], ErrTuple[1], ErrTuple[2] )
        CL.LOGR.error( errMsg )
        qMF6.put( QUEUE_ERROR )
        qHSP2.put( QUEUE_ERROR )
        mCaptID.close()
        sys.exit( errMsg )
    # process
    retStat = processEndComm( EndList )
    if retStat != 0:
        # an error
        errMsg = "Error received for end message 2!!!"
        qMF6.put( QUEUE_ERROR )
        qHSP2.put( QUEUE_ERROR )
        mCaptID.close()
        sys.exit( errMsg )
    else:
        infoMsg = "Received successful end message 2!!!"
        CL.LOGR.info( infoMsg )
    # end if
    mCaptID.close()
    # close the logger
    CL.loggerEnd()
    # print
    print("Successful termination coupled programs")
    # end


#EOF