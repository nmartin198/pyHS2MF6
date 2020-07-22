module f2pwrap
!====================================================================
! Collection of wrappers needed to reproduce the Program modules
!   statements in Python. These subroutines are compiled to a pyd
!   module so that can be imported into Python. In the pyd compilation
!   a DLL composed of all MF6 compiled object code will be linked
!   so that full executable MF6 versions is created.
!====================================================================
! SPECIFICATIONS:
  ! ---------------------------------------------------------------
  ! -- modules
  use KindModule,             only: DP, I4B
  use ConstantsModule,        only: ISTDOUT
  use VersionModule,          only: VERSION, MFVNAM, MFTITLE, FMTDISCLAIMER,   & 
                                    IDEVELOPMODE
  use CompilerVersion
  use InputOutputModule,      only: write_centered
  use SimulationCreateModule, only: simulation_cr, simulation_da
  use cphSimulationCreateModule, only: cphsimulation_cr, cphsimulation_da
  use TimerModule,            only: start_time, elapsed_time
  use MemoryManagerModule,    only: mem_usage, mem_da
  use BaseModelModule,        only: BaseModelType, GetBaseModelFromList
  use BaseExchangeModule,     only: BaseExchangeType, GetBaseExchangeFromList
  use BaseSolutionModule,     only: BaseSolutionType, GetBaseSolutionFromList
  use SolutionGroupModule,    only: SolutionGroupType, GetSolutionGroupFromList
  use ListsModule,            only: basesolutionlist, solutiongrouplist,       &
                                    basemodellist, baseexchangelist,           &
                                    lists_da
  use SimVariablesModule,     only: iout 
  use SimModule,              only: converge_reset, converge_check
  use SimModule,              only: ustop
  use TdisModule,             only: tdis_tu, tdis_da
  use cphGwfModule,           only: cphGwfModelType
  
  implicit none
  !
  private
  public :: setup
  public :: cphsetup
  public :: objsetup
  public :: innertimeloop
  public :: cphinnertimeloop
  public :: finalproc
  public :: deallocall
  public :: cphdeallocall
  public :: fwraps
  public :: pytdistu
  public :: getendsim
  public :: f2pconverge_check
  public :: pyfinal_message
  public :: pyustop
  
  ! local
  ! -- local
  class(SolutionGroupType), pointer :: sgp => null()
  class(BaseSolutionType), pointer :: sp => null()
  class(BaseModelType), pointer :: mp => null()
  class(BaseExchangeType), pointer :: ep => null()
  integer(I4B) :: im, ic, is, isg
  character(len=80) :: compiler
  
  contains
  
  subroutine setup
