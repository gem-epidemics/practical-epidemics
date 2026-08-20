#!/bin/bash

SCRIPTDIR=$(dirname "$0")
INPUTDIR=$1
OUTPUTDIR=$2

mkdir -p $OUTPUTDIR

for NB in `find $INPUTDIR -maxdepth 1 -name "*.ipynb"`; do
    OUTPUTFILE=$OUTPUTDIR/`basename $NB`
    echo Processing '$NB' to '$OUTPUTFILE'
    python $SCRIPTDIR/myst_exercise_to_colab.py $NB -o $OUTPUTFILE
    echo Done
done
