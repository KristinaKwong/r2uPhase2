##--------------------------------------------------
##--TransLink Phase 2 Regional Transportation Model - HDR
##--03-01_TripAttractions.PY
##--Path: translink.emme.tripattraction
##--Purpose of 03-01_TripAttractions: develop attraction totals for RTM generation model
##--------------------------------------------------
##--Last modified 2014-02-14 Kevin Bragg (INRO)
##--Reason: Update to Emme 4.0 namespaces
##          Code cleanup PEP 8 compliance
##--Last modified 2013-09-03 Rhys Wolff (HDR)
##--Last modification reason - add comments and notes
##---------------------------------------------------
##--Called by: 00_00_RUN_ALL.PY
##--Calls:     None
##--Accesses:  MatrixTransactionFile.txt, 31_VARIABLES.csv,
##--           32_COEFFICIENTS.csv, 33_GroupingsPerPurpose.csv
##--Outputs: 03-01_OUTPUT_RESULTS.txt
##---------------------------------------------------
##--Status/additional notes:
##--Supersedes all earlier versions of 03-01_TripAttractions
##---------------------------------------------------

import inro.modeller as _modeller
import csv
import os
import traceback as _traceback
from datetime import datetime
from collections import defaultdict


class TripAttractions(_modeller.Tool()):
    LandUse = _modeller.Attribute(_modeller.InstanceType)

    CoefficientsPerGrouping = _modeller.Attribute(_modeller.InstanceType)
    GroupingsPerPurpose = _modeller.Attribute(_modeller.InstanceType)
    OutputFile = _modeller.Attribute(_modeller.InstanceType)
    tool_run_msg = _modeller.Attribute(unicode)

    def page(self):
        start_path = os.path.dirname(_modeller.Modeller().emmebank.path)
        pb = _modeller.ToolPageBuilder(self, title="Trip Attractions")
        pb.description = """
Trip Attractions<br>
Data Needed from a prior Toolbox:<br>
mo20, mo365, mo366, mo367, mo368, mo369, mo370, mo371, mo372, mo373, mo374, mo375, mo376"""
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)
        # TODO: add inputs to page

        return pb.render()

    def run(self):
        print "--------03-01 - RUN - TRIP ATTRACTIONS: " + str(datetime.now().strftime('%H:%M:%S'))
        self.tool_run_msg = ""
        try:
            self.__call__(self.LandUse, self.CoefficientsPerGrouping, self.OutputFile, self.GroupingsPerPurpose)
            run_msg = "Tool completed"
            self.tool_run_msg = _modeller.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _modeller.PageBuilder.format_exception(e, _traceback.format_exc(e))

    def __call__(self, PathHeader):
        with _modeller.logbook_trace("03-01 - Trip Attractions"):
            print "----03-01 - Trip Attractions: " + str(datetime.now().strftime('%H:%M:%S'))

            LandUse = PathHeader + "03_TRIP_ATTRACTIONS/Inputs/31_VARIABLES.csv"
            CoefficientsPerGrouping = PathHeader + "03_TRIP_ATTRACTIONS/Inputs/32_COEFFICIENTS.csv"
            GroupingsPerPurpose = PathHeader + "03_TRIP_ATTRACTIONS/Inputs/33_GroupingsPerPurpose.csv"
            OutputFile = PathHeader + "03_TRIP_ATTRACTIONS/Outputs/03-01_OUTPUT_RESULTS.txt"
            ##Batchin File
            self.Matrix_Batchins(PathHeader)

            ## Creates Low and High Income Households from the 'mo' matrices
            self.CreateHouseholds_LowHighIncome_TotalPop()

            ##Store Coefficients
            coefficients_data = self.Store_Coefficients(CoefficientsPerGrouping)

            ##Store Groupings Per Purpose
            groupings_per_purpose = self.Store_Groupings(GroupingsPerPurpose)

            ## md31-md41 Calculate Trip Rates
            self.Calculate_TripRates(coefficients_data, groupings_per_purpose, PathHeader)

            ## md31-md41 Remove negative values from Trip Rates
            self.Check_forNegatives()

            ## Output results
            self.Output_Results(OutputFile, LandUse, CoefficientsPerGrouping, GroupingsPerPurpose)

            ## Export Matrices to CSV
            self.Export_Matrices(OutputFile)

    #Export all mo matrices to CSV
    def Export_Matrices(self, OutputFile):
        with _modeller.logbook_trace("Export_Matrices"):
            print "--------Export_Matrices, " + str(datetime.now().strftime('%H:%M:%S'))
            ExportToCSV = _modeller.Modeller().tool("translink.emme.stage4.step9.exporttocsv")
            list_of_matrices = ["md" + str(i) for i in range(5, 12) + range(20, 27) + range(31, 42)]
            ExportToCSV(list_of_matrices, OutputFile)

        ##    Outputs results matrix to a file

    def Output_Results(self, OutputFile, LandUse, CoefficientsPerGrouping, GroupingsPerPurpose):
        with _modeller.logbook_trace("Output Results"):
            print "--------Output_Results, " + str(datetime.now().strftime('%H:%M:%S'))
            ##    Create emmebank object
            my_modeller = _modeller.Modeller()
            my_emmebank = my_modeller.desktop.data_explorer().active_database().core_emmebank

            Output_File = OutputFile.replace(",", "")
            Output_File_GY = OutputFile.replace(",", "").replace(".", "_GY.")
            Output_File_GU = OutputFile.replace(",", "").replace(".", "_GU.")

            ##    List to hold matrix objects
            md_value = []

            ##    Loop to append all result matrices onto the variable 'md_value'
            for mo_num in [24, 25, 26] + range(31, 42):
                md_value.append(my_emmebank.matrix("md" + str(mo_num)))

            ##    Export matrices using the appended list of md_value matrices
            export_matrices = _modeller.Modeller().tool(
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
                f.write("c " + LandUse + "\n")
                f.write("c " + CoefficientsPerGrouping + "\n")
                f.write("c " + GroupingsPerPurpose + "\n")
                f.close()

            ##    Open up window with the OutputFile Selected
            print "----------------OutputFile: ", Output_File
            #subprocess.Popen(r'explorer /select, ' + OutputFile.replace("/","\\").replace(",","") + '"')

    ## md31-md41 Remove negative values from Trip Rates
    def Check_forNegatives(self):
        with _modeller.logbook_trace("Check_forNegatives"):
            print "--------Check_forNegatives, " + str(datetime.now().strftime('%H:%M:%S'))
            NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
            compute_matrix = _modeller.Modeller().tool(NAMESPACE)

            spec_as_dict = {
                "expression": "0",
                "result": "RESULT",
                "constraint": {
                    "by_value": {
                        "od_values": "RESULT",
                        "interval_min": -1000000000,
                        "interval_max": 0,
                        "condition": "INCLUDE"
                    },
                    "by_zone": {"origins": None, "destinations": None}
                },
                "aggregation": {"origins": None, "destinations": None},
                "type": "MATRIX_CALCULATION"
            }

            for i in range(1, 12):
                spec_as_dict["result"] = "md" + str(30 + i)
                spec_as_dict["constraint"]["by_value"]["od_values"] = "md" + str(30 + i)
                # print spec_as_dict["constraint"]["by_value"]["interval_min"]
                report = compute_matrix(spec_as_dict)

    def Calculate_TripRates(self, coefficients_data, groupings_per_purpose, PathHeader):
        print "--------Calculate_TripRates, " + str(datetime.now().strftime('%H:%M:%S'))
        with _modeller.logbook_trace("Calculate_TripRates"):

            NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
            compute_matrix = _modeller.Modeller().tool(NAMESPACE)

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

            #Define Attraction attributes
            Variable_Matrix = [['Contruction/Mfg', 'md5'],
                               ['FIRE', 'md6'],
                               ['TCU/Wholesale', 'md7'],
                               ['Retail', 'md8'],
                               ['AccomFood/InfoCult', 'md10'],
                               ['Health/Educat/PubAdmin', 'md11'],
                               ['POP 5 to 17', '(md21+md22)'],
                               ['Total_Population', 'md20'],
                               ['Households_Low', 'md24'],
                               ['Household_Medium', 'md25'],
                               ['Households_high', 'md26'],
                               ['PS2011', 'md23'],
                               ['Business/OtherServices', 'md9']]

            # print "coefficients_data",coefficients_data
            # print "groupings_per_purpose", groupings_per_purpose

            for i in range(1, len(groupings_per_purpose)):
                for j in range(1, len(groupings_per_purpose[0])):
                    expression = "0"
                    for x in Variable_Matrix:
                        expression = expression + " + " + \
                                     coefficients_data[groupings_per_purpose[0][j]][groupings_per_purpose[i][j]][x[0]][
                                         0] + "*" + x[1]

                    gy_value = "gy" + groupings_per_purpose[i][0]
                    # print "expression: ", expression
                    # print "gy_value:",gy_value
                    # print "md"+str(j+30)

                    f = open(PathHeader + '03_TRIP_ATTRACTIONS/Inputs/RegressionEquations', 'a')
                    # f.write("--------------------------------------------------\n")
                    f.write("md" + str(j + 30) + " : " + groupings_per_purpose[i][
                        j] + " : " + gy_value + " : " + expression + "\n")
                    f.close()

                    spec_as_dict["expression"] = expression
                    spec_as_dict["result"] = "md" + str(j + 30)
                    spec_as_dict["constraint"]["by_zone"]["destinations"] = gy_value
                    report = compute_matrix(spec_as_dict)

    def Store_Groupings(self, GroupingsPerPurpose):
        print "--------Store_Groupings, " + str(datetime.now().strftime('%H:%M:%S'))
        with _modeller.logbook_trace("Store Store_Groupings"):
            with open(GroupingsPerPurpose, 'rb') as f:
                reader = csv.reader(f, dialect='excel')
                header = reader.next()
                data = [header]
                for row in reader:
                    data.append(row)
                    #dict_data = dict( (data[i][0],data[i][1:]) for i in range(0,len(data)))
        return data

    def Store_Coefficients(self, CoefficientsPerGrouping):
        print "--------Store_Coefficients, " + str(datetime.now().strftime('%H:%M:%S'))
        with _modeller.logbook_trace("Store_Coefficients"):
            with open(CoefficientsPerGrouping, 'rb') as f:
                reader = csv.reader(f, dialect='excel')
                header = reader.next()
                data = [header]
                for row in reader:
                    data.append(row)

                temp_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
                for i in data[1:]:
                    for j in range(2, len(i)):
                        if i[j] == "":
                            value = "0"
                        else:
                            value = i[j]
                        temp_dict[i[0]][i[1]][data[0][j]].append(value)

        return temp_dict

    ##    Creates low and high-income households and transposes population and parking matrices
    def CreateHouseholds_LowHighIncome_TotalPop(self):
        with _modeller.logbook_trace("CreateHouseholds_LowHighIncome_TotalPop"):
            print "--------CreateHouseholds_LowHighIncome_TotalPop, " + str(datetime.now().strftime('%H:%M:%S'))

            NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
            compute_matrix = _modeller.Modeller().tool(NAMESPACE)

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

            spec_as_dict["expression"] = "mo365' + mo366' + mo367' + mo368'"
            spec_as_dict["result"] = "md24"
            report = compute_matrix(spec_as_dict)

            spec_as_dict["expression"] = "mo369' + mo370' + mo371' + mo372'"
            spec_as_dict["result"] = "md25"
            report = compute_matrix(spec_as_dict)

            spec_as_dict["expression"] = "mo373' + mo374' + mo375' + mo376'"
            spec_as_dict["result"] = "md26"
            report = compute_matrix(spec_as_dict)

            spec_as_dict["expression"] = "mo20'"
            spec_as_dict["result"] = "md20"
            report = compute_matrix(spec_as_dict)

            spec_as_dict["expression"] = "mo27'"
            spec_as_dict["result"] = "md27"
            report = compute_matrix(spec_as_dict)

            spec_as_dict["expression"] = "mo28'"
            spec_as_dict["result"] = "md28"
            report = compute_matrix(spec_as_dict)

            spec_as_dict["expression"] = "mo13'"
            spec_as_dict["result"] = "md13"
            report = compute_matrix(spec_as_dict)

            spec_as_dict["expression"] = "mo17'"
            spec_as_dict["result"] = "md17"
            report = compute_matrix(spec_as_dict)

            spec_as_dict["expression"] = "mo29'"
            spec_as_dict["result"] = "md29"
            report = compute_matrix(spec_as_dict)

        ##    Batches in the batchin file

    def Matrix_Batchins(self, PathHeader):
        with _modeller.logbook_trace("Matrix Batchin"):
            print "--------Matrix_Batchins, " + str(datetime.now().strftime('%H:%M:%S'))
            ##        Sets up the 'matrix transaction' tool and runs it
            NAMESPACE = "inro.emme.data.matrix.matrix_transaction"
            process = _modeller.Modeller().tool(NAMESPACE)
            matrix_file = PathHeader + "03_TRIP_ATTRACTIONS/Inputs/MatrixTransactionFile.txt"

            ##        Creates process transaction
            process(transaction_file=matrix_file,
                    throw_on_error=True,
                    scenario=_modeller.Modeller().scenario)
