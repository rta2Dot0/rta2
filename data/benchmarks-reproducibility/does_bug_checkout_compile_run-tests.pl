#!/usr/bin/env perl
# ------------------------------------------------------------------------------
# This script determines whether the checkout, compile, metadata, and run tests
# procedures execute successfully on a specific version, either buggy and fixed.
# The script exits with 0 if the checkout, compile and run tests procedures
# executed successfully, 1 otherwise.
#
# Usage:
# ./does_bug_checkout_compile_metadata_run-tests.pl
#   <status.csv>
#
# ------------------------------------------------------------------------------

use strict;
use warnings;

$#ARGV == 0 or die("Usage: does_bug_checkout_compile_metadata_run-tests.pl <status.csv>");

# Inputs
my $STATUS_CSV_FILE = $ARGV[0];
-e $STATUS_CSV_FILE or die("$STATUS_CSV_FILE does not exist!");

#
# Check whether checkouts, compiles, and runs the test cases successfully.
#
# Note: A bug can only be reproducible if and only if it checkout, compile, and
# run test cases successfully.
#

my $status_data = `tail -n1 $STATUS_CSV_FILE`;
# benchmark,project,bug,java_version,exclude_broken_tests,buggy_version,checkout,compile,metadata,test,num_all_tests,num_failing_tests
$status_data =~ /(true|false),(true|false),(\d+|NA),(\d+|NA),(\d+|NA),(\d+|NA),(\d+|NA),(\d+|NA)$/ or die("data row of $STATUS_CSV_FILE is incorrectly formatted!");
my $checkout          = $3;
my $compile           = $4;
my $metadata          = $5;
my $test              = $6;
my $num_all_tests     = $7;

if ( ($checkout eq "NA") || ($checkout eq "0") ) {
  print(STDERR "Checkout procedure failed\n");
  exit(1);
}

if ( ($compile eq "NA") || ($compile eq "0") ) {
  print(STDERR "Compile procedure failed\n");
  exit(1);
}

if ( ($metadata eq "NA") || ($metadata eq "0") ) {
  print(STDERR "Metadata procedure failed\n");
  exit(1);
}

if ( ($test eq "NA") || ($test eq "0") ) {
  print(STDERR "Test procedure failed\n");
  exit(1);
}

if ( ($num_all_tests eq "NA") || ($num_all_tests eq "0") ) {
  print(STDERR "No test case was executed\n");
  exit(1);
}

print("OK!\n");
exit(0);
