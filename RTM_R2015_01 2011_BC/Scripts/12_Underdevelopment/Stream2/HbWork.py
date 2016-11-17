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
        VOC = 0.18
        Occ = 3.25
        Df['AutoTim'] = util.get_matrix_numpy(eb, 'mf8000')
        Df['AutoDis'] = util.get_matrix_numpy(eb, 'mf8001')
        Df['AutoCos'] = Df['AutoDis']*VOC + util.get_matrix_numpy(eb, 'mf8002')

        # Coefficients
        AscH2 = -3.343842
        AscH3 = -5.184035
        CstI1 = -0.345117
        CstI2 = -0.225996
        CstI3 = -0.190001
        AutTi = -0.110655
        SOVA1 =  2.178567
        SOVA2 =  2.725776
        HOVA1 =  1.276692
        HOVA2 =  1.822254

        # Utilities
        # SOV
        ## TODO Parking Cost
        ## Auto Accessibility
        Coef = [AutTi]
        Vari = [Df['AutoTim']]
        Df['GeUtl']  = util.sumproduct(Coef, Vari)
        Df['GeUtl']  = MChM.AutoAvail(Df['AutoDis'], Df['GeUtl'])

        DfU['SOVI1']  = Df['GeUtl'] + CstI1*Df['AutoCos']
        DfU['SOVI2']  = Df['GeUtl'] + CstI2*Df['AutoCos']
        DfU['SOVI3']  = Df['GeUtl'] + CstI3*Df['AutoCos']
#        DfU['SOVI1A0'] = MChM.SOVAvail(DfU['SOVI1'])
#        DfU['SOVI2A0'] = MChM.SOVAvail(DfU['SOVI2'])
#        DfU['SOVI3A0'] = MChM.SOVAvail(DfU['SOVI3'])

        # HOV2
        ## TODO Parking Cost
        ## Auto Accessibility
        Coef = [AutTi]
        Vari = [Df['AutoTim']]
        Df['GeUtl']  = util.sumproduct(Coef, Vari) + AscH2
        Df['GeUtl']  = MChM.AutoAvail(Df['AutoDis'], Df['GeUtl'])

        DfU['HV2I1']  = Df['GeUtl'] + CstI1*Df['AutoCos']/2.0
        DfU['HV2I2']  = Df['GeUtl'] + CstI2*Df['AutoCos']/2.0
        DfU['HV2I3']  = Df['GeUtl'] + CstI3*Df['AutoCos']/2.0

        # HOV3
        ## TODO Parking Cost
        ## Auto Accessibility
        Coef = [AutTi]
        Vari = [Df['AutoTim']]
        Df['GeUtl']  = util.sumproduct(Coef, Vari) + AscH3
        Df['GeUtl']  = MChM.AutoAvail(Df['AutoDis'], Df['GeUtl'])

        DfU['HV3I1']  = Df['GeUtl'] + CstI1*Df['AutoCos']/Occ
        DfU['HV3I2']  = Df['GeUtl'] + CstI2*Df['AutoCos']/Occ
        DfU['HV3I3']  = Df['GeUtl'] + CstI3*Df['AutoCos']/Occ

