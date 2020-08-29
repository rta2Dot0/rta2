#!/usr/bin/env bash
# ------------------------------------------------------------------------------
# This script collects the reproducibility of all bugs. For each bug it executes
# the is_bug_reproducible.sh script.
#
# Usage:
# ./are_all_bugs_reproducible.sh
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

USAGE="Usage: ${BASH_SOURCE[0]}"
[ "$#" -eq "0" ] || die "$USAGE"

# ------------------------------------------------------------------------- Main

BUGGY_STR="buggy"
FIXED_STR="fixed"

echo "benchmark,project,bug,java_version,status,comment"
for jvm in "7" "8"; do
  while read -r bug; do
    benchmark=$(echo "$bug" | cut -f1 -d',')
      project=$(echo "$bug" | cut -f2 -d',')
          bug=$(echo "$bug" | cut -f3 -d',')
    bash "$SCRIPT_DIR/is_bug_reproducible.sh" --benchmark "$benchmark" --project "$project" --bug "$bug" --jvm "$jvm" || die "Failed to check the reproducibility of $benchmark -- $project -- $bug under Java-$jvm!"
  done < <(tail -n +2 "$BUGS_FILE")
done

echo "DONE!" >&2
exit 0
