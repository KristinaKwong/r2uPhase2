##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage2.step3.factoredtripattraction
##--Purpose: factor attraction totals for RTM generation model
##---------------------------------------------------------------------
import inro.modeller as _m
import os
import traceback as _traceback

class FactoredTripAttractions(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Trip Attractions"
        pb.description = "Factored Trip Attractions<br>Data Needed from a prior Module:<br>mo161-mo265"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)
        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            self.__call__(_m.Modeller().emmebank)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("03-02 - Factored Trip Attractions")
    def __call__(self, eb):
        ## Define variables to store/locate values.
        purpose_list = ["HBWL", "HBWM", "HBWH", "NHBW", "HBU", "HBSCHO", "HBSHOP", "HBPB", "HBSOC", "HBESC", "NHBO"]
        purpose_factors = {"HBWL": {"moSum": 0, "mdSum": 0, "Factor": 0},
                           "HBWM": {"moSum": 0, "mdSum": 0, "Factor": 0},
                           "HBWH": {"moSum": 0, "mdSum": 0, "Factor": 0},
                           "NHBW": {"moSum": 0, "mdSum": 0, "Factor": 0},
                           "HBU": {"moSum": 0, "mdSum": 0, "Factor": 0},
                           "HBSCHO": {"moSum": 0, "mdSum": 0, "Factor": 0},
                           "HBSHOP": {"moSum": 0, "mdSum": 0, "Factor": 0},
                           "HBPB": {"moSum": 0, "mdSum": 0, "Factor": 0},
                           "HBSOC": {"moSum": 0, "mdSum": 0, "Factor": 0},
                           "HBESC": {"moSum": 0, "mdSum": 0, "Factor": 0},
                           "NHBO": {"moSum": 0, "mdSum": 0, "Factor": 0}
        }

        ## Calculates factors from "md" to "mo" segmentation
        purpose_factors = self.Calculate_Factors(purpose_list, purpose_factors)

        ## Apply Factors for the md to scale them to equal to the sum of the respective "mo" segments
        self.Apply_Factors(purpose_list, purpose_factors)

        ## Output results
        self.Output_Results(eb)

    @_m.logbook_trace("Output Results")
    def Output_Results(self, eb):
        util = _m.Modeller().tool("translink.emme.util")
        output_path = util.get_output_path(eb)
        output_file =    os.path.join(output_path, "03-02_OUTPUT_RESULTS.txt")
        output_file_gy = os.path.join(output_path, "03-02_OUTPUT_RESULTS_GY.txt")
        output_file_gu = os.path.join(output_path, "03-02_OUTPUT_RESULTS_GU.txt")
        output_file_csv = os.path.join(output_path, "03-02_OUTPUT_RESULTS_matrices.csv")

        list_of_matrices = ["md" + str(i) for i in range(5, 12) + range(20, 26) + range(31, 53)]
        list_of_matrices = list_of_matrices + ["mo" + str(i) for i in range(915, 927)]
        util.export_csv(eb, list_of_matrices, output_file_csv)

        ##    List to hold matrix objects
        md_value = []

        ##    Loop to append all result matrices onto the variable "md_value"
        for mo_num in [24, 25] + range(31, 53):
            md_value.append(eb.matrix("md" + str(mo_num)))


        ##    Export matrices using the appended list of md_value matrices
        export_matrices = _m.Modeller().tool("inro.emme.data.matrix.export_matrices")

        ## Export all matrix data
        export_matrices(export_file=output_file,
                        field_separator=" ",
                        matrices=md_value,
                        export_format="PROMPT_DATA_FORMAT",
                        skip_default_values=True,
                        full_matrix_line_format="ONE_ENTRY_PER_LINE")

        ## Export matrix data aggregated to the gy ensemble
        export_matrices(export_file=output_file_gy,
                        field_separator=" ",
                        matrices=md_value,
                        partition_aggregation={"destinations": "gy", "operator": "sum"},
                        export_format="PROMPT_DATA_FORMAT",
                        skip_default_values=True,
                        full_matrix_line_format="ONE_ENTRY_PER_LINE")

        ## Export matrix data aggregated to the gu ensemble
        export_matrices(export_file=output_file_gu,
                        field_separator=" ",
                        matrices=md_value,
                        partition_aggregation={"destinations": "gu", "operator": "sum"},
                        export_format="PROMPT_DATA_FORMAT",
                        skip_default_values=True,
                        full_matrix_line_format="ONE_ENTRY_PER_LINE")

        for Output in [output_file, output_file_gy, output_file_gu]:
            f = open(Output, "a")
            f.write("c ------Data Sources:\n")
            f.write("c " + output_file + "\n")
            f.close()

    @_m.logbook_trace("Apply_Factors")
    def Apply_Factors(self, purpose_list, purpose_factors):
        util = _m.Modeller().tool("translink.emme.util")

        ## Scaling all the mds to match the "mo" total, except for md46, HBU.
        for i in range(42, 46) + range(47, 53):
            expression = "md" + str(i - 11) + "*" + str(purpose_factors[purpose_list[i - 42]]["Factor"])
            result = "md" + str(i)
            # print result + " = " + expression
            spec = util.matrix_spec(result, expression)
            util.compute_matrix(spec)

        util.compute_matrix(util.matrix_spec("md46", "md35"))

        ## scaling the mo - HBU to match md for HBU
        for i in range(1, 13):
            expression = "mo" + str(i + 184) + "/" + str(purpose_factors["HBU"]["Factor"])
            result = "mo" + str(i + 914)
            util.compute_matrix(util.matrix_spec(result, expression))

    @_m.logbook_trace("Calculate_Factors")
    def Calculate_Factors(self, purpose_list, purpose_factors):
        util = _m.Modeller().tool("translink.emme.util")

        for i in range(0, 3):
            x = i + 161
            # print purpose_list[i], x, x+3, x+6, x+9
            spec = util.matrix_spec(None, "mo%d + mo%d + mo%d + mo%d" % (x, x + 3, x + 6, x + 9))
            spec["aggregation"] = {"origins": "+", "destinations": None}
            report = util.compute_matrix(spec)
            purpose_factors[purpose_list[i]]["moSum"] = report["sum"]

        for i in range(173, 269, 12):
            expression = "0"
            for j in range(0, 12):
                expression = expression + " + mo" + str(i + j)
            spec = util.matrix_spec(None, expression)
            spec["aggregation"] = {"origins": "+", "destinations": None}
            report = util.compute_matrix(spec)
            purpose_factors[purpose_list[(i - 173) / 12 + 3]]["moSum"] = report["sum"]

        for i in range(31, 42):
            spec = util.matrix_spec(None, "md" + str(i))
            spec["aggregation"] = {"origins": None, "destinations": "+"}
            report = util.compute_matrix(spec)
            purpose_factors[purpose_list[i - 31]]["mdSum"] = report["sum"]

        for i in range(0, 11):
            purpose_factors[purpose_list[i]]["Factor"] = purpose_factors[purpose_list[i]]["moSum"] / \
                                                         purpose_factors[purpose_list[i]]["mdSum"]

                # print "purpose_factors: ", purpose_factors
        return purpose_factors
