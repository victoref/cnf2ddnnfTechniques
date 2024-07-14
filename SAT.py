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
import re

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
TIMEOUT_D4 = 10000

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
                                [-e <example> / --example <example>]")
    print("[INFO] List of solvers [pmc, maple, mapleLRB, glucose+, comsps]")


# Function to get command-line arguments
def getargs(argv):
    """
    Parses command-line arguments to determine debug mode and vivification option.
    """
    solver = ""
    example = ""

    try:
        opts, args = getopt.getopt(argv, "hs:e:", ["help", "solver=", "example="])
    except getopt.GetoptError:
        usage()
        sys.exit(1)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit(0)

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

    if solver == "" and example == "":
        print("[ERROR] Solver and example are mandatory arguments")
        print("[ERROR] EXITING...")
        sys.exit(1)

    return solver, example


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


def compareWorlds(w1, w2, logFile):
    sameWs = False
    if w1 != None and w2 != None:
        if w1 == w2:
            sameWs = True
    with open(logFile, 'a') as f:
        if sameWs:
            f.write("TRUE;")
        else:
            f.write("FALSE;")


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
        os.remove(example)


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
        with open(logFile, "a") as f:
            f.write("TIMEOUT;-;-;-;")


def grepTimeInC2D(output, logFile, deleteFile):
    cmd = f"grep \"Total Time\" {output} | sed -E 's/Total Time: ([^s]+)s/\\1/' |  tr '\n' ';' >> {logFile}"
    os.system(cmd)
    if deleteFile:
        cmd = f"rm -f {output}"
        os.system(cmd)


def cnfCountWorlds(example, logFile):
    d4Cmd = [D4_PATH, '-mc', example]
    worlds = None

    try:
        stepD4 = subprocess.run(d4Cmd, timeout=TIMEOUT_D4, capture_output=True)
        if stepD4.returncode == 0:
            with open(logFile, 'a') as f:
                stdoutD4 = (stepD4.stdout).decode('utf-8')
                worlds = re.search(r's (\d+)', stdoutD4)
                f.write(worlds.group(1) + ";")
    except subprocess.TimeoutExpired:
        with open(logFile, 'a') as f:
            f.write("TIMEOUT;")

    return worlds.group(1)


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

    #SATsolver;Example;Vivification;Backbone;#vars OGCNF;#clau OGCNF;OGCNF worlds;Vivify-Time;#vars VIVCNF;#clau VIVCNF;VIVCNF worlds;Same worlds;OGCNF2dDNNF Time;VIVCNF2dDNNF Time;OGdDNNF worlds;VIVdDNNF worlds;
    #os.system(command)

    with open(logFile, 'a') as f:
        f.write(f"{solverName};{example};TRUE;FALSE;")

    #First extract the number of vars & clauses of the original cnf
    getVarsandClauses(f"{EXAMPLES_PATH}/{example}", logFile)

    #Second count the number of solutions of the original cnf
    OGworlds = cnfCountWorlds(f"{EXAMPLES_PATH}/{example}", logFile)

    #Third vivify the cnf with desired mechanism TODO ADD D4 to vivification process
    vivifyCmd(solverPath, solverName, f"{EXAMPLES_PATH}/{example}", f"{OUTPUT_PATH}/{vivifiedExample}", logFile)
    if os.path.basename(solverPath) == "pmc":
        grepTimeInVivification(f"{OUTPUT_PATH}/{vivifiedExample}", logFile, False)
    else:
        grepTimeInVivification(f"{OUTPUT_PATH}/{vivifiedExample}_aux.log", logFile, True)

    #Fourth extract the number of vars & clauses of the vivified cnf
    getVarsandClauses(f"{OUTPUT_PATH}/{vivifiedExample}", logFile)

    #Fifth count the number of solutions of the vivified cnf
    VIVworlds = cnfCountWorlds(f"{OUTPUT_PATH}/{vivifiedExample}", logFile)

    #Sixth same solutions OG CNF - VIV CNF
    compareWorlds(OGworlds, VIVworlds, logFile)

    #Seventh convert original cnf to dDNNF TODO CAN BE DONE EVEN WITH D4
    cnf2dDNNFCmd(example, False, logFile, solverName)
    grepTimeInC2D(f"{OUTPUT_PATH}/c2d_{solverName}_{PID}_{example}.log", logFile, True)

    #Eighth convert vivified cnf to dDNNF TODO CAN BE DONE EVEN WITH D4
    cnf2dDNNFCmd(f"{vivifiedExample}", True, logFile)
    grepTimeInC2D(f"{OUTPUT_PATH}/c2d_{vivifiedExample}.log", logFile, True)

    #Ninth move original.nnf to result folder
    os.replace(f"mv {EXAMPLES_PATH}/{example}.nnf", f"{OUTPUT_PATH}/{PID}_{example}.nnf")

    #TODO Tenth count OG dDNNF - VIV dDNNF
    #ddnnfCountCmd()
    #ddnnfCountCmd()

    with open(logFile, 'a') as f:
        f.write("\n")


# Main function
def main():
    """
    Main function to orchestrate the execution of SAT solvers based on user input.
    """
    signal.signal(signal.SIGINT, signalHandler)
    checkBASEDIR(CURR_DIR)

    solverChoice = ""
    example = ""

    # Parse command-line arguments
    solverChoice, example = getargs(sys.argv[1:])

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

    # Execute the chosen solver on the specified example
    print(f"[INFO] Processing example {example} with solver {solverChoice}")
    print()
    execute(SOLVERS[solverChoice], example)
    print("[INFO] Process finished without errors")


# Entry point of the script
if __name__ == "__main__":
    main()
