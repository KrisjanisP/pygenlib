from dataclasses import dataclass
from pygenlib.isolate import run_cpp_code, run_py_code
import csv
import logging
import os
import shutil
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

class Reporter:
    def __init__(self, task_name, tests_dir, checker_path, testlib_path, cache_dir):
        """Initialize the reporter with task name and optional checker.
        
        Args:
            task_name: Name of the task
            tests_dir: Directory where test files are located
            checker_path: Path to the checker executable or source file (.cpp)
            testlib_path: Path to the testlib.h file
            cache_dir: Directory to cache compiled executables
        """
        self.task_name = task_name
        self.tests_dir = tests_dir
        self.checker_path = checker_path
        self.testlib_path = testlib_path
        self.cache_dir = cache_dir
        self.checker_executable = None
        logger.info(f"Reporter initialized for task: {task_name}, tests directory: {tests_dir}")
        if checker_path:
            logger.info(f"Using checker at: {checker_path}")

    def _compile_checker(self):
        """Compile the checker if it's a .cpp file"""
        if not os.path.exists(self.checker_path):
            logger.error(f"Checker file not found: {self.checker_path}")
            return

        # Create a unique name for the checker executable based on the checker path
        checker_hash = hashlib.md5(self.checker_path.encode()).hexdigest()
        checker_exe_path = os.path.join(self.cache_dir, f"checker_{checker_hash}")

        # Check if the checker is already compiled and cached
        if os.path.exists(checker_exe_path):
            logger.info(f"Using cached checker: {checker_exe_path}")
            self.checker_executable = checker_exe_path
            return
            
        # Copy testlib.h and checker.cpp to the cache directory
        logger.debug(f"Reading testlib from: {self.testlib_path}")
        with open(self.testlib_path, "r") as f:
            testlib_content = f.read()
        
        testlib_cache_path = os.path.join(self.cache_dir, "testlib.h")
        logger.debug(f"Writing testlib to cache: {testlib_cache_path}")
        with open(testlib_cache_path, "w") as f:
            f.write(testlib_content)
        
        logger.debug(f"Reading checker from: {self.checker_path}")
        with open(self.checker_path, "r") as f:
            checker_content = f.read()
        
        checker_cache_path = os.path.join(self.cache_dir, "checker.cpp")
        logger.debug(f"Writing checker to cache: {checker_cache_path}")
        with open(checker_cache_path, "w") as f:
            f.write(checker_content)
        
        # Compile the checker
        self.checker_executable = checker_exe_path
        compile_cmd = ["g++", "-std=c++17", "-O2", checker_cache_path, "-o", self.checker_executable]
        logger.info(f"Compiling checker with command: {' '.join(compile_cmd)}")
        
        try:
            subprocess.run(compile_cmd, check=True)
            logger.info(f"Checker compiled successfully: {self.checker_executable}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to compile checker: {e}")
            self.checker_executable = None

    def _run_checker(self, input_file, participant_output, jury_output):
        """Run the checker on a test case.
        
        Args:
            input_file: Path to input file
            participant_output: Participant's output as string
            jury_output: Jury's output as string
            
        Returns:
            Tuple (verdict, message) where verdict is "AC" or "WA" and message is the checker output
        """
        
        if not self.checker_executable:
            logger.warning("Checker not available, falling back to string comparison")
            # trim removes trailing newlines and space at the end of each line
            trim = lambda s: "\n".join(line.rstrip() for line in s.splitlines())
            result = "AC" if trim(participant_output) == trim(jury_output) else "WA"
            logger.debug(f"String comparison result: {result}")
            return result, ""
        
        # Create temporary files for participant and jury outputs
        logger.debug("Creating temporary files for checker inputs")
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as participant_file:
            participant_file.write(participant_output)
            participant_path = participant_file.name
        
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as jury_file:
            jury_file.write(jury_output)
            jury_path = jury_file.name
        
        try:
            # Run the checker
            checker_cmd = [self.checker_executable, input_file, participant_path, jury_path]
            logger.debug(f"Running checker: {' '.join(checker_cmd)}")
            proc = subprocess.run(
                checker_cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if proc.returncode == 0:
                logger.debug("Checker returned AC")
                return "AC", proc.stdout.strip()
            elif proc.returncode == 1:
                logger.debug(f"Checker returned WA: {proc.stdout.strip()}")
                return "WA", proc.stdout.strip()
            else:
                logger.error(f"Checker failed with return code {proc.returncode}")
                logger.error(f"Checker stderr: {proc.stderr}")
                return "WA", f"Checker error: {proc.stderr}"
                
        except subprocess.TimeoutExpired:
            logger.error("Checker timed out after 5 seconds")
            return "WA", "Checker timed out"
        except Exception as e:
            logger.error(f"Error running checker: {e}")
            return "WA", f"Checker error: {str(e)}"
        finally:
            # Clean up temporary files
            logger.debug("Cleaning up temporary checker files")
            os.unlink(participant_path)
            os.unlink(jury_path)

    def report(self, sol_path, output_file=None):
        """Generate a test report for a solution.
        
        Runs the solution on all test cases and generates a TSV report with results.
        The report includes test name, verdict (AC/WA/TLE/RE), CPU time and memory usage.

        Args:
            sol_path: Path to solution file (.cpp or .py)
            output_file: Path where to write the TSV report
        """
        if self.checker_path:
            if not self.checker_executable:
                logger.info("Checker executable not found, compiling...")
                os.makedirs(self.cache_dir, exist_ok=True)
                self._compile_checker()

        logger.info(f"Generating report for solution: {sol_path}")
        if output_file is None:
            output_file = sol_path.replace(".cpp", ".tsv").replace(".py", ".tsv")
            output_file = output_file.replace("../risin/", "./reports/")
            logger.info(f"Output file not specified, using: {output_file}")

        with open(sol_path, "r") as f:
            sol_code = f.read()
            logger.debug(f"Read solution code from {sol_path}, size: {len(sol_code)} bytes")

        with open(output_file, "w", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            if self.checker_executable:
                writer.writerow(["test", "res", "[sec]", "[mib]", "msg"])
            else:
                writer.writerow(["test", "res", "[sec]", "[mib]"])
            logger.debug(f"Created report file: {output_file}")

        test_files = sorted(f for f in os.listdir(self.tests_dir) if f.startswith(f"{self.task_name}.i"))
        logger.info(f"Found {len(test_files)} test files to process")
        
        for test_file in test_files:
            full_test_path = os.path.join(self.tests_dir, test_file)
            logger.info(f"Running test: {test_file}")
            result = self.run_test(
                full_test_path, sol_code, "cpp" if sol_path.endswith(".cpp") else "py"
            )

            with open(output_file, "a", newline="") as f:
                writer = csv.writer(f, delimiter="\t")
                row = [
                    result.test_name+' ',
                    result.verdict,
                    f"{result.exec_time:.2f}",
                    f"{result.mem_mib:.2f}",
                ]
                if len(result.checker_msg) > 0:
                    row.append(result.checker_msg[:100])
                else:
                    row.append("-")
                writer.writerow(row)
                logger.debug(f"Test {result.test_name}: {result.verdict}, time: {result.exec_time:.2f}s, mem: {result.mem_mib:.2f}MiB")

        logger.info(f"Results written to {output_file}")

    def run_test(self, test_file: str, sol_code: str, lang: str) -> TestCaseResult:
        """Run solution on a single test case and return the result.

        Expects:
        - test_file to be the full path to the input file
        - sol_code to be a valid solution source code
        - lang to be a valid language ("cpp" or "py")

        Args:
            test_file: Input test file path
            sol_code: Solution source code
            lang: Programming language ("cpp" or "py")

        Returns:
            TestCaseResult containing verdict and performance metrics

        Raises:
            ValueError: If language is not supported
            SystemExit: If execution fails with unexpected status
        """
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

        # Get test name from file path (extract the part after .i)
        test_name = os.path.basename(test_file).split(".i")[1]
        logger.debug(f"Test name: {test_name}, execution status: {run_result.status}")
        
        # Get corresponding answer file
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
            # Use checker to verify the answer if available
            if self.checker_executable:
                logger.debug("Using checker to verify output")
                verdict, checker_msg = self._run_checker(test_file, run_result.stdout, answer)
            else:
                # Fallback to string comparison
                logger.debug("Using string comparison to verify output")
                trim = lambda s: "\n".join(line.rstrip() for line in s.splitlines())
                if trim(run_result.stdout) != trim(answer):
                    logger.warning(f"Wrong answer on test {test_name}")
                    verdict = "WA"
                else:
                    logger.debug(f"Correct answer on test {test_name}")

        logger.info(f"Test {test_name} result: {verdict}, time: {run_result.exec_time:.2f}s, memory: {run_result.cg_mem_kib/1024:.2f}MiB")
        
        return TestCaseResult(
            verdict=verdict,
            exec_time=run_result.exec_time,
            mem_mib=run_result.cg_mem_kib / 1024,
            test_name=test_name,
            checker_msg=checker_msg
        )

default_reporter = None
def set_reporter(reporter: Reporter):
    global default_reporter
    default_reporter = reporter

def set_reporter_params(task_name, tests_dir, checker_path="checker.cpp", testlib_path="testlib.h", cache_dir="./cache"):
    global default_reporter
    default_reporter = Reporter(task_name, tests_dir, checker_path, testlib_path, cache_dir)

def report(sol_path):
    global default_reporter
    default_reporter.report(sol_path)