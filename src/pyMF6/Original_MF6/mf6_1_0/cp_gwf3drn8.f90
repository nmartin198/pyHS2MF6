module cphDrnModule
  use KindModule, only: DP, I4B
  use ConstantsModule, only: DZERO, LENFTYPE, LENPACKAGENAME
  use BndModule, only: BndType
  use ObsModule, only: DefaultObsIdProcessor
  use TimeSeriesLinkModule, only: TimeSeriesLinkType, &
                                  GetTimeSeriesLinkFromList
  !
  implicit none
  !
  private
  public :: cphdrn_create
  public :: cphDrnType
  !
  character(len=LENFTYPE)       :: ftype = 'DRN'
  character(len=LENPACKAGENAME) :: text  = '             DRN'
  !
  type, extends(BndType) :: cphDrnType
  contains
    procedure :: bnd_options => drn_options
    procedure :: bnd_ck => drn_ck
    procedure :: bnd_cf => drn_cf
    procedure :: bnd_fc => drn_fc
    procedure :: define_listlabel
    ! -- methods for observations
    procedure, public :: bnd_obs_supported => drn_obs_supported
    procedure, public :: bnd_df_obs => drn_df_obs
    ! -- method for time series
    procedure, public :: bnd_rp_ts => drn_rp_ts
    ! -- method for coupled model
    procedure :: cphdrn_exsdis
  end type cphDrnType

contains

  subroutine cphdrn_create(packobj, id, ibcnum, inunit, iout, namemodel, pakname)
! ******************************************************************************
! drn_create -- Create a New Drn Package
! Subroutine: (1) create new-style package
!             (2) point packobj to the new package
! ******************************************************************************
!
!    SPECIFICATIONS:
! ------------------------------------------------------------------------------
    ! -- dummy
    class(BndType), pointer :: packobj
    integer(I4B),intent(in) :: id
    integer(I4B),intent(in) :: ibcnum
    integer(I4B),intent(in) :: inunit
    integer(I4B),intent(in) :: iout
    character(len=*), intent(in) :: namemodel
    character(len=*), intent(in) :: pakname
    ! -- local
    type(cphDrnType), pointer :: drnobj
! ------------------------------------------------------------------------------
    !
    ! -- allocate the object and assign values to object variables
    allocate(drnobj)
    packobj => drnobj
    !
    ! -- create name and origin
    call packobj%set_names(ibcnum, namemodel, pakname, ftype)
    packobj%text = text
    !
    ! -- allocate scalars
    call drnobj%allocate_scalars()
    !s
    ! -- initialize package
    call packobj%pack_initialize()
    !
    ! -- initialize
    packobj%inunit=inunit
    packobj%iout=iout
    packobj%id=id
    packobj%ibcnum = ibcnum
    packobj%ncolbnd=2  ! drnelev, conductance
    packobj%iscloc=2   !sfac applies to conductance
    packobj%ictorigin = 'NPF'
    !
    ! -- return
    return
  end subroutine cphdrn_create

  subroutine drn_options(this, option, found)
! ******************************************************************************
! drn_options -- set options specific to DrnType
!
! drn_options overrides BndType%bnd_options
! ******************************************************************************
!
!    SPECIFICATIONS:
! ------------------------------------------------------------------------------
    use InputOutputModule, only: urword
    ! -- dummy
    class(cphDrnType),   intent(inout) :: this
    character(len=*), intent(inout) :: option
    logical,          intent(inout) :: found
    ! -- local
! ------------------------------------------------------------------------------
    !
    select case (option)
      case('MOVER')
        this%imover = 1
        write(this%iout, '(4x,A)') 'MOVER OPTION ENABLED'
        found = .true.
      case default
        !
        ! -- No options found
        found = .false.
    end select
    !
    ! -- return
    return
  end subroutine drn_options

  subroutine drn_ck(this)
! ******************************************************************************
! drn_ck -- Check drain boundary condition data
! ******************************************************************************
!
!    SPECIFICATIONS:
! ------------------------------------------------------------------------------
    ! -- modules
    use ConstantsModule, only: LINELENGTH
    use SimModule, only: ustop, store_error, count_errors, store_error_unit
    ! -- dummy
    class(cphDrnType),intent(inout) :: this
    ! -- local
    character(len=LINELENGTH) :: errmsg
    integer(I4B) :: i
    integer(I4B) :: node
    real(DP) :: bt
    ! -- formats
    character(len=*), parameter :: fmtdrnerr = &
      "('DRN BOUNDARY (',i0,') ELEVATION (',f10.3,') IS LESS THAN CELL " // &
      "BOTTOM (',f10.3,')')"
