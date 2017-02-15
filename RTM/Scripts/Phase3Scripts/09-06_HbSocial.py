##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage2.hbsocial
##--Purpose:
##---------------------------------------------------------------------
import inro.modeller as _m
import csv
import os
import numpy as np
import pandas as pd
import sqlite3

class HbSoc(_m.Tool()):

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Home Base Social Recreation"
        pb.description = "Calculate home base Social Recreation person trips by mode and time of day"
        pb.branding_text = "TransLink"
        pb.runnable = False
        return pb.render()

    @_m.logbook_trace("Run Home Base Social Recreation")
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
                     'AutCost' : 0.0,
                     'WlkDist' : 5.0,
                     'BikDist' : 10.0,
                     'TranIVT' : 1.0,
                     'TranWat' : 20.0,
                     'TranAux' : 30.0,
                     'WCEWat'  : 30.0,
                     'WCEAux'  : 40.0,
                     'TranBrd' : 4.0,
                     'BRTotLow': 10.0,
                     'BRTotHig': 120.0,
                     'WCTotLow': 30.0,
                     'WCTotHig': 130.0,
                     'PRAutTim': 0.0
                    }

        # Declare Utilities Data Frame
        DfU = {}

        # Add Coefficients
        p2   =   2.204905
        p4   =  -2.407282
        p6   =  -0.363680
        p10  =   3.062157
        p11  =  -2.029603
        p12  =  -0.335491
        p13  =  -0.142971
        p15  =  -0.049536
        p17  =  -0.115394
        p18  =  -0.155784
        p19  =  -0.775042
        p20  =  -1.960462
        p21  =  -1.037444
        p160 =   4.974279
        p161 =   6.053567
        p162 =   2.892778
        p163 =   4.452698
        p164 =   1.358995
        p602 =   0.811588
        p701 =   1.286440
        p870 =   0.322948
        thet =   0.474270

