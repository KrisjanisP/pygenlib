from dataclasses import dataclass
import json
from typing import Mapping, Optional

from pygenlib import config
from pygenlib.isolate import run_cpp_code
import logging
import os

logger = logging.getLogger(__name__)


@dataclass
class GeneratorConfig:
    task_name: str
    model_solution_path: str
    generator_path: str
    testlib_header_path: str
    tests_dir: str

_default_generator_config: Optional[GeneratorConfig] = None

def override_generator_config(cfg: GeneratorConfig):
    """Set the default generator configuration used by the module-level gen function."""
    global _default_generator_config
    _default_generator_config = cfg

def gen(tg_ext, *args, cfg: Optional[GeneratorConfig] = None, extra_files: Optional[Mapping[str, str]] = None):
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
        cfg: Optional explicit configuration. If omitted, uses the stored default
            or falls back to the global configuration.
        extra_files: Optional mapping of filename -> file path or literal contents.
            Files are added alongside testlib.h inside the generator sandbox.
    """
    cfg = _resolve_generator_config(cfg)
    os.makedirs(cfg.tests_dir, exist_ok=True)

    logger.debug(f"Generating test {tg_ext} with args: {args}")
    args = [str(arg) for arg in args]
    args.append(tg_ext)

    with open(cfg.testlib_header_path, "r") as f:
        testlib_h = f.read()

    compile_files = {"testlib.h": testlib_h}
    run_files = _prepare_extra_files(extra_files)
    compile_files.update(run_files)

    with open(cfg.generator_path, "r") as f:
        gen_res = run_cpp_code(
            f.read(), "", args=args, extra_compile_files=compile_files, extra_run_files=run_files
        )
        if gen_res.exit_code != 0:
            logger.error(
                f"Generator {cfg.generator_path} returned exit code {gen_res.exit_code} "
                f"for test {tg_ext} with args {args}"
            )
            logger.error(f"Generator data: {json.dumps(gen_res.__dict__, indent=4)}")
            raise Exception(
                f"Generator {cfg.generator_path} returned exit code {gen_res.exit_code} "
                f"for test {tg_ext} with args {args}"
            )
        input_path = os.path.join(cfg.tests_dir, f"{cfg.task_name}.i{tg_ext}")
        with open(input_path, "w") as f_out:
            f_out.write(gen_res.stdout)

    with open(cfg.model_solution_path, "r") as f:
        model_sol_code = f.read()
        prog_res = run_cpp_code(model_sol_code, stdin=gen_res.stdout)
        if prog_res.exit_code != 0:
            logger.error(
                f"Model solution {cfg.model_solution_path} returned exit code {prog_res.exit_code} "
                f"for test {tg_ext} with args {args}"
            )
            logger.error(f"Model solution data: {json.dumps(prog_res.__dict__, indent=4)}")
            raise Exception(
                f"Model solution {cfg.model_solution_path} returned exit code {prog_res.exit_code} "
                f"for test {tg_ext} with args {args}"
            )
        output_path = os.path.join(cfg.tests_dir, f"{cfg.task_name}.o{tg_ext}")
        with open(output_path, "w") as f_out:
            f_out.write(prog_res.stdout)


def _resolve_generator_config(generator_config: Optional[GeneratorConfig]) -> GeneratorConfig:
    if generator_config is not None:
        return generator_config
    if _default_generator_config is not None:
        return _default_generator_config
    return GeneratorConfig(
        task_name=config.get_task_id(),
        model_solution_path=config.get_model_solution_path(),
        generator_path=config.get_testlib_gen_path(),
        testlib_header_path=config.get_testlib_header_path(),
        tests_dir=config.get_tests_dir_path(),
    )


def _prepare_extra_files(extra_files: Optional[Mapping[str, str]]) -> dict[str, str]:
    """Return mapping of filename->contents for extra files."""
    prepared: dict[str, str] = {}
    if not extra_files:
        return prepared
    for filename, src in extra_files.items():
        if os.path.isfile(src):
            with open(src, "r") as f:
                prepared[filename] = f.read()
        else:
            prepared[filename] = src
    return prepared