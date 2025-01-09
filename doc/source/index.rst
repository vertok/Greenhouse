.. greenhouse documentation master file, created by
   sphinx-quickstart on Thu Jan  9 23:33:29 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Greenhouse's Documentation!
======================================

This is the documentation for the **Greenhouse** project. This project 
provides tools for monitoring and managing a greenhouse environment. It 
includes:

*   A custom logging module (`school_logging`) for flexible and colored logging.
*   Functionality to process and store measurements in db (`greenhouse/measurements2db.py`).

Installation
------------

To install the Greenhouse project, follow these steps:

1.  Clone the repository:

    .. code-block:: bash

        git clone <your_repository_url> #todo

2.  Install the required packages:

    .. code-block:: bash

        pip install -r requirements.txt

Usage Example
-------------

Here's a quick example of how to use the `ColoredLogger` from the `school_logging` module:

.. code-block:: python

    from school_logging.log import ColoredLogger

    log = ColoredLogger(__name__)
    log.info("This is an informational message.")

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   school_logging
   measurements2db

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