#        ##############################################################################
#        ##       Auto Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        MaxPark = 10.0

        Occ = util.get_matrix_numpy(eb, 'HOVOccHBsoc')
        Df['ParkCost'] = util.get_matrix_numpy(eb, 'prk2hr')  # 2 hour parking

        Df['ParkCost'] = Df['ParkCost'].reshape(1, NoTAZ) + np.zeros((NoTAZ, 1))

        # Get SOV Skims by income
        # Low Income
        Df['AutoCosSOV1'] = util.get_matrix_numpy(eb, 'HbSoBlSovCost_I1') #SOV Cost
        Df['AutoTimSOV1'] = util.get_matrix_numpy(eb, 'HbSoBlSovTime_I1') #SOV Time
        Df['AutoTotCosSOV1'] = Df['AutoCosSOV1'] + Df['ParkCost'] #SOV Cost (per km + Toll + Parking)

        # Med Income
        Df['AutoCosSOV2'] = util.get_matrix_numpy(eb, 'HbSoBlSovCost_I2') #SOV Cost
        Df['AutoTimSOV2'] = util.get_matrix_numpy(eb, 'HbSoBlSovTime_I2') #SOV Time
        Df['AutoTotCosSOV2'] = Df['AutoCosSOV2'] + Df['ParkCost'] #SOV Cost (per km + Toll + Parking)

        # High Income
        Df['AutoCosSOV3'] = util.get_matrix_numpy(eb, 'HbSoBlSovCost_I3') #SOV Cost
        Df['AutoTimSOV3'] = util.get_matrix_numpy(eb, 'HbSoBlSovTime_I3') #SOV Time
        Df['AutoTotCosSOV3'] = Df['AutoCosSOV3'] + Df['ParkCost'] #SOV Cost (per km + Toll + Parking)

        # Get HOV Skims by income
        # Low Income
        Df['AutoCosHOV1'] = util.get_matrix_numpy(eb, 'HbSoBlHovCost_I1') #HOV Cost
        Df['AutoTimHOV1'] = util.get_matrix_numpy(eb, 'HbSoBlHovTime_I1') #HOV Time
        Df['AutoTotCosHOV1'] = Df['AutoCosHOV1'] + Df['ParkCost'] #HOV Cost (per km + Toll + Parking)

        # Med Income
        Df['AutoCosHOV2'] = util.get_matrix_numpy(eb, 'HbSoBlHovCost_I2') #HOV Cost
        Df['AutoTimHOV2'] = util.get_matrix_numpy(eb, 'HbSoBlHovTime_I2') #HOV Time
        Df['AutoTotCosHOV2'] = Df['AutoCosHOV2'] + Df['ParkCost'] #HOV Cost (per km + Toll + Parking)

        # High Income
        Df['AutoCosHOV3'] = util.get_matrix_numpy(eb, 'HbSoBlHovCost_I3') #HOV Cost
        Df['AutoTimHOV3'] = util.get_matrix_numpy(eb, 'HbSoBlHovTime_I3') #HOV Time
        Df['AutoTotCosHOV3'] = Df['AutoCosHOV3'] + Df['ParkCost'] #HOV Cost (per km + Toll + Parking)

        # Utilities
        # SOV

        Df['SOVI1'] = ( 0
                      + p15*Df['AutoTimSOV1']
                      + p12*Df['AutoTotCosSOV1'])
        Df['SOVI2'] = ( 0
                      + p15*Df['AutoTimSOV2']
                      + p13*Df['AutoTotCosSOV2'])
        Df['SOVI3'] = ( 0
                      + p15*Df['AutoTimSOV3']
                      + p13*Df['AutoTotCosSOV3'])


        DfU['SOVI1']  = MChM.AutoAvail(Df['AutoCosSOV1'], Df['SOVI1'], AvailDict) #Check Availability condition if mode not available then set to high negative utility (-99999)
        DfU['SOVI2']  = MChM.AutoAvail(Df['AutoCosSOV2'], Df['SOVI2'], AvailDict)
        DfU['SOVI3']  = MChM.AutoAvail(Df['AutoCosSOV3'], Df['SOVI3'], AvailDict)

        # HOV

        Df['HOVI1'] = ( p2
                      + p15*Df['AutoTimHOV1']
                      + p12*Df['AutoTotCosHOV1']/Occ)


        Df['HOVI2'] = ( p2
                      + p15*Df['AutoTimHOV2']
                      + p13*Df['AutoTotCosHOV2']/Occ)


        Df['HOVI3'] = ( p2
                      + p15*Df['AutoTimHOV3']
                      + p13*Df['AutoTotCosHOV3']/Occ)

        DfU['HOVI1']  = MChM.AutoAvail(Df['AutoCosHOV1'], Df['HOVI1'], AvailDict) #Check Availability condition if mode not available then set to high negative utility (-99999)
        DfU['HOVI2']  = MChM.AutoAvail(Df['AutoCosHOV2'], Df['HOVI2'], AvailDict)
        DfU['HOVI3']  = MChM.AutoAvail(Df['AutoCosHOV3'], Df['HOVI3'], AvailDict)


