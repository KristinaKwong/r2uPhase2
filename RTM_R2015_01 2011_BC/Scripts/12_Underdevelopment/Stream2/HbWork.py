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
        # Declare Utilities Data Frame
        DfU = {}
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
        Df['ParkCost'] = Df['ParkCost'].reshape(1, 1741) + np.zeros((1741, 1))

        Df['AutoAccess'] = util.get_matrix_numpy(eb, 'mo220').reshape(1741,1) + np.zeros((1, 1741))

        Df['AutoDisSOV'] = util.get_matrix_numpy(eb, 'mf5100')
        Df['AutoTimSOV'] = util.get_matrix_numpy(eb, 'mf5101')

        Df['AutoCosSOV'] = Df['AutoDisSOV']*VOC + util.get_matrix_numpy(eb, 'mf5102') + Df['ParkCost']

        Df['AutoDisHOV'] = util.get_matrix_numpy(eb, 'mf5106')
        Df['AutoTimHOV'] = util.get_matrix_numpy(eb, 'mf5107')
        Df['AutoCosHOV'] = Df['AutoDisHOV']*VOC + util.get_matrix_numpy(eb, 'mf5108') + Df['ParkCost']

        # Coefficients
        AscH2 = -2.660152
        AscH3 = -4.427692
        CstI1 = -0.251320
        CstI2 = -0.161345
        CstI3 = -0.139374
        AutTi = -0.068191
        SOVA1 =  1.800794
        SOVA2 =  2.328981
        HOVA1 =  1.041047
        HOVA2 =  1.559570
        AuAcc =  0.092440

        # Utilities
        # SOV
        ## TODO Parking Cost
        ## Auto Accessibility
        Coef = [AutTi, AuAcc]
        Vari = [Df['AutoTimSOV'], Df['AutoAccess']]
        Df['GeUtl']  = util.sumproduct(Coef, Vari)
        Df['GeUtl']  = MChM.AutoAvail(Df['AutoDisSOV'], Df['GeUtl'])

        DfU['SOVI1']  = Df['GeUtl'] + CstI1*Df['AutoCosSOV']
        DfU['SOVI2']  = Df['GeUtl'] + CstI2*Df['AutoCosSOV']
        DfU['SOVI3']  = Df['GeUtl'] + CstI3*Df['AutoCosSOV']

        # HOV2
        ## TODO Parking Cost
        ## Auto Accessibility
        Coef = [AutTi, AuAcc]
        Vari = [Df['AutoTimHOV'], Df['AutoAccess']]
        Df['GeUtl']  = util.sumproduct(Coef, Vari) + AscH2
        Df['GeUtl']  = MChM.AutoAvail(Df['AutoDisHOV'], Df['GeUtl'])

        DfU['HV2I1']  = Df['GeUtl'] + CstI1*Df['AutoCosHOV']/2.0
        DfU['HV2I2']  = Df['GeUtl'] + CstI2*Df['AutoCosHOV']/2.0
        DfU['HV2I3']  = Df['GeUtl'] + CstI3*Df['AutoCosHOV']/2.0

        # HOV3
        ## TODO Parking Cost
        ## Auto Accessibility
        Coef = [AutTi, AuAcc]
        Vari = [Df['AutoTimHOV'], Df['AutoAccess']]
        Df['GeUtl']  = util.sumproduct(Coef, Vari) + AscH3
        Df['GeUtl']  = MChM.AutoAvail(Df['AutoDisHOV'], Df['GeUtl'])

        DfU['HV3I1']  = Df['GeUtl'] + CstI1*Df['AutoCosHOV']/Occ
        DfU['HV3I2']  = Df['GeUtl'] + CstI2*Df['AutoCosHOV']/Occ
        DfU['HV3I3']  = Df['GeUtl'] + CstI3*Df['AutoCosHOV']/Occ

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

        Df['TranAccess'] = util.get_matrix_numpy(eb, 'mo221').reshape(1741,1) + np.zeros((1, 1741))
        Df['IntZnl'] = util.get_matrix_numpy(eb, 'mf970')


        # Coefficients
        AscBs =  0.404758
        AscRl =  1.503990
        AscWc =  2.505564
        CstI1 = -0.345117
        CstI2 = -0.225996
        CstI3 = -0.190001
        BsIVT = -0.067919
        RTIVT = -0.059250
        TrWat = -0.080276
        TrAux = -0.086025
        TrTrf = -0.844939
        TraA0 =  0.709275
        TrAcc =  0.052047

        # Utilities
        # Bus Utility
        ## TODO Transit Accessibility

        Coef = [BsIVT, TrWat, TrAux, TrTrf, TrAcc]
        Vari = [Df['BusIVT'], Df['BusWat'], Df['BusAux'],
                Df['BusBrd'] -1, Df['TranAccess']]
        Df['GeUtl'] = util.sumproduct(Coef, Vari) + AscBs
        Df['GeUtl'] = MChM.BusAvail(Df, Df['GeUtl'])

        DfU['BusI1'] = Df['GeUtl'] + CstI1*Df['BusFar']
        DfU['BusI2'] = Df['GeUtl'] + CstI2*Df['BusFar']
        DfU['BusI3'] = Df['GeUtl'] + CstI3*Df['BusFar']

        # Rail Utility
        ## TODO Transit Accessibility
        Coef = [AscBs, AscRl, BsIVT, RTIVT, TrWat, TrAux, TrTrf, TrAcc]
        Vari = [Df['RalIBR'],Df['RalIRR'], Df['RalIVB'], Df['RalIVR'],
                Df['RalWat'],Df['RalAux'], Df['RalBrd'] -1, Df['TranAccess']]

        Df['GeUtl'] = util.sumproduct(Coef, Vari)
        Df['GeUtl'] = MChM.RailAvail(Df, Df['GeUtl'])

        DfU['RalI1'] = Df['GeUtl'] + CstI1*Df['RalFar']
        DfU['RalI2'] = Df['GeUtl'] + CstI2*Df['RalFar']
        DfU['RalI3'] = Df['GeUtl'] + CstI3*Df['RalFar']

        # WCE Utility
        ## TODO Transit Accessibility
        Coef = [AscBs, AscRl, AscWc, BsIVT, RTIVT, RTIVT, TrWat, TrAux, TrTrf, TrAcc]
        Vari = [Df['WCEIBR'], Df['WCEIRR'], Df['WCEIWR'], Df['WCEIVB'],
                Df['WCEIVR'], Df['WCEIVW'],Df['WCEWat'], Df['WCEAux'], Df['WCEBrd'] -1, Df['TranAccess']]
        Df['GeUtl'] = util.sumproduct(Coef, Vari) + AscWc
        Df['GeUtl'] = MChM.WCEAvail(Df, Df['GeUtl'])

        DfU['WCEI1'] = Df['GeUtl'] + CstI1*Df['WCEFar']
        DfU['WCEI2'] = Df['GeUtl'] + CstI2*Df['WCEFar']
        DfU['WCEI3'] = Df['GeUtl'] + CstI3*Df['WCEFar']

