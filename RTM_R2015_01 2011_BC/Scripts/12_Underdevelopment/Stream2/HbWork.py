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
        MChM = _m.Modeller().tool("translink.emme.modechoicemethods")
        input_path = util.get_input_path(eb)
        self.matrix_batchins(eb)
        NoTAZ = len(util.get_matrix_numpy(eb, "mo51"))

#        ##############################################################################
#        ##       Define Availability thresholds
#        ##############################################################################

        AvailDict = {
                     'AutDist ' = 0.0
                     'WlkDist ' = 5.0
                     'BikDist ' = 20.0
                     'TranIVT ' = 1.0
                     'TranWat ' = 20.0
                     'TranAux ' = 30.0
                     'WCEWat '  = 30.0
                     'WCEAux '  = 40.0
                     'TranBrd ' = 4.0
                     'BRTotLow' = 10.0
                     'BRTotHig' = 120.0
                     'WCTotLow' = 30.0
                     'WCTotHig' = 130.0
                     'PRAutTim' = 0.0
                    }

        # Declare Utilities Data Frame
        DfU = {}
        # Add Coefficients
        p2   = -2.739199
        p3   = -4.513300
        p4   =  0.364863
        p5   = -5.661864
        p6   =  2.062068
        p7   = -3.709914
        p8   =  3.708285
        p9   = -3.876351
        p10  =  1.859068
        p11  = -3.047269
        p12  = -0.263245
        p13  = -0.168725
        p14  = -0.142092
        p17  = -0.162279
        p18  = -0.102166
        p19  = -0.437862
        p20  = -1.422625
        p21  = -0.395458
        p151 = -0.066325
        p152 = -0.086352
        p153 = -0.081145
        p160 =  1.884225
        p161 =  2.388802
        p162 =  1.114524
        p163 =  1.611342
        p164 =  0.593249
        p505 = -0.341555
        p506 = -0.379044
        p601 =  0.101757
        p602 =  0.053887
        p701 =  0.243799
        p850 =  1.658570
        p870 =  0.695337
        p991 = -0.043989
        p993 =  0.000409
        p995 =  1.605373
        thet =  0.622993

#        ##############################################################################
#        ##       Auto Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        MaxPark = 10.0
        VOC = util.get_matrix_numpy(eb, 'ms100')
        Occ = util.get_matrix_numpy(eb, 'ms103')
        Df['ParkCost'] = util.get_matrix_numpy(eb, 'mo61')
        Df['ParkCost'][Df['ParkCost']>MaxPark] = MaxPark
        Df['ParkCost'] = Df['ParkCost'].reshape(1, NoTAZ) + np.zeros((NoTAZ, 1))

        Df['AutoAccess'] = util.get_matrix_numpy(eb, 'mo220').reshape(NoTAZ,1) + np.zeros((1, NoTAZ))

        Df['AutoDisSOV'] = util.get_matrix_numpy(eb, 'mf5100')
        Df['AutoTimSOV'] = util.get_matrix_numpy(eb, 'mf5101')
        Df['AutoCosSOV'] = Df['AutoDisSOV']*VOC + util.get_matrix_numpy(eb, 'mf5102') + Df['ParkCost']

        Df['AutoDisHOV'] = util.get_matrix_numpy(eb, 'mf5106')
        Df['AutoTimHOV'] = util.get_matrix_numpy(eb, 'mf5107')
        Df['AutoCosHOV'] = Df['AutoDisHOV']*VOC + util.get_matrix_numpy(eb, 'mf5108') + Df['ParkCost']

        # Utilities
        # SOV
        Df['GeUtl'] = ( 0
                      + p151*Df['AutoTimSOV']
                      + p601*Df['AutoAccess'])

        Df['GeUtl']  = MChM.AutoAvail(Df['AutoDisSOV'], Df['GeUtl'], AvailDict)

        DfU['SOVI1']  = Df['GeUtl'] + p12*Df['AutoCosSOV']
        DfU['SOVI2']  = Df['GeUtl'] + p13*Df['AutoCosSOV']
        DfU['SOVI3']  = Df['GeUtl'] + p14*Df['AutoCosSOV']

        # HOV2
        Df['GeUtl'] = ( p2
                      + p151*Df['AutoTimHOV']
                      + p601*Df['AutoAccess'])

        Df['GeUtl']  = MChM.AutoAvail(Df['AutoDisHOV'], Df['GeUtl'], AvailDict)

        DfU['HV2I1']  = Df['GeUtl'] + p12*Df['AutoCosHOV']/2.0
        DfU['HV2I2']  = Df['GeUtl'] + p13*Df['AutoCosHOV']/2.0
        DfU['HV2I3']  = Df['GeUtl'] + p14*Df['AutoCosHOV']/2.0

        # HOV3
        Df['GeUtl'] = ( p3
                      + p151*Df['AutoTimHOV']
                      + p601*Df['AutoAccess'])

        Df['GeUtl']  = MChM.AutoAvail(Df['AutoDisHOV'], Df['GeUtl'], AvailDict)

        DfU['HV3I1']  = Df['GeUtl'] + p12*Df['AutoCosHOV']/Occ
        DfU['HV3I2']  = Df['GeUtl'] + p13*Df['AutoCosHOV']/Occ
        DfU['HV3I3']  = Df['GeUtl'] + p14*Df['AutoCosHOV']/Occ

