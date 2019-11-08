##---------------------------------------------------------------------
##--TransLink Phase 3.2 Regional Transportation Model
##--
##--Path: EconomicAnalysis.summarizebenefits
##--Purpose: Summarize User Benefits
##---------------------------------------------------------------------
import inro.modeller as _m
import inro.emme.desktop as _d
import csv
import os
import numpy as np
import pandas as pd
import sqlite3
import traceback as _traceback

class SummarizeUserBenefits(_m.Tool()):        
    tool_run_msg = _m.Attribute(unicode)
    ensem_selector = _m.Attribute(str)
        
    def __init__(self):
        self.ensem_selector = ""
        
    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Summarize User Benefits" 
        pb.description = "Specify BAU and Alternative Databanks in EconomicAnalysisTool_Input.csv"
        pb.add_text_box(tool_attribute_name="ensem_selector", title="Calaculate Agglomeration: Select Project Area gh Ensemble",note="comma separated, example: 810, 820, 830",multi_line=True)

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)
        
        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            eb = _m.Modeller().emmebank

            self(eb,self.ensem_selector)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Summarize User Benefits")
    def __call__(self, eb, ensem_selector):
        
        ##load emmebank title, emmebank path, emmebank EcoAnalysis path, emmebank object into dictionary
        emmebank_object = {}
        database_object = {}
        emmebank_path   = {}
        emmebank_EApath = {}
        emmebank_title  = []
        
        dt = _d.app.connect()
        de = dt.data_explorer()
        db = de.active_database()
        ebs = de.databases()
        
        for eb in ebs:
            title = eb.title()
            database_object[title] = eb
            eb.open()
            eb = _m.Modeller().emmebank
            emmebank_object[title] = eb
            emmebank_path[title]   = os.path.dirname(eb.path)
            emmebank_EApath[title] = os.path.join(os.path.dirname(eb.path), "EconomicAnalysis")
            emmebank_title.append(title)
        
        # load input csv file, check if all the emmebanks are in this EMME project
        with open('EconomicAnalysis/EconomicAnalysisTool_Input.csv') as Input_csvfile: #this file to be a user input
            reader = csv.DictReader(Input_csvfile)
            for row in reader:
                if not(row["Alternative Databank"] in (emmebank_title)):
                    raise Exception("%s is not in this EMME project"%row["Alternative Databank"])
                elif not(row["BAU Databank"] in (emmebank_title)):
                    raise Exception("%s is not in this EMME project"%row["BAU Databank"]) 
        
        # setup tracker to note scenario with freeflow/LOS_D assignment, do not rerun
        LOS_D_Assignment_Tracker = {}
        for emmebank in emmebank_title:
            LOS_D_Assignment_Tracker[emmebank] = False
        
        # load input csv file, check if all the emmebanks are in this EMME project
        with open('EconomicAnalysis/EconomicAnalysisTool_Input.csv') as Input_csvfile, open('EconomicAnalysis/Benefit_Summary.csv', 'wb') as Output_csvfile: #this file to be a user input
            reader = csv.DictReader(Input_csvfile)
            
            fieldnames = ['Alternative', 'Alternative Databank', 'BAU Databank', 'Horizon']
            Units = {'Alternative':'', 'Alternative Databank':'', 'BAU Databank':'', 'Horizon':''}
            fieldnames.append('Auto Logsum Benefit')
            Units['Auto Logsum Benefit'] = 'Daily Minutes'
            fieldnames.append('Light Truck Travel Benefit')
            Units['Light Truck Travel Benefit'] = 'Daily Minutes'
            fieldnames.append('Heavy Truck Travel Benefit')
            Units['Heavy Truck Travel Benefit'] = 'Daily Minutes'
            fieldnames.append('Transit Logsum Benefit')
            Units['Transit Logsum Benefit'] = 'Daily Minutes'
            fieldnames.append('Auto Reliability')
            Units['Auto Reliability'] = 'Daily Minutes'
            fieldnames.append('Light Truck Reliability')
            Units['Light Truck Reliability'] = 'Daily Minutes'
            fieldnames.append('Heavy Truck Reliability')
            Units['Heavy Truck Reliability'] = 'Daily Minutes'
            fieldnames.append('Incremental Fare Revenue')
            Units['Incremental Fare Revenue'] = 'Daily 2016$'
            fieldnames.append('Agglomeration Benefit')
            Units['Agglomeration Benefit'] = 'Annual $'
            fieldnames.append('GHG')
            Units['GHG'] = 'Annual $'
            fieldnames.append('Safety Benefit')
            Units['Safety Benefit'] = 'Annual $'
            
            writer = csv.DictWriter(Output_csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # expansion factor used for: agglomeration, getVKT, auto reliability, conventional benefits
            expansion_factors = {"SOV": [3.44, 8.41, 3.95],
                                 "HOV": [1.51, 8.58, 5.32],
                                 "BUS": [2.54, 9.44, 2.57],
                                 "RAL": [2.53, 9.54, 2.92],
                                 "WCE": [3.34,    0, 2.02],
                                 "LGV": [3.59, 5.63, 6.17],
                                 "HGV": [4.88, 5.43, 6.36]}
            
            ensem = "gy"
            
            for row in reader:
                BaseScenario_Folder = emmebank_EApath[row["BAU Databank"]]
                AlternativeScenario_Folder = emmebank_EApath[row["Alternative Databank"]]
                BAU_emmebank = emmebank_object[row["BAU Databank"]]
                Alternative_emmebank = emmebank_object[row["Alternative Databank"]]
                Horizon = row['Horizon']
                
                # get GHG/Safety Benefit
                getVKT = _m.Modeller().tool("EconomicAnalysis.getvkt")
                # getVKT returns annual vkt by emmebank
                database_object[row["BAU Databank"]].open()
                Auto_BaseVKT, LGV_BaseVKT, HGV_BaseVKT = getVKT.get_annual_vkt(BAU_emmebank, expansion_factors, "all")
                database_object[row["Alternative Databank"]].open()
                Auto_AltrVKT, LGV_AltrVKT, HGV_AltrVKT = getVKT.get_annual_vkt(Alternative_emmebank, expansion_factors, "all")
                # GHG Emission rates $2018/vkt by mode, [2017, 2035, 2050]
                GHG_Emission_Rates = {"Auto":[0.0118332, 0.0144050, 0.0158190],
                                      "LGV" :[0.0183361, 0.0234403, 0.0271553],
                                      "HGV" :[0.0431519, 0.0750505, 0.0919084]}
                horizon_index = ['2017', '2035', '2050'].index(Horizon)
                GHG_Emission_Benefit = 0
                GHG_Emission_Benefit += (Auto_BaseVKT - Auto_AltrVKT) * GHG_Emission_Rates["Auto"][horizon_index]
                GHG_Emission_Benefit += (LGV_BaseVKT  -  LGV_AltrVKT) * GHG_Emission_Rates["LGV"][horizon_index]
                GHG_Emission_Benefit += (HGV_BaseVKT  -  HGV_AltrVKT) * GHG_Emission_Rates["HGV"][horizon_index]
                row["GHG"] = GHG_Emission_Benefit
                # Safety Benefit rate $2018/VKT
                # Safety benefit to be added as user input on tool page
                Safety_Benefit_rate = 0.15803386 #this rate is specific to Fraser hwy corridor
                Safety_Benefit = (Auto_BaseVKT + LGV_BaseVKT + HGV_BaseVKT - Auto_AltrVKT - LGV_AltrVKT - HGV_AltrVKT) * Safety_Benefit_rate
                row["Safety Benefit"] = Safety_Benefit
                
                # get Truck Daily OpCost Savings (in dollar)
                LightTruck_DailyToAnnualFactor = 313
                HeavyTruck_DailyToAnnualFactor = 276
                LightTruck_OpCostBenefit = (LGV_BaseVKT - LGV_AltrVKT) * 0.24 / LightTruck_DailyToAnnualFactor
                HeavyTruck_OpCostBenefit = (HGV_BaseVKT - HGV_AltrVKT) * 0.56 / HeavyTruck_DailyToAnnualFactor
                
                # get conventional benefits
                # Export npz files
                ConventionalBenefits = _m.Modeller().tool("EconomicAnalysis.conventionalbenefits")
                for databank in [row["BAU Databank"], row["Alternative Databank"]]:
                    database_object[databank].open()
                    eb = _m.Modeller().emmebank
                    ConventionalBenefits.Export_ROH_Demand(eb)
                    ConventionalBenefits.Export_ROH_TimeCost(eb)
                    ConventionalBenefits.Export_LogSum_Demand(eb)
                    ConventionalBenefits.Export_PA_Factors(eb)
                    # re-calculate utility in mode choice, then export utility
                    ConventionalBenefits.Export_LogSum_Utility(eb)
                ConventionalBenefits_df = ConventionalBenefits.compute_LogsumROH_benefits(database_object[row["Alternative Databank"]], BaseScenario_Folder, AlternativeScenario_Folder, ensem, expansion_factors)    
                ConventionalBenefits_df.drop(ConventionalBenefits_df.tail(3).index,inplace=True)
                # Update Benefit Category Name (deal with missing pandas function rsplit)
                ConventionalBenefits_df["Benefit_Category"] = np.where(ConventionalBenefits_df["Benefit_Category"]=="Light_Truck_Cost($)","LightTruck_Cost($)",ConventionalBenefits_df["Benefit_Category"])
                ConventionalBenefits_df["Benefit_Category"] = np.where(ConventionalBenefits_df["Benefit_Category"]=="Heavy_Truck_Cost($)","HeavyTruck_Cost($)",ConventionalBenefits_df["Benefit_Category"])
                ConventionalBenefits_df["Benefit_Category"] = np.where(ConventionalBenefits_df["Benefit_Category"]=="Light_Truck_Time(min)","LightTruck_Time(min)",ConventionalBenefits_df["Benefit_Category"])
                ConventionalBenefits_df["Benefit_Category"] = np.where(ConventionalBenefits_df["Benefit_Category"]=="Heavy_Truck_Time(min)","HeavyTruck_Time(min)",ConventionalBenefits_df["Benefit_Category"])
                ConventionalBenefits_df["Mode"], ConventionalBenefits_df["Category"] = ConventionalBenefits_df["Benefit_Category"].str.split("_", 1).str
                IsCostBenefit = (ConventionalBenefits_df["Category"]=="Cost($)")
                IsTruckCostBenefit = IsCostBenefit & ((ConventionalBenefits_df["Mode"]=="LightTruck")|(ConventionalBenefits_df["Mode"]=="HeavyTruck"))
                # Convert OpCost to Minutes
                ConventionalBenefits_df["Benefit_minutes"] = np.where(IsCostBenefit, ConventionalBenefits_df["Daily_Benefits"].astype(np.float64)/0.31, ConventionalBenefits_df["Daily_Benefits"].astype(np.float64))
                # Zero out truck opcost benefit from ROH method (truck opcost is affected by truck penalty)
                ConventionalBenefits_df["Benefit_minutes"] = np.where(IsTruckCostBenefit, 0, ConventionalBenefits_df["Benefit_minutes"].astype(np.float64))
                ConventionalBenefits_df = ConventionalBenefits_df.groupby(["Mode","Method"])["Benefit_minutes"].sum().reset_index()
                row["Auto Logsum Benefit"] = ConventionalBenefits_df.loc[(ConventionalBenefits_df.Mode=="Auto")&(ConventionalBenefits_df.Method=="Logsum"),"Benefit_minutes"].sum()
                row["Transit Logsum Benefit"] = ConventionalBenefits_df.loc[(ConventionalBenefits_df.Mode=="Transit")&(ConventionalBenefits_df.Method=="Logsum"),"Benefit_minutes"].sum()
                LightTruck_TravelTimeBenefit = ConventionalBenefits_df.loc[(ConventionalBenefits_df.Mode=="LightTruck")&(ConventionalBenefits_df.Method=="ROH"),"Benefit_minutes"].sum()
                HeavyTruck_TravelTimeBenefit = ConventionalBenefits_df.loc[(ConventionalBenefits_df.Mode=="HeavyTruck")&(ConventionalBenefits_df.Method=="ROH"),"Benefit_minutes"].sum()
                row["Light Truck Travel Benefit"] = LightTruck_TravelTimeBenefit + LightTruck_OpCostBenefit/0.52 #convert $ benefit to minutes
                row["Heavy Truck Travel Benefit"] = HeavyTruck_TravelTimeBenefit + HeavyTruck_OpCostBenefit/0.52
                
                # get Auto Reliability Benefit
                # run auto reliability/LOS_D assignment
                for databank in [row["BAU Databank"], row["Alternative Databank"]]:
                    if LOS_D_Assignment_Tracker[databank]:
                        continue #to next databank, do not re-run freeflow/LOS_D assignment
                    database_object[databank].open()
                    eb = _m.Modeller().emmebank
                    am_scen = eb.scenario(int(eb.matrix("msAmScen").data))
                    md_scen = eb.scenario(int(eb.matrix("msMdScen").data))
                    pm_scen = eb.scenario(int(eb.matrix("msPmScen").data))
                    assignment_type = 1
                    inc = 100
                    ReliabilityAssignment = _m.Modeller().tool("EconomicAnalysis.ffassignment")
                    ReliabilityAssignment(eb, am_scen, md_scen, pm_scen, assignment_type, inc)
                    LOS_D_Assignment_Tracker[databank] = True
                # calculate auto reliability benefits
                getReliabilityBenefit = _m.Modeller().tool("EconomicAnalysis.autoreliability")
                ReliabilityBenefit_df = getReliabilityBenefit.Calculate_ROH_Reliability_Benefits(eb, BaseScenario_Folder, AlternativeScenario_Folder, ensem, expansion_factors)
                row["Auto Reliability"] = ReliabilityBenefit_df.loc[ReliabilityBenefit_df.Benefit_Category=="Auto_RelTime(min)","Daily_Benefits"].sum()
                row["Light Truck Reliability"] = ReliabilityBenefit_df.loc[ReliabilityBenefit_df.Benefit_Category=="Light_Truck_RelTime(min)","Daily_Benefits"].sum()
                # Calculate Heavy Truck Relibility by adjusting light truck reliability with truck annual travel benefits factors
                row["Heavy Truck Reliability"] = row["Light Truck Reliability"] * (row["Heavy Truck Travel Benefit"]*276)/(row["Light Truck Travel Benefit"]*313)
                
                # get incremental fare revenue
                getIncFareRevenue = _m.Modeller().tool("EconomicAnalysis.fareelasticity")
                DailyIncFareRev = getIncFareRevenue.export_transit_data("%s\emmebank"%emmebank_path[row["BAU Databank"]],"%s\emmebank"%emmebank_path[row["Alternative Databank"]])
                row["Incremental Fare Revenue"] = DailyIncFareRev
                
                getagglomeration = _m.Modeller().tool("EconomicAnalysis.agglomeration")
                # Export npz files
                for databank in [row["BAU Databank"], row["Alternative Databank"]]:
                    database_object[databank].open()
                    eb = _m.Modeller().emmebank
                    getagglomeration.Export_AgglomerationData(eb)
                    getagglomeration.Export_ROH_Demand(eb)
                    getagglomeration.Export_ROH_TimeCost(eb)
                eb = emmebank_object[row["Alternative Databank"]]
                # calculate agglomeration benefit
                agglomeration_benefit = getagglomeration.Calculate_Agglomeration_Benefits(eb, BaseScenario_Folder, AlternativeScenario_Folder, ensem_selector, expansion_factors)
                row["Agglomeration Benefit"] = agglomeration_benefit
                
                
                writer.writerow(row)
            
            writer.writerow(Units)
        
        # Transpose output table to be consistent format with benefit/cost streaming spreadsheet
        output_df = pd.read_csv('EconomicAnalysis/Benefit_Summary.csv')
        output_df.transpose().to_csv('EconomicAnalysis/Benefit_Summary.csv')
        
        
        
        
        
        
        
        
        
        
        
        
        
        