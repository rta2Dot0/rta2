#!/usr/bin/env bash
#
# ------------------------------------------------------------------------------
# This script collects the list of Math bugs that are in the Bugs.jar benchmark
# and also in the Defects4J benchmarks.  The script prints to the stdout the
# list of bugs in common. The format of the output is as follows:
#   Math,<Bugs.jar identifier, i.e., branch-name>,<Bugs.jar RTA id>,Commonts-Math,<Defects4J identifier, i.e., bug-id>,<Defects4J RTA id>
#
# Usage:
# ./get_common_bugs_d4j_and_bugs_dot_jar.sh
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

D4J_HOME="$SCRIPT_DIR/../../../benchmarks/defects4j"
[ -d "$D4J_HOME" ] || die "$D4J_HOME does not exist!"

USAGE="Usage: ${BASH_SOURCE[0]}"
[ "$#" -eq "0" ] || die "$USAGE"

# ------------------------------------------------------------------------- Main

TMP_DIR="/tmp/$$-get_common_bugs_d4j_and_bugs_dot_jar"
rm -rf "$TMP_DIR" && mkdir "$TMP_DIR" || die "Failed to create a temporary directory!"

#
# Get commit messages from D4J commons-math
#

D4J_COMMONS_MATH_COMMIT_DB_FILE="$D4J_HOME/framework/projects/Math/commit-db"
[ -s "$D4J_COMMONS_MATH_COMMIT_DB_FILE" ] || die "'$D4J_COMMONS_MATH_COMMIT_DB_FILE' does not exist or it is empty!"

D4J_COMMONS_MATH_GIT_REPOSITORY="$D4J_HOME/project_repos/commons-math.git"
D4J_COMMONS_MATH_GIT_LOG_FILE="$TMP_DIR/d4j-commons-math-git.log"

git --git-dir="$D4J_COMMONS_MATH_GIT_REPOSITORY" log --format=%H | while read sha1; do
  git --git-dir="$D4J_COMMONS_MATH_GIT_REPOSITORY" show -s --format='%H,%B' "$sha1" | tr '\n' ' ' >> "$D4J_COMMONS_MATH_GIT_LOG_FILE"
  # Add \n to the file, so that next entry is a new row
  echo >> "$D4J_COMMONS_MATH_GIT_LOG_FILE"
done || die "Failed to get commit messages from D4J commons-math repository!"
[ -s "$D4J_COMMONS_MATH_GIT_LOG_FILE" ] || die "'$D4J_COMMONS_MATH_GIT_LOG_FILE' does not exist or it is empty!"

#
# Get Bugs.jar commons-math
#

BUGS_DOT_JAR_COMMONS_MATH_DIR="$TMP_DIR/bugs-dot-jar-commons-math"
git clone https://github.com/bugs-dot-jar/commons-math.git "$BUGS_DOT_JAR_COMMONS_MATH_DIR" >&2 || die "Failed to clone commons-math from Bugs.jar!"

#
# Get common bugs
#

pushd . > /dev/null 2>&1
cd "$BUGS_DOT_JAR_COMMONS_MATH_DIR"
  git checkout eafb16c711d5cd79edad5fbb2055252acdb3825e >&2 || die "Failed to checkout eafb16c!"

  # Header
  echo "bugs_dot_jar_project_name,bugs_dot_jar_bug_id,bugs_dot_jar_repair_them_all_id,d4j_project_name,d4j_bug_id,d4j_repair_them_all_id"

  git br -a | grep "bugs-dot-jar" | cut -f3 -d'/' | while read -r branch; do
    issue_id=$(echo "$branch" | cut -f2 -d'_')
        hash=$(echo "$branch" | cut -f3 -d'_')

    # The Bugs.jar commons-math issue-id is not in D4J
    grep -q ",$issue_id," "$D4J_COMMONS_MATH_COMMIT_DB_FILE"|| continue

    # Get commit message from Bugs.jar commons-math repository
    msg=$(git show -s --format='%B' -n 1 "$hash" | tr '\n' ' ')

    # The commit message from Bugs.jar commons-math repository must be known D4J commons-math
    grep -q -F ",$msg" "$D4J_COMMONS_MATH_GIT_LOG_FILE"
    if [ "$?" -ne "0" ]; then
      echo "Although the issue-id ($issue_id) is in the D4J commit-db, the commit message '$msg' does not appear in the D4J commons-math commit history!" >&2
      echo "One possible reason is that the issue/commit in Bugs.jar is too new for D4J commons-math repository." >&2
      continue
    fi

    # Check for duplicates
    num_entries=$(grep -F ",$msg" "$D4J_COMMONS_MATH_GIT_LOG_FILE" | wc -l)
    [ "$num_entries" -eq "1" ] || die "In the entire D4J commons-math commit history the commit message '$msg' appears more than once!"

    # Get commit hash from D4J commons-math repository based on the commit
    # message from Bugs.jar commons-math repository
    hash_in_d4j=$(grep -F ",$msg" "$D4J_COMMONS_MATH_GIT_LOG_FILE" | cut -f1 -d',')

    # Get D4J bug identifier
    bug_id=$(grep ",$hash_in_d4j,$issue_id," "$D4J_COMMONS_MATH_COMMIT_DB_FILE" | cut -f1 -d',')

    if [ "$bug_id" == "" ]; then
      echo "Although the issue-id ($issue_id) is in the D4J commit-db and the commit message '$msg' is in the D4J commons-math commit history, the hash '$hash_in_d4j' is not in the D4J commit-db!" >&2
      echo "I.e., the bug in D4J has the same id as Bugs.jar but it is a different commit" >&2
      continue
    fi

    echo "Commons-Math,$hash,Commons-Math-$hash,Math,$bug_id,Math-$bug_id"
  done
popd > /dev/null 2>&1

# Clean up
rm -rf "$TMP_DIR"

exit 0