!====================================================================
! Does all of the set-up things for MODFLOW 6 prior to object
!    allocation and creation.
!====================================================================
    ! local
    
    !    LOGIC: lines 45 - 67 of mf6.f90
    ! ---------------------------------------------------------------
    ! -- parse any command line arguments
    ! call GetCommandLineArguments()
    !
    ! -- Write banner to screen (unit 6) and start timer
    call write_centered('MODFLOW'//MFVNAM, ISTDOUT, 80)
    call write_centered(MFTITLE, ISTDOUT, 80)
    call write_centered('VERSION '//VERSION, ISTDOUT, 80)
    !
    ! -- Write if develop mode
    if (IDEVELOPMODE == 1) call write_centered('***DEVELOP MODE***', &
                                              ISTDOUT, 80)
    !
    ! -- Write compiler version
    call get_compiler(compiler)
    call write_centered(' ', ISTDOUT, 80)
    call write_centered(trim(adjustl(compiler)), ISTDOUT, 80)
    !
    ! -- Write disclaimer
    write(ISTDOUT, FMTDISCLAIMER)
    ! -- get start time
    call start_time()
    !
    !
    ! -- CREATE (CR)
    call simulation_cr()
    ! end
  end subroutine setup


  subroutine cphsetup
!====================================================================
! Does all of the set-up things for MODFLOW 6 prior to object
!    allocation and creation. This particular version is for running
!    the coupled model
!====================================================================
    ! local
    
    !    LOGIC: lines 45 - 67 of mf6.f90
    ! ---------------------------------------------------------------
    ! -- parse any command line arguments
    ! call GetCommandLineArguments()
    !
    ! -- Write banner to screen (unit 6) and start timer
    call write_centered('MODFLOW'//MFVNAM, ISTDOUT, 80)
    call write_centered(MFTITLE, ISTDOUT, 80)
    call write_centered('VERSION '//VERSION, ISTDOUT, 80)
    !
    ! -- Write if develop mode
    if (IDEVELOPMODE == 1) call write_centered('***DEVELOP MODE***', &
                                                ISTDOUT, 80)
    !
    ! -- Write compiler version
    call get_compiler(compiler)
    call write_centered(' ', ISTDOUT, 80)
    call write_centered(trim(adjustl(compiler)), ISTDOUT, 80)
    !
    ! -- Write disclaimer
    write(ISTDOUT, FMTDISCLAIMER)
    ! -- get start time
    call start_time()
    !
    !
    ! -- CREATE (CR)
    call cphsimulation_cr()
    ! end
  end subroutine cphsetup


  subroutine objsetup
!====================================================================
! Setup the objects of various types for the main time loop
!====================================================================
    
    !    LOGIC: lines 71-107 of mf6.f90
    !
    ! -- DEFINE (DF)
    ! -- Define each model
    do im = 1, basemodellist%Count()
        mp => GetBaseModelFromList(basemodellist, im)
        call mp%model_df()
    enddo
    !
    ! -- Define each exchange
    do ic = 1, baseexchangelist%Count()
        ep => GetBaseExchangeFromList(baseexchangelist, ic)
        call ep%exg_df()
    enddo
    !
    ! -- Define each solution
    do is = 1, basesolutionlist%Count()
        sp => GetBaseSolutionFromList(basesolutionlist, is)
        call sp%sln_df()
    enddo
    !
    !
    ! -- ALLOCATE AND READ (AR)
    ! -- Allocate and read each model
    do im = 1, basemodellist%Count()
        mp => GetBaseModelFromList(basemodellist, im)
        call mp%model_ar()
    enddo
    !
    ! -- Allocate and read each exchange
    do ic = 1, baseexchangelist%Count()
        ep => GetBaseExchangeFromList(baseexchangelist, ic)
        call ep%exg_ar()
    enddo
    !
    ! -- Allocate and read each solution
    do is=1,basesolutionlist%Count()
        sp => GetBaseSolutionFromList(basesolutionlist, is)
        call sp%sln_ar()
    enddo
    !
  end subroutine objsetup


  subroutine innertimeloop
!====================================================================
! within time step logic after the call to tdis
!====================================================================
    ! LOGIC - lines 116-162 of mf6.f90
     !
    ! -- READ AND PREPARE (RP)
    ! -- Read and prepare each model
    do im = 1, basemodellist%Count()
      mp => GetBaseModelFromList(basemodellist, im)
      call mp%model_rp()
    enddo
    !
    ! -- Read and prepare each exchange
    do ic = 1, baseexchangelist%Count()
      ep => GetBaseExchangeFromList(baseexchangelist, ic)
      call ep%exg_rp()
    enddo
    !
    ! -- Read and prepare each solution
    do is=1,basesolutionlist%Count()
      sp => GetBaseSolutionFromList(basesolutionlist, is)
      call sp%sln_rp()
    enddo
    !
    ! -- CALCULATE (CA)
    call converge_reset()
    do isg = 1, solutiongrouplist%Count()
      sgp => GetSolutionGroupFromList(solutiongrouplist, isg)
      call sgp%sgp_ca()
    enddo
    !
    !
    ! -- OUTPUT (OT)
    ! -- Write output for each model
    do im = 1, basemodellist%Count()
      mp => GetBaseModelFromList(basemodellist, im)
      call mp%model_ot()
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
    !
  end subroutine innertimeloop


  subroutine finalproc( ioutlocal )
!====================================================================
! Final processing after the main time loop is over
!====================================================================
    ! -- dummy arguments
    implicit none
    integer, intent(out) :: ioutlocal
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
  end subroutine finalproc


  subroutine deallocall( ioutlocal )
!====================================================================
! Deallocation of all of our allocatables
!====================================================================
    ! -- dummy arguments
    implicit none
    integer, intent(out) :: ioutlocal
    !
    ioutlocal = 1
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
    call simulation_da()
    call lists_da()
    !
    ioutlocal = 0
    !
  end subroutine deallocall


  subroutine cphdeallocall( ioutlocal )
!====================================================================
! Deallocation of all of our allocatables
!====================================================================
    ! -- dummy arguments
    implicit none
    integer, intent(out) :: ioutlocal
    !
    ioutlocal = 1
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
    ioutlocal = 0
    !
  end subroutine cphdeallocall


  subroutine fwraps( ioutlocal )
!====================================================================
! Final wrap up items
!====================================================================
    ! -- dummy arguments
    implicit none
    integer, intent(out) :: ioutlocal
    ! locals
    integer :: pfinalpass
    ! initialize
    ioutlocal = 1
    pfinalpass = 1
    ! LOGIC from lines 225-230
    !
    ! -- Calculate memory usage, elapsed time and terminate
    call mem_usage(iout)
    call mem_da()
    call elapsed_time(iout, 1)
    call pyfinal_message( pfinalpass )
    ! 
    ioutlocal = pfinalpass
    !
  end subroutine fwraps

  subroutine pytdistu
!====================================================================
! wrapper for calling tdis_tu to do a time update
!====================================================================
    call tdis_tu()
    !
  end subroutine pytdistu

  subroutine getendsim( endsim )
!====================================================================
! Get the logical for if at the end of simulation
!====================================================================
!
!   SPECIFICATIONS:
!--------------------------------------------------------------------
    ! ! -- modules
    use TdisModule, only: endofsimulation
    ! dummy reference variables
    integer, intent(out) :: endsim 
    !
    ! now get our values
    if (endofsimulation) then
        endsim = 0
    else
        endsim = 1
    end if
    ! now return
  end subroutine getendsim

  subroutine f2pconverge_check(iexLoop)
! ***************************************************************
! f2Py version of converge_check
! ***************************************************************
!
!    SPECIFICATIONS:
! ---------------------------------------------------------------
    ! -- modules
    use SimVariablesModule, only: isimcnvg, numnoconverge, isimcontinue
    ! -- dummy
    integer, intent(out) :: iexLoop
    ! -- format
    character(len=*), parameter :: fmtfail =                                   &
      "(1x, 'Simulation convergence failure.',                                 &
        &' Simulation will terminate after output and deallocation.')"
! ------------------------------------------------------------------------------
    ! locals
    logical :: exit_tsloop
    !
    ! -- Initialize
    exit_tsloop = .false.
    !
    ! -- Count number of failures
    if(isimcnvg == 0) numnoconverge = numnoconverge + 1
    !
    ! -- Continue if 'CONTINUE' specified in simulation control file
    if(isimcontinue == 1) then
      if(isimcnvg == 0) then
        isimcnvg = 1
      endif
    endif
    !
    ! --
    if(isimcnvg == 0) then
      write(iout, fmtfail)
      exit_tsloop = .true.
    endif
    ! convert to an integer
    if (exit_tsloop) then
      iexLoop = 1
    else
      iexLoop = 0
    end if
    !
    ! -- Return
    return
    ! 
  end subroutine f2pconverge_check

  subroutine pyfinal_message( ioutlocal )
! ******************************************************************************
! Python compatible version of final_message
! ******************************************************************************
!
!    SPECIFICATIONS:
! ------------------------------------------------------------------------------
    ! -- modules
    use SimVariablesModule, only: isimcnvg, numnoconverge, ireturnerr
    ! -- dummy arguments
    implicit none
    integer, intent(inout) :: ioutlocal
    ! -- formats
    character(len=*), parameter :: fmtnocnvg =                                 &
      "(1x, 'Simulation convergence failure occurred ', i0, ' time(s).')"
    character(len=*), parameter :: nrmterm =                                   &
      "(1x, 'Normal termination of MODFLOW 6 simulation.')"
    character(len=*), parameter :: prmterm =                                   &
      "(1x, 'Premature termination of MODFLOW 6 simulation.')"
! ------------------------------------------------------------------------------
    !
    ! -- Write message if any nonconvergence
    if(numnoconverge > 0) then
      write(*, fmtnocnvg) numnoconverge
      write(iout, fmtnocnvg) numnoconverge
    endif
    !
    if(isimcnvg == 0) then
      ireturnerr = 1
      write(*, prmterm )
      !write( iout, prmterm )
      !call pyustop('Premature termination of simulation.', iout)
    else
      write(*, nrmterm )
      !write( iout, nrmterm )
      !call pyustop('Normal termination of simulation.', iout)
    endif
    !
    ioutlocal = 0
    ! -- Return
    return
  end subroutine pyfinal_message

  subroutine pyustop( stopmess, ioutlocal )
!====================================================================
! wrapper for calling USTOP from Python if needed
!====================================================================
    ! -- dummy arguments
    implicit none
    character, optional, intent(in) :: stopmess*(*)
    integer, optional, intent(in) :: ioutlocal
    ! now call USTOP
    call ustop( stopmess, ioutlocal )
    !
  end subroutine pyustop 


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
    ! LOGIC - lines 116-162 of mf6.f90
    ! -- READ AND PREPARE (RP)
    ! -- Read and prepare each model
    do im = 1, basemodellist%Count()
      mp => GetBaseModelFromList(basemodellist, im)
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
    do is=1,basesolutionlist%Count()
      sp => GetBaseSolutionFromList(basesolutionlist, is)
      call sp%sln_rp()
    end do
    !
    ! -- CALCULATE (CA)
    call converge_reset()
    do isg = 1, solutiongrouplist%Count()
      sgp => GetSolutionGroupFromList(solutiongrouplist, isg)
      call sgp%sgp_ca()
    end do
    !
    !
    ! -- OUTPUT (OT)
    ! -- Write output for each model
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
    end do
    !
    ! -- Write output for each exchange
    do ic = 1, baseexchangelist%Count()
      ep => GetBaseExchangeFromList(baseexchangelist, ic)
      call ep%exg_ot()
    end do
    !
    ! -- Write output for each solution
    do is=1,basesolutionlist%Count()
      sp => GetBaseSolutionFromList(basesolutionlist, is)
      call sp%sln_ot()
    end do
    ! now need to assign our psdicharge values to our return
    surfdis(:, :) = psdischarge(:, :)
    !do im = 1, numnodes
    !  surfdis(im) = psdischarge(im)
    !end do
    !
    return
    !
  end subroutine cphinnertimeloop


end module f2pwrap
