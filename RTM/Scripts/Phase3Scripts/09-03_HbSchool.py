##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage2.hbschool
##--Purpose:
##---------------------------------------------------------------------
import inro.modeller as _m
import numpy as np
import pandas as pd

class HbSchool(_m.Tool()):

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Home Base School"
        pb.description = "Calculate home base School person trips by mode and time of day"
        pb.branding_text = "TransLink"
        pb.runnable = False
        return pb.render()

    @_m.logbook_trace("Run Home Base School")
    def __call__(self, eb, Bus_Bias, Rail_Bias, WCE_Bias):
        util = _m.Modeller().tool("translink.util")
        MChM = _m.Modeller().tool("translink.RTM3.stage2.modechoiceutils")

        self.matrix_batchins(eb)
        NoTAZ = len(util.get_matrix_numpy(eb, "mo51"))
        tnc_occupancy = float(util.get_matrix_numpy(eb, 'TNCOccHbsch'))  # TNC Occupancy

        tnc_av_rate = 0.0

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
                     'BRTotLow':10.0,
                     'BRTotHig':120.0,
                     'WCTotLow':30.0,
                     'WCTotHig':130.0,
                     'PRAutTim':0.0,
                     'br_ratio': 2.0,
                     'r_time'  : 20.0
                    }

        # Declare Utilities Data Frame
        DfU = {}

        # Add Coefficients
        p2   = -5.133076
        p4   = -4.512706
        p6   = -5.226410
        p11  = -4.012878
        p12  = -0.445877
        p20  = -1.874970
        p21  = -1.320351
        p162 =  1.385854
        p163 =  2.905327
        p602 =  0.370481
        p701 =  0.222423
        thet =  0.500000
        LS_Coeff = 0.4

        # TNC Cost Factors
        # alpha_tnc and beta_tnc are calculated in Blended_Skims.py
        # TNC Coefficients and Calibration
        p30 = -9999.0  # Unavailable for School Trips
        #TNC Wait Time Coefficient = 1.92*p12*VOT/60

        tnc_cost_scale = 50  # Coeff3 = coeff 2/lambda
        tnc_cost_exponent = 2  # TNC Cost exponent ; non-linear calibration constant

#        ##############################################################################
#        ##       Auto Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        MaxPark = 10.0
        Hov_scale = 0.50
        tnc_scale = 0.50 # TODO: update

        Occ = util.get_matrix_numpy(eb, 'HOVOccHBsch')    # Occ=3.02
        VOT = 5.0 # rs: hard coded

        Df['AutoCosHOV'] = util.get_matrix_numpy(eb, 'HbScBlHovCost')
        Df['AutoTimHOV'] = util.get_matrix_numpy(eb, 'HbScBlHovTime')
        Df['AutoTotCosHOV'] = (Df['AutoCosHOV'])/(pow(Occ,Hov_scale)) # students do not pay any cost adjustment

        Df['TNCCost'] = util.get_matrix_numpy(eb, 'HbScBlTNCCost')
        Df['TNCWaitTime'] = util.get_matrix_numpy(eb, 'tncwaittime')
        Df['TNCWaitTime'] = Df['TNCWaitTime'].reshape(NoTAZ,1)+ np.zeros((1,NoTAZ))

        # Utilities
        # HOV2+
        # HOV2+ Utility across all incomes
        Df['GeUtl'] = (p2
                      + (p12*(VOT*Df['AutoTimHOV']/60+Df['AutoTotCosHOV'])))
        # Check Availability conditions
        DfU['HOV']  = MChM.AutoAvail(Df['AutoCosHOV'], Df['GeUtl'], AvailDict)

        ## Taxi/TNC
        # Use HOV Skims, TNC Cost and Wait Times
        Df['TNC'] = (p30
                     + p12 * VOT* (Df['AutoTimHOV']+ 1.5 * Df['TNCWaitTime'])/60
                     + p12 * Df['TNCCost']/pow(tnc_occupancy, tnc_scale)+
                     + (p12/tnc_cost_scale)*np.power((Df['TNCCost']/pow(tnc_occupancy, tnc_scale)), tnc_cost_exponent))

        DfU['TNC'] = MChM.AutoAvail(Df['TNCCost'], Df['TNC'], AvailDict)

