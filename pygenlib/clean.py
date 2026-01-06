import glob
import os
import shutil

from pygenlib import config


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

    # Remove all .out files
    for out_file in glob.glob("./**/*.out", recursive=True):
        os.remove(out_file)

    # Remove cache directory
    cache_dir = config.get_cache_dir_path()
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)

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
    tests_dir = config.get_tests_dir_path()
    if os.path.exists(tests_dir):
        shutil.rmtree(tests_dir)

    # Remove reports directory
    reports_dir = config.get_reports_dir_path()
    if os.path.exists(reports_dir):
        shutil.rmtree(reports_dir)

    # Remove task.yaml
    if os.path.exists("task.yaml"):
        os.remove("task.yaml")
    
    # Remove scores directory
    scores_dir = config.get_scores_dir_path()
    if os.path.exists(scores_dir):
        shutil.rmtree(scores_dir)
