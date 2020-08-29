#!/usr/bin/env bash

# Get Java-7 and Java-8
rm -rf jdks
mkdir jdks
cd jdks
  wget https://github.com/frekele/oracle-java/releases/download/8u181-b13/jdk-8u181-linux-x64.tar.gz
  tar -xvzf jdk-8u181-linux-x64.tar.gz
  wget https://github.com/frekele/oracle-java/releases/download/7u80-b15/jdk-7u80-linux-x64.tar.gz
  tar -xvzf jdk-7u80-linux-x64.tar.gz

  JDKS_DIR=`pwd`
  for jdk in "jdk1.7.0_80" "jdk1.8.0_181"; do
    for bin_dir in "$jdk/bin" "$jdk/jre/bin"; do
      # Copy java wrapper script
      cp -v "$JDKS_DIR/../script/java_wrapper.pl" "$JDKS_DIR/$bin_dir/java_wrapper.pl"
      chmod +x "$JDKS_DIR/$bin_dir/java_wrapper.pl"
      # Wrap java command
      mv "$JDKS_DIR/$bin_dir/java" "$JDKS_DIR/$bin_dir/java_exec"
      ln -s "$JDKS_DIR/$bin_dir/java_wrapper.pl" "$JDKS_DIR/$bin_dir/java"
      # Sanity check
      "$JDKS_DIR/$bin_dir/java" -version
    done
  done
cd ..
