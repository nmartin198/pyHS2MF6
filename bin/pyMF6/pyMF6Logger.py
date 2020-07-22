"""
.. module:: pyMF6Logger.py
   :platform: Windows, Linux
   :synopsis: pyMF6 custom logger

.. moduleauthor:: Nick Martin <nmartin@swri.org>

Provides specification and configuration of Python's logging API to use for
debugging and informational purposes.

A log file, specified with LOGNAME, is used for receipt of log statements.
Logging level is set with LOG_LEVEL.

"""
import logging
import os

# parameters
LOGNAME = "pyMF6_Log.txt"
"""Log file name"""
LOG_LEVEL = logging.DEBUG
"""Logging level"""
START_TIME = None
"""MODFLOW 6 model start time"""

# set up the logger
LOGR = logging.getLogger('pyMF6')
"""Custom logger"""
LOGR.setLevel( LOG_LEVEL )

FH = None
"""File handler"""
FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
"""Custom formatter"""


def loggerStart(  LFPath  ):
    """Start the logger to use for the entire program
    """
    # local imports
    import datetime as dt
    # globals
    global LOGR, START_TIME
    # start the configuration
    # get the full log file path
    LFPath = os.path.normpath( os.path.join( LFPath, LOGNAME ) )
    FH = logging.FileHandler( LFPath, mode='w' )
    FH.setLevel( LOG_LEVEL )
    FH.setFormatter( FORMATTER )
    LOGR.addHandler( FH )
    # write the first entry
    START_TIME = dt.datetime.now()
    LOGR.info( "Start MODFLOW6 model at %s\n" % 
                  START_TIME.strftime( "%Y-%m-%d %H:%M:%S" ) )


def loggerEnd():
    """End the program-wide logger
    """
    # imports
    import datetime as dt
    # globals
    global LOGR, START_TIME
    # set the end time
    END_TIME = dt.datetime.now()
    eTimerS = ( END_TIME - START_TIME ).total_seconds()
    eTimerM = eTimerS/60.0
    LOGR.info( "End of MODFLOW6 mods at %s - elapsed time - %10.2f min\n" % 
               ( END_TIME.strftime( "%Y-%m-%d %H:%M:%S" ), eTimerM ) )


#EOF