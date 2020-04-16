##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage2.hbuniv
##--Purpose:
##---------------------------------------------------------------------
import inro.modeller as _m
import numpy as np
import pandas as pd

class HbWork(_m.Tool()):

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Home Base University"
        pb.description = "Calculate home base University person trips by mode and time of day"
        pb.branding_text = "TransLink"
        pb.runnable = False
        return pb.render()

    @_m.logbook_trace("Run Home Base University")
    def __call__(self, eb, Bus_Bias, Rail_Bias, WCE_Bias):
        util = _m.Modeller().tool("translink.util")
        MChM = _m.Modeller().tool("translink.RTM3.stage2.modechoiceutils")

        tnc_av_rate = 0.0

        tnc_xfer_time = float(eb.matrix("tncxtime").data)
        self.matrix_batchins(eb)
        NoTAZ = len(util.get_matrix_numpy(eb, "mo51"))
        tnc_occupancy = float(util.get_matrix_numpy(eb, 'TNCOccHbu'))  # TNC Occupancy
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
                     'TranAux': 40.0,
                     'WCEWat' : 30.0,
                     'WCEAux' : 40.0,
                     'TranBrd': 4.0,
                     'BRTotLow': 10.0,
                     'BRTotHig': 120.0,
                     'WCTotLow': 30.0,
                     'WCTotHig': 130.0,
                     #'PRAutTim': 0.0,
                     'PRAutTim_min': 0.0,
                     'PRAutTim_max': 35.0,
                     'br_ratio': 2.0,
                     'r_time'  : 20.0,
                     'pr_ratio': 2.0
                    }

        # Declare Utilities Data Frame
        DfU = {}

        # Add Coefficients

        p2   = -2.655347
        p4   =  2.767892
        p6   =  4.112298
        p10  =  5.727228
        p11  = -0.439153
        p12  = -0.352974
        p15  = -0.061574
        p17  = -0.212326
        p18  = -0.112302
        p19  = -0.695843
        p20  = -2.767938
        p21  = -0.807705
        p602 =  0.122524
        p991 =  0.097689
        thet =  0.459772
        LS_Coeff = 0.4

        # PNR Coefficients
        # Borrowed from HBW purpose
        p5 = -2.5
        p7 = -2.5
        p34 = 0

        # TNC Cost Factors
        # alpha_tnc and beta_tnc are calculated in Blended_Skims.py
        # TNC Coefficients and Calibration
        p30 =  -2.0  #
        tnc_cost_scale = 30  # Coeff3 = coeff 2/lambda
        tnc_cost_exponent = 2 # TNC Cost exponent ; non-linear calibration constant
        p604 = 0.1 #   TNC Accessibility measure
        tnc_wait_percep = 1.5 # multiplied to IVTT coefficient

        # TNC/Taxi Access to Transit Coefficient
        # Additional constant on top of PNR Coeff by bus, rail and wce
        p31 =  0
