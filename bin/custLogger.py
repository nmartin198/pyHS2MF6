# -*- coding: utf-8 -*-
"""
.. module:: custLogger.py
   :platform: Windows, Linux
   :synopsis: Coupled model logger

.. moduleauthor:: Nick Martin <nmartin@swri.org>

Provides specification and configuration of Python's logging API to use for
debugging and informational purposes.

"""
# imports
import logging
import os

# parameters
LOGNAME = "pyHS2MF6_Log.txt"
"""Log file name"""
LOG_LEVEL = logging.DEBUG
"""Logging level"""
START_TIME = None
"""Coupled model start time"""

# set up the logger
LOGR = logging.getLogger('COUPLED')
"""Custom logging object"""
LOGR.setLevel( LOG_LEVEL )

FH = None
"""File handler"""
FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
"""Custom formatter"""


def loggerStart( LFPath ):
    """Start the logger to use for the entire program

    Args:
        LFPath (str): FQDN path for the log file
    """
    # local imports
    import datetime as dt
    # globals
    global LOGR, START_TIME, FH, LOGNAME, FORMATTER, LOGR
    # start the configuration
    # get the full log file path
    LFPath = os.path.normpath( os.path.join( LFPath, LOGNAME ) )
    FH = logging.FileHandler( LFPath, mode='w' )
    FH.setLevel( LOG_LEVEL )
    FH.setFormatter( FORMATTER )
    LOGR.addHandler( FH )
    # now write the first entry
    START_TIME = dt.datetime.now()
    LOGR.info( "Start Coupled HSP2 and MODFLOW6 at %s\n" % 
                  START_TIME.strftime( "%Y-%m-%d %H:%M:%S" ) )
    # return
    return


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
    LOGR.info( "End Coupled HSP2 and MODFLOW6 at %s - elapsed time " \
               "- %10.2f min\n" % \
               ( END_TIME.strftime( "%Y-%m-%d %H:%M:%S" ), eTimerM ) )
    # return
    return 


#EOF    