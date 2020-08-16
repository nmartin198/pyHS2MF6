.. _case_study:

============================
 Coupled Mode Example Model 
============================

**pyHS2MF6** was designed and constructed under the premise that it would be 
applied to link existing :abbr:`HSPF (Hydrological Simulation Program – FORTRAN)` 
and MODFLOW models into a dynamically coupled, integrated hydrologic model.
Consequently, **coupled mode** is the primary simulation mode. A 
**standalone mode** is provided so that they user can check that **pyHS2MF6** 
is satisfactorily reproducing the solutions of the standalone 
:abbr:`HSPF (Hydrological Simulation Program – FORTRAN)` and MODFLOW models.

An example model is provided as a case study and test case to walk the 
user through the process of transitioning from standalone 
:abbr:`HSPF (Hydrological Simulation Program – FORTRAN)` and MODFLOW 
models to a fully coupled simulation. This case study also explains
and provides samples of **pyHS2MF6** inputs and outputs.

|

.. note:: The case study models were derived solely for use in testing 
    coupled mode simulation. Consequently, there was not an existing 
    HSPF or MODFLOW 6 model available for the test case. As a result,
    the case study focuses on **pyHS2MF6** implementation and simulation
    rather than on the study site.

|

.. caution:: It is assumed for this test case that the user is an expert
    user of both :abbr:`HSPF (Hydrological Simulation Program – FORTRAN)` 
    and MODFLOW 6.

|

.. note:: It is the user's responsibility to ensure that **pyHS2MF6** is 
    satisfactorily reproducing the standalone model representations.

|


**Section Contents**

.. toctree::
    :maxdepth: 4
    :name: tcasetoc

    cs_study_site.rst
    cs_sa_HSPF.rst
    cs_sa_MF6.rst
    cs_cpmode.rst


