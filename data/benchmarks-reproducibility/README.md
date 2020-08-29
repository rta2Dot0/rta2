# Benchmarks Reproducibility Analysis

The first version of the [RTA framework](https://github.com/program-repair/RepairThemAll) (a961df6)
used an inconsistent combination of Java 7 and 8 to compile each bug's source
code and to run each repair tool:

* Bears's bugs are [compiled](https://github.com/program-repair/RepairThemAll/blob/a961df65870f17a221be316b165ac3a17bdc9d35/script/core/benchmarks/Bears.py#L111)
under whatever Java version is on the classpath, which might neither be 7 nor 8.
* All Bugs.jar's projects but [Wicket](https://github.com/program-repair/RepairThemAll/blob/a961df65870f17a221be316b165ac3a17bdc9d35/script/core/benchmarks/BugDotJar.py#L78) are compiled under [Java 8](https://github.com/program-repair/RepairThemAll/blob/a961df65870f17a221be316b165ac3a17bdc9d35/script/core/benchmarks/BugDotJar.py#L76).
* Defects4J's bugs are [compiled](https://github.com/program-repair/RepairThemAll/blob/a961df65870f17a221be316b165ac3a17bdc9d35/script/core/benchmarks/Defects4J.py#L79)
under Java 7.
* IntroClassJava's bugs are [compiled](https://github.com/program-repair/RepairThemAll/blob/a961df65870f17a221be316b165ac3a17bdc9d35/script/core/benchmarks/IntroClassJava.py#L66)
under whatever Java version is on the classpath, which might neither be 7 nor 8.
* QuixBugs's bugs are [compiled](https://github.com/program-repair/RepairThemAll/blob/a961df65870f17a221be316b165ac3a17bdc9d35/script/core/benchmarks/QuixBugs.py#L83)
under whatever Java version is on the classpath, which might neither be 7 nor 8.
* [Arja repair framework](https://github.com/program-repair/RepairThemAll/blob/a961df65870f17a221be316b165ac3a17bdc9d35/script/core/repair_tools/Arja.py#L51)
runs under Java 7 unless the bug requires a version higher than 7.
* [Astor repair framework](https://github.com/program-repair/RepairThemAll/blob/a961df65870f17a221be316b165ac3a17bdc9d35/script/core/repair_tools/Astor.py#L86)
runs under Java 8.
* [NPEFix repair framework](https://github.com/program-repair/RepairThemAll/blob/a961df65870f17a221be316b165ac3a17bdc9d35/script/core/repair_tools/NPEFix.py#L55)
runs under Java 8.
* [Nopol repair framework](https://github.com/program-repair/RepairThemAll/blob/a961df65870f17a221be316b165ac3a17bdc9d35/script/core/repair_tools/Nopol.py#L65)
runs under Java 8.

This inconsistent may produce invalid or misleading repair attempts. For
instance, 125 of the 395 bugs in Defects4J show either more or fewer failing
test cases when executed under Java 8. Attempting to repair these bugs may lead
to an invalid repair attempt as the repair tool would incorrectly consider non
related failing tests as trigger tests, invalidating the repair attempt.
Likewise, 100 of the 147 Commons-Math bugs in Bugs.jar cannot be repaired under
Java 8 under default conditions because of unfixable failing tests. Thus,
repairing these bugs is impossible by design.

As all repair tools are able to execute under Java 8 but no under Java 7, we
have adapted all RTA's runtime procedures (e.g., the `compile` and the
`run_test` procedures) of each benchmark to run, by default, under Java 8. We
have also explicitly specified that all repair tools must run under Java 8 for
consistent:

* [Arja repair framework under Java 8](https://github.com/jose/repair_them_all_framework/blob/experiments/script/core/repair_tools/Arja.py#L73)
* [Astor repair framework under Java 8](https://github.com/jose/repair_them_all_framework/blob/experiments/script/core/repair_tools/Astor.py#L41)
* [NPEFix repair framework under Java 8](https://github.com/jose/repair_them_all_framework/blob/experiments/script/core/repair_tools/NPEFix.py#L61)
* [Nopol repair framework under Java 8](https://github.com/jose/repair_them_all_framework/blob/experiments/script/core/repair_tools/Nopol.py#L72)

This changes, however, require careful handling of the underlying benchmarks as
each benchmark has been designed for use under particular versions of Java.
[Defects4J](https://github.com/rjust/defects4j) (< v2.0), for example, is
designed to operate under Java 7. When used with a different version of Java,
expected failing tests may pass and unexpected failing tests may fail. Thus, we
updated all benchmarks to operate under Java 8 which requires each bug to be
reproducible under Java 8, meaning:

* The build infrastructure compiles the bug's source code under Java 8 successfully.
* There are no unexpected flaky or broken test cases under Java 8. Note that a change
of Java version might make cause an unexpected failing test that RTA or the APR
tool might, incorrectly, consider as a triggering test, invalidating any repair
attempt.
* The bug triggers the same set of test cases as reported by the benchmark's authors.

## Procedure to reproduce a bug under Java 8

For all bugs, we performed the following procedure under Java 8 using RTA's API
to checkout, compile, and run the project's test cases.

1. Checkout the fixed version. To obtain the fixed version of each bug, we
checkout the buggy version and apply the manually-written patch provided in the
benchmark metadata. (Note: IntroClassJava and QuixBugs benchmarks do not provide
the patch that fixes each bug and therefore there is no official way to checkout
the fixed version of each bug.)

2. Compile the fixed version under Java 8. For Bears and Bugs.jar benchmarks,
the RTA framework uses Maven to compile each project/bug. For Defects4J, it uses
the provided `compile` interface which internally launches an Ant build. Bugs
that do not compile are excluded.

3. Run the project's test cases in the fixed version under Java 8. For Bears and
Bugs.jar benchmarks, the RTA framework uses Maven to run the test cases of each
project/bug. For Defects4J, it uses the provided `test` interface which
internally launches an Ant build. Bugs that fail to run the project's test cases
are excluded.

4. Collect the outcome of all test cases executed in (3). To perform these first
four steps, execute the following command:

```bash
export RTA_FRAMEWORK_DIR="......./repair_them_all_framework"
export PYTHONPATH="$RTA_FRAMEWORK_DIR/script/:$PYTHONPATH"

./checkout_and_compile_and_metadata_and_test.py \
  --benchmark "<benchmark id>" \
  --project "<project id>" \
  --bug "<bug id>" \
  --jvm "8" \
  --exclude_broken "false" \
  --buggy_version "false" \
  --output_dir "fixed"
```

5. Checkout the buggy version.

6. Compile the buggy version under Java 8. Bugs that do not compile are
excluded.

7. Run the project's test cases in the buggy version under Java 8. Bugs that
fail to run the project's test cases are excluded.

8. Collect the outcome of all test cases executed in (7). To perform these last
four steps, execute the following command:

```bash
export RTA_FRAMEWORK_DIR="......./repair_them_all_framework"
export PYTHONPATH="$RTA_FRAMEWORK_DIR/script/:$PYTHONPATH"

./checkout_and_compile_and_metadata_and_test.py \
  --benchmark "<benchmark id>" \
  --project "<project id>" \
  --bug "<bug id>" \
  --jvm "8" \
  --exclude_broken "false" \
  --buggy_version "true" \
  --output_dir "buggy"
```

The execution of this script generates the following data

```
[version: either 'buggy' or 'fixed']/benchmark_id/project_id/bug_id/[java: either '7' or '8']
  /compile.log
  /test.log
  /all_tests.txt
  /failing_tests.txt
  /status.csv
```

where

* `compile.log` and `test.log` report all log messages.

* `all_tests.txt` lists all test cases (one per row) executed by the `test`
routine. The name of each test follows the following format:

```
--- <test class name>::<test case name>
e.g.,
--- org.apache.flink.compiler.BranchingPlansCompilerTest::testBranchingWithMultipleDataSinks2
```

* `failing_tests.txt` lists all test cases (one per row) executed by the `test`
routine that fail. The name of each test case follows the following format:

```
--- <test class name>::<test case name>
e.g.,
--- org.apache.flink.runtime.operators.sort.LargeRecordHandlerTest::testRecordHandlerSingleKey
```

* `status.csv` reports the reproducibility status of each bug. The file follows
the following format:

```
benchmark,project,bug,java_version,exclude_broken_tests,buggy_version,checkout,compile,metadata,test,num_all_tests,num_failing_tests
```

where

1. benchmark: benchmark id
  * factor: "Bears", "Bugs.jar", "Defects4J", "IntroClassJava", or "QuixBugs"
2. project: project id
  * factor, e.g., "Closure", "Maven", "INRIA−spoon"
3. bug: bug id
  * factor, e.g., "19", "176912167-190405643"
4. java_version: java version used to compile the bug and run its test cases
  * numerical: 7 for Java-7 or 8 for Java-8
5. exclude_broken_tests:
  * factor: true or false (if true the known flaky test cases were removed at
  checkout, false otherwise)
6. buggy_version:
  * factor: true or false (if true the checkout procedure gets the buggy
  version, false it gets the fixed version)
7. checkout: does the `checkout` routine successfully clone the project/bug?
  * numerical: 0, 1 (1 if the routine successfully clones the project/bug, 0
  otherwise)
8. compile: does the `compile` routine successfully compile the project/bug?
  * numerical: **NA** if checkout=0/NA; 0, 1 (1 if the routine successfully
  compiles the project/bug, 0 otherwise)
9. metadata: does the `metadata` routine successfully call all methods that
return metadata?
  * numerical: **NA** if checkout=0/NA or compile=0/NA; 0, 1 (1 if the routine
  successfully calls all metadata methods, 0 otherwise)
10. test: does the `test` routine successfully run the test cases?
  * numerical: **NA** if checkout=0/NA or compile=0/NA or metadata=0/NA; 0, 1
  (1 if the routine successfully runs the test cases, 0 otherwise)
11. num_all_tests: number of test cases
  * numerical: **NA** if checkout=0/NA or compile=0/NA or metadata=0/NA or
  test=0/NA; >= 0 otherwise
12. num_failing_tests: number of failing test cases
  * numerical: **NA** if checkout=0/NA or compile=0/NA or metadata=0/NA or
  test=0/NA; >= 0 otherwise

## Procedure to check the reproducibility of a bug under Java 8

- As Bears and Defects4J benchmarks provide the list of expected trigger tests
per bug, we proceed as follows:
  * If no test fails on the buggy version under Java 8, the bug is not
  reproducible under Java 8 and therefore excluded.
  * If none of the tests failing on the buggy version under Java 8 are expected
  trigger tests, the bug is not reproducible under Java 8 and therefore
  excluded.
  * If at least one expected trigger test no longer fails on the buggy version
  under Java 8, the bug is not reproducible under Java 8 and therefore excluded.
  * If all expected trigger tests do fail on the buggy version under Java 8, the
  bug reproducible under Java 8. Additionally, all failing tests on the fixed
  version and any non-trigger test failing on the buggy version are annotated as
  broken.

- As the Bugs.jar benchmark does not provide a list of expected trigger tests
per bug, we proceed as follows:
  * If no test fails on the buggy version under Java 8, the bug is not
  reproducible under Java 8 and therefore excluded.
  * If the set of failing tests is the same on the fixed and buggy version, the
  bug is not reproducible under Java 8 and therefore excluded.
  * Any test that fails on the buggy version but does not fail on the fixed
  version is annotated as a trigger test. The remaining failing tests on either
  the buggy or the fixed version are annotated as broken.

[Benchmark.py](https://github.com/jose/repair_them_all_framework/blob/experiments/script/core/Benchmark.py)
is a core script in the RTA framework that controls how the benchmarks are used.
It acts as a wrapper for project-specific benchmark files, defining an interface
for checking out, compiling, and running tests. This script has been modified
and a new
[`rm_tests`](https://github.com/jose/repair_them_all_framework/blob/experiments/script/core/Benchmark.py#L72)
method has been added to the script. It is removes, at checkout, from the
project source code all test cases that fail on the fixed version and that have
been annotated as broken.

This procedure ensures that all repair attempts are valid. If we cannot compile
a bug, it is removed from consideration. If at least one of the expected trigger
tests no longer fails, the bug is removed from consideration. If there are
unexpected failing tests, we remove them from the source code. This process
results in identical results to a situation where the benchmarks were created
using Java 8 in the first place instead of Java 7. It also respects the intended
use of benchmarks — filtering flaky and broken tests that would have been
filtered using the benchmark-provided build files.

To check reproducibility of a bug, run the `is_bug_reproducible.sh` script as:

```bash
./is_bug_reproducible.sh.sh \
  --benchmark <benchmark> \
  --project <project> \
  --bug <bug> \
  --jvm 8
```

The script writes to the STDOUT the following information
```
benchmark,project,bug,java_version,status
```

where

1. benchmark: benchmark id
  * factor: "Bears", "Bugs.jar", "Defects4J", "IntroClassJava", or "QuixBugs"

2. project: project id
  * factor, e.g., "Closure", "Maven", "INRIA−spoon"

3. bug: bug id
  * factor, e.g., "19", "176912167-190405643"

4. java_version: java version used to compile the bug and run its test cases
  * numerical: 7 for Java-7 or 8 for Java-8

5. status: reproducibility outcome
  * factor
  * 'Checkout procedure has failed' --- if the checkout procedure of the
  fixed the buggy version failed.
  * 'Compile procedure has failed' --- if the compilation procedure of the
  fixed or the buggy version failed.
  * 'Test procedure has failed' --- if the test procedure of the fixed or the
  buggy version failed.
  * 'No trigger tests' --- if there are not any trigger test on the buggy
  version.
  * 'Incorrect set of trigger tests' --- if the set of trigger tests on the
  buggy version does not include all trigger tests previously identified by
  the benchmark.
  * 'OK' --- otherwise.

Note: To check the reproducibility of **all** bugs under Java 8, use the
`are_all_bugs_reproducible.sh` script instead, which runs the
`is_bug_reproducible.sh` script for every single bug as described above.

Note that the procedure described in this document discarded the following bugs:
* Closure-115 and Lang-57 from Defects4J due to fewer trigger tests on the
buggy version.
* Time-21 and Lang-2 from Defects4J due to no triggering test on the buggy
version.
* REVERSE_LINKED_LIST and MINIMUM_SPANNING_TREE from QuixBugs due to compilation
issues.
* 18 bugs from Bears (8 due to compilation issues, 4 due to incorrect set of
trigger tests, and 6 due to no triggering test on the buggy version).
* 366 bugs from Bugs.jar (243 due to compilation issues, 78 incorrect set of
trigger tests, 42 due to no triggering tests on the buggy version, and 3 due to
severe failures on the `test` procedure).
