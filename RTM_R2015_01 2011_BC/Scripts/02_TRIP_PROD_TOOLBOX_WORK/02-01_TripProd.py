##--------------------------------------------------
##--TransLink Phase 2 Regional Transportation Model - HDR
##--02-01_TripProd.PY
##--Path: translink.emme.tripproduction
##--Purpose of 02-01_TripProd: develop production totals for RTM generation model
##--------------------------------------------------
##--Last modified 2014-02-14 Kevin Bragg (INRO)
##--Reason: Update to Emme 4.0 namespaces
##          Code cleanup PEP 8 compliance
##--Last modified 2013-09-03 Rhys Wolff (HDR)
##--Last modification reason - add comments and notes
##---------------------------------------------------
##--Called by: 00_00_RUN_ALL.PY
##--Calls:     None
##--Accesses:  21_TripRates_ALLPURPOSES.csv, 22_CalibFactors.csv, MatrixTransactionFile.txt
##--Outputs: 02-01_OUTPUT_FILE.txt
##---------------------------------------------------
##--Status/additional notes:
##--Supersedes all earlier versions of 02-01_TripProd
##---------------------------------------------------

import inro.modeller as _m
import csv
import os
import traceback as _traceback
from datetime import datetime


class TripProd(_m.Tool()):
    ##Modify path for new package implementation

    ##Create global attributes (referring to dialogue boxes on the pages)
    TripRateFile = _m.Attribute(_m.InstanceType)
    CalibrationFactors = _m.Attribute(_m.InstanceType)
    OutputFile = _m.Attribute(_m.InstanceType)
    last_mo_num = _m.Attribute(int) ##Last inputted MO number
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        start_path = os.path.dirname(_m.Modeller().emmebank.path)
        pb = _m.ToolPageBuilder(self, title="Trip Production",
                                       description="Collects trip rates and land use to output trip productions. <br> Then saves it to the databank and outputs data",
                                       branding_text="TransLink")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)
        return pb.render()

    def run(self):
        print "--------02-01 - RUN - TRIP PRODUCTIONS: " + str(datetime.now().strftime('%H:%M:%S'))
        self.tool_run_msg = ""
        try:
            self.__call__()
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    def __call__(self, PathHeader):
        with _m.logbook_trace("02-01 - Trip Production"):
            print "----02-01 - Trip Production: " + str(datetime.now().strftime('%H:%M:%S'))
            TripRateFile = PathHeader + "02_TRIP_PROD_TOOLBOX_WORK/Inputs/21_TripRates_ALLPURPOSES.csv"
            CalibrationFactors = PathHeader + "02_TRIP_PROD_TOOLBOX_WORK/Inputs/22_CalibFactors.csv"
            OutputFile = PathHeader + "02_TRIP_PROD_TOOLBOX_WORK/Outputs/02-01_OUTPUT_FILE.txt"
            FirstResultMoNum = "404"

            self.Matrix_Batchins(PathHeader)

            ##            All the trip rates are read in and stored inthis 'TripRate_Data'
            TripRate_Data = self.Store_TripRates(TripRateFile)

            Calibration_Factors = self.Store_CalibrationFactors(CalibrationFactors)

            ##            mo404-mo835 - Run Trip Production
            self.TripProduction(TripRate_Data, FirstResultMoNum)

            ##            mo404-835 - Update
            self.Calibration(Calibration_Factors)

            ## mo836-mo898 - Aggregation of production to income-ownership splits for each purpose
            self.Aggregation()

            ## mo161-mo268 - Aggregation of production to Income-Ownership splits for each purpose
            self.Aggregation_IncomeOwnership()

            ##mo899-mo903 - Calculate total number of auto
            self.CalculateNumAutos()

            ##mo904-mo914 - Calculate total number of auto
            self.Aggregate_Purposes()

            ##            Output these new result files
            self.Output_Results(OutputFile, FirstResultMoNum, TripRateFile, CalibrationFactors)

            ## Export Matrices to CSV
            self.Export_Matrices(OutputFile)

    #Export all mo matrices to CSV
    def Export_Matrices(self, OutputFile):
        with _m.logbook_trace("Export_Matrices"):
            print "--------Export_Matrices, " + str(datetime.now().strftime('%H:%M:%S'))
            ExportToCSV = _m.Modeller().tool("translink.emme.stage4.step9.exporttocsv")
            list_of_matrices = ["mo" + str(i) for i in range(161, 365) + range(404, 915)]
            ExportToCSV(list_of_matrices, OutputFile)

    ##    Outputs results matrix to a file
    def Output_Results(self, OutputFile, FirstResultMoNum, TripRateFile, CalibrationFactors):
        with _m.logbook_trace("Output Results"):
            print "--------Output_Results, " + str(datetime.now().strftime('%H:%M:%S'))

            ##    Create emmebank object
            my_modeller = _m.Modeller()
            my_emmebank = my_modeller.desktop.data_explorer().active_database().core_emmebank

            Output_File = OutputFile.replace(",", "")
            Output_File_GY = OutputFile.replace(",", "").replace(".", "_GY.")
            Output_File_GU = OutputFile.replace(",", "").replace(".", "_GU.")

            ##    List to hold matrix objects
            mo_value = []

            for i in range(161, 269):
                mo_value.append(my_emmebank.matrix("mo" + str(i)))

            ##    Two loops to append all result matrices onto the variable 'mo_value'
            for purpose_index in range(1, 10):
                mo_result_num = int(FirstResultMoNum) + (purpose_index - 1) * (96 / 2)
                for mo_num in range(0, 96 / 2):
                    mo_value.append(my_emmebank.matrix("mo" + str(mo_num + mo_result_num)))

            for i in range(899, 915):
                mo_value.append(my_emmebank.matrix("mo" + str(i)))


            ##    Export matrices using the appended list of mo_value matrices
            NAMESPACE = "inro.emme.data.matrix.export_matrices"
            export_matrices = _m.Modeller().tool(NAMESPACE)
            export_matrices_gy = _m.Modeller().tool(NAMESPACE)

            export_matrices(export_file=Output_File,
                            field_separator=' ',
                            matrices=mo_value,
                            export_format="PROMPT_DATA_FORMAT",
                            skip_default_values=True,
                            full_matrix_line_format="ONE_ENTRY_PER_LINE")

            ## Export matrix data aggregated to the gy ensemble
            export_matrices_gy(export_file=Output_File_GY,
                               field_separator=' ',
                               matrices=mo_value,
                               partition_aggregation={'origins': 'gy', 'operator': 'sum'},
                               export_format="PROMPT_DATA_FORMAT",
                               skip_default_values=True,
                               full_matrix_line_format="ONE_ENTRY_PER_LINE")

            ## Export matrix data aggregated to the gu ensemble
            export_matrices_gy(export_file=Output_File_GU,
                               field_separator=' ',
                               matrices=mo_value,
                               partition_aggregation={'origins': 'gu', 'operator': 'sum'},
                               export_format="PROMPT_DATA_FORMAT",
                               skip_default_values=True,
                               full_matrix_line_format="ONE_ENTRY_PER_LINE")

            for Output in [Output_File, Output_File_GY, Output_File_GU]:
                f = open(Output, 'a')
                f.write("c ------Data Sources:\n")
                f.write("c " + TripRateFile + "\n")
                f.write("c " + CalibrationFactors + "\n")
                f.write("c " + OutputFile + "\n")
                f.close()


            ##    Open up window with the OutputFile Selected
            print "----------------OutputFile: ", Output_File
            #subprocess.Popen(r'explorer /select, ' + OutputFile.replace("/","\\").replace(",","") + '"')

    def Aggregate_Purposes(self):
        with _m.logbook_trace("Aggregate_Purposes"):
            print "--------Aggregate_Purposes, " + str(datetime.now().strftime('%H:%M:%S'))
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

            mo_result_num = 904
            for i in range(0, 3):
                x = i + 161
                expression = "mo" + str(x) + " + mo" + str(x + 3) + " + mo" + str(x + 6) + " + mo" + str(x + 9)
                spec_as_dict["expression"] = expression
                spec_as_dict["result"] = "mo" + str(mo_result_num)
                report = compute_matrix(spec_as_dict)
                mo_result_num = mo_result_num + 1

            for i in range(173, 268, 12):
                expression = "0"
                for x in range(0, 12):
                    expression = expression + " + mo" + str(x + i)
                spec_as_dict["expression"] = expression
                spec_as_dict["result"] = "mo" + str(mo_result_num)
                #print str(mo_result_num) + expression
                report = compute_matrix(spec_as_dict)
                mo_result_num = mo_result_num + 1

    ##mo899-mo903 - Calculate total number of auto
    def CalculateNumAutos(self):
        with _m.logbook_trace("CalculateNumAutos"):
            print "--------CalculateNumAutos, " + str(datetime.now().strftime('%H:%M:%S'))
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

            mo_result_num = 899
            expression = "mo269"
            for i in range(270, 281):
                expression = expression + " + mo" + str(i)
            spec_as_dict["expression"] = expression
            spec_as_dict["result"] = "mo" + str(mo_result_num)
            report = compute_matrix(spec_as_dict)

            mo_result_num = 900
            expression = "mo281"
            for i in range(282, 293):
                expression = expression + " + mo" + str(i)
            spec_as_dict["expression"] = expression
            spec_as_dict["result"] = "mo" + str(mo_result_num)
            report = compute_matrix(spec_as_dict)

            mo_result_num = 901
            expression = "mo293"
            for i in range(294, 305):
                expression = expression + " + mo" + str(i)
            spec_as_dict["expression"] = expression
            spec_as_dict["result"] = "mo" + str(mo_result_num)
            report = compute_matrix(spec_as_dict)

            mo_result_num = 902
            expression = "mo305"
            for i in range(306, 317):
                expression = expression + " + mo" + str(i)
            spec_as_dict["expression"] = expression
            spec_as_dict["result"] = "mo" + str(mo_result_num)
            report = compute_matrix(spec_as_dict)

            mo_result_num = 903
            spec_as_dict["expression"] = "mo900 + 2*mo901 + 3.35*mo902"
            spec_as_dict["result"] = "mo" + str(mo_result_num)
            report = compute_matrix(spec_as_dict)

    ##mo161-268 - Aggregate Income Auto Ownership
    def Aggregation_IncomeOwnership(self):
        with _m.logbook_trace("Aggregation_IncomeOwnership"):
            print "--------Aggregation_IncomeOwnership, " + str(datetime.now().strftime('%H:%M:%S'))

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

            mo_result_num = 161
            for mo_num in range(404, 836, 4):
                expression = "mo" + str(mo_num) + \
                             " + mo" + str(mo_num + 1) + \
                             " + mo" + str(mo_num + 2) + \
                             " + mo" + str(mo_num + 3)
                spec_as_dict["expression"] = expression
                spec_as_dict["result"] = "mo" + str(mo_result_num)
                report = compute_matrix(spec_as_dict)
                mo_result_num = mo_result_num + 1

    ## mo836-mo898 - Aggregation of production to income-ownership splits for each purpose
    def Aggregation(self):
        with _m.logbook_trace("Aggregation"):
            print "--------Aggregation, " + str(datetime.now().strftime('%H:%M:%S'))
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

            ## mo836-mo871 - Purpose x AutoOwnership
            mo_result_num = 836
            for mo_num in range(404, 836, 12):
                expression = "0"
                for x in range(0, 12):
                    expression = expression + "+ mo" + str(mo_num + x)
                spec_as_dict["expression"] = expression
                spec_as_dict["result"] = "mo" + str(mo_result_num)
                mo_result_num = mo_result_num + 1
                report = compute_matrix(spec_as_dict)

            ## mo872-mo898 - Purpose x IncomeCategory
            for mo_num in range(404, 836, 48):
                for i in range(0, 12, 4):
                    expression = "mo" + str(mo_num + i) + \
                                 " + mo" + str(mo_num + i + 1) + \
                                 " + mo" + str(mo_num + i + 2) + \
                                 " + mo" + str(mo_num + i + 3) + \
                                 " + mo" + str(mo_num + i + 12) + \
                                 " + mo" + str(mo_num + i + 13) + \
                                 " + mo" + str(mo_num + i + 14) + \
                                 " + mo" + str(mo_num + i + 15) + \
                                 " + mo" + str(mo_num + i + 24) + \
                                 " + mo" + str(mo_num + i + 25) + \
                                 " + mo" + str(mo_num + i + 26) + \
                                 " + mo" + str(mo_num + i + 27) + \
                                 " + mo" + str(mo_num + i + 36) + \
                                 " + mo" + str(mo_num + i + 37) + \
                                 " + mo" + str(mo_num + i + 38) + \
                                 " + mo" + str(mo_num + i + 39)
                    spec_as_dict["expression"] = expression
                    spec_as_dict["result"] = "mo" + str(mo_result_num)
                    mo_result_num = mo_result_num + 1
                    report = compute_matrix(spec_as_dict)

    def Calibration(self, Calibration_Factors):
        with _m.logbook_trace("Calibration"):
            print "--------Calibration, " + str(datetime.now().strftime('%H:%M:%S'))
            NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
            compute_matrix = _m.Modeller().tool(NAMESPACE)

            ##    Create specs for matrix
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
            for i in range(1, 432):
                expression = "0"
                for x in range(1, 15):
                    expression = expression + " + (mo29.eq." + str(x) + ")*" + Calibration_Factors[i][x + 5]
                expression = "mo" + str(403 + i) + "*(" + expression + ")"
                result = "mo" + str(403 + i)
                #if (403 + i) < 549: print "result: " + result + " : " + expression
                spec_as_dict["expression"] = expression
                spec_as_dict["result"] = result
                report = compute_matrix(spec_as_dict)

    ##  mo404-mo835 Performs the actual matrix calculation from the LandUse 'mo's with the TripRates for the various trip purposes
    def TripProduction(self, TripRate_Data, FirstResultMoNum):
        with _m.logbook_trace("Perform Matrix calculations"):
            print "--------TripProduction, " + str(datetime.now().strftime('%H:%M:%S'))
            NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
            compute_matrix = _m.Modeller().tool(NAMESPACE)

            ##            Create specs for matrix
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

            ## Loop to do the expression calculations
            for purpose_index in range(1, 10):
                mo_result_num = int(FirstResultMoNum) + (purpose_index - 1) * (96 / 2)
                if purpose_index <= 2:
                    start_mo = (96 / 2) + 269
                    shift_value = 0
                else:
                    start_mo = 269
                    shift_value = 48

                for mo_num in range(start_mo, ((96 / 2) + start_mo)):
                    expression = "mo" + str(mo_num) + "*" + str(
                        TripRate_Data[mo_num - start_mo + 1 + shift_value][purpose_index + 3])
                    result = "mo" + str(mo_result_num)
                    spec_as_dict["expression"] = expression
                    spec_as_dict["result"] = result
                    #print "initial result: " + result + " : " + expression
                    report = compute_matrix(spec_as_dict)
                    mo_result_num = mo_result_num + 1

    def Store_CalibrationFactors(self, CalibrationFactors):
        with _m.logbook_trace("Store_CalibrationFactors"):
            print "--------Store_CalibrationFactors, " + str(datetime.now().strftime('%H:%M:%S'))
            with open(CalibrationFactors, 'rb') as f:
                reader = csv.reader(f, dialect='excel')
                header = reader.next()
                data = [header]
                for row in reader:
                    data.append(row)
        return data

    ##    Stores the triprates into a data structure and return it
    def Store_TripRates(self, TripRateFile):
        with _m.logbook_trace("Store_TripRates"):
            print "--------Store_TripRates, " + str(datetime.now().strftime('%H:%M:%S'))
            with open(TripRateFile, 'rb') as f:
                reader = csv.reader(f, dialect='excel')
                header = reader.next()
                data = [header]
                for row in reader:
                    data.append(row)
        return data

    ##    Batches in the batchin file
    def Matrix_Batchins(self, PathHeader):
        with _m.logbook_trace("Matrix Batchin"):
            print "--------Matrix_Batchins, " + str(datetime.now().strftime('%H:%M:%S'))
            ##        Sets up the 'matrix transaction' tool and runs it
            NAMESPACE = "inro.emme.data.matrix.matrix_transaction"
            process = _m.Modeller().tool(NAMESPACE)
            matrix_file = PathHeader + "02_TRIP_PROD_TOOLBOX_WORK/Inputs/MatrixTransactionFile.txt"

            ##        Creates process transaction
            process(transaction_file=matrix_file,
                    throw_on_error=True,
                    scenario=_m.Modeller().scenario)
