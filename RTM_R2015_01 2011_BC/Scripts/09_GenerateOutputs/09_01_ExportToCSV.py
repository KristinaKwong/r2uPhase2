##--------------------------------------------------
##--TransLink Phase 2 Regional Transportation Model
##--
##--Path:
##--Purpose:
##--------------------------------------------------
##--Last modified 2014-02-14 Kevin Bragg (INRO)
##--Reason: Update to Emme 4.0 namespaces
##          Code cleanup PEP 8 compliance
##---------------------------------------------------
##--Called by:
##--Calls:
##--Accesses:
##--Outputs:
## Export Matrices to CSV - HDR

import inro.modeller as _modeller
import os
import traceback as _traceback
from datetime import datetime

#import inro.modeller as _m
import inro.emme.database.emmebank as _eb
import csv as _csv


class exporttocsv(_modeller.Tool()):
    ##Modify path for new package implementation
    # TODO: why is there a hardcoded path here?
    PathHeader = 'C:\\Users\\adarwiche\\Desktop\\Model_Cleanup\\Databank_Testing_School\\'

    ##Create global attributes (referring to dialogue boxes on the pages)
    TripRateFile = _modeller.Attribute(_modeller.InstanceType)
    Purpose = _modeller.Attribute(list)
    #    SelectMatrixSelection = _modeller.Attribute(_modeller.InstanceType)
    MatrixSelection = _modeller.Attribute(list)
    tool_run_msg = _modeller.Attribute(unicode)
    list_of_matrices = _modeller.Attribute(list)
    OutputFile = _modeller.Attribute(_modeller.InstanceType)

    def page(self):
        start_path = os.path.dirname(_modeller.Modeller().emmebank.path)
        ##Create various aspects to the page
        pb = _modeller.ToolPageBuilder(self, title="List of all matrices to export",
                                       description="Select Matrices to Export",
                                       branding_text="TransLink")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        pb.add_select_matrix(tool_attribute_name="MatrixSelection",
                             filter=['ORIGIN', 'DESTINATION'],
                             title="List of all matrices to export to csv",
        )

        pb.add_select_file(tool_attribute_name="OutputFile",
                           window_type="save_file",
                           #TODO                        start_path=start_path,
                           start_path=self.PathHeader + '00_OtherFiles\\00_03_ExportToCSV.csv',
                           file_filter='*.csv',
                           title="Batchout Location",
                           note="Export location for matrices selected"
        )

        return pb.render()

    def run(self):
    ##        This gets executed when someone presses the big 'Start this Tool' button
        self.tool_run_msg = ""
        try:
            self.list_of_matrices = [s for s in self.MatrixSelection if
                                     (s.type == 'ORIGIN' or s.type == 'DESTINATION')]
            self.__call__(self.list_of_matrices, self.OutputFile)
            run_msg = "Tool completed"
            self.tool_run_msg = _modeller.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _modeller.PageBuilder.format_exception(e, _traceback.format_exc(e))

    def __call__(self, list_of_matrices, OutputFile):
    ##        Start logging this under a new 'nest'
        with _modeller.logbook_trace("Export Matrices Toolbox"):
            print "--------Export_Matrices_Toolbox, " + str(datetime.now().strftime('%H:%M:%S'))

            emme_path = os.path.dirname(_modeller.Modeller().emmebank.path).replace("\"", "\\") + "\\emmebank"
            emmebank = _eb.Emmebank(emme_path)
            scenario = list(emmebank.scenarios())[0]
            zones = scenario.zone_numbers

            matrix_data = []
            matrix_name = []
            matrix_description = []
            for matrix_id in list_of_matrices:
                matrix = scenario.emmebank.matrix(matrix_id)
                matrix_data.append(matrix.get_data(scenario.id))
                matrix_name.append(matrix.name)
                matrix_description.append(matrix.description)

            with open(OutputFile.replace(",", "").replace(".txt", "_matrices.csv"), 'wb') as f:
                writer = _csv.writer(f, dialect='excel')
                writer.writerow(["matrices:"] + list_of_matrices)
                writer.writerow(["name:"] + matrix_name)
                writer.writerow(["description"] + matrix_description)

                for z in zones:
                    writer.writerow([z] + [data.get(z) for data in matrix_data])
