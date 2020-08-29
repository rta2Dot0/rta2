#!/usr/bin/env bash

REPAIR_THEM_ALL_FRAMEWORK_DIR=`pwd`

# Remove any existing data and create required directories
mvn_deps_dir="$REPAIR_THEM_ALL_FRAMEWORK_DIR/mvn_deps"
rm -rf "$mvn_deps_dir"; mkdir -p "$mvn_deps_dir"
mvn_deps_sym_dir="$REPAIR_THEM_ALL_FRAMEWORK_DIR/mvn_deps_sym"
rm -rf "$mvn_deps_sym_dir"; mkdir -p "$mvn_deps_sym_dir"

mvn_deps_zip="$REPAIR_THEM_ALL_FRAMEWORK_DIR/mvn_deps.zip"

# Try to get a cached version of all maven dependencies
GDRIVE_FILE_ID="1sa6qqiIp_xTqKsyQjHHFP3DkARNRZb91"
GDRIVE_FILE_URL="https://drive.google.com/uc?export=download&id=$GDRIVE_FILE_ID"
wget --load-cookies /tmp/cookies.txt \
  "https://drive.google.com/uc?export=download&confirm=$(wget --quiet \
    --save-cookies /tmp/cookies.txt \
    --keep-session-cookies \
    --no-check-certificate "$GDRIVE_FILE_URL" -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=$GDRIVE_FILE_ID" -O "$mvn_deps_zip"
rm -f /tmp/cookies.txt

#
# If there a zip file with all maven dependencies, extract it and set the symlinks
#
if [ -s "$mvn_deps_zip" ]; then
  echo "Unzipping $mvn_deps_zip"
  unzip -u "$mvn_deps_zip"

