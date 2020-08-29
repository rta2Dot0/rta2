#!/usr/bin/env bash
# ------------------------------------------------------------------------------
#
# This script collects metadata of all bugs in Bears benchmark.
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

BUGS_FILE="$SCRIPT_DIR/../../../benchmarks/bugs.csv"
[ -s "$BUGS_FILE" ] || die "$BUGS_FILE does not exist or it is empty!"

USAGE="Usage: ${BASH_SOURCE[0]}"
[ "$#" -eq "0" ] || die "$USAGE"

# ------------------------------------------------------------------------- Main

repository_dir="/tmp/bears-$$"
rm -rf "$pid_bid_checkout_dir"

repository_url="https://github.com/bears-bugs/bears-benchmark.git"
git clone "$repository_url" "$repository_dir" || die "Failed to clone $repository_url to $repository_dir!"

while read -r line; do
  pid=$(echo "$line" | cut -f2 -d',')
  bid=$(echo "$line" | cut -f3 -d',')
  echo "project: $pid :: bug: $bid"

  #
  # Get bug
  #

  pushd . > /dev/null 2>&1
  cd "$repository_dir"
    commit_id="$pid-$bid"
    # checkout the buggy code
    git checkout "$commit_id" || die "Failed to checkout commit $commit_id!"
  popd > /dev/null 2>&1

  #
  # Copy over metadata
  #

  local_metadata_dir="$SCRIPT_DIR/$pid/$bid/"
  mkdir -p "$local_metadata_dir" || die "Failed to create $local_metadata_dir!"

  json_file="$repository_dir/bears.json"
  [ -s "$json_file" ] || die "$json_file does not exist or it is empty!"
  cp -v "$json_file" "$local_metadata_dir/" || die "Failed to copy $json_file to $local_metadata_dir!"
done < <(grep "Bears," "$BUGS_FILE")

rm -rf "$repository_dir" # Clean up

echo "DONE!"
exit 0
