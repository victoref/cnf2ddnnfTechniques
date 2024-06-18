#!/usr/bin/env python
######################### HEADER ############################
# Author: Víctor Emiliano Fernández Rubio
# TFM project: PRE-PROCESSING TECHNIQUES IN SAT SOLVERS: VIVIFICATION
#############################################################
import os
import sys
import signal
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Constants for SAT solvers
SOLVERS = ["Minisat-2.2.0", "Glucose-4.2.1", "Lingeling-1.0.0", "Cadical-2.0.0"]

# Directory paths
CURR_DIR = os.getenv("PWD")
BASE_DIR = os.path.dirname(CURR_DIR)
DATA_DIR = f"{BASE_DIR}/data"
#SCRIPT_DIR = f"{BASE_DIR}/scripts"
#PROGRAM_DIR = f"{BASE_DIR}/programs"

# Paths for examples and results
EXAMPLES_PATH = f"{DATA_DIR}/CNF_EXAMPLES"
OUTPUT_PATH = f"{DATA_DIR}/SAT_RESULTS"

# Patterns to identify satisfiability in output
SAT_PATTERN = 'SATISFIABLE'
UNSAT_PATTERN = 'UNSATISFIABLE'

# Grep expressions for different solvers
GREP_EXP_MINISAT = "CPU time"
GREP_EXP_GLUCOSE = "CPU time"
GREP_EXP_LINGELING = "% all"
GREP_EXP_CADICAL = "real time since initialization: "

# Sed suffix for extracting numeric values
SED_SUFFIX = 'sed -E \'s/.* ([0-9.]+) .*/\1/\''

# Signal handler for clean exit
def signalHandler(sig, frame):
    print("\n[INFO] EXITING...")
    sys.exit(0)

# Function to check if BASE_DIR contains required folders
def checkBASEDIR(path):
    myFolders = os.listdir(path)
    if not "data" in myFolders or not "scripts" in myFolders or not "programs" in myFolders:
        print("[ERROR] Please execute the scripts in its specific folder")
        sys.exit(1)

# Function to read data from results and examples
def readData():
    solver = []
    test = []
    time = []
    satisfiable = []

    TESTS = os.listdir(EXAMPLES_PATH)
    TESTS.sort()  # Sort tests for consistent ordering

    RESULTS = os.listdir(OUTPUT_PATH)
    RESULTS.sort()  # Sort results for consistent ordering

    # Populate solver and test lists
    for s in SOLVERS:
        for t in TESTS:
            solver.append(s)
            test.append(t)

    # Read each result file and extract relevant information
    for r in RESULTS:  # This can be done more robustly
        f = open(os.path.join(OUTPUT_PATH, r), 'r')
        init = ""
        end = ""
        for line in f:
            if "INIT" in line:
                init = float(line.split()[-1])
            elif "END" in line:
                end = float(line.split()[-1])
            elif UNSAT_PATTERN in line:
                satisfiable.append(False)
            elif SAT_PATTERN in line:
                satisfiable.append(True)
        f.close()
        time.append(end - init)

    # Create a dictionary with the data
    data = {
        'Solver': solver,
        'Test': test,
        'Time': time,
        'Satisfiable': satisfiable
    }

    return data

# Function to plot execution time for each test and solver
def plotExampleTime(df):
    # Create a base scatter plot using seaborn
    plt.figure(figsize=(14, 8))
    markers = {True: "o", False: "X"}  # Markers for satisfiability
    sns.scatterplot(x='Test', y='Time', hue='Solver', style=df['Satisfiable'], data=df, palette='muted', markers=markers)
    # Add title and labels
    plt.title('Execution Time per Test for Each Solver with Satisfiability Indicator')
    plt.xlabel('Test')
    plt.xticks(rotation=45)
    plt.ylabel('Time (s)')
    plt.legend(loc='center', bbox_to_anchor=(-0.08, 1))
    plt.grid(True)

    # Display the plot
    plt.show()

# Function to calculate median execution time per solver
def calculateMedianTime(df):
    medianTimes = df.groupby('Solver')['Time'].median().reset_index()
    medianTimes.columns = ['Solver', 'MedianTime']
    return medianTimes

# Function to plot median execution time per solver
def plotMedian(medianTimes):
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Solver', y='MedianTime', data=medianTimes, hue='Solver', palette='muted')
    plt.title('Median Execution Time per Solver')
    plt.xlabel('Solver')
    plt.ylabel('Median Time (s)')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.show()

# Main function
def main():
    signal.signal(signal.SIGINT, signalHandler)
    checkBASEDIR(BASE_DIR)

    data = readData()
    df = pd.DataFrame(data)

    plotExampleTime(df)

    plotMedian(calculateMedianTime(df))

# Entry point of the script
if __name__ == "__main__":
    main()