#        ##############################################################################
#        ##       Walk to Transit Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        Tiny=0.000001
        Df['BusIVT'] = util.get_matrix_numpy(eb, 'HbSoBlBusIvtt')
        Df['BusWat'] = util.get_matrix_numpy(eb, 'HbSoBlBusWait')
        Df['BusAux'] = util.get_matrix_numpy(eb, 'HbSoBlBusAux')
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'HbSoBlBusBoard')
        Df['BusFar'] = util.get_matrix_numpy(eb, 'HbSoBlBusFare')
        Df['BusTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux'] + Df['BusBrd'] # Total Bus Travel Time

        Df['RalIVR'] = util.get_matrix_numpy(eb, 'HbSoBlRailIvtt')
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'HbSoBlRailIvttBus')
        Df['RalWat'] = util.get_matrix_numpy(eb, 'HbSoBlRailWait')
        Df['RalAux'] = util.get_matrix_numpy(eb, 'HbSoBlRailAux')
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'HbSoBlRailBoard')
        Df['RalFar'] = util.get_matrix_numpy(eb, 'HbSoBlRailFare')
        Df['RalTot'] = Df['RalIVB'] + Df['RalIVR'] + Df['RalWat'] + Df['RalAux'] + Df['RalBrd'] # Total Bus Travel Time
        Df['RalIBR'] = Df['RalIVB']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Bus IVT to Total Time
        Df['RalIRR'] = Df['RalIVR']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Rail IVT to Total Time
        Df['SocAccess'] = util.get_matrix_numpy(eb, 'socAccLn').reshape(NoTAZ,1) + np.zeros((1, NoTAZ)) # Log transit accessiblity broadcast

        Df['IntZnl'] = np.identity(NoTAZ)

        # Utilities
        # Bus Utility
        # Bus Utility across all incomes
        Df['GeUtl'] = ( p4
                      + p15*Df['BusIVT']
                      + p17*Df['BusWat']
                      + p18*Df['BusAux']
                      + p19*Df['BusBrd']
                      + p602*Df['SocAccess'])

        # Check Availability conditions
        Df['GeUtl'] = MChM.BusAvail(Df, Df['GeUtl'], AvailDict)
        # Add Income parameters
        DfU['BusI1'] = Df['GeUtl'] + p12*Df['BusFar']
        DfU['BusI2'] = Df['GeUtl'] + p13*Df['BusFar']
        DfU['BusI3'] = Df['GeUtl'] + p13*Df['BusFar']

        # Rail Utility
        # Rail Utility across all incomes
        Df['GeUtl'] = ( p4* Df['RalIBR']
                      + p6* Df['RalIRR']
                      + p15*Df['RalIVB']
                      + p15*Df['RalIVR']
                      + p17*Df['RalWat']
                      + p18*Df['RalAux']
                      + p19*Df['RalBrd']
                      + p602*Df['SocAccess'])

        # Check Availability conditions
        Df['GeUtl'] = MChM.RailAvail(Df, Df['GeUtl'],AvailDict)
        # Add Income parameters
        DfU['RalI1'] = Df['GeUtl'] + p12*Df['RalFar']
        DfU['RalI2'] = Df['GeUtl'] + p13*Df['RalFar']
        DfU['RalI3'] = Df['GeUtl'] + p13*Df['RalFar']

#        ##############################################################################
#        ##       Active Modes
#        ##############################################################################

        Df = {}
        Df['AutoDis'] = util.get_matrix_numpy(eb, "mfdistAON") # Distance

        Df['PopEmpDen'] = util.get_matrix_numpy(eb, 'combinedensln')
        Df['PopEmpDen'] = Df['PopEmpDen'].reshape(NoTAZ, 1) + np.zeros((1, NoTAZ))
        Df['BikScr'] = util.get_matrix_numpy(eb, 'bikeskim')

        # Walk Utility
        DfU['Walk'] = ( p10
                      + p20*Df['AutoDis']
                      + p701*Df['PopEmpDen'])
        # Check Availability conditions
        DfU['Walk'] = MChM.WalkAvail(Df['AutoDis'], DfU['Walk'], AvailDict)

        # Bike Utility
        DfU['Bike'] = ( p11
                      + p21*Df['AutoDis']
                      + p701*Df['PopEmpDen']
                      + p870*Df['BikScr'])

        # Check Availability conditions
        DfU['Bike'] = MChM.BikeAvail(Df['AutoDis'], DfU['Bike'], AvailDict)

        del Df

