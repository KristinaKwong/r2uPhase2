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

class Non_hbwork(_m.Tool()):

    ##Global attribute for Tool Run Message (successful/not successful)
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Non-home base Other"
        pb.description = "Calculate non-home base other trips by mode and time of day"
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

    @_m.logbook_trace("Run Non-home base other")
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
                     'BRTotLow': 10.0,
                     'BRTotHig': 120.0,
                     'WCTotLow': 30.0,
                     'WCTotHig': 130.0,
                     'PRAutTim': 0.0
                    }

        # Declare Utilities Data Frame
        DfU = {}

        # Add Coefficients

        p4   =  -2.215763
        p6   =  -1.388479
        p10  =  -2.591491
        p11  =  -7.296778
        p12  =  -0.609932
        p15  =  -0.037342
        p17  =  -0.102264
        p18  =  -0.064987
        p19  =  -0.591899
        p20  =  -1.491104
        p21  =  -0.610183
        p700 =   0.246500
        p701 =   0.450339
        p870 =   0.849681
        thet =   0.669384

#        ##############################################################################
#        ##       Auto Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        MaxPark = 10.0

        VOC = util.get_matrix_numpy(eb, 'autoOpCost')
        Occ = util.get_matrix_numpy(eb, 'HOVOccNHBo')
        Df['ParkCost'] = util.get_matrix_numpy(eb, 'prk2hr')  # 2 hour parking

        Df['ParkCost'] = Df['ParkCost'].reshape(1, NoTAZ) + np.zeros((NoTAZ, 1))


        Df['AutoDisHOV'] = util.get_matrix_numpy(eb, 'NHbOBlHovDist')
        Df['AutoTimHOV'] = util.get_matrix_numpy(eb, 'NHbOBlHovTime')
        Df['AutoCosHOV'] = Df['AutoDisHOV']*VOC + util.get_matrix_numpy(eb, 'NHbOBlHovToll') + Df['ParkCost']

        # Auto Utility across all incomes
        Df['GeUtl'] = ( 0.0
                      + p12*Df['AutoCosHOV']/Occ
                      + p15*Df['AutoTimHOV'])
        # Check Availability conditions
        Df['GeUtl']  = MChM.AutoAvail(Df['AutoDisHOV'], Df['GeUtl'], AvailDict)
        # Add Income parameters
        DfU['Auto'] = Df['GeUtl']

#        ##############################################################################
#        ##       Walk to Transit Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        Tiny=0.000001
        Df['BusIVT'] = util.get_matrix_numpy(eb, 'NHbOBlBusIvtt')
        Df['BusWat'] = util.get_matrix_numpy(eb, 'NHbOBlBusWait')
        Df['BusAux'] = util.get_matrix_numpy(eb, 'NHbOBlBusAux')
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'NHbOBlBusBoard')
        Df['BusFar'] = util.get_matrix_numpy(eb, 'NHbOBlBusFare')
        Df['BusTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux'] + Df['BusBrd'] # Total Bus Travel Time

        Df['RalIVR'] = util.get_matrix_numpy(eb, 'NHbOBlRailIvtt')
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'NHbOBlRailIvttBus')
        Df['RalWat'] = util.get_matrix_numpy(eb, 'NHbOBlRailWait')
        Df['RalAux'] = util.get_matrix_numpy(eb, 'NHbOBlRailAux')
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'NHbOBlRailBoard')
        Df['RalFar'] = util.get_matrix_numpy(eb, 'NHbOBlRailFare')
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
                      + p12*Df['BusFar']
                      + p15*Df['BusIVT']
                      + p17*Df['BusWat']
                      + p18*Df['BusAux']
                      + p19*Df['BusBrd']
                      + p700*Df['PopEmpDen'])

        # Check Availability conditions
        Df['GeUtl'] = MChM.BusAvail(Df, Df['GeUtl'], AvailDict)
        DfU['Bus'] = Df['GeUtl']

        # Rail Utility
        # Rail Utility across all incomes
        Df['GeUtl'] = ( p4*Df['RalIBR']
                      + p6*Df['RalIRR']
                      + p12*Df['RalFar']
                      + p15*Df['RalIVB']
                      + p15*Df['RalIVR']
                      + p17*Df['RalWat']
                      + p18*Df['RalAux']
                      + p19*Df['RalBrd']
                      + p700*Df['PopEmpDen'])
        # Check Availability conditions
        Df['GeUtl'] = MChM.RailAvail(Df, Df['GeUtl'],AvailDict)
        DfU['Ral'] = Df['GeUtl']

