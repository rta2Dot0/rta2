#!/usr/bin/env bash
# ------------------------------------------------------------------------------
#
# This script collects metadata of all bugs in Bugs.jar benchmark.
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

bugs_dot_jar_dissection_checkout_dir="/tmp/bugs-dot-jar-dissection-$$"
rm -rf "$bugs_dot_jar_dissection_checkout_dir"
git clone https://github.com/tdurieux/bugs-dot-jar-dissection.git "$bugs_dot_jar_dissection_checkout_dir" || die "Failed to clone bugs-dot-jar-dissection to $bugs_dot_jar_dissection_checkout_dir!"

while read -r line; do
  pid=$(echo "$line" | cut -f2 -d',')
  bid=$(echo "$line" | cut -f3 -d',')
  echo "project: $pid :: bug: $bid"

  #
  # Get bug
  #

  pid_bid_checkout_dir="/tmp/bugs-dot-jar-$pid-$bid-$$"
  rm -rf "$pid_bid_checkout_dir"

  repository_url="https://github.com/bugs-dot-jar/$(echo $pid | tr '[:upper:]' '[:lower:]').git"
  git clone "$repository_url" "$pid_bid_checkout_dir" || die "Failed to clone $repository_url to $pid_bid_checkout_dir!"
  pushd . > /dev/null 2>&1
  cd "$pid_bid_checkout_dir"
    # find the commit
    commit_id=$(git branch -a | grep "_$bid$" | tail -n1 | cut -f3 -d '/')
    # checkout the buggy code
    git checkout "$commit_id" || die "Failed to checkout commit $commit_id!"
  popd > /dev/null 2>&1

  #
  # Copy over metadata
  #

  remote_metadata_dir="$pid_bid_checkout_dir/.bugs-dot-jar"
  [ -d "$remote_metadata_dir" ] || die "$remote_metadata_dir does not exist!"

  local_metadata_dir="$SCRIPT_DIR/$pid/$bid/"
  mkdir -p "$local_metadata_dir" || die "Failed to create $local_metadata_dir!"

  cp -v $remote_metadata_dir/* "$local_metadata_dir/" || die "Failed to copy data from $remote_metadata_dir/* to $local_metadata_dir!"

  json_file="$bugs_dot_jar_dissection_checkout_dir/data/$(echo $pid | tr '[:upper:]' '[:lower:]')/$bid.json"
  [ -s "$json_file" ] || die "$json_file does not exist or it is empty!"
  cp -v "$json_file" "$local_metadata_dir/" || die "Failed to copy $json_file to $local_metadata_dir!"

  rm -rf "$pid_bid_checkout_dir" # Clean up
done < <(grep "Bugs.jar," "$BUGS_FILE")

rm -rf "$bugs_dot_jar_dissection_checkout_dir" # Clean up

echo "DONE!"
exit 0
