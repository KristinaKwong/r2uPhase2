##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage2.nhbwork
##--Purpose:
##---------------------------------------------------------------------
import inro.modeller as _m
import csv
import os
import numpy as np
import pandas as pd
import sqlite3

class Non_hbwork(_m.Tool()):

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Non-home Base work"
        pb.description = "Calculate non-home base work trips by mode and time of day"
        pb.branding_text = "TransLink"
        pb.runnable = False
        return pb.render()

    @_m.logbook_trace("Run Non-home base work")
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
                     'TranAux': 30.0,
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
        p2   = -2.224486
        p4   = -1.740781
        p6   = -0.315615
        p10  = -4.927195
        p11  = -8.893019
        p12  = -0.133546
        p15  = -0.048709
        p17  = -0.110062
        p18  = -0.091187
        p19  = -0.400061
        p20  = -1.735333
        p21  = -0.399194
        p700 =  0.188804
        p701 =  1.076643
        p702 =  0.514682
        p870 =  0.800286
        thet =  0.695843

#        ##############################################################################
#        ##       Auto Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        MaxPark = 10.0

        Occ = util.get_matrix_numpy(eb, 'HOVOccNHBw')
        Df['ParkCost'] = 0.5*(util.get_matrix_numpy(eb, 'prk8hr') +  util.get_matrix_numpy(eb, 'prk2hr'))# average parking of 2hrs and 8hrs parking
        Df['ParkCost'][Df['ParkCost']>MaxPark] = MaxPark
        Df['ParkCost'] = Df['ParkCost'].reshape(1, NoTAZ) + np.zeros((NoTAZ, 1))

        Df['AutoCosSOV'] = util.get_matrix_numpy(eb, 'NHbWBlSovCost')
        Df['AutoTimSOV'] = util.get_matrix_numpy(eb, 'NHbWBlSovTime')
        Df['AutoTotCosSOV'] = Df['AutoCosSOV'] + Df['ParkCost']

        Df['AutoCosHOV'] = util.get_matrix_numpy(eb, 'NHbWBlHovCost')
        Df['AutoTimHOV'] = util.get_matrix_numpy(eb, 'NHbWBlHovTime')
        Df['AutoTotCosHOV'] = Df['AutoCosHOV'] + Df['ParkCost']

        # Utilities
        # SOV
        # SOV Utility across all incomes
        Df['GeUtl'] = ( 0
                      + p12*Df['AutoTotCosSOV']
                      + p15*Df['AutoTimSOV'])

        # Check Availability conditions
        Df['GeUtl']  = MChM.AutoAvail(Df['AutoCosSOV'], Df['GeUtl'], AvailDict)
        DfU['SOV'] = Df['GeUtl']

        # HOV2+
        # HOV2+ Utility across all incomes
        Df['GeUtl'] = ( p2
                      + p12*Df['AutoTotCosHOV']/Occ
                      + p15*Df['AutoTimHOV'])
        # Check Availability conditions
        Df['GeUtl']  = MChM.AutoAvail(Df['AutoCosHOV'], Df['GeUtl'], AvailDict)
        # Add Income parameters
        DfU['HOV'] = Df['GeUtl']

#        ##############################################################################
#        ##       Walk to Transit Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        Tiny=0.000001
        Df['BusIVT'] = util.get_matrix_numpy(eb, 'NHbWBlBusIvtt')
        Df['BusWat'] = util.get_matrix_numpy(eb, 'NHbWBlBusWait')
        Df['BusAux'] = util.get_matrix_numpy(eb, 'NHbWBlBusAux')
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'NHbWBlBusBoard')
        Df['BusFar'] = util.get_matrix_numpy(eb, 'NHbWBlBusFare')
        Df['BusTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux'] + Df['BusBrd'] # Total Bus Travel Time

        Df['RalIVR'] = util.get_matrix_numpy(eb, 'NHbWBlRailIvtt')
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'NHbWBlRailIvttBus')
        Df['RalWat'] = util.get_matrix_numpy(eb, 'NHbWBlRailWait')
        Df['RalAux'] = util.get_matrix_numpy(eb, 'NHbWBlRailAux')
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'NHbWBlRailBoard')
        Df['RalFar'] = util.get_matrix_numpy(eb, 'NHbWBlRailFare')
        Df['RalTot'] = Df['RalIVB'] + Df['RalIVR'] + Df['RalWat'] + Df['RalAux'] + Df['RalBrd'] # Total Bus Travel Time
        Df['RalIBR'] = Df['RalIVB']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Bus IVT to Total Time
        Df['RalIRR'] = Df['RalIVR']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Rail IVT to Total Time

        Df['IntZnl'] = np.identity(NoTAZ)
        Df['PopEmpDen'] = util.get_matrix_numpy(eb, 'combinedensln')
        Df['PopEmpDen'] = Df['PopEmpDen'].reshape(NoTAZ, 1) + np.zeros((1, NoTAZ))

        # Utilities
        # Bus Utility
        # Bus Utility across all incomes
        Df['GeUtl'] = ( p4
                      + p12*Df['BusFar']
                      + p15*Df['BusIVT']
                      + p17*Df['BusWat']
                      + p18*Df['BusAux']
                      + p19*Df['BusBrd']
                      + p700*Df['PopEmpDen'])

        # Check Availability conditions
        Df['GeUtl'] = MChM.BusAvail(Df, Df['GeUtl'], AvailDict)
        DfU['Bus'] = Df['GeUtl']

        # Rail Utility
        # Rail Utility across all incomes
        Df['GeUtl'] = ( p4*Df['RalIBR']
                      + p6*Df['RalIRR']
                      + p12*Df['RalFar']
                      + p15*Df['RalIVB']
                      + p15*Df['RalIVR']
                      + p17*Df['RalWat']
                      + p18*Df['RalAux']
                      + p19*Df['RalBrd']
                      + p700*Df['PopEmpDen'])
        # Check Availability conditions
        Df['GeUtl'] = MChM.RailAvail(Df, Df['GeUtl'],AvailDict)
        DfU['Ral'] = Df['GeUtl']

