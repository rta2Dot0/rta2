#!/usr/bin/env bash
# ------------------------------------------------------------------------------
# This script analyzes the reproducibility of a given bugs
#
# A bug is reproducible if and only if:
#
#   1) it checkouts, compiles, verifies metadata, and runs the test cases
#      successfully on the buggy and fixed version.
#   2) it triggers at least one test case on the buggy version (i.e.,
#      `trigger_tests.txt` generated on the buggy version is not empty).
#   3) it triggers the same set of tests as the ones provided by benchmark's
#      metadata. (Only applied for Bears, Bugs.jar, and Defects4J)
#
# Usage:
# ./is_bug_reproducible.sh
#   --benchmark <benchmark>
#   --project <project>
#   --bug <bug>
#   --jvm <jvm>
#   [--help]
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

D4J_HOME="$SCRIPT_DIR/../../benchmarks/defects4j"
[ -d "$D4J_HOME" ] || die "$D4J_HOME does not exist!"

LIST_COMMON_BUGS_FILE="$SCRIPT_DIR/../benchmarks-metadata/Bugs.jar/common_bugs_d4j_and_bugs_dot_jar.csv"
[ -s "$LIST_COMMON_BUGS_FILE" ] || die "$LIST_COMMON_BUGS_FILE does not exist or it is empty!"

USAGE="Usage: ${BASH_SOURCE[0]} --benchmark <benchmark> --project <project> --bug <bug> --jvm <jvm> [--help]"
if [ "$#" -ne "1" ] && [ "$#" -ne "8" ]; then
  die "$USAGE"
fi

BENCHMARK=""
PROJECT=""
BUG=""
JVM=""

while [[ "$1" = --* ]]; do
  OPTION=$1; shift
  case $OPTION in
    (--benchmark)
      BENCHMARK=$1;
      shift;;
    (--project)
      PROJECT=$1;
      shift;;
    (--bug)
      BUG=$1;
      shift;;
    (--jvm)
      JVM=$1;
      shift;;
    (--help)
      echo "$USAGE"
      exit 0
    (*)
      die "$USAGE";;
  esac
done

[ "$BENCHMARK" != "" ] || die "--benchmark is not defined! $USAGE"
[ "$PROJECT" != "" ]   || die "--project is not defined! $USAGE"
if [ "$BENCHMARK" != "QuixBugs" ]; then
  [ "$BUG" != "" ]     || die "$USAGE" # All benchmarks but 'QuixBugs' have bug IDs
fi
[ "$JVM" != "" ]       || die "--jvm is not defined! $USAGE"

# -------------------------------------------------------------------- Constants

BUGGY_STR="buggy"
FIXED_STR="fixed"

# Input for the analysis
  failing_tests_file_on_buggy="$SCRIPT_DIR/$BUGGY_STR/$BENCHMARK/$PROJECT/$BUG/$JVM/failing_tests.txt"
  failing_tests_file_on_fixed="$SCRIPT_DIR/$FIXED_STR/$BENCHMARK/$PROJECT/$BUG/$JVM/failing_tests.txt"
benchmarks_trigger_tests_file="$SCRIPT_DIR/../benchmarks-metadata/$BENCHMARK/$PROJECT/$BUG/trigger_tests.txt"
# Output of the analysis
         trigger_tests_file="$SCRIPT_DIR/$BUGGY_STR/$BENCHMARK/$PROJECT/$BUG/$JVM/trigger_tests.txt"
          broken_tests_file="$SCRIPT_DIR/$FIXED_STR/$BENCHMARK/$PROJECT/$BUG/$JVM/broken_tests.txt"

REPRODUCIBLE_STR="Reproducible"
NOT_REPRODUCIBLE_STR="Not reproducible"

# ------------------------------------------------------------------------- Main

#
# Check status.csv files
#

for version in "$BUGGY_STR" "$FIXED_STR"; do

  if [ "$version" == "$FIXED_STR" ]; then
    if [ "$BENCHMARK" == "IntroClassJava" ] || [ "$BENCHMARK" == "QuixBugs" ]; then
      # IntroClassJava and QuixBugs benchmarks do not provide a fixed version
      continue
    fi
  fi

  status_csv_file="$SCRIPT_DIR/$version/$BENCHMARK/$PROJECT/$BUG/$JVM/status.csv"
  [ -s "$status_csv_file" ] || die "$status_csv_file does not exist or it is empty!"

  num_rows=$(wc -l "$status_csv_file" | cut -f1 -d' ')
  [ "$num_rows" -eq "2" ] || die "Expected 2 rows but $status_csv_file has $num_rows!"

  status=$(perl "$SCRIPT_DIR/does_bug_checkout_compile_run-tests.pl" "$status_csv_file" 2>&1 > /dev/null)
  if [ "$?" -ne 0 ]; then
    echo "$BENCHMARK,$PROJECT,$BUG,$JVM,$NOT_REPRODUCIBLE_STR,$status"
    exit 0
  fi
