##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage2.hbshop
##--Purpose:
##---------------------------------------------------------------------
import inro.modeller as _m
import numpy as np
import pandas as pd

class HbWork(_m.Tool()):

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Home Base Shopping"
        pb.description = "Calculate home base shopping person trips by mode and time of day"
        pb.branding_text = "TransLink"
        pb.runnable = False
        return pb.render()

    @_m.logbook_trace("Run Home Base Shopping")
    def __call__(self, eb, Bus_Bias, Rail_Bias, WCE_Bias):
        util = _m.Modeller().tool("translink.util")
        MChM = _m.Modeller().tool("translink.RTM3.stage2.modechoiceutils")

        self.matrix_batchins(eb)
        NoTAZ = len(util.get_matrix_numpy(eb, "mo51"))
        tnc_occupancy = float(util.get_matrix_numpy(eb, 'TNCOccHbshop'))  # TNC Occupancy

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

        p2   = eb.matrix("hbshop_asc_hov" ).data # hov
        p4   = eb.matrix("hbshop_asc_bus" ).data # bus
        p6   = eb.matrix("hbshop_asc_rail").data # rail
        p10  = eb.matrix("hbshop_asc_walk").data # walk
        p11  = eb.matrix("hbshop_asc_bike").data # bike
        p12  = -0.772843
        p14  = -0.420448
        p15  = -0.105966
        p17  = -0.138613
        p18  = -0.186170
        p19  = -0.378664
        p20  = -3.367424
        p21  = -2.419374
        p160 =  9.800320
        p161 = 12.494787
        p162 =  6.881428
        p163 =  9.625813
        p164 =  2.604866
        p701 =  0.672142
        p870 =  0.471205
        thet =  0.303572
        LS_Coeff = 0.8

        # TNC Cost Factors
        # alpha_tnc and beta_tnc are calculated in Blended_Skims.py
        # TNC Coefficients and Calibration
        p30 = eb.matrix("hbshop_asc_tnc" ).data
        tnc_cost_scale = 20  # Coeff3 = coeff 2/lambda
        tnc_cost_exponent = 2.0 # TNC Cost exponent ; non-linear calibration constant
        p604 = 0.4  # TNC Accessibility measure coefficient
        tnc_wait_percep = 1.5 # multiplied to IVTT coefficient

