import json
import os
import re
import sys
import subprocess
from shutil import copyfile

from config import JAVA_VERSION, JAVA8_HOME, D4J_HOME, BENCHMARK_METADATA_DIR, BENCHMARKS_REPRODUCIBILITY_DIR

class Benchmark(object):
    """Benchmark"""

    def __init__(self, name):
        self.name = name
        pass

    def _get_project_info(self, bug, failing_module):
        try:
            return bug.maven_info
        except AttributeError:
            pass

        # Compile and install all modules before running the plug-in to extract
        # module-specific information
        print("Compile top-level project")
        if self.compile(bug, bug.working_directory) != 0:
            raise Exception("Project has not compiled successfully!")

        # Make sure all relevant folders exist
        self.init_test(bug, bug.working_directory)

        print("Get module information")
        work_dir = os.path.join(bug.working_directory, failing_module)
        cmd = """cd %s;
export JAVA_HOME="%s";
export PATH="$JAVA_HOME/bin:$PATH";
mvn -Dmaven.repo.local=%s/.m2 com.github.tdurieux:project-config-maven-plugin:1.0-SNAPSHOT:info -q > project-config-maven-plugin.json;
""" % (work_dir, JAVA8_HOME, bug.working_directory)

        json_file = os.path.join(work_dir, "project-config-maven-plugin.json")

        try:
            subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError:
            assert os.path.isfile(json_file),"The json file '" + json_file + "' does not exist!"
            print("[ERROR] The 'com.github.tdurieux:project-config-maven-plugin' has returned a non-zero exit status!")
            print(open(json_file, 'r').readlines())
            raise

        assert os.path.isfile(json_file),"The json file '" + json_file + "' does not exist!"
        with open(json_file, 'r') as fin:
            try:
                info = json.load(fin)
            except ValueError:
                print("[ERROR] The json file created by 'com.github.tdurieux:project-config-maven-plugin' is not well formatted!")
                print(fin.readlines())
                raise
            bug.maven_info = info # Cache project info
            return info

        raise Exception("No project info has been collected!")

    def checkout(self, bug, working_directory, rm_tests=True, buggy_version=True):
        pass

    #
    # Remove known failing and flaky test methods as well as test classes excluded
    # in the build file.
    #
    # Returns 0 if remove is performed successfully, 1 otherwise.
    #
    def rm_tests(self, bug):

        src_test_dir = os.path.join(bug.working_directory, bug.test_folders()[0])
        if not os.path.isdir(src_test_dir):
            sys.stderr.write("The source directory '" + src_test_dir + "' does not exist!\n")
            return 1

        # File that lists all broken test methods (one per line)
        # --- <test class name>::<test method name>
        # (e.g., --- org.foo.TestFoo::testBar)

        # data/benchmarks-reproducibility/fixed/Defects4J/Lang/13/[7/8]/failing_tests.txt
        failing_tests_file = os.path.join(BENCHMARKS_REPRODUCIBILITY_DIR, "fixed", str(self.name), str(bug.project), str(bug.bug_id), JAVA_VERSION, "failing_tests.txt")
        if os.path.isfile(failing_tests_file):
            sys.stdout.write("Removing the tests listed in " + failing_tests_file + "\n")
            cmd = "%s/framework/util/rm_broken_tests.pl %s %s;" %(D4J_HOME, failing_tests_file, src_test_dir)
            subprocess.check_output(cmd, shell=True)
            # The `rm_broken_tests.pl` script does remove broken test classes,
            # thus we remove them in here.  This is going to be applied to the
            # following bugs:
            #   Bugs.jar :: Accumulo :: 0cf2ff72
            #   Bugs.jar :: Accumulo :: 0cf2ff72
            #   Bugs.jar :: Logging-Log4J2 :: ca59ece6
            cmd = "cat %s | grep -v \"::\" | sort -u | sed 's/^--- //g' | tr '.' '/' | sed 's/$/.java/g' | while read -r file; do if [ -f \"%s/$file\" ]; then rm -f -v \"%s/$file\"; fi; done" %(failing_tests_file, src_test_dir, src_test_dir)
            subprocess.check_output(cmd, shell=True)

            # Bears :: shapesecurity-shift-java :: 455763022-456154969
            if bug.project == "shapesecurity-shift-java" and str(bug.bug_id) == "455763022-456154969":
                cmd = "cat %s | grep \"::initializationError\" | cut -f1 -d':' | sort -u | sed 's/^--- //g' | tr '.' '/' | sed 's/$/.java/g' | while read -r file; do if [ -f \"%s/$file\" ]; then rm -f -v \"%s/$file\"; fi; done" %(failing_tests_file, src_test_dir, src_test_dir)
                subprocess.check_output(cmd, shell=True)
                # and remove a test suite that depends on the removed ones
                os.remove("%s/com/shapesecurity/shift/es2017/test262/parser/XFailHelper.java" %(src_test_dir))
        else:
            sys.stdout.write(failing_tests_file + " does not exist. Thus, no test method is going to excluded\n")

        # remove test cases that have been considered flaky or broken
        broken_tests_file = os.path.join(BENCHMARKS_REPRODUCIBILITY_DIR, "fixed", str(self.name), str(bug.project), str(bug.bug_id), JAVA_VERSION, "broken_tests.txt")
        if os.path.isfile(broken_tests_file):
            sys.stdout.write("Removing the tests listed in " + broken_tests_file + "\n")
            cmd = "%s/framework/util/rm_broken_tests.pl %s %s;" %(D4J_HOME, broken_tests_file, src_test_dir)
            subprocess.check_output(cmd, shell=True)
        else:
            sys.stdout.write(broken_tests_file + " does not exist. Thus, no test method is going to excluded\n")

        # File that lists all excluded test classes (one per line)
        # --- <test class name>
        # (e.g., --- org.foo.TestFoo)
        # e.g., data/benchmarks-metadata/Defects4J/Math/84/excluded.txt
        # --- org.apache.commons.math.random.AbstractRandomGeneratorTest
        # --- org.apache.commons.math.random.CorrelatedRandomVectorGeneratorTest
        # --- org.apache.commons.math.random.EmpiricalDistributionTest
        # ...
        #
        # Common bugs in Bugs.jar and Defects4J
        common_bugs_in_bugs_jar_and_d4j = os.path.join(BENCHMARK_METADATA_DIR, "Bugs.jar", "common_bugs_d4j_and_bugs_dot_jar.csv")
        # e.g.,
        # bugs_dot_jar_project_name,bugs_dot_jar_bug_id,bugs_dot_jar_repair_them_all_id,d4j_project_name,d4j_bug_id,d4j_repair_them_all_id
        # Commons-Math,91d280b7,Commons-Math-91d280b7,Math,3,Math-3
        # Commons-Math,dbdff075,Commons-Math-dbdff075,Math,83,Math-83
        # Commons-Math,38983e82,Commons-Math-38983e82,Math,82,Math-82
        # ...
        if os.path.isfile(common_bugs_in_bugs_jar_and_d4j):
            bugs_jar_pid = None
            bugs_jar_bid = None
            d4j_pid      = None
            d4j_bid      = None

            bugs_jar_pattern = r"^" + str(bug.project) + "," + str(bug.bug_id) + ",.*,(.*),(.*),.*$"
            d4j_pattern      = r"^(.*),(.*),.*," + str(bug.project) + "," + str(bug.bug_id) + ",.*$"

            with open(common_bugs_in_bugs_jar_and_d4j) as fin:
                for line in fin:
                    line = line.rstrip() # remove '\n'
                    if re.match(bugs_jar_pattern, line):
                        bugs_jar_pid = str(bug.project)
                        bugs_jar_bid = str(bug.bug_id)
                        search = re.search(bugs_jar_pattern, line)
                        d4j_pid = search.group(1)
                        d4j_bid = search.group(2)
                        break
                    elif re.match(d4j_pattern, line):
                        d4j_pid = str(bug.project)
                        d4j_bid = str(bug.bug_id)
                        search = re.search(d4j_pattern, line)
                        bugs_jar_pid = search.group(1)
                        bugs_jar_bid = search.group(2)
                        break

            if bugs_jar_pid != None and bugs_jar_bid != None and d4j_pid != None and d4j_bid != None:
                for excluded_test_classes_file in [os.path.join(BENCHMARK_METADATA_DIR, "Bugs.jar", bugs_jar_pid, bugs_jar_bid, "excluded.txt"), os.path.join(BENCHMARK_METADATA_DIR, "Defects4J", d4j_pid, d4j_bid, "excluded.txt")]:
                    if os.path.isfile(excluded_test_classes_file):
                        pattern = re.compile(r'^--- (.*)') # test class pattern, e.g., --- org.foo.TestFoo
                        with open(excluded_test_classes_file) as fin:
                            for line in fin:
                                line = line.rstrip() # remove '\n' at end of line
                                test_class_name = pattern.search(line).group(1)
                                sys.stdout.write("Attempt to remove test class '" + test_class_name + "'\n")
                                java_file = os.path.join(src_test_dir, test_class_name.replace('.', '/') + ".java")
                                if not os.path.isfile(java_file):
                                    sys.stdout.write("Test class '" + test_class_name + "' has not been removed because the " + java_file + " does not exist\n")
                                    continue

                                # Replace an existing class with a dummy one to avoid compilation issues
                                # and non-triggering test cases
                                replace_java_file = os.path.join(BENCHMARKS_REPRODUCIBILITY_DIR, "fix_broken_tests", "Bugs.jar", bugs_jar_pid, bugs_jar_bid, test_class_name.replace('.', '/') + ".java")
                                if os.path.isfile(replace_java_file):
                                    sys.stdout.write("Replacing '" + java_file + "' with '" + replace_java_file + "'\n")
                                    copyfile(replace_java_file, java_file)
                                    continue

                                # Last resource, remove it
                                os.remove(java_file)
                                sys.stdout.write("Test class '" + test_class_name + "' has been removed\n")

                if str(bug.project) == "Commons-Math":
                    CMAESOptimizerTest = os.path.join(src_test_dir, "org.apache.commons.math.optimization.direct.CMAESOptimizerTest".replace('.', '/') + ".java")
                    if os.path.isfile(CMAESOptimizerTest):
                        cmd = "echo \"--- org.apache.commons.math.optimization.direct.CMAESOptimizerTest::testMaximize\" > /tmp/$$-BugsJar-Commons-Math.txt; %s/framework/util/rm_broken_tests.pl /tmp/$$-BugsJar-Commons-Math.txt %s; rm -f /tmp/$$-BugsJar-Commons-Math.txt;" %(D4J_HOME, src_test_dir)
                        subprocess.check_output(cmd, shell=True)

        #
        # Corner cases
        #

        if bug.project == "Jackrabbit-Oak":
            # The `rm_broken_tests.pl` script is not able to remove a test suite
            # that is in the jar file of a dependency of the following bugs
            if str(bug.bug_id) == "7a84b3a8" or str(bug.bug_id) == "3270e761" or str(bug.bug_id) == "f63d745a" or str(bug.bug_id) == "f0fbacab" or str(bug.bug_id) == "8ed779dc":
                # jackrabbit-oak/oak-jcr/src/test/java/org/apache/jackrabbit/oak/jcr/query/QueryJcrTest.java:49:        suite.addTestSuite(SQL2OrderByTest.class);
                QueryJcrTest_java_file = os.path.join(bug.working_directory, "oak-jcr/src/test/java/org/apache/jackrabbit/oak/jcr/query/QueryJcrTest.java")
                if not os.path.isfile(QueryJcrTest_java_file):
                    sys.stderr.write("The java file '" + QueryJcrTest_java_file + "' does not exist therefore 'SQL2OrderByTest' is not going to be disabled!\n")
                else:
                    cmd = "sed -i 's/suite.addTestSuite(SQL2OrderByTest.class);//g' %s;" %(QueryJcrTest_java_file)
                    subprocess.check_output(cmd, shell=True)

        # Bears :: raphw-byte-buddy :: 352481508-352894244
        # Bears :: raphw-byte-buddy :: 357569370-357575635
        if bug.project == "raphw-byte-buddy":
            if str(bug.bug_id) == "352481508-352894244" or str(bug.bug_id) == "357569370-357575635":
                cmd = "echo \"--- net.bytebuddy.description.type.AbstractTypeDescriptionGenericTest::testNestedTypeVariableType\" > /tmp/$$-raphw-byte-buddy.txt; %s/framework/util/rm_broken_tests.pl /tmp/$$-raphw-byte-buddy.txt %s; rm -f /tmp/$$-raphw-byte-buddy.txt;" %(D4J_HOME, src_test_dir)
                subprocess.check_output(cmd, shell=True)

        # Bugs.jar :: Flink :: 380ef878
        # Bugs.jar :: Flink :: a56aad74
        # Bugs.jar :: Flink :: af477563
        # Bugs.jar :: Flink :: 5308ac83
        if bug.project == "Flink":
            if str(bug.bug_id) == "380ef878" or str(bug.bug_id) == "a56aad74" or str(bug.bug_id) == "af477563" or str(bug.bug_id) == "5308ac83":
                cmd = """
                    echo \"--- org.apache.flink.runtime.jobmanager.JobManagerProcessReapingTest::testReapProcessOnFailure\"        > /tmp/$$-Flink-380ef878-a56aad74-af477563-5308ac83.txt;
                    echo \"--- org.apache.flink.runtime.taskmanager.TaskManagerProcessReapingTest::testReapProcessOnFailure\"     >> /tmp/$$-Flink-380ef878-a56aad74-af477563-5308ac83.txt;
                    echo \"--- org.apache.flink.runtime.io.network.netty.CancelPartitionRequestTest::testCancelPartitionRequest\" >> /tmp/$$-Flink-380ef878-a56aad74-af477563-5308ac83.txt;
                    %s/framework/util/rm_broken_tests.pl /tmp/$$-Flink-380ef878-a56aad74-af477563-5308ac83.txt %s;
                    rm -f /tmp/$$-Flink-380ef878-a56aad74-af477563-5308ac83.txt;""" %(D4J_HOME, src_test_dir)
                subprocess.check_output(cmd, shell=True)

        # Bugs.jar :: Logging-Log4J2 :: 50340d0c
        if bug.project == "Logging-Log4J2" and str(bug.bug_id) == "50340d0c":
            cmd = "echo \"--- org.apache.logging.log4j.core.net.SocketReconnectTest::testReconnect\" > /tmp/$$-Logging-Log4J2-50340d0c.txt; %s/framework/util/rm_broken_tests.pl /tmp/$$-Logging-Log4J2-50340d0c.txt %s; rm -f /tmp/$$-Logging-Log4J2-50340d0c.txt;" %(D4J_HOME, src_test_dir)
            subprocess.check_output(cmd, shell=True)

        return 0

    def compile(self, bug, working_directory, java_version):
        return 0

    def init_test(self, bug, working_directory):
        return 0

    def run_test(self, bug, working_directory, java_home):
        return 0

    def get_tests(self, bug, working_directory):
        # Run tests
        self.run_test(bug, working_directory)
        # Collect tests
        tests = []
        pattern = re.compile(r'^TEST-(.*)\.xml$')
        failing_module = self.failing_module(bug)
        buggy_module_directory = os.path.join(working_directory, failing_module) if failing_module != None else working_directory
        for root, directories, files in os.walk(buggy_module_directory):
            for file in files:
                if pattern.match(file):
                    test = pattern.match(file).group(1)
                    if "[" in test:
                        # ignore the name of the parameterized test and collect the root test class name
                        test = test[0:test.index('[')]
                    if test != '' and test != "junit.framework.TestSuite":
                        tests.append(test)
        tests = list(set(tests)) # Remove duplicates, if any
        assert len(tests) > 0
        return tests

    def classpath(self, bug):
        pass

    def compliance_level(self, bug):
        pass

    def source_folders(self, bug):
        pass

    def test_folders(self, bug):
        pass

    def failing_tests(self, bug):
        pass

    def failing_module(self, bug):
        pass

    def __str__(self):
        return self.name
