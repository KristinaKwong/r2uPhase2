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
        MChM = _m.Modeller().tool("translink.RTM3.stage2.mcutil")
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

        p2  =   4.273762
        p4  =   2.799811
        p6  =   4.435847
        p10 =   8.403278
        p11 =   4.438331
        p12 =  -0.729930
        p13 =  -0.557544
        p14 =  -0.427097
        p15 =  -0.066912
        p17 =  -0.084509
        p18 =  -0.130873
        p19 =  -1.249354
        p20 =  -4.020084
        p21 =  -3.238632
        p160=  12.961291
        p161=  15.905761
        p162=   5.366765
        p163=   8.927652
        p164=   2.832292
        p700=   1.757929
        p701=   2.160435
        thet=   0.233511

#        ##############################################################################
#        ##       Auto Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        MaxPark = 10.0
        VOC = util.get_matrix_numpy(eb, 'autoOpCost')
        Occ = util.get_matrix_numpy(eb, 'HOVOccHbpb')
        Df['ParkCost'] = util.get_matrix_numpy(eb, 'prk2hr')  # 2 hour parking

        Df['ParkCost'] = Df['ParkCost'].reshape(1, NoTAZ) + np.zeros((NoTAZ, 1))

        # Get SOV Skims by income
        # Low Income
        Df['AutoDisSOV1'] = util.get_matrix_numpy(eb, 'HbPbBlSovDist_I1') #SOV Distance
        Df['AutoTimSOV1'] = util.get_matrix_numpy(eb, 'HbPbBlSovTime_I1') #SOV Time
        Df['AutoCosSOV1'] = Df['AutoDisSOV1']*VOC + util.get_matrix_numpy(eb, 'HbPbBlSovToll_I1') + Df['ParkCost'] #SOV Cost (per km + Toll + Parking)

        # Med Income
        Df['AutoDisSOV2'] = util.get_matrix_numpy(eb, 'HbPbBlSovDist_I2') #SOV Distance
        Df['AutoTimSOV2'] = util.get_matrix_numpy(eb, 'HbPbBlSovTime_I2') #SOV Time
        Df['AutoCosSOV2'] = Df['AutoDisSOV2']*VOC + util.get_matrix_numpy(eb, 'HbPbBlSovToll_I2') + Df['ParkCost'] #SOV Cost (per km + Toll + Parking)

        # High Income
        Df['AutoDisSOV3'] = util.get_matrix_numpy(eb, 'HbPbBlSovDist_I3') #SOV Distance
        Df['AutoTimSOV3'] = util.get_matrix_numpy(eb, 'HbPbBlSovTime_I3') #SOV Time
        Df['AutoCosSOV3'] = Df['AutoDisSOV3']*VOC + util.get_matrix_numpy(eb, 'HbPbBlSovToll_I3') + Df['ParkCost'] #SOV Cost (per km + Toll + Parking)

        # Get HOV Skims by income
        # Low Income
        Df['AutoDiPbOV1'] = util.get_matrix_numpy(eb, 'HbPbBlHovDist_I1') #HOV Distance
        Df['AutoTimHOV1'] = util.get_matrix_numpy(eb, 'HbPbBlHovTime_I1') #HOV Time
        Df['AutoCoPbOV1'] = Df['AutoDiPbOV1']*VOC + util.get_matrix_numpy(eb, 'HbPbBlHovToll_I1') + Df['ParkCost'] #HOV Cost (per km + Toll + Parking)

        # Med Income
        Df['AutoDiPbOV2'] = util.get_matrix_numpy(eb, 'HbPbBlHovDist_I2') #HOV Distance
        Df['AutoTimHOV2'] = util.get_matrix_numpy(eb, 'HbPbBlHovTime_I2') #HOV Time
        Df['AutoCoPbOV2'] = Df['AutoDiPbOV2']*VOC + util.get_matrix_numpy(eb, 'HbPbBlHovToll_I2') + Df['ParkCost'] #HOV Cost (per km + Toll + Parking)

        # High Income
        Df['AutoDiPbOV3'] = util.get_matrix_numpy(eb, 'HbPbBlHovDist_I3') #HOV Distance
        Df['AutoTimHOV3'] = util.get_matrix_numpy(eb, 'HbPbBlHovTime_I3') #HOV Time
        Df['AutoCoPbOV3'] = Df['AutoDiPbOV3']*VOC + util.get_matrix_numpy(eb, 'HbPbBlHovToll_I3') + Df['ParkCost'] #HOV Cost (per km + Toll + Parking)

        # Utilities
        # SOV

        Df['SOVI1'] = ( 0
                      + p15*Df['AutoTimSOV1']
                      + p12*Df['AutoCosSOV1'])
        Df['SOVI2'] = ( 0
                      + p15*Df['AutoTimSOV2']
                      + p13*Df['AutoCosSOV2'])
        Df['SOVI3'] = ( 0
                      + p15*Df['AutoTimSOV3']
                      + p14*Df['AutoCosSOV3'])


        DfU['SOVI1']  = MChM.AutoAvail(Df['AutoDisSOV1'], Df['SOVI1'], AvailDict) #Check Availability condition if mode not available then set to high negative utility (-99999)
        DfU['SOVI2']  = MChM.AutoAvail(Df['AutoDisSOV2'], Df['SOVI2'], AvailDict)
        DfU['SOVI3']  = MChM.AutoAvail(Df['AutoDisSOV3'], Df['SOVI3'], AvailDict)

        # HOV

        Df['HOVI1'] = ( p2
                      + p15*Df['AutoTimHOV1']
                      + p12*Df['AutoCosHOV1']/Occ)


        Df['HOVI2'] = ( p2
                      + p15*Df['AutoTimHOV2']
                      + p13*Df['AutoCosHOV2']/Occ)


        Df['HOVI3'] = ( p2
                      + p15*Df['AutoTimHOV3']
                      + p14*Df['AutoCosHOV3']/Occ)

        DfU['HOVI1']  = MChM.AutoAvail(Df['AutoDisHOV1'], Df['HOVI1'], AvailDict) #Check Availability condition if mode not available then set to high negative utility (-99999)
        DfU['HOVI2']  = MChM.AutoAvail(Df['AutoDisHOV2'], Df['HOVI2'], AvailDict)
        DfU['HOVI3']  = MChM.AutoAvail(Df['AutoDisHOV3'], Df['HOVI3'], AvailDict)


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
        Df['PopEmpDen'] = util.get_matrix_numpy(eb, 'combinedensln')
        Df['PopEmpDen'] = Df['PopEmpDen'].reshape(NoTAZ, 1) + np.zeros((1, NoTAZ))


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
        Df['AutoDis'] = util.get_matrix_numpy(eb, 'HbPbBlSovDist_I2')

        Df['PopEmpDen'] = util.get_matrix_numpy(eb, 'combinedensln')
        Df['PopEmpDen'] = Df['PopEmpDen'].reshape(NoTAZ, 1) + np.zeros((1, NoTAZ))

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
               'HOV'  : [DfU['HOVI1']],
               'WTra' : [DfU['BusI1'] + p164, DfU['RalI1'] + p164],  # Zero car households additional transit bias term
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }

        I1A0_Dict = self.Calc_Prob(eb, Dict, "HbPbLSI1A0", thet)

        ## Low Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI1'] + p160], # One car households additional SOV bias term
               'HOV'  : [DfU['HOVI1'] + p162], # One car households additional HOV bias term
               'WTra' : [DfU['BusI1'], DfU['RalI1']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I1A1_Dict = self.Calc_Prob(eb, Dict, "HbPbLSI1A1", thet)

        ## Low Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI1'] + p161], # One car households additional SOV bias term
               'HOV'  : [DfU['HOVI1'] + p163], # One car households additional HOV bias term
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
               'HOV'  : [DfU['HOVI2']],
               'WTra' : [DfU['BusI2'] + p164, DfU['RalI2'] + p164],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }

        I2A0_Dict = self.Calc_Prob(eb, Dict, "HbPbLSI2A0", thet)

        ## Med Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI2'] + p160],
               'HOV'  : [DfU['HOVI2'] + p162],
               'WTra' : [DfU['BusI2'], DfU['RalI2']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I2A1_Dict = self.Calc_Prob(eb, Dict, "HbPbLSI2A1", thet)

        ## Med Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI2'] + p161],
               'HOV'  : [DfU['HOVI2'] + p163],
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
               'HOV'  : [DfU['HOVI3']],
               'WTra' : [DfU['BusI3'] + p164, DfU['RalI3'] + p164],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I3A0_Dict = self.Calc_Prob(eb, Dict, "HbPbLSI3A0", thet)

        ## High Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI3'] + p160],
               'HOV'  : [DfU['HOVI3'] + p162],
               'WTra' : [DfU['BusI3'], DfU['RalI3']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I3A1_Dict = self.Calc_Prob(eb, Dict, "HbPbLSI3A1", thet)

        ## High Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI3'] + p161],
               'HOV'  : [DfU['HOVI3'] + p163],
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
        MChM.ImpCalc(eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, util.get_matrix_numpy(eb, "HbPbBlSovDist_I2"))
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
#        ##       Get Time Slice Factors
#       ##############################################################################

        db_loc = util.get_eb_path(eb)
        db_path = os.path.join(db_loc, 'rtm.db')
        conn = sqlite3.connect(db_path)
        ts_df = pd.read_sql("SELECT * from timeSlicingFactors", conn)
        conn.close()
        # Subset Time Slice Factor Dataframes by purpose
        hbw_ts = ts_df.loc[ts_df['purpose'] == 'hbpb']

        # Subset Time Slice Factor Dataframes by mode
        Auto_AM_Fct, Auto_MD_Fct, Auto_PM_Fct = self.get_ts_factor(hbw_ts.loc[ts_df['mode'] == 'Auto']) # Auto Factors
        Tran_AM_Fct, Tran_MD_Fct, Tran_PM_Fct = self.get_ts_factor(hbw_ts.loc[ts_df['mode'] == 'Transit']) # Transit Factors
        Acti_AM_Fct, Acti_MD_Fct, Acti_PM_Fct = self.get_ts_factor(hbw_ts.loc[ts_df['mode'] == 'Active']) # Active Factors

        del ts_df, hbw_ts

      ##########################################################################################
       ##       Calculate peak hour O-D person trips and final 24 hour P-A Trips
      ##########################################################################################
      ## SOV Trips      #SOV*PA_Factor + SOV_transpose*AP_Factor
        SOVI1_AM = SOVI1*Auto_AM_Fct[0] + SOVI1.transpose()*Auto_AM_Fct[1]  # Low Income
        SOVI1_MD = SOVI1*Auto_MD_Fct[0] + SOVI1.transpose()*Auto_MD_Fct[1]
        SOVI1_PM = SOVI1*Auto_PM_Fct[0] + SOVI1.transpose()*Auto_PM_Fct[1]

        SOVI2_AM = SOVI2*Auto_AM_Fct[0] + SOVI2.transpose()*Auto_AM_Fct[1]  # Med Income
        SOVI2_MD = SOVI2*Auto_MD_Fct[0] + SOVI2.transpose()*Auto_MD_Fct[1]
        SOVI2_PM = SOVI2*Auto_PM_Fct[0] + SOVI2.transpose()*Auto_PM_Fct[1]

        SOVI3_AM = SOVI3*Auto_AM_Fct[0] + SOVI3.transpose()*Auto_AM_Fct[1]  # High Income
        SOVI3_MD = SOVI3*Auto_MD_Fct[0] + SOVI3.transpose()*Auto_MD_Fct[1]
        SOVI3_PM = SOVI3*Auto_PM_Fct[0] + SOVI3.transpose()*Auto_PM_Fct[1]



        HOVI1_AM = HOVI1*Auto_AM_Fct[0] + HOVI1.transpose()*Auto_AM_Fct[1]  # Low Income
        HOVI1_MD = HOVI1*Auto_MD_Fct[0] + HOVI1.transpose()*Auto_MD_Fct[1]
        HOVI1_PM = HOVI1*Auto_PM_Fct[0] + HOVI1.transpose()*Auto_PM_Fct[1]

        HOVI2_AM = HOVI2*Auto_AM_Fct[0] + HOVI2.transpose()*Auto_AM_Fct[1]  # Med Income
        HOVI2_MD = HOVI2*Auto_MD_Fct[0] + HOVI2.transpose()*Auto_MD_Fct[1]
        HOVI2_PM = HOVI2*Auto_PM_Fct[0] + HOVI2.transpose()*Auto_PM_Fct[1]

        HOVI3_AM = HOVI3*Auto_AM_Fct[0] + HOVI3.transpose()*Auto_AM_Fct[1]  # High Income
        HOVI3_MD = HOVI3*Auto_MD_Fct[0] + HOVI3.transpose()*Auto_MD_Fct[1]
        HOVI3_PM = HOVI3*Auto_PM_Fct[0] + HOVI3.transpose()*Auto_PM_Fct[1]


        ## Transit Trips
        Bus_AM = Bus*Tran_AM_Fct[0] + Bus.transpose()*Tran_AM_Fct[1]
        Bus_MD = Bus*Tran_MD_Fct[0] + Bus.transpose()*Tran_MD_Fct[1]
        Bus_PM = Bus*Tran_PM_Fct[0] + Bus.transpose()*Tran_PM_Fct[1]

        Rail_AM = Rail*Tran_AM_Fct[0] + Rail.transpose()*Tran_AM_Fct[1]
        Rail_MD = Rail*Tran_MD_Fct[0] + Rail.transpose()*Tran_MD_Fct[1]
        Rail_PM = Rail*Tran_PM_Fct[0] + Rail.transpose()*Tran_PM_Fct[1]


        ## Active Trips
        Walk_AM = Walk*Acti_AM_Fct[0] + Walk.transpose()*Acti_AM_Fct[1]
        Walk_MD = Walk*Acti_MD_Fct[0] + Walk.transpose()*Acti_MD_Fct[1]
        Walk_PM = Walk*Acti_PM_Fct[0] + Walk.transpose()*Acti_PM_Fct[1]

        Bike_AM = Bike*Acti_AM_Fct[0] + Bike.transpose()*Acti_AM_Fct[1]
        Bike_MD = Bike*Acti_MD_Fct[0] + Bike.transpose()*Acti_MD_Fct[1]
        Bike_PM = Bike*Acti_PM_Fct[0] + Bike.transpose()*Acti_PM_Fct[1]


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
        util.set_matrix_numpy(eb, "HbPbSOVI1PerTrips", SOVI1)
        util.set_matrix_numpy(eb, "HbPbSOVI2PerTrips", SOVI2)
        util.set_matrix_numpy(eb, "HbPbSOVI3PerTrips", SOVI3)
        util.set_matrix_numpy(eb, "HbPbHOVI1PerTrips", HOVI1)
        util.set_matrix_numpy(eb, "HbPbHOVI2PerTrips", HOVI2)
        util.set_matrix_numpy(eb, "HbPbHOVI3PerTrips", HOVI3)
        util.set_matrix_numpy(eb, "HbPbBusPerTrips", Bus)
        util.set_matrix_numpy(eb, "HbPbRailPerTrips", Rail)
        util.set_matrix_numpy(eb, "HbPbWalkPerTrips", Walk)
        util.set_matrix_numpy(eb, "HbPbBikePerTrips", Bike)

        # SOV
        # AM
        self.set_pkhr_mats(eb, SOVI1_AM, "SOV_pertrp_VOT_1_Am")
        self.set_pkhr_mats(eb, SOVI2_AM, "SOV_pertrp_VOT_2_Am")
        self.set_pkhr_mats(eb, SOVI3_AM, "SOV_pertrp_VOT_2_Am")
        # MD
        self.set_pkhr_mats(eb, SOVI1_MD, "SOV_pertrp_VOT_1_Md")
        self.set_pkhr_mats(eb, SOVI2_MD, "SOV_pertrp_VOT_2_Md")
        self.set_pkhr_mats(eb, SOVI3_MD, "SOV_pertrp_VOT_2_Md")
        # PM
        self.set_pkhr_mats(eb, SOVI1_PM, "SOV_pertrp_VOT_1_Pm")
        self.set_pkhr_mats(eb, SOVI2_PM, "SOV_pertrp_VOT_2_Pm")
        self.set_pkhr_mats(eb, SOVI3_PM, "SOV_pertrp_VOT_2_Pm")

        # HOV
        # AM
        self.set_pkhr_mats(eb, HOVI1_AM, "HOV_pertrp_VOT_1_Am")
        self.set_pkhr_mats(eb, HOVI2_AM, "HOV_pertrp_VOT_2_Am")
        self.set_pkhr_mats(eb, HOVI3_AM, "HOV_pertrp_VOT_2_Am")
        # MD
        self.set_pkhr_mats(eb, HOVI1_MD, "HOV_pertrp_VOT_1_Md")
        self.set_pkhr_mats(eb, HOVI2_MD, "HOV_pertrp_VOT_2_Md")
        self.set_pkhr_mats(eb, HOVI3_MD, "HOV_pertrp_VOT_2_Md")
        # PM
        self.set_pkhr_mats(eb, HOVI1_PM, "HOV_pertrp_VOT_1_Pm")
        self.set_pkhr_mats(eb, HOVI2_PM, "HOV_pertrp_VOT_2_Pm")
        self.set_pkhr_mats(eb, HOVI3_PM, "HOV_pertrp_VOT_2_Pm")

        # Transit
        # AM
        self.set_pkhr_mats(eb, Bus_AM, "Bus_pertrp_Am")
        self.set_pkhr_mats(eb, Rail_AM, "Rail_pertrp_Am")

        # MD
        self.set_pkhr_mats(eb, Bus_MD, "Bus_pertrp_Md")
        self.set_pkhr_mats(eb, Rail_MD, "Rail_pertrp_Md")

        # PM
        self.set_pkhr_mats(eb, Bus_PM, "Bus_pertrp_Pm")
        self.set_pkhr_mats(eb, Rail_PM, "Rail_pertrp_Pm")


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
        self.set_pkhr_mats(eb, SOVI3_AM, "SOV_drvtrp_VOT_2_Am")
        # MD
        self.set_pkhr_mats(eb, SOVI1_MD, "SOV_drvtrp_VOT_1_Md")
        self.set_pkhr_mats(eb, SOVI2_MD, "SOV_drvtrp_VOT_2_Md")
        self.set_pkhr_mats(eb, SOVI3_MD, "SOV_drvtrp_VOT_2_Md")
        # PM
        self.set_pkhr_mats(eb, SOVI1_PM, "SOV_drvtrp_VOT_1_Pm")
        self.set_pkhr_mats(eb, SOVI2_PM, "SOV_drvtrp_VOT_2_Pm")
        self.set_pkhr_mats(eb, SOVI3_PM, "SOV_drvtrp_VOT_2_Pm")


        # HOV
        # AM
        self.set_pkhr_mats(eb, AuDr_HOVI1_AM, "HOV_drvtrp_VOT_1_Am")
        self.set_pkhr_mats(eb, AuDr_HOVI2_AM, "HOV_drvtrp_VOT_2_Am")
        self.set_pkhr_mats(eb, AuDr_HOVI3_AM, "HOV_drvtrp_VOT_2_Am")
        # MD
        self.set_pkhr_mats(eb, AuDr_HOVI1_MD, "HOV_drvtrp_VOT_1_Md")
        self.set_pkhr_mats(eb, AuDr_HOVI2_MD, "HOV_drvtrp_VOT_2_Md")
        self.set_pkhr_mats(eb, AuDr_HOVI3_MD, "HOV_drvtrp_VOT_2_Md")
        # PM
        self.set_pkhr_mats(eb, AuDr_HOVI1_PM, "HOV_drvtrp_VOT_1_Pm")
        self.set_pkhr_mats(eb, AuDr_HOVI2_PM, "HOV_drvtrp_VOT_2_Pm")
        self.set_pkhr_mats(eb, AuDr_HOVI3_PM, "HOV_drvtrp_VOT_2_Pm")


    def Calc_Prob(self, eb, Dict, Logsum, Th):
        util = _m.Modeller().tool("translink.emme.util")

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

    def get_ts_factor (self, ts_df):


        AM_Ts_List = [float(ts_df .loc[(ts_df['peakperiod'] == 'AM') & (ts_df['direction'] == 'PtoA'), 'shares']),
                      float(ts_df .loc[(ts_df['peakperiod'] == 'AM') & (ts_df['direction'] == 'AtoP'), 'shares'])]

        MD_Ts_List = [float(ts_df .loc[(ts_df['peakperiod'] == 'MD') & (ts_df['direction'] == 'PtoA'), 'shares']),
                      float(ts_df .loc[(ts_df['peakperiod'] == 'MD') & (ts_df['direction'] == 'AtoP'), 'shares'])]

        PM_Ts_List = [float(ts_df .loc[(ts_df['peakperiod'] == 'PM') & (ts_df['direction'] == 'PtoA'), 'shares']),
                      float(ts_df .loc[(ts_df['peakperiod'] == 'PM') & (ts_df['direction'] == 'AtoP'), 'shares'])]


        return (AM_Ts_List, MD_Ts_List, PM_Ts_List)

    def set_pkhr_mats(self, eb, MatVal, MatID):

        util = _m.Modeller().tool("translink.emme.util")
        Value = util.get_matrix_numpy(eb, MatID)
        Value += MatVal
        util.set_matrix_numpy(eb, MatID, Value)




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
        util.initmat(eb, "mf3405", "HbPbHOVI1PerTrips", "HbPb HOV Low Income Per-Trips", 0)
        util.initmat(eb, "mf3406", "HbPbHOVI2PerTrips", "HbPb HOV Med Income Per-Trips", 0)
        util.initmat(eb, "mf3407", "HbPbHOVI3PerTrips", "HbPb HOV High Income Per-Trips", 0)
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


