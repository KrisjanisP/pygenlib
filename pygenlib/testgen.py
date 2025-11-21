from pygenlib.isolate import run_cpp_code
import logging
import os

logger = logging.getLogger(__name__)

class Generator:
    def __init__(self, task_name, model_sol, gen_cpp_path="gen.cpp", testlib_path="testlib.h", tests_dir="./tests"):
        """Initialize the generator with task name and model solution.
        
        Args:
            task_name: Name of the task
            model_sol: Path to the model solution
            gen_cpp_path: Path to the generator cpp file
            testlib_path: Path to the testlib.h file
            tests_dir: Directory where test files will be saved
        """
        self.task_name = task_name
        self.model_sol = model_sol
        self.gen_cpp_path = gen_cpp_path
        self.testlib_path = testlib_path
        self.tests_dir = tests_dir
        
        # Ensure tests directory exists
        os.makedirs(self.tests_dir, exist_ok=True)
    
    def gen(self, tg_ext, *args):
        """Generate input and expected output (answer) for a test case.

        1. Adds testlib.h and gen.cpp to the isolate sandbox.
        2. Runs gen.cpp with the given args to generate the input.
        3. Saves the input to {tests_dir}/{task_name}.i{tg_ext}
        4. Adds model solution to a new isolate sandbox.
        5. Runs the model solution on the input to generate the expected output.
        6. Saves the expected output to {tests_dir}/{task_name}.o{tg_ext}

        Args:
            tg_ext: Suffix for the test case (e.g. "00a", "00b")
            args: list of arguments to pass to the generator
        """
        logger.info(f"Generating test {tg_ext} with args: {args}")
        args = [str(arg) for arg in args]
        # add testgroup as the last argument
        args.append(tg_ext)
        with open(self.testlib_path, "r") as f:
            testlib_h = f.read()

        with open(self.gen_cpp_path, "r") as f:
            gen_res = run_cpp_code(
                f.read(), "", args=args, additional_files={"testlib.h": testlib_h}
            )
            assert gen_res.exit_code == 0
            input_path = os.path.join(self.tests_dir, f"{self.task_name}.i{tg_ext}")
            with open(input_path, "w") as f:
                f.write(gen_res.stdout)

        with open(self.model_sol, "r") as f:
            model_sol_code = f.read()
            prog_res = run_cpp_code(model_sol_code, stdin=gen_res.stdout)
            if prog_res.exit_code != 0:
                logger.error(f"Model solution {self.model_sol} returned exit code {prog_res.exit_code} for test {tg_ext} with args {args}")
                import json
                logger.error(f"Model solution data: {json.dumps(prog_res.__dict__, indent=4)}")
                raise Exception(f"Model solution {self.model_sol} returned exit code {prog_res.exit_code} for test {tg_ext} with args {args}")
            output_path = os.path.join(self.tests_dir, f"{self.task_name}.o{tg_ext}")
            with open(output_path, "w") as f:
                f.write(prog_res.stdout)
