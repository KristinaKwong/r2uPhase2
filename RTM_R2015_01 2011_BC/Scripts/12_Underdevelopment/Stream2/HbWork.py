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

class HbWork(_m.Tool()):

    ##Global attribute for Tool Run Message (successful/not successful)
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Home Base Work"
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

    @_m.logbook_trace("Run Home Base Work")
    def __call__(self, eb):
        util = _m.Modeller().tool("translink.emme.util")
        MChM = _m.Modeller().tool("translink.RTM3.testtdmc.ModeChoiceUtils")
        input_path = util.get_input_path(eb)
        self.matrix_batchins(eb)
        NoTAZ = len(util.get_matrix_numpy(eb, "zoneindex"))

#        ##############################################################################
#        ##       Define Availability conditions
#        ##############################################################################

        AvailDict = {
                     'AutDist': 0.0,
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
                     'PRAutTim': 0.0
                    }

        # Declare Utilities Data Frame
        DfU = {}
        # Add Coefficients

        p2   =  0.165342
        p3   = -1.631934
        p4   =  1.073040
        p5   = -4.263437
        p6   =  2.703188
        p7   = -2.317327
        p8   =  3.380394
        p9   = -2.365022
        p10  =  5.328974
        p11  =  0.124672
        p12  = -0.268663
        p13  = -0.189000
        p14  = -0.160833
        p17  = -0.141318
        p18  = -0.101003
        p19  = -0.591656
        p20  = -1.483697
        p21  = -0.444447
        p151 = -0.075147
        p152 = -0.087667
        p153 = -0.083120
        p160 =  4.420636
        p161 =  6.444305
        p162 =  1.244796
        p163 =  2.494739
        p164 =  1.326848
        p505 = -0.217369
        p506 = -0.307408
        p602 =  0.165480
        p603 =  0.122307
        p701 =  0.152645
        p850 =  1.711530
        p870 =  0.602662
        p991 = -0.114845
        p992 =  0.001120
        p993 =  2.196992
        p994 =  0.104691
        p995 = -0.001051
        p996 =  1.041571
        thet =  0.578051