#        ##############################################################################
#        ##       Auto Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        MaxPark = 10.0
        Hov_scale = 0.75
        tnc_scale = 0.75 # TODO: Update

        Occ = util.get_matrix_numpy(eb, 'HOVOccHBshop')
        Df['ParkCost'] = util.get_matrix_numpy(eb, 'prk2hr')  # 2 hour parking
        Df['ParkCost'] = Df['ParkCost'].reshape(1, NoTAZ) + np.zeros((NoTAZ, 1))
        Df['TNCWaitTime'] = util.get_matrix_numpy(eb, 'tncwaittime')
        Df['TNCWaitTime'] = Df['TNCWaitTime'].reshape(NoTAZ,1)+ np.zeros((1,NoTAZ))

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

        # Get TNC Skims by income
        # Use HOV Distance Skims
        # Low Income
        Df['TNCCost1'] = util.get_matrix_numpy(eb, 'HbShBlTNCCost_I1')
        # Medium Income
        Df['TNCCost2'] = util.get_matrix_numpy(eb, 'HbShBlTNCCost_I2')
        # High Income
        Df['TNCCost3'] = util.get_matrix_numpy(eb, 'HbShBlTNCCost_I3')

        # TNC Accessibbility
        Df['TNCAccess'] = util.get_matrix_numpy(eb,'tncAccLn').reshape(NoTAZ, 1) + np.zeros((1, NoTAZ))

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
                      + p12*Df['AutoTotCosHOV1']/(pow(Occ,Hov_scale)))


        Df['HOVI2'] = ( p2
                      + p15*Df['AutoTimHOV2']
                      + p12*Df['AutoTotCosHOV2']/(pow(Occ,Hov_scale)))


        Df['HOVI3'] = ( p2
                      + p15*Df['AutoTimHOV3']
                      + p14*Df['AutoTotCosHOV3']/(pow(Occ,Hov_scale)))

        DfU['HOVI1']  = MChM.AutoAvail(Df['AutoCosHOV1'], Df['HOVI1'], AvailDict) #Check Availability condition if mode not available then set to high negative utility (-99999)
        DfU['HOVI2']  = MChM.AutoAvail(Df['AutoCosHOV2'], Df['HOVI2'], AvailDict)
        DfU['HOVI3']  = MChM.AutoAvail(Df['AutoCosHOV3'], Df['HOVI3'], AvailDict)

        # Taxi/TNC
        # Use HOV Skims, TNC Cost and Wait Times

        DfU['TNCI1'] = (p30
                       + p15 * Df['AutoTimHOV1']
                       + p12 * Df['TNCCost1']/pow(tnc_occupancy, tnc_scale) +
                       + (p12 / tnc_cost_scale) * np.power(Df['TNCCost1']/pow(tnc_occupancy, tnc_scale), tnc_cost_exponent)
                       + tnc_wait_percep * p15 * Df['TNCWaitTime']
                       + p604 * Df['TNCAccess'])

        DfU['TNCI2'] = (p30
                       + p15 * Df['AutoTimHOV2']
                       + p12 * Df['TNCCost2']/pow(tnc_occupancy, tnc_scale) +
                       + (p12 / tnc_cost_scale) * np.power(Df['TNCCost2']/pow(tnc_occupancy, tnc_scale), tnc_cost_exponent)
                       + tnc_wait_percep * p15 * Df['TNCWaitTime']
                       + p604 * Df['TNCAccess'])

        DfU['TNCI3'] = (p30
                       + p15 * Df['AutoTimHOV3']
                       + p14 * Df['TNCCost3']/pow(tnc_occupancy, tnc_scale) +
                       + (p14 / tnc_cost_scale) * np.power(Df['TNCCost3']/pow(tnc_occupancy, tnc_scale), tnc_cost_exponent)
                       + tnc_wait_percep * p15 * Df['TNCWaitTime']
                       + p604 * Df['TNCAccess'])
