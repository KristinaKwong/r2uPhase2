##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage2.hbuniv
##--Purpose:
##---------------------------------------------------------------------
import inro.modeller as _m
import csv
import os
import numpy as np
import pandas as pd
import sqlite3

class HbWork(_m.Tool()):

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Home Base University"
        pb.description = "Calculate home base University person trips by mode and time of day"
        pb.branding_text = "TransLink"
        pb.runnable = False
        return pb.render()

    @_m.logbook_trace("Run Home Base University")
    def __call__(self, eb):
        util = _m.Modeller().tool("translink.util")
        MChM = _m.Modeller().tool("translink.RTM3.stage2.modechoiceutils")
        input_path = util.get_input_path(eb)
        self.matrix_batchins(eb)
        NoTAZ = len(util.get_matrix_numpy(eb, "mo51"))

#        ##############################################################################
#        ##       Define Availability thresholds
#        ##############################################################################

        AvailDict = {
                     'AutCost': 0.0,
                     'WlkDist': 5.0,
                     'BikDist': 20.0,
                     'TranIVT': 1.0,
                     'TranWat': 20.0,
                     'TranAux': 40.0,
                     'WCEWat' : 30.0,
                     'WCEAux' : 40.0,
                     'TranBrd': 4.0,
                     'BRTotLow': 10.0,
                     'BRTotHig': 120.0,
                     'WCTotLow': 30.0,
                     'WCTotHig': 130.0,
                     'PRAutTim': 0.0
                    }

        # Declare Utilities Data Frame
        DfU = {}
        # Add Coefficients

        p2   = -2.778773
        p4   =  4.232185
        p6   =  5.306844
        p10  =  5.459996
        p11  = -0.798531
        p12  = -0.620939
        p15  = -0.070561
        p17  = -0.148509
        p18  = -0.103273
        p19  = -0.824006
        p20  = -3.055662
        p21  = -1.189485
        thet =  0.296057

#        ##############################################################################
#        ##       Auto Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        MaxPark = 10.0


        ##
        Occ = util.get_matrix_numpy(eb, 'HOVOccHbu')
        Df['ParkCost'] = util.get_matrix_numpy(eb, 'prk8hr') # 8 hr parking
        Df['ParkCost'][Df['ParkCost']>MaxPark] = MaxPark
        Df['ParkCost'] = Df['ParkCost'].reshape(1, NoTAZ) + np.zeros((NoTAZ, 1))

        ##
        Df['AutoCosSOV'] = util.get_matrix_numpy(eb, 'HbUBlSovCost')
        Df['AutoTimSOV'] = util.get_matrix_numpy(eb, 'HbUBlSovTime')
        Df['AutoTotCosSOV'] = Df['AutoCosSOV'] + Df['ParkCost']

        Df['AutoCosHOV'] = util.get_matrix_numpy(eb, 'HbUBlHovCost')
        Df['AutoTimHOV'] = util.get_matrix_numpy(eb, 'HbUBlHovTime')
        Df['AutoTotCosHOV'] = Df['AutoCosHOV'] + Df['ParkCost']

        # Utilities
        # SOV
        # SOV Utility for all incomes
        Df['GeUtl'] = (0
                      + p15*Df['AutoTimSOV']
                      + p12*Df['AutoTotCosSOV'])
        # Check SOV Availability
        Df['GeUtl']  = MChM.AutoAvail(Df['AutoCosSOV'], Df['GeUtl'], AvailDict)

        DfU['SOV'] = Df['GeUtl']

        ##     HOV - 2 and more persons
        # HOV
        # HOV Utility for all incomes

        Df['GeUtl'] = ( p2
                      + p15*Df['AutoTimHOV']
                      + p12*Df['AutoTotCosHOV']/Occ)

        # Check HOV Availability
        Df['GeUtl'] = MChM.AutoAvail(Df['AutoCosHOV'], Df['GeUtl'], AvailDict)
        DfU['HOV']  = Df['GeUtl']

