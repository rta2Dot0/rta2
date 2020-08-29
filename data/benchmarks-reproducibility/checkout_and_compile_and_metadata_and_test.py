#!/usr/bin/env python
# ------------------------------------------------------------------------------
#
# This script check out, compile, verify metadata, and run the test cases of a
# given benchmark, project, and bug.
#
# Usage:
# ./checkout_and_compile_and_metadata_and_test.py
#   --benchmark <benchmark>
#   --project <project>
#   --bug <bug>
#   --jvm <jvm>
#   --output_dir <path>
#   --exclude_broken <true/false>
#   --buggy_version <true/false>
#
# Requirements:
#   export PYTHONPATH=$RTA_FRAMEWORK_DIR/script:$PYTHONPATH
#
# ------------------------------------------------------------------------------

import argparse
import os
import sys
import traceback

import utils

# RTA imports
from config     import JAVA_VERSION, JAVA7_HOME, JAVA8_HOME
from core.utils import get_benchmark

# ------------------------------------------------------------------ Envs & Args

parser = argparse.ArgumentParser(prog="checkout_and_compile_and_metadata_and_test", description='Compile and Run test suites')
parser.add_argument("--benchmark",   required=True, help="Benchmark name, e.g., Bugs.jar")
parser.add_argument("--project",     required=True, help="Project name, e.g., Commons-Math")
parser.add_argument("--bug",         required=True, help="Bug id, e.g., 7")
parser.add_argument("--jvm",         required=True, help="Java version, either 7 or 8")
parser.add_argument("--output_dir",  required=True, help="Directory to write log files")
parser.add_argument("--exclude_broken", required=True, help="Exclude (true) or include (false) broken tests")
parser.add_argument("--buggy_version", required=True, help="Checkout the buggy version (true) or the fixed version (false)")

# Parse arguments
args        = parser.parse_args()
benchmark   = args.benchmark
project     = args.project
bug         = args.bug
jvm         = int(args.jvm)
output_dir  = os.path.abspath(args.output_dir)
exclude     = args.exclude_broken.lower()
buggy       = args.buggy_version.lower()

if not os.path.isdir(output_dir):
    os.makedirs(output_dir)

java_home_dir = JAVA8_HOME
os.environ['JAVA_VERSION'] = '8'
if jvm == 7:
    java_home_dir = JAVA7_HOME
    os.environ['JAVA_VERSION'] = '7'

# ------------------------------------------------------------------------- Main

# Create required objects for RTA framework
benchmarkObj = get_benchmark(benchmark)
bugObj       = benchmarkObj.get_bug(project if benchmark == "QuixBugs" else project + "-" + bug)
CHECKOUT_DIR = os.path.join("/tmp", benchmark + "_" + project + "_" + bug + "_java-" + str(jvm))
utils.remove_checkout_dir(CHECKOUT_DIR)

#
# File fields
#

checkout = "NA" # 1 success, 0 failure
compile  = "NA" # 1 success, 0 failure
metadata = "NA" # 1 success, 0 failure
test     = "NA" # 1 success, 0 failure
num_all_tests  = "NA" # Number of tests run
num_fail_tests = "NA" # Number of failing tests

fd_output_file = open(os.path.join(output_dir, "status.csv"), "w")
fd_output_file.write("benchmark,project,bug,java_version,exclude_broken_tests,buggy_version,checkout,compile,metadata,test,num_all_tests,num_failing_tests\n")

def print_row():
    fd_output_file.write(benchmark + "," + project + "," + str(bug) + "," + str(jvm) + "," +
                         str(exclude) + "," + str(buggy) + "," +
                         str(checkout) + "," + str(compile) + "," + str(metadata) + "," +
                         str(test) + "," + str(num_all_tests) + "," + str(num_fail_tests) + "\n")

#
# Print error message, remove checkout directory (if exists) and exit.
#
def die(msg=""):
    utils.die(msg=msg, checkout_dir=CHECKOUT_DIR)

try:

#
# Checkout
#

    exclude_broken_tests = True
    if exclude == "false":
        exclude_broken_tests = False

    buggy_version = True
    if buggy == "false":
        buggy_version = False

    checkout = utils.checkout(bugObj, CHECKOUT_DIR, exclude_broken_tests, buggy_version)
    if checkout == 0:
        die()

#
# Compile
#

    compile = utils.compile(bugObj, CHECKOUT_DIR, java_home_dir, os.path.join(output_dir, "compile.log"))
    if compile == 0:
        die()

#
# Metadata
#

    metadata = utils.metadata(bugObj, CHECKOUT_DIR)
    if metadata == 0:
        die()

#
# Test
#

    test, all_tests, failing_tests = utils.test(bugObj, CHECKOUT_DIR, java_home_dir, os.path.join(output_dir, "test.log"))
    if isinstance(test, (int, long)) and test == 0:
        die()

    num_all_tests = len(all_tests)
    num_fail_tests = len(failing_tests)

    utils.print_list_to_file(all_tests, os.path.join(output_dir, "all_tests.txt"))
    utils.print_list_to_file(failing_tests, os.path.join(output_dir, "failing_tests.txt"))

    # Clean up checkout directory
    utils.remove_checkout_dir(CHECKOUT_DIR)

except:
    traceback.print_exc()
    die()
finally:
    print_row()

sys.exit(0)
