#!/usr/bin/env perl
# ------------------------------------------------------------------------------
#
# This script collects the list of trigger test cases originally reported by the
# benchmark metadata for a given bug and prints the name of each test to the
# provided output file. The name of a trigger test case follows the following
# format:
#   --- <test class name>[::<test method name>]
# E.g.,
#   --- org.foo.TestFoo::testBar
#
# Usage:
# ./get_trigger_tests.pl
#   <Bears json file>
#   <output file, e.g., trigger_tests.txt>
#
# ------------------------------------------------------------------------------

use strict;
use warnings;

use JSON::MaybeXS qw(decode_json);

$#ARGV == 1 or die("Usage: get_trigger_tests.pl <Bears json file> <output file, e.g., trigger_tests.txt>");

# Inputs
my $JSON_FILE          = $ARGV[0];
# Output
my $TRIGGER_TESTS_FILE = $ARGV[1];

-e $JSON_FILE or die("$JSON_FILE does not exist!");

#
# Parse json file
#

open(IN, "<$JSON_FILE") or die("Cannot read $JSON_FILE!");
  my @json_input = <IN>;
close(IN);

my $data = decode_json(join('', @json_input));
my $failureDetails = $data->{tests}->{failureDetails};

# Print list of trigger tests to the output file
open(my $fh, ">$TRIGGER_TESTS_FILE") or die("Could not open $TRIGGER_TESTS_FILE to write the list of trigger tests!");
foreach my $failureDetail (@{$failureDetails}) {
  my $trigger_test = $failureDetail->{testClass} . "::" . $failureDetail->{testMethod};
  print $fh "--- $trigger_test\n";
}
close($fh);
