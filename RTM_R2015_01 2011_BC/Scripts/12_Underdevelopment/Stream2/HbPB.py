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
import traceback as _traceback

class HbPersonalBusiness(_m.Tool()):

    ##Global attribute for Tool Run Message (successful/not successful)
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Home Base Personal Business"
        pb.description = "Calculate home base work person trips by mode and time of day"
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

    @_m.logbook_trace("Run Home Base Personal Business")
    def __call__(self, eb):
        util = _m.Modeller().tool("translink.emme.util")
        MChM = _m.Modeller().tool("translink.RTM3.testtdmc.ModeChoiceUtils")
        input_path = util.get_input_path(eb)
        self.matrix_batchins(eb)
        NoTAZ = len(util.get_matrix_numpy(eb, "mo51"))

#        ##############################################################################
#        ##       Define Availability thresholds
#        ##############################################################################

        AvailDict = {
                     'AutDist': 0.0,
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
                     'PRAutTim': 0.0
                    }

        # Declare Utilities Data Frame
        DfU = {}

        # Add Coefficients
        p2 =   -3.273302
        p4 =  -12.840877
        p6 =  -11.278883
        p10 =  -6.031951
        p11 =  -9.963846
        p12 =  -0.819450
        p13 =  -0.513504
        p14 =  -0.375733
        p15 =  -0.067479
        p17 =  -0.091304
        p18 =  -0.127404
        p19 =  -1.221026
        p20 =  -3.783202
        p21 =  -3.017122
        p160 =  3.185451
        p161 =  3.906782
        p162 =  4.011569
        p163 =  4.134952
        p164 =  2.595965
        p700 =  2.489581
        p701 =  2.656500
        thet =  0.238964

#        ##############################################################################
#        ##       Auto Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        MaxPark = 10.0
        VOC = util.get_matrix_numpy(eb, 'autoOpCost')
        Occ = util.get_matrix_numpy(eb, 'HOVOccHbpb')
        Df['ParkCost'] = util.get_matrix_numpy(eb, 'prk2hr')  # 2 hour parking
        Df['ParkCost'][Df['ParkCost']>MaxPark] = MaxPark
        Df['ParkCost'] = Df['ParkCost'].reshape(1, NoTAZ) + np.zeros((NoTAZ, 1))

        Df['AutoDisSOV'] = util.get_matrix_numpy(eb, 'HbPbBlSovDist')
        Df['AutoTimSOV'] = util.get_matrix_numpy(eb, 'HbPbBlSovTime')
        Df['AutoCosSOV'] = Df['AutoDisSOV']*VOC + util.get_matrix_numpy(eb, 'HbPbBlSovToll') + Df['ParkCost']

        Df['AutoDisHOV'] = util.get_matrix_numpy(eb, 'HbPbBlHovDist')
        Df['AutoTimHOV'] = util.get_matrix_numpy(eb, 'HbPbBlHovTime')
        Df['AutoCosHOV'] = Df['AutoDisHOV']*VOC + util.get_matrix_numpy(eb, 'HbPbBlHovToll') + Df['ParkCost']

        # Utilities
        # SOV
        # SOV Utility across all incomes
        Df['GeUtl'] = ( 0
                      + p15*Df['AutoTimSOV'])

        # Check Availability conditions
        Df['GeUtl']  = MChM.AutoAvail(Df['AutoDisSOV'], Df['GeUtl'], AvailDict)
        # Add Income parameters
        DfU['SOVI1']  = Df['GeUtl'] + p12*Df['AutoCosSOV']
        DfU['SOVI2']  = Df['GeUtl'] + p13*Df['AutoCosSOV']
        DfU['SOVI3']  = Df['GeUtl'] + p14*Df['AutoCosSOV']

        # HOV2+
        # HOV2+ Utility across all incomes
        Df['GeUtl'] = ( p2
                      + p15*Df['AutoTimHOV'])
        # Check Availability conditions
        Df['GeUtl']  = MChM.AutoAvail(Df['AutoDisHOV'], Df['GeUtl'], AvailDict)
        # Add Income parameters
        DfU['HV2+I1']  = Df['GeUtl'] + p12*Df['AutoCosHOV']/Occ
        DfU['HV2+I2']  = Df['GeUtl'] + p13*Df['AutoCosHOV']/Occ
        DfU['HV2+I3']  = Df['GeUtl'] + p14*Df['AutoCosHOV']/Occ


