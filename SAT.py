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
D4_PATH = f"{PROGRAM_DIR}/d4/d4"
dREASONER_PATH = f"{PROGRAM_DIR}/dDNNFreasoner/query-dnnf"

EXAMPLES_PATH = f"{DATA_DIR}/CNF_EXAMPLES"
OUTPUT_PATH = f"{DATA_DIR}/SAT_RESULTS"

# List of available SAT solvers
SOLVERS = {
    1: PMC_PATH,
    2: MAPLE_PATH,
    3: MAPLELRB_PATH,
    4: GLUCOSEP_PATH,
    5: COMSPS_PATH
}

PID=os.getpid()


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


def vivifyCmd(solverPath, solverName, example, logFile, varElimination=False):
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
        cmd = f"{solverPath} -verb=1 -vivification {EXAMPLES_PATH}/{example} | tee -a {OUTPUT_PATH}/vivified_{solverName}_{example}"

    else:
        cmd = f"{solverPath} {eliminationFlag} -pre -verb=2 -dimacs={OUTPUT_PATH}/vivified_{solverName}_{example} {EXAMPLES_PATH}/{example}"
        cmd += f"| grep \"CPU time\" | awk '{{print \"Vivify: \" $5}}' > {logFile}"
        #cmd += f"; grep \"CPU time\" {OUTPUT_PATH}/vivified_{solverName}_{example} | awk '{{print \"Vivify: \" $5}}' > {logFile}"
    os.system(cmd)


def cnf2dDNNFCmd(example, vivified, solverName=""):
    if vivified:
        cmd = f"{C2D_PATH} -in {example} -dt_count 50 -smooth_all -count -cache_size 10 -nnf_block_size 50 | tee -a {OUTPUT_PATH}/c2d_{os.path.basename(example).split('.')[0]}.log"
    else:
        cmd = f"{C2D_PATH} -in {example} -dt_count 50 -smooth_all -count -cache_size 10 -nnf_block_size 50 | tee -a {OUTPUT_PATH}/c2d_{solverName}_{os.path.basename(example).split('.')[0]}.log"
    os.system(cmd)


def grepTimeInOutput(output, logFile):
    cmd = f"grep \"Time\" {output} | sed -e 's/s \\/ /\\n/g' -e 's/s$//g' >> {logFile}"
    os.system(cmd)


def cnfCountCmd(example, logFile):
    cmd = f"{D4_PATH} -mc {example} 2>&1 | grep \"^s\" | awk '{{print \"CNF worlds: \" $2}}' >> {logFile}"
    os.system(cmd)


def ddnnfCountCmd(example, logFile):
    cmd = f"{dREASONER_PATH} | awk '{{print \"dDNNF worlds: \" $2}}' >> {logFile}"
    os.system(cmd)


# Function to execute SAT solver with a given example
def execute(solverPath, example):
    """
    Executes the specified SAT solver on a given example file and logs the output.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    solverName = solverPath.split('/')[5]
    logFile = f"{OUTPUT_PATH}/{solverName}_{example}_{timestamp}.log"

    #First vivify the cnf with desired mechanism
    vivifyCmd(solverPath, solverName, f"{example}", logFile)

    if os.path.basename(solverPath) == "pmc":
        command = f"grep \"CPU time\" {OUTPUT_PATH}/vivified_{solverName}_{example} | awk '{{print \"Vivify: \" $5}}' > {logFile}"
        os.system(command)

    #Second count the number of solutions of the original cnf
    cnfCountCmd(f"{EXAMPLES_PATH}/{example}", logFile)

    #Third count the number of solutions of the vivified cnf
    cnfCountCmd(f"{OUTPUT_PATH}/vivified_{solverName}_{example}", logFile)

    #Fourth convert vivified cnf to dDNNF
    cnf2dDNNFCmd(f"{OUTPUT_PATH}/vivified_{solverName}_{example}", True)
    grepTimeInOutput(f"{OUTPUT_PATH}/c2d_vivified_{solverName}_{example.split('.')[0]}.log", logFile)

    #Fifth convert original cnf to dDNNF
    cnf2dDNNFCmd(f"{EXAMPLES_PATH}/{example}", False, solverName)
    grepTimeInOutput(f"{OUTPUT_PATH}/c2d_{solverName}_{example.split('.')[0]}.log", logFile)

    #Sixth move original.nnf to result folder
    command = f"mv {EXAMPLES_PATH}/{example}.nnf {OUTPUT_PATH}/"
    os.system(command)

    #Seventh extract metrics like smallest ddnnf, time, memory ...
    #The another script, here it only saves the results in a format csv, log, ...


# Main function
def main():
    """
    Main function to orchestrate the execution of SAT solvers based on user input or automatic mode.
    """
    signal.signal(signal.SIGINT, signalHandler)
    checkBASEDIR(CURR_DIR)

    solverChoice = ""
    example = ""
    debug = False
    automatic = False

    # Parse command-line arguments
    if len(sys.argv) == 3:
        solverChoice = int(sys.argv[1])
        example = str(sys.argv[2])
    else:
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
    # Manual mode: Use args or ask user for input
    else:
        if len(sys.argv) == 3:
            if solverChoice not in SOLVERS:
                print("[ERROR] Invalid choice.")
                print("[ERROR] EXITING...")
                sys.exit(1)
            if not exampleExists(example):
                print("[ERROR] Example not found.")
                print("[ERROR] EXITING...")
                sys.exit(1)
            execute(SOLVERS[solverChoice], example)
            print("[INFO] Proccess finished without errors")
            print("[INFO] EXITING...")
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
