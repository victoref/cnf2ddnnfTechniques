#!/usr/bin/env python
######################### HEADER ############################
# Author: Víctor Emiliano Fernández Rubio
# TFM project: TÉCNICAS DE PRE-PROCESADO EN SOLUCIONADORES
#              SAT: VIVIFICACIÓN
#############################################################
import os
import numpy as np
import getopt
import sys
import signal
from datetime import datetime

# Constants
CURR_DIR = os.getenv("PWD")
BASE_DIR = os.path.dirname(CURR_DIR)
DATA_DIR = f"{BASE_DIR}/data"
SCRIPT_DIR = f"{BASE_DIR}/scripts"
PROGRAM_DIR = f"{BASE_DIR}/programs"

CADICAL_PATH = f"{PROGRAM_DIR}/SAT_cadical-2.0.0/build/cadical"
PMC_PATH = f"{PROGRAM_DIR}/pmc/pmc"
MAPLE_PATH = f"{PROGRAM_DIR}/Maple+/simp/glucose"
MAPLELRB_PATH = f"{PROGRAM_DIR}/MapleLRB/simp/glucose"
GLUCOSEP_PATH = f"{PROGRAM_DIR}/Glucose+/simp/glucose"
COMSPS_PATH = f"{PROGRAM_DIR}/COMSPS+/simp/glucose"
C2D_PATH = f"{PROGRAM_DIR}/c2d/c2d"
#C2D_PATH = f"{PROGRAM_DIR}/c2d/mc2d"
D4_PATH = f"{PROGRAM_DIR}/d4/d4"

EXAMPLES_PATH = f"{DATA_DIR}/CNF_EXAMPLES"
OUTPUT_PATH = f"{DATA_DIR}/SAT_RESULTS"

# List of available SAT solvers
SOLVERS = {
    1: PMC_PATH,
    2: MAPLE_PATH,
    3: MAPLELRB_PATH,
    4: GLUCOSEP_PATH,
    5: COMSPS_PATH
#    6: C2D_PATH
#    7: D4_PATH
}

def signalHandler(sig, frame):
    print("\n[INFO] EXITING...")
    sys.exit(0)

def checkBASEDIR(path):

    myFolders = os.listdir(path)
    if os.path.basename(path) != "scripts":
        print("[ERROR] Please execute the scripts in its specific folder")
        sys.exit(1)

# Function to get command-line arguments
def getargs(argv):
    """
    Parses command-line arguments to determine debug mode, automatic execution, and vivification option.
    """
    debug = False
    automatic = False
    vivification = False
    try:
        opts, args = getopt.getopt(argv, "hda", ["help", "debug", "automatic"])
    except getopt.GetoptError:
        print("[INFO] Usage: python script.py\n\
                                [-h/--help]\n\
                                [-d/--debug]\n\
                                [-a/--automatic]\n")
        sys.exit(1)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print("[INFO] Usage: python script.py\n\
                                [-h/--help]\n\
                                [-d/--debug]\n\
                                [-a/--automatic]\n")
            sys.exit(0)
        elif opt in ("-d", "--debug"):
            debug = True
        elif opt in ("-a", "--automatic"):
            automatic = True
    return debug, automatic

# Function to verify if the example file exists
def exampleExists(example):
    """
    Checks if the specified example file exists in the examples directory.
    """
    return os.path.isfile(os.path.join(EXAMPLES_PATH, example))

def vivifyCmd(solverPath, example, logFile, varElimination=False):
    """
    Constructs the command to execute a SAT solver based on its path and vivification option.
    Currently, this function is not fully implemented.
    """
    eliminationFlag = ""
    if varElimination:
        eliminationFlag = "-elim"
    else:
        eliminationFlag = "-no-elim"

    cmd = ""
    if os.path.basename(solverPath) == "pmc":
        cmd = f"{solverPath} -verb=1 -vivification {EXAMPLES_PATH}/{example} | tee -a {OUTPUT_PATH}/vivfied_{os.path.basename(solverPath)}_{example}"

    else:
        cmd = f"{solverPath} {eliminationFlag} -pre -verb=2 -dimacs={OUTPUT_PATH}/vivfied_{os.path.basename(solverPath)}_{example} {EXAMPLES_PATH}/{example}"
        cmd += f"grep \"CPU time\" vivfied_{example} | awk '{{print \"Vivify: \" $5}}' > {logFile}"

    return cmd

