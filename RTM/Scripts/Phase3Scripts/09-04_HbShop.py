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

class HbWork(_m.Tool()):

    ##Global attribute for Tool Run Message (successful/not successful)
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Home Base Shopping"
        pb.description = "Calculate home base shopping person trips by mode and time of day"
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

    @_m.logbook_trace("Run Home Base Shopping")
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
                     'BRTotHig': 120.0,
                     'WCTotLow': 30.0,
                     'WCTotHig': 130.0,
                     'PRAutTim': 0.0
                    }

        # Declare Utilities Data Frame
        DfU = {}

        # Add Coefficients

        p2   =  0.651542
        p4   =  7.472637
        p6   =  8.593067
        p10  =  7.111678
        p11  =  1.562356
        p12  = -0.706036
        p14  = -0.310116
        p15  = -0.081328
        p17  = -0.139302
        p18  = -0.179677
        p19  = -0.741140
        p20  = -2.911105
        p21  = -1.981457
        p160 =  7.477510
        p161 =  9.651366
        p162 =  5.286841
        p163 =  7.572595
        p164 =  2.300508
        p701 =  0.882130
        p870 =  0.432030
        thet =  0.343018


#        ##############################################################################
#        ##       Auto Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        MaxPark = 10.0

        Occ = util.get_matrix_numpy(eb, 'HOVOccHBshop')
        Df['ParkCost'] = util.get_matrix_numpy(eb, 'prk2hr')  # 2 hour parking
        Df['ParkCost'] = Df['ParkCost'].reshape(1, NoTAZ) + np.zeros((NoTAZ, 1))

        # Get SOV Skims by income
        # Low Income
        Df['AutoCosSOV1'] = util.get_matrix_numpy(eb, 'HbShBlSovCost_I1') #SOV Cost
        Df['AutoTimSOV1'] = util.get_matrix_numpy(eb, 'HbShBlSovTime_I1') #SOV Time
        Df['AutoTotCosSOV1'] = Df['AutoCosSOV1'] + Df['ParkCost'] #SOV Cost (per km + Toll + Parking)

        # Med Income
        Df['AutoCosSOV2'] = util.get_matrix_numpy(eb, 'HbShBlSovCost_I2') #SOV Cost
        Df['AutoTimSOV2'] = util.get_matrix_numpy(eb, 'HbShBlSovTime_I2') #SOV Time
        Df['AutoTotCosSOV2'] = Df['AutoCosSOV2'] + Df['ParkCost'] #SOV Cost (per km + Toll + Parking)

        # High Income
        Df['AutoCosSOV3'] = util.get_matrix_numpy(eb, 'HbShBlSovCost_I3') #SOV Cost
        Df['AutoTimSOV3'] = util.get_matrix_numpy(eb, 'HbShBlSovTime_I3') #SOV Time
        Df['AutoTotCosSOV3'] = Df['AutoCosSOV3']+ Df['ParkCost'] #SOV Cost (per km + Toll + Parking)

        # Get HOV Skims by income
        # Low Income
        Df['AutoCosHOV1'] = util.get_matrix_numpy(eb, 'HbShBlHovCost_I1') #HOV Cost
        Df['AutoTimHOV1'] = util.get_matrix_numpy(eb, 'HbShBlHovTime_I1') #HOV Time
        Df['AutoTotCosHOV1'] = Df['AutoCosHOV1'] + Df['ParkCost'] #HOV Cost (per km + Toll + Parking)

        # Med Income
        Df['AutoCosHOV2'] = util.get_matrix_numpy(eb, 'HbShBlHovCost_I2') #HOV Cost
        Df['AutoTimHOV2'] = util.get_matrix_numpy(eb, 'HbShBlHovTime_I2') #HOV Time
        Df['AutoTotCosHOV2'] = Df['AutoCosHOV2'] + Df['ParkCost'] #HOV Cost (per km + Toll + Parking)

        # High Income
        Df['AutoCosHOV3'] = util.get_matrix_numpy(eb, 'HbShBlHovCost_I3') #HOV Cost
        Df['AutoTimHOV3'] = util.get_matrix_numpy(eb, 'HbShBlHovTime_I3') #HOV Time
        Df['AutoTotCosHOV3'] = Df['AutoCosHOV3'] + Df['ParkCost'] #HOV Cost (per km + Toll + Parking)

        # Utilities
        # SOV

        Df['SOVI1'] = ( 0
                      + p15*Df['AutoTimSOV1']
                      + p12*Df['AutoTotCosSOV1'])
        Df['SOVI2'] = ( 0
                      + p15*Df['AutoTimSOV2']
                      + p12*Df['AutoTotCosSOV2'])
        Df['SOVI3'] = ( 0
                      + p15*Df['AutoTimSOV3']
                      + p14*Df['AutoTotCosSOV3'])


        DfU['SOVI1']  = MChM.AutoAvail(Df['AutoCosSOV1'], Df['SOVI1'], AvailDict) #Check Availability condition if mode not available then set to high negative utility (-99999)
        DfU['SOVI2']  = MChM.AutoAvail(Df['AutoCosSOV2'], Df['SOVI2'], AvailDict)
        DfU['SOVI3']  = MChM.AutoAvail(Df['AutoCosSOV3'], Df['SOVI3'], AvailDict)

        # HOV

        Df['HOVI1'] = ( p2
                      + p15*Df['AutoTimHOV1']
                      + p12*Df['AutoTotCosHOV1']/Occ)


        Df['HOVI2'] = ( p2
                      + p15*Df['AutoTimHOV2']
                      + p12*Df['AutoTotCosHOV2']/Occ)


        Df['HOVI3'] = ( p2
                      + p15*Df['AutoTimHOV3']
                      + p14*Df['AutoTotCosHOV3']/Occ)

        DfU['HOVI1']  = MChM.AutoAvail(Df['AutoCosHOV1'], Df['HOVI1'], AvailDict) #Check Availability condition if mode not available then set to high negative utility (-99999)
        DfU['HOVI2']  = MChM.AutoAvail(Df['AutoCosHOV2'], Df['HOVI2'], AvailDict)
        DfU['HOVI3']  = MChM.AutoAvail(Df['AutoCosHOV3'], Df['HOVI3'], AvailDict)

