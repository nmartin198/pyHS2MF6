.. _pyMF6_m6exts_f:

Extended MODFLOW 6 Types
=========================

The type extensions involve little new code. Mostly this functionality 
is implemented by making copies of existing MODFLOW 6 modules and 
renaming the modules, types, and subroutines to avoid issues with 
having the same names for types and subroutines that use different
types.

Documentation and comments are only provided for the modified portions
of these four modules.



.. _pyMF6_cphSimulationCreateModule_f:

**cphSimulationCreateModule** in cp_SimulationCreate.f90
---------------------------------------------------------

Copy of MODFLOW 6, v.6.1.1 SimulationCreateModule that has been slightly 
extended to provde for coupled mode simulation with HSPF. There are really 
only three modifications or extensions to this module.

    1. simulation_cr() replaced cphsimulation_cr() so that this module provides 
        a unique name for simulation object creation 
    
    2. simulation_da() replaced by cphsimulation_da() so that this module 
        provides a unique name for simulation object deallocation
    
    3. cphgwf_cr() from cphGwfModule is used in models_create() so that extended 
        type GWF models are created and used for coupled simulation.


**Module** :f:mod:`cphSimulationCreateModule`

.. f:module:: cphSimulationCreateModule
    :synopsis: Provides a modified simulation creation module that utilizes
        the new type extensions


.. f:subroutine:: cphsimulation_cr()

    Reads the simulation name file and initializes the models and exchanges.
    Only the name has changed and no functionality altered.

    :from: :f:subr:`f2pwrap/cphsetup`

    :to:
        * `getunit in InputOutputModule`
        * `sim_message in GenericUtilitiesModule`
        * `write_simulation_header in` :f:mod:`cphSimulationCreateModule`
        * `read_simulation_namefile in` :f:mod:`cphSimulationCreateModule`


.. f:subroutine:: cphsimulation_da()

    Deallocates simulation variables. Only the name is changed and no 
    functionality altered.

    :from: :f:subr:`f2pwrap/cphdeallocall`


.. f:subroutine:: models_create()

    Create model objects for the simulation. Only modification is to use
    cphgwf_cr from cphGwfModule for groundwater flow model (GWF) creation.

    :from: `read_simulation_namefile in cphSimlationCreateModule`

    :to: :f:subr:`cphGwfModule/cphgwf_cr`



.. _pyMF6_cphGwfModule_f:

**cphGwfModule** in cp_gwf3.f90
-----------------------------------------------------

Copy of MODFLOW 6, v.6.1.1 GwfModule that has been slightly extended 
to provde for coupled mode simulation with HSPF. There are really 
only five modifications or extensions.

    1. GwfModelType replaced cphGwfModelType so that the types can 
        coexist in pyMF6
 
    2. gwf_cr() replaced by cphgwf_cr() to ensure that this version of 
        create is only called for coupled
    
    3. package_create() subroutine has been extended to create 
        :f:type:`cphUzfModule/cphUzfType` UZF packages and 
        :f:type:`cphDrnModule/cphDrnType` DRN packages.

    3. Added gwf_chprp() for groundwater model read and prepare. The 
        original gwf_rp is maintained. gwf_chprp provides for passing in 
        of the array of UZF infiltration to the model from an external process. 
        It also calls the modified UZF type that is customized to deal with 
        receiving this array each simulation day.

    4. Added cphsurfdis() to extract simulated groundwater discharges to 
        the surface for the just simulated time step. This includes DRN 
        package discharge, UZF seepage to surface, and UZF rejected 
        infiltration.


**Module** :f:mod:`cphGwfModule`

.. f:module:: cphGwfModule
    :synopsis: Provides a modified GWF type that can receive and send 
            arrays to external processes


.. f:type:: cphGwfModelType

    GWF model type that extended to provide for receiving an array of 
    infiltration at the start of each simulation day and returning an 
    array of groundwater discharge to the surface at the end of each 
    simulation day.


.. f:subroutine:: cphgwf_cr( filename, id, modelname, smr )

    Create a new groundwater flow model object and add it to the internal 
    list of models. Also assign the values for this model object. This 
    routine is unchanged, just renamed.

    :param character filename(*)[in]: name file
    :param integer id[in]: model identifier
    :param character modelname(*)[in]: model name string 
    :param logical smr[in]: is a single model run?

    :to: :f:subr:`package_create`

    :from: :f:subr:`cphSimulationCreateModule/models_create`


.. f:subroutine:: package_create(this, filtyp, ipakid, ipaknum, pakname, inunit, iout)

    Create boundary condition packages for the GWF model. Uses the same
    parameters and is unchanged except for creation of 
    :f:type:`cphUzfModule/cphUzfType` and :f:type:`cphDrnModule/cphDrnType` 
    packages.

    :to:
        * :f:subr:`cphUzfModule/cphuzf_create`
        * :f:subr:`cphDrnModule/cphdrn_create`
    
    :from: :f:subr:`cphgwf_cr`


.. f:subroutine:: gwf_chprp( this, cpinalen, cpinarr )

    Modified GroundWater Flow Model (GWF) read and prepare which calls 
    package read and prepare routines. Main modification is to receive 
    an array from HSPF and a length for this array and then pass the 
    array to the modified UZF package.

    :param `cphGwfModelType` this[in]: self

    :param integer cpinalen[optional, in]: length of the cpinarr array, NUZFCELLS
    
    :param float cpinarr(cpinalen)[optional, in]: array of fixed infiltration rates

    :to: :f:subr:`cphUzfModule/cphuzf_rp`

    :from: :f:subr:`f2pwrap/cphinnertimeloop`