#        ##############################################################################
#        ##       Walk to Transit Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        Tiny=0.000001
        UPass_Disc = 0.1
        ##
        ##    Bus and rail related variables for University purpose
        ##
        Df['BusIVT'] = util.get_matrix_numpy(eb, 'HbUBlBusIvtt')
        Df['BusWat'] = util.get_matrix_numpy(eb, 'HbUBlBusWait')
        Df['BusAux'] = util.get_matrix_numpy(eb, 'HbUBlBusAux')
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'HbUBlBusBoard')
        Df['BusFar'] = util.get_matrix_numpy(eb, 'HbUBlBusFare')
        Df['BusTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux'] + Df['BusBrd'] # Bus Total Travel Time

        Df['RalIVR'] = util.get_matrix_numpy(eb, 'HbUBlRailIvtt')
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'HbUBlRailIvttBus')
        Df['RalWat'] = util.get_matrix_numpy(eb, 'HbUBlRailWait')
        Df['RalAux'] = util.get_matrix_numpy(eb, 'HbUBlRailAux')
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'HbUBlRailBoard')
        Df['RalFar'] = util.get_matrix_numpy(eb, 'HbUBlRailFare')

        Df['RalTot'] = Df['RalIVB'] + Df['RalIVR'] + Df['RalWat'] + Df['RalAux'] + Df['RalBrd'] # Bus Total Travel Time
        Df['RalIBR'] = Df['RalIVB']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Bus IVT to Total Time
        Df['RalIRR'] = Df['RalIVR']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Rail IVT to Total Time

        Df['IntZnl'] = np.identity(NoTAZ)

        # Utilities
        # Bus Utility
        # Bus Utility for all incomes
        Df['GeUtl'] = ( p4
                      + p12*(Df['BusFar'])*UPass_Disc
                      + p15*Df['BusIVT']
                      + p17*Df['BusWat']
                      + p18*Df['BusAux']
                      + p19*Df['BusBrd'])
        # Check Bus Availability
        Df['GeUtl'] = MChM.BusAvail(Df, Df['GeUtl'], AvailDict)
        DfU['Bus'] = Df['GeUtl']

        #     Rail Utility
        ##
        Df['GeUtl'] = ( p4*Df['RalIBR']
                      + p6*Df['RalIRR']
                      + p12*(Df['RalFar'])*UPass_Disc
                      + p15*Df['RalIVB']
                      + p15*Df['RalIVR']
                      + p17*Df['RalWat']
                      + p18*Df['RalAux']
                      + p19*Df['RalBrd'])

        # Check Rail Availability
        Df['GeUtl'] = MChM.RailAvail(Df, Df['GeUtl'],AvailDict)
        DfU['Ral'] = Df['GeUtl']

#        ##############################################################################
#        ##
#        ##        Active Modes
#        ##        rs: HbU SOV distance is used.
#        ##
#        ##############################################################################

        Df = {}
        Df['AutoDis'] = util.get_matrix_numpy(eb, "mfdistAON") # Distance

        # Walk Utility
        DfU['Walk'] = ( p10
                      + p20*Df['AutoDis'])

        # Check Walk Availability
        DfU['Walk'] = MChM.WalkAvail(Df['AutoDis'], DfU['Walk'], AvailDict)

        # Bike Utility
        DfU['Bike'] = ( p11
                      + p21*Df['AutoDis'])

        # Check Bike Availability
        DfU['Bike'] = MChM.BikeAvail(Df['AutoDis'], DfU['Bike'], AvailDict)

        del Df

