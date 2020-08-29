#!/usr/bin/env python
# ------------------------------------------------------------------------------
#
# This script provides helper functions for the RepairThemAll framework.
#
# Usage:
#   import utils
#
# Requirements:
#   export PYTHONPATH=$RTA_FRAMEWORK_DIR/script:$PYTHONPATH
#
# ------------------------------------------------------------------------------

import os
import glob
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

# RTA imports
from config import REPAIR_ROOT
from core.utils import run_cmd
from filelock import FileLock

LOCK_FILE = "LOCK_INIT"

#
# Print error message, remove checkout directory (if exists) and exit.
#
def die(msg="", checkout_dir=None):
    sys.stderr.write(msg)
    remove_checkout_dir(checkout_dir)
    sys.exit(1)

#
# Remove the checkout directory
#
def remove_checkout_dir(checkout_dir):
    if checkout_dir != None and os.path.isdir(checkout_dir):
        shutil.rmtree(checkout_dir)

#
# Copy a file to another directory.
#
def copy_file(src, dest):
    if not os.path.isfile(src):
        die("'" + src + "' does not exist!\n")
    shutil.copyfile(src, dest)

#
# Cat a file to the stdout.
#
def print_log_file(file):
    if not os.path.isfile(file):
        die("The log file '" + file + "' does not exist!\n")
    with open(file, 'r') as fin:
        print(fin.read())

#
#
#
def print_list_to_file(list, file):
    with open(file, 'w') as file_handler:
        for item in list:
            file_handler.write("{}\n".format(item.encode('utf-8').strip()))

#
# Checkout a Bug instance to a defined directory.
#
# Returns 1 if checkout is performed successfully, 0 otherwise.
#
def checkout(bug, checkout_dir, rm_tests=True, buggy_version=True):
    print("Checkout " + str(bug))

    ret = 1 # Success
    lock = FileLock(os.path.join(REPAIR_ROOT, LOCK_FILE))
    try:
        lock.acquire()
        if bug.checkout(checkout_dir, rm_tests, buggy_version) != 0:
            ret = 0 # Failure
    finally:
        lock.release()

    if not os.path.isdir(checkout_dir):
        sys.stderr.write("The checkout directory '" + checkout_dir + "' does not exist!\n")
        ret = 0 # Failure

    return ret

#
# Apply a patch to a provided checkout directory.
#
# Return 1 if the patch is applied successfully, 0 otherwise.
#
def apply_patch(benchmarkObj, bugObj, checkout_dir, tool, patch_file):

    if tool == "Nopol" or tool == "DynaMoth" or tool == "NPEFix":
        # Nopol, DynaMoth, and NPEFix patches look like git patches, i.e.,
        #   a/src/main/java/...
        #   b/src/main/java/...
        patch_command  = "cd %s; git init;" %(checkout_dir)
        patch_command += " git apply --ignore-whitespace --verbose -p1 < %s || exit 1;" %(patch_file)

    elif tool == "Arja" or tool == "GenProg" or tool == "Kali" or tool == "RSRepair":
        # Arja, GenProg, Kali, and RSRepair include the full path of each file to
        # patch
        patch_command  = "cd %s; git init;" %(checkout_dir)
        patch_command += " git apply --ignore-whitespace --verbose -p3 < %s || exit 1;" %(patch_file)

    elif tool == "Cardumen" or tool == "jGenProg" or tool == "jKali" or tool == "jMutRepair":
        # Cardumen, jGenProg, jKali, and jMutRepair are relative to the
        # source directory
        src_dir = os.path.join(checkout_dir, benchmarkObj.source_folders(bugObj)[0])
        # Need to handle overlap between src_dir and relative directory in patch header
        f = open(patch_file)
        header = f.readline()
        f.close()
        header = header[4:]
        header_segments = header.split("/")
        src_segments = src_dir.split("/")
        found = 0
        for segment in range(len(src_segments)):
            for h_segment in range(len(header_segments)):
                if src_segments[segment] == header_segments[h_segment]:
                    src_dir = "/".join(src_segments[0:segment])
                    found = 1
                    break
            if found == 1:
                break
        if not os.path.isdir(src_dir):
            die("Source directory '" + src_dir + "' does not exist!\n")
        patch_command  = "cd %s; git init;" %(checkout_dir)
        patch_command += " cd %s;" %(src_dir)
        patch_command += " git apply --ignore-whitespace --verbose -p0 < %s || exit 1;" %(patch_file)

    elif tool == "Developer":
        patch_command  = "cd %s; git init;" %(checkout_dir)
        patch_command += " git apply --ignore-whitespace --verbose < %s || exit 1;" %(patch_file)

    else:
        die("Tool '" + tool + "' not supported!\n", checkout_dir)

    if run_cmd(patch_command, sys.stdout, sys.stderr) == 0:
        return 1
    return 0

