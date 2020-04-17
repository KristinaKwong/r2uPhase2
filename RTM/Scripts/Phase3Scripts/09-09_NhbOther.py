##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage2.nhbother
##--Purpose:
##---------------------------------------------------------------------
import inro.modeller as _m
import numpy as np
import pandas as pd

class Non_hbwork(_m.Tool()):

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Non-home Base Other"
        pb.description = "Calculate non-home base other trips by mode and time of day"
        pb.branding_text = "TransLink"
        pb.runnable = False
        return pb.render()

    @_m.logbook_trace("Run Non-home base other")
    def __call__(self, eb, Bus_Bias, Rail_Bias, WCE_Bias):
        util = _m.Modeller().tool("translink.util")
        MChM = _m.Modeller().tool("translink.RTM3.stage2.modechoiceutils")

        tnc_av_rate = 0.0
        self.matrix_batchins(eb)
        self.trip_generation(eb)
        NoTAZ = len(util.get_matrix_numpy(eb, "mo51"))
        hov_occupancy = eb.matrix("msAutoOcc").data
#        ##############################################################################
#        ##       Define Availability thresholds
#        ##############################################################################

        AvailDict = {
                     'AutCost': 0.0,
                     'WlkDist': 5.0,
                     'BikDist': 10.0,
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


        p4   =   -2.797376
        p6   =   -1.613582
        p10  =   -2.436925
        p11  =   -7.316941
        p12  =   -0.471434
        p15  =   -0.049362
        p17  =   -0.138370
        p18  =   -0.063832
        p19  =   -0.307963
        p20  =   -1.596608
        p21  =   -0.658804
        p700 =    0.235778
        p701 =    0.425751
        p870 =    0.817462
        thet =    0.639408

        LS_Coeff = 0.8

        # TNC Cost Factors
        # alpha_tnc and beta_tnc are calculated in Blended_Skims.py
        # TNC Coefficients and Calibration
        p30 = 0  #
        tnc_cost_scale = 30  # Coeff3 = coeff 2/lambda
        tnc_cost_exponent = 2 # TNC Cost exponent ; non-linear calibration constant
        p604 = 0.3  # TNC Accessibility measure
        tnc_wait_percep = 1.5 # multiplied to IVTT coefficient

        # HB mode to NHB mode calibration constants
        p41 = 0.55  # Auto to Auto
        p42 = -4.47  # Auto to TNC
        p43 = -0.85  # Auto to Transit
        p44 = -0.74  # Auto to Active

        p51 = -1.98  # TNC to Auto
        p52 = 0.79  # TNC to TNC
        p53 = 1.77  # TNC to Transit
        p54 = 1.98  # TNC to Active

        p61 = -2.30  # Transit to Auto
        p62 = -5.12  # Transit to TNC
        p63 = 3.58  # Transit to Transit
        p64 = 0.15  # Transit to Active

        p71 = -1.08  # Active to Auto
        p72 = -4.45  # Active to TNC
        p73 = 1.12  # Active to Transit
        p74 = 3.00  # Active to Active

        # CAVs : TODO: Set these coefficients
        # Scale coefficients by 1/2 or 2/3 for TNC-Others and Others-TNC
        p46 = 0.55  # Auto to Auto
        p47 = -2.24  # Auto to TNC
        p48 = -0.42  # Auto to Transit
        p49 = -0.37  # Auto to Active

        p56 = -0.99  # TNC to Auto
        p57 = 0.79  # TNC to TNC
        p58 = 1.77  # TNC to Transit
        p59 = 1.98  # TNC to Active

        p66 = -1.15  # Transit to Auto
        p67 = -5.12  # Transit to TNC
        p68 = 3.58  # Transit to Transit
        p69 = 0.15  # Transit to Active

        p76 = -0.54  # Active to Auto
        p77 = -4.45  # Active to TNC
        p78 = 1.12  # Active to Transit
        p79 = 3.00  # Active to Active
#        ##############################################################################
#        ##       Auto Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        MaxPark = 10.0
        Hov_scale = 0.70
        tnc_scale = 0.70

        Occ = util.get_matrix_numpy(eb, 'AutoOccNHBo') # Occupancy across SOV and HOV
        tnc_occupancy = float(util.get_matrix_numpy(eb, 'TNCOccNhbo')) # TNC Occupancy
        Df['ParkCost'] = util.get_matrix_numpy(eb, 'prk2hr')  # 2 hour parking

        Df['ParkCost'] = Df['ParkCost'].reshape(1, NoTAZ) + np.zeros((NoTAZ, 1))


        Df['AutoCosHOV'] = util.get_matrix_numpy(eb, 'NHbOBlHovCost')
        Df['AutoTimHOV'] = util.get_matrix_numpy(eb, 'NHbOBlHovTime')
        Df['AutoTotCosHOV'] = Df['AutoCosHOV'] + Df['ParkCost']

        Df['TNCCost'] = util.get_matrix_numpy(eb, 'NHbOBlTNCCost')
        Df['TNCWaitTime'] = util.get_matrix_numpy(eb, 'tncwaittime')
        Df['TNCWaitTime'] = Df['TNCWaitTime'].reshape(NoTAZ,1)+ np.zeros((1,NoTAZ))

        Df['TNCAccess'] = util.get_matrix_numpy(eb,'tncAccLn').reshape(NoTAZ, 1) + np.zeros((1, NoTAZ))

        # Auto Utility across all incomes
        Df['GeUtl'] = ( 0.0
                      + p12*Df['AutoTotCosHOV']/(pow(Occ,Hov_scale))
                      + p15*Df['AutoTimHOV'])
        # Check Availability conditions
        Df['GeUtl']  = MChM.AutoAvail(Df['AutoCosHOV'], Df['GeUtl'], AvailDict)
        # Add Income parameters
        DfU['Auto'] = Df['GeUtl']

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

        Df['BusIVT'] = util.get_matrix_numpy(eb, 'NHbOBlBusIvtt')
        Df['BusWat'] = util.get_matrix_numpy(eb, 'NHbOBlBusWait')
        Df['BusAux'] = util.get_matrix_numpy(eb, 'NHbOBlBusAux')
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'NHbOBlBusBoard')
        Df['BusFar'] = util.get_matrix_numpy(eb, 'NHbOBlBusFare')
        Df['BusTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux'] # Total Bus Travel Time
        Df['BusIVTBRT'] = util.get_matrix_numpy(eb, 'NHbOBlBusIvttBRT') #In vehicle Bus BRT time

        Df['RalIVR'] = util.get_matrix_numpy(eb, 'NHbOBlRailIvtt')
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'NHbOBlRailIvttBus')
        Df['RalWat'] = util.get_matrix_numpy(eb, 'NHbOBlRailWait')
        Df['RalAux'] = util.get_matrix_numpy(eb, 'NHbOBlRailAux')
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'NHbOBlRailBoard')
        Df['RalFar'] = util.get_matrix_numpy(eb, 'NHbOBlRailFare')
        Df['RalTot'] = Df['RalIVB'] + Df['RalIVR'] + Df['RalWat'] + Df['RalAux'] # Total Bus Travel Time
        Df['RalIBR'] = Df['RalIVB']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Bus IVT to Total Time
        Df['RalIRR'] = Df['RalIVR']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Rail IVT to Total Time
        Df['RalIVBRT'] = util.get_matrix_numpy(eb, 'NHbOBlRailIvttBRT') #In vehicle Rail time BRT
        Df['RalIVLRT'] = util.get_matrix_numpy(eb, 'NHbOBlRailIvttLRT') #In vehicle Rail time LRT

        Df['IntZnl'] = np.identity(NoTAZ)
        Df['PopEmpDen'] = util.get_matrix_numpy(eb, 'combinedensln')
        Df['PopEmpDen'] = Df['PopEmpDen'].reshape(NoTAZ, 1) + np.zeros((1, NoTAZ))

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
                      + p700*Df['PopEmpDen'])

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
                      + p700*Df['PopEmpDen'])
        # Check Availability conditions
        Df['GeUtl'] = MChM.RailAvail(Df, Df['GeUtl'],AvailDict)
        DfU['Ral'] = Df['GeUtl']

