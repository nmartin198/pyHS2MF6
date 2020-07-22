"""
Methods and data set respository specifically for coupling.

Repository for global-level variables that introduced as part of coupling
HSP2 and MODFLOW 6. Also contains functions specifically related to
coupling.

**Note** queue communications and handling are by necessity in the main 
block or module for each process.

"""
# Copyright and License
"""
Copyright 2020 Nick Martin, Paul Southard, Stuart Stothoff

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
# package imports
import locaLogger as CL
import numpy as np


# ---------------------------------------------------------------------
# MODULE-level globals
RR_GW_MAPPING = dict()
"""Dictionary of mappings for RCHRES segments to GW model cells.

Keys are TargID, e.g. 'R001', and values are a list whose members
are enumerated below.

0. (int): groundwater exit index
1. (list): sub-list enumerated below
    0. (list): another sublist with np.arrays with dimension NCPL as items
        0. (np.array): Cell ID, 2D 1-based
        1. (np.array): weighting factor
        2. (np.array): cell area within the target ID
        3. (np.array): Layer index for top active, 1-based
        4. (np.array): UZF index, 1-based
    1. (list): sublist np.arrays with dimension NUZF as items
        0. (np.array): UZF index, 1-based
        1. (np.array): weighting factor
        2. (np.array): cell area within the target ID
        3. (np.array): Layer index for top active, 1-based
        4. (np.array): Cell ID, 2D 1-based
 
"""
PL_GW_MAPPING = dict()
"""Dictionary of mappings for PERLND areas to GW model cells.

Keys are TargID, e.g. 'P001', and values are a list that is 
enumerated below.

0. (list): sub-list with np.arrays with dimension NCPL as items
    0. (np.array): Cell ID, 2D 1-based
    1. (np.array): weighting factor
    2. (np.array): cell area within the target ID
    3. (np.array): Layer index for top active, 1-based
    4. (np.array): UZF index, 1-based
1. (list): np.arrays with dimension NUZF as items
    0. (np.array): UZF index, 1-based
    1. (np.array): weighting factor
    2. (np.array): cell area within the target ID
    3. (np.array): Layer index for top active, 1-based
    4. (np.array): Cell ID, 2D 1-based

"""
SP_GW_MAPPING = dict()
"""Dictionary of mappings for defined springs in the area 
covered by the HSPF model.

Keys are a spring index and values are a list of descriptive values.

0. (str): target ID for this spring
1. (int): 2D cell ID, 1-based
2. (int): top active layer for spring location
3. (float): cell surface area
4. (str): spring name or label

"""
NUM_CPL = 0
"""Number of MODFLOW 6 cells in a layer.

Provides the array size for receiving from MODFLOW 6
"""
NUM_UZF = 0
"""Number of UZF MODFLOW 6 cells in the model.

Provides the array size for passing discharges to MODFLOW 6
"""
NUM_SPRINGS = 0
"""Number of spring locations that are represented by MODFLOW 6 drain
cells in the model.

Used to route discharge to ground surface appropriately.
"""
# coupling time series
GWIVOL = None
"""Volume of water coming into each RCHRES directly from MODFLOW 6 in af/day.
"""
GWOVOL = None
"""Volume of water sent to MODFLOW 6 as losses to groundwater for each
RCHRES in af/day.
"""
IGWOVOL = None
"""Volume of water sent to MODFLOW 6 as inflow to inactive groundwater 
for each PERLND in af/day.
"""
GWILZONE = None
"""MODFLOW discharge assigned to the lower zone in inches.
"""
GWIUZONE = None
"""MODFLOW discharge assigned to the upper zone in inches.
"""
GWIOVOL = None
"""MODFLOW discharge that becomes runoff and goes directly to a RCHRES in
acre-ft.

Includes spring discharge from DRN boundaries in MODFLOW 6
"""
GWITOTAL = None
"""Total inflow from MODFLOW discharge to HSPF in af/day.
"""
GWIUATOTAL = None
"""Total inflow from MODFLOW discharge that is outside of HSPF
area in af/day.
"""
GWOTOTAL = None
"""Total outflow to MODFLOW UZF in af/day"""
GWITOTPL = None
"""Total inflow from MODFLOW discharge in af/day by pervious HRU"""
GWITOTRR = None
"""Total inflow from MODFLOW discharge in af/day by RCHRES.