#
# Compile a Bug in a defined checkout directory under a Java version.
#
# Returns 1 if compilation is performed successfully, 0 otherwise.
#
def compile(bug, checkout_dir, java_home_dir, compile_log_file):
    print("Compile " + str(bug))

    compile_exit_code = bug.compile(java_home_dir)

    rta_compile_log_file = os.path.join(checkout_dir, "repair_them_all.compile.log")
    copy_file(rta_compile_log_file, compile_log_file)

    ret = "NA"
    if compile_exit_code == 0:
        ret = 1
    else:
        ret = 0
        sys.stderr.write("compile has failed!\n")

    return ret

#
# Sanity check the metadata of a given bug.
#
# Returns 1 if the sanity check is performed successfully, 0 otherwise.
#
def metadata(bug, checkout_dir):
    try:
        for source_folder in bug.source_folders():
            if not os.path.isdir(os.path.abspath(os.path.join(checkout_dir, source_folder))):
                sys.stderr.write("source_folder: " + source_folder + " does not exist!\n")
                return 0 # Failure

        for test_folder in bug.test_folders():
            if not os.path.isdir(os.path.abspath(os.path.join(checkout_dir, test_folder))):
                sys.stderr.write("test_folder: " + test_folder + " does not exist!\n")
                return 0 # Failure

        for bin_folder in bug.bin_folders():
            if not os.path.isdir(os.path.abspath(os.path.join(checkout_dir, bin_folder))):
                sys.stderr.write("bin_folder: " + bin_folder + " does not exist!\n")
                return 0 # Failure

        for test_bin_folder in bug.test_bin_folders():
            if not os.path.isdir(os.path.abspath(os.path.join(checkout_dir, test_bin_folder))):
                sys.stderr.write("test_bin_folder: " + test_bin_folder + " does not exist!\n")
                return 0 # Failure

        bug.classpath() # Any error in this method will be thrown by the assertions in place
    except:
        sys.stderr.write("An exception has occurred in the utils.metadata function!\n")
        return 0 # Failure
    return 1