#        ##############################################################################
#        ##       Active Modes
#        ##############################################################################

        Df = {}
        Df['AutoDis'] = util.get_matrix_numpy(eb, "mfdistAON")

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
            'Auto': [DfU['Auto'] + p41],
            'WTra': [DfU['Bus'] + p43, DfU['Ral'] + p43],
            'Acti': [DfU['Walk'] + p44, DfU['Bike'] + p44],
            'TNC': [DfU['TNC'] + p42]
        }

        # get a list of all keys
        taz_list = util.get_matrix_numpy(eb, 'zoneindex', reshape=False)
        keys_list = list(Dict.keys())
        modes_dict = {'All':keys_list, 'Auto': ['Auto'], 'Auto2': ['Auto', 'TNC'], 'TNC': ['TNC'],
                     'Transit': ['WTra'], 'Active': ['Acti']}

        Dict_Au = MChM.Calc_Prob(eb, Dict, "NHbOLSAut", thet, 'aut_nhboatr', LS_Coeff, modes_dict, taz_list)

        # HB Mode Taxi/TNC
        Dict = {
            'Auto': [DfU['Auto'] + p51],
            'WTra': [DfU['Bus'] + p53, DfU['Ral'] + p53],
            'Acti': [DfU['Walk'] + p54, DfU['Bike'] + p54],
            'TNC': [DfU['TNC'] + p52]
        }
        Dict_Tn = MChM.Calc_Prob(eb, Dict, "NHbOLSTnc", thet, 'tnc_nhboatr', LS_Coeff, modes_dict, taz_list)

        # HB Mode Transit
        Dict = {
            'Auto': [DfU['Auto'] + p61],
            'WTra': [DfU['Bus'] + p63, DfU['Ral'] + p63],
            'Acti': [DfU['Walk'] + p64, DfU['Bike'] + p64],
            'TNC': [DfU['TNC'] + p62]
        }

        Dict_Tr = MChM.Calc_Prob(eb, Dict, "NHbOLSTrn", thet, 'tra_nhboatr', LS_Coeff, modes_dict, taz_list)

        # HB Mode Active
        Dict = {
            'Auto': [DfU['Auto'] + p71],
            'WTra': [DfU['Bus'] + p73, DfU['Ral'] + p73],
            'Acti': [DfU['Walk'] + p74, DfU['Bike'] + p74],
            'TNC': [DfU['TNC'] + p72]
        }

        Dict_Ac = MChM.Calc_Prob(eb, Dict, "NHbOLSAct", thet, 'act_nhboatr', LS_Coeff, modes_dict, taz_list)

        del DfU, Dict