#        ##############################################################################
#        ##       Auto Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        MaxPark = 10.0
        Hov_scale = 0.75
        tnc_scale = 0.75

        ##
        Occ = util.get_matrix_numpy(eb, 'HOVOccHbu')
        Df['ParkCost'] = util.get_matrix_numpy(eb, 'prk8hr') # 8 hr parking
        Df['ParkCost'][Df['ParkCost']>MaxPark] = MaxPark
        Df['ParkCost'] = Df['ParkCost'].reshape(1, NoTAZ) + np.zeros((NoTAZ, 1))

        ##
        Df['AutoCosSOV'] = util.get_matrix_numpy(eb, 'HbUBlSovCost')
        Df['AutoTimSOV'] = util.get_matrix_numpy(eb, 'HbUBlSovTime')
        Df['AutoTotCosSOV'] = Df['AutoCosSOV'] + Df['ParkCost']

        Df['AutoCosHOV'] = util.get_matrix_numpy(eb, 'HbUBlHovCost')
        Df['AutoTimHOV'] = util.get_matrix_numpy(eb, 'HbUBlHovTime')
        Df['AutoTotCosHOV'] = Df['AutoCosHOV'] + Df['ParkCost']

        Df['TNCCost'] = util.get_matrix_numpy(eb, 'HbUBlTNCCost')
        Df['TNCWaitTime'] = util.get_matrix_numpy(eb, 'tncwaittime')
        Df['TNCWaitTime'] = Df['TNCWaitTime'].reshape(NoTAZ,1)+ np.zeros((1,NoTAZ))

        # TNC Accessibbility
        Df['TNCAccess'] = util.get_matrix_numpy(eb,'tncuniAccLn').reshape(NoTAZ, 1) + np.zeros((1, NoTAZ))

        # Utilities
        # SOV
        # SOV Utility for all incomes
        Df['GeUtl'] = (0
                      + p15*Df['AutoTimSOV']
                      + p12*Df['AutoTotCosSOV'])
        # Check SOV Availability
        Df['GeUtl']  = MChM.AutoAvail(Df['AutoCosSOV'], Df['GeUtl'], AvailDict)

        DfU['SOV'] = Df['GeUtl']

        ##     HOV - 2 and more persons
        # HOV
        # HOV Utility for all incomes

        Df['GeUtl'] = ( p2
                      + p15*Df['AutoTimHOV']
                      + p12*Df['AutoTotCosHOV']/(pow(Occ,Hov_scale)))

        # Check HOV Availability
        Df['GeUtl'] = MChM.AutoAvail(Df['AutoCosHOV'], Df['GeUtl'], AvailDict)
        DfU['HOV']  = Df['GeUtl']

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
        UPass_Disc = 0.1
        B_IVT_perc = 1.06
        ##
        ##    Bus and rail related variables for University purpose
        ##
        Df['BusIVT'] = util.get_matrix_numpy(eb, 'HbUBlBusIvtt')
        Df['BusWat'] = util.get_matrix_numpy(eb, 'HbUBlBusWait')
        Df['BusAux'] = util.get_matrix_numpy(eb, 'HbUBlBusAux')
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'HbUBlBusBoard')
        Df['BusFar'] = util.get_matrix_numpy(eb, 'HbUBlBusFare')
        Df['BusTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux'] # Bus Total Travel Time
        Df['BusIVTBRT'] = util.get_matrix_numpy(eb, 'HbUBlBusIvttBRT') #In vehicle Bus BRT time

        Df['RalIVR'] = util.get_matrix_numpy(eb, 'HbUBlRailIvtt')
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'HbUBlRailIvttBus')
        Df['RalWat'] = util.get_matrix_numpy(eb, 'HbUBlRailWait')
        Df['RalAux'] = util.get_matrix_numpy(eb, 'HbUBlRailAux')
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'HbUBlRailBoard')
        Df['RalFar'] = util.get_matrix_numpy(eb, 'HbUBlRailFare')

        Df['RalTot'] = Df['RalIVB'] + Df['RalIVR'] + Df['RalWat'] + Df['RalAux'] # Bus Total Travel Time
        Df['RalIBR'] = Df['RalIVB']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Bus IVT to Total Time
        Df['RalIRR'] = Df['RalIVR']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Rail IVT to Total Time
        Df['RalIVBRT'] = util.get_matrix_numpy(eb, 'HbUBlRailIvttBRT') #In vehicle Rail time BRT
        Df['RalIVLRT'] = util.get_matrix_numpy(eb, 'HbUBlRailIvttLRT') #In vehicle Rail time LRT

        Df['AutoDis'] = util.get_matrix_numpy(eb, "mfdistAON") # Distance
        Df['IntZnl'] = np.identity(NoTAZ)
        Df['UniAccess'] = util.get_matrix_numpy(eb, 'uniAccLn').reshape(NoTAZ,1) + np.zeros((1, NoTAZ))

        # Calculate mode specific constant for BRT and LRT as a fraction of bus and rail constants
        BRT_fac, LRT_fac = MChM.calc_BRT_LRT_asc(eb, p4, p6)

        p15b = p15*B_IVT_perc
        BRT_ivt, LRT_ivt = MChM.calc_BRT_LRT_ivt(eb, p15b, p15)

        Bus_const = ((p4 * (Df['BusIVT']-Df['BusIVTBRT'])) + (BRT_fac * Df['BusIVTBRT'])) / (Df['BusIVT'] + Tiny)
        Rail_const = (p4 * (Df['RalIVB']-Df['RalIVBRT'])
                    + BRT_fac * Df['RalIVBRT']
                    + LRT_fac * Df['RalIVLRT']
                    + p6 * (Df['RalIVR']-Df['RalIVLRT'])) / (Df['RalIVR'] + Df['RalIVB'] + Tiny)
        # Utilities
        # Bus Utility
        # Bus Utility for all incomes
        Df['GeUtl'] = ( Bus_const
                      + Bus_Bias
                      + p12*(Df['BusFar'])*UPass_Disc
                      + p15*(Df['BusIVT'] - Df['BusIVTBRT'])*B_IVT_perc
                      + BRT_ivt*(Df['BusIVTBRT'])
                      + p17*Df['BusWat']
                      + p18*Df['BusAux']
                      + p19*Df['BusBrd']
                      + p602*Df['UniAccess']
                      + p991*Df['AutoDis']
                      )

        # Check Bus Availability
        Df['GeUtl'] = MChM.BusAvail(Df, Df['GeUtl'], AvailDict)
        DfU['Bus'] = Df['GeUtl']

        #     Rail Utility
        ##
        Df['GeUtl'] = ( Rail_const
                      + Rail_Bias
                      + p12*(Df['RalFar'])*UPass_Disc
                      + p15*(Df['RalIVB'] - Df['RalIVBRT'])*B_IVT_perc
                      + BRT_ivt*(Df['RalIVBRT'])
                      + p15*(Df['RalIVR'] - Df['RalIVLRT'])
                      + LRT_ivt*(Df['RalIVLRT'])
                      + p17*Df['RalWat']
                      + p18*Df['RalAux']
                      + p19*Df['RalBrd']
                      + p602*Df['UniAccess']
                      + p991*Df['AutoDis']
                      )

        # Check Rail Availability
        Df['GeUtl'] = MChM.RailAvail(Df, Df['GeUtl'],AvailDict)
        DfU['Ral'] = Df['GeUtl']

