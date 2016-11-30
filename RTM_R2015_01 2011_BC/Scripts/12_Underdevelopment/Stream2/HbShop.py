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
                     'BikDist ' = 10.0
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

        p2   = -1.629845
        p4   =  1.015371
        p6   =  2.125109
        p10  = -0.254472
        p11  = -5.823884
        p12  = -0.696618
        p14  = -0.285214
        p15  = -0.069414
        p17  = -0.157412
        p18  = -0.166942
        p19  = -0.679105
        p20  = -2.672878
        p21  = -1.738592
        p160 =  2.617800
        p161 =  3.446040
        p162 =  3.067046
        p163 =  3.247404
        p164 =  0.954408
        p701 =  0.953901
        p870 =  0.435314
        thet =  0.369560

#        ##############################################################################
#        ##       Auto Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        MaxPark = 10.0
        VOC = util.get_matrix_numpy(eb, 'ms100')
        Occ = util.get_matrix_numpy(eb, 'ms115')
        Df['ParkCost'] = util.get_matrix_numpy(eb, 'mo60')  # 2 hour parking
        Df['ParkCost'][Df['ParkCost']>MaxPark] = MaxPark
        Df['ParkCost'] = Df['ParkCost'].reshape(1, NoTAZ) + np.zeros((NoTAZ, 1))

        Df['AutoDisSOV'] = util.get_matrix_numpy(eb, 'mf5130')
        Df['AutoTimSOV'] = util.get_matrix_numpy(eb, 'mf5131')
        Df['AutoCosSOV'] = Df['AutoDisSOV']*VOC + util.get_matrix_numpy(eb, 'mf5132') + Df['ParkCost']

        Df['AutoDisHOV'] = util.get_matrix_numpy(eb, 'mf5136')
        Df['AutoTimHOV'] = util.get_matrix_numpy(eb, 'mf5137')
        Df['AutoCosHOV'] = Df['AutoDisHOV']*VOC + util.get_matrix_numpy(eb, 'mf5138') + Df['ParkCost']

        # Utilities
        # SOV
        Df['GeUtl'] = ( 0
                      + p15*Df['AutoTimSOV'])


        Df['GeUtl']  = MChM.AutoAvail(Df['AutoDisSOV'], Df['GeUtl'], AvailDict)

        DfU['SOVI1']  = Df['GeUtl'] + p12*Df['AutoCosSOV']
        DfU['SOVI2']  = Df['GeUtl'] + p12*Df['AutoCosSOV']
        DfU['SOVI3']  = Df['GeUtl'] + p14*Df['AutoCosSOV']

        # HOV2+
        Df['GeUtl'] = ( p2
                      + p15*Df['AutoTimHOV'])

        Df['GeUtl']  = MChM.AutoAvail(Df['AutoDisHOV'], Df['GeUtl'], AvailDict)

        DfU['HV2+I1']  = Df['GeUtl'] + p12*Df['AutoCosHOV']/Occ
        DfU['HV2+I2']  = Df['GeUtl'] + p12*Df['AutoCosHOV']/Occ
        DfU['HV2+I3']  = Df['GeUtl'] + p14*Df['AutoCosHOV']/Occ