#        ##############################################################################
#        ##       Walk to Transit Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        Tiny=0.000001
        Df['BusIVT'] = util.get_matrix_numpy(eb, 'mf8010')
        Df['BusWat'] = util.get_matrix_numpy(eb, 'mf8011')
        Df['BusAux'] = util.get_matrix_numpy(eb, 'mf8012')
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'mf8013')
        Df['BusFar'] = util.get_matrix_numpy(eb, 'mf8014')
        Df['BusTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux'] + Df['BusBrd']

        Df['RalIVB'] = util.get_matrix_numpy(eb, 'mf8020')
        Df['RalIVR'] = util.get_matrix_numpy(eb, 'mf8021')
        Df['RalWat'] = util.get_matrix_numpy(eb, 'mf8022')
        Df['RalAux'] = util.get_matrix_numpy(eb, 'mf8023')
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'mf8024')
        Df['RalFar'] = util.get_matrix_numpy(eb, 'mf8025')
        Df['RalTot'] = Df['RalIVB'] + Df['RalIVR'] + Df['RalWat'] + Df['RalAux'] + Df['RalBrd']
        Df['RalIBR'] = Df['RalIVB']/(Df['RalIVB'] + Df['RalIVR'] + Tiny)
        Df['RalIRR'] = Df['RalIVR']/(Df['RalIVB'] + Df['RalIVR'] + Tiny)
        
        Df['WCEIVB'] = util.get_matrix_numpy(eb, 'mf8030')
        Df['WCEIVR'] = util.get_matrix_numpy(eb, 'mf8031')
        Df['WCEIVW'] = util.get_matrix_numpy(eb, 'mf8032')
        Df['WCEWat'] = util.get_matrix_numpy(eb, 'mf8033')
        Df['WCEAux'] = util.get_matrix_numpy(eb, 'mf8034')
        Df['WCEBrd'] = util.get_matrix_numpy(eb, 'mf8035')
        Df['WCEFar'] = util.get_matrix_numpy(eb, 'mf8036')
        Df['WCETot'] = Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW'] + Df['WCEWat'] + Df['WCEAux'] + Df['WCEBrd']
        Df['WCEIBR'] = Df['WCEIVB']/(Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW'] + Tiny)
        Df['WCEIRR'] = Df['WCEIVR']/(Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW'] + Tiny)
        Df['WCEIWR'] = Df['WCEIVW']/(Df['WCEIVB'] + Df['WCEIVR'] + Df['WCEIVW'] + Tiny)        
        
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

        # Utilities
        # Bus Utility
        ## TODO Transit Accessibility

        Coef = [BsIVT, TrWat, TrAux, TrTrf]
        Vari = [Df['BusIVT'], Df['BusWat'], Df['BusAux'],
                Df['BusBrd'] -1]
        Df['GeUtl'] = util.sumproduct(Coef, Vari) + AscBs
        Df['GeUtl'] = MChM.BusAvail(Df, Df['GeUtl'])

        DfU['BusI1'] = Df['GeUtl'] + CstI1*Df['BusFar']
        DfU['BusI2'] = Df['GeUtl'] + CstI2*Df['BusFar']
        DfU['BusI3'] = Df['GeUtl'] + CstI3*Df['BusFar']

        # Rail Utility
        ## TODO Transit Accessibility
        Coef = [AscBs, AscRl, BsIVT, RTIVT, TrWat, TrAux, TrTrf]
        Vari = [Df['RalIBR'],Df['RalIRR'], Df['RalIVB'], Df['RalIVR'],
                Df['RalWat'],Df['RalAux'], Df['RalBrd'] -1]
                
        Df['GeUtl'] = util.sumproduct(Coef, Vari)
        Df['GeUtl'] = MChM.RailAvail(Df, Df['GeUtl'])

        DfU['RalI1'] = Df['GeUtl'] + CstI1*Df['RalFar']
        DfU['RalI2'] = Df['GeUtl'] + CstI2*Df['RalFar']
        DfU['RalI3'] = Df['GeUtl'] + CstI3*Df['RalFar']

        # WCE Utility
        ## TODO Transit Accessibility
        Coef = [AscBs, AscRl, AscWc, BsIVT, RTIVT, RTIVT, TrWat, TrAux, TrTrf]
        Vari = [Df['WCEIBR'], Df['WCEIRR'], Df['WCEIWR'], Df['WCEIVB'],
                Df['WCEIVR'], Df['WCEIVW'],Df['WCEWat'], Df['WCEAux'], Df['WCEBrd'] -1]
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
        Df['BAuTim'] = util.get_matrix_numpy(eb, 'mf8040')
        Df['BAuDis'] = util.get_matrix_numpy(eb, 'mf8041')
        Df['BAuCos'] = Df['BAuDis']*VOC + util.get_matrix_numpy(eb, 'mf8042')
        Df['BusIVT'] = util.get_matrix_numpy(eb, 'mf8043')
        Df['BusWat'] = util.get_matrix_numpy(eb, 'mf8044')
        Df['BusAux'] = util.get_matrix_numpy(eb, 'mf8045')
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'mf8046')
        Df['BusFar'] = util.get_matrix_numpy(eb, 'mf8047')
        Df['BAuTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux'] + Df['BusBrd'] + Df['BAuTim']
        Df['BAuIBR'] = Df['BusIVT']/(Df['BusIVT'] + Df['BAuTim'] + Tiny)
   

        Df['RAuTim'] = util.get_matrix_numpy(eb, 'mf8050')
        Df['RAuDis'] = util.get_matrix_numpy(eb, 'mf8051')
        Df['RAuCos'] = Df['RAuDis']*VOC + util.get_matrix_numpy(eb, 'mf8052')
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'mf8053')
        Df['RalIVR'] = util.get_matrix_numpy(eb, 'mf8054')
        Df['RalWat'] = util.get_matrix_numpy(eb, 'mf8055')
        Df['RalAux'] = util.get_matrix_numpy(eb, 'mf8056')
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'mf8057')
        Df['RalFar'] = util.get_matrix_numpy(eb, 'mf8058')
        Df['RAuTot'] = Df['RalIVB'] + Df['RalIVR'] + Df['RalWat'] + Df['RalAux'] + Df['RalBrd'] +  Df['RAuTim']
        Df['RAuIBR'] = Df['RalIVB']/(Df['RalIVB'] + Df['RalIVR'] + Df['RAuTim'] + Tiny)        
        Df['RAuIRR'] = Df['RalIVR']/(Df['RalIVB'] + Df['RalIVR'] + Df['RAuTim'] + Tiny)         

        Df['WAuTim'] = util.get_matrix_numpy(eb, 'mf8060')
        Df['WAuDis'] = util.get_matrix_numpy(eb, 'mf8061')
        Df['WAuCos'] = Df['WAuDis']*VOC + util.get_matrix_numpy(eb, 'mf8062')
        Df['WCEIVB'] = util.get_matrix_numpy(eb, 'mf8063')
        Df['WCEIVR'] = util.get_matrix_numpy(eb, 'mf8064')
        Df['WCEIVW'] = util.get_matrix_numpy(eb, 'mf8065')
        Df['WCEWat'] = util.get_matrix_numpy(eb, 'mf8066')
        Df['WCEAux'] = util.get_matrix_numpy(eb, 'mf8067')
        Df['WCEBrd'] = util.get_matrix_numpy(eb, 'mf8068')
        Df['WCEFar'] = util.get_matrix_numpy(eb, 'mf8069')
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
        Df['AutoDis'] = util.get_matrix_numpy(eb, 'mf8001')
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

        ## Low Income Zero Autos
        Dict = {
               'SOV'  : [DfU['SOVI1']],
               'HOV'  : [DfU['HV2I1'], DfU['HV3I1']],
               'WTra' : [DfU['BusI1'] + TraA0, DfU['RalI1'] + TraA0, DfU['WCEI1'] + TraA0],
               'DTra' : [DfU['BAuI1'], DfU['RAuI1'], DfU['WAuI1']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }

        Dict1 = self.Calc_Prob(eb, Dict, "mf9000")

        ## Low Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI1'] + SOVA1],
               'HOV'  : [DfU['HV2I1'] + HOVA1, DfU['HV3I1'] + HOVA1],
               'WTra' : [DfU['BusI1'], DfU['RalI1'], DfU['WCEI1']],
               'DTra' : [DfU['BAuI1'], DfU['RAuI1'], DfU['WAuI1']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        Dict2 = self.Calc_Prob(eb, Dict, "mf9001")

        ## Low Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI1'] + SOVA2],
               'HOV'  : [DfU['HV2I1'] + HOVA2, DfU['HV3I1'] + HOVA2],
               'WTra' : [DfU['BusI1'], DfU['RalI1'], DfU['WCEI1']],
               'DTra' : [DfU['BAuI1'], DfU['RAuI1'], DfU['WAuI1']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        Dict3 = self.Calc_Prob(eb, Dict, "mf9002")

        ## Med Income Zero Autos
        Dict = {
               'SOV'  : [DfU['SOVI2']],
               'HOV'  : [DfU['HV2I2'], DfU['HV3I2']],
               'WTra' : [DfU['BusI2'] + TraA0, DfU['RalI2'] + TraA0, DfU['WCEI2'] + TraA0],
               'DTra' : [DfU['BAuI2'], DfU['RAuI2'], DfU['WAuI2']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        Dict4 = self.Calc_Prob(eb, Dict, "mf9003")

        ## Med Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI2'] + SOVA1],
               'HOV'  : [DfU['HV2I2'] + HOVA1, DfU['HV3I2'] + HOVA1],
               'WTra' : [DfU['BusI2'], DfU['RalI2'], DfU['WCEI2']],
               'DTra' : [DfU['BAuI2'], DfU['RAuI2'], DfU['WAuI2']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        Dict5 = self.Calc_Prob(eb, Dict, "mf9004")

        ## Med Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI2'] + SOVA2],
               'HOV'  : [DfU['HV2I2'] + HOVA2, DfU['HV3I2'] + HOVA2],
               'WTra' : [DfU['BusI2'], DfU['RalI2'], DfU['WCEI2']],
               'DTra' : [DfU['BAuI2'], DfU['RAuI2'], DfU['WAuI2']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        Dict6 = self.Calc_Prob(eb, Dict, "mf9005")

        ## High Income Zero Autos
        Dict = {
               'SOV'  : [DfU['SOVI3']],
               'HOV'  : [DfU['HV2I3'], DfU['HV3I3']],
               'WTra' : [DfU['BusI3'] + TraA0, DfU['RalI3'] + TraA0, DfU['WCEI3'] + TraA0],
               'DTra' : [DfU['BAuI3'], DfU['RAuI3'], DfU['WAuI3']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        Dict7 = self.Calc_Prob(eb, Dict, "mf9006")

        ## High Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI3'] + SOVA1],
               'HOV'  : [DfU['HV2I3'] + HOVA1, DfU['HV3I3'] + HOVA1],
               'WTra' : [DfU['BusI3'], DfU['RalI3'], DfU['WCEI3']],
               'DTra' : [DfU['BAuI3'], DfU['RAuI3'], DfU['WAuI3']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        Dict8 = self.Calc_Prob(eb, Dict, "mf9007")

        ## High Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI3'] + SOVA2],
               'HOV'  : [DfU['HV2I3'] + HOVA2, DfU['HV3I3'] + HOVA2],
               'WTra' : [DfU['BusI3'], DfU['RalI3'], DfU['WCEI3']],
               'DTra' : [DfU['BAuI3'], DfU['RAuI3'], DfU['WAuI3']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        Dict9 = self.Calc_Prob(eb, Dict, "mf9008")
        del DfU
        
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

        Dict1 = self.Calc_Demand(Dict1, util.get_matrix_numpy(eb,"mf9510"))
        Dict2 = self.Calc_Demand(Dict2, util.get_matrix_numpy(eb,"mf9511"))
        Dict3 = self.Calc_Demand(Dict3, util.get_matrix_numpy(eb,"mf9512"))
        Dict4 = self.Calc_Demand(Dict4, util.get_matrix_numpy(eb,"mf9513"))
        Dict5 = self.Calc_Demand(Dict5, util.get_matrix_numpy(eb,"mf9514"))
        Dict6 = self.Calc_Demand(Dict6, util.get_matrix_numpy(eb,"mf9515"))
        Dict7 = self.Calc_Demand(Dict7, util.get_matrix_numpy(eb,"mf9516"))
        Dict8 = self.Calc_Demand(Dict8, util.get_matrix_numpy(eb,"mf9517"))
        Dict9 = self.Calc_Demand(Dict9, util.get_matrix_numpy(eb,"mf9518"))

        SOVI1 = Dict1['SOV'][0] + Dict2['SOV'][0] + Dict3['SOV'][0]
        SOVI2 = Dict4['SOV'][0] + Dict5['SOV'][0] + Dict6['SOV'][0]
        SOVI3 = Dict7['SOV'][0] + Dict8['SOV'][0] + Dict9['SOV'][0]

        HV2I1 = Dict1['HOV'][0] + Dict2['HOV'][0] + Dict3['HOV'][0]
        HV2I2 = Dict4['HOV'][0] + Dict5['HOV'][0] + Dict6['HOV'][0]
        HV2I3 = Dict7['HOV'][0] + Dict8['HOV'][0] + Dict9['HOV'][0]
        HV3I1 = Dict1['HOV'][1] + Dict2['HOV'][1] + Dict3['HOV'][1]
        HV3I2 = Dict4['HOV'][1] + Dict5['HOV'][1] + Dict6['HOV'][1]
        HV3I3 = Dict7['HOV'][1] + Dict8['HOV'][1] + Dict9['HOV'][1]

        Bus  =  Dict1['WTra'][0] + Dict2['WTra'][0] + Dict3['WTra'][0]
        Bus +=  Dict4['WTra'][0] + Dict5['WTra'][0] + Dict6['WTra'][0]
        Bus +=  Dict7['WTra'][0] + Dict8['WTra'][0] + Dict9['WTra'][0]
        Rail =  Dict1['WTra'][1] + Dict2['WTra'][1] + Dict3['WTra'][1]
        Rail += Dict4['WTra'][1] + Dict5['WTra'][1] + Dict6['WTra'][1]
        Rail += Dict7['WTra'][1] + Dict8['WTra'][1] + Dict9['WTra'][1]
        WCE =   Dict1['WTra'][2] + Dict2['WTra'][2] + Dict3['WTra'][2]
        WCE +=  Dict4['WTra'][2] + Dict5['WTra'][2] + Dict6['WTra'][2]
        WCE +=  Dict7['WTra'][2] + Dict8['WTra'][2] + Dict9['WTra'][2]

        Walk =  Dict1['Acti'][0] + Dict2['Acti'][0] + Dict3['Acti'][0]
        Walk += Dict4['Acti'][0] + Dict5['Acti'][0] + Dict6['Acti'][0]
        Walk += Dict7['Acti'][0] + Dict8['Acti'][0] + Dict9['Acti'][0]
        Bike =  Dict1['Acti'][1] + Dict2['Acti'][1] + Dict3['Acti'][1]
        Bike += Dict4['Acti'][1] + Dict5['Acti'][1] + Dict6['Acti'][1]
        Bike += Dict7['Acti'][1] + Dict8['Acti'][1] + Dict9['Acti'][1]

        BAuI1 = Dict1['DTra'][0] + Dict2['DTra'][0] + Dict3['DTra'][0]
        BAuI2 = Dict4['DTra'][0] + Dict5['DTra'][0] + Dict6['DTra'][0]
        BAuI3 = Dict7['DTra'][0] + Dict8['DTra'][0] + Dict9['DTra'][0]
        RAuI1 = Dict1['DTra'][1] + Dict2['DTra'][1] + Dict3['DTra'][1]
        RAuI2 = Dict4['DTra'][1] + Dict5['DTra'][1] + Dict6['DTra'][1]
        RAuI3 = Dict7['DTra'][1] + Dict8['DTra'][1] + Dict9['DTra'][1]
        WAuI1 = Dict1['DTra'][2] + Dict2['DTra'][2] + Dict3['DTra'][2]
        WAuI2 = Dict4['DTra'][2] + Dict5['DTra'][2] + Dict6['DTra'][2]
        WAuI3 = Dict7['DTra'][2] + Dict8['DTra'][2] + Dict9['DTra'][2]

        del Dict1, Dict2, Dict3
        del Dict4, Dict5, Dict6
        del Dict7, Dict8, Dict9

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
