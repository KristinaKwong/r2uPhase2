##--------------------------------------------------
##--TransLink Phase 2 Regional Transportation Model
##--01-01_SocioEconomicSegmentation.PY
##--Path: translink.emme.segmentation
##--Purpose of 01-01_SocioEconomicSegmentation:
##--------------------------------------------------
##--Last modified 2014-02-14 Kevin Bragg (INRO)
##--Reason: Update to Emme 4.0 namespaces
##          Code cleanup PEP 8 compliance
##--Last modified 2013-11-05 Rhys Wolff (HDR)
##--Last modification reason - add  parkcost flag
##--Add parking cost call
##---------------------------------------------------
##--Called by: 00_00_RUN_ALL
##--Calls:     01-02AutoOwnership 01-03ParkingCost
##--Accesses:  Auto ownership toolbox CSV files
##--Outputs: Auto ownership toolbox txt files
##---------------------------------------------------
##--Status/additional notes:
##--Supersedes all earlier versions of 01-01_SocioEconomicSegmentation.PY
##---------------------------------------------------


import inro.modeller as _modeller
import csv
import os
import traceback as _traceback

from datetime import datetime


class SocioEconomicSegmentation(_modeller.Tool()):
    ##Create global attributes (referring to dialogue boxes on the pages)

    ##Global attribute for Tool Run Message (successful/not successful)
    tool_run_msg = _modeller.Attribute(unicode)

    def page(self):
        start_path = os.path.dirname(_modeller.Modeller().emmebank.path)
        ##Create various aspects to the page
        pb = _modeller.ToolPageBuilder(self, title="Socio-economic Segmentation",
                                       description="Collects Households Numbers, Workers Numbers, "
                                                   "Income and Auto Ownership Data and provides "
                                                   "various segmentation for use in Trip Production.",
                                       branding_text=" TransLink")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        print "--------01-01 - RUN - SOCIOECONOMIC SEGMENTATION: " + str(datetime.now().strftime('%H:%M:%S'))
        self.tool_run_msg = ""
        try:
            self.__call__()
            run_msg = "Tool completed"
            self.tool_run_msg = _modeller.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _modeller.PageBuilder.format_exception(e, _traceback.format_exc(e))


    def __call__(self, PathHeader):
    ##        Start logging this under a new 'nest'
        with _modeller.logbook_trace("01-01 - Socio Economic Segmentation"):
            print "----01-01 - Socio Economic Segmentation: " + str(datetime.now().strftime('%H:%M:%S'))

            HHWorkerRate = PathHeader + "01_SOCIOECON-SEG_AUTOOWN_TOOLBOX_WORK/Inputs/12_HH_Worker_Rates.csv"
            OutputFile = PathHeader + "01_SOCIOECON-SEG_AUTOOWN_TOOLBOX_WORK/Outputs/01-01_OUTPUT_RESULTS.txt"
            IncomeData = PathHeader + "01_SOCIOECON-SEG_AUTOOWN_TOOLBOX_WORK/Inputs/13_HHWrkrIncome.csv"
            AutoOwnershipCoefficients = PathHeader + "01_SOCIOECON-SEG_AUTOOWN_TOOLBOX_WORK/Inputs/14_AutoOwnershipCoefficients.csv"
            ##Batchin File
            self.Matrix_Batchins(PathHeader)

            ## Calculate adjusted parking costs
            #Check for flag to run parking cost or otherwise

            eb = _modeller.Modeller().emmebank
            parkcost = eb.matrix("ms144").data
            if (parkcost == 1):
                ParkingCost = _modeller.Modeller().tool("translink.emme.stage1.step1.parkingcost")
                ParkingCost()

            ##Create mo16, mo18 from existing matrices
            self.InitialMatrixCalculations()

            ##Store HHData
            HHData = self.Store_TripRates(HHWorkerRate)

            ##Store IncomeData
            IncData = self.Store_IncomeData(IncomeData)

            ##Store Auto Ownership Coefficients
            AutoOwnCoeff = self.Store_AutoOwnCoeff(AutoOwnershipCoefficients)

            ##Calculate Number workers matrices - mo54-57, mo58
            self.Calculate_Workers(HHData)

            ##Calculate Number of Households Per Worker category - mo61-73
            self.Calculate_WorkersHousehold(HHData)

            ## Calculated Number of Households Per Worker Cateogry and Per Income Category - mo74-mo112
            self.Calculate_IncomeWorkersHousehold(IncData)

            ## Calculated Number of Households Per Worker, Per Income and Per Auto Ownership Category - mo113-mo268
            AutoOwnership = _modeller.Modeller().module("translink.emme.stage1.step1.autoownership")

            ## mo404-mo442 - Store utility value while for AutoOwn=0 for various HHSize, NumWorkers, IncomeCat
            AutoOwnership.Calculate_AutoOwnership_0Cars(self, AutoOwnCoeff)
            ## mo443-mo481 - Store utility value while for AutoOwn=1 for various HHSize, NumWorkers, IncomeCat
            AutoOwnership.Calculate_AutoOwnership_1Cars(self, AutoOwnCoeff)
            ## mo482-mo520 - Store utility value while for AutoOwn=2 for various HHSize, NumWorkers, IncomeCat
            AutoOwnership.Calculate_AutoOwnership_2Cars(self, AutoOwnCoeff)
            ## mo521-mo559 - Store utility value while for AutoOwn=3 for various HHSize, NumWorkers, IncomeCat
            AutoOwnership.Calculate_AutoOwnership_3Cars(self, AutoOwnCoeff)

            ## mo560-mo715 - Calculated probabilities of having a AutoOwnership0-3 for HHSize, NumWorkers, IncomeCat
            AutoOwnership.Calculate_Probabilities(self, AutoOwnCoeff)

            ## mo113-mo268 - Calculated Number of Households Per Worker, Per Income and Per Auto Ownership Category
            AutoOwnership.Calculate_AutoOwnership_PerHH(self)

            ## mo269-mo364 - Aggregate Non-Workers
            self.Aggregate_NonWorkers_and_Workers()

            ## mo365-mo388 - Aggregate Income Categories
            self.Aggregate_IncomeCategories()

            ## mo389-mo391 - Aggregate Num Workers in each Income Category
            self.Aggregate_NumWorkerIncomeCategories()

            ## mo716-mo718 - Calculated Number of Auto Per HH Size
            AutoOwnership.Autos_PerHHSize(self)

            # Output number of worker matrices
            self.Output_Results(OutputFile, HHWorkerRate, IncomeData, AutoOwnershipCoefficients)

            ## Export Matrices to CSV
            self.Export_Matrices(OutputFile)

    #Export all mo matrices to CSV
    def Export_Matrices(self, OutputFile):
        with _modeller.logbook_trace("Export_Matrices"):
            print "--------Export_Matrices, " + str(datetime.now().strftime('%H:%M:%S'))
            ExportToCSV = _modeller.Modeller().tool("translink.emme.stage4.step9.exporttocsv")
            list_of_matrices = ["mo" + str(i) for i in [1] + range(16, 21) + range(50, 60) + range(61, 398) + range(404, 716)]
            ExportToCSV(list_of_matrices, OutputFile)

        ##    Outputs results matrix to a file

    def Output_Results(self, OutputFile, HHWorkerRate, IncomeData, AutoOwnershipCoefficients):
        with _modeller.logbook_trace("Output Results"):
			print "--------Output_Results, " + str(datetime.now())
			##    Create emmebank object
			my_modeller = _modeller.Modeller()
			my_emmebank = my_modeller.desktop.data_explorer().active_database().core_emmebank

			Output_File = OutputFile.replace(",", "")
			Output_File_GY = OutputFile.replace(",", "").replace(".", "_GY.")
			Output_File_GU = OutputFile.replace(",", "").replace(".", "_GU.")
			# TODO: the replace(".", ...) means that the directory cannot have a "."
			#       in the path....

			##    List to hold matrix objects
			mo_value = []

			##    Loop to append all result matrices onto the variable 'mo_value'
			for mo_num in range(54, 59):
				mo_value.append(my_emmebank.matrix("mo" + str(mo_num)))

			for mo_num in range(61, 74):
				mo_value.append(my_emmebank.matrix("mo" + str(mo_num)))

			for mo_num in range(74, 113):
				mo_value.append(my_emmebank.matrix("mo" + str(mo_num)))

			for mo_num in range(113, 269):
				mo_value.append(my_emmebank.matrix("mo" + str(mo_num)))

			for mo_num in range(269, 389):
				mo_value.append(my_emmebank.matrix("mo" + str(mo_num)))

			for mo_num in range(389, 392):
				mo_value.append(my_emmebank.matrix("mo" + str(mo_num)))

			for mo_num in range(392, 398):
				mo_value.append(my_emmebank.matrix("mo" + str(mo_num)))
				
			for mo_num in range(404, 560):
				mo_value.append(my_emmebank.matrix("mo" + str(mo_num)))
				
			for mo_num in range(560, 716):
				mo_value.append(my_emmebank.matrix("mo" + str(mo_num)))

			for mo_num in range(716, 719):
				mo_value.append(my_emmebank.matrix("mo" + str(mo_num)))

			##    Export matrices using the appended list of mo_value matrices
			export_matrices = _modeller.Modeller().tool(
				"inro.emme.data.matrix.export_matrices")

			## Export all matrix data
			export_matrices(export_file=Output_File,
							field_separator=' ',
							matrices=mo_value,
							export_format="PROMPT_DATA_FORMAT",
							skip_default_values=True,
							full_matrix_line_format="ONE_ENTRY_PER_LINE")

			## Export matrix data aggregated to the gy ensemble
			export_matrices(export_file=Output_File_GY,
							field_separator=' ',
							matrices=mo_value,
							partition_aggregation={'origins': 'gy', 'operator': 'sum'},
							export_format="PROMPT_DATA_FORMAT",
							skip_default_values=True,
							full_matrix_line_format="ONE_ENTRY_PER_LINE")

			## Export matrix data aggregated to the gu ensemble
			export_matrices(export_file=Output_File_GU,
							field_separator=' ',
							matrices=mo_value,
							partition_aggregation={'origins': 'gu', 'operator': 'sum'},
							export_format="PROMPT_DATA_FORMAT",
							skip_default_values=True,
							full_matrix_line_format="ONE_ENTRY_PER_LINE")

			for Output in [Output_File, Output_File_GY, Output_File_GU]:
				f = open(Output, 'a')
				f.write("c ------Data Sources:\n")
				f.write("c " + HHWorkerRate + "\n")
				f.write("c " + IncomeData + "\n")
				f.write("c " + AutoOwnershipCoefficients + "\n")
				f.close()

				##    Open up window with the OutputFile Selected
				##print "----------------OutputFile: ", Output_File
				##subprocess.Popen(r'explorer /select, ' + OutputFile.replace("/","\\").replace(",","") + '"')

			##     mo389-mo391 - Aggregate Num Workers in each Income Category

    def Aggregate_NumWorkerIncomeCategories(self):
        with _modeller.logbook_trace("Aggregate Number of Worker Income Categories"):
            print "--------Aggregate Number of Worker Income Categories, " + str(datetime.now().strftime('%H:%M:%S'))
            NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
            compute_matrix = _modeller.Modeller().tool(NAMESPACE)

            spec_as_dict = {
                "expression": "EXPRESSION",
                "result": "RESULT",
                "constraint": {
                    "by_value": None,
                    "by_zone": {
                        "origins": None,
                        "destinations": None
                    }
                },
                "aggregation": {
                    "origins": None,
                    "destinations": None
                },
                "type": "MATRIX_CALCULATION"
            }

            result_mo_num = 389
            for count in range(377, 388, 4):
                spec_as_dict["expression"] = "mo" + str(count + 0) + "*0 +" + "mo" + str(
                    count + 1) + "*1 +" + "mo" + str(count + 2) + "*2 +" + "mo" + str(count + 3) + "*mo58"
                spec_as_dict["result"] = "mo" + str(result_mo_num)
                #                print "mo"+str(count+0) + "*0 +" + "mo"+str(count+1) + "*1 +" + "mo"+str(count+2) + "*2 +" + "mo"+str(count+3) + "*mo58"
                #                print "mo"+str(result_mo_num)
                ##Outputs Matrices: mo389-mo391. Income Cat x Num Workers
                report = compute_matrix(spec_as_dict)
                result_mo_num = result_mo_num + 1

            ##    mo365-mo388 - Aggregate Income Categories

    def Aggregate_IncomeCategories(self):
        with _modeller.logbook_trace("Aggregate Income Categories"):
            print "--------Aggregate Income Categories, " + str(datetime.now().strftime('%H:%M:%S'))
            NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
            compute_matrix = _modeller.Modeller().tool(NAMESPACE)

            spec_as_dict = {
                "expression": "EXPRESSION",
                "result": "RESULT",
                "constraint": {
                    "by_value": None,
                    "by_zone": {
                        "origins": None,
                        "destinations": None
                    }
                },
                "aggregation": {
                    "origins": None,
                    "destinations": None
                },
                "type": "MATRIX_CALCULATION"
            }

            start_mo_num = 73
            result_mo_num = 365

            ## create additional columns to add household size and income categories
            hh_expression = []
            for count in range(start_mo_num, 112, 13):
                hh_expression = ["mo" + str(1 + count) + " + mo" + str(2 + count),
                                 "mo" + str(3 + count) + " + mo" + str(4 + count) + " + mo" + str(5 + count),
                                 "mo" + str(6 + count) + " + mo" + str(7 + count) + " + mo" + str(
                                     8 + count) + " + mo" + str(9 + count),
                                 "mo" + str(10 + count) + " + mo" + str(11 + count) + " + mo" + str(
                                     12 + count) + " + mo" + str(13 + count)
                ]
                for hh_ex in hh_expression:
                    spec_as_dict["expression"] = hh_ex
                    spec_as_dict["result"] = "mo" + str(result_mo_num)

                    ##Outputs Matrices: mo365-mo376. HHSize x Income
                    report = compute_matrix(spec_as_dict)
                    result_mo_num = result_mo_num + 1

            ## create additional columns to add worker number and income categories
            wk_expression = []
            for count in range(start_mo_num, 112, 13):
                wk_expression = [
                    "mo" + str(1 + count) + " + mo" + str(3 + count) + " + mo" + str(6 + count) + " + mo" + str(
                        10 + count),
                    "mo" + str(2 + count) + " + mo" + str(4 + count) + " + mo" + str(7 + count) + " + mo" + str(
                        11 + count),
                    "mo" + str(5 + count) + " + mo" + str(8 + count) + " + mo" + str(12 + count),
                    "mo" + str(9 + count) + " + mo" + str(13 + count)
                ]
                for wk_ex in wk_expression:
                    spec_as_dict["expression"] = wk_ex
                    spec_as_dict["result"] = "mo" + str(result_mo_num)

                    ##Outputs Matrices: mo377-mo388. NumWorkers x Income
                    report = compute_matrix(spec_as_dict)
                    result_mo_num = result_mo_num + 1

                ##     mo269-mo364 - Aggregate Non-Workers

    def Aggregate_NonWorkers_and_Workers(self):
        with _modeller.logbook_trace("Aggregate NonWorkers and Workers"):
            print "--------Aggregate NonWorkers and Workers, " + str(datetime.now().strftime('%H:%M:%S'))
            NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
            compute_matrix = _modeller.Modeller().tool(NAMESPACE)

            spec_as_dict = {
                "expression": "EXPRESSION",
                "result": "RESULT",
                "constraint": {
                    "by_value": None,
                    "by_zone": {
                        "origins": None,
                        "destinations": None
                    }
                },
                "aggregation": {
                    "origins": None,
                    "destinations": None
                },
                "type": "MATRIX_CALCULATION"
            }

            start_mo_num = 112
            result_mo_num = 269

            ## create additional columns to aggregate to Non-workers
            hh_expression = []
            for count in range(start_mo_num, 268, 13):
                hh_expression = ["mo" + str(1 + count) + " + mo" + str(2 + count),
                                 "mo" + str(3 + count) + " + mo" + str(4 + count) + " + mo" + str(5 + count),
                                 "mo" + str(6 + count) + " + mo" + str(7 + count) + " + mo" + str(
                                     8 + count) + " + mo" + str(9 + count),
                                 "mo" + str(10 + count) + " + mo" + str(11 + count) + " + mo" + str(
                                     12 + count) + " + mo" + str(13 + count)
                ]
                for hh_ex in hh_expression:
                    spec_as_dict["expression"] = hh_ex
                    spec_as_dict["result"] = "mo" + str(result_mo_num)
                    # print "mo"+str(result_mo_num) + " = " + hh_ex

                    ##Outputs Matrices: mo269-mo316. NonWorkers: HHSize x Income x AutoOwnership
                    report = compute_matrix(spec_as_dict)
                    result_mo_num = result_mo_num + 1

            ## create additional columns to aggregate to Workers
            wk_expression = []
            for count in range(start_mo_num, 268, 13):
                wk_expression = [
                    "mo" + str(1 + count) + " + mo" + str(3 + count) + " + mo" + str(6 + count) + " + mo" + str(
                        10 + count),
                    "mo" + str(2 + count) + " + mo" + str(4 + count) + " + mo" + str(7 + count) + " + mo" + str(
                        11 + count),
                    "mo" + str(5 + count) + " + mo" + str(8 + count) + " + mo" + str(12 + count),
                    "mo" + str(9 + count) + " + mo" + str(13 + count)
                ]
                for wk_ex in wk_expression:
                    spec_as_dict["expression"] = wk_ex
                    spec_as_dict["result"] = "mo" + str(result_mo_num)
                    # print "mo"+str(result_mo_num) + " = " + wk_ex

                    ##Outputs Matrices: mo317-mo364. Workers: NumWorkers x Income x AutoOwnership
                    report = compute_matrix(spec_as_dict)
                    result_mo_num = result_mo_num + 1

                ##     mo74-mo112 - Calculated Number of Households Per Worker Category and Per Income Category

    def Calculate_IncomeWorkersHousehold(self, IncomeData):
        with _modeller.logbook_trace("Calculate Number of Households Per Worker Category Per Income Category"):
            print "--------Calculate_IncomeWorkersHousehold, " + str(datetime.now().strftime('%H:%M:%S'))
            NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
            compute_matrix = _modeller.Modeller().tool(NAMESPACE)

            spec_as_dict = {
                "expression": "mo61*0.005",
                "result": "mo95",
                "constraint": {
                    "by_value": None,
                    "by_zone": {
                        "origins": "gu1",
                        "destinations": None
                    }
                },
                "aggregation": {
                    "origins": None,
                    "destinations": None
                },
                "type": "MATRIX_CALCULATION"
            }

            ##Two loops: Go through IncomeData and extract multipliers and multiplies by matrix for HHSize x WorkerNumber

            for inc_cat in range(3, 6):
                for row in range(1, IncomeData.__len__()):
                    spec_as_dict["expression"] = "mo" + str(((row - 1) % 13) + 61) + "*" + str(IncomeData[row][inc_cat])
                    spec_as_dict["result"] = "mo" + str(((row - 1) % 13) + 74 + (inc_cat - 3) * 13)
                    spec_as_dict["constraint"]["by_zone"]["origins"] = "gu" + str(IncomeData[row][0])

                    ##Outputs Matrices: mo74-mo112, HHSize x NumWorkers x Income
                    report = compute_matrix(spec_as_dict)

                ##     mo61-73 - Calculate Number of Households Per Worker category

    def Calculate_WorkersHousehold(self, HHData):
        with _modeller.logbook_trace("Calculate Number of Workers Per Household Category"):
            print "--------Calculate_WorkersHousehold, " + str(datetime.now().strftime('%H:%M:%S'))
            NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
            compute_matrix = _modeller.Modeller().tool(NAMESPACE)

            spec_as_dict2 = {
                "expression": "EXPRESSION",
                "result": "RESULT",
                "constraint": {
                    "by_value": {
                        "od_values": "mo18",
                        "interval_min": 0,
                        "interval_max": 0.2,
                        "condition": "INCLUDE"
                    },
                    "by_zone": {
                        "destinations": None,
                        "origins": "gu1"
                    }
                },
                "aggregation": {
                    "origins": None,
                    "destinations": None
                },
                "type": "MATRIX_CALCULATION"
            }

            ##    Dictionary for senior proportion lookup
            sr_prop_flag = {'0': "INCLUDE", '1': "EXCLUDE"}

            ##
            for count in range(1, HHData.__len__(), 4):
                mo_num = 0
                for hh in range(1, 5):
                    wkr = 0
                    while (hh >= wkr and wkr < 4):
                        spec_as_dict2["expression"] = "mo" + str(hh + 49) + "*" + HHData[count + hh - 1][wkr + 3]
                        spec_as_dict2["result"] = "mo" + str(mo_num + 61)
                        spec_as_dict2["constraint"]["by_value"]["condition"] = sr_prop_flag[HHData[count][1]]
                        spec_as_dict2["constraint"]["by_zone"]["origins"] = "gu" + str(HHData[count][0])

                        ## Output Matrices: mo61-73. Number of Households by workers
                        report = compute_matrix(spec_as_dict2)
                        wkr = wkr + 1
                        mo_num = mo_num + 1

                    ##    Calculate Number workers matrices - mo54-57, mo58, mo59

    def Calculate_Workers(self, HHData):
        with _modeller.logbook_trace("Calculate Number of Workers"):
            print "--------Calculate_Workers, " + str(datetime.now().strftime('%H:%M:%S'))
            NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
            compute_matrix = _modeller.Modeller().tool(NAMESPACE)

            ##Create specs for matrix calculation
            spec_as_dict = {
                "expression": "EXPRESSION",
                "result": "RESULT",
                "constraint": {
                    "by_value": {
                        "od_values": "mo18",
                        "interval_min": 0,
                        "interval_max": 0.2,
                        "condition": "INCLUDE"
                    },
                    "by_zone": {
                        "destinations": None,
                        "origins": "gu1"
                    }
                },
                "aggregation": {
                    "origins": None,
                    "destinations": None
                },
                "type": "MATRIX_CALCULATION"
            }



            ##    Dictionary for senior proprtion lookup - set senior proportion constraint
            ## 0 - less than 20% Sr. Proportion
            ## 1 - more than 20% Sr. Proportion
            sr_prop_flag = {'0': "INCLUDE", '1': "EXCLUDE"}

            for num_workers in range(0, 4):
                for count in range(1, HHData.__len__(), 4):
                    spec_as_dict["expression"] = "mo50*" + str(HHData[count + 0][num_workers + 3]) + " + mo51*" + str(
                        HHData[count + 1][num_workers + 3]) + " + mo52*" + str(
                        HHData[count + 2][num_workers + 3]) + " + mo53*" + str(HHData[count + 3][num_workers + 3])
                    spec_as_dict["result"] = "mo" + str(54 + num_workers)
                    spec_as_dict["constraint"]["by_value"]["condition"] = sr_prop_flag[
                        HHData[count][1]] ## include/exclude (less than sr. over sr.)
                    spec_as_dict["constraint"]["by_zone"]["origins"] = "gu" + str(HHData[count][0])

                    ##Output Matrix: mo54-57. Number of households with X number of workers.  (Where X=1,2,3,4)
                    report = compute_matrix(spec_as_dict)


            ## Create mo58 - 3+ worker adjustment factor
            num_workers = 4
            for count in range(1, HHData.__len__(), 4):
                spec_as_dict["expression"] = str(HHData[count + 0][num_workers + 3])
                spec_as_dict["result"] = "mo" + str(54 + num_workers)
                spec_as_dict["constraint"]["by_value"]["condition"] = sr_prop_flag[
                    HHData[count][1]] ## include/exclude (less than sr. over sr.)
                spec_as_dict["constraint"]["by_zone"]["origins"] = "gu" + str(HHData[count][0])

                report = compute_matrix(spec_as_dict)

            ## Calculate the total number of workers by adding the recently calculated columns of number of HH with X workers
            spec2 = {
                "expression": "mo55+mo56*2+mo57*mo58",
                "result": "mo59",
                "constraint": {
                    "by_value": None,
                    "by_zone": None
                },
                "aggregation": {
                    "origins": None,
                    "destinations": None
                },
                "type": "MATRIX_CALCULATION"
            }
            report = compute_matrix(spec2)

    def Store_AutoOwnCoeff(self, AutoOwnCoefficients):
        print "--------Store_AutoOwnershipCoefficients, " + str(datetime.now().strftime('%H:%M:%S'))
        with _modeller.logbook_trace("Store AutoOwnCoefficients"):
            with open(AutoOwnCoefficients, 'rb') as f:
                reader = csv.reader(f, dialect='excel')
                header = reader.next()
                data = [header]
                #dict_data = dict((rows[0]:rows[1]) for rows in reader)
                for row in reader:
                    data.append(row)
                dict_data = dict((data[i][0], data[i][1:]) for i in range(0, len(data)))
        return dict_data

    def Store_IncomeData(self, IncomeData):
        print "--------Store_IncomeData, " + str(datetime.now().strftime('%H:%M:%S'))
        with _modeller.logbook_trace("Store IncomeData"):
            with open(IncomeData, 'rb') as f:
                reader = csv.reader(f, dialect='excel')
                header = reader.next()
                data = [header]
                for row in reader:
                    data.append(row)
        return data

    def Store_TripRates(self, HHWorkerRate):
        with _modeller.logbook_trace("Store HHWorkerRates"):
            print "--------Store_TripRates, " + str(datetime.now().strftime('%H:%M:%S'))
            with open(HHWorkerRate, 'rb') as f:
                reader = csv.reader(f, dialect='excel')
                header = reader.next()
                data = [header]
                for row in reader:
                    data.append(row)
        return data

    ##Create mo16, mo18 from existing matrices
    def InitialMatrixCalculations(self):
        with _modeller.logbook_trace("InitialMatrixCalculations"):
            print "--------InitialMatrixCalculations, " + str(datetime.now().strftime('%H:%M:%S'))

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

            spec_as_dict["expression"] = "mo19/(mo20+0.00000000001)"
            spec_as_dict["result"] = "mo18"
            report = compute_matrix(spec_as_dict)

            spec_as_dict["expression"] = "10000*mo20/(mo17+0.00000000001)"
            spec_as_dict["result"] = "mo16"
            report = compute_matrix(spec_as_dict)

        ##    Batches in the batchin file

    def Matrix_Batchins(self, PathHeader):
        with _modeller.logbook_trace("Matrix Batchin"):
            print "--------Matrix_Batchins, " + str(datetime.now().strftime('%H:%M:%S'))
            ##        Sets up the 'matrix transaction' tool and runs it
            NAMESPACE = "inro.emme.data.matrix.matrix_transaction"
            process = _modeller.Modeller().tool(NAMESPACE)
            ##        Develops appropriate path files for the processor
            matrix_file = PathHeader + "01_SOCIOECON-SEG_AUTOOWN_TOOLBOX_WORK/Inputs/MatrixTransactionFile.txt"

            ##        Creates process transaction
            process(transaction_file=matrix_file,
                    throw_on_error=True,
                    scenario=_modeller.Modeller().scenario)