#        ##############################################################################
#        ##       Walk to Transit Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        Tiny=0.000001
        B_IVT_perc = 1.06

        Disc_Fare = 0.85 # Student Fare Discount
        Df['BusIVT'] = util.get_matrix_numpy(eb, 'HbScBlBusIvtt')
        Df['BusWat'] = util.get_matrix_numpy(eb, 'HbScBlBusWait')
        Df['BusAux'] = util.get_matrix_numpy(eb, 'HbScBlBusAux')
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'HbScBlBusBoard')
        Df['BusFar'] = util.get_matrix_numpy(eb, 'HbScBlBusFare')
        Df['BusTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux']  # Total Bus Travel Time
        Df['BusFar'] = Df['BusFar'] * Disc_Fare  ## discount fare for students
        Df['BusIVTBRT'] = util.get_matrix_numpy(eb, 'HbScBlBusIvttBRT') #In vehicle Bus BRT time

        Df['RalIVR'] = util.get_matrix_numpy(eb, 'HbScBlRailIvtt')
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'HbScBlRailIvttBus')
        Df['RalWat'] = util.get_matrix_numpy(eb, 'HbScBlRailWait')
        Df['RalAux'] = util.get_matrix_numpy(eb, 'HbScBlRailAux')
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'HbScBlRailBoard')
        Df['RalFar'] = util.get_matrix_numpy(eb, 'HbScBlRailFare')
        Df['RalTot'] = Df['RalIVB'] + Df['RalIVR'] + Df['RalWat'] + Df['RalAux']  # Total Bus Travel Time
        Df['RalIBR'] = Df['RalIVB']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Bus IVT to Total Time
        Df['RalIRR'] = Df['RalIVR']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Rail IVT to Total Time
        Df['RalFar'] = Df['RalFar'] * Disc_Fare  ## discount fare for students
        Df['RalIVBRT'] = util.get_matrix_numpy(eb, 'HbScBlRailIvttBRT') #In vehicle Rail time BRT
        Df['RalIVLRT'] = util.get_matrix_numpy(eb, 'HbScBlRailIvttLRT') #In vehicle Rail time LRT

        Df['IntZnl'] = np.identity(NoTAZ)
        Df['PopEmpDen'] = util.get_matrix_numpy(eb, 'combinedensln')
        Df['PopEmpDen'] = Df['PopEmpDen'].reshape(NoTAZ, 1) + np.zeros((1, NoTAZ))

        p15r = 1.0
        p15b = p15r*B_IVT_perc

        BRT_ivt, LRT_ivt = MChM.calc_BRT_LRT_ivt(eb, p15b, p15r)

        Df['GenCostBus'] = ((Df['BusIVT'] - Df['BusIVTBRT'])*B_IVT_perc
                           + Df['BusIVTBRT']*BRT_ivt
                           + 1.92*Df['BusWat']
                           + 1.71*Df['BusAux']
                           + 10.81*Df['BusBrd'])

        Df['GenCostBus'] = VOT*Df['GenCostBus']/60.0 + Df['BusFar']

        Df['GenCostRal'] = ((Df['RalIVB'] - Df['RalIVBRT'])*B_IVT_perc
                           + Df['RalIVBRT']*BRT_ivt
                           +(Df['RalIVR'] - Df['RalIVLRT'])
                           + LRT_ivt*(Df['RalIVLRT'])
                           + 2.03*Df['RalWat']
                           + 1.80*Df['RalAux']
                           + 11.80*Df['RalBrd'])

        Df['GenCostRal'] = VOT*Df['GenCostRal']/60.0 + Df['RalFar']

        # Calculate mode specific constant for BRT and LRT as a fraction of bus and rail constants
        BRT_fac, LRT_fac = MChM.calc_BRT_LRT_asc(eb, p4, p6)
        Bus_const = ((p4 * (Df['BusIVT']-Df['BusIVTBRT'])) + (BRT_fac * Df['BusIVTBRT'])) / (Df['BusIVT'] + Tiny)
        Rail_const = (p4 * (Df['RalIVB']-Df['RalIVBRT'])
                    + BRT_fac * Df['RalIVBRT']
                    + LRT_fac * Df['RalIVLRT']
                    + p6 * (Df['RalIVR']-Df['RalIVLRT'])) / (Df['RalIVR'] + Df['RalIVB'] + Tiny)
        # Utilities
        # Bus Utility

        Df['GeUtl'] = ( Bus_const
                      + Bus_Bias
                      + p12*Df['GenCostBus']
                      + p602*Df['PopEmpDen'])

        # Check Availability conditions
        Df['GeUtl'] = MChM.BusAvail(Df, Df['GeUtl'],AvailDict)
        DfU['Bus'] = Df['GeUtl']

        # Rail Utility
        # log(pop+emp) at production zone will be added below
        # Rail Utility across all incomes
        Df['GeUtl'] = ( Rail_const
                      + Rail_Bias
                      + p12*Df['GenCostRal']
                      + p602*Df['PopEmpDen'])

        # Check Availability conditions
        Df['GeUtl'] = MChM.RailAvail(Df, Df['GeUtl'],AvailDict)
        # Add Income parameters
        DfU['Ral'] = Df['GeUtl']