#        ##############################################################################
#        ##       Park and Ride to Transit Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        Df['BAuCos'] = util.get_matrix_numpy(eb, 'HbUBlBAuPRCost')  # Bus PR Drive Distance
        Df['BAuTim'] = util.get_matrix_numpy(eb, 'HbUBlBAuPRTime')  # Bus PR Drive Time
        Df['BAuTotCos'] = Df['BAuCos'] + util.get_matrix_numpy(eb, 'HbUBAuPrkCst')  # Bus PR Drive Cost
        Df['BAuTrm'] = util.get_matrix_numpy(eb, 'HbUBAuTrmTim')  # Bus PR Terminal Time
        Df['BusIVT'] = util.get_matrix_numpy(eb, 'HbUBlBAuBusIvtt')  # Bus IVTT
        Df['BusWat'] = util.get_matrix_numpy(eb, 'HbUBlBAuBusWait')  # Bus Wait Time
        Df['BusAux'] = util.get_matrix_numpy(eb, 'HbUBlBAuBusAux')  # Bus Walk Time
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'HbUBlBAuBusBoard')  # Bus Boarding Time
        Df['BusFar'] = util.get_matrix_numpy(eb, 'HbUBlBAuBusFare')  # Bus Fare
        Df['BusTot'] = util.get_matrix_numpy(eb, 'HbUBlBusIvtt') + util.get_matrix_numpy(eb,'HbUBlBusWait') + util.get_matrix_numpy(eb, 'HbUBlBusAux')
        Df['BusIVT'] = util.get_matrix_numpy(eb, 'HbUBlBusIvtt')  # In vehicle Bus time
        Df['BAuTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux'] + Df['BAuTim']  # Total Travel Time
        Df['BAuIBR'] = Df['BusIVT'] / (Df['BusIVT'] + Df['BAuTim'] + Tiny)  # Ratio of Time on Bus to total travel time
        Df['WBusFar'] = util.get_matrix_numpy(eb, 'HbUBlBusFare')  # Walk to Transit Fare

        Df['RAuCos'] = util.get_matrix_numpy(eb, 'HbUBlRAuPRCost')  # Rail PR Drive Distance
        Df['RAuTim'] = util.get_matrix_numpy(eb, 'HbUBlRAuPRTime')  # Rail PR Drive Time
        Df['RAuTotCos'] = Df['RAuCos'] + util.get_matrix_numpy(eb, 'HbURAuPrkCst')  # Rail PR Drive Cost
        Df['RAuTrm'] = util.get_matrix_numpy(eb, 'HbURAuTrmTim')  # Rail PR Terminal Time
        Df['RalIVR'] = util.get_matrix_numpy(eb, 'HbUBlRAuRailIvtt')  # IVT on Rail
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'HbUBlRAuRailIvttBus')  # IVT on Bus
        Df['RalWat'] = util.get_matrix_numpy(eb, 'HbUBlRAuRailWait')  # Rail Wait Time
        Df['RalAux'] = util.get_matrix_numpy(eb, 'HbUBlRAuRailAux')  # Rail Walk Time
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'HbUBlRAuRailBoard')  # Rail Board Time
        Df['RalFar'] = util.get_matrix_numpy(eb, 'HbUBlRAuRailFare')  # Rail Fare
        Df['RAuTot'] = Df['RalIVB'] + Df['RalIVR'] + Df['RalWat'] + Df['RalAux'] + Df['RAuTim']  # Total Travel Time
        Df['RAuIBR'] = Df['RalIVB'] / (
                    Df['RalIVB'] + Df['RalIVR'] + Df['RAuTim'] + Tiny)  # Ratio of Time on Bus to total travel time
        Df['RAuIRR'] = Df['RalIVR'] / (
                    Df['RalIVB'] + Df['RalIVR'] + Df['RAuTim'] + Tiny)  # Ratio of Time on Rail to total travel time

        Df['WRalFar'] = util.get_matrix_numpy(eb, 'HbUBlRailFare')
        Df['WRalIVR'] = util.get_matrix_numpy(eb, 'HbUBlRailIvtt')  # In vehicle Rail time on rail
        Df['RalTot'] = (util.get_matrix_numpy(eb, 'HbUBlRailIvtt') + util.get_matrix_numpy(eb, 'HbUBlRailIvttBus')
                        + util.get_matrix_numpy(eb, 'HbUBlRailWait') + util.get_matrix_numpy(eb, 'HbUBlRailAux'))

        Df['IntZnl'] = np.identity(NoTAZ)  # Intra-zonal
        Df['AutoDis'] = util.get_matrix_numpy(eb, "mfdistAON")  # Distance

        # Utilities
        # PR Bus Utility
        Df['GeUtl'] = (p34 + p5 +
                       + p12 * Df['BusFar'] * UPass_Disc
                       + p12 * Df['BAuTotCos']
                       + p4 * Df['BAuIBR']
                       + p15 * Df['BAuTim']
                       + p15 * Df['BusIVT'] * B_IVT_perc
                       + p17 * Df['BusWat']
                       + p18 * Df['BusAux']
                       + p18 * Df['BAuTrm']
                       + p19 * Df['BusBrd']
                       + p991 * Df['AutoDis'])

        # Check availability conditions else add high negative utility (-99999)
        DfU['BusPnR'] = MChM.BAuAvail(Df, Df['GeUtl'], AvailDict)

        # Rail Utility
        # PR Rail Utility
        Df['GeUtl'] = (p34 + p7 +
                       + p4 * Df['RAuIBR']
                       + p6 * Df['RAuIRR']
                       + p12 * (Df['RalFar'] * UPass_Disc + Df['RAuTotCos'])
                       + p15 * Df['RAuTim']
                       + p15 * Df['RalIVB'] * B_IVT_perc
                       + p15 * Df['RalIVR']
                       + p17 * Df['RalWat']
                       + p18 * (Df['RalAux'] + Df['RAuTrm'])
                       + p19 * Df['RalBrd']
                       + p991 * Df['AutoDis'])

        # Check availability conditions else add high negative utility (-99999)
        DfU['RaiPnR'] = MChM.RAuAvail(Df, Df['GeUtl'], AvailDict)
