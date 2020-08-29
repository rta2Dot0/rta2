#!/usr/bin/env perl
# ------------------------------------------------------------------------------
# This script collects the set of trigger test cases, i.e., test cases that fail
# on the buggy version (and that have not been considered broken tests) but do
# not fail on the fixed version. The script exits with 0 if there is at least
# one trigger test case, 1 otherwise.
#
# Usage:
# ./get_trigger_tests.pl
#   <failing_tests.txt on the buggy version>
#   <failing_tests.txt on the fixed version>
#   <broken_tests.txt>
#   <output file: trigger_tests.txt>
#
# ------------------------------------------------------------------------------

use strict;
use warnings;

use Array::Utils;
use List::MoreUtils qw(uniq);

$#ARGV == 3 or die("Usage: get_trigger_tests.pl <failing_tests.txt on the buggy version> <failing_tests.txt on the fixed version> <broken_tests.txt> <output file: trigger_tests.txt>");

# Inputs
my $FAILING_TESTS_FILE_ON_BUGGY = $ARGV[0];
my $FAILING_TESTS_FILE_ON_FIXED = $ARGV[1];
-e $FAILING_TESTS_FILE_ON_BUGGY or die("$FAILING_TESTS_FILE_ON_BUGGY does not exist!");
-e $FAILING_TESTS_FILE_ON_FIXED or die("$FAILING_TESTS_FILE_ON_FIXED does not exist!");
my $BROKEN_TESTS_FILE           = $ARGV[2];
# Output
my $TRIGGER_TESTS_FILE          = $ARGV[3];
system("rm -f $TRIGGER_TESTS_FILE; touch $TRIGGER_TESTS_FILE;") == 0 or die("Failed to remove and create an empty $TRIGGER_TESTS_FILE file!");

open(IN, "<$FAILING_TESTS_FILE_ON_BUGGY") or die("Cannot read failing_tests.txt file generated on the buggy version!");
  my @failing_tests_on_buggy = sort(<IN>);
close(IN);
my $num_failing_tests_on_buggy = scalar(@failing_tests_on_buggy);
if ($num_failing_tests_on_buggy == 0) {
  print(STDERR "No failing tests\n");
  exit(1);
}

open(IN, "<$FAILING_TESTS_FILE_ON_FIXED") or die("Cannot read failing_tests.txt file generated on the fixed version!");
  my @failing_tests_on_fixed = sort(<IN>);
close(IN);

my @broken_tests = ();
if (-e $BROKEN_TESTS_FILE) {
  open(IN, "<$BROKEN_TESTS_FILE") or die("Cannot read broken_tests.txt file!");
    @broken_tests = sort(<IN>);
  close(IN);
}

#
# Compute the set of trigger tests as:
#   trigger_tests = failing_tests_on_buggy - failing_tests_on_fixed - broken_tests
#

# Collect the set of tests that pass on the fixed version and fail on the buggy
# version, i.e., trigger_tests = failing_tests_on_buggy - failing_tests_on_fixed
my @trigger_tests = Array::Utils::array_minus(@failing_tests_on_buggy, @failing_tests_on_fixed);
if (scalar(@trigger_tests) == 0) {
  print(STDERR "No trigger test but $num_failing_tests_on_buggy non-trigger tests\n");
  exit(1);
}

# Given the set of tests that pass on the fixed version and fail on the buggy
# version, exclude the ones that have been considered broken tests (i.e., fail
# on the buggy version but are not true fault revealing tests), i.e., compute
#   trigger_tests = trigger_tests - broken_tests
if (scalar(@broken_tests) > 0) {
  @trigger_tests = Array::Utils::array_minus(@trigger_tests, @broken_tests);
  if (scalar(@trigger_tests) == 0) {
    print(STDERR "No trigger test but $num_failing_tests_on_buggy non-trigger tests\n");
    exit(1);
  }
}

open(my $fh, ">$TRIGGER_TESTS_FILE") or die("Could not open $TRIGGER_TESTS_FILE to write the list of trigger tests!");
  foreach my $trigger_test (uniq @trigger_tests) {
    print(STDERR "$trigger_test");
    print($fh "$trigger_test");
  }
close($fh);

print("DONE!\n");
exit(0);
