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

class HbSchool(_m.Tool()):

    ##Global attribute for Tool Run Message (successful/not successful)
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Home Base School"
        pb.description = "Calculate home base School person trips by mode and time of day"
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

    @_m.logbook_trace("Run Home Base School")
    def __call__(self, eb):
        util = _m.Modeller().tool("translink.emme.util")
        MChM = _m.Modeller().tool("translink.RTM3.testtdmc.ModeChoiceUtils")
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
                     'BRTotLow':10.0,
                     'BRTotHig':120.0,
                     'WCTotLow':30.0,
                     'WCTotHig':130.0,
                     'PRAutTim':0.0
                    }

        # Declare Utilities Data Frame
        DfU = {}

        # Add Coefficients

        p2   = -20.242759
        p4   = -18.940425
        p6   = -20.136158
        p11  =  -3.758208
        p12  =  -1.630150
        p20  =  -7.296188
        p21  =  -6.664596
        p162 =   4.456847
        p163 =  10.673441
        p701 =   0.751139
        p702 =   0.774884
        p900 =   1.424131
        thet =   0.122610


#        ##############################################################################
#        ##       Auto Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        MaxPark = 10.0
        VOC = util.get_matrix_numpy(eb, 'autoOpCost')
        Occ = util.get_matrix_numpy(eb, 'HOVOccHBsch')    # Occ=3.02
        VOT = 4.0 # rs: hard coded

        Df['AutoDisHOV'] = util.get_matrix_numpy(eb, 'HbScBlHovDist')
        Df['AutoTimHOV'] = util.get_matrix_numpy(eb, 'HbScBlHovTime')
        Df['AutoCosHOV'] = (Df['AutoDisHOV']*VOC + util.get_matrix_numpy(eb, 'HbScBlHovToll'))/(Occ*2.0) # students do not pay any cost adjustment

        # Utilities
        # HOV2+
        # HOV2+ Utility across all incomes
        Df['GeUtl'] = (p2
                      + (p12*(VOT*Df['AutoTimHOV']/60+Df['AutoCosHOV'])))
        # Check Availability conditions
        DfU['HOV']  = MChM.AutoAvail(Df['AutoDisHOV'], Df['GeUtl'], AvailDict)

#        ##############################################################################
#        ##       Walk to Transit Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        Tiny=0.000001
        Disc_Fare = 0.85 # Student Fare Discount
        Df['BusIVT'] = util.get_matrix_numpy(eb, 'HbScBlBusIvtt')
        Df['BusWat'] = util.get_matrix_numpy(eb, 'HbScBlBusWait')
        Df['BusAux'] = util.get_matrix_numpy(eb, 'HbScBlBusAux')
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'HbScBlBusBoard')
        Df['BusFar'] = util.get_matrix_numpy(eb, 'HbScBlBusFare')
        Df['BusTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux'] + Df['BusBrd'] # Total Bus Travel Time
        Df['BusFar'] = Df['BusFar'] * Disc_Fare  ## discount fare for students

        Df['RalIVR'] = util.get_matrix_numpy(eb, 'HbScBlRailIvtt')
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'HbScBlRailIvttBus')
        Df['RalWat'] = util.get_matrix_numpy(eb, 'HbScBlRailWait')
        Df['RalAux'] = util.get_matrix_numpy(eb, 'HbScBlRailAux')
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'HbScBlRailBoard')
        Df['RalFar'] = util.get_matrix_numpy(eb, 'HbScBlRailFare')
        Df['RalTot'] = Df['RalIVB'] + Df['RalIVR'] + Df['RalWat'] + Df['RalAux'] + Df['RalBrd'] # Total Bus Travel Time
        Df['RalIBR'] = Df['RalIVB']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Bus IVT to Total Time
        Df['RalIRR'] = Df['RalIVR']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Rail IVT to Total Time
        Df['RalFar'] = Df['RalFar'] * Disc_Fare  ## discount fare for students

        Df['IntZnl'] = np.identity(NoTAZ)
        Df['PopEmpDen'] = util.get_matrix_numpy(eb, 'combinedensln')
        Df['PopEmpDen'] = Df['PopEmpDen'].reshape(NoTAZ, 1) + np.zeros((1, NoTAZ))

        Df['GenCostBus'] = ( Df['BusIVT']
                           + 2.5*Df['BusWat']
                           + 2.0*Df['BusAux']
                           + 10.0*Df['BusBrd'])

        Df['GenCostBus'] = VOT*Df['GenCostBus']/60.0 + Df['BusFar']

        Df['GenCostRal'] = ( Df['RalIVR']
                           + Df['RalIVR']
                           + 2.5*Df['RalWat']
                           + 2.0*Df['RalAux']
                           + 10.0*Df['RalBrd'])

        Df['GenCostRal'] = VOT*Df['GenCostBus']/60.0 + Df['RalFar']


        # Utilities
        # Bus Utility

        Df['GeUtl'] = ( p4
                      + p12*Df['GenCostBus']
                      + p900*Df['PopEmpDen'])

        # Check Availability conditions
        Df['GeUtl'] = MChM.BusAvail(Df, Df['GeUtl'],AvailDict)
        DfU['Bus'] = Df['GeUtl']

        # Rail Utility
        # log(pop+emp) at production zone will be added below
        # Rail Utility across all incomes
        Df['GeUtl'] = ( p4*Df['RalIBR']
                      + p6*Df['RalIRR']
                      + p12*Df['GenCostRal']
                      + p900*Df['PopEmpDen'])

        # Check Availability conditions
        Df['GeUtl'] = MChM.RailAvail(Df, Df['GeUtl'],AvailDict)
        # Add Income parameters
        DfU['Ral'] = Df['GeUtl']