#        ##############################################################################
#        ##       Drive to Transit Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        Df['BAuDis'] = util.get_matrix_numpy(eb, 'mf6800')
        Df['BAuTim'] = util.get_matrix_numpy(eb, 'mf6801')
        Df['BAuCos'] = Df['BAuDis']*VOC + util.get_matrix_numpy(eb, 'mf6802')
        Df['BusIVT'] = util.get_matrix_numpy(eb, 'mf6900')
        Df['BusWat'] = util.get_matrix_numpy(eb, 'mf6901')
        Df['BusAux'] = util.get_matrix_numpy(eb, 'mf6902')
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'mf6903')
        Df['BusFar'] = util.get_matrix_numpy(eb, 'mf6904')
        Df['BAuTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux'] + Df['BusBrd'] + Df['BAuTim']
        Df['BAuIBR'] = Df['BusIVT']/(Df['BusIVT'] + Df['BAuTim'] + Tiny)

        Df['RAuDis'] = util.get_matrix_numpy(eb, 'mf6810')
        Df['RAuTim'] = util.get_matrix_numpy(eb, 'mf6811')
        Df['RAuCos'] = Df['RAuDis']*VOC + util.get_matrix_numpy(eb, 'mf6812')
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
        Df['WAuCos'] = Df['WAuDis']*VOC + util.get_matrix_numpy(eb, 'mf6822')
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

        Df['IntZnl'] = util.get_matrix_numpy(eb, 'mf970')

        # Coefficients
        AscBAu =  2.478336
        AscRAu =  3.869495
        AscWAu =  3.364910
        CstI1 = -0.345117
        CstI2 = -0.225996
        CstI3 = -0.190001
        BsIVT = -0.067919
        RTIVT = -0.059250
        TrWat = -0.080276
        TrAux = -0.086025
        TrTrf = -0.844939
        AutTi = -0.110655

        # Utilities
        # Bus Utility
        Coef = [AscBs, AutTi, BsIVT, TrWat, TrAux, TrTrf]
        Vari = [Df['BAuIBR'], Df['BAuTim'], Df['BusIVT'], Df['BusWat'],
                Df['BusAux'], (Df['BusBrd'] -1)]

        DfU['GeUtl'] = util.sumproduct(Coef, Vari) + AscBAu
        DfU['GeUtl'] = MChM.BAuAvail(Df, DfU['GeUtl'])

        DfU['BAuI1'] = DfU['GeUtl'] + CstI1*(Df['BusFar'] + Df['BAuCos'])
        DfU['BAuI2'] = DfU['GeUtl'] + CstI2*(Df['BusFar'] + Df['BAuCos'])
        DfU['BAuI3'] = DfU['GeUtl'] + CstI3*(Df['BusFar'] + Df['BAuCos'])

        # Rail Utility
        Coef = [AscBs, AscRl, AutTi, BsIVT, RTIVT, TrWat, TrAux, TrTrf]
        Vari = [Df['RAuIBR'], Df['RAuIRR'], Df['RAuTim'], Df['RalIVB'],
                Df['RalIVR'], Df['RalWat'], Df['RalAux'], Df['RalBrd'] -1]
        DfU['GeUtl'] = util.sumproduct(Coef, Vari) + AscRAu
        DfU['GeUtl'] = MChM.RAuAvail(Df, DfU['GeUtl'])
        DfU['RAuI1'] = DfU['GeUtl'] + CstI1*(Df['RalFar'] + Df['RAuCos'])
        DfU['RAuI2'] = DfU['GeUtl'] + CstI2*(Df['RalFar'] + Df['RAuCos'])
        DfU['RAuI3'] = DfU['GeUtl'] + CstI3*(Df['RalFar'] + Df['RAuCos'])


        # WCE Utility
        Coef = [AscBs, AscRl, AscWc, AutTi, BsIVT, RTIVT, RTIVT, TrWat, TrAux, TrTrf]
        Vari = [Df['WAuIBR'], Df['WAuIRR'], Df['WAuIWR'], Df['WAuTim'], Df['WCEIVB'],
                Df['WCEIVR'], Df['WCEIVW'],Df['WCEWat'], Df['WCEAux'], Df['WCEBrd'] -1]
        DfU['GeUtl'] = util.sumproduct(Coef, Vari) + AscWAu
        DfU['GeUtl'] = MChM.WAuAvail(Df, DfU['GeUtl'])
        DfU['WAuI1'] = DfU['GeUtl'] + CstI1*(Df['WCEFar'] + Df['WAuCos'])
        DfU['WAuI2'] = DfU['GeUtl'] + CstI2*(Df['WCEFar'] + Df['WAuCos'])
        DfU['WAuI3'] = DfU['GeUtl'] + CstI3*(Df['WCEFar'] + Df['WAuCos'])