#        ##############################################################################
#        ##       Walk to Transit Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        Tiny=0.000001
        Df['BusIVT'] = util.get_matrix_numpy(eb, 'HbPbBlBusIvtt')
        Df['BusWat'] = util.get_matrix_numpy(eb, 'HbPbBlBusWait')
        Df['BusAux'] = util.get_matrix_numpy(eb, 'HbPbBlBusAux')
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'HbPbBlBusBoard')
        Df['BusFar'] = util.get_matrix_numpy(eb, 'HbPbBlBusFare')
        Df['BusTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux'] + Df['BusBrd'] # Total Bus Travel Time

        Df['RalIVR'] = util.get_matrix_numpy(eb, 'HbPbBlRailIvtt')
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'HbPbBlRailIvttBus')
        Df['RalWat'] = util.get_matrix_numpy(eb, 'HbPbBlRailWait')
        Df['RalAux'] = util.get_matrix_numpy(eb, 'HbPbBlRailAux')
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'HbPbBlRailBoard')
        Df['RalFar'] = util.get_matrix_numpy(eb, 'HbPbBlRailFare')
        Df['RalTot'] = Df['RalIVB'] + Df['RalIVR'] + Df['RalWat'] + Df['RalAux'] + Df['RalBrd'] # Total Bus Travel Time
        Df['RalIBR'] = Df['RalIVB']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Bus IVT to Total Time
        Df['RalIRR'] = Df['RalIVR']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Rail IVT to Total Time

        Df['IntZnl'] = np.identity(NoTAZ)
        Df['PopEmpDen'] = util.get_matrix_numpy(eb, 'popdens') + util.get_matrix_numpy(eb, 'empdens') # Pop + Emp Density
        Df['PopEmpDen'] = Df['PopEmpDen'].reshape(NoTAZ, 1) + np.zeros((1, NoTAZ))
        Df['PopEmpDen'][Df['PopEmpDen']<1.0] = 1.0
        Df['PopEmpDen'] = np.log(Df['PopEmpDen']) # Log Pop+Emp Density




        # Utilities
        # Bus Utility
        # Bus Utility across all incomes
        Df['GeUtl'] = ( p4
                      + p15*Df['BusIVT']
                      + p17*Df['BusWat']
                      + p18*Df['BusAux']
                      + p19*Df['BusBrd']
                      + p700*Df['PopEmpDen'])

        # Check Availability conditions
        Df['GeUtl'] = MChM.BusAvail(Df, Df['GeUtl'], AvailDict)
        # Add Income parameters
        DfU['BusI1'] = Df['GeUtl'] + p12*Df['BusFar']
        DfU['BusI2'] = Df['GeUtl'] + p13*Df['BusFar']
        DfU['BusI3'] = Df['GeUtl'] + p14*Df['BusFar']

        # Rail Utility
        # Rail Utility across all incomes
        Df['GeUtl'] = ( p4*Df['RalIBR']
                      + p6*Df['RalIRR']
                      + p15*Df['RalIVB']
                      + p15*Df['RalIVR']
                      + p17*Df['RalWat']
                      + p18*Df['RalAux']
                      + p19*Df['RalBrd']
                      + p700*Df['PopEmpDen'])
        # Check Availability conditions
        Df['GeUtl'] = MChM.RailAvail(Df, Df['GeUtl'],AvailDict)
        # Add Income parameters
        DfU['RalI1'] = Df['GeUtl'] + p12*Df['RalFar']
        DfU['RalI2'] = Df['GeUtl'] + p13*Df['RalFar']
        DfU['RalI3'] = Df['GeUtl'] + p14*Df['RalFar']

