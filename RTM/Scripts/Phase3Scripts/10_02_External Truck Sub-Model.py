##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage5.step10.externaltruck
##--Purpose: This module generates external light and heavy truck matrices
##--         Regression functions are used to generate base and future demand
##--         Trip Distribution is conducted using 1999 Truck O-D survey
##---------------------------------------------------------------------
import inro.modeller as _m
import os

class ExternalTruckModel(_m.Tool()):
    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "External Truck Trips Model"
        pb.description = "Generates base/future forecasts for external light and heavy trucks trips"
        pb.branding_text = "TransLink"
        pb.runnable = False

        return pb.render()

    @_m.logbook_trace("External Truck Trips Model")
    def __call__(self, eb, Year):
        # Call Modules of External Model
        self.CrossBorder(eb, Year) # Import Cascade Cross-Border Matrices
        self.TripGeneration(Year)
        self.TripDistribution()
        self.TimeSlicing()

    @_m.logbook_trace("Import Cascade Cross-Border Matrices")
    def CrossBorder(self, eb, Year):
        util = _m.Modeller().tool("translink.util")

        util.initmat(eb, "mo1003",  "IRAdj", "IR Adjustment Calc", 0)
        util.initmat(eb, "md203",   "IRAdj", "IR Adjustment Calc", 0)
        util.initmat(eb, "mf1010", "IRLg24", "IR LgTruck Daily Trips", 0)
        util.initmat(eb, "mf1011", "IRHv24", "IR HvTruck Daily Trips", 0)
        util.initmat(eb, "mf1012", "IRLgAM", "IR LgTruck AM Trips", 0)
        util.initmat(eb, "mf1013", "IRHvAM", "IR HvTruck AM Trips", 0)
        util.initmat(eb, "mf1014", "IRLgMD", "IR LgTruck MD Trips", 0)
        util.initmat(eb, "mf1015", "IRHvMD", "IR HvTruck MD Trips", 0)

