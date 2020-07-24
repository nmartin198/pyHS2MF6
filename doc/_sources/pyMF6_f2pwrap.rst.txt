.. _pyMF6_f2pwrap_f:

Module **f2pwrap** in f2pWrappers.f90
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Special module to replace MODFLOW 6 main program block and to provide
for array passing logic. The array passing provides for dynamic 
coupling between MODFLOW 6 and HSPF as information is exchanged for 
each simulation day.


**Module** :f:mod:`f2pwrap`

.. f:module:: f2pwrap 
    :synopsis: Python version of MODFLOW 6 main program block


.. f:subroutine:: setup()

    Does all of the set-up things for MODFLOW 6 prior to object allocation 
    and creation.

    :from: :py:func:`pyMF6py.saMF6TimeLoop`

    :to:
        * `printInfo() in Mf6CoreModule`
        * `simulation_cr() in SimulationCreateModule`


.. f:subroutine:: cphsetup()

    Does all of the set-up things for MODFLOW 6 prior to object allocation
    and creation. This particular version is for running the coupled 
    model and so use the simulation create from the special coupled model
    type.

    :from: :py:func:`pyMF6py.MF6TimeLoop`

    :to: 
        * `printInfo() in Mf6CoreModule`
        * `cphsimulation_cr() in cphSimulationCreateModule`


.. f:subroutine:: objsetup()

    Setup the objects of various types for the main time loop

    :from: 
        * :py:func:`pyMF6py.saMF6TimeLoop`
        * :py:func:`pyMF6py.MF6TimeLoop`

    :to:
        * `simulation_df() in Mf6CoreModule`
        * `simulation_ar() in Mf6CoreModule`


.. f:subroutine:: innertimeloop( ioutlocal )

    Provides all of the within time step logic for a standalone simulation.
    Directly employs the subroutines in the *mfcore.f90* file.

    :param integer ioutlocal[out]: convergence status; 0 == converged

    :from: :py:func:`pyMF6py.saMF6TimeLoop`

    :to: 
        * `Mf6PrepareTimestep() in Mf6CoreModule`
        * `Mf6DoTimestep() in Mf6CoreModule`
        * `Mf6FinalizeTimestep() in Mf6CoreModule`


.. f:subroutine:: finalproc( ioutlocal )

    Calls the required processing, deallocation and messaging, after the 
    main time loop is over. Standalone simulation only. Custom extended
    types are not used in standalone simulation so that the standard 
    MODFLOW 6 deallocation and wrap-up routines can be used.

    :param integer ioutlocal[out]: function status; 0 == success

    :from: :py:func:`pyMF6py.saMF6TimeLoop` 

    :to: `Mf6Finalize() in Mf6CoreModule`


.. f:subroutine:: cphfinalproc( ioutlocal )

    Calls the required final model, exchange, and solution processing 
    after the main time loop is over. Coupled simulation only. The 
    coupled version is more involved than the standalone because 
    have *new* deallocation from the new types and so have to customize 
    many of the subroutines called from *mfcore.f90* to implement
    individual pieces of larger routines.

    :param integer ioutlocal[out]: function status; 0 == success

    :from: :py:func:`pyMF6py.MF6TimeLoop`


.. f:subroutine:: cphdeallocall()

    Deallocation subroutine needed for coupled mode. Custom deallocation 
    had to be added to include dealloc for the extended types.

    :from: :py:func:`pyMF6py.MF6TimeLoop`

    :to:
        * `tdis_da() in TdisModule`
        * `cphsimulation_da() in cphSimulationCreateModule`
        * `lists_da() in ListsModule`
        * `mem_write_usage() in MemoryManagerModule`
        * `mem_da() in MemoryManagerModule`
        * `elapsed_time() in TimerModule`
        * :f:subr:`cphfinal_message()`


.. f:subroutine:: cphfinal_message()

    Override of the final message output functionality so that **stop** 
    is not called within MODFLOW and control returns to **pyMF6** for 
    normal program termination.

    :from: :f:subr:`cphdeallocall`

    :to: 
        * :f:subr:`cphprint_final_message`
        * `sim_message() in GenericUtilitiesModule`