#
# Run the test cases of a Bug in a defined checkout directory under a Java
# version.
#
# Returns multiple values at once:
#   - 1 if test is performed successfully, 0 otherwise
#   - list of all tests executed
#   - list of failing tests
#
def test(bug, checkout_dir, java_home_dir, test_log_file):
    print("Run tests on " + str(bug))

    run_tests_exit_code = bug.run_test(java_home_dir)

    rta_test_log_file = os.path.join(checkout_dir, "repair_them_all.run_test.log")
    copy_file(rta_test_log_file, test_log_file)

    ret           = "NA"
    all_tests     = []
    failing_tests = []
    if run_tests_exit_code < 0 or run_tests_exit_code == 137: # A negative value -N indicates that the child was terminated by signal N | SIGKILL = 137
        ret = 0
        sys.stderr.write("test has failed!\n")
        return ret, all_tests, failing_tests

    if bug.benchmark.name == "Defects4J":
        dj_all_tests     = os.path.join(checkout_dir, "all_tests")
        dj_failing_tests = os.path.join(checkout_dir, "failing_tests")

        print("All tests:")
        # File format:
        # testMethodName(testClassName)
        # E.g.,
        # testBar(org.foo.TestFoo)
        print_log_file(dj_all_tests)

        print("Failing tests:")
        # File format:
        # --- testClassName::testMethodName
        #   <stack trace>
        # E.g.,
        # --- org.foo.TestFoo::testBar
        #   at ...
        print_log_file(dj_failing_tests)

        pattern = re.compile(r'^(.*)\((.*)\)$') # test pattern, e.g., testBar(org.foo.TestFoo)
        with open(dj_all_tests, 'r') as fin:
            for line in fin:
                line = line.rstrip() # remove '\n' at end of line
                search = pattern.search(line)
                all_tests.append(format_test_name(search.group(2), search.group(1)))
        assert len(all_tests) > 0

        pattern = re.compile(r'^--- .*[::.*]?') # test pattern, e.g., --- org.foo.TestFoo::testBar
        with open(dj_failing_tests, 'r') as fin:
            for line in fin:
                line = line.rstrip() # remove '\n' at end of line
                if pattern.match(line):
                    failing_tests.append(line)

    else:
        # ^Tests run: 1564, Failures: 3, Errors: 0, Skipped: 5$
        # ^[ERROR] Tests run: 1564, Failures: 3, Errors: 0, Skipped: 5$
        # ^Tests run: 5552, Failures: 1, Errors: 0, Skipped: 4, Flakes: 1$
        test_run_message = os.popen('grep -a -P "Tests run: \d+, Failures: \d+, Errors: \d+, Skipped: \d+" ' + test_log_file).read()
        if test_run_message == '':
            ret = 0
            sys.stderr.write("test has not returned a non-zero exit code but it has not executed any test case either!\n")
            return ret, all_tests, failing_tests

        # Collect all TEST-*.xml file created by `mvn test`. Each one
        # has all runtime information of each test suite.
        xml_files = collect_maven_surefire_xml_files(checkout_dir, rta_test_log_file)
        assert len(xml_files) > 0

        # Collect all tests reported by maven
        all_tests = collect_all_tests(xml_files)
        assert len(all_tests) > 0

        # Collect all failing tests reported by maven
        failing_tests = collect_failing_tests(xml_files)
        # Remove duplicates
        failing_tests = list(set(failing_tests))

    # At this point, the test command was successfully executed. One should
    # then check the list of failing tests (in case is relevant, e.g., for
    # patch plausibility) that is returned at the end of this function.
    ret = 1

    return ret, all_tests, failing_tests

#
# Construct a formated test name string as:
# '--- testClassName::testMethodName'
#
def format_test_name(class_name, method_name):
    test_method_name = method_name

    parameterized_test_pattern = r'(\S*)\[.*\]?' # e.g., testAppender[1] or testAppender[log4j-rolling-gz.xml \u2192 .gz] or testContract[public interface CtAnnotationFieldAccess<T> extends spoon.reflect.code.CtTargetedExpression<T, spoon.reflect.code.CtExpression<?>> , spoon.reflect.code.CtVariableRead<T> {
    extra_info_pattern = r'(\S*) .*$' # e.g., getHostFromAkkaURL should handle 'akka.tcp' as protocol

    if re.match(parameterized_test_pattern, method_name):
        test_method_name = re.search(parameterized_test_pattern, method_name).group(1)
    elif re.match(extra_info_pattern, method_name):
        test_method_name = re.search(extra_info_pattern, method_name).group(1)

    if "/" in test_method_name or "$" in test_method_name or test_method_name == class_name:
        # 1. Test case might not be a JUnit test case.
        #
        # E.g.,
        # Bears -- jenkinsci-ansicolor-plugin -- 440438437-449394834
        # InjectedTest test suite
        # hudson/plugins/ansicolor/AnsiColorStep/config.jelly
        # hudson/plugins/ansicolor/AnsiColorBuildWrapper/global.jelly
        # hudson/plugins/ansicolor/Messages.properties
        #
        # 2. Test case name as a inner class
        #
        # E.g.,
        # Bears -- jenkinsci-ansicolor-plugin -- 440438437-449394834
        # <testcase name="org.jvnet.hudson.test.JellyTestSuiteBuilder$JellyTestSuite" classname="org.jvnet.hudson.test.junit.FailedTest" time="0"/>
        #
        # 3. Test class has failed to initialize
        return "--- " + class_name

    assert "." not in test_method_name,"Test method name '" + test_method_name + "' includes '.'!"
    return "--- " + class_name + "::" + test_method_name

