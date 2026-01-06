from dataclasses import dataclass, field
from typing import Optional
import os
import re

@dataclass
class CommonConfig:
    task_id: str = ""

    solution_paths: list[str] = field(default_factory=list)
    model_solution_path: str = ""

    testlib_gen_path: str = "gen.cpp"
    testlib_checker_path: str = ""  # Empty by default - no checker, use character comparison
    testlib_header_path: str = "testlib.h"

    tests_dir: str = "./tests"
    cache_dir: str = "./cache"
    reports_dir: str = "./reports"
    scores_dir: str = "./scores"
    
    gen_extra_files: dict[str, str] = field(default_factory=dict)

_conf = CommonConfig()

def set_task_id(new_task_id):
    global _conf
    # check if the new_task id is well-formed
    # task id is a string of alphanumeric characters, hyphens, and underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', new_task_id):
        raise ValueError(f"task ID {new_task_id} is not well-formed")
    _conf.task_id = new_task_id


def get_task_id() -> str:
    if not _conf.task_id:
        raise ValueError("task ID is not configured")
    return _conf.task_id

def _normalize_path(path: str) -> str:
    if not path:
        raise ValueError("path cannot be empty")
    return os.path.abspath(os.path.expanduser(path))


def _require_existing_file(path: str, description: str) -> str:
    abs_path = _normalize_path(path)
    if not os.path.isfile(abs_path):
        raise FileNotFoundError(f"{description} path '{path}' does not exist or is not a file")
    return abs_path


def _allow_missing_dir(path: str, description: str) -> str:
    abs_path = _normalize_path(path)
    parent_dir = os.path.dirname(abs_path) or os.path.abspath(os.curdir)
    if not os.path.isdir(parent_dir):
        raise FileNotFoundError(f"parent directory '{parent_dir}' for {description} path '{path}' does not exist")
    if os.path.exists(abs_path) and not os.path.isdir(abs_path):
        raise NotADirectoryError(f"{description} path '{path}' exists but is not a directory")
    return abs_path


def add_solution(new_solution_path, is_model=False):
    global _conf
    abs_path = _require_existing_file(new_solution_path, "solution")
    if is_model:
        _conf.model_solution_path = abs_path
    if abs_path not in _conf.solution_paths:
        _conf.solution_paths.append(abs_path)
    return abs_path


def override_generator_path(path):
    global _conf
    _conf.testlib_gen_path = _require_existing_file(path, "testlib generator")
    return _conf.testlib_gen_path


def override_checker_path(path):
    global _conf
    _conf.testlib_checker_path = _require_existing_file(path, "testlib checker")
    return _conf.testlib_checker_path

def enable_checker():
    global _conf
    _conf.testlib_checker_path = "checker.cpp"


def override_testlib_h_path(path):
    global _conf
    _conf.testlib_header_path = _require_existing_file(path, "testlib header")
    return _conf.testlib_header_path


def override_tests_dir_path(path):
    global _conf
    _conf.tests_dir = _allow_missing_dir(path, "tests directory")
    return _conf.tests_dir


def override_cache_dir_path(path):
    global _conf
    _conf.cache_dir = _allow_missing_dir(path, "cache directory")
    return _conf.cache_dir


def override_reports_dir_path(path):
    global _conf
    _conf.reports_dir = _allow_missing_dir(path, "reports directory")
    return _conf.reports_dir


def get_cache_dir_path() -> str:
    global _conf
    _conf.cache_dir = _allow_missing_dir(_conf.cache_dir, "cache directory")
    return _conf.cache_dir


def get_tests_dir_path() -> str:
    global _conf
    _conf.tests_dir = _allow_missing_dir(_conf.tests_dir, "tests directory")
    return _conf.tests_dir


def get_reports_dir_path() -> str:
    global _conf
    _conf.reports_dir = _allow_missing_dir(_conf.reports_dir, "reports directory")
    return _conf.reports_dir


def get_testlib_checker_path() -> Optional[str]:
    global _conf
    if not _conf.testlib_checker_path:
        return None
    _conf.testlib_checker_path = _require_existing_file(_conf.testlib_checker_path, "testlib checker")
    return _conf.testlib_checker_path


def get_testlib_header_path() -> str:
    global _conf
    _conf.testlib_header_path = _require_existing_file(_conf.testlib_header_path, "testlib header")
    return _conf.testlib_header_path


def get_testlib_gen_path() -> str:
    global _conf
    _conf.testlib_gen_path = _require_existing_file(_conf.testlib_gen_path, "testlib generator")
    return _conf.testlib_gen_path


def get_model_solution_path() -> str:
    global _conf
    if not _conf.model_solution_path:
        raise ValueError("model solution path is not configured")
    _conf.model_solution_path = _require_existing_file(_conf.model_solution_path, "model solution")
    return _conf.model_solution_path

def get_solution_paths() -> list[str]:
    global _conf
    return _conf.solution_paths


def include_file(filename: str, source: str):
    """Add an extra file to be included in all gen() calls.
    
    Args:
        filename: Name of the file to add to the generator sandbox
        source: Either a file path to read, or literal file contents
    """
    global _conf
    _conf.gen_extra_files[filename] = source


def clear_gen_files():
    """Clear all extra files added via add_gen_file()."""
    global _conf
    _conf.gen_extra_files = {}


def get_gen_extra_files() -> dict[str, str]:
    """Get all extra files registered for generator runs."""
    global _conf
    return _conf.gen_extra_files.copy()

def get_scores_dir_path() -> str:
    global _conf
    _conf.scores_dir = _allow_missing_dir(_conf.scores_dir, "scores directory")
    return _conf.scores_dir