done

#
# Check failing_tests.txt files and create list of trigger_tests.txt and
# broken_tests.txt
#

# IntroClassJava and QuixBugs benchmarks do not provide the set of failing tests
# on the fixed version neither the true set of trigger tests, therefore, this
# script excludes IntroClassJava and QuixBugs benchmarks for further analyses
if [ "$BENCHMARK" == "IntroClassJava" ] || [ "$BENCHMARK" == "QuixBugs" ]; then
  num_trigger_tests=$(cat "$failing_tests_file_on_buggy" | wc -l)
  if [ "$num_trigger_tests" -eq "0" ]; then
    echo "$BENCHMARK,$PROJECT,$BUG,$JVM,$NOT_REPRODUCIBLE_STR,No failing tests"
    exit 0
  else
    cat "$failing_tests_file_on_buggy" > "$trigger_tests_file"
    echo "$BENCHMARK,$PROJECT,$BUG,$JVM,$REPRODUCIBLE_STR,Same trigger tests and 0 non-trigger tests"
    exit 0
  fi
fi

[ -f "$failing_tests_file_on_buggy" ]   || die "$failing_tests_file_on_buggy does not exist!"
[ -f "$failing_tests_file_on_fixed" ]   || die "$failing_tests_file_on_fixed does not exist!"
[ -f "$benchmarks_trigger_tests_file" ] || die "$benchmarks_trigger_tests_file does not exist!"

#
# Figure out the set of broken tests, the ones that fail on the buggy version
# but are not trigger tests
#

broken_tests_status=$(perl "$SCRIPT_DIR/get_broken_tests.pl" "$benchmarks_trigger_tests_file" "$failing_tests_file_on_buggy" "$broken_tests_file" 2>&1 > /dev/null)
if [ "$?" -ne 0 ]; then
  echo "$BENCHMARK,$PROJECT,$BUG,$JVM,$NOT_REPRODUCIBLE_STR,$broken_tests_status"
  exit 0
fi

#
# Augment the broken_tests file of, e.g., Commons-Math bugs from the Bugs.jar
# benchmark that are also Defects4j bugs, with data from the Defects4j benchmark
#

if grep -q "^$PROJECT,$BUG," "$LIST_COMMON_BUGS_FILE"; then
  d4j_project_name=$(grep "^$PROJECT,$BUG," "$LIST_COMMON_BUGS_FILE" | cut -f4 -d',')
        d4j_bug_id=$(grep "^$PROJECT,$BUG," "$LIST_COMMON_BUGS_FILE" | cut -f5 -d',')

  rev_id=$(grep "^$d4j_bug_id," "$D4J_HOME/framework/projects/$d4j_project_name/commit-db" | cut -f3 -d',')
  d4j_failing_tests_file="$D4J_HOME/framework/projects/$d4j_project_name/failing_tests/$rev_id"
  if [ -f "$d4j_failing_tests_file" ]; then
    grep -a "^\-\-\- " "$d4j_failing_tests_file" | grep "::" | sort -u >> "$broken_tests_file"
  fi

  if [ -s "$broken_tests_file" ]; then # remove duplicates, if any
    sort -u "$broken_tests_file" > "$broken_tests_file.tmp" && mv "$broken_tests_file.tmp" "$broken_tests_file" || die "Failed to remove duplicates from $broken_tests_file!"
  fi
fi

#
# Collect set of trigger tests.  A trigger test case is a test that only fails
# on the buggy version and it is a true trigger test (i.e., is not in the set
# of broken tests)

trigger_status=$(perl "$SCRIPT_DIR/get_trigger_tests.pl" "$failing_tests_file_on_buggy" "$failing_tests_file_on_fixed" "$broken_tests_file" "$trigger_tests_file" 2>&1 > /dev/null)
if [ "$?" -ne 0 ]; then
  echo "$BENCHMARK,$PROJECT,$BUG,$JVM,$NOT_REPRODUCIBLE_STR,$trigger_status"
  exit 0
fi

#
# Check whether the set of trigger tests is the expected one
#

check_trigger_status=$(perl "$SCRIPT_DIR/check_trigger_tests.pl" "$failing_tests_file_on_buggy" "$benchmarks_trigger_tests_file" "$trigger_tests_file" 2>&1 > /dev/null)
if [ "$?" -ne 0 ]; then
  echo "$BENCHMARK,$PROJECT,$BUG,$JVM,$NOT_REPRODUCIBLE_STR,$check_trigger_status"
else
  echo "$BENCHMARK,$PROJECT,$BUG,$JVM,$REPRODUCIBLE_STR,$check_trigger_status"
fi

exit 0