#
       ##############################################################################
        ##       Trip Distribution
       ##############################################################################

        Logsum =  ["NHbOLSAut", "NHbOLSTrn", "NHbOLSAct", "NHbOLSTnc"]

        imp_list = ["P-AFrictionFact1", "P-AFrictionFact2", "P-AFrictionFact3","P-AFrictionFact4"]

        mo_list =  ["aut_nhboprd", "tra_nhboprd", "act_nhboprd", "tnc_nhboprd"]

        md_list =  ["aut_nhboatr", "tra_nhboatr", "act_nhboatr", "tnc_nhboatr"]

        out_list = ["NHbOP-AAut","NHbOP-ATrn","NHbOP-AAct","NHbOP-ATnc"]


        LambdaList = [-0.244182, -0.278400, -0.384027, -0.260000]

        AlphaList =  [0.002548,  0.005041,  0.0, 0.003800]

        GammaList =  [-0.000007, -0.000050, 0.0, -0.000028]


        Kij = util.get_matrix_numpy(eb, "Kij_nhbo")

        Bridge_Factor = 0.5

        MChM.ImpCalc(eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, util.get_matrix_numpy(eb, "mfdistAON"), Kij, "NHbOBl_BPen", Bridge_Factor)
        for i in range (len(out_list)):

            MChM.one_dim_matrix_balancing(eb, [mo_list[i]], [md_list[i]], [imp_list[i]], [out_list[i]])



