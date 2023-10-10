! Copyright and License
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
! Copyright 2021 Southwest Research Institute
! 
! Module Author: Nick Martin <nick.martin@alumni.stanford.edu>
! 
! This file is part of pyHS2MF6.
! 
! pyHS2MF6 is free software: you can redistribute it and/or modify
! it under the terms of the GNU Affero General Public License as published by
! the Free Software Foundation, either version 3 of the License, or
! (at your option) any later version.
! 
! pyHS2MF6 is distributed in the hope that it will be useful,
! but WITHOUT ANY WARRANTY; without even the implied warranty of
! MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
! GNU Affero General Public License for more details.
! 
! You should have received a copy of the GNU Affero General Public License
! along with pyHS2MF6.  If not, see <https://www.gnu.org/licenses/>.
!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
module f2pwrap
!====================================================================
! MODFLOW 6, version 6.2.1
! Collection of wrappers needed to reproduce the Program modules
!   statements in Python. These subroutines are compiled to a pyd
!   module so that can be imported into Python. In the pyd compilation
!   a DLL composed of all MF6 compiled object code will be linked
!   so that full executable MF6 versions is created.
! 
! mf6core.f90 is identical between 6.2.0 and 6.2.1.
!====================================================================
! SPECIFICATIONS:
  ! ---------------------------------------------------------------
  ! -- modules
  use KindModule,             only: DP, I4B
  use Mf6CoreModule,          only: printInfo, simulation_ar, simulation_df,   &
                                    Mf6DoTimestep, Mf6FinalizeTimestep,        &
                                    Mf6Finalize, Mf6PrepareTimestep
  use BaseModelModule,        only: BaseModelType, GetBaseModelFromList
  use BaseExchangeModule,     only: BaseExchangeType, GetBaseExchangeFromList
  use BaseSolutionModule,     only: BaseSolutionType, GetBaseSolutionFromList
  use SolutionGroupModule,    only: SolutionGroupType, GetSolutionGroupFromList
  use ListsModule,            only: basesolutionlist, solutiongrouplist,       &
                                    basemodellist, baseexchangelist  
  implicit none
  !
  private
  public :: setup
  public :: cphsetup
  public :: objsetup
  public :: innertimeloop
  public :: finalproc
  public :: cphfinalproc
  public :: cphdeallocall
  public :: cphfinal_message
  public :: cphprint_final_message
  public :: cphconverge_check
  public :: gettotim
  public :: gettotalsimtime
  public :: cphinnertimeloop
  
  contains
  
  subroutine setup()
!====================================================================
! Does all of the set-up things for MODFLOW 6 prior to object
!    allocation and creation.
!====================================================================
    use SimulationCreateModule,     only: simulation_cr
    ! local
    
    !    LOGIC: lines 45 - 67 of mf6.f90, ver 6.1.0
    !    LOGIC: Mf6Initialize() in Mf6CoreModule, ver 6.1.1 but 
    !             cannot do GetCommandLineArguments() and
    !             simulation_df() and simulation_ar() are in objsetup()
    ! ---------------------------------------------------------------
    ! -- parse any command line arguments
    ! call GetCommandLineArguments()
    !
    ! -- print banner and info to screen
    call printInfo()
    !
    ! -- CREATE (CR)
    call simulation_cr()
    ! end
    ! --Return
    return 
    !
  end subroutine setup


  subroutine cphsetup()
!====================================================================
! Does all of the set-up things for MODFLOW 6 prior to object
!    allocation and creation. This particular version is for running
!    the coupled model and so use the simulation create from the
!    special coupled model type
!====================================================================
    use cphSimulationCreateModule,    only: cphsimulation_cr
    ! local
    
    !    LOGIC: lines 45 - 67 of mf6.f90
    !    LOGIC: Mf6Initialize() in Mf6CoreModule, ver 6.1.1
    !    v6.2.0 logic same as v6.1.1
    ! ---------------------------------------------------------------
    ! -- parse any command line arguments
    ! call GetCommandLineArguments()
    !
    ! -- print banner and info to screen
    call printInfo()
    ! -- CREATE (CR)
    call cphsimulation_cr()
    ! end
    ! --Return
    return 
    !
  end subroutine cphsetup


  subroutine objsetup()
