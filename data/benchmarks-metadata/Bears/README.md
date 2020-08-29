# Bears Metatada

This directory contains the official metadata of the Bears benchmark for each
project / bug.

* `get_metadata.sh` collects metadata of all bugs in the Bears benchmark.

* `get_trigger_tests.sh` (which internally runs the `get_trigger_tests.pl`
script) collects the list of trigger test cases originally reported by the
benchmark metadata for all bugs and writes the name of each test case to
`<project>/<bug>/trigger_tests.txt`. The name of a trigger test case follows the
following format:

```
--- <test class name>::<test method name>
```
For example:
```
--- org.foo.TestFoo::testBar
```
