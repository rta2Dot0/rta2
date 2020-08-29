# Benchmarks Metatada

This directory contains the official metadata of each benchmark / project / bug
extracted from the official benchmarks repositories.

`get_metadata.sh` script collects metadata of all Bears, Bugs.jar, and Defects4J
bugs. (Note: no metadata is available for IntroClassJava and QuixBugs). For each
bug, the `get_metadata.sh` script generate the following metadata:

* `trigger_tests.txt`: file that lists all test cases (one per row) that are
expected to fail for the buggy version. Format:

```
--- <test class name>::<test method name>
```
For example:
```
--- org.foo.TestFoo::testBar
```

* `excluded.txt`: file that lists all excluded test classes (one per row) that
are excluded by the correspondent benchmark. Note that only the Defects4J
benchmark provides this data. The same data is computed for all the other
benchmarks with the `get_excluded_test_classes_maven_projects.py` script. Format
of the `excluded.txt` file:

```
--- <test class name>
```
For example:
```
--- org.foo.TestFoo
```

Different benchmarks / bugs provide extra metadata. For instance, Bears and
Bugs.jar provide a json file with all metadata of each bug. Bugs.jar also
provides for each bug: the patch to fix the bug (`developer-patch.diff`), the
set of flaky test cases (`flaky-test-results.txt`), the bug report
(`bug-report.yml`), and the maven output log (`test-results.txt`).

### Known issues

* The manually-written patches originally provided by the benchmark for the
  following bugs, attempt to add java files that already exist in the working
  directory. Therefore, `git apply` fails to apply the patch and fix the bug.
  - Bugs.jar -- Accumulo - db4a291f
  - Bugs.jar -- Flink - ce68cbd9
  - Bugs.jar -- Wicket - 087c0a26
  - Bugs.jar -- Wicket - 7c89598a
  - Bugs.jar -- Wicket - 87fa630f
  - Bugs.jar -- Wicket - 96330447
  - Bugs.jar -- Camel - 7bbb88ba
  - Bugs.jar -- Camel - baece126
  - Bugs.jar -- Jackrabbit-Oak - 374e3f3d
  - Bugs.jar -- Jackrabbit-Oak - d645112f

* Maven failed to build Bugs.jar -- Accumulo-699b8bf0 therefore there is no
  information of the trigger test cases. More on this
  [here](https://github.com/bugs-dot-jar/bugs-dot-jar/issues/1) and
  [here](https://github.com/bugs-dot-jar/bugs-dot-jar/issues/3).

* Unable to figure out the list of trigger test methods for the following bugs:
  - Bugs.jar -- Logging-Log4J2 - 88641f49
  - Bugs.jar -- Logging-Log4J2 - c79a743b
  - Bugs.jar -- Logging-Log4J2 - 3b12e13d
  - Bugs.jar -- Logging-Log4J2 - 7f391872
  - Bugs.jar -- Logging-Log4J2 - 2afe3dff
  - Bugs.jar -- Logging-Log4J2 - d8af1c93