#        ##############################################################################
#        ##       Active Modes
#        ##############################################################################

        Df = {}
        Df['AutoDis'] = util.get_matrix_numpy(eb, "mfdistAON") # Distance
        Df['PopEmpDen'] = util.get_matrix_numpy(eb, 'combinedensln')
        Df['PopEmpDen'] = Df['PopEmpDen'].reshape(NoTAZ, 1) + np.zeros((1, NoTAZ))

        Df['PopEmpDenPA'] = util.get_matrix_numpy(eb, 'combinedens') + Tiny#Pop+Emp Density at Prod and Attr Zones
        Df['PopEmpDenPA'] = np.log(Df['PopEmpDenPA'].reshape(NoTAZ, 1) + Df['PopEmpDenPA'].reshape(1, NoTAZ)) #Broadcast Density

        # Walk Utility
        DfU['Walk'] = ( 0
                      + p20*Df['AutoDis']
                      + p701*Df['PopEmpDenPA'])

        # Check Availability conditions
        DfU['Walk'] = MChM.WalkAvail(Df['AutoDis'], DfU['Walk'], AvailDict)

        # Bike Utility
        DfU['Bike'] = ( p11
                      + p21*Df['AutoDis']
                      + p701*Df['PopEmpDenPA'])

        # Check Availability conditions
        DfU['Bike'] = MChM.BikeAvail(Df['AutoDis'], DfU['Bike'], AvailDict)

        del Df

#        ##############################################################################
#        ##       Calculate Probabilities
#        ##############################################################################

        #############
        # All Incomes
        #############

        taz_list = util.get_matrix_numpy(eb, 'zoneindex', reshape = False)

        ## Zero Autos
        Dict = {
               'HOV'  : [DfU['HOV']],
               'WTra' : [DfU['Bus'], DfU['Ral']],
               'Acti' : [DfU['Walk'], DfU['Bike']],
               'TNC'  : [DfU['TNC']]
               }

        # get a list of all keys

        keys_list = list(Dict.keys())
        modes_dict = {'All':keys_list, 'Auto': ['HOV', 'TNC'],
                     'Transit': ['WTra'], 'Active': ['Acti']}

        A0_Dict = MChM.Calc_Prob(eb, Dict, "HbScLSA0", thet, 'hbschatr', LS_Coeff, modes_dict, taz_list)

        ## One Auto
        Dict = {
               'HOV'  : [DfU['HOV'] + p162],
               'WTra' : [DfU['Bus'], DfU['Ral']],
               'Acti' : [DfU['Walk'], DfU['Bike']],
               'TNC'  : [DfU['TNC']]
               }

        A1_Dict = MChM.Calc_Prob(eb, Dict, "HbScLSA1", thet, 'hbschatr', LS_Coeff, modes_dict, taz_list)

        ## Two Auto
        Dict = {
               'HOV'  : [DfU['HOV'] + p163],
               'WTra' : [DfU['Bus'], DfU['Ral']],
               'Acti' : [DfU['Walk'], DfU['Bike']],
               'TNC'  : [DfU['TNC']]
               }

        A2_Dict = MChM.Calc_Prob(eb, Dict, "HbScLSA2", thet, 'hbschatr', LS_Coeff, modes_dict, taz_list)

