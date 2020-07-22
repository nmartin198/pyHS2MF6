"""
pyMF6 custom logger leveraging Python logging

Provides specification and configuration of Python's logging API to use for
debugging and informational purposes.

A log file, specified with LOGNAME, is used for receipt of log statements.
Logging level is set with LOG_LEVEL.

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
    """Start the logger to use for pyMF6
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
    LOGR.info( "Start pyMF6 model at %s\n" % 
                  START_TIME.strftime( "%Y-%m-%d %H:%M:%S" ) )


def loggerEnd():
    """End the pyMF6 logger
    """
    # imports
    import datetime as dt
    # globals
    global LOGR, START_TIME
    # set the end time
    END_TIME = dt.datetime.now()
    eTimerS = ( END_TIME - START_TIME ).total_seconds()
    eTimerM = eTimerS/60.0
    LOGR.info( "End of pyMF6 model at %s - elapsed time - %10.2f min\n" % 
               ( END_TIME.strftime( "%Y-%m-%d %H:%M:%S" ), eTimerM ) )


#EOF