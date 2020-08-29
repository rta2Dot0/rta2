import os
import shutil
import subprocess

from config import REPAIR_ROOT, JAVA8_HOME, TEST_TIMEOUT
from core.Benchmark import Benchmark
from core.Bug import Bug
from core.utils import add_benchmark
from core.utils import run_cmd

class IntroClassJava(Benchmark):
    """IntroClassJava Benchmark"""

    def __init__(self):
        super(IntroClassJava, self).__init__("IntroClassJava")
        self.path = os.path.join(REPAIR_ROOT, "benchmarks", "IntroclassJava")
        self.bugs = None
        self.get_bugs()

    def get_bugs(self):
        if self.bugs is not None:
            return self.bugs
        self.bugs = []
        dataset_path = os.path.join(self.path, "dataset")
        for project in os.listdir(dataset_path):
            project_path = os.path.join(dataset_path, project)
            if os.path.isfile(project_path):
                continue
            for user in os.listdir(project_path):
                user_path = os.path.join(project_path, user)
                if os.path.isfile(user_path):
                    continue
                for revision in os.listdir(user_path):
                    if revision == "reference":
                        continue
                    revision_path = os.path.join(user_path, revision)
                    if os.path.isfile(revision_path):
                        continue
                    bug = Bug(self, project, "%s-%s" % (user, revision))
                    self.bugs += [bug]
        return self.bugs

    def get_bug(self, bug_id):
        (project, user, revision) = bug_id.split("-")

        for bug in self.get_bugs():
            if project != bug.project:
                continue
            (bug_user, bug_revision) = bug.bug_id.split("-")
            if user in bug_user and int(revision) == int(bug_revision):
                return bug
        return None

    def checkout(self, bug, working_directory, rm_tests=True, buggy_version=True):
        user, revision = bug.bug_id.split("-")
        bug_path = os.path.join(self.path, "dataset", bug.project, user, revision)
        shutil.copytree(bug_path, working_directory)
        if rm_tests:
            # Remove known flaky tests
            if bug.rm_tests() != 0:
                return 1
        return 0

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
        (bug_user, bug_revision) = bug.bug_id.split("-")
        bug_user = bug_user[:8]
        tests = [
            "introclassJava.%s_%s_%sBlackboxTest" % (bug.project.lower(), bug_user, bug_revision),
            "introclassJava.%s_%s_%sWhiteboxTest" % (bug.project.lower(), bug_user, bug_revision)
        ]

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
        return 7

add_benchmark("IntroClassJava", IntroClassJava)
