#!/usr/bin/env python
# ------------------------------------------------------------------------------
#
# This script check out, compile and collect the list of excluded test classes
# of a given benchmark -- project -- bug.
#
# Usage:
# ./get_excluded_test_classes_maven_projects.py
#   --benchmark <benchmark>
#   --project <project>
#   --bug <bug>
#   --output_file <path>
#
# Requirements:
#   export PYTHONPATH=$RTA_FRAMEWORK_DIR/script:$PYTHONPATH
#
# ------------------------------------------------------------------------------

import argparse
import os
import sys
import re
import traceback
import subprocess
import xml.etree.ElementTree as ET
import fnmatch as FN

import utils

# RTA imports
from config     import JAVA_VERSION, JAVA8_HOME, TEST_TIMEOUT
from core.utils import get_benchmark

DEVNULL = open(os.devnull, 'r+b', 0)

# ------------------------------------------------------------------ Envs & Args

SCRIPT_DIR = os.path.abspath(os.path.dirname(sys.argv[0]))

parser = argparse.ArgumentParser(prog="get_excluded_test_classes_maven_projects", description='Checkout, compile and collect list of excluded test classes')
parser.add_argument("--benchmark",   required=True, help="Benchmark name, e.g., Bugs.jar")
parser.add_argument("--project",     required=True, help="Project name, e.g., Commons-Math")
parser.add_argument("--bug",         required=True, help="Bug id, e.g., 7")
parser.add_argument("--output_file", required=True, help="Output file path")

# Parse arguments
args        = parser.parse_args()
benchmark   = args.benchmark
project     = args.project
bug         = args.bug
output_file = args.output_file

if os.path.isfile(output_file):
    os.remove(output_file)

try:
   COLLECT_TEST_CLASSES_UTIL_JAR_FILE = os.environ['COLLECT_TEST_CLASSES_UTIL_JAR_FILE']
except KeyError:
   COLLECT_TEST_CLASSES_UTIL_JAR_FILE = SCRIPT_DIR + "/util/collect_test_classes/target/collecttestclasses-0.0.1-SNAPSHOT-jar-with-dependencies.jar"
   if not os.path.isfile(COLLECT_TEST_CLASSES_UTIL_JAR_FILE):
       print(COLLECT_TEST_CLASSES_UTIL_JAR_FILE + " does not exist!")
       sys.exit(1)

java_home_dir = JAVA8_HOME
os.environ['JAVA_VERSION'] = '8'

# ------------------------------------------------------------------------- Main

# Create required objects for RTA framework
benchmarkObj = get_benchmark(benchmark)
bugObj       = benchmarkObj.get_bug(project if benchmark == "QuixBugs" else project + "-" + bug)
CHECKOUT_DIR = os.path.abspath(os.path.join("/tmp", benchmark + "_" + project + "_" + bug))
utils.remove_checkout_dir(CHECKOUT_DIR)

#
# Print error message and exit.
#
def die(msg=""):
    utils.die(msg=msg, checkout_dir=CHECKOUT_DIR)

#
# Extracts from a pom.xml file the list of patterns to include/exclude.
#
def extract_include_exclude_patterns(pom_xml_file):
    print("Extracting include/exclude patterns from " + pom_xml_file)

    # Load the pom.xml file and get root element, i.e., <project>
    root = ET.parse(pom_xml_file).getroot()
    assert root != None
    xmlns = re.sub(r'project$', '', root.tag)

    patterns_to_be_included = []
    patterns_to_be_excluded = []

    maven_surefire_plugins = root.findall(".//" + xmlns + "plugin[" + xmlns + "artifactId='maven-surefire-plugin']")
    if (len(maven_surefire_plugins) == 0):
        print("No instance of the maven-surefire-plugin is defined in the pom.xml file!")
        try:
            print(ET.tostring(root, encoding='utf8').decode('utf8'))
        except UnicodeEncodeError:
            print("Failed to write to the stdout the content of the pom.xml file!")
        finally:
            return patterns_to_be_included, patterns_to_be_excluded

    for maven_surefire_plugin in maven_surefire_plugins:
        includes = maven_surefire_plugin.findall(".//" + xmlns + "configuration/" + xmlns + "includes/" + xmlns + "include")
        for include in includes:
            patterns_to_be_included.append(include.text)
        excludes = maven_surefire_plugin.findall(".//" + xmlns + "configuration/" + xmlns + "excludes/" + xmlns + "exclude")
        for exclude in excludes:
            patterns_to_be_excluded.append(exclude.text)

    return patterns_to_be_included, patterns_to_be_excluded

try:

#
# Checkout
#

    checkout = utils.checkout(bugObj, CHECKOUT_DIR, rm_tests=False, buggy_version=True)
    if checkout == 0:
        die("Checkout procedure has failed!")

