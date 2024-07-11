#!/usr/bin/env python
######################### HEADER ############################
# Author: Víctor Emiliano Fernández Rubio
# TFM project: TÉCNICAS DE PRE-PROCESADO EN SOLUCIONADORES
#              SAT: VIVIFICACIÓN
#############################################################
import os
import getopt
import sys
import signal
import subprocess
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
MAPLELRB_PATH = f"{PROGRAM_DIR}/MapleLRB+/simp/glucose"
GLUCOSEP_PATH = f"{PROGRAM_DIR}/Glucose+/simp/glucose"
COMSPS_PATH = f"{PROGRAM_DIR}/COMSPS+/simp/glucose"
C2D_PATH = f"{PROGRAM_DIR}/c2d/c2d"
D4_PATH = f"{PROGRAM_DIR}/d4/d4"
dREASONER_PATH = f"{PROGRAM_DIR}/dDNNFreasoner/query-dnnf"

EXAMPLES_PATH = f"{DATA_DIR}/CNF_EXAMPLES"
OUTPUT_PATH = f"{DATA_DIR}/SAT_RESULTS"

# List of available SAT solvers
SOLVERS = {
    "pmc": PMC_PATH,
    "maple": MAPLE_PATH,
    "mapleLRB": MAPLELRB_PATH,
    "glucose+": GLUCOSEP_PATH,
    "comsps": COMSPS_PATH
}

PID=os.getpid()

TIMEOUT_C2D = 1200

def signalHandler(sig, frame):
    print("\n[INFO] EXITING...")
    sys.exit(0)


def checkBASEDIR(path):
    if os.path.basename(path) != "scripts":
        print("[ERROR] Please execute the scripts in its specific folder")
        sys.exit(1)


def usage():
    print("[INFO] Usage: python script.py\n\
                                [-h / --help]\n\
                                [-s <solver> / --solver <solver>]\n\
                                [-e <example> / --example <example>]\n\
                                [-a / --automatic]")
    print("[INFO] List of solvers [pmc, maple, mapleLRB, glucose+, comsps]")


# Function to get command-line arguments
def getargs(argv):
    """
    Parses command-line arguments to determine debug mode, automatic execution, and vivification option.
    """
    solver = ""
    example = ""
    automatic = False

    try:
        opts, args = getopt.getopt(argv, "hs:e:a", ["help", "solver=", "example=", "automatic"])
    except getopt.GetoptError:
        usage()
        sys.exit(1)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit(0)

        elif opt in ("-a", "--automatic"):
            automatic = True

        elif opt in ("-s", "--solver"):
            if "pmc" == arg:
                solver = "pmc"
            elif "maple" == arg:
                solver = "maple"
            elif "mapleLRB" == arg:
                solver = "mapleLRB"
            elif "glucose+" == arg:
                solver = "glucose+"
            elif "comsps" == arg:
                solver = "comsps"

        elif opt in ("-e", "--example"):
            example = arg

    if solver == "" and example == "" and automatic == False:
        print("[ERROR] Solver and example are mandatory arguments")
        print("[ERROR] EXITING...")
        sys.exit(1)

    return solver, example, automatic


# Function to verify if the example file exists
def exampleExists(example):
    """
    Checks if the specified example file exists in the examples directory.
    """
    return os.path.isfile(os.path.join(EXAMPLES_PATH, example))


def getVarsandClauses(example, logFile):
    numVars = 0
    numClauses = 0
    with open(example, 'r') as f:
        for l in f:
            if l.startswith('p cnf'):
                parts = l.split()
                numVars = int(parts[2])
                numClauses = int(parts[3])

    with open(logFile, 'a') as f:
                f.write(f"{numVars};{numClauses};")

    return numVars, numClauses

def vivifyCmd(solverPath, solverName, example, vivifiedExample, logFile, varElimination=False):
    """
    Constructs the command to execute a SAT solver based on its path and vivification option.
    Currently, this function is not fully implemented.
    """
    eliminationFlag = "-no-elim"
    if varElimination:
        eliminationFlag = "-elim"

    cmd = ""
    if solverName == "pmc":
        cmd = f"{solverPath} -verb=1 -vivification {example} | tee -a {vivifiedExample}"

    else:
        cmd = f"{solverPath} {eliminationFlag} -pre -verb=2 -dimacs={vivifiedExample} {example}  | tee -a {vivifiedExample}_aux.log"
    os.system(cmd)


def grepTimeInVivification(example, logFile, deleteFile):
    command = f"grep \"CPU time\" {example} | awk '{{print $5}}' | tr '\n' ';' >> {logFile}"
    os.system(command)

    if deleteFile:
        command = f"rm -f {example}"
        os.system(command)


def cnf2dDNNFCmd(example, vivified, logFile, solverName=""):
    try:
        inArg = ""
        outputArg = ""
        if vivified:
            inArg = f"{OUTPUT_PATH}/{example}"
            outputArg = f"{OUTPUT_PATH}/c2d_{example}.log"
        else:
            inArg = f"{EXAMPLES_PATH}/{example}"
            outputArg = f"{OUTPUT_PATH}/c2d_{solverName}_{PID}_{example}.log"

        cmd = [
            C2D_PATH,
            "-in", inArg,
            "-dt_count", "50",
            "-smooth_all",
            "-count",
            "-cache_size", "10",
            "-nnf_block_size", "50"
        ]
        with open(outputArg, "a") as sOutFile:
            subprocess.run(cmd, stdout=sOutFile, timeout=TIMEOUT_C2D)
    except subprocess.TimeoutExpired:
        command = f"echo \"TIMEOUT;-;-;-\" | tr '\n' ';' >> {logFile}"
        os.system(command)


