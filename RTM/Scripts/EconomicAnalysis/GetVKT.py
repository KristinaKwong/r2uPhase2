##---------------------------------------------------------------------
##--TransLink Phase 3.2 Regional Transportation Model
##--
##--Path: EconomicAnalysis.getvkt
##--Purpose: Summarize VKT
##---------------------------------------------------------------------
import inro.modeller as _m
import csv
import os
import numpy as np
import pandas as pd
import sqlite3
import traceback as _traceback

class GetAnnualVKT(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Summarize VKT by Time of Day"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            eb = _m.Modeller().emmebank

            self(eb)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Summarize VKT")
    def __call__(self, eb):

        expansion_factors = {"SOV": [3.44, 8.41, 3.95],
                             "HOV": [1.51, 8.58, 5.32],
                             "LGV": [3.59, 5.63, 6.17],
                             "HGV": [4.88, 5.43, 6.36]}
        #self.print_all_scenario_vkt(eb, expansion_factors, "all")
        self.get_annual_vkt(eb, expansion_factors, "all")

    def get_annual_vkt(self, eb, expansion_factors, selection):
        #load AM/MD/PM scenario from ms matrices
        am_scenario = int(eb.matrix("ms2").data)
        md_scenario = int(eb.matrix("ms3").data)
        pm_scenario = int(eb.matrix("ms4").data)
        Auto_VKT, LGV_VKT, HGV_VKT = [0, 0, 0]

        dt = _m.Modeller().desktop
        de = dt.data_explorer()
        db = de.active_database()
        for sc in db.scenarios():
            scenario_number = sc.number()

            if scenario_number in [am_scenario, md_scenario, pm_scenario]:
                de.replace_primary_scenario(sc)
                component_list = self.compute_network_based_vkt(sc, expansion_factors, selection)
                Auto_VKT, LGV_VKT, HGV_VKT = [sum(x) for x in zip([Auto_VKT, LGV_VKT, HGV_VKT], component_list)]
        return Auto_VKT, LGV_VKT, HGV_VKT

    def print_all_scenario_vkt(self, eb, expansion_factors):

        dt = _m.Modeller().desktop()
        de = dt.data_explorer()
        db = de.active_database()
        for sc in db.scenarios():
            scenario_number = sc.number()

            if scenario_number<10000:
                continue
            de.replace_primary_scenario(sc)
            self.compute_network_based_vkt(sc, expansion_factors, "all")

    def compute_network_based_vkt(self, sc, expansion_factors, selection):
        util = _m.Modeller().tool("translink.util")
        calc_link = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")

        title = sc.title().split(":",1)[1][1:]
        tod = title[-2:]
        expansion_factors_Index = ["AM","MD","PM"].index(tod)

        if "@speedau" in selection:
            create_extra = _m.Modeller().tool("inro.emme.data.extra_attribute.create_extra_attribute")
            create_extra(extra_attribute_type="LINK",extra_attribute_name="@speedau",extra_attribute_description="network speed",overwrite=True)
            spec = {"result": "@speedau", "expression": "length*60/timau", "selections": {"link": "timau=0,99999"}, "aggregation": None, "type": "NETWORK_CALCULATION"}
            calc_link(spec)

        spec = {"result": None, "expression": "(@sov1+@sov2+@sov3+@sov4)*length", "selections": {"link": selection}, "aggregation": None, "type": "NETWORK_CALCULATION"}
        Auto_VKT = calc_link(spec)["sum"]*expansion_factors["SOV"][expansion_factors_Index]*335
        spec = {"result": None, "expression": "(@hov1+@hov2+@hov3)*length", "selections":  {"link": selection}, "aggregation": None, "type": "NETWORK_CALCULATION"}
        Auto_VKT += calc_link(spec)["sum"]*expansion_factors["HOV"][expansion_factors_Index]*335
        spec = {"result": None, "expression": "(@lgvol/1.5)*length", "selections":  {"link": selection}, "aggregation": None, "type": "NETWORK_CALCULATION"}
        LGV_VKT = calc_link(spec)["sum"]*expansion_factors["LGV"][expansion_factors_Index]*313
        spec = {"result": None, "expression": "(@hgvol/2.5)*length", "selections":  {"link": selection}, "aggregation": None, "type": "NETWORK_CALCULATION"}
        HGV_VKT = calc_link(spec)["sum"]*expansion_factors["HGV"][expansion_factors_Index]*276
        #print("Annual VKT disaggregated by AM/MD/PM Time Period")
        #print("%s, Auto, %.0f"%(title, Auto_VKT))
        #print("%s, Light_Truck, %.0f"%(title, LGV_VKT))
        #print("%s, Heavy_Truck, %.0f"%(title, HGV_VKT))
        return Auto_VKT, LGV_VKT, HGV_VKT
