##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage2.hbescorting
##--Purpose:
##---------------------------------------------------------------------
import inro.modeller as _m
import numpy as np
import pandas as pd

class HbEscorting(_m.Tool()):

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Home Base Escorting"
        pb.description = "Calculate home base escorting person trips by mode and time of day"
        pb.branding_text = "TransLink"
        pb.runnable = False
        return pb.render()

    @_m.logbook_trace("Run Home Base Escorting")
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
                     'BikDist': 10.0,
                     'TranIVT': 1.0,
                     'TranWat': 20.0,
                     'TranAux': 30.0,
                     'WCEWat' : 30.0,
                     'WCEAux' : 40.0,
                     'TranBrd': 4.0,
                     'BRTotLow': 10.0,
                     'BRTotHig': 90.0,
                     'WCTotLow': 30.0,
                     'WCTotHig': 130.0,
                     'PRAutTim': 0.0,
                     'br_ratio': 2.0,
                     'r_time'  : 20.0
                    }

        # Declare Utilities Data Frame
        DfU = {}

        # Add Coefficients

        p4   =-4.120999
        p6   =-0.863372
        p10  = 2.387704
        p11  =-1.471055
        p12  =-0.399781
        p20  =-2.483381
        p21  =-1.769784
        p160 = 1.028527
        p161 = 2.731352
        p164 = 4.789199
        thet = 0.500000


#        ##############################################################################
#        ##       Auto Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        MaxPark = 10.0
        Hov_scale = 0.70
        VOT = 10.0

        Occ = util.get_matrix_numpy(eb, 'AutoOccHbesc') # Occupancy across SOV and HOV

        Df['AutoCosHOV'] = util.get_matrix_numpy(eb, 'HbEsBlHovCost')
        Df['AutoTimHOV'] = util.get_matrix_numpy(eb, 'HbEsBlHovTime')
        Df['AutoTotCosHOV'] = Df['AutoCosHOV']
        Df['GenCostAuto']= Df['AutoTotCosHOV']/(pow(Occ,Hov_scale)) + VOT*Df['AutoTimHOV']/60.0

        # Utilities
        # Auto
        # Auto Utility across all incomes
        DfU['Auto'] = ( 0
                      + p12*Df['GenCostAuto'])


#        ##############################################################################
#        ##       Walk to Transit Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        Tiny=0.000001
        B_IVT_perc = 1.06

        Df['BusIVT'] = util.get_matrix_numpy(eb, 'HbEsBlBusIvtt')
        Df['BusWat'] = util.get_matrix_numpy(eb, 'HbEsBlBusWait')
        Df['BusAux'] = util.get_matrix_numpy(eb, 'HbEsBlBusAux')
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'HbEsBlBusBoard')
        Df['BusFar'] = util.get_matrix_numpy(eb, 'HbEsBlBusFare')
        Df['BusTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux']  # Total Bus Travel Time

        Df['RalIVR'] = util.get_matrix_numpy(eb, 'HbEsBlRailIvtt')
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'HbEsBlRailIvttBus')
        Df['RalWat'] = util.get_matrix_numpy(eb, 'HbEsBlRailWait')
        Df['RalAux'] = util.get_matrix_numpy(eb, 'HbEsBlRailAux')
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'HbEsBlRailBoard')
        Df['RalFar'] = util.get_matrix_numpy(eb, 'HbEsBlRailFare')
        Df['RalTot'] = Df['RalIVB'] + Df['RalIVR'] + Df['RalWat'] + Df['RalAux'] # Total Bus Travel Time
        Df['RalIBR'] = Df['RalIVB']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Bus IVT to Total Time
        Df['RalIRR'] = Df['RalIVR']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Rail IVT to Total Time

        Df['IntZnl'] = np.identity(NoTAZ)

        Df['GenCostBus'] = ( Df['BusIVT']*B_IVT_perc
                           + 1.92*Df['BusWat']
                           + 1.71*Df['BusAux']
                           + 10.81*Df['BusBrd'])

        Df['GenCostBus'] = VOT*Df['GenCostBus']/60.0 + Df['BusFar']

        Df['GenCostRal'] = ( Df['RalIVR']
                           + Df['RalIVB']*B_IVT_perc
                           + 2.03*Df['RalWat']
                           + 1.80*Df['RalAux']
                           + 11.80*Df['RalBrd'])

        Df['GenCostRal'] = VOT*Df['GenCostRal']/60.0 + Df['RalFar']


        # Utilities
        # Bus Utility
        # Bus Utility across all incomes
        Df['GeUtl'] = ( p4
                      + p12*Df['GenCostBus'])

        # Check Availability conditions
        Df['GeUtl'] = MChM.BusAvail(Df, Df['GeUtl'], AvailDict)

        DfU['Bus'] = Df['GeUtl']

        # Rail Utility
        # Rail Utility across all incomes
        Df['GeUtl'] = ( p4*Df['RalIBR']
                      + p6*Df['RalIRR']
                      + p12*Df['GenCostRal'])
        # Check Availability conditions
        Df['GeUtl'] = MChM.RailAvail(Df, Df['GeUtl'],AvailDict)
        # Add Income parameters
        DfU['Ral'] = Df['GeUtl']

