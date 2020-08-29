import os
import shutil
import subprocess

from config import REPAIR_ROOT, DATA_PATH, JAVA8_HOME, TEST_TIMEOUT
from core.Benchmark import Benchmark
from core.Bug import Bug
from core.utils import add_benchmark
from core.utils import run_cmd

class QuixBugs(Benchmark):
    """QuixBugs Benchmark"""

    def __init__(self):
        super(QuixBugs, self).__init__("QuixBugs")
        self.path = os.path.join(REPAIR_ROOT, "benchmarks", "QuixBugs")
        self.bugs = None
        self.get_bugs()

    def get_bugs(self):
        if self.bugs is not None:
            return self.bugs
        self.bugs = []
        dataset_path = os.path.join(self.path, "java_programs")
        for program in os.listdir(dataset_path):
            project_path = os.path.join(dataset_path, program)
            program = program.replace(".java", "")
            if not os.path.isfile(project_path) or program != program.upper():
                continue
            bug = Bug(self, program, "")
            self.bugs += [bug]
        return self.bugs

    def get_bug(self, bug_id):
        if bug_id[-1] == '_':
            bug_id = bug_id[:-1]
        for bug in self.get_bugs():
            if bug_id.lower() == bug.project.lower():
                return bug
        return None

    def checkout(self, bug, working_directory, rm_tests=True, buggy_version=True):
        dataset_path = os.path.join(self.path, "java_programs")
        test_path = os.path.join(self.path, "java_testcases", "junit")

        source_path = os.path.join(working_directory, "src", "main", "java")
        test_dst_path = os.path.join(working_directory, "src", "test", "java")

        os.makedirs(test_dst_path)
        os.makedirs(source_path)

        shutil.copy(os.path.join(DATA_PATH, "benchmarks", "QuixBugs", "pom.xml"), working_directory)
        for program in os.listdir(dataset_path):
            project_path = os.path.join(dataset_path, program)
            program = program.replace(".java", "")
            if not os.path.isfile(project_path) or ".class" in program or program == program.upper():
                continue
            shutil.copy(project_path, source_path)

        shutil.copy(os.path.join(dataset_path, "%s.java" % bug.project), source_path)
        test_file_path = os.path.join(test_path, "%s_TEST.java" % bug.project)
        if os.path.exists(test_file_path):
            self.prepare_test(bug, test_dst_path, test_file_path)
        else:
            test_file_path = os.path.join(DATA_PATH, "benchmarks", "QuixBugs", "%s_TEST.java" % bug.project)
            if os.path.exists(test_file_path):
                self.prepare_test(bug, test_dst_path, test_file_path)
        shutil.copy(os.path.join(test_path, "QuixFixOracleHelper.java"), test_dst_path)

        if rm_tests:
            # Remove known flaky tests
            if bug.rm_tests() != 0:
                return 1

        # TODO create folders
        # TODO copy src, test and QuixFixOracleHelper
        return 0

    def prepare_test(self, bug, test_dst_path, test_file_path):
        with open(test_file_path) as fd1:
            content = fd1.read().replace("%s_TEST" % bug.project, "%s_Test" % bug.project)
            with open(os.path.join(test_dst_path, "%s_Test.java" % bug.project), "w+") as fd2:
                fd2.write(content)

    def compile(self, bug, working_directory, java_home_dir=None):
        if java_home_dir == None:
            java_home_dir = JAVA8_HOME
        cmd = "cd %s; export _JAVA_OPTIONS=-Djdk.net.URLClassPath.disableClassPathURLCheck=true; export JAVA_HOME=\"%s\"; export PATH=\"$JAVA_HOME/bin:$PATH\"; mvn -Dhttps.protocols=TLSv1.2 clean test -DskipTests;" % (working_directory, java_home_dir)
        log_file = file(os.path.join(working_directory, "repair_them_all.compile.log"), 'w')
        return run_cmd(cmd, log_file, log_file)

    def run_test(self, bug, working_directory, java_home_dir=None):
        if java_home_dir == None:
            java_home_dir = JAVA8_HOME
        cmd = "cd %s; export _JAVA_OPTIONS=-Djdk.net.URLClassPath.disableClassPathURLCheck=true; export JAVA_HOME=\"%s\"; export PATH=\"$JAVA_HOME/bin:$PATH\"; timeout -s KILL %s mvn -Dhttps.protocols=TLSv1.2 test;" % (working_directory, java_home_dir, TEST_TIMEOUT)
        log_file = file(os.path.join(working_directory, "repair_them_all.run_test.log"), 'w')
        return run_cmd(cmd, log_file, log_file)

    def failing_tests(self, bug):
        tests = ["java_testcases.junit.%s_Test" % bug.project]
        return tests

    def source_folders(self, bug):
        return [os.path.join("src", "main", "java")]

    def test_folders(self, bug):
        return [os.path.join("src", "test", "java")]

    def bin_folders(self, bug):
        return [os.path.join("target", "classes")]

    def test_bin_folders(self, bug):
        return [os.path.join("target", "test-classes")]

    def classpath(self, bug):
        classpath = []
        m2_repository = os.path.expanduser("~/.m2/repository")
        assert os.path.isdir(m2_repository),"Directory '" + m2_repository + "' does not exist!"

        junit_jar = os.path.join(m2_repository, "junit", "junit", "4.11", "junit-4.11.jar")
        assert os.path.isfile(junit_jar),"The '" + junit_jar + "' file does not exist!"
        classpath.append(junit_jar)

        hamcrest_core_jar = os.path.join(m2_repository, "org", "hamcrest", "hamcrest-core", "1.3", "hamcrest-core-1.3.jar")
        classpath.append(hamcrest_core_jar)
        assert os.path.isfile(hamcrest_core_jar),"The '" + hamcrest_core_jar + "' file does not exist!"

        return ":".join(classpath)

    def compliance_level(self, bug):
        return 8

add_benchmark("QuixBugs", QuixBugs)