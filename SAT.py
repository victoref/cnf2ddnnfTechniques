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
BACKBONE_PATH = f"{PROGRAM_DIR}/rubenBackbone/backbone.sh"

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

PID = os.getpid()

TIMEOUT_C2D = 1200
TIMEOUT_D4 = 2400

# Signal handler for clean exit
def signalHandler(sig, frame):
    print("\n[INFO] EXITING...")
    sys.exit(0)

# Function to check if the script is being executed in the correct directory
def checkBASEDIR(path):
    if os.path.basename(path) != "scripts":
        print("[ERROR] Please execute the scripts in its specific folder")
        sys.exit(1)

# Function to verify if the specified example file exists in the examples directory
def exampleExists(example):
    return os.path.isfile(os.path.join(EXAMPLES_PATH, example))

# Function to display usage information
def usage():
    print("[INFO] Usage: python script.py\n\
                                [-h / --help]\n\
                                [-s <solver> / --solver <solver>]\n\
                                [-e <example> / --example <example>]")
    print("[INFO] List of solvers [pmc, maple, mapleLRB, glucose+, comsps]")

# Function to get command-line arguments
def getargs(argv):
    solver = ""
    example = ""
    preProcessingList = []

    try:
        opts, args = getopt.getopt(argv, "hs:e:vb", ["help", "solver=", "example=", "vivification", "backbone"])
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

        elif opt in ("-v",  "--vivification"):
            preProcessingList.append("v")

        elif opt in ("-b", "--backbone"):
            preProcessingList.append("b")

    if solver == "" and example == "":
        print("[ERROR] Solver and example are mandatory arguments")
        print("[ERROR] EXITING...")
        sys.exit(1)

    if solver not in SOLVERS:
        print("[ERROR] Provide correct solver")
        print("[ERROR] EXITING...")
        sys.exit(1)

    if not exampleExists(example):
        print("[ERROR] Example not found")
        print("[ERROR] EXITING...")
        sys.exit(1)

    if len(preProcessingList) < 1:
        print("[ERROR] One preprocessing technique is mandatory")
        print("[ERROR] EXITING...")
        sys.exit(1)

    return solver, example, preProcessingList

# Function to write metadata to a log file
def writeMetadata(solverName, example, preProcessingList, logFile):
    cv = "FALSE"
    cb = "FALSE"
    pos = 1
    for p in preProcessingList:
        if p == "v":
            cv = pos
        if p == "b":
            cb = pos
        pos += 1

    with open(logFile, 'a') as f:
        f.write(f"{solverName};{example};{cv};{cb};")

# Function to get the number of variables and clauses from an example file
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

# Function to compare worlds and log the result
def compareWorlds(w1, w2, logFile):
    sameWs = False
    if w1 != None and w2 != None and w1 != "" and w2 != "":
        if w1 == w2:
            sameWs = True
    with open(logFile, 'a') as f:
        if sameWs:
            f.write("TRUE;")
        else:
            f.write("FALSE;")

# Function to perform vivification
def vivification(solverPath, solverName, example, vivifiedExample, varElimination=False):
    eliminationFlag = "-no-elim"
    if varElimination:
        eliminationFlag = "-elim"

    cmd = ""
    if solverName == "pmc":
        cmd = f"{solverPath} -verb=1 -vivification {example} | tee -a {vivifiedExample}"

    else:
        cmd = f"{solverPath} {eliminationFlag} -pre -verb=2 -dimacs={vivifiedExample} {example}  | tee -a {vivifiedExample}_aux.log"
    os.system(cmd)

# Function to grep vivification time in the logs
def grepTimeInVivification(example, logFile, deleteFile):
    command = f"grep \"CPU time\" {example} | awk '{{print $5}}' | tr '\n' ';' >> {logFile}"
    os.system(command)

    if deleteFile:
        os.remove(example)

# Function to execute backbone script on given example
def backbone(solverPath, example, backbonedExample):
    cmd = f"{solverPath} {example} {OUTPUT_PATH} {backbonedExample}"
    os.system(cmd)

# Function to grep backbone time in the logs
def grepTimeInBackbone(example, logFile):
    auxName = ('.'.join(os.path.basename(example).split('.')[:-1]))
    cmd = f"grep \"time\" {OUTPUT_PATH}/{auxName}.stats | sed 's/.*time=\\([0-9.]*\\).*/\\1/' | xargs echo | awk '{{printf \"%f;\", $1 + $2}}' | sed 's/\./,/g' >> {logFile}"
    os.system(cmd)
    os.remove(f"{OUTPUT_PATH}/{auxName}.stats")

# Function to establish techniques order
def preProcessing(techniques, solverPath, solverName, example, preproExample, logFile):

    PREPROCESSINGMECH = {
        'v': vivification,
        'b': backbone
    }

    for t in techniques:
        if t == 'v':
            PREPROCESSINGMECH[t](solverPath, solverName, example, preproExample)
            if os.path.basename(solverPath) == "pmc":
                grepTimeInVivification(f"{preproExample}", logFile, False)
            else:
                grepTimeInVivification(f"{preproExample}_aux.log", logFile, True)

        else:
            PREPROCESSINGMECH[t](BACKBONE_PATH, BACKBONE_PATH.split('/')[-1], example, preproExample)
            grepTimeInBackbone(example, logFile, True)


