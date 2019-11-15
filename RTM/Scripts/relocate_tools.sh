#!/bin/sh
# Batch procedure to relocate tool references in the toolbox to the present
# location of the EMME project files.
#
# Find the installed EMME python as it may not exist in $PATH
PYTHON=$(cygpath "$EMMEPATH")/Python27/python.exe
"$PYTHON" toolbox_modify.py ../Scripts/Phase3Scripts/RTM_Phase3.mtbx Phase3Scripts
"$PYTHON" toolbox_modify.py ../Scripts/util/RTM_util.mtbx util
"$PYTHON" toolbox_modify.py ../Scripts/Phase3Analytics/Analytics.mtbx Phase3Analytics
"$PYTHON" toolbox_modify.py ../Scripts/EconomicAnalysis/EconomicAnalysis.mtbx EconomicAnalysis
