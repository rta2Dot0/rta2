#!/usr/bin/env bash
#
# ------------------------------------------------------------------------------
# This script collects the list of test classes that are by default excluded by
# the Maven Sufire plugin when one runs `mvn test`. For example, the
# [pom.xml file](https://github.com/bears-bugs/bears-benchmark/blob/FasterXML-jackson-databind-247621332-247674379/pom.xml#L103)
# of the FasterXML-jackson-databind 247621332-247674379 bug excludes all test
# classes in the com.fasterxml.jackson.failing package from the test execution:
# ```
# <plugin>
#   <groupId>org.apache.maven.plugins</groupId>
#   <version>${version.plugin.surefire}</version>
#   <artifactId>maven-surefire-plugin</artifactId>
#   <configuration>
#     <classpathDependencyExcludes>
#       <exclude>javax.measure:jsr-275</exclude>
#     </classpathDependencyExcludes>
#     <excludes>
#       <exclude>com/fasterxml/jackson/failing/*.java</exclude>
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

BUGS_FILE="$SCRIPT_DIR/../../../benchmarks/bugs.csv"
[ -s "$BUGS_FILE" ] || die "$BUGS_FILE does not exist or it is empty!"

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

  python ../get_excluded_test_classes_maven_projects.py --benchmark "Bears" --project "$pid" --bug "$bid" --output_file "$excluded_file" || die "Failed to collect list of excluded test classes of $pid::$bid!"

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
  fi

done < <(grep "^Bears," "$BUGS_FILE")

echo "DONE!"
exit 0