#        ##############################################################################
#        ##       Auto Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        MaxPark = 10.0
        VOC = float(util.get_matrix_numpy(eb, 'autoOpCost')) # Veh Op Cost
        Occ = float(util.get_matrix_numpy(eb, 'HOVOccHbw')) # Occupancy
        Df['ParkCost'] = util.get_matrix_numpy(eb, 'prk8hr') # 8hr Parking
        Df['ParkCost'][Df['ParkCost']>MaxPark] = MaxPark # set parking>$10 to $10
        Df['ParkCost'] = Df['ParkCost'].reshape(1, NoTAZ) + np.zeros((NoTAZ, 1)) # Broadcast parking from vector to matrix

        Df['AutoDisSOV'] = util.get_matrix_numpy(eb, 'HbWBlSovDist') #SOV Distance
        Df['AutoTimSOV'] = util.get_matrix_numpy(eb, 'HbWBlSovTime') #SOV Time
        Df['AutoCosSOV'] = Df['AutoDisSOV']*VOC + util.get_matrix_numpy(eb, 'HbWBlSovToll') + Df['ParkCost'] #SOV Cost (per km + Toll + Parking)

        Df['AutoDisHOV'] = util.get_matrix_numpy(eb, 'HbWBlHovDist') #HOV Distance
        Df['AutoTimHOV'] = util.get_matrix_numpy(eb, 'HbWBlHovTime') #hOV Time
        Df['AutoCosHOV'] = Df['AutoDisHOV']*VOC + util.get_matrix_numpy(eb, 'HbWBlHovToll') + Df['ParkCost'] #HOV Cost (per km + Toll + Parking)

        # Utilities
        # SOV Common Utility for all incomes
        Df['GeUtl'] = ( 0
                      + p151*Df['AutoTimSOV'])


        Df['GeUtl']  = MChM.AutoAvail(Df['AutoDisSOV'], Df['GeUtl'], AvailDict) #Check Availability condition if mode not available then set to high negative utility (-9999)
        # Add Income Parameters
        DfU['SOVI1']  = Df['GeUtl'] + p12*Df['AutoCosSOV']
        DfU['SOVI2']  = Df['GeUtl'] + p13*Df['AutoCosSOV']
        DfU['SOVI3']  = Df['GeUtl'] + p14*Df['AutoCosSOV']

        # HOV2
        # HOV Common Utility for all incomes
        Df['GeUtl'] = ( p2
                      + p151*Df['AutoTimHOV'])


        Df['GeUtl']  = MChM.AutoAvail(Df['AutoDisHOV'], Df['GeUtl'], AvailDict) #Check Availability condition if mode not available then set to high negative utility (-9999)
        # Add Income Parameters
        DfU['HV2I1']  = Df['GeUtl'] + p12*Df['AutoCosHOV']/2.0
        DfU['HV2I2']  = Df['GeUtl'] + p13*Df['AutoCosHOV']/2.0
        DfU['HV2I3']  = Df['GeUtl'] + p14*Df['AutoCosHOV']/2.0

        # HOV3
        # HOV Common Utility for all incomes
        Df['GeUtl'] = ( p3
                      + p151*Df['AutoTimHOV'])

        Df['GeUtl']  = MChM.AutoAvail(Df['AutoDisHOV'], Df['GeUtl'], AvailDict) #Check Availability condition if mode not available then set to high negative utility (-9999)
        # Add Income Parameters
        DfU['HV3I1']  = Df['GeUtl'] + p12*Df['AutoCosHOV']/Occ
        DfU['HV3I2']  = Df['GeUtl'] + p13*Df['AutoCosHOV']/Occ
        DfU['HV3I3']  = Df['GeUtl'] + p14*Df['AutoCosHOV']/Occ


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
        Df['BusTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux'] + Df['BusBrd'] #Total travel Time

        Df['RalIVR'] = util.get_matrix_numpy(eb, 'HbWBlRailIvtt') #In vehicle Rail time on rail
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'HbWBlRailIvttBus') #In vehicle Rail time on bus
        Df['RalWat'] = util.get_matrix_numpy(eb, 'HbWBlRailWait') # Wait Rail Time
        Df['RalAux'] = util.get_matrix_numpy(eb, 'HbWBlRailAux') # Auxiliary Time
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'HbWBlRailBoard')
        Df['RalFar'] = util.get_matrix_numpy(eb, 'HbWBlRailFare')
        Df['RalTot'] = Df['RalIVB'] + Df['RalIVR'] + Df['RalWat'] + Df['RalAux'] + Df['RalBrd'] #Total travel Time
        Df['RalIBR'] = Df['RalIVB']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) #Ratio of IVT on Bus to total IVTT
        Df['RalIRR'] = Df['RalIVR']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) #Ratio of IVT on Rail to total IVTT

        Df['WCEIVW'] = util.get_matrix_numpy(eb, 'HbWBlWceIvtt') #In vehicle Rail time on wce
        Df['WCEIVR'] = util.get_matrix_numpy(eb, 'HbWBlWceIvttRail') #In vehicle Rail time on rail
        Df['WCEIVB'] = util.get_matrix_numpy(eb, 'HbWBlWceIvttBus') #In vehicle Rail time on bus
        Df['WCEWat'] = util.get_matrix_numpy(eb, 'HbWBlWceWait') # wait time
        Df['WCEAux'] = util.get_matrix_numpy(eb, 'HbWBlWceAux') # walk time
        Df['WCEBrd'] = util.get_matrix_numpy(eb, 'HbWBlWceBoards') # board time
        Df['WCEFar'] = util.get_matrix_numpy(eb, 'HbWBlWceFare') # wce fare
        Df['WCETot'] = Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW'] + Df['WCEWat'] + Df['WCEAux'] + Df['WCEBrd'] #Total travel Time
        Df['WCEIBR'] = Df['WCEIVB']/(Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW'] + Tiny) #Ratio of IVT on Bus to total IVTT
        Df['WCEIRR'] = Df['WCEIVR']/(Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW'] + Tiny) #Ratio of IVT on Rail to total IVTT
        Df['WCEIWR'] = Df['WCEIVW']/(Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW'] + Tiny) #Ratio of IVT on WCE to total IVTT

        Df['TranAccess'] = util.get_matrix_numpy(eb, 'transitAccLn').reshape(NoTAZ,1) + np.zeros((1, NoTAZ)) # Log transit accessiblity broadcast
        Df['IntZnl'] = np.identity(NoTAZ) # Intra-zonal matrix
        Df['AutoDis'] = util.get_matrix_numpy(eb, 'HbWBlSovDist') # Distance
        Df['AutoDisSqd'] = Df['AutoDis']* Df['AutoDis'] #Distance squared
        Df['LogAutoDis'] = np.log(Df['AutoDis'] + Tiny) # Log Distance

        # Utilities
        # Bus Utility
        # Bus Common Utility for all incomes
        Df['GeUtl'] = ( p4
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
                      + p152*Df['WCEIVB']
                      + p153*Df['WCEIVR']
                      + p153*Df['WCEIVW']
                      + p17*Df['WCEWat']
                      + p18*Df['WCEAux']
                      + p19*Df['WCEBrd']
                      + p994*Df['AutoDis']
                      + p995*Df['AutoDisSqd']
                      + p996*Df['LogAutoDis']
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
        Df['BAuDis'] = util.get_matrix_numpy(eb, 'HbWBlBAuPRDist') #Bus PR Drive Distance
        Df['BAuTim'] = util.get_matrix_numpy(eb, 'HbWBlBAuPRTime') # Bus PR Drive Time
        Df['BAuCos'] = Df['BAuDis']*VOC + util.get_matrix_numpy(eb, 'HbWBlBAuPRToll') + util.get_matrix_numpy(eb, 'HbWBAuPrkCst') # Bus PR Drive Cost
        Df['BAuTrm'] = util.get_matrix_numpy(eb, 'HbWBAuTrmTim') #Bus PR Terminal Time
        Df['BusIVT'] = util.get_matrix_numpy(eb, 'HbWBlBAuBusIvtt') #Bus IVTT
        Df['BusWat'] = util.get_matrix_numpy(eb, 'HbWBlBAuBusWait') #Bus Wait Time
        Df['BusAux'] = util.get_matrix_numpy(eb, 'HbWBlBAuBusAux') # Bus Walk Time
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'HbWBlBAuBusBoard') # Bus Boarding Time
        Df['BusFar'] = util.get_matrix_numpy(eb, 'HbWBlBAuBusFare') # Bus Fare
        Df['BAuTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux'] + Df['BusBrd'] + Df['BAuTim'] # Total Travel Time
        Df['BAuIBR'] = Df['BusIVT']/(Df['BusIVT'] + Df['BAuTim'] + Tiny) # Ratio of Time on Bus to total travel time


        Df['RAuDis'] = util.get_matrix_numpy(eb, 'HbWBlRAuPRDist') #Rail PR Drive Distance
        Df['RAuTim'] = util.get_matrix_numpy(eb, 'HbWBlRAuPRTime') #Rail PR Drive Time
        Df['RAuCos'] = Df['RAuDis']*VOC + util.get_matrix_numpy(eb, 'HbWBlRAuPRToll') + util.get_matrix_numpy(eb, 'HbWRAuPrkCst') # Rail PR Drive Cost
        Df['RAuTrm'] = util.get_matrix_numpy(eb, 'HbWRAuTrmTim') #Rail PR Terminal Time
        Df['RalIVR'] = util.get_matrix_numpy(eb, 'HbWBlRAuRailIvtt') #IVT on Rail
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'HbWBlRAuRailIvttBus') #IVT on Bus
        Df['RalWat'] = util.get_matrix_numpy(eb, 'HbWBlRAuRailWait') #Rail Wait Time
        Df['RalAux'] = util.get_matrix_numpy(eb, 'HbWBlRAuRailAux') #Rail Walk Time
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'HbWBlRAuRailBoard') #Rail Board Time
        Df['RalFar'] = util.get_matrix_numpy(eb, 'HbWBlRAuRailFare') #Rail Fare
        Df['RAuTot'] = Df['RalIVB'] + Df['RalIVR'] + Df['RalWat'] + Df['RalAux'] + Df['RalBrd'] +  Df['RAuTim'] # Total Travel Time
        Df['RAuIBR'] = Df['RalIVB']/(Df['RalIVB'] + Df['RalIVR'] + Df['RAuTim'] + Tiny) # Ratio of Time on Bus to total travel time
        Df['RAuIRR'] = Df['RalIVR']/(Df['RalIVB'] + Df['RalIVR'] + Df['RAuTim'] + Tiny) # Ratio of Time on Rail to total travel time


        Df['WAuDis'] = util.get_matrix_numpy(eb, 'HbWBlWAuPRDist') #WCE PR Drive Distance
        Df['WAuTim'] = util.get_matrix_numpy(eb, 'HbWBlWAuPRTime') #WCE PR Drive Time
        Df['WAuCos'] = Df['WAuDis']*VOC + util.get_matrix_numpy(eb, 'HbWBlWAuPRToll') + util.get_matrix_numpy(eb, 'HbWWAuPrkCst') # WCE PR Drive Cost
        Df['WAuTrm'] = util.get_matrix_numpy(eb, 'HbWWAuTrmTim') #WCE PR Terminal Time
        Df['WCEIVW'] = util.get_matrix_numpy(eb, 'HbWBlWAuWceIvtt') #IVT on WCE
        Df['WCEIVR'] = util.get_matrix_numpy(eb, 'HbWBlWAuWceIvttRail') #IVT on Rail
        Df['WCEIVB'] = util.get_matrix_numpy(eb, 'HbWBlWAuWceIvttBus') #IVT on Bus
        Df['WCEWat'] = util.get_matrix_numpy(eb, 'HbWBlWAuWceWait') #WCE Wait Time
        Df['WCEAux'] = util.get_matrix_numpy(eb, 'HbWBlWAuWceAux')  #WCE Walk Time
        Df['WCEBrd'] = util.get_matrix_numpy(eb, 'HbWBlWAuWceBoards') #WCE Board Time
        Df['WCEFar'] = util.get_matrix_numpy(eb, 'HbWBlWAuWceFare') #WCE Fare
        Df['WAuTot'] = Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW'] + Df['WCEWat'] + Df['WCEAux'] + Df['WCEBrd'] + Df['WAuTim'] # Total Travel Time
        Df['WAuIBR'] = Df['WCEIVB']/(Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW']+ Df['WAuTim'] + Tiny) # Ratio of Time on Bus to total travel time
        Df['WAuIRR'] = Df['WCEIVR']/(Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW']+ Df['WAuTim'] + Tiny) # Ratio of Time on Rail to total travel time
        Df['WAuIWR'] = Df['WCEIVW']/(Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW']+ Df['WAuTim'] + Tiny) # Ratio of Time on WCE to total travel time

        Df['IntZnl'] = np.identity(NoTAZ) # Intra-zonal
        Df['AutoDis'] = util.get_matrix_numpy(eb, 'HbWBlSovDist') # Distance
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
        DfU['BAuI1'] = Df['GeUtl'] + p12*(Df['BusFar'] + Df['BAuCos'])
        DfU['BAuI2'] = Df['GeUtl'] + p13*(Df['BusFar'] + Df['BAuCos'])
        DfU['BAuI3'] = Df['GeUtl'] + p14*(Df['BusFar'] + Df['BAuCos'])

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
                      + p994*Df['AutoDis']
                      + p995*Df['AutoDisSqd']
                      + p996*Df['LogAutoDis'])

        # Check availability conditions else add high negative utility (-99999)
        Df['GeUtl'] = MChM.RAuAvail(Df, Df['GeUtl'], AvailDict)
        # Add Income Parameters
        DfU['RAuI1'] = Df['GeUtl'] + p12*(Df['RalFar'] + Df['RAuCos'])
        DfU['RAuI2'] = Df['GeUtl'] + p13*(Df['RalFar'] + Df['RAuCos'])
        DfU['RAuI3'] = Df['GeUtl'] + p14*(Df['RalFar'] + Df['RAuCos'])

        # Utilities
        # PR WCE Utility
        # PR WCE Common Utility for all incomes
        DfU['GeUtl'] = ( p9
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
                       + p994*Df['AutoDis']
                       + p995*Df['AutoDisSqd']
                       + p996*Df['LogAutoDis'])

        # Check availability conditions else add high negative utility (-99999)
        Df['GeUtl'] = MChM.WAuAvail(Df, DfU['GeUtl'],AvailDict)
        # Add Income Parameters
        DfU['WAuI1'] = Df['GeUtl'] + p12*(Df['WCEFar'] + Df['WAuCos'])
        DfU['WAuI2'] = Df['GeUtl'] + p13*(Df['WCEFar'] + Df['WAuCos'])
        DfU['WAuI3'] = Df['GeUtl'] + p14*(Df['WCEFar'] + Df['WAuCos'])

#        ##############################################################################
#        ##       Active Modes
#        ##############################################################################

        Df = {}
        Df['AutoDis'] = util.get_matrix_numpy(eb, 'HbWBlSovDist') #Distance
        Df['IntrCBD'] = util.get_matrix_numpy(eb, 'd_cbd') #Intra-CBD
        Df['IntrCBD'] = Df['IntrCBD'].reshape(NoTAZ, 1)*Df['IntrCBD'].reshape(1, NoTAZ) #Broadcast intra-CBD

        Df['PopEmpDenPA'] = util.get_matrix_numpy(eb, 'combinedens')#Pop+Emp Density at Prod and Attr Zones
        Df['PopEmpDenPA'] = Df['PopEmpDenPA'].reshape(NoTAZ, 1) + Df['PopEmpDenPA'].reshape(1, NoTAZ) #Broadcast Density

        Df['PopSen'] = util.get_matrix_numpy(eb, 'Pop55t64') + util.get_matrix_numpy(eb, 'Pop65Up') #Senior Proportion
        Df['PopTot'] = util.get_matrix_numpy(eb, 'TotEmp')
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

        ## Add SOV Availability Term

        CarShare = util.get_matrix_numpy(eb, 'cs500').reshape(NoTAZ,1) + np.zeros((1, NoTAZ))
        LrgU     = -99999.0
        ## Low Income Zero Autos
        Dict = {
               'SOV'  : [np.where(CarShare>0, DfU['SOVI1'], LrgU)],
               'HOV'  : [DfU['HV2I1'], DfU['HV3I1']],
               'WTra' : [DfU['BusI1'] + p164, DfU['RalI1'] + p164, DfU['WCEI1'] + p164], # Add zero vehicle segment bias
               'DTra' : [DfU['BAuI1'], DfU['RAuI1'], DfU['WAuI1']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }

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
               'SOV'  : [np.where(CarShare>0, DfU['SOVI2'], LrgU)],
               'HOV'  : [DfU['HV2I2'], DfU['HV3I2']],
               'WTra' : [DfU['BusI2'] + p164, DfU['RalI2'] + p164, DfU['WCEI2'] + p164],
               'DTra' : [DfU['BAuI2'], DfU['RAuI2'], DfU['WAuI2']],
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
               'SOV'  : [np.where(CarShare>0, DfU['SOVI3'], LrgU)],
               'HOV'  : [DfU['HV2I3'], DfU['HV3I3']],
               'WTra' : [DfU['BusI3'] + p164, DfU['RalI3'] + p164, DfU['WCEI3'] + p164],
               'DTra' : [DfU['BAuI3'], DfU['RAuI3'], DfU['WAuI3']],
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
        MChM.ImpCalc(eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, util.get_matrix_numpy(eb, "HbWBlSovDist"))
        MChM.two_dim_matrix_balancing(eb, mo_list, md_list, imp_list, out_list, Dist_Iter)


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
#        ##       Split Park and Ride to Auto and Transit Legs
#       ##############################################################################
        ## General Setup
        BLBsWk = util.get_matrix_numpy(eb, "buspr-lotChceWkAMPA").flatten() #Best Lot Bus Work
        BLRlWk = util.get_matrix_numpy(eb, "railpr-lotChceWkAMPA").flatten() #Best Lot Rail Work
        BLWcWk = util.get_matrix_numpy(eb, "wcepr-lotChceWkAMPA").flatten() #Best Lot WCE Work
        DfInt = util.get_pd_ij_df(eb)

        # Bus
        Dfmerge = util.get_pd_ij_df(eb) # pandas Dataframe
        Dfmerge['BL'] = BLBsWk # best bus lot
        Dfmerge['BAuI1'] = BAuI1.flatten()
        Dfmerge['BAuI2'] = BAuI2.flatten()
        Dfmerge['BAuI3'] = BAuI3.flatten()

        DfmergedAuto = Dfmerge.groupby(['i', 'BL']).sum().reset_index()
        DfmergedTran = Dfmerge.groupby(['BL', 'j']).sum().reset_index()
        DfAuto, DfTran = self.splitpnr(DfmergedAuto, DfmergedTran, DfInt)
        SOVI1 += DfAuto['BAuI1'].reshape(NoTAZ, NoTAZ)
        SOVI2 += DfAuto['BAuI2'].reshape(NoTAZ, NoTAZ)
        SOVI3 += DfAuto['BAuI3'].reshape(NoTAZ, NoTAZ)
        Bus   += DfTran['BAuI1'].reshape(NoTAZ, NoTAZ)
        Bus   += DfTran['BAuI2'].reshape(NoTAZ, NoTAZ)
        Bus   += DfTran['BAuI3'].reshape(NoTAZ, NoTAZ)

        # Rail
        Dfmerge = util.get_pd_ij_df(eb)
        Dfmerge['BL'] = BLRlWk
        Dfmerge['RAuI1'] = RAuI1.flatten()
        Dfmerge['RAuI2'] = RAuI2.flatten()
        Dfmerge['RAuI3'] = RAuI3.flatten()

        DfmergedAuto = Dfmerge.groupby(['i', 'BL']).sum().reset_index()
        DfmergedTran = Dfmerge.groupby(['BL', 'j']).sum().reset_index()
        DfAuto, DfTran = self.splitpnr(DfmergedAuto, DfmergedTran, DfInt)
        SOVI1 += DfAuto['RAuI1'].reshape(NoTAZ, NoTAZ)
        SOVI2 += DfAuto['RAuI2'].reshape(NoTAZ, NoTAZ)
        SOVI3 += DfAuto['RAuI3'].reshape(NoTAZ, NoTAZ)
        Rail  += DfTran['RAuI1'].reshape(NoTAZ, NoTAZ)
        Rail  += DfTran['RAuI2'].reshape(NoTAZ, NoTAZ)
        Rail  += DfTran['RAuI3'].reshape(NoTAZ, NoTAZ)

        #WCE
        Dfmerge = util.get_pd_ij_df(eb)
        Dfmerge['BL'] = BLWcWk
        Dfmerge['WAuI1'] = WAuI1.flatten()
        Dfmerge['WAuI2'] = WAuI2.flatten()
        Dfmerge['WAuI3'] = WAuI3.flatten()

        DfmergedAuto = Dfmerge.groupby(['i', 'BL']).sum().reset_index()
        DfmergedTran = Dfmerge.groupby(['BL', 'j']).sum().reset_index()
        DfAuto, DfTran = self.splitpnr(DfmergedAuto, DfmergedTran, DfInt)
        SOVI1 += DfAuto['WAuI1'].reshape(NoTAZ, NoTAZ)
        SOVI2 += DfAuto['WAuI2'].reshape(NoTAZ, NoTAZ)
        SOVI3 += DfAuto['WAuI3'].reshape(NoTAZ, NoTAZ)
        WCE   += DfTran['WAuI1'].reshape(NoTAZ, NoTAZ)
        WCE   += DfTran['WAuI2'].reshape(NoTAZ, NoTAZ)
        WCE   += DfTran['WAuI3'].reshape(NoTAZ, NoTAZ)

#       ##############################################################################
#        ##       Set Demand Matrices
#       ##############################################################################
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

    def Calc_Prob(self, eb, Dict, Logsum, Th):
        util = _m.Modeller().tool("translink.emme.util")

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

        ## Initialize P-A Trip Tables by mode
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

        ## Initialize P-A Trip Tables from trip distribution
        util.initmat(eb, "mf3050", "HbWP-AI1A0", " HbW P-A Trips I1 A0", 0)
        util.initmat(eb, "mf3051", "HbWP-AI1A1", " HbW P-A Trips I1 A1", 0)
        util.initmat(eb, "mf3052", "HbWP-AI1A2", " HbW P-A Trips I1 A2", 0)
        util.initmat(eb, "mf3053", "HbWP-AI2A0", " HbW P-A Trips I1 A0", 0)
        util.initmat(eb, "mf3054", "HbWP-AI2A1", " HbW P-A Trips I1 A1", 0)
        util.initmat(eb, "mf3055", "HbWP-AI2A2", " HbW P-A Trips I1 A2", 0)
        util.initmat(eb, "mf3056", "HbWP-AI3A0", " HbW P-A Trips I1 A0", 0)
        util.initmat(eb, "mf3057", "HbWP-AI3A1", " HbW P-A Trips I1 A1", 0)
        util.initmat(eb, "mf3058", "HbWP-AI3A2", " HbW P-A Trips I1 A2", 0)