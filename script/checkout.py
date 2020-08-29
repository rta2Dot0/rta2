#!/usr/bin/env python

import argparse
import os
import sys

import utils
from core.utils import get_benchmark

parser = argparse.ArgumentParser(prog="checkout", description='Checkout bug')
parser.add_argument("--benchmark", "-b", required=True, default="Defects4J",
                        help="The benchmark to repair")
parser.add_argument("--id", "-i", required=True, help="The bug id")
parser.add_argument("--working_directory", "-w", required=True, help="The working directory")

if __name__ == "__main__":
    # Get arguments
    args              = parser.parse_args()
    benchmark         = args.benchmark
    bug_id            = args.id
    working_directory = args.working_directory

    # Create required objects for the RTA framework
    benchmarkObj = get_benchmark(benchmark)
    bugObj       = benchmarkObj.get_bug(bug_id)
    utils.remove_checkout_dir(working_directory)

    exclude_broken_tests = False
    buggy_version        = True
    if utils.checkout(bugObj, working_directory, exclude_broken_tests, buggy_version) == 0:
        die("Failed to checkout " + bug_id + "!")

    sys.exit(0)
