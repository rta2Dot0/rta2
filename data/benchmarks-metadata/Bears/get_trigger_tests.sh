#!/usr/bin/env bash
# ------------------------------------------------------------------------------
#
# This script runs the `get_trigger_tests.pl` for all bugs in the Bears
# benchmark.
#
# Usage:
# ./get_trigger_tests.sh
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

BUGS_FILE="$SCRIPT_DIR/../../../benchmarks/bugs.csv"
[ -s "$BUGS_FILE" ] || die "$BUGS_FILE does not exist or it is empty!"

USAGE="Usage: ${BASH_SOURCE[0]}"
[ "$#" -eq "0" ] || die "$USAGE"

# ------------------------------------------------------------------------- Main

while read -r line; do
  pid=$(echo "$line" | cut -f2 -d',')
  bid=$(echo "$line" | cut -f3 -d',')
  echo "project: $pid :: bug: $bid"

  trigger_tests_file="$SCRIPT_DIR/$pid/$bid/trigger_tests.txt"
  ./get_trigger_tests.pl "$SCRIPT_DIR/$pid/$bid/bears.json" "$trigger_tests_file" || die "Failed to compute list of trigger tests!"
  if [ -s "$trigger_tests_file" ]; then # Remove duplicates
    sort -u "$trigger_tests_file" > "$trigger_tests_file.tmp" && mv "$trigger_tests_file.tmp" "$trigger_tests_file" || die "Failed to remove duplicates!"
  fi
done < <(grep "Bears," "$BUGS_FILE")

echo "DONE!"
exit 0
