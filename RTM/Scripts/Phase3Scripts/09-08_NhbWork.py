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
        # self.trip_generation(eb)

        # get dataframe for tripgeneration
        MChM.agg_hb_att(eb)
        self.trip_generation(eb)
        tnc_av_rate = 0.0
        NoTAZ = len(util.get_matrix_numpy(eb, "mo51"))

        hov_occupancy = eb.matrix("msAutoOcc").data
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

        # TNC Cost Factors
        # alpha_tnc and beta_tnc are calculated in Blended_Skims.py
        # TNC Coefficients and Calibration
        p30 = 0  #
        tnc_cost_scale = 30  # Coeff3 = coeff 2/lambda
        tnc_cost_exponent = 2 # TNC Cost exponent ; non-linear calibration constant
        p604 = 0.3  # TNC Accessibility measure
        tnc_wait_percep = 1.5 # multiplied to IVTT coefficient

        # HB mode to NHB mode calibration constants
        # Regular Vehicles
        p41 = 0.50  # Auto to Auto
        p42 = -5.43  # Auto to TNC
        p43 = -1.14  # Auto to Transit
        p44 = -0.81  # Auto to Active

        p51 = -3.20  # TNC to Auto
        p52 = 1.37  # TNC to TNC
        p53 = 2.34  # TNC to Transit
        p54 = 3.53  # TNC to Active

        p61 = -6.16  # Transit to Auto
        p62 = -5.47  # Transit to TNC
        p63 = 3.65  # Transit to Transit
        p64 = 0.35  # Transit to Active

        p71 = -5.20  # Active to Auto
        p72 = -6.66  # Active to TNC
        p73 = 0.28  # Active to Transit
        p74 = 3.53  # Active to Active

        # CAVs : TODO: Set these coefficients
        # Scale coefficients by 1/2 or 2/3 for TNC-Others and Others-TNC
        p46 = 0.50  # Auto to Auto
        p47 = -2.71  # Auto to TNC
        p48 = -0.57  # Auto to Transit
        p49 = -0.40  # Auto to Active

        p56 = -1.60  # TNC to Auto
        p57 = 1.37  # TNC to TNC
        p58 = 2.34  # TNC to Transit
        p59 = 3.53  # TNC to Active

        p66 = -3.08  # Transit to Auto
        p67 = -5.47  # Transit to TNC
        p68 = 3.65  # Transit to Transit
        p69 = 0.35  # Transit to Active

        p76 = -2.60  # Active to Auto
        p77 = -6.66  # Active to TNC
        p78 = 0.28  # Active to Transit
        p79 = 3.53  # Active to Active