#        ##############################################################################
#        ##       Walk to Transit Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        Tiny=0.000001
        B_IVT_perc = 1.06

        Df['BusIVT'] = util.get_matrix_numpy(eb, 'HbShBlBusIvtt')
        Df['BusWat'] = util.get_matrix_numpy(eb, 'HbShBlBusWait')
        Df['BusAux'] = util.get_matrix_numpy(eb, 'HbShBlBusAux')
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'HbShBlBusBoard')
        Df['BusFar'] = util.get_matrix_numpy(eb, 'HbShBlBusFare')
        Df['BusTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux']  # Total Bus Travel Time
        Df['BusIVTBRT'] = util.get_matrix_numpy(eb, 'HbShBlBusIvttBRT') #In vehicle Bus BRT time

        Df['RalIVR'] = util.get_matrix_numpy(eb, 'HbShBlRailIvtt')
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'HbShBlRailIvttBus')
        Df['RalWat'] = util.get_matrix_numpy(eb, 'HbShBlRailWait')
        Df['RalAux'] = util.get_matrix_numpy(eb, 'HbShBlRailAux')
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'HbShBlRailBoard')
        Df['RalFar'] = util.get_matrix_numpy(eb, 'HbShBlRailFare')
        Df['RalTot'] = Df['RalIVB'] + Df['RalIVR'] + Df['RalWat'] + Df['RalAux']  # Total Bus Travel Time
        Df['RalIBR'] = Df['RalIVB']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Bus IVT to Total Time
        Df['RalIRR'] = Df['RalIVR']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Rail IVT to Total Time
        Df['RalIVBRT'] = util.get_matrix_numpy(eb, 'HbShBlRailIvttBRT') #In vehicle Rail time BRT
        Df['RalIVLRT'] = util.get_matrix_numpy(eb, 'HbShBlRailIvttLRT') #In vehicle Rail time LRT



        Df['IntZnl'] = np.identity(NoTAZ)

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
                      + p15*(Df['BusIVT'] - Df['BusIVTBRT'])*B_IVT_perc
                      + BRT_ivt*(Df['BusIVTBRT'])
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
        Df['GeUtl'] = ( Rail_const
                      + Rail_Bias
                      + p15*(Df['RalIVB'] - Df['RalIVBRT'])*B_IVT_perc
                      + BRT_ivt*(Df['RalIVBRT'])
                      + p15*(Df['RalIVR'] - Df['RalIVLRT'])
                      + LRT_ivt*(Df['RalIVLRT'])
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

        Df['PopEmpDenPA'] = util.get_matrix_numpy(eb, 'combinedens') + Tiny #Pop+Emp Density at Prod and Attr Zones
        Df['PopEmpDenPA'] = np.log(Df['PopEmpDenPA'].reshape(NoTAZ, 1) + Df['PopEmpDenPA'].reshape(1, NoTAZ)) #Broadcast Density

        Df['BikScr'] = util.get_matrix_numpy(eb, 'bikeskim')

        # Walk Utility
        DfU['Walk'] = ( p10
                      + p20*Df['AutoDis']
                      + p701*Df['PopEmpDenPA'])
        # Check Availability conditions
        DfU['Walk'] = MChM.WalkAvail(Df['AutoDis'], DfU['Walk'], AvailDict)

        # Bike Utility
        DfU['Bike'] = ( p11
                      + p21*Df['AutoDis']
                      + p701*Df['PopEmpDenPA']
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

        taz_list = util.get_matrix_numpy(eb, 'zoneindex', reshape = False)

        ## Add SOV Availability car share term for households with zero vehicles

        CarShare = util.get_matrix_numpy(eb, 'cs500').reshape(NoTAZ,1) + np.zeros((1, NoTAZ))
        LrgU     = -99999.0
        ## Low Income Zero Autos
        Dict = {
               'SOV'  : [np.where(CarShare>0, DfU['SOVI1'], LrgU)],
               'HOV'  : [DfU['HOVI1']],
               'WTra' : [DfU['BusI1'] + p164, DfU['RalI1'] + p164],  # Zero car households additional transit bias term
               'Acti' : [DfU['Walk'], DfU['Bike']],
               'TNC'  : [DfU['TNCI1']+ p164]
               }

        keys_list = list(Dict.keys())
        modes_dict = {'All':keys_list, 'Auto': ['SOV', 'HOV', 'TNC'],
                     'Transit': ['WTra'],  'Active': ['Acti']}

        I1A0_Dict = MChM.Calc_Prob(eb, Dict, "HbShLSI1A0", thet, 'hbshopatr', LS_Coeff, modes_dict, taz_list)

        ## Low Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI1'] + p160], # One car households additional SOV bias term
               'HOV'  : [DfU['HOVI1'] + p162], # One car households additional HOV bias term
               'WTra' : [DfU['BusI1'], DfU['RalI1']],
               'Acti' : [DfU['Walk'], DfU['Bike']],
               'TNC'  : [DfU['TNCI1']]
               }
        I1A1_Dict = MChM.Calc_Prob(eb, Dict, "HbShLSI1A1", thet, 'hbshopatr', LS_Coeff, modes_dict, taz_list)

        ## Low Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI1'] + p161], # One car households additional SOV bias term
               'HOV'  : [DfU['HOVI1'] + p163], # One car households additional HOV bias term
               'WTra' : [DfU['BusI1'], DfU['RalI1']],
               'Acti' : [DfU['Walk'], DfU['Bike']],
               'TNC'  : [DfU['TNCI1']]
               }
        I1A2_Dict = MChM.Calc_Prob(eb, Dict, "HbShLSI1A2", thet, 'hbshopatr', LS_Coeff, modes_dict, taz_list)

        ############
        # Med Income
        ############

        ## Med Income Zero Autos
        Dict = {
               'SOV'  : [np.where(CarShare>0, DfU['SOVI2'], LrgU)],
               'HOV'  : [DfU['HOVI2']],
               'WTra' : [DfU['BusI2'] + p164, DfU['RalI2'] + p164],
               'Acti' : [DfU['Walk'], DfU['Bike']],
               'TNC'  : [DfU['TNCI2']+ p164]
               }

        I2A0_Dict = MChM.Calc_Prob(eb, Dict, "HbShLSI2A0", thet, 'hbshopatr', LS_Coeff, modes_dict, taz_list)

        ## Med Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI2'] + p160],
               'HOV'  : [DfU['HOVI2'] + p162],
               'WTra' : [DfU['BusI2'], DfU['RalI2']],
               'Acti' : [DfU['Walk'], DfU['Bike']],
               'TNC'  : [DfU['TNCI2']]
               }
        I2A1_Dict = MChM.Calc_Prob(eb, Dict, "HbShLSI2A1", thet, 'hbshopatr', LS_Coeff, modes_dict, taz_list)

        ## Med Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI2'] + p161],
               'HOV'  : [DfU['HOVI2'] + p163],
               'WTra' : [DfU['BusI2'], DfU['RalI2']],
               'Acti' : [DfU['Walk'], DfU['Bike']],
               'TNC'  : [DfU['TNCI2']]
               }
        I2A2_Dict = MChM.Calc_Prob(eb, Dict, "HbShLSI2A2", thet, 'hbshopatr', LS_Coeff, modes_dict, taz_list)

        #############
        # High Income
        #############

        ## High Income Zero Autos
        Dict = {
               'SOV'  : [np.where(CarShare>0, DfU['SOVI3'], LrgU)],
               'HOV'  : [DfU['HOVI3']],
               'WTra' : [DfU['BusI3'] + p164, DfU['RalI3'] + p164],
               'Acti' : [DfU['Walk'], DfU['Bike']],
               'TNC'  : [DfU['TNCI3']+ p164]
               }
        I3A0_Dict = MChM.Calc_Prob(eb, Dict, "HbShLSI3A0", thet, 'hbshopatr', LS_Coeff, modes_dict, taz_list)

        ## High Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI3'] + p160],
               'HOV'  : [DfU['HOVI3'] + p162],
               'WTra' : [DfU['BusI3'], DfU['RalI3']],
               'Acti' : [DfU['Walk'], DfU['Bike']],
               'TNC'  : [DfU['TNCI3']]
               }
        I3A1_Dict = MChM.Calc_Prob(eb, Dict, "HbShLSI3A1", thet, 'hbshopatr', LS_Coeff, modes_dict, taz_list)

        ## High Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI3'] + p161],
               'HOV'  : [DfU['HOVI3'] + p163],
               'WTra' : [DfU['BusI3'], DfU['RalI3']],
               'Acti' : [DfU['Walk'], DfU['Bike']],
               'TNC'  : [DfU['TNCI3']]
               }
        I3A2_Dict = MChM.Calc_Prob(eb, Dict, "HbShLSI3A2", thet, 'hbshopatr', LS_Coeff, modes_dict, taz_list)

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

        LambdaList = [-0.269174,-0.308665,-0.288528,-0.269174,-0.308665,-0.288528,-0.269174,-0.308665,-0.288528]




        AlphaList =  [0.004639,0.004853,0.005203,0.004639,0.004853,0.005203,0.004639,0.004853,0.005203]




        GammaList =  [-0.000065,-0.000066,-0.000092,-0.000065,-0.000066,-0.000092,-0.000065,-0.000066,-0.000092]


        Kij = util.get_matrix_numpy(eb, "Kij_hbshop")

        Bridge_Factor = 0.5

        MChM.ImpCalc(eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, util.get_matrix_numpy(eb, "mfdistAON"), Kij, "HbShBl_BPen", Bridge_Factor)
        MChM.one_dim_matrix_balancing(eb, mo_list, md_list, imp_list, out_list)


