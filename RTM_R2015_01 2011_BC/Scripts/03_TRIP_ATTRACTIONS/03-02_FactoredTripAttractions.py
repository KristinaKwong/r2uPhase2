##--------------------------------------------------
##--TransLink Phase 2 Regional Transportation Model - HDR
##--03-02_FactoredTripAttractions.PY
##--Path: translink.emme.factoredtripattraction
##--Purpose of 03-02_FactoredTripAttractions: factor attraction totals for RTM generation model
##--------------------------------------------------
##--Last modified 2014-02-14 Kevin Bragg (INRO)
##--Reason: Update to Emme 4.0 namespaces
##          Code cleanup PEP 8 compliance
##--Last modified 2013-09-03 Rhys Wolff (HDR)
##--Last modification reason - add comments and notes
##---------------------------------------------------
##--Called by: 00_00_RUN_ALL.PY
##--Calls:     None
##--Accesses:  None
##--Outputs: 03-02_OUTPUT_RESULTS.txt
##---------------------------------------------------
##--Status/additional notes:
##--Supersedes all earlier versions of 03-02_FactoredTripAttractions
##---------------------------------------------------

import inro.modeller as _m
import os
import traceback as _traceback
from datetime import datetime


class FactoredTripAttractions(_m.Tool()):
    ##Modify path for new package implementation


    OutputFile = _m.Attribute(_m.InstanceType)
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        start_path = os.path.dirname(_m.Modeller().emmebank.path)
        pb = _m.ToolPageBuilder(self, title="Trip Attractions",
                                       description="Factored Trip Attractions<br>Data Needed from a prior Module:<br>mo161-mo265",
                                       branding_text="TransLink")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)
        # TODO: add PathHeader input to page

        return pb.render()

    def run(self):
        print "--------03-02 - RUN - FACTORED TRIP ATTRACTIONS: " + str(datetime.now().strftime('%H:%M:%S'))
        self.tool_run_msg = ""
        self.PathHeader = os.path.dirname(_m.Modeller().emmebank.path) + "\\"
        self.OutputFile = self.PathHeader + "03_TRIP_ATTRACTIONS/Outputs/03-02_OUTPUT_RESULTS.txt"
        print "self.OutputFile: ", self.OutputFile
        try:
            self.__call__(self.PathHeader )
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    def __call__(self, PathHeader):
        with _m.logbook_trace("03-02 - Factored Trip Attractions"):
            print "----03-02 - Factored Trip Attractions: " + str(datetime.now().strftime('%H:%M:%S'))
            OutputFile = PathHeader + "03_TRIP_ATTRACTIONS/Outputs/03-02_OUTPUT_RESULTS.txt"

            ## Define variables to store/locate values.
            purpose_list = ['HBWL', 'HBWM', 'HBWH', 'NHBW', 'HBU', 'HBSCHO', 'HBSHOP', 'HBPB', 'HBSOC', 'HBESC', 'NHBO']
            purpose_factors = {'HBWL': {'moSum': 0, 'mdSum': 0, 'Factor': 0},
                               'HBWM': {'moSum': 0, 'mdSum': 0, 'Factor': 0},
                               'HBWH': {'moSum': 0, 'mdSum': 0, 'Factor': 0},
                               'NHBW': {'moSum': 0, 'mdSum': 0, 'Factor': 0},
                               'HBU': {'moSum': 0, 'mdSum': 0, 'Factor': 0},
                               'HBSCHO': {'moSum': 0, 'mdSum': 0, 'Factor': 0},
                               'HBSHOP': {'moSum': 0, 'mdSum': 0, 'Factor': 0},
                               'HBPB': {'moSum': 0, 'mdSum': 0, 'Factor': 0},
                               'HBSOC': {'moSum': 0, 'mdSum': 0, 'Factor': 0},
                               'HBESC': {'moSum': 0, 'mdSum': 0, 'Factor': 0},
                               'NHBO': {'moSum': 0, 'mdSum': 0, 'Factor': 0}
            }

            ## Calculates factors from 'md' to 'mo' segmentation
            purpose_factors = self.Calculate_Factors(purpose_list, purpose_factors)

            ## Apply Factors for the md to scale them to equal to the sum of the respective 'mo' segments
            self.Apply_Factors(purpose_list, purpose_factors)

            ## Output results
            self.Output_Results(OutputFile)

            ## Export Matrices to CSV
            self.Export_Matrices(OutputFile)

    #Export all mo matrices to CSV
    def Export_Matrices(self, OutputFile):
        with _m.logbook_trace("Export_Matrices"):
            print "--------Export_Matrices, " + str(datetime.now().strftime('%H:%M:%S'))
            ExportToCSV = _m.Modeller().tool("translink.emme.stage4.step9.exporttocsv")
            list_of_matrices = ["md" + str(i) for i in range(5, 12) + range(20, 26) + range(31, 53)] + ["mo" + str(i)
                                                                                                        for i in
                                                                                                        range(915, 927)]
            ExportToCSV(list_of_matrices, OutputFile)

        ##    Outputs results matrix to a file

    def Output_Results(self, OutputFile):
        with _m.logbook_trace("Output Results"):
            print "--------Output_Results, " + str(datetime.now().strftime('%H:%M:%S'))
            ##    Create emmebank object
            my_modeller = _m.Modeller()
            my_emmebank = my_modeller.desktop.data_explorer().active_database().core_emmebank

            Output_File = OutputFile.replace(",", "")
            Output_File_GY = OutputFile.replace(",", "").replace(".", "_GY.")
            Output_File_GU = OutputFile.replace(",", "").replace(".", "_GU.")
            # TODO: replace "." means file path cannot contain a "." elsewhere

            ##    List to hold matrix objects
            md_value = []

            ##    Loop to append all result matrices onto the variable 'md_value'
            for mo_num in [24, 25] + range(31, 53):
                md_value.append(my_emmebank.matrix("md" + str(mo_num)))


            ##    Export matrices using the appended list of md_value matrices
            export_matrices = _m.Modeller().tool(
                "inro.emme.data.matrix.export_matrices")

            ## Export all matrix data
            export_matrices(export_file=Output_File,
                            field_separator=' ',
                            matrices=md_value,
                            export_format="PROMPT_DATA_FORMAT",
                            skip_default_values=True,
                            full_matrix_line_format="ONE_ENTRY_PER_LINE")

            ## Export matrix data aggregated to the gy ensemble
            export_matrices(export_file=Output_File_GY,
                            field_separator=' ',
                            matrices=md_value,
                            partition_aggregation={'destinations': 'gy', 'operator': 'sum'},
                            export_format="PROMPT_DATA_FORMAT",
                            skip_default_values=True,
                            full_matrix_line_format="ONE_ENTRY_PER_LINE")

            ## Export matrix data aggregated to the gu ensemble
            export_matrices(export_file=Output_File_GU,
                            field_separator=' ',
                            matrices=md_value,
                            partition_aggregation={'destinations': 'gu', 'operator': 'sum'},
                            export_format="PROMPT_DATA_FORMAT",
                            skip_default_values=True,
                            full_matrix_line_format="ONE_ENTRY_PER_LINE")

            for Output in [Output_File, Output_File_GY, Output_File_GU]:
                f = open(Output, 'a')
                f.write("c ------Data Sources:\n")
                f.write("c " + Output_File + "\n")
                f.close()

    def Apply_Factors(self, purpose_list, purpose_factors):
        with _m.logbook_trace("Apply_Factors"):
            print "--------Apply_Factors, " + str(datetime.now().strftime('%H:%M:%S'))

            NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
            compute_matrix = _m.Modeller().tool(NAMESPACE)

            spec_as_dict = {
                "expression": "EXPRESSION",
                "result": "RESULT",
                "constraint": {
                    "by_value": None,
                    "by_zone": {"origins": None, "destinations": None}
                },
                "aggregation": {"origins": None, "destinations": None},
                "type": "MATRIX_CALCULATION"
            }

            ## Scaling all the mds to match the 'mo' total, except for md46, HBU.
            for i in range(42, 46) + range(47, 53):
                expression = "md" + str(i - 11) + "*" + str(purpose_factors[purpose_list[i - 42]]["Factor"])
                result = "md" + str(i)
                # print result + " = " + expression
                spec_as_dict["expression"] = expression
                spec_as_dict["result"] = result
                report = compute_matrix(spec_as_dict)

            spec_as_dict["expression"] = "md35"
            spec_as_dict["result"] = "md46"
            report = compute_matrix(spec_as_dict)

            ## scaling the mo - HBU to match md for HBU
            for i in range(1, 13):
                expression = "mo" + str(i + 184) + "/" + str(purpose_factors['HBU']['Factor'])
                result = "mo" + str(i + 914)
                spec_as_dict["expression"] = expression
                spec_as_dict["result"] = result
                report = compute_matrix(spec_as_dict)

    def Calculate_Factors(self, purpose_list, purpose_factors):
        with _m.logbook_trace("Calculate_Factors"):
            print "--------Calculate_Factors, " + str(datetime.now().strftime('%H:%M:%S'))

            NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
            compute_matrix = _m.Modeller().tool(NAMESPACE)

            spec_as_dict = {
                "expression": "EXPRESSION",
                "result": None,
                "constraint": {
                    "by_value": None,
                    "by_zone": {"origins": None, "destinations": None}
                },
                "aggregation": {"origins": None, "destinations": None},
                "type": "MATRIX_CALCULATION"
            }

            for i in range(0, 3):
                x = i + 161
                # print purpose_list[i], x, x+3, x+6, x+9

                spec_as_dict["expression"] = "mo" + str(x) + " + " + "mo" + str(x + 3) + " + " + "mo" + str(
                    x + 6) + " + " + "mo" + str(x + 9)
                spec_as_dict["aggregation"]["origins"] = "+"
                report = compute_matrix(spec_as_dict)
                purpose_factors[purpose_list[i]]['moSum'] = report["sum"]

            spec_as_dict["aggregation"]["origins"] = None

            for i in range(173, 269, 12):
                expression = "0"
                for j in range(0, 12):
                    expression = expression + " + mo" + str(i + j)
                spec_as_dict["expression"] = expression
                spec_as_dict["aggregation"]["origins"] = "+"
                report = compute_matrix(spec_as_dict)
                purpose_factors[purpose_list[(i - 173) / 12 + 3]]['moSum'] = report["sum"]

            spec_as_dict["aggregation"]["origins"] = None

            for i in range(31, 42):
                spec_as_dict["expression"] = "md" + str(i)
                spec_as_dict["aggregation"]["destinations"] = "+"
                report = compute_matrix(spec_as_dict)
                purpose_factors[purpose_list[i - 31]]['mdSum'] = report["sum"]

            spec_as_dict["aggregation"]["destinations"] = None

            for i in range(0, 11):
                purpose_factors[purpose_list[i]]['Factor'] = purpose_factors[purpose_list[i]]['moSum'] / \
                                                             purpose_factors[purpose_list[i]]['mdSum']

                # print "purpose_factors: ", purpose_factors
        return purpose_factors