#        ##############################################################################
#        ##       Active Modes
#        ##############################################################################

        Df = {}
        Df['AutoDis'] = util.get_matrix_numpy(eb, 'HbScBlHovDist')
        Df['PopEmpDen'] = util.get_matrix_numpy(eb, 'combinedensln')
        Df['PopEmpDen'] = Df['PopEmpDen'].reshape(NoTAZ, 1) + np.zeros((1, NoTAZ))

        Df['PopEmpDenPA'] = util.get_matrix_numpy(eb, 'combinedens')#Pop+Emp Density at Prod and Attr Zones
        Df['PopEmpDenPA'] = Df['PopEmpDenPA'].reshape(NoTAZ, 1) + Df['PopEmpDenPA'].reshape(1, NoTAZ) #Broadcast Density

        # Walk Utility
        DfU['Walk'] = ( 0
                      + p20*Df['AutoDis']
                      + p701*Df['PopEmpDenPA'])

        # Check Availability conditions
        DfU['Walk'] = MChM.WalkAvail(Df['AutoDis'], DfU['Walk'], AvailDict)

        # Bike Utility
        DfU['Bike'] = ( p11
                      + p21*Df['AutoDis']
                      + p702*Df['PopEmpDen'])

        # Check Availability conditions
        DfU['Bike'] = MChM.BikeAvail(Df['AutoDis'], DfU['Bike'], AvailDict)

        del Df

