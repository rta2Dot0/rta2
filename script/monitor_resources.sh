#!/usr/bin/env bash
# ------------------------------------------------------------------------------
#
# Every 5 seconds, this script writes to /tmp/$USER-$(hostname -s).resources.csv
# the number of processes and memory available. Format:
#   timestamp,num_processes,mem_total,mem_available,tmp_space_avail,scratch_space_avail
#
# If at any point the number of processes and threads is higher than 4000 or the
# available space in /tmp is less than 5GB, this script dumps the list of
# running processes and threads to
#   /tmp/$USER-$(hostname -s).processes-and-threads.txt
# and kills all processes and threads.
#
# Usage:
#   nohup ./monitor_resources.sh > /dev/null 2>&1 &
#
# ------------------------------------------------------------------------------

RESOURCES_OUTPUT_FILE="/tmp/$USER-$(hostname -s).resources.csv"
echo "timestamp,num_processes,mem_total,mem_available,tmp_avail,scratch_avail" > "$RESOURCES_OUTPUT_FILE"

DUMP_PROCESSES_FILE="/tmp/$USER-$(hostname -s).processes-and-threads.txt"

# ------------------------------------------------------------------------- Util

#
# Kill all processes and threads running on the machine
#
_kill() {
  # Attempt to terminate them all
  for cmd in "java_exec" "java" "perl" "python"; do
    killall "$cmd"
  done

  local MY_PID="$$"

  ps -ef | \
    grep "^$USER" | \
    grep "java\|perl\|python\|monitor_resources.sh" | \
    grep -v "tmux" | grep -v "screen" | \
    grep -v "ssh" | \
    grep -v "grep" | cut -f2 -d' ' | while read -r pid; do
      if [ "$MY_PID" -eq "$pid" ]; then
        # Do not kill itself
        continue
      fi

      while ps --pid "$pid" > /dev/null 2>&1; do # Returns 0 if $pid still exists, 1 otherwise
        kill "$pid"
        sleep 3
        if ps --pid "$pid" > /dev/null 2>&1; then
          kill -9 "$pid"
        fi
      done
    done

  return 0
}

# ------------------------------------------------------------------------- Main

while true; do
  # Number of processes
  num_proc=$(ps -eLf | grep "^$USER" | wc -l)

  # Memory
  mem_total=$(cat /proc/meminfo | grep "^MemTotal: "     | cut -f8 -d' ')
  mem_avail=$(cat /proc/meminfo | grep "^MemAvailable: " | cut -f4 -d' ')

  # Disk space
  tmp_space_avail=$(df --output=avail "/tmp" | tail -n1 | tr -d ' ')
  scratch_space_avail="NA"
  if [ -d "/scratch" ]; then
    scratch_space_avail=$(df --output=avail "/scratch" | tail -n1 | tr -d ' ')
  fi

  # File content
  echo "$(date),$num_proc,$mem_total,$mem_avail,$tmp_space_avail,$scratch_space_avail" >> "$RESOURCES_OUTPUT_FILE"

  if [ "$num_proc" -ge "4000" ] || [ "$tmp_space_avail" -lt "5242880" ]; then
    # Dump list of processes and threads
    ps -emf | grep "^$USER" > "$DUMP_PROCESSES_FILE"

    # Kill any remaining process/thread
    _kill
  fi

  # Some test cases in the logging-log4j2 project from the Bugs.jar benchmark
  # populate two known log files with billions of debug messages. Those two
  # files grow in size so quickly that no file system could handle them. As they
  # are only used to log debug messages and nothing else, in here, every 5
  # seconds, those two log files are shrinked to 0 bytes.
  find /tmp/*_Bugs.jar_Logging-Log4J2_*/ -type f -name testlog4j.log   -exec truncate -s0 {} \;
  find /tmp/*_Bugs.jar_Logging-Log4J2_*/ -type f -name testlogback.log -exec truncate -s0 {} \;

  sleep 5
done
