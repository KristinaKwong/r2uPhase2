##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage2.hbwork
##--Purpose:
##---------------------------------------------------------------------
import inro.modeller as _m
import numpy as np
import pandas as pd

class HbWork(_m.Tool()):

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Home Base Work"
        pb.description = "Calculate home base work person trips by mode and time of day"
        pb.branding_text = "TransLink"
        pb.runnable = False
        return pb.render()

    @_m.logbook_trace("Run Home Base Work")
    def __call__(self, eb, Bus_Bias, Rail_Bias, WCE_Bias):
        util = _m.Modeller().tool("translink.util")
        MChM = _m.Modeller().tool("translink.RTM3.stage2.modechoiceutils")

        self.matrix_batchins(eb)
        NoTAZ = len(util.get_matrix_numpy(eb, "zoneindex"))

#        ##############################################################################
#        ##       Define Availability conditions
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
                     'r_time': 20.0,
                     'brw_ratio': 1.5,
                     'pr_ratio': 2.0
                    }

        # Declare Utilities Data Frame
        DfU = {}

        # Add Coefficients
        p2   =  0.957766
        p3   = -0.839134
        p4   = -0.164578
        p5   = -2.027129
        p6   =  1.657704
        p7   =  0.725872
        p8   =  3.203539
        p9   =  0.117616
        p10  =  6.743114
        p11  =  1.342106
        p12  = -0.256430
        p13  = -0.183268
        p14  = -0.158294
        p17  = -0.147158
        p18  = -0.101607
        p19  = -0.656231
        p20  = -1.511973
        p21  = -0.431762
        p151 = -0.048225
        p152 = -0.059809
        p153 = -0.047601
        p160 =  5.479080
        p161 =  7.505207
        p162 =  1.589878
        p163 =  2.837890
        p164 =  1.213446
        p505 = -0.196322
        p506 = -0.334867
        p602 =  0.351509
        p603 =  0.321393
        p701 =  0.115601
        p850 =  1.616486
        p870 =  0.550211
        p991 = -0.135461
        p992 =  0.001341
        p993 =  2.122578
        thet =  0.585846

#        ##############################################################################
#        ##       Auto Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        MaxPark = 10.0
        Hov_scale = 0.85

        Occ = float(util.get_matrix_numpy(eb, 'HOVOccHbw')) # Occupancy
        Df['ParkCost'] = util.get_matrix_numpy(eb, 'prk8hr') # 8hr Parking
        Df['ParkCost'][Df['ParkCost']>MaxPark] = MaxPark # set parking>$10 to $10
        Df['ParkCost'] = Df['ParkCost'].reshape(1, NoTAZ) + np.zeros((NoTAZ, 1)) # Broadcast parking from vector to matrix


        # Get SOV Skims by income
        # Low Income
        Df['AutoCosSOV1'] = util.get_matrix_numpy(eb, 'HbWBlSovCost_I1') #SOV Cost
        Df['AutoTimSOV1'] = util.get_matrix_numpy(eb, 'HbWBlSovTime_I1') #SOV Time
        Df['AutoTotCosSOV1'] = Df['AutoCosSOV1'] + Df['ParkCost'] #SOV Cost (per km + Toll + Parking)

        # Med Income
        Df['AutoCosSOV2'] = util.get_matrix_numpy(eb, 'HbWBlSovCost_I2') #SOV Cost
        Df['AutoTimSOV2'] = util.get_matrix_numpy(eb, 'HbWBlSovTime_I2') #SOV Time
        Df['AutoTotCosSOV2'] = Df['AutoCosSOV2'] + Df['ParkCost'] #SOV Cost (per km + Toll + Parking)

        # High Income
        Df['AutoCosSOV3'] = util.get_matrix_numpy(eb, 'HbWBlSovCost_I3') #SOV Cost
        Df['AutoTimSOV3'] = util.get_matrix_numpy(eb, 'HbWBlSovTime_I3') #SOV Time
        Df['AutoTotCosSOV3'] = Df['AutoCosSOV3'] + Df['ParkCost'] #SOV Cost (per km + Toll + Parking)

        # Get HOV Skims by income
        # Low Income
        Df['AutoCosHOV1'] = util.get_matrix_numpy(eb, 'HbWBlHovCost_I1') #HOV Cost
        Df['AutoTimHOV1'] = util.get_matrix_numpy(eb, 'HbWBlHovTime_I1') #HOV Time
        Df['AutoTotCosHOV1'] = Df['AutoCosHOV1'] + Df['ParkCost'] #HOV Cost (per km + Toll + Parking)

        # Med Income
        Df['AutoCosHOV2'] = util.get_matrix_numpy(eb, 'HbWBlHovCost_I2') #HOV Cost
        Df['AutoTimHOV2'] = util.get_matrix_numpy(eb, 'HbWBlHovTime_I2') #HOV Time
        Df['AutoTotCosHOV2'] = Df['AutoCosHOV2'] + Df['ParkCost'] #HOV Cost (per km + Toll + Parking)

        # High Income
        Df['AutoCosHOV3'] = util.get_matrix_numpy(eb, 'HbWBlHovCost_I3') #HOV Cost
        Df['AutoTimHOV3'] = util.get_matrix_numpy(eb, 'HbWBlHovTime_I3') #HOV Time
        Df['AutoTotCosHOV3'] = Df['AutoCosHOV3'] + Df['ParkCost'] #HOV Cost (per km + Toll + Parking)

        # Utilities
        # SOV

        Df['SOVI1'] = ( 0
                      + p151*Df['AutoTimSOV1']
                      + p12*Df['AutoTotCosSOV1'])


        Df['SOVI2'] = ( 0
                      + p151*Df['AutoTimSOV2']
                      + p13*Df['AutoTotCosSOV2'])


        Df['SOVI3'] = ( 0
                      + p151*Df['AutoTimSOV3']
                      + p14*Df['AutoTotCosSOV3'])




        DfU['SOVI1']  = MChM.AutoAvail(Df['AutoCosSOV1'], Df['SOVI1'], AvailDict) #Check Availability condition if mode not available then set to high negative utility (-99999)
        DfU['SOVI2']  = MChM.AutoAvail(Df['AutoCosSOV2'], Df['SOVI2'], AvailDict)
        DfU['SOVI3']  = MChM.AutoAvail(Df['AutoCosSOV3'], Df['SOVI3'], AvailDict)

        # HOV2

        Df['HV2I1'] = ( p2
                      + p151*Df['AutoTimHOV1']
                      + p12*Df['AutoTotCosHOV1']/(pow(2.0, Hov_scale)))


        Df['HV2I2'] = ( p2
                      + p151*Df['AutoTimHOV2']
                      + p13*Df['AutoTotCosHOV2']/(pow(2.0, Hov_scale)))


        Df['HV2I3'] = ( p2
                      + p151*Df['AutoTimHOV3']
                      + p14*Df['AutoTotCosHOV3']/(pow(2.0, Hov_scale)))




        DfU['HV2I1']  = MChM.AutoAvail(Df['AutoCosHOV1'], Df['HV2I1'], AvailDict) #Check Availability condition if mode not available then set to high negative utility (-99999)
        DfU['HV2I2']  = MChM.AutoAvail(Df['AutoCosHOV2'], Df['HV2I2'], AvailDict)
        DfU['HV2I3']  = MChM.AutoAvail(Df['AutoCosHOV3'], Df['HV2I3'], AvailDict)

        # HOV3

        Df['HV3I1'] = ( p3
                      + p151*Df['AutoTimHOV1']
                      + p12*Df['AutoTotCosHOV1']/(pow(Occ, Hov_scale)))


        Df['HV3I2'] = ( p3
                      + p151*Df['AutoTimHOV2']
                      + p13*Df['AutoTotCosHOV2']/(pow(Occ, Hov_scale)))


        Df['HV3I3'] = ( p3
                      + p151*Df['AutoTimHOV3']
                      + p14*Df['AutoTotCosHOV3']/(pow(Occ, Hov_scale)))

        DfU['HV3I1']  = MChM.AutoAvail(Df['AutoCosHOV1'], Df['HV3I1'], AvailDict) #Check Availability condition if mode not available then set to high negative utility (-99999)
        DfU['HV3I2']  = MChM.AutoAvail(Df['AutoCosHOV2'], Df['HV3I2'], AvailDict)
        DfU['HV3I3']  = MChM.AutoAvail(Df['AutoCosHOV3'], Df['HV3I3'], AvailDict)