#        ##############################################################################
#        ##       Auto Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        MaxPark = 10.0
        Hov_scale = 0.85
        tnc_scale = 0.85

        Occ = util.get_matrix_numpy(eb, 'HOVOccNHBw')
        tnc_occupancy = float(util.get_matrix_numpy(eb, 'TNCOccNhbw')) # TNC Occupancy
        Df['ParkCost'] = 0.5*(util.get_matrix_numpy(eb, 'prk8hr') +  util.get_matrix_numpy(eb, 'prk2hr'))# average parking of 2hrs and 8hrs parking
        Df['ParkCost'][Df['ParkCost']>MaxPark] = MaxPark
        Df['ParkCost'] = Df['ParkCost'].reshape(1, NoTAZ) + np.zeros((NoTAZ, 1))

        Df['AutoCosSOV'] = util.get_matrix_numpy(eb, 'NHbWBlSovCost')
        Df['AutoTimSOV'] = util.get_matrix_numpy(eb, 'NHbWBlSovTime')
        Df['AutoTotCosSOV'] = Df['AutoCosSOV'] + Df['ParkCost']

        Df['AutoCosHOV'] = util.get_matrix_numpy(eb, 'NHbWBlHovCost')
        Df['AutoTimHOV'] = util.get_matrix_numpy(eb, 'NHbWBlHovTime')
        Df['AutoTotCosHOV'] = Df['AutoCosHOV'] + Df['ParkCost']

        Df['TNCCost'] = util.get_matrix_numpy(eb, 'NHbWBlTNCCost')
        Df['TNCWaitTime'] = util.get_matrix_numpy(eb, 'tncwaittime')
        Df['TNCWaitTime'] = Df['TNCWaitTime'].reshape(NoTAZ,1)+ np.zeros((1,NoTAZ))

        Df['TNCAccess'] = util.get_matrix_numpy(eb,'tncAccLn').reshape(NoTAZ, 1) + np.zeros((1, NoTAZ))

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

        ## Taxi/TNC
        # Use HOV Skims, TNC Cost and Wait Times
        DfU['TNC'] = (p30
                     + p15 * Df['AutoTimHOV']
                     + p12 * Df['TNCCost']/pow(tnc_occupancy, tnc_scale)+
                     + (p12/tnc_cost_scale)*np.power(Df['TNCCost']/pow(tnc_occupancy, tnc_scale), tnc_cost_exponent)
                     + tnc_wait_percep * p15 * Df['TNCWaitTime']
                     + p604 * Df['TNCAccess']
        )
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
        BRT_fac, LRT_fac = MChM.calc_BRT_LRT_asc(eb, p4, p6)
        Bus_const = ((p4 * (Df['BusIVT']-Df['BusIVTBRT'])) + (BRT_fac * Df['BusIVTBRT'])) / (Df['BusIVT'] + Tiny)
        Rail_const = (p4 * (Df['RalIVB']-Df['RalIVBRT'])
                    + BRT_fac * Df['RalIVBRT']
                    + LRT_fac * Df['RalIVLRT']
                    + p6 * (Df['RalIVR']-Df['RalIVLRT'])) / (Df['RalIVR'] + Df['RalIVB'] + Tiny)

        p15b = p15*B_IVT_perc
        BRT_ivt, LRT_ivt = MChM.calc_BRT_LRT_ivt(eb, p15b, p15)

        # Utilities
        # Bus Utility
        # Bus Utility across all incomes
        Df['GeUtl'] = ( Bus_const
                      + Bus_Bias
                      + p12*Df['BusFar']
                      + p15*(Df['BusIVT'] - Df['BusIVTBRT'])*B_IVT_perc
                      + BRT_ivt*(Df['BusIVTBRT'])
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
                      + p15*(Df['RalIVB'] - Df['RalIVBRT'])*B_IVT_perc
                      + BRT_ivt*(Df['RalIVBRT'])
                      + p15*(Df['RalIVR'] - Df['RalIVLRT'])
                      + LRT_ivt*(Df['RalIVLRT'])
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
        # All Incomes
        LrgU = -9999

        # Regular Auto HHs
        # HB Mode Auto
        Dict = {
               'SOV'  : [DfU['SOV'] + p41],
               'HOV'  : [DfU['HOV'] + p41],
               'WTra' : [DfU['Bus'] + p43, DfU['Ral'] + p43],
               'Acti' : [DfU['Walk']+ p44, DfU['Bike'] + p44],
               'TNC'  : [DfU['TNC']+ p42]
               }

        # get a list of all keys
        taz_list = util.get_matrix_numpy(eb, 'zoneindex', reshape = False)
        keys_list = list(Dict.keys())
        modes_dict = {'All':keys_list, 'Auto': ['SOV', 'HOV', 'TNC'],
                     'Transit': ['WTra'], 'Active': ['Acti']}

        Dict_Au = MChM.Calc_Prob(eb, Dict, "NHbWLSAut", thet, 'aut_nhbwatr', LS_Coeff, modes_dict, taz_list)
        # HB Mode Taxi/TNC
        Dict = {
               'SOV'  : [DfU['SOV'] + p51],
               'HOV'  : [DfU['HOV'] + p51],
               'WTra' : [DfU['Bus']+ p53, DfU['Ral']+ p53],
               'Acti' : [DfU['Walk'] +p54, DfU['Bike']+p54],
               'TNC'  : [DfU['TNC'] +p52]
               }
        Dict_Tn = MChM.Calc_Prob(eb, Dict, "NHbWLSTnc", thet, 'tnc_nhbwatr', LS_Coeff, modes_dict, taz_list)

        # HB Mode Transit
        Dict = {
               'SOV'  : [DfU['SOV'] + p61],
               'HOV'  : [DfU['HOV'] + p61],
               'WTra' : [DfU['Bus'] + p63, DfU['Ral'] + p63],
               'Acti' : [DfU['Walk'] + p64, DfU['Bike'] + p64],
               'TNC'  : [DfU['TNC'] + p62]
               }

        Dict_Tr = MChM.Calc_Prob(eb, Dict, "NHbWLSTrn", thet, 'tra_nhbwatr', LS_Coeff, modes_dict, taz_list)

        # HB Mode Active
        Dict = {
               'SOV'  : [DfU['SOV'] + p71],
               'HOV'  : [DfU['HOV'] + p71],
               'WTra' : [DfU['Bus'] + p73, DfU['Ral'] + p73],
               'Acti' : [DfU['Walk'] + p74, DfU['Bike'] + p74],
               'TNC'  : [DfU['TNC'] + p72]
               }

        Dict_Ac = MChM.Calc_Prob(eb, Dict, "NHbWLSAct", thet, 'act_nhbwatr', LS_Coeff, modes_dict, taz_list)

        del DfU, Dict
#
       ##############################################################################
        ##       Trip Distribution
       ##############################################################################

        Logsum =  ["NHbWLSAut", "NHbWLSTrn", "NHbWLSAct", "NHbWLSTnc"]

        imp_list = ["P-AFrictionFact1", "P-AFrictionFact2", "P-AFrictionFact3","P-AFrictionFact4"]

        mo_list =  ["aut_nhbwprd", "tra_nhbwprd", "act_nhbwprd", "tnc_nhbwprd"]

        md_list =  ["aut_nhbwatr", "tra_nhbwatr", "act_nhbwatr", "tnc_nhbwatr"]

        out_list = ["NHbWP-AAut","NHbWP-ATrn","NHbWP-AAct","NHbWP-ATnc"]



        LambdaList = [-0.101658, -0.051249, -0.225967, -0.075000]




        AlphaList =  [0.0, 0.0, 0.0, 0.0]



        GammaList =  [0.0, 0.0, 0.0, 0.0]

        Kij = util.get_matrix_numpy(eb, "Kij_nhbw")

        Bridge_Factor = 0

        MChM.ImpCalc(eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, util.get_matrix_numpy(eb, "mfdistAON"), Kij, "Zero", Bridge_Factor)
        for i in range (len(out_list)):

            MChM.two_dim_matrix_balancing(eb, [mo_list[i]], [md_list[i]], [imp_list[i]], [out_list[i]])
#


#       ##############################################################################
#        ##       Calculate Demand
#       ##############################################################################

        Dict_Au = MChM.Calc_Demand(eb, Dict_Au,"NHbWP-AAut", write_att_demand = False)
        Dict_Tr = MChM.Calc_Demand(eb, Dict_Tr,"NHbWP-ATrn", write_att_demand = False)
        Dict_Ac = MChM.Calc_Demand(eb, Dict_Ac,"NHbWP-AAct", write_att_demand = False)
        Dict_Tn = MChM.Calc_Demand(eb, Dict_Tn,"NHbWP-ATnc", write_att_demand = False)

        SOV =   Dict_Au['SOV'][0]+Dict_Tr['SOV'][0]+Dict_Ac['SOV'][0]+Dict_Tn['SOV'][0]
        HOV =   Dict_Au['HOV'][0]+ Dict_Tr['HOV'][0]+Dict_Ac['HOV'][0]+ Dict_Tn['HOV'][0]

        Bus  =  Dict_Au['WTra'][0]+Dict_Tr['WTra'][0]+Dict_Ac['WTra'][0]+Dict_Tn['WTra'][0]
        Rail = Dict_Au['WTra'][1]+Dict_Tr['WTra'][1]+Dict_Ac['WTra'][1]+Dict_Tn['WTra'][1]

        Walk =  Dict_Au['Acti'][0]+Dict_Tr['Acti'][0]+Dict_Ac['Acti'][0]+Dict_Tn['Acti'][0]
        Bike = Dict_Au['Acti'][1]+Dict_Tr['Acti'][1]+Dict_Ac['Acti'][1]+Dict_Tn['Acti'][1]

        TNC = Dict_Au['TNC'][0]+Dict_Tr['TNC'][0]+Dict_Ac['TNC'][0]+Dict_Tn['TNC'][0]

        del Dict_Au, Dict_Tr, Dict_Ac, Dict_Tn


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

        #TNC
        TNC_AM = TNC*Auto_AM_Fct_PA
        TNC_MD = TNC*Auto_MD_Fct_PA
        TNC_PM = TNC*Auto_PM_Fct_PA

        # Convert TNC HOV to Vehicles
        HOV_TNC_AM = TNC_AM / tnc_occupancy
        HOV_TNC_MD = TNC_MD / tnc_occupancy
        HOV_TNC_PM = TNC_PM / tnc_occupancy

        # Convert HOV to Auto Drivers
        # HOV2
        # Add TNC HOV Trips
        AuDr_HOV_AM = HOV_AM/Occ + HOV_TNC_AM
        AuDr_HOV_MD = HOV_MD/Occ + HOV_TNC_MD
        AuDr_HOV_PM = HOV_PM/Occ + HOV_TNC_PM

        ## add TNC matrices for empty TNC component
        util.add_matrix_numpy(eb, "TncAMVehicleTrip", HOV_TNC_AM)
        util.add_matrix_numpy(eb, "TncMDVehicleTrip", HOV_TNC_MD)
        util.add_matrix_numpy(eb, "TncPMVehicleTrip", HOV_TNC_PM)


        del HOV_TNC_AM, HOV_TNC_MD, HOV_TNC_PM


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
        util.set_matrix_numpy(eb, "NHbWTNCPerTrips", TNC)

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


        # TNC
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_3_Am", TNC_AM)
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_3_Md", TNC_MD)
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_3_Pm", TNC_PM)

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

        # HOV (includes TNC trips)
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
        T_TNC_AM = TNC_AM


        # MD
        T_SOV_MD = np.where((Zone_Index_O>9999) & (Zone_Index_D>9999), SOV_MD, 0)
        T_HOV_MD = HOV_MD
        T_TNC_MD = TNC_MD

        # PM
        T_SOV_PM = np.where((Zone_Index_O>9999) & (Zone_Index_D>9999), SOV_PM, 0)
        T_HOV_PM = HOV_PM
        T_TNC_PM = TNC_PM

        # Daily
        T_SOV = np.where((Zone_Index_O>9999) & (Zone_Index_D>9999), SOV, 0)
        T_HOV = HOV
        T_TNC = TNC
        #
        df_demand = pd.DataFrame()

        Gy_P = util.get_matrix_numpy(eb, 'gy_ensem')  + np.zeros((1, NoTAZ))
        Gy_A = Gy_P.transpose()

        df_demand['gy_i'] = Gy_P.flatten()
        df_demand['gy_j'] = Gy_A.flatten()
        df_demand.gy_i = df_demand.gy_i.astype(int)
        df_demand.gy_j = df_demand.gy_j.astype(int)
        mode_list_am_pm = ['sov', 'hov', 'bus', 'rail', 'walk', 'bike', 'tnc']
        mode_list_md = ['sov', 'hov', 'bus', 'rail', 'walk', 'bike', 'tnc']
        mode_list_daily = ['sov', 'hov', 'bus', 'rail', 'walk', 'bike', 'tnc']

        AM_Demand_List = [T_SOV_AM, T_HOV_AM, Bus_AM, Rail_AM,  Walk_AM, Bike_AM, T_TNC_AM]
        MD_Demand_List = [T_SOV_MD, T_HOV_MD, Bus_MD, Rail_MD, Walk_MD, Bike_MD, T_TNC_MD]
        PM_Demand_List = [T_SOV_PM, T_HOV_PM, Bus_PM, Rail_PM,  Walk_PM, Bike_PM, T_TNC_PM]
        Daily_Demand_List = [T_SOV, T_HOV, Bus, Rail, Walk, Bike, T_TNC]

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

        df_gy_phr.to_sql(name='phr_gy', con=conn, index=False, if_exists='append')

        df_Daily_Gy.to_sql(name='daily_gy', con=conn, index=False, if_exists='append')

        conn.close()

    @_m.logbook_trace("Trip Generation")
    def trip_generation(self, eb):

        util = _m.Modeller().tool("translink.util")
        # get hb-attraction dataframe
        stat_sql = "SELECT * from trip_att_tots"
        conn = util.get_db_byname(eb, "trip_summaries.db")
        df = pd.read_sql(stat_sql, conn)
        conn.close()
        tiny = 0.0000001

        df['prod'], df['attr'] = 'p', 'a'

        df_coeff = pd.DataFrame()
        df_coeff['purpose'] = ['hbw', 'hbw',    'hbw',   'hbo', 'hbo' ,   'hbo',   'hbw', 'hbw',    'hbw',   'hbo', 'hbo' ,   'hbo',    'hbw', 'hbo', 'hbw', 'hbo']
        df_coeff['p-a'] =     ['p',    'p',     'p',     'p',   'p',      'p',     'a',   'a',      'a',     'a',   'a',      'a',      'p',   'p',   'a',   'a']
        df_coeff['mode'] =    ['Auto','Transit','Active','Auto','Transit','Active','Auto','Transit','Active','Auto','Transit','Active', 'TNC', 'TNC', 'TNC', 'TNC']
        df_coeff['coef'] = [0.267961,0.17766,0.357431,0.075147,0.023397,0.027981,0.20518,0.182704,0.30559,0.104174,0.020993,0.047189,0.117011,0.117011,0.117011,0.117011]

        df = pd.merge(df, df_coeff, how = 'left', left_on = ['purp', 'mode_agg', 'prod'], right_on = ['purpose', 'mode', 'p-a'])
        df['trip_prod'] = df['trips']*df['coef']
        df = df[['tz', 'purp', 'mode_agg', 'trips', 'trip_prod', 'attr']]

        df = pd.merge(df, df_coeff, how = 'left', left_on = ['purp', 'mode_agg', 'attr'], right_on = ['purpose', 'mode', 'p-a'])
        df['trip_attr'] = df['trips']*df['coef']
        df = df[['tz', 'purp', 'mode_agg', 'trip_prod', 'trip_attr']]
        df = df.groupby(['tz', 'mode_agg']).sum().reset_index()
        df = df.fillna(0)

        # Balance productions to attractions (use midpoint)
        df['trip_prod_adj'] = df['trip_prod']* 0.5*(1 + df.groupby(['mode_agg']).trip_attr.transform(np.sum)/(np.where(df.groupby(['mode_agg']).trip_prod.transform(np.sum) == 0, tiny, df.groupby(['mode_agg']).trip_prod.transform(np.sum))))
        df['trip_attr_adj'] = df['trip_attr']* 0.5*(1 + df.groupby(['mode_agg']).trip_prod.transform(np.sum)/(np.where(df.groupby(['mode_agg']).trip_attr.transform(np.sum) == 0, tiny, df.groupby(['mode_agg']).trip_attr.transform(np.sum))))

        #RV Auto
        df1 = df.loc[(df['mode_agg'] == "Auto")]
        util.set_matrix_numpy(eb, "aut_nhbwprd", df1['trip_prod_adj'].values)
        util.set_matrix_numpy(eb, "aut_nhbwatr", df1['trip_attr_adj'].values)

        #RV Transit
        df1 = df.loc[(df['mode_agg'] == "Transit")]
        util.set_matrix_numpy(eb, "tra_nhbwprd", df1['trip_prod_adj'].values)
        util.set_matrix_numpy(eb, "tra_nhbwatr", df1['trip_attr_adj'].values)

        #RV Active
        df1 = df.loc[(df['mode_agg'] == "Active")]
        util.set_matrix_numpy(eb, "act_nhbwprd", df1['trip_prod_adj'].values)
        util.set_matrix_numpy(eb, "act_nhbwatr", df1['trip_attr_adj'].values)

        #RV TNC
        df1 = df.loc[(df['mode_agg'] == "TNC")]
        util.set_matrix_numpy(eb, "tnc_nhbwprd", df1['trip_prod_adj'].values)
        util.set_matrix_numpy(eb, "tnc_nhbwatr", df1['trip_attr_adj'].values)

        df = df.groupby(['tz']).sum().reset_index()

        # upload data to sql database
        stat_sql1 = "SELECT * from TripsTazPrds"
        stat_sql2 = "SELECT * from TripsTazAtrs"

        conn = util.get_db_byname(eb, "rtm.db")
        df1 = pd.read_sql(stat_sql1, conn)
        df1['nhbw'] = df['trip_prod_adj']
        df1.to_sql(name='TripsTazPrds', con=conn, index=False, if_exists='replace')

        df1 = pd.read_sql(stat_sql2, conn)
        df1['nhbw'] = df['trip_attr_adj']
        df1.to_sql(name='TripsTazAtrs', con=conn, index=False, if_exists='replace')
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
        # Auto Segment
        util.initmat(eb, "mf9070", "NHbWLSAut", " NHbW LogSum HB Auto", 0)
        util.initmat(eb, "mf9370", "NHbWLSAUAut", "NHBW Auto Seg LogSum AU", 0)
        util.initmat(eb, "mf9470", "NHbWLSTRAut", "NHBW Auto Seg LogSum TR", 0)
        util.initmat(eb, "mf9570", "NHbWLSACAut", "NHBW Auto Seg LogSum AC", 0)

        # Transit Segment
        util.initmat(eb, "mf9071", "NHbWLSTrn", " NHbW LogSum HB Transit", 0)
        util.initmat(eb, "mf9371", "NHbWLSAUTrn", "NHBW Transit Seg LogSum AU", 0)
        util.initmat(eb, "mf9471", "NHbWLSTRTrn", "NHBW Transit Seg LogSum TR", 0)
        util.initmat(eb, "mf9571", "NHbWLSACTrn", "NHBW Transit Seg LogSum AC", 0)

        # Active Segment
        util.initmat(eb, "mf9072", "NHbWLSAct", " NHbW LogSum HB Active", 0)
        util.initmat(eb, "mf9372", "NHbWLSAUAct", "NHBW Active Seg LogSum AU", 0)
        util.initmat(eb, "mf9472", "NHbWLSTRAct", "NHBW Active Seg LogSum TR", 0)
        util.initmat(eb, "mf9572", "NHbWLSACAct", "NHBW Active Seg LogSum AC", 0)

        # TNC Segment
        util.initmat(eb, "mf9073", "NHbWLSTnc", " NHbW LogSum HB TNC", 0)
        util.initmat(eb, "mf9373", "NHbWLSAUTnc", "NHBW TNC Seg LogSum AU", 0)
        util.initmat(eb, "mf9473", "NHbWLSTRTnc", "NHBW TNC Seg LogSum TR", 0)
        util.initmat(eb, "mf9573", "NHbWLSACTnc", "NHBW TNC Seg LogSum AC", 0)

        ## Initialze Friction Factor Matrices
        util.initmat(eb, "mf9100", "P-AFrictionFact1", "Trip Distribution Friction Factor 1", 0)
        util.initmat(eb, "mf9101", "P-AFrictionFact2", "Trip Distribution Friction Factor 2", 0)
        util.initmat(eb, "mf9102", "P-AFrictionFact3", "Trip Distribution Friction Factor 3", 0)
        util.initmat(eb, "mf9103", "P-AFrictionFact4", "Trip Distribution Friction Factor 4", 0)

        ## Initialize P-A Trip Tables by mode
        util.initmat(eb, "mf3700", "NHbWSOVPerTrips", "NHbW SOV Per-Trips", 0)
        util.initmat(eb, "mf3705", "NHbWHOVPerTrips", "NHbW HOV Per-Trips", 0)
        util.initmat(eb, "mf3715", "NHbWBusPerTrips", "NHbW Bus Per-Trips", 0)
        util.initmat(eb, "mf3720", "NHbWRailPerTrips", "NHbW Rail Per-Trips", 0)
        util.initmat(eb, "mf3730", "NHbWWalkPerTrips", "NHbW Walk Per-Trips", 0)
        util.initmat(eb, "mf3735", "NHbWBikePerTrips", "NHbW Bike Per-Trips", 0)
        util.initmat(eb, "mf3740", "NHbWTNCPerTrips", "NHbW TNC Per-Trips", 0)

        ## Initialize P-A Trip Tables from trip distribution
        util.initmat(eb, "mf3760", "NHbWP-AAut", " NHbW P-A Trips HB Auto", 0)
        util.initmat(eb, "mf3761", "NHbWP-ATrn", " NHbW P-A Trips HB Transit", 0)
        util.initmat(eb, "mf3762", "NHbWP-AAct", " NHbW P-A Trips HB Active", 0)
        util.initmat(eb, "mf3763", "NHbWP-ATnc", " NHbW P-A Trips HB TNC", 0)

        ## Initialize trip generation matrices
        util.initmat(eb, "mo2070", "aut_nhbwprd", " Auto segment NHBW", 0)
        util.initmat(eb, "mo2071", "tra_nhbwprd", " Transit segment NHBW", 0)
        util.initmat(eb, "mo2072", "act_nhbwprd", " Active segment NHBW", 0)
        util.initmat(eb, "mo2073", "tnc_nhbwprd", " TNC segment NHBW", 0)


        util.initmat(eb, "md2070", "aut_nhbwatr", " Auto segment NHBW atr ", 0)
        util.initmat(eb, "md2071", "tra_nhbwatr", " Transit segment NHBW atr ", 0)
        util.initmat(eb, "md2072", "act_nhbwatr", " Active segment NHBW atr ", 0)
        util.initmat(eb, "md2073", "tnc_nhbwatr", " TNC segment NHBW atr ", 0)