#        ##############################################################################
#        ##       TNC/Taxi-and-Ride to Transit Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        Df['BAuCos'] = util.get_matrix_numpy(eb, 'HbUBlBAuTNCCost')  # Bus TNC Drive Distance
        Df['BAuTim'] = util.get_matrix_numpy(eb, 'HbUBlBAuTNCTime')  # Bus TNC Drive Time

        Df['BusIVT'] = util.get_matrix_numpy(eb, 'HbUBlBTncBusIvtt')  # Bus IVTT
        Df['BusWat'] = util.get_matrix_numpy(eb, 'HbUBlBTncBusWait')  # Bus Wait Time
        Df['BusAux'] = util.get_matrix_numpy(eb, 'HbUBlBTncBusAux')  # Bus Walk Time
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'HbUBlBTncBusBoard')  # Bus Boarding Time
        Df['BusFar'] = util.get_matrix_numpy(eb, 'HbUBlBTncBusFare')  # Bus Fare
        Df['BusTot'] = util.get_matrix_numpy(eb, 'HbUBlBusIvtt') + util.get_matrix_numpy(eb,'HbUBlBusWait') + util.get_matrix_numpy(eb, 'HbUBlBusAux')
        Df['BusIVT'] = util.get_matrix_numpy(eb, 'HbUBlBusIvtt')  # In vehicle Bus time
        Df['BAuTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux'] + Df['BAuTim']  # Total Travel Time
        Df['BAuIBR'] = Df['BusIVT'] / (Df['BusIVT'] + Df['BAuTim'] + Tiny)  # Ratio of Time on Bus to total travel time
        Df['WBusFar'] = util.get_matrix_numpy(eb, 'HbUBlBusFare')  # Walk to Transit Fare

        Df['RAuCos'] = util.get_matrix_numpy(eb, 'HbUBlRAuTNCCost')  # Rail TNC Drive Distance
        Df['RAuTim'] = util.get_matrix_numpy(eb, 'HbUBlRAuTNCTime')  # Rail TNC Drive Time

        Df['RalIVR'] = util.get_matrix_numpy(eb, 'HbUBlRTncRailIvtt')  # IVT on Rail
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'HbUBlRTncRailIvttBus')  # IVT on Bus
        Df['RalWat'] = util.get_matrix_numpy(eb, 'HbUBlRTncRailWait')  # Rail Wait Time
        Df['RalAux'] = util.get_matrix_numpy(eb, 'HbUBlRTncRailAux')  # Rail Walk Time
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'HbUBlRTncRailBoard')  # Rail Board Time
        Df['RalFar'] = util.get_matrix_numpy(eb, 'HbUBlRTncRailFare')  # Rail Fare
        Df['RAuTot'] = Df['RalIVB'] + Df['RalIVR'] + Df['RalWat'] + Df['RalAux'] + Df['RAuTim']  # Total Travel Time
        Df['RAuIBR'] = Df['RalIVB'] / (
                Df['RalIVB'] + Df['RalIVR'] + Df['RAuTim'] + Tiny)  # Ratio of Time on Bus to total travel time
        Df['RAuIRR'] = Df['RalIVR'] / (
                Df['RalIVB'] + Df['RalIVR'] + Df['RAuTim'] + Tiny)  # Ratio of Time on Rail to total travel time

        Df['WRalFar'] = util.get_matrix_numpy(eb, 'HbUBlRailFare')
        Df['WRalIVR'] = util.get_matrix_numpy(eb, 'HbUBlRailIvtt')  # In vehicle Rail time on rail
        Df['RalTot'] = (util.get_matrix_numpy(eb, 'HbUBlRailIvtt') + util.get_matrix_numpy(eb, 'HbUBlRailIvttBus')
                        + util.get_matrix_numpy(eb, 'HbUBlRailWait') + util.get_matrix_numpy(eb, 'HbUBlRailAux'))

        Df['IntZnl'] = np.identity(NoTAZ)  # Intra-zonal
        Df['AutoDis'] = util.get_matrix_numpy(eb, "mfdistAON")  # Distance
        Df['AutoDisSqd'] = Df['AutoDis'] * Df['AutoDis']  # Distance-squared
        Df['LogAutoDis'] = np.log(Df['AutoDis'] + Tiny)  # log-distance

        Df['TNCWaitTime'] = util.get_matrix_numpy(eb, 'tncwaittime')
        Df['TNCWaitTime'] = Df['TNCWaitTime'].reshape(NoTAZ, 1) + np.zeros((1, NoTAZ))

        # Utilities
        # TNC Bus Utility
        # TNC Bus Common Utility for all incomes
        Df['GeUtl'] = (p31 + p5 +
                       + p12 * Df['BusFar'] * UPass_Disc
                       + p12 * Df['BAuCos']
                       + p4 * Df['BAuIBR']
                       + p15 * Df['BAuTim']
                       + p15 * Df['BusIVT'] * B_IVT_perc
                       + tnc_wait_percep* p15 * Df['TNCWaitTime']
                       + p17 * Df['BusWat']
                       + p18 * Df['BusAux']
                       + p18 * tnc_xfer_time
                       + p19 * Df['BusBrd']
                       + p991 * Df['AutoDis'])

        # Check availability conditions else add high negative utility (-99999)
        DfU['BusTNC'] = MChM.BAuAvail(Df, Df['GeUtl'], AvailDict)

        # Rail Utility
        # TNC Rail Utility
        # TNC Rail Common Utility for all incomes
        Df['GeUtl'] = (p31 + p7 +
                       + tnc_wait_percep* p15 * Df['TNCWaitTime']
                       + p4 * Df['RAuIBR']
                       + p6 * Df['RAuIRR']
                       + p12 * (Df['RalFar'] * UPass_Disc + Df['RAuCos'])
                       + p15 * Df['RAuTim']
                       + p15 * Df['RalIVB'] * B_IVT_perc
                       + p15 * Df['RalIVR']
                       + p17 * Df['RalWat']
                       + p18 * Df['RalAux']
                       + p18 * tnc_xfer_time
                       + p19 * Df['RalBrd']
                       + p991 * Df['AutoDis'])

        # Check availability conditions else add high negative utility (-99999)
        DfU['RaiTNC'] = MChM.RAuAvail(Df, Df['GeUtl'], AvailDict)

