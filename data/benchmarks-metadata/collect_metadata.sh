#!/usr/bin/env bash
# ------------------------------------------------------------------------------
#
# This script collects metadata of all Bears, Bugs.jar, and Defects4J bugs.
#
# Usage:
# ./get_metadata.sh
#
# ------------------------------------------------------------------------------

SCRIPT_DIR=$(cd `dirname $0` && pwd)

#
# Print error message and exit
#
die() {
  echo "$@" >&2
  exit 1
}

# ------------------------------------------------------------------ Envs & Args

BUGS_FILE="$SCRIPT_DIR/../../benchmarks/bugs.csv"
[ -s "$BUGS_FILE" ] || die "$BUGS_FILE does not exist or it is empty!"

export JAVA_HOME="$SCRIPT_DIR/../../jdks/jdk1.8.0_181"
[ -d "$JAVA_HOME" ] || die "$JAVA_HOME does not exist!"
export PATH="$JAVA_HOME/bin:$PATH"

COLLECT_TEST_CLASSES_UTIL_JAR_FILE="$SCRIPT_DIR/util/collect_test_classes/target/collecttestclasses-0.0.1-SNAPSHOT-jar-with-dependencies.jar"
pushd . > /dev/null 2>&1
cd "$SCRIPT_DIR/util/collect_test_classes" || die "Failed to switch to '$SCRIPT_DIR/util/collect_test_classes'!"
  mvn clean package || die "Failed to compile the collect_test_classes utility!"
  [ -s "$COLLECT_TEST_CLASSES_UTIL_JAR_FILE" ] || die "$COLLECT_TEST_CLASSES_UTIL_JAR_FILE does not exist!"
popd > /dev/null 2>&1

USAGE="Usage: ${BASH_SOURCE[0]}"
[ "$#" -eq "0" ] || die "$USAGE"

# ------------------------------------------------------------------------- Main

benchmark="Bears"
pushd . > /dev/null 2>&1
cd "$benchmark" || die "Failed to switch to '$benchmark'!"
  ./get_metadata.sh || die "Failed to run get_metadata.sh on $benchmark!"
  ./get_trigger_tests.sh || die "Failed to run get_trigger_tests.sh on $benchmark!"
  ./get_excluded_test_classes.sh || die "Failed to run get_excluded_test_classes.sh on $benchmark!"
popd > /dev/null 2>&1

benchmark="Defects4J"
pushd . > /dev/null 2>&1
cd "$benchmark" || die "Failed to switch to '$benchmark'!"
  ./get_excluded_test_classes.sh || die "Failed to run get_excluded_test_classes.sh on $benchmark!"
  ./get_trigger_tests.sh || die "Failed to run get_trigger_tests.sh on $benchmark!"
popd > /dev/null 2>&1

# As some Bugs.jar's bugs depend on the metadata of some Defects4J's bugs,
# the metadata collection of Bugs.jar's bugs must be performed after
benchmark="Bugs.jar"
pushd . > /dev/null 2>&1
cd "$benchmark" || die "Failed to switch to '$benchmark'!"
  ./get_metadata.sh || die "Failed to run get_metadata.sh on $benchmark!"
  ./get_trigger_tests.sh || die "Failed to run get_trigger_tests.sh on $benchmark!"
  ./get_common_bugs_d4j_and_bugs_dot_jar.sh > "common_bugs_d4j_and_bugs_dot_jar.csv" || die "Failed to run get_common_bugs_d4j_and_bugs_dot_jar.sh on $benchmark!"
  ./get_excluded_test_classes.sh || die "Failed to run get_excluded_test_classes.sh on $benchmark!"
popd > /dev/null 2>&1

echo "DONE!"
exit 0
