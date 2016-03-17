##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.stage2.step2.tripattraction
##--Purpose: develop attraction totals for RTM generation model
##---------------------------------------------------------------------
import inro.modeller as _m
import csv
import os
import traceback as _traceback
from collections import defaultdict

class TripAttractions(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Trip Attractions"
        pb.description = "Collects trip rates and land use to output trip Attractions. <br> Then saves it to the databank and outputs data"
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

    @_m.logbook_trace("03-01 - Trip Attractions")
    def __call__(self, eb):
        PathHeader = os.path.dirname(eb.path) + "\\"
        CoefficientsPerGrouping = PathHeader + "03_TRIP_ATTRACTIONS/Inputs/32_COEFFICIENTS.csv"

        ##Batchin File
        self.Matrix_Batchins(eb)

        ## Creates Low and High Income Households from the 'mo' matrices
        self.CreateHouseholds_LowHighIncome_TotalPop()

        ##Store Coefficients
        coefficients_data = self.Store_Coefficients(CoefficientsPerGrouping)

        ## md31-md41 Calculate Trip Rates
        self.Calculate_TripRates(coefficients_data)

        ## Output results
        self.Output_Results(eb, CoefficientsPerGrouping)

    @_m.logbook_trace("Output Results")
    def Output_Results(self, eb, CoefficientsPerGrouping):
        util = _m.Modeller().tool("translink.emme.util")
        output_path = util.get_output_path(eb)
        output_file =    os.path.join(output_path, "03-01_OUTPUT_RESULTS.txt")
        output_file_gy = os.path.join(output_path, "03-01_OUTPUT_RESULTS_GY.txt")
        output_file_gu = os.path.join(output_path, "03-01_OUTPUT_RESULTS_GU.txt")
        output_file_csv = os.path.join(output_path, "03-01_OUTPUT_RESULTS_matrices.csv")

        list_of_matrices = ["md" + str(i) for i in range(5, 12) + range(20, 27) + range(31, 42)]
        util.export_csv(eb, list_of_matrices, output_file_csv)

        ##    List to hold matrix objects
        md_value = []

        ##    Loop to append all result matrices onto the variable 'md_value'
        for mo_num in [24, 25, 26] + range(31, 42):
            md_value.append(eb.matrix("md" + str(mo_num)))

        ##    Export matrices using the appended list of md_value matrices
        export_matrices = _m.Modeller().tool("inro.emme.data.matrix.export_matrices")

        ## Export all matrix data
        export_matrices(export_file=output_file,
                        field_separator=' ',
                        matrices=md_value,
                        export_format="PROMPT_DATA_FORMAT",
                        skip_default_values=True,
                        full_matrix_line_format="ONE_ENTRY_PER_LINE")

        ## Export matrix data aggregated to the gy ensemble
        export_matrices(export_file=output_file_gy,
                        field_separator=' ',
                        matrices=md_value,
                        partition_aggregation={'destinations': 'gy', 'operator': 'sum'},
                        export_format="PROMPT_DATA_FORMAT",
                        skip_default_values=True,
                        full_matrix_line_format="ONE_ENTRY_PER_LINE")

        ## Export matrix data aggregated to the gu ensemble
        export_matrices(export_file=output_file_gu,
                        field_separator=' ',
                        matrices=md_value,
                        partition_aggregation={'destinations': 'gu', 'operator': 'sum'},
                        export_format="PROMPT_DATA_FORMAT",
                        skip_default_values=True,
                        full_matrix_line_format="ONE_ENTRY_PER_LINE")

        for Output in [output_file, output_file_gy, output_file_gu]:
            f = open(Output, 'a')
            f.write("c ------Data Sources:\n")
            f.write("c " + CoefficientsPerGrouping + "\n")
            f.close()

    @_m.logbook_trace("Calculate_TripRates")
    def Calculate_TripRates(self, coefficients_data):
        util = _m.Modeller().tool("translink.emme.util")
        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

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
        purposes = ["HBWL", "HBWM", "HBWH", "NHBW", "HBU", "HBSCHO", "HBSHOP", "HBPB", "HBSOC", "HBESC", "NHBO"]
        specs = []
        for i in range(1, 15):
            gy = str(i)
            gy_value = "gy" + gy
            for j in range(0, len(purposes)):
                purpose_gy_coeff = coefficients_data[purposes[j]][gy]
                expression = "0"
                for x in Variable_Matrix:
                    expression = expression + " + " + purpose_gy_coeff[x[0]][0] + "*" + x[1]

                spec = util.matrix_spec("md" + str(j + 31), expression)
                spec["constraint"]["by_zone"] = {"origins": None, "destinations": gy_value}
                specs.append(spec)

        ## md31-md41 Remove negative values from Trip Rates
        for j in range(0, len(purposes)):
            mat = "md" + str(j + 31)
            specs.append(util.matrix_spec(mat, mat +".max.0"))

        report = compute_matrix(specs)

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
        util = _m.Modeller().tool("translink.emme.util")
        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

        specs = []

        specs.append(util.matrix_spec("md24", "mo365' + mo366' + mo367' + mo368'"))
        specs.append(util.matrix_spec("md25", "mo369' + mo370' + mo371' + mo372'"))
        specs.append(util.matrix_spec("md26", "mo373' + mo374' + mo375' + mo376'"))
        specs.append(util.matrix_spec("md20", "mo20'"))
        specs.append(util.matrix_spec("md27", "mo27'"))
        specs.append(util.matrix_spec("md28", "mo28'"))
        specs.append(util.matrix_spec("md13", "mo13'"))
        specs.append(util.matrix_spec("md17", "mo17'"))

        report = compute_matrix(specs)

    @_m.logbook_trace("Matrix Batchin")
    def Matrix_Batchins(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        year = util.get_year(eb)
        yr = year[2:]

        # Initialize transposes of some land use variables, kill this eventually
        util.initmat(eb, "md13", "BkSc", "Bike Score tpose", 0)
        util.initmat(eb, "md17", "Area", "Area m2 tpose", 0)
        util.initmat(eb, "md27", "WkPr", "Work Park tpose", 0)
        util.initmat(eb, "md28", "OtPk", "Other Park tpose", 0)

        util.initmat(eb, "md20", "PpTt" + yr, year + "_total_population", 0)
        util.initmat(eb, "md24", "HhLwIn", "Household Low Income", 0)
        util.initmat(eb, "md25", "HhMdIn", "Household Medium Income", 0)
        util.initmat(eb, "md26", "HhHiIn", "Household High Income", 0)
        util.initmat(eb, "md31", "aWkL", "AttracWkL", 0)
        util.initmat(eb, "md32", "aWkM", "AttracWkM", 0)
        util.initmat(eb, "md33", "aWkH", "AttracWkH", 0)
        util.initmat(eb, "md34", "aNw", "AttracNw", 0)
        util.initmat(eb, "md35", "aUv", "AttracUv", 0)
        util.initmat(eb, "md36", "aSc", "AttracSc", 0)
        util.initmat(eb, "md37", "aSh", "AttracSh", 0)
        util.initmat(eb, "md38", "aPB", "AttracPB", 0)
        util.initmat(eb, "md39", "aSo", "AttracSo", 0)
        util.initmat(eb, "md40", "aEc", "AttracEc", 0)
        util.initmat(eb, "md41", "aNo", "AttracNo", 0)
        util.initmat(eb, "md42", "aWkLf", "FactoredAttracWkL", 0)
        util.initmat(eb, "md43", "aWkMf", "FactoredAttracWkM", 0)
        util.initmat(eb, "md44", "aWkHf", "FactoredAttracWkH", 0)
        util.initmat(eb, "md45", "aNwf", "FactoredAttracNw", 0)
        util.initmat(eb, "md46", "aUvnf", "NOTFactoredAttracUv", 0)
        util.initmat(eb, "md47", "aScf", "FactoredAttracSc", 0)
        util.initmat(eb, "md48", "aShf", "FactoredAttracSh", 0)
        util.initmat(eb, "md49", "aPBf", "FactoredAttracPB", 0)
        util.initmat(eb, "md50", "aSof", "FactoredAttracSo", 0)
        util.initmat(eb, "md51", "aEcf", "FactoredAttracEc", 0)
        util.initmat(eb, "md52", "aNof", "FactoredAttracNo", 0)
        util.initmat(eb, "mo915", "p2-10f", "FactoredProducUvLA0", 0)
        util.initmat(eb, "mo916", "p2-20f", "FactoredProducUvMA0", 0)
        util.initmat(eb, "mo917", "p2-30f", "FactoredProducUvHA0", 0)
        util.initmat(eb, "mo918", "p2-11f", "FactoredProducUvLA1", 0)
        util.initmat(eb, "mo919", "p2-21f", "FactoredProducUvMA1", 0)
        util.initmat(eb, "mo920", "p2-31f", "FactoredProducUvHA1", 0)
        util.initmat(eb, "mo921", "p2-12f", "FactoredProducUvLA2", 0)
        util.initmat(eb, "mo922", "p2-22f", "FactoredProducUvMA2", 0)
        util.initmat(eb, "mo923", "p2-32f", "FactoredProducUvHA2", 0)
        util.initmat(eb, "mo924", "p2-13f", "FactoredProducUvLA3+", 0)
        util.initmat(eb, "mo925", "p2-23f", "FactoredProducUvMA3+", 0)
        util.initmat(eb, "mo926", "p2-33f", "FactoredProducUvHA3+", 0)
