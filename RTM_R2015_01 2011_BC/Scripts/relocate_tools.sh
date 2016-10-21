#!/bin/sh
# Batch procedure to relocate tool references in the toolbox to the present
# location of the EMME project files.
#
# Find the installed EMME python as it may not exist in $PATH
PYTHON=$(cygpath "$EMMEPATH")/Python27/python.exe
"$PYTHON" toolbox_modify.py ../Scripts/TL_RTM_Release_2015_01.00.mtbx Scripts
