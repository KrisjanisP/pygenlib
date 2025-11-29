import hashlib
from dataclasses import dataclass
import os
import subprocess
import tempfile
import shutil
import logging

from pygenlib import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class IsolateResult:
    """Result from running code in isolate sandbox"""
    stdout: str 
    stderr: str
    exit_code: int
    exec_time: float  # CPU time used
    wall_time: float  # Total wall clock time
    status: str  # "OK" or "TO" for timeout
    killed: bool  # Whether process was killed
    max_rss_kib: int  # Peak memory usage in KB
    cg_mem_kib: int  # Memory usage reported by cgroups

def run_cmd_in_isolate(command: str, 
                          isolate_args: dict = None,
                          stdin: str = "", box_path: str = None, time_limit: float = 5.0) -> IsolateResult:
    """Run arbitrary command in IOI isolate sandbox
    
    Args:
        command: Command to execute (e.g. "python3 solution.py 1 2 3")
        isolate_args: Dictionary of isolate parameters. Defaults to:
            {
                "mem": 2048000,      # Memory limit in KB
                "time": 50.0,        # CPU time limit
                "extra-time": 0.5,   # Extra time before kill
                "wall-time": 10.0,   # Wall clock limit
                "processes": 128,     # Max processes
                "open-files": 128,    # Max open files
                "dirs": ["/usr/include", "/usr"],  # Allowed directories
                "envs": {"HOME": "/box", "PATH": None}  # Environment vars
            }
        stdin: Input to feed to program
    """
    logger.debug(f"Running command in isolate: {command}")
    
    # Use default isolate arguments if none provided
    default_args = {
        "mem": 2048000,
        "time": time_limit,
        "extra-time": 0.5,
        "wall-time": time_limit*2,
        "processes": 128,
        "open-files": 128,
        "dirs": ["/usr/include", "/usr"],
        "envs": {"HOME": "/box", "PATH": None}
    }
    
    if isolate_args is None:
        isolate_args = default_args
    else:
        # Merge with defaults, allowing override
        merged = default_args.copy()
        merged.update(isolate_args)
        isolate_args = merged

    logger.debug(f"Using isolate args: {isolate_args}")

    # Start sandbox and get path
    if box_path is None:
        init_proc = subprocess.run(['isolate', '--init', '--cg'], 
                             capture_output=True, text=True)
        if init_proc.returncode != 0:
            logger.error(f"Failed to initialize isolate: {init_proc.stderr}")
        raise RuntimeError(f"Failed to initialize isolate: {init_proc.stderr}")
    
        box_path = init_proc.stdout.strip()
        logger.debug(f"Initialized sandbox at: {box_path}")
    
    try:
        # Build isolate command with parameters
        run_cmd = ["isolate", "--cg"]
        
        if isolate_args:
            # Add numeric parameters
            for param in ["mem", "time", "extra-time", "wall-time", "processes", "open-files"]:
                if param in isolate_args:
                    run_cmd.extend([f"--{param}={isolate_args[param]}"])
            
            # Add directory access
            if "dirs" in isolate_args:
                for dir_path in isolate_args["dirs"]:
                    run_cmd.extend([f"--dir={dir_path}"])
            
            # Add environment variables
            if "envs" in isolate_args:
                for env_name, env_value in isolate_args["envs"].items():
                    if env_value is None:
                        run_cmd.extend([f"--env={env_name}"])
                    else:
                        run_cmd.extend([f"--env={env_name}={env_value}"])
        
        # Add meta file
        meta_path = os.path.join("meta.txt")
        run_cmd.extend(["-M", meta_path])
        
        # Add command to execute
        run_cmd.extend(["-s", "--run", "--", f'/usr/bin/bash', '-c', f'{command}'])
        
        logger.debug(f"Running isolate command: {run_cmd}")
        run_proc = subprocess.run(run_cmd,
                                input=stdin,
                                capture_output=True,
                                text=True)

        # Parse meta file (same as before)
        meta = {}
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                for line in f:
                    if ":" in line:
                        key, value = line.strip().split(":", 1)
                        meta[key] = value
        
        os.remove(meta_path)
        result = IsolateResult(
            stdout=run_proc.stdout,
            stderr=run_proc.stderr,
            exit_code=run_proc.returncode,
            exec_time=float(meta.get("time", "0")),
            wall_time=float(meta.get("time-wall", "0")),
            status=meta.get("status", "OK"),
            killed=meta.get("killed", "0") == "1",
            max_rss_kib=int(meta.get("max-rss", "0")),
            cg_mem_kib=int(meta.get("cg-mem", "0"))
        )
        logger.debug(f"Command completed with status: {result.status}, exit code: {result.exit_code}")
        return result
    finally:
        logger.debug("Cleaning up sandbox")
        subprocess.run(["isolate", "--cleanup", "--cg"])