#        ##############################################################################
#        ##       Active Modes
#        ##############################################################################
        Df = {}
        Df['AutoDis'] = util.get_matrix_numpy(eb, 'mf5100')
        # Coefficients
        AscWk =  8.135155
        AscBk =  3.142009
        DisWk = -1.720279
        DisBk = -0.556467

        # Walk Utility
        ## TODO Intra-CBD
        ## Population Density
        ## Log Senior Proportion
        Coef = [DisWk]
        Vari = [Df['AutoDis']]
        DfU['Walk'] = util.sumproduct(Coef, Vari) + AscWk
        DfU['Walk']  = MChM.WalkAvail(Df['AutoDis'], DfU['Walk'])

        # Bike Utility
        ## TODO Bike Score
        ## TODO Intra-CBD
        ## Log Senior Proportion
        Coef = [DisBk]
        Vari = [Df['AutoDis']]
        DfU['Bike'] = util.sumproduct(Coef, Vari) + AscBk
        DfU['Bike']  = MChM.BikeAvail(Df['AutoDis'], DfU['Walk'])

        del Df

#        ##############################################################################
#        ##       Calculate Probabilities
#        ##############################################################################
        ## Add SOV Availability Term
        
        CarShare = util.get_matrix_numpy(eb, 'mo71').reshape(1741,1) + np.zeros((1, 1741))
        LrgU     = -99999.0
        ## Low Income Zero Autos
        Dict = {
               'SOV'  : [np.where(CarShare>0, DfU['SOVI1'], LrgU)],
               'HOV'  : [DfU['HV2I1'], DfU['HV3I1']],
               'WTra' : [DfU['BusI1'] + TraA0, DfU['RalI1'] + TraA0, DfU['WCEI1'] + TraA0],
               'DTra' : [DfU['BAuI1'], DfU['RAuI1'], DfU['WAuI1']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }

        I1A0_Dict = self.Calc_Prob(eb, Dict, "mf9000")

        ## Low Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI1'] + SOVA1],
               'HOV'  : [DfU['HV2I1'] + HOVA1, DfU['HV3I1'] + HOVA1],
               'WTra' : [DfU['BusI1'], DfU['RalI1'], DfU['WCEI1']],
               'DTra' : [DfU['BAuI1'], DfU['RAuI1'], DfU['WAuI1']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I1A1_Dict = self.Calc_Prob(eb, Dict, "mf9001")

        ## Low Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI1'] + SOVA2],
               'HOV'  : [DfU['HV2I1'] + HOVA2, DfU['HV3I1'] + HOVA2],
               'WTra' : [DfU['BusI1'], DfU['RalI1'], DfU['WCEI1']],
               'DTra' : [DfU['BAuI1'], DfU['RAuI1'], DfU['WAuI1']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I1A2_Dict = self.Calc_Prob(eb, Dict, "mf9002")

        ## Med Income Zero Autos
        Dict = {
               'SOV'  : [np.where(CarShare>0, DfU['SOVI2'], LrgU)],
               'HOV'  : [DfU['HV2I2'], DfU['HV3I2']],
               'WTra' : [DfU['BusI2'] + TraA0, DfU['RalI2'] + TraA0, DfU['WCEI2'] + TraA0],
               'DTra' : [DfU['BAuI2'], DfU['RAuI2'], DfU['WAuI2']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I2A0_Dict = self.Calc_Prob(eb, Dict, "mf9003")

        ## Med Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI2'] + SOVA1],
               'HOV'  : [DfU['HV2I2'] + HOVA1, DfU['HV3I2'] + HOVA1],
               'WTra' : [DfU['BusI2'], DfU['RalI2'], DfU['WCEI2']],
               'DTra' : [DfU['BAuI2'], DfU['RAuI2'], DfU['WAuI2']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I2A1_Dict = self.Calc_Prob(eb, Dict, "mf9004")

        ## Med Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI2'] + SOVA2],
               'HOV'  : [DfU['HV2I2'] + HOVA2, DfU['HV3I2'] + HOVA2],
               'WTra' : [DfU['BusI2'], DfU['RalI2'], DfU['WCEI2']],
               'DTra' : [DfU['BAuI2'], DfU['RAuI2'], DfU['WAuI2']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I2A2_Dict = self.Calc_Prob(eb, Dict, "mf9005")

        ## High Income Zero Autos
        Dict = {
               'SOV'  : [np.where(CarShare>0, DfU['SOVI3'], LrgU)],
               'HOV'  : [DfU['HV2I3'], DfU['HV3I3']],
               'WTra' : [DfU['BusI3'] + TraA0, DfU['RalI3'] + TraA0, DfU['WCEI3'] + TraA0],
               'DTra' : [DfU['BAuI3'], DfU['RAuI3'], DfU['WAuI3']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I3A0_Dict = self.Calc_Prob(eb, Dict, "mf9006")

        ## High Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI3'] + SOVA1],
               'HOV'  : [DfU['HV2I3'] + HOVA1, DfU['HV3I3'] + HOVA1],
               'WTra' : [DfU['BusI3'], DfU['RalI3'], DfU['WCEI3']],
               'DTra' : [DfU['BAuI3'], DfU['RAuI3'], DfU['WAuI3']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I3A1_Dict = self.Calc_Prob(eb, Dict, "mf9007")

        ## High Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI3'] + SOVA2],
               'HOV'  : [DfU['HV2I3'] + HOVA2, DfU['HV3I3'] + HOVA2],
               'WTra' : [DfU['BusI3'], DfU['RalI3'], DfU['WCEI3']],
               'DTra' : [DfU['BAuI3'], DfU['RAuI3'], DfU['WAuI3']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I3A2_Dict = self.Calc_Prob(eb, Dict, "mf9008")

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
                  "mf9500", "mf9501", "mf9502",
                  "mf9503", "mf9504", "mf9505",
                  "mf9506", "mf9507", "mf9508"
                   ]

        mo_list =  [
                    "mo161", "mo164", "mo167+mo170",
                    "mo162", "mo165", "mo168+mo171",
                    "mo163", "mo166", "mo169+mo172"
                   ]

        md_list =  ["md200"]

        out_list = [
                    "mf9510", "mf9511", "mf9512",
                    "mf9513", "mf9514", "mf9515",
                    "mf9516", "mf9517", "mf9518"
                   ]

        LS_Coeff = 0.5
        LambdaList = [-0.2, -0.2, -0.2, -0.2, -0.2, -0.2, -0.2, -0.2, -0.2]
        AlphaList =  [0.02, 0.02, 0.02,0.02, 0.02, 0.02,0.02, 0.02, 0.02]
        GammaList =  [-0.0004, -0.0004, -0.0004,-0.0004, -0.0004, -0.0004,-0.0004, -0.0004, -0.0004]

        MChM.ImpCalc(eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, "mf8001")
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
        DfInt = pd.DataFrame({'Origin': Or, 'Destination': De})

        # Bus
        Dfmerge = pd.DataFrame({'Or': Or, 'De': De, 'BL': BLBsWk, 'BAuI1':BAuI1.flatten(),
                               'BAuI2':BAuI2.flatten(), 'BAuI3':BAuI3.flatten()})
        DfmergedAuto = Dfmerge.groupby(['Or', 'BL']).sum().reset_index()
        DfmergedTran = Dfmerge.groupby(['BL', 'De']).sum().reset_index()
        DfAuto, DfTran = self.splitpnr(DfmergedAuto, DfmergedTran, DfInt)
        SOVI1 += DfAuto['BAuI1'].reshape(1741, 1741)
        SOVI2 += DfAuto['BAuI2'].reshape(1741, 1741)
        SOVI3 += DfAuto['BAuI3'].reshape(1741, 1741)
        Bus   += DfTran['BAuI1'].reshape(1741, 1741)
        Bus   += DfTran['BAuI2'].reshape(1741, 1741)
        Bus   += DfTran['BAuI3'].reshape(1741, 1741)

        # Rail
        Dfmerge = pd.DataFrame({'Or': Or, 'De': De, 'BL': BLRlWk, 'RAuI1':RAuI1.flatten(),
                                       'RAuI2':RAuI2.flatten(), 'RAuI3':RAuI3.flatten()})
        DfmergedAuto = Dfmerge.groupby(['Or', 'BL']).sum().reset_index()
        DfmergedTran = Dfmerge.groupby(['BL', 'De']).sum().reset_index()
        DfAuto, DfTran = self.splitpnr(DfmergedAuto, DfmergedTran, DfInt)
        SOVI1 += DfAuto['RAuI1'].reshape(1741, 1741)
        SOVI2 += DfAuto['RAuI2'].reshape(1741, 1741)
        SOVI3 += DfAuto['RAuI3'].reshape(1741, 1741)
        Rail  += DfTran['RAuI1'].reshape(1741, 1741)
        Rail  += DfTran['RAuI2'].reshape(1741, 1741)
        Rail  += DfTran['RAuI3'].reshape(1741, 1741)

        #WCE
        Dfmerge = pd.DataFrame({'Or': Or, 'De': De, 'BL': BLWcWk, 'WAuI1':WAuI1.flatten(),
                                       'WAuI2':WAuI2.flatten(), 'WAuI3':WAuI3.flatten()})
        DfmergedAuto = Dfmerge.groupby(['Or', 'BL']).sum().reset_index()
        DfmergedTran = Dfmerge.groupby(['BL', 'De']).sum().reset_index()
        DfAuto, DfTran = self.splitpnr(DfmergedAuto, DfmergedTran, DfInt)
        SOVI1 += DfAuto['WAuI1'].reshape(1741, 1741)
        SOVI2 += DfAuto['WAuI2'].reshape(1741, 1741)
        SOVI3 += DfAuto['WAuI3'].reshape(1741, 1741)
        WCE   += DfTran['WAuI1'].reshape(1741, 1741)
        WCE   += DfTran['WAuI2'].reshape(1741, 1741)
        WCE   += DfTran['WAuI3'].reshape(1741, 1741)

#       ##############################################################################
#        ##       Set Demand Matrices
#       ##############################################################################
        util.set_matrix_numpy(eb, "mf9100", SOVI1)
        util.set_matrix_numpy(eb, "mf9101", SOVI2)
        util.set_matrix_numpy(eb, "mf9102", SOVI3)
        util.set_matrix_numpy(eb, "mf9103", HV2I1)
        util.set_matrix_numpy(eb, "mf9104", HV2I2)
        util.set_matrix_numpy(eb, "mf9105", HV2I3)
        util.set_matrix_numpy(eb, "mf9106", HV3I1)
        util.set_matrix_numpy(eb, "mf9107", HV3I2)
        util.set_matrix_numpy(eb, "mf9108", HV3I3)
        util.set_matrix_numpy(eb, "mf9109", Bus)
        util.set_matrix_numpy(eb, "mf9110", Rail)
        util.set_matrix_numpy(eb, "mf9111", WCE)
        util.set_matrix_numpy(eb, "mf9112", Walk)
        util.set_matrix_numpy(eb, "mf9113", Bike)
        util.set_matrix_numpy(eb, "mf9114", BAuI1)
        util.set_matrix_numpy(eb, "mf9115", BAuI2)
        util.set_matrix_numpy(eb, "mf9116", BAuI3)
        util.set_matrix_numpy(eb, "mf9117", RAuI1)
        util.set_matrix_numpy(eb, "mf9118", RAuI2)
        util.set_matrix_numpy(eb, "mf9119", RAuI3)
        util.set_matrix_numpy(eb, "mf9120", WAuI1)
        util.set_matrix_numpy(eb, "mf9121", WAuI2)
        util.set_matrix_numpy(eb, "mf9122", WAuI3)


    def Calc_Prob(self, eb, Dict, Logsum):
        util = _m.Modeller().tool("translink.emme.util")
        Th =    0.517330
        Tiny = 0.000000001
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
        DfAuto = pd.merge(DfInt, DfmergedAuto, left_on = ['Origin', 'Destination'],
                     right_on = ['Or', 'BL'], how = 'left')
        DfAuto = DfAuto.fillna(0)

        DfTran = pd.merge(DfInt, DfmergedTran, left_on = ['Origin', 'Destination'],
                     right_on = ['BL', 'De'], how = 'left')
        DfTran = DfTran.fillna(0)

        return (DfAuto, DfTran)

    @_m.logbook_trace("Initialize Matrices")
    def matrix_batchins(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        util.initmat(eb, "mf9000", "WkLSI1A1", "LogSum Wk I1 A1", 0)
        util.initmat(eb, "mf9001", "WkLSI1A2", "LogSum Wk I1 A2", 0)
        util.initmat(eb, "mf9002", "WkLSI1A3", "LogSum Wk I1 A3", 0)
        util.initmat(eb, "mf9003", "WkLSI2A1", "LogSum Wk I2 A1", 0)
        util.initmat(eb, "mf9004", "WkLSI2A2", "LogSum Wk I2 A2", 0)
        util.initmat(eb, "mf9005", "WkLSI2A3", "LogSum Wk I2 A3", 0)
        util.initmat(eb, "mf9006", "WkLSI3A1", "LogSum Wk I3 A1", 0)
        util.initmat(eb, "mf9007", "WkLSI3A2", "LogSum Wk I3 A2", 0)
        util.initmat(eb, "mf9008", "WkLSI3A3", "LogSum Wk I3 A3", 0)
        util.initmat(eb, "mf9100", "SOVI1", "LogSum Wk I1 A1", 0)
        util.initmat(eb, "mf9101", "SOVI2", "LogSum Wk I1 A2", 0)
        util.initmat(eb, "mf9102", "SOVI3", "LogSum Wk I1 A3", 0)
        util.initmat(eb, "mf9103", "HV2I1", "LogSum Wk I2 A1", 0)
        util.initmat(eb, "mf9104", "HV2I2", "LogSum Wk I2 A2", 0)
        util.initmat(eb, "mf9105", "HV2I3", "LogSum Wk I2 A3", 0)
        util.initmat(eb, "mf9106", "HV3I1", "LogSum Wk I3 A1", 0)
        util.initmat(eb, "mf9107", "HV3I2", "LogSum Wk I3 A2", 0)
        util.initmat(eb, "mf9108", "HV3I3", "LogSum Wk I3 A3", 0)
        util.initmat(eb, "mf9109", "Bus", "LogSum Wk I3 A3", 0)
        util.initmat(eb, "mf9110", "Rail", "LogSum Wk I1 A1", 0)
        util.initmat(eb, "mf9111", "WCE", "LogSum Wk I1 A2", 0)
        util.initmat(eb, "mf9112", "Walk", "LogSum Wk I1 A3", 0)
        util.initmat(eb, "mf9113", "Bike", "LogSum Wk I2 A1", 0)
        util.initmat(eb, "mf9114", "BAUI1", "LogSum Wk I1 A2", 0)
        util.initmat(eb, "mf9115", "BAUI2", "LogSum Wk I1 A3", 0)
        util.initmat(eb, "mf9116", "BAUI3", "LogSum Wk I2 A1", 0)
        util.initmat(eb, "mf9117", "RAUI1", "LogSum Wk I1 A2", 0)
        util.initmat(eb, "mf9118", "RAUI2", "LogSum Wk I1 A3", 0)
        util.initmat(eb, "mf9119", "RAUI3", "LogSum Wk I2 A1", 0)
        util.initmat(eb, "mf9120", "WAUI1", "LogSum Wk I1 A2", 0)
        util.initmat(eb, "mf9121", "WAUI2", "LogSum Wk I1 A3", 0)
        util.initmat(eb, "mf9122", "WAUI3", "LogSum Wk I2 A1", 0)
        util.initmat(eb, "mf9500", "WkLSI1A1", "LogSum Wk I1 A1", 0)
        util.initmat(eb, "mf9501", "WkLSI1A2", "LogSum Wk I1 A2", 0)
        util.initmat(eb, "mf9502", "WkLSI1A3", "LogSum Wk I1 A3", 0)
        util.initmat(eb, "mf9503", "WkLSI2A1", "LogSum Wk I2 A1", 0)
        util.initmat(eb, "mf9504", "WkLSI2A2", "LogSum Wk I2 A2", 0)
        util.initmat(eb, "mf9505", "WkLSI2A3", "LogSum Wk I2 A3", 0)
        util.initmat(eb, "mf9506", "WkLSI3A1", "LogSum Wk I3 A1", 0)
        util.initmat(eb, "mf9507", "WkLSI3A2", "LogSum Wk I3 A2", 0)
        util.initmat(eb, "mf9508", "WkLSI3A3", "LogSum Wk I3 A3", 0)
        util.initmat(eb, "mf9510", "WkLSI1A1", "LogSum Wk I1 A1", 0)
        util.initmat(eb, "mf9511", "WkLSI1A2", "LogSum Wk I1 A2", 0)
        util.initmat(eb, "mf9512", "WkLSI1A3", "LogSum Wk I1 A3", 0)
        util.initmat(eb, "mf9513", "WkLSI2A1", "LogSum Wk I2 A1", 0)
        util.initmat(eb, "mf9514", "WkLSI2A2", "LogSum Wk I2 A2", 0)
        util.initmat(eb, "mf9515", "WkLSI2A3", "LogSum Wk I2 A3", 0)
        util.initmat(eb, "mf9516", "WkLSI3A1", "LogSum Wk I3 A1", 0)
        util.initmat(eb, "mf9517", "WkLSI3A2", "LogSum Wk I3 A2", 0)
        util.initmat(eb, "mf9518", "WkLSI3A3", "LogSum Wk I3 A3", 0)
