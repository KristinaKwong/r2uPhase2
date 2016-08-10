##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage5.step10.regionaltruck
##--Purpose: This module generates light and heavy regional truck matrices
##--         Landuse Based Model produces trip light and heavy productions and attractions which are balanced
##--         Trip Distribution is conducted using gravity model
##--         Time Slice Factors used to derive AM and MD truck traffic
##---------------------------------------------------------------------
import inro.modeller as _m
import os
import traceback as _traceback

class RegTruckModel(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Regional Truck Trips Model"
        pb.description = "Generates base/future forecasts for regional light and heavy trucks trips"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""

        try:
            self.__call__()
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Regional Truck Model")
    def __call__(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        util.delmat(eb, "mf1025")
        util.delmat(eb, "mf1026")
        util.delmat(eb, "mf1027")
        util.delmat(eb, "mf1028")
        process = _m.Modeller().tool("inro.emme.data.matrix.matrix_transaction")
        root_directory = util.get_input_path(_m.Modeller().emmebank)
        matrix_file1 = os.path.join(root_directory, "TruckBatchFiles", "RGBatchIn.txt")
        process(transaction_file=matrix_file1, throw_on_error=True)

        util.initmat(eb, "ms154", "RGphAM", "Rg Truck Peak Hour Factor AM", .26000)
        util.initmat(eb, "ms155", "RGphMD", "Rg Truck Peak Hour Factor MD", .24100)
        # Run regional truck model Macro
        self.run_regional_truck_model(eb)

        spec = util.matrix_spec("ms151", "mf1031")
        spec["aggregation"]["origins"] = "+"
        spec["aggregation"]["destinations"] = "+"
        util.compute_matrix(spec)

        spec = util.matrix_spec("ms152", "mf1034")
        spec["aggregation"]["origins"] = "+"
        spec["aggregation"]["destinations"] = "+"
        util.compute_matrix(spec)

    def run_regional_truck_model(self, eb):
        """
        Runs the regional truck model.
        :param eb: current emmebank
        :return: None
        """

        util = _m.Modeller().tool("translink.emme.util")
        specs = []

        """
        Compute light and heavy truck prod/attr (Non-CBD, CBD)
        """
        util.initmat(eb, "mo1007", "RGLgPr", "Rg Daily LgTruck Trip Prod", 0)

        spec = util.matrix_spec("mo1007", "((.0714)*md5'+(.138)*md7'+.1539*md8'+.0496*(md6'+md9')+.017*md11'+.0981*md10'+.0077*mo20)*1.0/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy1-gy14", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("mo1007", "((.016)*md5'+(0.044)*md7'+.0845*md8'+.0163*(md6'+md9')+.0190*md11'+.0645*md10'+.0037*mo20)*1.0/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy2;gy13-gy14", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("mo1007", "((.1235)*md5'+(.277)*md7'+.1390*md8'+.0176*(md6'+md9')+.0233*md11'+.1596*md10'+.0216*mo20)*1.0/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy1;gy4;gy11", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("mo1007", "(.0378*md12')*1.0/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy3", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("mo1007", "mo1007*0.75/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy3;gy4;gy5", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("mo1007", "mo1007*1/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy11-gy14", "destinations": None}
        specs.append(spec)

        util.initmat(eb, "md207", "RGLgAt", "Rg Daily LgTruck Trip Att", 0)
        spec = util.matrix_spec("md207", "mo1007'")
        specs.append(spec)


        """
        Compute heavy truck trip prod/attr (Non-CBD, CBD)
        """
        util.initmat(eb, "mo1008", "RGHvPr", "Rg Daily HvTruck Trip Prod", 0)

        spec = util.matrix_spec("mo1008", "((.081708)*md5'+(.049246)*md7'+.03294*md8'+.016721*(md6'+md9')+.002417*md11'+.046216*md10'+.0006*mo20)*1.0/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy1-gy14", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("mo1008", "((.0534886)*md5'+(.0430371)*md7'+.0277756*md8'+.00141249*(md6'+md9')+.00362843*md11'+.02071*md10'+.0006*mo20)*1.0/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy4;gy5", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("mo1008", "((.079903)*md5'+(.140189)*md7'+.035748*md8'+.011378*(md6'+md9')+.006965*md11'+.067798*md10'+.0016*mo20)*1.0/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy6;gy8;gy11;gy12", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("mo1008", "(.0059*md12')*1.0/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy3", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("mo1008", "mo1008*1/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy1;gy2;gy4-gy14", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("mo1008", "mo1008*1.1/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy7;gy8", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("mo1008", "mo1008*1.25/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy9;gy10;gy12;gy14", "destinations": None}
        specs.append(spec)

        util.initmat(eb, "md208", "RGHvAt", "Rg Daily HvTruck Trip Att", 0)
        spec = util.matrix_spec("md208", "mo1008'")
        specs.append(spec)


        """
        Trip Distribution - Compute Friction and Combine Tables
        """
        util.initmat(eb, "mf1029", "RGLgFc", "Rg Lg Truck Impedance", 0)

        spec = util.matrix_spec("mf1029", "exp(-.09*mf1024)")
        spec["constraint"]["by_zone"] = {"origins": "gy1-gy14", "destinations": "gy1-gy14"}
        specs.append(spec)

        spec = util.matrix_spec("mf1029", "exp(-.13*mf1024)")
        spec["constraint"]["by_zone"] = {"origins": "gy1-gy11", "destinations": "gy1-gy11"}
        specs.append(spec)

        spec = util.matrix_spec("mf1029", "exp(-.3*mf1024)")
        spec["constraint"]["by_zone"] = {"origins": "gy1-gy4;gy7", "destinations": "gy1-gy4;gy7"}
        specs.append(spec)

        util.initmat(eb, "mf1032", "RGHvFc", "Rg Hv Truck Impedance", 0)

        spec = util.matrix_spec("mf1032", "exp(-.07*mf1024)")
        spec["constraint"]["by_zone"] = {"origins": "gy1-gy14", "destinations": "gy1-gy14"}
        specs.append(spec)

        spec = util.matrix_spec("mf1032", "exp(-.11*mf1024)")
        spec["constraint"]["by_zone"] = {"origins": "gy3", "destinations": "gy1-gy14"}
        specs.append(spec)

        spec = util.matrix_spec("mf1032", "exp(-.11*mf1024)")
        spec["constraint"]["by_zone"] = {"origins": "gy1-gy14", "destinations": "gy3"}
        specs.append(spec)

        util.compute_matrix(specs)


        """
        TRIP DISTRIBUTION: BALANCE ij TRIP TOTALS
        and Add Externals and Special Gen Trips to Lt Total
        """
        balance_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_balancing")

        util.initmat(eb, "mf1030", "RGLg24", "Rg LgTruck Daily Trips", 0)
        balance_spec = {
            "type": "MATRIX_BALANCING",
            "od_values_to_balance": "mf1029",
            "results": {
                "od_balanced_values": "mf1030"
            },
            "origin_totals": "mo1007",
            "destination_totals": "md207",
            "constraint": {
                "by_zone": {
                    "origins": "gy1-gy14",
                    "destinations": "gy1-gy14"
                },
                "by_value": None
            },
        }
        balance_matrix(balance_spec)

        util.initmat(eb, "mf1033", "RGHv24", "Rg HvTruck Daily Trips", 0)
        balance_spec = {
            "type": "MATRIX_BALANCING",
            "od_values_to_balance": "mf1032",
            "results": {
                "od_balanced_values": "mf1033"
            },
            "origin_totals": "mo1008",
            "destination_totals": "md208",
            "constraint": {
                "by_zone": {
                    "origins": "gy1-gy14",
                    "destinations": "gy1-gy14"
                },
                "by_value": None
            },
        }
        balance_matrix(balance_spec)

        specs = []

        util.initmat(eb, "mf1031", "RGLgAd", "Rg LgTruck Daily Trips Adj", 0)
        spec = util.matrix_spec("mf1031", "mf1030")
        specs.append(spec)

        util.initmat(eb, "mf1034", "RGHvAd", "Rg HvTruck Daily Trips Adj", 0)
        spec = util.matrix_spec("mf1034", "mf1033")
        specs.append(spec)

        util.compute_matrix(specs)

        # Peak Hour Factoring: Factor from Peak Period to Peak Hour Demand
        util.initmat(eb, "mf1035", "RGLgAM", "Rg LgTruck AM Trips", 0)
        util.initmat(eb, "mf1036", "RGLgMD", "Rg LgTruck MD Trips", 0)
        util.initmat(eb, "mf1037", "RGHvAM", "Rg HvTruck AM Trips", 0)
        util.initmat(eb, "mf1038", "RGHvMD", "Rg HvTruck MD Trips", 0)

        specs = []

        spec = util.matrix_spec("mf1035", "mf1031*mf1025*ms154")
        specs.append(spec)

        spec = util.matrix_spec("mf1036", "mf1031*mf1026*ms155")
        specs.append(spec)

        spec = util.matrix_spec("mf1037", "mf1034*mf1027*ms154")
        specs.append(spec)

        spec = util.matrix_spec("mf1038", "mf1034*mf1028*ms155")
        specs.append(spec)

        util.compute_matrix(specs)