#       ##############################################################################
#        ##       Calculate Demand
#       ##############################################################################

        I1A0_Dict = MChM.Calc_Demand(eb, I1A0_Dict, "HbShP-AI1A0")
        I1A1_Dict = MChM.Calc_Demand(eb, I1A1_Dict, "HbShP-AI1A1")
        I1A2_Dict = MChM.Calc_Demand(eb, I1A2_Dict, "HbShP-AI1A2")
        I2A0_Dict = MChM.Calc_Demand(eb, I2A0_Dict, "HbShP-AI2A0")
        I2A1_Dict = MChM.Calc_Demand(eb, I2A1_Dict, "HbShP-AI2A1")
        I2A2_Dict = MChM.Calc_Demand(eb, I2A2_Dict, "HbShP-AI2A2")
        I3A0_Dict = MChM.Calc_Demand(eb, I3A0_Dict, "HbShP-AI3A0")
        I3A1_Dict = MChM.Calc_Demand(eb, I3A1_Dict, "HbShP-AI3A1")
        I3A2_Dict = MChM.Calc_Demand(eb, I3A2_Dict, "HbShP-AI3A2")

        # SOV Trips
        SOVI1 = I1A0_Dict['SOV'][0] + I1A1_Dict['SOV'][0] + I1A2_Dict['SOV'][0]
        SOVI2 = I2A0_Dict['SOV'][0] + I2A1_Dict['SOV'][0] + I2A2_Dict['SOV'][0]
        SOVI3 = I3A0_Dict['SOV'][0] + I3A1_Dict['SOV'][0] + I3A2_Dict['SOV'][0]

        # HOV Trips
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


        del I1A0_Dict, I1A1_Dict, I1A2_Dict
        del I2A0_Dict, I2A1_Dict, I2A2_Dict
        del I3A0_Dict, I3A1_Dict, I3A2_Dict

