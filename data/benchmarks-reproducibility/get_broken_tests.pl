#!/usr/bin/env perl
# ------------------------------------------------------------------------------
# This script collects the set of test cases that fail on the buggy version but
# are not true bug revealing tests.
#
# Usage:
# ./get_broken_tests.pl
#   <benchmarks trigger_tests.txt>
#   <failing_tests.txt on the buggy version>
#   <output file: broken_tests.txt>
#
# ------------------------------------------------------------------------------

use strict;
use warnings;

use Array::Utils;
use List::MoreUtils qw(uniq);

$#ARGV == 2 or die("Usage: get_broken_tests.pl <benchmarks trigger_tests.txt> <failing_tests.txt on the buggy version> <output file: broken_tests.txt>");

# Inputs
my $BENCHMARK_TRIGGER_TESTS_FILE = $ARGV[0];
my $GENERATED_FAILING_TESTS_FILE = $ARGV[1];
-e $BENCHMARK_TRIGGER_TESTS_FILE or die("$BENCHMARK_TRIGGER_TESTS_FILE does not exist!");
-e $GENERATED_FAILING_TESTS_FILE or die("$GENERATED_FAILING_TESTS_FILE does not exist!");
# Output
my $BROKEN_TESTS_FILE = $ARGV[2];
system("rm -f $BROKEN_TESTS_FILE;") == 0 or die("Failed to remove $BROKEN_TESTS_FILE!");

open(IN, "<$BENCHMARK_TRIGGER_TESTS_FILE") or die("Cannot read benchmark's trigger_tests.txt file!");
  my @benchmark_trigger_tests = sort(<IN>);
close(IN);
if (scalar(@benchmark_trigger_tests) == 0) {
  # Nothing to compare with
  print("DONE!\n");
  exit(0);
}

open(IN, "<$GENERATED_FAILING_TESTS_FILE") or die("Cannot read generated failing_tests.txt file!");
  my @generated_failing_tests = sort(<IN>);
close(IN);
if (scalar(@generated_failing_tests) == 0) {
  print(STDERR "No test to be considered as broken\n");
  exit(0);
}

# get those tests that exist in '@generated_failing_tests' and do not exist in
# '@benchmark_trigger_tests'. by other words, get the list of tests that fail
# on the buggy version but are not trigger tests
my @broken_tests = Array::Utils::array_minus(@generated_failing_tests, @benchmark_trigger_tests);
if (scalar(@broken_tests) > 0) {
  open(my $fh, ">$BROKEN_TESTS_FILE") or die("Could not open $BROKEN_TESTS_FILE to write the list of broken tests!");
    foreach my $broken_test (uniq @broken_tests) {
      print(STDERR "$broken_test");
      print($fh "$broken_test");
    }
  close($fh);
}

print("DONE!\n");
exit(0);