#        ##############################################################################
#        ##       Calculate Probabilities
#        ##############################################################################
        ## Add SOV Availability Term


        LrgU     = -99999.0
        ## Low Income Zero Autos
        Dict = {
               'SOV'  : [DfU['SOV']],
               'HOV'  : [DfU['HOV']],
               'WTra' : [DfU['Bus'], DfU['Ral']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }

        Prob_Dict = self.Calc_Prob(eb, Dict, "HbULS", thet)
        del DfU, Dict

       ##############################################################################
        ##       Trip Distribution
       ##############################################################################

        Logsum =  ["HbULS"]

        imp_list = ["P-AFrictionFact1"]

        mo_list =  ["hbuprd"]

        md_list =  ["hbuatr"]

        out_list = ["HbUP-A"]

        LS_Coeff = 0.4

        LambdaList = [-0.107653]

        AlphaList =  [0.001014]

        GammaList =  [-0.000005]

        Kij = util.get_matrix_numpy(eb, "Kij_hbu")

        Bridge_Factor = 0

        MChM.ImpCalc(eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, util.get_matrix_numpy(eb, "mfdistAON"), Kij, "Zero", Bridge_Factor)
        MChM.two_dim_matrix_balancing(eb, mo_list, md_list, imp_list, out_list)


#       ##############################################################################
#        ##       Calculate Demand
#       ##############################################################################

        Demand_Dict = self.Calc_Demand(Prob_Dict, util.get_matrix_numpy(eb,"HbUP-A"))


        SOV =   Demand_Dict['SOV'][0]

        HOV =   Demand_Dict['HOV'][0]

        Bus  =  Demand_Dict['WTra'][0]

        Rail =  Demand_Dict['WTra'][1]

        Walk =  Demand_Dict['Acti'][0]

        Bike =  Demand_Dict['Acti'][1]


        del Demand_Dict
        del Prob_Dict

#       ##############################################################################
#        ##       Get Time Slice Factors
#       ##############################################################################
        min_val=0.000143
        purp='hbu'

        # setup for hbw auto time slice matrices
        conn = util.get_rtm_db(eb)
        ij = util.get_pd_ij_df(eb)
        gb = pd.read_sql("SELECT TAZ1700 as TAZ, gb FROM ensembles", conn)
        ts_uw = pd.read_sql("SELECT * FROM timeSlicingFactorsGb", conn)
        conn.close()

        # build basic ij mat with gb for production end and internal or external gb for attraction
        df_mats = pd.merge(ij, gb, how='left', left_on='i', right_on = 'TAZ')
        df_mats.drop('TAZ', axis=1, inplace=True)
        df_mats.rename(columns={'gb': 'Gb_P'}, inplace=True)
        df_mats = pd.merge(df_mats, gb, how='left', left_on='j', right_on = 'TAZ')
        df_mats.drop('TAZ', axis=1, inplace=True)
        df_mats.rename(columns={'gb': 'Gb_A'}, inplace=True)
        df_mats['IX'] = np.where(df_mats['Gb_P']==df_mats['Gb_A'], 'I', 'X')

        # Auto factors return a  multi-dimensional array, the other modes return a scalar
        Auto_AM_Fct_PA = MChM.ts_mat(df_mats, ts_uw, min_val, purp, 'AM', 'PtoA', NoTAZ)
        Auto_MD_Fct_PA = MChM.ts_mat(df_mats, ts_uw, min_val, purp, 'MD', 'PtoA', NoTAZ)
        Auto_PM_Fct_PA = MChM.ts_mat(df_mats, ts_uw, min_val, purp, 'PM', 'PtoA', NoTAZ)

        Auto_AM_Fct_AP = MChM.ts_mat(df_mats, ts_uw, min_val, purp, 'AM', 'AtoP', NoTAZ)
        Auto_MD_Fct_AP = MChM.ts_mat(df_mats, ts_uw, min_val, purp, 'MD', 'AtoP', NoTAZ)
        Auto_PM_Fct_AP = MChM.ts_mat(df_mats, ts_uw, min_val, purp, 'PM', 'AtoP', NoTAZ)

        Tran_AM_Fct_PA, Tran_AM_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Transit',peakperiod='AM', geo='A',minimum_value=min_val)
        Tran_AM_Fct_PA, Tran_AM_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Transit',peakperiod='AM', geo='A',minimum_value=min_val)
        Tran_MD_Fct_PA, Tran_MD_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Transit',peakperiod='MD', geo='A',minimum_value=min_val)
        Tran_MD_Fct_PA, Tran_MD_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Transit',peakperiod='MD', geo='A',minimum_value=min_val)
        Tran_PM_Fct_PA, Tran_PM_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Transit',peakperiod='PM', geo='A',minimum_value=min_val)
        Tran_PM_Fct_PA, Tran_PM_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Transit',peakperiod='PM', geo='A',minimum_value=min_val)

        Acti_AM_Fct_PA, Acti_AM_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Active',peakperiod='AM', geo='A',minimum_value=min_val)
        Acti_AM_Fct_PA, Acti_AM_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Active',peakperiod='AM', geo='A',minimum_value=min_val)
        Acti_MD_Fct_PA, Acti_MD_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Active',peakperiod='MD', geo='A',minimum_value=min_val)
        Acti_MD_Fct_PA, Acti_MD_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Active',peakperiod='MD', geo='A',minimum_value=min_val)
        Acti_PM_Fct_PA, Acti_PM_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Active',peakperiod='PM', geo='A',minimum_value=min_val)
        Acti_PM_Fct_PA, Acti_PM_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Active',peakperiod='PM', geo='A',minimum_value=min_val)


      ##########################################################################################
       ##       Calculate peak hour O-D person trips and final 24 hour P-A Trips
      ##########################################################################################
      ## SOV Trips      #SOV*PA_Factor + SOV_transpose*AP_Factor
        SOV_AM = SOV*Auto_AM_Fct_PA + SOV.transpose()*Auto_AM_Fct_AP
        SOV_MD = SOV*Auto_MD_Fct_PA + SOV.transpose()*Auto_MD_Fct_AP
        SOV_PM = SOV*Auto_PM_Fct_PA + SOV.transpose()*Auto_PM_Fct_AP

        ## HOV Trips
        HOV_AM = HOV*Auto_AM_Fct_PA + HOV.transpose()*Auto_AM_Fct_AP
        HOV_MD = HOV*Auto_MD_Fct_PA + HOV.transpose()*Auto_MD_Fct_AP
        HOV_PM = HOV*Auto_PM_Fct_PA + HOV.transpose()*Auto_PM_Fct_AP

        ## Transit Trips
        Bus_AM = Bus*Tran_AM_Fct_PA + Bus.transpose()*Tran_AM_Fct_AP
        Bus_MD = Bus*Tran_MD_Fct_PA + Bus.transpose()*Tran_MD_Fct_AP
        Bus_PM = Bus*Tran_PM_Fct_PA + Bus.transpose()*Tran_PM_Fct_AP

        Rail_AM = Rail*Tran_AM_Fct_PA + Rail.transpose()*Tran_AM_Fct_AP
        Rail_MD = Rail*Tran_MD_Fct_PA + Rail.transpose()*Tran_MD_Fct_AP
        Rail_PM = Rail*Tran_PM_Fct_PA + Rail.transpose()*Tran_PM_Fct_AP

        ## Active Trips
        Walk_AM = Walk*Acti_AM_Fct_PA + Walk.transpose()*Acti_AM_Fct_AP
        Walk_MD = Walk*Acti_MD_Fct_PA + Walk.transpose()*Acti_MD_Fct_AP
        Walk_PM = Walk*Acti_PM_Fct_PA + Walk.transpose()*Acti_PM_Fct_AP

        Bike_AM = Bike*Acti_AM_Fct_PA + Bike.transpose()*Acti_AM_Fct_AP
        Bike_MD = Bike*Acti_MD_Fct_PA + Bike.transpose()*Acti_MD_Fct_AP
        Bike_PM = Bike*Acti_PM_Fct_PA + Bike.transpose()*Acti_PM_Fct_AP


        # Convert HOV to Auto Drivers
        # HOV2
        AuDr_HOV_AM = HOV_AM/Occ
        AuDr_HOV_MD = HOV_MD/Occ
        AuDr_HOV_PM = HOV_PM/Occ


#       ##############################################################################
#        ##       Set Demand Matrices
#       ##############################################################################
        # 24 hour trips

        util.set_matrix_numpy(eb, "HbUSOVPerTrips", SOV)
        util.set_matrix_numpy(eb, "HbUHOVPerTrips", HOV)
        util.set_matrix_numpy(eb, "HbUBusPerTrips", Bus)
        util.set_matrix_numpy(eb, "HbURailPerTrips", Rail)
        util.set_matrix_numpy(eb, "HbUWalkPerTrips", Walk)
        util.set_matrix_numpy(eb, "HbUBikePerTrips", Bike)

       # Auto-person

       # SOV
        # AM
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_1_Am", SOV_AM)
        # MD
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_1_Md", SOV_MD)

        # PM
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_1_Pm", SOV_PM)


        # HOV
        # AM
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_1_Am", HOV_AM)

        # MD
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_1_Md", HOV_MD)

        # PM
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_1_Pm", HOV_PM)

        # Transit
        # AM
        util.add_matrix_numpy(eb, "busAm", Bus_AM)
        util.add_matrix_numpy(eb, "railAm", Rail_AM)

        # MD
        util.add_matrix_numpy(eb, "busMd", Bus_MD)
        util.add_matrix_numpy(eb, "railMd", Rail_MD)

        # PM
        util.add_matrix_numpy(eb, "busPm", Bus_PM)
        util.add_matrix_numpy(eb, "railPm", Rail_PM)


        # Active
        # AM
        util.add_matrix_numpy(eb, "Wk_pertrp_Am", Walk_AM)
        util.add_matrix_numpy(eb, "Bk_pertrp_Am", Bike_AM)

        # MD
        util.add_matrix_numpy(eb, "Wk_pertrp_Md", Walk_MD)
        util.add_matrix_numpy(eb, "Bk_pertrp_Md", Bike_MD)

        # PM
        util.add_matrix_numpy(eb, "Wk_pertrp_Pm", Walk_PM)
        util.add_matrix_numpy(eb, "Bk_pertrp_Pm", Bike_PM)

        # Auto-driver

        # SOV
        # AM
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_1_Am", SOV_AM)

        # MD
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_1_Md", SOV_MD)

        # PM
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_1_Pm", SOV_PM)

        # HOV
        # AM
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_1_Am", AuDr_HOV_AM)

        # MD
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_1_Md", AuDr_HOV_MD)

        # PM
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_1_Pm", AuDr_HOV_PM)

        ## Dump demands to SQL Database
        # AM
        Zone_Index_O = util.get_matrix_numpy(eb, "zoneindex") + np.zeros((1, NoTAZ))
        Zone_Index_D = Zone_Index_O.transpose()

        T_SOV_AM = np.where((Zone_Index_O>9999) & (Zone_Index_D>9999), SOV_AM, 0)
        T_HOV_AM = HOV_AM


        # MD
        T_SOV_MD = np.where((Zone_Index_O>9999) & (Zone_Index_D>9999), SOV_MD, 0)
        T_HOV_MD = HOV_MD

        # PM
        T_SOV_PM = np.where((Zone_Index_O>9999) & (Zone_Index_D>9999), SOV_PM, 0)
        T_HOV_PM = HOV_PM

        # Take park and ride out of auto trips




        #
        df_pkhr_demand = pd.DataFrame()

        Gy_P = util.get_matrix_numpy(eb, 'gy_ensem')  + np.zeros((1, NoTAZ))
        Gy_A = Gy_P.transpose()

        df_pkhr_demand['Gy_O'] = Gy_P.flatten()
        df_pkhr_demand['Gy_D'] = Gy_A.flatten()
        df_pkhr_demand.Gy_O = df_pkhr_demand.Gy_O.astype(int)
        df_pkhr_demand.Gy_D = df_pkhr_demand.Gy_D.astype(int)
        mode_list_am_pm = ['sov', 'hov', 'bus', 'rail', 'walk', 'bike']
        mode_list_md = ['sov', 'hov', 'bus', 'rail', 'walk', 'bike']

        AM_Demand_List = [T_SOV_AM, T_HOV_AM, Bus_AM, Rail_AM,  Walk_AM, Bike_AM]
        MD_Demand_List = [T_SOV_MD, T_HOV_MD, Bus_MD, Rail_MD, Walk_MD, Bike_MD]
        PM_Demand_List = [T_SOV_PM, T_HOV_PM, Bus_PM, Rail_PM,  Walk_PM, Bike_PM]


        purp = "hbu"

        df_AM_summary, df_AM_Gy = MChM.PHr_Demand(df_pkhr_demand, purp, "AM", AM_Demand_List, mode_list_am_pm)


        df_MD_summary, df_MD_Gy = MChM.PHr_Demand(df_pkhr_demand, purp, "MD", MD_Demand_List, mode_list_md)

        df_PM_summary, df_PM_Gy = MChM.PHr_Demand(df_pkhr_demand, purp, "PM", PM_Demand_List, mode_list_am_pm)

        df_summary = pd.concat([df_AM_summary, df_MD_summary, df_PM_summary])
        df_gy = pd.concat([df_AM_Gy, df_MD_Gy, df_PM_Gy])

        ## Dump to SQLite DB

        db_loc = util.get_eb_path(eb)
        db_path = os.path.join(db_loc, 'trip_summaries.db')
        conn = sqlite3.connect(db_path)

        df_summary.to_sql(name='phr_summary', con=conn, flavor='sqlite', index=False, if_exists='append')
        df_gy.to_sql(name='phr_gy', con=conn, flavor='sqlite', index=False, if_exists='append')
        conn.close()

    def Calc_Prob(self, eb, Dict, Logsum, Th):
        util = _m.Modeller().tool("translink.util")

        Tiny=0.000001
        L_Nst = {key:sum(np.exp(nest))
                      for key,nest in Dict.items()}

        U_Nst  = {key:pow(nest,Th)
                      for key,nest in L_Nst.items()}

        L_Nst = {key:np.where(value == 0, Tiny, value)
                      for key,value in L_Nst.items()}

        F_Utl = sum(U_Nst.values())
        F_Utl = np.where(F_Utl ==0, Tiny, F_Utl)
        util.set_matrix_numpy(eb, Logsum, np.log(F_Utl))

        Prob_Dict = {key:np.exp(nest)/L_Nst[key]*U_Nst[key]/F_Utl
                         for key, nest in Dict.items()}
        return Prob_Dict

    def Calc_Demand(self, Dict, Dem):
        util = _m.Modeller().tool("translink.util")

        Seg_Dict = {key:Dem*nest_len
                    for key, nest_len in Dict.items()}
        return Seg_Dict
    @_m.logbook_trace("PnR")
    def splitpnr (self, DfmergedAuto, DfmergedTran, DfInt):

        DfAuto = pd.DataFrame()
        DfAuto = pd.merge(DfInt, DfmergedAuto, left_on = ['i', 'j'],
                     right_on = ['i', 'BL'], how = 'left')
        DfAuto = DfAuto.fillna(0)

        DfTran = pd.merge(DfInt, DfmergedTran, left_on = ['i', 'j'],
                     right_on = ['BL', 'j'], how = 'left')
        DfTran = DfTran.fillna(0)

        return (DfAuto, DfTran)

    @_m.logbook_trace("Initialize Matrices")
    def matrix_batchins(self, eb):
        util = _m.Modeller().tool("translink.util")

        ## Initialze Logsum Matrices
        util.initmat(eb, "mf9010", "HbULS", " HbU LogSum ", 0)

        ## Initialze Friction Factor Matrices
        util.initmat(eb, "mf9100", "P-AFrictionFact1", "Trip Distribution Friction Factor 1", 0)

        ## Initialize P-A Trip Tables by mode
        util.initmat(eb, "mf3100", "HbUSOVPerTrips", "HbU SOV Per-Trips", 0)
        util.initmat(eb, "mf3105", "HbUHOVPerTrips", "HbU HOV Per-Trips", 0)
        util.initmat(eb, "mf3115", "HbUBusPerTrips", "HbU Bus Per-Trips", 0)
        util.initmat(eb, "mf3120", "HbURailPerTrips", "HbU Rail Per-Trips", 0)
        util.initmat(eb, "mf3130", "HbUWalkPerTrips", "HbU Walk Per-Trips", 0)
        util.initmat(eb, "mf3135", "HbUBikePerTrips", "HbU Bike Per-Trips", 0)

        ## Initialize P-A Trip Tables from trip distribution
        util.initmat(eb, "mf3150", "HbUP-A", " HbU P-A Trips ", 0)
