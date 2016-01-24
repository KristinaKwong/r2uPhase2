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


import inro.modeller as _m
import csv
import os
import traceback as _traceback

class SocioEconomicSegmentation(_m.Tool()):
    ##Create global attributes (referring to dialogue boxes on the pages)

    ##Global attribute for Tool Run Message (successful/not successful)
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        ##Create various aspects to the page
        pb = _m.ToolPageBuilder(self, title="Socio-economic Segmentation",
                                       description="Collects Households Numbers, Workers Numbers, "
                                                   "Income and Auto Ownership Data and provides "
                                                   "various segmentation for use in Trip Production.",
                                       branding_text=" TransLink")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            self.__call__(_m.Modeller().emmebank)
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))


    @_m.logbook_trace("01-01 - Socio Economic Segmentation")
    def __call__(self, eb):
        PathHeader = os.path.dirname(eb.path) + "\\"
        HHWorkerRate = PathHeader + "01_SOCIOECON-SEG_AUTOOWN_TOOLBOX_WORK/Inputs/12_HH_Worker_Rates.csv"
        IncomeData = PathHeader + "01_SOCIOECON-SEG_AUTOOWN_TOOLBOX_WORK/Inputs/13_HHWrkrIncome.csv"
        AutoOwnershipCoefficients = PathHeader + "01_SOCIOECON-SEG_AUTOOWN_TOOLBOX_WORK/Inputs/14_AutoOwnershipCoefficients.csv"
        ##Batchin File
        self.Matrix_Batchins(eb)

        ## Calculate adjusted parking costs
        #Check for flag to run parking cost or otherwise

        parkcost = eb.matrix("ms144").data
        if (parkcost == 1):
            ParkingCost = _m.Modeller().tool("translink.emme.stage1.step1.parkingcost")
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
        AutoOwnership = _m.Modeller().tool("translink.emme.stage1.step1.autoownership")
        AutoOwnership(AutoOwnCoeff)

        ## mo269-mo364 - Aggregate Non-Workers
        self.Aggregate_NonWorkers_and_Workers()

        ## mo365-mo388 - Aggregate Income Categories
        self.Aggregate_IncomeCategories()

        ## mo389-mo391 - Aggregate Num Workers in each Income Category
        self.Aggregate_NumWorkerIncomeCategories()

        ## mo716-mo718 - Calculated Number of Auto Per HH Size
        self.Autos_PerHHSize()

        # Output number of worker matrices
        self.Output_Results(eb, HHWorkerRate, IncomeData, AutoOwnershipCoefficients)

    @_m.logbook_trace("Output Results")
    def Output_Results(self, eb, HHWorkerRate, IncomeData, AutoOwnershipCoefficients):
        output_path = os.path.join(os.path.dirname(eb.path), "01_SOCIOECON-SEG_AUTOOWN_TOOLBOX_WORK", "Outputs")
        output_file =    os.path.join(output_path, "01-01_OUTPUT_RESULTS.txt")
        output_file_gy = os.path.join(output_path, "01-01_OUTPUT_RESULTS_GY.txt")
        output_file_gu = os.path.join(output_path, "01-01_OUTPUT_RESULTS_GU.txt")
        output_file_csv = os.path.join(output_path, "01-01_OUTPUT_RESULTS_matrices.csv")

        util = _m.Modeller().tool("translink.emme.util")
        list_of_matrices = ["mo" + str(i) for i in [1] + range(16, 21) + range(50, 60) + range(61, 398) + range(404, 716)]
        util.export_csv(eb, list_of_matrices, output_file_csv)

        ##    List to hold matrix objects
        mo_value = []

        ##    Loop to append all result matrices onto the variable 'mo_value'
        for mo_num in range(54, 59) + range(61, 74) + range(74, 113) + range(113, 269) + range(269, 389) + range(389, 392) + range(392, 398) + range(404, 560) + range(560, 716) + range(716, 719):
            mo_value.append(eb.matrix("mo%d" % mo_num))

        ##    Export matrices using the appended list of mo_value matrices
        export_matrices = _m.Modeller().tool("inro.emme.data.matrix.export_matrices")

        ## Export all matrix data
        export_matrices(export_file=output_file,
                        field_separator=' ',
                        matrices=mo_value,
                        export_format="PROMPT_DATA_FORMAT",
                        skip_default_values=True,
                        full_matrix_line_format="ONE_ENTRY_PER_LINE")

        ## Export matrix data aggregated to the gy ensemble
        export_matrices(export_file=output_file_gy,
                        field_separator=' ',
                        matrices=mo_value,
                        partition_aggregation={'origins': 'gy', 'operator': 'sum'},
                        export_format="PROMPT_DATA_FORMAT",
                        skip_default_values=True,
                        full_matrix_line_format="ONE_ENTRY_PER_LINE")

        ## Export matrix data aggregated to the gu ensemble
        export_matrices(export_file=output_file_gu,
                        field_separator=' ',
                        matrices=mo_value,
                        partition_aggregation={'origins': 'gu', 'operator': 'sum'},
                        export_format="PROMPT_DATA_FORMAT",
                        skip_default_values=True,
                        full_matrix_line_format="ONE_ENTRY_PER_LINE")

        for Output in [output_file, output_file_gy, output_file_gu]:
            f = open(Output, 'a')
            f.write("c ------Data Sources:\n")
            f.write("c " + HHWorkerRate + "\n")
            f.write("c " + IncomeData + "\n")
            f.write("c " + AutoOwnershipCoefficients + "\n")
            f.close()

    ##     mo389-mo391 - Aggregate Num Workers in each Income Category
    @_m.logbook_trace("Aggregate Number of Worker Income Categories")
    def Aggregate_NumWorkerIncomeCategories(self):
        util = _m.Modeller().tool("translink.emme.util")
        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

        result_mo_num = 389
        specs = []
        for count in range(377, 388, 4):
            expression = "mo" + str(count + 0) + "*0 +" + "mo" + str(
                count + 1) + "*1 +" + "mo" + str(count + 2) + "*2 +" + "mo" + str(count + 3) + "*mo58"
            result = "mo" + str(result_mo_num)
            result_mo_num = result_mo_num + 1
            specs.append(util.matrix_spec(result, expression))

        ##Outputs Matrices: mo389-mo391. Income Cat x Num Workers
        report = compute_matrix(specs)

    @_m.logbook_trace("Aggregate Income Categories")
    def Aggregate_IncomeCategories(self):
        util = _m.Modeller().tool("translink.emme.util")
        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

        start_mo_num = 73
        result_mo_num = 365

        ## create additional columns to add household size and income categories
        hh_expression = []
        specs = []
        for count in range(start_mo_num, 112, 13):
            hh_expression = ["mo" + str(1 + count) + " + mo" + str(2 + count),
                             "mo" + str(3 + count) + " + mo" + str(4 + count) + " + mo" + str(5 + count),
                             "mo" + str(6 + count) + " + mo" + str(7 + count) + " + mo" + str(
                                 8 + count) + " + mo" + str(9 + count),
                             "mo" + str(10 + count) + " + mo" + str(11 + count) + " + mo" + str(
                                 12 + count) + " + mo" + str(13 + count)
            ]
            for hh_ex in hh_expression:
                specs.append(util.matrix_spec("mo" + str(result_mo_num), hh_ex))
                result_mo_num = result_mo_num + 1

        ##Outputs Matrices: mo365-mo376. HHSize x Income
        report = compute_matrix(specs)

        ## create additional columns to add worker number and income categories
        wk_expression = []
        specs = []
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
                specs.append(util.matrix_spec("mo" + str(result_mo_num), wk_ex))
                result_mo_num = result_mo_num + 1

        ##Outputs Matrices: mo377-mo388. NumWorkers x Income
        report = compute_matrix(specs)

    @_m.logbook_trace("Aggregate NonWorkers and Workers")
    def Aggregate_NonWorkers_and_Workers(self):
        util = _m.Modeller().tool("translink.emme.util")
        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

        start_mo_num = 112
        result_mo_num = 269

        ## create additional columns to aggregate to Non-workers
        hh_expression = []
        specs = []
        for count in range(start_mo_num, 268, 13):
            hh_expression = ["mo" + str(1 + count) + " + mo" + str(2 + count),
                             "mo" + str(3 + count) + " + mo" + str(4 + count) + " + mo" + str(5 + count),
                             "mo" + str(6 + count) + " + mo" + str(7 + count) + " + mo" + str(
                                 8 + count) + " + mo" + str(9 + count),
                             "mo" + str(10 + count) + " + mo" + str(11 + count) + " + mo" + str(
                                 12 + count) + " + mo" + str(13 + count)
            ]
            for hh_ex in hh_expression:
                specs.append(util.matrix_spec("mo" + str(result_mo_num), hh_ex))
                result_mo_num = result_mo_num + 1

                ##Outputs Matrices: mo269-mo316. NonWorkers: HHSize x Income x AutoOwnership
        report = compute_matrix(specs)

        ## create additional columns to aggregate to Workers
        wk_expression = []
        specs = []
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
                specs.append(util.matrix_spec("mo" + str(result_mo_num), wk_ex))
                result_mo_num = result_mo_num + 1

        report = compute_matrix(specs)

            ##     mo74-mo112 - Calculated Number of Households Per Worker Category and Per Income Category

    @_m.logbook_trace("Calculate Number of Households Per Worker Category Per Income Category")
    def Calculate_IncomeWorkersHousehold(self, IncomeData):
        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

        ##Two loops: Go through IncomeData and extract multipliers and multiplies by matrix for HHSize x WorkerNumber

        specs = []
        for inc_cat in range(3, 6):
            for row in range(1, IncomeData.__len__()):
                spec_as_dict = {
                    "expression": "mo" + str(((row - 1) % 13) + 61) + "*" + str(IncomeData[row][inc_cat]),
                    "result": "mo" + str(((row - 1) % 13) + 74 + (inc_cat - 3) * 13),
                    "constraint": {
                        "by_value": None,
                        "by_zone": {
                            "origins": "gu" + str(IncomeData[row][0]),
                            "destinations": None
                        }
                    },
                    "type": "MATRIX_CALCULATION"
                }
                specs.append(spec_as_dict)

        ##Outputs Matrices: mo74-mo112, HHSize x NumWorkers x Income
        report = compute_matrix(specs)

    @_m.logbook_trace("Calculate Number of Workers Per Household Category")
    def Calculate_WorkersHousehold(self, HHData):
        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

        ##    Dictionary for senior proportion lookup
        sr_prop_flag = {'0': "INCLUDE", '1': "EXCLUDE"}

        specs = []
        for count in range(1, HHData.__len__(), 4):
            mo_num = 0
            for hh in range(1, 5):
                wkr = 0
                while (hh >= wkr and wkr < 4):
                    spec_as_dict = {
                        "expression": "mo" + str(hh + 49) + "*" + HHData[count + hh - 1][wkr + 3],
                        "result": "mo" + str(mo_num + 61),
                        "constraint": {
                            "by_value": {
                                "od_values": "mo18",
                                "interval_min": 0,
                                "interval_max": 0.2,
                                "condition": sr_prop_flag[HHData[count][1]]
                            },
                            "by_zone": {
                                "destinations": None,
                                "origins": "gu" + str(HHData[count][0])
                            }
                        },
                        "type": "MATRIX_CALCULATION"
                    }
                    specs.append(spec_as_dict)
                    ## Output Matrices: mo61-73. Number of Households by workers
                    wkr = wkr + 1
                    mo_num = mo_num + 1

        report = compute_matrix(specs)

    @_m.logbook_trace("Calculate Number of Workers")
    def Calculate_Workers(self, HHData):
        util = _m.Modeller().tool("translink.emme.util")
        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

        ##    Dictionary for senior proprtion lookup - set senior proportion constraint
        ## 0 - less than 20% Sr. Proportion
        ## 1 - more than 20% Sr. Proportion
        sr_prop_flag = {'0': "INCLUDE", '1': "EXCLUDE"}

        specs = []
        for num_workers in range(0, 4):
            for count in range(1, HHData.__len__(), 4):
                exp = "mo50*" + str(HHData[count + 0][num_workers + 3]) + " + mo51*" + str(
                    HHData[count + 1][num_workers + 3]) + " + mo52*" + str(
                    HHData[count + 2][num_workers + 3]) + " + mo53*" + str(HHData[count + 3][num_workers + 3])
                spec_as_dict = {
                    "expression": exp,
                    "result": "mo" + str(54 + num_workers),
                    "constraint": {
                        "by_value": {
                            "od_values": "mo18",
                            "interval_min": 0,
                            "interval_max": 0.2,
                            "condition": sr_prop_flag[HHData[count][1]]
                        },
                        "by_zone": {
                            "destinations": None,
                            "origins": "gu" + str(HHData[count][0])
                        }
                    },
                    "type": "MATRIX_CALCULATION"
                }
                specs.append(spec_as_dict)

        ##Output Matrix: mo54-57. Number of households with X number of workers.  (Where X=1,2,3,4)
        report = compute_matrix(specs)


        specs = []
        ## Create mo58 - 3+ worker adjustment factor
        num_workers = 4
        for count in range(1, HHData.__len__(), 4):
            spec_as_dict = {
                "expression": str(HHData[count + 0][num_workers + 3]),
                "result": "mo" + str(54 + num_workers),
                "constraint": {
                    "by_value": {
                        "od_values": "mo18",
                        "interval_min": 0,
                        "interval_max": 0.2,
                        "condition": sr_prop_flag[HHData[count][1]]
                    },
                    "by_zone": {
                        "destinations": None,
                        "origins": "gu" + str(HHData[count][0])
                    }
                },
                "type": "MATRIX_CALCULATION"
            }
            specs.append(spec_as_dict)

        report = compute_matrix(specs)

        ## Calculate the total number of workers by adding the recently calculated columns of number of HH with X workers
        spec2 = util.matrix_spec("mo59", "mo55+mo56*2+mo57*mo58")
        report = compute_matrix(spec2)

    @_m.logbook_trace("Store AutoOwnCoefficients")
    def Store_AutoOwnCoeff(self, AutoOwnCoefficients):
        with open(AutoOwnCoefficients, 'rb') as f:
            reader = csv.reader(f, dialect='excel')
            header = reader.next()
            data = [header]
            #dict_data = dict((rows[0]:rows[1]) for rows in reader)
            for row in reader:
                data.append(row)
            dict_data = dict((data[i][0], data[i][1:]) for i in range(0, len(data)))
        return dict_data

    @_m.logbook_trace("Store IncomeData")
    def Store_IncomeData(self, IncomeData):
        with open(IncomeData, 'rb') as f:
            reader = csv.reader(f, dialect='excel')
            header = reader.next()
            data = [header]
            for row in reader:
                data.append(row)
        return data

    @_m.logbook_trace("Store HHWorkerRates")
    def Store_TripRates(self, HHWorkerRate):
        with open(HHWorkerRate, 'rb') as f:
            reader = csv.reader(f, dialect='excel')
            header = reader.next()
            data = [header]
            for row in reader:
                data.append(row)
        return data

    ## mo716-mo718 - Calculated Number of Auto Per HH Size
    @_m.logbook_trace("Autos_PerHHSize")
    def Autos_PerHHSize(self):
        util = _m.Modeller().tool("translink.emme.util")
        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

        ## Loop each set of Auto Ownership classification and perform summation.
        specs = []
        for x in range(0, 3):
            expression = ""
            for i in range(281 + x * 12, 281 + x * 12 + 12):
                expression = expression + "mo" + str(i) + " + "
            expression = expression + " 0"

            specs.append(util.matrix_spec("mo" + str(x + 716), expression))

        report = compute_matrix(specs)

    ##Create mo16, mo18 from existing matrices
    @_m.logbook_trace("InitialMatrixCalculations")
    def InitialMatrixCalculations(self):
        util = _m.Modeller().tool("translink.emme.util")
        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

        specs = []

        specs.append(util.matrix_spec("mo18", "mo19/(mo20+0.00000000001)"))
        specs.append(util.matrix_spec("mo16", "10000*mo20/(mo17+0.00000000001)"))
 
        report = compute_matrix(specs)

    @_m.logbook_trace("Matrix Batchin")
    def Matrix_Batchins(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        util.initmat(eb, "mo54", "s-0--", "Segment W0", 0)
        util.initmat(eb, "mo55", "s-1--", "Segment W1", 0)
        util.initmat(eb, "mo56", "s-2--", "Segment W2", 0)
        util.initmat(eb, "mo57", "s-3--", "Segment W3+", 0)
        util.initmat(eb, "mo58", "Wk3Adj", "Adjustment 3+ Num Workers", 0)
        util.initmat(eb, "mo59", "TotWrk", "Total Number of Workers", 0)
        util.initmat(eb, "mo16", "Dnsty", "Density person per hectare", 0)
        util.initmat(eb, "mo18", "SnPrp", "Proportion of Srs in Zone", 0)
        util.initmat(eb, "mo61", "s10--", "Segment H1W0", 0)
        util.initmat(eb, "mo62", "s11--", "Segment H1W1", 0)
        util.initmat(eb, "mo63", "s20--", "Segment H2W0", 0)
        util.initmat(eb, "mo64", "s21--", "Segment H2W1", 0)
        util.initmat(eb, "mo65", "s22--", "Segment H2W2", 0)
        util.initmat(eb, "mo66", "s30--", "Segment H3W0", 0)
        util.initmat(eb, "mo67", "s31--", "Segment H3W1", 0)
        util.initmat(eb, "mo68", "s32--", "Segment H3W2", 0)
        util.initmat(eb, "mo69", "s33--", "Segment H3W3", 0)
        util.initmat(eb, "mo70", "s40--", "Segment H4+W0", 0)
        util.initmat(eb, "mo71", "s41--", "Segment H4+W1", 0)
        util.initmat(eb, "mo72", "s42--", "Segment H4+W2", 0)
        util.initmat(eb, "mo73", "s43--", "Segment H4+W3+", 0)
        util.initmat(eb, "mo74", "s101-", "Segment H1W0L", 0)
        util.initmat(eb, "mo75", "s111-", "Segment H1W1L", 0)
        util.initmat(eb, "mo76", "s201-", "Segment H2W0L", 0)
        util.initmat(eb, "mo77", "s211-", "Segment H2W1L", 0)
        util.initmat(eb, "mo78", "s221-", "Segment H2W2L", 0)
        util.initmat(eb, "mo79", "s301-", "Segment H3W0L", 0)
        util.initmat(eb, "mo80", "s311-", "Segment H3W1L", 0)
        util.initmat(eb, "mo81", "s321-", "Segment H3W2L", 0)
        util.initmat(eb, "mo82", "s331-", "Segment H3W3L", 0)
        util.initmat(eb, "mo83", "s401-", "Segment H4+W0L", 0)
        util.initmat(eb, "mo84", "s411-", "Segment H4+W1L", 0)
        util.initmat(eb, "mo85", "s421-", "Segment H4+W2L", 0)
        util.initmat(eb, "mo86", "s431-", "Segment H4+W3+L", 0)
        util.initmat(eb, "mo87", "s102-", "Segment H1W0M", 0)
        util.initmat(eb, "mo88", "s112-", "Segment H1W1M", 0)
        util.initmat(eb, "mo89", "s202-", "Segment H2W0M", 0)
        util.initmat(eb, "mo90", "s212-", "Segment H2W1M", 0)
        util.initmat(eb, "mo91", "s222-", "Segment H2W2M", 0)
        util.initmat(eb, "mo92", "s302-", "Segment H3W0M", 0)
        util.initmat(eb, "mo93", "s312-", "Segment H3W1M", 0)
        util.initmat(eb, "mo94", "s322-", "Segment H3W2M", 0)
        util.initmat(eb, "mo95", "s332-", "Segment H3W3M", 0)
        util.initmat(eb, "mo96", "s402-", "Segment H4+W0M", 0)
        util.initmat(eb, "mo97", "s412-", "Segment H4+W1M", 0)
        util.initmat(eb, "mo98", "s422-", "Segment H4+W2M", 0)
        util.initmat(eb, "mo99", "s432-", "Segment H4+W3+M", 0)
        util.initmat(eb, "mo100", "s103-", "Segment H1W0H", 0)
        util.initmat(eb, "mo101", "s113-", "Segment H1W1H", 0)
        util.initmat(eb, "mo102", "s203-", "Segment H2W0H", 0)
        util.initmat(eb, "mo103", "s213-", "Segment H2W1H", 0)
        util.initmat(eb, "mo104", "s223-", "Segment H2W2H", 0)
        util.initmat(eb, "mo105", "s303-", "Segment H3W0H", 0)
        util.initmat(eb, "mo106", "s313-", "Segment H3W1H", 0)
        util.initmat(eb, "mo107", "s323-", "Segment H3W2H", 0)
        util.initmat(eb, "mo108", "s333-", "Segment H3W3H", 0)
        util.initmat(eb, "mo109", "s403-", "Segment H4+W0H", 0)
        util.initmat(eb, "mo110", "s413-", "Segment H4+W1H", 0)
        util.initmat(eb, "mo111", "s423-", "Segment H4+W2H", 0)
        util.initmat(eb, "mo112", "s433-", "Segment H4+W3+H", 0)
        util.initmat(eb, "mo113", "s1010", "Segment H1W0LA0", 0)
        util.initmat(eb, "mo114", "s1110", "Segment H1W1LA0", 0)
        util.initmat(eb, "mo115", "s2010", "Segment H2W0LA0", 0)
        util.initmat(eb, "mo116", "s2110", "Segment H2W1LA0", 0)
        util.initmat(eb, "mo117", "s2210", "Segment H2W2LA0", 0)
        util.initmat(eb, "mo118", "s3010", "Segment H3W0LA0", 0)
        util.initmat(eb, "mo119", "s3110", "Segment H3W1LA0", 0)
        util.initmat(eb, "mo120", "s3210", "Segment H3W2LA0", 0)
        util.initmat(eb, "mo121", "s3310", "Segment H3W3LA0", 0)
        util.initmat(eb, "mo122", "s4010", "Segment H4+W0LA0", 0)
        util.initmat(eb, "mo123", "s4110", "Segment H4+W1LA0", 0)
        util.initmat(eb, "mo124", "s4210", "Segment H4+W2LA0", 0)
        util.initmat(eb, "mo125", "s4310", "Segment H4+W3+LA0", 0)
        util.initmat(eb, "mo126", "s1020", "Segment H1W0MA0", 0)
        util.initmat(eb, "mo127", "s1120", "Segment H1W1MA0", 0)
        util.initmat(eb, "mo128", "s2020", "Segment H2W0MA0", 0)
        util.initmat(eb, "mo129", "s2120", "Segment H2W1MA0", 0)
        util.initmat(eb, "mo130", "s2220", "Segment H2W2MA0", 0)
        util.initmat(eb, "mo131", "s3020", "Segment H3W0MA0", 0)
        util.initmat(eb, "mo132", "s3120", "Segment H3W1MA0", 0)
        util.initmat(eb, "mo133", "s3220", "Segment H3W2MA0", 0)
        util.initmat(eb, "mo134", "s3320", "Segment H3W3MA0", 0)
        util.initmat(eb, "mo135", "s4020", "Segment H4+W0MA0", 0)
        util.initmat(eb, "mo136", "s4120", "Segment H4+W1MA0", 0)
        util.initmat(eb, "mo137", "s4220", "Segment H4+W2MA0", 0)
        util.initmat(eb, "mo138", "s4320", "Segment H4+W3+MA0", 0)
        util.initmat(eb, "mo139", "s1030", "Segment H1W0HA0", 0)
        util.initmat(eb, "mo140", "s1130", "Segment H1W1HA0", 0)
        util.initmat(eb, "mo141", "s2030", "Segment H2W0HA0", 0)
        util.initmat(eb, "mo142", "s2130", "Segment H2W1HA0", 0)
        util.initmat(eb, "mo143", "s2230", "Segment H2W2HA0", 0)
        util.initmat(eb, "mo144", "s3030", "Segment H3W0HA0", 0)
        util.initmat(eb, "mo145", "s3130", "Segment H3W1HA0", 0)
        util.initmat(eb, "mo146", "s3230", "Segment H3W2HA0", 0)
        util.initmat(eb, "mo147", "s3330", "Segment H3W3HA0", 0)
        util.initmat(eb, "mo148", "s4030", "Segment H4+W0HA0", 0)
        util.initmat(eb, "mo149", "s4130", "Segment H4+W1HA0", 0)
        util.initmat(eb, "mo150", "s4230", "Segment H4+W2HA0", 0)
        util.initmat(eb, "mo151", "s4330", "Segment H4+W3+HA0", 0)
        util.initmat(eb, "mo152", "s1011", "Segment H1W0LA1", 0)
        util.initmat(eb, "mo153", "s1111", "Segment H1W1LA1", 0)
        util.initmat(eb, "mo154", "s2011", "Segment H2W0LA1", 0)
        util.initmat(eb, "mo155", "s2111", "Segment H2W1LA1", 0)
        util.initmat(eb, "mo156", "s2211", "Segment H2W2LA1", 0)
        util.initmat(eb, "mo157", "s3011", "Segment H3W0LA1", 0)
        util.initmat(eb, "mo158", "s3111", "Segment H3W1LA1", 0)
        util.initmat(eb, "mo159", "s3211", "Segment H3W2LA1", 0)
        util.initmat(eb, "mo160", "s3311", "Segment H3W3LA1", 0)
        util.initmat(eb, "mo161", "s4011", "Segment H4+W0LA1", 0)
        util.initmat(eb, "mo162", "s4111", "Segment H4+W1LA1", 0)
        util.initmat(eb, "mo163", "s4211", "Segment H4+W2LA1", 0)
        util.initmat(eb, "mo164", "s4311", "Segment H4+W3+LA1", 0)
        util.initmat(eb, "mo165", "s1021", "Segment H1W0MA1", 0)
        util.initmat(eb, "mo166", "s1121", "Segment H1W1MA1", 0)
        util.initmat(eb, "mo167", "s2021", "Segment H2W0MA1", 0)
        util.initmat(eb, "mo168", "s2121", "Segment H2W1MA1", 0)
        util.initmat(eb, "mo169", "s2221", "Segment H2W2MA1", 0)
        util.initmat(eb, "mo170", "s3021", "Segment H3W0MA1", 0)
        util.initmat(eb, "mo171", "s3121", "Segment H3W1MA1", 0)
        util.initmat(eb, "mo172", "s3221", "Segment H3W2MA1", 0)
        util.initmat(eb, "mo173", "s3321", "Segment H3W3MA1", 0)
        util.initmat(eb, "mo174", "s4021", "Segment H4+W0MA1", 0)
        util.initmat(eb, "mo175", "s4121", "Segment H4+W1MA1", 0)
        util.initmat(eb, "mo176", "s4221", "Segment H4+W2MA1", 0)
        util.initmat(eb, "mo177", "s4321", "Segment H4+W3+MA1", 0)
        util.initmat(eb, "mo178", "s1031", "Segment H1W0HA1", 0)
        util.initmat(eb, "mo179", "s1131", "Segment H1W1HA1", 0)
        util.initmat(eb, "mo180", "s2031", "Segment H2W0HA1", 0)
        util.initmat(eb, "mo181", "s2131", "Segment H2W1HA1", 0)
        util.initmat(eb, "mo182", "s2231", "Segment H2W2HA1", 0)
        util.initmat(eb, "mo183", "s3031", "Segment H3W0HA1", 0)
        util.initmat(eb, "mo184", "s3131", "Segment H3W1HA1", 0)
        util.initmat(eb, "mo185", "s3231", "Segment H3W2HA1", 0)
        util.initmat(eb, "mo186", "s3331", "Segment H3W3HA1", 0)
        util.initmat(eb, "mo187", "s4031", "Segment H4+W0HA1", 0)
        util.initmat(eb, "mo188", "s4131", "Segment H4+W1HA1", 0)
        util.initmat(eb, "mo189", "s4231", "Segment H4+W2HA1", 0)
        util.initmat(eb, "mo190", "s4331", "Segment H4+W3+HA1", 0)
        util.initmat(eb, "mo191", "s1012", "Segment H1W0LA2", 0)
        util.initmat(eb, "mo192", "s1112", "Segment H1W1LA2", 0)
        util.initmat(eb, "mo193", "s2012", "Segment H2W0LA2", 0)
        util.initmat(eb, "mo194", "s2112", "Segment H2W1LA2", 0)
        util.initmat(eb, "mo195", "s2212", "Segment H2W2LA2", 0)
        util.initmat(eb, "mo196", "s3012", "Segment H3W0LA2", 0)
        util.initmat(eb, "mo197", "s3112", "Segment H3W1LA2", 0)
        util.initmat(eb, "mo198", "s3212", "Segment H3W2LA2", 0)
        util.initmat(eb, "mo199", "s3312", "Segment H3W3LA2", 0)
        util.initmat(eb, "mo200", "s4012", "Segment H4+W0LA2", 0)
        util.initmat(eb, "mo201", "s4112", "Segment H4+W1LA2", 0)
        util.initmat(eb, "mo202", "s4212", "Segment H4+W2LA2", 0)
        util.initmat(eb, "mo203", "s4312", "Segment H4+W3+LA2", 0)
        util.initmat(eb, "mo204", "s1022", "Segment H1W0MA2", 0)
        util.initmat(eb, "mo205", "s1122", "Segment H1W1MA2", 0)
        util.initmat(eb, "mo206", "s2022", "Segment H2W0MA2", 0)
        util.initmat(eb, "mo207", "s2122", "Segment H2W1MA2", 0)
        util.initmat(eb, "mo208", "s2222", "Segment H2W2MA2", 0)
        util.initmat(eb, "mo209", "s3022", "Segment H3W0MA2", 0)
        util.initmat(eb, "mo210", "s3122", "Segment H3W1MA2", 0)
        util.initmat(eb, "mo211", "s3222", "Segment H3W2MA2", 0)
        util.initmat(eb, "mo212", "s3322", "Segment H3W3MA2", 0)
        util.initmat(eb, "mo213", "s4022", "Segment H4+W0MA2", 0)
        util.initmat(eb, "mo214", "s4122", "Segment H4+W1MA2", 0)
        util.initmat(eb, "mo215", "s4222", "Segment H4+W2MA2", 0)
        util.initmat(eb, "mo216", "s4322", "Segment H4+W3+MA2", 0)
        util.initmat(eb, "mo217", "s1032", "Segment H1W0HA2", 0)
        util.initmat(eb, "mo218", "s1132", "Segment H1W1HA2", 0)
        util.initmat(eb, "mo219", "s2032", "Segment H2W0HA2", 0)
        util.initmat(eb, "mo220", "s2132", "Segment H2W1HA2", 0)
        util.initmat(eb, "mo221", "s2232", "Segment H2W2HA2", 0)
        util.initmat(eb, "mo222", "s3032", "Segment H3W0HA2", 0)
        util.initmat(eb, "mo223", "s3132", "Segment H3W1HA2", 0)
        util.initmat(eb, "mo224", "s3232", "Segment H3W2HA2", 0)
        util.initmat(eb, "mo225", "s3332", "Segment H3W3HA2", 0)
        util.initmat(eb, "mo226", "s4032", "Segment H4+W0HA2", 0)
        util.initmat(eb, "mo227", "s4132", "Segment H4+W1HA2", 0)
        util.initmat(eb, "mo228", "s4232", "Segment H4+W2HA2", 0)
        util.initmat(eb, "mo229", "s4332", "Segment H4+W3+HA2", 0)
        util.initmat(eb, "mo230", "s1013", "Segment H1W0LA3+", 0)
        util.initmat(eb, "mo231", "s1113", "Segment H1W1LA3+", 0)
        util.initmat(eb, "mo232", "s2013", "Segment H2W0LA3+", 0)
        util.initmat(eb, "mo233", "s2113", "Segment H2W1LA3+", 0)
        util.initmat(eb, "mo234", "s2213", "Segment H2W2LA3+", 0)
        util.initmat(eb, "mo235", "s3013", "Segment H3W0LA3+", 0)
        util.initmat(eb, "mo236", "s3113", "Segment H3W1LA3+", 0)
        util.initmat(eb, "mo237", "s3213", "Segment H3W2LA3+", 0)
        util.initmat(eb, "mo238", "s3313", "Segment H3W3LA3+", 0)
        util.initmat(eb, "mo239", "s4013", "Segment H4+W0LA3+", 0)
        util.initmat(eb, "mo240", "s4113", "Segment H4+W1LA3+", 0)
        util.initmat(eb, "mo241", "s4213", "Segment H4+W2LA3+", 0)
        util.initmat(eb, "mo242", "s4313", "Segment H4+W3+LA3+", 0)
        util.initmat(eb, "mo243", "s1023", "Segment H1W0MA3+", 0)
        util.initmat(eb, "mo244", "s1123", "Segment H1W1MA3+", 0)
        util.initmat(eb, "mo245", "s2023", "Segment H2W0MA3+", 0)
        util.initmat(eb, "mo246", "s2123", "Segment H2W1MA3+", 0)
        util.initmat(eb, "mo247", "s2223", "Segment H2W2MA3+", 0)
        util.initmat(eb, "mo248", "s3023", "Segment H3W0MA3+", 0)
        util.initmat(eb, "mo249", "s3123", "Segment H3W1MA3+", 0)
        util.initmat(eb, "mo250", "s3223", "Segment H3W2MA3+", 0)
        util.initmat(eb, "mo251", "s3323", "Segment H3W3MA3+", 0)
        util.initmat(eb, "mo252", "s4023", "Segment H4+W0MA3+", 0)
        util.initmat(eb, "mo253", "s4123", "Segment H4+W1MA3+", 0)
        util.initmat(eb, "mo254", "s4223", "Segment H4+W2MA3+", 0)
        util.initmat(eb, "mo255", "s4323", "Segment H4+W3+MA3+", 0)
        util.initmat(eb, "mo256", "s1033", "Segment H1W0HA3+", 0)
        util.initmat(eb, "mo257", "s1133", "Segment H1W1HA3+", 0)
        util.initmat(eb, "mo258", "s2033", "Segment H2W0HA3+", 0)
        util.initmat(eb, "mo259", "s2133", "Segment H2W1HA3+", 0)
        util.initmat(eb, "mo260", "s2233", "Segment H2W2HA3+", 0)
        util.initmat(eb, "mo261", "s3033", "Segment H3W0HA3+", 0)
        util.initmat(eb, "mo262", "s3133", "Segment H3W1HA3+", 0)
        util.initmat(eb, "mo263", "s3233", "Segment H3W2HA3+", 0)
        util.initmat(eb, "mo264", "s3333", "Segment H3W3HA3+", 0)
        util.initmat(eb, "mo265", "s4033", "Segment H4+W0HA3+", 0)
        util.initmat(eb, "mo266", "s4133", "Segment H4+W1HA3+", 0)
        util.initmat(eb, "mo267", "s4233", "Segment H4+W2HA3+", 0)
        util.initmat(eb, "mo268", "s4333", "Segment H4+W3+HA3+", 0)
        util.initmat(eb, "mo269", "s1-10", "Segment H1LA0", 0)
        util.initmat(eb, "mo270", "s2-10", "Segment H2LA0", 0)
        util.initmat(eb, "mo271", "s3-10", "Segment H3LA0", 0)
        util.initmat(eb, "mo272", "s4-10", "Segment H4+LA0", 0)
        util.initmat(eb, "mo273", "s1-20", "Segment H1MA0", 0)
        util.initmat(eb, "mo274", "s2-20", "Segment H2MA0", 0)
        util.initmat(eb, "mo275", "s3-20", "Segment H3MA0", 0)
        util.initmat(eb, "mo276", "s4-20", "Segment H4+MA0", 0)
        util.initmat(eb, "mo277", "s1-30", "Segment H1HA0", 0)
        util.initmat(eb, "mo278", "s2-30", "Segment H2HA0", 0)
        util.initmat(eb, "mo279", "s3-30", "Segment H3HA0", 0)
        util.initmat(eb, "mo280", "s4-30", "Segment H4+HA0", 0)
        util.initmat(eb, "mo281", "s1-11", "Segment H1LA1", 0)
        util.initmat(eb, "mo282", "s2-11", "Segment H2LA1", 0)
        util.initmat(eb, "mo283", "s3-11", "Segment H3LA1", 0)
        util.initmat(eb, "mo284", "s4-11", "Segment H4+LA1", 0)
        util.initmat(eb, "mo285", "s1-21", "Segment H1MA1", 0)
        util.initmat(eb, "mo286", "s2-21", "Segment H2MA1", 0)
        util.initmat(eb, "mo287", "s3-21", "Segment H3MA1", 0)
        util.initmat(eb, "mo288", "s4-21", "Segment H4+MA1", 0)
        util.initmat(eb, "mo289", "s1-31", "Segment H1HA1", 0)
        util.initmat(eb, "mo290", "s2-31", "Segment H2HA1", 0)
        util.initmat(eb, "mo291", "s3-31", "Segment H3HA1", 0)
        util.initmat(eb, "mo292", "s4-31", "Segment H4+HA1", 0)
        util.initmat(eb, "mo293", "s1-12", "Segment H1LA2", 0)
        util.initmat(eb, "mo294", "s2-12", "Segment H2LA2", 0)
        util.initmat(eb, "mo295", "s3-12", "Segment H3LA2", 0)
        util.initmat(eb, "mo296", "s4-12", "Segment H4+LA2", 0)
        util.initmat(eb, "mo297", "s1-22", "Segment H1MA2", 0)
        util.initmat(eb, "mo298", "s2-22", "Segment H2MA2", 0)
        util.initmat(eb, "mo299", "s3-22", "Segment H3MA2", 0)
        util.initmat(eb, "mo300", "s4-22", "Segment H4+MA2", 0)
        util.initmat(eb, "mo301", "s1-32", "Segment H1HA2", 0)
        util.initmat(eb, "mo302", "s2-32", "Segment H2HA2", 0)
        util.initmat(eb, "mo303", "s3-32", "Segment H3HA2", 0)
        util.initmat(eb, "mo304", "s4-32", "Segment H4+HA2", 0)
        util.initmat(eb, "mo305", "s1-13", "Segment H1LA3+", 0)
        util.initmat(eb, "mo306", "s2-13", "Segment H2LA3+", 0)
        util.initmat(eb, "mo307", "s3-13", "Segment H3LA3+", 0)
        util.initmat(eb, "mo308", "s4-13", "Segment H4+LA3+", 0)
        util.initmat(eb, "mo309", "s1-23", "Segment H1MA3+", 0)
        util.initmat(eb, "mo310", "s2-23", "Segment H2MA3+", 0)
        util.initmat(eb, "mo311", "s3-23", "Segment H3MA3+", 0)
        util.initmat(eb, "mo312", "s4-23", "Segment H4+MA3+", 0)
        util.initmat(eb, "mo313", "s1-33", "Segment H1HA3+", 0)
        util.initmat(eb, "mo314", "s2-33", "Segment H2HA3+", 0)
        util.initmat(eb, "mo315", "s3-33", "Segment H3HA3+", 0)
        util.initmat(eb, "mo316", "s4-33", "Segment H4+HA3+", 0)
        util.initmat(eb, "mo317", "s-010", "Segment W0LA0", 0)
        util.initmat(eb, "mo318", "s-110", "Segment W1LA0", 0)
        util.initmat(eb, "mo319", "s-210", "Segment W2LA0", 0)
        util.initmat(eb, "mo320", "s-310", "Segment W3+LA0", 0)
        util.initmat(eb, "mo321", "s-020", "Segment W0MA0", 0)
        util.initmat(eb, "mo322", "s-120", "Segment W1MA0", 0)
        util.initmat(eb, "mo323", "s-220", "Segment W2MA0", 0)
        util.initmat(eb, "mo324", "s-320", "Segment W3+MA0", 0)
        util.initmat(eb, "mo325", "s-030", "Segment W0HA0", 0)
        util.initmat(eb, "mo326", "s-130", "Segment W1HA0", 0)
        util.initmat(eb, "mo327", "s-230", "Segment W2HA0", 0)
        util.initmat(eb, "mo328", "s-330", "Segment W3+HA0", 0)
        util.initmat(eb, "mo329", "s-011", "Segment W0LA1", 0)
        util.initmat(eb, "mo330", "s-111", "Segment W1LA1", 0)
        util.initmat(eb, "mo331", "s-211", "Segment W2LA1", 0)
        util.initmat(eb, "mo332", "s-311", "Segment W3+LA1", 0)
        util.initmat(eb, "mo333", "s-021", "Segment W0MA1", 0)
        util.initmat(eb, "mo334", "s-121", "Segment W1MA1", 0)
        util.initmat(eb, "mo335", "s-221", "Segment W2MA1", 0)
        util.initmat(eb, "mo336", "s-321", "Segment W3+MA1", 0)
        util.initmat(eb, "mo337", "s-031", "Segment W0HA1", 0)
        util.initmat(eb, "mo338", "s-131", "Segment W1HA1", 0)
        util.initmat(eb, "mo339", "s-231", "Segment W2HA1", 0)
        util.initmat(eb, "mo340", "s-331", "Segment W3+HA1", 0)
        util.initmat(eb, "mo341", "s-012", "Segment W0LA2", 0)
        util.initmat(eb, "mo342", "s-112", "Segment W1LA2", 0)
        util.initmat(eb, "mo343", "s-212", "Segment W2LA2", 0)
        util.initmat(eb, "mo344", "s-312", "Segment W3+LA2", 0)
        util.initmat(eb, "mo345", "s-022", "Segment W0MA2", 0)
        util.initmat(eb, "mo346", "s-122", "Segment W1MA2", 0)
        util.initmat(eb, "mo347", "s-222", "Segment W2MA2", 0)
        util.initmat(eb, "mo348", "s-322", "Segment W3+MA2", 0)
        util.initmat(eb, "mo349", "s-032", "Segment W0HA2", 0)
        util.initmat(eb, "mo350", "s-132", "Segment W1HA2", 0)
        util.initmat(eb, "mo351", "s-232", "Segment W2HA2", 0)
        util.initmat(eb, "mo352", "s-332", "Segment W3+HA2", 0)
        util.initmat(eb, "mo353", "s-013", "Segment W0LA3+", 0)
        util.initmat(eb, "mo354", "s-113", "Segment W1LA3+", 0)
        util.initmat(eb, "mo355", "s-213", "Segment W2LA3+", 0)
        util.initmat(eb, "mo356", "s-313", "Segment W3+LA3+", 0)
        util.initmat(eb, "mo357", "s-023", "Segment W0MA3+", 0)
        util.initmat(eb, "mo358", "s-123", "Segment W1MA3+", 0)
        util.initmat(eb, "mo359", "s-223", "Segment W2MA3+", 0)
        util.initmat(eb, "mo360", "s-323", "Segment W3+MA3+", 0)
        util.initmat(eb, "mo361", "s-033", "Segment W0HA3+", 0)
        util.initmat(eb, "mo362", "s-133", "Segment W1HA3+", 0)
        util.initmat(eb, "mo363", "s-233", "Segment W2HA3+", 0)
        util.initmat(eb, "mo364", "s-333", "Segment W3+HA3+", 0)
        util.initmat(eb, "mo365", "s1-1-", "Segment H1L", 0)
        util.initmat(eb, "mo366", "s2-1-", "Segment H2L", 0)
        util.initmat(eb, "mo367", "s3-1-", "Segment H3L", 0)
        util.initmat(eb, "mo368", "s4-1-", "Segment H4+L", 0)
        util.initmat(eb, "mo369", "s1-2-", "Segment H1M", 0)
        util.initmat(eb, "mo370", "s2-2-", "Segment H2M", 0)
        util.initmat(eb, "mo371", "s3-2-", "Segment H3M", 0)
        util.initmat(eb, "mo372", "s4-2-", "Segment H4+M", 0)
        util.initmat(eb, "mo373", "s1-3-", "Segment H1H", 0)
        util.initmat(eb, "mo374", "s2-3-", "Segment H2H", 0)
        util.initmat(eb, "mo375", "s3-3-", "Segment H3H", 0)
        util.initmat(eb, "mo376", "s4-3-", "Segment H4+H", 0)
        util.initmat(eb, "mo377", "s-01-", "Segment W0L", 0)
        util.initmat(eb, "mo378", "s-11-", "Segment W1L", 0)
        util.initmat(eb, "mo379", "s-21-", "Segment W2L", 0)
        util.initmat(eb, "mo380", "s-31-", "Segment W3+L", 0)
        util.initmat(eb, "mo381", "s-02-", "Segment W0M", 0)
        util.initmat(eb, "mo382", "s-12-", "Segment W1M", 0)
        util.initmat(eb, "mo383", "s-22-", "Segment W2M", 0)
        util.initmat(eb, "mo384", "s-32-", "Segment W3+M", 0)
        util.initmat(eb, "mo385", "s-03-", "Segment W0H", 0)
        util.initmat(eb, "mo386", "s-13-", "Segment W1H", 0)
        util.initmat(eb, "mo387", "s-23-", "Segment W2H", 0)
        util.initmat(eb, "mo388", "s-33-", "Segment W3+H", 0)
        util.initmat(eb, "mo389", "WrkInL", "Number of Workers - Low Income Segment", 0)
        util.initmat(eb, "mo390", "WrkInM", "Number of Workers - Med Income Segment", 0)
        util.initmat(eb, "mo391", "WrkInH", "Number of Workers - High Income Segment", 0)
        util.initmat(eb, "mo395", "Scr1", "Scratch - Carshare 250 - LowDen", 0)
        util.initmat(eb, "mo396", "Scr2", "Scratch - Carshare 250 - HighDen", 0)
        util.initmat(eb, "mo397", "Scr3", "Scratch - Carshare 500", 0)
        util.initmat(eb, "mo404", "u1010", "AuUtil H1W0LA0", 0)
        util.initmat(eb, "mo405", "u1110", "AuUtil H1W1LA0", 0)
        util.initmat(eb, "mo406", "u2010", "AuUtil H2W0LA0", 0)
        util.initmat(eb, "mo407", "u2110", "AuUtil H2W1LA0", 0)
        util.initmat(eb, "mo408", "u2210", "AuUtil H2W2LA0", 0)
        util.initmat(eb, "mo409", "u3010", "AuUtil H3W0LA0", 0)
        util.initmat(eb, "mo410", "u3110", "AuUtil H3W1LA0", 0)
        util.initmat(eb, "mo411", "u3210", "AuUtil H3W2LA0", 0)
        util.initmat(eb, "mo412", "u3310", "AuUtil H3W3LA0", 0)
        util.initmat(eb, "mo413", "u4010", "AuUtil H4+W0LA0", 0)
        util.initmat(eb, "mo414", "u4110", "AuUtil H4+W1LA0", 0)
        util.initmat(eb, "mo415", "u4210", "AuUtil H4+W2LA0", 0)
        util.initmat(eb, "mo416", "u4310", "AuUtil H4+W3+LA0", 0)
        util.initmat(eb, "mo417", "u1020", "AuUtil H1W0MA0", 0)
        util.initmat(eb, "mo418", "u1120", "AuUtil H1W1MA0", 0)
        util.initmat(eb, "mo419", "u2020", "AuUtil H2W0MA0", 0)
        util.initmat(eb, "mo420", "u2120", "AuUtil H2W1MA0", 0)
        util.initmat(eb, "mo421", "u2220", "AuUtil H2W2MA0", 0)
        util.initmat(eb, "mo422", "u3020", "AuUtil H3W0MA0", 0)
        util.initmat(eb, "mo423", "u3120", "AuUtil H3W1MA0", 0)
        util.initmat(eb, "mo424", "u3220", "AuUtil H3W2MA0", 0)
        util.initmat(eb, "mo425", "u3320", "AuUtil H3W3MA0", 0)
        util.initmat(eb, "mo426", "u4020", "AuUtil H4+W0MA0", 0)
        util.initmat(eb, "mo427", "u4120", "AuUtil H4+W1MA0", 0)
        util.initmat(eb, "mo428", "u4220", "AuUtil H4+W2MA0", 0)
        util.initmat(eb, "mo429", "u4320", "AuUtil H4+W3+MA0", 0)
        util.initmat(eb, "mo430", "u1030", "AuUtil H1W0HA0", 0)
        util.initmat(eb, "mo431", "u1130", "AuUtil H1W1HA0", 0)
        util.initmat(eb, "mo432", "u2030", "AuUtil H2W0HA0", 0)
        util.initmat(eb, "mo433", "u2130", "AuUtil H2W1HA0", 0)
        util.initmat(eb, "mo434", "u2230", "AuUtil H2W2HA0", 0)
        util.initmat(eb, "mo435", "u3030", "AuUtil H3W0HA0", 0)
        util.initmat(eb, "mo436", "u3130", "AuUtil H3W1HA0", 0)
        util.initmat(eb, "mo437", "u3230", "AuUtil H3W2HA0", 0)
        util.initmat(eb, "mo438", "u3330", "AuUtil H3W3HA0", 0)
        util.initmat(eb, "mo439", "u4030", "AuUtil H4+W0HA0", 0)
        util.initmat(eb, "mo440", "u4130", "AuUtil H4+W1HA0", 0)
        util.initmat(eb, "mo441", "u4230", "AuUtil H4+W2HA0", 0)
        util.initmat(eb, "mo442", "u4330", "AuUtil H4+W3+HA0", 0)
        util.initmat(eb, "mo443", "u1011", "AuUtil H1W0LA1", 0)
        util.initmat(eb, "mo444", "u1111", "AuUtil H1W1LA1", 0)
        util.initmat(eb, "mo445", "u2011", "AuUtil H2W0LA1", 0)
        util.initmat(eb, "mo446", "u2111", "AuUtil H2W1LA1", 0)
        util.initmat(eb, "mo447", "u2211", "AuUtil H2W2LA1", 0)
        util.initmat(eb, "mo448", "u3011", "AuUtil H3W0LA1", 0)
        util.initmat(eb, "mo449", "u3111", "AuUtil H3W1LA1", 0)
        util.initmat(eb, "mo450", "u3211", "AuUtil H3W2LA1", 0)
        util.initmat(eb, "mo451", "u3311", "AuUtil H3W3LA1", 0)
        util.initmat(eb, "mo452", "u4011", "AuUtil H4+W0LA1", 0)
        util.initmat(eb, "mo453", "u4111", "AuUtil H4+W1LA1", 0)
        util.initmat(eb, "mo454", "u4211", "AuUtil H4+W2LA1", 0)
        util.initmat(eb, "mo455", "u4311", "AuUtil H4+W3+LA1", 0)
        util.initmat(eb, "mo456", "u1021", "AuUtil H1W0MA1", 0)
        util.initmat(eb, "mo457", "u1121", "AuUtil H1W1MA1", 0)
        util.initmat(eb, "mo458", "u2021", "AuUtil H2W0MA1", 0)
        util.initmat(eb, "mo459", "u2121", "AuUtil H2W1MA1", 0)
        util.initmat(eb, "mo460", "u2221", "AuUtil H2W2MA1", 0)
        util.initmat(eb, "mo461", "u3021", "AuUtil H3W0MA1", 0)
        util.initmat(eb, "mo462", "u3121", "AuUtil H3W1MA1", 0)
        util.initmat(eb, "mo463", "u3221", "AuUtil H3W2MA1", 0)
        util.initmat(eb, "mo464", "u3321", "AuUtil H3W3MA1", 0)
        util.initmat(eb, "mo465", "u4021", "AuUtil H4+W0MA1", 0)
        util.initmat(eb, "mo466", "u4121", "AuUtil H4+W1MA1", 0)
        util.initmat(eb, "mo467", "u4221", "AuUtil H4+W2MA1", 0)
        util.initmat(eb, "mo468", "u4321", "AuUtil H4+W3+MA1", 0)
        util.initmat(eb, "mo469", "u1031", "AuUtil H1W0HA1", 0)
        util.initmat(eb, "mo470", "u1131", "AuUtil H1W1HA1", 0)
        util.initmat(eb, "mo471", "u2031", "AuUtil H2W0HA1", 0)
        util.initmat(eb, "mo472", "u2131", "AuUtil H2W1HA1", 0)
        util.initmat(eb, "mo473", "u2231", "AuUtil H2W2HA1", 0)
        util.initmat(eb, "mo474", "u3031", "AuUtil H3W0HA1", 0)
        util.initmat(eb, "mo475", "u3131", "AuUtil H3W1HA1", 0)
        util.initmat(eb, "mo476", "u3231", "AuUtil H3W2HA1", 0)
        util.initmat(eb, "mo477", "u3331", "AuUtil H3W3HA1", 0)
        util.initmat(eb, "mo478", "u4031", "AuUtil H4+W0HA1", 0)
        util.initmat(eb, "mo479", "u4131", "AuUtil H4+W1HA1", 0)
        util.initmat(eb, "mo480", "u4231", "AuUtil H4+W2HA1", 0)
        util.initmat(eb, "mo481", "u4331", "AuUtil H4+W3+HA1", 0)
        util.initmat(eb, "mo482", "u1012", "AuUtil H1W0LA2", 0)
        util.initmat(eb, "mo483", "u1112", "AuUtil H1W1LA2", 0)
        util.initmat(eb, "mo484", "u2012", "AuUtil H2W0LA2", 0)
        util.initmat(eb, "mo485", "u2112", "AuUtil H2W1LA2", 0)
        util.initmat(eb, "mo486", "u2212", "AuUtil H2W2LA2", 0)
        util.initmat(eb, "mo487", "u3012", "AuUtil H3W0LA2", 0)
        util.initmat(eb, "mo488", "u3112", "AuUtil H3W1LA2", 0)
        util.initmat(eb, "mo489", "u3212", "AuUtil H3W2LA2", 0)
        util.initmat(eb, "mo490", "u3312", "AuUtil H3W3LA2", 0)
        util.initmat(eb, "mo491", "u4012", "AuUtil H4+W0LA2", 0)
        util.initmat(eb, "mo492", "u4112", "AuUtil H4+W1LA2", 0)
        util.initmat(eb, "mo493", "u4212", "AuUtil H4+W2LA2", 0)
        util.initmat(eb, "mo494", "u4312", "AuUtil H4+W3+LA2", 0)
        util.initmat(eb, "mo495", "u1022", "AuUtil H1W0MA2", 0)
        util.initmat(eb, "mo496", "u1122", "AuUtil H1W1MA2", 0)
        util.initmat(eb, "mo497", "u2022", "AuUtil H2W0MA2", 0)
        util.initmat(eb, "mo498", "u2122", "AuUtil H2W1MA2", 0)
        util.initmat(eb, "mo499", "u2222", "AuUtil H2W2MA2", 0)
        util.initmat(eb, "mo500", "u3022", "AuUtil H3W0MA2", 0)
        util.initmat(eb, "mo501", "u3122", "AuUtil H3W1MA2", 0)
        util.initmat(eb, "mo502", "u3222", "AuUtil H3W2MA2", 0)
        util.initmat(eb, "mo503", "u3322", "AuUtil H3W3MA2", 0)
        util.initmat(eb, "mo504", "u4022", "AuUtil H4+W0MA2", 0)
        util.initmat(eb, "mo505", "u4122", "AuUtil H4+W1MA2", 0)
        util.initmat(eb, "mo506", "u4222", "AuUtil H4+W2MA2", 0)
        util.initmat(eb, "mo507", "u4322", "AuUtil H4+W3+MA2", 0)
        util.initmat(eb, "mo508", "u1032", "AuUtil H1W0HA2", 0)
        util.initmat(eb, "mo509", "u1132", "AuUtil H1W1HA2", 0)
        util.initmat(eb, "mo510", "u2032", "AuUtil H2W0HA2", 0)
        util.initmat(eb, "mo511", "u2132", "AuUtil H2W1HA2", 0)
        util.initmat(eb, "mo512", "u2232", "AuUtil H2W2HA2", 0)
        util.initmat(eb, "mo513", "u3032", "AuUtil H3W0HA2", 0)
        util.initmat(eb, "mo514", "u3132", "AuUtil H3W1HA2", 0)
        util.initmat(eb, "mo515", "u3232", "AuUtil H3W2HA2", 0)
        util.initmat(eb, "mo516", "u3332", "AuUtil H3W3HA2", 0)
        util.initmat(eb, "mo517", "u4032", "AuUtil H4+W0HA2", 0)
        util.initmat(eb, "mo518", "u4132", "AuUtil H4+W1HA2", 0)
        util.initmat(eb, "mo519", "u4232", "AuUtil H4+W2HA2", 0)
        util.initmat(eb, "mo520", "u4332", "AuUtil H4+W3+HA2", 0)
        util.initmat(eb, "mo521", "u1013", "AuUtil H1W0LA3+", 0)
        util.initmat(eb, "mo522", "u1113", "AuUtil H1W1LA3+", 0)
        util.initmat(eb, "mo523", "u2013", "AuUtil H2W0LA3+", 0)
        util.initmat(eb, "mo524", "u2113", "AuUtil H2W1LA3+", 0)
        util.initmat(eb, "mo525", "u2213", "AuUtil H2W2LA3+", 0)
        util.initmat(eb, "mo526", "u3013", "AuUtil H3W0LA3+", 0)
        util.initmat(eb, "mo527", "u3113", "AuUtil H3W1LA3+", 0)
        util.initmat(eb, "mo528", "u3213", "AuUtil H3W2LA3+", 0)
        util.initmat(eb, "mo529", "u3313", "AuUtil H3W3LA3+", 0)
        util.initmat(eb, "mo530", "u4013", "AuUtil H4+W0LA3+", 0)
        util.initmat(eb, "mo531", "u4113", "AuUtil H4+W1LA3+", 0)
        util.initmat(eb, "mo532", "u4213", "AuUtil H4+W2LA3+", 0)
        util.initmat(eb, "mo533", "u4313", "AuUtil H4+W3+LA3+", 0)
        util.initmat(eb, "mo534", "u1023", "AuUtil H1W0MA3+", 0)
        util.initmat(eb, "mo535", "u1123", "AuUtil H1W1MA3+", 0)
        util.initmat(eb, "mo536", "u2023", "AuUtil H2W0MA3+", 0)
        util.initmat(eb, "mo537", "u2123", "AuUtil H2W1MA3+", 0)
        util.initmat(eb, "mo538", "u2223", "AuUtil H2W2MA3+", 0)
        util.initmat(eb, "mo539", "u3023", "AuUtil H3W0MA3+", 0)
        util.initmat(eb, "mo540", "u3123", "AuUtil H3W1MA3+", 0)
        util.initmat(eb, "mo541", "u3223", "AuUtil H3W2MA3+", 0)
        util.initmat(eb, "mo542", "u3323", "AuUtil H3W3MA3+", 0)
        util.initmat(eb, "mo543", "u4023", "AuUtil H4+W0MA3+", 0)
        util.initmat(eb, "mo544", "u4123", "AuUtil H4+W1MA3+", 0)
        util.initmat(eb, "mo545", "u4223", "AuUtil H4+W2MA3+", 0)
        util.initmat(eb, "mo546", "u4323", "AuUtil H4+W3+MA3+", 0)
        util.initmat(eb, "mo547", "u1033", "AuUtil H1W0HA3+", 0)
        util.initmat(eb, "mo548", "u1133", "AuUtil H1W1HA3+", 0)
        util.initmat(eb, "mo549", "u2033", "AuUtil H2W0HA3+", 0)
        util.initmat(eb, "mo550", "u2133", "AuUtil H2W1HA3+", 0)
        util.initmat(eb, "mo551", "u2233", "AuUtil H2W2HA3+", 0)
        util.initmat(eb, "mo552", "u3033", "AuUtil H3W0HA3+", 0)
        util.initmat(eb, "mo553", "u3133", "AuUtil H3W1HA3+", 0)
        util.initmat(eb, "mo554", "u3233", "AuUtil H3W2HA3+", 0)
        util.initmat(eb, "mo555", "u3333", "AuUtil H3W3HA3+", 0)
        util.initmat(eb, "mo556", "u4033", "AuUtil H4+W0HA3+", 0)
        util.initmat(eb, "mo557", "u4133", "AuUtil H4+W1HA3+", 0)
        util.initmat(eb, "mo558", "u4233", "AuUtil H4+W2HA3+", 0)
        util.initmat(eb, "mo559", "u4333", "AuUtil H4+W3+HA3+", 0)
        util.initmat(eb, "mo560", "o1010", "AuPr H1W0LA0", 0)
        util.initmat(eb, "mo561", "o1110", "AuPr H1W1LA0", 0)
        util.initmat(eb, "mo562", "o2010", "AuPr H2W0LA0", 0)
        util.initmat(eb, "mo563", "o2110", "AuPr H2W1LA0", 0)
        util.initmat(eb, "mo564", "o2210", "AuPr H2W2LA0", 0)
        util.initmat(eb, "mo565", "o3010", "AuPr H3W0LA0", 0)
        util.initmat(eb, "mo566", "o3110", "AuPr H3W1LA0", 0)
        util.initmat(eb, "mo567", "o3210", "AuPr H3W2LA0", 0)
        util.initmat(eb, "mo568", "o3310", "AuPr H3W3LA0", 0)
        util.initmat(eb, "mo569", "o4010", "AuPr H4+W0LA0", 0)
        util.initmat(eb, "mo570", "o4110", "AuPr H4+W1LA0", 0)
        util.initmat(eb, "mo571", "o4210", "AuPr H4+W2LA0", 0)
        util.initmat(eb, "mo572", "o4310", "AuPr H4+W3+LA0", 0)
        util.initmat(eb, "mo573", "o1020", "AuPr H1W0MA0", 0)
        util.initmat(eb, "mo574", "o1120", "AuPr H1W1MA0", 0)
        util.initmat(eb, "mo575", "o2020", "AuPr H2W0MA0", 0)
        util.initmat(eb, "mo576", "o2120", "AuPr H2W1MA0", 0)
        util.initmat(eb, "mo577", "o2220", "AuPr H2W2MA0", 0)
        util.initmat(eb, "mo578", "o3020", "AuPr H3W0MA0", 0)
        util.initmat(eb, "mo579", "o3120", "AuPr H3W1MA0", 0)
        util.initmat(eb, "mo580", "o3220", "AuPr H3W2MA0", 0)
        util.initmat(eb, "mo581", "o3320", "AuPr H3W3MA0", 0)
        util.initmat(eb, "mo582", "o4020", "AuPr H4+W0MA0", 0)
        util.initmat(eb, "mo583", "o4120", "AuPr H4+W1MA0", 0)
        util.initmat(eb, "mo584", "o4220", "AuPr H4+W2MA0", 0)
        util.initmat(eb, "mo585", "o4320", "AuPr H4+W3+MA0", 0)
        util.initmat(eb, "mo586", "o1030", "AuPr H1W0HA0", 0)
        util.initmat(eb, "mo587", "o1130", "AuPr H1W1HA0", 0)
        util.initmat(eb, "mo588", "o2030", "AuPr H2W0HA0", 0)
        util.initmat(eb, "mo589", "o2130", "AuPr H2W1HA0", 0)
        util.initmat(eb, "mo590", "o2230", "AuPr H2W2HA0", 0)
        util.initmat(eb, "mo591", "o3030", "AuPr H3W0HA0", 0)
        util.initmat(eb, "mo592", "o3130", "AuPr H3W1HA0", 0)
        util.initmat(eb, "mo593", "o3230", "AuPr H3W2HA0", 0)
        util.initmat(eb, "mo594", "o3330", "AuPr H3W3HA0", 0)
        util.initmat(eb, "mo595", "o4030", "AuPr H4+W0HA0", 0)
        util.initmat(eb, "mo596", "o4130", "AuPr H4+W1HA0", 0)
        util.initmat(eb, "mo597", "o4230", "AuPr H4+W2HA0", 0)
        util.initmat(eb, "mo598", "o4330", "AuPr H4+W3+HA0", 0)
        util.initmat(eb, "mo599", "o1011", "AuPr H1W0LA1", 0)
        util.initmat(eb, "mo600", "o1111", "AuPr H1W1LA1", 0)
        util.initmat(eb, "mo601", "o2011", "AuPr H2W0LA1", 0)
        util.initmat(eb, "mo602", "o2111", "AuPr H2W1LA1", 0)
        util.initmat(eb, "mo603", "o2211", "AuPr H2W2LA1", 0)
        util.initmat(eb, "mo604", "o3011", "AuPr H3W0LA1", 0)
        util.initmat(eb, "mo605", "o3111", "AuPr H3W1LA1", 0)
        util.initmat(eb, "mo606", "o3211", "AuPr H3W2LA1", 0)
        util.initmat(eb, "mo607", "o3311", "AuPr H3W3LA1", 0)
        util.initmat(eb, "mo608", "o4011", "AuPr H4+W0LA1", 0)
        util.initmat(eb, "mo609", "o4111", "AuPr H4+W1LA1", 0)
        util.initmat(eb, "mo610", "o4211", "AuPr H4+W2LA1", 0)
        util.initmat(eb, "mo611", "o4311", "AuPr H4+W3+LA1", 0)
        util.initmat(eb, "mo612", "o1021", "AuPr H1W0MA1", 0)
        util.initmat(eb, "mo613", "o1121", "AuPr H1W1MA1", 0)
        util.initmat(eb, "mo614", "o2021", "AuPr H2W0MA1", 0)
        util.initmat(eb, "mo615", "o2121", "AuPr H2W1MA1", 0)
        util.initmat(eb, "mo616", "o2221", "AuPr H2W2MA1", 0)
        util.initmat(eb, "mo617", "o3021", "AuPr H3W0MA1", 0)
        util.initmat(eb, "mo618", "o3121", "AuPr H3W1MA1", 0)
        util.initmat(eb, "mo619", "o3221", "AuPr H3W2MA1", 0)
        util.initmat(eb, "mo620", "o3321", "AuPr H3W3MA1", 0)
        util.initmat(eb, "mo621", "o4021", "AuPr H4+W0MA1", 0)
        util.initmat(eb, "mo622", "o4121", "AuPr H4+W1MA1", 0)
        util.initmat(eb, "mo623", "o4221", "AuPr H4+W2MA1", 0)
        util.initmat(eb, "mo624", "o4321", "AuPr H4+W3+MA1", 0)
        util.initmat(eb, "mo625", "o1031", "AuPr H1W0HA1", 0)
        util.initmat(eb, "mo626", "o1131", "AuPr H1W1HA1", 0)
        util.initmat(eb, "mo627", "o2031", "AuPr H2W0HA1", 0)
        util.initmat(eb, "mo628", "o2131", "AuPr H2W1HA1", 0)
        util.initmat(eb, "mo629", "o2231", "AuPr H2W2HA1", 0)
        util.initmat(eb, "mo630", "o3031", "AuPr H3W0HA1", 0)
        util.initmat(eb, "mo631", "o3131", "AuPr H3W1HA1", 0)
        util.initmat(eb, "mo632", "o3231", "AuPr H3W2HA1", 0)
        util.initmat(eb, "mo633", "o3331", "AuPr H3W3HA1", 0)
        util.initmat(eb, "mo634", "o4031", "AuPr H4+W0HA1", 0)
        util.initmat(eb, "mo635", "o4131", "AuPr H4+W1HA1", 0)
        util.initmat(eb, "mo636", "o4231", "AuPr H4+W2HA1", 0)
        util.initmat(eb, "mo637", "o4331", "AuPr H4+W3+HA1", 0)
        util.initmat(eb, "mo638", "o1012", "AuPr H1W0LA2", 0)
        util.initmat(eb, "mo639", "o1112", "AuPr H1W1LA2", 0)
        util.initmat(eb, "mo640", "o2012", "AuPr H2W0LA2", 0)
        util.initmat(eb, "mo641", "o2112", "AuPr H2W1LA2", 0)
        util.initmat(eb, "mo642", "o2212", "AuPr H2W2LA2", 0)
        util.initmat(eb, "mo643", "o3012", "AuPr H3W0LA2", 0)
        util.initmat(eb, "mo644", "o3112", "AuPr H3W1LA2", 0)
        util.initmat(eb, "mo645", "o3212", "AuPr H3W2LA2", 0)
        util.initmat(eb, "mo646", "o3312", "AuPr H3W3LA2", 0)
        util.initmat(eb, "mo647", "o4012", "AuPr H4+W0LA2", 0)
        util.initmat(eb, "mo648", "o4112", "AuPr H4+W1LA2", 0)
        util.initmat(eb, "mo649", "o4212", "AuPr H4+W2LA2", 0)
        util.initmat(eb, "mo650", "o4312", "AuPr H4+W3+LA2", 0)
        util.initmat(eb, "mo651", "o1022", "AuPr H1W0MA2", 0)
        util.initmat(eb, "mo652", "o1122", "AuPr H1W1MA2", 0)
        util.initmat(eb, "mo653", "o2022", "AuPr H2W0MA2", 0)
        util.initmat(eb, "mo654", "o2122", "AuPr H2W1MA2", 0)
        util.initmat(eb, "mo655", "o2222", "AuPr H2W2MA2", 0)
        util.initmat(eb, "mo656", "o3022", "AuPr H3W0MA2", 0)
        util.initmat(eb, "mo657", "o3122", "AuPr H3W1MA2", 0)
        util.initmat(eb, "mo658", "o3222", "AuPr H3W2MA2", 0)
        util.initmat(eb, "mo659", "o3322", "AuPr H3W3MA2", 0)
        util.initmat(eb, "mo660", "o4022", "AuPr H4+W0MA2", 0)
        util.initmat(eb, "mo661", "o4122", "AuPr H4+W1MA2", 0)
        util.initmat(eb, "mo662", "o4222", "AuPr H4+W2MA2", 0)
        util.initmat(eb, "mo663", "o4322", "AuPr H4+W3+MA2", 0)
        util.initmat(eb, "mo664", "o1032", "AuPr H1W0HA2", 0)
        util.initmat(eb, "mo665", "o1132", "AuPr H1W1HA2", 0)
        util.initmat(eb, "mo666", "o2032", "AuPr H2W0HA2", 0)
        util.initmat(eb, "mo667", "o2132", "AuPr H2W1HA2", 0)
        util.initmat(eb, "mo668", "o2232", "AuPr H2W2HA2", 0)
        util.initmat(eb, "mo669", "o3032", "AuPr H3W0HA2", 0)
        util.initmat(eb, "mo670", "o3132", "AuPr H3W1HA2", 0)
        util.initmat(eb, "mo671", "o3232", "AuPr H3W2HA2", 0)
        util.initmat(eb, "mo672", "o3332", "AuPr H3W3HA2", 0)
        util.initmat(eb, "mo673", "o4032", "AuPr H4+W0HA2", 0)
        util.initmat(eb, "mo674", "o4132", "AuPr H4+W1HA2", 0)
        util.initmat(eb, "mo675", "o4232", "AuPr H4+W2HA2", 0)
        util.initmat(eb, "mo676", "o4332", "AuPr H4+W3+HA2", 0)
        util.initmat(eb, "mo677", "o1013", "AuPr H1W0LA3+", 0)
        util.initmat(eb, "mo678", "o1113", "AuPr H1W1LA3+", 0)
        util.initmat(eb, "mo679", "o2013", "AuPr H2W0LA3+", 0)
        util.initmat(eb, "mo680", "o2113", "AuPr H2W1LA3+", 0)
        util.initmat(eb, "mo681", "o2213", "AuPr H2W2LA3+", 0)
        util.initmat(eb, "mo682", "o3013", "AuPr H3W0LA3+", 0)
        util.initmat(eb, "mo683", "o3113", "AuPr H3W1LA3+", 0)
        util.initmat(eb, "mo684", "o3213", "AuPr H3W2LA3+", 0)
        util.initmat(eb, "mo685", "o3313", "AuPr H3W3LA3+", 0)
        util.initmat(eb, "mo686", "o4013", "AuPr H4+W0LA3+", 0)
        util.initmat(eb, "mo687", "o4113", "AuPr H4+W1LA3+", 0)
        util.initmat(eb, "mo688", "o4213", "AuPr H4+W2LA3+", 0)
        util.initmat(eb, "mo689", "o4313", "AuPr H4+W3+LA3+", 0)
        util.initmat(eb, "mo690", "o1023", "AuPr H1W0MA3+", 0)
        util.initmat(eb, "mo691", "o1123", "AuPr H1W1MA3+", 0)
        util.initmat(eb, "mo692", "o2023", "AuPr H2W0MA3+", 0)
        util.initmat(eb, "mo693", "o2123", "AuPr H2W1MA3+", 0)
        util.initmat(eb, "mo694", "o2223", "AuPr H2W2MA3+", 0)
        util.initmat(eb, "mo695", "o3023", "AuPr H3W0MA3+", 0)
        util.initmat(eb, "mo696", "o3123", "AuPr H3W1MA3+", 0)
        util.initmat(eb, "mo697", "o3223", "AuPr H3W2MA3+", 0)
        util.initmat(eb, "mo698", "o3323", "AuPr H3W3MA3+", 0)
        util.initmat(eb, "mo699", "o4023", "AuPr H4+W0MA3+", 0)
        util.initmat(eb, "mo700", "o4123", "AuPr H4+W1MA3+", 0)
        util.initmat(eb, "mo701", "o4223", "AuPr H4+W2MA3+", 0)
        util.initmat(eb, "mo702", "o4323", "AuPr H4+W3+MA3+", 0)
        util.initmat(eb, "mo703", "o1033", "AuPr H1W0HA3+", 0)
        util.initmat(eb, "mo704", "o1133", "AuPr H1W1HA3+", 0)
        util.initmat(eb, "mo705", "o2033", "AuPr H2W0HA3+", 0)
        util.initmat(eb, "mo706", "o2133", "AuPr H2W1HA3+", 0)
        util.initmat(eb, "mo707", "o2233", "AuPr H2W2HA3+", 0)
        util.initmat(eb, "mo708", "o3033", "AuPr H3W0HA3+", 0)
        util.initmat(eb, "mo709", "o3133", "AuPr H3W1HA3+", 0)
        util.initmat(eb, "mo710", "o3233", "AuPr H3W2HA3+", 0)
        util.initmat(eb, "mo711", "o3333", "AuPr H3W3HA3+", 0)
        util.initmat(eb, "mo712", "o4033", "AuPr H4+W0HA3+", 0)
        util.initmat(eb, "mo713", "o4133", "AuPr H4+W1HA3+", 0)
        util.initmat(eb, "mo714", "o4233", "AuPr H4+W2HA3+", 0)
        util.initmat(eb, "mo715", "o4333", "AuPr H4+W3+HA3+", 0)
        util.initmat(eb, "mo716", "s---1", "Segment A1", 0)
        util.initmat(eb, "mo717", "s---2", "Segment A2", 0)
        util.initmat(eb, "mo718", "s---3", "Segment A3+", 0)
        util.initmat(eb, "mo44", "TEMP1", "Temp Mo 1", 0)
        util.initmat(eb, "mo45", "TEMP2", "Temp Mo 2", 0)
        util.initmat(eb, "mo46", "TEMP3", "Temp Mo 3", 0)
        util.initmat(eb, "mo927", "Scr1", "Scratch_MO_1", 0)
        util.initmat(eb, "mo928", "Scr2", "Scratch_MO_2", 0)
        util.initmat(eb, "mo929", "Scr3", "Scratch_MO_3", 0)
        util.initmat(eb, "mo930", "Scr4", "Scratch_MO_4", 0)