#
# Collect all TEST-*.xml files generated by `mvn test`.
#
# Extract the location of the TEST-*.xml files from a maven log and collects all
# files named `TEST-*.xml`. They usually live in
#   `<project_dir>/target/surefire-reports`
# Note that maven-based projects with multiple modules may have multiple
#   `target/surefire-reports` directories.
#
def collect_maven_surefire_xml_files(checkout_dir, maven_log_file):
    xml_files = []

    try:
        # Expression to get the location of .xml files
        # "^\[ERROR\] Please refer to (.*) for the individual test results."
        grep = subprocess.check_output('grep -a -P "Please refer to (.*) for the individual test results." ' + maven_log_file, shell=True)
        locations = grep.splitlines() # Maven projects with multiple modules may create multiple `target/surefire-reports` directories

        pattern = re.compile(r'Please refer to (.*) for the individual test results.')
        for location in locations:
            test_results_dir = pattern.search(location).group(1)
            if not os.path.isdir(test_results_dir):
                die("Directory with expected maven test results '" + test_results_dir + "' does not exist!\n")
            xml_files.extend(glob.glob(os.path.join(test_results_dir, "TEST-*.xml")))
    except subprocess.CalledProcessError:
        sys.stderr.write("There was no 'Please refer to (.*) for the individual test results.' in the maven log file!\n")
        # E.g.,
        # https://github.com/bugs-dot-jar/wicket/blob/bugs-dot-jar_WICKET-3885_beb9086d/.bugs-dot-jar/test-results.txt
        # Wicket-beb9086d there is no information of where are the xml files
        #
        # Tests in error:
        #   sendRedirectAjax(org.apache.wicket.protocol.http.servlet.ServletWebResponseTest)
        #   sendRedirect(org.apache.wicket.protocol.http.servlet.ServletWebResponseTest)
        #
        # Tests run: 1170, Failures: 0, Errors: 2, Skipped: 2
        #
        # [INFO] ------------------------------------------------------------------------
        # [INFO] BUILD SUCCESS
        # [INFO] ------------------------------------------------------------------------
        # [INFO] Total time: 51.869 s
        # [INFO] Finished at: 2019-08-16T03:09:25-07:00
        # [INFO] Final Memory: 23M/1963M
        # [INFO] ------------------------------------------------------------------------
        #
        # In such cases, search for the surefire-reports in the checkout directory
        pattern = re.compile(r'^TEST-.*\.xml$')
        for root, directories, files in os.walk(checkout_dir):
            for file in files:
                if pattern.match(file):
                    xml_files.append(os.path.join(root, file))

    assert len(xml_files) > 0
    return xml_files

#
# Collect all test cases on a given list of maven-surefire xml files.
#
def collect_all_tests(maven_surefire_xml_files):
    all_tests = []
    for maven_surefire_xml_file in maven_surefire_xml_files:
        all_tests.extend(extract_all_tests(maven_surefire_xml_file))
    return all_tests

#
# Extract all test cases of a given maven-surefire report xml.
#
def extract_all_tests(maven_surefire_xml_file):
    all_tests = []

    # Load .xml file and get root element, i.e., <testsuite>
    testsuite = ET.parse(maven_surefire_xml_file).getroot()
    assert testsuite != None
    assert testsuite.get('name') != None

    if int(testsuite.get('tests')) == 0:
        # Test suite did not execute any test case
        return all_tests

    # Find all <testcase> elements in the entire tree
    testcases = testsuite.findall('.//testcase')
    assert len(testcases) > 0

    # Construct list of all tests. Each test is identified as
    # '--- testClassName::testMethodName'
    for testcase in testcases:
        # Find the first subelement matching the tag 'skipped'. If there is
        # indeed a child named tag 'skipped', the execution of the test case has
        # been skipped by maven and therefore it can be ignored.
        if testcase.find("skipped") != None:
            continue

        classname = testcase.get('classname')
        if classname == None or " " in classname:
            classname = testsuite.get('name')
            assert classname != None
            assert " " not in classname,"Class name '" + classname + "' is not well formatted '.'!"
        name = testcase.get('name')
        assert name != None
        all_tests.append(format_test_name(classname, name))

    return all_tests