!====================================================================
! Setup the objects of various types for the main time loop
!====================================================================
    
    !    LOGIC: lines 71-107 of mf6.f90, v6.1.0
    !    LOGIC: simulation_df() and simulation_ar() of mf6core.f90, v6.1.1
    !    v6.2.0 logic same as v6.1.1
    !
    ! -- define
    call simulation_df()
    !
    ! -- allocate and read
    call simulation_ar()
    !
    !-- Return
    return
    !
  end subroutine objsetup


  subroutine innertimeloop( ioutlocal )
!====================================================================
! Within time step logic after the call to tdis
! v6.2.0 logic is identical to v6.1.1
! In version 6.1.1 this logic, including tdis is in Mf6PrepareTimestep(),
!     Mf6DoTimestep(), and Mf6FinalizeTimestep() which are called by 
!     Mf6Update().
! LOGIC - lines 116-162 of mf6.f90, version 6.1.0
!====================================================================
    ! -- dummy
    integer, intent(out) :: ioutlocal
    ! -- local
    logical :: hasConverged
    !
    ! -- READ AND PREPARE (RP)
    call Mf6PrepareTimestep()
    !
    ! -- CALCULATE (CA); call Mf6DoTimestep
    call Mf6DoTimestep()
    !
    ! time step evaluation and output using Mf6FinalizeTimestep
    hasConverged = Mf6FinalizeTimestep()
    !
    ! convert to an integer
    if (hasConverged) then
      ioutlocal = 0
    else
      ioutlocal = 1
    end if
    !
    !--Return
    return
    !
  end subroutine innertimeloop


  subroutine finalproc( ioutlocal )
!====================================================================
! Final processing after the main time loop is over.
! v6.2.0 logic identical to v6.1.1
! In ver 6.1.1, just call Mf6Finalize() which takes care of final
!   processing and deallocation. 
! In ver 6.1.0, used two subroutines one for final processing and
!   one for deallocation. For coupled simulation still need to do
!   this because have some "new" deallocation.
!====================================================================
    implicit none
    ! -- dummy arguments
    integer, intent(out) :: ioutlocal
    !
    ioutlocal = 1
    !
    call Mf6Finalize()
    ! 
    ioutlocal = 0
    !
    ! -- Return
    return
    !
  end subroutine finalproc


  subroutine cphfinalproc( ioutlocal )
!====================================================================
! Coupled final processing after the main time loop is over.
! In ver 6.1.1, just call Mf6Finalize() which takes care of final
!   processing and deallocation. 
! In ver 6.1.0, used two subroutines one for final processing and
!   one for deallocation.
! For coupled simulation still need to do this because have some 
!   "new" deallocation and new to be able to customize it
!====================================================================
    ! -- dummy arguments
    implicit none
    integer, intent(out) :: ioutlocal
    ! locals
    integer(I4B) :: im
    integer(I4B) :: ic
    integer(I4B) :: is
    class(BaseSolutionType), pointer :: sp => null()
    class(BaseModelType), pointer :: mp => null()
    class(BaseExchangeType), pointer :: ep => null()
    !
    ioutlocal = 1
    !
    ! -- FINAL PROCESSING (FP)
    ! -- Final processing for each model
    do im = 1, basemodellist%Count()
        mp => GetBaseModelFromList(basemodellist, im)
        call mp%model_fp()
    enddo
    !
    ! -- Final processing for each exchange
    do ic = 1, baseexchangelist%Count()
        ep => GetBaseExchangeFromList(baseexchangelist, ic)
        call ep%exg_fp()
    enddo
    !
    ! -- Final processing for each solution
    do is=1,basesolutionlist%Count()
        sp => GetBaseSolutionFromList(basesolutionlist, is)
        call sp%sln_fp()
    enddo
    ! 
    ioutlocal = 0
    !
    !-- Return
    return
    !
  end subroutine cphfinalproc


  subroutine cphdeallocall( )
