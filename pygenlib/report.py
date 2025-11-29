from dataclasses import dataclass
from typing import Optional, Tuple

from pygenlib.isolate import run_cpp_code, run_py_code
from pygenlib import config
import csv
import logging
import os
import tempfile
import subprocess
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class TestCaseResult:
    """Result of running a solution on a test case"""

    verdict: str  # "AC", "WA", "TLE", or "RE"
    exec_time: float  # CPU time in seconds
    mem_mib: float  # Memory usage in MiB
    test_name: str  # Test case name without task prefix
    checker_msg: str = ""  # Output message from the checker


@dataclass
class ReporterConfig:
    task_name: str
    tests_dir: str
    checker_path: Optional[str]
    testlib_path: str
    cache_dir: str
    reports_dir: str


_default_reporter_config: Optional[ReporterConfig] = None

def override_reporter_config(cfg: ReporterConfig):
    """Set the default reporter configuration used by the module-level report function."""
    global _default_reporter_config
    _default_reporter_config = cfg


def report(sol_path, output_file=None, cfg: Optional[ReporterConfig] = None):
    """Generate a TSV report for the provided solution path."""
    cfg = _resolve_reporter_config(cfg)
    lang = _detect_language(sol_path)
    checker_executable = _compile_checker(cfg) if cfg.checker_path else None
    include_checker_msg = checker_executable is not None

    logger.info(f"Generating report for solution: {sol_path}")
    if checker_executable:
        logger.info(f"Using checker executable: {checker_executable}")

    with open(sol_path, "r") as f:
        sol_code = f.read()
        logger.debug(f"Read solution code from {sol_path}, size: {len(sol_code)} bytes")

    output_path = _resolve_output_path(sol_path, output_file, cfg)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    _initialize_report_file(output_path, include_checker_msg)

    test_files = sorted(
        f for f in os.listdir(cfg.tests_dir) if f.startswith(f"{cfg.task_name}.i")
    )
    logger.info(f"Found {len(test_files)} test files to process")

    for test_file in test_files:
        full_test_path = os.path.join(cfg.tests_dir, test_file)
        logger.info(f"Running test: {test_file}")
        result = _run_test(
            full_test_path,
            sol_code,
            lang,
            checker_executable,
        )
        _append_result(output_path, result, include_checker_msg)

    logger.info(f"Results written to {output_path}")


def _resolve_reporter_config(reporter_config: Optional[ReporterConfig]) -> ReporterConfig:
    if reporter_config is not None:
        return reporter_config
    if _default_reporter_config is not None:
        return _default_reporter_config
    return ReporterConfig(
        task_name=config.get_task_id(),
        tests_dir=config.get_tests_dir_path(),
        checker_path=config.get_testlib_checker_path(),
        testlib_path=config.get_testlib_header_path(),
        cache_dir=config.get_cache_dir_path(),
        reports_dir=config.get_reports_dir_path(),
    )


def _compile_checker(cfg: ReporterConfig) -> Optional[str]:
    if cfg.checker_path is None:
        return None

    if not os.path.exists(cfg.checker_path):
        logger.error(f"Checker file not found: {cfg.checker_path}")
        return None

    os.makedirs(cfg.cache_dir, exist_ok=True)

    checker_hash = hashlib.md5(cfg.checker_path.encode()).hexdigest()
    checker_exe_path = os.path.join(cfg.cache_dir, f"checker_{checker_hash}")

    if os.path.exists(checker_exe_path):
        logger.info(f"Using cached checker: {checker_exe_path}")
        return checker_exe_path

    with open(cfg.testlib_path, "r") as f:
        testlib_content = f.read()
    testlib_cache_path = os.path.join(cfg.cache_dir, "testlib.h")
    with open(testlib_cache_path, "w") as f:
        f.write(testlib_content)

    with open(cfg.checker_path, "r") as f:
        checker_content = f.read()
    checker_cache_path = os.path.join(cfg.cache_dir, "checker.cpp")
    with open(checker_cache_path, "w") as f:
        f.write(checker_content)

    compile_cmd = ["g++", "-std=c++17", "-O2", checker_cache_path, "-o", checker_exe_path]
    logger.info(f"Compiling checker with command: {' '.join(compile_cmd)}")
    try:
        subprocess.run(compile_cmd, check=True)
        logger.info(f"Checker compiled successfully: {checker_exe_path}")
        return checker_exe_path
    except subprocess.CalledProcessError as exc:
        logger.error(f"Failed to compile checker: {exc}")
        return None


