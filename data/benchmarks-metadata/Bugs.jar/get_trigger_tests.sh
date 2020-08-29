#!/usr/bin/env bash
# ------------------------------------------------------------------------------
#
# This script runs the `get_trigger_tests.pl` for all bugs in the Bugs.jar
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

# ------------------------------------------------------------------------- Main

USAGE="Usage: ${BASH_SOURCE[0]}"
[ "$#" -eq "0" ] || die "$USAGE"

while read -r line; do
  pid=$(echo "$line" | cut -f2 -d',')
  bid=$(echo "$line" | cut -f3 -d',')
  echo "project: $pid :: bug: $bid"

  ./get_trigger_tests.pl "$SCRIPT_DIR/$pid/$bid/$bid.json" "$SCRIPT_DIR/$pid/$bid/test-results.txt" "$SCRIPT_DIR/$pid/$bid/trigger_tests.txt"
done < <(grep "Bugs.jar," "$BUGS_FILE")

echo "DONE!"
exit 0