#        ##############################################################################
#        ##       Active Modes
#        ##############################################################################

        Df = {}
        Df['AutoDis'] = util.get_matrix_numpy(eb, "mfdistAON") # Distance


        # Walk Utility
        DfU['Walk'] = ( p10
                      + p20*Df['AutoDis'])

        # Check Availability conditions
        DfU['Walk'] = MChM.WalkAvail(Df['AutoDis'], DfU['Walk'], AvailDict)

        # Bike Utility
        DfU['Bike'] = ( p11
                      + p21*Df['AutoDis'])

        # Check Availability conditions
        DfU['Bike'] = MChM.BikeAvail(Df['AutoDis'], DfU['Bike'], AvailDict)

        del Df

#        ##############################################################################
#        ##       Calculate Probabilities
#        ##############################################################################

        #############
        # All Incomes
        #############

        ## Zero Autos
        Dict = {
               'Auto'  : [DfU['Auto']],
               'WTra' : [DfU['Bus'] + p164, DfU['Ral'] + p164],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }

        A0_Dict = self.Calc_Prob(eb, Dict, "HbEsLSA0", thet)

        ## One Auto
        Dict = {
               'Auto'  : [DfU['Auto'] + p160],
               'WTra' : [DfU['Bus'], DfU['Ral']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }

        A1_Dict = self.Calc_Prob(eb, Dict, "HbEsLSA1", thet)

        ## Two Auto
        Dict = {
               'Auto'  : [DfU['Auto'] + p161],
               'WTra' : [DfU['Bus'], DfU['Ral']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }

        A2_Dict = self.Calc_Prob(eb, Dict, "HbEsLSA2", thet)

#
#       ##############################################################################
#        ##       Trip Distribution
#       ##############################################################################

        Logsum =  [
                  "HbEsLSA0", "HbEsLSA1", "HbEsLSA2",
                  "HbEsLSA0", "HbEsLSA1", "HbEsLSA2",
                  "HbEsLSA0", "HbEsLSA1", "HbEsLSA2"
                   ]

        imp_list = [
                  "P-AFrictionFact1", "P-AFrictionFact2", "P-AFrictionFact3",
                  "P-AFrictionFact4", "P-AFrictionFact5", "P-AFrictionFact6",
                  "P-AFrictionFact7", "P-AFrictionFact8", "P-AFrictionFact9"
                   ]

        mo_list =  [
                    "hbescInc1Au0prd", "hbescInc1Au1prd", "hbescInc1Au2prd",
                    "hbescInc2Au0prd", "hbescInc2Au1prd", "hbescInc2Au2prd",
                    "hbescInc3Au0prd", "hbescInc3Au1prd", "hbescInc3Au2prd"
                   ]

        md_list =  ["hbescatr"]

        out_list = [
                    "HbEsP-AI1A0", "HbEsP-AI1A1", "HbEsP-AI1A2",
                    "HbEsP-AI2A0", "HbEsP-AI2A1", "HbEsP-AI2A2",
                    "HbEsP-AI3A0", "HbEsP-AI3A1", "HbEsP-AI3A2"
                   ]

        LS_Coeff = 0.2

        LambdaList = [-0.406931,-0.386407,-0.391416,-0.406931,-0.386407,-0.391416,-0.406931,-0.386407,-0.391416]




        AlphaList =  [0,0,0,0,0,0,0,0,0]


        GammaList =  [0,0,0,0,0,0,0,0,0]

        Kij = util.get_matrix_numpy(eb, "Kij_hbesc")

        Bridge_Factor = 0.5

        MChM.ImpCalc(eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, util.get_matrix_numpy(eb, "mfdistAON"), Kij, "HbEsBl_BPen", Bridge_Factor)
        MChM.two_dim_matrix_balancing(eb, mo_list, md_list, imp_list, out_list)


#       ##############################################################################
#        ##       Calculate Demand
#       ##############################################################################

        I1A0_Dict = self.Calc_Demand(A0_Dict, util.get_matrix_numpy(eb,"HbEsP-AI1A0"))
        I1A1_Dict = self.Calc_Demand(A1_Dict, util.get_matrix_numpy(eb,"HbEsP-AI1A1"))
        I1A2_Dict = self.Calc_Demand(A2_Dict, util.get_matrix_numpy(eb,"HbEsP-AI1A2"))
        I2A0_Dict = self.Calc_Demand(A0_Dict, util.get_matrix_numpy(eb,"HbEsP-AI2A0"))
        I2A1_Dict = self.Calc_Demand(A1_Dict, util.get_matrix_numpy(eb,"HbEsP-AI2A1"))
        I2A2_Dict = self.Calc_Demand(A2_Dict, util.get_matrix_numpy(eb,"HbEsP-AI2A2"))
        I3A0_Dict = self.Calc_Demand(A0_Dict, util.get_matrix_numpy(eb,"HbEsP-AI3A0"))
        I3A1_Dict = self.Calc_Demand(A1_Dict, util.get_matrix_numpy(eb,"HbEsP-AI3A1"))
        I3A2_Dict = self.Calc_Demand(A2_Dict, util.get_matrix_numpy(eb,"HbEsP-AI3A2"))

        # Auto Trips
        AutoI1 = I1A0_Dict['Auto'][0] + I1A1_Dict['Auto'][0] + I1A2_Dict['Auto'][0]
        AutoI2 = I2A0_Dict['Auto'][0] + I2A1_Dict['Auto'][0] + I2A2_Dict['Auto'][0]
        AutoI3 = I3A0_Dict['Auto'][0] + I3A1_Dict['Auto'][0] + I3A2_Dict['Auto'][0]

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

        min_val=0.000143
        purp='hbesc'

        # setup for hbw auto time slice matrices
        conn = util.get_rtm_db(eb)
        ts_uw = pd.read_sql("SELECT * FROM timeSlicingFactorsGb", conn)
        conn.close()

        # build basic ij mat with gb for production end and internal or external gb for attraction
        df_mats = util.get_ijensem_df(eb, ensem_o = 'gb')
        df_mats['IX'] = np.where(df_mats['gb_i']==df_mats['gb_j'], 'I', 'X')

        Auto_AM_Fct_PA = MChM.ts_mat(df_mats, ts_uw, min_val, purp, 'AM', 'PtoA', NoTAZ)
        Auto_MD_Fct_PA = MChM.ts_mat(df_mats, ts_uw, min_val, purp, 'MD', 'PtoA', NoTAZ)
        Auto_PM_Fct_PA = MChM.ts_mat(df_mats, ts_uw, min_val, purp, 'PM', 'PtoA', NoTAZ)

        Auto_AM_Fct_AP = MChM.ts_mat(df_mats, ts_uw, min_val, purp, 'AM', 'AtoP', NoTAZ)
        Auto_MD_Fct_AP = MChM.ts_mat(df_mats, ts_uw, min_val, purp, 'MD', 'AtoP', NoTAZ)
        Auto_PM_Fct_AP = MChM.ts_mat(df_mats, ts_uw, min_val, purp, 'PM', 'AtoP', NoTAZ)

        Tran_AM_Fct_PA, Tran_AM_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Transit',peakperiod='AM', geo='A',minimum_value=min_val)
        Tran_MD_Fct_PA, Tran_MD_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Transit',peakperiod='MD', geo='A',minimum_value=min_val)
        Tran_PM_Fct_PA, Tran_PM_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Transit',peakperiod='PM', geo='A',minimum_value=min_val)

        Acti_AM_Fct_PA, Acti_AM_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Active',peakperiod='AM', geo='A',minimum_value=min_val)
        Acti_MD_Fct_PA, Acti_MD_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Active',peakperiod='MD', geo='A',minimum_value=min_val)
        Acti_PM_Fct_PA, Acti_PM_Fct_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Active',peakperiod='PM', geo='A',minimum_value=min_val)

      ##########################################################################################
       ##       Calculate peak hour O-D person trips and final 24 hour P-A Trips
      ##########################################################################################

        # Get split between SOV and HOV trips
        SOV_Split =  util.get_matrix_numpy(eb, 'sov_pct_Hbesc')
        # HOV-specific occumancy
        HOcc = util.get_matrix_numpy(eb, 'HOVOccHbesc')

        SOVI1 = AutoI1*SOV_Split
        HOVI1 = AutoI1 - SOVI1

        SOVI2 = AutoI2*SOV_Split
        HOVI2 = AutoI2 - SOVI2

        SOVI3 = AutoI3*SOV_Split
        HOVI3 = AutoI3 - SOVI3

      ## SOV Trips      #SOV*PA_Factor + SOV_transpose*AP_Factor
        SOVI1_AM = SOVI1*Auto_AM_Fct_PA + SOVI1.transpose()*Auto_AM_Fct_AP  # Low Income
        SOVI1_MD = SOVI1*Auto_MD_Fct_PA + SOVI1.transpose()*Auto_MD_Fct_AP
        SOVI1_PM = SOVI1*Auto_PM_Fct_PA + SOVI1.transpose()*Auto_PM_Fct_AP

        SOVI2_AM = SOVI2*Auto_AM_Fct_PA + SOVI2.transpose()*Auto_AM_Fct_AP  # Med Income
        SOVI2_MD = SOVI2*Auto_MD_Fct_PA + SOVI2.transpose()*Auto_MD_Fct_AP
        SOVI2_PM = SOVI2*Auto_PM_Fct_PA + SOVI2.transpose()*Auto_PM_Fct_AP

        SOVI3_AM = SOVI3*Auto_AM_Fct_PA + SOVI3.transpose()*Auto_AM_Fct_AP  # High Income
        SOVI3_MD = SOVI3*Auto_MD_Fct_PA + SOVI3.transpose()*Auto_MD_Fct_AP
        SOVI3_PM = SOVI3*Auto_PM_Fct_PA + SOVI3.transpose()*Auto_PM_Fct_AP



        HOVI1_AM = HOVI1*Auto_AM_Fct_PA + HOVI1.transpose()*Auto_AM_Fct_AP  # Low Income
        HOVI1_MD = HOVI1*Auto_MD_Fct_PA + HOVI1.transpose()*Auto_MD_Fct_AP
        HOVI1_PM = HOVI1*Auto_PM_Fct_PA + HOVI1.transpose()*Auto_PM_Fct_AP

        HOVI2_AM = HOVI2*Auto_AM_Fct_PA + HOVI2.transpose()*Auto_AM_Fct_AP  # Med Income
        HOVI2_MD = HOVI2*Auto_MD_Fct_PA + HOVI2.transpose()*Auto_MD_Fct_AP
        HOVI2_PM = HOVI2*Auto_PM_Fct_PA + HOVI2.transpose()*Auto_PM_Fct_AP

        HOVI3_AM = HOVI3*Auto_AM_Fct_PA + HOVI3.transpose()*Auto_AM_Fct_AP  # High Income
        HOVI3_MD = HOVI3*Auto_MD_Fct_PA + HOVI3.transpose()*Auto_MD_Fct_AP
        HOVI3_PM = HOVI3*Auto_PM_Fct_PA + HOVI3.transpose()*Auto_PM_Fct_AP


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

        AuDr_HOVI1_AM = HOVI1_AM/HOcc
        AuDr_HOVI1_MD = HOVI1_MD/HOcc
        AuDr_HOVI1_PM = HOVI1_PM/HOcc

        AuDr_HOVI2_AM = HOVI2_AM/HOcc
        AuDr_HOVI2_MD = HOVI2_MD/HOcc
        AuDr_HOVI2_PM = HOVI2_PM/HOcc

        AuDr_HOVI3_AM = HOVI3_AM/HOcc
        AuDr_HOVI3_MD = HOVI3_MD/HOcc
        AuDr_HOVI3_PM = HOVI3_PM/HOcc


#       ##############################################################################
#        ##       Set Demand Matrices
#       ##############################################################################
        util.set_matrix_numpy(eb, "HbEsSOVI1PerTrips", SOVI1)
        util.set_matrix_numpy(eb, "HbEsSOVI2PerTrips", SOVI2)
        util.set_matrix_numpy(eb, "HbEsSOVI3PerTrips", SOVI3)
        util.set_matrix_numpy(eb, "HbEsHOVI1PerTrips", HOVI1)
        util.set_matrix_numpy(eb, "HbEsHOVI2PerTrips", HOVI2)
        util.set_matrix_numpy(eb, "HbEsHOVI3PerTrips", HOVI3)


        util.set_matrix_numpy(eb, "HbEsBusPerTrips", Bus)
        util.set_matrix_numpy(eb, "HbEsRailPerTrips", Rail)
        util.set_matrix_numpy(eb, "HbEsWalkPerTrips", Walk)
        util.set_matrix_numpy(eb, "HbEsBikePerTrips", Bike)

        # SOV
        # AM
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_2_Am", SOVI1_AM)
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_2_Am", SOVI2_AM)
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_2_Am", SOVI3_AM)
        # MD
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_2_Md", SOVI1_MD)
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_2_Md", SOVI2_MD)
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_2_Md", SOVI3_MD)
        # PM
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_2_Pm", SOVI1_PM)
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_2_Pm", SOVI2_PM)
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_2_Pm", SOVI3_PM)

        # HOV
        # AM
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_2_Am", HOVI1_AM)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_2_Am", HOVI2_AM)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_2_Am", HOVI3_AM)
        # MD
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_2_Md", HOVI1_MD)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_2_Md", HOVI2_MD)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_2_Md", HOVI3_MD)
        # PM
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_2_Pm", HOVI1_PM)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_2_Pm", HOVI2_PM)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_2_Pm", HOVI3_PM)

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
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_2_Am", SOVI1_AM)
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_2_Am", SOVI2_AM)
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_2_Am", SOVI3_AM)
        # MD
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_2_Md", SOVI1_MD)
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_2_Md", SOVI2_MD)
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_2_Md", SOVI3_MD)
        # PM
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_2_Pm", SOVI1_PM)
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_2_Pm", SOVI2_PM)
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_2_Pm", SOVI3_PM)


        # HOV
        # AM
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_2_Am", AuDr_HOVI1_AM)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_2_Am", AuDr_HOVI2_AM)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_2_Am", AuDr_HOVI3_AM)
        # MD
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_2_Md", AuDr_HOVI1_MD)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_2_Md", AuDr_HOVI2_MD)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_2_Md", AuDr_HOVI3_MD)
        # PM
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_2_Pm", AuDr_HOVI1_PM)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_2_Pm", AuDr_HOVI2_PM)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_2_Pm", AuDr_HOVI3_PM)

        ## Dump demands to SQL Database
        # AM
        Zone_Index_O = util.get_matrix_numpy(eb, "zoneindex") + np.zeros((1, NoTAZ))
        Zone_Index_D = Zone_Index_O.transpose()

        T_SOV_AM = np.where((Zone_Index_O>9999) & (Zone_Index_D>9999), SOVI1_AM + SOVI2_AM + SOVI3_AM, 0)
        T_HOV_AM = HOVI1_AM + HOVI2_AM + HOVI3_AM

        # MD
        T_SOV_MD = np.where((Zone_Index_O>9999) & (Zone_Index_D>9999), SOVI1_MD + SOVI2_MD + SOVI3_MD, 0)
        T_HOV_MD = HOVI1_MD + HOVI2_MD + HOVI3_MD

        # PM
        T_SOV_PM = np.where((Zone_Index_O>9999) & (Zone_Index_D>9999), SOVI1_PM + SOVI2_PM + SOVI3_PM, 0)
        T_HOV_PM = HOVI1_PM + HOVI2_PM + HOVI3_PM

        # Daily
        T_SOV = np.where((Zone_Index_O>9999) & (Zone_Index_D>9999), SOVI1 + SOVI2 + SOVI3, 0)
        T_HOV = HOVI1 + HOVI2 + HOVI3

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

        AM_Demand_List = [T_SOV_AM, T_HOV_AM, Bus_AM, Rail_AM, Walk_AM, Bike_AM]
        MD_Demand_List = [T_SOV_MD, T_HOV_MD, Bus_MD, Rail_MD, Walk_MD, Bike_MD]
        PM_Demand_List = [T_SOV_PM, T_HOV_PM, Bus_PM, Rail_PM, Walk_PM, Bike_PM]
        Daily_Demand_List = [T_SOV, T_HOV, Bus, Rail, Walk, Bike]

        zero_demand = 0
        purp = "hbesc"

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

        del Auto_AM_Fct_PA, Auto_MD_Fct_PA, Auto_PM_Fct_PA, Auto_AM_Fct_AP, Auto_MD_Fct_AP, Auto_PM_Fct_AP

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
        util.initmat(eb, "mf9060", "HbEsLSA0", " HbEs LogSum A0", 0)
        util.initmat(eb, "mf9061", "HbEsLSA1", " HbEs LogSum A1", 0)
        util.initmat(eb, "mf9062", "HbEsLSA2", " HbEs LogSum A2", 0)

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
        util.initmat(eb, "mf3600", "HbEsSOVI1PerTrips", "HbEs SOV Low Income Per-Trips", 0)
        util.initmat(eb, "mf3601", "HbEsSOVI2PerTrips", "HbEs SOV Med Income Per-Trips", 0)
        util.initmat(eb, "mf3602", "HbEsSOVI3PerTrips", "HbEs SOV High Income Per-Trips", 0)
        util.initmat(eb, "mf3605", "HbEsHOVI1PerTrips", "HbEs HOV Low Income Per-Trips", 0)
        util.initmat(eb, "mf3606", "HbEsHOVI2PerTrips", "HbEs HOV Med Income Per-Trips", 0)
        util.initmat(eb, "mf3607", "HbEsHOVI3PerTrips", "HbEs HOV High Income Per-Trips", 0)
        util.initmat(eb, "mf3615", "HbEsBusPerTrips", "HbEs Bus Per-Trips", 0)
        util.initmat(eb, "mf3620", "HbEsRailPerTrips", "HbEs Rail Per-Trips", 0)
        util.initmat(eb, "mf3630", "HbEsWalkPerTrips", "HbEs Walk Per-Trips", 0)
        util.initmat(eb, "mf3635", "HbEsBikePerTrips", "HbEs Bike Per-Trips", 0)

        ## Initialize P-A Trip Tables from trip distribution
#        util.initmat(eb, "mf3650", "HbEsP-AI1A0", " HbEs P-A Trips I1 A0", 0)
#        util.initmat(eb, "mf3651", "HbEsP-AI1A1", " HbEs P-A Trips I1 A1", 0)
#        util.initmat(eb, "mf3652", "HbEsP-AI1A2", " HbEs P-A Trips I1 A2", 0)
#        util.initmat(eb, "mf3653", "HbEsP-AI2A0", " HbEs P-A Trips I1 A0", 0)
#        util.initmat(eb, "mf3654", "HbEsP-AI2A1", " HbEs P-A Trips I1 A1", 0)
#        util.initmat(eb, "mf3655", "HbEsP-AI2A2", " HbEs P-A Trips I1 A2", 0)
#        util.initmat(eb, "mf3656", "HbEsP-AI3A0", " HbEs P-A Trips I1 A0", 0)
#        util.initmat(eb, "mf3657", "HbEsP-AI3A1", " HbEs P-A Trips I1 A1", 0)
#        util.initmat(eb, "mf3658", "HbEsP-AI3A2", " HbEs P-A Trips I1 A2", 0)
