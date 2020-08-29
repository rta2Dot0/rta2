#!/usr/bin/env python
# ------------------------------------------------------------------------------
#
# This script collects all maven dependencies of a given benchmark, project, and
# bug from the maven central repository.
# 
#
# Usage:
# ./get-mvn-deps.py
#   --benchmark <benchmark>
#   --project <project>
#   --bug <bug>
#   --mtwo_dir <path>
#
# Requirements:
#   export PYTHONPATH=$REPAIR_THEM_ALL_FRAMEWORK_DIR/script:$PYTHONPATH
#
# ------------------------------------------------------------------------------

import argparse
import os
import sys
import shutil

# RTA imports
from config     import REPAIR_ROOT, JAVA7_HOME, JAVA8_HOME
from core.utils import get_benchmark
from core.utils import run_cmd
from filelock   import FileLock

LOCK_FILE = "LOCK_INIT"

# ------------------------------------------------------------------ Envs & Args

parser = argparse.ArgumentParser(prog="get-mvn-deps", description='Download all maven dependencies from the maven central repository')
parser.add_argument("--benchmark",   required=True, help="Benchmark name, e.g., Bugs.jar")
parser.add_argument("--project",     required=True, help="Project name, e.g., Commons-Math")
parser.add_argument("--bug",         required=True, help="Bug id, e.g., 7")
parser.add_argument("--mtwo_dir",    required=True, help=".m2 directory")

# Parse arguments
args        = parser.parse_args()
benchmark   = args.benchmark
project     = args.project
bug         = args.bug
mtwo_dir    = args.mtwo_dir

java_home_dir = os.path.abspath(os.path.join(JAVA8_HOME, ".."))

# ------------------------------------------------------------------------- Util

#
# Print error message and exit.
#
def die(msg=""):
    sys.stderr.write(msg)
    sys.exit(1)

#
# Remove the checkout directory.
#
def remove_checkout_dir(checkout_dir):
    if checkout_dir != None and os.path.isdir(checkout_dir):
        shutil.rmtree(checkout_dir)

#
# Checkout a Bug instance to a defined directory.
#
# Returns 0 if checkout is performed successfully, 1 otherwise.
#
def checkout(bug, checkout_dir):
    print("Checkout " + str(bug))

    lock = FileLock(os.path.join(REPAIR_ROOT, LOCK_FILE))
    try:
        lock.acquire()
        bug.checkout(checkout_dir, False)
    finally:
        lock.release()

    if not os.path.isdir(checkout_dir):
        sys.stderr.write("The checkout directory '" + checkout_dir + "' does not exist!\n")
        return 1

    return 0 # Success

# ------------------------------------------------------------------------- Main

# Create required objects for RTA framework
benchmarkObj = get_benchmark(benchmark)
bugObj       = benchmarkObj.get_bug(project if benchmark == "QuixBugs" else project + "-" + bug)
CHECKOUT_DIR = os.path.join("/tmp", benchmark + "_" + project + "_" + bug)
remove_checkout_dir(CHECKOUT_DIR)

#
# Checkout
#
try:
    checkout_exit_code = checkout(bugObj, CHECKOUT_DIR)
    if checkout_exit_code != 0:
        die()
except:
    die()

#
# Get all dependencies
#

if str(benchmark) == "Bear" and str(project) == "dhis2-dhis2-core" and str(bug) == "365246679-365386294":
    fix_pom_cmd = "sed -i 's|http://download.osgeo.org/webdav/geotools/|https://repo.osgeo.org/repository/release/|g' %s/dhis-2/pom.xml" %(CHECKOUT_DIR)
    run_cmd(fix_pom_cmd, sys.stdout, sys.stderr)

cmd  = "export JAVA_HOME=\"%s\"; export PATH=\"$JAVA_HOME/bin:$PATH\";" %(java_home_dir)
cmd += " cd %s; find . -type f -name pom.xml | while read -r pom_file; do dir=$(dirname $pom_file); (cd $dir; mvn dependency:go-offline -Dmaven.repo.local=%s --fail-never;) done" %(CHECKOUT_DIR, mtwo_dir)
cmd_exit_code = run_cmd(cmd, sys.stdout, sys.stderr)

# Clean up checkout directory
remove_checkout_dir(CHECKOUT_DIR)

sys.exit(cmd_exit_code)