#       ##############################################################################
#        ##       Calculate Demand
#       ##############################################################################

        Dict_Au = MChM.Calc_Demand(eb, Dict_RvAu,"NHbOP-AAut", write_att_demand = False)
        Dict_Tr = MChM.Calc_Demand(eb, Dict_RvTr,"NHbOP-ATrn", write_att_demand = False)
        Dict_Ac = MChM.Calc_Demand(eb, Dict_RvAc,"NHbOP-AAct", write_att_demand = False)
        Dict_Tn = MChM.Calc_Demand(eb, Dict_RvTn,"NHbOP-ATnc", write_att_demand = False)


        Auto =   Dict_Au['Auto'][0]+Dict_Tr['Auto'][0]+Dict_Ac['Auto'][0]+Dict_Tn['Auto'][0]

        Bus  =  Dict_Au['WTra'][0]+Dict_Tr['WTra'][0]+Dict_Ac['WTra'][0]+Dict_Tn['WTra'][0]
        Rail = Dict_Au['WTra'][1]+Dict_Tr['WTra'][1]+Dict_Ac['WTra'][1]+Dict_Tn['WTra'][1]

        Walk =  Dict_Au['Acti'][0]+Dict_Tr['Acti'][0]+Dict_Ac['Acti'][0]+Dict_Tn['Acti'][0]
        Bike = Dict_Au['Acti'][1]+Dict_Tr['Acti'][1]+Dict_Ac['Acti'][1]+Dict_Tn['Acti'][1]

        TNC = Dict_Au['TNC'][0]+Dict_Tr['TNC'][0]+Dict_Ac['TNC'][0]+Dict_Tn['TNC'][0]

        del Dict_RvAu, Dict_Tr, Dict_Ac, Dict_Tn


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
        purp='nhbo'

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

        # Get split between SOV and HOV trips
        SOV_Split =  util.get_matrix_numpy(eb, 'sov_pct_NHBo')
        # HOV-specific occumancy
        HOcc = util.get_matrix_numpy(eb, 'HOVOccNHBo')

        SOV = Auto*SOV_Split
        HOV = Auto - SOV

      ## SOV Trips      #SOV*PA_Factor
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

        # Split TNC trips into SOV and HOV
        # TNC CAV Trips
        split_tnc_sov = (hov_occupancy - tnc_occupancy) / (hov_occupancy - 1)
        SOV_TNC_AM = TNC_AM * tnc_av_rate * split_tnc_sov
        SOV_TNC_MD = TNC_MD * tnc_av_rate * split_tnc_sov
        SOV_TNC_PM = TNC_PM * tnc_av_rate * split_tnc_sov

        HOV_TNC_AM = TNC_AM * tnc_av_rate * (1 - split_tnc_sov) / hov_occupancy + TNC_AM * (
                    1 - tnc_av_rate) / tnc_occupancy
        HOV_TNC_MD = TNC_MD * tnc_av_rate * (1 - split_tnc_sov) / hov_occupancy + TNC_MD * (
                    1 - tnc_av_rate) / tnc_occupancy
        HOV_TNC_PM = TNC_PM * tnc_av_rate * (1 - split_tnc_sov) / hov_occupancy + TNC_PM * (
                    1 - tnc_av_rate) / tnc_occupancy

        # Convert HOV to Auto Drivers
        # HOV2
        # Add TNC HOV Trips
        AuDr_HOV_AM = HOV_AM/Occ + HOV_TNC_AM
        AuDr_HOV_MD = HOV_MD/Occ + HOV_TNC_MD
        AuDr_HOV_PM = HOV_PM/Occ + HOV_TNC_PM

        ## add TNC matrices for empty TNC component
        util.add_matrix_numpy(eb, "TncAMVehicleTrip", SOV_TNC_AM)
        util.add_matrix_numpy(eb, "TncAMVehicleTrip", HOV_TNC_AM)

        util.add_matrix_numpy(eb, "TncMDVehicleTrip", SOV_TNC_MD)
        util.add_matrix_numpy(eb, "TncMDVehicleTrip", HOV_TNC_MD)

        util.add_matrix_numpy(eb, "TncPMVehicleTrip", SOV_TNC_PM)
        util.add_matrix_numpy(eb, "TncPMVehicleTrip", HOV_TNC_PM)


        del HOV_TNC_AM, HOV_TNC_MD, HOV_TNC_PM