!====================================================================
! Coupled mode deallocation of all of our allocatables
!====================================================================
    use TdisModule,                 only: tdis_da
    use ListsModule,                only: lists_da
    use SimModule,                  only: final_message
    use MemoryManagerModule,        only: mem_write_usage, mem_da
    use TimerModule,                only: elapsed_time   
    use SimVariablesModule,         only: iout
    use cphSimulationCreateModule,  only: cphsimulation_da
    ! implicit none
    implicit none
    ! -- dummy arguments
    ! -- local
    integer(I4B) :: im
    integer(I4B) :: ic
    integer(I4B) :: is
    integer(I4B) :: isg
    class(SolutionGroupType), pointer :: sgp => null()
    class(BaseSolutionType), pointer :: sp => null()
    class(BaseModelType), pointer :: mp => null()
    class(BaseExchangeType), pointer :: ep => null()
    !
    !  LOGIC, lines 195-223
    ! -- DEALLOCATE (DA)
    ! -- Deallocate tdis
    call tdis_da()
    !
    ! -- Deallocate for each model
    do im = 1, basemodellist%Count()
        mp => GetBaseModelFromList(basemodellist, im)
        call mp%model_da()
        deallocate(mp)
    enddo
    !
    ! -- Deallocate for each exchange
    do ic = 1, baseexchangelist%Count()
        ep => GetBaseExchangeFromList(baseexchangelist, ic)
        call ep%exg_da()
        deallocate(ep)
    enddo
    !
    ! -- Deallocate for each solution
    do is=1,basesolutionlist%Count()
        sp => GetBaseSolutionFromList(basesolutionlist, is)
        call sp%sln_da()
        deallocate(sp)
    enddo
    !
    ! -- Deallocate solution group and simulation variables
    do isg = 1, solutiongrouplist%Count()
        sgp => GetSolutionGroupFromList(solutiongrouplist, isg)
        call sgp%sgp_da()
        deallocate(sgp)
    enddo
    !
    call cphsimulation_da()
    call lists_da()
    !
    ! -- Write memory usage, elapsed time and terminate
    call mem_write_usage(iout)
    call mem_da()
    call elapsed_time(iout, 1)
    call cphfinal_message()
    ! 
    ! -- Return
    return
    !
  end subroutine cphdeallocall


  subroutine cphfinal_message()
! ******************************************************************************
! Coupled model only - important to override this so that control returns
!   to Python at the end for clean closure.
!
! Create the appropriate final message and terminate the program
! ******************************************************************************
!
!    SPECIFICATIONS:
! ------------------------------------------------------------------------------
    ! -- modules
    use GenericUtilitiesModule,   only: sim_message
    use SimVariablesModule,       only: isimcnvg, numnoconverge, ireturnerr, iout 
    use ConstantsModule,          only: LINELENGTH
    ! -- local
    character(len=LINELENGTH) :: line
    ! -- formats
    character(len=*), parameter :: fmtnocnvg =                                 &
      "(1x, 'Simulation convergence failure occurred ', i0, ' time(s).')"
! ------------------------------------------------------------------------------
    !
    ! -- Write message if any nonconvergence
    if(numnoconverge > 0) then
      write(line, fmtnocnvg) numnoconverge
      call sim_message(line, iunit=iout)
      call sim_message(line)
    endif
    !
    if(isimcnvg == 0) then
      ireturnerr = 1
      call cphprint_final_message('Premature termination of simulation.', iout)
    else
      call cphprint_final_message('Normal termination of simulation.', iout)
    endif
    !
    ! -- Return or halt
    !if (iforcestop == 1) then
    !  call stop_with_error(ireturnerr)
    !end if
    ! -- Return
    return
    !
  end subroutine cphfinal_message


  subroutine cphprint_final_message(stopmess, ioutlocal)
