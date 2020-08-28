.. _standalone_HSPF:

Standalone HSPF Model 
======================

This case study application was developed to assist in **pyHS2MF6** 
development and testing. There was not an existing 
HSPF model to use as a starting point. A standalone 
HSPF model was created expressly for testing **pyHS2MF6**.

**mHSP2** is the name of the standalone HSPF component of **pyHS2MF6**. 
The **mHSP2** code base is documented in :ref:`mHSP2`. It uses the 
same input file format as used by the 
`HSPsquared <https://github.com/respec/HSPsquared>`_ variant of HSPF.

The **mHSP2** input file for the case study is a 
`HDF5 file <https://portal.hdfgroup.org/display/knowledge/What+is+HDF5>`_. 
This `standalone mHSP2 input file <https://github.com/nmartin198/pyHS2MF6/blob/master/example_models/standalone/HSPF>`_  
is available on the **pyHS2MF6** GitHub site.

|

.. _cs_saHSPF_model:

HSPF Model Layout and Configuration
-------------------------------------

The site watershed was divided into 12 sub-watershed, 
:abbr:`HRUs (Hydrologic Response Units)`. Each HRU has PERLND, pervious 
land, and IMPLND, impervious land, components or areas. IMPLND areas are 
composed of gravel roads and structures. Given the limited development 
in this area, the pervious land area is ``>>`` impervious land area. 

Five RCHRES, stream reach or well mixed reservoirs, are used to route 
water from the upstream-most :abbr:`HRU (Hydrologic Response Unit)` to 
the watershed outlet. RCHRES #5 is the stream segment where the stream 
gage and the springs are located. This reach is hypothesized to be a 
gaining stream reach where external water enters the reach from springs 
in addition to the water that is routed downstream from Reach #4. 
Reaches #1 - #4 are hypothesized to be losing reaches.

An important conceptualization for coupled model simulation is how to 
treat gaining and losing reaches for communication with the groundwater
flow model. Gaining and losing requires different HSPF configurations 
to facilitate future coupling to a groundwater flow model.

* **Gaining** reaches: additional input water from spring discharge or 
  other baseflow components is input to a *RCHRES* structure as an 
  external inflow time series.

  - This is the treatment used for Reach #5 to represent contributions 
    from Dolan Springs and YR-70-01-701.

* **Losing** reaches: In HSPF, there is not a preconfigured process for 
  stream losses to groundwater because saturated groundwater conditions 
  are not really represented in HSPF. The representation of loses from 
  stream segments to groundwater is then largely up to the modeler. In 
  **pyHS2MF6** the modeler should specify one *RCHRES* exit to represent
  loses to groundwater. Typically, one *RCHRES* exit is used to 
  calculate downstream discharge that is routed to the next *RCHRES* 
  downstream and one *RCHES* exit is used to remove water from the 
  model that represents loses to groundwater.

  - In the standalone HSPF model, exit #2 for Reaches #1 - #4 represents
    seepage to groundwater from the stream. HSPF calculates this seepage 
    using a volume-based, or FTAB, calculation for the standalone model.
    This volume-based, seepage relationship was part of the calibration
    to reproduce the gage discharge at the watershed outlet.

  - If desired, the user can implement a time-based relationship for 
    discharge from an exit. Consequently, a time-based relationship 
    could be used for exit #2 to represent seepage to groundwater.

|

.. note:: A single reach can be represented as both gaining and losing 
   using both a specified external time series inflow and an outflow 
   calculation for a designated exit for discharge to groundwater. This
   is not recommended. The recommended approach would be to use two 
   *RCHRES* for the stream segment with one portraying gaining 
   conditions and one representing losing conditions.

|

**Figure** :ref:`fig_cs_sahspf` shows the HSPF model layout for the study 
site. Complete details of HSPF model configuration are available in 
the `standalone mHSP2 input file <https://github.com/nmartin198/pyHS2MF6/blob/master/example_models/standalone/HSPF>`_.


.. _fig_cs_sahspf:
.. figure:: ./images/HSPF_Layout.png 
    :width: 800px
    :align: center
    :alt: HSPF model layout
    :figclass: align-center 

    **HSPF model configuration**


|

.. _cs_saHSPF_calib:

Calibration
~~~~~~~~~~~~~