#        ##############################################################################
#        ##
#        ##        Active Modes
#        ##        rs: HbU SOV distance is used.
#        ##
#        ##############################################################################

        Df = {}
        Df['AutoDis'] = util.get_matrix_numpy(eb, "mfdistAON") # Distance

        # Walk Utility
        DfU['Walk'] = ( p10
                      + p20*Df['AutoDis'])

        # Check Walk Availability
        DfU['Walk'] = MChM.WalkAvail(Df['AutoDis'], DfU['Walk'], AvailDict)

        # Bike Utility
        DfU['Bike'] = ( p11
                      + p21*Df['AutoDis'])

        # Check Bike Availability
        DfU['Bike'] = MChM.BikeAvail(Df['AutoDis'], DfU['Bike'], AvailDict)

        del Df

#        ##############################################################################
#        ##       Calculate Probabilities
#        ##############################################################################

        LrgU     = -99999.0
        taz_list = util.get_matrix_numpy(eb, 'zoneindex', reshape = False)

        Dict = {
               'SOV'  : [DfU['SOV']],
               'HOV'  : [DfU['HOV']],
               'WTra' : [DfU['Bus'], DfU['Ral']],
               'DTra':  [DfU['BusPnR'], DfU['RaiPnR'],
                         DfU['BusTNC'], DfU['RaiTNC']],
               'Acti' : [DfU['Walk'], DfU['Bike']],
               'TNC'  : [DfU['TNC']]
               }

        # get a list of all keys

        keys_list = list(Dict.keys())
        modes_dict = {'All':keys_list, 'Auto': ['SOV', 'HOV'], 'Auto2': ['SOV', 'HOV', 'TNC'],
                     'Transit': ['WTra', 'DTra'], 'TNC': ['TNC'], 'Active': ['Acti']}

        Prob_Dict = MChM.Calc_Prob(eb, Dict, "HbULS", thet, 'hbuatr', LS_Coeff, modes_dict, taz_list)
        del DfU, Dict

       ##############################################################################
        ##       Trip Distribution
       ##############################################################################

        Logsum =  ["HbULS"]

        imp_list = ["P-AFrictionFact1"]

        mo_list =  ["hbuprd"]

        md_list =  ["hbuatr"]

        out_list = ["HbUP-A"]



        LambdaList = [-0.106753]


        AlphaList =  [0.00103]


        GammaList =  [-0.000005]


        Kij = util.get_matrix_numpy(eb, "Kij_hbu")

        Bridge_Factor = 0

        MChM.ImpCalc(eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, util.get_matrix_numpy(eb, "mfdistAON"), Kij, "Zero", Bridge_Factor)
        MChM.two_dim_matrix_balancing(eb, mo_list, md_list, imp_list, out_list)


#       ##############################################################################
#        ##       Calculate Demand
#       ##############################################################################

        name_dict = {
            'SOV': ['SOV'],
            'HOV': ['HV2'],
            'WTra': ['Bus', 'Ral'],
            'DTra': ['BAu', 'RAu', 'BTnc', 'RTnc'],
            'Acti': ['Walk', 'Bike'],
            'TNC': ['TNC']
        }

        Demand_Dict = MChM.Calc_Demand(eb, Prob_Dict, "HbUP-A", name_dict)


        SOV =   Demand_Dict['SOV'][0]

        HOV =   Demand_Dict['HOV'][0]

        TNC = Demand_Dict['TNC'][0]

        Bus  =  Demand_Dict['WTra'][0]
        BAu  =  Demand_Dict['DTra'][0]
        BTnc =  Demand_Dict['DTra'][2]

        Rail =  Demand_Dict['WTra'][1]
        RAu  =  Demand_Dict['DTra'][1]
        RTnc =  Demand_Dict['DTra'][3]

        Walk =  Demand_Dict['Acti'][0]

        Bike =  Demand_Dict['Acti'][1]


        del Demand_Dict
        del Prob_Dict

#       ##############################################################################
#        ##       Get Time Slice Factors
#       ##############################################################################
        min_val=0.000143
        purp='hbu'

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

        # Auto factors return a  multi-dimensional array, the other modes return a scalar
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