#        ##############################################################################
#        ##       Active Modes
#        ##############################################################################

        Df = {}
        Df['AutoDis'] = util.get_matrix_numpy(eb, "mfdistAON") # Distance
        Df['PopEmpDen'] = util.get_matrix_numpy(eb, 'combinedensln')
        Df['PopEmpDen'] = Df['PopEmpDen'].reshape(NoTAZ, 1) + np.zeros((1, NoTAZ))

        Df['PopEmpDenPA'] = util.get_matrix_numpy(eb, 'combinedensln')#Pop+Emp Density at Prod and Attr Zones
        Df['PopEmpDenPA'] = Df['PopEmpDenPA'].reshape(NoTAZ, 1) + Df['PopEmpDenPA'].reshape(1, NoTAZ) #Broadcast Density

        Df['BikScr'] = util.get_matrix_numpy(eb, 'bikeskim') # Bike Score


        # Walk Utility
        DfU['Walk'] = ( p10
                      + p20*Df['AutoDis']
                      + p701*Df['PopEmpDenPA'])
        # Check Availability conditions
        DfU['Walk'] = MChM.WalkAvail(Df['AutoDis'], DfU['Walk'], AvailDict)

        # Bike Utility
        DfU['Bike'] = ( p11
                      + p21*Df['AutoDis']
                      + p702*Df['PopEmpDen']
                      + p870*Df['BikScr'])
        # Check Availability conditions
        DfU['Bike'] = MChM.BikeAvail(Df['AutoDis'], DfU['Bike'], AvailDict)

        del Df

