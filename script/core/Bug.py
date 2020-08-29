import json
import os

from core.Benchmark import Benchmark


class Bug(object):
    """A bug"""

    def __init__(self, benchmark, project, bug_id):
        """
        :param benchmark:
        :type benchmark: Benchmark
        :param project:
        :param bug_id:
        """
        self.project = project
        self.bug_id = bug_id
        self.benchmark = benchmark
        self.working_directory = None

    def _get_project_data(self):
        if self.project_data is not None:
            return self.project_data

        project_data_path = os.path.join(self.benchmark.get_data_path(), "%s.json" % self.project.lower())
        with open(project_data_path) as fd:
            self.project_data = json.load(fd)
            return self.project_data

    def checkout(self, working_directory, rm_tests=True, buggy_version=True):
        self.working_directory  = os.path.realpath(working_directory)

        return self.benchmark.checkout(self, self.working_directory, rm_tests, buggy_version)

    #
    # Remove known failing and flaky test methods as well as test classes excluded
    # in the build file.
    #
    # Returns 1 if remove is performed successfully, 0 otherwise.
    #
    def rm_tests(self):
        return self.benchmark.rm_tests(self)

    def compile(self, java_home=None):
        return self.benchmark.compile(self, self.working_directory, java_home)

    def run_test(self, java_home=None):
        return self.benchmark.run_test(self, self.working_directory, java_home)

    def get_tests(self):
        return self.benchmark.get_tests(self, self.working_directory)

    def failing_tests(self):
        return self.benchmark.failing_tests(self)

    def source_folders(self):
        return self.benchmark.source_folders(self)

    def test_folders(self):
        return self.benchmark.test_folders(self)

    def bin_folders(self):
        return self.benchmark.bin_folders(self)

    def test_bin_folders(self):
        return self.benchmark.test_bin_folders(self)

    def classpath(self):
        return self.benchmark.classpath(self)

    def compliance_level(self):
        return self.benchmark.compliance_level(self)

    def __str__(self):
        return "%s_%s_%s" % (self.benchmark, self.project, self.bug_id)
