#!/bin/bash
######################### HEADER ############################
# Author: Rubén Heradio Gil
# TFM project: TÉCNICAS DE PRE-PROCESADO EN SOLUCIONADORES
#              SAT: VIVIFICACIÓN
#############################################################
if [ $# -lt 1 ]; then 
    echo "Usage: preprocess dimacs_file"
    exit
fi

example=$1 
OUTPUT_PATH=$2 
backbonedResultPath=$3
auxOuput="aux.file"

# Remove extension from filename
filename="${1%.*}"
basename="${filename##*/}"

# Get current bash script directory
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Running minibones on $example"
#echo "/usr/bin/time -f \"minibones stats: time=%e secs, average memory=%K KB, max memory=%M KB\" -o \"${OUTPUT_PATH}/${basename}_back.time\" $DIR/bin/minibones -ubm ${example} 1> \"${filename}.back\" 2> \"/dev/null"
/usr/bin/time -f "minibones stats: time=%e secs, average memory=%K KB, max memory=%M KB" -o "${OUTPUT_PATH}/${basename}_back.time" $DIR/bin/minibones -ubm ${example} 1> "${filename}.back" 2> "/dev/null"


echo "Preprocessing $example with its backbone"
#echo "/usr/bin/time -f \"preprocessing stats: time=%e secs, average memory=% KB, max memory=%M KB\" -o \"${OUTPUT_PATH}/${basename}_preproc.time\" $DIR/bin/bone_cleaner \"${example}\" \"${OUTPUT_PATH}/aux.file\" > \"${OUTPUT_PATH}/${basename}_preproc.stats"
/usr/bin/time -f "preprocessing stats: time=%e secs, average memory=% KB, max memory=%M KB" -o "${OUTPUT_PATH}/${basename}_preproc.time" $DIR/bin/bone_cleaner "${example}" "${OUTPUT_PATH}/aux.file" > "${OUTPUT_PATH}/${basename}_preproc.stats"

cat "${OUTPUT_PATH}/${basename}_back.time" "${OUTPUT_PATH}/${basename}_preproc.time" "${OUTPUT_PATH}/${basename}_preproc.stats" > "${OUTPUT_PATH}/${basename}.stats"

rm "${OUTPUT_PATH}/${basename}_back.time"
rm "${filename}.back"
rm "${OUTPUT_PATH}/${basename}_preproc.time"
rm "${OUTPUT_PATH}/${basename}_preproc.stats"

mv "${OUTPUT_PATH}/aux.file" "${backbonedResultPath}"