#        ##############################################################################
#        ##       Active Modes
#        ##############################################################################

        Df = {}
        Df['AutoDis'] = util.get_matrix_numpy(eb, 'HbPbBlSovDist')

        Df['PopEmpDen'] = util.get_matrix_numpy(eb, 'popdens') + util.get_matrix_numpy(eb, 'empdens') # Pop + Emp Density
        Df['PopEmpDen'] = Df['PopEmpDen'].reshape(NoTAZ, 1) + np.zeros((1, NoTAZ))
        Df['PopEmpDen'][Df['PopEmpDen']<1.0] = 1.0
        Df['PopEmpDen'] = np.log(Df['PopEmpDen']) # Log Pop+Emp Density

        # Walk Utility
        DfU['Walk'] = ( p10
                      + p20*Df['AutoDis']
                      + p701*Df['PopEmpDen'])
        # Check Availability conditions
        DfU['Walk'] = MChM.WalkAvail(Df['AutoDis'], DfU['Walk'], AvailDict)

        # Bike Utility
        DfU['Bike'] = ( p11
                      + p21*Df['AutoDis']
                      + p701*Df['PopEmpDen'])


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
               'HOV'  : [DfU['HV2+I1']],
               'WTra' : [DfU['BusI1'] + p164, DfU['RalI1'] + p164],  # Zero car households additional transit bias term
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }

        I1A0_Dict = self.Calc_Prob(eb, Dict, "HbPbLSI1A0", thet)

        ## Low Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI1'] + p160], # One car households additional SOV bias term
               'HOV'  : [DfU['HV2+I1'] + p162], # One car households additional HOV bias term
               'WTra' : [DfU['BusI1'], DfU['RalI1']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I1A1_Dict = self.Calc_Prob(eb, Dict, "HbPbLSI1A1", thet)

        ## Low Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI1'] + p161], # One car households additional SOV bias term
               'HOV'  : [DfU['HV2+I1'] + p163], # One car households additional HOV bias term
               'WTra' : [DfU['BusI1'], DfU['RalI1']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I1A2_Dict = self.Calc_Prob(eb, Dict, "HbPbLSI1A2", thet)

        ############
        # Med Income
        ############

        ## Med Income Zero Autos
        Dict = {
               'SOV'  : [np.where(CarShare>0, DfU['SOVI2'], LrgU)],
               'HOV'  : [DfU['HV2+I2']],
               'WTra' : [DfU['BusI2'] + p164, DfU['RalI2'] + p164],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }

        I2A0_Dict = self.Calc_Prob(eb, Dict, "HbPbLSI2A0", thet)

        ## Med Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI2'] + p160],
               'HOV'  : [DfU['HV2+I2'] + p162],
               'WTra' : [DfU['BusI2'], DfU['RalI2']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I2A1_Dict = self.Calc_Prob(eb, Dict, "HbPbLSI2A1", thet)

        ## Med Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI2'] + p161],
               'HOV'  : [DfU['HV2+I2'] + p163],
               'WTra' : [DfU['BusI2'], DfU['RalI2']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I2A2_Dict = self.Calc_Prob(eb, Dict, "HbPbLSI2A2", thet)

        #############
        # High Income
        #############

        ## High Income Zero Autos
        Dict = {
               'SOV'  : [np.where(CarShare>0, DfU['SOVI3'], LrgU)],
               'HOV'  : [DfU['HV2+I3']],
               'WTra' : [DfU['BusI3'] + p164, DfU['RalI3'] + p164],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I3A0_Dict = self.Calc_Prob(eb, Dict, "HbPbLSI3A0", thet)

        ## High Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI3'] + p160],
               'HOV'  : [DfU['HV2+I3'] + p162],
               'WTra' : [DfU['BusI3'], DfU['RalI3']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I3A1_Dict = self.Calc_Prob(eb, Dict, "HbPbLSI3A1", thet)

        ## High Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI3'] + p161],
               'HOV'  : [DfU['HV2+I3'] + p163],
               'WTra' : [DfU['BusI3'], DfU['RalI3']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I3A2_Dict = self.Calc_Prob(eb, Dict, "HbPbLSI3A2", thet)

        del DfU, Dict
#
#       ##############################################################################
#        ##       Trip Distribution
#       ##############################################################################

        Logsum =  [
                  "HbPbLSI1A0", "HbPbLSI1A1", "HbPbLSI1A2",
                  "HbPbLSI2A0", "HbPbLSI2A1", "HbPbLSI2A2",
                  "HbPbLSI3A0", "HbPbLSI3A1", "HbPbLSI3A2",
                   ]

        imp_list = [
                  "P-AFrictionFact1", "P-AFrictionFact2", "P-AFrictionFact3",
                  "P-AFrictionFact4", "P-AFrictionFact5", "P-AFrictionFact6",
                  "P-AFrictionFact7", "P-AFrictionFact8", "P-AFrictionFact9"
                   ]

        mo_list =  [
                    "hbpbInc1Au0prd", "hbpbInc1Au1prd", "hbpbInc1Au2prd",
                    "hbpbInc2Au0prd", "hbpbInc2Au1prd", "hbpbInc2Au2prd",
                    "hbpbInc3Au0prd", "hbpbInc3Au1prd", "hbpbInc3Au2prd"
                   ]

        md_list =  ["hbpbatr"]

        out_list = [
                    "HbPbP-AI1A0", "HbPbP-AI1A1", "HbPbP-AI1A2",
                    "HbPbP-AI2A0", "HbPbP-AI2A1", "HbPbP-AI2A2",
                    "HbPbP-AI3A0", "HbPbP-AI3A1", "HbPbP-AI3A2"
                   ]

        LS_Coeff = 0.5

        LambdaList = [-0.2, -0.2, -0.2,
                      -0.2, -0.2, -0.2,
                      -0.2, -0.2, -0.2]

        AlphaList =  [0.02, 0.02, 0.02,
                      0.02, 0.02, 0.02,
                      0.02, 0.02, 0.02]

        GammaList =  [-0.0004, -0.0004, -0.0004,
                      -0.0004, -0.0004, -0.0004,
                      -0.0004, -0.0004, -0.0004]

        Dist_Iter = int(util.get_matrix_numpy(eb, 'IterDist'))
        MChM.ImpCalc(eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, util.get_matrix_numpy(eb, "HbPbBlSovDist"))
        MChM.two_dim_matrix_balancing(eb, mo_list, md_list, imp_list, out_list, Dist_Iter)


#       ##############################################################################
#        ##       Calculate Demand
#       ##############################################################################

        I1A0_Dict = self.Calc_Demand(I1A0_Dict, util.get_matrix_numpy(eb,"HbPbP-AI1A0"))
        I1A1_Dict = self.Calc_Demand(I1A1_Dict, util.get_matrix_numpy(eb,"HbPbP-AI1A1"))
        I1A2_Dict = self.Calc_Demand(I1A2_Dict, util.get_matrix_numpy(eb,"HbPbP-AI1A2"))
        I2A0_Dict = self.Calc_Demand(I2A0_Dict, util.get_matrix_numpy(eb,"HbPbP-AI2A0"))
        I2A1_Dict = self.Calc_Demand(I2A1_Dict, util.get_matrix_numpy(eb,"HbPbP-AI2A1"))
        I2A2_Dict = self.Calc_Demand(I2A2_Dict, util.get_matrix_numpy(eb,"HbPbP-AI2A2"))
        I3A0_Dict = self.Calc_Demand(I3A0_Dict, util.get_matrix_numpy(eb,"HbPbP-AI3A0"))
        I3A1_Dict = self.Calc_Demand(I3A1_Dict, util.get_matrix_numpy(eb,"HbPbP-AI3A1"))
        I3A2_Dict = self.Calc_Demand(I3A2_Dict, util.get_matrix_numpy(eb,"HbPbP-AI3A2"))

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
#        ##       Set Demand Matrices
#       ##############################################################################
        util.set_matrix_numpy(eb, "HbPbSOVI1PerTrips", SOVI1)
        util.set_matrix_numpy(eb, "HbPbSOVI2PerTrips", SOVI2)
        util.set_matrix_numpy(eb, "HbPbSOVI3PerTrips", SOVI3)
        util.set_matrix_numpy(eb, "HbPbHV2+I1PerTrips", HOVI1)
        util.set_matrix_numpy(eb, "HbPbHV2+I2PerTrips", HOVI2)
        util.set_matrix_numpy(eb, "HbPbHV2+I3PerTrips", HOVI3)
        util.set_matrix_numpy(eb, "HbPbBusPerTrips", Bus)
        util.set_matrix_numpy(eb, "HbPbRailPerTrips", Rail)
        util.set_matrix_numpy(eb, "HbPbWalkPerTrips", Walk)
        util.set_matrix_numpy(eb, "HbPbBikePerTrips", Bike)


    def Calc_Prob(self, eb, Dict, Logsum, Th):
        util = _m.Modeller().tool("translink.emme.util")

        Tiny =  0.000000001
        L_Nst = {key:sum(np.exp(nest))
                      for key,nest in Dict.items()}

        U_Nst  = {key:pow(nest,Th)
                      for key,nest in L_Nst.items()}

        F_Utl = sum(U_Nst.values())
        F_Utl = np.where(F_Utl ==0, Tiny, F_Utl)
        util.set_matrix_numpy(eb, Logsum, np.log(F_Utl))

        Prob_Dict = {key:np.where(L_Nst[key] == 0, 0, np.exp(nest)/L_Nst[key])*U_Nst[key]/F_Utl
                        for key, nest in Dict.items()}
        return Prob_Dict

    def Calc_Demand(self, Dict, Dem):
        util = _m.Modeller().tool("translink.emme.util")

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
        util = _m.Modeller().tool("translink.emme.util")

        ## Initialze Logsum Matrices
        util.initmat(eb, "mf9040", "HbPbLSI1A0", " HbPb LogSum I1 A0", 0)
        util.initmat(eb, "mf9041", "HbPbLSI1A1", " HbPb LogSum I1 A1", 0)
        util.initmat(eb, "mf9042", "HbPbLSI1A2", " HbPb LogSum I1 A2", 0)
        util.initmat(eb, "mf9043", "HbPbLSI2A0", " HbPb LogSum I1 A0", 0)
        util.initmat(eb, "mf9044", "HbPbLSI2A1", " HbPb LogSum I1 A1", 0)
        util.initmat(eb, "mf9045", "HbPbLSI2A2", " HbPb LogSum I1 A2", 0)
        util.initmat(eb, "mf9046", "HbPbLSI3A0", " HbPb LogSum I1 A0", 0)
        util.initmat(eb, "mf9047", "HbPbLSI3A1", " HbPb LogSum I1 A1", 0)
        util.initmat(eb, "mf9048", "HbPbLSI3A2", " HbPb LogSum I1 A2", 0)


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
        util.initmat(eb, "mf3400", "HbPbSOVI1PerTrips", "HbPb SOV Low Income Per-Trips", 0)
        util.initmat(eb, "mf3401", "HbPbSOVI2PerTrips", "HbPb SOV Med Income Per-Trips", 0)
        util.initmat(eb, "mf3402", "HbPbSOVI3PerTrips", "HbPb SOV High Income Per-Trips", 0)
        util.initmat(eb, "mf3405", "HbPbHV2+I1PerTrips", "HbPb HV2+ Low Income Per-Trips", 0)
        util.initmat(eb, "mf3406", "HbPbHV2+I2PerTrips", "HbPb HV2+ Med Income Per-Trips", 0)
        util.initmat(eb, "mf3407", "HbPbHV2+I3PerTrips", "HbPb HV2+ High Income Per-Trips", 0)
        util.initmat(eb, "mf3415", "HbPbBusPerTrips", "HbPb Bus Per-Trips", 0)
        util.initmat(eb, "mf3420", "HbPbRailPerTrips", "HbPb Rail Per-Trips", 0)
        util.initmat(eb, "mf3430", "HbPbWalkPerTrips", "HbPb Walk Per-Trips", 0)
        util.initmat(eb, "mf3435", "HbPbBikePerTrips", "HbPb Bike Per-Trips", 0)

        ## Initialize P-A Trip Tables from trip distribution
        util.initmat(eb, "mf3450", "HbPbP-AI1A0", " HbPb P-A Trips I1 A0", 0)
        util.initmat(eb, "mf3451", "HbPbP-AI1A1", " HbPb P-A Trips I1 A1", 0)
        util.initmat(eb, "mf3452", "HbPbP-AI1A2", " HbPb P-A Trips I1 A2", 0)
        util.initmat(eb, "mf3453", "HbPbP-AI2A0", " HbPb P-A Trips I1 A0", 0)
        util.initmat(eb, "mf3454", "HbPbP-AI2A1", " HbPb P-A Trips I1 A1", 0)
        util.initmat(eb, "mf3455", "HbPbP-AI2A2", " HbPb P-A Trips I1 A2", 0)
        util.initmat(eb, "mf3456", "HbPbP-AI3A0", " HbPb P-A Trips I1 A0", 0)
        util.initmat(eb, "mf3457", "HbPbP-AI3A1", " HbPb P-A Trips I1 A1", 0)
        util.initmat(eb, "mf3458", "HbPbP-AI3A2", " HbPb P-A Trips I1 A2", 0)


