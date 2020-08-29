import collections
import json
import os
import sys
import re
import subprocess
from sets import Set

from config import DATA_PATH, JAVA8_HOME, TEST_TIMEOUT
from config import REPAIR_ROOT
from core.Benchmark import Benchmark
from core.Bug import Bug
from core.utils import add_benchmark
from core.utils import run_cmd

FNULL = open(os.devnull, 'w')


class Defects4J(Benchmark):
    """Defects4j Benchmark"""

    def __init__(self):
        super(Defects4J, self).__init__("Defects4J")
        self.path = os.path.join(REPAIR_ROOT, "benchmarks", "defects4j")
        self.project_data = {}
        self.bugs = None
        self.get_bugs()

    def get_data_path(self):
        return os.path.join(DATA_PATH, "benchmarks", "defects4j")

    def get_bug(self, bug_id):
        separator = "-"
        if "_" in bug_id:
            separator = "_"
        (project, id) = bug_id.split(separator)
        for bug in self.get_bugs():
            if bug.project.lower() == project.lower():
                if int(bug.bug_id) == int(id):
                    return bug
        return None

    def get_bugs(self):
        if self.bugs is not None:
            return self.bugs
        self.bugs = []
        data_defects4j_path = self.get_data_path()
        for project_data in os.listdir(data_defects4j_path):
            project_data_path = os.path.join(data_defects4j_path, project_data)
            if not os.path.isfile(project_data_path):
                continue
            with open(project_data_path) as fd:
                data = json.load(fd)
                self.project_data[data['project']] = data
                for i in range(1, data['nbBugs'] + 1):
                    bug = Bug(self, data['project'], i)
                    bug.project_data = data
                    self.bugs += [bug]
        return self.bugs

    def _get_benchmark_path(self):
        return os.path.join(self.path, "framework", "bin")

    def checkout(self, bug, working_directory, rm_tests=True, buggy_version=True):
        str_bug_id = "%sb" %(bug.bug_id)
        if not buggy_version:
            str_bug_id = "%sf" %(bug.bug_id)
        cmd = """export JAVA_HOME="%s";
export PATH="%s:$JAVA_HOME/bin:$PATH";
defects4j checkout -p %s -v %s -w %s;
""" % (JAVA8_HOME,
       self._get_benchmark_path(),
       bug.project,
       str_bug_id,
       working_directory)
        subprocess.check_output(cmd, shell=True)
        if rm_tests:
            # Remove known flaky tests
            if bug.rm_tests() != 0:
                return 1
        return 0

    def compile(self, bug, working_directory, java_home_dir=None):
        if java_home_dir == None:
            java_home_dir = JAVA8_HOME
        cmd = """export JAVA_HOME="%s";
export PATH="%s:$JAVA_HOME/bin:$PATH";
export _JAVA_OPTIONS=-Djdk.net.URLClassPath.disableClassPathURLCheck=true;
cd %s;
if [ -d "build/classes" ];       then find build/classes       -type f -name "*.class" -exec rm -f -v {} \\+; fi;
if [ -d "build/test" ];          then find build/test          -type f -name "*.class" -exec rm -f -v {} \\+; fi;
if [ -d "build-tests" ];         then find build-tests         -type f -name "*.class" -exec rm -f -v {} \\+; fi;
if [ -d "target/classes" ];      then find target/classes      -type f -name "*.class" -exec rm -f -v {} \\+; fi;
if [ -d "target/test-classes" ]; then find target/test-classes -type f -name "*.class" -exec rm -f -v {} \\+; fi;
if [ -d "target/tests" ];        then find target/tests        -type f -name "*.class" -exec rm -f -v {} \\+; fi;
defects4j compile;
""" % (java_home_dir,
       self._get_benchmark_path(),
       working_directory)
        log_file = file(os.path.join(working_directory, "repair_them_all.compile.log"), 'w')
        return run_cmd(cmd, log_file, log_file)

    def run_test(self, bug, working_directory, java_home_dir=None):
        if java_home_dir == None:
            java_home_dir = JAVA8_HOME
        cmd = """export JAVA_HOME="%s";
export PATH="%s:$JAVA_HOME/bin:$PATH";
export _JAVA_OPTIONS=-Djdk.net.URLClassPath.disableClassPathURLCheck=true; 
cd %s;
timeout -s KILL %s defects4j test;
""" % (java_home_dir,
       self._get_benchmark_path(),
       working_directory,
       TEST_TIMEOUT)
        log_file = file(os.path.join(working_directory, "repair_them_all.run_test.log"), 'w')
        return run_cmd(cmd, log_file, log_file)

    def get_tests(self, bug, working_directory):
        # Run tests
        self.run_test(bug, working_directory)
        # Collect tests
        tests = []

        all_tests_file_path = os.path.join(working_directory, "all_tests")
        assert os.path.isfile(all_tests_file_path),"File '" + all_tests_file_path + "' does not exist!"

        pattern = re.compile(r'^.*\((.*)\)') # test class pattern, e.g., testToString(org.apache.commons.lang3.tuple.TripleTest)
        with open(all_tests_file_path) as fin:
            for row in fin:
                row = row.rstrip() # remove '\n' at end of line
                test = pattern.search(row).group(1)
                if test != '' and test != "junit.framework.TestSuite":
                    tests.append(test)

        tests = list(set(tests)) # Remove duplicates, if any
        assert len(tests) > 0
        return tests

    def failing_tests(self, bug):
        cmd = """export JAVA_HOME="%s";
export PATH="%s:$JAVA_HOME/bin:$PATH";
defects4j info -p %s -b %s;
""" % (JAVA8_HOME,
       self._get_benchmark_path(),
       bug.project,
       bug.bug_id)
        info = subprocess.check_output(cmd, shell=True, stderr=FNULL)

        tests = Set()
        reg = re.compile('- (.*)::(.*)')
        m = reg.findall(info)
        for i in m:
            tests.add(i[0])
        return list(tests)

    def _get_metadata(self, bug, property):
        cmd = """export JAVA_HOME="%s";
        export PATH="%s:$JAVA_HOME/bin:$PATH";
        cd %s;
        defects4j export -p %s 2> /dev/null;
        defects4j compile > /dev/null 2>&1;
        """ % (JAVA8_HOME,
        self._get_benchmark_path(),
        bug.working_directory,
        property)
        property_outcome = subprocess.check_output(cmd, shell=True, stderr=FNULL)
        assert bool(property_outcome and property_outcome.strip()),"Outcome of " + property + ": '" + property_outcome + "' might be incorrect!"
        return property_outcome

    def source_folders(self, bug):
        dir_src_classes = self._get_metadata(bug, "dir.src.classes")
        assert os.path.isdir(os.path.abspath(os.path.join(bug.working_directory, dir_src_classes))),"Directory '" + dir_src_classes + "' does not exist!"
        return [dir_src_classes]

    def test_folders(self, bug):
        dir_src_tests = self._get_metadata(bug, "dir.src.tests")
        assert os.path.isdir(os.path.abspath(os.path.join(bug.working_directory, dir_src_tests))),"Directory '" + dir_src_tests + "' does not exist!"
        return [dir_src_tests]

    def bin_folders(self, bug):
        dir_bin_classes = self._get_metadata(bug, "dir.bin.classes")
        assert os.path.isdir(os.path.abspath(os.path.join(bug.working_directory, dir_bin_classes))),"Directory '" + dir_bin_classes + "' does not exist!"
        return [dir_bin_classes]

    def test_bin_folders(self, bug):
        dir_bin_tests = self._get_metadata(bug, "dir.bin.tests")
        assert os.path.isdir(os.path.abspath(os.path.join(bug.working_directory, dir_bin_tests))),"Directory '" + dir_bin_tests + "' does not exist!"
        return [dir_bin_tests]

    def classpath(self, bug):
        classpath = self._get_metadata(bug, "cp.test")
        assert ":" in classpath,"Classpath '" + classpath + "' might be incorrect!"

        # Check if all entries exist and only consider the valid ones
        cp = []
        for entry in classpath.split(":"):
            # is it a file?
            if os.path.isfile(entry):
                cp.append(entry)
            # is it a file in the working directory?
            elif os.path.isfile(os.path.abspath(os.path.join(bug.working_directory, entry))):
                cp.append(os.path.abspath(os.path.join(bug.working_directory, entry)))
            # is it a directory in the working directory?
            elif os.path.isdir(os.path.abspath(os.path.join(bug.working_directory, entry))):
                dir_a = os.path.abspath(os.path.join(bug.working_directory, entry))
                dir_b = os.path.abspath(os.path.join(bug.working_directory, self.test_bin_folders(bug)[0]))
                if dir_a != dir_b:
                    # Avoid test build/target directory to appear in the
                    # classpath (aka dependencies) as some repair tools look for
                    # tests in the classpath rather than just looking for tests
                    # in the test build/target directory
                    cp.append(dir_a)
            else:
                sys.stderr.write(entry + " does not exist!\n")

        assert len(cp) > 0,"Classpath is empty!"
        return ":".join([str(elem) for elem in cp]) + ":" + os.path.abspath(os.path.join(self.path, "framework", "projects", "lib", "junit-4.11.jar"))

    def compliance_level(self, bug):
        return self.project_data[bug.project]["complianceLevel"][str(bug.bug_id)]["source"]

add_benchmark("Defects4J", Defects4J)