#        ##############################################################################
#        ##       Calculate Probabilities
#        ##############################################################################

        ############
        # Low Income
        ############

        ## Add SOV Availability car share term for households with zero vehicles

        CarShare = util.get_matrix_numpy(eb, 'cs500').reshape(NoTAZ,1) + np.zeros((1, NoTAZ))
        LrgU     = -99999.0
        ## Low Income Zero Autos
        Dict = {
               'SOV'  : [np.where(CarShare>0, DfU['SOVI1'], LrgU)],
               'HOV'  : [DfU['HOVI1']],
               'WTra' : [DfU['BusI1'] + p164, DfU['RalI1'] + p164],  # Zero car households additional transit bias term
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }

        I1A0_Dict = self.Calc_Prob(eb, Dict, "HbSoLSI1A0", thet)

        ## Low Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI1'] + p160], # One car households additional SOV bias term
               'HOV'  : [DfU['HOVI1'] + p162], # One car households additional HOV bias term
               'WTra' : [DfU['BusI1'], DfU['RalI1']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I1A1_Dict = self.Calc_Prob(eb, Dict, "HbSoLSI1A1", thet)

        ## Low Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI1'] + p161], # One car households additional SOV bias term
               'HOV'  : [DfU['HOVI1'] + p163], # One car households additional HOV bias term
               'WTra' : [DfU['BusI1'], DfU['RalI1']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I1A2_Dict = self.Calc_Prob(eb, Dict, "HbSoLSI1A2", thet)

        ############
        # Med Income
        ############

        ## Med Income Zero Autos
        Dict = {
               'SOV'  : [np.where(CarShare>0, DfU['SOVI2'], LrgU)],
               'HOV'  : [DfU['HOVI2']],
               'WTra' : [DfU['BusI2'] + p164, DfU['RalI2'] + p164],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }

        I2A0_Dict = self.Calc_Prob(eb, Dict, "HbSoLSI2A0", thet)

        ## Med Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI2'] + p160],
               'HOV'  : [DfU['HOVI2'] + p162],
               'WTra' : [DfU['BusI2'], DfU['RalI2']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I2A1_Dict = self.Calc_Prob(eb, Dict, "HbSoLSI2A1", thet)

        ## Med Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI2'] + p161],
               'HOV'  : [DfU['HOVI2'] + p163],
               'WTra' : [DfU['BusI2'], DfU['RalI2']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I2A2_Dict = self.Calc_Prob(eb, Dict, "HbSoLSI2A2", thet)

        #############
        # High Income
        #############

        ## High Income Zero Autos
        Dict = {
               'SOV'  : [np.where(CarShare>0, DfU['SOVI3'], LrgU)],
               'HOV'  : [DfU['HOVI3']],
               'WTra' : [DfU['BusI3'] + p164, DfU['RalI3'] + p164],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I3A0_Dict = self.Calc_Prob(eb, Dict, "HbSoLSI3A0", thet)

        ## High Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI3'] + p160],
               'HOV'  : [DfU['HOVI3'] + p162],
               'WTra' : [DfU['BusI3'], DfU['RalI3']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I3A1_Dict = self.Calc_Prob(eb, Dict, "HbSoLSI3A1", thet)

        ## High Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI3'] + p161],
               'HOV'  : [DfU['HOVI3'] + p163],
               'WTra' : [DfU['BusI3'], DfU['RalI3']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I3A2_Dict = self.Calc_Prob(eb, Dict, "HbSoLSI3A2", thet)

        del DfU, Dict

       ##############################################################################
        ##       Trip Distribution
       ##############################################################################

        Logsum =  [
                  "HbSoLSI1A0", "HbSoLSI1A1", "HbSoLSI1A2",
                  "HbSoLSI2A0", "HbSoLSI2A1", "HbSoLSI2A2",
                  "HbSoLSI3A0", "HbSoLSI3A1", "HbSoLSI3A2",
                   ]

        imp_list = [
                  "P-AFrictionFact1", "P-AFrictionFact2", "P-AFrictionFact3",
                  "P-AFrictionFact4", "P-AFrictionFact5", "P-AFrictionFact6",
                  "P-AFrictionFact7", "P-AFrictionFact8", "P-AFrictionFact9"
                   ]

        mo_list =  [
                    "hbsocInc1Au0prd", "hbsocInc1Au1prd", "hbsocInc1Au2prd",
                    "hbsocInc2Au0prd", "hbsocInc2Au1prd", "hbsocInc2Au2prd",
                    "hbsocInc3Au0prd", "hbsocInc3Au1prd", "hbsocInc3Au2prd"
                   ]

        md_list =  ["hbsocatr"]

        out_list = [
                    "HbSoP-AI1A0", "HbSoP-AI1A1", "HbSoP-AI1A2",
                    "HbSoP-AI2A0", "HbSoP-AI2A1", "HbSoP-AI2A2",
                    "HbSoP-AI3A0", "HbSoP-AI3A1", "HbSoP-AI3A2"
                   ]

        LS_Coeff = 0.8

        LambdaList = [-0.213941,-0.24621,-0.247044,-0.213941,-0.24621,-0.247044,-0.213941,-0.24621,-0.247044]



        AlphaList =  [0.003977,0.00433,0.003793,0.003977,0.00433,0.003793,0.003977,0.00433,0.003793]



        GammaList =  [-0.000045,-0.000052,-0.000037,-0.000045,-0.000052,-0.000037,-0.000045,-0.000052,-0.000037]

        Kij = util.get_matrix_numpy(eb, "Kij_hbsoc")

        Bridge_Factor = 0.75

        MChM.ImpCalc(eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, util.get_matrix_numpy(eb, "mfdistAON"), Kij, "HbSoBl_BPen", Bridge_Factor)
        MChM.one_dim_matrix_balancing(eb, mo_list, md_list, imp_list, out_list)

#       ##############################################################################
#        ##       Calculate Demand
#       ##############################################################################

        I1A0_Dict = self.Calc_Demand(I1A0_Dict, util.get_matrix_numpy(eb,"HbSoP-AI1A0"))
        I1A1_Dict = self.Calc_Demand(I1A1_Dict, util.get_matrix_numpy(eb,"HbSoP-AI1A1"))
        I1A2_Dict = self.Calc_Demand(I1A2_Dict, util.get_matrix_numpy(eb,"HbSoP-AI1A2"))
        I2A0_Dict = self.Calc_Demand(I2A0_Dict, util.get_matrix_numpy(eb,"HbSoP-AI2A0"))
        I2A1_Dict = self.Calc_Demand(I2A1_Dict, util.get_matrix_numpy(eb,"HbSoP-AI2A1"))
        I2A2_Dict = self.Calc_Demand(I2A2_Dict, util.get_matrix_numpy(eb,"HbSoP-AI2A2"))
        I3A0_Dict = self.Calc_Demand(I3A0_Dict, util.get_matrix_numpy(eb,"HbSoP-AI3A0"))
        I3A1_Dict = self.Calc_Demand(I3A1_Dict, util.get_matrix_numpy(eb,"HbSoP-AI3A1"))
        I3A2_Dict = self.Calc_Demand(I3A2_Dict, util.get_matrix_numpy(eb,"HbSoP-AI3A2"))

        # SOV Trips
        SOVI1 = I1A0_Dict['SOV'][0] + I1A1_Dict['SOV'][0] + I1A2_Dict['SOV'][0]
        SOVI2 = I2A0_Dict['SOV'][0] + I2A1_Dict['SOV'][0] + I2A2_Dict['SOV'][0]
        SOVI3 = I3A0_Dict['SOV'][0] + I3A1_Dict['SOV'][0] + I3A2_Dict['SOV'][0]

        # HOV Trips
        HOVI1 = I1A0_Dict['HOV'][0] + I1A1_Dict['HOV'][0] + I1A2_Dict['HOV'][0]
        HOVI2 = I2A0_Dict['HOV'][0] + I2A1_Dict['HOV'][0] + I2A2_Dict['HOV'][0]
        HOVI3 = I3A0_Dict['HOV'][0] + I3A1_Dict['HOV'][0] + I3A2_Dict['HOV'][0]
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


        del I1A0_Dict, I1A1_Dict, I1A2_Dict
        del I2A0_Dict, I2A1_Dict, I2A2_Dict
        del I3A0_Dict, I3A1_Dict, I3A2_Dict

#       ##############################################################################
#        ##       Get Time Slice Factors
#       ##############################################################################

        min_val=0.000143
        purp='hbsoc'

        db_loc = util.get_eb_path(eb)
        db_path = os.path.join(db_loc, 'rtm.db')
        conn = sqlite3.connect(db_path)

        # setup for hbw auto time slice matrices
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

        AuDr_HOVI1_AM = HOVI1_AM/Occ
        AuDr_HOVI1_MD = HOVI1_MD/Occ
        AuDr_HOVI1_PM = HOVI1_PM/Occ

        AuDr_HOVI2_AM = HOVI2_AM/Occ
        AuDr_HOVI2_MD = HOVI2_MD/Occ
        AuDr_HOVI2_PM = HOVI2_PM/Occ

        AuDr_HOVI3_AM = HOVI3_AM/Occ
        AuDr_HOVI3_MD = HOVI3_MD/Occ
        AuDr_HOVI3_PM = HOVI3_PM/Occ


#       ##############################################################################
#        ##       Set Demand Matrices
#       ##############################################################################
        util.set_matrix_numpy(eb, "HbSoSOVI1PerTrips", SOVI1)
        util.set_matrix_numpy(eb, "HbSoSOVI2PerTrips", SOVI2)
        util.set_matrix_numpy(eb, "HbSoSOVI3PerTrips", SOVI3)
        util.set_matrix_numpy(eb, "HbSoHOVI1PerTrips", HOVI1)
        util.set_matrix_numpy(eb, "HbSoHOVI2PerTrips", HOVI2)
        util.set_matrix_numpy(eb, "HbSoHOVI3PerTrips", HOVI3)
        util.set_matrix_numpy(eb, "HbSoBusPerTrips", Bus)
        util.set_matrix_numpy(eb, "HbSoRailPerTrips", Rail)
        util.set_matrix_numpy(eb, "HbSoWalkPerTrips", Walk)
        util.set_matrix_numpy(eb, "HbSoBikePerTrips", Bike)


        # SOV
        # AM
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_2_Am", SOVI1_AM)
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_3_Am", SOVI2_AM)
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_4_Am", SOVI3_AM)
        # MD
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_2_Md", SOVI1_MD)
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_3_Md", SOVI2_MD)
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_4_Md", SOVI3_MD)
        # PM
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_2_Pm", SOVI1_PM)
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_3_Pm", SOVI2_PM)
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_4_Pm", SOVI3_PM)

        # HOV
        # AM
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_2_Am", HOVI1_AM)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_3_Am", HOVI2_AM)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_4_Am", HOVI3_AM)
        # MD
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_2_Md", HOVI1_MD)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_3_Md", HOVI2_MD)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_4_Md", HOVI3_MD)
        # PM
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_2_Pm", HOVI1_PM)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_3_Pm", HOVI2_PM)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_4_Pm", HOVI3_PM)

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
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_3_Am", SOVI2_AM)
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_4_Am", SOVI3_AM)
        # MD
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_2_Md", SOVI1_MD)
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_3_Md", SOVI2_MD)
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_4_Md", SOVI3_MD)
        # PM
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_2_Pm", SOVI1_PM)
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_3_Pm", SOVI2_PM)
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_4_Pm", SOVI3_PM)


        # HOV
        # AM
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_2_Am", AuDr_HOVI1_AM)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_3_Am", AuDr_HOVI2_AM)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_4_Am", AuDr_HOVI3_AM)
        # MD
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_2_Md", AuDr_HOVI1_MD)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_3_Md", AuDr_HOVI2_MD)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_4_Md", AuDr_HOVI3_MD)
        # PM
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_2_Pm", AuDr_HOVI1_PM)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_3_Pm", AuDr_HOVI2_PM)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_4_Pm", AuDr_HOVI3_PM)

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
        purp = "hbsoc"

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
        util.initmat(eb, "mf9050", "HbSoLSI1A0", "LogSum HbSo I1 A0", 0)
        util.initmat(eb, "mf9051", "HbSoLSI1A1", "LogSum HbSo I1 A1", 0)
        util.initmat(eb, "mf9052", "HbSoLSI1A2", "LogSum HbSo I1 A2", 0)
        util.initmat(eb, "mf9053", "HbSoLSI2A0", "LogSum HbSo I2 A0", 0)
        util.initmat(eb, "mf9054", "HbSoLSI2A1", "LogSum HbSo I2 A1", 0)
        util.initmat(eb, "mf9055", "HbSoLSI2A2", "LogSum HbSo I2 A2", 0)
        util.initmat(eb, "mf9056", "HbSoLSI3A0", "LogSum HbSo I3 A0", 0)
        util.initmat(eb, "mf9057", "HbSoLSI3A1", "LogSum HbSo I3 A1", 0)
        util.initmat(eb, "mf9058", "HbSoLSI3A2", "LogSum HbSo I3 A2", 0)

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
        util.initmat(eb, "mf3500", "HbSoSOVI1PerTrips", "HbSo SOV Low Income Per-Trips", 0)
        util.initmat(eb, "mf3501", "HbSoSOVI2PerTrips", "HbSo SOV Med Income Per-Trips", 0)
        util.initmat(eb, "mf3502", "HbSoSOVI3PerTrips", "HbSo SOV High Income Per-Trips", 0)
        util.initmat(eb, "mf3505", "HbSoHOVI1PerTrips", "HbSo HOV Low Income Per-Trips", 0)
        util.initmat(eb, "mf3506", "HbSoHOVI2PerTrips", "HbSo HOV Med Income Per-Trips", 0)
        util.initmat(eb, "mf3507", "HbSoHOVI3PerTrips", "HbSo HOV High Income Per-Trips", 0)
        util.initmat(eb, "mf3515", "HbSoBusPerTrips",  "HbSo Bus Per-Trips", 0)
        util.initmat(eb, "mf3520", "HbSoRailPerTrips", "HbSo Rail Per-Trips", 0)
        util.initmat(eb, "mf3530", "HbSoWalkPerTrips", "HbSo Walk Per-Trips", 0)
        util.initmat(eb, "mf3535", "HbSoBikePerTrips", "HbSo Bike Per-Trips", 0)


        ## Initialize P-A Trip Tables from trip distribution
        util.initmat(eb, "mf3550", "HbSoP-AI1A0", " HbSo P-A Trips I1 A0", 0)
        util.initmat(eb, "mf3551", "HbSoP-AI1A1", " HbSo P-A Trips I1 A1", 0)
        util.initmat(eb, "mf3552", "HbSoP-AI1A2", " HbSo P-A Trips I1 A2", 0)
        util.initmat(eb, "mf3553", "HbSoP-AI2A0", " HbSo P-A Trips I1 A0", 0)
        util.initmat(eb, "mf3554", "HbSoP-AI2A1", " HbSo P-A Trips I1 A1", 0)
        util.initmat(eb, "mf3555", "HbSoP-AI2A2", " HbSo P-A Trips I1 A2", 0)
        util.initmat(eb, "mf3556", "HbSoP-AI3A0", " HbSo P-A Trips I1 A0", 0)
        util.initmat(eb, "mf3557", "HbSoP-AI3A1", " HbSo P-A Trips I1 A1", 0)
        util.initmat(eb, "mf3558", "HbSoP-AI3A2", " HbSo P-A Trips I1 A2", 0)
