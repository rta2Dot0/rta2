#!/usr/bin/env bash
# ------------------------------------------------------------------------------
# Given a data directory and a file with a list of jobs, this script checks
# which jobs did not finish successfully and writes the command to re-run those
# to a file.
#
# Usage:
# ./get_list_missing_jobs.sh
#   --data_dir <path>
#   --jobs_file <path>
#   --version_type <'fixed'|'buggy'>
#   --output_file <path>
#   [help]
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

USAGE="Usage: ${BASH_SOURCE[0]} --data_dir <path> --jobs_file <path> --version_type <'fixed'|'buggy'> --output_file <path> [help]"
if [ "$#" -ne "1" ] && [ "$#" -ne "8" ]; then
  die "$USAGE"
fi

DATA_DIR=""
JOBS_FILE=""
VERSION_TYPE=""
OUTPUT_FILE=""

while [[ "$1" = --* ]]; do
  OPTION=$1; shift
  case $OPTION in
    (--data_dir)
      DATA_DIR=$1;
      shift;;
    (--jobs_file)
      JOBS_FILE=$1;
      shift;;
    (--version_type)
      VERSION_TYPE=$1;
      shift;;
    (--output_file)
      OUTPUT_FILE=$1;
      shift;;
    (--help)
      echo "$USAGE"
      exit 0
    (*)
      die "$USAGE";;
  esac
done

[ "$DATA_DIR" != "" ]     || die "'--data_dir' not defined. $USAGE"
[ -d "$DATA_DIR" ]        || die "$DATA_DIR does not exist!"

[ "$JOBS_FILE" != "" ]    || die "'--jobs_file' not defined. $USAGE"
[ -s "$JOBS_FILE" ]       || die "$JOBS_FILE does not exist or it is empty!"

[ "$VERSION_TYPE" != "" ] || die "'--version_type' not defined. $USAGE"

[ "$OUTPUT_FILE" != "" ]  || die "'--output_file' not defined. $USAGE"
rm -f "$OUTPUT_FILE"

# ------------------------------------------------------------------ Envs & Args

cat "$JOBS_FILE" | tr ' ' '\n' | grep "job.log" | tr -d '"' | rev | cut -f1,2,3,4,5 -d'/' | rev | while read row; do \

  log_file="$DATA_DIR/$row"
  if [ ! -f "$log_file" ]; then
    grep "$row" "$JOBS_FILE" >> "$OUTPUT_FILE"
    continue
  fi

  compile_log_file=$(echo "$log_file" | sed "s|job.log|compile.log|g")
  if [ -f "$compile_log_file" ]; then
    if grep -q "invalid target release: 1.8" "$compile_log_file"; then
      continue
    fi
    if grep -q "Unsupported major.minor version 52.0" "$compile_log_file"; then
      continue
    fi
    if grep -q "error: unexpected end tag:" "$compile_log_file"; then
      grep "$row" "$JOBS_FILE" >> "$OUTPUT_FILE"
      continue
    fi
  fi

  if grep -q "fatal: Unable to create " "$log_file"; then
    grep "$row" "$JOBS_FILE" >> "$OUTPUT_FILE"
    continue
  fi

  if grep -q "ParseError: no element found: " "$log_file"; then
    grep "$row" "$JOBS_FILE" >> "$OUTPUT_FILE"
    continue
  fi

  if grep -q "already exists in working directory" "$log_file"; then
    grep "$row" "$JOBS_FILE" >> "$OUTPUT_FILE"
    continue
  fi

  if ! grep -q "^DONE\!$" "$log_file"; then
    grep "$row" "$JOBS_FILE" >> "$OUTPUT_FILE"
    continue
  fi

  status_csv_file=$(echo "$log_file" | sed "s|job.log|status.csv|g")
  if [ ! -f "$status_csv_file" ]; then
    grep "$row" "$JOBS_FILE" >> "$OUTPUT_FILE"
    continue
  fi;

  num_rows=$(wc -l "$status_csv_file" | cut -f1 -d' ')
  if [ "$num_rows" -ne "2" ]; then
    grep "$row" "$JOBS_FILE" >> "$OUTPUT_FILE"
    continue
  fi

  if grep -q ",NA$" "$status_csv_file"; then
    grep "$row" "$JOBS_FILE" >> "$OUTPUT_FILE"
    continue
  fi

  if [ "$VERSION_TYPE" == "buggy" ]; then
    if grep -q ",0$" "$status_csv_file"; then
      grep "$row" "$JOBS_FILE" >> "$OUTPUT_FILE"
      continue
    fi
  fi

done

echo "DONE!" >&2
exit 0
