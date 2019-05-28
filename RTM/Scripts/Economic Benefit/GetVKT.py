##---------------------------------------------------------------------
##--TransLink Phase 3.2 Regional Transportation Model
##--
##--Path: translink.internal_tools.getvkt
##--Purpose: Summarize Annual VKT
##---------------------------------------------------------------------
import inro.modeller as _m
import inro.emme.desktop as _d
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
        util = _m.Modeller().tool("translink.util")
        dt = _d.app.connect()
        de = dt.data_explorer()
        db = de.active_database()
        ebs = de.databases()
        for eb in ebs:
            title = eb.title()
            
            eb.open()
            eb = _m.Modeller().emmebank
            
            expansion_factor = {"AM":0, "MD":20, "PM":40}
            
            print("%s Annual VKT: %.1f"%(title,self.getVKT(eb, "AM") + self.getVKT(eb, "MD") + self.getVKT(eb, "PM")))
            
    def getVKT(self, eb, tod):
        util = _m.Modeller().tool("translink.util")
        
        sov_demand_matrix_list = [300, 301, 302, 303]
        hov_demand_matrix_list = [306, 307, 308]
        lgv_demand_matrix_list = [312]
        hgv_demand_matrix_list = [313]
        sov_opcost_matrix_list = [5000, 5003, 5006, 5009]
        hov_opcost_matrix_list = [5012, 5015, 5018]
        lgv_opcost_matrix_list = [5024]
        hgv_opcost_matrix_list = [5027]
        
        auto_voc = np.asscalar(util.get_matrix_numpy(eb, "msautoOpCost"))
        lgv_voc  = np.asscalar(util.get_matrix_numpy(eb, "mslgvOpCost"))
        hgv_voc  = np.asscalar(util.get_matrix_numpy(eb, "mshgvOpCost"))
        
        VKT = 0
        demand_offset = {"AM":0, "MD":20, "PM":40}
        opcost_offset = {"AM":0, "MD":30, "PM":60}
        
        expansion_factors = {"SOV": [3.44, 8.41, 3.95],
                             "HOV": [1.51, 8.58, 5.32],
                             "LGV": [3.59, 5.63, 6.17],
                             "HGV": [4.88, 5.43, 6.36]}
        expansion_factors_Index = ["AM","MD","PM"].index(tod)
        
        for demand_id, opcost_id in zip(sov_demand_matrix_list,sov_opcost_matrix_list):
            Vehicle_OpCost = auto_voc
            Demand = util.get_matrix_numpy(eb, "mf{}".format(demand_id+demand_offset[tod]))
            OpCost = util.get_matrix_numpy(eb, "mf{}".format(opcost_id+opcost_offset[tod]))
            VKT += np.multiply(Demand,OpCost).sum()*expansion_factors["SOV"][expansion_factors_Index]*335/Vehicle_OpCost
            
        for demand_id, opcost_id in zip(hov_demand_matrix_list,hov_opcost_matrix_list):
            Vehicle_OpCost = auto_voc
            Demand = util.get_matrix_numpy(eb, "mf{}".format(demand_id+demand_offset[tod]))
            OpCost = util.get_matrix_numpy(eb, "mf{}".format(opcost_id+opcost_offset[tod]))
            VKT += np.multiply(Demand,OpCost).sum()*expansion_factors["HOV"][expansion_factors_Index]*335/Vehicle_OpCost
        
        for demand_id, opcost_id in zip(lgv_demand_matrix_list,lgv_opcost_matrix_list):
            Vehicle_OpCost = lgv_voc*1.5 #1.5 is PCE adjustment
            Demand = util.get_matrix_numpy(eb, "mf{}".format(demand_id+demand_offset[tod]))
            OpCost = util.get_matrix_numpy(eb, "mf{}".format(opcost_id+opcost_offset[tod]))
            VKT += np.multiply(Demand,OpCost).sum()*expansion_factors["LGV"][expansion_factors_Index]*313/Vehicle_OpCost
        
        for demand_id, opcost_id in zip(hgv_demand_matrix_list,hgv_opcost_matrix_list):
            Vehicle_OpCost = hgv_voc*2.5 #2.5 is PCE adjustment
            Demand = util.get_matrix_numpy(eb, "mf{}".format(demand_id+demand_offset[tod]))
            OpCost = util.get_matrix_numpy(eb, "mf{}".format(opcost_id+opcost_offset[tod]))
            VKT += np.multiply(Demand,OpCost).sum()*expansion_factors["HGV"][expansion_factors_Index]*276/Vehicle_OpCost
            
        return VKT
        
        