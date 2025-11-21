import glob
import os
import shutil
import logging

logger = logging.getLogger(__name__)

def clean():
    """Cleans up generated files and directories.
    
    Removes:
    - all .out files
    - cache directory
    - all .o files
    - all meta.txt files
    - __pycache__ directories (including in subdirs)
    - tests directory
    - task.yaml
    """

    logger.info("Cleaning up generated files and directories")

    # Remove all .out files
    for out_file in glob.glob("./**/*.out", recursive=True):
        os.remove(out_file)

    # Remove cache directory
    if os.path.exists("cache"):
        shutil.rmtree("cache")

    # Remove all .o files
    for o_file in glob.glob("./**/*.o", recursive=True):
        os.remove(o_file)

    # Remove meta.txt files
    for meta_file in glob.glob("./**/meta.txt", recursive=True):
        os.remove(meta_file)

    # Remove __pycache__ directories (including in subdirectories)
    for pycache_dir in glob.glob("./**/__pycache__", recursive=True):
        shutil.rmtree(pycache_dir)

    # Remove tests directory
    if os.path.exists("tests"):
        shutil.rmtree("tests")

    # Remove task.yaml
    if os.path.exists("task.yaml"):
        os.remove("task.yaml")
