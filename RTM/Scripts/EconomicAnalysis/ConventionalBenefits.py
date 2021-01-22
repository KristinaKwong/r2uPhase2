##---------------------------------------------------------------------
##--TransLink Phase 3.2 Regional Transportation Model
##--
##--Path: EconomicAnalysis.conventionalbenefits
##--Purpose: Compute conventional user benefits using ROH/Logsum approach
##---------------------------------------------------------------------
import inro.modeller as _m
import inro.emme.desktop as _d
import csv
import os
import numpy as np
import pandas as pd
import sqlite3
import traceback as _traceback

class EconomicAnalysis(_m.Tool()):
    baseScenarioName = _m.Attribute(str)

    ensem = _m.Attribute(str)

    tool_run_msg = _m.Attribute(unicode)

    def __init__(self):
        self.baseScenarioName = "2016Base"
        self.ensem = "gm"

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Export Data for Economic Benefit Analysis"
        pb.description = "Logsum and Rule-of-Half Benefits"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        pb.add_text_box(tool_attribute_name="baseScenarioName", size=50, title="Baseline scenario name: ")
        pb.add_text_box(tool_attribute_name="ensem", size=2, title="Ensemble")

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            eb = _m.Modeller().emmebank

            self(self.baseScenarioName, self.ensem)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Export Data for Economic Benefit Analysis")
    def __call__(self, baseline_eb_title, ensem):
        dt = _m.Modeller().desktop
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

        # Check if ensemble is valid
        if not ((ensem[0]=="g") and ensem[1].isalpha() and ensem[1].islower()):
            raise Exception("Ensemble should be 'g' followed by a lowercase letter a-z.")

        # Export Data to .npz repository
        for eb in ebs:
            title = eb.title()
            if title == 'Minimal Base Databank':
                continue

            eb.open()
            eb = _m.Modeller().emmebank

            self.Export_ROH_Demand(eb)
            self.Export_ROH_TimeCost(eb)
            self.Export_LogSum_Demand(eb)
            self.Export_PA_Factors(eb)

            # re-calculate utility in mode choice, then export utility
            self.Export_LogSum_Utility(eb)

        # Calculation
        for eb in ebs:
            title = eb.title()
            if title == 'Minimal Base Databank' or title == baseline_eb_title:
                continue
            eb.open()
            eb_object = _m.Modeller().emmebank
            AlternativeScenario_Folder = os.path.join(os.path.dirname(eb_object.path), "EconomicAnalysis")

            expansion_factors = {"SOV": [3.44, 8.41, 3.95],
                                 "HOV": [1.51, 8.58, 5.32],
                                 "BUS": [4.24, 4.85, 4.22],
                                 "RAL": [4.24, 4.85, 4.22],
                                 "WCE": [3.34,    0, 2.02],
                                 "LGV": [3.59, 5.63, 6.17],
                                 "HGV": [4.88, 5.43, 6.36]}
            self.compute_LogsumROH_benefits(eb, BaseScenario_Folder, AlternativeScenario_Folder, ensem, expansion_factors)

    def compute_LogsumROH_benefits(self, eb, BaseScenario_Folder, AlternativeScenario_Folder, ensem, expansion_factors):
        title = eb.title()
        eb.open()
        eb = _m.Modeller().emmebank
        ROH_Master_DF = pd.DataFrame()
        Logsum_Master_DF = pd.DataFrame()
        ROH_Master_DF = ROH_Master_DF.append(self.Calculate_ROH_Benefits(eb, BaseScenario_Folder, AlternativeScenario_Folder, ensem, expansion_factors))
        Logsum_Master_DF = Logsum_Master_DF.append(self.Calculate_Logsum_Benefits(eb, BaseScenario_Folder, AlternativeScenario_Folder, ensem))

        ROH_Master_DF = ROH_Master_DF[["Year", "{}_from".format(ensem), "{}_to".format(ensem), "Scenario", "Benefit_Category", "Daily_Benefits"]]
        Logsum_Master_DF = Logsum_Master_DF[["Year", "{}_from".format(ensem), "{}_to".format(ensem), "Scenario", "Purpose", "Income", "Auto_Ownership", "Mode", "Daily_Benefits(min)"]]

        conn = sqlite3.connect(os.path.join(AlternativeScenario_Folder,"EconomicAnalysis.db"))
        ROH_Master_DF.to_sql(name='ROH_Benefits', con=conn, index=False, if_exists='replace')
        Logsum_Master_DF.to_sql(name='Logsum_Benefits', con=conn, index=False, if_exists='replace')
        conn.close()

        ROH_Master_DF.to_csv(os.path.join(AlternativeScenario_Folder,"ROH_Benefits.csv"), index=False)
        Logsum_Master_DF.to_csv(os.path.join(AlternativeScenario_Folder,"Logsum_Benefits.csv"), index=False)

        #Summarize Project benefits
        Summary_DF = ROH_Master_DF.groupby("Benefit_Category")["Daily_Benefits"].sum().reset_index()
        Summary_DF["Method"] = "ROH"
        Summary_DF.loc[len(Summary_DF)] = ["Total_Time(min)",Logsum_Master_DF["Daily_Benefits(min)"].sum(),"Logsum"]
        Summary_DF.loc[len(Summary_DF)] = ["Auto_Time(min)",Logsum_Master_DF.loc[Logsum_Master_DF.Mode=="Auto","Daily_Benefits(min)"].sum(),"Logsum"]
        Summary_DF.loc[len(Summary_DF)] = ["Transit_Time(min)",Logsum_Master_DF.loc[Logsum_Master_DF.Mode=="Transit","Daily_Benefits(min)"].sum(),"Logsum"]
        Summary_DF.loc[len(Summary_DF)] = ["Active_Time(min)",Logsum_Master_DF.loc[Logsum_Master_DF.Mode=="Active","Daily_Benefits(min)"].sum(),"Logsum"]
        Summary_DF.loc[len(Summary_DF)] = ["Project_Scenario",self.get_scenario_info(eb, "alternative"),"-"]
        Summary_DF.loc[len(Summary_DF)] = ["Project_Year",self.get_scenario_info(eb, "horizon_year"),"-"]
        Summary_DF.loc[len(Summary_DF)] = ["Emmebank_Name",title,"-"]
        Summary_DF.to_csv(os.path.join(AlternativeScenario_Folder,"ProjectBenefits.csv"), index=False)
        return Summary_DF

    @_m.logbook_trace("Calculate Logsum Benefits")
    def Calculate_Logsum_Benefits(self, eb, BaseScenario_Folder, AlternativeScenario_Folder, ensem):
        util = _m.Modeller().tool("translink.util")

        #load npz into dictionary
        Base_Demand= np.load("{}/{}".format(BaseScenario_Folder,"LogSum_Demand.npz"))
        Base_Utility  = np.load("{}/{}".format(BaseScenario_Folder,"LogSum_Utility.npz"))
        Altr_Demand= np.load("{}/{}".format(AlternativeScenario_Folder,"LogSum_Demand.npz"))
        Altr_Utility  = np.load("{}/{}".format(AlternativeScenario_Folder,"LogSum_Utility.npz"))

        Base_UtilitySplit  = np.load("{}/{}".format(BaseScenario_Folder,"LogSum_UtilitySplit.npz"))
        Altr_UtilitySplit  = np.load("{}/{}".format(AlternativeScenario_Folder,"LogSum_UtilitySplit.npz"))

        PA_Factor_Dict = np.load("{}/{}".format(AlternativeScenario_Folder,"PA_to_OD_Factors.npz"))

        # purpose_dict = {purpose: Auto_IVTT_Coefficients}
        purpose_dict = {"HWRK": -0.048225,
                        "HUNI": -0.061574,
                        "HSCH": -0.037156417,
                        "HSHP": -0.105966,
                        "HPBS": -0.054559,
                        "HSOC": -0.045506,
                        "HESC": -0.066630167,
                        "NWAU": -0.045283,
                        "NWTR": -0.045283,
                        "NWAC": -0.045283,
                        "NWTN": -0.045283,
                        "NOAU": -0.049362,
                        "NOTR": -0.049362,
                        "NOAC": -0.049362,
                        "NOTN": -0.049362}

        theta_dict = {"HWRK": 0.585846,
                      "HUNI": 0.459772,
                      "HSCH": 0.500000,
                      "HSHP": 0.303572,
                      "HPBS": 0.319341,
                      "HSOC": 0.554886,
                      "HESC": 0.500000,
                      "NWAU": 0.542267,
                      "NWTR": 0.542267,
                      "NWAC": 0.542267,
                      "NWTN": 0.542267,
                      "NOAU": 0.639408,
                      "NOTR": 0.639408,
                      "NOAC": 0.639408,
                      "NOTN": 0.639408}

        income_label = {"1": "Low",
                        "2": "Medium",
                        "3": "High",
                        "9": "All"}
        auto_ownership_label = {"0": "No Car",
                                "1": "1 Car",
                                "2": "2 Cars",
                                "9": "All"}

        Scenario_Master_DF = pd.DataFrame()
        NoTAZ = len(util.get_matrix_numpy(eb, "zoneindex"))
        BenefitVector = np.zeros((1,NoTAZ))
        for demand_key in Base_Demand.keys():
            purpose = demand_key[3:7]
            Income = demand_key[-3]
            Auto_Ownership = demand_key[-1]

            #The mode choice model was estimated using A-logit,
            #which generates coefficients scaled by the nesting coefficient theta
            #To calculate user benefits,
            #the estimated IVTT travel time coefficients are multiplied by theta
            #to properly capture the correct magnitude of the IVTT coefficient.
            IVTT_Coeff = purpose_dict[purpose]*theta_dict[purpose]

            utility_key = self.get_utility_key(demand_key)

            #logsum benefits (ROH formula)
            #Benefit = 0.5 * (self.PA_to_OD(Altr_Demand[demand_key],PA_Factor_Dict[purpose]) + self.PA_to_OD(Base_Demand[demand_key],PA_Factor_Dict[purpose]))*(Base_Utility[utility_key] - Altr_Utility[utility_key]) / IVTT_Coeff
            Benefit = 0.5 * (Altr_Demand[demand_key] + Base_Demand[demand_key])*(Base_Utility[utility_key] - Altr_Utility[utility_key]) / IVTT_Coeff
            #logsum benefits (Formula A)
            #Benefit = (Base_Demand[demand_key])*(Base_Utility[utility_key] - Altr_Utility[utility_key]) / IVTT_Coeff

            BenefitByMode_dict = {"All":Benefit}
            ModeList = ["All"]
            if True: #split logsum by modes

                utility_key_auto    = "LSS" + utility_key[3:7] + "AU" + utility_key[7:]
                utility_key_transit = "LSS" + utility_key[3:7] + "TR" + utility_key[7:]
                utility_key_active  = "LSS" + utility_key[3:7] + "AC" + utility_key[7:]

                Auto_portion    = -(Altr_UtilitySplit[utility_key_auto]    - Base_UtilitySplit[utility_key_auto]    )
                Transit_portion = -(Altr_UtilitySplit[utility_key_transit] - Base_UtilitySplit[utility_key_transit] )
                Active_portion  = -(Altr_UtilitySplit[utility_key_active]  - Base_UtilitySplit[utility_key_active]  )
                Sum_portions = Auto_portion + Transit_portion + Active_portion

                Auto_Benefit    = np.where(Sum_portions!=0, Benefit * Auto_portion    / Sum_portions, 0)
                Transit_Benefit = np.where(Sum_portions!=0, Benefit * Transit_portion / Sum_portions, 0)
                Active_Benefit  = np.where(Sum_portions!=0, Benefit * Active_portion  / Sum_portions, 0)

                ModeList = ["Auto", "Transit", "Active"]
                BenefitByMode_dict = {"Auto":Auto_Benefit, "Transit":Transit_Benefit, "Active":Active_Benefit}

            for Mode in ModeList:
                BenefitVector += self.PA_to_OD(BenefitByMode_dict[Mode],PA_Factor_Dict[purpose]).sum(axis=1)

                df = pd.concat([util.get_pd_ij_df(eb),util.get_ijensem_df(eb, ensem, ensem)], axis=1)
                ensem_i = '{}_from'.format(ensem)
                ensem_j = '{}_to'.format(ensem)
                df[['i','j', ensem_i, ensem_j]] = df[['i','j', '{}_i'.format(ensem), '{}_j'.format(ensem)]].astype(int)
                df["Daily_Benefits(min)"] = self.PA_to_OD(BenefitByMode_dict[Mode],PA_Factor_Dict[purpose]).flatten()
                #df["Daily_Benefits(min)"] = BenefitByMode_dict[Mode].flatten()
                df = df.drop(['i','j'], axis = 1)
                df = df.groupby([ensem_i, ensem_j])
                df = df.sum().reset_index()
                df["Purpose"] = purpose
                df["Income"] = income_label[Income]
                df["Auto_Ownership"] = auto_ownership_label[Auto_Ownership]
                df["Mode"] = Mode

                Scenario_Master_DF = Scenario_Master_DF.append(df)

        year = self.get_scenario_info(eb, "horizon_year")
        alternative = self.get_scenario_info( eb, "alternative")
        Scenario_Master_DF["Year"] = year
        Scenario_Master_DF["Scenario"] = alternative

        BenefitVector = np.concatenate((util.get_matrix_numpy(eb, "zoneindex"),np.transpose(BenefitVector)),axis = 1)
        np.savetxt('EconomicAnalysis\%s_BenefitVector.csv'%alternative, BenefitVector, delimiter=',')

        return Scenario_Master_DF

    def PA_to_OD(self, pa_mat, pa_factors):
        pa_Factor_AM, pa_Factor_MD, pa_Factor_PM = pa_factors
        pa_fac = pa_Factor_AM + pa_Factor_MD + pa_Factor_PM
        ap_fac = 1 - pa_fac

        return pa_mat * pa_fac + pa_mat.transpose() * ap_fac

    def get_utility_key(self, demand_key):
        if demand_key[3:7] in ["HSCH", "HESC"]:
            utility_key = "LSM" + demand_key[3:8] + "9" + demand_key[9:]
        else:
            utility_key = "LSM" + demand_key[3:]

        return utility_key

    @_m.logbook_trace("Calculate ROH Benefits")
    def Calculate_ROH_Benefits(self, eb, BaseScenario_Folder, AlternativeScenario_Folder, ensem, expansion_factors):
        util = _m.Modeller().tool("translink.util")

        #load npz into dictionary
        Base_Demand= np.load("{}/{}".format(BaseScenario_Folder,"ROH_Demand.npz"))
        Base_Time  = np.load("{}/{}".format(BaseScenario_Folder,"ROH_Time.npz"))
        Base_Cost  = np.load("{}/{}".format(BaseScenario_Folder,"ROH_Cost.npz"))
        Altr_Demand= np.load("{}/{}".format(AlternativeScenario_Folder,"ROH_Demand.npz"))
        Altr_Time  = np.load("{}/{}".format(AlternativeScenario_Folder,"ROH_Time.npz"))
        Altr_Cost  = np.load("{}/{}".format(AlternativeScenario_Folder,"ROH_Cost.npz"))

        # mode_list = {mode_category: mode_group [mode, mode, mode]}
        mode_list = {"Auto": ["SOV1", "SOV2", "SOV3", "SOV4", "HOV1", "HOV2", "HOV3"],
                     "Transit": ["BUS", "RAL", "WCE"],
                     "Light_Truck": ["LGV"],
                     "Heavy_Truck": ["HGV"]}
        DailyToAnnual_factors = {"SOV":335,"HOV":335,"BUS":270,"RAL":270,"WCE":224,"LGV":313,"HGV":276}

        # voc_list = {mode_category: vehicle operating cost ($/min)}
        voc_list = {"Auto": np.asscalar(util.get_matrix_numpy(eb, "msautoOpCost")),
                    "Transit": 1,
                    "Light_Truck": np.asscalar(util.get_matrix_numpy(eb, "mslgvOpCost")),
                    "Heavy_Truck": np.asscalar(util.get_matrix_numpy(eb, "mshgvOpCost"))}

        NoTAZ = len(util.get_matrix_numpy(eb, "zoneindex"))

        Scenario_Master_DF = pd.DataFrame()
        for mode_category, mode_group in mode_list.iteritems():
            Time_Benefit_AM = np.zeros((NoTAZ,NoTAZ))
            Time_Benefit_MD = np.zeros((NoTAZ,NoTAZ))
            Time_Benefit_PM = np.zeros((NoTAZ,NoTAZ))
            Cost_Benefit_AM = np.zeros((NoTAZ,NoTAZ))
            Cost_Benefit_MD = np.zeros((NoTAZ,NoTAZ))
            Cost_Benefit_PM = np.zeros((NoTAZ,NoTAZ))
            Daily_Time_Benefit = np.zeros((NoTAZ,NoTAZ))
            Daily_Cost_Benefit = np.zeros((NoTAZ,NoTAZ))

            if mode_category=="Transit":
                Sum_TransitTrip_Base_AM = np.zeros((NoTAZ,NoTAZ))
                Sum_TransitTime_Base_AM = np.zeros((NoTAZ,NoTAZ))
                Sum_TransitCost_Base_AM = np.zeros((NoTAZ,NoTAZ))
                Sum_TransitTrip_Altr_AM = np.zeros((NoTAZ,NoTAZ))
                Sum_TransitTime_Altr_AM = np.zeros((NoTAZ,NoTAZ))
                Sum_TransitCost_Altr_AM = np.zeros((NoTAZ,NoTAZ))

                Sum_TransitTrip_Base_PM = np.zeros((NoTAZ,NoTAZ))
                Sum_TransitTime_Base_PM = np.zeros((NoTAZ,NoTAZ))
                Sum_TransitCost_Base_PM = np.zeros((NoTAZ,NoTAZ))
                Sum_TransitTrip_Altr_PM = np.zeros((NoTAZ,NoTAZ))
                Sum_TransitTime_Altr_PM = np.zeros((NoTAZ,NoTAZ))
                Sum_TransitCost_Altr_PM = np.zeros((NoTAZ,NoTAZ))

                Sum_TransitTrip_Base_MD = np.zeros((NoTAZ,NoTAZ))
                Sum_TransitTime_Base_MD = np.zeros((NoTAZ,NoTAZ))
                Sum_TransitCost_Base_MD = np.zeros((NoTAZ,NoTAZ))
                Sum_TransitTrip_Altr_MD = np.zeros((NoTAZ,NoTAZ))
                Sum_TransitTime_Altr_MD = np.zeros((NoTAZ,NoTAZ))
                Sum_TransitCost_Altr_MD = np.zeros((NoTAZ,NoTAZ))

                #initialize large value for minimum matrices
                Min_TransitTime_Base_AM = np.zeros((NoTAZ,NoTAZ)) + 99999
                Min_TransitCost_Base_AM = np.zeros((NoTAZ,NoTAZ)) + 99999
                Min_TransitTime_Altr_AM = np.zeros((NoTAZ,NoTAZ)) + 99999
                Min_TransitCost_Altr_AM = np.zeros((NoTAZ,NoTAZ)) + 99999
                Min_TransitTime_Base_MD = np.zeros((NoTAZ,NoTAZ)) + 99999
                Min_TransitCost_Base_MD = np.zeros((NoTAZ,NoTAZ)) + 99999
                Min_TransitTime_Altr_MD = np.zeros((NoTAZ,NoTAZ)) + 99999
                Min_TransitCost_Altr_MD = np.zeros((NoTAZ,NoTAZ)) + 99999
                Min_TransitTime_Base_PM = np.zeros((NoTAZ,NoTAZ)) + 99999
                Min_TransitCost_Base_PM = np.zeros((NoTAZ,NoTAZ)) + 99999
                Min_TransitTime_Altr_PM = np.zeros((NoTAZ,NoTAZ)) + 99999
                Min_TransitCost_Altr_PM = np.zeros((NoTAZ,NoTAZ)) + 99999

                TransitTrip_Base_AM = np.zeros((NoTAZ,NoTAZ))
                TransitTrip_Altr_AM = np.zeros((NoTAZ,NoTAZ))
                TransitTrip_Base_MD = np.zeros((NoTAZ,NoTAZ))
                TransitTrip_Altr_MD = np.zeros((NoTAZ,NoTAZ))
                TransitTrip_Base_PM = np.zeros((NoTAZ,NoTAZ))
                TransitTrip_Altr_PM = np.zeros((NoTAZ,NoTAZ))

                for mode in mode_group:
                    AM_Fac, MD_Fac, PM_Fac = expansion_factors[mode[:3]]
                    DailyToAnnual = DailyToAnnual_factors[mode[:3]]
                    AM_AnnualFac = AM_Fac * DailyToAnnual
                    MD_AnnualFac = MD_Fac * DailyToAnnual
                    PM_AnnualFac = PM_Fac * DailyToAnnual

                    mode = mode + "9"
                    TransitTrip_Base_AM += Base_Demand["AMT"+mode] * AM_Fac
                    TransitTrip_Altr_AM += Altr_Demand["AMT"+mode] * AM_Fac
                    TransitTrip_Base_PM += Base_Demand["PMT"+mode] * PM_Fac
                    TransitTrip_Altr_PM += Altr_Demand["PMT"+mode] * PM_Fac

                    Sum_TransitTrip_Base_AM += Base_Demand["AMT"+mode] * AM_AnnualFac
                    Sum_TransitTime_Base_AM += Base_Demand["AMT"+mode] * Base_Time["AMM"+mode] * AM_AnnualFac
                    Sum_TransitCost_Base_AM += Base_Demand["AMT"+mode] * Base_Cost["AMC"+mode] * AM_AnnualFac
                    Min_TransitTime_Base_AM = np.minimum(Min_TransitTime_Base_AM, Base_Time["AMM"+mode])
                    Min_TransitCost_Base_AM = np.minimum(Min_TransitCost_Base_AM, Base_Cost["AMC"+mode])
                    Sum_TransitTrip_Altr_AM += Altr_Demand["AMT"+mode] * AM_AnnualFac
                    Sum_TransitTime_Altr_AM += Altr_Demand["AMT"+mode] * Altr_Time["AMM"+mode] * AM_AnnualFac
                    Sum_TransitCost_Altr_AM += Altr_Demand["AMT"+mode] * Altr_Cost["AMC"+mode] * AM_AnnualFac
                    Min_TransitTime_Altr_AM = np.minimum(Min_TransitTime_Altr_AM, Altr_Time["AMM"+mode])
                    Min_TransitCost_Altr_AM = np.minimum(Min_TransitCost_Altr_AM, Altr_Cost["AMC"+mode])

                    Sum_TransitTrip_Base_PM += Base_Demand["PMT"+mode] * PM_AnnualFac
                    Sum_TransitTime_Base_PM += Base_Demand["PMT"+mode] * Base_Time["PMM"+mode] * PM_AnnualFac
                    Sum_TransitCost_Base_PM += Base_Demand["PMT"+mode] * Base_Cost["PMC"+mode] * PM_AnnualFac
                    Min_TransitTime_Base_PM = np.minimum(Min_TransitTime_Base_PM, Base_Time["PMM"+mode])
                    Min_TransitCost_Base_PM = np.minimum(Min_TransitCost_Base_PM, Base_Cost["PMC"+mode])
                    Sum_TransitTrip_Altr_PM += Altr_Demand["PMT"+mode] * PM_AnnualFac
                    Sum_TransitTime_Altr_PM += Altr_Demand["PMT"+mode] * Altr_Time["PMM"+mode] * PM_AnnualFac
                    Sum_TransitCost_Altr_PM += Altr_Demand["PMT"+mode] * Altr_Cost["PMC"+mode] * PM_AnnualFac
                    Min_TransitTime_Altr_PM = np.minimum(Min_TransitTime_Altr_PM, Altr_Time["PMM"+mode])
                    Min_TransitCost_Altr_PM = np.minimum(Min_TransitCost_Altr_PM, Altr_Cost["PMC"+mode])

                    if mode=="WCE9":
                        continue # to next mode in mode_group, do not add mid-day benefit

                    TransitTrip_Base_MD += Base_Demand["MDT"+mode] * MD_Fac
                    TransitTrip_Altr_MD += Altr_Demand["MDT"+mode] * MD_Fac

                    Sum_TransitTrip_Base_MD += Base_Demand["MDT"+mode] * MD_AnnualFac
                    Sum_TransitTime_Base_MD += Base_Demand["MDT"+mode] * Base_Time["MDM"+mode] * MD_AnnualFac
                    Sum_TransitCost_Base_MD += Base_Demand["MDT"+mode] * Base_Cost["MDC"+mode] * MD_AnnualFac
                    Min_TransitTime_Base_MD = np.minimum(Min_TransitTime_Base_MD, Base_Time["MDM"+mode])
                    Min_TransitCost_Base_MD = np.minimum(Min_TransitCost_Base_MD, Base_Cost["MDC"+mode])
                    Sum_TransitTrip_Altr_MD += Altr_Demand["MDT"+mode] * MD_AnnualFac
                    Sum_TransitTime_Altr_MD += Altr_Demand["MDT"+mode] * Altr_Time["MDM"+mode] * MD_AnnualFac
                    Sum_TransitCost_Altr_MD += Altr_Demand["MDT"+mode] * Altr_Cost["MDC"+mode] * MD_AnnualFac
                    Min_TransitTime_Altr_MD = np.minimum(Min_TransitTime_Altr_MD, Altr_Time["MDM"+mode])
                    Min_TransitCost_Altr_MD = np.minimum(Min_TransitCost_Altr_MD, Altr_Cost["MDC"+mode])

                TransitTime_Base_AM = np.where(Sum_TransitTrip_Base_AM==0, Min_TransitTime_Base_AM, Sum_TransitTime_Base_AM/Sum_TransitTrip_Base_AM)
                TransitTime_Base_MD = np.where(Sum_TransitTrip_Base_MD==0, Min_TransitTime_Base_MD, Sum_TransitTime_Base_MD/Sum_TransitTrip_Base_MD)
                TransitTime_Base_PM = np.where(Sum_TransitTrip_Base_PM==0, Min_TransitTime_Base_PM, Sum_TransitTime_Base_PM/Sum_TransitTrip_Base_PM)
                TransitCost_Base_AM = np.where(Sum_TransitTrip_Base_AM==0, Min_TransitCost_Base_AM, Sum_TransitCost_Base_AM/Sum_TransitTrip_Base_AM)
                TransitCost_Base_MD = np.where(Sum_TransitTrip_Base_MD==0, Min_TransitCost_Base_MD, Sum_TransitCost_Base_MD/Sum_TransitTrip_Base_MD)
                TransitCost_Base_PM = np.where(Sum_TransitTrip_Base_PM==0, Min_TransitCost_Base_PM, Sum_TransitCost_Base_PM/Sum_TransitTrip_Base_PM)

                TransitTime_Altr_AM = np.where(Sum_TransitTrip_Altr_AM==0, Min_TransitTime_Altr_AM, Sum_TransitTime_Altr_AM/Sum_TransitTrip_Altr_AM)
                TransitTime_Altr_MD = np.where(Sum_TransitTrip_Altr_MD==0, Min_TransitTime_Altr_MD, Sum_TransitTime_Altr_MD/Sum_TransitTrip_Altr_MD)
                TransitTime_Altr_PM = np.where(Sum_TransitTrip_Altr_PM==0, Min_TransitTime_Altr_PM, Sum_TransitTime_Altr_PM/Sum_TransitTrip_Altr_PM)
                TransitCost_Altr_AM = np.where(Sum_TransitTrip_Altr_AM==0, Min_TransitCost_Altr_AM, Sum_TransitCost_Altr_AM/Sum_TransitTrip_Altr_AM)
                TransitCost_Altr_MD = np.where(Sum_TransitTrip_Altr_MD==0, Min_TransitCost_Altr_MD, Sum_TransitCost_Altr_MD/Sum_TransitTrip_Altr_MD)
                TransitCost_Altr_PM = np.where(Sum_TransitTrip_Altr_PM==0, Min_TransitCost_Altr_PM, Sum_TransitCost_Altr_PM/Sum_TransitTrip_Altr_PM)

                #ROH
                Time_Benefit_AM = 0.5 * (TransitTrip_Base_AM + TransitTrip_Altr_AM) * (TransitTime_Base_AM - TransitTime_Altr_AM)
                Time_Benefit_MD = 0.5 * (TransitTrip_Base_MD + TransitTrip_Altr_MD) * (TransitTime_Base_MD - TransitTime_Altr_MD)
                Time_Benefit_PM = 0.5 * (TransitTrip_Base_PM + TransitTrip_Altr_PM) * (TransitTime_Base_PM - TransitTime_Altr_PM)
                Cost_Benefit_AM = 0.5 * (TransitTrip_Base_AM + TransitTrip_Altr_AM) * (TransitCost_Base_AM - TransitCost_Altr_AM)
                Cost_Benefit_MD = 0.5 * (TransitTrip_Base_MD + TransitTrip_Altr_MD) * (TransitCost_Base_MD - TransitCost_Altr_MD)
                Cost_Benefit_PM = 0.5 * (TransitTrip_Base_PM + TransitTrip_Altr_PM) * (TransitCost_Base_PM - TransitCost_Altr_PM)

                Daily_Time_Benefit = Time_Benefit_AM + Time_Benefit_MD + Time_Benefit_PM
                Daily_Cost_Benefit = Cost_Benefit_AM + Cost_Benefit_MD + Cost_Benefit_PM

            else:
                for mode in mode_group:
                    if len(mode)==3:
                        mode = mode + "9"

                    if "HOV" in mode:
                        Occupancy = 2.25
                    else:
                        Occupancy = 1

                    AvgParking_Diff = np.transpose(0.5 * (Base_Cost["prk2hr"] + Base_Cost["prk8hr"] - Altr_Cost["prk2hr"] - Altr_Cost["prk8hr"]))

                    Time_Benefit_AM = 0.5 * (Altr_Demand["AMT"+mode] + Base_Demand["AMT"+mode]) * (Base_Time["AMM"+mode] - Altr_Time["AMM"+mode])
                    Time_Benefit_MD = 0.5 * (Altr_Demand["MDT"+mode] + Base_Demand["MDT"+mode]) * (Base_Time["MDM"+mode] - Altr_Time["MDM"+mode])
                    Time_Benefit_PM = 0.5 * (Altr_Demand["PMT"+mode] + Base_Demand["PMT"+mode]) * (Base_Time["PMM"+mode] - Altr_Time["PMM"+mode])
                    Cost_Benefit_AM = 0.5 * (Altr_Demand["AMT"+mode] + Base_Demand["AMT"+mode]) * (Base_Cost["AMC"+mode] - Altr_Cost["AMC"+mode] + AvgParking_Diff) /Occupancy
                    Cost_Benefit_MD = 0.5 * (Altr_Demand["MDT"+mode] + Base_Demand["MDT"+mode]) * (Base_Cost["MDC"+mode] - Altr_Cost["MDC"+mode] + AvgParking_Diff) /Occupancy
                    Cost_Benefit_PM = 0.5 * (Altr_Demand["PMT"+mode] + Base_Demand["PMT"+mode]) * (Base_Cost["PMC"+mode] - Altr_Cost["PMC"+mode] + AvgParking_Diff) /Occupancy

                    AM_Fac, MD_Fac, PM_Fac = expansion_factors[mode[:3]]
                    Daily_Time_Benefit += Time_Benefit_AM * AM_Fac + Time_Benefit_MD * MD_Fac + Time_Benefit_PM * PM_Fac
                    Daily_Cost_Benefit += Cost_Benefit_AM * AM_Fac + Cost_Benefit_MD * MD_Fac + Cost_Benefit_PM * PM_Fac

            # aggregate to ensemble
            for benefit_type in ["Time(min)","Cost($)"]:
                df = pd.concat([util.get_pd_ij_df(eb),util.get_ijensem_df(eb, ensem, ensem)], axis=1)
                ensem_i = '{}_from'.format(ensem)
                ensem_j = '{}_to'.format(ensem)
                df[['i','j', ensem_i, ensem_j]] = df[['i','j', '{}_i'.format(ensem), '{}_j'.format(ensem)]].astype(int)
                if benefit_type=="Time(min)":
                    df["Daily_Benefits"] = Daily_Time_Benefit.flatten()
                else:
                    df["Daily_Benefits"] = Daily_Cost_Benefit.flatten()
                df = df.drop(['i','j'], axis = 1)
                df = df.groupby([ensem_i, ensem_j])
                df = df.sum().reset_index()
                df["Benefit_Category"] = '{}_{}'.format(mode_category, benefit_type)
                Scenario_Master_DF = Scenario_Master_DF.append(df)

        Scenario_Master_DF["Year"] = self.get_scenario_info(eb, "horizon_year")
        Scenario_Master_DF["Scenario"] = self.get_scenario_info(eb, "alternative")
        return Scenario_Master_DF

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

        for mat_id in [60, 61]: #add parking
            mat_name = "mo{}".format(mat_id)
            mat_exists = eb.matrix(mat_name)
            if mat_exists:
                Cost_Dict[eb.matrix(mat_name).name] = util.get_matrix_numpy(eb, mat_name)

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

    @_m.logbook_trace("Export LogSum Demand Data")
    def Export_LogSum_Demand(self, eb):
        util = _m.Modeller().tool("translink.util")

        with_previous_export = os.path.isfile(os.path.join(util.get_eb_path(eb), 'EconomicAnalysis', 'LogSum_Demand.npz'))
        if with_previous_export:
            return # do not re-export

        # list mf matrix number to be exported
        matrix_list = []
        matrix_list += range(3050,3059) # PA Matrices - HbW
        matrix_list += [3150]           # PA Matrices - HbU
        matrix_list += range(3250,3259) # PA Matrices - HbSc
        matrix_list += range(3350,3359) # PA Matrices - HbSh
        matrix_list += range(3450,3459) # PA Matrices - HbPb
        matrix_list += range(3550,3559) # PA Matrices - HbSo
        matrix_list += range(3650,3659) # PA Matrices - HbEx
        matrix_list += range(3760,3764) # PA Matrices - NHbW
        matrix_list += range(3860,3864) # PA Matrices - NHbO

        Dict = {}
        for mat_id in matrix_list:
            mat_name = "mf{}".format(mat_id)
            mat_exists = eb.matrix(mat_name)
            name_key = self.rename_LogSum_Demand(eb, mat_id)
            Dict[name_key] = self.Get_Daily_OD(eb, mat_name)

        self.ExportData(eb, Dict, "LogSum_Demand.npz")

    def Get_Daily_OD(self, eb, mat_name):
        util = _m.Modeller().tool("translink.util")

        pa_mat = util.get_matrix_numpy(eb, mat_name)
        if True: #return PA demand
            return pa_mat

        matrix_name = eb.matrix(mat_name).name
        purpose = matrix_name.split("P-A")[0]
        purpose_List = ["HbW",  "HbU",  "HbSc", "HbSh", "HbPb", "HbSo", "HbEs", "NHbW", "NHbO"]
        purpose_index = purpose_List.index(purpose)

        pa_Factor_AM = np.asscalar(util.get_matrix_numpy(eb, "ms4{}0".format(purpose_index)))
        pa_Factor_MD = np.asscalar(util.get_matrix_numpy(eb, "ms4{}1".format(purpose_index)))
        pa_Factor_PM = np.asscalar(util.get_matrix_numpy(eb, "ms4{}2".format(purpose_index)))
        pa_fac = pa_Factor_AM + pa_Factor_MD + pa_Factor_PM
        ap_fac = 1 - pa_fac

        return pa_mat * pa_fac + pa_mat.transpose() * ap_fac

    def Export_PA_Factors(self, eb):
        util = _m.Modeller().tool("translink.util")

        Dict = {}

        purpose_List = [["HbW"],  ["HbU"],  ["HbSc"], ["HbSh"], ["HbPb"], ["HbSo"], ["HbEs"],
                        ["NHbWAut", "NHbWTrn", "NHbWAct", "NHbWTnc"], ["NHbOAut", "NHbOTrn", "NHbOAct", "NHbOTnc"]]
        for purpose in purpose_List:
            purpose_index = purpose_List.index(purpose)

            for purp in purpose:

                purp = self.rename_Purpose(purp)
                Dict[purp] = np.array([np.asscalar(util.get_matrix_numpy(eb, "ms4{}0".format(purpose_index))),
                                             np.asscalar(util.get_matrix_numpy(eb, "ms4{}1".format(purpose_index))),
                                             np.asscalar(util.get_matrix_numpy(eb, "ms4{}2".format(purpose_index)))])



        self.ExportData(eb, Dict, "PA_to_OD_Factors.npz")

    def rename_LogSum_Demand(self, eb, mf_number):
        matrix_name = eb.matrix("mf{}".format(mf_number)).name

        #get purpose
        purpose = matrix_name.split("P-A")[0]

        #rename NHb Purposes differently
        if purpose in ("NHbW", "NHbO"):
            purpose = purpose + matrix_name.split("P-A")[1]

        purpose = self.rename_Purpose(purpose)

        #get auto ownership
        if matrix_name[-2]=="A" and (matrix_name.split("P-A")[0] not in ("NHbW", "NHbO")):
            Auto_Ownership = matrix_name[-2:]
        else:
            Auto_Ownership = "A9"

        #get income
        if matrix_name[-4]=="I" and (matrix_name.split("P-A")[0] not in ("NHbW", "NHbO")):
            Income = matrix_name[-4:-2]
        else:
            Income = "I9"

        # DLT = Daily Trips
        export_name = "DLT" + purpose + Income + Auto_Ownership
        return export_name.upper()

    @_m.logbook_trace("Export LogSum Utility Data")
    def Export_LogSum_Utility(self, eb):
        util = _m.Modeller().tool("translink.util")

        with_previous_export = os.path.isfile(os.path.join(util.get_eb_path(eb), 'EconomicAnalysis', 'LogSum_Utility.npz'))
        with_previous_export = with_previous_export & os.path.isfile(os.path.join(util.get_eb_path(eb), 'EconomicAnalysis', 'Logsum_UtilitySplit.npz'))
        if with_previous_export:
            return # do not re-export

        blended_skims = _m.Modeller().tool("translink.RTM3.stage2.blendedskims")
        mode_choice = _m.Modeller().tool("translink.RTM3.stage2.modechoice")
        blended_skims(eb)
        mode_choice(eb)

        # list mf matrix number to be exported
        matrix_list = []
        matrix_list += range(9000,9100) # Logsum Matrices

        Dict = {}
        for mat_id in matrix_list:
            mat_name = "mf{}".format(mat_id)
            mat_exists = eb.matrix(mat_name)
            if mat_exists:
                name_key = self.rename_LogSum_Utility(eb, mat_id)
                Dict[name_key] = util.get_matrix_numpy(eb, mat_name)

        self.ExportData(eb, Dict, "LogSum_Utility.npz")

        # list mf matrix number to be exported
        matrix_list = []
        matrix_list += range(9300,9600) # Split auto/transit/active

        Dict = {}
        for mat_id in matrix_list:
            mat_name = "mf{}".format(mat_id)
            mat_exists = eb.matrix(mat_name)
            if mat_exists:
                name_key = self.rename_LogSum_UtilitySplit(eb, mat_id)
                Dict[name_key] = util.get_matrix_numpy(eb, mat_name)

        self.ExportData(eb, Dict, "LogSum_UtilitySplit.npz")

    def rename_LogSum_Utility(self, eb, mf_number):
        matrix_name = eb.matrix("mf{}".format(mf_number)).name

        #get purpose
        purpose = matrix_name.split("LS")[0]

        #rename NHb Purposes differently
        if purpose in ("NHbW", "NHbO"):
            purpose = purpose + matrix_name.split("LS")[1]

        purpose = self.rename_Purpose(purpose)

        #get auto ownership
        if matrix_name[-2]=="A" and (matrix_name.split("LS")[0] not in ("NHbW", "NHbO")):
            Auto_Ownership = matrix_name[-2:]
        else:
            Auto_Ownership = "A9"

        #get income
        if matrix_name[-4]=="I" and (matrix_name.split("LS")[0] not in ("NHbW", "NHbO")):
            Income = matrix_name[-4:-2]
        else:
            Income = "I9"

        # LSM = LogSum
        export_name = "LSM" + purpose + Income + Auto_Ownership
        return export_name.upper()

    def rename_LogSum_UtilitySplit(self, eb, mf_number):
        matrix_name = eb.matrix("mf{}".format(mf_number)).name

        #get purpose
        purpose = matrix_name.split("LS")[0]

        if purpose in ("NHbW", "NHbO"):
            purpose = purpose + matrix_name.split("LS")[1][2:]

        purpose = self.rename_Purpose(purpose)


        #get mode
        mode = matrix_name.split("LS")[1][:2]

        #get auto ownership
        if (matrix_name[-2]=="A") & (matrix_name.split("LS")[0]!="NHbO")& (matrix_name.split("LS")[0]!="HbU")& (matrix_name.split("LS")[0]!="NHbW"):
            Auto_Ownership = matrix_name[-2:]
        else:
            Auto_Ownership = "A9"

        #get income
        if matrix_name[-4]=="I":
            Income = matrix_name[-4:-2]
        else:
            Income = "I9"

        # LSS = LogSum Split (by Auto/Transit/Active)
        export_name = "LSS" + purpose + mode + Income + Auto_Ownership
        return export_name.upper()

    def rename_Purpose(self, key):
        ## rename Purpose
        Purpose_Old = ["NHbWAut", "NHbWTrn", "NHbWAct", "NHbWTnc", "HbW",  "HbU",  "HbSc",
                       "HbSh", "HbPb", "HbSo", "HbEs", "NHbOAut", "NHbOTrn", "NHbOAct", "NHbOTnc"]

        Purpose_New = ["NWAU", "NWTR", "NWAC", "NWTN", "HWRK", "HUNI", "HSCH",
                       "HSHP", "HPBS", "HSOC", "HESC", "NOAU" , "NOTR", "NOAC", "NOTN"]

        return_index = Purpose_Old.index(key)
        return Purpose_New[return_index]

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
