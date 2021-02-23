##---------------------------------------------------------------------
##--TransLink Phase 3.2 Regional Transportation Model
##--
##--Path: translink.internal_tools.DailyTripsbyMode
##--Purpose: Summarize Daily Trips by Mode
##---------------------------------------------------------------------
import inro.modeller as _m
import inro.emme.desktop as _d
import csv
import os
import numpy as np
import pandas as pd
import sqlite3
import traceback as _traceback

class DailyTripsbyMode(_m.Tool()):        
    tool_run_msg = _m.Attribute(unicode)

    def __init__(self):
        self.baseScenarioName = "2016Base"
        self.ensem = "gm"
        
    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Summarize Daily Trips by Mode"

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

    @_m.logbook_trace("Summarize Daily Trips by Mode")
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
            trip_total, trips_by_mode_Dict = self.getDemand(eb)
            print("%s: %.1f"%(title, trip_total))
            break
            
    def getDemand(self, eb, filter_vector=None):
        util = _m.Modeller().tool("translink.util")
        SOV_matrix_list = []
        SOV_matrix_list += [3000, 3001, 3002, 3100, 3300, 3301, 3302, 3400, 3401, 3402]         
        SOV_matrix_list += [3500, 3501, 3502, 3600, 3601, 3602, 3700, 3800]
        
        HOV_matrix_list = []
        HOV_matrix_list += [3105, 3305, 3306, 3307, 3405, 3406, 3407, 3505, 3506, 3507]
        HOV_matrix_list += [3605, 3606, 3607, 3705, 3805]
        HOV_matrix_list += [3005, 3006, 3007, 3205, 3206, 3207]
        HOV_matrix_list += [3010, 3011, 3012]
        
        Transit_matrix_list = []
        Transit_matrix_list += [3015, 3020, 3025, 3115, 3120, 3215, 3220, 3315, 3320]
        Transit_matrix_list += [3415, 3420, 3515, 3520, 3615, 3620, 3715, 3720, 3815, 3820]
        
        Walk_matrix_list = []
        Walk_matrix_list += [3030, 3130, 3230, 3330, 3430, 3530, 3630, 3730, 3830]
        
        Bike_matrix_list = []
        Bike_matrix_list += [3035, 3135, 3235, 3335, 3535, 3635, 3735, 3835]
        
        # quick print sum total
        Total_matrix_list = []
        Total_matrix_list += SOV_matrix_list
        Total_matrix_list += HOV_matrix_list
        Total_matrix_list += Transit_matrix_list
        Total_matrix_list += Walk_matrix_list
        Total_matrix_list += Bike_matrix_list
        
        zoneindex = util.get_matrix_numpy(eb, "zoneindex")
        NoTAZ = len(zoneindex)
        Sum = np.zeros((NoTAZ,NoTAZ))
        for mat_id in Total_matrix_list:
            mat_name = "mf{}".format(mat_id)
            Sum += self.Get_Daily_OD(eb, mat_name)
        
        # compute mode share: get HOV Driver and HOV Passenger
        Sum_HOV_Driver = np.zeros((NoTAZ,NoTAZ))
        Sum_Passenger = np.zeros((NoTAZ,NoTAZ))
        for mat_id in HOV_matrix_list:
            mat_name = "mf{}".format(mat_id)
            HOV_Factor = self.Get_HOV_Factor(mat_id)
            Sum_HOV_Driver += (self.Get_Daily_OD(eb, mat_name)/HOV_Factor)
            Sum_Passenger += (self.Get_Daily_OD(eb, mat_name)*(HOV_Factor-1)/HOV_Factor)
        # compute mode share: get SOV
        Sum_Driver = np.zeros((NoTAZ,NoTAZ))
        for mat_id in SOV_matrix_list:
            mat_name = "mf{}".format(mat_id)
            Sum_Driver += self.Get_Daily_OD(eb, mat_name)
        Sum_Driver += Sum_HOV_Driver
        # compute mode share: get Transit
        Sum_Transit = np.zeros((NoTAZ,NoTAZ))
        for mat_id in Transit_matrix_list:
            mat_name = "mf{}".format(mat_id)
            Sum_Transit += self.Get_Daily_OD(eb, mat_name)
        # compute mode share: get Walk
        Sum_Walk = np.zeros((NoTAZ,NoTAZ))
        for mat_id in Walk_matrix_list:
            mat_name = "mf{}".format(mat_id)
            Sum_Walk += self.Get_Daily_OD(eb, mat_name)
        # compute mode share: get Bike
        Sum_Bike = np.zeros((NoTAZ,NoTAZ))
        for mat_id in Bike_matrix_list:
            mat_name = "mf{}".format(mat_id)
            Sum_Bike += self.Get_Daily_OD(eb, mat_name)
        
        #Apply Study Area Filter
        Zone_Ensemble = util.get_matrix_numpy(eb, "mo99")
        if filter_vector==None:
            filter_vector = 1+np.zeros((NoTAZ,NoTAZ))
        #filter_vector = np.where(Zone_Ensemble==210,1,0)+np.zeros((NoTAZ,NoTAZ))
        #filter = filter_vector #trip originated from study area
        #filter = np.transpose(filter_vector) #trip destinated in study area
        #filter = filter_vector * np.transpose(filter_vector) #study area internal trip
        filter = np.minimum(filter_vector + np.transpose(filter_vector), 1) #study area related trips
        print(filter)
        print("Auto Driver: %.0f"%(Sum_Driver*filter).sum())
        print("Auto Passenger: %.0f"%(Sum_Passenger*filter).sum())
        print("Transit: %.0f"%(Sum_Transit*filter).sum())
        print("Walk: %.0f"%(Sum_Walk*filter).sum())
        print("Bike: %.0f"%(Sum_Bike*filter).sum())
        
        trips_by_mode_Dict = {"Auto Driver": (Sum_Driver*filter).sum(),
                              "Auto Passenger": (Sum_Passenger*filter).sum(),
                              "Transit": (Sum_Transit*filter).sum(),
                              "Walk": (Sum_Walk*filter).sum(),
                              "Bike": (Sum_Bike*filter).sum()}
        
        
        return Sum.sum(), trips_by_mode_Dict
        
    def getPercentLowIncomeAutoDemand(self, eb, filter_vector=None):
        util = _m.Modeller().tool("translink.util")
        
        #low income trips
        matrix_list = []
        matrix_list += [3000,3005,3010,3205,3300,3305,3400,3405,3500,3505,3600,3605]  
        
        zoneindex = util.get_matrix_numpy(eb, "zoneindex")
        NoTAZ = len(zoneindex)
        Sum = np.zeros((NoTAZ,NoTAZ))
        for mat_id in matrix_list:
            mat_name = "mf{}".format(mat_id)
            Sum += self.Get_Daily_OD(eb, mat_name)    
        LowIncome_Trips = Sum.sum()            
            
        #trip purposes with low income
        matrix_list = []
        matrix_list += [3000, 3001, 3002, 3300, 3301, 3302, 3400, 3401, 3402]         
        matrix_list += [3500, 3501, 3502, 3600, 3601, 3602]
        matrix_list
        matrix_list = []
        matrix_list += [3305, 3306, 3307, 3405, 3406, 3407, 3505, 3506, 3507]
        matrix_list += [3605, 3606, 3607]
        matrix_list += [3005, 3006, 3007, 3205, 3206, 3207]
        matrix_list += [3010, 3011, 3012]
        
        Sum = np.zeros((NoTAZ,NoTAZ))
        for mat_id in matrix_list:
            mat_name = "mf{}".format(mat_id)
            Sum += self.Get_Daily_OD(eb, mat_name)     
        All_Trips = Sum.sum()  
        
        return LowIncome_Trips/All_Trips
        
    def Get_HOV_Factor(self, mat_id):   
        if mat_id in [3005,3006,3007]:
            return 2
        if mat_id == 3105:
            return 2.48
        if mat_id in [3205,3206,3207]:
            return 3.02
        if mat_id in [3305,3306,3307]:
            return 2.35
        if mat_id in [3405,3406,3407]:
            return 2.31
        if mat_id in [3505,3506,3507]:
            return 2.61
        if mat_id in [3605,3606,3607]:
            return 2.6 
        if mat_id == 3705:
            return 2.58
        if mat_id == 3805:
            return 2.58
        if mat_id in [3010,3011,3012]:
            return 2.31
        
    def Get_Daily_OD(self, eb, mat_name):    
        util = _m.Modeller().tool("translink.util")
        
        matrix_name = eb.matrix(mat_name).name
        purpose_List = ["HbW",  "HbU",  "HbSc", "HbSh", "HbPb", "HbSo", "HbEs", "NHbW", "NHbO"]
        for purpose in purpose_List:
            if purpose in matrix_name:
                purpose_index = purpose_List.index(purpose)
        
        pa_mat = util.get_matrix_numpy(eb, mat_name)
        
        pa_Factor_AM = np.asscalar(util.get_matrix_numpy(eb, "ms4{}0".format(purpose_index)))
        pa_Factor_MD = np.asscalar(util.get_matrix_numpy(eb, "ms4{}1".format(purpose_index)))
        pa_Factor_PM = np.asscalar(util.get_matrix_numpy(eb, "ms4{}2".format(purpose_index)))
        pa_fac = pa_Factor_AM + pa_Factor_MD + pa_Factor_PM
        ap_fac = 1 - pa_fac
        
        return pa_mat * pa_fac + pa_mat.transpose() * ap_fac
        