#        ##############################################################################
#        ##       Calculate Probabilities
#        ##############################################################################

        # All Incomes All Autos
        Dict = {
               'SOV'  : [DfU['SOV']],
               'HOV'  : [DfU['HOV']],
               'WTra' : [DfU['Bus'], DfU['Ral']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }

        Prob_Dict = self.Calc_Prob(eb, Dict, "NHbWLS", thet)
        del DfU, Dict
#
       ##############################################################################
        ##       Trip Distribution
       ##############################################################################

        Logsum =  ["NHbWLS"]

        imp_list = ["P-AFrictionFact1"]

        mo_list =  ["nhbwprd"]

        md_list =  ["nhbwatr"]

        out_list = ["NHbWP-A"]

        LS_Coeff = 0.8

        LambdaList = [-0.071422]



        AlphaList =  [0.000501]



        GammaList =  [-0.000003]

        Kij = util.get_matrix_numpy(eb, "Kij_nhbw")

        Bridge_Factor = 0

        MChM.ImpCalc(eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, util.get_matrix_numpy(eb, "mfdistAON"), Kij, "Zero", Bridge_Factor)
        MChM.two_dim_matrix_balancing(eb, mo_list, md_list, imp_list, out_list)


#       ##############################################################################
#        ##       Calculate Demand
#       ##############################################################################

        Demand_Dict = self.Calc_Demand(Prob_Dict, util.get_matrix_numpy(eb,"NHbWP-A"))


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
        purp='nhbw'

        Auto_AM_Fct_PA, Auto_AM_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Auto',peakperiod='AM', geo='A',minimum_value=min_val)
        Auto_AM_Fct_PA, Auto_AM_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Auto',peakperiod='AM', geo='A',minimum_value=min_val)
        Auto_MD_Fct_PA, Auto_MD_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Auto',peakperiod='MD', geo='A',minimum_value=min_val)
        Auto_MD_Fct_PA, Auto_MD_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Auto',peakperiod='MD', geo='A',minimum_value=min_val)
        Auto_PM_Fct_PA, Auto_PM_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Auto',peakperiod='PM', geo='A',minimum_value=min_val)
        Auto_PM_Fct_PA, Auto_PM_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Auto',peakperiod='PM', geo='A',minimum_value=min_val)

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
        SOV_AM = SOV*Auto_AM_Fct_PA
        SOV_MD = SOV*Auto_MD_Fct_PA
        SOV_PM = SOV*Auto_PM_Fct_PA

        ## HOV Trips
        HOV_AM = HOV*Auto_AM_Fct_PA
        HOV_MD = HOV*Auto_MD_Fct_PA
        HOV_PM = HOV*Auto_PM_Fct_PA

        ## Transit Trips
        Bus_AM = Bus*Tran_AM_Fct_PA
        Bus_MD = Bus*Tran_MD_Fct_PA
        Bus_PM = Bus*Tran_PM_Fct_PA

        Rail_AM = Rail*Tran_AM_Fct_PA
        Rail_MD = Rail*Tran_MD_Fct_PA
        Rail_PM = Rail*Tran_PM_Fct_PA

        ## Active Trips
        Walk_AM = Walk*Acti_AM_Fct_PA
        Walk_MD = Walk*Acti_MD_Fct_PA
        Walk_PM = Walk*Acti_PM_Fct_PA

        Bike_AM = Bike*Acti_AM_Fct_PA
        Bike_MD = Bike*Acti_MD_Fct_PA
        Bike_PM = Bike*Acti_PM_Fct_PA


        # Convert HOV to Auto Drivers
        # HOV2
        AuDr_HOV_AM = HOV_AM/Occ
        AuDr_HOV_MD = HOV_MD/Occ
        AuDr_HOV_PM = HOV_PM/Occ


#       ##############################################################################
#        ##       Set Demand Matrices
#       ##############################################################################
        # 24 hour trips

        util.set_matrix_numpy(eb, "NHbWSOVPerTrips", SOV)
        util.set_matrix_numpy(eb, "NHbWHOVPerTrips", HOV)
        util.set_matrix_numpy(eb, "NHbWBusPerTrips", Bus)
        util.set_matrix_numpy(eb, "NHbWRailPerTrips", Rail)
        util.set_matrix_numpy(eb, "NHbWWalkPerTrips", Walk)
        util.set_matrix_numpy(eb, "NHbWBikePerTrips", Bike)

       # Auto-person

       # SOV
        # AM
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_4_Am", SOV_AM)
        # MD
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_4_Md", SOV_MD)

        # PM
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_4_Pm", SOV_PM)


        # HOV
        # AM
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_4_Am", HOV_AM)

        # MD
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_4_Md", HOV_MD)

        # PM
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_4_Pm", HOV_PM)

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
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_4_Am", SOV_AM)

        # MD
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_4_Md", SOV_MD)

        # PM
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_4_Pm", SOV_PM)

        # HOV
        # AM
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_4_Am", AuDr_HOV_AM)

        # MD
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_4_Md", AuDr_HOV_MD)

        # PM
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_4_Pm", AuDr_HOV_PM)

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

        AM_Demand_List = [T_SOV_AM, T_HOV_AM, Bus_AM, Rail_AM, Walk_AM, Bike_AM]
        MD_Demand_List = [T_SOV_MD, T_HOV_MD, Bus_MD, Rail_MD, Walk_MD, Bike_MD]
        PM_Demand_List = [T_SOV_PM, T_HOV_PM, Bus_PM, Rail_PM, Walk_PM, Bike_PM]

        zero_demand = 0
        purp = "nhbw"

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

        Tiny =  0.000000001
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
        util.initmat(eb, "mf9070", "NHbWLS", " NHbW LogSum ", 0)

        ## Initialze Friction Factor Matrices
        util.initmat(eb, "mf9100", "P-AFrictionFact1", "Trip Distribution Friction Factor 1", 0)

        ## Initialize P-A Trip Tables by mode
        util.initmat(eb, "mf3700", "NHbWSOVPerTrips", "NHbW SOV Per-Trips", 0)
        util.initmat(eb, "mf3705", "NHbWHOVPerTrips", "NHbW HOV Per-Trips", 0)
        util.initmat(eb, "mf3715", "NHbWBusPerTrips", "NHbW Bus Per-Trips", 0)
        util.initmat(eb, "mf3720", "NHbWRailPerTrips", "NHbW Rail Per-Trips", 0)
        util.initmat(eb, "mf3730", "NHbWWalkPerTrips", "NHbW Walk Per-Trips", 0)
        util.initmat(eb, "mf3735", "NHbWBikePerTrips", "NHbW Bike Per-Trips", 0)

        ## Initialize P-A Trip Tables from trip distribution
        util.initmat(eb, "mf3750", "NHbWP-A", " NHbW P-A Trips ", 0)