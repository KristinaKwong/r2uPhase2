##---------------------------------------------------------------------
##--TransLink Phase 3.2 Regional Transportation Model
##--
##--Path: EconomicAnalysis.agglomeration
##--Purpose: Compute Agglomeration
##---------------------------------------------------------------------
import inro.modeller as _m
import inro.emme.desktop as _d
import csv
import os
import numpy as np
import pandas as pd
import sqlite3
import traceback as _traceback

class ComputeAgglomeration(_m.Tool()):
    baseScenarioName = _m.Attribute(str)
    
    ensem_selector = _m.Attribute(str)
        
    tool_run_msg = _m.Attribute(unicode)
    
    def __init__(self):
        self.baseScenarioName = ""
        self.ensem_selector = ""
        
    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Compute Agglomeration"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)
            
        pb.add_text_box(tool_attribute_name="baseScenarioName", size=50, title="Baseline scenario name: ")
        pb.add_text_box(tool_attribute_name="ensem_selector", title="Select Project Area gh Ensemble",note="comma separated, example: 810, 820, 830",multi_line=True)
        
        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            eb = _m.Modeller().emmebank

            self(self.baseScenarioName, self.ensem_selector)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    def __call__(self, baseline_eb_title, ensem_selector):
        dt = _d.app.connect()
        de = dt.data_explorer()
        db = de.active_database()
        ebs = de.databases()
        util = _m.Modeller().tool("translink.util")
        
        # Get Base Scenario Folder
        BaseScenario_Folder = ""
        for eb in ebs:
            title = eb.title()
            if title == baseline_eb_title:
                BaseScenario_Folder = os.path.join(os.path.dirname(eb.path), "EconomicAnalysis")
        if BaseScenario_Folder=="":
            raise Exception('Base scenario emmebank is not in this project.')
                
        # Export Data to .npz repository
        for eb in ebs:
            title = eb.title()
            if title == 'Minimal Base Databank':
                continue
            
            eb.open()
            eb = _m.Modeller().emmebank
            
            self.Export_AgglomerationData(eb)
            self.Export_ROH_Demand(eb)
            self.Export_ROH_TimeCost(eb)
            
        # Calculation
        for eb in ebs:
            title = eb.title()
            if title == 'Minimal Base Databank' or title == baseline_eb_title:
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
            self.Calculate_Agglomeration_Benefits(eb, BaseScenario_Folder, AlternativeScenario_Folder, ensem_selector, expansion_factors)
        
    @_m.logbook_trace("Calculate Agglomeration Benefits")
    def Calculate_Agglomeration_Benefits(self, eb, BaseScenario_Folder, AlternativeScenario_Folder, ensem_selector, expansion_factors):
        # do not calculate agglomeration if ensemble is not selected
        if ensem_selector=="":
            return 0
    
        util = _m.Modeller().tool("translink.util")
        
        #load npz into dictionary
        Base_Demand= np.load("{}/{}".format(BaseScenario_Folder,"ROH_Demand.npz"))
        Base_Time  = np.load("{}/{}".format(BaseScenario_Folder,"ROH_Time.npz"))
        Base_Cost  = np.load("{}/{}".format(BaseScenario_Folder,"ROH_Cost.npz"))
        Altr_Demand= np.load("{}/{}".format(AlternativeScenario_Folder,"ROH_Demand.npz"))
        Altr_Time  = np.load("{}/{}".format(AlternativeScenario_Folder,"ROH_Time.npz"))
        Altr_Cost  = np.load("{}/{}".format(AlternativeScenario_Folder,"ROH_Cost.npz"))
        
        Base_Agglo  = np.load("{}/{}".format(BaseScenario_Folder,"AgglomerationData.npz"))
        Altr_Agglo  = np.load("{}/{}".format(AlternativeScenario_Folder,"AgglomerationData.npz"))
        
        # mode_list = {mode_category: mode_group [mode, mode, mode]}
        mode_list = {"Auto": ["SOV1", "SOV2", "SOV3", "SOV4"],
                     "Transit": ["BUS", "RAL", "WCE"]}
                     
        # voc_list = {mode_category: vehicle operating cost ($/min)}
        #voc_list = {"Auto": np.asscalar(util.get_matrix_numpy(eb, "msautoOpCost")),
        #            "Transit": 1,
        #            "Light_Truck": np.asscalar(util.get_matrix_numpy(eb, "mslgvOpCost")), 
        #            "Heavy_Truck": np.asscalar(util.get_matrix_numpy(eb, "mshgvOpCost"))}
        voc_list = {"Auto": 0.31,
                    "Transit": 0.31}
                    
        # elasticity_list = {sector: elasticity}
        # source: Graham et al. UK
        elasticity_list = {"ConMfg":   0.026,
                           "Fire":     0.083,
                           "TcuWh":    0.024,
                           "Ret":      0.024,
                           "BoS":      0.083,
                           "AcFoInCu": 0.024,
                           "HeEdPuAd": 0.024}
                           
        # distancedecay_list = {sector: distance decay}
        distancedecay_list = {"ConMfg":   1.298,
                              "Fire":     1.746,
                              "TcuWh":    1.818,
                              "Ret":      1.818,
                              "BoS":      1.746,
                              "AcFoInCu": 1.818,
                              "HeEdPuAd": 1.818}
                           
        # PerWorkerGDP_List = {sector: [2016 GDP/Worker [$], 2035 GDP/Worker [$], 2050 GDP/Worker [$]]}
        with open('EconomicAnalysis/Assumption_PerWorkerGDP.csv') as Input_csvfile:
            PerWorkerGDP_List = {}
            reader = csv.DictReader(Input_csvfile)
            for row in reader:
                PerWorkerGDP = [int(row["2016"]),int(row["2035"]),int(row["2050"])]
                PerWorkerGDP_List[row["Sector"]]=PerWorkerGDP
        
        NoTAZ = len(util.get_matrix_numpy(eb, "zoneindex"))
        
        master_df = pd.DataFrame()
        
        ensem = "gh"
        df = pd.concat([util.get_pd_ij_df(eb),util.get_ijensem_df(eb, ensem, ensem)], axis=1)
        ensem_i = '{}_from'.format(ensem)
        ensem_j = '{}_to'.format(ensem)
        df[['i','j', ensem_i, ensem_j]] = df[['i','j', '{}_i'.format(ensem), '{}_j'.format(ensem)]].astype(int)
        
        #get Employment by gh
        ensem = "gh"
        emp_i_df = pd.concat([util.get_pd_ij_df(eb),util.get_ijensem_df(eb, ensem, ensem)], axis=1)
        ensem_i = '{}_from'.format(ensem)
        ensem_j = '{}_to'.format(ensem)
        emp_i_df[['i','j', ensem_i, ensem_j]] = emp_i_df[['i','j', '{}_i'.format(ensem), '{}_j'.format(ensem)]].astype(int)
        for employment in ["TotEmp", "EmpConMfg", "EmpFire", "EmpTcuWh", "EmpRet", "EmpBoS", "EmpAcFoInCu", "EmpHeEdPuAd"]:        
            emp_i_df[employment] = np.where(emp_i_df.gh_from==1,(np.zeros((NoTAZ,NoTAZ))+np.transpose(Base_Agglo[employment])).flatten(),0)
        #get employment by gh
        emp_i_df =  emp_i_df.groupby([ensem_j])
        emp_i_df = emp_i_df.sum().reset_index()
        emp_i_df["gh"] = emp_i_df[ensem_j]
        emp_i_df = emp_i_df[(emp_i_df[ensem_i]>99)&(emp_i_df[ensem_j]>99)].drop(["i","j","gh_i","gh_j","gh_from","gh_to"], axis = 1)
            
        for mode_category, mode_group in mode_list.iteritems():
            AverageGC_Base = np.zeros((NoTAZ,NoTAZ))
            AverageGC_Altr = np.zeros((NoTAZ,NoTAZ))
            Demand_Daily_Base = np.zeros((NoTAZ,NoTAZ))
            Demand_Daily_Altr = np.zeros((NoTAZ,NoTAZ))
            DemandCost_Daily_Base = np.zeros((NoTAZ,NoTAZ))
            DemandCost_Daily_Altr = np.zeros((NoTAZ,NoTAZ))
            
            for mode in mode_group:
                if len(mode)==3:
                    mode = mode + "9"
                
                AM_Fac, MD_Fac, PM_Fac = expansion_factors[mode[:3]]
                GC_AM_Base = Base_Time["AMM"+mode] * voc_list[mode_category] + Base_Cost["AMC"+mode]
                GC_PM_Base = Base_Time["PMM"+mode] * voc_list[mode_category] + Base_Cost["PMC"+mode]
                if mode_category=="Auto":
                    GC_AM_Base += np.transpose(Base_Agglo["prk2hr"])
                    GC_PM_Base += np.transpose(Base_Agglo["prk2hr"])
                Demand_AM = Base_Demand["AMT"+mode] * AM_Fac
                Demand_PM = Base_Demand["PMT"+mode] * PM_Fac
                
                if mode == "WCE9":
                    GC_MD_Base = np.zeros((NoTAZ,NoTAZ))
                    Demand_MD = np.zeros((NoTAZ,NoTAZ))
                else:
                    GC_MD_Base = Base_Time["MDM"+mode] * voc_list[mode_category] + Base_Cost["MDC"+mode]
                    if mode_category=="Auto":
                        GC_MD_Base += np.transpose(Base_Agglo["prk2hr"])
                    Demand_MD = Base_Demand["MDT"+mode] * MD_Fac
                
                Demand_Daily_Base += Demand_AM + Demand_MD + Demand_PM
                DemandCost_Daily_Base += GC_AM_Base * Demand_AM + GC_MD_Base * Demand_MD + GC_PM_Base * Demand_PM
                ################
                GC_AM_Altr = Altr_Time["AMM"+mode] * voc_list[mode_category] + Altr_Cost["AMC"+mode]
                GC_PM_Altr = Altr_Time["PMM"+mode] * voc_list[mode_category] + Altr_Cost["PMC"+mode]
                if mode_category=="Auto":
                    GC_AM_Altr += np.transpose(Base_Agglo["prk2hr"])
                    GC_PM_Altr += np.transpose(Base_Agglo["prk2hr"])
                Demand_AM = Altr_Demand["AMT"+mode] * AM_Fac
                Demand_PM = Altr_Demand["PMT"+mode] * PM_Fac
                
                if mode == "WCE9":
                    GC_MD_Altr = np.zeros((NoTAZ,NoTAZ))
                    Demand_MD = np.zeros((NoTAZ,NoTAZ))
                else:
                    GC_MD_Altr = Altr_Time["MDM"+mode] * voc_list[mode_category] + Altr_Cost["MDC"+mode]
                if mode_category=="Auto":
                    GC_MD_Altr += np.transpose(Base_Agglo["prk2hr"])
                    Demand_MD = Altr_Demand["MDT"+mode] * MD_Fac
                
                Demand_Daily_Altr += Demand_AM + Demand_MD + Demand_PM
                DemandCost_Daily_Altr += GC_AM_Altr * Demand_AM + GC_MD_Altr * Demand_MD + GC_PM_Altr * Demand_PM
                
            
            df['DemandCost_Daily_Base_{}'.format(mode_category)] = DemandCost_Daily_Base.flatten()                      
            df['DemandCost_Daily_Altr_{}'.format(mode_category)] = DemandCost_Daily_Altr.flatten()                  
            df['Demand_Daily_Base_{}'.format(mode_category)] = Demand_Daily_Base.flatten()                                    
            df['Demand_Daily_Altr_{}'.format(mode_category)] = Demand_Daily_Altr.flatten()      
                       
        df = df.groupby([ensem_i, ensem_j])
        df = df.sum().reset_index()
        df['AverageGC_Base_Auto'] = np.where(df["Demand_Daily_Base_Auto"]==0, 0, df["DemandCost_Daily_Base_Auto"]/df["Demand_Daily_Base_Auto"])
        df['AverageGC_Base_Transit'] = np.where(df["Demand_Daily_Base_Transit"]==0, 0, df["DemandCost_Daily_Base_Transit"]/df["Demand_Daily_Base_Transit"])
        df['AverageGC_Altr_Auto'] = np.where(df["Demand_Daily_Altr_Auto"]==0, 0, df["DemandCost_Daily_Altr_Auto"]/df["Demand_Daily_Altr_Auto"])
        df['AverageGC_Altr_Transit'] = np.where(df["Demand_Daily_Altr_Transit"]==0, 0, df["DemandCost_Daily_Altr_Transit"]/df["Demand_Daily_Altr_Transit"])
        
        df = df.drop(['i','j','{}_i'.format(ensem), '{}_j'.format(ensem)], axis = 1)        
        
        #join total employment to gh_by_gh_dataframe
        df = pd.merge(df, emp_i_df, left_on="gh_to", right_on="gh", how="left")
        
        #Calculate Effective Density
        for employment in ["EmpConMfg", "EmpFire", "EmpTcuWh", "EmpRet", "EmpBoS", "EmpAcFoInCu", "EmpHeEdPuAd"]:        
            distance_decay = distancedecay_list[employment[3:]]
            df['EffDensity_Base_{}'.format(employment)] = np.where(df['AverageGC_Base_Auto']   ==0, 0, df["TotEmp"]/np.power(df['AverageGC_Base_Auto']   , distance_decay)) \
                                                        + np.where(df['AverageGC_Base_Transit']==0, 0, df["TotEmp"]/np.power(df['AverageGC_Base_Transit'], distance_decay))
            df['EffDensity_Altr_{}'.format(employment)] = np.where(df['AverageGC_Altr_Auto']   ==0, 0, df["TotEmp"]/np.power(df['AverageGC_Altr_Auto']   , distance_decay)) \
                                                        + np.where(df['AverageGC_Altr_Transit']==0, 0, df["TotEmp"]/np.power(df['AverageGC_Altr_Transit'], distance_decay))
        #print(df.describe())
        
        header_list = [ensem_i]
        for employment in ["EmpConMfg", "EmpFire", "EmpTcuWh", "EmpRet", "EmpBoS", "EmpAcFoInCu", "EmpHeEdPuAd"]:
            header_list.append('EffDensity_Base_{}'.format(employment))
            header_list.append('EffDensity_Altr_{}'.format(employment))
        i_df = df[header_list].groupby([ensem_i])
        i_df = i_df.sum().reset_index()
        
        #Calculat Productivity Improvement (as %GDP)
        for employment in ["EmpConMfg", "EmpFire", "EmpTcuWh", "EmpRet", "EmpBoS", "EmpAcFoInCu", "EmpHeEdPuAd"]:
            elasticity = elasticity_list[employment[3:]]
            i_df['Productivity_{}'.format(employment)] = np.where(i_df['EffDensity_Base_{}'.format(employment)]==0, 0, np.power(i_df['EffDensity_Altr_{}'.format(employment)]/i_df['EffDensity_Base_{}'.format(employment)], elasticity) - 1)
        
        i_df = pd.merge(i_df, emp_i_df, left_on="gh_from", right_on="gh", how="left")
        
        #Calculate Productivity_Impact
        year = self.get_scenario_info(eb, "horizon_year")
        year_index = [2016, 2035, 2050].index(year)
        for employment in ["EmpConMfg", "EmpFire", "EmpTcuWh", "EmpRet", "EmpBoS", "EmpAcFoInCu", "EmpHeEdPuAd"]:  
            PerWorkerGDP = PerWorkerGDP_List[employment[3:]][year_index]  
            i_df['ProductivityImpact_{}'.format(employment)] = i_df['Productivity_{}'.format(employment)] * i_df[employment] * PerWorkerGDP
        
        ProductivityImpact_Scenario = 0
        # convert the ensemble selector input to a list
        ensem_selector = map(int,ensem_selector.split(","))
        for employment in ["EmpConMfg", "EmpFire", "EmpTcuWh", "EmpRet", "EmpBoS", "EmpAcFoInCu", "EmpHeEdPuAd"]:  
            ProductivityImpact_Scenario += i_df[i_df[ensem_i].isin(ensem_selector)]['ProductivityImpact_{}'.format(employment)].sum()
        
        # drop irrelevant columns
        header_list = [ensem_i]
        for employment in ["EmpConMfg", "EmpFire", "EmpTcuWh", "EmpRet", "EmpBoS", "EmpAcFoInCu", "EmpHeEdPuAd"]:
            header_list.append('ProductivityImpact_{}'.format(employment))
        i_df = i_df[header_list]
        return ProductivityImpact_Scenario
        
    @_m.logbook_trace("Export Parking and Employment for Agglomeration Calculation")
    def Export_AgglomerationData(self, eb):
        util = _m.Modeller().tool("translink.util")
        
        with_previous_export = os.path.isfile(os.path.join(util.get_eb_path(eb), 'EconomicAnalysis', 'AgglomerationData.npz'))
        if with_previous_export:
            return # do not re-export
                    
        # list mf matrix number to be exported
        matrix_list = [60, 61] # parking
        matrix_list += range(20, 28) # Employment
        
        Dict = {}
        for mat_id in matrix_list:
            mat_name = "mo{}".format(mat_id)
            mat_exists = eb.matrix(mat_name)
            if mat_exists:
                Dict[eb.matrix(mat_name).name] = util.get_matrix_numpy(eb, mat_name)
        
        self.ExportData(eb, Dict, "AgglomerationData.npz")
                
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

    @_m.logbook_trace("Export ROH Time and OpCost Data")
    def Export_ROH_TimeCost(self, eb):
        util = _m.Modeller().tool("translink.util")
        
        with_previous_export = os.path.isfile(os.path.join(util.get_eb_path(eb), 'EconomicAnalysis', 'ROH_Time.npz'))
        with_previous_export = with_previous_export & (os.path.isfile(os.path.join(util.get_eb_path(eb), 'EconomicAnalysis', 'ROH_Cost.npz')))
        if with_previous_export:
            return # do not re-export
        
        Time_Dict = {}
        Cost_Dict = {}
        
        # list Auto and Truck matrix number to be exported
        matrix_list = []
        matrix_list += range(5000,5020) # AM SOV/HOV Time/Cost
        matrix_list += range(5024,5050) # AM LGV/HGV, MD SOV/HOV Time/Cost
        matrix_list += range(5054,5080) # MD LGV/HGV, PM SOV/HOV Time/Cost
        matrix_list += range(5084,5089) # PM LGV/HGV Time/Cost
        for mat_id in matrix_list:
            mat_name = "mf{}".format(mat_id)
            mat_exists = eb.matrix(mat_name)
            if mat_exists:
                name_key = self.rename_ROH_AutoTimeCost(eb, mat_id)
                Is_Time_Skim = "Time" in mat_exists.name
                if Is_Time_Skim:
                    Time_Dict[name_key] = util.get_matrix_numpy(eb, mat_name)
                else:
                    Cost_Dict[name_key] = util.get_matrix_numpy(eb, mat_name)
                
        # list Transit Fare matrix number to be exported
        matrix_list = []
        matrix_list += [5304, 5314, 5324] # AM/MD/PM Bus Fare
        matrix_list += [5505, 5515, 5525] # AM/MD/PM Rail Fare
        matrix_list += [5706, 5726] # AM/PM WCE Fare
        NoTAZ = len(util.get_matrix_numpy(eb, "zoneindex"))
        for mat_id in matrix_list:
            mat_name = "mf{}".format(mat_id)
            name_key = self.rename_ROH_TransitTimeCost(eb, mat_id)
            Cost_Dict[name_key] = util.get_matrix_numpy(eb, mat_name)
            
            name_key = name_key[:2] + "M" + name_key[-4:]
            TimeMatrixCount = int(mat_name[-1])
            Time_Dict[name_key] = np.zeros((NoTAZ,NoTAZ))
            for TimeMatrixDigit in range(0,TimeMatrixCount):
                # lookup transit time perception factor
                if TimeMatrixCount-TimeMatrixDigit==1:
                    transit_perception_factor = 10.0 #boarding time
                elif TimeMatrixCount-TimeMatrixDigit==2:
                    transit_perception_factor = 2.0 #auxilliary time
                elif TimeMatrixCount-TimeMatrixDigit==3:
                    transit_perception_factor = 2.5 # waiting time
                elif TimeMatrixCount-TimeMatrixDigit==4:
                    transit_perception_factor = 1.25 # bus IVTT time
                else:
                    transit_perception_factor = 1.0
                
                time_mat_name = mat_name[:-1] + str(TimeMatrixDigit)
                Time_Dict[name_key] += util.get_matrix_numpy(eb, time_mat_name)*transit_perception_factor
                
        self.ExportData(eb, Time_Dict, "ROH_Time.npz")
        self.ExportData(eb, Cost_Dict, "ROH_Cost.npz")
        
    def rename_ROH_TransitTimeCost(self, eb, mf_number):
        #convert matrix name to npz export name
        
        matrix_name = eb.matrix("mf{}".format(mf_number)).name
        Time_of_Day = matrix_name[:2]
        if "Rail" in matrix_name:
            Class = "RAL"
        else:
            Class = matrix_name[2:5]
        export_name = Time_of_Day + "C" + Class + "9"
        return export_name.upper()
        
    def rename_ROH_AutoTimeCost(self, eb, mf_number):
        #convert matrix name to npz export name
        
        matrix_name = eb.matrix("mf{}".format(mf_number)).name
        Time_of_Day = matrix_name[:2]
        Class = matrix_name[2:5]
        if "Time" in matrix_name:
            Data_Type = "M"
        else:
            Data_Type = "C"
        if "ov" in Class:
            VOT = matrix_name[-1:]
            export_name = Time_of_Day + Data_Type + Class + VOT
        else:
            export_name = Time_of_Day + Data_Type + Class + "9"
        return export_name.upper()
        
        
    @_m.logbook_trace("Export Data to npz file")
    def ExportData(self, eb, Dict, filename):
        util = _m.Modeller().tool("translink.util")
        
        OutputPath = os.path.join(util.get_eb_path(_m.Modeller().emmebank), 'EconomicAnalysis')
        if not os.path.exists(OutputPath):
            os.makedirs(OutputPath)
        OutputFile = os.path.join(OutputPath, filename)
        np.savez_compressed(OutputFile, **Dict)
        
    def get_scenario_info(self, eb, info):
        util = _m.Modeller().tool("translink.util")
        
        conn = util.get_rtm_db(eb)
        df = pd.read_sql_query("SELECT * FROM metadata", conn)
        conn.close()
        
        dict = df.to_dict("list")
        return dict[info][0]