#        ##############################################################################
#        ##       Walk to Transit Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        Tiny=0.000001
        Df['BusIVT'] = util.get_matrix_numpy(eb, 'HbShBlBusIvtt')
        Df['BusWat'] = util.get_matrix_numpy(eb, 'HbShBlBusWait')
        Df['BusAux'] = util.get_matrix_numpy(eb, 'HbShBlBusAux')
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'HbShBlBusBoard')
        Df['BusFar'] = util.get_matrix_numpy(eb, 'HbShBlBusFare')
        Df['BusTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux'] + Df['BusBrd'] # Total Bus Travel Time

        Df['RalIVR'] = util.get_matrix_numpy(eb, 'HbShBlRailIvtt')
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'HbShBlRailIvttBus')
        Df['RalWat'] = util.get_matrix_numpy(eb, 'HbShBlRailWait')
        Df['RalAux'] = util.get_matrix_numpy(eb, 'HbShBlRailAux')
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'HbShBlRailBoard')
        Df['RalFar'] = util.get_matrix_numpy(eb, 'HbShBlRailFare')
        Df['RalTot'] = Df['RalIVB'] + Df['RalIVR'] + Df['RalWat'] + Df['RalAux'] + Df['RalBrd'] # Total Bus Travel Time
        Df['RalIBR'] = Df['RalIVB']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Bus IVT to Total Time
        Df['RalIRR'] = Df['RalIVR']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Rail IVT to Total Time


        Df['IntZnl'] = np.identity(NoTAZ)

        # Utilities
        # Bus Utility
        # Bus Utility across all incomes
        Df['GeUtl'] = ( p4
                      + p15*Df['BusIVT']
                      + p17*Df['BusWat']
                      + p18*Df['BusAux']
                      + p19*Df['BusBrd'])

        # Check Availability conditions
        Df['GeUtl'] = MChM.BusAvail(Df, Df['GeUtl'], AvailDict)
        # Add Income parameters
        DfU['BusI1'] = Df['GeUtl'] + p12*Df['BusFar']
        DfU['BusI2'] = Df['GeUtl'] + p12*Df['BusFar']
        DfU['BusI3'] = Df['GeUtl'] + p14*Df['BusFar']

        # Rail Utility
        # Rail Utility across all incomes
        Df['GeUtl'] = ( p4*Df['RalIBR']
                      + p6*Df['RalIRR']
                      + p15*Df['RalIVB']
                      + p15*Df['RalIVR']
                      + p17*Df['RalWat']
                      + p18*Df['RalAux']
                      + p19*Df['RalBrd'])

        # Check Availability conditions
        Df['GeUtl'] = MChM.RailAvail(Df, Df['GeUtl'],AvailDict)
        # Add Income parameters
        DfU['RalI1'] = Df['GeUtl'] + p12*Df['RalFar']
        DfU['RalI2'] = Df['GeUtl'] + p12*Df['RalFar']
        DfU['RalI3'] = Df['GeUtl'] + p14*Df['RalFar']