#
# Compile
#

    compile_log_path = os.path.join(CHECKOUT_DIR, "compile.log")
    compile = utils.compile(bugObj, CHECKOUT_DIR, java_home_dir, compile_log_path)
    if compile == 0:
        print("Compile procedure has failed!")
        print(open(compile_log_path, "r").read())
        sys.exit(0)

#
# Get failing module name/path
#

    failing_module_dir = benchmarkObj.failing_module(bugObj)
    working_dir = os.path.abspath(os.path.join(CHECKOUT_DIR, failing_module_dir))
    assert os.path.isdir(working_dir),"Directory '" + working_dir + "' does not exist!"

    deps = benchmarkObj.classpath(bugObj)
    print("Deps: " + deps)

    bin_folder = str(benchmarkObj.bin_folders(bugObj)[0])
    abs_bin_folder = os.path.abspath(os.path.join(CHECKOUT_DIR, bin_folder))
    print("BinFolder: " + bin_folder)
    print("AbsBinFolder: " + abs_bin_folder)
    assert os.path.isdir(abs_bin_folder),"Directory '" + abs_bin_folder + "' does not exist!"

    test_bin_folder = str(benchmarkObj.test_bin_folders(bugObj)[0])
    abs_test_bin_folder = os.path.abspath(os.path.join(CHECKOUT_DIR, test_bin_folder))
    print("TestBinFolder: " + test_bin_folder)
    print("AbsTestBinFolder: " + abs_test_bin_folder)
    assert os.path.isdir(abs_test_bin_folder),"Directory '" + abs_test_bin_folder + "' does not exist!"

#
# Get tests folder path
#

    tests_dir = os.path.abspath(os.path.join(CHECKOUT_DIR, str(benchmarkObj.test_folders(bugObj)[0])))
    assert os.path.isdir(tests_dir),"Directory '" + tests_dir + "' does not exist!"

