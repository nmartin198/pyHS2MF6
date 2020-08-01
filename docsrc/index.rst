.. pyHS2MF6 documentation master file, created by
   sphinx-quickstart on Thu Jul 16 17:24:27 2020.

.. meta::
   :description: pyHS2MF6: a dynamically coupled, HSPF and MODFLOW 6 
                  integrated hydrologic model

   :keywords: pyHS2MF6, HSPF, MODFLOW 6, integrated hydrologic model, mHSPF, pyMF6


Welcome to the pyHS2MF6 documentation
======================================

pyHS2MF6 is an integrated hydrologic model created using a dynamic 
coupling of :abbr:`HSPF (Hydrological Simulation Program – FORTRAN)` 
and MODFLOW 6 in Python. The coupling is dynamic because 
:abbr:`HSPF (Hydrological Simulation Program – FORTRAN)` and MODFLOW 
6 exchange information during each simulation time step. At this time,
pyHS2MF6 can only use and simulate the basic water movement and storage 
processes in :abbr:`HSPF (Hydrological Simulation Program – FORTRAN)` and 
MODFLOW.

A fundamental goal in the design of pyHS2MF6 was to provide for the 
ability to build on existing, independently created, 
:abbr:`HSPF (Hydrological Simulation Program – FORTRAN)` and MODFLOW 
models. Consequently, pyHS2MF6 provides two simulation modes.

1. **Coupled mode**: Main simulation mode with dynamically coupled
   :abbr:`HSPF (Hydrological Simulation Program – FORTRAN)` and MODFLOW 6

2. **Standalone mode**: Included purely so that the user can check or 
   verify the function of the independent, existing model (either
   HSPF or MODFLOW 6) in pyHS2MF6. It is not recommended to use 
   pyHS2MF6 standalone mode in place of just using 
   :abbr:`HSPF (Hydrological Simulation Program – FORTRAN)` or just 
   using MODFLOW 6.

|

.. attention:: Please see :ref:`getting_started` before trying to 
   install and run pyHS2MF6.
   
   It is recommended to at least browse through the :ref:`case_study` 
   before trying to apply pyHS2MF6 to a specific site.

|

.. note:: pyHS2MF6 is available for free under the 
   `GNU Affero General Public License version 3 <https://www.gnu.org/licenses/agpl-3.0.html>`_  
   and without warranty or support.
   
   * Technical support can be arranged, if desired.

   * pyHS2MF6 builds upon and extends two independent models and provides for dynamic information 
     exchange between the models. As a result, pyHS2MF6 configuration, implementation,
     and use requires a number of prerequisites.

|

    
Table of Contents
---------------------

.. toctree::
   :maxdepth: 2
   :numbered:
   :name: maintoc
   
   getting_started.rst
   installation.rst
   case_study.rst 
   code_doc.rst 



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
