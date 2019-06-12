##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage2.nhbwork
##--Purpose:
##---------------------------------------------------------------------
import inro.modeller as _m
import numpy as np
import pandas as pd

class Non_hbwork(_m.Tool()):

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Non-home Base work"
        pb.description = "Calculate non-home base work trips by mode and time of day"
        pb.branding_text = "TransLink"
        pb.runnable = False
        return pb.render()

    @_m.logbook_trace("Run Non-home base work")
    def __call__(self, eb, Bus_Bias, Rail_Bias, WCE_Bias):
        util = _m.Modeller().tool("translink.util")
        MChM = _m.Modeller().tool("translink.RTM3.stage2.modechoiceutils")

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
                     'PRAutTim': 0.0,
                     'br_ratio': 2.0,
                     'r_time'  : 20.0
                    }

        # Declare Utilities Data Frame
        DfU = {}

        # Add Coefficients

        p2   =  -2.823279
        p4   = -15.642681
        p6   = -13.669753
        p10  =  -5.787548
        p11  = -10.588930
        p12  =  -0.176712
        p15  =  -0.045283
        p17  =  -0.158322
        p18  =  -0.112071
        p19  =  -0.414299
        p20  =  -2.090444
        p21  =  -0.620644
        p602 =   1.089487
        p701 =   1.242719
        p702 =   0.673350
        p870 =   0.937169
        thet =   0.542267

        LS_Coeff = 0.7

