import os
from os.path import expanduser
from core.Support import getGridTime

REPAIR_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_PATH = os.path.join(REPAIR_ROOT, "data")
REPAIR_TOOL_FOLDER = os.path.join(REPAIR_ROOT, "repair_tools")
WORKING_DIRECTORY = os.path.join("/tmp/")
OUTPUT_PATH = os.path.join(REPAIR_ROOT, "results/")

Z3_PATH = os.path.join(REPAIR_ROOT, "libs", "z3", "build")
D4J_HOME = os.path.join(REPAIR_ROOT, "benchmarks", "defects4j")

BENCHMARK_METADATA_DIR         = os.path.join(DATA_PATH, "benchmarks-metadata")
BENCHMARKS_REPRODUCIBILITY_DIR = os.path.join(DATA_PATH, "benchmarks-reproducibility")

JAVA7_HOME = os.path.join(REPAIR_ROOT, "jdks", "jdk1.7.0_80")
JAVA8_HOME = os.path.join(REPAIR_ROOT, "jdks", "jdk1.8.0_181")
JAVA_ARGS = "-Xmx32g -Xms1g"
JAVA_VERSION = os.environ.get('JAVA_VERSION', '8')

LOCAL_THREAD = 1
GRID5K_MAX_NODE = 50
##In minutes
TOOL_TIMEOUT = "60"
TEST_TIMEOUT = "480m" # 8 hours
#Format: HH:MM ## the fuction getGridTime calculates the timeout of the grid taking into account an overhead (expressed as percentage)
GRID5K_TIME_OUT = getGridTime(TOOL_TIMEOUT, overhead=0.33)