#        ##############################################################################
#        ##       Active Modes
#        ##############################################################################

        Df = {}
        Df['AutoDis'] = util.get_matrix_numpy(eb, 'NHbOBlSovDist')

        Df['PopEmpDenPA'] = util.get_matrix_numpy(eb, 'combinedens')#Pop+Emp Density at Prod and Attr Zones
        Df['PopEmpDenPA'] = Df['PopEmpDenPA'].reshape(NoTAZ, 1) + Df['PopEmpDenPA'].reshape(1, NoTAZ) #Broadcast Density

        Df['BikScr'] = util.get_matrix_numpy(eb, 'bikeskim') # Bike Score

        # Walk Utility
        DfU['Walk'] = ( p10
                      + p20*Df['AutoDis']
                      + p701*Df['PopEmpDenPA'])
        # Check Availability conditions
        DfU['Walk'] = MChM.WalkAvail(Df['AutoDis'], DfU['Walk'], AvailDict)

        # Bike Utility
        DfU['Bike'] = ( p11
                      + p21*Df['AutoDis']
                      + p870*Df['BikScr'])
        # Check Availability conditions
        DfU['Bike'] = MChM.BikeAvail(Df['AutoDis'], DfU['Bike'], AvailDict)

        del Df

#        ##############################################################################
#        ##       Calculate Probabilities
#        ##############################################################################

        # All Incomes All Autos
        Dict = {
               'Auto'  : [DfU['Auto']],
               'WTra' : [DfU['Bus'], DfU['Ral']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }

        Prob_Dict = self.Calc_Prob(eb, Dict, "NHbOLS", thet)
        del DfU, Dict
#
       ##############################################################################
        ##       Trip Distribution
       ##############################################################################

        Logsum =  ["NHbOLS"]

        imp_list = ["P-AFrictionFact1"]

        mo_list =  ["nhboprd"]

        md_list =  ["nhboatr"]

        out_list = ["NHbOP-A"]

        LS_Coeff = 0.5

        LambdaList = [-0.2]

        AlphaList =  [0.02]

        GammaList =  [-0.0004]

        Dist_Iter = int(util.get_matrix_numpy(eb, 'IterDist'))
        MChM.ImpCalc(eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, util.get_matrix_numpy(eb, "NHbOBlSovDist"))
        MChM.two_dim_matrix_balancing(eb, mo_list, md_list, imp_list, out_list, Dist_Iter)


#       ##############################################################################
#        ##       Calculate Demand
#       ##############################################################################

        Demand_Dict = self.Calc_Demand(Prob_Dict, util.get_matrix_numpy(eb,"NHbOP-A"))


        Auto =   Demand_Dict['Auto'][0]

        Bus  =  Demand_Dict['WTra'][0]

        Rail =  Demand_Dict['WTra'][1]

        Walk =  Demand_Dict['Acti'][0]

        Bike =  Demand_Dict['Acti'][1]


        del Demand_Dict
        del Prob_Dict

#       ##############################################################################
#        ##       Set Demand Matrices
#       ##############################################################################

        util.set_matrix_numpy(eb, "NHbOHV2+PerTrips", Auto)
        util.set_matrix_numpy(eb, "NHbOBusPerTrips", Bus)
        util.set_matrix_numpy(eb, "NHbORailPerTrips", Rail)
        util.set_matrix_numpy(eb, "NHbOWalkPerTrips", Walk)
        util.set_matrix_numpy(eb, "NHbOBikePerTrips", Bike)

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

    @_m.logbook_trace("Initialize Matrices")
    def matrix_batchins(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        ## Initialze Logsum Matrices
        util.initmat(eb, "mf9080", "NHbOLS", " NHbO LogSum", 0)

        ## Initialze Friction Factor Matrices
        util.initmat(eb, "mf9100", "P-AFrictionFact1", "Trip Distribution Friction Factor 1", 0)

        ## Initialize P-A Trip Tables by mode
        util.initmat(eb, "mf3800", "NHbOSOVPerTrips",  "NHbO SOV Per-Trips", 0)
        util.initmat(eb, "mf3805", "NHbOHV2+PerTrips", "NHbO HV2+ Per-Trips", 0)
        util.initmat(eb, "mf3815", "NHbOBusPerTrips",  "NHbO Bus Per-Trips", 0)
        util.initmat(eb, "mf3820", "NHbORailPerTrips", "NHbO Rail Per-Trips", 0)
        util.initmat(eb, "mf3830", "NHbOWalkPerTrips", "NHbO Walk Per-Trips", 0)
        util.initmat(eb, "mf3835", "NHbOBikePerTrips", "NHbO Bike Per-Trips", 0)

        ## Initialize P-A Trip Tables from trip distribution
        util.initmat(eb, "mf3850", "NHbOP-A", " NHbO P-A Trips ", 0)