Does not include runoff from MODFLOW discharge to pervious lands.
"""


# -------------------------------------------------------------------
# coupling related methods
def setUpRRRecArrays( pwList, sim_len ):
    """ Create and initialize RCHRES coupling tracking arrays

    Args:
        pwList (list): list of IDs for this target type
        sim_len (int): number of output intervals in the simulation
    
    """
    # imports
    # globals
    global GWIVOL, GWOVOL, GWITOTAL, GWOTOTAL, GWITOTRR
    global GWIUATOTAL
    # parameters
    # locals
    # start
    typeLister = list()
    for tID in pwList:
        typeLister.append( ( tID, 'f4' ) )
    # end for
    DEF_DT = np.dtype( typeLister )
    TOT_DT = np.dtype( [ ("Total", 'f4' ) ] )
    # no initialize and allocate
    GWIVOL = np.rec.array( np.zeros( sim_len, dtype=DEF_DT ) )
    GWOVOL = np.rec.array( np.zeros( sim_len, dtype=DEF_DT ) )
    GWITOTRR = np.rec.array( np.zeros( sim_len, dtype=DEF_DT ) )
    GWITOTAL = np.rec.array( np.zeros( sim_len, dtype=TOT_DT ) )
    GWOTOTAL = np.rec.array( np.zeros( sim_len, dtype=TOT_DT ) )
    GWIUATOTAL = np.rec.array( np.zeros( sim_len, dtype=TOT_DT ) )
    # return
    return


def setUpPLRecArrays( pwList, sim_len ):
    """ Create and initialize pervious land, coupling tracking arrays.

    Args:
        pwList (list): list of IDs for this target type
        sim_len (int): number of output intervals in the simulation
    
    """
    # imports
    # globals
    global IGWOVOL, GWILZONE, GWIUZONE, GWIOVOL, GWITOTPL
    # parameters
    # locals
    # start
    typeLister = list()
    for tID in pwList:
        typeLister.append( ( tID, 'f4' ) )
    # end for
    DEF_DT = np.dtype( typeLister )
    # no initialize and allocate
    IGWOVOL = np.rec.array( np.zeros( sim_len, dtype=DEF_DT ) )
    GWILZONE = np.rec.array( np.zeros( sim_len, dtype=DEF_DT ) )
    GWIUZONE = np.rec.array( np.zeros( sim_len, dtype=DEF_DT ) )
    GWIOVOL = np.rec.array( np.zeros( sim_len, dtype=DEF_DT ) )
    GWITOTPL = np.rec.array( np.zeros( sim_len, dtype=DEF_DT ) )
    # return
    return


def processReceivedArray( tDict, iI, fromGWArray ):
    """Process the array of received, rejected infiltration and
    discharge to the ground surface. 
    
    Assumes that the received array is in m3/day.
    
    Args:
        tDict (dict): TARG_DICT from locaMain
        iI (int): current day, 0-based in the simulation
        fromGWArray (np.array): 1D array received from MODFLOW 6
                                dimension should be NCPL

    Returns:
        int: function status; 0 == success
    
    """
    # imports
    from locaMain import TARG_RCHRES, TARG_PERVLND
    # globals
    global RR_GW_MAPPING, PL_GW_MAPPING, SP_GW_MAPPING, GWITOTPL
    global GWITOTAL, GWITOTRR, GWIUATOTAL, GWIOVOL
    # parameters
    ConvM3toAF = 1.0 / 1233.48
    goodReturn = 0
    badReturn = -1
    # locals
    # get the totals and track total inflow and outflow volumes
    #  to MODFLOW 6
    mfDomTotal = fromGWArray.sum()
    mfDomTotalaf = mfDomTotal * ConvM3toAF
    # get the target dictionary for locaMain
    # springs
    SPKeys = sorted( SP_GW_MAPPING.keys() )
    for sKey in SPKeys:
        targID = SP_GW_MAPPING[sKey][0]
        # get the 2D Cell ID 1-based
        idLU = SP_GW_MAPPING[sKey][1]
        # change the array of indexes to 0-based indexes
        idLU0 = idLU - 1
        # get the total discharge from this spring
        totRegionm3 = float( fromGWArray[ idLU0 ] )
        # convert to acre-ft/day
        totRegionaf = totRegionm3 * ConvM3toAF
        if targID in tDict[ TARG_RCHRES ]:
            # then goes directly to a RCHRES
            # set the total tracker
            GWITOTRR[targID][iI] = float( GWITOTRR[targID][iI] ) + totRegionaf
            # now set the RCHRES inflow
            setIVOLfromGW( iI, targID, totRegionaf )
        elif targID in tDict[ TARG_PERVLND ]:
            # then goes into PERLND but route directly to runoff
            GWIOVOL[targID][iI] = float( GWIOVOL[targID][iI] ) + totRegionaf
            # add to the total PERLND accounting
            GWITOTPL[targID][iI] = float( GWITOTPL[targID][iI] ) + totRegionaf
        else:
            # for error checking
            errMsg = "Spring %d, targ ID of %s not found in TARG_DICT!!!" \
                     % ( sKey, targID )
            CL.LOGR.error( errMsg )
            return badReturn
        # end if
        # now clear out these values so no double counting
        fromGWArray[ idLU0 ] = 0.0
    # end for
    # RCHRES
    RRKeys = sorted( RR_GW_MAPPING.keys() )
    for rKey in RRKeys:
        idLU = RR_GW_MAPPING[rKey][1][0][0]
        # change the array of indexes to 0-based indexes
        idLU0 = idLU - 1
        # now get the total discharge in cubic meters per day
        # for the river valley
        totRegionm3 = fromGWArray[ idLU0 ].sum()
        # convert to acre-ft/day
        totRegionaf = totRegionm3 * ConvM3toAF
        # set the total tracker
        GWITOTRR[rKey][iI] = float( GWITOTRR[rKey][iI] ) + totRegionaf
        # now set the RCHRES inflow
        setIVOLfromGW( iI, rKey, totRegionaf )
        # now clear out these values so no double counting
        fromGWArray[ idLU0 ] = 0.0
    # end for rKey
    # then do PERLND
    PLKeys = sorted( PL_GW_MAPPING.keys() )
    for pKey in PLKeys:
        idLU = PL_GW_MAPPING[pKey][0][0]
        # change the array of indexes to 0-based indexes
        idLU0 = idLU - 1
        # now get the total discharge in cubic meters 
        # per day for the HRU
        totRegionm3 = fromGWArray[ idLU0 ].sum()
        # convert to acre-ft per day
        totRegionaf = totRegionm3 * ConvM3toAF
        # set the total tracker
        GWITOTPL[pKey][iI] = float( GWITOTPL[pKey][iI] ) + totRegionaf
        # set the soil moisture storage and runoff
        adjustPervWStorage( iI, pKey, totRegionaf )
        # now clear out these values so no double counting
        fromGWArray[ idLU0 ] = 0.0
    # end of pKey for
    # check that got all of the discharge allocated
    remSum = fromGWArray.sum()
    remSumaf = remSum * ConvM3toAF
    oaTotalIn = mfDomTotalaf - remSumaf
    GWITOTAL["Total"][iI] = float( GWITOTAL["Total"][iI] ) + oaTotalIn
    GWIUATOTAL["Total"][iI] = float( GWIUATOTAL["Total"][iI] ) + remSumaf
    # return
    return goodReturn


def calcSendArray( iI ):
    """Calculate the numpy array to send to MODFLOW 6.

    This array is 1D and has size/length == NUM_UZF. It provides
    the specified inflow/recharge rate for that day (day == iI) in
    m/day for the UZF package. It is calculated by adding
    first the RCHRES mappings to each cell and then the 
    PERLND mappings for each cell.

    Args:
        iI (int): current day, 0-based in the simulation

    Returns:
        numpy.array: NUZF array of m/day inflow to UZF surface for 
                     each cell
    
    """
    # imports
    from locaHyperwat import getIGWIbyTargTS
    # globals
    global NUM_UZF, RR_GW_MAPPING, PL_GW_MAPPING, GWOTOTAL, GWOVOL
    global IGWOVOL
    # parameters
    ConvAFtoM3 = 1233.48
    # locals
    toGWArray = np.zeros( NUM_UZF, dtype=np.float64 )
    # start with RCHRES
    RRKeys = sorted( RR_GW_MAPPING.keys() )
    for rKey in RRKeys:
        gwExit = RR_GW_MAPPING[rKey][0]
        if gwExit <= 0:
            continue
        idLU = RR_GW_MAPPING[rKey][1][1][0]
        arWgt = RR_GW_MAPPING[rKey][1][1][1]
        tcArea = RR_GW_MAPPING[rKey][1][1][2]
        # change the array of indexes to 0-based indexes
        idLU0 = idLU - 1
        # get the volume out of the RCHRES for the specified
        #  exit. This is in acre-ft per day
        afExVol = getOVOLbyExitandTime( iI, rKey, gwExit )
        # convert to meters cubed per day
        m3ExVol = afExVol * ConvAFtoM3
        # now add to our pass array
        toGWArray[ idLU0 ] = toGWArray[ idLU0 ] + ( ( arWgt * m3ExVol )
                                / tcArea )
        # add to our tracker
        GWOVOL[rKey][iI] = float( GWOVOL[rKey][iI] ) + afExVol
        GWOTOTAL["Total"][iI] = float( GWOTOTAL["Total"][iI] ) + afExVol
    # end for rKey
    # then do PERLND
    PLKeys = sorted( PL_GW_MAPPING.keys() )
    for pKey in PLKeys:
        idLU = PL_GW_MAPPING[pKey][1][0]
        arWgt = PL_GW_MAPPING[pKey][1][1]
        tcArea = PL_GW_MAPPING[pKey][1][2]
        # change the array of indexes to 0-based indexes
        idLU0 = idLU - 1
        # get the rate to UZF in acre feet per day
        afOVol = getIGWIbyTargTS( iI, pKey )
        # convert to meters cubed to day
        m3OVol = afOVol * ConvAFtoM3 
        # now add to our pass array
        toGWArray[ idLU0 ] = toGWArray[ idLU0 ] + ( ( arWgt * m3OVol ) 
                                / tcArea )
        # add to our tracker
        IGWOVOL[pKey][iI] = float( IGWOVOL[pKey][iI] ) + afOVol
        GWOTOTAL["Total"][iI] = float( GWOTOTAL["Total"][iI] ) + afOVol
    # end for
    # return
    return toGWArray


def mapSetup( tDict, ncpl, nuzf, rr_file, pl_file, sp_file ):
    """Create our mapping setup and check the passed information.

    Mapping files are passed in as paths to pickle files that contain
    a mapping dictionary. There are three mapping dictionaries.
    
    1. **RCHRES** dictionary, in rr_file, has keys that are the HSPF target 
    Id, i.e., 'R001'. The values are a list, L, with 3 items.

        0. (int): HSPF RCHRES exit that goes to groundwater. Must be > 1 and <= 5.

        1. (float): total UZF cell area in this target ID

        2. (pd.DataFrame): DataFrame that describes the UZF cell
        specifications within this target ID. The DataFrame index is the 2D 
        Cell ID, 1-based. The DataFrame has four columns.

            * "iuzno" (int): UZF cell ID, 1-based

            * "TopActive" (int): the top active layer for this model cell, 1-based

            * "SArea_m2" (float): surface area of this cell within the HSPF target 
                ID in m2

            * "Weight" (float): dimensionless weight for allocating flows from HSPF 
                to this cell. Should be > 0 and <= 100.0
    
    2. **PERLND** dictionrary, in pl_file, is similar to the RCHRES dictionary.
    The dictionary keys are the HSPF target Id, i.e., 'P001'. The values 
    are a list, L, with 2 items.

        0. (float): total UZF cell area in this target ID

        1. (pd.DataFrame): DataFrame that describes the UZF cell specifications 
        within this target ID. The DataFrame index is the 2D Cell ID, 1-based.
        The DataFrame has four columns.

            * "iuzno" (int): UZF cell ID, 1-based

            * "TopActive" (int): the top active layer for this model cell, 
                1-based

            * "SArea_m2" (float): surface area of this cell within the HSPF 
                target ID in m2

            * "Weight" (float): dimensionless weight for allocating flows from
                HSPF to this cell. Should be > 0 and <= 100.0

    3. **SPRING** dictionary, in sp_file, provides locations of the springs within
    the HSPF model that could be discharging to the ground surface. The 
    dictionary keys are the labels/names for the springs as represented in 
    the .drn and .drn.obs files. The values are lists, described below.

        0. (str): target ID for the HSPF location

        1. (int): 2D cell Id, 1-based, for the cell where the drain is placed

        2. (int): top active layer, 1-based, for the cell where the drain
            is placed

        3. (float): surface area for the cell where the drain is located

    The main outcome of this function is to fill in the module-level global
    mapping dictionaries (RR_GW_MAPPING, PL_GW_MAPPING, SP_GW_MAPPING). 
    These dictionaries have targID as keys and a list for values.

    1. **RR_GW_MAPPING** is a dictionary with Targ ID for keys and a list 
        for values.

        0. (int): groundwater exit index

        1. (list): sub-list holding another sub-list of arrays

            0. (list): with numpy.arrays with dimension NCPL as items

                0. (numpy.array): Cell ID, 2D 1-based

                1. (numpy.array): weighting factor

                2. (numpy.array): cell area within the target ID

                3. (numpy.array): Layer index for top active, 1-based

                4. (numpy.array): UZF index, 1-based

            1. (list): numpy.arrays with dimension NUZF as items

                0. (numpy.array): UZF index, 1-based

                1. (numpy.array): weighting factor

                2. (numpy.array): cell area within the target ID

                3. (numpy.array): Layer index for top active, 1-based

                4. (numpy.array): Cell ID, 2D 1-based

    2. **PL_GW_MAPPING** is a dictionary with Targ ID for keys and a list of
    values.

        0. (list): sub-list with numpy.arrays with dimension NCPL as items

            0. (numpy.array): Cell ID, 2D 1-based

            1. (numpy.array): weighting factor

            2. (numpy.array): cell area within the target ID

            3. (numpy.array): Layer index for top active, 1-based

            4. (numpy.array): UZF index, 1-based

        1. (list): np.arrays with dimension NUZF as items

            0. (numpy.array): UZF index, 1-based

            1. (numpy.array): weighting factor

            2. (numpy.array): cell area within the target ID

            3. (numpy.array): Layer index for top active, 1-based

            4. (numpy.array): Cell ID, 2D 1-based

    3. **SP_GW_MAPPING** is a dictionary with spring index, 1-based, as the
    keys and a list of values.

        0. (str): target ID for this spring

        1. (int): 2D cell ID, 1-based

        2. (int): top active layer for spring location

        3. (float): cell surface area

        4. (str): spring name/label

    Args:
        tDict (dict): TARG_DICT from locaMain
        ncpl (int): number of cells per layer in the MODFLOW 6 model
        nuzf (int): the number of UZF cells in the MODFLOW 6 model
        rr_file (str): fqdn path for file that has RCHRES mapping dictionary
        pl_file (str): fqdn path for file that has PERLND mapping dictionary
        sp_file (str): fqdn path for file that has SPRING mapping dictionary

    Returns:
        int: function status; 0 == success

    """
    # imports
    import pickle
    from locaMain import TARG_PERVLND, TARG_RCHRES
    # globals
    global RR_GW_MAPPING, PL_GW_MAPPING, SP_GW_MAPPING, NUM_CPL, NUM_UZF
    global NUM_SPRINGS
    # parameters
    goodReturn = 0
    badReturn = -1
    IUZNO_HDR = "iuzno"
    TA_HDR = "TopActive"
    AREA_HDR = "SArea_m2"
    WGT_HDR = "Weight"
    OUT_WS = "Outside"
    # locals
    # start
    # get the RCHRES dictionary from the pickle file
    with open( rr_file, 'rb' ) as InP:
        RR_Dict = pickle.load( InP )
    # end with and close file
    if type( RR_Dict ) != dict:
        # this is an error
        errMsg = "Unrecognized object type of %s for RCHRES mapping" % \
                 type( RR_Dict )
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    RRKeys = sorted( RR_Dict.keys() )
    # check that all keys are valid
    for rKey in RRKeys:
        if not rKey in tDict[TARG_RCHRES]:
            # this is an error
            errMsg = "Did not find %s in the list of known RCHRES!!!" % \
                     rKey
            CL.LOGR.error( errMsg )
            return badReturn
        # end if
    # end for
    # Now go through and make our mapping dictionary entries
    for rKey in RRKeys:
        gwExit = RR_Dict[rKey][0]
        totArea = RR_Dict[rKey][1]
        mDF = RR_Dict[rKey][2]
        if not AREA_HDR in mDF.columns:
            # this is an error
            errMsg = "Did not find %s in the columns of the mapping " \
                     "DataFrame for %s!!!" % ( AREA_HDR, rKey )
            CL.LOGR.error( errMsg )
            return badReturn
        if not IUZNO_HDR in mDF.columns:
            # this is an error
            errMsg = "Did not find %s in the columns of the mapping " \
                     "DataFrame for %s!!!" % ( IUZNO_HDR, rKey )
            CL.LOGR.error( errMsg )
            return badReturn
        if not TA_HDR in mDF.columns:
            # this is an error
            errMsg = "Did not find %s in the columns of the mapping " \
                     "DataFrame for %s!!!" % ( TA_HDR, rKey )
            CL.LOGR.error( errMsg )
            return badReturn
        if not WGT_HDR in mDF.columns:
            # this is an error
            errMsg = "Did not find %s in the columns of the mapping " \
                     "DataFrame for %s!!!" % ( WGT_HDR, rKey )
            CL.LOGR.error( errMsg )
            return badReturn
        # end if
        NCPLIndexer = np.array( mDF.index.tolist(), dtype=np.int32 )
        if ( ( NCPLIndexer.max() > ncpl ) or ( NCPLIndexer.min() <= 0 ) ):
            # errors
            errMsg = "Found cell Ids outside of acceptable range for " \
                     "RCHRES mapping, %s. Max cell Id is %d and min is " \
                     "%d. Found max of %d and min of %d." % \
                     ( rKey, ncpl, 1, NCPLIndexer.max(), NCPLIndexer.min() )
            CL.LOGR.error( errMsg )
            return badReturn
        # end if
        # first get the NCPL based list
        nciUZ = np.array( mDF[IUZNO_HDR].tolist(), dtype=np.int32 )
        ncTpAct = np.array( mDF[TA_HDR].tolist(), dtype=np.int32 )
        ncWeights = np.array( mDF[WGT_HDR].tolist(), dtype=np.float64 )
        totWeights = ncWeights.sum()
        ncArea = np.array( mDF[AREA_HDR].tolist(), dtype=np.float64 )
        ncWghtFactor = 0.5 * ( ( ncWeights / totWeights ) + 
                               ( ncArea / totArea ) )
        NCPLList = [ NCPLIndexer, ncWghtFactor, ncArea, ncTpAct, nciUZ ]
        # get the iuzno based list
        uzmDF = mDF[ mDF[IUZNO_HDR] > 0 ].copy()
        NUZIIndexer = np.array( uzmDF.index.tolist(), dtype=np.int32 )
        uziUZ = np.array( uzmDF[IUZNO_HDR].tolist(), dtype=np.int32 )
        if ( ( uziUZ.max() > nuzf ) or ( uziUZ.min() <= 0 ) ):
            # errors
            errMsg = "Found UZF Ids outside of acceptable range for " \
                     "RCHRES mapping, %s. Max UZF Id is %d and min is " \
                     "%d. Found max of %d and min of %d." % \
                     ( rKey, nuzf, 1, uziUZ.max(), uziUZ.min() )
            CL.LOGR.error( errMsg )
            return badReturn
        # end if
        uziTpAct = np.array( uzmDF[TA_HDR].tolist(), dtype=np.int32 )
        uziWeights = np.array( uzmDF[WGT_HDR].tolist(), dtype=np.float64 )
        uziTotWght = uziWeights.sum()
        uziArea = np.array( uzmDF[AREA_HDR].tolist(), dtype=np.float64 )
        uziTotArea = uziArea.sum()
        uziWghtFactor = 0.5 * ( ( uziWeights / uziTotWght ) + 
                                ( uziArea / uziTotArea ) )
        NUZIList = [ uziUZ, uziWghtFactor, uziArea, uziTpAct, NUZIIndexer ]
        # now add to our mapping directory
        RR_GW_MAPPING[rKey] = [ gwExit, [ NCPLList, NUZIList ] ]
    # end for rKey
    # next do the pervious land mapping
    # get the PERLND dictionary from the pickle file
    with open( pl_file, 'rb' ) as InP:
        PL_Dict = pickle.load( InP )
    # end with and close file
    if type( PL_Dict ) != dict:
        # this is an error
        errMsg = "Unrecognized object type of %s for PERLND mapping" % \
                 type( PL_Dict )
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    PLKeys = sorted( PL_Dict.keys() )
    # check that all keys are valid
    for pKey in PLKeys:
        if not pKey in tDict[TARG_PERVLND]:
            # this is an error
            errMsg = "Did not find %s in the list of known %s!!!" % \
                     ( pKey, TARG_PERVLND )
            CL.LOGR.error( errMsg )
            return badReturn
        # end if
    # end for
    # Now go through and make our mapping dictionary entries
    for pKey in PLKeys:
        totArea = PL_Dict[pKey][0]
        mDF = PL_Dict[pKey][1]
        if not AREA_HDR in mDF.columns:
            # this is an error
            errMsg = "Did not find %s in the columns of the mapping " \
                     "DataFrame for %s!!!" % ( AREA_HDR, pKey )
            CL.LOGR.error( errMsg )
            return badReturn
        # end if
        NCPLIndexer = np.array( mDF.index.tolist(), dtype=np.int32 )
        if ( ( NCPLIndexer.max() > ncpl ) or ( NCPLIndexer.min() <= 0 ) ):
            # errors
            errMsg = "Found cell Ids outside of acceptable range for " \
                     "PERLND mapping, %s. Max cell Id is %d and min is " \
                     "%d. Found max of %d and min of %d." % \
                     ( pKey, ncpl, 1, NCPLIndexer.max(), NCPLIndexer.min() )
            CL.LOGR.error( errMsg )
            return badReturn
        # end if
        # first get the NCPL based list
        nciUZ = np.array( mDF[IUZNO_HDR].tolist(), dtype=np.int32 )
        ncTpAct = np.array( mDF[TA_HDR].tolist(), dtype=np.int32 )
        ncWeights = np.array( mDF[WGT_HDR].tolist(), dtype=np.float64 )
        totWeights = ncWeights.sum()
        ncArea = np.array( mDF[AREA_HDR].tolist(), dtype=np.float64 )
        ncWghtFactor = 0.5 * ( ( ncWeights / totWeights ) + 
                               ( ncArea / totArea ) )
        NCPLList = [ NCPLIndexer, ncWghtFactor, ncArea, ncTpAct, nciUZ ]
        # get the iuzno based list
        uzmDF = mDF[ mDF[IUZNO_HDR] > 0 ].copy()
        NUZIIndexer = np.array( uzmDF.index.tolist(), dtype=np.int32 )
        uziUZ = np.array( uzmDF[IUZNO_HDR].tolist(), dtype=np.int32 )
        if ( ( uziUZ.max() > nuzf ) or ( uziUZ.min() <= 0 ) ):
            # errors
            errMsg = "Found UZF Ids outside of acceptable range for " \
                     "PERLND mapping, %s. Max UZF Id is %d and min is " \
                     "%d. Found max of %d and min of %d." % \
                     ( rKey, nuzf, 1, uziUZ.max(), uziUZ.min() )
            CL.LOGR.error( errMsg )
            return badReturn
        # end if
        uziTpAct = np.array( uzmDF[TA_HDR].tolist(), dtype=np.int32 )
        uziWeights = np.array( uzmDF[WGT_HDR].tolist(), dtype=np.float64 )
        uziTotWght = uziWeights.sum()
        uziArea = np.array( uzmDF[AREA_HDR].tolist(), dtype=np.float64 )
        uziTotArea = uziArea.sum()
        uziWghtFactor = 0.5 * ( ( uziWeights / uziTotWght ) + 
                                ( uziArea / uziTotArea ) )
        NUZIList = [ uziUZ, uziWghtFactor, uziArea, uziTpAct, NUZIIndexer ]
        # now add to our mapping directory
        PL_GW_MAPPING[pKey] = [ NCPLList, NUZIList ]
    # end for pKey
    # get the springs dictionary from the pickle file
    with open( sp_file, 'rb' ) as InP:
        SP_Dict = pickle.load( InP )
    # end with and close file
    if type( SP_Dict ) != dict:
        # this is an error
        errMsg = "Unrecognized object type of %s for SPRING mapping" % \
                 type( SP_Dict )
        CL.LOGR.error( errMsg )
        return badReturn
    # end if
    # make the springs dictionary
    springKeys = sorted( SP_Dict.keys() )
    iCnt = 1
    for sKey in springKeys:
        dVals = SP_Dict[ sKey ]
        if dVals[0] == OUT_WS:
            continue
        # end if
        dVals.append( sKey )
        SP_GW_MAPPING[iCnt] = dVals
        iCnt += 1
    # end for
    # do some checks
    nsprings = len( SP_GW_MAPPING )
    if len( SP_GW_MAPPING ) < 1:
        # no springs passed !!!
        warnMsg = "No spring locations extracted from %s !!!" % sp_file
        CL.LOGR.warning( warnMsg )
    else:
        # check the target IDs
        spKeys = sorted( SP_GW_MAPPING.keys() )
        for sKey in spKeys:
            targID = SP_GW_MAPPING[sKey][0]
            if ( ( not targID in tDict[TARG_PERVLND] ) and 
                        ( not targID in tDict[TARG_RCHRES] ) ):
                # this is an error because the location is unknown
                errMsg = "Unknown spring location of %s for spring " \
                         "%s !!!" % ( targID, SP_GW_MAPPING[sKey][4] )
                CL.LOGR.error( errMsg )
                return badReturn
            # end if
        # end for
    # if check
    # now assign our globals
    NUM_CPL = ncpl
    NUM_UZF = nuzf
    NUM_SPRINGS = nsprings
    # return
    return goodReturn


def getNUM_CPL():
    """Get the module level global NUM_CPL

    Requires that mapSetup has already been called

    Returns:
        int: NUM_CPL, number of MODFLOW 6 cells per layer
    
    """
    global NUM_CPL
    return NUM_CPL


def getNUM_UZF():
    """Get the module level global NUM_UZF

    Requires that mapSetup has already been called

    Returns:
        int: NUM_UZF, number of MODFLOW 6 cells per layer

    """
    global NUM_UZF
    return NUM_UZF


def getOVOLbyExitandTime( iI, targID, gwExit ):
    """Get the calculated OVOL for day, iI, and exit, gwExit

    Args:
        iI (int): index of current simulation day
        targID (str): ID for recarray columns
        gwExit (int): gw discharge exit

    Returns:
        float: exOvol, exit outflow volume in acre-ft per day

    """
    # imports
    from locaHrchhyd import getOVOLbyExit
    # globals
    # parameters
    # locals
    # start
    OVOL = getOVOLbyExit( gwExit )
    exOvol = float( OVOL[targID][iI] )
    # return
    return exOvol


def setIVOLfromGW( iI, targID, volAFpd ):
    """Set the external inflow volume value for inflow from 
    MODFLOW 6.

    Args:
        iI (int): index of current simulation day
        targID (str): ID for recarray columns
        volAFpd (float): volume in acre-ft/day

    """
    # imports
    # globals
    global GWIVOL
    # set
    GWIVOL[targID][iI] = volAFpd
    # return
    return


def getGWIVOLbyTargTS( iI, targID ):
    """Return the value for groundwater inflow to RCHRES by target ID and
    by time step index.

    Args:
        iI (int): index of current simulation day
        targID (str): ID for recarray columns
    
    Returns:
        float: ivol, inflow volume in acre-ft per day

    """
    # globals
    global GWIVOL
    # start
    ivol = float( GWIVOL[targID][iI] )
    # return
    return ivol


def getIGWIbyTS( iI, targID ):
    """Get inflow to inactive groundwater (IGWI) to pass to MODFLOW 6.

    Inflow to inactivate groundwater is stored in inches per 
    interval. Convert this to acre-ft per day before returning

    IGWI is the DEEPFR percentage of the inflow to groundwater
    from the Lower Zone. Inflow to groundwater is the total
    percolation from Upper Zone to Lower Zone plus the 
    infiltraton from the surface directly to the Lower Zone
    less the calculated Lower Zone inflow.

    Args:
        iI (int): current simulation day index, 0-based
        targID (str): current PERLND target
    
    Returns:
        float: oVol, outflow to UZF in acre-ft/day

    """
    # imports
    from locaHyperwat import getIGWIbyTargTS, getWatershedAreabyTarg
    # globals
    # parameters
    # locals
    # start - get the outflow to inactive groundwater which is inches
    oIgwi = getIGWIbyTargTS( iI, targID )
    # get the area in acres
    aArea = getWatershedAreabyTarg( targID )
    # calculate our volume in acre -ft
    oVol = ( oIgwi / 12.0 ) * aArea
    # return
    return oVol


def adjustPervWStorage( iI, targID, totVolafd ):
    """Adjust the pervious water storage to account for groundwater 
    discharged to the land surface in MODFLOW 6.

    The adjustment is implemented between time steps and so the
    adjustment results in addition to the lower zone and upper zone
    storages. The additions can only result in lower zone and upper
    zone storage that is less than or equal to the nominal storage
    capacity. If the additions, exceed what can be applied to
    lower and upper zone storage, the excess is routed to the
    appropriate stream segment or RCHRES target.

    **Note** that we need the current storage for the soil zones from
    time step iI - 1 as this is called at the beginning of the
    HSPF time loop, prior to the iI calculations.

    This should never be called for iI == 0. In the current formulation
    this is prevented by the if statement in locaMain, time loop.

    Args:
        iI (int): current simulation day index, 0-based
        targID (str): current PERLND target
        totVolafd (float): total volume in acre-ft per day to add
                           to the specified PERLND target
    
    """
    # imports
    from locaHyperwat import getWatershedAreabyTarg, getNominalStorages
    from locaHyperwat import getCurrentStorages, setCurrentStorages 
    # globals
    global GWILZONE, GWIUZONE, GWIOVOL
    # parameters
    smallVal = 1.0E-13
    # locals
    addLowerZone = float(0.0)  # amount in inches to add to lower zone
    addUpperZone = float(0.0)  # amount in inches to add to upper zone
    addRRin = float(0.0)       # amount in inches to add to outflow
    addRRaf = float(0.0)       # amount in acre-ft to add to outflow
    # start
    # get the area in acres
    aArea = getWatershedAreabyTarg( targID )
    # calculate the total volume in inches
    totVolin = ( totVolafd / aArea ) * 12.0
    if ( totVolin - 0.0 ) < smallVal:
        # nothing to do
        return
    # next get the lower and upper zone nominal storages
    uzsn, lzsn = getNominalStorages( targID )
    # now get the current storage volumes
    if iI < 1:
        piI = 1
    else:
        piI = iI 
    uzs, lzs = getCurrentStorages( piI, targID )
    # now do our calculations
    remVolin = totVolin
    lAvail = lzsn - lzs 
    if ( ( lAvail - 0.0 ) >= smallVal ):
        if ( ( remVolin - lAvail ) >= smallVal ):
            addLowerZone = lAvail
            remVolin = remVolin - lAvail
        else:
            addLowerZone = remVolin
            remVolin = 0.0
        # end inner if
    # end if lower zone storage available
    uAvail = uzsn - uzs 
    if ( ( ( uAvail - 0.0 ) >= smallVal ) and 
                ( ( remVolin - 0.0 ) >= smallVal ) ):
        # then add some to lower zone
        if ( ( remVolin - uAvail ) >= smallVal ):
            addUpperZone = uAvail
            remVolin = remVolin - uAvail
        else:
            addUpperZone = remVolin
            remVolin = 0.0
        # end inner if
    # end if upper zone storage is available
    # finally if we have an volume left to add to the watershed
    #   then we need to assign this to outflow to RCHRES
    if ( ( remVolin - 0.0 ) >= smallVal ):
        addRRin = remVolin
        remVolin = 0.0
    # end if remaining volume
    # now update our storages and tracking arrays
    addRRaf = ( addRRin / 12.0 ) * aArea
    GWILZONE[targID][iI] = addLowerZone
    GWIUZONE[targID][iI] = addUpperZone
    GWIOVOL[targID][iI] = addRRaf
    # update the storages
    setCurrentStorages( piI, targID, ( uzs + addUpperZone ), 
                        ( lzs + addLowerZone ) )
    # return
    return


def getGWIOVOLbyTargTS( iI, targID ):
    """Get the excess groundwater discharge from MODFLOW 6 that is routed
    to stream segments.
    
    This value returned in acre-ft/day

    Args:
        iI (int): current simulation day index, 0-based
        targID (str): current PERLND target

    Returns:
        float: oVolAF, outflow volume in acre-feet/day to streams

    """
    # global
    global GWIOVOL
    # 
    oVolAF = float( GWIOVOL[targID][iI] )
    # return
    return oVolAF


def writeOutputs( store, tIndex ):
    """Write the outputs to the hdf file at the end of the simulation

    Args:
        store (pandas.HDFStore): hdf5 file store to write to
        tIndex (pandas.DateIndex): time index for the simulation

    Returns:
        int: function status; 0 == success

    """
    # imports
    import pandas as pd
    # globals
    # perland
    global IGWOVOL, GWILZONE, GWIUZONE, GWIOVOL, GWITOTPL
    # rr
    global GWIVOL, GWOVOL, GWITOTRR
    # total
    global GWITOTAL, GWOTOTAL, GWIUATOTAL
    # parameters
    goodReturn = 0
    badReturn = -1
    pathStart = "/RESULTS"
    pathStartPL = "/RESULTS/PERLND_"
    pathStartRR = "/RESULTS/RCHRES_"
    pathEnd = "/COUPLED"
    # locals
    # start
    PervOut = [ "Mf6_Total", "Mf6_LZS", "Mf6_UZS", "Mf6_RO", "IGWO_Mf6" ]
    RrOut = [ "Mf6_Total", "Mf6_VOL", "OVOL_Mf6" ]
    # get the columns list for recarrays
    colsList = list( GWITOTPL.dtype.names )
    # go through pervious first
    for tCol in colsList:
        # get the path
        path = "%s%s%s" % ( pathStartPL, tCol, pathEnd )
        # create an empty DataFrame with a time index
        df = pd.DataFrame(index=tIndex)
        iCnt = 0
        for cOut in PervOut:
            if cOut == "Mf6_Total":
                outView = GWITOTPL[tCol].view( dtype=np.float32 )
                df[cOut] = outView
            elif cOut == "Mf6_LZS":
                outView = GWILZONE[tCol].view( dtype=np.float32 )
                df[cOut] = outView
            elif cOut == "Mf6_UZS":
                outView = GWIUZONE[tCol].view( dtype=np.float32 )
                df[cOut] = outView
            elif cOut == "Mf6_RO":
                outView = GWIOVOL[tCol].view( dtype=np.float32 )
                df[cOut] = outView
            elif cOut == "IGWO_Mf6":
                outView = IGWOVOL[tCol].view( dtype=np.float32 )
                df[cOut] = outView
            else:
                # this is an error - unsupported output
                errMsg = "Unsupported output type of %s!!!!" % cOut
                CL.LOGR.error( errMsg )
                return badReturn
            # end if
            # increment our counter
            iCnt += 1
        # end for output type
        # have the dataframe to save to our path
        store.put( path, df.astype( np.float32 ) )
    # end of column for
    # now do the RCHRES
    colsList = list( GWITOTRR.dtype.names )
    for tCol in colsList:
        # get the path
        path = "%s%s%s" % ( pathStartRR, tCol, pathEnd )
        # create an empty DataFrame with a time index
        df = pd.DataFrame(index=tIndex)
        iCnt = 0
        for cOut in RrOut:
            if cOut == "Mf6_Total":
                outView = GWITOTRR[tCol].view( dtype=np.float32 )
                df[cOut] = outView
            elif cOut == "Mf6_VOL":
                outView = GWIVOL[tCol].view( dtype=np.float32 )
                df[cOut] = outView
            elif cOut == "OVOL_Mf6":
                outView = GWOVOL[tCol].view( dtype=np.float32 )
                df[cOut] = outView
            else:
                # this is an error - unsupported output
                errMsg = "Unsupported output type of %s!!!!" % cOut
                CL.LOGR.error( errMsg )
                return badReturn
            # end if
            # increment our counter
            iCnt += 1
        # end for output type
        # have the dataframe to save to our path
        store.put( path, df.astype( np.float32 ) )
    # end of column for
    # finall do the totals
    outView = GWOTOTAL["Total"].view( dtype=np.float32 )
    inView = GWITOTAL["Total"].view( dtype=np.float32 )
    exInView = GWIUATOTAL["Total"].view( dtype=np.float32 )
    path = "%s%s" % ( pathStart, pathEnd )
    df = pd.DataFrame(index=tIndex)
    df["Tot_from_Mf6_toWS"] = inView
    df["Tot_from_Mf6_toOutSide"] = exInView
    df["Tot_to_Mf6"] = outView
    store.put( path, df.astype( np.float32 ) )
    # return
    return goodReturn


#EOF