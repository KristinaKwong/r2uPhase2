##---------------------------------------------------------------------
##--Regional Transportation Model - ModSum
##--
##--Path: Analytics.ModSum
##--Purpose: Export high-level model run summary
##---------------------------------------------------------------------
import inro.modeller as _m
import inro.emme.desktop as _d
import traceback as _traceback

import os
import csv as csv

import sqlite3
import pandas as pd
import numpy as np



class ModSum(_m.Tool()):

    compile_all = _m.Attribute(bool)
    tool_run_msg = _m.Attribute(unicode)


    def __init__(self):
        self.compile_all = False


    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Export ModSum from Model Run"
        pb.description = "Exports High-Level Results of Model Run"

        with pb.section("Export Format Options"):
            pb.add_checkbox("compile_all", label="Compile ModSum for all the databanks.")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            self.__call__()
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))


    @_m.logbook_trace("ModSum")
    def __call__(self):
        if self.compile_all:
            self.generateComparisonFile()
        else:
            eb = _m.Modeller().emmebank
            self.generateModSumVector(eb)
        
    def generateComparisonFile(self):
        util = _m.Modeller().tool("translink.util")
        
        # combine modsum for all emmebanks into one comparison file
        modsum_forAllDatabanks = pd.DataFrame()
        
        dt = _m.Modeller().desktop
        de = dt.data_explorer()
        db = de.active_database()
        ebs = de.databases()
        for eb in ebs:
            title = eb.title()
            if title == 'Minimal Base Databank':
                continue
            eb.open()
            eb = _m.Modeller().emmebank
            # to-do: check if am/md/pm scenarios are run, if not: continue to next emmebank
            try:
                am_scen, md_scen, pm_scen = util.get_tod_scenarios(eb)
            except:
                continue #to next databank
            modsum_vector = self.generateModSumVector(eb)
            if modsum_forAllDatabanks.empty:
                modsum_forAllDatabanks = modsum_vector
            else:
                modsum_forAllDatabanks = pd.merge(modsum_forAllDatabanks, modsum_vector, on="Measure", how = "outer")

        project = dt.project
        proj_path = os.path.dirname(project.path)
        modsum_compare = os.path.join(proj_path, "ModSumComparison.csv")

        modsum_forAllDatabanks.to_csv(modsum_compare, index=False)
        
    def generateModSumVector(self, eb):
        util = _m.Modeller().tool("translink.util")
        model_year = int(util.get_year(eb))
        am_scen, md_scen, pm_scen = util.get_tod_scenarios(eb)
        
        # Merge all the modsum measures into one vector
        DatabankName = eb.title
        modsum_header = ["Measure",DatabankName]
        modsum_vector = pd.DataFrame(columns=modsum_header)

        conn = util.get_db_byname(eb, "trip_summaries.db")
        
        # daily trips by purpose
        # summarized after mode choice
    	df_daily_gy = pd.read_sql("select * from daily_gy", conn)
        df_DailyTripByPurpose = pd.DataFrame(df_daily_gy[["purpose","trips"]].groupby(["purpose"]).sum().reset_index())
        df_DailyTripByPurpose["Measure"] = "DailyTripsByPurpose_"+df_DailyTripByPurpose["purpose"]
        df_DailyTripByPurpose[DatabankName] = df_DailyTripByPurpose["trips"]
        modsum_vector = modsum_vector.append(df_DailyTripByPurpose[modsum_header])
        
        # daily trips by mode
        # summarized after mode choice
        df_DailyTripByMode = pd.DataFrame(df_daily_gy[["mode","trips"]].groupby(["mode"]).sum().reset_index())
        df_DailyTripByMode["Measure"] = "DailyTripsByMode_"+df_DailyTripByMode["mode"]
        df_DailyTripByMode[DatabankName] = df_DailyTripByMode["trips"]
        modsum_vector = modsum_vector.append(df_DailyTripByMode[modsum_header])
        
        # time-of-day trips by mode
    	df_autoTrips_gy = pd.read_sql("select * from autoTripsGy", conn)
        df_TODTripByMode = pd.DataFrame(df_autoTrips_gy[["peak", "mode","trips"]].groupby(["peak", "mode"]).sum().reset_index())
        for demand in ["busAm","busMd","busPm","railAm","railMd","railPm","WCEAm","WCEMd","WCEPm"]:
            df_TODTripByMode.loc[len(df_TODTripByMode)] = [demand[-2:].lower(),demand[:-2],util.get_matrix_numpy(eb, "mf"+demand).sum()]
        df_TODTripByMode["Measure"] = "TimeofDayTripsByMode_"+df_TODTripByMode["peak"]+"-"+df_TODTripByMode["mode"]
        df_TODTripByMode[DatabankName] = df_TODTripByMode["trips"]
        modsum_vector = modsum_vector.append(df_TODTripByMode[modsum_header])
        
        # transit boardings
        df_transit_network = pd.read_sql("select * from transitResults", conn)
        df_transit_boardings = pd.DataFrame(df_transit_network[["peakperiod", "modeDesc","boardings"]].groupby(["peakperiod", "modeDesc"]).sum().reset_index())
        df_transit_boardings["Measure"] = "TransitBoardings_"+df_transit_boardings["peakperiod"]+"-"+df_transit_boardings["modeDesc"]
        df_transit_boardings[DatabankName] = df_transit_boardings["boardings"]
        modsum_vector = modsum_vector.append(df_transit_boardings[modsum_header])
        
        # vkt
        # sum((@wsovl+@whovl+@lgvol/1.5+@hgvol/2.5+volad/2.5)*length), exclude centroids
        df_VKT = pd.read_sql("select * from aggregateNetResults", conn)[["period","measure","value"]]
        df_VKT["Measure"] = "VKT_"+df_VKT["period"]+"-"+df_VKT["measure"]
        df_VKT[DatabankName] = df_VKT["value"]
        modsum_vector = modsum_vector.append(df_VKT[modsum_header])
        
        # Land Use: Pop/Emp/HH
        dict_LandUse = [["TotalPop",util.get_matrix_numpy(eb, "moTotPop").sum()],
                        ["TotalEmp",util.get_matrix_numpy(eb, "moTotEmp").sum()],
                        ["TotalHH",util.get_matrix_numpy(eb, "moTotHh").sum()]]
        df_LandUse = pd.DataFrame.from_records(dict_LandUse,columns=modsum_header)
        modsum_vector = modsum_vector.append(df_LandUse[modsum_header])
        
        # RTS - Network-Based VKT by Mode (Auto/LGV/HGV)
        GetVKT = _m.Modeller().tool("translink.RTM3Analytics.GetVKT")
        Auto_VKT, LGV_VKT, HGV_VKT = [0, 0, 0]
        expansion_factors = {"SOV": [3.44, 8.41, 3.95], # time-of-day to daily expansion factors
                             "HOV": [1.51, 8.58, 5.32],
                             "LGV": [3.59, 5.63, 6.17],
                             "HGV": [4.88, 5.43, 6.36]}
        dt = _m.Modeller().desktop
        de = dt.data_explorer()
        db = de.active_database()
        for sc in db.scenarios():
            scenario_number = sc.number()
            if eb.scenario(scenario_number) in [am_scen, md_scen, pm_scen]:
                de.replace_primary_scenario(sc)
                component_list = GetVKT.compute_network_based_vkt(sc, expansion_factors, "all")
                Auto_VKT, LGV_VKT, HGV_VKT = [sum(x) for x in zip([Auto_VKT, LGV_VKT, HGV_VKT], component_list)]
        dict_AnnualVKT = [["NetworkBasedAnnualVKT_Auto", Auto_VKT],
                          ["NetworkBasedAnnualVKT_LGV" , LGV_VKT],
                          ["NetworkBasedAnnualVKT_HGV" , HGV_VKT]]
        df_AnnualVKT = pd.DataFrame.from_records(dict_AnnualVKT,columns=modsum_header)
        modsum_vector = modsum_vector.append(df_AnnualVKT[modsum_header])
        
        # RTS - Matrix-Based VKT by Mode (LGV/HGV)
        truckPCE = {"Lgv":1.5, "Hgv":2.5}
        daily_to_annual = {"Lgv":313, "Hgv":276}
        dict_AnnualVKT = []
        AnnualTruckVKT = 0
        for mode in ["Lgv", "Hgv"]:
            Daily_VKT = 0.0
            for tod in ["Am","Md","Pm"]:
                Demand_Matrix = "mf"+mode.lower()+"Pce"+tod
                Distance_Matrix = "mfSkim"+tod+mode+"Dist"
                truckPCE_factor =  truckPCE[mode]
                tod_to_daily_fac = expansion_factors[mode.upper()][["Am","Md","Pm"].index(tod)]
                tod_vkt = np.multiply(util.get_matrix_numpy(eb, Demand_Matrix),util.get_matrix_numpy(eb, Distance_Matrix)).sum()
                Daily_VKT += tod_to_daily_fac*tod_vkt/truckPCE_factor
            dict_AnnualVKT.append(["MatrixBasedAnnualVKT_"+mode, Daily_VKT*daily_to_annual[mode]])
            AnnualTruckVKT += Daily_VKT*daily_to_annual[mode]
        GHG_Factor_2050 = 836.517262727637/1000000 # truck CO2 emission: g/VKT --> converted to tonnes/VKT
        dict_AnnualVKT.append(["AnnualTruckGHG(tonnes)", AnnualTruckVKT*GHG_Factor_2050])
        df_AnnualVKT = pd.DataFrame.from_records(dict_AnnualVKT,columns=modsum_header)
        modsum_vector = modsum_vector.append(df_AnnualVKT[modsum_header])
        
        # Auto Ownership
        conn_rtm = util.get_rtm_db(eb)
        df_AutoOwnership = pd.read_sql("select * from segmentedHouseholds", conn_rtm)
        df_AutoOwnership["NumCar"] = df_AutoOwnership["HHAuto"] * df_AutoOwnership["CountHHs"]
        df_AutoOwnership = df_AutoOwnership[["HHInc","NumCar"]].groupby(["HHInc"])["NumCar"].sum().reset_index()
        df_AutoOwnership["Measure"] = ["AutoOwnership_LowIncHH","AutoOwnership_MedIncHH","AutoOwnership_HigIncHH"]
        df_AutoOwnership[DatabankName] = df_AutoOwnership["NumCar"]
        modsum_vector = modsum_vector.append(df_AutoOwnership[modsum_header])

        # export to csv
        modsum_vector.to_csv(os.path.join(util.get_eb_path(eb), "ModSum_"+DatabankName+".csv"),index=False)

        conn.close()
        conn_rtm.close()


        return modsum_vector