#
# Get list of excluded test classes
#

    # bug's pom.xml file
    pom_xml_file = os.path.abspath(os.path.join(working_dir, "pom.xml"))
    if not os.path.isfile(pom_xml_file):
        print("As there is no 'pom.xml' file, no maven-surefire-plugin can be analyzed!")
        sys.exit(0)

    patterns_to_be_included = []
    patterns_to_be_excluded = []

    a, b = extract_include_exclude_patterns(pom_xml_file)
    patterns_to_be_included.extend(a)
    patterns_to_be_excluded.extend(b)

    # super's pom.xml file
    pom_dir = working_dir
    while pom_dir != CHECKOUT_DIR:
        pom_dir = os.path.abspath(os.path.join(pom_dir, ".."))
        pom_xml_file = os.path.abspath(os.path.join(pom_dir, "pom.xml"))
        if os.path.isfile(pom_xml_file):
            a, b = extract_include_exclude_patterns(pom_xml_file)
            patterns_to_be_included.extend(a)
            patterns_to_be_excluded.extend(b)

    if (len(patterns_to_be_included) == 0 and len(patterns_to_be_excluded) == 0):
        print("No <include> and/or <exclude> has been defined!")
        sys.exit(0)

    java_files_to_be_included = []
    java_files_to_be_excluded = []

    for root, directories, files in os.walk(tests_dir):
        for file in files:
            if file.endswith('.java'):
                absolute_path_file = os.path.abspath(os.path.join(root, file))
                relative_path_file = absolute_path_file.replace(tests_dir + "/", '')
                print("* " + absolute_path_file)

                to_be_included = False if len(patterns_to_be_included) > 0 else None
                to_be_excluded = False if len(patterns_to_be_excluded) > 0 else None
                assert to_be_included != None or to_be_excluded != None

                for pattern_to_be_included in patterns_to_be_included:
                    if FN.fnmatch(absolute_path_file, pattern_to_be_included):
                        to_be_included = True
                        print("    " + str(absolute_path_file) + " matches include pattern: " + str(pattern_to_be_included))
                        break
                    else:
                        print("    " + str(absolute_path_file) + " does not match include pattern: " + str(pattern_to_be_included))

                for pattern_to_be_excluded in patterns_to_be_excluded:
                    if FN.fnmatch(absolute_path_file, pattern_to_be_excluded):
                        to_be_excluded = True
                        print("    " + str(absolute_path_file) + " matches exclude pattern: " + str(pattern_to_be_excluded))
                        break
                    else:
                        print("    " + str(absolute_path_file) + " does not match exclude pattern: " + str(pattern_to_be_excluded))

                if to_be_included == None and to_be_excluded == True:
                    # if <includes> is not defined, <excludes> is defined, and the
                    # java files matches it, exclude the java file
                    java_files_to_be_excluded.append(relative_path_file)
                    print("    " + str(relative_path_file) + " goes to the exclude bucket")
                elif to_be_included == None and to_be_excluded == False:
                    # if <includes> is not defined, <excludes> is defined, and the
                    # java files does not matches it, include the java file
                    java_files_to_be_included.append(relative_path_file)
                    print("    " + str(relative_path_file) + " goes to the include bucket")

                elif to_be_included == True and to_be_excluded == None:
                    # if <excludes> is not defined, <includes> is defined, and the
                    # java files matches it, include the java file
                    java_files_to_be_included.append(relative_path_file)
                    print("    " + str(relative_path_file) + " goes to the include bucket")
                elif to_be_included == False and to_be_excluded == None:
                    # if <excludes> is not defined, <includes> is defined, and the
                    # java files does not matches it, exclude the java file
                    java_files_to_be_excluded.append(relative_path_file)
                    print("    " + str(relative_path_file) + " goes to the exclude bucket")

                elif to_be_included == True and to_be_excluded == False:
                    # if <includes> is defined, <excludes> is defined, and the java
                    # files matches the include and does not match the exclude,
                    # include the java file
                    java_files_to_be_included.append(relative_path_file)
                    print("    " + str(relative_path_file) + " goes to the include bucket")
                elif to_be_included == True and to_be_excluded == True:
                    # if <includes> is defined, <excludes> is defined, and the java
                    # files matches the include and matches the exclude, exclude the
                    # java file
                    java_files_to_be_excluded.append(relative_path_file)
                    print("    " + str(relative_path_file) + " goes to the exclude bucket")

                elif to_be_included == False and to_be_excluded == True:
                    # if <includes> is defined, <excludes> is defined, and the
                    # java files does not match the include but matches the exclude,
                    # exclude the java file
                    java_files_to_be_excluded.append(relative_path_file)
                    print("    " + str(relative_path_file) + " goes to the exclude bucket")
                elif to_be_included == False and to_be_excluded == False:
                    # if <includes> is defined, <excludes> is defined, and the
                    # java files does not match the include and does not match the
                    # exclude, exclude the java file
                    java_files_to_be_excluded.append(relative_path_file)
                    print("    " + str(relative_path_file) + " goes to the exclude bucket")

                else:
                    raise Exception("Unexpected configuration!")

    java_files_to_be_included = list(set(java_files_to_be_included)) # remove duplicates, if any
    java_files_to_be_excluded = list(set(java_files_to_be_excluded)) # remove duplicates, if any

    if len(java_files_to_be_excluded) > 0:

        #
        # Filter out .java files that are not test classes
        #

        tests_classes_file = os.path.abspath(os.path.join(CHECKOUT_DIR, "test-classes.txt"))
        cmd = """
        export JAVA_HOME="%s";
        export PATH="$JAVA_HOME/bin:$PATH";
        timeout -s KILL %s java -ea -cp %s:%s:%s:%s collecttestclasses.Main %s %s
        """ % (java_home_dir, TEST_TIMEOUT, abs_bin_folder, abs_test_bin_folder, deps, COLLECT_TEST_CLASSES_UTIL_JAR_FILE, abs_test_bin_folder, tests_classes_file)
        process = subprocess.Popen(cmd, shell=True, stdin=DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
        # Wait for the process to terminate
        process.wait()
        # Check exit code
        exit_code = process.returncode
        if exit_code != 0:
            raise Exception("Collection of test classes has failed!")

        # Load classes identified as JUnit test classes
        test_classes_found = []
        with open(tests_classes_file) as f:
            for test_class in f:
                test_classes_found.append(test_class.rstrip())
        test_classes_found = list(set(test_classes_found)) # Remove duplicates, if any
        if len(test_classes_found) == 0:
            raise Exception("Found 0 tests!")

        # Filter out classes (aka .java files) that are not true test classes
        post_process_java_files_to_be_excluded = []
        for java_file_to_be_excluded in java_files_to_be_excluded:
            if str(java_file_to_be_excluded).replace('/', '.').replace('.java', '') in test_classes_found:
                post_process_java_files_to_be_excluded.append(java_file_to_be_excluded)

        if len(post_process_java_files_to_be_excluded) > 0:
            fd_output_file = open(output_file, "w")
            for java_file_to_be_excluded in post_process_java_files_to_be_excluded:
                fd_output_file.write("--- " + str(java_file_to_be_excluded).replace('/', '.').replace('.java', '') + "\n")

except SystemExit:
    if sys.exc_info()[1] != 0:
        traceback.print_exc()
    sys.exit(sys.exc_info()[1])
except:
    traceback.print_exc()
    die()
finally:
    utils.remove_checkout_dir(CHECKOUT_DIR) # Clean up

sys.exit(0)
