.. 
    List all modules containing docstrings from which to construct the docs.
    
    To run and compile doctests:
    
        (docs) $ make doctest
        
    To build docs:
    
        (docs) $ make html
        
    To clean build directory for a fresh start:
    
        (docs) $ make clean


datopy
======

The ``datopy`` package includes utilities for managing data I/O,
data modelling, ETL pipelines, and utilities for testing, inspecting data,
and styling matplotlib plots.

.. rubric:: Modules

..
    .. autosummary::
    :toctree: generated

    datopy

.. autosummary::
    :toctree: datopy
    :recursive:
    
    datopy.inspection
    datopy.workflow
    datopy.modeling
    datopy.etl
    datopy.stylesheet
    datopy.run_doctests
    datopy._examples
    datopy._media_scrape