#       #########################################################################################
#        ##       Split Park and Ride to Auto and Transit Legs
#       ##########################################################################################
        ## General Setup
        BLBsWk = util.get_matrix_numpy(eb, "buspr-lotChceWkAMPA").flatten()  # Best Lot Bus Work
        BLRlWk = util.get_matrix_numpy(eb, "railpr-lotChceWkAMPA").flatten()  # Best Lot Rail Work
        DfInt = util.get_pd_ij_df(eb)

        ## Bus
        Dfmerge = util.get_pd_ij_df(eb)  # pandas Dataframe
        Dfmerge['BL'] = BLBsWk  # best bus lot
        Dfmerge['BAu'] = BAu.flatten()

        DfmergedAuto = Dfmerge.groupby(['i', 'BL']).sum().reset_index()
        DfmergedTran = Dfmerge.groupby(['BL', 'j']).sum().reset_index()
        DfAuto, DfTran = self.splitpnr(DfmergedAuto, DfmergedTran, DfInt)

        # Store park and ride Demands separately for time slicing
        SOV_BAu = DfAuto['BAu'].values.reshape(NoTAZ, NoTAZ)  # low income SOV trips to PnR Zones
        Bus_BAu = DfTran['BAu'].values.reshape(NoTAZ, NoTAZ)  # bus trips from PnR zone to destination

        ## Rail
        Dfmerge = util.get_pd_ij_df(eb)
        Dfmerge['BL'] = BLRlWk
        Dfmerge['RAu'] = RAu.flatten()

        DfmergedAuto = Dfmerge.groupby(['i', 'BL']).sum().reset_index()
        DfmergedTran = Dfmerge.groupby(['BL', 'j']).sum().reset_index()
        DfAuto, DfTran = self.splitpnr(DfmergedAuto, DfmergedTran, DfInt)

        SOV_RAu = DfAuto['RAu'].values.reshape(NoTAZ, NoTAZ)  # low income SOV trips to PnR Zones
        Ral_RAu = DfTran['RAu'].values.reshape(NoTAZ, NoTAZ)  # rail trips from PnR zone to destination

        del Dfmerge, DfmergedAuto, DfmergedTran
        del DfAuto, DfTran