def _init_sandbox() -> str:
    """Initialize isolate sandbox and return box path and stdin path"""
    logger.debug("Initializing sandbox")
    init_proc = subprocess.run(['isolate', '--init', '--cg'], 
                             capture_output=True, text=True)
    if init_proc.returncode != 0:
        logger.error(f"Failed to initialize isolate: {init_proc.stderr}")
        raise RuntimeError(f"Failed to initialize isolate: {init_proc.stderr}")
    
    box_path = init_proc.stdout.strip()
    logger.debug(f"Sandbox initialized at: {box_path}")
    return box_path


def run_cpp_code(source_code: str, stdin: str, time_limit: float = 5.0, args: list = None, additional_files: dict = None) -> IsolateResult:
    """Run C++ code in IOI isolate sandbox
    
    Args:
        source_code: C++ source code to compile and run
        stdin: Input to feed to program
        time_limit: Time limit in seconds
        args: Command line arguments to pass to program
        additional_files: Dictionary mapping filenames to file contents to include in compilation directory
    """
    logger.debug("Running C++ code")
    box_path = _init_sandbox()
    
    # Calculate checksum of source and additional files
    m = hashlib.sha256()
    m.update(source_code.encode())
    if additional_files:
        for filename in sorted(additional_files.keys()):
            m.update(filename.encode())
            m.update(additional_files[filename].encode())
    checksum = m.hexdigest()
    
    # Check cache directory
    cache_dir = config.get_cache_dir_path()
    os.makedirs(cache_dir, exist_ok=True)
    cached_exe = os.path.join(cache_dir, checksum)
    
    if os.path.exists(cached_exe):
        logger.debug("Found cached executable")
        # Copy from cache to sandbox
        box_exe_path = os.path.join(box_path, "box", "solution")
        shutil.copy2(cached_exe, box_exe_path)
        assert os.path.exists(box_exe_path)
        return run_cmd_in_isolate(f"./solution {' '.join(args) if args else ''}", None, stdin, box_path=box_path, time_limit=time_limit)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set up compilation
        src_path = os.path.join(tmpdir, "solution.cpp")
        exe_name = "solution"
        
        # Write source
        logger.debug(f"Writing source to {src_path}")
        with open(src_path, "w") as f:
            f.write(source_code)

        # Write any additional files
        if additional_files:
            for filename, content in additional_files.items():
                file_path = os.path.join(tmpdir, filename)
                logger.debug(f"Writing additional file: {file_path}")
                with open(file_path, "w") as f:
                    f.write(content)

        # Compile
        logger.info("Compiling C++ code")
        compile_cmd = ["g++", "-O2", "-std=c++17", src_path, "-o", 
                        os.path.join(tmpdir, exe_name)]
        
        compile_proc = subprocess.run(compile_cmd,
                                      cwd=tmpdir,
                                    capture_output=True,
                                    text=True)
        if compile_proc.returncode != 0:
            logger.error(f"Compilation failed: {compile_proc.stderr}")
            raise RuntimeError(f"Compilation failed: {compile_proc.stderr}")

        # Cache the executable
        logger.debug(f"Caching executable to {cached_exe}")
        shutil.copy2(os.path.join(tmpdir, exe_name), cached_exe)

        # Move executable to sandbox
        box_exe_path = os.path.join(box_path, "box", exe_name)
        logger.debug(f"Moving executable to sandbox: {box_exe_path}")
        shutil.copy2(os.path.join(tmpdir, exe_name), box_exe_path)
        
        # make sure that the executable is in the box
        assert os.path.exists(box_exe_path)

        return run_cmd_in_isolate(f"./{exe_name} {' '.join(args) if args else ''}", None, stdin, box_path=box_path, time_limit=time_limit)

def run_py_code(source_code: str, stdin: str, time_limit: float = 5.0, extra_args: list = None) -> IsolateResult:
    """Run Python code in IOI isolate sandbox"""
    logger.debug("Running Python code")
    box_path = _init_sandbox()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set up file
        src_path = os.path.join(tmpdir, "solution.py")
        exe_name = "solution.py"
        
        # Write source
        logger.debug(f"Writing source to {src_path}")
        with open(src_path, "w") as f:
            f.write(source_code)

        # Move to sandbox
        box_exe_path = os.path.join(box_path, "box", exe_name)
        logger.debug(f"Moving script to sandbox: {box_exe_path}")
        shutil.copy2(src_path, box_exe_path)

        # Build command
        cmd = ["python3"]
        cmd.append(exe_name)
        
        return run_cmd_in_isolate(f"{' '.join(cmd)} {' '.join(extra_args) if extra_args else ''}", None, stdin, box_path=box_path, time_limit=time_limit)
