'''
Script drives the `pygenlib` workflow for the Radiotorni task:
1. Cleans previous artifacts, then generates tests for each subtask.
2. Records testgroup points, subtask, and public status in task.yaml.
3. Reports verdict, time, mem for each solution from running checker.
'''

# SCRIPT CONFIGURATION

# well-formed task name for prefixing test files and "reports"
task_name = "radiotorni"

# filepaths to external dependencies
solution_paths = [
    "../risin/kp_radiotorni_ok.cpp",
    "../risin/kp_radiotorni_brute_force.cpp",
    "../risin/vk_radiotorni_ok.cpp",]
checker_path = "./checker.cpp"
examples_dir = "./examples"

# ================================

from pygenlib.isolate import *
from pygenlib.testgen import Generator
from pygenlib.clean import clean
from pygenlib.report import Reporter
from pygenlib.tgyaml import TgYaml

logger = logging.getLogger(__name__)

# filepaths to generated files
tests_dir = "./tests"
reports_dir = "./reports"

reporter = Reporter(task_name, tests_dir=tests_dir, checker_path=checker_path)
tg_yaml = TgYaml()
record_tg = tg_yaml.record_tg

model_solution = solution_paths[0]
generator = Generator(task_name, model_solution, tests_dir=tests_dir)
def gen(tg_ext, *args):
    generator.gen(tg_ext, *args)

min_n = 2
max_n = 500000
max_freq = 10**9

def main():
    clean()
    # gen_tests()
    # tg_yaml.export()
    # gen_reports()

