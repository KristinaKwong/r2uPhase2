rem Batch procedure to relocate tool references in the toolbox to the present
rem location of the EMME project files.
rem
rem Find the installed EMME python as it may not exist in $PATH
set PYTHON=%EMMEPATH%\Python27\python.exe
"%PYTHON%" toolbox_modify.py ../Scripts/Phase3Scripts/RTM_Phase3.mtbx Phase3Scripts
"%PYTHON%" toolbox_modify.py ../Scripts/util/RTM_util.mtbx util
"%PYTHON%" toolbox_modify.py ../Scripts/Phase3Analytics/RTM3Analytics.mtbx Phase3Analytics
"%PYTHON%" toolbox_modify.py ../Scripts/Phase3Tools/RTM3Tools.mtbx Phase3Tools
PAUSE
