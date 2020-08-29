#!/usr/bin/env perl

use strict;
use warnings;
use sigtrap qw/handler kill_cmd normal-signals/;
use Proc::Simple;
use File::Basename;

my $HERE = dirname(__FILE__);

# Set up environment
my $jopts  = $ENV{_JAVA_OPTIONS} // "";
my $jtopts = $ENV{JAVA_TOOL_OPTIONS} // "";
$ENV{JAVA_TOOL_OPTIONS} = "-XX:CICompilerCount=2 -XX:ParallelGCThreads=2 -XX:ConcGCThreads=2 $jopts $jtopts";

# Create command
my $CMD = "$HERE/java_exec";

# Create a new process object
my $PROC = Proc::Simple->new();

# Launch command
$PROC->start($CMD, @ARGV);

# Kill process when the object is destroyed (i.e., set flag to true)
$PROC->kill_on_destroy(1);
$PROC->signal_on_destroy("KILL");

# Limit the number of threads the JVM is allowed to create
my $THREAD_LIMIT = 500;

# PIDs
my $PARENT_ID = getppid();
my $MY_PID    = $$;
my $JVM_PID   = $PROC->pid;

while (1) {
    # Check if the process is still running, 1 if it is, 0 otherwise
    if ($PROC->poll() == 0) {
        # JVM already terminated
        exit($PROC->exit_status() == 0 ? 0 : 1);
    } else { # JVM is still alive
        # Get current parent pid
        my $current_ppid = getppid();
        if ($current_ppid == 1) {
            # Parent shell is gone; parent is now 1 -- the init process
            print(STDERR "Parent $PARENT_ID is gone. Kill $JVM_PID!\n");
            kill_cmd(1);
        } else {
            my $num_threads = `ps -T -p $JVM_PID | wc -l`;
            if ($num_threads >= $THREAD_LIMIT) {
                # Rogue JVM process
                print(STDERR "JVM seems rogue. Kill $JVM_PID!\n");
                kill_cmd(1);
            } else {
                # Parent shell may still be alive; sleep 1 sec and check again
                sleep 1;
            }
        }
    }
}

sub kill_cmd {
    my $log_events = shift // 0;

    if ($log_events) {print(STDERR "Terminate $JVM_PID!\n");}
    $PROC->kill("TERM");
    sleep 2;
    if ($PROC->poll() == 1) { # Is it still alive?
        if ($log_events) {print(STDERR "Kill $JVM_PID!\n");}
        $PROC->kill("KILL");
    }
    die "Killed $JVM_PID!";
}