#        ##############################################################################
#        ##       Walk to Transit Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        Tiny=0.000001
        Df['BusIVT'] = util.get_matrix_numpy(eb, 'mf5300')
        Df['BusWat'] = util.get_matrix_numpy(eb, 'mf5301')
        Df['BusAux'] = util.get_matrix_numpy(eb, 'mf5302')
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'mf5303')
        Df['BusFar'] = util.get_matrix_numpy(eb, 'mf5304')
        Df['BusTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux'] + Df['BusBrd']

        Df['RalIVR'] = util.get_matrix_numpy(eb, 'mf5500')
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'mf5501')
        Df['RalWat'] = util.get_matrix_numpy(eb, 'mf5502')
        Df['RalAux'] = util.get_matrix_numpy(eb, 'mf5503')
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'mf5504')
        Df['RalFar'] = util.get_matrix_numpy(eb, 'mf5505')
        Df['RalTot'] = Df['RalIVB'] + Df['RalIVR'] + Df['RalWat'] + Df['RalAux'] + Df['RalBrd']
        Df['RalIBR'] = Df['RalIVB']/(Df['RalIVB'] + Df['RalIVR'] + Tiny)
        Df['RalIRR'] = Df['RalIVR']/(Df['RalIVB'] + Df['RalIVR'] + Tiny)

        Df['WCEIVW'] = util.get_matrix_numpy(eb, 'mf5700')
        Df['WCEIVR'] = util.get_matrix_numpy(eb, 'mf5701')
        Df['WCEIVB'] = util.get_matrix_numpy(eb, 'mf5702')
        Df['WCEWat'] = util.get_matrix_numpy(eb, 'mf5703')
        Df['WCEAux'] = util.get_matrix_numpy(eb, 'mf5704')
        Df['WCEBrd'] = util.get_matrix_numpy(eb, 'mf5705')
        Df['WCEFar'] = util.get_matrix_numpy(eb, 'mf5706')
        Df['WCETot'] = Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW'] + Df['WCEWat'] + Df['WCEAux'] + Df['WCEBrd']
        Df['WCEIBR'] = Df['WCEIVB']/(Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW'] + Tiny)
        Df['WCEIRR'] = Df['WCEIVR']/(Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW'] + Tiny)
        Df['WCEIWR'] = Df['WCEIVW']/(Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW'] + Tiny)

        Df['TranAccess'] = util.get_matrix_numpy(eb, 'mo221').reshape(NoTAZ,1) + np.zeros((1, NoTAZ))
        Df['IntZnl'] = np.identity(NoTAZ)
        Df['AutoDis'] = util.get_matrix_numpy(eb, 'mf5100')
        Df['AutoDisSqd'] = Df['AutoDis']* Df['AutoDis']
        Df['LogAutoDis'] = np.log(Df['AutoDis'] + Tiny)

        # Utilities
        # Bus Utility
        Coef = [BsIVT, TrWat, TrAux, TrTrf, AuDis, AuDSq, LgAuD, TrAcc]

        Vari = [Df['BusIVT'], Df['BusWat'], Df['BusAux'], Df['BusBrd'] -1,
                Df['AutoDis'], Df['AutoDisSqd'], Df['LogAutoDis'], Df['TranAccess']]

        Df['GeUtl'] = ( p4
                      + p152*Df['BusIVT']
                      + p17*Df['BusWat']
                      + p18*Df['BusAux']
                      + p19*(Df['BusBrd'] - 1)
                      + p991*Df['AutoDis']
                      + p993*Df['AutoDisSqd']
                      + p995*Df['LogAutoDis']
                      + p602*Df['TranAccess'])

        Df['GeUtl'] = MChM.BusAvail(Df, Df['GeUtl'], AvailDict)

        DfU['BusI1'] = Df['GeUtl'] + p12*Df['BusFar']
        DfU['BusI2'] = Df['GeUtl'] + p13*Df['BusFar']
        DfU['BusI3'] = Df['GeUtl'] + p14*Df['BusFar']

        # Rail Utility
        Df['GeUtl'] = ( p4*Df['RalIBR']
                      + p6*Df['RalIRR']
                      + p152*Df['RalIVB']
                      + p153*Df['RalIVR']
                      + p17*Df['RalWat']
                      + p18*Df['RalAux']
                      + p19*(Df['RalBrd'] - 1)
                      + p991*Df['AutoDis']
                      + p993*Df['AutoDisSqd']
                      + p995*Df['LogAutoDis'])


        Df['GeUtl'] = MChM.RailAvail(Df, Df['GeUtl'],AvailDict)

        DfU['RalI1'] = Df['GeUtl'] + p12*Df['RalFar']
        DfU['RalI2'] = Df['GeUtl'] + p13*Df['RalFar']
        DfU['RalI3'] = Df['GeUtl'] + p14*Df['RalFar']

        # WCE Utility
        Df['GeUtl'] = ( p4*Df['WCEIBR']
                      + p6*Df['WCEIRR']
                      + p8*Df['WCEIWR']
                      + p152*Df['WCEIVB']
                      + p153*Df['WCEIVR']
                      + p153*Df['WCEIVW']
                      + p17*Df['WCEWat']
                      + p18*Df['WCEAux']
                      + p19*(Df['WCEBrd'] - 1)
                      + p991*Df['AutoDis']
                      + p993*Df['AutoDisSqd']
                      + p995*Df['LogAutoDis'])

        Df['GeUtl'] = MChM.WCEAvail(Df, Df['GeUtl'], AvailDict)

        DfU['WCEI1'] = Df['GeUtl'] + p12*Df['WCEFar']
        DfU['WCEI2'] = Df['GeUtl'] + p13*Df['WCEFar']
        DfU['WCEI3'] = Df['GeUtl'] + p14*Df['WCEFar']

#        ##############################################################################
#        ##       Drive to Transit Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        Df['BAuDis'] = util.get_matrix_numpy(eb, 'mf6800')
        Df['BAuTim'] = util.get_matrix_numpy(eb, 'mf6801')
        Df['BAuCos'] = Df['BAuDis']*VOC + util.get_matrix_numpy(eb, 'mf6802') + util.get_matrix_numpy(eb, 'mf6803')
        Df['BAuTrm'] = util.get_matrix_numpy(eb, 'mf6804')
        Df['BusIVT'] = util.get_matrix_numpy(eb, 'mf6900')
        Df['BusWat'] = util.get_matrix_numpy(eb, 'mf6901')
        Df['BusAux'] = util.get_matrix_numpy(eb, 'mf6902')
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'mf6903')
        Df['BusFar'] = util.get_matrix_numpy(eb, 'mf6904')
        Df['BAuTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux'] + Df['BusBrd'] + Df['BAuTim']
        Df['BAuIBR'] = Df['BusIVT']/(Df['BusIVT'] + Df['BAuTim'] + Tiny)

        Df['RAuDis'] = util.get_matrix_numpy(eb, 'mf6810')
        Df['RAuTim'] = util.get_matrix_numpy(eb, 'mf6811')
        Df['RAuCos'] = Df['RAuDis']*VOC + util.get_matrix_numpy(eb, 'mf6812') + util.get_matrix_numpy(eb, 'mf6813')
        Df['RAuTrm'] = util.get_matrix_numpy(eb, 'mf6814')
        Df['RalIVR'] = util.get_matrix_numpy(eb, 'mf6910')
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'mf6911')
        Df['RalWat'] = util.get_matrix_numpy(eb, 'mf6912')
        Df['RalAux'] = util.get_matrix_numpy(eb, 'mf6913')
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'mf6914')
        Df['RalFar'] = util.get_matrix_numpy(eb, 'mf6915')
        Df['RAuTot'] = Df['RalIVB'] + Df['RalIVR'] + Df['RalWat'] + Df['RalAux'] + Df['RalBrd'] +  Df['RAuTim']
        Df['RAuIBR'] = Df['RalIVB']/(Df['RalIVB'] + Df['RalIVR'] + Df['RAuTim'] + Tiny)
        Df['RAuIRR'] = Df['RalIVR']/(Df['RalIVB'] + Df['RalIVR'] + Df['RAuTim'] + Tiny)

        Df['WAuDis'] = util.get_matrix_numpy(eb, 'mf6820')
        Df['WAuTim'] = util.get_matrix_numpy(eb, 'mf6821')
        Df['WAuCos'] = Df['WAuDis']*VOC + util.get_matrix_numpy(eb, 'mf6822') + util.get_matrix_numpy(eb, 'mf6823')
        Df['WAuTrm'] = util.get_matrix_numpy(eb, 'mf6824')
        Df['WCEIVW'] = util.get_matrix_numpy(eb, 'mf6920')
        Df['WCEIVR'] = util.get_matrix_numpy(eb, 'mf6921')
        Df['WCEIVB'] = util.get_matrix_numpy(eb, 'mf6922')
        Df['WCEWat'] = util.get_matrix_numpy(eb, 'mf6923')
        Df['WCEAux'] = util.get_matrix_numpy(eb, 'mf6924')
        Df['WCEBrd'] = util.get_matrix_numpy(eb, 'mf6925')
        Df['WCEFar'] = util.get_matrix_numpy(eb, 'mf6926')
        Df['WAuTot'] = Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW'] + Df['WCEWat'] + Df['WCEAux'] + Df['WCEBrd'] + Df['WAuTim']
        Df['WAuIBR'] = Df['WCEIVB']/(Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW']+ Df['WAuTim'] + Tiny)
        Df['WAuIRR'] = Df['WCEIVR']/(Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW']+ Df['WAuTim'] + Tiny)
        Df['WAuIWR'] = Df['WCEIVW']/(Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW']+ Df['WAuTim'] + Tiny)

        Df['IntZnl'] = np.identity(NoTAZ)
        Df['AutoDis'] = util.get_matrix_numpy(eb, 'mf5100')
        Df['AutoDisSqd'] = Df['AutoDis']* Df['AutoDis']
        Df['LogAutoDis'] = np.log(Df['AutoDis'] + Tiny)

        # Utilities
        # Bus Utility
        Df['GeUtl'] = ( p5
                      + p4*Df['BAuIBR']
                      + p151*Df['BAuTim']
                      + p152*Df['BusIVT']
                      + p17*Df['BusWat']
                      + p18*(Df['BusAux'] + Df['BAuTrm'])
                      + p19*(Df['BusBrd'] - 1)
                      + p991*Df['AutoDis']
                      + p993*Df['AutoDisSqd']
                      + p995*Df['LogAutoDis'])

        Df['GeUtl'] = MChM.BAuAvail(Df, Df['GeUtl'], AvailDict)

        DfU['BAuI1'] = Df['GeUtl'] + p12*(Df['BusFar'] + Df['BAuCos'])
        DfU['BAuI2'] = Df['GeUtl'] + p13*(Df['BusFar'] + Df['BAuCos'])
        DfU['BAuI3'] = Df['GeUtl'] + p14*(Df['BusFar'] + Df['BAuCos'])

        # Rail Utility
        Df['GeUtl'] = ( p7
                      + p4*Df['RAuIBR']
                      + p6*Df['RAuIRR']
                      + p151*Df['RAuTim']
                      + p152*Df['RalIVB']
                      + p153*Df['RalIVR']
                      + p17*Df['RalWat']
                      + p18*(Df['RalAux'] + Df['RAuTrm'])
                      + p19*(Df['RalBrd'] - 1)
                      + p991*Df['AutoDis']
                      + p993*Df['AutoDisSqd']
                      + p995*Df['LogAutoDis'])

        Df['GeUtl'] = MChM.RAuAvail(Df, Df['GeUtl'], AvailDict)

        DfU['RAuI1'] = Df['GeUtl'] + p12*(Df['RalFar'] + Df['RAuCos'])
        DfU['RAuI2'] = Df['GeUtl'] + p13*(Df['RalFar'] + Df['RAuCos'])
        DfU['RAuI3'] = Df['GeUtl'] + p14*(Df['RalFar'] + Df['RAuCos'])

        # WCE Utility
        DfU['GeUtl'] = ( p9
                       + p4*Df['WAuIBR']
                       + p6*Df['WAuIRR']
                       + p8*Df['WAuIWR']
                       + p151*Df['WAuTim']
                       + p152*Df['WCEIVB']
                       + p153*Df['WCEIVR']
                       + p153*Df['WCEWat']
                       + p17*Df['RalWat']
                       + p18*(Df['WCEAux'] + Df['WAuTrm'])
                       + p19*(Df['WCEBrd'] - 1)
                       + p991*Df['AutoDis']
                       + p993*Df['AutoDisSqd']
                       + p995*Df['LogAutoDis'])

        Df['GeUtl'] = MChM.WAuAvail(Df, DfU['GeUtl'],AvailDict)

        DfU['WAuI1'] = Df['GeUtl'] + p12*(Df['WCEFar'] + Df['WAuCos'])
        DfU['WAuI2'] = Df['GeUtl'] + p13*(Df['WCEFar'] + Df['WAuCos'])
        DfU['WAuI3'] = Df['GeUtl'] + p14*(Df['WCEFar'] + Df['WAuCos'])

#        ##############################################################################
#        ##       Active Modes
#        ##############################################################################

        Df = {}
        Df['AutoDis'] = util.get_matrix_numpy(eb, 'mf5100')
        Df['IntrCBD'] = util.get_matrix_numpy(eb, 'mo100')
        Df['IntrCBD'] = Df['IntrCBD'].reshape(NoTAZ, 1)*Df['IntrCBD'].reshape(1, NoTAZ)

        Df['PopEmpDen'] = util.get_matrix_numpy(eb, 'mo200') + util.get_matrix_numpy(eb, 'mo201')
        Df['PopEmpDen'] = Df['PopEmpDen'].reshape(NoTAZ, 1) + Df['PopEmpDen'].reshape(1, NoTAZ)
        Df['PopEmpDen'][Df['PopEmpDen']<1.0] = 1.0
        Df['PopEmpDen'] = np.log(Df['PopEmpDen'])

        Df['PopSen'] = util.get_matrix_numpy(eb, 'mo17') + util.get_matrix_numpy(eb, 'mo18')
        Df['PopTot'] = util.get_matrix_numpy(eb, 'mo20')
        Df['PopSPr'] = np.log(Df['PopSen']/(Df['PopTot'] + Tiny) + 0.0001)
        Df['PopSPr'] = Df['PopSPr'].reshape(NoTAZ, 1) + np.zeros(1, NoTAZ)

        Df['BikScr'] = util.get_matrix_numpy(eb, 'mf90')

        # Walk Utility
        DfU['Walk'] = ( p10
                      + p20*Df['AutoDis']
                      + p850*Df['IntrCBD']
                      + p701*Df['PopDen']
                      + p505*Df['PopSPr'])

        DfU['Walk'] = MChM.WalkAvail(Df['AutoDis'], DfU['Walk'], AvailDict)

        # Bike Utility
        DfU['Bike'] = ( p11
                      + p21*Df['AutoDis']
                      + p870*Df['BikScr']
                      + p506*Df['PopSPr'])

        DfU['Bike'] = MChM.BikeAvail(Df['AutoDis'], DfU['Bike'], AvailDict)

        del Df

#        ##############################################################################
#        ##       Calculate Probabilities
#        ##############################################################################

        ############
        # Low Income
        ############

        ## Add SOV Availability Term

        CarShare = util.get_matrix_numpy(eb, 'mo71').reshape(NoTAZ,1) + np.zeros((1, NoTAZ))
        LrgU     = -99999.0
        ## Low Income Zero Autos
        Dict = {
               'SOV'  : [np.where(CarShare>0, DfU['SOVI1'], LrgU)],
               'HOV'  : [DfU['HV2I1'], DfU['HV3I1']],
               'WTra' : [DfU['BusI1'] + p164, DfU['RalI1'] + p164, DfU['WCEI1'] + p164],
               'DTra' : [DfU['BAuI1'], DfU['RAuI1'], DfU['WAuI1']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }

        I1A0_Dict = self.Calc_Prob(eb, Dict, "mf9000", thet)

        ## Low Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI1'] + p160],
               'HOV'  : [DfU['HV2I1'] + p162, DfU['HV3I1'] + p162],
               'WTra' : [DfU['BusI1'], DfU['RalI1'], DfU['WCEI1']],
               'DTra' : [DfU['BAuI1'], DfU['RAuI1'], DfU['WAuI1']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I1A1_Dict = self.Calc_Prob(eb, Dict, "mf9001", thet)

        ## Low Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI1'] + p161],
               'HOV'  : [DfU['HV2I1'] + p163, DfU['HV3I1'] + p163],
               'WTra' : [DfU['BusI1'], DfU['RalI1'], DfU['WCEI1']],
               'DTra' : [DfU['BAuI1'], DfU['RAuI1'], DfU['WAuI1']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I1A2_Dict = self.Calc_Prob(eb, Dict, "mf9002", thet)

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
        I2A0_Dict = self.Calc_Prob(eb, Dict, "mf9003", thet)

        ## Med Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI2'] + p160],
               'HOV'  : [DfU['HV2I2'] + p162, DfU['HV3I2'] + p162],
               'WTra' : [DfU['BusI2'], DfU['RalI2'], DfU['WCEI2']],
               'DTra' : [DfU['BAuI2'], DfU['RAuI2'], DfU['WAuI2']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I2A1_Dict = self.Calc_Prob(eb, Dict, "mf9004", thet)

        ## Med Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI2'] + p161],
               'HOV'  : [DfU['HV2I2'] + p163, DfU['HV3I2'] + p163],
               'WTra' : [DfU['BusI2'], DfU['RalI2'], DfU['WCEI2']],
               'DTra' : [DfU['BAuI2'], DfU['RAuI2'], DfU['WAuI2']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I2A2_Dict = self.Calc_Prob(eb, Dict, "mf9005", thet)

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
        I3A0_Dict = self.Calc_Prob(eb, Dict, "mf9006", thet)

        ## High Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI3'] + p160],
               'HOV'  : [DfU['HV2I3'] + p162, DfU['HV3I3'] + p162],
               'WTra' : [DfU['BusI3'], DfU['RalI3'], DfU['WCEI3']],
               'DTra' : [DfU['BAuI3'], DfU['RAuI3'], DfU['WAuI3']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I3A1_Dict = self.Calc_Prob(eb, Dict, "mf9007", thet)

        ## High Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI3'] + p161],
               'HOV'  : [DfU['HV2I3'] + p163, DfU['HV3I3'] + p163],
               'WTra' : [DfU['BusI3'], DfU['RalI3'], DfU['WCEI3']],
               'DTra' : [DfU['BAuI3'], DfU['RAuI3'], DfU['WAuI3']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I3A2_Dict = self.Calc_Prob(eb, Dict, "mf9008", thet)

        del DfU, Dict

       ##############################################################################
        ##       Trip Distribution
       ##############################################################################

        Logsum =  [
                  "mf9000", "mf9001", "mf9002",
                  "mf9003", "mf9004", "mf9005",
                  "mf9006", "mf9007", "mf9008"
                   ]

        imp_list = [
                  "mf9100", "mf9101", "mf9102",
                  "mf9103", "mf9104", "mf9105",
                  "mf9106", "mf9107", "mf9108"
                   ]

        mo_list =  [
                    "mo2000", "mo2003", "mo2006",
                    "mo2001", "mo2004", "mo2007",
                    "mo2002", "mo2005", "mo2008"
                   ]

        md_list =  ["md2000"]

        out_list = [
                    "mf3050", "mf3051", "mf3052",
                    "mf3053", "mf3054", "mf3055",
                    "mf3056", "mf3057", "mf3058"
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

        MChM.ImpCalc(eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, "mf5100")
        MChM.two_dim_matrix_balancing(eb, mo_list, md_list, imp_list, out_list, 60)


#       ##############################################################################
#        ##       Calculate Demand
#       ##############################################################################

        I1A0_Dict = self.Calc_Demand(I1A0_Dict, util.get_matrix_numpy(eb,"mf9510"))
        I1A1_Dict = self.Calc_Demand(I1A1_Dict, util.get_matrix_numpy(eb,"mf9511"))
        I1A2_Dict = self.Calc_Demand(I1A2_Dict, util.get_matrix_numpy(eb,"mf9512"))
        I2A0_Dict = self.Calc_Demand(I2A0_Dict, util.get_matrix_numpy(eb,"mf9513"))
        I2A1_Dict = self.Calc_Demand(I2A1_Dict, util.get_matrix_numpy(eb,"mf9514"))
        I2A2_Dict = self.Calc_Demand(I2A2_Dict, util.get_matrix_numpy(eb,"mf9515"))
        I3A0_Dict = self.Calc_Demand(I3A0_Dict, util.get_matrix_numpy(eb,"mf9516"))
        I3A1_Dict = self.Calc_Demand(I3A1_Dict, util.get_matrix_numpy(eb,"mf9517"))
        I3A2_Dict = self.Calc_Demand(I3A2_Dict, util.get_matrix_numpy(eb,"mf9518"))

        SOVI1 = I1A0_Dict['SOV'][0] + I1A1_Dict['SOV'][0] + I1A2_Dict['SOV'][0]
        SOVI2 = I2A0_Dict['SOV'][0] + I2A1_Dict['SOV'][0] + I2A2_Dict['SOV'][0]
        SOVI3 = I3A0_Dict['SOV'][0] + I3A1_Dict['SOV'][0] + I3A2_Dict['SOV'][0]

        HV2I1 = I1A0_Dict['HOV'][0] + I1A1_Dict['HOV'][0] + I1A2_Dict['HOV'][0]
        HV2I2 = I2A0_Dict['HOV'][0] + I2A1_Dict['HOV'][0] + I2A2_Dict['HOV'][0]
        HV2I3 = I3A0_Dict['HOV'][0] + I3A1_Dict['HOV'][0] + I3A2_Dict['HOV'][0]
        HV3I1 = I1A0_Dict['HOV'][1] + I1A1_Dict['HOV'][1] + I1A2_Dict['HOV'][1]
        HV3I2 = I2A0_Dict['HOV'][1] + I2A1_Dict['HOV'][1] + I2A2_Dict['HOV'][1]
        HV3I3 = I3A0_Dict['HOV'][1] + I3A1_Dict['HOV'][1] + I3A2_Dict['HOV'][1]

        Bus  =  I1A0_Dict['WTra'][0] + I1A1_Dict['WTra'][0] + I1A2_Dict['WTra'][0]
        Bus +=  I2A0_Dict['WTra'][0] + I2A1_Dict['WTra'][0] + I2A2_Dict['WTra'][0]
        Bus +=  I3A0_Dict['WTra'][0] + I3A1_Dict['WTra'][0] + I3A2_Dict['WTra'][0]
        Rail =  I1A0_Dict['WTra'][1] + I1A1_Dict['WTra'][1] + I1A2_Dict['WTra'][1]
        Rail += I2A0_Dict['WTra'][1] + I2A1_Dict['WTra'][1] + I2A2_Dict['WTra'][1]
        Rail += I3A0_Dict['WTra'][1] + I3A1_Dict['WTra'][1] + I3A2_Dict['WTra'][1]
        WCE =   I1A0_Dict['WTra'][2] + I1A1_Dict['WTra'][2] + I1A2_Dict['WTra'][2]
        WCE +=  I2A0_Dict['WTra'][2] + I2A1_Dict['WTra'][2] + I2A2_Dict['WTra'][2]
        WCE +=  I3A0_Dict['WTra'][2] + I3A1_Dict['WTra'][2] + I3A2_Dict['WTra'][2]

        Walk =  I1A0_Dict['Acti'][0] + I1A1_Dict['Acti'][0] + I1A2_Dict['Acti'][0]
        Walk += I2A0_Dict['Acti'][0] + I2A1_Dict['Acti'][0] + I2A2_Dict['Acti'][0]
        Walk += I3A0_Dict['Acti'][0] + I3A1_Dict['Acti'][0] + I3A2_Dict['Acti'][0]
        Bike =  I1A0_Dict['Acti'][1] + I1A1_Dict['Acti'][1] + I1A2_Dict['Acti'][1]
        Bike += I2A0_Dict['Acti'][1] + I2A1_Dict['Acti'][1] + I2A2_Dict['Acti'][1]
        Bike += I3A0_Dict['Acti'][1] + I3A1_Dict['Acti'][1] + I3A2_Dict['Acti'][1]

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
        Or = util.get_matrix_numpy(eb, "mf1").flatten()  #Store Vector by origin
        De = util.get_matrix_numpy(eb, "mf2").flatten() #Store Vector by destination
        BLBsWk = util.get_matrix_numpy(eb, "mf6000").flatten() #Best Lot Bus Work
        BLRlWk = util.get_matrix_numpy(eb, "mf6001").flatten() #Best Lot Rail Work
        BLWcWk = util.get_matrix_numpy(eb, "mf6002").flatten() #Best Lot WCE Work
        DfInt = util.get_pd_ij_df(eb)

        # Bus
        Dfmerge = util.get_pd_ij_df(eb)
        Dfmerge['BL'] = BLBsWk
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

        DfmergedAuto = Dfmerge.groupby(['Or', 'BL']).sum().reset_index()
        DfmergedTran = Dfmerge.groupby(['BL', 'De']).sum().reset_index()
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

        DfmergedAuto = Dfmerge.groupby(['Or', 'BL']).sum().reset_index()
        DfmergedTran = Dfmerge.groupby(['BL', 'De']).sum().reset_index()
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
        util.set_matrix_numpy(eb, "mf3000", SOVI1)
        util.set_matrix_numpy(eb, "mf3001", SOVI2)
        util.set_matrix_numpy(eb, "mf3002", SOVI3)
        util.set_matrix_numpy(eb, "mf3005", HV2I1)
        util.set_matrix_numpy(eb, "mf3006", HV2I2)
        util.set_matrix_numpy(eb, "mf3007", HV2I3)
        util.set_matrix_numpy(eb, "mf3010", HV3I1)
        util.set_matrix_numpy(eb, "mf3011", HV3I2)
        util.set_matrix_numpy(eb, "mf3012", HV3I3)
        util.set_matrix_numpy(eb, "mf3015", Bus)
        util.set_matrix_numpy(eb, "mf3020", Rail)
        util.set_matrix_numpy(eb, "mf3025", WCE)
        util.set_matrix_numpy(eb, "mf3030", Walk)
        util.set_matrix_numpy(eb, "mf3035", Bike)

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