! ******************************************************************************
! Coupled model only - needed to allow control to return back to Python. Have
!    to remove a bit of the functionality because cannot access the message
!    types from here.
!
! Print a final message and close all open files
! ******************************************************************************
!
!    SPECIFICATIONS:
! ------------------------------------------------------------------------------
    use GenericUtilitiesModule,   only: sim_message
    use SimVariablesModule,       only: iout, iunext
    use ConstantsModule,          only: IUSTART
    ! -- dummy
    character, optional, intent(in) :: stopmess*(*)
    integer(I4B),   optional, intent(in) :: ioutlocal  
    ! -- local
    character(len=*), parameter :: fmt = '(1x,a)'
    character(len=*), parameter :: msg = 'Stopping due to error(s)'
    integer(I4B) :: i
    logical :: opened
    !---------------------------------------------------------------------------
    !
    ! -- print the accumulated messages; cannot access these from here
    !call sim_notes%print_message('NOTES:', 'note(s)',                              &
    !                              iunit=iout, level=VALL)
    !call sim_warnings%print_message('WARNING REPORT:', 'warning(s)',               &
    !                                iunit=iout, level=VALL)
    !call sim_errors%print_message('ERROR REPORT:', 'error(s)', iunit=iout)
    !call sim_uniterrors%print_message('UNIT ERROR REPORT:',                        &
    !                                  'file unit error(s)', iunit=iout)
    !
    ! -- write a stop message, if one is passed 
    if (present(stopmess)) then
      if (stopmess.ne.' ') then
        call sim_message(stopmess, fmt=fmt, iunit=iout)
        call sim_message(stopmess, fmt=fmt)
        if (present(ioutlocal)) then
          if (ioutlocal > 0 .and. ioutlocal /= iout) then
            write(ioutlocal,fmt) trim(stopmess)
            close (ioutlocal)
          endif
        endif
      endif
    endif
    !
    ! -- determine if an error condition has occurred
    !if (sim_errors%count_message() > 0) then
    !  ireturnerr = 2
    !  if (iout > 0) then
    !    call sim_message(stopmess, fmt=fmt, iunit=iout)
    !  end if
    !  call sim_message(stopmess, fmt=fmt)
    !  
    !  if (present(ioutlocal)) then
    !    if (ioutlocal > 0 .and. ioutlocal /= iout) write(ioutlocal,fmt) msg
    !  endif
    !endif
    !
    ! -- close all open files
    ! call sim_closefiles()
    ! Add this functionality here because sim_closefiles() is not public
    ! -- close all open file units
    do i = IUSTART, iunext - 1
      !
      ! -- determine if file unit i is open
      inquire(unit=i, opened=opened)
      !
      ! -- skip file units that are no longer open
      if(.not. opened) then
        cycle
      end if
      !
      ! -- close file unit i
      close(i)
    end do
    !
    ! -- return
    return
    !
  end subroutine cphprint_final_message


  subroutine cphconverge_check(iexLoop)
! ***************************************************************
! Coupled model convergence check. Run as a subroutine
!   after cphinnertimeloop so that can pass the array back to
!   Python in cphinnertimeloop
! ***************************************************************
!
!    SPECIFICATIONS:
! ---------------------------------------------------------------
    ! -- modules
    use SimModule,              only: converge_check
    ! -- dummy
    integer, intent(out) :: iexLoop
    ! -- format
    character(len=*), parameter :: fmtfail =                                   &
      "(1x, 'Simulation convergence failure.',                                 &
        &' Simulation will terminate after output and deallocation.')"
! ------------------------------------------------------------------------------
    ! locals
    logical :: hasConverged
    !
    ! -- Check if we're done
    call converge_check(hasConverged)
    ! convert to an integer
    if (hasConverged) then
      iexLoop = 0
    else
      iexLoop = 1
    end if
    !
    ! -- Return
    return
    ! 
  end subroutine cphconverge_check


  subroutine gettotim( mftotim )
! ***************************************************************
! Get the MODFLOW 6 totim variable which has the current 
! simulation time.
! ***************************************************************
!
!    SPECIFICATIONS:
! ---------------------------------------------------------------
    use TdisModule,     only: totim
    ! -- dummy
    real(kind=8), intent(out) :: mftotim
    ! 
    mftotim = totim
    !
    ! -- Return
    return
    !
  end subroutine gettotim

    
  subroutine gettotalsimtime( mftotsim )
! ***************************************************************
! Get the MODFLOW 6 totalsimtime variable which has the total
!  simulation time
! ***************************************************************
!
!    SPECIFICATIONS:
! ---------------------------------------------------------------
    use TdisModule,     only: totalsimtime
    ! -- dummy
    real(kind=8), intent(out) :: mftotsim
    ! 
    mftotsim = totalsimtime
    !
    ! -- Return
    return
    !
  end subroutine gettotalsimtime
    

  subroutine cphinnertimeloop( finf, iuzno, ncpl, surfdis )
