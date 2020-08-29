#!/usr/bin/env perl
# ------------------------------------------------------------------------------
# This script checks whether the set of failing tests on the buggy version
# includes the expected set of trigger test cases provided by the benchmark.
#
#   - If none of the tests failing on the buggy version are expected trigger
#     tests, this script exits with 1.
#   - If at least one expected trigger test no longer fails on the buggy
#     version, this script exits with 1.
#   - If all expected trigger tests do fail, this script exits with 0.
#
# Usage:
# ./check_trigger_tests.pl
#   <failing_tests.txt on the buggy version>
#   <benchmarks trigger_tests.txt>
#   <generated trigger_tests.txt>
#
# ------------------------------------------------------------------------------

use strict;
use warnings;

use Array::Utils;

$#ARGV == 2 or die("Usage: $#ARGV check_trigger_tests.pl <failing_tests.txt on the buggy version> <benchmarks trigger_tests.txt> <generated trigger_tests.txt>");

# Inputs
my $FAILING_TESTS_FILE_ON_BUGGY  = $ARGV[0];
my $BENCHMARK_TRIGGER_TESTS_FILE = $ARGV[1];
my $GENERATED_TRIGGER_TESTS_FILE = $ARGV[2];
-e $FAILING_TESTS_FILE_ON_BUGGY  or die("$FAILING_TESTS_FILE_ON_BUGGY does not exist!");
-e $BENCHMARK_TRIGGER_TESTS_FILE or die("$BENCHMARK_TRIGGER_TESTS_FILE does not exist!");
-e $GENERATED_TRIGGER_TESTS_FILE or die("$GENERATED_TRIGGER_TESTS_FILE does not exist!");

open(IN, "<$FAILING_TESTS_FILE_ON_BUGGY") or die("Cannot read failing_tests.txt file generated on the buggy version!");
  my @failing_tests_on_buggy = sort(<IN>);
close(IN);
my $num_failing_tests_on_buggy = scalar(@failing_tests_on_buggy);
if ($num_failing_tests_on_buggy == 0) {
  print(STDERR "No failing tests\n");
  exit(1);
}

open(IN, "<$BENCHMARK_TRIGGER_TESTS_FILE") or die("Cannot read benchmark's trigger_tests.txt file!");
  my @benchmark_trigger_tests = sort(<IN>);
close(IN);
my $num_expected_trigger_tests = scalar(@benchmark_trigger_tests);
if ($num_expected_trigger_tests == 0) {
  # Nothing to compare with, so its assumed the buggy version is triggering same set of tests
  print(STDERR "Same trigger tests and 0 non-trigger tests\n");
  exit(0);
}

open(IN, "<$GENERATED_TRIGGER_TESTS_FILE") or die("Cannot read generated trigger_tests.txt file!");
  my @generated_trigger_tests = sort(<IN>);
close(IN);
my $num_actual_trigger_tests = scalar(@generated_trigger_tests);
if ($num_actual_trigger_tests == 0) {
  print(STDERR "No set of trigger tests to check\n");
  exit(1);
}

my @intersect = Array::Utils::intersect(@benchmark_trigger_tests, @generated_trigger_tests);
my $num_tests_intersect = scalar(@intersect);
$num_tests_intersect <= $num_expected_trigger_tests or die("$num_tests_intersect is not <= than $num_expected_trigger_tests");

if ($num_tests_intersect < $num_expected_trigger_tests) {
  my $num_non_trigger_tests = $num_failing_tests_on_buggy - $num_tests_intersect;
  print(STDERR "Fewer trigger tests ($num_tests_intersect vs $num_expected_trigger_tests) and $num_non_trigger_tests non-trigger tests\n");
  exit(1); # Bug cannot be reproducible
}

if ($num_tests_intersect == $num_expected_trigger_tests) {
  my $num_non_trigger_tests = $num_failing_tests_on_buggy - $num_tests_intersect;
  # $num_non_trigger_tests == 0, bug can be reproducible
  # $num_non_trigger_tests  > 0, bug could be reproducible if non-trigger tests get removed at checkout
  print(STDERR "Same trigger tests and $num_non_trigger_tests non-trigger tests\n");
  exit(0);
}