.. f:subroutine:: cphsurfdis( this, surfd, numnodes2d ) 

    Extract all simulated discharges to the ground surface and compile 
    these to an array representing a layer surface. This array is returned
    to the calling program for passing to an external process. The array
    is calculated from DRN discharge, UZF seepage, and UZF rejected 
    infiltration.

    :param `cphGwfModelType` this[in]: self

    :param float surf2d(2, numnodes2d)[inout]: array of cell discharge values

        1. UZF groundwater discharge and DRN discharge

        2. UZF rejected infiltration
    
    :param integer numnodes2d[in]: number of cells in a layer, NCPL

    :to:
        * :f:subr:`cphUzfModule/cphuzf_exsdis`
        * :f:subr:`cphDrnModule/cphdrn_exsdis`

    :from: :f:subr:`f2pwrap/cphinnertimeloop`



.. _pyMF6_cphUzfModule_f:

**cphUzfModule** in cp_gwf3uzf8.f90
-----------------------------------------------------

Copy of MODFLOW 6, v.6.1.1 UzfModule that has been slightly extended to 
provde for coupled mode simulation with HSPF. There are really only 
four modifications or extensions.

    1. UzfType replaced cphUzfType so that the types can coexist in pyMF6 
    
    2. uzf_create() replaced by cphuzf_create() to ensure that this version
        of create is only called for coupled
    
    3. Added cphuzf_rp for package read and prepare. The original uzf_rp is 
        maintained. cphuzf_rp provides for passing in of the array of UZF 
        infiltration to the model from an external process. These 
        infiltration values are then written into the time series inputs 
        for the current day.

    4. Added cphuzf_exsdis() to extract simulated groundwater discharges to
        the surface for the just simulated time step. This includes UZF 
        seepage to surface and UZF rejected infiltration.


**Module** :f:mod:`cphUzfModule`

.. f:module:: cphUzfModule
    :synopsis: Provides a modified UZF package that can receive infiltration
            from HSPF and send groundwater discharge to HSPF


.. f:type:: cphUzfType

    UZF package type that extended to provide for receiving an array of 
    infiltration at the start of each simulation day and returning an 
    array of groundwater discharge to the surface at the end of each 
    simulation day.


.. f:subroutine:: cphuzf_create(packobj, id, ibcnum, inunit, iout, namemodel, pakname)

    Create a new UZF boundary forcing package for the GWF model at the start 
    of the simulation. The subroutine is unchanged, including parameters, but is
    extended to use the coupled model UZF type.

    :from: :f:subr:`cphGwfModule/package_create`


.. f:subroutine:: cphuzf_rp( this, cpinalen, cpinarr )

    New subroutine based on uzf_rp that puts the infiltration from HSPF 
    into the sinf values location so that will be incorporated into the 
    time step solution for the current day. Does this every simulation day.

    :param `cphUzfType` this[in]: self

    :param integer cpinalen[optional, in]: length of the cpinarr array, NUZFCELLS
    
    :param float cpinarr(cpinalen)[optional, in]: array of fixed infiltration rates

    :from: :f:subr:`cphGwfModule/gwf_chprp`


.. f:subroutine:: cphuzf_exsdis( this, surfd, numnodes2d )

    New subroutine for coupling to HSPF. It provides an extension to 
    extract surface discharges. Both groundwater seepage discharge and 
    rejected infiltration are collated from the UZF solution for the current 
    time step.

    :param `cphUzfType` this[in]: self

    :param float surf2d(2, numnodes2d)[inout]: array of cell discharge values

        1. UZF groundwater discharge and DRN discharge

        2. UZF rejected infiltration
    
    :param integer numnodes2d[in]: number of cells in a layer, NCPL

    :from: :f:subr:`cphGwfModule/cphsurfdis`



.. _pyMF6_cphDrnModule_f:

**cphDrnModule** in cp_gwf3drn8.f90
-----------------------------------------------------

Copy of MODFLOW 6, v.6.1.1 DRN Module that has been slightly extended 
to provide for coupled mode simulation with HSPF. There are really only
three modifications or extensions.

    1. DrnType replaced cphDrnType so that the types can coexist in pyMF6 

    2. drn_create() replaced by cphdrn_create() to ensure that this version 
        of create is only called for coupled
    
    3. Added cphdrn_exsdis() to extract simulated groundwater discharges to 
        the surface for the just simulated time step.


**Module** :f:mod:`cphDrnModule`

.. f:module:: cphDrnModule
    :synopsis: Provides a modified DRN package that send groundwater 
            discharge to HSPF


.. f:type:: cphDrnType

    DRN package type that extended to provide for returning an 
    array of groundwater discharge to the surface at the end of each 
    simulation day.


.. f:subroutine:: cphdrn_create(packobj, id, ibcnum, inunit, iout, namemodel, pakname)

    Create a new DRN boundary forcing package for the GWF model at the start 
    of the simulation. The subroutine is unchanged, including parameters, but is
    extended to use the coupled model DRN type.

    :from: :f:subr:`cphGwfModule/package_create`


.. f:subroutine:: cphdrn_exsdis( this, surfd, numnodes2d )

    New subroutine for coupling to HSPF. It provides an extension to 
    extract surface discharges. DRN package discharge is added to the
    array that returned to the external process.

    :param `cphDrnType` this[in]: self

    :param float surf2d(2, numnodes2d)[inout]: array of cell discharge values

        1. UZF groundwater discharge and DRN discharge

        2. UZF rejected infiltration
    
    :param integer numnodes2d[in]: number of cells in a layer, NCPL

    :from: :f:subr:`cphGwfModule/cphsurfdis`

