# Defects4J Metatada

This directory contains the official metadata of the Defects4J benchmark for
each project / bug.

* `get_trigger_tests.sh` collects the list of trigger test cases provided by
Defects4J's official metadata for each project / bug.

* `get_excluded_test_classes.sh` generates the `<project>/<bug>/excluded.txt`
files by extracting the exclusion patterns from the project build files and
expanding them into full test class names, as well as all test classes under a
`random` directory, all that match `*Abstract*Test.java`, and test classes
previously identified by Defects4J with broken test cases (this data lives in
the `failing_tests` file, e.g.,
[Math's failing tests file](https://github.com/rjust/defects4j/tree/master/framework/projects/Math/failing_tests)).