#       ##############################################################################
#        ##       Trip Distribution
#       ##############################################################################

        Logsum =  [
                  "HbScLSA0", "HbScLSA1", "HbScLSA2",
                  "HbScLSA0", "HbScLSA1", "HbScLSA2",
                  "HbScLSA0", "HbScLSA1", "HbScLSA2"
                   ]

        imp_list = [
                  "P-AFrictionFact1", "P-AFrictionFact2", "P-AFrictionFact3",
                  "P-AFrictionFact4", "P-AFrictionFact5", "P-AFrictionFact6",
                  "P-AFrictionFact7", "P-AFrictionFact8", "P-AFrictionFact9"
                   ]

        mo_list =  [
                    "hbschInc1Au0prd", "hbschInc1Au1prd", "hbschInc1Au2prd",
                    "hbschInc2Au0prd", "hbschInc2Au1prd", "hbschInc2Au2prd",
                    "hbschInc3Au0prd", "hbschInc3Au1prd", "hbschInc3Au2prd"
                   ]

        md_list =  ["hbschatr"]

        out_list = [
                    "HbScP-AI1A0", "HbScP-AI1A1", "HbScP-AI1A2",
                    "HbScP-AI2A0", "HbScP-AI2A1", "HbScP-AI2A2",
                    "HbScP-AI3A0", "HbScP-AI3A1", "HbScP-AI3A2"
                   ]

        LambdaList = [-0.938565,-0.944464,-0.839627,-0.938565,-0.944464,-0.839627,-0.938565,-0.944464,-0.839627]





        AlphaList =  [0.0, 0.0, 0.0,
                      0.0, 0.0, 0.0,
                      0.0, 0.0, 0.0]

        GammaList =  [0.0, 0.0, 0.0,
                      0.0, 0.0, 0.0,
                      0.0, 0.0, 0.0]

        Kij = util.get_matrix_numpy(eb, "Kij_hbsch")

        Bridge_Factor = 0.75

        MChM.ImpCalc(eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, util.get_matrix_numpy(eb, "mfdistAON"), Kij, "HbScBl_BPen", Bridge_Factor)

        # Zero out the friction factor for any trips outside of the same school zone (gx ensemble)
        specs = []
        for i in range (len(imp_list)):
            # this is a bit ugly as we need to quote the matrix name in emme due to the - in the names
            mat_name='mf"'+imp_list[i]+'"'
            specs.append(util.matrix_spec(mat_name, mat_name+'*(gx(p).eq.gx(q))'))
        util.compute_matrix(specs)

        MChM.two_dim_matrix_balancing(eb, mo_list, md_list, imp_list, out_list)

