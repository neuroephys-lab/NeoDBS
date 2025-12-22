NeoDBS documentation
====================

.. meta::
   :description lang=en: Automate building, versioning, and hosting of your
    technical documentation continuously on Read the Docs.

About NeoDBS
------------

NeoDBS is an open-source user-oriented platform developed in Python, designed to examine electrophysiological 
brain activity data offline from recordings acquired with Medtronic's Percept BrainSense™ Technology.

This new platform was developed in order to facilitate the analysis of multiple independent recordings,
by experienced or non-experienced users like health physicians. It offers a:

* Browser-like design, allowing multiple workspaces open simultaneously
* Workspaces focused on a single recording session or on multiple recording sessions
* Analysis pipelines with default or customizable parameters
* Event-locked analysis and event marking
* Exportation of tables, signals and images
* Several filtering and spectral analysis methods
* Interface and data customization

NeoDBS includes several open-source organized modules focused in data preparation (Data Handling), data processing - including filtering, 
segmentation, and method application - (Preprocessing) and feature extraction (Features). A collection of
utility tools was also developed (Utils). All modules and functions are described in (:doc:`Modules <api/neodbs>`).

Quick Start
-----------

If you're ready to start using NeoDBS, follow the general workflow described in :doc:`First Steps <quickstart/first_steps>`.
If you haven't installed NeoDBS, follow the instructions.

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Quick Start

   quickstart/first_steps
   quickstart/first_usage


Tutorials
---------

Several tutorials have been prepared to facilitate the use of NeoDBS. Tutorials don't fully explain all functinalities available.

.. toctree::
   :maxdepth: 2
   :hidden:
   :numbered:
   :caption: Tutorials

   tutorials/td
   tutorials/chronic
   tutorials/features
   

API Documentation
-----------------

Full documentation of all function's and modules.

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Modules

   api/neodbs   