def gen_reports():
    logger.info("Generating reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    for sol in solution_paths:
        reporter.report(sol)


def gen_tests():
    logger.info("Generating test cases")
    os.makedirs(tests_dir, exist_ok=True)

    gen_subtask1()
    gen_subtask2()
    gen_subtask3()
    gen_subtask4()
    gen_subtask5()
    gen_subtask6()

def gen_subtask1():
    """Copy example files to tests directory"""
    logger.info("Copying example files to tests directory")
    for filename in os.listdir(examples_dir):
        logger.debug(f"Copying example file: {filename}")
        shutil.copy(examples_dir + "/" + filename, tests_dir + "/" + filename)

def gen_subtask2():
    """N <= 10, 13 points"""
    global max_freq
   
    curr_tg=1
    record_tg(st=2, tg=curr_tg, pts=2)
    gen(f"{curr_tg:02}a", 10, 1, 5, "star", "random", 1, 5)
    gen(f"{curr_tg:02}b", 10, 1, 5, "star", "walk", 1, 5)

    curr_tg+=1
    record_tg(st=2, tg=curr_tg, pts=2)
    gen(f"{curr_tg:02}a", 10, 1, 5, "random", "random", 1, 5)
    gen(f"{curr_tg:02}b", 10, 1, 5, "random", "walk", 1, 5)

    curr_tg+=1
    record_tg(st=2, tg=curr_tg, pts=3)
    gen(f"{curr_tg:02}a", 10, 1, 5, "binary", "random", 1, 5)
    gen(f"{curr_tg:02}b", 10, 1, 5, "binary", "walk", 1, 5)

    curr_tg+=1
    record_tg(st=2, tg=curr_tg, pts=3)
    gen(f"{curr_tg:02}a", 10, 1, max_freq, "random", "random", 1, max_freq)
    gen(f"{curr_tg:02}b", 10, 1, max_freq, "random", "walk", 1, max_freq)

    curr_tg+=1
    record_tg(st=2, tg=curr_tg, pts=3, public=True)
    gen(f"{curr_tg:02}a", 10, 1, 3, "random", "random", 1, 3)
    gen(f"{curr_tg:02}b", 10, 1, 3, "random", "walk", 1, 3)


def gen_subtask3():
    """L=K+1 (freq interval [l,l+1]), 18 points"""
    global max_n,max_freq
    sqrt_n = int(max_n**0.5)
    
    curr_tg=6
    record_tg(st=3, tg=curr_tg, pts=3)
    gen(f"{curr_tg:02}a", max_n, 9, 10, "star", "random", 9, 10)
    gen(f"{curr_tg:02}b", max_n, 9, 10, "star", "walk", 9, 10)

    curr_tg+=1
    record_tg(st=3, tg=curr_tg, pts=3)
    gen(f"{curr_tg:02}a", max_n, sqrt_n-1, sqrt_n, "star", "random", sqrt_n-1, sqrt_n)
    gen(f"{curr_tg:02}b", max_n, sqrt_n-1, sqrt_n, "star", "walk", sqrt_n-1, sqrt_n)

    curr_tg+=1
    record_tg(st=3, tg=curr_tg, pts=3)
    gen(f"{curr_tg:02}a", max_n, 9, 10, "binary", "random", 9, 10)
    gen(f"{curr_tg:02}b", max_n, 9, 10, "binary", "walk", 9, 10)

    curr_tg+=1
    record_tg(st=3, tg=curr_tg, pts=3)
    gen(f"{curr_tg:02}a", max_n, sqrt_n-1, sqrt_n, "binary", "random", sqrt_n-1, sqrt_n)
    gen(f"{curr_tg:02}b", max_n, sqrt_n-1, sqrt_n, "binary", "walk", sqrt_n-1, sqrt_n)

    curr_tg+=1
    record_tg(st=3, tg=curr_tg, pts=3)
    gen(f"{curr_tg:02}a", max_n, max_freq-1, max_freq, "random", "random", max_freq-1, max_freq)
    gen(f"{curr_tg:02}b", max_n, 9, 10, "random", "walk", 9, 10)

    curr_tg+=1
    record_tg(st=3, tg=curr_tg, pts=3, public=True)
    gen(f"{curr_tg:02}a", max_n, sqrt_n-1, sqrt_n, "random", "random", sqrt_n-1, sqrt_n)
    gen(f"{curr_tg:02}b", max_n, sqrt_n-1, sqrt_n, "random", "walk", sqrt_n-1, sqrt_n)

def gen_subtask4():
    """tree is a line graph, 20 points"""
    global max_n
    sqrt_n = int(max_n**0.5)

    curr_tg=12
    record_tg(st=4, tg=curr_tg, pts=10)
    gen(f"{curr_tg:02}a", max_n, 9, sqrt_n, "line", "random", 9, sqrt_n)
    gen(f"{curr_tg:02}b", max_n, 9, sqrt_n, "line", "walk", 9, sqrt_n)
    gen(f"{curr_tg:02}c", max_n, 1, 3, "line", "random", 1, 3)

    curr_tg+=1
    record_tg(st=4, tg=curr_tg, pts=10, public=True)
    gen(f"{curr_tg:02}a", max_n, 8, 10, "line", "random", 8, 10)
    gen(f"{curr_tg:02}b", max_n, 8, 10, "line", "walk", 8, 10)

def gen_subtask5():
    """all frequencies are the same ([x,x]), 21 points"""
    global max_n
    sqrt_n = int(max_n**0.5)
    
    curr_tg=14
    record_tg(st=5, tg=curr_tg, pts=8)
    gen(f"{curr_tg:02}a", max_n, 10, 10, "star", "random", 8, 12)
    gen(f"{curr_tg:02}b", max_n, 10, 10, "star", "walk", 8, 12)
    gen(f"{curr_tg:02}c", max_n, sqrt_n, sqrt_n, "star", "random", sqrt_n-2, sqrt_n+2)
    gen(f"{curr_tg:02}d", max_n, sqrt_n, sqrt_n, "star", "walk", sqrt_n-2, sqrt_n+2)

    curr_tg+=1
    record_tg(st=5, tg=curr_tg, pts=8)
    gen(f"{curr_tg:02}a", max_n, 10, 10, "binary", "random", 8, 12)
    gen(f"{curr_tg:02}b", max_n, 10, 10, "binary", "walk", 8, 12)
    gen(f"{curr_tg:02}c", max_n, sqrt_n, sqrt_n, "binary", "random", sqrt_n-2, sqrt_n+2)
    gen(f"{curr_tg:02}d", max_n, sqrt_n, sqrt_n, "binary", "walk", sqrt_n-2, sqrt_n+2)

    curr_tg+=1
    record_tg(st=5, tg=curr_tg, pts=5, public=True)
    gen(f"{curr_tg:02}a", max_n, 10, 10, "random", "random", 8, 12)
    gen(f"{curr_tg:02}b", max_n, 10, 10, "random", "walk", 8, 12)
    gen(f"{curr_tg:02}c", max_n, sqrt_n, sqrt_n, "random", "random", sqrt_n-2, sqrt_n+2)
    gen(f"{curr_tg:02}d", max_n, sqrt_n, sqrt_n, "random", "walk", sqrt_n-2, sqrt_n+2)

def gen_subtask6():
    """no additional restrictions, 28 points"""
    global max_n
    sqrt_n = int(max_n**0.5)

    curr_tg=17
    record_tg(st=6, tg=curr_tg, pts=6)
    gen(f"{curr_tg:02}a", max_n, 1, 10, "star", "random", 1, 10)
    gen(f"{curr_tg:02}b", max_n, 1, 10, "star", "walk", 1, 11)
    gen(f"{curr_tg:02}c", max_n, 1, sqrt_n, "star", "random", 1, sqrt_n+1)
    gen(f"{curr_tg:02}d", max_n, 1, sqrt_n, "star", "walk", 1, sqrt_n)

    curr_tg+=1
    record_tg(st=6, tg=curr_tg, pts=6)
    gen(f"{curr_tg:02}a", max_n, 1, 10, "line", "random", 1, 11)
    gen(f"{curr_tg:02}b", max_n, 1, 10, "line", "walk", 1, 10)
    gen(f"{curr_tg:02}c", max_n, 1, sqrt_n, "line", "random", 1, sqrt_n)
    gen(f"{curr_tg:02}d", max_n, 1, sqrt_n, "line", "walk", 1, sqrt_n+1)

    curr_tg+=1
    record_tg(st=6, tg=curr_tg, pts=6)
    gen(f"{curr_tg:02}a", max_n, 1, 10, "binary", "random", 1, 10)
    gen(f"{curr_tg:02}b", max_n, 1, 10, "binary", "walk", 1, 11)
    gen(f"{curr_tg:02}c", max_n, 1, sqrt_n, "binary", "random", 1, sqrt_n+1)
    gen(f"{curr_tg:02}d", max_n, 1, sqrt_n, "binary", "walk", 1, sqrt_n+1)

    curr_tg+=1
    record_tg(st=6, tg=curr_tg, pts=10,public=True)
    gen(f"{curr_tg:02}a", max_n, 1, 10, "random", "random", 1, 10)
    gen(f"{curr_tg:02}b", max_n, 1, 10, "random", "walk", 1, 11)
    gen(f"{curr_tg:02}c", max_n, 1, sqrt_n, "random", "random", 1, sqrt_n+1)
    gen(f"{curr_tg:02}d", max_n, 1, sqrt_n, "random", "walk", 1, sqrt_n+1)

if __name__ == "__main__":
    main()