! ------------------------------------------------------------------------------
    !
    ! -- check stress period data
    do i = 1, this%nbound
        node = this%nodelist(i)
        bt = this%dis%bot(node)
        ! -- accumulate errors
        if (this%bound(1,i) < bt .and. this%icelltype(node) /= 0) then
          write(errmsg, fmt=fmtdrnerr) i, this%bound(1,i), bt
          call store_error(errmsg)
        end if
    end do
    !
    ! -- write summary of drain package error messages
    if (count_errors() > 0) then
      call store_error_unit(this%inunit)
      call ustop()
    end if
    !
    ! -- return
    return
  end subroutine drn_ck

  subroutine drn_cf(this)
! ******************************************************************************
! drn_cf -- Formulate the HCOF and RHS terms
! Subroutine: (1) skip if no drains
!             (2) calculate hcof and rhs
! ******************************************************************************
!
!    SPECIFICATIONS:
! ------------------------------------------------------------------------------
    class(cphDrnType) :: this
    integer(I4B) :: i, node
    real(DP) :: drnelev, cdrn
! ------------------------------------------------------------------------------
    !
    ! -- Return if no drains
    if(this%nbound == 0) return
    !
    ! -- pakmvrobj cf
    if(this%imover == 1) then
      call this%pakmvrobj%cf()
    endif
    !
    ! -- Calculate hcof and rhs for each drn entry
    do i = 1, this%nbound
      node = this%nodelist(i)
      if(this%ibound(node) <= 0) then
        this%hcof(i) = DZERO
        this%rhs(i) = DZERO
        cycle
      endif
      drnelev = this%bound(1,i)
      cdrn = this%bound(2,i)
      if(this%xnew(node) <= drnelev) then
        this%rhs(i) = DZERO
        this%hcof(i) = DZERO
      else
        this%rhs(i) = -cdrn * drnelev
        this%hcof(i) = -cdrn
      endif
    enddo
    !
    ! -- return
    return
  end subroutine drn_cf

  subroutine drn_fc(this, rhs, ia, idxglo, amatsln)
! **************************************************************************
! drn_fc -- Copy rhs and hcof into solution rhs and amat
! **************************************************************************
!
!    SPECIFICATIONS:
! --------------------------------------------------------------------------
    ! -- dummy
    class(cphDrnType) :: this
    real(DP), dimension(:), intent(inout) :: rhs
    integer(I4B), dimension(:), intent(in) :: ia
    integer(I4B), dimension(:), intent(in) :: idxglo
    real(DP), dimension(:), intent(inout) :: amatsln
    ! -- local
    integer(I4B) :: i, n, ipos
    real(DP) :: drncond, drnelev, qdrn
! --------------------------------------------------------------------------
    !
    ! -- packmvrobj fc
    if(this%imover == 1) then
      call this%pakmvrobj%fc()
    endif
    !
    ! -- Copy package rhs and hcof into solution rhs and amat
    do i = 1, this%nbound
      n = this%nodelist(i)
      rhs(n) = rhs(n) + this%rhs(i)
      ipos = ia(n)
      amatsln(idxglo(ipos)) = amatsln(idxglo(ipos)) + this%hcof(i)
      !
      ! -- If mover is active and this drain is discharging,
      !    store available water (as positive value).
      drnelev = this%bound(1,i)
      if(this%imover == 1 .and. this%xnew(n) > drnelev) then
        drncond = this%bound(2,i)
        qdrn = drncond * (this%xnew(n) - drnelev)
        call this%pakmvrobj%accumulate_qformvr(i, qdrn)
      endif
    enddo
    !
    ! -- return
    return
  end subroutine drn_fc

  subroutine define_listlabel(this)
! ******************************************************************************
! define_listlabel -- Define the list heading that is written to iout when
!   PRINT_INPUT option is used.
! ******************************************************************************
!
!    SPECIFICATIONS:
! ------------------------------------------------------------------------------
    class(cphDrnType), intent(inout) :: this