#       ##############################################################################
#        ##       Calculate Demand
#       ##############################################################################

        I1A0_Dict = MChM.Calc_Demand(eb, A0_Dict, "HbScP-AI1A0")
        I1A1_Dict = MChM.Calc_Demand(eb, A1_Dict, "HbScP-AI1A1")
        I1A2_Dict = MChM.Calc_Demand(eb, A2_Dict, "HbScP-AI1A2")
        I2A0_Dict = MChM.Calc_Demand(eb, A0_Dict, "HbScP-AI2A0")
        I2A1_Dict = MChM.Calc_Demand(eb, A1_Dict, "HbScP-AI2A1")
        I2A2_Dict = MChM.Calc_Demand(eb, A2_Dict, "HbScP-AI2A2")
        I3A0_Dict = MChM.Calc_Demand(eb, A0_Dict, "HbScP-AI3A0")
        I3A1_Dict = MChM.Calc_Demand(eb, A1_Dict, "HbScP-AI3A1")
        I3A2_Dict = MChM.Calc_Demand(eb, A2_Dict, "HbScP-AI3A2")

        # Auto Trips
        HOVI1 = I1A0_Dict['HOV'][0] + I1A1_Dict['HOV'][0] + I1A2_Dict['HOV'][0]
        HOVI2 = I2A0_Dict['HOV'][0] + I2A1_Dict['HOV'][0] + I2A2_Dict['HOV'][0]
        HOVI3 = I3A0_Dict['HOV'][0] + I3A1_Dict['HOV'][0] + I3A2_Dict['HOV'][0]
        # TNC Trips
        TNCI1 = I1A0_Dict['TNC'][0] + I1A1_Dict['TNC'][0] + I1A2_Dict['TNC'][0]
        TNCI2 = I2A0_Dict['TNC'][0] + I2A1_Dict['TNC'][0] + I2A2_Dict['TNC'][0]
        TNCI3 = I3A0_Dict['TNC'][0] + I3A1_Dict['TNC'][0] + I3A2_Dict['TNC'][0]

        # Bus/Rail Trips
        Bus  =  I1A0_Dict['WTra'][0] + I1A1_Dict['WTra'][0] + I1A2_Dict['WTra'][0]
        Bus +=  I2A0_Dict['WTra'][0] + I2A1_Dict['WTra'][0] + I2A2_Dict['WTra'][0]
        Bus +=  I3A0_Dict['WTra'][0] + I3A1_Dict['WTra'][0] + I3A2_Dict['WTra'][0]
        Rail =  I1A0_Dict['WTra'][1] + I1A1_Dict['WTra'][1] + I1A2_Dict['WTra'][1]
        Rail += I2A0_Dict['WTra'][1] + I2A1_Dict['WTra'][1] + I2A2_Dict['WTra'][1]
        Rail += I3A0_Dict['WTra'][1] + I3A1_Dict['WTra'][1] + I3A2_Dict['WTra'][1]

        
        
        # Active Trips
        Walk =  I1A0_Dict['Acti'][0] + I1A1_Dict['Acti'][0] + I1A2_Dict['Acti'][0]
        Walk += I2A0_Dict['Acti'][0] + I2A1_Dict['Acti'][0] + I2A2_Dict['Acti'][0]
        Walk += I3A0_Dict['Acti'][0] + I3A1_Dict['Acti'][0] + I3A2_Dict['Acti'][0]
        Bike =  I1A0_Dict['Acti'][1] + I1A1_Dict['Acti'][1] + I1A2_Dict['Acti'][1]
        Bike += I2A0_Dict['Acti'][1] + I2A1_Dict['Acti'][1] + I2A2_Dict['Acti'][1]
        Bike += I3A0_Dict['Acti'][1] + I3A1_Dict['Acti'][1] + I3A2_Dict['Acti'][1]

        del A0_Dict,   A1_Dict,   A2_Dict
        del I1A0_Dict, I1A1_Dict, I1A2_Dict
        del I2A0_Dict, I2A1_Dict, I2A2_Dict
        del I3A0_Dict, I3A1_Dict, I3A2_Dict

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
        purp='hbsch'

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
        HOVI1_AM = HOVI1*Auto_AM_Fct_PA + HOVI1.transpose()*Auto_AM_Fct_AP  # Low Income
        HOVI1_MD = HOVI1*Auto_MD_Fct_PA + HOVI1.transpose()*Auto_MD_Fct_AP
        HOVI1_PM = HOVI1*Auto_PM_Fct_PA + HOVI1.transpose()*Auto_PM_Fct_AP

        HOVI2_AM = HOVI2*Auto_AM_Fct_PA + HOVI2.transpose()*Auto_AM_Fct_AP  # Med Income
        HOVI2_MD = HOVI2*Auto_MD_Fct_PA + HOVI2.transpose()*Auto_MD_Fct_AP
        HOVI2_PM = HOVI2*Auto_PM_Fct_PA + HOVI2.transpose()*Auto_PM_Fct_AP

        HOVI3_AM = HOVI3*Auto_AM_Fct_PA + HOVI3.transpose()*Auto_AM_Fct_AP  # High Income
        HOVI3_MD = HOVI3*Auto_MD_Fct_PA + HOVI3.transpose()*Auto_MD_Fct_AP
        HOVI3_PM = HOVI3*Auto_PM_Fct_PA + HOVI3.transpose()*Auto_PM_Fct_AP

        ## TNC Trips      #TNC*PA_Factor + TNC_transpose*AP_Factor
        TNCI1_AM = TNCI1 * Auto_AM_Fct_PA + TNCI1.transpose() * Auto_AM_Fct_AP  # Low Income
        TNCI1_MD = TNCI1 * Auto_MD_Fct_PA + TNCI1.transpose() * Auto_MD_Fct_AP
        TNCI1_PM = TNCI1 * Auto_PM_Fct_PA + TNCI1.transpose() * Auto_PM_Fct_AP

        TNCI2_AM = TNCI2 * Auto_AM_Fct_PA + TNCI2.transpose() * Auto_AM_Fct_AP  # Med Income
        TNCI2_MD = TNCI2 * Auto_MD_Fct_PA + TNCI2.transpose() * Auto_MD_Fct_AP
        TNCI2_PM = TNCI2 * Auto_PM_Fct_PA + TNCI2.transpose() * Auto_PM_Fct_AP

        TNCI3_AM = TNCI3 * Auto_AM_Fct_PA + TNCI3.transpose() * Auto_AM_Fct_AP  # High Income
        TNCI3_MD = TNCI3 * Auto_MD_Fct_PA + TNCI3.transpose() * Auto_MD_Fct_AP
        TNCI3_PM = TNCI3 * Auto_PM_Fct_PA + TNCI3.transpose() * Auto_PM_Fct_AP

        
        ## Transit Trips
        Bus_AM = Bus*Bus_AM_Fct_PA + Bus.transpose()*Bus_AM_Fct_AP
        Bus_MD = Bus*Tran_MD_Fct_PA + Bus.transpose()*Tran_MD_Fct_AP
        Bus_PM = Bus*Bus_PM_Fct_PA + Bus.transpose()*Bus_PM_Fct_AP

        Rail_AM = Rail*Rail_AM_Fct_PA + Rail.transpose()*Rail_AM_Fct_AP
        Rail_MD = Rail*Tran_MD_Fct_PA + Rail.transpose()*Tran_MD_Fct_AP
        Rail_PM = Rail*Rail_PM_Fct_PA + Rail.transpose()*Rail_PM_Fct_AP


        ## Active Trips
        Walk_AM = Walk*Acti_AM_Fct_PA + Walk.transpose()*Acti_AM_Fct_AP
        Walk_MD = Walk*Acti_MD_Fct_PA + Walk.transpose()*Acti_MD_Fct_AP
        Walk_PM = Walk*Acti_PM_Fct_PA + Walk.transpose()*Acti_PM_Fct_AP

        Bike_AM = Bike*Acti_AM_Fct_PA + Bike.transpose()*Acti_AM_Fct_AP
        Bike_MD = Bike*Acti_MD_Fct_PA + Bike.transpose()*Acti_MD_Fct_AP
        Bike_PM = Bike*Acti_PM_Fct_PA + Bike.transpose()*Acti_PM_Fct_AP

       # Convert TNC HOV to Vehicles
        HOV_TNCI1_AM = TNCI1_AM / tnc_occupancy
        HOV_TNCI2_AM = TNCI2_AM / tnc_occupancy
        HOV_TNCI3_AM = TNCI3_AM / tnc_occupancy
 
        HOV_TNCI1_MD = TNCI1_MD / tnc_occupancy
        HOV_TNCI2_MD = TNCI2_MD / tnc_occupancy
        HOV_TNCI3_MD = TNCI3_MD / tnc_occupancy
 
        HOV_TNCI1_PM = TNCI1_PM / tnc_occupancy
        HOV_TNCI2_PM = TNCI2_PM / tnc_occupancy
        HOV_TNCI3_PM = TNCI3_PM / tnc_occupancy

        # Convert HOV to Auto Drivers

        AuDr_HOVI1_AM = HOVI1_AM/Occ + HOV_TNCI1_AM
        AuDr_HOVI1_MD = HOVI1_MD/Occ + HOV_TNCI1_MD
        AuDr_HOVI1_PM = HOVI1_PM/Occ + HOV_TNCI1_PM

        AuDr_HOVI2_AM = HOVI2_AM/Occ + HOV_TNCI2_AM
        AuDr_HOVI2_MD = HOVI2_MD/Occ + HOV_TNCI2_MD
        AuDr_HOVI2_PM = HOVI2_PM/Occ + HOV_TNCI2_PM

        AuDr_HOVI3_AM = HOVI3_AM/Occ + HOV_TNCI3_AM
        AuDr_HOVI3_MD = HOVI3_MD/Occ + HOV_TNCI3_MD
        AuDr_HOVI3_PM = HOVI3_PM/Occ + HOV_TNCI3_PM

        ## add TNC matrices for empty TNC component
        util.add_matrix_numpy(eb, "TncAMVehicleTrip", HOV_TNCI1_AM)
        util.add_matrix_numpy(eb, "TncAMVehicleTrip", HOV_TNCI2_AM)
        util.add_matrix_numpy(eb, "TncAMVehicleTrip", HOV_TNCI3_AM)

        util.add_matrix_numpy(eb, "TncMDVehicleTrip", HOV_TNCI1_MD)
        util.add_matrix_numpy(eb, "TncMDVehicleTrip", HOV_TNCI2_MD)
        util.add_matrix_numpy(eb, "TncMDVehicleTrip", HOV_TNCI3_MD)

        util.add_matrix_numpy(eb, "TncPMVehicleTrip", HOV_TNCI1_PM)
        util.add_matrix_numpy(eb, "TncPMVehicleTrip", HOV_TNCI2_PM)
        util.add_matrix_numpy(eb, "TncPMVehicleTrip", HOV_TNCI3_PM)
		
        del HOV_TNCI1_AM, HOV_TNCI1_MD, HOV_TNCI1_PM
        del HOV_TNCI2_AM, HOV_TNCI2_MD, HOV_TNCI2_PM
        del HOV_TNCI3_AM, HOV_TNCI3_MD, HOV_TNCI3_PM