#       #########################################################################################
#       ##       Split TNC and Ride to Auto and Transit Legs
#       ##########################################################################################
        ## General Setup
        TncBsWk = util.get_matrix_numpy(eb, "bustnc-lotChceWkAMPA").flatten()  # Best Lot Bus Work
        TncRlWk = util.get_matrix_numpy(eb, "railtnc-lotChceWkAMPA").flatten()  # Best Lot Rail Work
        DfInt = util.get_pd_ij_df(eb)

        ## Bus
        Dfmerge = util.get_pd_ij_df(eb)  # pandas Dataframe
        Dfmerge['BL'] = TncBsWk  # best bus lot
        Dfmerge['BTnc'] = BTnc.flatten()

        DfmergedAuto = Dfmerge.groupby(['i', 'BL']).sum().reset_index()
        DfmergedTran = Dfmerge.groupby(['BL', 'j']).sum().reset_index()
        DfAuto, DfTran = self.splitpnr(DfmergedAuto, DfmergedTran, DfInt)

        # Store park and ride Demands separately for time slicing
        HOV_BTnc = DfAuto['BTnc'].values.reshape(NoTAZ, NoTAZ)  # low income TNC trips to PnR Zones
        Bus_BTnc = DfTran['BTnc'].values.reshape(NoTAZ, NoTAZ)  # bus trips from TNC zone to destination

        ## Rail
        Dfmerge = util.get_pd_ij_df(eb)
        Dfmerge['BL'] = TncRlWk
        Dfmerge['RTnc'] = RTnc.flatten()

        DfmergedAuto = Dfmerge.groupby(['i', 'BL']).sum().reset_index()
        DfmergedTran = Dfmerge.groupby(['BL', 'j']).sum().reset_index()
        DfAuto, DfTran = self.splitpnr(DfmergedAuto, DfmergedTran, DfInt)

        HOV_RTnc = DfAuto['RTnc'].values.reshape(NoTAZ, NoTAZ)  #  TNC trips to PnR Zones
        Ral_RTnc = DfTran['RTnc'].values.reshape(NoTAZ, NoTAZ)  # rail trips from PnR zone to destination

        del Dfmerge, DfmergedAuto, DfmergedTran
        del DfAuto, DfTran


      ##########################################################################################
       ##       Calculate peak hour O-D person trips and final 24 hour P-A Trips
      ##########################################################################################
      ## SOV Trips      #SOV*PA_Factor + SOV_transpose*AP_Factor
        SOV_AM = SOV*Auto_AM_Fct_PA + SOV.transpose()*Auto_AM_Fct_AP
        SOV_MD = SOV*Auto_MD_Fct_PA + SOV.transpose()*Auto_MD_Fct_AP
        SOV_PM = SOV*Auto_PM_Fct_PA + SOV.transpose()*Auto_PM_Fct_AP

        ## HOV Trips
        HOV_AM = HOV*Auto_AM_Fct_PA + HOV.transpose()*Auto_AM_Fct_AP
        HOV_MD = HOV*Auto_MD_Fct_PA + HOV.transpose()*Auto_MD_Fct_AP
        HOV_PM = HOV*Auto_PM_Fct_PA + HOV.transpose()*Auto_PM_Fct_AP

        ## TNC Trips
        TNC_AM = TNC*Auto_AM_Fct_PA + TNC.transpose()*Auto_AM_Fct_AP
        TNC_MD = TNC*Auto_MD_Fct_PA + TNC.transpose()*Auto_MD_Fct_AP
        TNC_PM = TNC*Auto_PM_Fct_PA + TNC.transpose()*Auto_PM_Fct_AP
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

        ## Park and Ride Trips - Added by SG

        # Bus PnR Trips Auto leg by income and TOD
        SOV_BAu_AM = SOV_BAu*Auto_AM_Fct_PA + SOV_BAu.transpose()*Auto_AM_Fct_AP
        SOV_BAu_MD = SOV_BAu*Auto_MD_Fct_PA + SOV_BAu.transpose()*Auto_MD_Fct_AP
        SOV_BAu_PM = SOV_BAu*Auto_PM_Fct_PA + SOV_BAu.transpose()*Auto_PM_Fct_AP

        # Bus PnR Trips Transit leg
        Bus_BAu_AM = Bus_BAu*Auto_AM_Fct_PA + Bus_BAu.transpose()*Auto_AM_Fct_AP
        Bus_BAu_MD = Bus_BAu*Auto_MD_Fct_PA + Bus_BAu.transpose()*Auto_MD_Fct_AP
        Bus_BAu_PM = Bus_BAu*Auto_PM_Fct_PA + Bus_BAu.transpose()*Auto_PM_Fct_AP

        # Rail PnR Trips Auto Leg by income and TOD
        SOV_RAu_AM = SOV_RAu*Auto_AM_Fct_PA + SOV_RAu.transpose()*Auto_AM_Fct_AP
        SOV_RAu_MD = SOV_RAu*Auto_MD_Fct_PA + SOV_RAu.transpose()*Auto_MD_Fct_AP
        SOV_RAu_PM = SOV_RAu*Auto_PM_Fct_PA + SOV_RAu.transpose()*Auto_PM_Fct_AP

        # Rail PnR Transit Leg
        Ral_RAu_AM = Ral_RAu*Auto_AM_Fct_PA + Ral_RAu.transpose()*Auto_AM_Fct_AP
        Ral_RAu_MD = Ral_RAu*Auto_MD_Fct_PA + Ral_RAu.transpose()*Auto_MD_Fct_AP
        Ral_RAu_PM = Ral_RAu*Auto_PM_Fct_PA + Ral_RAu.transpose()*Auto_PM_Fct_AP

        ## TNC-Transit Trips
        # Bus TNC Trips Auto leg by income and TOD
        HOV_BTnc_AM = HOV_BTnc * Auto_AM_Fct_PA + HOV_BTnc.transpose() * Auto_AM_Fct_AP
        HOV_BTnc_MD = HOV_BTnc * Auto_MD_Fct_PA + HOV_BTnc.transpose() * Auto_MD_Fct_AP
        HOV_BTnc_PM = HOV_BTnc * Auto_PM_Fct_PA + HOV_BTnc.transpose() * Auto_PM_Fct_AP

        # Bus TNC Trips Transit leg
        Bus_BTnc_AM = Bus_BTnc * Auto_AM_Fct_PA + Bus_BTnc.transpose() * Auto_AM_Fct_AP
        Bus_BTnc_MD = Bus_BTnc * Auto_MD_Fct_PA + Bus_BTnc.transpose() * Auto_MD_Fct_AP
        Bus_BTnc_PM = Bus_BTnc * Auto_PM_Fct_PA + Bus_BTnc.transpose() * Auto_PM_Fct_AP

        # Rail TNC Trips Auto Leg by income and TOD
        HOV_RTnc_AM = HOV_RTnc * Auto_AM_Fct_PA + HOV_RTnc.transpose() * Auto_AM_Fct_AP
        HOV_RTnc_MD = HOV_RTnc * Auto_MD_Fct_PA + HOV_RTnc.transpose() * Auto_MD_Fct_AP
        HOV_RTnc_PM = HOV_RTnc * Auto_PM_Fct_PA + HOV_RTnc.transpose() * Auto_PM_Fct_AP

        # Rail TNC Transit Leg
        Ral_RTnc_AM = Ral_RTnc * Auto_AM_Fct_PA + Ral_RTnc.transpose() * Auto_AM_Fct_AP
        Ral_RTnc_MD = Ral_RTnc * Auto_MD_Fct_PA + Ral_RTnc.transpose() * Auto_MD_Fct_AP
        Ral_RTnc_PM = Ral_RTnc * Auto_PM_Fct_PA + Ral_RTnc.transpose() * Auto_PM_Fct_AP

        # Combine all similar trips
        # Add PnR and KrNR legs
        SOV = SOV + SOV_BAu + SOV_RAu

        # TNC -to-Transit Auto Leg to Other TNC Trips
        TNC = TNC + HOV_BTnc + HOV_RTnc

        # Add Transit legs
        Bus = Bus + Bus_BAu + Bus_BTnc
        Rail = Rail + Ral_RAu + Ral_RTnc

        del SOV_BAu, SOV_RAu, HOV_BTnc, HOV_RTnc
        
        Bus_AM += Bus_BAu_AM + Bus_BTnc_AM
        Bus_MD += Bus_BAu_MD + Bus_BTnc_MD
        Bus_PM += Bus_BAu_PM + Bus_BTnc_PM

        Rail_AM += Ral_RAu_AM + Ral_RTnc_AM
        Rail_MD += Ral_RAu_MD + Ral_RTnc_MD
        Rail_PM += Ral_RAu_PM + Ral_RTnc_PM


        # Add TNC-Auto Leg of Tnc-ride
        TNC_AM += HOV_BTnc_AM + HOV_RTnc_AM
        TNC_MD += HOV_BTnc_MD + HOV_RTnc_MD
        TNC_PM += HOV_BTnc_PM + HOV_RTnc_PM


        # Split TNC trips into SOV and HOV
        # TNC CAV Trips
        split_tnc_sov = (hov_occupancy - tnc_occupancy)/(hov_occupancy-1)
        SOV_TNC_AM = TNC_AM * tnc_av_rate * split_tnc_sov
        SOV_TNC_MD = TNC_MD * tnc_av_rate * split_tnc_sov
        SOV_TNC_PM = TNC_PM * tnc_av_rate * split_tnc_sov

        HOV_TNC_AM = TNC_AM * tnc_av_rate * (1 - split_tnc_sov) / hov_occupancy + TNC_AM * (1 - tnc_av_rate) / tnc_occupancy
        HOV_TNC_MD = TNC_MD * tnc_av_rate * (1 - split_tnc_sov) / hov_occupancy + TNC_MD * (1 - tnc_av_rate) / tnc_occupancy
        HOV_TNC_PM = TNC_PM * tnc_av_rate * (1 - split_tnc_sov) / hov_occupancy + TNC_PM * (1 - tnc_av_rate) / tnc_occupancy


        ## add TNC matrices for empty TNC component
        util.add_matrix_numpy(eb, "TncAMVehicleTrip", SOV_TNC_AM)
        util.add_matrix_numpy(eb, "TncAMVehicleTrip", HOV_TNC_AM)

        util.add_matrix_numpy(eb, "TncMDVehicleTrip", SOV_TNC_MD)
        util.add_matrix_numpy(eb, "TncMDVehicleTrip", HOV_TNC_MD)

        util.add_matrix_numpy(eb, "TncPMVehicleTrip", SOV_TNC_PM)
        util.add_matrix_numpy(eb, "TncPMVehicleTrip", HOV_TNC_PM)


        # Convert HOV to Auto Drivers
        # HOV2 + TNC HOV
        AuDr_HOV_AM = HOV_AM/Occ + HOV_TNC_AM
        AuDr_HOV_MD = HOV_MD/Occ + HOV_TNC_MD
        AuDr_HOV_PM = HOV_PM/Occ + HOV_TNC_PM