!====================================================================
! within time step logic after the call to tdis
! This is the version to use for coupled models
!     In terms of arguments, surfdis is to be returned or out only
!         surfdis(2, ncpl) where row index 1 is for discharge to the
!                      surface. Discharge comes from UZF groundwater
!                      discharge and from DRN discharge
!                      Row index 2 is for rejected infiltration
!====================================================================
    ! use statements
    use cphGwfModule,           only: cphGwfModelType
    use TdisModule,             only: tdis_tu, kstp, kper
    use ConstantsModule,        only: LINELENGTH, MNORMAL, MVALIDATE
    use SimModule,              only: converge_reset
    use SimVariablesModule,     only: isim_mode
    ! -- dummy arguments
    ! Need to use kind=8 rather than DP here because of f2py limitations
    implicit none
    integer, intent(in) :: iuzno
    integer, intent(in) :: ncpl
    real(kind=8), dimension(iuzno), intent(in) :: finf
    real(kind=8), dimension(2, ncpl), intent(out) :: surfdis
    ! -- locals
    real(DP), dimension(iuzno) :: cpinarr
    real(DP), dimension(2, ncpl) :: psdischarge
    integer(I4B) :: cpinalen
    integer(I4B) :: numnodes
    integer(I4B) :: im
    integer(I4B) :: ic
    integer(I4B) :: is
    character(len=LINELENGTH) :: line
    character(len=LINELENGTH) :: fmt
    class(BaseSolutionType), pointer :: sp => null()
    class(BaseModelType), pointer :: mp => null()
    class(BaseExchangeType), pointer :: ep => null()
    ! assign our locals
    cpinarr = 0.0 
    psdischarge = 0.0 
    cpinalen = iuzno
    numnodes = ncpl
    ! because we can't use DP, go through and transfer the input arguments
    !  to the appropriately typed array
    do im = 1, cpinalen
      cpinarr(im) = finf(im)
    end do
    !
    ! set our initial value for surfdis
    surfdis = 0.0
    ! LOGIC - Mf6PrepareTimestep
    !
    ! -- initialize fmt
    fmt = "(/,a,/)"
    ! -- time update
    call tdis_tu()
    !
    ! -- set base line
    write(line, '(a,i0,a,i0,a)')                                                 &
      'start timestep kper="', kper, '" kstp="', kstp, '" mode="'
    !
    ! -- evaluate simulation mode
    select case (isim_mode)
      case (MVALIDATE)
        line = trim(line) // 'validate"'
      case(MNORMAL)
        line = trim(line) // 'normal"'
    end select
    !
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
    !
    ! -- Read and prepare each exchange
    do ic = 1, baseexchangelist%Count()
      ep => GetBaseExchangeFromList(baseexchangelist, ic)
      call ep%exg_rp()
    end do
    !
    ! -- Read and prepare each solution
    ! Only used in v 6.1.0
    !do is=1,basesolutionlist%Count()
    !  sp => GetBaseSolutionFromList(basesolutionlist, is)
    !  call sp%sln_rp()
    !end do
    ! -- reset simulation convergence flag
    call converge_reset()
    !
    ! end of Mf6PrepareTimestep
    !
    ! -- CALCULATE (CA) - use Mf6DoTimestep()
    call Mf6DoTimestep()
    !
    ! Next have logic from Mf6FinalizeTimestep()
    !
    ! -- initialize format and line
    line = 'end timestep'
    !
    ! -- evaluate simulation mode
    ! -- OUTPUT (OT)
    select case (isim_mode)
      case(MVALIDATE)
        !
        ! -- Write final message for timestep for each model 
        do im = 1, basemodellist%Count()
          mp => GetBaseModelFromList(basemodellist, im)
          call mp%model_message(line, fmt=fmt)
        end do
      case(MNORMAL)
        !
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
        !
        ! -- Write output for each exchange
        do ic = 1, baseexchangelist%Count()
          ep => GetBaseExchangeFromList(baseexchangelist, ic)
          call ep%exg_ot()
        enddo
        !
        ! -- Write output for each solution
        do is=1,basesolutionlist%Count()
          sp => GetBaseSolutionFromList(basesolutionlist, is)
          call sp%sln_ot()
        enddo
    end select
    !
    ! now need to assign our psdicharge values to our return
    surfdis(:, :) = psdischarge(:, :)
    !
    return
    !
  end subroutine cphinnertimeloop


end module f2pwrap