#        ##############################################################################
#        ##       Walk to Transit Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        Tiny=0.000001
        Df['BusIVT'] = util.get_matrix_numpy(eb, 'mf5330')
        Df['BusWat'] = util.get_matrix_numpy(eb, 'mf5331')
        Df['BusAux'] = util.get_matrix_numpy(eb, 'mf5332')
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'mf5333')
        Df['BusFar'] = util.get_matrix_numpy(eb, 'mf5334')
        Df['BusTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux'] + Df['BusBrd']

        Df['RalIVR'] = util.get_matrix_numpy(eb, 'mf5530')
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'mf5531')
        Df['RalWat'] = util.get_matrix_numpy(eb, 'mf5532')
        Df['RalAux'] = util.get_matrix_numpy(eb, 'mf5533')
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'mf5534')
        Df['RalFar'] = util.get_matrix_numpy(eb, 'mf5535')
        Df['RalTot'] = Df['RalIVB'] + Df['RalIVR'] + Df['RalWat'] + Df['RalAux'] + Df['RalBrd']
        Df['RalIBR'] = Df['RalIVB']/(Df['RalIVB'] + Df['RalIVR'] + Tiny)
        Df['RalIRR'] = Df['RalIVR']/(Df['RalIVB'] + Df['RalIVR'] + Tiny)

        Df['IntZnl'] = np.identity(NoTAZ)

        # Utilities
        # Bus Utility

        Df['GeUtl'] = ( p4
                      + p15*Df['BusIVT']
                      + p17*Df['BusWat']
                      + p18*Df['BusAux']
                      + p19*(Df['BusBrd'])


        Df['GeUtl'] = MChM.BusAvail(Df, Df['GeUtl'], AvailDict)

        DfU['BusI1'] = Df['GeUtl'] + p12*Df['BusFar']
        DfU['BusI2'] = Df['GeUtl'] + p12*Df['BusFar']
        DfU['BusI3'] = Df['GeUtl'] + p14*Df['BusFar']

        # Rail Utility
        Df['GeUtl'] = ( p4*Df['RalIBR']
                      + p6*Df['RalIRR']
                      + p15*Df['RalIVB']
                      + p15*Df['RalIVR']
                      + p17*Df['RalWat']
                      + p18*Df['RalAux']
                      + p19*(Df['RalBrd'])


        Df['GeUtl'] = MChM.RailAvail(Df, Df['GeUtl'],AvailDict)

        DfU['RalI1'] = Df['GeUtl'] + p12*Df['RalFar']
        DfU['RalI2'] = Df['GeUtl'] + p12*Df['RalFar']
        DfU['RalI3'] = Df['GeUtl'] + p14*Df['RalFar']

#        ##############################################################################
#        ##       Active Modes
#        ##############################################################################

        Df = {}
        Df['AutoDis'] = util.get_matrix_numpy(eb, 'mf5130')

        Df['PopEmpDen'] = util.get_matrix_numpy(eb, 'mo200') + util.get_matrix_numpy(eb, 'mo201')
        Df['PopEmpDen'] = Df['PopEmpDen'].reshape(NoTAZ, 1) + np.zeros(1, NoTAZ)
        Df['PopEmpDen'][Df['PopEmpDen']<1.0] = 1.0
        Df['PopEmpDen'] = np.log(Df['PopEmpDen'])
        Df['BikScr'] = util.get_matrix_numpy(eb, 'mf90')

        # Walk Utility
        DfU['Walk'] = ( p10
                      + p20*Df['AutoDis']
                      + p701*Df['PopEmpDen'])

        DfU['Walk'] = MChM.WalkAvail(Df['AutoDis'], DfU['Walk'], AvailDict)

        # Bike Utility
        DfU['Bike'] = ( p11
                      + p21*Df['AutoDis']
                      + p701*Df['PopEmpDen']
                      + p870*Df['BikScr'])


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
               'HOV'  : [DfU['HV2+I1']],
               'WTra' : [DfU['BusI1'] + p164, DfU['RalI1'] + p164],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }

        I1A0_Dict = self.Calc_Prob(eb, Dict, "mf9030", thet)

        ## Low Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI1'] + p160],
               'HOV'  : [DfU['HV2+I1'] + p162],
               'WTra' : [DfU['BusI1'], DfU['RalI1']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I1A1_Dict = self.Calc_Prob(eb, Dict, "mf9031", thet)

        ## Low Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI1'] + p161],
               'HOV'  : [DfU['HV2+I1'] + p163],
               'WTra' : [DfU['BusI1'], DfU['RalI1']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I1A2_Dict = self.Calc_Prob(eb, Dict, "mf9032", thet)

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

        I2A0_Dict = self.Calc_Prob(eb, Dict, "mf9033", thet)

        ## Med Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI2'] + p160],
               'HOV'  : [DfU['HV2+I2'] + p162],
               'WTra' : [DfU['BusI2'], DfU['RalI2']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I2A1_Dict = self.Calc_Prob(eb, Dict, "mf9034", thet)

        ## Med Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI2'] + p161],
               'HOV'  : [DfU['HV2+I2'] + p163],
               'WTra' : [DfU['BusI2'], DfU['RalI2']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I2A2_Dict = self.Calc_Prob(eb, Dict, "mf9035", thet)

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
        I3A0_Dict = self.Calc_Prob(eb, Dict, "mf9036", thet)

        ## High Income One Auto
        Dict = {
               'SOV'  : [DfU['SOVI3'] + p160],
               'HOV'  : [DfU['HV2+I3'] + p162],
               'WTra' : [DfU['BusI3'], DfU['RalI3']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I3A1_Dict = self.Calc_Prob(eb, Dict, "mf9037", thet)

        ## High Income Two Autos
        Dict = {
               'SOV'  : [DfU['SOVI3'] + p161],
               'HOV'  : [DfU['HV2+I3'] + p163],
               'WTra' : [DfU['BusI3'], DfU['RalI3']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }
        I3A2_Dict = self.Calc_Prob(eb, Dict, "mf9038", thet)

        del DfU, Dict

       ##############################################################################
        ##       Trip Distribution
       ##############################################################################

        Logsum =  [
                  "mf9030", "mf9031", "mf9032",
                  "mf9033", "mf9034", "mf9035",
                  "mf9036", "mf9037", "mf9038"
                   ]

        imp_list = [
                  "mf9100", "mf9101", "mf9102",
                  "mf9103", "mf9104", "mf9105",
                  "mf9106", "mf9107", "mf9108"
                   ]

        mo_list =  [
                    "mo2040", "mo2043", "mo2046",
                    "mo2041", "mo2044", "mo2047",
                    "mo2042", "mo2045", "mo2048"
                   ]

        md_list =  ["md2040"]

        out_list = [
                    "mf3350", "mf30351", "mf3352",
                    "mf3353", "mf30354", "mf3355",
                    "mf3356", "mf30357", "mf3358"
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

        MChM.ImpCalc(eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, "mf5130")
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

        HV2+I1 = I1A0_Dict['HOV'][0] + I1A1_Dict['HOV'][0] + I1A2_Dict['HOV'][0]
        HV2+I2 = I2A0_Dict['HOV'][0] + I2A1_Dict['HOV'][0] + I2A2_Dict['HOV'][0]
        HV2+I3 = I3A0_Dict['HOV'][0] + I3A1_Dict['HOV'][0] + I3A2_Dict['HOV'][0]

        Bus  =  I1A0_Dict['WTra'][0] + I1A1_Dict['WTra'][0] + I1A2_Dict['WTra'][0]
        Bus +=  I2A0_Dict['WTra'][0] + I2A1_Dict['WTra'][0] + I2A2_Dict['WTra'][0]
        Bus +=  I3A0_Dict['WTra'][0] + I3A1_Dict['WTra'][0] + I3A2_Dict['WTra'][0]
        Rail =  I1A0_Dict['WTra'][1] + I1A1_Dict['WTra'][1] + I1A2_Dict['WTra'][1]
        Rail += I2A0_Dict['WTra'][1] + I2A1_Dict['WTra'][1] + I2A2_Dict['WTra'][1]
        Rail += I3A0_Dict['WTra'][1] + I3A1_Dict['WTra'][1] + I3A2_Dict['WTra'][1]

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
        util.set_matrix_numpy(eb, "mf3000", SOVI1)
        util.set_matrix_numpy(eb, "mf3001", SOVI2)
        util.set_matrix_numpy(eb, "mf3002", SOVI3)
        util.set_matrix_numpy(eb, "mf3005", HV2I1)
        util.set_matrix_numpy(eb, "mf3006", HV2I2)
        util.set_matrix_numpy(eb, "mf3007", HV2I3)
        util.set_matrix_numpy(eb, "mf3015", Bus)
        util.set_matrix_numpy(eb, "mf3020", Rail)
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
        util.initmat(eb, "mf3305", "HbShHV2+I1PerTrips", "HbSh HV2+ Low Income Per-Trips", 0)
        util.initmat(eb, "mf3306", "HbShHV2+I2PerTrips", "HbSh HV2+ Med Income Per-Trips", 0)
        util.initmat(eb, "mf3307", "HbShHV2+I3PerTrips", "HbSh HV2+ High Income Per-Trips", 0)
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