! ------------------------------------------------------------------------------
    !
    ! -- create the header list label
    this%listlabel = trim(this%filtyp) // ' NO.'
    if(this%dis%ndim == 3) then
      write(this%listlabel, '(a, a7)') trim(this%listlabel), 'LAYER'
      write(this%listlabel, '(a, a7)') trim(this%listlabel), 'ROW'
      write(this%listlabel, '(a, a7)') trim(this%listlabel), 'COL'
    elseif(this%dis%ndim == 2) then
      write(this%listlabel, '(a, a7)') trim(this%listlabel), 'LAYER'
      write(this%listlabel, '(a, a7)') trim(this%listlabel), 'CELL2D'
    else
      write(this%listlabel, '(a, a7)') trim(this%listlabel), 'NODE'
    endif
    write(this%listlabel, '(a, a16)') trim(this%listlabel), 'DRAIN EL.'
    write(this%listlabel, '(a, a16)') trim(this%listlabel), 'CONDUCTANCE'
    if(this%inamedbound == 1) then
      write(this%listlabel, '(a, a16)') trim(this%listlabel), 'BOUNDARY NAME'
    endif
    !
    ! -- return
    return
  end subroutine define_listlabel

  ! -- Procedures related to observations

  logical function drn_obs_supported(this)
! ******************************************************************************
! drn_obs_supported
!   -- Return true because DRN package supports observations.
!   -- Overrides BndType%bnd_obs_supported()
! ******************************************************************************
!
!    SPECIFICATIONS:
! ------------------------------------------------------------------------------
    implicit none
    class(cphDrnType) :: this
! ------------------------------------------------------------------------------
    drn_obs_supported = .true.
    !
    ! -- return
    return
  end function drn_obs_supported

  subroutine drn_df_obs(this)
! ******************************************************************************
! drn_df_obs (implements bnd_df_obs)
!   -- Store observation type supported by DRN package.
!   -- Overrides BndType%bnd_df_obs
! ******************************************************************************
!
!    SPECIFICATIONS:
! ------------------------------------------------------------------------------
    implicit none
    ! -- dummy
    class(cphDrnType) :: this
    ! -- local
    integer(I4B) :: indx
! ------------------------------------------------------------------------------
    call this%obs%StoreObsType('drn', .true., indx)
    this%obs%obsData(indx)%ProcessIdPtr => DefaultObsIdProcessor
    !
    ! -- Store obs type and assign procedure pointer
    !    for to-mvr observation type.
    call this%obs%StoreObsType('to-mvr', .true., indx)
    this%obs%obsData(indx)%ProcessIdPtr => DefaultObsIdProcessor
    !
    ! -- return
    return
  end subroutine drn_df_obs

  ! -- Procedure related to time series

  subroutine drn_rp_ts(this)
    ! -- Assign tsLink%Text appropriately for
    !    all time series in use by package.
    !    In DRN package variables ELEV and COND
    !    can be controlled by time series.
    ! -- dummy
    class(cphDrnType), intent(inout) :: this
    ! -- local
    integer(I4B) :: i, nlinks
    type(TimeSeriesLinkType), pointer :: tslink => null()
    !
    nlinks = this%TsManager%boundtslinks%Count()
    do i=1,nlinks
      tslink => GetTimeSeriesLinkFromList(this%TsManager%boundtslinks, i)
      if (associated(tslink)) then
        select case (tslink%JCol)
        case (1)
          tslink%Text = 'ELEV'
        case (2)
          tslink%Text = 'COND'
        end select
      endif
    enddo
    !
    return
  end subroutine drn_rp_ts


  subroutine cphdrn_exsdis(this, surfd, numnodes2d)
! ******************************************************************************
! procedure subroutine for overloading for dealing with extracting surface
!   discharges
! BC must override the default functionality - 
! ******************************************************************************
!
!    SPECIFICATIONS:
! ------------------------------------------------------------------------------
    implicit none
    ! -- dummy
    class(cphDrnType),intent(inout) :: this
    real(DP), dimension(2, numnodes2d), intent(inout) :: surfd
    integer(I4B), intent(in) :: numnodes2d
    ! -- locals
    integer(I4B) :: i, n 
    integer(I4B) :: curunode, inode, remmod, ntimes
    real(DP) :: drndischarge
    !
    ! start
    do i = 1, this%nbound
      n = this%nodelist(i)
      if (n <= 0 ) then
        continue
      end if
      ! now get the user form
      curunode = this%dis%get_nodeuser(n) 
      ! now calculate our index from the user node
      if ( curunode <= numnodes2d ) then
        inode = curunode
      else
        remmod = MOD( curunode, numnodes2d )
        ntimes = curunode / numnodes2d 
        if ( remmod == 0 ) then
          inode = numnodes2d
        else
          inode = remmod
        end if
      end if
      drndischarge = this%simvals(i)
      ! drain discharge is negative because it leaves the model
      if ( drndischarge < DZERO ) then
        drndischarge = -1.0 * drndischarge
      end if
      ! assign to our tracking matrix. This is discharge so goes to
      ! index 1
      surfd(1, inode) = surfd(1, inode) + drndischarge
      !
    end do
    ! -- return
    return
    end subroutine cphdrn_exsdis


end module cphDrnModule