The goal for the standalone model is to produce Reach #5 outflow that 
approximately represents the observed Dolan Creek stream flow discharge from 
`USGS Gage 08449100 <https://waterdata.usgs.gov/tx/nwis/uv/?site_no=08449100&PARAmeter_cd=00065,00060>`_.
In the set-up for calibration, estimates of spring discharge from Dolan 
Springs and YR-70-01-701 (see **Figure** :ref:`fig_cs_focused_ws`) are provided 
to the HSPF model as an external time series of inflows to Reach #5.

An automated calibration process using `PEST <http://www.pesthomepage.org/>`_ 
was used to tweak watershed parameters to best reproduce the observed 
Dolan Creek stream flow. The results from this best-fit case are shown 
on **Figure** :ref:`fig_cs_sahspf_calib`. In this figure, the orange shaded 
area denotes the estimated, external inflow time series to Reach #5 that
represents the combination of Dolan Springs and YR-70-01-701 discharge.


.. _fig_cs_sahspf_calib:
.. figure:: ./images/HSPF_SA_Calib.svg 
    :width: 800px
    :align: center
    :alt: Standalone HSPF Calibration
    :figclass: align-center 

    **Standalone HSPF Calibration**


|

.. _cs_saHSPF_osoft:

HSPF Software Packages and Conversion
----------------------------------------

The standalone HSPF model was created using the following combinations 
of HSPF-variant software.

1. The initial HSPF model set-up and configuration were implemented 
   using `PyHSPF <https://github.com/djlampert/PyHSPF>`_. This produces 
   a HSPF :abbr:`UCI (User Control Interface)` file and input and 
   output :abbr:`WDM (Watershed Data Management)` files.

2. `HSPsquared <https://github.com/respec/HSPsquared>`_ was then employed 
   to convert the :abbr:`UCI (User Control Interface)` file and input
   :abbr:`WDM (Watershed Data Management)` file to an `HSPsquared` 
   input `HDF5 file <https://portal.hdfgroup.org/display/knowledge/What+is+HDF5>`_.
   This format is similar to what is required for **mHSP2**.

3. Next, the Jupyter Notebook 
   `mHSP2_SetSaves <https://github.com/nmartin198/pyHS2MF6/blob/master/example_models/jupyter_notebooks/mHSP2_SetSaves.ipynb>`_ 
   was employed to modify the `HSPsquared`, input HDF5 file to be 
   provide the specification of model outputs that is required by **mHSP2**.


|

.. _cs_saHSPF_runmod:

Running a Standalone mHSP2 Simulation
----------------------------------------

A standalone **mHSP2** simulation is executed from an 
`Anaconda Prompt <https://docs.anaconda.com/anaconda/user-guide/getting-started/#open-anaconda-prompt>`_ 
using the instructions below. For these instructions it is assumed, 
that **pyHS2MF6** is installed at `C:\\pyHS2MF6` and that the model 
HDF5 file is in the directory `C:\\Models\\sa_mHSP2`.

1. `Activate <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#activating-an-environment>`_ 
   the pyhs2mf6 Anaconda virtual environment. Additional details can be 
   found at :ref:`install_pyconda`. ::
   
      (base) > conda activate pyhs2mf6

2. Make the current directory the model directory. ::

      (pyhs2mf6) > cd C:\Models\sa_mHSP2

3. Run the model ::

      (pyhs2mf6) > python C:\pyHS2MF6\bin\standaloneMain.py HSP2 C:\\Models\\sa_mHSP2 -f DC_CalibmHSP2.h5


The model will create a log file that records general information and 
any issues encountered during the run. The log file provides a listing
of input parameters along with required units. It also provides a 
listing of output parameters along with output units.

For the example provided above, the run log is written to the file 
`C:\\Models\\sa_mHSP2\\mHSP2_Log.txt`. An example 
`mHSP2_Log.txt <https://github.com/nmartin198/pyHS2MF6/tree/master/example_models/standalone/HSPF>`_ 
is available in the standalone, example model directory.

In terms of accessing standalone simulation results, the Jupyter Notebook 
`mHSP2_SA_Results <https://github.com/nmartin198/pyHS2MF6/blob/master/example_models/jupyter_notebooks/mHSP2_SA_Results.ipynb>`_ 
provides a simple example of extracting and analyzing standalone **mHSP2**
results.

|