def _run_test(test_file: str, sol_code: str, lang: str, checker_executable: Optional[str]) -> TestCaseResult:
    logger.debug(f"Processing test file: {test_file}")

    with open(test_file, "r") as f:
        stdin = f.read()
        logger.debug(f"Read input file, size: {len(stdin)} bytes")

    logger.debug(f"Running solution in {lang} language")
    if lang == "cpp":
        run_result = run_cpp_code(sol_code, stdin=stdin)
    elif lang == "py":
        run_result = run_py_code(sol_code, stdin=stdin)
    else:
        logger.error(f"Unsupported language: {lang}")
        raise ValueError(f"Unsupported language: {lang}")

    if run_result.status not in ["OK", "TO", "SG"]:
        logger.error(f"Execution failed with status: {run_result.status}")
        print(run_result)
        exit()

    test_name = os.path.basename(test_file).split(".i")[1]
    logger.debug(f"Test name: {test_name}, execution status: {run_result.status}")

    answer_file = test_file.replace(".i", ".o")
    logger.debug(f"Reading answer from: {answer_file}")
    with open(answer_file, "r") as f:
        answer = f.read()

    verdict = "AC"
    checker_msg = "-"

    if run_result.status == "SG":
        logger.warning(f"Runtime error on test {test_name}")
        verdict = "RE"
    elif run_result.status == "TO" or run_result.exec_time > 1:
        logger.warning(f"Time limit exceeded on test {test_name}: {run_result.exec_time}s")
        verdict = "TLE"
    else:
        if checker_executable:
            logger.debug("Using checker to verify output")
            verdict, checker_msg = _run_checker(checker_executable, test_file, run_result.stdout, answer)
        else:
            logger.debug("Using string comparison to verify output")
            verdict = _string_compare(run_result.stdout, answer)

    logger.info(
        f"Test {test_name} result: {verdict}, time: {run_result.exec_time:.2f}s, "
        f"memory: {run_result.cg_mem_kib/1024:.2f}MiB"
    )

    return TestCaseResult(
        verdict=verdict,
        exec_time=run_result.exec_time,
        mem_mib=run_result.cg_mem_kib / 1024,
        test_name=test_name,
        checker_msg=checker_msg,
    )


def _run_checker(checker_executable: str, input_file: str, participant_output: str, jury_output: str) -> Tuple[str, str]:
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as participant_file:
        participant_file.write(participant_output)
        participant_path = participant_file.name

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as jury_file:
        jury_file.write(jury_output)
        jury_path = jury_file.name

    try:
        checker_cmd = [checker_executable, input_file, participant_path, jury_path]
        logger.debug(f"Running checker: {' '.join(checker_cmd)}")
        proc = subprocess.run(
            checker_cmd,
            capture_output=True,
            text=True,
            timeout=5,
        )

        if proc.returncode == 0:
            logger.debug("Checker returned AC")
            return "AC", proc.stdout.strip()
        if proc.returncode == 1:
            logger.debug(f"Checker returned WA: {proc.stdout.strip()}")
            return "WA", proc.stdout.strip()

        logger.error(f"Checker failed with return code {proc.returncode}")
        logger.error(f"Checker stderr: {proc.stderr}")
        return "WA", f"Checker error: {proc.stderr}"
    except subprocess.TimeoutExpired:
        logger.error("Checker timed out after 5 seconds")
        return "WA", "Checker timed out"
    except Exception as exc:
        logger.error(f"Error running checker: {exc}")
        return "WA", f"Checker error: {exc}"
    finally:
        logger.debug("Cleaning up temporary checker files")
        os.unlink(participant_path)
        os.unlink(jury_path)


def _string_compare(participant_output: str, jury_output: str) -> str:
    trim = lambda s: "\n".join(line.rstrip() for line in s.splitlines())
    if trim(participant_output) != trim(jury_output):
        logger.warning("Wrong answer detected via string comparison")
        return "WA"
    logger.debug("String comparison accepted the answer")
    return "AC"


def _initialize_report_file(output_path: str, include_checker_msg: bool):
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        if include_checker_msg:
            writer.writerow(["test", "res", "[sec]", "[mib]", "msg"])
        else:
            writer.writerow(["test", "res", "[sec]", "[mib]"])
    logger.debug(f"Created report file: {output_path}")


def _append_result(output_path: str, result: TestCaseResult, include_checker_msg: bool):
    with open(output_path, "a", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        row = [
            result.test_name + " ",
            result.verdict,
            f"{result.exec_time:.2f}",
            f"{result.mem_mib:.2f}",
        ]
        if include_checker_msg:
            if result.checker_msg:
                row.append(result.checker_msg[:100])
            else:
                row.append("-")
        writer.writerow(row)
    logger.debug(
        f"Test {result.test_name}: {result.verdict}, "
        f"time: {result.exec_time:.2f}s, mem: {result.mem_mib:.2f}MiB"
    )


def _resolve_output_path(sol_path: str, provided_output: Optional[str], cfg: ReporterConfig) -> str:
    if provided_output:
        return provided_output
    base_name = os.path.splitext(os.path.basename(sol_path))[0]
    default_name = f"{cfg.task_name}_{base_name}.tsv"
    default_path = os.path.join(cfg.reports_dir, default_name)
    logger.info(f"Output file not specified, using: {default_path}")
    return default_path


def _detect_language(sol_path: str) -> str:
    if sol_path.endswith(".cpp"):
        return "cpp"
    if sol_path.endswith(".py"):
        return "py"
    raise ValueError(f"Unsupported solution extension for {sol_path}")