#       ##############################################################################
#        ##       Set Demand Matrices
#       ##############################################################################
        # 24 hour trips

        util.set_matrix_numpy(eb, "NHbOSOVPerTrips", SOV)
        util.set_matrix_numpy(eb, "NHbOHOVPerTrips", HOV)
        util.set_matrix_numpy(eb, "NHbOBusPerTrips", Bus)
        util.set_matrix_numpy(eb, "NHbORailPerTrips", Rail)
        util.set_matrix_numpy(eb, "NHbOWalkPerTrips", Walk)
        util.set_matrix_numpy(eb, "NHbOBikePerTrips", Bike)
        util.set_matrix_numpy(eb, "NHbOTNCPerTrips", TNC)

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

        # TNC
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_1_Am", TNC_AM)
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_1_Md", TNC_MD)
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_1_Pm", TNC_PM)

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

        # Add SOV TNC Trips to SOV trip tables
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_1_Am", SOV_TNC_AM)
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_1_Md", SOV_TNC_MD)
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_1_Pm", SOV_TNC_PM)

        # HOV (includes TNC trips)
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

        T_SOV_AM = np.where((Zone_Index_O > 9999) & (Zone_Index_D > 9999), SOV_AM, 0)
        T_HOV_AM = HOV_AM
        T_TNC_AM = TNC_AM

        # MD
        T_SOV_MD = np.where((Zone_Index_O > 9999) & (Zone_Index_D > 9999), SOV_MD, 0)
        T_HOV_MD = HOV_MD
        T_TNC_MD = TNC_MD

        # PM
        T_SOV_PM = np.where((Zone_Index_O > 9999) & (Zone_Index_D > 9999), SOV_PM, 0)
        T_HOV_PM = HOV_PM
        T_TNC_PM = TNC_PM

        # Daily
        T_SOV = np.where((Zone_Index_O > 9999) & (Zone_Index_D > 9999), SOV, 0)
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

        AM_Demand_List = [T_SOV_AM, T_HOV_AM, Bus_AM, Rail_AM, Walk_AM, Bike_AM, T_TNC_AM]
        MD_Demand_List = [T_SOV_MD, T_HOV_MD, Bus_MD, Rail_MD, Walk_MD, Bike_MD, T_TNC_MD]
        PM_Demand_List = [T_SOV_PM, T_HOV_PM, Bus_PM, Rail_PM, Walk_PM, Bike_PM, T_TNC_PM]
        Daily_Demand_List = [T_SOV, T_HOV, Bus, Rail, Walk, Bike, T_TNC]

        purp = "nhbo"

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
        df_coeff['purpose'] = ['hbw', 'hbw', 'hbw', 'hbo', 'hbo' , 'hbo', 'hbw', 'hbw', 'hbw', 'hbo', 'hbo' , 'hbo', 'hbw', 'hbo', 'hbw', 'hbo']
        df_coeff['p-a'] = ['p', 'p', 'p','p', 'p', 'p', 'a', 'a', 'a','a', 'a', 'a', 'p', 'p', 'a', 'a']
        df_coeff['mode'] = ['Auto','Transit','Active','Auto','Transit','Active','Auto','Transit','Active','Auto','Transit','Active', 'TNC', 'TNC', 'TNC', 'TNC']
        df_coeff['coef'] = [0.050583,0.099943,0.210649,0.244174,0.114599,0.130311,0.027661,0.16644,0.17312,0.254689,0.07916,0.15068,0.150795,0.150795,0.150795,0.150795]

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
        util.set_matrix_numpy(eb, "aut_nhboprd", df1['trip_prod_adj'].values)
        util.set_matrix_numpy(eb, "aut_nhboatr", df1['trip_attr_adj'].values)

        #RV Transit
        df1 = df.loc[(df['mode_agg'] == "Transit")]
        util.set_matrix_numpy(eb, "tra_nhboprd", df1['trip_prod_adj'].values)
        util.set_matrix_numpy(eb, "tra_nhboatr", df1['trip_attr_adj'].values)

        #RV Active
        df1 = df.loc[(df['mode_agg'] == "Active")]
        util.set_matrix_numpy(eb, "act_nhboprd", df1['trip_prod_adj'].values)
        util.set_matrix_numpy(eb, "act_nhboatr", df1['trip_attr_adj'].values)

        #RV TNC
        df1 = df.loc[(df['mode_agg'] == "TNC")]
        util.set_matrix_numpy(eb, "tnc_nhboprd", df1['trip_prod_adj'].values)
        util.set_matrix_numpy(eb, "tnc_nhboatr", df1['trip_attr_adj'].values)



        df = df.groupby(['tz']).sum().reset_index()

         # upload data to sql database
        stat_sql1 = "SELECT * from TripsTazPrds"
        stat_sql2 = "SELECT * from TripsTazAtrs"

        conn = util.get_db_byname(eb, "rtm.db")
        df1 = pd.read_sql(stat_sql1, conn)
        df1['nhbo'] = df['trip_prod_adj']
        df1.to_sql(name='TripsTazPrds', con=conn, flavor='sqlite', index=False, if_exists='replace')

        df1 = pd.read_sql(stat_sql2, conn)
        df1['nhbo'] = df['trip_attr_adj']
        df1.to_sql(name='TripsTazAtrs', con=conn, flavor='sqlite', index=False, if_exists='replace')
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
        util.initmat(eb, "mf9080", "NHbOLSAut", " NhbO LogSum HB Auto", 0)
        util.initmat(eb, "mf9380", "NHbOAutLSAU", "NHBO Auto Seg LogSum AU", 0)
        util.initmat(eb, "mf9480", "NHbOAutLSTR", "NHBO Auto Seg LogSum TR", 0)
        util.initmat(eb, "mf9580", "NHbOAutLSAC", "NHBO Auto Seg LogSum AC", 0)

        # Transit Segment
        util.initmat(eb, "mf9081", "NHbOLSTrn", " NhbO LogSum HB Transit", 0)
        util.initmat(eb, "mf9381", "NHbOTrnLSAU", "NHBO Transit Seg LogSum AU", 0)
        util.initmat(eb, "mf9481", "NHbOTrnLSTR", "NHBO Transit Seg LogSum TR", 0)
        util.initmat(eb, "mf9581", "NHbOTrnLSAC", "NHBO Transit Seg LogSum AC", 0)

        # Active Segment
        util.initmat(eb, "mf9082", "NHbOLSAct", " NhbO LogSum HB Active", 0)
        util.initmat(eb, "mf9382", "NHbOActLSAU", "NHBO Active Seg LogSum AU", 0)
        util.initmat(eb, "mf9482", "NHbOActLSTR", "NHBO Active Seg LogSum TR", 0)
        util.initmat(eb, "mf9582", "NHbOActLSAC", "NHBO Active Seg LogSum AC", 0)

        # TNC Segment
        util.initmat(eb, "mf9083", "NHbOLSTnc", " NhbO LogSum HB TNC", 0)
        util.initmat(eb, "mf9383", "NHbOTncLSAU", "NHBO TNC Seg LogSum AU", 0)
        util.initmat(eb, "mf9483", "NHbOTncLSTR", "NHBO TNC Seg LogSum TR", 0)
        util.initmat(eb, "mf9583", "NHbOTncLSAC", "NHBO TNC Seg LogSum AC", 0)


        ## Initialze Friction Factor Matrices
        util.initmat(eb, "mf9100", "P-AFrictionFact1", "Trip Distribution Friction Factor 1", 0)
        util.initmat(eb, "mf9101", "P-AFrictionFact2", "Trip Distribution Friction Factor 2", 0)
        util.initmat(eb, "mf9102", "P-AFrictionFact3", "Trip Distribution Friction Factor 3", 0)
        util.initmat(eb, "mf9103", "P-AFrictionFact4", "Trip Distribution Friction Factor 4", 0)


        ## Initialize P-A Trip Tables by mode
        util.initmat(eb, "mf3800", "NHbOSOVPerTrips",  "NHbO SOV Per-Trips", 0)
        util.initmat(eb, "mf3805", "NHbOHOVPerTrips", "NHbO HOV Per-Trips", 0)
        util.initmat(eb, "mf3815", "NHbOBusPerTrips",  "NHbO Bus Per-Trips", 0)
        util.initmat(eb, "mf3820", "NHbORailPerTrips", "NHbO Rail Per-Trips", 0)
        util.initmat(eb, "mf3830", "NHbOWalkPerTrips", "NHbO Walk Per-Trips", 0)
        util.initmat(eb, "mf3835", "NHbOBikePerTrips", "NHbO Bike Per-Trips", 0)
        util.initmat(eb, "mf3840", "NHbOTNCPerTrips", "NHbO TNC Per-Trips", 0)

        ## Initialize P-A Trip Tables from trip distribution
        util.initmat(eb, "mf3860", "NHbOP-AAut", " NHbO P-A Trips HB Auto", 0)
        util.initmat(eb, "mf3861", "NHbOP-ATrn", " NHbO P-A Trips HB Transit", 0)
        util.initmat(eb, "mf3862", "NHbOP-AAct", " NHbO P-A Trips HB Active", 0)
        util.initmat(eb, "mf3863", "NHbOP-ATnc", " NHbO P-A Trips HB TNC", 0)

        ## Initialize trip generation matrices
        util.initmat(eb, "mo2080", "aut_nhboprd", " Auto segment NHBO prd ", 0)
        util.initmat(eb, "mo2081", "tra_nhboprd", " Transit segment NHBO prd ", 0)
        util.initmat(eb, "mo2082", "act_nhboprd", " Active segment NHBO prd ", 0)
        util.initmat(eb, "mo2083", "tnc_nhboprd", " TNC segment NHBO prd ", 0)

        util.initmat(eb, "md2080", "aut_nhboatr", " Auto segment NHBO atr ", 0)
        util.initmat(eb, "md2081", "tra_nhboatr", " Transit segment NHBO atr ", 0)
        util.initmat(eb, "md2082", "act_nhboatr", " Active segment NHBO atr ", 0)
        util.initmat(eb, "md2083", "tnc_nhboatr", " TNC segment NHBO atr ", 0)