# Function to construct and execute c2d command to convert CNF to dDNNF
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
            f.write("TIMEOUT;")
            return False
    return True

# Function to grep total time from c2d output
def grepTimeInC2D(output, logFile, deleteFile):
    cmd = f"grep \"Total Time\" {output} | sed -E 's/Total Time: ([^s]+)s/\\1/' |  tr '\n' ';' >> {logFile}"
    os.system(cmd)
    if deleteFile:
        cmd = f"rm -f {output}"
        os.system(cmd)

# Function to count CNF worlds using d4
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
        else:
            with open(logFile, 'a') as f:
                f.write("ABORT;")
            return None

    except subprocess.TimeoutExpired:
        with open(logFile, 'a') as f:
            f.write("TIMEOUT;")
        return None
    except:
        with open(logFile, 'a') as f:
            f.write("ABORT;")
        return None
    return worlds.group(1)


def ddnnfCountCmd(example, logFile):
    cmd = f"{dREASONER_PATH} |  tr '\n' ';' >> {logFile}"
    os.system(cmd)


# Function which executes all the steps to collect all metrics of a given example
def execute(solverPath, example, preProcessingList):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    pSplited = solverPath.split('/')
    index = pSplited.index("programs")
    solverName = pSplited[(index + 1)]

    logFile = f"{OUTPUT_PATH}/{solverName}_{PID}_{example}_{timestamp}.log"

    preproExample = f"prepro_{solverName}_{PID}_{example}"

    #SATsolver;Example;Vivification;Backbone;#vars OGCNF;#clau OGCNF;OGCNF worlds;Vivify-Time;#vars VIVCNF;#clau VIVCNF;VIVCNF worlds;Same worlds;OGCNF2dDNNF Time;VIVCNF2dDNNF Time;OGdDNNF worlds;VIVdDNNF worlds;
    #os.system(command)

    writeMetadata(solverName, example, preProcessingList, logFile)

    # First extract the number of vars & clauses of the original cnf
    getVarsandClauses(f"{EXAMPLES_PATH}/{example}", logFile)

    # Second count the number of solutions of the original cnf
    OGworlds = None
    OGworlds = cnfCountWorlds(f"{EXAMPLES_PATH}/{example}", logFile)

    # Third preprocess the cnf with desired mechanism and techniques TODO ADD D4 to vivification process
    preProcessing(preProcessingList, solverPath, solverName, f"{EXAMPLES_PATH}/{example}", f"{OUTPUT_PATH}/{preproExample}", logFile)

    # Fourth extract the number of vars & clauses of the vivified cnf
    getVarsandClauses(f"{OUTPUT_PATH}/{preproExample}", logFile)

    # Fifth count the number of solutions of the vivified cnf
    PREworlds = None
    PREworlds = cnfCountWorlds(f"{OUTPUT_PATH}/{preproExample}", logFile)

    # Sixth same solutions OG CNF - VIV CNF
    compareWorlds(OGworlds, PREworlds, logFile)

    # Seventh convert original cnf to dDNNF TODO CAN BE DONE EVEN WITH D4
    compOGdDNNF = cnf2dDNNFCmd(example, False, logFile, solverName)
    grepTimeInC2D(f"{OUTPUT_PATH}/c2d_{solverName}_{PID}_{example}.log", logFile, True)
    if compOGdDNNF:
        os.replace(f"{EXAMPLES_PATH}/{example}.nnf", f"{OUTPUT_PATH}/{PID}_{example}.nnf")

    # Eighth convert vivified cnf to dDNNF TODO CAN BE DONE EVEN WITH D4
    compPredDNNF = cnf2dDNNFCmd(f"{preproExample}", True, logFile)
    grepTimeInC2D(f"{OUTPUT_PATH}/c2d_{preproExample}.log", logFile, True)

    # TODO Tenth count OG dDNNF - VIV dDNNF
    OGdDNNFworlds = None
    PREdDNNFworlds = None
    if compOGdDNNF:
        OGdDNNFworlds = ddnnfCountWorlds(f"{OUTPUT_PATH}/{PID}_{example}.nnf", logFile)
    if compPredDNNF:
        PREdDNNFworlds = ddnnfCountWorlds(f"{OUTPUT_PATH}/{preproExample}.nnf", logFile)

    compareWorlds(OGdDNNFworlds, PREdDNNFworlds, logFile)

    with open(logFile, 'a') as f:
        f.write("\n")


# Main function
def main():
    signal.signal(signal.SIGINT, signalHandler)
    checkBASEDIR(CURR_DIR)

    solverChoice = ""
    example = ""

    # Parse command-line arguments
    solverChoice, example, preProcessingList = getargs(sys.argv[1:])

    # Create output directory if it does not exist
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    # Execute the chosen solver on the specified example
    print(f"[INFO] Processing example {example} with solver {solverChoice}")
    print()
    execute(SOLVERS[solverChoice], example, preProcessingList)
    print("[INFO] Process finished without errors")


# Entry point of the script
if __name__ == "__main__":
    main()