#
# Collect all failing test cases on a given list of maven-surefire xml files.
#
def collect_failing_tests(maven_surefire_xml_files):
    failing_tests = []
    for maven_surefire_xml_file in maven_surefire_xml_files:
        failing_tests.extend(extract_failing_tests(maven_surefire_xml_file))
    return failing_tests

#
# Extract failing test cases of a given maven-surefire report xml.
#
# `mvn test` produces a TEST-*.xml file per test suite with runtime information,
# e.g., number of test cases in the test suite, time, number of failing / skipped
# tests, etc. A TEST-*.xml file looks like:
#
# <?xml version="1.0" encoding="UTF-8" ?>
# <testsuite tests="101" failures="1" name="org.apache.jackrabbit.oak.security.authorization.accesscontrol.AccessControlManagerImplTest" time="6.924" errors="0" skipped="0">
#   <properties>
#     <property name="java.runtime.name" value="Java(TM) SE Runtime Environment"/>
#     ...
#   </properties>
#   <testcase classname="org.apache.jackrabbit.oak.security.authorization.accesscontrol.AccessControlManagerImplTest" name="testGetPolicies" time="0.067"/>
#   ...
#   <testcase classname="org.apache.jackrabbit.oak.security.authorization.accesscontrol.AccessControlManagerImplTest" name="testSetPolicyWritesAcContent" time="0.071">
#       <failure message="arrays first differed at element [0]; expected:&lt;jcr:addChildNodes&gt; but was:&lt;jcr:read&gt;" type="arrays first differed at element [0]; expected">arrays first differed at element [0]; expected:&lt;jcr:addChildNodes&gt; but was:&lt;jcr:read&gt;
#           at org.junit.internal.ComparisonCriteria.arrayEquals(ComparisonCriteria.java:52)
#           at org.junit.Assert.internalArrayEquals(Assert.java:416)
#           at org.junit.Assert.assertArrayEquals(Assert.java:168)
#           at org.junit.Assert.assertArrayEquals(Assert.java:185)
#           at org.apache.jackrabbit.oak.security.authorization.accesscontrol.AccessControlManagerImplTest.testSetPolicyWritesAcContent(AccessControlManagerImplTest.java:1237)
#       </failure>
#   </testcase>
#
# and they usually live in <project_dir>/target/surefire-reports
#
# Given a TEST-*.xml file, this function extracts all <testcase> elements in the
# provided .xml file with a <failure> or <error> element. Note, the content of
# <failure> or <error> is the actual stackstrace, in case is needed. Each
# <testcase> has the necessary information to uniquely identify it:
#   - classname is the test class name
#   - name      is the test method name
#
# In case there is not any <testcase> element with a <failure> / <error> element
# it returns an empty list.
#
def extract_failing_tests(maven_surefire_xml_file):
    failing_tests = []

    # Load .xml file and get root element, i.e., <testsuite>
    testsuite = ET.parse(maven_surefire_xml_file).getroot()
    assert testsuite != None
    assert testsuite.get('name') != None

    if int(testsuite.get('tests')) == 0:
        # Test suite did not execute any test case
        return failing_tests

    # Check whether testsuite's `failures="(\d+)" or errors="(\d+)"` are greater
    # than 0, if not, no test case has failed
    num_failures = int(testsuite.get('failures'))
    num_errors   = int(testsuite.get('errors'))
    if num_failures + num_errors == 0:
        return failing_tests

    # Find all <testcase> elements with a <failure> or <error> element in the
    # entire tree
    testcases = testsuite.findall('.//testcase/failure/..')
    testcases.extend(testsuite.findall('.//testcase/error/..'))

    # Construct list of failing tests. Each failing test is identified as
    # '--- testClassName::testMethodName'
    for testcase in testcases:
        classname = testcase.get('classname')
        if classname == None or " " in classname:
            classname = testsuite.get('name')
            assert classname != None
            assert " " not in classname,"Class name '" + classname + "' is not well formatted '.'!"
        name = testcase.get('name')
        assert name != None
        failing_tests.append(format_test_name(classname, name))

    return failing_tests
