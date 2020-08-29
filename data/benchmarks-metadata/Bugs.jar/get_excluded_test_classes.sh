#!/usr/bin/env bash
#
# ------------------------------------------------------------------------------
# This script collects the list of test classes that are by default excluded by
# the Maven Sufire plugin when one runs `mvn test`. For example, the
# [pom.xml file](https://github.com/bugs-dot-jar/commons-math/blob/bugs-dot-jar_MATH-286_dbdff075/pom.xml)
# of the Commons-Math dbdff075 bug excludes all test classes that their name
# end with 'GraggBulirschStoerIntegratorTest' from the test execution:
# ```
# <plugin>
#   <groupId>org.apache.maven.plugins</groupId>
#   <artifactId>maven-surefire-plugin</artifactId>
#   <configuration>
#     <includes>
#       <include>**/*Test.java</include>
#     </includes>
#     <excludes>
#       <exclude>**/*AbstractTest.java</exclude>
#       <exclude>**/*GraggBulirschStoerIntegratorTest.java</exclude>
#       <exclude>**/*GraggBulirschStoerIntegratorTest.java</exclude>
#       <exclude>**/*org/apache/commons/math/ode/nonstiff/GraggBulirschStoerStepInterpolatorTest.java</exclude>
#     </excludes>
#   </configuration>
# </plugin>
# ```
#
# Usage:
# ./get_excluded_test_classes.sh
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

D4J_HOME="$SCRIPT_DIR/../../../benchmarks/defects4j"
[ -d "$D4J_HOME" ] || die "$D4J_HOME does not exist!"

BUGS_FILE="$SCRIPT_DIR/../../../benchmarks/bugs.csv"
[ -s "$BUGS_FILE" ] || die "$BUGS_FILE does not exist or it is empty!"

LIST_COMMON_BUGS_FILE="$SCRIPT_DIR/common_bugs_d4j_and_bugs_dot_jar.csv"
[ -s "$LIST_COMMON_BUGS_FILE" ] || die "$LIST_COMMON_BUGS_FILE does not exist or it is empty. Please (re-)run the get_common_bugs_d4j_and_bugs_dot_jar.sh script!"

COLLECT_TEST_CLASSES_UTIL_JAR_FILE="$SCRIPT_DIR/../util/collect_test_classes/target/collecttestclasses-0.0.1-SNAPSHOT-jar-with-dependencies.jar"
[ -s "$COLLECT_TEST_CLASSES_UTIL_JAR_FILE" ] || die "$COLLECT_TEST_CLASSES_UTIL_JAR_FILE does not exist!"

export PYTHONPATH="$SCRIPT_DIR/../../../script:$PYTHONPATH"

USAGE="Usage: ${BASH_SOURCE[0]}"
[ "$#" -eq "0" ] || die "$USAGE"

# ------------------------------------------------------------------------- Main

while read -r line; do
  pid=$(echo "$line" | cut -f2 -d',')
  bid=$(echo "$line" | cut -f3 -d',')
  echo "$pid::$bid"

  dir="$SCRIPT_DIR/$pid/$bid"
  mkdir -p "$dir"
  excluded_file="$dir/excluded.txt"
  rm -f "$excluded_file"

  python ../get_excluded_test_classes_maven_projects.py --benchmark "Bugs.jar" --project "$pid" --bug "$bid" --output_file "$excluded_file" || die "Failed to collect list of excluded test classes of $pid::$bid!"

  # It is known that some bugs of the Commons-Math project in the Bugs.jar
  # benchmark share some bugs with the Math project in the Defects4J benchmark.
  # The following procedure, therefore, collects the list of test classes, for
  # Commons-Math bugs, that are excluded by construction by Defects4J.  So that
  # Commons-Math bugs in the Bugs.jar benchmark do not include known flaky test
  # classes.
  if grep -q "^$pid,$bid," "$LIST_COMMON_BUGS_FILE"; then
    d4j_project_name=$(grep "^$pid,$bid," "$LIST_COMMON_BUGS_FILE" | cut -f4 -d',')
          d4j_bug_id=$(grep "^$pid,$bid," "$LIST_COMMON_BUGS_FILE" | cut -f5 -d',')
    if [ -f "$SCRIPT_DIR/../Defects4J/$d4j_project_name/$d4j_bug_id/excluded.txt" ]; then
      cat "$SCRIPT_DIR/../Defects4J/$d4j_project_name/$d4j_bug_id/excluded.txt" >> "$excluded_file"
    fi
  fi

  if [ -s "$excluded_file" ]; then
    # Check: A test class annotated as excluded must not be considered for
    # exclusion if it includes a trigger test case
    trigger_tests_file="$SCRIPT_DIR/$pid/$bid/trigger_tests.txt"
    [ -s "$trigger_tests_file" ] || die "$trigger_tests_file does not exist or it is empty!"
    while read -r excluded_test_class; do
      if grep -q "^$excluded_test_class:" "$trigger_tests_file"; then
        echo "$excluded_test_class has been considered for exclusion but it should not be excluded because it has at least one trigger test case"
      else
        echo "$excluded_test_class" >> "$excluded_file.tmp"
      fi
    done < <(cat "$excluded_file")

    if [ -s "$excluded_file.tmp" ]; then
      # Remove duplicates, if any
      sort -u "$excluded_file.tmp" > "$excluded_file" || die "Failed to sort and remove duplicates of $excluded_file.tmp!"
      rm -f "$excluded_file.tmp"
    else
      # excluded.txt is empty or no longer exists, in either cases try to remove it
      rm -f "$excluded_file" "$excluded_file.tmp"
    fi
  else
    # excluded.txt is empty or no longer exists, in either cases try to remove it
    rm -f "$excluded_file"
  fi

done < <(grep "^Bugs.jar," "$BUGS_FILE")

echo "DONE!"
exit 0