#        ##############################################################################
#        ##       Active Modes
#        ##############################################################################

        Df = {}
        Df['AutoDis'] = util.get_matrix_numpy(eb, "mfdistAON")

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

        I1A0_Dict = self.Calc_Prob(eb, Dict, "HbShLSI1A0", thet)

        ## Low Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI1'] + p160], # One car households additional SOV bias term
               'HOV'  : [DfU['HOVI1'] + p162], # One car households additional HOV bias term
               'WTra' : [DfU['BusI1'], DfU['RalI1']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I1A1_Dict = self.Calc_Prob(eb, Dict, "HbShLSI1A1", thet)

        ## Low Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI1'] + p161], # One car households additional SOV bias term
               'HOV'  : [DfU['HOVI1'] + p163], # One car households additional HOV bias term
               'WTra' : [DfU['BusI1'], DfU['RalI1']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I1A2_Dict = self.Calc_Prob(eb, Dict, "HbShLSI1A2", thet)

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

        I2A0_Dict = self.Calc_Prob(eb, Dict, "HbShLSI2A0", thet)

        ## Med Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI2'] + p160],
               'HOV'  : [DfU['HOVI2'] + p162],
               'WTra' : [DfU['BusI2'], DfU['RalI2']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I2A1_Dict = self.Calc_Prob(eb, Dict, "HbShLSI2A1", thet)

        ## Med Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI2'] + p161],
               'HOV'  : [DfU['HOVI2'] + p163],
               'WTra' : [DfU['BusI2'], DfU['RalI2']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I2A2_Dict = self.Calc_Prob(eb, Dict, "HbShLSI2A2", thet)

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
        I3A0_Dict = self.Calc_Prob(eb, Dict, "HbShLSI3A0", thet)

        ## High Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI3'] + p160],
               'HOV'  : [DfU['HOVI3'] + p162],
               'WTra' : [DfU['BusI3'], DfU['RalI3']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I3A1_Dict = self.Calc_Prob(eb, Dict, "HbShLSI3A1", thet)

        ## High Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI3'] + p161],
               'HOV'  : [DfU['HOVI3'] + p163],
               'WTra' : [DfU['BusI3'], DfU['RalI3']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I3A2_Dict = self.Calc_Prob(eb, Dict, "HbShLSI3A2", thet)

        del DfU, Dict
#
#       ##############################################################################
#        ##       Trip Distribution
#       ##############################################################################

        Logsum =  [
                  "HbShLSI1A0", "HbShLSI1A1", "HbShLSI1A2",
                  "HbShLSI2A0", "HbShLSI2A1", "HbShLSI2A2",
                  "HbShLSI3A0", "HbShLSI3A1", "HbShLSI3A2",
                   ]

        imp_list = [
                  "P-AFrictionFact1", "P-AFrictionFact2", "P-AFrictionFact3",
                  "P-AFrictionFact4", "P-AFrictionFact5", "P-AFrictionFact6",
                  "P-AFrictionFact7", "P-AFrictionFact8", "P-AFrictionFact9"
                   ]

        mo_list =  [
                    "hbshopInc1Au0prd", "hbshopInc1Au1prd", "hbshopInc1Au2prd",
                    "hbshopInc2Au0prd", "hbshopInc2Au1prd", "hbshopInc2Au2prd",
                    "hbshopInc3Au0prd", "hbshopInc3Au1prd", "hbshopInc3Au2prd"
                   ]

        md_list =  ["hbshopatr"]

        out_list = [
                    "HbShP-AI1A0", "HbShP-AI1A1", "HbShP-AI1A2",
                    "HbShP-AI2A0", "HbShP-AI2A1", "HbShP-AI2A2",
                    "HbShP-AI3A0", "HbShP-AI3A1", "HbShP-AI3A2"
                   ]

        LS_Coeff = 0.8

        LambdaList = [-0.291171,-0.331585,-0.312873,-0.291171,-0.331585,-0.312873,-0.291171,-0.331585,-0.312873]


        AlphaList =  [0.004307,0.004477,0.005022,0.004307,0.004477,0.005022,0.004307,0.004477,0.005022]


        GammaList =  [-0.000049,-0.000047,-0.000075,-0.000049,-0.000047,-0.000075,-0.000049,-0.000047,-0.000075]


        MChM.ImpCalc(eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, util.get_matrix_numpy(eb, "mfdistAON"))
        MChM.one_dim_matrix_balancing(eb, mo_list, md_list, imp_list, out_list)


#       ##############################################################################
#        ##       Calculate Demand
#       ##############################################################################

        I1A0_Dict = self.Calc_Demand(I1A0_Dict, util.get_matrix_numpy(eb,"HbShP-AI1A0"))
        I1A1_Dict = self.Calc_Demand(I1A1_Dict, util.get_matrix_numpy(eb,"HbShP-AI1A1"))
        I1A2_Dict = self.Calc_Demand(I1A2_Dict, util.get_matrix_numpy(eb,"HbShP-AI1A2"))
        I2A0_Dict = self.Calc_Demand(I2A0_Dict, util.get_matrix_numpy(eb,"HbShP-AI2A0"))
        I2A1_Dict = self.Calc_Demand(I2A1_Dict, util.get_matrix_numpy(eb,"HbShP-AI2A1"))
        I2A2_Dict = self.Calc_Demand(I2A2_Dict, util.get_matrix_numpy(eb,"HbShP-AI2A2"))
        I3A0_Dict = self.Calc_Demand(I3A0_Dict, util.get_matrix_numpy(eb,"HbShP-AI3A0"))
        I3A1_Dict = self.Calc_Demand(I3A1_Dict, util.get_matrix_numpy(eb,"HbShP-AI3A1"))
        I3A2_Dict = self.Calc_Demand(I3A2_Dict, util.get_matrix_numpy(eb,"HbShP-AI3A2"))

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
        purp='hbshop'

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
        util.set_matrix_numpy(eb, "HbShSOVI1PerTrips", SOVI1)
        util.set_matrix_numpy(eb, "HbShSOVI2PerTrips", SOVI2)
        util.set_matrix_numpy(eb, "HbShSOVI3PerTrips", SOVI3)
        util.set_matrix_numpy(eb, "HbShHOVI1PerTrips", HOVI1)
        util.set_matrix_numpy(eb, "HbShHOVI2PerTrips", HOVI2)
        util.set_matrix_numpy(eb, "HbShHOVI3PerTrips", HOVI3)
        util.set_matrix_numpy(eb, "HbShBusPerTrips", Bus)
        util.set_matrix_numpy(eb, "HbShRailPerTrips", Rail)
        util.set_matrix_numpy(eb, "HbShWalkPerTrips", Walk)
        util.set_matrix_numpy(eb, "HbShBikePerTrips", Bike)


        # SOV
        # AM
        self.set_pkhr_mats(eb, SOVI1_AM, "SOV_pertrp_VOT_1_Am")
        self.set_pkhr_mats(eb, SOVI2_AM, "SOV_pertrp_VOT_2_Am")
        self.set_pkhr_mats(eb, SOVI3_AM, "SOV_pertrp_VOT_3_Am")
        # MD
        self.set_pkhr_mats(eb, SOVI1_MD, "SOV_pertrp_VOT_1_Md")
        self.set_pkhr_mats(eb, SOVI2_MD, "SOV_pertrp_VOT_2_Md")
        self.set_pkhr_mats(eb, SOVI3_MD, "SOV_pertrp_VOT_3_Md")
        # PM
        self.set_pkhr_mats(eb, SOVI1_PM, "SOV_pertrp_VOT_1_Pm")
        self.set_pkhr_mats(eb, SOVI2_PM, "SOV_pertrp_VOT_2_Pm")
        self.set_pkhr_mats(eb, SOVI3_PM, "SOV_pertrp_VOT_3_Pm")

        # HOV
        # AM
        self.set_pkhr_mats(eb, HOVI1_AM, "HOV_pertrp_VOT_1_Am")
        self.set_pkhr_mats(eb, HOVI2_AM, "HOV_pertrp_VOT_2_Am")
        self.set_pkhr_mats(eb, HOVI3_AM, "HOV_pertrp_VOT_3_Am")
        # MD
        self.set_pkhr_mats(eb, HOVI1_MD, "HOV_pertrp_VOT_1_Md")
        self.set_pkhr_mats(eb, HOVI2_MD, "HOV_pertrp_VOT_2_Md")
        self.set_pkhr_mats(eb, HOVI3_MD, "HOV_pertrp_VOT_3_Md")
        # PM
        self.set_pkhr_mats(eb, HOVI1_PM, "HOV_pertrp_VOT_1_Pm")
        self.set_pkhr_mats(eb, HOVI2_PM, "HOV_pertrp_VOT_2_Pm")
        self.set_pkhr_mats(eb, HOVI3_PM, "HOV_pertrp_VOT_3_Pm")

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
        self.set_pkhr_mats(eb, SOVI1_AM, "SOV_drvtrp_VOT_1_Am")
        self.set_pkhr_mats(eb, SOVI2_AM, "SOV_drvtrp_VOT_2_Am")
        self.set_pkhr_mats(eb, SOVI3_AM, "SOV_drvtrp_VOT_3_Am")
        # MD
        self.set_pkhr_mats(eb, SOVI1_MD, "SOV_drvtrp_VOT_1_Md")
        self.set_pkhr_mats(eb, SOVI2_MD, "SOV_drvtrp_VOT_2_Md")
        self.set_pkhr_mats(eb, SOVI3_MD, "SOV_drvtrp_VOT_3_Md")
        # PM
        self.set_pkhr_mats(eb, SOVI1_PM, "SOV_drvtrp_VOT_1_Pm")
        self.set_pkhr_mats(eb, SOVI2_PM, "SOV_drvtrp_VOT_2_Pm")
        self.set_pkhr_mats(eb, SOVI3_PM, "SOV_drvtrp_VOT_3_Pm")


        # HOV
        # AM
        self.set_pkhr_mats(eb, AuDr_HOVI1_AM, "HOV_drvtrp_VOT_1_Am")
        self.set_pkhr_mats(eb, AuDr_HOVI2_AM, "HOV_drvtrp_VOT_2_Am")
        self.set_pkhr_mats(eb, AuDr_HOVI3_AM, "HOV_drvtrp_VOT_3_Am")
        # MD
        self.set_pkhr_mats(eb, AuDr_HOVI1_MD, "HOV_drvtrp_VOT_1_Md")
        self.set_pkhr_mats(eb, AuDr_HOVI2_MD, "HOV_drvtrp_VOT_2_Md")
        self.set_pkhr_mats(eb, AuDr_HOVI3_MD, "HOV_drvtrp_VOT_3_Md")
        # PM
        self.set_pkhr_mats(eb, AuDr_HOVI1_PM, "HOV_drvtrp_VOT_1_Pm")
        self.set_pkhr_mats(eb, AuDr_HOVI2_PM, "HOV_drvtrp_VOT_2_Pm")
        self.set_pkhr_mats(eb, AuDr_HOVI3_PM, "HOV_drvtrp_VOT_3_Pm")

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
        purp = "hbshop"

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


    def set_pkhr_mats(self, eb, MatVal, MatID):

        util = _m.Modeller().tool("translink.util")
        Value = util.get_matrix_numpy(eb, MatID)
        Value += MatVal
        util.set_matrix_numpy(eb, MatID, Value)


    @_m.logbook_trace("Initialize Matrices")
    def matrix_batchins(self, eb):
        util = _m.Modeller().tool("translink.util")

        ## Initialze Logsum Matrices
        util.initmat(eb, "mf9030", "HbShLSI1A0", "LogSum HbSh I1 A0", 0)
        util.initmat(eb, "mf9031", "HbShLSI1A1", "LogSum HbSh I1 A1", 0)
        util.initmat(eb, "mf9032", "HbShLSI1A2", "LogSum HbSh I1 A2", 0)
        util.initmat(eb, "mf9033", "HbShLSI2A0", "LogSum HbSh I2 A0", 0)
        util.initmat(eb, "mf9034", "HbShLSI2A1", "LogSum HbSh I2 A1", 0)
        util.initmat(eb, "mf9035", "HbShLSI2A2", "LogSum HbSh I2 A2", 0)
        util.initmat(eb, "mf9036", "HbShLSI3A0", "LogSum HbSh I3 A0", 0)
        util.initmat(eb, "mf9037", "HbShLSI3A1", "LogSum HbSh I3 A1", 0)
        util.initmat(eb, "mf9038", "HbShLSI3A2", "LogSum HbSh I3 A2", 0)

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
        util.initmat(eb, "mf3300", "HbShSOVI1PerTrips", "HbSh SOV Low Income Per-Trips", 0)
        util.initmat(eb, "mf3301", "HbShSOVI2PerTrips", "HbSh SOV Med Income Per-Trips", 0)
        util.initmat(eb, "mf3302", "HbShSOVI3PerTrips", "HbSh SOV High Income Per-Trips", 0)
        util.initmat(eb, "mf3305", "HbShHOVI1PerTrips", "HbSh HOV Low Income Per-Trips", 0)
        util.initmat(eb, "mf3306", "HbShHOVI2PerTrips", "HbSh HOV Med Income Per-Trips", 0)
        util.initmat(eb, "mf3307", "HbShHOVI3PerTrips", "HbSh HOV High Income Per-Trips", 0)
        util.initmat(eb, "mf3315", "HbShBusPerTrips", "HbSh Bus Per-Trips", 0)
        util.initmat(eb, "mf3320", "HbShRailPerTrips", "HbSh Rail Per-Trips", 0)
        util.initmat(eb, "mf3330", "HbShWalkPerTrips", "HbSh Walk Per-Trips", 0)
        util.initmat(eb, "mf3335", "HbShBikePerTrips", "HbSh Bike Per-Trips", 0)


        ## Initialize P-A Trip Tables from trip distribution
        util.initmat(eb, "mf3350", "HbShP-AI1A0", " HbSh P-A Trips I1 A0", 0)
        util.initmat(eb, "mf3351", "HbShP-AI1A1", " HbSh P-A Trips I1 A1", 0)
        util.initmat(eb, "mf3352", "HbShP-AI1A2", " HbSh P-A Trips I1 A2", 0)
        util.initmat(eb, "mf3353", "HbShP-AI2A0", " HbSh P-A Trips I1 A0", 0)
        util.initmat(eb, "mf3354", "HbShP-AI2A1", " HbSh P-A Trips I1 A1", 0)
        util.initmat(eb, "mf3355", "HbShP-AI2A2", " HbSh P-A Trips I1 A2", 0)
        util.initmat(eb, "mf3356", "HbShP-AI3A0", " HbSh P-A Trips I1 A0", 0)
        util.initmat(eb, "mf3357", "HbShP-AI3A1", " HbSh P-A Trips I1 A1", 0)
        util.initmat(eb, "mf3358", "HbShP-AI3A2", " HbSh P-A Trips I1 A2", 0)
