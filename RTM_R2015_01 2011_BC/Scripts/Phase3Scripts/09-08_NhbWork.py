##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.emme.xxxx
##--Purpose:
##---------------------------------------------------------------------
import inro.modeller as _m
import csv
import os
import numpy as np
import pandas as pd
import sqlite3
import traceback as _traceback

class Non_hbwork(_m.Tool()):

    ##Global attribute for Tool Run Message (successful/not successful)
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Non-home Base work"
        pb.description = "Calculate non-home base work trips by mode and time of day"
        pb.branding_text = "TransLink"
        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            self.__call__(_m.Modeller().emmebank)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

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
                     'AutDist': 0.0,
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

        VOC = util.get_matrix_numpy(eb, 'autoOpCost')
        Occ = util.get_matrix_numpy(eb, 'HOVOccNHBw')
        Df['ParkCost'] = 0.5*(util.get_matrix_numpy(eb, 'prk8hr') +  util.get_matrix_numpy(eb, 'prk2hr'))# average parking of 2hrs and 8hrs parking
        Df['ParkCost'][Df['ParkCost']>MaxPark] = MaxPark
        Df['ParkCost'] = Df['ParkCost'].reshape(1, NoTAZ) + np.zeros((NoTAZ, 1))

        Df['AutoDisSOV'] = util.get_matrix_numpy(eb, 'NHbWBlSovDist')
        Df['AutoTimSOV'] = util.get_matrix_numpy(eb, 'NHbWBlSovTime')
        Df['AutoCosSOV'] = Df['AutoDisSOV']*VOC + util.get_matrix_numpy(eb, 'NHbWBlSovToll') + Df['ParkCost']

        Df['AutoDisHOV'] = util.get_matrix_numpy(eb, 'NHbWBlHovDist')
        Df['AutoTimHOV'] = util.get_matrix_numpy(eb, 'NHbWBlHovTime')
        Df['AutoCosHOV'] = Df['AutoDisHOV']*VOC + util.get_matrix_numpy(eb, 'NHbWBlHovToll') + Df['ParkCost']

        # Utilities
        # SOV
        # SOV Utility across all incomes
        Df['GeUtl'] = ( 0
                      + p12*Df['AutoCosSOV']
                      + p15*Df['AutoTimSOV'])

        # Check Availability conditions
        Df['GeUtl']  = MChM.AutoAvail(Df['AutoDisSOV'], Df['GeUtl'], AvailDict)
        DfU['SOV'] = Df['GeUtl']

        # HOV2+
        # HOV2+ Utility across all incomes
        Df['GeUtl'] = ( p2
                      + p12*Df['AutoCosHOV']/Occ
                      + p15*Df['AutoTimHOV'])
        # Check Availability conditions
        Df['GeUtl']  = MChM.AutoAvail(Df['AutoDisHOV'], Df['GeUtl'], AvailDict)
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
        Df['AutoDis'] = util.get_matrix_numpy(eb, 'HbWBlSovDist_I1')
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

        LambdaList = [-0.097334]

        AlphaList =  [0.001020]

        GammaList =  [-0.000005]

        MChM.ImpCalc(eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, util.get_matrix_numpy(eb, 'HbWBlSovDist_I1'))
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

        db_loc = util.get_eb_path(eb)
        db_path = os.path.join(db_loc, 'rtm.db')
        conn = sqlite3.connect(db_path)
        ts_df = pd.read_sql("SELECT * from timeSlicingFactors", conn)
        conn.close()
        # Subset Time Slice Factor Dataframes by purpose
        nhbw_ts = ts_df.loc[ts_df['purpose'] == 'nhbw']

        # Subset Time Slice Factor Dataframes by mode
        Auto_AM_Fct, Auto_MD_Fct, Auto_PM_Fct = self.get_ts_factor(nhbw_ts.loc[nhbw_ts['mode'] == 'Auto']) # Auto Factors
        Tran_AM_Fct, Tran_MD_Fct, Tran_PM_Fct = self.get_ts_factor(nhbw_ts.loc[nhbw_ts['mode'] == 'Transit']) # Transit Factors
        Acti_AM_Fct, Acti_MD_Fct, Acti_PM_Fct = self.get_ts_factor(nhbw_ts.loc[nhbw_ts['mode'] == 'Active']) # Active Factors

        del ts_df, nhbw_ts

      ##########################################################################################
       ##       Calculate peak hour O-D person trips and final 24 hour P-A Trips
      ##########################################################################################
      ## SOV Trips      #SOV*PA_Factor + SOV_transpose*AP_Factor
        SOV_AM = SOV*Auto_AM_Fct[0]
        SOV_MD = SOV*Auto_MD_Fct[0]
        SOV_PM = SOV*Auto_PM_Fct[0]

        ## HOV Trips
        HOV_AM = HOV*Auto_AM_Fct[0]
        HOV_MD = HOV*Auto_MD_Fct[0]
        HOV_PM = HOV*Auto_PM_Fct[0]

        ## Transit Trips
        Bus_AM = Bus*Tran_AM_Fct[0]
        Bus_MD = Bus*Tran_MD_Fct[0]
        Bus_PM = Bus*Tran_PM_Fct[0]

        Rail_AM = Rail*Tran_AM_Fct[0]
        Rail_MD = Rail*Tran_MD_Fct[0]
        Rail_PM = Rail*Tran_PM_Fct[0]

        ## Active Trips
        Walk_AM = Walk*Acti_AM_Fct[0]
        Walk_MD = Walk*Acti_MD_Fct[0]
        Walk_PM = Walk*Acti_PM_Fct[0]

        Bike_AM = Bike*Acti_AM_Fct[0]
        Bike_MD = Bike*Acti_MD_Fct[0]
        Bike_PM = Bike*Acti_PM_Fct[0]


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
        self.set_pkhr_mats(eb, SOV_AM, "SOV_pertrp_VOT_4_Am")
        # MD
        self.set_pkhr_mats(eb, SOV_MD, "SOV_pertrp_VOT_4_Md")

        # PM
        self.set_pkhr_mats(eb, SOV_PM, "SOV_pertrp_VOT_4_Pm")


        # HOV
        # AM
        self.set_pkhr_mats(eb, HOV_AM, "HOV_pertrp_VOT_4_Am")

        # MD
        self.set_pkhr_mats(eb, HOV_MD, "HOV_pertrp_VOT_4_Md")

        # PM
        self.set_pkhr_mats(eb, HOV_PM, "HOV_pertrp_VOT_4_Pm")

        # Transit
        # AM
        self.set_pkhr_mats(eb, Bus_AM, "busAm")
        self.set_pkhr_mats(eb, Rail_AM, "railAm")

        # MD
        self.set_pkhr_mats(eb, Bus_MD, "busMd")
        self.set_pkhr_mats(eb, Rail_MD, "railMd")

        # PM
        self.set_pkhr_mats(eb, Bus_PM, "busPm")
        self.set_pkhr_mats(eb, Rail_PM, "railPm")

        # Active
        # AM
        self.set_pkhr_mats(eb, Walk_AM, "Wk_pertrp_Am")
        self.set_pkhr_mats(eb, Bike_AM, "Bk_pertrp_Am")

        # MD
        self.set_pkhr_mats(eb, Walk_MD, "Wk_pertrp_Md")
        self.set_pkhr_mats(eb, Bike_MD, "Bk_pertrp_Md")

        # PM
        self.set_pkhr_mats(eb, Walk_PM, "Wk_pertrp_Pm")
        self.set_pkhr_mats(eb, Bike_PM, "Bk_pertrp_Pm")

        # Auto-driver

        # SOV
        # AM
        self.set_pkhr_mats(eb, SOV_AM, "SOV_drvtrp_VOT_4_Am")

        # MD
        self.set_pkhr_mats(eb, SOV_MD, "SOV_drvtrp_VOT_4_Md")

        # PM
        self.set_pkhr_mats(eb, SOV_PM, "SOV_drvtrp_VOT_4_Pm")

        # HOV
        # AM
        self.set_pkhr_mats(eb, AuDr_HOV_AM, "HOV_drvtrp_VOT_4_Am")

        # MD
        self.set_pkhr_mats(eb, AuDr_HOV_MD, "HOV_drvtrp_VOT_4_Md")

        # PM
        self.set_pkhr_mats(eb, AuDr_HOV_PM, "HOV_drvtrp_VOT_4_Pm")

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

    def get_ts_factor (self, ts_df):

        AM_Ts_List = [float(ts_df .loc[(ts_df['peakperiod'] == 'AM') & (ts_df['direction'] == 'PtoA'), 'shares'])]


        MD_Ts_List = [float(ts_df .loc[(ts_df['peakperiod'] == 'MD') & (ts_df['direction'] == 'PtoA'), 'shares'])]


        PM_Ts_List = [float(ts_df .loc[(ts_df['peakperiod'] == 'PM') & (ts_df['direction'] == 'PtoA'), 'shares'])]


        return (AM_Ts_List, MD_Ts_List, PM_Ts_List)

    def set_pkhr_mats(self, eb, MatVal, MatID):

        util = _m.Modeller().tool("translink.util")
        Value = util.get_matrix_numpy(eb, MatID)
        Value += MatVal
        util.set_matrix_numpy(eb, MatID, Value)

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