#       ##############################################################################
#        ##       Set Demand Matrices
#       ##############################################################################

        util.set_matrix_numpy(eb, "HbScHOVI1PerTrips", HOVI1)
        util.set_matrix_numpy(eb, "HbScHOVI2PerTrips", HOVI2)
        util.set_matrix_numpy(eb, "HbScHOVI3PerTrips", HOVI3)
        util.set_matrix_numpy(eb, "HbScTNCI1PerTrips", TNCI1)
        util.set_matrix_numpy(eb, "HbScTNCI2PerTrips", TNCI2)
        util.set_matrix_numpy(eb, "HbScTNCI3PerTrips", TNCI3)
        util.set_matrix_numpy(eb, "HbScBusPerTrips", Bus)
        util.set_matrix_numpy(eb, "HbScRailPerTrips", Rail)
        util.set_matrix_numpy(eb, "HbScWalkPerTrips", Walk)
        util.set_matrix_numpy(eb, "HbScBikePerTrips", Bike)

       # Auto-person

        # HOV
        # AM
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_1_Am", HOVI1_AM)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_1_Am", HOVI2_AM)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_1_Am", HOVI3_AM)
        # MD
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_1_Md", HOVI1_MD)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_1_Md", HOVI2_MD)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_1_Md", HOVI3_MD)
        # PM
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_1_Pm", HOVI1_PM)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_1_Pm", HOVI2_PM)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_1_Pm", HOVI3_PM)

        # TNC
        # AM
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_2_Am", TNCI1_AM)
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_3_Am", TNCI2_AM)
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_4_Am", TNCI3_AM)
        # MD
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_2_Md", TNCI1_MD)
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_3_Md", TNCI2_MD)
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_4_Md", TNCI3_MD)
        # PM
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_2_Pm", TNCI1_PM)
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_3_Pm", TNCI2_PM)
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_4_Pm", TNCI3_PM)

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
        # HOV (includes TNC)
        # AM
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_1_Am", AuDr_HOVI1_AM)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_1_Am", AuDr_HOVI2_AM)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_1_Am", AuDr_HOVI3_AM)
        # MD
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_1_Md", AuDr_HOVI1_MD)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_1_Md", AuDr_HOVI2_MD)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_1_Md", AuDr_HOVI3_MD)
        # PM
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_1_Pm", AuDr_HOVI1_PM)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_1_Pm", AuDr_HOVI2_PM)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_1_Pm", AuDr_HOVI3_PM)

        ## Dump demands to SQL Database
        # AM
        Zone_Index_O = util.get_matrix_numpy(eb, "zoneindex") + np.zeros((1, NoTAZ))
        Zone_Index_D = Zone_Index_O.transpose()

        T_HOV_AM = HOVI1_AM + HOVI2_AM + HOVI3_AM
        T_TNC_AM = TNCI1_AM + TNCI2_AM + TNCI3_AM

        # MD
        T_HOV_MD = HOVI1_MD + HOVI2_MD + HOVI3_MD
        T_TNC_MD = TNCI1_MD + TNCI2_MD + TNCI3_MD

        # PM
        T_HOV_PM = HOVI1_PM + HOVI2_PM + HOVI3_PM
        T_TNC_PM = TNCI1_PM + TNCI2_PM + TNCI3_PM

        # Daily
        T_HOV = HOVI1 + HOVI2 + HOVI3
        T_TNC = TNCI1 + TNCI2 + TNCI3

        #
        df_demand = pd.DataFrame()

        Gy_P = util.get_matrix_numpy(eb, 'gy_ensem')  + np.zeros((1, NoTAZ))
        Gy_A = Gy_P.transpose()

        df_demand['gy_i'] = Gy_P.flatten()
        df_demand['gy_j'] = Gy_A.flatten()
        df_demand.gy_i = df_demand.gy_i.astype(int)
        df_demand.gy_j = df_demand.gy_j.astype(int)
        mode_list_am_pm = ['hov', 'bus', 'rail', 'walk', 'bike', 'tnc']
        mode_list_md = ['hov', 'bus', 'rail', 'walk', 'bike', 'tnc']
        mode_list_daily = ['hov', 'bus', 'rail', 'walk', 'bike', 'tnc']

        AM_Demand_List = [T_HOV_AM, Bus_AM, Rail_AM, Walk_AM, Bike_AM, T_TNC_AM]
        MD_Demand_List = [T_HOV_MD, Bus_MD, Rail_MD, Walk_MD, Bike_MD, T_TNC_MD]
        PM_Demand_List = [T_HOV_PM, Bus_PM, Rail_PM, Walk_PM, Bike_PM, T_TNC_PM]
        Daily_Demand_List = [T_HOV, Bus, Rail, Walk, Bike, T_TNC]

        zero_demand = 0
        purp = "hbsch"

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
        util.initmat(eb, "mf9020", "HbScLSA0", " HbSc LogSum A0", 0)
        util.initmat(eb, "mf9021", "HbScLSA1", " HbSc LogSum A1", 0)
        util.initmat(eb, "mf9022", "HbScLSA2", " HbSc LogSum A2", 0)

        util.initmat(eb, "mf9320", "HbScLSAUA0", " HbSc LogSum Auto A0", 0)
        util.initmat(eb, "mf9321", "HbScLSAUA1", " HbSc LogSum Auto A1", 0)
        util.initmat(eb, "mf9322", "HbScLSAUA2", " HbSc LogSum Auto A2", 0)

        util.initmat(eb, "mf9420", "HbScLSTRA0", " HbSc LogSum Transit A0", 0)
        util.initmat(eb, "mf9421", "HbScLSTRA1", " HbSc LogSum Transit A1", 0)
        util.initmat(eb, "mf9422", "HbScLSTRA2", " HbSc LogSum Transit A2", 0)

        util.initmat(eb, "mf9520", "HbScLSACA0", " HbSc LogSum Active A0", 0)
        util.initmat(eb, "mf9521", "HbScLSACA1", " HbSc LogSum Active A1", 0)
        util.initmat(eb, "mf9522", "HbScLSACA2", " HbSc LogSum Active A2", 0)

        ## Initialze Friction Factor Matrices
        util.initmat(eb, "mf9100", "P-AFrictionFact1", "Trip Distribution Friction Factor 1", 0)
        util.initmat(eb, "mf9101", "P-AFrictionFact2", "Trip Distribution Friction Factor 2", 0)
        util.initmat(eb, "mf9102", "P-AFrictionFact3", "Trip Distribution Friction Factor 3", 0)
        util.initmat(eb, "mf9103", "P-AFrictionFact4", "Trip Distribution Friction Factor 4", 0)
        util.initmat(eb, "mf9104", "P-AFrictionFact5", "Trip Distribution Friction Factor 5", 0)
        util.initmat(eb, "mf9105", "P-AFrictionFact6", "Trip Distribution Friction Factor 6", 0)
        util.initmat(eb, "mf9106", "P-AFrictionFact7", "Trip Distribution Friction Factor 7", 0)
        util.initmat(eb, "mf9107", "P-AFrictionFact8", "Trip Distribution Friction Factor 8", 0)
        util.initmat(eb, "mf9108", "P-AFrictionFact9", "Trip Distribution Friction Factor 9", 0)

        ## Initialize P-A Trip Tables by mode
        util.initmat(eb, "mf3205", "HbScHOVI1PerTrips", "HbSc HV2+ Low Income Per-Trips", 0)
        util.initmat(eb, "mf3206", "HbScHOVI2PerTrips", "HbSc HV2+ Med Income Per-Trips", 0)
        util.initmat(eb, "mf3207", "HbScHOVI3PerTrips", "HbSc HV2+ High Income Per-Trips", 0)
        util.initmat(eb, "mf3215", "HbScBusPerTrips", "HbSc Bus Per-Trips", 0)
        util.initmat(eb, "mf3220", "HbScRailPerTrips", "HbSc Rail Per-Trips", 0)
        util.initmat(eb, "mf3230", "HbScWalkPerTrips", "HbSc Walk Per-Trips", 0)
        util.initmat(eb, "mf3235", "HbScBikePerTrips", "HbSc Bike Per-Trips", 0)
        util.initmat(eb, "mf3245", "HbScTNCI1PerTrips", "HbSc TNC Low Income Per-Trips", 0)
        util.initmat(eb, "mf3246", "HbScTNCI2PerTrips", "HbSc TNC Med Income Per-Trips", 0)
        util.initmat(eb, "mf3247", "HbScTNCI3PerTrips", "HbSc TNC High Income Per-Trips", 0)


        ## Initialize P-A Trip Tables from trip distribution
        util.initmat(eb, "mf3250", "HbScP-AI1A0", " HbSc P-A Trips I1 A0", 0)
        util.initmat(eb, "mf3251", "HbScP-AI1A1", " HbSc P-A Trips I1 A1", 0)
        util.initmat(eb, "mf3252", "HbScP-AI1A2", " HbSc P-A Trips I1 A2", 0)
        util.initmat(eb, "mf3253", "HbScP-AI2A0", " HbSc P-A Trips I1 A0", 0)
        util.initmat(eb, "mf3254", "HbScP-AI2A1", " HbSc P-A Trips I1 A1", 0)
        util.initmat(eb, "mf3255", "HbScP-AI2A2", " HbSc P-A Trips I1 A2", 0)
        util.initmat(eb, "mf3256", "HbScP-AI3A0", " HbSc P-A Trips I1 A0", 0)
        util.initmat(eb, "mf3257", "HbScP-AI3A1", " HbSc P-A Trips I1 A1", 0)
        util.initmat(eb, "mf3258", "HbScP-AI3A2", " HbSc P-A Trips I1 A2", 0)

