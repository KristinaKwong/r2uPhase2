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

class RegTruckModel(_m.Tool()):
    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Regional Truck Trips Model"
        pb.description = "Generates base/future forecasts for regional light and heavy trucks trips"
        pb.branding_text = "TransLink"
        pb.runnable = False

        return pb.render()

    @_m.logbook_trace("Regional Truck Model")
    def __call__(self, eb):
        util = _m.Modeller().tool("translink.util")
        # Run regional truck model Macro
        self.run_regional_truck_model(eb)

    def run_regional_truck_model(self, eb):
        """
        Runs the regional truck model.
        :param eb: current emmebank
        :return: None
        """

        util = _m.Modeller().tool("translink.util")
        specs = []

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
            "origin_totals": "mo8050",
            "destination_totals": "md8050",
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
            "origin_totals": "mo8051",
            "destination_totals": "md8051",
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
