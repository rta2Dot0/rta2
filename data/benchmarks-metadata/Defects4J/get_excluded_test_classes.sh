#!/usr/bin/env bash
#
# ------------------------------------------------------------------------------
# This script collects the list of test classes that are by default excluded by
# Defects4J per project/bug. The list excluded of test classes includes:
#
# - The excluded test classes defined in the `build.xml` file. For example, the
# build file for
# [Math](https://github.com/rjust/defects4j/blob/master/framework/projects/Math/Math.build.xml)
# ```
#    <!-- List of all developer-written tests that reliably pass on the fixed version -->
#    <fileset id="all.manual.tests" dir="${test.home}" excludes="${d4j.tests.exclude}">
#        <include name="**/*Test.java"/>
#        <include name="**/*TestBinary.java"/>
#        <include name="**/*TestPermutations.java"/>
#        <exclude name="**/random/*.java"/>
#        <exclude name="**/*Abstract*Test.java"/>
#    </fileset>
# ```
# excludes all test classes under the `random` directory and all test classes
# that are in java filenames that match `*Abstract*Test.java`.
#
# - The broken test classes previously identified by Defects4J, this information
# lives in, for example for Math project,
# https://github.com/rjust/defects4j/tree/master/framework/projects/Math/failing_tests
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

BUGS_FILE="$SCRIPT_DIR/../../../benchmarks/bugs.csv"
[ -s "$BUGS_FILE" ] || die "$BUGS_FILE does not exist or it is empty!"

D4J_HOME="$SCRIPT_DIR/../../../benchmarks/defects4j"
[ -d "$D4J_HOME" ] || die "$D4J_HOME does not exist!"

COLLECT_TEST_CLASSES_UTIL_JAR_FILE="$SCRIPT_DIR/../util/collect_test_classes/target/collecttestclasses-0.0.1-SNAPSHOT-jar-with-dependencies.jar"
[ -s "$COLLECT_TEST_CLASSES_UTIL_JAR_FILE" ] || die "$COLLECT_TEST_CLASSES_UTIL_JAR_FILE does not exist!"

export JAVA_HOME="$SCRIPT_DIR/../../../jdks/jdk1.8.0_181"
[ -d "$JAVA_HOME" ] || die "$JAVA_HOME does not exist!"
export PATH="$JAVA_HOME/bin:$PATH"

USAGE="Usage: ${BASH_SOURCE[0]}"
[ "$#" -eq "0" ] || die "$USAGE"

TMP_DIR="/tmp"

# ------------------------------------------------------------------------- Main