#       ##############################################################################
#        ##       Get Time Slice Factors
#       ##############################################################################

        min_val=0.000143
        purp='hbshop'

        # setup for hbw auto time slice matrices
        conn = util.get_rtm_db(eb)
        ts_uw = pd.read_sql("SELECT * FROM timeSlicingFactorsGb", conn)
		# bus and rail AM PM factors
        ts_uw_b = pd.read_sql("SELECT * FROM timeSlicingFactors where mode='Bus' ", conn)
        ts_uw_r = pd.read_sql("SELECT * FROM timeSlicingFactors where mode='Rail'", conn)

        conn.close()

        # build basic ij mat with gb for production end and internal or external gb for attraction
        df_mats = util.get_ijensem_df(eb, ensem_o = 'gb')
        df_mats['IX'] = np.where(df_mats['gb_i']==df_mats['gb_j'], 'I', 'X')

        # build basic ij mat with gb for production end
        df_mats_br = util.get_ijensem_df(eb, ensem_o = 'gb')
        df_mats_br['IX'] = 'IX'

        Auto_AM_Fct_PA = MChM.ts_mat(df_mats, ts_uw, min_val, purp, 'AM', 'PtoA', NoTAZ)
        Auto_MD_Fct_PA = MChM.ts_mat(df_mats, ts_uw, min_val, purp, 'MD', 'PtoA', NoTAZ)
        Auto_PM_Fct_PA = MChM.ts_mat(df_mats, ts_uw, min_val, purp, 'PM', 'PtoA', NoTAZ)

        Auto_AM_Fct_AP = MChM.ts_mat(df_mats, ts_uw, min_val, purp, 'AM', 'AtoP', NoTAZ)
        Auto_MD_Fct_AP = MChM.ts_mat(df_mats, ts_uw, min_val, purp, 'MD', 'AtoP', NoTAZ)
        Auto_PM_Fct_AP = MChM.ts_mat(df_mats, ts_uw, min_val, purp, 'PM', 'AtoP', NoTAZ)

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

        TNCI1_AM = TNCI1*Auto_AM_Fct_PA + TNCI1.transpose()*Auto_AM_Fct_AP  # Low Income
        TNCI1_MD = TNCI1*Auto_MD_Fct_PA + TNCI1.transpose()*Auto_MD_Fct_AP
        TNCI1_PM = TNCI1*Auto_PM_Fct_PA + TNCI1.transpose()*Auto_PM_Fct_AP

        TNCI2_AM = TNCI2*Auto_AM_Fct_PA + TNCI2.transpose()*Auto_AM_Fct_AP  # Med Income
        TNCI2_MD = TNCI2*Auto_MD_Fct_PA + TNCI2.transpose()*Auto_MD_Fct_AP
        TNCI2_PM = TNCI2*Auto_PM_Fct_PA + TNCI2.transpose()*Auto_PM_Fct_AP

        TNCI3_AM = TNCI3*Auto_AM_Fct_PA + TNCI3.transpose()*Auto_AM_Fct_AP  # High Income
        TNCI3_MD = TNCI3*Auto_MD_Fct_PA + TNCI3.transpose()*Auto_MD_Fct_AP
        TNCI3_PM = TNCI3*Auto_PM_Fct_PA + TNCI3.transpose()*Auto_PM_Fct_AP


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
        util.set_matrix_numpy(eb, "HbShTNCI1PerTrips", TNCI1)
        util.set_matrix_numpy(eb, "HbShTNCI2PerTrips", TNCI2)
        util.set_matrix_numpy(eb, "HbShTNCI3PerTrips", TNCI3)


        # SOV
        # AM
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_1_Am", SOVI1_AM)
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_2_Am", SOVI2_AM)
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_3_Am", SOVI3_AM)
        # MD
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_1_Md", SOVI1_MD)
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_2_Md", SOVI2_MD)
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_3_Md", SOVI3_MD)
        # PM
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_1_Pm", SOVI1_PM)
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_2_Pm", SOVI2_PM)
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_3_Pm", SOVI3_PM)

        # HOV
        # AM
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_1_Am", HOVI1_AM)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_2_Am", HOVI2_AM)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_3_Am", HOVI3_AM)
        # MD
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_1_Md", HOVI1_MD)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_2_Md", HOVI2_MD)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_3_Md", HOVI3_MD)
        # PM
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_1_Pm", HOVI1_PM)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_2_Pm", HOVI2_PM)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_3_Pm", HOVI3_PM)

        # TNC
        # AM
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_1_Am", TNCI1_AM)
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_2_Am", TNCI2_AM)
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_3_Am", TNCI3_AM)
        # MD
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_1_Md", TNCI1_MD)
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_2_Md", TNCI2_MD)
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_3_Md", TNCI3_MD)
        # PM
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_1_Pm", TNCI1_PM)
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_2_Pm", TNCI2_PM)
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_3_Pm", TNCI3_PM)
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
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_1_Am", SOVI1_AM)
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_2_Am", SOVI2_AM)
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_3_Am", SOVI3_AM)
        # MD
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_1_Md", SOVI1_MD)
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_2_Md", SOVI2_MD)
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_3_Md", SOVI3_MD)
        # PM
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_1_Pm", SOVI1_PM)
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_2_Pm", SOVI2_PM)
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_3_Pm", SOVI3_PM)


        # HOV (includes TNC)
        # AM
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_1_Am", AuDr_HOVI1_AM)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_2_Am", AuDr_HOVI2_AM)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_3_Am", AuDr_HOVI3_AM)
        # MD
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_1_Md", AuDr_HOVI1_MD)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_2_Md", AuDr_HOVI2_MD)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_3_Md", AuDr_HOVI3_MD)
        # PM
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_1_Pm", AuDr_HOVI1_PM)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_2_Pm", AuDr_HOVI2_PM)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_3_Pm", AuDr_HOVI3_PM)

        ## Dump demands to SQL Database
        # AM
        Zone_Index_O = util.get_matrix_numpy(eb, "zoneindex") + np.zeros((1, NoTAZ))
        Zone_Index_D = Zone_Index_O.transpose()

        T_SOV_AM = np.where((Zone_Index_O>9999) & (Zone_Index_D>9999), SOVI1_AM + SOVI2_AM + SOVI3_AM, 0)
        T_HOV_AM = HOVI1_AM + HOVI2_AM + HOVI3_AM
        T_TNC_AM = TNCI1_AM + TNCI2_AM + TNCI3_AM

        # MD
        T_SOV_MD = np.where((Zone_Index_O>9999) & (Zone_Index_D>9999), SOVI1_MD + SOVI2_MD + SOVI3_MD, 0)
        T_HOV_MD = HOVI1_MD + HOVI2_MD + HOVI3_MD
        T_TNC_MD = TNCI1_MD + TNCI2_MD + TNCI3_MD

        # PM
        T_SOV_PM = np.where((Zone_Index_O>9999) & (Zone_Index_D>9999), SOVI1_PM + SOVI2_PM + SOVI3_PM, 0)
        T_HOV_PM = HOVI1_PM + HOVI2_PM + HOVI3_PM
        T_TNC_PM = TNCI1_PM + TNCI2_PM + TNCI3_PM

        # Take park and ride out of auto trips
        T_SOV = np.where((Zone_Index_O>9999) & (Zone_Index_D>9999), SOVI1 + SOVI2 + SOVI3, 0)
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
        mode_list_am_pm = ['sov', 'hov', 'bus', 'rail', 'walk', 'bike', 'tnc']
        mode_list_md = ['sov', 'hov', 'bus', 'rail', 'walk', 'bike', 'tnc']
        mode_list_daily = ['sov', 'hov', 'bus', 'rail', 'walk', 'bike', 'tnc']

        AM_Demand_List = [T_SOV_AM, T_HOV_AM, Bus_AM, Rail_AM, Walk_AM, Bike_AM, T_TNC_AM]
        MD_Demand_List = [T_SOV_MD, T_HOV_MD, Bus_MD, Rail_MD, Walk_MD, Bike_MD, T_TNC_MD]
        PM_Demand_List = [T_SOV_PM, T_HOV_PM, Bus_PM, Rail_PM, Walk_PM, Bike_PM, T_TNC_PM]
        Daily_Demand_List = [T_SOV, T_HOV, Bus, Rail, Walk, Bike, T_TNC]

        zero_demand = 0
        purp = "hbshop"

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
        util.initmat(eb, "mf9030", "HbShLSI1A0", "LogSum HbSh I1 A0", 0)
        util.initmat(eb, "mf9031", "HbShLSI1A1", "LogSum HbSh I1 A1", 0)
        util.initmat(eb, "mf9032", "HbShLSI1A2", "LogSum HbSh I1 A2", 0)
        util.initmat(eb, "mf9033", "HbShLSI2A0", "LogSum HbSh I2 A0", 0)
        util.initmat(eb, "mf9034", "HbShLSI2A1", "LogSum HbSh I2 A1", 0)
        util.initmat(eb, "mf9035", "HbShLSI2A2", "LogSum HbSh I2 A2", 0)
        util.initmat(eb, "mf9036", "HbShLSI3A0", "LogSum HbSh I3 A0", 0)
        util.initmat(eb, "mf9037", "HbShLSI3A1", "LogSum HbSh I3 A1", 0)
        util.initmat(eb, "mf9038", "HbShLSI3A2", "LogSum HbSh I3 A2", 0)

        util.initmat(eb, "mf9330", "HbShLSAUI1A0", "LogSum HbSh Auto I1 A0", 0)
        util.initmat(eb, "mf9331", "HbShLSAUI1A1", "LogSum HbSh Auto I1 A1", 0)
        util.initmat(eb, "mf9332", "HbShLSAUI1A2", "LogSum HbSh Auto I1 A2", 0)
        util.initmat(eb, "mf9333", "HbShLSAUI2A0", "LogSum HbSh Auto I2 A0", 0)
        util.initmat(eb, "mf9334", "HbShLSAUI2A1", "LogSum HbSh Auto I2 A1", 0)
        util.initmat(eb, "mf9335", "HbShLSAUI2A2", "LogSum HbSh Auto I2 A2", 0)
        util.initmat(eb, "mf9336", "HbShLSAUI3A0", "LogSum HbSh Auto I3 A0", 0)
        util.initmat(eb, "mf9337", "HbShLSAUI3A1", "LogSum HbSh Auto I3 A1", 0)
        util.initmat(eb, "mf9338", "HbShLSAUI3A2", "LogSum HbSh Auto I3 A2", 0)

        util.initmat(eb, "mf9430", "HbShLSTRI1A0", "LogSum HbSh Transit I1 A0", 0)
        util.initmat(eb, "mf9431", "HbShLSTRI1A1", "LogSum HbSh Transit I1 A1", 0)
        util.initmat(eb, "mf9432", "HbShLSTRI1A2", "LogSum HbSh Transit I1 A2", 0)
        util.initmat(eb, "mf9433", "HbShLSTRI2A0", "LogSum HbSh Transit I2 A0", 0)
        util.initmat(eb, "mf9434", "HbShLSTRI2A1", "LogSum HbSh Transit I2 A1", 0)
        util.initmat(eb, "mf9435", "HbShLSTRI2A2", "LogSum HbSh Transit I2 A2", 0)
        util.initmat(eb, "mf9436", "HbShLSTRI3A0", "LogSum HbSh Transit I3 A0", 0)
        util.initmat(eb, "mf9437", "HbShLSTRI3A1", "LogSum HbSh Transit I3 A1", 0)
        util.initmat(eb, "mf9438", "HbShLSTRI3A2", "LogSum HbSh Transit I3 A2", 0)

        util.initmat(eb, "mf9530", "HbShLSACI1A0", "LogSum HbSh Active I1 A0", 0)
        util.initmat(eb, "mf9531", "HbShLSACI1A1", "LogSum HbSh Active I1 A1", 0)
        util.initmat(eb, "mf9532", "HbShLSACI1A2", "LogSum HbSh Active I1 A2", 0)
        util.initmat(eb, "mf9533", "HbShLSACI2A0", "LogSum HbSh Active I2 A0", 0)
        util.initmat(eb, "mf9534", "HbShLSACI2A1", "LogSum HbSh Active I2 A1", 0)
        util.initmat(eb, "mf9535", "HbShLSACI2A2", "LogSum HbSh Active I2 A2", 0)
        util.initmat(eb, "mf9536", "HbShLSACI3A0", "LogSum HbSh Active I3 A0", 0)
        util.initmat(eb, "mf9537", "HbShLSACI3A1", "LogSum HbSh Active I3 A1", 0)
        util.initmat(eb, "mf9538", "HbShLSACI3A2", "LogSum HbSh Active I3 A2", 0)

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
        util.initmat(eb, "mf3340", "HbShTNCI1PerTrips", "HbSh TNC Low Income Per-Trips", 0)
        util.initmat(eb, "mf3341", "HbShTNCI2PerTrips", "HbSh TNC Med Income Per-Trips", 0)
        util.initmat(eb, "mf3342", "HbShTNCI3PerTrips", "HbSh TNC High Income Per-Trips", 0)


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