.. f:subroutine:: cphprint_final_message( stopmess, ioutlocal )

    Override of the print_final_message() because this is where the **stop** 
    is called within MODFLOW. This routine called by cphfinal_message(), 
    and the purpose of this routine is to allow control to return 
    to **pyMF6** for normal program termination. **Note** that the end 
    of simulation listing of warnings (related to changes in parameters 
    between v.6.1.0 and 6.1.1) will not be printed for coupled simulation 
    because these output routines are not public in the MODFLOW code 
    base.

    :param character stopmess(*)[in]: message for output

    :param integer ioutlocal[in]: file output unit number

    :from: :f:subr:`cphfinal_message`

    :to: `sim_message() in GenericUtilitiesModule`


.. f:subroutine:: cphconverge_check( iexLoop )

    Coupled model convergence check. Designed to be called independently 
    at the end of the inner time loop logic in coupled simulation. This 
    routine had to split out so that custom array passing logic could be
    used to couple the programs. 

    :param integer iexLoop[out]: convergence flag, 0 means converged

    :from: :py:func:`pyMF6py.MF6TimeLoop` 

    :to: `converge_check() in SimModule`


.. f:subroutine:: gettotim( mftotim )

    Get the MODFLOW 6 public totim which holds the total elapsed 
    simulation time. 

    :param float mftotim[out]: elapsed simulation time

    :from: 
        * :py:func:`pyMF6py.MF6TimeLoop`
        * :py:func:`pyMF6py.saMF6TimeLoop` 

    :to: `totim in TdisModule`


.. f:subroutine:: gettotalsimtime( mftotsim )

    Get the MODFLOW 6 public totalsimtime which holds the total 
    simulation time. 

    :param float mftotsim[out]: total simulation time

    :from: 
        * :py:func:`pyMF6py.MF6TimeLoop`
        * :py:func:`pyMF6py.saMF6TimeLoop` 

    :to: `totalsimtime in TdisModule`


.. f:subroutine:: cphinnertimeloop( finf, iuzno, ncpl, surfdis )

    Within simulation time step logic for coupled model simulation. 
    Provides for receipt of a one-dimensional array of **iuzno** 
    length that has infiltration for the UZF package from HSPF. Also
    returns a one-dimensional array of **ncpl** length that has 
    groundwater discharge to the surface for each two-dimensional 
    grid cell.

    This routine is necessary to call the custom extended types that
    are used to implement coupling for MODFLOW 6. Fortran 
    `Select Type <https://software.intel.com/content/www/us/en/develop/documentation/fortran-compiler-developer-guide-and-reference/top/language-reference/a-to-z-reference/s-1/select-type.html>`_ 
    statements are used to call the extended logic for coupling. 
    This statement is used for model read and prepare ::

        ! -- READ AND PREPARE (RP)
        ! -- Read and prepare each model
        do im = 1, basemodellist%Count()
        mp => GetBaseModelFromList(basemodellist, im)
        call mp%model_message(line, fmt=fmt)
        ! select type
        select type (mp)
            type is (cphGwfModelType)
            call mp%gwf_chprp( cpinalen, cpinarr )
            class default
            call mp%model_rp()
        end select
        end do

    and for collating solution values at the end of a timestep. ::

        ! -- Write output and final message for timestep for each model 
        do im = 1, basemodellist%Count()
          mp => GetBaseModelFromList(basemodellist, im)
          ! select type
          select type (mp)
          type is (cphGwfModelType)
            call mp%model_ot()
            call mp%cphsurfdis( psdischarge, numnodes )
          class default
            call mp%model_ot()
          end select
          call mp%model_message(line, fmt=fmt)
        enddo


    :param integer iuzno[in]: NUZFCELL or number of UZF package cells

    :param integer ncpl[in]: NCPL or number of cells in a layer

    :param float finf(iuzno)[in]: fixed infiltration rate for the current day 

    :param surfdis(2, ncpl)[out]: groundwater discharge to the surface for 
        each computational cell 

        1. UZF groundwater discharge and DRN discharge

        2. UZF rejected infiltration
    
    :from: :py:func:`pyMF6py.MF6TimeLoop` 
    
    :to:
        * `gwf_chprp in cphGwfModule`
        * `cphsurfdis in cphGwfModule`
        * `tdis_tu() in TdisModule`
        * `converge_reset() in SimModule`
        * `Mf6DoTimestep() in Mf6CoreModule`