#        ##############################################################################
#        ##       Calculate Probabilities
#        ##############################################################################

        #############
        # All Incomes
        #############

        ## Zero Autos
        Dict = {
               'HOV'  : [DfU['HOV']],
               'WTra' : [DfU['Bus'], DfU['Ral']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }

        A0_Dict = self.Calc_Prob(eb, Dict, "HbScLSA0", thet)

        ## One Auto
        Dict = {
               'HOV'  : [DfU['HOV'] + p162],
               'WTra' : [DfU['Bus'], DfU['Ral']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }

        A1_Dict = self.Calc_Prob(eb, Dict, "HbScLSA1", thet)

        ## Two Auto
        Dict = {
               'HOV'  : [DfU['HOV'] + p163],
               'WTra' : [DfU['Bus'], DfU['Ral']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }

        A2_Dict = self.Calc_Prob(eb, Dict, "HbScLSA2", thet)

#       ##############################################################################
#        ##       Trip Distribution
#       ##############################################################################

        Logsum =  [
                  "HbScLSA0", "HbScLSA1", "HbScLSA2",
                  "HbScLSA0", "HbScLSA1", "HbScLSA2",
                  "HbScLSA0", "HbScLSA1", "HbScLSA2"
                   ]

        imp_list = [
                  "P-AFrictionFact1", "P-AFrictionFact2", "P-AFrictionFact3",
                  "P-AFrictionFact4", "P-AFrictionFact5", "P-AFrictionFact6",
                  "P-AFrictionFact7", "P-AFrictionFact8", "P-AFrictionFact9"
                   ]

        mo_list =  [
                    "hbschInc1Au0prd", "hbschInc1Au1prd", "hbschInc1Au2prd",
                    "hbschInc2Au0prd", "hbschInc2Au1prd", "hbschInc2Au2prd",
                    "hbschInc3Au0prd", "hbschInc3Au1prd", "hbschInc3Au2prd"
                   ]

        md_list =  ["hbschatr"]

        out_list = [
                    "HbScP-AI1A0", "HbScP-AI1A1", "HbScP-AI1A2",
                    "HbScP-AI2A0", "HbScP-AI2A1", "HbScP-AI2A2",
                    "HbScP-AI3A0", "HbScP-AI3A1", "HbScP-AI3A2"
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
        MChM.ImpCalc(eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, util.get_matrix_numpy(eb, "HbScBlSovDist"))
        MChM.two_dim_matrix_balancing(eb, mo_list, md_list, imp_list, out_list, Dist_Iter)

#       ##############################################################################
#        ##       Calculate Demand
#       ##############################################################################

        I1A0_Dict = self.Calc_Demand(A0_Dict, util.get_matrix_numpy(eb,"HbScP-AI1A0"))
        I1A1_Dict = self.Calc_Demand(A1_Dict, util.get_matrix_numpy(eb,"HbScP-AI1A1"))
        I1A2_Dict = self.Calc_Demand(A2_Dict, util.get_matrix_numpy(eb,"HbScP-AI1A2"))
        I2A0_Dict = self.Calc_Demand(A0_Dict, util.get_matrix_numpy(eb,"HbScP-AI2A0"))
        I2A1_Dict = self.Calc_Demand(A1_Dict, util.get_matrix_numpy(eb,"HbScP-AI2A1"))
        I2A2_Dict = self.Calc_Demand(A2_Dict, util.get_matrix_numpy(eb,"HbScP-AI2A2"))
        I3A0_Dict = self.Calc_Demand(A0_Dict, util.get_matrix_numpy(eb,"HbScP-AI3A0"))
        I3A1_Dict = self.Calc_Demand(A1_Dict, util.get_matrix_numpy(eb,"HbScP-AI3A1"))
        I3A2_Dict = self.Calc_Demand(A2_Dict, util.get_matrix_numpy(eb,"HbScP-AI3A2"))

        # Auto Trips
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

        del A0_Dict,   A1_Dict,   A2_Dict
        del I1A0_Dict, I1A1_Dict, I1A2_Dict
        del I2A0_Dict, I2A1_Dict, I2A2_Dict
        del I3A0_Dict, I3A1_Dict, I3A2_Dict

#       ##############################################################################
#        ##       Set Demand Matrices
#       ##############################################################################
        util.set_matrix_numpy(eb, "HbScHV2+I1PerTrips", HOVI1)
        util.set_matrix_numpy(eb, "HbScHV2+I2PerTrips", HOVI2)
        util.set_matrix_numpy(eb, "HbScHV2+I3PerTrips", HOVI3)
        util.set_matrix_numpy(eb, "HbScBusPerTrips", Bus)
        util.set_matrix_numpy(eb, "HbScRailPerTrips", Rail)
        util.set_matrix_numpy(eb, "HbScWalkPerTrips", Walk)
        util.set_matrix_numpy(eb, "HbScBikePerTrips", Bike)


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
        util.initmat(eb, "mf9020", "HbScLSA0", " HbSc LogSum A0", 0)
        util.initmat(eb, "mf9021", "HbScLSA1", " HbSc LogSum A1", 0)
        util.initmat(eb, "mf9022", "HbScLSA2", " HbSc LogSum A2", 0)


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
        util.initmat(eb, "mf3205", "HbScHV2+I1PerTrips", "HbSc HV2+ Low Income Per-Trips", 0)
        util.initmat(eb, "mf3206", "HbScHV2+I2PerTrips", "HbSc HV2+ Med Income Per-Trips", 0)
        util.initmat(eb, "mf3207", "HbScHV2+I3PerTrips", "HbSc HV2+ High Income Per-Trips", 0)
        util.initmat(eb, "mf3215", "HbScBusPerTrips", "HbSc Bus Per-Trips", 0)
        util.initmat(eb, "mf3220", "HbScRailPerTrips", "HbSc Rail Per-Trips", 0)
        util.initmat(eb, "mf3230", "HbScWalkPerTrips", "HbSc Walk Per-Trips", 0)
        util.initmat(eb, "mf3235", "HbScBikePerTrips", "HbSc Bike Per-Trips", 0)

        ## Initialize P-A Trip Tables from trip distribution
        util.initmat(eb, "mf3250", "HbScP-AI1A0", " HbSc P-A Trips I1 A0", 0)
        util.initmat(eb, "mf3251", "HbScP-AI1A1", " HbSc P-A Trips I1 A1", 0)
        util.initmat(eb, "mf3252", "HbScP-AI1A2", " HbSc P-A Trips I1 A2", 0)
        util.initmat(eb, "mf3253", "HbScP-AI2A0", " HbSc P-A Trips I1 A0", 0)
        util.initmat(eb, "mf3254", "HbScP-AI2A1", " HbSc P-A Trips I1 A1", 0)
        util.initmat(eb, "mf3255", "HbScP-AI2A2", " HbSc P-A Trips I1 A2", 0)
        util.initmat(eb, "mf3256", "HbScP-AI3A0", " HbSc P-A Trips I1 A0", 0)
        util.initmat(eb, "mf3257", "HbScP-AI3A1", " HbSc P-A Trips I1 A1", 0)
        util.initmat(eb, "mf3258", "HbScP-AI3A2", " HbSc P-A Trips I1 A2", 0)



