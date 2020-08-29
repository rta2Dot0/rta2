# Bugs.jar Metatada

This directory contains the official metadata of the Bugs.jar benchmark for each
project / bug.

* `get_metadata.sh` collects metadata of all bugs in the Bugs.jar benchmark.

* `get_trigger_tests.sh` (which internally runs the `get_trigger_tests.pl`
script) collects the list of trigger test cases originally reported by the
benchmark metadata for all bugs and writes the name of each test case to
`<project>/<bug>/trigger_tests.txt`. The name of a trigger test case follows the
following format:

```
--- <test class name>[::<test method name>]
```
For example:
```
--- org.foo.TestFoo::testBar
```

* It is known that some bugs of the Commons-Math project in the Bugs.jar
benchmark share some bugs with the Math project in the Defects4J benchmark.
`get_excluded_tests_based_on_d4j.sh` script, therefore, collects the list of
test cases, for Commons-Math bugs, that are excluded by construction by
Defects4J. The scripts writes all excluded test cases to
`<project>/<bug>/excluded-tests.txt`. Format:

```
--- <test class name>
```
For example:
```
--- org.foo.TestFoo
```

* `get_common_bugs_d4j_and_bugs_dot_jar.sh` collects the list of Math bugs that
are in the Bugs.jar benchmark and also in the Defects4J benchmarks. The script
prints to the STDOUT the list of bugs in common. The format of the output is as
follows:
```
Math,<Bugs.jar identifier, i.e., branch-name>,<Bugs.jar RTA id>,Commonts-Math,<Defects4J identifier, i.e., bug-id>,<Defects4J RTA id>
```
