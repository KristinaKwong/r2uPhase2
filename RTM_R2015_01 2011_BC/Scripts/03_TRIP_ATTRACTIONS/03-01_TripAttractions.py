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

import inro.modeller as _m
import csv
import os
import traceback as _traceback
from collections import defaultdict


class TripAttractions(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self, title="Trip Attractions",
                                       description="Collects trip rates and land use to output trip Attractions. <br> Then saves it to the databank and outputs data",
                                       branding_text="TransLink")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)
        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            eb = _m.Modeller().emmebank
            self.__call__(eb)
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("03-01 - Trip Attractions")
    def __call__(self, eb):
        PathHeader = os.path.dirname(eb.path) + "\\"
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
        self.Output_Results(eb, OutputFile, CoefficientsPerGrouping, GroupingsPerPurpose)

        ## Export Matrices to CSV
        self.Export_Matrices(OutputFile)

    #Export all mo matrices to CSV
    @_m.logbook_trace("Export_Matrices")
    def Export_Matrices(self, OutputFile):
        ExportToCSV = _m.Modeller().tool("translink.emme.stage4.step9.exporttocsv")
        list_of_matrices = ["md" + str(i) for i in range(5, 12) + range(20, 27) + range(31, 42)]
        ExportToCSV(list_of_matrices, OutputFile)

        ##    Outputs results matrix to a file

    @_m.logbook_trace("Output Results")
    def Output_Results(self, eb, OutputFile, CoefficientsPerGrouping, GroupingsPerPurpose):
        Output_File = OutputFile.replace(",", "")
        Output_File_GY = OutputFile.replace(",", "").replace(".", "_GY.")
        Output_File_GU = OutputFile.replace(",", "").replace(".", "_GU.")

        ##    List to hold matrix objects
        md_value = []

        ##    Loop to append all result matrices onto the variable 'md_value'
        for mo_num in [24, 25, 26] + range(31, 42):
            md_value.append(eb.matrix("md" + str(mo_num)))

        ##    Export matrices using the appended list of md_value matrices
        export_matrices = _m.Modeller().tool("inro.emme.data.matrix.export_matrices")

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
            f.write("c " + CoefficientsPerGrouping + "\n")
            f.write("c " + GroupingsPerPurpose + "\n")
            f.close()

    ## md31-md41 Remove negative values from Trip Rates
    @_m.logbook_trace("Check_forNegatives")
    def Check_forNegatives(self):
        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

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

    @_m.logbook_trace("Calculate_TripRates")
    def Calculate_TripRates(self, coefficients_data, groupings_per_purpose, PathHeader):
        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

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

    @_m.logbook_trace("Store Store_Groupings")
    def Store_Groupings(self, GroupingsPerPurpose):
        with open(GroupingsPerPurpose, 'rb') as f:
            reader = csv.reader(f, dialect='excel')
            header = reader.next()
            data = [header]
            for row in reader:
                data.append(row)
                #dict_data = dict( (data[i][0],data[i][1:]) for i in range(0,len(data)))
        return data

    @_m.logbook_trace("Store_Coefficients")
    def Store_Coefficients(self, CoefficientsPerGrouping):
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
    @_m.logbook_trace("CreateHouseholds_LowHighIncome_TotalPop")
    def CreateHouseholds_LowHighIncome_TotalPop(self):
        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

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

    @_m.logbook_trace("Matrix Batchin")
    def Matrix_Batchins(self, PathHeader):
        process = _m.Modeller().tool("inro.emme.data.matrix.matrix_transaction")
        matrix_file = PathHeader + "03_TRIP_ATTRACTIONS/Inputs/MatrixTransactionFile.txt"

        ##        Creates process transaction
        process(transaction_file=matrix_file,
                throw_on_error=True,
                scenario=_m.Modeller().scenario)