#       ##############################################################################
#        ##       Set Demand Matrices
#       ##############################################################################
        # 24 hour trips

        util.set_matrix_numpy(eb, "HbUSOVPerTrips", SOV)
        util.set_matrix_numpy(eb, "HbUHOVPerTrips", HOV)
        util.set_matrix_numpy(eb, "HbUBusPerTrips", Bus)
        util.set_matrix_numpy(eb, "HbURailPerTrips", Rail)
        util.set_matrix_numpy(eb, "HbUWalkPerTrips", Walk)
        util.set_matrix_numpy(eb, "HbUBikePerTrips", Bike)
        util.set_matrix_numpy(eb, "HbUTNCPerTrips", TNC)

       # Auto-person

       # SOV
        # AM
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_2_Am", SOV_AM)
        # MD
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_2_Md", SOV_MD)

        # PM
        util.add_matrix_numpy(eb, "SOV_pertrp_VOT_2_Pm", SOV_PM)


        # HOV
        # AM
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_2_Am", HOV_AM)

        # MD
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_2_Md", HOV_MD)

        # PM
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_2_Pm", HOV_PM)

         # TNC
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_2_Am", TNC_AM)
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_2_Md", TNC_MD)
        util.add_matrix_numpy(eb, "TNC_pertrp_VOT_2_Pm", TNC_PM)
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
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_2_Am", SOV_AM)

        # MD
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_2_Md", SOV_MD)

        # PM
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_2_Pm", SOV_PM)

        # Add SOV TNC Trips to SOV trip tables
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_2_Am", SOV_TNC_AM)
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_2_Md", SOV_TNC_MD)
        util.add_matrix_numpy(eb, "SOV_drvtrp_VOT_2_Pm", SOV_TNC_PM)

        # HOV
        # AM
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_2_Am", AuDr_HOV_AM)

        # MD
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_2_Md", AuDr_HOV_MD)

        # PM
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_2_Pm", AuDr_HOV_PM)

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

        purp = "hbu"

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
        util.initmat(eb, "mf9010", "HbULS", " HbU LogSum ", 0)

        util.initmat(eb, "mf9310", "HbULSAU", " HbU LogSum Auto ", 0)

        util.initmat(eb, "mf9410", "HbULSTR", " HbU LogSum Transit ", 0)

        util.initmat(eb, "mf9510", "HbULSAC", " HbU LogSum Active ", 0)

        ## Initialze Friction Factor Matrices
        util.initmat(eb, "mf9100", "P-AFrictionFact1", "Trip Distribution Friction Factor 1", 0)

        ## Initialize P-A Trip Tables by mode
        util.initmat(eb, "mf3100", "HbUSOVPerTrips", "HbU SOV Per-Trips", 0)
        util.initmat(eb, "mf3105", "HbUHOVPerTrips", "HbU HOV Per-Trips", 0)
        util.initmat(eb, "mf3115", "HbUBusPerTrips", "HbU Bus Per-Trips", 0)
        util.initmat(eb, "mf3120", "HbURailPerTrips", "HbU Rail Per-Trips", 0)
        util.initmat(eb, "mf3130", "HbUWalkPerTrips", "HbU Walk Per-Trips", 0)
        util.initmat(eb, "mf3135", "HbUBikePerTrips", "HbU Bike Per-Trips", 0)
        util.initmat(eb, "mf3140", "HbUTNCPerTrips", "HbU TNC Per-Trips", 0)

        ## Initialize P-A Trip Tables from trip distribution
        util.initmat(eb, "mf3150", "HbUP-A", " HbU P-A Trips ", 0)
