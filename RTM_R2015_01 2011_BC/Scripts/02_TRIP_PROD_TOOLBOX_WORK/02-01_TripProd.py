##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage2.step2.tripproduction
##--Purpose: develop production totals for RTM generation model
##---------------------------------------------------------------------
import inro.modeller as _m
import csv
import os
import traceback as _traceback

class TripProd(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Trip Production"
        pb.description = "Collects trip rates and land use to output trip productions. <br> Then saves it to the databank and outputs data"
        pb.branding_text = "TransLink"

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

    @_m.logbook_trace("02-01 - Trip Production")
    def __call__(self, eb):
        util = _m.Modeller().tool("translink.emme.util")
        input_path = util.get_input_path(eb)

        TripRateFile = os.path.join(input_path, "21_TripRates_ALLPURPOSES.csv")
        CalibrationFactors = os.path.join(input_path, "22_CalibFactors.csv")
        FirstResultMoNum = "404"

        self.Matrix_Batchins(eb)

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
        self.Output_Results(eb, FirstResultMoNum, TripRateFile, CalibrationFactors)

    ##    Outputs results matrix to a file
    @_m.logbook_trace("Output Results")
    def Output_Results(self, eb, FirstResultMoNum, TripRateFile, CalibrationFactors):
        util = _m.Modeller().tool("translink.emme.util")
        output_path = util.get_output_path(eb)
        output_file =    os.path.join(output_path, "02-01_OUTPUT_FILE.txt")
        output_file_gy = os.path.join(output_path, "02-01_OUTPUT_FILE_GY.txt")
        output_file_gu = os.path.join(output_path, "02-01_OUTPUT_FILE_GU.txt")
        output_file_csv = os.path.join(output_path, "02-01_OUTPUT_FILE_matrices.csv")

        list_of_matrices = ["mo" + str(i) for i in range(161, 365) + range(404, 915)]
        util.export_csv(eb, list_of_matrices, output_file_csv)

        ##    List to hold matrix objects
        mo_value = []

        for i in range(161, 269):
            mo_value.append(eb.matrix("mo" + str(i)))

        ##    Two loops to append all result matrices onto the variable 'mo_value'
        for purpose_index in range(1, 10):
            mo_result_num = int(FirstResultMoNum) + (purpose_index - 1) * (96 / 2)
            for mo_num in range(0, 96 / 2):
                mo_value.append(eb.matrix("mo" + str(mo_num + mo_result_num)))

        for i in range(899, 915):
            mo_value.append(eb.matrix("mo" + str(i)))


        ##    Export matrices using the appended list of mo_value matrices
        export_matrices = _m.Modeller().tool("inro.emme.data.matrix.export_matrices")
        export_matrices_gy = _m.Modeller().tool("inro.emme.data.matrix.export_matrices")

        export_matrices(export_file=output_file,
                        field_separator=' ',
                        matrices=mo_value,
                        export_format="PROMPT_DATA_FORMAT",
                        skip_default_values=True,
                        full_matrix_line_format="ONE_ENTRY_PER_LINE")

        ## Export matrix data aggregated to the gy ensemble
        export_matrices_gy(export_file=output_file_gy,
                           field_separator=' ',
                           matrices=mo_value,
                           partition_aggregation={'origins': 'gy', 'operator': 'sum'},
                           export_format="PROMPT_DATA_FORMAT",
                           skip_default_values=True,
                           full_matrix_line_format="ONE_ENTRY_PER_LINE")

        ## Export matrix data aggregated to the gu ensemble
        export_matrices_gy(export_file=output_file_gu,
                           field_separator=' ',
                           matrices=mo_value,
                           partition_aggregation={'origins': 'gu', 'operator': 'sum'},
                           export_format="PROMPT_DATA_FORMAT",
                           skip_default_values=True,
                           full_matrix_line_format="ONE_ENTRY_PER_LINE")

        for Output in [output_file, output_file_gy, output_file_gu]:
            f = open(Output, 'a')
            f.write("c ------Data Sources:\n")
            f.write("c " + TripRateFile + "\n")
            f.write("c " + CalibrationFactors + "\n")
            f.write("c " + output_file + "\n")
            f.close()

    @_m.logbook_trace("Aggregate_Purposes")
    def Aggregate_Purposes(self):
        util = _m.Modeller().tool("translink.emme.util")
        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

        mo_result_num = 904
        specs = []
        for i in range(0, 3):
            x = i + 161
            expression = "mo" + str(x) + " + mo" + str(x + 3) + " + mo" + str(x + 6) + " + mo" + str(x + 9)
            specs.append(util.matrix_spec("mo" + str(mo_result_num), expression))
            mo_result_num = mo_result_num + 1

        report = compute_matrix(specs)

        specs = []
        for i in range(173, 268, 12):
            exp = util.matrix_sum(["mo%d" % n for n in range(i, i + 12)])
            specs.append(util.matrix_spec("mo" + str(mo_result_num), exp))
            mo_result_num = mo_result_num + 1

        report = compute_matrix(specs)

    ##mo899-mo903 - Calculate total number of auto
    @_m.logbook_trace("CalculateNumAutos")
    def CalculateNumAutos(self):
        util = _m.Modeller().tool("translink.emme.util")
        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

        specs = []

        exp = util.matrix_sum(["mo%d" % i for i in range(269, 281)])
        specs.append(util.matrix_spec("mo899", exp))

        exp = util.matrix_sum(["mo%d" % i for i in range(281, 293)])
        specs.append(util.matrix_spec("mo900", exp))

        exp = util.matrix_sum(["mo%d" % i for i in range(293, 305)])
        specs.append(util.matrix_spec("mo901", exp))

        exp = util.matrix_sum(["mo%d" % i for i in range(305, 317)])
        specs.append(util.matrix_spec("mo902", exp))

        specs.append(util.matrix_spec("mo903", "mo900 + 2*mo901 + 3.35*mo902"))

        report = compute_matrix(specs)

    ##mo161-268 - Aggregate Income Auto Ownership
    @_m.logbook_trace("Aggregation_IncomeOwnership")
    def Aggregation_IncomeOwnership(self):
        util = _m.Modeller().tool("translink.emme.util")
        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

        mo_result_num = 161
        specs = []
        for mo_num in range(404, 836, 4):
            expression = util.matrix_sum(["mo%d" % i for i in range(mo_num, mo_num + 4)])
            specs.append(util.matrix_spec("mo" + str(mo_result_num), expression))
            mo_result_num = mo_result_num + 1

        report = compute_matrix(specs)

    ## mo836-mo898 - Aggregation of production to income-ownership splits for each purpose
    @_m.logbook_trace("Aggregation")
    def Aggregation(self):
        util = _m.Modeller().tool("translink.emme.util")
        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

        ## mo836-mo871 - Purpose x AutoOwnership
        specs = []
        mo_result_num = 836
        for mo_num in range(404, 836, 12):
            expression = "0"
            for x in range(0, 12):
                expression = expression + "+ mo" + str(mo_num + x)
            specs.append(util.matrix_spec("mo" + str(mo_result_num), expression))
            mo_result_num = mo_result_num + 1
        report = compute_matrix(specs)

        ## mo872-mo898 - Purpose x IncomeCategory
        specs = []
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
                specs.append(util.matrix_spec("mo" + str(mo_result_num), expression))
                mo_result_num = mo_result_num + 1
        report = compute_matrix(specs)

    @_m.logbook_trace("Calibration")
    def Calibration(self, Calibration_Factors):
        util = _m.Modeller().tool("translink.emme.util")
        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

        specs = []
        for i in range(1, 432):
            expression = "0"
            for x in range(1, 15):
                expression = expression + " + (gy(p).eq." + str(x) + ")*" + Calibration_Factors[i][x + 5]
            expression = "mo" + str(403 + i) + "*(" + expression + ")"
            result = "mo" + str(403 + i)
            specs.append(util.matrix_spec(result, expression))

        report = compute_matrix(specs)

    ##  mo404-mo835 Performs the actual matrix calculation from the LandUse 'mo's with the TripRates for the various trip purposes
    @_m.logbook_trace("Perform Matrix calculations")
    def TripProduction(self, TripRate_Data, FirstResultMoNum):
        util = _m.Modeller().tool("translink.emme.util")
        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

        ## Loop to do the expression calculations
        specs = []
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
                specs.append(util.matrix_spec(result, expression))
                mo_result_num = mo_result_num + 1

        report = compute_matrix(specs)

    @_m.logbook_trace("Store_CalibrationFactors")
    def Store_CalibrationFactors(self, CalibrationFactors):
        with open(CalibrationFactors, 'rb') as f:
            reader = csv.reader(f, dialect='excel')
            header = reader.next()
            data = [header]
            for row in reader:
                data.append(row)
        return data

    ##    Stores the triprates into a data structure and return it
    @_m.logbook_trace("Store_TripRates")
    def Store_TripRates(self, TripRateFile):
        with open(TripRateFile, 'rb') as f:
            reader = csv.reader(f, dialect='excel')
            header = reader.next()
            data = [header]
            for row in reader:
                data.append(row)
        return data

    ##    Batches in the batchin file
    @_m.logbook_trace("Matrix Batchin")
    def Matrix_Batchins(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        util.initmat(eb, "mo404", "p1010", "Produc WkW0LA0", 0)
        util.initmat(eb, "mo405", "p1110", "Produc WkW1LA0", 0)
        util.initmat(eb, "mo406", "p1210", "Produc WkW2LA0", 0)
        util.initmat(eb, "mo407", "p1310", "Produc WkW3+LA0", 0)
        util.initmat(eb, "mo408", "p1020", "Produc WkW0MA0", 0)
        util.initmat(eb, "mo409", "p1120", "Produc WkW1MA0", 0)
        util.initmat(eb, "mo410", "p1220", "Produc WkW2MA0", 0)
        util.initmat(eb, "mo411", "p1320", "Produc WkW3+MA0", 0)
        util.initmat(eb, "mo412", "p1030", "Produc WkW0HA0", 0)
        util.initmat(eb, "mo413", "p1130", "Produc WkW1HA0", 0)
        util.initmat(eb, "mo414", "p1230", "Produc WkW2HA0", 0)
        util.initmat(eb, "mo415", "p1330", "Produc WkW3+HA0", 0)
        util.initmat(eb, "mo416", "p1011", "Produc WkW0LA1", 0)
        util.initmat(eb, "mo417", "p1111", "Produc WkW1LA1", 0)
        util.initmat(eb, "mo418", "p1211", "Produc WkW2LA1", 0)
        util.initmat(eb, "mo419", "p1311", "Produc WkW3+LA1", 0)
        util.initmat(eb, "mo420", "p1021", "Produc WkW0MA1", 0)
        util.initmat(eb, "mo421", "p1121", "Produc WkW1MA1", 0)
        util.initmat(eb, "mo422", "p1221", "Produc WkW2MA1", 0)
        util.initmat(eb, "mo423", "p1321", "Produc WkW3+MA1", 0)
        util.initmat(eb, "mo424", "p1031", "Produc WkW0HA1", 0)
        util.initmat(eb, "mo425", "p1131", "Produc WkW1HA1", 0)
        util.initmat(eb, "mo426", "p1231", "Produc WkW2HA1", 0)
        util.initmat(eb, "mo427", "p1331", "Produc WkW3+HA1", 0)
        util.initmat(eb, "mo428", "p1012", "Produc WkW0LA2", 0)
        util.initmat(eb, "mo429", "p1112", "Produc WkW1LA2", 0)
        util.initmat(eb, "mo430", "p1212", "Produc WkW2LA2", 0)
        util.initmat(eb, "mo431", "p1312", "Produc WkW3+LA2", 0)
        util.initmat(eb, "mo432", "p1022", "Produc WkW0MA2", 0)
        util.initmat(eb, "mo433", "p1122", "Produc WkW1MA2", 0)
        util.initmat(eb, "mo434", "p1222", "Produc WkW2MA2", 0)
        util.initmat(eb, "mo435", "p1322", "Produc WkW3+MA2", 0)
        util.initmat(eb, "mo436", "p1032", "Produc WkW0HA2", 0)
        util.initmat(eb, "mo437", "p1132", "Produc WkW1HA2", 0)
        util.initmat(eb, "mo438", "p1232", "Produc WkW2HA2", 0)
        util.initmat(eb, "mo439", "p1332", "Produc WkW3+HA2", 0)
        util.initmat(eb, "mo440", "p1013", "Produc WkW0LA3+", 0)
        util.initmat(eb, "mo441", "p1113", "Produc WkW1LA3+", 0)
        util.initmat(eb, "mo442", "p1213", "Produc WkW2LA3+", 0)
        util.initmat(eb, "mo443", "p1313", "Produc WkW3+LA3+", 0)
        util.initmat(eb, "mo444", "p1023", "Produc WkW0MA3+", 0)
        util.initmat(eb, "mo445", "p1123", "Produc WkW1MA3+", 0)
        util.initmat(eb, "mo446", "p1223", "Produc WkW2MA3+", 0)
        util.initmat(eb, "mo447", "p1323", "Produc WkW3+MA3+", 0)
        util.initmat(eb, "mo448", "p1033", "Produc WkW0HA3+", 0)
        util.initmat(eb, "mo449", "p1133", "Produc WkW1HA3+", 0)
        util.initmat(eb, "mo450", "p1233", "Produc WkW2HA3+", 0)
        util.initmat(eb, "mo451", "p1333", "Produc WkW3+HA3+", 0)
        util.initmat(eb, "mo452", "p8010", "Produc NwW0LA0", 0)
        util.initmat(eb, "mo453", "p8110", "Produc NwW1LA0", 0)
        util.initmat(eb, "mo454", "p8210", "Produc NwW2LA0", 0)
        util.initmat(eb, "mo455", "p8310", "Produc NwW3+LA0", 0)
        util.initmat(eb, "mo456", "p8020", "Produc NwW0MA0", 0)
        util.initmat(eb, "mo457", "p8120", "Produc NwW1MA0", 0)
        util.initmat(eb, "mo458", "p8220", "Produc NwW2MA0", 0)
        util.initmat(eb, "mo459", "p8320", "Produc NwW3+MA0", 0)
        util.initmat(eb, "mo460", "p8030", "Produc NwW0HA0", 0)
        util.initmat(eb, "mo461", "p8130", "Produc NwW1HA0", 0)
        util.initmat(eb, "mo462", "p8230", "Produc NwW2HA0", 0)
        util.initmat(eb, "mo463", "p8330", "Produc NwW3+HA0", 0)
        util.initmat(eb, "mo464", "p8011", "Produc NwW0LA1", 0)
        util.initmat(eb, "mo465", "p8111", "Produc NwW1LA1", 0)
        util.initmat(eb, "mo466", "p8211", "Produc NwW2LA1", 0)
        util.initmat(eb, "mo467", "p8311", "Produc NwW3+LA1", 0)
        util.initmat(eb, "mo468", "p8021", "Produc NwW0MA1", 0)
        util.initmat(eb, "mo469", "p8121", "Produc NwW1MA1", 0)
        util.initmat(eb, "mo470", "p8221", "Produc NwW2MA1", 0)
        util.initmat(eb, "mo471", "p8321", "Produc NwW3+MA1", 0)
        util.initmat(eb, "mo472", "p8031", "Produc NwW0HA1", 0)
        util.initmat(eb, "mo473", "p8131", "Produc NwW1HA1", 0)
        util.initmat(eb, "mo474", "p8231", "Produc NwW2HA1", 0)
        util.initmat(eb, "mo475", "p8331", "Produc NwW3+HA1", 0)
        util.initmat(eb, "mo476", "p8012", "Produc NwW0LA2", 0)
        util.initmat(eb, "mo477", "p8112", "Produc NwW1LA2", 0)
        util.initmat(eb, "mo478", "p8212", "Produc NwW2LA2", 0)
        util.initmat(eb, "mo479", "p8312", "Produc NwW3+LA2", 0)
        util.initmat(eb, "mo480", "p8022", "Produc NwW0MA2", 0)
        util.initmat(eb, "mo481", "p8122", "Produc NwW1MA2", 0)
        util.initmat(eb, "mo482", "p8222", "Produc NwW2MA2", 0)
        util.initmat(eb, "mo483", "p8322", "Produc NwW3+MA2", 0)
        util.initmat(eb, "mo484", "p8032", "Produc NwW0HA2", 0)
        util.initmat(eb, "mo485", "p8132", "Produc NwW1HA2", 0)
        util.initmat(eb, "mo486", "p8232", "Produc NwW2HA2", 0)
        util.initmat(eb, "mo487", "p8332", "Produc NwW3+HA2", 0)
        util.initmat(eb, "mo488", "p8013", "Produc NwW0LA3+", 0)
        util.initmat(eb, "mo489", "p8113", "Produc NwW1LA3+", 0)
        util.initmat(eb, "mo490", "p8213", "Produc NwW2LA3+", 0)
        util.initmat(eb, "mo491", "p8313", "Produc NwW3+LA3+", 0)
        util.initmat(eb, "mo492", "p8023", "Produc NwW0MA3+", 0)
        util.initmat(eb, "mo493", "p8123", "Produc NwW1MA3+", 0)
        util.initmat(eb, "mo494", "p8223", "Produc NwW2MA3+", 0)
        util.initmat(eb, "mo495", "p8323", "Produc NwW3+MA3+", 0)
        util.initmat(eb, "mo496", "p8033", "Produc NwW0HA3+", 0)
        util.initmat(eb, "mo497", "p8133", "Produc NwW1HA3+", 0)
        util.initmat(eb, "mo498", "p8233", "Produc NwW2HA3+", 0)
        util.initmat(eb, "mo499", "p8333", "Produc NwW3+HA3+", 0)
        util.initmat(eb, "mo500", "p2110", "Produc UvH1LA0", 0)
        util.initmat(eb, "mo501", "p2210", "Produc UvH2LA0", 0)
        util.initmat(eb, "mo502", "p2310", "Produc UvH3LA0", 0)
        util.initmat(eb, "mo503", "p2410", "Produc UvH4+LA0", 0)
        util.initmat(eb, "mo504", "p2120", "Produc UvH1MA0", 0)
        util.initmat(eb, "mo505", "p2220", "Produc UvH2MA0", 0)
        util.initmat(eb, "mo506", "p2320", "Produc UvH3MA0", 0)
        util.initmat(eb, "mo507", "p2420", "Produc UvH4+MA0", 0)
        util.initmat(eb, "mo508", "p2130", "Produc UvH1HA0", 0)
        util.initmat(eb, "mo509", "p2230", "Produc UvH2HA0", 0)
        util.initmat(eb, "mo510", "p2330", "Produc UvH3HA0", 0)
        util.initmat(eb, "mo511", "p2430", "Produc UvH4+HA0", 0)
        util.initmat(eb, "mo512", "p2111", "Produc UvH1LA1", 0)
        util.initmat(eb, "mo513", "p2211", "Produc UvH2LA1", 0)
        util.initmat(eb, "mo514", "p2311", "Produc UvH3LA1", 0)
        util.initmat(eb, "mo515", "p2411", "Produc UvH4+LA1", 0)
        util.initmat(eb, "mo516", "p2121", "Produc UvH1MA1", 0)
        util.initmat(eb, "mo517", "p2221", "Produc UvH2MA1", 0)
        util.initmat(eb, "mo518", "p2321", "Produc UvH3MA1", 0)
        util.initmat(eb, "mo519", "p2421", "Produc UvH4+MA1", 0)
        util.initmat(eb, "mo520", "p2131", "Produc UvH1HA1", 0)
        util.initmat(eb, "mo521", "p2231", "Produc UvH2HA1", 0)
        util.initmat(eb, "mo522", "p2331", "Produc UvH3HA1", 0)
        util.initmat(eb, "mo523", "p2431", "Produc UvH4+HA1", 0)
        util.initmat(eb, "mo524", "p2112", "Produc UvH1LA2", 0)
        util.initmat(eb, "mo525", "p2212", "Produc UvH2LA2", 0)
        util.initmat(eb, "mo526", "p2312", "Produc UvH3LA2", 0)
        util.initmat(eb, "mo527", "p2412", "Produc UvH4+LA2", 0)
        util.initmat(eb, "mo528", "p2122", "Produc UvH1MA2", 0)
        util.initmat(eb, "mo529", "p2222", "Produc UvH2MA2", 0)
        util.initmat(eb, "mo530", "p2322", "Produc UvH3MA2", 0)
        util.initmat(eb, "mo531", "p2422", "Produc UvH4+MA2", 0)
        util.initmat(eb, "mo532", "p2132", "Produc UvH1HA2", 0)
        util.initmat(eb, "mo533", "p2232", "Produc UvH2HA2", 0)
        util.initmat(eb, "mo534", "p2332", "Produc UvH3HA2", 0)
        util.initmat(eb, "mo535", "p2432", "Produc UvH4+HA2", 0)
        util.initmat(eb, "mo536", "p2113", "Produc UvH1LA3+", 0)
        util.initmat(eb, "mo537", "p2213", "Produc UvH2LA3+", 0)
        util.initmat(eb, "mo538", "p2313", "Produc UvH3LA3+", 0)
        util.initmat(eb, "mo539", "p2413", "Produc UvH4+LA3+", 0)
        util.initmat(eb, "mo540", "p2123", "Produc UvH1MA3+", 0)
        util.initmat(eb, "mo541", "p2223", "Produc UvH2MA3+", 0)
        util.initmat(eb, "mo542", "p2323", "Produc UvH3MA3+", 0)
        util.initmat(eb, "mo543", "p2423", "Produc UvH4+MA3+", 0)
        util.initmat(eb, "mo544", "p2133", "Produc UvH1HA3+", 0)
        util.initmat(eb, "mo545", "p2233", "Produc UvH2HA3+", 0)
        util.initmat(eb, "mo546", "p2333", "Produc UvH3HA3+", 0)
        util.initmat(eb, "mo547", "p2433", "Produc UvH4+HA3+", 0)
        util.initmat(eb, "mo548", "p3110", "Produc ScH1LA0", 0)
        util.initmat(eb, "mo549", "p3210", "Produc ScH2LA0", 0)
        util.initmat(eb, "mo550", "p3310", "Produc ScH3LA0", 0)
        util.initmat(eb, "mo551", "p3410", "Produc ScH4+LA0", 0)
        util.initmat(eb, "mo552", "p3120", "Produc ScH1MA0", 0)
        util.initmat(eb, "mo553", "p3220", "Produc ScH2MA0", 0)
        util.initmat(eb, "mo554", "p3320", "Produc ScH3MA0", 0)
        util.initmat(eb, "mo555", "p3420", "Produc ScH4+MA0", 0)
        util.initmat(eb, "mo556", "p3130", "Produc ScH1HA0", 0)
        util.initmat(eb, "mo557", "p3230", "Produc ScH2HA0", 0)
        util.initmat(eb, "mo558", "p3330", "Produc ScH3HA0", 0)
        util.initmat(eb, "mo559", "p3430", "Produc ScH4+HA0", 0)
        util.initmat(eb, "mo560", "p3111", "Produc ScH1LA1", 0)
        util.initmat(eb, "mo561", "p3211", "Produc ScH2LA1", 0)
        util.initmat(eb, "mo562", "p3311", "Produc ScH3LA1", 0)
        util.initmat(eb, "mo563", "p3411", "Produc ScH4+LA1", 0)
        util.initmat(eb, "mo564", "p3121", "Produc ScH1MA1", 0)
        util.initmat(eb, "mo565", "p3221", "Produc ScH2MA1", 0)
        util.initmat(eb, "mo566", "p3321", "Produc ScH3MA1", 0)
        util.initmat(eb, "mo567", "p3421", "Produc ScH4+MA1", 0)
        util.initmat(eb, "mo568", "p3131", "Produc ScH1HA1", 0)
        util.initmat(eb, "mo569", "p3231", "Produc ScH2HA1", 0)
        util.initmat(eb, "mo570", "p3331", "Produc ScH3HA1", 0)
        util.initmat(eb, "mo571", "p3431", "Produc ScH4+HA1", 0)
        util.initmat(eb, "mo572", "p3112", "Produc ScH1LA2", 0)
        util.initmat(eb, "mo573", "p3212", "Produc ScH2LA2", 0)
        util.initmat(eb, "mo574", "p3312", "Produc ScH3LA2", 0)
        util.initmat(eb, "mo575", "p3412", "Produc ScH4+LA2", 0)
        util.initmat(eb, "mo576", "p3122", "Produc ScH1MA2", 0)
        util.initmat(eb, "mo577", "p3222", "Produc ScH2MA2", 0)
        util.initmat(eb, "mo578", "p3322", "Produc ScH3MA2", 0)
        util.initmat(eb, "mo579", "p3422", "Produc ScH4+MA2", 0)
        util.initmat(eb, "mo580", "p3132", "Produc ScH1HA2", 0)
        util.initmat(eb, "mo581", "p3232", "Produc ScH2HA2", 0)
        util.initmat(eb, "mo582", "p3332", "Produc ScH3HA2", 0)
        util.initmat(eb, "mo583", "p3432", "Produc ScH4+HA2", 0)
        util.initmat(eb, "mo584", "p3113", "Produc ScH1LA3+", 0)
        util.initmat(eb, "mo585", "p3213", "Produc ScH2LA3+", 0)
        util.initmat(eb, "mo586", "p3313", "Produc ScH3LA3+", 0)
        util.initmat(eb, "mo587", "p3413", "Produc ScH4+LA3+", 0)
        util.initmat(eb, "mo588", "p3123", "Produc ScH1MA3+", 0)
        util.initmat(eb, "mo589", "p3223", "Produc ScH2MA3+", 0)
        util.initmat(eb, "mo590", "p3323", "Produc ScH3MA3+", 0)
        util.initmat(eb, "mo591", "p3423", "Produc ScH4+MA3+", 0)
        util.initmat(eb, "mo592", "p3133", "Produc ScH1HA3+", 0)
        util.initmat(eb, "mo593", "p3233", "Produc ScH2HA3+", 0)
        util.initmat(eb, "mo594", "p3333", "Produc ScH3HA3+", 0)
        util.initmat(eb, "mo595", "p3433", "Produc ScH4+HA3+", 0)
        util.initmat(eb, "mo596", "p4110", "Produc ShH1LA0", 0)
        util.initmat(eb, "mo597", "p4210", "Produc ShH2LA0", 0)
        util.initmat(eb, "mo598", "p4310", "Produc ShH3LA0", 0)
        util.initmat(eb, "mo599", "p4410", "Produc ShH4+LA0", 0)
        util.initmat(eb, "mo600", "p4120", "Produc ShH1MA0", 0)
        util.initmat(eb, "mo601", "p4220", "Produc ShH2MA0", 0)
        util.initmat(eb, "mo602", "p4320", "Produc ShH3MA0", 0)
        util.initmat(eb, "mo603", "p4420", "Produc ShH4+MA0", 0)
        util.initmat(eb, "mo604", "p4130", "Produc ShH1HA0", 0)
        util.initmat(eb, "mo605", "p4230", "Produc ShH2HA0", 0)
        util.initmat(eb, "mo606", "p4330", "Produc ShH3HA0", 0)
        util.initmat(eb, "mo607", "p4430", "Produc ShH4+HA0", 0)
        util.initmat(eb, "mo608", "p4111", "Produc ShH1LA1", 0)
        util.initmat(eb, "mo609", "p4211", "Produc ShH2LA1", 0)
        util.initmat(eb, "mo610", "p4311", "Produc ShH3LA1", 0)
        util.initmat(eb, "mo611", "p4411", "Produc ShH4+LA1", 0)
        util.initmat(eb, "mo612", "p4121", "Produc ShH1MA1", 0)
        util.initmat(eb, "mo613", "p4221", "Produc ShH2MA1", 0)
        util.initmat(eb, "mo614", "p4321", "Produc ShH3MA1", 0)
        util.initmat(eb, "mo615", "p4421", "Produc ShH4+MA1", 0)
        util.initmat(eb, "mo616", "p4131", "Produc ShH1HA1", 0)
        util.initmat(eb, "mo617", "p4231", "Produc ShH2HA1", 0)
        util.initmat(eb, "mo618", "p4331", "Produc ShH3HA1", 0)
        util.initmat(eb, "mo619", "p4431", "Produc ShH4+HA1", 0)
        util.initmat(eb, "mo620", "p4112", "Produc ShH1LA2", 0)
        util.initmat(eb, "mo621", "p4212", "Produc ShH2LA2", 0)
        util.initmat(eb, "mo622", "p4312", "Produc ShH3LA2", 0)
        util.initmat(eb, "mo623", "p4412", "Produc ShH4+LA2", 0)
        util.initmat(eb, "mo624", "p4122", "Produc ShH1MA2", 0)
        util.initmat(eb, "mo625", "p4222", "Produc ShH2MA2", 0)
        util.initmat(eb, "mo626", "p4322", "Produc ShH3MA2", 0)
        util.initmat(eb, "mo627", "p4422", "Produc ShH4+MA2", 0)
        util.initmat(eb, "mo628", "p4132", "Produc ShH1HA2", 0)
        util.initmat(eb, "mo629", "p4232", "Produc ShH2HA2", 0)
        util.initmat(eb, "mo630", "p4332", "Produc ShH3HA2", 0)
        util.initmat(eb, "mo631", "p4432", "Produc ShH4+HA2", 0)
        util.initmat(eb, "mo632", "p4113", "Produc ShH1LA3+", 0)
        util.initmat(eb, "mo633", "p4213", "Produc ShH2LA3+", 0)
        util.initmat(eb, "mo634", "p4313", "Produc ShH3LA3+", 0)
        util.initmat(eb, "mo635", "p4413", "Produc ShH4+LA3+", 0)
        util.initmat(eb, "mo636", "p4123", "Produc ShH1MA3+", 0)
        util.initmat(eb, "mo637", "p4223", "Produc ShH2MA3+", 0)
        util.initmat(eb, "mo638", "p4323", "Produc ShH3MA3+", 0)
        util.initmat(eb, "mo639", "p4423", "Produc ShH4+MA3+", 0)
        util.initmat(eb, "mo640", "p4133", "Produc ShH1HA3+", 0)
        util.initmat(eb, "mo641", "p4233", "Produc ShH2HA3+", 0)
        util.initmat(eb, "mo642", "p4333", "Produc ShH3HA3+", 0)
        util.initmat(eb, "mo643", "p4433", "Produc ShH4+HA3+", 0)
        util.initmat(eb, "mo644", "p5110", "Produc PBH1LA0", 0)
        util.initmat(eb, "mo645", "p5210", "Produc PBH2LA0", 0)
        util.initmat(eb, "mo646", "p5310", "Produc PBH3LA0", 0)
        util.initmat(eb, "mo647", "p5410", "Produc PBH4+LA0", 0)
        util.initmat(eb, "mo648", "p5120", "Produc PBH1MA0", 0)
        util.initmat(eb, "mo649", "p5220", "Produc PBH2MA0", 0)
        util.initmat(eb, "mo650", "p5320", "Produc PBH3MA0", 0)
        util.initmat(eb, "mo651", "p5420", "Produc PBH4+MA0", 0)
        util.initmat(eb, "mo652", "p5130", "Produc PBH1HA0", 0)
        util.initmat(eb, "mo653", "p5230", "Produc PBH2HA0", 0)
        util.initmat(eb, "mo654", "p5330", "Produc PBH3HA0", 0)
        util.initmat(eb, "mo655", "p5430", "Produc PBH4+HA0", 0)
        util.initmat(eb, "mo656", "p5111", "Produc PBH1LA1", 0)
        util.initmat(eb, "mo657", "p5211", "Produc PBH2LA1", 0)
        util.initmat(eb, "mo658", "p5311", "Produc PBH3LA1", 0)
        util.initmat(eb, "mo659", "p5411", "Produc PBH4+LA1", 0)
        util.initmat(eb, "mo660", "p5121", "Produc PBH1MA1", 0)
        util.initmat(eb, "mo661", "p5221", "Produc PBH2MA1", 0)
        util.initmat(eb, "mo662", "p5321", "Produc PBH3MA1", 0)
        util.initmat(eb, "mo663", "p5421", "Produc PBH4+MA1", 0)
        util.initmat(eb, "mo664", "p5131", "Produc PBH1HA1", 0)
        util.initmat(eb, "mo665", "p5231", "Produc PBH2HA1", 0)
        util.initmat(eb, "mo666", "p5331", "Produc PBH3HA1", 0)
        util.initmat(eb, "mo667", "p5431", "Produc PBH4+HA1", 0)
        util.initmat(eb, "mo668", "p5112", "Produc PBH1LA2", 0)
        util.initmat(eb, "mo669", "p5212", "Produc PBH2LA2", 0)
        util.initmat(eb, "mo670", "p5312", "Produc PBH3LA2", 0)
        util.initmat(eb, "mo671", "p5412", "Produc PBH4+LA2", 0)
        util.initmat(eb, "mo672", "p5122", "Produc PBH1MA2", 0)
        util.initmat(eb, "mo673", "p5222", "Produc PBH2MA2", 0)
        util.initmat(eb, "mo674", "p5322", "Produc PBH3MA2", 0)
        util.initmat(eb, "mo675", "p5422", "Produc PBH4+MA2", 0)
        util.initmat(eb, "mo676", "p5132", "Produc PBH1HA2", 0)
        util.initmat(eb, "mo677", "p5232", "Produc PBH2HA2", 0)
        util.initmat(eb, "mo678", "p5332", "Produc PBH3HA2", 0)
        util.initmat(eb, "mo679", "p5432", "Produc PBH4+HA2", 0)
        util.initmat(eb, "mo680", "p5113", "Produc PBH1LA3+", 0)
        util.initmat(eb, "mo681", "p5213", "Produc PBH2LA3+", 0)
        util.initmat(eb, "mo682", "p5313", "Produc PBH3LA3+", 0)
        util.initmat(eb, "mo683", "p5413", "Produc PBH4+LA3+", 0)
        util.initmat(eb, "mo684", "p5123", "Produc PBH1MA3+", 0)
        util.initmat(eb, "mo685", "p5223", "Produc PBH2MA3+", 0)
        util.initmat(eb, "mo686", "p5323", "Produc PBH3MA3+", 0)
        util.initmat(eb, "mo687", "p5423", "Produc PBH4+MA3+", 0)
        util.initmat(eb, "mo688", "p5133", "Produc PBH1HA3+", 0)
        util.initmat(eb, "mo689", "p5233", "Produc PBH2HA3+", 0)
        util.initmat(eb, "mo690", "p5333", "Produc PBH3HA3+", 0)
        util.initmat(eb, "mo691", "p5433", "Produc PBH4+HA3+", 0)
        util.initmat(eb, "mo692", "p6110", "Produc SoH1LA0", 0)
        util.initmat(eb, "mo693", "p6210", "Produc SoH2LA0", 0)
        util.initmat(eb, "mo694", "p6310", "Produc SoH3LA0", 0)
        util.initmat(eb, "mo695", "p6410", "Produc SoH4+LA0", 0)
        util.initmat(eb, "mo696", "p6120", "Produc SoH1MA0", 0)
        util.initmat(eb, "mo697", "p6220", "Produc SoH2MA0", 0)
        util.initmat(eb, "mo698", "p6320", "Produc SoH3MA0", 0)
        util.initmat(eb, "mo699", "p6420", "Produc SoH4+MA0", 0)
        util.initmat(eb, "mo700", "p6130", "Produc SoH1HA0", 0)
        util.initmat(eb, "mo701", "p6230", "Produc SoH2HA0", 0)
        util.initmat(eb, "mo702", "p6330", "Produc SoH3HA0", 0)
        util.initmat(eb, "mo703", "p6430", "Produc SoH4+HA0", 0)
        util.initmat(eb, "mo704", "p6111", "Produc SoH1LA1", 0)
        util.initmat(eb, "mo705", "p6211", "Produc SoH2LA1", 0)
        util.initmat(eb, "mo706", "p6311", "Produc SoH3LA1", 0)
        util.initmat(eb, "mo707", "p6411", "Produc SoH4+LA1", 0)
        util.initmat(eb, "mo708", "p6121", "Produc SoH1MA1", 0)
        util.initmat(eb, "mo709", "p6221", "Produc SoH2MA1", 0)
        util.initmat(eb, "mo710", "p6321", "Produc SoH3MA1", 0)
        util.initmat(eb, "mo711", "p6421", "Produc SoH4+MA1", 0)
        util.initmat(eb, "mo712", "p6131", "Produc SoH1HA1", 0)
        util.initmat(eb, "mo713", "p6231", "Produc SoH2HA1", 0)
        util.initmat(eb, "mo714", "p6331", "Produc SoH3HA1", 0)
        util.initmat(eb, "mo715", "p6431", "Produc SoH4+HA1", 0)
        util.initmat(eb, "mo716", "p6112", "Produc SoH1LA2", 0)
        util.initmat(eb, "mo717", "p6212", "Produc SoH2LA2", 0)
        util.initmat(eb, "mo718", "p6312", "Produc SoH3LA2", 0)
        util.initmat(eb, "mo719", "p6412", "Produc SoH4+LA2", 0)
        util.initmat(eb, "mo720", "p6122", "Produc SoH1MA2", 0)
        util.initmat(eb, "mo721", "p6222", "Produc SoH2MA2", 0)
        util.initmat(eb, "mo722", "p6322", "Produc SoH3MA2", 0)
        util.initmat(eb, "mo723", "p6422", "Produc SoH4+MA2", 0)
        util.initmat(eb, "mo724", "p6132", "Produc SoH1HA2", 0)
        util.initmat(eb, "mo725", "p6232", "Produc SoH2HA2", 0)
        util.initmat(eb, "mo726", "p6332", "Produc SoH3HA2", 0)
        util.initmat(eb, "mo727", "p6432", "Produc SoH4+HA2", 0)
        util.initmat(eb, "mo728", "p6113", "Produc SoH1LA3+", 0)
        util.initmat(eb, "mo729", "p6213", "Produc SoH2LA3+", 0)
        util.initmat(eb, "mo730", "p6313", "Produc SoH3LA3+", 0)
        util.initmat(eb, "mo731", "p6413", "Produc SoH4+LA3+", 0)
        util.initmat(eb, "mo732", "p6123", "Produc SoH1MA3+", 0)
        util.initmat(eb, "mo733", "p6223", "Produc SoH2MA3+", 0)
        util.initmat(eb, "mo734", "p6323", "Produc SoH3MA3+", 0)
        util.initmat(eb, "mo735", "p6423", "Produc SoH4+MA3+", 0)
        util.initmat(eb, "mo736", "p6133", "Produc SoH1HA3+", 0)
        util.initmat(eb, "mo737", "p6233", "Produc SoH2HA3+", 0)
        util.initmat(eb, "mo738", "p6333", "Produc SoH3HA3+", 0)
        util.initmat(eb, "mo739", "p6433", "Produc SoH4+HA3+", 0)
        util.initmat(eb, "mo740", "p7110", "Produc EcH1LA0", 0)
        util.initmat(eb, "mo741", "p7210", "Produc EcH2LA0", 0)
        util.initmat(eb, "mo742", "p7310", "Produc EcH3LA0", 0)
        util.initmat(eb, "mo743", "p7410", "Produc EcH4+LA0", 0)
        util.initmat(eb, "mo744", "p7120", "Produc EcH1MA0", 0)
        util.initmat(eb, "mo745", "p7220", "Produc EcH2MA0", 0)
        util.initmat(eb, "mo746", "p7320", "Produc EcH3MA0", 0)
        util.initmat(eb, "mo747", "p7420", "Produc EcH4+MA0", 0)
        util.initmat(eb, "mo748", "p7130", "Produc EcH1HA0", 0)
        util.initmat(eb, "mo749", "p7230", "Produc EcH2HA0", 0)
        util.initmat(eb, "mo750", "p7330", "Produc EcH3HA0", 0)
        util.initmat(eb, "mo751", "p7430", "Produc EcH4+HA0", 0)
        util.initmat(eb, "mo752", "p7111", "Produc EcH1LA1", 0)
        util.initmat(eb, "mo753", "p7211", "Produc EcH2LA1", 0)
        util.initmat(eb, "mo754", "p7311", "Produc EcH3LA1", 0)
        util.initmat(eb, "mo755", "p7411", "Produc EcH4+LA1", 0)
        util.initmat(eb, "mo756", "p7121", "Produc EcH1MA1", 0)
        util.initmat(eb, "mo757", "p7221", "Produc EcH2MA1", 0)
        util.initmat(eb, "mo758", "p7321", "Produc EcH3MA1", 0)
        util.initmat(eb, "mo759", "p7421", "Produc EcH4+MA1", 0)
        util.initmat(eb, "mo760", "p7131", "Produc EcH1HA1", 0)
        util.initmat(eb, "mo761", "p7231", "Produc EcH2HA1", 0)
        util.initmat(eb, "mo762", "p7331", "Produc EcH3HA1", 0)
        util.initmat(eb, "mo763", "p7431", "Produc EcH4+HA1", 0)
        util.initmat(eb, "mo764", "p7112", "Produc EcH1LA2", 0)
        util.initmat(eb, "mo765", "p7212", "Produc EcH2LA2", 0)
        util.initmat(eb, "mo766", "p7312", "Produc EcH3LA2", 0)
        util.initmat(eb, "mo767", "p7412", "Produc EcH4+LA2", 0)
        util.initmat(eb, "mo768", "p7122", "Produc EcH1MA2", 0)
        util.initmat(eb, "mo769", "p7222", "Produc EcH2MA2", 0)
        util.initmat(eb, "mo770", "p7322", "Produc EcH3MA2", 0)
        util.initmat(eb, "mo771", "p7422", "Produc EcH4+MA2", 0)
        util.initmat(eb, "mo772", "p7132", "Produc EcH1HA2", 0)
        util.initmat(eb, "mo773", "p7232", "Produc EcH2HA2", 0)
        util.initmat(eb, "mo774", "p7332", "Produc EcH3HA2", 0)
        util.initmat(eb, "mo775", "p7432", "Produc EcH4+HA2", 0)
        util.initmat(eb, "mo776", "p7113", "Produc EcH1LA3+", 0)
        util.initmat(eb, "mo777", "p7213", "Produc EcH2LA3+", 0)
        util.initmat(eb, "mo778", "p7313", "Produc EcH3LA3+", 0)
        util.initmat(eb, "mo779", "p7413", "Produc EcH4+LA3+", 0)
        util.initmat(eb, "mo780", "p7123", "Produc EcH1MA3+", 0)
        util.initmat(eb, "mo781", "p7223", "Produc EcH2MA3+", 0)
        util.initmat(eb, "mo782", "p7323", "Produc EcH3MA3+", 0)
        util.initmat(eb, "mo783", "p7423", "Produc EcH4+MA3+", 0)
        util.initmat(eb, "mo784", "p7133", "Produc EcH1HA3+", 0)
        util.initmat(eb, "mo785", "p7233", "Produc EcH2HA3+", 0)
        util.initmat(eb, "mo786", "p7333", "Produc EcH3HA3+", 0)
        util.initmat(eb, "mo787", "p7433", "Produc EcH4+HA3+", 0)
        util.initmat(eb, "mo788", "p9110", "Produc NoH1LA0", 0)
        util.initmat(eb, "mo789", "p9210", "Produc NoH2LA0", 0)
        util.initmat(eb, "mo790", "p9310", "Produc NoH3LA0", 0)
        util.initmat(eb, "mo791", "p9410", "Produc NoH4+LA0", 0)
        util.initmat(eb, "mo792", "p9120", "Produc NoH1MA0", 0)
        util.initmat(eb, "mo793", "p9220", "Produc NoH2MA0", 0)
        util.initmat(eb, "mo794", "p9320", "Produc NoH3MA0", 0)
        util.initmat(eb, "mo795", "p9420", "Produc NoH4+MA0", 0)
        util.initmat(eb, "mo796", "p9130", "Produc NoH1HA0", 0)
        util.initmat(eb, "mo797", "p9230", "Produc NoH2HA0", 0)
        util.initmat(eb, "mo798", "p9330", "Produc NoH3HA0", 0)
        util.initmat(eb, "mo799", "p9430", "Produc NoH4+HA0", 0)
        util.initmat(eb, "mo800", "p9111", "Produc NoH1LA1", 0)
        util.initmat(eb, "mo801", "p9211", "Produc NoH2LA1", 0)
        util.initmat(eb, "mo802", "p9311", "Produc NoH3LA1", 0)
        util.initmat(eb, "mo803", "p9411", "Produc NoH4+LA1", 0)
        util.initmat(eb, "mo804", "p9121", "Produc NoH1MA1", 0)
        util.initmat(eb, "mo805", "p9221", "Produc NoH2MA1", 0)
        util.initmat(eb, "mo806", "p9321", "Produc NoH3MA1", 0)
        util.initmat(eb, "mo807", "p9421", "Produc NoH4+MA1", 0)
        util.initmat(eb, "mo808", "p9131", "Produc NoH1HA1", 0)
        util.initmat(eb, "mo809", "p9231", "Produc NoH2HA1", 0)
        util.initmat(eb, "mo810", "p9331", "Produc NoH3HA1", 0)
        util.initmat(eb, "mo811", "p9431", "Produc NoH4+HA1", 0)
        util.initmat(eb, "mo812", "p9112", "Produc NoH1LA2", 0)
        util.initmat(eb, "mo813", "p9212", "Produc NoH2LA2", 0)
        util.initmat(eb, "mo814", "p9312", "Produc NoH3LA2", 0)
        util.initmat(eb, "mo815", "p9412", "Produc NoH4+LA2", 0)
        util.initmat(eb, "mo816", "p9122", "Produc NoH1MA2", 0)
        util.initmat(eb, "mo817", "p9222", "Produc NoH2MA2", 0)
        util.initmat(eb, "mo818", "p9322", "Produc NoH3MA2", 0)
        util.initmat(eb, "mo819", "p9422", "Produc NoH4+MA2", 0)
        util.initmat(eb, "mo820", "p9132", "Produc NoH1HA2", 0)
        util.initmat(eb, "mo821", "p9232", "Produc NoH2HA2", 0)
        util.initmat(eb, "mo822", "p9332", "Produc NoH3HA2", 0)
        util.initmat(eb, "mo823", "p9432", "Produc NoH4+HA2", 0)
        util.initmat(eb, "mo824", "p9113", "Produc NoH1LA3+", 0)
        util.initmat(eb, "mo825", "p9213", "Produc NoH2LA3+", 0)
        util.initmat(eb, "mo826", "p9313", "Produc NoH3LA3+", 0)
        util.initmat(eb, "mo827", "p9413", "Produc NoH4+LA3+", 0)
        util.initmat(eb, "mo828", "p9123", "Produc NoH1MA3+", 0)
        util.initmat(eb, "mo829", "p9223", "Produc NoH2MA3+", 0)
        util.initmat(eb, "mo830", "p9323", "Produc NoH3MA3+", 0)
        util.initmat(eb, "mo831", "p9423", "Produc NoH4+MA3+", 0)
        util.initmat(eb, "mo832", "p9133", "Produc NoH1HA3+", 0)
        util.initmat(eb, "mo833", "p9233", "Produc NoH2HA3+", 0)
        util.initmat(eb, "mo834", "p9333", "Produc NoH3HA3+", 0)
        util.initmat(eb, "mo835", "p9433", "Produc NoH4+HA3+", 0)
        util.initmat(eb, "mo836", "p1--0", "Produc WkA0", 0)
        util.initmat(eb, "mo837", "p1--1", "Produc WkA1", 0)
        util.initmat(eb, "mo838", "p1--2", "Produc WkA2", 0)
        util.initmat(eb, "mo839", "p1--3", "Produc WkA3+", 0)
        util.initmat(eb, "mo840", "p8--0", "Produc NwA0", 0)
        util.initmat(eb, "mo841", "p8--1", "Produc NwA1", 0)
        util.initmat(eb, "mo842", "p8--2", "Produc NwA2", 0)
        util.initmat(eb, "mo843", "p8--3", "Produc NwA3+", 0)
        util.initmat(eb, "mo844", "p2--0", "Produc UvA0", 0)
        util.initmat(eb, "mo845", "p2--1", "Produc UvA1", 0)
        util.initmat(eb, "mo846", "p2--2", "Produc UvA2", 0)
        util.initmat(eb, "mo847", "p2--3", "Produc UvA3+", 0)
        util.initmat(eb, "mo848", "p3--0", "Produc ScA0", 0)
        util.initmat(eb, "mo849", "p3--1", "Produc ScA1", 0)
        util.initmat(eb, "mo850", "p3--2", "Produc ScA2", 0)
        util.initmat(eb, "mo851", "p3--3", "Produc ScA3+", 0)
        util.initmat(eb, "mo852", "p4--0", "Produc ShA0", 0)
        util.initmat(eb, "mo853", "p4--1", "Produc ShA1", 0)
        util.initmat(eb, "mo854", "p4--2", "Produc ShA2", 0)
        util.initmat(eb, "mo855", "p4--3", "Produc ShA3+", 0)
        util.initmat(eb, "mo856", "p5--0", "Produc PBA0", 0)
        util.initmat(eb, "mo857", "p5--1", "Produc PBA1", 0)
        util.initmat(eb, "mo858", "p5--2", "Produc PBA2", 0)
        util.initmat(eb, "mo859", "p5--3", "Produc PBA3+", 0)
        util.initmat(eb, "mo860", "p6--0", "Produc SoA0", 0)
        util.initmat(eb, "mo861", "p6--1", "Produc SoA1", 0)
        util.initmat(eb, "mo862", "p6--2", "Produc SoA2", 0)
        util.initmat(eb, "mo863", "p6--3", "Produc SoA3+", 0)
        util.initmat(eb, "mo864", "p7--0", "Produc EcA0", 0)
        util.initmat(eb, "mo865", "p7--1", "Produc EcA1", 0)
        util.initmat(eb, "mo866", "p7--2", "Produc EcA2", 0)
        util.initmat(eb, "mo867", "p7--3", "Produc EcA3+", 0)
        util.initmat(eb, "mo868", "p9--0", "Produc NoA0", 0)
        util.initmat(eb, "mo869", "p9--1", "Produc NoA1", 0)
        util.initmat(eb, "mo870", "p9--2", "Produc NoA2", 0)
        util.initmat(eb, "mo871", "p9--3", "Produc NoA3+", 0)
        util.initmat(eb, "mo872", "p1-1-", "Produc WkL", 0)
        util.initmat(eb, "mo873", "p1-2-", "Produc WkM", 0)
        util.initmat(eb, "mo874", "p1-3-", "Produc WkH", 0)
        util.initmat(eb, "mo875", "p8-1-", "Produc NwL", 0)
        util.initmat(eb, "mo876", "p8-2-", "Produc NwM", 0)
        util.initmat(eb, "mo877", "p8-3-", "Produc NwH", 0)
        util.initmat(eb, "mo878", "p2-1-", "Produc UvL", 0)
        util.initmat(eb, "mo879", "p2-2-", "Produc UvM", 0)
        util.initmat(eb, "mo880", "p2-3-", "Produc UvH", 0)
        util.initmat(eb, "mo881", "p3-1-", "Produc ScL", 0)
        util.initmat(eb, "mo882", "p3-2-", "Produc ScM", 0)
        util.initmat(eb, "mo883", "p3-3-", "Produc ScH", 0)
        util.initmat(eb, "mo884", "p4-1-", "Produc ShL", 0)
        util.initmat(eb, "mo885", "p4-2-", "Produc ShM", 0)
        util.initmat(eb, "mo886", "p4-3-", "Produc ShH", 0)
        util.initmat(eb, "mo887", "p5-1-", "Produc PBL", 0)
        util.initmat(eb, "mo888", "p5-2-", "Produc PBM", 0)
        util.initmat(eb, "mo889", "p5-3-", "Produc PBH", 0)
        util.initmat(eb, "mo890", "p6-1-", "Produc SoL", 0)
        util.initmat(eb, "mo891", "p6-2-", "Produc SoM", 0)
        util.initmat(eb, "mo892", "p6-3-", "Produc SoH", 0)
        util.initmat(eb, "mo893", "p7-1-", "Produc EcL", 0)
        util.initmat(eb, "mo894", "p7-2-", "Produc EcM", 0)
        util.initmat(eb, "mo895", "p7-3-", "Produc EcH", 0)
        util.initmat(eb, "mo896", "p9-1-", "Produc NoL", 0)
        util.initmat(eb, "mo897", "p9-2-", "Produc NoM", 0)
        util.initmat(eb, "mo898", "p9-3-", "Produc NoH", 0)
        util.initmat(eb, "mo899", "s---0", "SegmentA0", 0)
        util.initmat(eb, "mo900", "s---1", "SegmentA1", 0)
        util.initmat(eb, "mo901", "s---2", "SegmentA2", 0)
        util.initmat(eb, "mo902", "s---3", "SegmentA3+", 0)
        util.initmat(eb, "mo903", "TotAu", "Total Number of Autos", 0)
        util.initmat(eb, "mo161", "p1-10", "ProducWkLA0", 0)
        util.initmat(eb, "mo162", "p1-20", "ProducWkMA0", 0)
        util.initmat(eb, "mo163", "p1-30", "ProducWkHA0", 0)
        util.initmat(eb, "mo164", "p1-11", "ProducWkLA1", 0)
        util.initmat(eb, "mo165", "p1-21", "ProducWkMA1", 0)
        util.initmat(eb, "mo166", "p1-31", "ProducWkHA1", 0)
        util.initmat(eb, "mo167", "p1-12", "ProducWkLA2", 0)
        util.initmat(eb, "mo168", "p1-22", "ProducWkMA2", 0)
        util.initmat(eb, "mo169", "p1-32", "ProducWkHA2", 0)
        util.initmat(eb, "mo170", "p1-13", "ProducWkLA3+", 0)
        util.initmat(eb, "mo171", "p1-23", "ProducWkMA3+", 0)
        util.initmat(eb, "mo172", "p1-33", "ProducWkHA3+", 0)
        util.initmat(eb, "mo173", "p8-10", "ProducNwLA0", 0)
        util.initmat(eb, "mo174", "p8-20", "ProducNwMA0", 0)
        util.initmat(eb, "mo175", "p8-30", "ProducNwHA0", 0)
        util.initmat(eb, "mo176", "p8-11", "ProducNwLA1", 0)
        util.initmat(eb, "mo177", "p8-21", "ProducNwMA1", 0)
        util.initmat(eb, "mo178", "p8-31", "ProducNwHA1", 0)
        util.initmat(eb, "mo179", "p8-12", "ProducNwLA2", 0)
        util.initmat(eb, "mo180", "p8-22", "ProducNwMA2", 0)
        util.initmat(eb, "mo181", "p8-32", "ProducNwHA2", 0)
        util.initmat(eb, "mo182", "p8-13", "ProducNwLA3+", 0)
        util.initmat(eb, "mo183", "p8-23", "ProducNwMA3+", 0)
        util.initmat(eb, "mo184", "p8-33", "ProducNwHA3+", 0)
        util.initmat(eb, "mo185", "p2-10", "ProducUvLA0", 0)
        util.initmat(eb, "mo186", "p2-20", "ProducUvMA0", 0)
        util.initmat(eb, "mo187", "p2-30", "ProducUvHA0", 0)
        util.initmat(eb, "mo188", "p2-11", "ProducUvLA1", 0)
        util.initmat(eb, "mo189", "p2-21", "ProducUvMA1", 0)
        util.initmat(eb, "mo190", "p2-31", "ProducUvHA1", 0)
        util.initmat(eb, "mo191", "p2-12", "ProducUvLA2", 0)
        util.initmat(eb, "mo192", "p2-22", "ProducUvMA2", 0)
        util.initmat(eb, "mo193", "p2-32", "ProducUvHA2", 0)
        util.initmat(eb, "mo194", "p2-13", "ProducUvLA3+", 0)
        util.initmat(eb, "mo195", "p2-23", "ProducUvMA3+", 0)
        util.initmat(eb, "mo196", "p2-33", "ProducUvHA3+", 0)
        util.initmat(eb, "mo197", "p3-10", "ProducScLA0", 0)
        util.initmat(eb, "mo198", "p3-20", "ProducScMA0", 0)
        util.initmat(eb, "mo199", "p3-30", "ProducScHA0", 0)
        util.initmat(eb, "mo200", "p3-11", "ProducScLA1", 0)
        util.initmat(eb, "mo201", "p3-21", "ProducScMA1", 0)
        util.initmat(eb, "mo202", "p3-31", "ProducScHA1", 0)
        util.initmat(eb, "mo203", "p3-12", "ProducScLA2", 0)
        util.initmat(eb, "mo204", "p3-22", "ProducScMA2", 0)
        util.initmat(eb, "mo205", "p3-32", "ProducScHA2", 0)
        util.initmat(eb, "mo206", "p3-13", "ProducScLA3+", 0)
        util.initmat(eb, "mo207", "p3-23", "ProducScMA3+", 0)
        util.initmat(eb, "mo208", "p3-33", "ProducScHA3+", 0)
        util.initmat(eb, "mo209", "p4-10", "ProducShLA0", 0)
        util.initmat(eb, "mo210", "p4-20", "ProducShMA0", 0)
        util.initmat(eb, "mo211", "p4-30", "ProducShHA0", 0)
        util.initmat(eb, "mo212", "p4-11", "ProducShLA1", 0)
        util.initmat(eb, "mo213", "p4-21", "ProducShMA1", 0)
        util.initmat(eb, "mo214", "p4-31", "ProducShHA1", 0)
        util.initmat(eb, "mo215", "p4-12", "ProducShLA2", 0)
        util.initmat(eb, "mo216", "p4-22", "ProducShMA2", 0)
        util.initmat(eb, "mo217", "p4-32", "ProducShHA2", 0)
        util.initmat(eb, "mo218", "p4-13", "ProducShLA3+", 0)
        util.initmat(eb, "mo219", "p4-23", "ProducShMA3+", 0)
        util.initmat(eb, "mo220", "p4-33", "ProducShHA3+", 0)
        util.initmat(eb, "mo221", "p5-10", "ProducPBLA0", 0)
        util.initmat(eb, "mo222", "p5-20", "ProducPBMA0", 0)
        util.initmat(eb, "mo223", "p5-30", "ProducPBHA0", 0)
        util.initmat(eb, "mo224", "p5-11", "ProducPBLA1", 0)
        util.initmat(eb, "mo225", "p5-21", "ProducPBMA1", 0)
        util.initmat(eb, "mo226", "p5-31", "ProducPBHA1", 0)
        util.initmat(eb, "mo227", "p5-12", "ProducPBLA2", 0)
        util.initmat(eb, "mo228", "p5-22", "ProducPBMA2", 0)
        util.initmat(eb, "mo229", "p5-32", "ProducPBHA2", 0)
        util.initmat(eb, "mo230", "p5-13", "ProducPBLA3+", 0)
        util.initmat(eb, "mo231", "p5-23", "ProducPBMA3+", 0)
        util.initmat(eb, "mo232", "p5-33", "ProducPBHA3+", 0)
        util.initmat(eb, "mo233", "p6-10", "ProducSoLA0", 0)
        util.initmat(eb, "mo234", "p6-20", "ProducSoMA0", 0)
        util.initmat(eb, "mo235", "p6-30", "ProducSoHA0", 0)
        util.initmat(eb, "mo236", "p6-11", "ProducSoLA1", 0)
        util.initmat(eb, "mo237", "p6-21", "ProducSoMA1", 0)
        util.initmat(eb, "mo238", "p6-31", "ProducSoHA1", 0)
        util.initmat(eb, "mo239", "p6-12", "ProducSoLA2", 0)
        util.initmat(eb, "mo240", "p6-22", "ProducSoMA2", 0)
        util.initmat(eb, "mo241", "p6-32", "ProducSoHA2", 0)
        util.initmat(eb, "mo242", "p6-13", "ProducSoLA3+", 0)
        util.initmat(eb, "mo243", "p6-23", "ProducSoMA3+", 0)
        util.initmat(eb, "mo244", "p6-33", "ProducSoHA3+", 0)
        util.initmat(eb, "mo245", "p7-10", "ProducEcLA0", 0)
        util.initmat(eb, "mo246", "p7-20", "ProducEcMA0", 0)
        util.initmat(eb, "mo247", "p7-30", "ProducEcHA0", 0)
        util.initmat(eb, "mo248", "p7-11", "ProducEcLA1", 0)
        util.initmat(eb, "mo249", "p7-21", "ProducEcMA1", 0)
        util.initmat(eb, "mo250", "p7-31", "ProducEcHA1", 0)
        util.initmat(eb, "mo251", "p7-12", "ProducEcLA2", 0)
        util.initmat(eb, "mo252", "p7-22", "ProducEcMA2", 0)
        util.initmat(eb, "mo253", "p7-32", "ProducEcHA2", 0)
        util.initmat(eb, "mo254", "p7-13", "ProducEcLA3+", 0)
        util.initmat(eb, "mo255", "p7-23", "ProducEcMA3+", 0)
        util.initmat(eb, "mo256", "p7-33", "ProducEcHA3+", 0)
        util.initmat(eb, "mo257", "p9-10", "ProducNoLA0", 0)
        util.initmat(eb, "mo258", "p9-20", "ProducNoMA0", 0)
        util.initmat(eb, "mo259", "p9-30", "ProducNoHA0", 0)
        util.initmat(eb, "mo260", "p9-11", "ProducNoLA1", 0)
        util.initmat(eb, "mo261", "p9-21", "ProducNoMA1", 0)
        util.initmat(eb, "mo262", "p9-31", "ProducNoHA1", 0)
        util.initmat(eb, "mo263", "p9-12", "ProducNoLA2", 0)
        util.initmat(eb, "mo264", "p9-22", "ProducNoMA2", 0)
        util.initmat(eb, "mo265", "p9-32", "ProducNoHA2", 0)
        util.initmat(eb, "mo266", "p9-13", "ProducNoLA3+", 0)
        util.initmat(eb, "mo267", "p9-23", "ProducNoMA3+", 0)
        util.initmat(eb, "mo268", "p9-33", "ProducNoHA3+", 0)
        util.initmat(eb, "mo904", "p1-1-", "ProducWkL", 0)
        util.initmat(eb, "mo905", "p1-2-", "ProducWkM", 0)
        util.initmat(eb, "mo906", "p1-3-", "ProducWkH", 0)
        util.initmat(eb, "mo907", "p8---", "ProducNw", 0)
        util.initmat(eb, "mo908", "p2---", "ProducUv", 0)
        util.initmat(eb, "mo909", "p3---", "ProducSc", 0)
        util.initmat(eb, "mo910", "p4---", "ProducSh", 0)
        util.initmat(eb, "mo911", "p5---", "ProducPB", 0)
        util.initmat(eb, "mo912", "p6---", "ProducSo", 0)
        util.initmat(eb, "mo913", "p7---", "ProducEc", 0)
        util.initmat(eb, "mo914", "p9---", "ProducNo", 0)