#
# Otherwise, collect and cache all mvn dependencies
#
else
  # Build the project-info-maven-plugin (with Java-8) and install it in the local
  # mvn_deps repository
  echo "Building project-info-maven-plugin"
  git clone https://github.com/tdurieux/project-info-maven-plugin
  cd project-info-maven-plugin
  export JAVA_HOME="$REPAIR_THEM_ALL_FRAMEWORK_DIR/jdks/jdk1.8.0_181" && mvn -DskipTests -Dmaven.repo.local="$mvn_deps_dir/plugin" install
  if [ "$?" -ne "0" ]; then
    echo "Failed to build the project-info-maven-plugin project and install it in $mvn_deps_dir/plugin!"
    exit 1
  fi
  export JAVA_HOME="$REPAIR_THEM_ALL_FRAMEWORK_DIR/jdks/jdk1.8.0_181" && mvn -DskipTests install
  if [ "$?" -ne "0" ]; then
    echo "Failed to build the project-info-maven-plugin project and install it in ~/.m2/!"
    exit 1
  fi
  cd ..
  rm -rf project-info-maven-plugin

  echo "Collecting and caching all mvn dependencies"

  # Each project/bug may need the project-info-maven-plugin in the mvn_deps_sym
  # directory to get project info, e.g., path to the source directory
  mkdir -p "$mvn_deps_sym_dir/plugin"
  cp -R $mvn_deps_dir/plugin/* "$mvn_deps_sym_dir/plugin/"

  bugs_file="$REPAIR_THEM_ALL_FRAMEWORK_DIR/benchmarks/bugs.csv"
  if [ ! -s "$bugs_file" ]; then
    echo "$bugs_file does not exist or it is empty!"
    exit 1
  fi

  # Get maven .m2 per benchmark/project
  while read -r entry; do

    benchmark=$(echo "$entry" | cut -f1 -d',')
      project=$(echo "$entry" | cut -f2 -d',')
          bug=$(echo "$entry" | cut -f3 -d',')

    if [ "$benchmark" == "Defects4J" ] || [ "$benchmark" == "IntroClassJava" ] || [ "$benchmark" == "QuixBugs" ]; then
      continue
    fi
    # For only Bears and BugsDotJar

    echo "Downloading mvn dependencies of $benchmark :: $project :: $bug"

    mtwo_dir="$mvn_deps_dir/$project"
    mkdir -p "$mtwo_dir"

    export PYTHONPATH="$REPAIR_THEM_ALL_FRAMEWORK_DIR/script:$PYTHONPATH" && \
    python "$REPAIR_THEM_ALL_FRAMEWORK_DIR/get-mvn-deps.py" \
      --benchmark "$benchmark" \
      --project "$project" \
      --bug "$bug" \
      --mtwo_dir "$mtwo_dir"
    if [ "$?" -ne "0" ]; then
      echo "get-mvn-deps.py has failed!"
      exit 1
    fi

  done < <(tail -n +2 "$bugs_file")

  # Create a master zip file with all maven dependencies
  zip -r "$mvn_deps_zip" mvn_deps/*
  if [ "$?" -ne "0" ]; then
    echo "Failed to zip the mvn_deps dir!"
    exit 1
  fi
fi

#
# Setting up symlinks
#

# echo "Setting up symlinks"
# rm -rf "$mvn_deps_sym_dir"; mkdir -p "$mvn_deps_sym_dir" # from scratch
# # Copy over the directory structure, with symlinks to all (leaf) files.
# cp -as $mvn_deps_dir/* mvn_deps_sym
# # Remove all files that might change
# find mvn_deps_sym -type l -regextype posix-egrep ! -regex ".*\.jar(\.sha1)?$|.*\.pom(\.sha1)?$" -exec rm {} +
# # Copy all remaining files
# echo "Setting up hard links"
# rsync -a --exclude "*.jar" --exclude "*.jar.sha1" --exclude "*.pom" --exclude "*.pom.sha1" mvn_deps/ mvn_deps_sym/
# # Change permissions of all files in mvn_deps to read-only
# echo "Making all mvn_deps files read-only"
# find mvn_deps -type f -exec chmod -w {} +

#
# Install junit-4.11.jar and hamcrest-core-1.3.jar in the local m2 (e.g., ~/.m2)
# as IntroClassJava and QuixBugs benchmarks are expecting to find those
# dependencies exactly in that location.
#

export JAVA_HOME="$REPAIR_THEM_ALL_FRAMEWORK_DIR/jdks/jdk1.8.0_181" && mvn \
  install:install-file -Dfile="$REPAIR_THEM_ALL_FRAMEWORK_DIR/libs/arja_external/lib/junit-4.11.jar" \
  -DgroupId="junit" -DartifactId="junit" -Dversion="4.11" -Dpackaging="jar"
if [ "$?" -ne "0" ]; then
  echo "Failed to install junit-4.11 in ~/.m2/!"
  exit 1
fi
if [ -s "~/.m2/repository/junit/junit/4.11/junit-4.11.jar" ]; then
  echo "There is no ~/.m2/repository/junit/junit/4.11/junit-4.11.jar file!"
  exit 1
fi

export JAVA_HOME="$REPAIR_THEM_ALL_FRAMEWORK_DIR/jdks/jdk1.8.0_181" && mvn \
  install:install-file -Dfile="$REPAIR_THEM_ALL_FRAMEWORK_DIR/libs/arja_external/lib/hamcrest-core-1.3.jar" \
  -DgroupId="org.hamcrest" -DartifactId="hamcrest-core" -Dversion="1.3" -Dpackaging="jar"
if [ "$?" -ne "0" ]; then
  echo "Failed to install hamcrest-core-1.3 in ~/.m2/!"
  exit 1
fi
if [ -s "~/.m2/repository/org/hamcrest/hamcrest-core/1.3/hamcrest-core-1.3.jar" ]; then
  echo "There is no ~/.m2/repository/org/hamcrest/hamcrest-core/1.3/hamcrest-core-1.3.jar file!"
  exit 1
fi
