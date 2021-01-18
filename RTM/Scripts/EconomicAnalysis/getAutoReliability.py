##---------------------------------------------------------------------
##--TransLink Phase 3.2 Regional Transportation Model
##--
##--Path: EconomicAnalysis.autoreliability
##--Purpose: Run Auto Reliability Assignment
##---------------------------------------------------------------------
import inro.modeller as _m
import inro.emme.desktop as _d
import csv
import os
import multiprocessing
import numpy as np
import pandas as pd
import sqlite3
import datetime
import traceback as _traceback

class getAutoReliability(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)
    baseScenarioName = _m.Attribute(str)
    ensem = _m.Attribute(str)
    run_reliability_assignment = _m.Attribute(bool)
    compute_auto_reliability_benefit = _m.Attribute(bool)
    inc = _m.Attribute(int)
    absolute_value = _m.Attribute(bool)

    def __init__(self):
        self.baseScenarioName = "2017_BAU_v4"
        self.ensem = "gy"
        self.run_reliability_assignment = True
        self.compute_auto_reliability_benefit = True
        self.inc = 5
        self.absolute_value = True
        
    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Run Auto Reliability Assignment"
        pb.description = "freeflow assignment and export reliability minutes"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)
        pb.add_checkbox("run_reliability_assignment", label="Run Auto Reliability Assignment")
        pb.add_text_box(tool_attribute_name="inc", size=5, title='Increment to Scenario ID', 
                        note='Make sure not overwriting other scenarios', multi_line=False)
        with pb.section("Auto Reliability Benefits"):
            pb.add_checkbox("compute_auto_reliability_benefit", label="Compute auto reliability benefits")
            pb.add_text_box(tool_attribute_name="baseScenarioName", size=50, title="Baseline scenario name: ")
            pb.add_text_box(tool_attribute_name="ensem", size=2, title="Ensemble")
            pb.add_checkbox("absolute_value",label="Calculate absolute relability value(Uncheck to calculate difference)")
        
        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            eb = _m.Modeller().emmebank

            self(self.baseScenarioName, self.ensem, self.run_reliability_assignment, self.inc, self.compute_auto_reliability_benefit,self.absolute_value)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Trip Simulation")
    def  __call__(self, baseline_eb_title, ensem, run_reliability_assignment, inc, compute_auto_reliability_benefit,absolute_value):
    
        dt = _m.Modeller().desktop
        de = dt.data_explorer()
        db = de.active_database()
        ebs = de.databases()
        util = _m.Modeller().tool("translink.util")
        absolute = absolute_value
        
        # Re-run reliability assignment and export reliability minutes matrices
        ReliabilityAssignment = _m.Modeller().tool("EconomicAnalysis.ffassignment")
        for eb in ebs:
            title = eb.title()
                
            if title == 'Minimal Base Databank':
                continue
            
            eb.open()
            
            current_time = datetime.datetime.now()
            print "\nstarting {} run at {}".format(title, current_time)
            
            try:    
                # reliability assignment
                current_time = datetime.datetime.now() 
                print "running Reliability Assignment for {} at {}".format(title, current_time)
                eb = _m.Modeller().emmebank
                try:
                    am_scen = eb.scenario(int(eb.matrix("msAmScen").data))
                    md_scen = eb.scenario(int(eb.matrix("msMdScen").data))
                    pm_scen = eb.scenario(int(eb.matrix("msPmScen").data))
                    if run_reliability_assignment:
                        assignment_type = 1
                        ReliabilityAssignment(eb, am_scen, md_scen, pm_scen, assignment_type, inc)
                    
                except Exception as e:
                    print("Scenario {} Reliability Assignment failed.".format(title), e)
            
            except Exception as e:
                current_time = datetime.datetime.now()
                print("Scenario {} run failed at {}.".format(title, current_time), e)
                
        if compute_auto_reliability_benefit==False:
            return
            
        # Check if ensemble is valid
        if not ((ensem[0]=="g") and ensem[1].isalpha() and ensem[1].islower()):
            raise Exception("Ensemble should be 'g' followed by a lowercase letter a-z.") 
            
        # Get Base Scenario Folder
        BaseScenario_Folder = None
        for eb in ebs:
            title = eb.title()
            if title == 'Minimal Base Databank':
                continue
            
            #Export ROH Demand
            eb.open()
            eb = _m.Modeller().emmebank
            self.Export_ROH_Demand(eb)
            
            if title == baseline_eb_title and absolute is False:
                BaseScenario_Folder = os.path.join(os.path.dirname(eb.path), "EconomicAnalysis")
        if BaseScenario_Folder=="":
            raise Exception('Base scenario emmebank is not in this project.')

        # Calculation
        for eb in ebs:
            title = eb.title()
            if title == 'Minimal Base Databank':
                continue
            
            eb.open()
            eb = _m.Modeller().emmebank
            AlternativeScenario_Folder = os.path.join(os.path.dirname(eb.path), "EconomicAnalysis")
            
            expansion_factors = {"SOV": [3.44, 8.41, 3.95],
                                 "HOV": [1.51, 8.58, 5.32],
                                 "BUS": [2.54, 9.44, 2.57],
                                 "RAL": [2.53, 9.54, 2.92],
                                 "WCE": [3.34,    0, 2.02],
                                 "LGV": [3.59, 5.63, 6.17],
                                 "HGV": [4.88, 5.43, 6.36]}
            self.Calculate_ROH_Reliability_Benefits(eb, BaseScenario_Folder, AlternativeScenario_Folder, ensem, expansion_factors)
            
            
    @_m.logbook_trace("Export ROH Demand Data")
    def Export_ROH_Demand(self, eb):
        util = _m.Modeller().tool("translink.util")
        
        with_previous_export = os.path.isfile(os.path.join(util.get_eb_path(eb), 'EconomicAnalysis', 'ROH_Demand.npz'))
        if with_previous_export:
            return # do not re-export
                    
        # list mf matrix number to be exported
        matrix_list = []
        matrix_list += range(200,209) # AM_SOV/HOV
        matrix_list += range(230,239) # MD_SOV/HOV
        matrix_list += range(260,269) # PM_SOV/HOV
        matrix_list += range(312,317) # AM_LGV/HGV/BUS/Rail/WCE
        matrix_list += range(332,336) # MD_LGV/HGV/BUS/Rail
        matrix_list += range(352,357) # PM_LGV/HGV/BUS/Rail/WCE
        
        Dict = {}
        for mat_id in matrix_list:
            mat_name = "mf{}".format(mat_id)
            mat_exists = eb.matrix(mat_name)
            if mat_exists:
                name_key = self.rename_ROH_Demand(eb, mat_id)
                if "LGV" in name_key:
                    Dict[name_key] = util.get_matrix_numpy(eb, mat_name)/1.5
                elif "HGV" in name_key:
                    Dict[name_key] = util.get_matrix_numpy(eb, mat_name)/2.5
                else:
                    Dict[name_key] = util.get_matrix_numpy(eb, mat_name)
        
        self.ExportData(eb, Dict, "ROH_Demand.npz")
        
    def rename_ROH_Demand(self, eb, mf_number):
        #convert matrix name to npz export name
    
        if mf_number<300: # SOV/HOV example "HOV_pertrp_VOT_2_Pm"
            matrix_name = eb.matrix("mf{}".format(mf_number)).name.split("_")
            Time_of_Day = matrix_name[-1]
            VOT = matrix_name[-2]
            Class = matrix_name[0]
            export_name = Time_of_Day + "T" + Class + VOT
        else: # LGV/HGV example "lgvPceMd", Transit Mode example "railPm"
            matrix_name = eb.matrix("mf{}".format(mf_number)).name
            Time_of_Day = matrix_name[-2:]
            if "Pce" in matrix_name:
                Class = matrix_name[0:3]
            elif "rail" in matrix_name:
                Class = "RAL"
            else:
                Class = matrix_name[0:-2]
            export_name = Time_of_Day + "T" + Class + "9"
        return export_name.upper()
                
    @_m.logbook_trace("Export Data to npz file")
    def ExportData(self, eb, Dict, filename):
        util = _m.Modeller().tool("translink.util")
        
        OutputPath = os.path.join(util.get_eb_path(_m.Modeller().emmebank), 'EconomicAnalysis')
        if not os.path.exists(OutputPath):
            os.makedirs(OutputPath)
        OutputFile = os.path.join(OutputPath, filename)
        np.savez_compressed(OutputFile, **Dict)
        
    @_m.logbook_trace("Calculate ROH Benefits")
    def Calculate_ROH_Reliability_Benefits(self, eb, BaseScenario_Folder, AlternativeScenario_Folder, ensem, expansion_factors):
        util = _m.Modeller().tool("translink.util")
        
        #load npz into dictionary
        if BaseScenario_Folder:
            Base_Demand= np.load("{}/{}".format(BaseScenario_Folder,"ROH_Demand.npz"))
            Base_Time  = np.load("{}/{}".format(BaseScenario_Folder,"RELISKIM.npz"))
        Altr_Demand= np.load("{}/{}".format(AlternativeScenario_Folder,"ROH_Demand.npz"))
        Altr_Time  = np.load("{}/{}".format(AlternativeScenario_Folder,"RELISKIM.npz"))
        
        # mode_list = {mode_category: mode_group [mode, mode, mode]}
        mode_list = {"Auto": ["SOV1", "SOV2", "SOV3", "SOV4", "HOV1", "HOV2", "HOV3"],
                     "Light_Truck": ["LGV"], 
                     "Heavy_Truck": ["HGV"]}
                     
        NoTAZ = len(util.get_matrix_numpy(eb, "zoneindex"))
        
        Scenario_Master_DF = pd.DataFrame()
        for mode_category, mode_group in mode_list.iteritems():
            Time_Benefit_AM = np.zeros((NoTAZ,NoTAZ))
            Time_Benefit_MD = np.zeros((NoTAZ,NoTAZ))
            Time_Benefit_PM = np.zeros((NoTAZ,NoTAZ))
            
            for mode in mode_group:
                if len(mode)==3:
                    mode = mode + "9"
                
                if "HOV" in mode:
                    Occupancy = 2.25
                else:
                    Occupancy = 1
                
                #Auto Benefit for Existing Users (take minimum of base/alternative demand)
                #Calculate absolute value of each scenario
                if BaseScenario_Folder is None:
                    Time_Benefit_AM += Altr_Demand["AMT"+mode] * Altr_Time[self.get_reliability_layer("AM", mode)]
                    Time_Benefit_MD += Altr_Demand["MDT"+mode] * Altr_Time[self.get_reliability_layer("MD", mode)]
                    Time_Benefit_PM += Altr_Demand["PMT"+mode] * Altr_Time[self.get_reliability_layer("PM", mode)]
                else:
                    Time_Benefit_AM += np.minimum(Altr_Demand["AMT"+mode], Base_Demand["AMT"+mode]) * (Base_Time[self.get_reliability_layer("AM", mode)] - Altr_Time[self.get_reliability_layer("AM", mode)])
                    Time_Benefit_MD += np.minimum(Altr_Demand["MDT"+mode], Base_Demand["MDT"+mode]) * (Base_Time[self.get_reliability_layer("MD", mode)] - Altr_Time[self.get_reliability_layer("MD", mode)])
                    Time_Benefit_PM += np.minimum(Altr_Demand["PMT"+mode], Base_Demand["PMT"+mode]) * (Base_Time[self.get_reliability_layer("PM", mode)] - Altr_Time[self.get_reliability_layer("PM", mode)])
            
            AM_Fac, MD_Fac, PM_Fac = expansion_factors[mode[:3]]
            Daily_Time_Benefit = Time_Benefit_AM * AM_Fac + Time_Benefit_MD * MD_Fac + Time_Benefit_PM * PM_Fac
            
            # aggregate to ensemble 
            df = pd.concat([util.get_pd_ij_df(eb),util.get_ijensem_df(eb, ensem, ensem)], axis=1)
            ensem_i = '{}_from'.format(ensem)
            ensem_j = '{}_to'.format(ensem)
            df[['i','j', ensem_i, ensem_j]] = df[['i','j', '{}_i'.format(ensem), '{}_j'.format(ensem)]].astype(int)
            df["Daily_Benefits"] = Daily_Time_Benefit.flatten()     
            df = df.drop(['i','j'], axis = 1)
            df = df.groupby([ensem_i, ensem_j])
            df = df.sum().reset_index()
            df["Benefit_Category"] = '{}_{}'.format(mode_category, "RelTime(min)")
            Scenario_Master_DF = Scenario_Master_DF.append(df)
        
        Scenario_Master_DF["Year"] = self.get_scenario_info(eb, "horizon_year")
        Scenario_Master_DF["Scenario"] = self.get_scenario_info(eb, "alternative")
        
        Scenario_Master_DF.to_csv(os.path.join(AlternativeScenario_Folder,"Reliability_Benefits.csv"), index=False)
        Summary_DF = Scenario_Master_DF.groupby("Benefit_Category")["Daily_Benefits"].sum().reset_index()
        Summary_DF.to_csv(os.path.join(AlternativeScenario_Folder,"ProjectReliabilityBenefits.csv"), index=False)
        return Summary_DF
        
    def get_reliability_layer(self, tod, mode):
        reliability_matrix_name = {"SOV1": ["AmSovRelVot1","MdSovRelVot1","PmSovRelVot1"],
                                   "SOV2": ["AmSovRelVot2","MdSovRelVot2","PmSovRelVot2"],
                                   "SOV3": ["AmSovRelVot3","MdSovRelVot3","PmSovRelVot3"],
                                   "SOV4": ["AmSovRelVot4","MdSovRelVot4","PmSovRelVot4"],
                                   "HOV1": ["AmHovRelVot1","MdHovRelVot1","PmHovRelVot1"],
                                   "HOV2": ["AmHovRelVot2","MdHovRelVot2","PmHovRelVot2"],
                                   "HOV3": ["AmHovRelVot3","MdHovRelVot3","PmHovRelVot3"],
                                   "LGV9": ["AmLgvRel","MdLgvRel","PmLgvRel"],
                                   "HGV9": ["AmHgvRel","MdHgvRel","PmHgvRel"]}
        tod_index = ["AM","MD","PM"].index(tod)
        matrix_name = reliability_matrix_name[mode][tod_index]
        matrix_name = matrix_name.replace("Rel","RTIM").upper()
        return matrix_name
                       
    def get_scenario_info(self, eb, info):
        util = _m.Modeller().tool("translink.util")
        
        conn = util.get_rtm_db(eb)
        df = pd.read_sql_query("SELECT * FROM metadata", conn)
        conn.close()
        
        dict = df.to_dict("list")
        return dict[info][0]
