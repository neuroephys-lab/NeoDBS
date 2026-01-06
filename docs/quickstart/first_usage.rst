First Usage
===========

.. meta::
   :description lang=en: The starting point for the tutorial set.

NeoDBS is a platform designed for maximal user-experience, with every item and functionality optimized for 
easy data analysis and natural workflow. *Even for unexperienced users in signal processing and analysis.*
With this, NeoDBS was developed to allow **several workspaces open symultaneously**. For that, the user can 
open multiple windows, each one corresponding to an independent workspace. Just like a browser.

Inside each window (or workspace), all the mentioned data is organized and accessed in a hierarchical order:


* Window |rarrow| File(s)
* Tab |rarrow| Recording(s)
* Child Tab |rarrow| Recording Analysis

.. |rarrow| unicode:: U+2192 .. RIGHT ARROW

This workflow is explained more in depth :ref:`below <general>`. With this arrangement, the platform facilitates access to data, while ensuring multiple independent and simultaneous analysis pipelines for 
each recording available. 

NeoDBS brings novelty in signal processing platforms by facilitating the user with 
signal **filtering** and **spectral analysis** pipelines with **default** or **customizable** parameters. Perfect for both unexperienced users 
like health professionals, or experienced users such as data analists and researchers.


.. image:: ../img/browser.png

Types of Workspaces
-------------------

As mentioned above, the user has the possibility to work with several workspaces simultaneously. 
Additionally, NeoDBS offers two different types of workspaces (windows). The **Individual Window** and the
**Combined Window**. While they share the majority of functionalities, their final goal differs.

Individual Window
^^^^^^^^^^^^^^^^^

The **Individual** window goal is to analyze a single recording session, focusing on the evolution of signals and 
events inside the same session. Therefore it includes functionalities like:

* Event marking in time-domain signals, and their time-frequency domain methods, according to user input;
* Compute joined time-frequency domain methods in same-channel recordings;

These are exclusive to this workspace, in order to enhance computing power and hetereogeneity in workspaces.

Combined Window
^^^^^^^^^^^^^^^
Unlike the individual window, the **Combined** window allows the selection of multiple files, focusing therefore on 
the evolution of the signals across different recording sessions. Additionally, it includes functionalities such as:

* Event-locked segmentation, automatically epoching recordings according to user input.

These functionalities are further explained in :ref:`here <ela>`.

If you're wondering what is the best window to use, here's a summary of the functionalities present in each type of window.

+------------------------------------+---------------------+--------------------+
| Feature                            | Individual Analysis | Combined Analysis  |
+====================================+=====================+====================+
| File Ingestion                     | Single file         | Multiple files     |
+------------------------------------+---------------------+--------------------+
| Metadata display                   | |check|             | |check|            |
+------------------------------------+---------------------+--------------------+
| Default/Customizable Filtering     | |check|             | |check|            |
+------------------------------------+---------------------+--------------------+
| Default/Customizable Spectral      | |check|             | |check|            |
| Analysis                           |                     |                    |
+------------------------------------+---------------------+--------------------+
| Event Annotation                   | |check|             | X                  |
+------------------------------------+---------------------+--------------------+
| Automatic Event-locked Segmentation| |check|             | |check|            |
+------------------------------------+---------------------+--------------------+
| Merged Same-Channel Recordings     | |check|             | X                  |
+------------------------------------+---------------------+--------------------+
| Manual Segmentation                | X                   | |check|            |
+------------------------------------+---------------------+--------------------+
| Before/After Event Analysis        | X                   | |check|            |
+------------------------------------+---------------------+--------------------+

.. |check| unicode:: U+2713 .. CHECK MARK

Types of Recordings
-------------------

NeoDBS is adapted to ingest and analyze files from commercialy available DBS systems with sensing capacities (Medtronic Percept + BrainSense™ system). 
The system allows to record signals on different recording modes with different purposes and configurations. To know more about these recording modes 
see `here <https://iopscience.iop.org/article/10.1088/1741-2552/ac1d5b>`_ (table 1). 