def cnf2dDNNFCmd(example):
    cmd = f"{C2D_PATH} -in {example} -dt_count 50 -smooth_all -count -cache_size 10 -nnf_block_size 50 | tee -a {OUTPUT_PATH}/c2d_{os.path.basename(example).split('.')[0]}.log"
    return cmd

def modelCountCmd(example):
    cmd = f"{D4_PATH} -mc {example} 2>1 | grep \"^s\" | awk '{{print $2}}'"
    return cmd

# Function to execute SAT solver with a given example
def execute(solverPath, example):
    """
    Executes the specified SAT solver on a given example file and logs the output.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    logFile = f"{OUTPUT_PATH}/{os.path.basename(solverPath)}_{example}_{timestamp}.log"

    #First vivify the cnf with desired mechanism
    command = vivifyCmd(solverPath, f"{example}", logFile)
    os.system(command)

    if os.path.basename(solverPath) == "pmc":
        command = f"grep \"CPU time\" {OUTPUT_PATH}/vivfied_{os.path.basename(solverPath)}_{example} | awk '{{print \"Vivify: \" $5}}' > {logFile}"
        os.system(command)

    #Second convert vivified cnf to dDNNF
    command = cnf2dDNNFCmd(f"{OUTPUT_PATH}/vivfied_{os.path.basename(solverPath)}_{example}")
    os.system(command)

    command = f"grep \"Time\" {OUTPUT_PATH}/c2d_vivfied_{os.path.basename(solverPath)}_{example.split('.')[0]}.log | sed -e 's/s \\/ /\\n/g' -e 's/s$//g' >> {logFile}"
    print(command)
    os.system(command)

    #Third convert original cnf to dDNNF
    #command = cnf2dDNNFCmd(f"{EXAMPLES_PATH}/{example}")
    #os.system(command)

    #command = f"grep \"Time\" {EXAMPLES_PATH}/vivfied_{example}.nnf | sed -e 's/s \/ /\n/g' -e 's/s$//g'" #Need to check EXAMPLES_PATH

# Main function
def main():
    """
    Main function to orchestrate the execution of SAT solvers based on user input or automatic mode.
    """
    signal.signal(signal.SIGINT, signalHandler)
    checkBASEDIR(CURR_DIR)

    # Parse command-line arguments
    debug, automatic = getargs(sys.argv[1:])

    # Create output directory if it does not exist
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    # Automatic mode: execute all examples with all solvers
    if automatic:
        tests = os.listdir(EXAMPLES_PATH)
        tests.sort()
        for s in SOLVERS:
            for t in tests:
                print(f"[INFO] Processing example: {t} SAT: {os.path.basename(SOLVERS[s])}")
                execute(SOLVERS[s], t, debug, vivification)
        print("[INFO] Proccess finished without errors")
        print("[INFO] EXITING...")
    # Manual mode: prompt user for input
    else:
        while True:
            # Display solver options
            print("[INFO] Choose a SAT solver: ")
            print("0 - EXIT")
            for key, value in SOLVERS.items():
                print(f"{key} - {value.split('/')[5]}")

            # Prompt user to choose a solver
            #try:
            solverChoice = int(input("(1-5): "))
            #except:
            #    print("[ERROR] Invalid choice, please try again.")
            #    continue

            if solverChoice == 0:
                print("\n[INFO] EXITING...")
                sys.exit(0)

            if solverChoice not in SOLVERS:
                print("[ERROR] Invalid choice, please try again.")
                continue

            # Prompt user to enter the name of the example file
            example = input("[INFO] Enter the name of the example: ")

            if not exampleExists(example):
                print("[ERROR] Example not found.")
                continue

            # Execute the chosen solver on the specified example
            execute(SOLVERS[solverChoice], example)
            print("[INFO] Proccess finished without errors")


# Entry point of the script
if __name__ == "__main__":
    main()
