rem Batch procedure to relocate tool references in the toolbox to the present
rem location of the EMME project files.
rem
rem Find the installed EMME python as it may not exist in $PATH
set PYTHON=%EMMEPATH%\Python27\python.exe
"%PYTHON%" toolbox_modify.py ../Scripts/EconomicAnalysis/EconomicAnalysis.mtbx EconomicAnalysis
PAUSE