def grepTimeInC2D(output, logFile, deleteFile):
    cmd = f"grep \"Total Time\" {output} | sed -E 's/Total Time: ([^s]+)s/\\1/' |  tr '\n' ';' >> {logFile}"
    os.system(cmd)
    if deleteFile:
        cmd = f"rm -f {output}"
        os.system(cmd)


def cnfCountCmd(example, logFile):
    cmd = f"{D4_PATH} -mc {example} 2>&1 | grep \"^s\" | sed -e 's/^s //g' | tr '\n' ';' >> {logFile}"
    os.system(cmd)


def ddnnfCountCmd(example, logFile):
    cmd = f"{dREASONER_PATH} |  tr '\n' ';' >> {logFile}"
    os.system(cmd)


# Function to execute SAT solver with a given example
def execute(solverPath, example):
    """
    Executes the specified SAT solver on a given example file and logs the output.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    pSplited = solverPath.split('/')
    index = pSplited.index("programs")
    solverName = pSplited[(index + 1)]

    logFile = f"{OUTPUT_PATH}/{solverName}_{PID}_{example}_{timestamp}.log"

    vivifiedExample = f"vivified_{solverName}_{PID}_{example}"

    #SATsolver;Example;Vivification;Backbone;#vars OGCNF;#clau OGCNF;OGCNF worlds;Vivify-Time;#vars VIVCNF;#clau VIVCNF;VIVCNF worlds;Same worlds;CNF2dDNNF Time;VivCNF2dDNNF Time;OGdDNNF worlds;VIVdDNNF worlds;
    #os.system(command)

    command = f"echo \"{solverName};{example};TRUE;FALSE\" | tr '\n' ';' > {logFile}"
    os.system(command)

    #First extract the numbaer of vars & clauses of the original cnf
    getVarsandClauses(f"{EXAMPLES_PATH}/{example}", logFile)

    #Second count the number of solutions of the original cnf
    cnfCountCmd(f"{EXAMPLES_PATH}/{example}", logFile)

    #Third vivify the cnf with desired mechanism
    vivifyCmd(solverPath, solverName, f"{EXAMPLES_PATH}/{example}", f"{OUTPUT_PATH}/{vivifiedExample}", logFile)
    if os.path.basename(solverPath) == "pmc":
        grepTimeInVivification(f"{OUTPUT_PATH}/{vivifiedExample}", logFile, False)
    else:
        grepTimeInVivification(f"{OUTPUT_PATH}/{vivifiedExample}_aux.log", logFile, True)

    #Fourth count the number of solutions of the vivified cnf
    getVarsandClauses(f"{OUTPUT_PATH}/{vivifiedExample}", logFile)

    #Fifth count the number of solutions of the vivified cnf
    cnfCountCmd(f"{OUTPUT_PATH}/{vivifiedExample}", logFile)

    #Sixth convert vivified cnf to dDNNF
    cnf2dDNNFCmd(f"{vivifiedExample}", True, logFile)
    grepTimeInC2D(f"{OUTPUT_PATH}/c2d_{vivifiedExample}.log", logFile, True)

    #TODO Same solutions OG CNF - VIV CNF

    #Seventh convert original cnf to dDNNF
    cnf2dDNNFCmd(example, False, logFile, solverName)
    grepTimeInC2D(f"{OUTPUT_PATH}/c2d_{solverName}_{PID}_{example}.log", logFile, True)

    #Eighth move original.nnf to result folder
    command = f"mv {EXAMPLES_PATH}/{example}.nnf {OUTPUT_PATH}/{PID}_{example}.nnf"
    os.system(command)

    #TODO Ninth count OG dDNNF - VIV dDNNF
    #ddnnfCountCmd()
    #ddnnfCountCmd()

    command = f"echo \"\" >> {logFile}"
    os.system(command)


# Main function
def main():
    """
    Main function to orchestrate the execution of SAT solvers based on user input or automatic mode.
    """
    signal.signal(signal.SIGINT, signalHandler)
    checkBASEDIR(CURR_DIR)

    solverChoice = ""
    example = ""
    automatic = False

    # Parse command-line arguments
    solverChoice, example, automatic = getargs(sys.argv[1:])

    if solverChoice not in SOLVERS:
        print("[ERROR] Provide correct solver")
        print("[ERROR] EXITING...")
        sys.exit(1)

    if not exampleExists(example):
        print("[ERROR] Example not found")
        print("[ERROR] EXITING...")
        sys.exit(1)

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
                execute(SOLVERS[s], t)
        print("[INFO] Process finished without errors")
        print("[INFO] EXITING...")
    # Manual mode
    else:
        # Execute the chosen solver on the specified example
        print(f"[INFO] Processing example {example} with solver {solverChoice}")
        print()
        execute(SOLVERS[solverChoice], example)
        print("[INFO] Process finished without errors")


# Entry point of the script
if __name__ == "__main__":
    main()