while read -r line; do
  pid=$(echo "$line" | cut -f2 -d',')
  bid=$(echo "$line" | cut -f3 -d',')

  dir="$SCRIPT_DIR/$pid/$bid"
  mkdir -p "$dir"
  excluded_file="$dir/excluded.txt"
  rm -f "$excluded_file"

  # Checkout
  work_dir="$TMP_DIR/$USER-$$-$pid-${bid}b"
  rm -rf "$work_dir"
  "$D4J_HOME/framework/bin/defects4j" checkout -p "$pid" -v "${bid}b" -w "$work_dir" || die "Checkout of $pid-${bid}b has failed!"

  # Get tests source directory
  tests_dir="$work_dir/$(cd "$work_dir" && "$D4J_HOME/framework/bin/defects4j" export -p dir.src.tests)"
  [ -d "$tests_dir" ] || die "$tests_dir does not exist!"

  # Get list of excluded classes
  pushd . > /dev/null 2>&1
  cd "$tests_dir" || die "Failed to switch to $tests_dir!"

  # Note that the deletion of 'abstract' classes may raise compilation issues,
  # therefore they are not marked to be excluded.

  if [ "$pid" == "Chart" ]; then
    # <exclude name="**/*Package*.java"/>
    for exp in "**/.*Package.*\.java"; do
      find . -type f -name "*.java" -printf '%P\n' | grep "$exp" | sed "s|\.java$||g" | sed "s|/|.|g" | sed 's|^|--- |g' >> "$excluded_file"
    done
  elif [ "$pid" == "Closure" ]; then
    # no test class is, by default, excluded
    rm -rf "$work_dir" # Clean up
    popd > /dev/null 2>&1
    continue
  elif [ "$pid" == "Lang" ]; then
    # <exclude name="**/*Abstract*Test.java"/>
    # <exclude name="**/RandomUtilsTest.java"/>
    for exp in "**/.*Abstract.*Test\.java" "**/RandomUtilsTest\.java"; do
      find . -type f -name "*.java" -printf '%P\n' | grep "$exp" | sed "s|\.java$||g" | sed "s|/|.|g" | sed 's|^|--- |g' >> "$excluded_file"
    done
  elif [ "$pid" == "Math" ]; then
    # <exclude name="**/random/*.java"/>
    # <exclude name="**/*Abstract*Test.java"/>
    for exp in "**/random/.*\.java" "**/.*Abstract.*Test\.java"; do
      find . -type f -name "*.java" -printf '%P\n' | grep "$exp" | sed "s|\.java$||g" | sed "s|/|.|g" | sed 's|^|--- |g' >> "$excluded_file"
    done
  elif [ "$pid" == "Mockito" ]; then
    # <exclude name="**/Abstract*.class"/>
    # <exclude name="**/GitHubTicketFetcherTest*"/>
    for exp in "**/Abstract.*\.java" "**/GitHubTicketFetcherTest.*"; do
      find . -type f -name "*.java" -printf '%P\n' | grep "$exp" | sed "s|\.java$||g" | sed "s|/|.|g" | sed 's|^|--- |g' >> "$excluded_file"
    done
  elif [ "$pid" == "Time" ]; then
    # <exclude name="**/TestAll*.java" />
    # <exclude name="**/TestParseISO.java" />
    # <exclude name="**/*Abstract*Test.java" />
    # <exclude name="**/gj/*.java" />
    for exp in "**/TestAll.*\.java" "**/TestParseISO\.java" "**/.*Abstract.*Test\.java" "**/gj/.*\.java"; do
      find . -type f -name "*.java" -printf '%P\n' | grep "$exp" | sed "s|\.java$||g" | sed "s|/|.|g" | sed 's|^|--- |g' >> "$excluded_file"
    done
  fi

  popd > /dev/null 2>&1

  #
  # Remove non-JUnit test classes, if any
  #
  if [ -s "$excluded_file" ]; then
    pushd . > /dev/null 2>&1
    cd "$work_dir" || die "Failed to switch to $tests_dir!"
      classpath=$("$D4J_HOME/framework/bin/defects4j" export -p cp.test)
      echo "classpath: $classpath"
      bin_tests_dir="$work_dir/$("$D4J_HOME/framework/bin/defects4j" export -p dir.bin.tests)"
      echo "bin_tests_dir: $bin_tests_dir"

      "$D4J_HOME/framework/bin/defects4j" compile || die "Failed to compile $pid-$bid!"
      [ -d "$bin_tests_dir" ] || die "$bin_tests_dir does not exist!"
    popd > /dev/null 2>&1

    java -cp "$D4J_HOME/framework/projects/lib/junit-4.11.jar:$classpath:$COLLECT_TEST_CLASSES_UTIL_JAR_FILE" \
      collecttestclasses.Main "$bin_tests_dir" "$work_dir/test-classes.txt" || die "Failed to collect list of true test classes of $pid-$bid!"
    [ -s "$work_dir/test-classes.txt" ] || die "0 test classes have been identified!"

    while read -r test; do
      if grep -q "^$test$" "$work_dir/test-classes.txt"; then
        echo "--- $test" >> "$excluded_file.tmp"
      fi
    done < <(cat "$excluded_file" | cut -f2 -d' ')
    if [ -s "$excluded_file.tmp" ]; then
      mv "$excluded_file.tmp" "$excluded_file"
    else
      # if there is no "$excluded_file.tmp" or it is empty, "$excluded_file" can
      # be removed
      rm -f "$excluded_file"
    fi
  fi

  # And also exclude the known failing test classes on the fixed version
  rev_id=$(grep "^$bid," "$D4J_HOME/framework/projects/$pid/commit-db" | cut -f3 -d',')
  failing_tests_file="$D4J_HOME/framework/projects/$pid/failing_tests/$rev_id"
  if [ -s "$failing_tests_file" ]; then
    grep -a "^\-\-\- " "$failing_tests_file" | grep -v "::" >> "$excluded_file"
  fi

  if [ -s "$excluded_file" ]; then # Remove duplicates
    sort -u "$excluded_file" > "$excluded_file.tmp" && mv "$excluded_file.tmp" "$excluded_file" || die "Failed to remove duplicates from $excluded_file!"
  else
    # excluded.txt is empty or no longer exists, in either cases try to remove it
    rm -f "$excluded_file"
  fi

  rm -rf "$work_dir" # Clean up
done < <(grep "^Defects4J," "$BUGS_FILE")

echo "DONE!"
exit 0
