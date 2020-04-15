##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage2.nhbother
##--Purpose:
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback
import numpy as np
import pandas as pd
from os import path

toolbox_dir, = [t.path for t in _m.Modeller().toolboxes if
                t.namespace() == 'translink.RTM3']
toolbox_path = path.dirname(toolbox_dir)
class Tnc_Zov(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "TNC ZOV trip model"
        pb.description = "Calculate empty TNC trips for assignment"
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
            self.tool_run_msg = _m.PageBuilder.format_exception(e,
                                                                _traceback.format_exc(
                                                                    e))


    @_m.logbook_trace("Run TNC ZOV model")
    def __call__(self, eb):

        self.matrix_batchins(eb)
        self.calc_empty_tnc_trips(eb)
#

    def calc_empty_tnc_trips(self,eb ):
        util = _m.Modeller().tool("translink.util")
        periods = ["Am","Md","Pm"]
        period_cap = ["AM","MD","PM"]
        NAMESPACE = "inro.emme.matrix_calculation.matrix_balancing"
        balance_matrix = _m.Modeller().tool(NAMESPACE)

        log_file = open(
            path.join(toolbox_path, "tnc_zov_summaries.txt"), "w")
        for i in range(0,len(periods)):
            period = periods[i]
            impedance_factor = eb.matrix("tnc_zov_imp_factor_"+period).data
            # calculate transpose
            expression ="mfTnc"+period_cap[i]+"VehicleTrip"
            result = "mfTncVehicleTranspose"+period
            spec = util.matrix_spec(result, expression)
            #util.compute_matrix(spec)
            total_trips = util.compute_matrix(spec)["sum"]
            util.get_matrix_transpose(eb,result)

            # calculate production
            expression = "mfTncVehicleTranspose"+period
            result = "moTncZovProduction" + period
            spec = util.matrix_spec(result, expression)
            spec["aggregation"] = {"origins": None,
                                   "destinations": "+"}

            util.compute_matrix(spec)

            # calculate attraction
            result = "mdTncZovAttraction" + period
            spec = util.matrix_spec(result, expression)
            spec["aggregation"] = {"origins": "+",
                                   "destinations": None}
            util.compute_matrix(spec)

            #calculate impedance matrix for balancing
            time_skims = "mf"+period+"SovTimeVOT4"
            expression = "exp(%s*(%s.min.30))"%(impedance_factor,time_skims)
            result = "mfTncZovImp"+period
            spec = util.matrix_spec(result,expression)
            util.compute_matrix(spec)

            specification = {
                "type": "MATRIX_BALANCING",
                "od_values_to_balance": result,
                "results": {
                    "od_balanced_values": "mfTncZov"+period
                },
                "origin_totals": "moTncZovProduction" + period,
                "destination_totals":"mdTncZovAttraction" + period,
                "constraint":None,
                "max_iterations": 100,
                "max_relative_error": 0.0001
            }

            report = balance_matrix(specification)

            # calculate average loaded VHT and empty VHT
            expression = "mfTnc" + period_cap[i] + "VehicleTrip*"+time_skims
            result = None
            spec = util.matrix_spec(result, expression)
            spec["aggregation"] ={"origins": "+",
                                   "destinations": "+"}
            loaded_total_VHT = util.compute_matrix(spec)["sum"]

            expression = "mfTncZov"+period+"*" + time_skims
            result = None
            spec = util.matrix_spec(result, expression)
            spec["aggregation"] = {"origins": "+",
                                   "destinations": "+"}

            empty_total_VHT = util.compute_matrix(spec)["sum"]

            average_loaded_VHT = loaded_total_VHT/total_trips
            average_empty_VHT = empty_total_VHT / total_trips

            log_file.write("Period = "+period + "\n")
            log_file.write("   Average loaded VHT = " + str(average_loaded_VHT) + "\n")
            log_file.write(
                "   Average empty VHT = " + str(average_empty_VHT) + "\n")




    @_m.logbook_trace("Initialize Matrices")
    def matrix_batchins(self, eb):
        util = _m.Modeller().tool("translink.util")

        # transpose of TNC loaded vehicle trips
        util.initmat(eb, "mf4004", "TncVehicleTransposeAm",
                     " TNC vehicle trips transpose AM", 0)
        util.initmat(eb, "mf4005", "TncVehicleTransposeMd",
                     " TNC vehicle trips transpose MD", 0)
        util.initmat(eb, "mf4006", "TncVehicleTransposePm",
                     " TNC vehicle trips transpose PM", 0)


        ## Initalize empty trip tables
        util.initmat(eb, "mf4010", "TncZovAm", " Tnc empty trips for assignment AM ", 0)
        util.initmat(eb, "mf4011", "TncZovMd",
                     " Tnc empty trips for assignment MD ", 0)
        util.initmat(eb, "mf4012", "TncZovPm",
                     " Tnc empty trips for assignment PM ", 0)

        util.initmat(eb, "mf4013", "TncZovImpAm",
                     " Tnc empty trips for assignment AM ", 0)
        util.initmat(eb, "mf4014", "TncZovImpMd",
                     " Tnc empty trips for assignment MD ", 0)
        util.initmat(eb, "mf4015", "TncZovImpPm",
                     " Tnc empty trips for assignment PM ", 0)



        # Attraction for TNC ZOV
        util.initmat(eb, "md4001", "TncZovAttractionAm", " Attraction for TNC ZOV AM", 0)
        util.initmat(eb, "md4002", "TncZovAttractionMd", " Attraction for TNC ZOV MD", 0)
        util.initmat(eb, "md4003", "TncZovAttractionPm", " Attraction for TNC ZOV PM", 0)

        # prodution for TNC ZOV
        util.initmat(eb, "mo4001", "TncZovProductionAm", " Production for TNC ZOV AM", 0)
        util.initmat(eb, "mo4002", "TncZovProductionMd", " Production for TNC ZOV MD", 0)
        util.initmat(eb, "mo4003", "TncZovProductionPm", " Production for TNC ZOV PM", 0)