#        ##############################################################################
#        ##       Walk to Transit Modes
#        ##############################################################################

        # Generate Dataframe
        Df = {}
        Tiny=0.000001
        Df['BusIVT'] = util.get_matrix_numpy(eb, 'HbWBlBusIvtt') #In vehicle Bus time
        Df['BusWat'] = util.get_matrix_numpy(eb, 'HbWBlBusWait') #Wait Bus time
        Df['BusAux'] = util.get_matrix_numpy(eb, 'HbWBlBusAux') #Walk Time
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'HbWBlBusBoard') #Boarding time
        Df['BusFar'] = util.get_matrix_numpy(eb, 'HbWBlBusFare') #Fare
        Df['BusTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux']  #Total travel Time

        Df['RalIVR'] = util.get_matrix_numpy(eb, 'HbWBlRailIvtt') #In vehicle Rail time on rail
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'HbWBlRailIvttBus') #In vehicle Rail time on bus
        Df['RalWat'] = util.get_matrix_numpy(eb, 'HbWBlRailWait') # Wait Rail Time
        Df['RalAux'] = util.get_matrix_numpy(eb, 'HbWBlRailAux') # Auxiliary Time
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'HbWBlRailBoard')
        Df['RalFar'] = util.get_matrix_numpy(eb, 'HbWBlRailFare')
        Df['RalTot'] = Df['RalIVB'] + Df['RalIVR'] + Df['RalWat'] + Df['RalAux']  #Total travel Time
        Df['RalIBR'] = Df['RalIVB']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) #Ratio of IVT on Bus to total IVTT
        Df['RalIRR'] = Df['RalIVR']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) #Ratio of IVT on Rail to total IVTT

        Df['WCEIVW'] = util.get_matrix_numpy(eb, 'HbWBlWceIvtt') #In vehicle Rail time on wce
        Df['WCEIVR'] = util.get_matrix_numpy(eb, 'HbWBlWceIvttRail') #In vehicle Rail time on rail
        Df['WCEIVB'] = util.get_matrix_numpy(eb, 'HbWBlWceIvttBus') #In vehicle Rail time on bus
        Df['WCEWat'] = util.get_matrix_numpy(eb, 'HbWBlWceWait') # wait time
        Df['WCEAux'] = util.get_matrix_numpy(eb, 'HbWBlWceAux') # walk time
        Df['WCEBrd'] = util.get_matrix_numpy(eb, 'HbWBlWceBoard') # board time
        Df['WCEFar'] = util.get_matrix_numpy(eb, 'HbWBlWceFare') # wce fare
        Df['WCETot'] = Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW'] + Df['WCEWat'] + Df['WCEAux'] #Total travel Time
        Df['WCEIBR'] = Df['WCEIVB']/(Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW'] + Tiny) #Ratio of IVT on Bus to total IVTT
        Df['WCEIRR'] = Df['WCEIVR']/(Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW'] + Tiny) #Ratio of IVT on Rail to total IVTT
        Df['WCEIWR'] = Df['WCEIVW']/(Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW'] + Tiny) #Ratio of IVT on WCE to total IVTT

        Df['TranAccess'] = util.get_matrix_numpy(eb, 'transitAccLn').reshape(NoTAZ,1) + np.zeros((1, NoTAZ)) # Log transit accessiblity broadcast
        Df['IntZnl'] = np.identity(NoTAZ) # Intra-zonal matrix
        Df['AutoDis'] = util.get_matrix_numpy(eb, "mfdistAON") # Distance
        Df['AutoDisSqd'] = Df['AutoDis']* Df['AutoDis'] #Distance squared
        Df['LogAutoDis'] = np.log(Df['AutoDis'] + Tiny) # Log Distance

        # Utilities
        # Bus Utility
        # Bus Common Utility for all incomes
        Df['GeUtl'] = ( p4
                      + Bus_Bias
                      + p152*Df['BusIVT']
                      + p17*Df['BusWat']
                      + p18*Df['BusAux']
                      + p19*(Df['BusBrd'])
                      + p991*Df['AutoDis']
                      + p992*Df['AutoDisSqd']
                      + p993*Df['LogAutoDis']
                      + p602*Df['TranAccess'])

        # Check availability conditions else add high negative utility (-99999)
        Df['GeUtl'] = MChM.BusAvail(Df, Df['GeUtl'], AvailDict)
        # Add Income Parameters
        DfU['BusI1'] = Df['GeUtl'] + p12*Df['BusFar']
        DfU['BusI2'] = Df['GeUtl'] + p13*Df['BusFar']
        DfU['BusI3'] = Df['GeUtl'] + p14*Df['BusFar']

        # Rail Utility
        # Rail Common Utility for all incomes
        Df['GeUtl'] = ( p4*Df['RalIBR']
                      + p6*Df['RalIRR']
                      + Rail_Bias
                      + p152*Df['RalIVB']
                      + p153*Df['RalIVR']
                      + p17*Df['RalWat']
                      + p18*Df['RalAux']
                      + p19*Df['RalBrd']
                      + p991*Df['AutoDis']
                      + p992*Df['AutoDisSqd']
                      + p993*Df['LogAutoDis']
                      + p603*Df['TranAccess'])

        # Check availability conditions else add high negative utility (-99999)
        Df['GeUtl'] = MChM.RailAvail(Df, Df['GeUtl'],AvailDict)
        # Add Income Parameters
        DfU['RalI1'] = Df['GeUtl'] + p12*Df['RalFar']
        DfU['RalI2'] = Df['GeUtl'] + p13*Df['RalFar']
        DfU['RalI3'] = Df['GeUtl'] + p14*Df['RalFar']

        # WCE Utility
        # WCE Common Utility for all incomes
        Df['GeUtl'] = ( p4*Df['WCEIBR']
                      + p6*Df['WCEIRR']
                      + p8*Df['WCEIWR']
                      + WCE_Bias
                      + p152*Df['WCEIVB']
                      + p153*Df['WCEIVR']
                      + p153*Df['WCEIVW']
                      + p17*Df['WCEWat']
                      + p18*Df['WCEAux']
                      + p19*Df['WCEBrd']
                      + p991*Df['AutoDis']
                      + p992*Df['AutoDisSqd']
                      + p993*Df['LogAutoDis']
                      + p603*Df['TranAccess'])
        # Check availability conditions else add high negative utility (-99999)
        Df['GeUtl'] = MChM.WCEAvail(Df, Df['GeUtl'], AvailDict)
        # Add Income Parameters
        DfU['WCEI1'] = Df['GeUtl'] + p12*Df['WCEFar']
        DfU['WCEI2'] = Df['GeUtl'] + p13*Df['WCEFar']
        DfU['WCEI3'] = Df['GeUtl'] + p14*Df['WCEFar']

#        ##############################################################################
#        ##       Drive to Transit Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        Df['BAuCos'] = util.get_matrix_numpy(eb, 'HbWBlBAuPRCost') #Bus PR Drive Distance
        Df['BAuTim'] = util.get_matrix_numpy(eb, 'HbWBlBAuPRTime') # Bus PR Drive Time
        Df['BAuTotCos'] = Df['BAuCos'] + util.get_matrix_numpy(eb, 'HbWBAuPrkCst') # Bus PR Drive Cost
        Df['BAuTrm'] = util.get_matrix_numpy(eb, 'HbWBAuTrmTim') #Bus PR Terminal Time
        Df['BusIVT'] = util.get_matrix_numpy(eb, 'HbWBlBAuBusIvtt') #Bus IVTT
        Df['BusWat'] = util.get_matrix_numpy(eb, 'HbWBlBAuBusWait') #Bus Wait Time
        Df['BusAux'] = util.get_matrix_numpy(eb, 'HbWBlBAuBusAux') # Bus Walk Time
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'HbWBlBAuBusBoard') # Bus Boarding Time
        Df['BusFar'] = util.get_matrix_numpy(eb, 'HbWBlBAuBusFare') # Bus Fare
        Df['BusTot'] = util.get_matrix_numpy(eb, 'HbWBlBusIvtt') + util.get_matrix_numpy(eb, 'HbWBlBusWait') + util.get_matrix_numpy(eb, 'HbWBlBusAux')
        Df['BusIVT'] = util.get_matrix_numpy(eb, 'HbWBlBusIvtt') #In vehicle Bus time
        Df['BAuTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux'] + Df['BAuTim'] # Total Travel Time
        Df['BAuIBR'] = Df['BusIVT']/(Df['BusIVT'] + Df['BAuTim'] + Tiny) # Ratio of Time on Bus to total travel time
        Df['WBusFar'] = util.get_matrix_numpy(eb, 'HbWBlBusFare') #Walk to Transit Fare

        Df['RAuCos'] = util.get_matrix_numpy(eb, 'HbWBlRAuPRCost') #Rail PR Drive Distance
        Df['RAuTim'] = util.get_matrix_numpy(eb, 'HbWBlRAuPRTime') #Rail PR Drive Time
        Df['RAuTotCos'] = Df['RAuCos'] + util.get_matrix_numpy(eb, 'HbWRAuPrkCst') # Rail PR Drive Cost
        Df['RAuTrm'] = util.get_matrix_numpy(eb, 'HbWRAuTrmTim') #Rail PR Terminal Time
        Df['RalIVR'] = util.get_matrix_numpy(eb, 'HbWBlRAuRailIvtt') #IVT on Rail
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'HbWBlRAuRailIvttBus') #IVT on Bus
        Df['RalWat'] = util.get_matrix_numpy(eb, 'HbWBlRAuRailWait') #Rail Wait Time
        Df['RalAux'] = util.get_matrix_numpy(eb, 'HbWBlRAuRailAux') #Rail Walk Time
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'HbWBlRAuRailBoard') #Rail Board Time
        Df['RalFar'] = util.get_matrix_numpy(eb, 'HbWBlRAuRailFare') #Rail Fare
        Df['RAuTot'] = Df['RalIVB'] + Df['RalIVR'] + Df['RalWat'] + Df['RalAux'] + Df['RAuTim'] # Total Travel Time
        Df['RAuIBR'] = Df['RalIVB']/(Df['RalIVB'] + Df['RalIVR'] + Df['RAuTim'] + Tiny) # Ratio of Time on Bus to total travel time
        Df['RAuIRR'] = Df['RalIVR']/(Df['RalIVB'] + Df['RalIVR'] + Df['RAuTim'] + Tiny) # Ratio of Time on Rail to total travel time

        Df['WRalFar'] = util.get_matrix_numpy(eb, 'HbWBlRailFare')
        Df['WRalIVR'] = util.get_matrix_numpy(eb, 'HbWBlRailIvtt') #In vehicle Rail time on rail
        Df['RalTot'] = (util.get_matrix_numpy(eb, 'HbWBlRailIvtt') + util.get_matrix_numpy(eb, 'HbWBlRailIvttBus')
                       + util.get_matrix_numpy(eb, 'HbWBlRailWait') + util.get_matrix_numpy(eb, 'HbWBlRailAux'))

        Df['WAuCos'] = util.get_matrix_numpy(eb, 'HbWBlWAuPRCost') #WCE PR Drive Distance
        Df['WAuTim'] = util.get_matrix_numpy(eb, 'HbWBlWAuPRTime') #WCE PR Drive Time
        Df['WAuTotCos'] = Df['WAuCos'] + util.get_matrix_numpy(eb, 'HbWWAuPrkCst') # WCE PR Drive Cost
        Df['WAuTrm'] = util.get_matrix_numpy(eb, 'HbWWAuTrmTim') #WCE PR Terminal Time
        Df['WCEIVW'] = util.get_matrix_numpy(eb, 'HbWBlWAuWceIvtt') #IVT on WCE
        Df['WCEIVR'] = util.get_matrix_numpy(eb, 'HbWBlWAuWceIvttRail') #IVT on Rail
        Df['WCEIVB'] = util.get_matrix_numpy(eb, 'HbWBlWAuWceIvttBus') #IVT on Bus
        Df['WCEWat'] = util.get_matrix_numpy(eb, 'HbWBlWAuWceWait') #WCE Wait Time
        Df['WCEAux'] = util.get_matrix_numpy(eb, 'HbWBlWAuWceAux')  #WCE Walk Time
        Df['WCEBrd'] = util.get_matrix_numpy(eb, 'HbWBlWAuWceBoards') #WCE Board Time
        Df['WCEFar'] = util.get_matrix_numpy(eb, 'HbWBlWAuWceFare') #WCE Fare
        Df['WAuTot'] = Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW'] + Df['WCEWat'] + Df['WCEAux'] + Df['WAuTim'] # Total Travel Time
        Df['WAuIBR'] = Df['WCEIVB']/(Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW']+ Df['WAuTim'] + Tiny) # Ratio of Time on Bus to total travel time
        Df['WAuIRR'] = Df['WCEIVR']/(Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW']+ Df['WAuTim'] + Tiny) # Ratio of Time on Rail to total travel time
        Df['WAuIWR'] = Df['WCEIVW']/(Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW']+ Df['WAuTim'] + Tiny) # Ratio of Time on WCE to total travel time

        Df['WWCEFar'] = util.get_matrix_numpy(eb, 'HbWBlWceFare') # wce fare
        Df['WWCEIVW'] = util.get_matrix_numpy(eb, 'HbWBlWceIvtt') #In vehicle Rail time on wce

        Df['WCETot'] = (util.get_matrix_numpy(eb, 'HbWBlWceIvtt')
                       + util.get_matrix_numpy(eb, 'HbWBlWceIvttRail')
                       + util.get_matrix_numpy(eb, 'HbWBlWceIvttBus')
                       + util.get_matrix_numpy(eb, 'HbWBlWceWait')
                       + util.get_matrix_numpy(eb, 'HbWBlWceAux'))



        Df['IntZnl'] = np.identity(NoTAZ) # Intra-zonal
        Df['AutoDis'] = util.get_matrix_numpy(eb, "mfdistAON") # Distance
        Df['AutoDisSqd'] = Df['AutoDis']* Df['AutoDis'] # Distance-squared
        Df['LogAutoDis'] = np.log(Df['AutoDis'] + Tiny) #log-distance


        # Utilities
        # PR Bus Utility
        # PR Bus Common Utility for all incomes
        Df['GeUtl'] = ( p5
                      + p4*Df['BAuIBR']
                      + p151*Df['BAuTim']
                      + p152*Df['BusIVT']
                      + p17*Df['BusWat']
                      + p18*Df['BusAux']
                      + p18*Df['BAuTrm']
                      + p19*Df['BusBrd']
                      + p991*Df['AutoDis']
                      + p992*Df['AutoDisSqd']
                      + p993*Df['LogAutoDis'])

        # Check availability conditions else add high negative utility (-99999)
        Df['GeUtl'] = MChM.BAuAvail(Df, Df['GeUtl'], AvailDict)
        # Add Income Parameters
        DfU['BAuI1'] = Df['GeUtl'] + p12*(Df['BusFar'] + Df['BAuTotCos'])
        DfU['BAuI2'] = Df['GeUtl'] + p13*(Df['BusFar'] + Df['BAuTotCos'])
        DfU['BAuI3'] = Df['GeUtl'] + p14*(Df['BusFar'] + Df['BAuTotCos'])

        # Rail Utility
        # PR Rail Utility
        # PR Rail Common Utility for all incomes
        Df['GeUtl'] = ( p7
                      + p4*Df['RAuIBR']
                      + p6*Df['RAuIRR']
                      + p151*Df['RAuTim']
                      + p152*Df['RalIVB']
                      + p153*Df['RalIVR']
                      + p17*Df['RalWat']
                      + p18*(Df['RalAux'] + Df['RAuTrm'])
                      + p19*Df['RalBrd']
                      + p991*Df['AutoDis']
                      + p992*Df['AutoDisSqd']
                      + p993*Df['LogAutoDis'])

        # Check availability conditions else add high negative utility (-99999)
        Df['GeUtl'] = MChM.RAuAvail(Df, Df['GeUtl'], AvailDict)
        # Add Income Parameters
        DfU['RAuI1'] = Df['GeUtl'] + p12*(Df['RalFar'] + Df['RAuTotCos'])
        DfU['RAuI2'] = Df['GeUtl'] + p13*(Df['RalFar'] + Df['RAuTotCos'])
        DfU['RAuI3'] = Df['GeUtl'] + p14*(Df['RalFar'] + Df['RAuTotCos'])

        # Utilities
        # PR WCE Utility
        # PR WCE Common Utility for all incomes
        Df['GeUtl'] = ( p9
                       + p4*Df['WAuIBR']
                       + p6*Df['WAuIRR']
                       + p8*Df['WAuIWR']
                       + p151*Df['WAuTim']
                       + p152*Df['WCEIVB']
                       + p153*Df['WCEIVR']
                       + p153*Df['WCEIVW']
                       + p17*Df['WCEWat']
                       + p18*(Df['WCEAux'] + Df['WAuTrm'])
                       + p19*Df['WCEBrd']
                       + p991*Df['AutoDis']
                       + p992*Df['AutoDisSqd']
                       + p993*Df['LogAutoDis'])

        # Check availability conditions else add high negative utility (-99999)
        Df['GeUtl'] = MChM.WAuAvail(Df, Df['GeUtl'],AvailDict)
        # Add Income Parameters
        DfU['WAuI1'] = Df['GeUtl'] + p12*(Df['WCEFar'] + Df['WAuTotCos'])
        DfU['WAuI2'] = Df['GeUtl'] + p13*(Df['WCEFar'] + Df['WAuTotCos'])
        DfU['WAuI3'] = Df['GeUtl'] + p14*(Df['WCEFar'] + Df['WAuTotCos'])

#        ##############################################################################
#        ##       Active Modes
#        ##############################################################################

        Df = {}
        Df['AutoDis'] = util.get_matrix_numpy(eb, "mfdistAON") # Distance
        Df['IntrCBD'] = util.get_matrix_numpy(eb, 'd_cbd') #Intra-CBD
        Df['IntrCBD'] = Df['IntrCBD'].reshape(NoTAZ, 1)*Df['IntrCBD'].reshape(1, NoTAZ) #Broadcast intra-CBD

        Df['PopEmpDenPA'] = util.get_matrix_numpy(eb, 'combinedens') + Tiny #Pop+Emp Density at Prod and Attr Zones
        Df['PopEmpDenPA'] = np.log(Df['PopEmpDenPA'].reshape(NoTAZ, 1) + Df['PopEmpDenPA'].reshape(1, NoTAZ)) #Broadcast Density

        Df['PopSen'] = util.get_matrix_numpy(eb, 'Pop55t64') + util.get_matrix_numpy(eb, 'Pop65Up') #Senior Proportion
        Df['PopTot'] = util.get_matrix_numpy(eb, 'TotPop')
        Df['PopSPr'] = np.log(Df['PopSen']/(Df['PopTot'] + Tiny) + Tiny)
        Df['PopSPr'] = Df['PopSPr'].reshape(NoTAZ, 1) + np.zeros((1, NoTAZ))

        Df['BikScr'] = util.get_matrix_numpy(eb, 'bikeskim') # Bike Score

        # Walk Utility
        DfU['Walk'] = ( p10
                      + p20*Df['AutoDis']
                      + p850*Df['IntrCBD']
                      + p701*Df['PopEmpDenPA']
                      + p505*Df['PopSPr'])
        # Check availability conditions else add high negative utility (-99999)
        DfU['Walk'] = MChM.WalkAvail(Df['AutoDis'], DfU['Walk'], AvailDict)

        # Bike Utility
        DfU['Bike'] = ( p11
                      + p21*Df['AutoDis']
                      + p870*Df['BikScr']
                      + p506*Df['PopSPr'])
        # Check availability conditions else add high negative utility (-99999)
        DfU['Bike'] = MChM.BikeAvail(Df['AutoDis'], DfU['Bike'], AvailDict)

        del Df

        ##############################################################################
        ##       Calculate Probabilities
        ##############################################################################

        ############
        # Low Income
        ############

        ## Add SOV Availability Term, Zones close to car shares assumed to have vehicle availability

        DfU['CarShare'] = util.get_matrix_numpy(eb, 'cs500').reshape(NoTAZ,1) + np.zeros((1, NoTAZ))
        LrgU     = -99999.0
        ## Low Income Zero Autos
        Dict = {
               'SOV'  : [np.where(DfU['CarShare']>0, DfU['SOVI1'], LrgU)],
               'HOV'  : [DfU['HV2I1'], DfU['HV3I1']],
               'WTra' : [DfU['BusI1'] + p164, DfU['RalI1'] + p164, DfU['WCEI1']], # Add zero vehicle segment bias
               'DTra' : [DfU['BAuI1'] + LrgU, DfU['RAuI1'] + LrgU, DfU['WAuI1'] +LrgU],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I1A0_Dict = self.Calc_Prob(eb, Dict, "HbWLSI1A0", thet)

        ## Low Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI1'] + p160], # Add one vehicle segment bias
               'HOV'  : [DfU['HV2I1'] + p162, DfU['HV3I1'] + p162], # Add one vehicle segment bias
               'WTra' : [DfU['BusI1'], DfU['RalI1'], DfU['WCEI1']],
               'DTra' : [DfU['BAuI1'], DfU['RAuI1'], DfU['WAuI1']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I1A1_Dict = self.Calc_Prob(eb, Dict, "HbWLSI1A1", thet)

        ## Low Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI1'] + p161], # Add two vehicle segment bias
               'HOV'  : [DfU['HV2I1'] + p163, DfU['HV3I1'] + p163], # Add two vehicle segment bias
               'WTra' : [DfU['BusI1'], DfU['RalI1'], DfU['WCEI1']],
               'DTra' : [DfU['BAuI1'], DfU['RAuI1'], DfU['WAuI1']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I1A2_Dict = self.Calc_Prob(eb, Dict, "HbWLSI1A2", thet)

        ############
        # Med Income
        ############

        ## Med Income Zero Autos
        Dict = {
               'SOV'  : [np.where(DfU['CarShare']>0, DfU['SOVI2'], LrgU)],
               'HOV'  : [DfU['HV2I2'], DfU['HV3I2']],
               'WTra' : [DfU['BusI2'] + p164, DfU['RalI2'] + p164, DfU['WCEI2']],
               'DTra' : [DfU['BAuI2'] + LrgU, DfU['RAuI2'] + LrgU, DfU['WAuI2'] + LrgU],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I2A0_Dict = self.Calc_Prob(eb, Dict, "HbWLSI2A0", thet)

        ## Med Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI2'] + p160],
               'HOV'  : [DfU['HV2I2'] + p162, DfU['HV3I2'] + p162],
               'WTra' : [DfU['BusI2'], DfU['RalI2'], DfU['WCEI2']],
               'DTra' : [DfU['BAuI2'], DfU['RAuI2'], DfU['WAuI2']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I2A1_Dict = self.Calc_Prob(eb, Dict, "HbWLSI2A1", thet)

        ## Med Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI2'] + p161],
               'HOV'  : [DfU['HV2I2'] + p163, DfU['HV3I2'] + p163],
               'WTra' : [DfU['BusI2'], DfU['RalI2'], DfU['WCEI2']],
               'DTra' : [DfU['BAuI2'], DfU['RAuI2'], DfU['WAuI2']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I2A2_Dict = self.Calc_Prob(eb, Dict, "HbWLSI2A2", thet)

        #############
        # High Income
        #############

        ## High Income Zero Autos
        Dict = {
               'SOV'  : [np.where(DfU['CarShare']>0, DfU['SOVI3'], LrgU)],
               'HOV'  : [DfU['HV2I3'], DfU['HV3I3']],
               'WTra' : [DfU['BusI3'] + p164, DfU['RalI3'] + p164, DfU['WCEI3']],
               'DTra' : [DfU['BAuI3'] + LrgU, DfU['RAuI3'] + LrgU, DfU['WAuI3'] +LrgU],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I3A0_Dict = self.Calc_Prob(eb, Dict, "HbWLSI3A0", thet)

        ## High Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI3'] + p160],
               'HOV'  : [DfU['HV2I3'] + p162, DfU['HV3I3'] + p162],
               'WTra' : [DfU['BusI3'], DfU['RalI3'], DfU['WCEI3']],
               'DTra' : [DfU['BAuI3'], DfU['RAuI3'], DfU['WAuI3']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I3A1_Dict = self.Calc_Prob(eb, Dict, "HbWLSI3A1", thet)

        ## High Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI3'] + p161],
               'HOV'  : [DfU['HV2I3'] + p163, DfU['HV3I3'] + p163],
               'WTra' : [DfU['BusI3'], DfU['RalI3'], DfU['WCEI3']],
               'DTra' : [DfU['BAuI3'], DfU['RAuI3'], DfU['WAuI3']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I3A2_Dict = self.Calc_Prob(eb, Dict, "HbWLSI3A2", thet)

        del DfU, Dict

#
       ##############################################################################
        ##       Trip Distribution
       ##############################################################################

        Logsum =  [
                  "HbWLSI1A0", "HbWLSI1A1", "HbWLSI1A2",
                  "HbWLSI2A0", "HbWLSI2A1", "HbWLSI2A2",
                  "HbWLSI3A0", "HbWLSI3A1", "HbWLSI3A2"
                   ]

        imp_list = [
                  "P-AFrictionFact1", "P-AFrictionFact2", "P-AFrictionFact3",
                  "P-AFrictionFact4", "P-AFrictionFact5", "P-AFrictionFact6",
                  "P-AFrictionFact7", "P-AFrictionFact8", "P-AFrictionFact9"
                   ]

        mo_list =  [
                    "hbwInc1Au0prd", "hbwInc1Au1prd", "hbwInc1Au2prd",
                    "hbwInc2Au0prd", "hbwInc2Au1prd", "hbwInc2Au2prd",
                    "hbwInc3Au0prd", "hbwInc3Au1prd", "hbwInc3Au2prd"
                   ]



        md_list =  ["hbwatr"]


        out_list = [
                    "HbWP-AI1A0", "HbWP-AI1A1", "HbWP-AI1A2",
                    "HbWP-AI2A0", "HbWP-AI2A1", "HbWP-AI2A2",
                    "HbWP-AI3A0", "HbWP-AI3A1", "HbWP-AI3A2"
                   ]

        LS_Coeff = 0.7

        LambdaList = [-0.159306,-0.131097,-0.131283,-0.15313,-0.108345,-0.106872,-0.0358,-0.118164,-0.10317]



        AlphaList =  [0.003906,0.001641,0.001578,0.002727,0.0018,0.001426,0.00039,0.002152,0.001612]



        GammaList =  [-0.000069,-0.000007,-0.000007,-0.000019,-0.000012,-0.000007,-0.000002,-0.000017,-0.000011]


        Kij = util.get_matrix_numpy(eb, "Kij_hbw")

        Bridge_Factor = 0

        MChM.ImpCalc(eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, util.get_matrix_numpy(eb, "mfdistAON"), Kij, "Zero", Bridge_Factor)

        MChM.two_dim_matrix_balancing(eb, mo_list, md_list, imp_list, out_list)

#       ##############################################################################
#        ##       Calculate Demand
#       ##############################################################################

        I1A0_Dict = self.Calc_Demand(I1A0_Dict, util.get_matrix_numpy(eb,"HbWP-AI1A0"))
        I1A1_Dict = self.Calc_Demand(I1A1_Dict, util.get_matrix_numpy(eb,"HbWP-AI1A1"))
        I1A2_Dict = self.Calc_Demand(I1A2_Dict, util.get_matrix_numpy(eb,"HbWP-AI1A2"))
        I2A0_Dict = self.Calc_Demand(I2A0_Dict, util.get_matrix_numpy(eb,"HbWP-AI2A0"))
        I2A1_Dict = self.Calc_Demand(I2A1_Dict, util.get_matrix_numpy(eb,"HbWP-AI2A1"))
        I2A2_Dict = self.Calc_Demand(I2A2_Dict, util.get_matrix_numpy(eb,"HbWP-AI2A2"))
        I3A0_Dict = self.Calc_Demand(I3A0_Dict, util.get_matrix_numpy(eb,"HbWP-AI3A0"))
        I3A1_Dict = self.Calc_Demand(I3A1_Dict, util.get_matrix_numpy(eb,"HbWP-AI3A1"))
        I3A2_Dict = self.Calc_Demand(I3A2_Dict, util.get_matrix_numpy(eb,"HbWP-AI3A2"))

        # SOV Trips by Low, Med and High Income
        SOVI1 = I1A0_Dict['SOV'][0] + I1A1_Dict['SOV'][0] + I1A2_Dict['SOV'][0]
        SOVI2 = I2A0_Dict['SOV'][0] + I2A1_Dict['SOV'][0] + I2A2_Dict['SOV'][0]
        SOVI3 = I3A0_Dict['SOV'][0] + I3A1_Dict['SOV'][0] + I3A2_Dict['SOV'][0]
        # HOV Trips by Low, Med and High Income
        HV2I1 = I1A0_Dict['HOV'][0] + I1A1_Dict['HOV'][0] + I1A2_Dict['HOV'][0]
        HV2I2 = I2A0_Dict['HOV'][0] + I2A1_Dict['HOV'][0] + I2A2_Dict['HOV'][0]
        HV2I3 = I3A0_Dict['HOV'][0] + I3A1_Dict['HOV'][0] + I3A2_Dict['HOV'][0]
        HV3I1 = I1A0_Dict['HOV'][1] + I1A1_Dict['HOV'][1] + I1A2_Dict['HOV'][1]
        HV3I2 = I2A0_Dict['HOV'][1] + I2A1_Dict['HOV'][1] + I2A2_Dict['HOV'][1]
        HV3I3 = I3A0_Dict['HOV'][1] + I3A1_Dict['HOV'][1] + I3A2_Dict['HOV'][1]
        # Walk to Transit Bus, Rail and WCE Trips
        Bus  =  I1A0_Dict['WTra'][0] + I1A1_Dict['WTra'][0] + I1A2_Dict['WTra'][0]
        Bus +=  I2A0_Dict['WTra'][0] + I2A1_Dict['WTra'][0] + I2A2_Dict['WTra'][0]
        Bus +=  I3A0_Dict['WTra'][0] + I3A1_Dict['WTra'][0] + I3A2_Dict['WTra'][0]
        Rail =  I1A0_Dict['WTra'][1] + I1A1_Dict['WTra'][1] + I1A2_Dict['WTra'][1]
        Rail += I2A0_Dict['WTra'][1] + I2A1_Dict['WTra'][1] + I2A2_Dict['WTra'][1]
        Rail += I3A0_Dict['WTra'][1] + I3A1_Dict['WTra'][1] + I3A2_Dict['WTra'][1]
        WCE =   I1A0_Dict['WTra'][2] + I1A1_Dict['WTra'][2] + I1A2_Dict['WTra'][2]
        WCE +=  I2A0_Dict['WTra'][2] + I2A1_Dict['WTra'][2] + I2A2_Dict['WTra'][2]
        WCE +=  I3A0_Dict['WTra'][2] + I3A1_Dict['WTra'][2] + I3A2_Dict['WTra'][2]
        # Active Trips
        Walk =  I1A0_Dict['Acti'][0] + I1A1_Dict['Acti'][0] + I1A2_Dict['Acti'][0]
        Walk += I2A0_Dict['Acti'][0] + I2A1_Dict['Acti'][0] + I2A2_Dict['Acti'][0]
        Walk += I3A0_Dict['Acti'][0] + I3A1_Dict['Acti'][0] + I3A2_Dict['Acti'][0]
        Bike =  I1A0_Dict['Acti'][1] + I1A1_Dict['Acti'][1] + I1A2_Dict['Acti'][1]
        Bike += I2A0_Dict['Acti'][1] + I2A1_Dict['Acti'][1] + I2A2_Dict['Acti'][1]
        Bike += I3A0_Dict['Acti'][1] + I3A1_Dict['Acti'][1] + I3A2_Dict['Acti'][1]
        # Drive to Transit Bus, Rail and WCE Trips
        BAuI1 = I1A0_Dict['DTra'][0] + I1A1_Dict['DTra'][0] + I1A2_Dict['DTra'][0]
        BAuI2 = I2A0_Dict['DTra'][0] + I2A1_Dict['DTra'][0] + I2A2_Dict['DTra'][0]
        BAuI3 = I3A0_Dict['DTra'][0] + I3A1_Dict['DTra'][0] + I3A2_Dict['DTra'][0]
        RAuI1 = I1A0_Dict['DTra'][1] + I1A1_Dict['DTra'][1] + I1A2_Dict['DTra'][1]
        RAuI2 = I2A0_Dict['DTra'][1] + I2A1_Dict['DTra'][1] + I2A2_Dict['DTra'][1]
        RAuI3 = I3A0_Dict['DTra'][1] + I3A1_Dict['DTra'][1] + I3A2_Dict['DTra'][1]
        WAuI1 = I1A0_Dict['DTra'][2] + I1A1_Dict['DTra'][2] + I1A2_Dict['DTra'][2]
        WAuI2 = I2A0_Dict['DTra'][2] + I2A1_Dict['DTra'][2] + I2A2_Dict['DTra'][2]
        WAuI3 = I3A0_Dict['DTra'][2] + I3A1_Dict['DTra'][2] + I3A2_Dict['DTra'][2]

        del I1A0_Dict, I1A1_Dict, I1A2_Dict
        del I2A0_Dict, I2A1_Dict, I2A2_Dict
        del I3A0_Dict, I3A1_Dict, I3A2_Dict

#       ##############################################################################
#        ##       Get Time Slice Factors
#       ##############################################################################
        purp = 'hbw'
        min_val = 0.000143

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

        del df_mats


        Tran_MD_Fct_N_PA, Tran_MD_Fct_N_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Transit',peakperiod='MD', geo='N',minimum_value=min_val)


        Acti_AM_Fct_N_PA, Acti_AM_Fct_N_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Active',peakperiod='AM', geo='N',minimum_value=min_val)
        Acti_MD_Fct_N_PA, Acti_MD_Fct_N_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Active',peakperiod='MD', geo='N',minimum_value=min_val)
        Acti_PM_Fct_N_PA, Acti_PM_Fct_N_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Active',peakperiod='PM', geo='N',minimum_value=min_val)

        WCE_AM_Fct_N_PA, WCE_AM_Fct_N_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='WCE',peakperiod='AM', geo='N',minimum_value=0)
        WCE_PM_Fct_N_PA, WCE_PM_Fct_N_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='WCE',peakperiod='PM', geo='N',minimum_value=0)


        Tran_MD_Fct_S_PA, Tran_MD_Fct_S_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Transit',peakperiod='MD', geo='S',minimum_value=min_val)


        Acti_AM_Fct_S_PA, Acti_AM_Fct_S_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Active',peakperiod='AM', geo='S',minimum_value=min_val)
        Acti_MD_Fct_S_PA, Acti_MD_Fct_S_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Active',peakperiod='MD', geo='S',minimum_value=min_val)
        Acti_PM_Fct_S_PA, Acti_PM_Fct_S_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='Active',peakperiod='PM', geo='S',minimum_value=min_val)

        WCE_AM_Fct_S_PA, WCE_AM_Fct_S_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='WCE',peakperiod='AM', geo='S',minimum_value=0)
        WCE_PM_Fct_S_PA, WCE_PM_Fct_S_AP = MChM.AP_PA_Factor(eb=eb, purpose=purp,mode='WCE',peakperiod='PM', geo='S',minimum_value=0)

        Gy_P = util.get_matrix_numpy(eb, 'gy_ensem')  + np.zeros((1, NoTAZ))


        Tran_MD_Fct = np.array([np.where(Gy_P<8, Tran_MD_Fct_N_PA, Tran_MD_Fct_S_PA), np.where(Gy_P<8, Tran_MD_Fct_N_AP, Tran_MD_Fct_S_AP)])


        Acti_AM_Fct = np.array([np.where(Gy_P<8, Acti_AM_Fct_N_PA, Acti_AM_Fct_S_PA), np.where(Gy_P<8, Acti_AM_Fct_N_AP, Acti_AM_Fct_S_AP)])
        Acti_MD_Fct = np.array([np.where(Gy_P<8, Acti_MD_Fct_N_PA, Acti_MD_Fct_S_PA), np.where(Gy_P<8, Acti_MD_Fct_N_AP, Acti_MD_Fct_S_AP)])
        Acti_PM_Fct = np.array([np.where(Gy_P<8, Acti_PM_Fct_N_PA, Acti_PM_Fct_S_PA), np.where(Gy_P<8, Acti_PM_Fct_N_AP, Acti_PM_Fct_S_AP)])

        WCE_AM_Fct = np.where(Gy_P<8, WCE_AM_Fct_N_PA, WCE_AM_Fct_S_PA)
        WCE_PM_Fct = np.where(Gy_P<8, WCE_PM_Fct_N_AP, WCE_PM_Fct_S_AP)


#       #########################################################################################
#        ##       Split Park and Ride to Auto and Transit Legs
#       ##########################################################################################
        ## General Setup
        BLBsWk = util.get_matrix_numpy(eb, "buspr-lotChceWkAMPA").flatten() #Best Lot Bus Work
        BLRlWk = util.get_matrix_numpy(eb, "railpr-lotChceWkAMPA").flatten() #Best Lot Rail Work
        BLWcWk = util.get_matrix_numpy(eb, "wcepr-lotChceWkAMPA").flatten() #Best Lot WCE Work
        DfInt = util.get_pd_ij_df(eb)

        ## Bus
        Dfmerge = util.get_pd_ij_df(eb) # pandas Dataframe
        Dfmerge['BL'] = BLBsWk # best bus lot
        Dfmerge['BAuI1'] = BAuI1.flatten()
        Dfmerge['BAuI2'] = BAuI2.flatten()
        Dfmerge['BAuI3'] = BAuI3.flatten()

        DfmergedAuto = Dfmerge.groupby(['i', 'BL']).sum().reset_index()
        DfmergedTran = Dfmerge.groupby(['BL', 'j']).sum().reset_index()
        DfAuto, DfTran = self.splitpnr(DfmergedAuto, DfmergedTran, DfInt)

# Store park and ride Demands separately for time slicing
        SOV_BAu_I1 = DfAuto['BAuI1'].reshape(NoTAZ, NoTAZ)  # low income SOV trips to PnR Zones
        SOV_BAu_I2 = DfAuto['BAuI2'].reshape(NoTAZ, NoTAZ)  # med income SOV trips to PnR Zones
        SOV_BAu_I3 = DfAuto['BAuI3'].reshape(NoTAZ, NoTAZ)  # high income SOV trips to PnR Zones
        Bus_BAu    = (DfTran['BAuI1'].reshape(NoTAZ, NoTAZ) # bus trips from PnR zone to destination
                     +DfTran['BAuI2'].reshape(NoTAZ, NoTAZ)
                     +DfTran['BAuI3'].reshape(NoTAZ, NoTAZ))

        ## Rail
        Dfmerge = util.get_pd_ij_df(eb)
        Dfmerge['BL'] = BLRlWk
        Dfmerge['RAuI1'] = RAuI1.flatten()
        Dfmerge['RAuI2'] = RAuI2.flatten()
        Dfmerge['RAuI3'] = RAuI3.flatten()

        DfmergedAuto = Dfmerge.groupby(['i', 'BL']).sum().reset_index()
        DfmergedTran = Dfmerge.groupby(['BL', 'j']).sum().reset_index()
        DfAuto, DfTran = self.splitpnr(DfmergedAuto, DfmergedTran, DfInt)

        SOV_RAu_I1 = DfAuto['RAuI1'].reshape(NoTAZ, NoTAZ) # low income SOV trips to PnR Zones
        SOV_RAu_I2 = DfAuto['RAuI2'].reshape(NoTAZ, NoTAZ) # med income SOV trips to PnR Zones
        SOV_RAu_I3 = DfAuto['RAuI3'].reshape(NoTAZ, NoTAZ) # high income SOV trips to PnR Zones
        Ral_RAu    = (DfTran['RAuI1'].reshape(NoTAZ, NoTAZ)# rail trips from PnR zone to destination
                     +DfTran['RAuI2'].reshape(NoTAZ, NoTAZ)
                     +DfTran['RAuI3'].reshape(NoTAZ, NoTAZ))
        ##WCE
        Dfmerge = util.get_pd_ij_df(eb)
        Dfmerge['BL'] = BLWcWk
        Dfmerge['WAuI1'] = WAuI1.flatten()
        Dfmerge['WAuI2'] = WAuI2.flatten()
        Dfmerge['WAuI3'] = WAuI3.flatten()

        DfmergedAuto = Dfmerge.groupby(['i', 'BL']).sum().reset_index()
        DfmergedTran = Dfmerge.groupby(['BL', 'j']).sum().reset_index()
        DfAuto, DfTran = self.splitpnr(DfmergedAuto, DfmergedTran, DfInt)

        SOV_WAu_I1 = DfAuto['WAuI1'].reshape(NoTAZ, NoTAZ) # low income SOV trips to PnR Zones
        SOV_WAu_I2 = DfAuto['WAuI2'].reshape(NoTAZ, NoTAZ) # med income SOV trips to PnR Zones
        SOV_WAu_I3 = DfAuto['WAuI3'].reshape(NoTAZ, NoTAZ) # high income SOV trips to PnR Zones
        WCE_WAu    = (DfTran['WAuI1'].reshape(NoTAZ, NoTAZ)# rail trips from PnR zone to destination
                     +DfTran['WAuI2'].reshape(NoTAZ, NoTAZ)
                     +DfTran['WAuI3'].reshape(NoTAZ, NoTAZ))

        del Dfmerge, DfmergedAuto, DfmergedTran
        del DfAuto, DfTran

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

        ## HOV2 Trips
        HV2I1_AM = HV2I1*Auto_AM_Fct_PA + HV2I1.transpose()*Auto_AM_Fct_AP # Low Income
        HV2I1_MD = HV2I1*Auto_MD_Fct_PA + HV2I1.transpose()*Auto_MD_Fct_AP
        HV2I1_PM = HV2I1*Auto_PM_Fct_PA + HV2I1.transpose()*Auto_PM_Fct_AP

        HV2I2_AM = HV2I2*Auto_AM_Fct_PA + HV2I2.transpose()*Auto_AM_Fct_AP # Med Income
        HV2I2_MD = HV2I2*Auto_MD_Fct_PA + HV2I2.transpose()*Auto_MD_Fct_AP
        HV2I2_PM = HV2I2*Auto_PM_Fct_PA + HV2I2.transpose()*Auto_PM_Fct_AP

        HV2I3_AM = HV2I3*Auto_AM_Fct_PA + HV2I3.transpose()*Auto_AM_Fct_AP # High Income
        HV2I3_MD = HV2I3*Auto_MD_Fct_PA + HV2I3.transpose()*Auto_MD_Fct_AP
        HV2I3_PM = HV2I3*Auto_PM_Fct_PA + HV2I3.transpose()*Auto_PM_Fct_AP

        ## HOV3 Trips
        HV3I1_AM = HV3I1*Auto_AM_Fct_PA + HV3I1.transpose()*Auto_AM_Fct_AP# Low Income
        HV3I1_MD = HV3I1*Auto_MD_Fct_PA + HV3I1.transpose()*Auto_MD_Fct_AP
        HV3I1_PM = HV3I1*Auto_PM_Fct_PA + HV3I1.transpose()*Auto_PM_Fct_AP

        HV3I2_AM = HV3I2*Auto_AM_Fct_PA + HV3I2.transpose()*Auto_AM_Fct_AP# Med Income
        HV3I2_MD = HV3I2*Auto_MD_Fct_PA + HV3I2.transpose()*Auto_MD_Fct_AP
        HV3I2_PM = HV3I2*Auto_PM_Fct_PA + HV3I2.transpose()*Auto_PM_Fct_AP

        HV3I3_AM = HV3I3*Auto_AM_Fct_PA + HV3I3.transpose()*Auto_AM_Fct_AP# High Income
        HV3I3_MD = HV3I3*Auto_MD_Fct_PA + HV3I3.transpose()*Auto_MD_Fct_AP
        HV3I3_PM = HV3I3*Auto_PM_Fct_PA + HV3I3.transpose()*Auto_PM_Fct_AP

        ## Transit Trips
        Bus_AM = Bus*Bus_AM_Fct_PA + Bus.transpose()*Bus_AM_Fct_AP
        Bus_MD = Bus*Tran_MD_Fct[0] + Bus.transpose()*Tran_MD_Fct[1]
        Bus_PM = Bus*Bus_PM_Fct_PA + Bus.transpose()*Bus_PM_Fct_AP

        Rail_AM = Rail*Rail_AM_Fct_PA + Rail.transpose()*Rail_AM_Fct_AP
        Rail_MD = Rail*Tran_MD_Fct[0] + Rail.transpose()*Tran_MD_Fct[1]
        Rail_PM = Rail*Rail_PM_Fct_PA + Rail.transpose()*Rail_PM_Fct_AP

        WCE_AM = WCE*WCE_AM_Fct  # no MD for WCE
        WCE_PM = WCE.transpose()*WCE_PM_Fct

        ## Active Trips
        Walk_AM = Walk*Acti_AM_Fct[0] + Walk.transpose()*Acti_AM_Fct[1]
        Walk_MD = Walk*Acti_MD_Fct[0] + Walk.transpose()*Acti_MD_Fct[1]
        Walk_PM = Walk*Acti_PM_Fct[0] + Walk.transpose()*Acti_PM_Fct[1]

        Bike_AM = Bike*Acti_AM_Fct[0] + Bike.transpose()*Acti_AM_Fct[1]
        Bike_MD = Bike*Acti_MD_Fct[0] + Bike.transpose()*Acti_MD_Fct[1]
        Bike_PM = Bike*Acti_PM_Fct[0] + Bike.transpose()*Acti_PM_Fct[1]

        ## Park and Ride Trips

        # Bus PnR Trips Auto leg by income and TOD
        SOV_BAu_I1_AM = SOV_BAu_I1*Auto_AM_Fct_PA + SOV_BAu_I1.transpose()*Auto_AM_Fct_AP
        SOV_BAu_I1_MD = SOV_BAu_I1*Auto_MD_Fct_PA + SOV_BAu_I1.transpose()*Auto_MD_Fct_AP
        SOV_BAu_I1_PM = SOV_BAu_I1*Auto_PM_Fct_PA + SOV_BAu_I1.transpose()*Auto_PM_Fct_AP

        SOV_BAu_I2_AM = SOV_BAu_I2*Auto_AM_Fct_PA + SOV_BAu_I2.transpose()*Auto_AM_Fct_AP
        SOV_BAu_I2_MD = SOV_BAu_I2*Auto_MD_Fct_PA + SOV_BAu_I2.transpose()*Auto_MD_Fct_AP
        SOV_BAu_I2_PM = SOV_BAu_I2*Auto_PM_Fct_PA + SOV_BAu_I2.transpose()*Auto_PM_Fct_AP

        SOV_BAu_I3_AM = SOV_BAu_I3*Auto_AM_Fct_PA + SOV_BAu_I3.transpose()*Auto_AM_Fct_AP
        SOV_BAu_I3_MD = SOV_BAu_I3*Auto_MD_Fct_PA + SOV_BAu_I3.transpose()*Auto_MD_Fct_AP
        SOV_BAu_I3_PM = SOV_BAu_I3*Auto_PM_Fct_PA + SOV_BAu_I3.transpose()*Auto_PM_Fct_AP

        # Bus PnR Trips Transit leg
        Bus_BAu_AM = Bus_BAu*Auto_AM_Fct_PA + Bus_BAu.transpose()*Auto_AM_Fct_AP
        Bus_BAu_MD = Bus_BAu*Auto_MD_Fct_PA + Bus_BAu.transpose()*Auto_MD_Fct_AP
        Bus_BAu_PM = Bus_BAu*Auto_PM_Fct_PA + Bus_BAu.transpose()*Auto_PM_Fct_AP

        # Rail PnR Trips Auto Leg by income and TOD
        SOV_RAu_I1_AM = SOV_RAu_I1*Auto_AM_Fct_PA + SOV_RAu_I1.transpose()*Auto_AM_Fct_AP
        SOV_RAu_I1_MD = SOV_RAu_I1*Auto_MD_Fct_PA + SOV_RAu_I1.transpose()*Auto_MD_Fct_AP
        SOV_RAu_I1_PM = SOV_RAu_I1*Auto_PM_Fct_PA + SOV_RAu_I1.transpose()*Auto_PM_Fct_AP

        SOV_RAu_I2_AM = SOV_RAu_I2*Auto_AM_Fct_PA + SOV_RAu_I2.transpose()*Auto_AM_Fct_AP
        SOV_RAu_I2_MD = SOV_RAu_I2*Auto_MD_Fct_PA + SOV_RAu_I2.transpose()*Auto_MD_Fct_AP
        SOV_RAu_I2_PM = SOV_RAu_I2*Auto_PM_Fct_PA + SOV_RAu_I2.transpose()*Auto_PM_Fct_AP

        SOV_RAu_I3_AM = SOV_RAu_I3*Auto_AM_Fct_PA + SOV_RAu_I3.transpose()*Auto_AM_Fct_AP
        SOV_RAu_I3_MD = SOV_RAu_I3*Auto_MD_Fct_PA + SOV_RAu_I3.transpose()*Auto_MD_Fct_AP
        SOV_RAu_I3_PM = SOV_RAu_I3*Auto_PM_Fct_PA + SOV_RAu_I3.transpose()*Auto_PM_Fct_AP

        # Rail PnR Transit Leg
        Ral_RAu_AM = Ral_RAu*Auto_AM_Fct_PA + Ral_RAu.transpose()*Auto_AM_Fct_AP
        Ral_RAu_MD = Ral_RAu*Auto_MD_Fct_PA + Ral_RAu.transpose()*Auto_MD_Fct_AP
        Ral_RAu_PM = Ral_RAu*Auto_PM_Fct_PA + Ral_RAu.transpose()*Auto_PM_Fct_AP


        # WCW PnR Trips Auto Leg by income and TOD
        SOV_WAu_I1_AM = SOV_WAu_I1*WCE_AM_Fct
        SOV_WAu_I1_PM = SOV_WAu_I1.transpose()*WCE_PM_Fct

        SOV_WAu_I2_AM = SOV_WAu_I2*WCE_AM_Fct
        SOV_WAu_I2_PM = SOV_WAu_I2.transpose()*WCE_PM_Fct

        SOV_WAu_I3_AM = SOV_WAu_I3*WCE_AM_Fct
        SOV_WAu_I3_PM = SOV_WAu_I3.transpose()*WCE_PM_Fct

        # WCW PnR Trips Transit Leg
        WCE_WAu_AM = WCE_WAu*WCE_AM_Fct
        WCE_WAu_PM = WCE_WAu.transpose()*WCE_PM_Fct

        # Put everything together
        # 24 Hour P-A Trips
        # Add PnR legs
        SOVI1 = SOVI1 + SOV_BAu_I1 + SOV_RAu_I1 + SOV_WAu_I1
        SOVI2 = SOVI2 + SOV_BAu_I2 + SOV_RAu_I2 + SOV_WAu_I2
        SOVI3 = SOVI3 + SOV_BAu_I3 + SOV_RAu_I3 + SOV_WAu_I3
        # Add PnR legs
        Bus =  Bus +  Bus_BAu
        Rail = Rail + Ral_RAu
        WCE = WCE + WCE_WAu

        del SOV_BAu_I1, SOV_RAu_I1, SOV_WAu_I1
        del SOV_BAu_I2, SOV_RAu_I2, SOV_WAu_I2
        del SOV_BAu_I3, SOV_RAu_I3, SOV_WAu_I3
        del Bus_BAu, Ral_RAu, WCE_WAu

        # Peak Hour Person Trips
        SOVI1_AM = SOVI1_AM + SOV_BAu_I1_AM + SOV_RAu_I1_AM + SOV_WAu_I1_AM
        SOVI1_MD = SOVI1_MD + SOV_BAu_I1_MD + SOV_RAu_I1_MD
        SOVI1_PM = SOVI1_PM + SOV_BAu_I1_PM + SOV_RAu_I1_PM + SOV_WAu_I1_PM

        del SOV_BAu_I1_AM, SOV_RAu_I1_AM, SOV_WAu_I1_AM
        del SOV_BAu_I1_MD, SOV_RAu_I1_MD
        del SOV_BAu_I1_PM, SOV_RAu_I1_PM, SOV_WAu_I1_PM

        SOVI2_AM = SOVI2_AM + SOV_BAu_I2_AM + SOV_RAu_I2_AM + SOV_WAu_I2_AM
        SOVI2_MD = SOVI2_MD + SOV_BAu_I2_MD + SOV_RAu_I2_MD
        SOVI2_PM = SOVI2_PM + SOV_BAu_I2_PM + SOV_RAu_I2_PM + SOV_WAu_I2_PM

        del SOV_BAu_I2_AM, SOV_RAu_I2_AM, SOV_WAu_I2_AM
        del SOV_BAu_I2_MD, SOV_RAu_I2_MD
        del SOV_BAu_I2_PM, SOV_RAu_I2_PM, SOV_WAu_I2_PM


        SOVI3_AM = SOVI3_AM + SOV_BAu_I3_AM + SOV_RAu_I3_AM + SOV_WAu_I3_AM
        SOVI3_MD = SOVI3_MD + SOV_BAu_I3_MD + SOV_RAu_I3_MD
        SOVI3_PM = SOVI3_PM + SOV_BAu_I3_PM + SOV_RAu_I3_PM + SOV_WAu_I3_PM

        del SOV_BAu_I3_AM, SOV_RAu_I3_AM, SOV_WAu_I3_AM
        del SOV_BAu_I3_MD, SOV_RAu_I3_MD
        del SOV_BAu_I3_PM, SOV_RAu_I3_PM, SOV_WAu_I3_PM

        HOVI1_AM = HV2I1_AM + HV3I1_AM
        HOVI1_MD = HV2I1_MD + HV3I1_MD
        HOVI1_PM = HV2I1_PM + HV3I1_PM

        HOVI2_AM = HV2I2_AM + HV3I2_AM
        HOVI2_MD = HV2I2_MD + HV3I2_MD
        HOVI2_PM = HV2I2_PM + HV3I2_PM

        HOVI3_AM = HV2I3_AM + HV3I3_AM
        HOVI3_MD = HV2I3_MD + HV3I3_MD
        HOVI3_PM = HV2I3_PM + HV3I3_PM

        Bus_AM   += Bus_BAu_AM
        Bus_MD   += Bus_BAu_MD
        Bus_PM   += Bus_BAu_PM
        del Bus_BAu_AM, Bus_BAu_MD, Bus_BAu_PM


        Rail_AM  += Ral_RAu_AM
        Rail_MD  += Ral_RAu_MD
        Rail_PM  += Ral_RAu_PM
        del Ral_RAu_AM, Ral_RAu_MD, Ral_RAu_PM

        WCE_AM   += WCE_WAu_AM
        WCE_PM   += WCE_WAu_PM

        del WCE_WAu_AM, WCE_WAu_PM

        # Convert HOV to Auto Drivers
        # HOV2
        AuDr_HV2I1_AM = HV2I1_AM/2.0
        AuDr_HV2I1_MD = HV2I1_MD/2.0
        AuDr_HV2I1_PM = HV2I1_PM/2.0

        AuDr_HV2I2_AM = HV2I2_AM/2.0
        AuDr_HV2I2_MD = HV2I2_MD/2.0
        AuDr_HV2I2_PM = HV2I2_PM/2.0

        AuDr_HV2I3_AM = HV2I3_AM/2.0
        AuDr_HV2I3_MD = HV2I3_MD/2.0
        AuDr_HV2I3_PM = HV2I3_PM/2.0

        # HOV3+
        AuDr_HV3I1_AM = HV3I1_AM/Occ
        AuDr_HV3I1_MD = HV3I1_MD/Occ
        AuDr_HV3I1_PM = HV3I1_PM/Occ

        AuDr_HV3I2_AM = HV3I2_AM/Occ
        AuDr_HV3I2_MD = HV3I2_MD/Occ
        AuDr_HV3I2_PM = HV3I2_PM/Occ

        AuDr_HV3I3_AM = HV3I3_AM/Occ
        AuDr_HV3I3_MD = HV3I3_MD/Occ
        AuDr_HV3I3_PM = HV3I3_PM/Occ

        # Add HOV2 and HOV3
        AuDr_HOVI1_AM = AuDr_HV2I1_AM + AuDr_HV3I1_AM
        AuDr_HOVI1_MD = AuDr_HV2I1_MD + AuDr_HV3I1_MD
        AuDr_HOVI1_PM = AuDr_HV2I1_PM + AuDr_HV3I1_PM

        AuDr_HOVI2_AM = AuDr_HV2I2_AM + AuDr_HV3I2_AM
        AuDr_HOVI2_MD = AuDr_HV2I2_MD + AuDr_HV3I2_MD
        AuDr_HOVI2_PM = AuDr_HV2I2_PM + AuDr_HV3I2_PM

        AuDr_HOVI3_AM = AuDr_HV2I3_AM + AuDr_HV3I3_AM
        AuDr_HOVI3_MD = AuDr_HV2I3_MD + AuDr_HV3I3_MD
        AuDr_HOVI3_PM = AuDr_HV2I3_PM + AuDr_HV3I3_PM

        # clean memory

        del HV2I1_AM, HV2I1_MD, HV2I1_PM
        del HV2I2_AM, HV2I2_MD, HV2I2_PM
        del HV2I3_AM, HV2I3_MD, HV2I3_PM

        del HV3I1_AM, HV3I1_MD, HV3I1_PM
        del HV3I2_AM, HV3I2_MD, HV3I2_PM
        del HV3I3_AM, HV3I3_MD, HV3I3_PM

        del AuDr_HV2I1_AM, AuDr_HV2I1_MD, AuDr_HV2I1_PM
        del AuDr_HV2I2_AM, AuDr_HV2I2_MD, AuDr_HV2I2_PM
        del AuDr_HV2I3_AM, AuDr_HV2I3_MD, AuDr_HV2I3_PM

        del AuDr_HV3I1_AM, AuDr_HV3I1_MD, AuDr_HV3I1_PM
        del AuDr_HV3I2_AM, AuDr_HV3I2_MD, AuDr_HV3I2_PM
        del AuDr_HV3I3_AM, AuDr_HV3I3_MD, AuDr_HV3I3_PM

        ##############################################################################
            ##       Set Demand Matrices
        ##############################################################################

        # 24 hours

        util.set_matrix_numpy(eb, "HbWSOVI1PerTrips", SOVI1)
        util.set_matrix_numpy(eb, "HbWSOVI2PerTrips", SOVI2)
        util.set_matrix_numpy(eb, "HbWSOVI3PerTrips", SOVI3)
        util.set_matrix_numpy(eb, "HbWHV2I1PerTrips", HV2I1)
        util.set_matrix_numpy(eb, "HbWHV2I2PerTrips", HV2I2)
        util.set_matrix_numpy(eb, "HbWHV2I3PerTrips", HV2I3)
        util.set_matrix_numpy(eb, "HbWHV3+I1PerTrips", HV3I1)
        util.set_matrix_numpy(eb, "HbWHV3+I2PerTrips", HV3I2)
        util.set_matrix_numpy(eb, "HbWHV3+I3PerTrips", HV3I3)
        util.set_matrix_numpy(eb, "HbWBusPerTrips", Bus)
        util.set_matrix_numpy(eb, "HbWRailPerTrips", Rail)
        util.set_matrix_numpy(eb, "HbWWCEPerTrips", WCE)
        util.set_matrix_numpy(eb, "HbWWalkPerTrips", Walk)
        util.set_matrix_numpy(eb, "HbWBikePerTrips", Bike)

       # Auto-person

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
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_3_Am", HOVI3_AM)
        # MD
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_2_Md", HOVI1_MD)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_3_Md", HOVI2_MD)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_3_Md", HOVI3_MD)
        # PM
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_2_Pm", HOVI1_PM)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_3_Pm", HOVI2_PM)
        util.add_matrix_numpy(eb, "HOV_pertrp_VOT_3_Pm", HOVI3_PM)

        # Transit
        # AM
        util.add_matrix_numpy(eb, "busAm", Bus_AM)
        util.add_matrix_numpy(eb, "railAm", Rail_AM)
        util.add_matrix_numpy(eb, "WCEAm", WCE_AM)
        # MD
        util.add_matrix_numpy(eb, "busMd", Bus_MD)
        util.add_matrix_numpy(eb, "railMd", Rail_MD)

        # PM
        util.add_matrix_numpy(eb, "busPm", Bus_PM)
        util.add_matrix_numpy(eb, "railPm", Rail_PM)
        util.add_matrix_numpy(eb, "WCEPm", WCE_PM)

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
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_3_Am", AuDr_HOVI3_AM)
        # MD
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_2_Md", AuDr_HOVI1_MD)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_3_Md", AuDr_HOVI2_MD)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_3_Md", AuDr_HOVI3_MD)
        # PM
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_2_Pm", AuDr_HOVI1_PM)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_3_Pm", AuDr_HOVI2_PM)
        util.add_matrix_numpy(eb, "HOV_drvtrp_VOT_3_Pm", AuDr_HOVI3_PM)

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
        T_HOV = HV2I1 + HV2I2 + HV2I3 + HV3I1 + HV3I2 + HV3I3

        #
        df_demand = pd.DataFrame()

        Gy_P = util.get_matrix_numpy(eb, 'gy_ensem')  + np.zeros((1, NoTAZ))
        Gy_A = Gy_P.transpose()

        df_demand['gy_i'] = Gy_P.flatten()
        df_demand['gy_j'] = Gy_A.flatten()
        df_demand.gy_i = df_demand.gy_i.astype(int)
        df_demand.gy_j = df_demand.gy_j.astype(int)
        mode_list_am_pm = ['sov', 'hov', 'bus', 'rail', 'wce', 'walk', 'bike']
        mode_list_md = ['sov', 'hov', 'bus', 'rail', 'walk', 'bike']
        mode_list_daily = ['sov', 'hov', 'bus', 'rail', 'wce', 'walk', 'bike']

        AM_Demand_List = [T_SOV_AM, T_HOV_AM, Bus_AM, Rail_AM, WCE_AM, Walk_AM, Bike_AM]
        MD_Demand_List = [T_SOV_MD, T_HOV_MD, Bus_MD, Rail_MD, Walk_MD, Bike_MD]
        PM_Demand_List = [T_SOV_PM, T_HOV_PM, Bus_PM, Rail_PM, WCE_PM, Walk_PM, Bike_PM]
        Daily_Demand_List = [T_SOV, T_HOV, Bus, Rail, WCE, Walk, Bike]

        zero_demand = 0
        purp = "hbw"

        df_AM_Gy = MChM.Demand_Summary(df_demand, purp, "AM", AM_Demand_List, mode_list_am_pm)

        df_MD_Gy = MChM.Demand_Summary(df_demand, purp, "MD", MD_Demand_List, mode_list_md)

        df_PM_Gy = MChM.Demand_Summary(df_demand, purp, "PM", PM_Demand_List, mode_list_am_pm)

        df_Daily_Gy = MChM.Demand_Summary(df_demand, purp, "daily", Daily_Demand_List, mode_list_am_pm)

        df_gy_phr = pd.concat([df_AM_Gy, df_MD_Gy, df_PM_Gy])

        df_gy_phr = df_gy_phr[['gy_i','gy_j','purpose','mode', 'period', 'trips']]

        df_Daily_Gy = df_Daily_Gy[['gy_i','gy_j','purpose','mode', 'period', 'trips']]


        ## Dump to SQLite DB
        conn = util.get_db_byname(eb, "trip_summaries.db")

        df_gy_phr.to_sql(name='phr_gy', con=conn, flavor='sqlite', index=False, if_exists='replace')

        df_Daily_Gy.to_sql(name='daily_gy', con=conn, flavor='sqlite', index=False, if_exists='replace')

        conn.close()

        return df_Daily_Gy

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
        util.initmat(eb, "mf9000", "HbWLSI1A0", " HbW LogSum I1 A0", 0)
        util.initmat(eb, "mf9001", "HbWLSI1A1", " HbW LogSum I1 A1", 0)
        util.initmat(eb, "mf9002", "HbWLSI1A2", " HbW LogSum I1 A2", 0)
        util.initmat(eb, "mf9003", "HbWLSI2A0", " HbW LogSum I1 A0", 0)
        util.initmat(eb, "mf9004", "HbWLSI2A1", " HbW LogSum I1 A1", 0)
        util.initmat(eb, "mf9005", "HbWLSI2A2", " HbW LogSum I1 A2", 0)
        util.initmat(eb, "mf9006", "HbWLSI3A0", " HbW LogSum I1 A0", 0)
        util.initmat(eb, "mf9007", "HbWLSI3A1", " HbW LogSum I1 A1", 0)
        util.initmat(eb, "mf9008", "HbWLSI3A2", " HbW LogSum I1 A2", 0)

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
#
#        ## Initialize P-A Trip Tables by mode
        util.initmat(eb, "mf3000", "HbWSOVI1PerTrips", "HbW SOV Low Income Per-Trips", 0)
        util.initmat(eb, "mf3001", "HbWSOVI2PerTrips", "HbW SOV Med Income Per-Trips", 0)
        util.initmat(eb, "mf3002", "HbWSOVI3PerTrips", "HbW SOV High Income Per-Trips", 0)
        util.initmat(eb, "mf3005", "HbWHV2I1PerTrips", "HbW HV2 Low Income Per-Trips", 0)
        util.initmat(eb, "mf3006", "HbWHV2I2PerTrips", "HbW HV2 Med Income Per-Trips", 0)
        util.initmat(eb, "mf3007", "HbWHV2I3PerTrips", "HbW HV2 High Income Per-Trips", 0)
        util.initmat(eb, "mf3010", "HbWHV3+I1PerTrips", "HbW HV3+ Low Income Per-Trips", 0)
        util.initmat(eb, "mf3011", "HbWHV3+I2PerTrips", "HbW HV3+ Med Income Per-Trips", 0)
        util.initmat(eb, "mf3012", "HbWHV3+I3PerTrips", "HbW HV3+ High Income Per-Trips", 0)
        util.initmat(eb, "mf3015", "HbWBusPerTrips", "HbW Bus Per-Trips", 0)
        util.initmat(eb, "mf3020", "HbWRailPerTrips", "HbW Rail Per-Trips", 0)
        util.initmat(eb, "mf3025", "HbWWCEPerTrips", "HbW WCE Per-Trips", 0)
        util.initmat(eb, "mf3030", "HbWWalkPerTrips", "HbW Walk Per-Trips", 0)
        util.initmat(eb, "mf3035", "HbWBikePerTrips", "HbW Bike Per-Trips", 0)
#
#        ## Initialize P-A Trip Tables from trip distribution
        util.initmat(eb, "mf3050", "HbWP-AI1A0", " HbW P-A Trips I1 A0", 0)
        util.initmat(eb, "mf3051", "HbWP-AI1A1", " HbW P-A Trips I1 A1", 0)
        util.initmat(eb, "mf3052", "HbWP-AI1A2", " HbW P-A Trips I1 A2", 0)
        util.initmat(eb, "mf3053", "HbWP-AI2A0", " HbW P-A Trips I1 A0", 0)
        util.initmat(eb, "mf3054", "HbWP-AI2A1", " HbW P-A Trips I1 A1", 0)
        util.initmat(eb, "mf3055", "HbWP-AI2A2", " HbW P-A Trips I1 A2", 0)
        util.initmat(eb, "mf3056", "HbWP-AI3A0", " HbW P-A Trips I1 A0", 0)
        util.initmat(eb, "mf3057", "HbWP-AI3A1", " HbW P-A Trips I1 A1", 0)
        util.initmat(eb, "mf3058", "HbWP-AI3A2", " HbW P-A Trips I1 A2", 0)