Because of the differences in purpose and configuration across the recording modes, they are accessed and treated independently, in the respective tabs, as mentioned above.

Here follows a simple summary of the recording modes, with their associated name in system and NeoDBS:

+-------------------------------+--------------------+-------------+-------------+--------------------------+
| System Name                   | NeoDBS Name        | Usage Con-  | Stimulation | Key Features             |
|                               |                    | text        | Status      |                          |
+===============================+====================+=============+=============+==========================+
| BrainSense™ *Setup*           | *Setup*            | In-clinic   | On or Off   | Required before other    |
|                               |                    |             |             | modes (except *Survey*); |
|                               |                    |             |             | Records each segment for |
|                               |                    |             |             | 21s each (~90s duration) |
+-------------------------------+--------------------+-------------+-------------+--------------------------+
| BrainSense™ *Survey*          | *Survey*           | In-clinic   | Off         | Records each segment for |
|                               |                    |             |             | 21s each (~90s duration) |
+-------------------------------+--------------------+-------------+-------------+--------------------------+
| BrainSense™ *Survey Indefinite| *Indefinite*       | In-clinic   | Off         | Long-duration LFP        |
| Streaming*                    | *Streaming*        |             |             | recording from contact   |
|                               |                    |             |             | pairs (0–2, 0–3, 1–3),   |
|                               |                    |             |             | full-bandwidth (up to    |
|                               |                    |             |             | 125 Hz)                  |
+-------------------------------+--------------------+-------------+-------------+--------------------------+
| BrainSense™ *Streaming*       | *Streaming*        | In-clinic   | On or Off   | Long-duration LFP        |
|                               |                    |             |             | recording from contact   |
|                               |                    |             |             | pairs compatible with    |
|                               |                    |             |             | stimulation              |
+-------------------------------+--------------------+-------------+-------------+--------------------------+
| BrainSense™ *Timeline*        | *Timeline*         | At home     | On          | Long-term monitoring     |
|                               |                    |             |             | from pre-selected        |
|                               |                    |             |             | bipolar pair; power of   |
|                               |                    |             |             | 5 Hz band stored every   |
|                               |                    |             |             | 10 min; contact pairs    |
|                               |                    |             |             | limited to stimulation-  |
|                               |                    |             |             | compatible               |
+-------------------------------+--------------------+-------------+-------------+--------------------------+
| BrainSense™ *Events*          | *Events*           | At home     | On          | Event-marked recordings, |
|                               |                    |             |             | 30 s LFP saved into PSD, |
|                               |                    |             |             | time-stamped by patient  |
|                               |                    |             |             | manual input             |
+-------------------------------+--------------------+-------------+-------------+--------------------------+

.. _general:
General Workflow
----------------

After understanding what workspaces exist, here is a simple workflow for analysis using NeoDBS.

1. **Select type of analysis to be performed:** Individual Window or Combined Window.

.. image:: ../img/main.png

2. **Select the recording session's file(s)**, in JSON format, to be analyzed. JSON files are highlighted with green letters.

.. image:: ../img/select_file.png

3. Window will present **session, device and stimulation information** for each recording session.

.. image:: ../img/window.png

4. Recordings can be accessed by clicking on the **respective recording mode button**. 
5. **Each recording mode will have its respective tab**, with the associated recordings and functionalities. Preprocessing and spectral analysis methods will only be applied to the selected signals (visible on the main plot of tab).

.. image:: ../img/tab.png

6. **Default methods** have the parameters predefined for an easier analysis, properly adapted for the recordings configuration.

.. image:: ../img/default.png

7. **Custom methods** allow the parameters to be adjusted according to the user needs. Documentation of the selected method and required parameters will appear to aid the user in selecting the best parameters. 

.. image:: ../img/custom.png

8. **Filtering** methods will update the signals in the main plot. **Signal Analysis** methods create a new plot, under a **child tab** named after the applied method.

9. **Signals, plots and tables can be easily exported** either individually, per window (workspace) or all windows at once.

.. image:: ../img/save.png

Here you can find a scheme that represents the possible workflow in NeoDBS.

.. image:: ../img/workflow.png