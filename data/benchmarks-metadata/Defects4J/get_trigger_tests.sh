#!/usr/bin/env bash
# ------------------------------------------------------------------------------
#
# This script collects the list of trigger tests from the official metadata
# provide by the Defects4J benchmark.
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

D4J_DIR="$SCRIPT_DIR/../../../benchmarks/defects4j"
[ -d "$D4J_DIR" ] || die "$D4J_DIR does not exist!"

USAGE="Usage: ${BASH_SOURCE[0]}"
[ "$#" -eq "0" ] || die "$USAGE"

# ------------------------------------------------------------------------- Main

while read -r line; do
  pid=$(echo "$line" | cut -f2 -d',')
  bid=$(echo "$line" | cut -f3 -d',')
  echo "project: $pid :: bug: $bid"

  grep -a "^\-\-\- " "$D4J_DIR/framework/projects/$pid/trigger_tests/$bid" > "$SCRIPT_DIR/$pid/$bid/trigger_tests.txt"
done < <(grep "Defects4J," "$BUGS_FILE")

echo "DONE!"
exit 0