#        ##############################################################################
#        ##       Auto Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        MaxPark = 10.0
        Hov_scale = 0.85

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
                      + p12*Df['AutoTotCosHOV']/(pow(Occ,Hov_scale))
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
        B_IVT_perc = 1.06

        Df['BusIVT'] = util.get_matrix_numpy(eb, 'NHbWBlBusIvtt')
        Df['BusWat'] = util.get_matrix_numpy(eb, 'NHbWBlBusWait')
        Df['BusAux'] = util.get_matrix_numpy(eb, 'NHbWBlBusAux')
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'NHbWBlBusBoard')
        Df['BusFar'] = util.get_matrix_numpy(eb, 'NHbWBlBusFare')
        Df['BusTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux']  # Total Bus Travel Time
        Df['BusIVTBRT'] = util.get_matrix_numpy(eb, 'NHbWBlBusIvttBRT') #In vehicle Bus BRT time

        Df['RalIVR'] = util.get_matrix_numpy(eb, 'NHbWBlRailIvtt')
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'NHbWBlRailIvttBus')
        Df['RalWat'] = util.get_matrix_numpy(eb, 'NHbWBlRailWait')
        Df['RalAux'] = util.get_matrix_numpy(eb, 'NHbWBlRailAux')
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'NHbWBlRailBoard')
        Df['RalFar'] = util.get_matrix_numpy(eb, 'NHbWBlRailFare')
        Df['RalTot'] = Df['RalIVB'] + Df['RalIVR'] + Df['RalWat'] + Df['RalAux'] # Total Bus Travel Time
        Df['RalIBR'] = Df['RalIVB']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Bus IVT to Total Time
        Df['RalIRR'] = Df['RalIVR']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Rail IVT to Total Time
        Df['RalIVBRT'] = util.get_matrix_numpy(eb, 'NHbWBlRailIvttBRT') #In vehicle Rail time BRT
        Df['RalIVLRT'] = util.get_matrix_numpy(eb, 'NHbWBlRailIvttLRT') #In vehicle Rail time LRT


        Df['IntZnl'] = np.identity(NoTAZ)
        Df['TranAccess'] = util.get_matrix_numpy(eb, 'transitAccLn').reshape(NoTAZ,1) + np.zeros((1, NoTAZ))

        # Calculate mode specific constant for BRT and LRT as a fraction of bus and rail constants
        BRT_asc, LRT_asc = MChM.calc_BRT_LRT_asc(eb, p4, p6)
        Bus_const = ((p4 * (Df['BusIVT']-Df['BusIVTBRT'])) + (BRT_fac * Df['BusIVTBRT'])) / (Df['BusIVT'] + Tiny)
        Rail_const = (p4 * (Df['RalIVB']-Df['RalIVBRT'])
                    + BRT_fac * Df['RalIVBRT']
                    + LRT_fac * Df['RalIVLRT']
                    + p6 * (Df['RalIVR']-Df['RalIVLRT'])) / (Df['RalIVR'] + Df['RalIVB'] + Tiny)
        # Utilities
        # Bus Utility
        # Bus Utility across all incomes
        Df['GeUtl'] = ( Bus_const
                      + Bus_Bias
                      + p12*Df['BusFar']
                      + p15*Df['BusIVT']*B_IVT_perc
                      + p17*Df['BusWat']
                      + p18*Df['BusAux']
                      + p19*Df['BusBrd']
                      + p602*Df['TranAccess'])

        # Check Availability conditions
        Df['GeUtl'] = MChM.BusAvail(Df, Df['GeUtl'], AvailDict)
        DfU['Bus'] = Df['GeUtl']

        # Rail Utility
        # Rail Utility across all incomes
        Df['GeUtl'] = ( Rail_const
                      + Rail_Bias
                      + p12*Df['RalFar']
                      + p15*Df['RalIVB']*B_IVT_perc
                      + p15*Df['RalIVR']
                      + p17*Df['RalWat']
                      + p18*Df['RalAux']
                      + p19*Df['RalBrd']
                      + p602*Df['TranAccess'])

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

        Df['PopEmpDenPA'] = util.get_matrix_numpy(eb, 'combinedens') + Tiny #Pop+Emp Density at Prod and Attr Zones
        Df['PopEmpDenPA'] = np.log(Df['PopEmpDenPA'].reshape(NoTAZ, 1) + Df['PopEmpDenPA'].reshape(1, NoTAZ)) #Broadcast Density

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

        taz_list = util.get_matrix_numpy(eb, 'zoneindex', reshape = False)

        # All Incomes All Autos
        Dict = {
               'SOV'  : [DfU['SOV']],
               'HOV'  : [DfU['HOV']],
               'WTra' : [DfU['Bus'], DfU['Ral']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }

        keys_list = list(Dict.keys())
        modes_dict = {'All':keys_list, 'Auto': ['SOV', 'HOV'],
                     'Transit': ['WTra'], 'Active': ['Acti']}

        Prob_Dict = MChM.Calc_Prob(eb, Dict, "NHbWLS", thet, 'nhbwatr', LS_Coeff, modes_dict, taz_list)
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



        LambdaList = [-0.094648]




        AlphaList =  [0.0]



        GammaList =  [0.0]

        Kij = util.get_matrix_numpy(eb, "Kij_nhbw")

        Bridge_Factor = 0

        MChM.ImpCalc(eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, util.get_matrix_numpy(eb, "mfdistAON"), Kij, "Zero", Bridge_Factor)
        MChM.two_dim_matrix_balancing(eb, mo_list, md_list, imp_list, out_list)


#       ##############################################################################
#        ##       Calculate Demand
#       ##############################################################################

        Demand_Dict = MChM.Calc_Demand(eb, Prob_Dict, "NHbWP-A")


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
        # setup for hbw auto time slice matrices
        conn = util.get_rtm_db(eb)

		# bus and rail AM PM factors
        ts_uw_b = pd.read_sql("SELECT * FROM timeSlicingFactors where mode='Bus' ", conn)
        ts_uw_r = pd.read_sql("SELECT * FROM timeSlicingFactors where mode='Rail'", conn)

        conn.close()

        # build basic ij mat with gb for production end
        df_mats_br = util.get_ijensem_df(eb, ensem_o = 'gb')
        df_mats_br['IX'] = 'IX'


        min_val=0.000143
        purp='nhbw'

        Auto_AM_Fct_PA, Auto_AM_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Auto',peakperiod='AM', geo='A',minimum_value=min_val)
        Auto_MD_Fct_PA, Auto_MD_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Auto',peakperiod='MD', geo='A',minimum_value=min_val)
        Auto_PM_Fct_PA, Auto_PM_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Auto',peakperiod='PM', geo='A',minimum_value=min_val)

		# Bus Factors for AM and PM
        Bus_AM_Fct_PA = MChM.ts_mat(df_mats_br, ts_uw_b, min_val, purp, 'AM', 'PtoA', NoTAZ)
        Bus_PM_Fct_PA = MChM.ts_mat(df_mats_br, ts_uw_b, min_val, purp, 'PM', 'PtoA', NoTAZ)

        Bus_AM_Fct_AP = MChM.ts_mat(df_mats_br, ts_uw_b, min_val, purp, 'AM', 'AtoP', NoTAZ)
        Bus_PM_Fct_AP = MChM.ts_mat(df_mats_br, ts_uw_b, min_val, purp, 'PM', 'AtoP', NoTAZ)

		# Rail Factors for AM and PM
        Rail_AM_Fct_PA = MChM.ts_mat(df_mats_br, ts_uw_r, min_val, purp, 'AM', 'PtoA', NoTAZ)
        Rail_PM_Fct_PA = MChM.ts_mat(df_mats_br, ts_uw_r, min_val, purp, 'PM', 'PtoA', NoTAZ)

        Rail_AM_Fct_AP = MChM.ts_mat(df_mats_br, ts_uw_r, min_val, purp, 'AM', 'AtoP', NoTAZ)
        Rail_PM_Fct_AP = MChM.ts_mat(df_mats_br, ts_uw_r, min_val, purp, 'PM', 'AtoP', NoTAZ)



        Tran_MD_Fct_PA, Tran_MD_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Transit',peakperiod='MD', geo='A',minimum_value=min_val)


        Acti_AM_Fct_PA, Acti_AM_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Active',peakperiod='AM', geo='A',minimum_value=min_val)
        Acti_MD_Fct_PA, Acti_MD_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Active',peakperiod='MD', geo='A',minimum_value=min_val)
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
        Bus_AM = Bus*Bus_AM_Fct_PA
        Bus_MD = Bus*Tran_MD_Fct_PA
        Bus_PM = Bus*Bus_PM_Fct_PA

        Rail_AM = Rail*Rail_AM_Fct_PA
        Rail_MD = Rail*Tran_MD_Fct_PA
        Rail_PM = Rail*Rail_PM_Fct_PA

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
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_3_Am", SOV_AM)
        # MD
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_3_Md", SOV_MD)

        # PM
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_3_Pm", SOV_PM)


        # HOV
        # AM
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_3_Am", HOV_AM)

        # MD
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_3_Md", HOV_MD)

        # PM
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_3_Pm", HOV_PM)

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
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_3_Am", SOV_AM)

        # MD
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_3_Md", SOV_MD)

        # PM
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_3_Pm", SOV_PM)

        # HOV
        # AM
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_3_Am", AuDr_HOV_AM)

        # MD
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_3_Md", AuDr_HOV_MD)

        # PM
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_3_Pm", AuDr_HOV_PM)

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

        # Daily
        T_SOV = np.where((Zone_Index_O>9999) & (Zone_Index_D>9999), SOV, 0)
        T_HOV = HOV
        #
        df_demand = pd.DataFrame()

        Gy_P = util.get_matrix_numpy(eb, 'gy_ensem')  + np.zeros((1, NoTAZ))
        Gy_A = Gy_P.transpose()

        df_demand['gy_i'] = Gy_P.flatten()
        df_demand['gy_j'] = Gy_A.flatten()
        df_demand.gy_i = df_demand.gy_i.astype(int)
        df_demand.gy_j = df_demand.gy_j.astype(int)
        mode_list_am_pm = ['sov', 'hov', 'bus', 'rail', 'walk', 'bike']
        mode_list_md = ['sov', 'hov', 'bus', 'rail', 'walk', 'bike']
        mode_list_daily = ['sov', 'hov', 'bus', 'rail', 'walk', 'bike']

        AM_Demand_List = [T_SOV_AM, T_HOV_AM, Bus_AM, Rail_AM,  Walk_AM, Bike_AM]
        MD_Demand_List = [T_SOV_MD, T_HOV_MD, Bus_MD, Rail_MD, Walk_MD, Bike_MD]
        PM_Demand_List = [T_SOV_PM, T_HOV_PM, Bus_PM, Rail_PM,  Walk_PM, Bike_PM]
        Daily_Demand_List = [T_SOV, T_HOV, Bus, Rail, Walk, Bike]

        purp = "nhbw"

        df_AM_Gy = MChM.Demand_Summary(df_demand, purp, "AM", AM_Demand_List, mode_list_am_pm)

        df_MD_Gy = MChM.Demand_Summary(df_demand, purp, "MD", MD_Demand_List, mode_list_md)

        df_PM_Gy = MChM.Demand_Summary(df_demand, purp, "PM", PM_Demand_List, mode_list_am_pm)

        df_Daily_Gy = MChM.Demand_Summary(df_demand, purp, "daily", Daily_Demand_List, mode_list_am_pm)

        df_gy_phr = pd.concat([df_AM_Gy, df_MD_Gy, df_PM_Gy])

        df_gy_phr = df_gy_phr[['gy_i','gy_j','purpose','mode', 'period', 'trips']]

        df_Daily_Gy = df_Daily_Gy[['gy_i','gy_j','purpose','mode', 'period', 'trips']]


        ## Dump to SQLite DB
        conn = util.get_db_byname(eb, "trip_summaries.db")

        df_gy_phr.to_sql(name='phr_gy', con=conn, flavor='sqlite', index=False, if_exists='append')

        df_Daily_Gy.to_sql(name='daily_gy', con=conn, flavor='sqlite', index=False, if_exists='append')

        conn.close()

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

        util.initmat(eb, "mf9370", "NHbWLSAU", " NHbW LogSum Auto", 0)

        util.initmat(eb, "mf9470", "NHbWLSTR", " NHbW LogSum Transit", 0)

        util.initmat(eb, "mf9570", "NHbWLSAC", " NHbW LogSum Active", 0)

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