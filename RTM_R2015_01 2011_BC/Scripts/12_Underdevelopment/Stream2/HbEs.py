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

class HbEscorting(_m.Tool()):

    ##Global attribute for Tool Run Message (successful/not successful)
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Home Base Escorting"
        pb.description = "Calculate home base escorting person trips by mode and time of day"
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

    @_m.logbook_trace("Run Home Base Escorting")
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
                     'BRTotHig': 90.0,
                     'WCTotLow': 30.0,
                     'WCTotHig': 130.0,
                     'PRAutTim': 0.0
                    }

        # Declare Utilities Data Frame
        DfU = {}

        # Add Coefficients
        p4   =  -5.720349
        p6   =  -1.360171
        p10  =   2.719601
        p11  =   0.027666
        p14  =  -1.038357
        p20  =  -4.524711
        p160 =   3.293559
        p161 =   5.446370
        thet =   0.263368
#        ##############################################################################
#        ##       Auto Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        MaxPark = 10.0
        VOT = 8.0
        VOC = util.get_matrix_numpy(eb, 'autoOpCost')
        Occ = util.get_matrix_numpy(eb, 'HOVOccHbesc')
        Df['ParkCost'] = util.get_matrix_numpy(eb, 'prk2hr')  # 2 hour parking
        Df['ParkCost'][Df['ParkCost']>MaxPark] = MaxPark
        Df['ParkCost'] = Df['ParkCost'].reshape(1, NoTAZ) + np.zeros((NoTAZ, 1))

        Df['AutoDisHOV'] = util.get_matrix_numpy(eb, 'HbEsBlHovDist')
        Df['AutoTimHOV'] = util.get_matrix_numpy(eb, 'HbEsBlHovTime')
        Df['AutoCosHOV'] = Df['AutoDisHOV']*VOC + util.get_matrix_numpy(eb, 'HbEsBlHovToll') + Df['ParkCost']
        Df['GenCostAuto']= Df['AutoCosHOV']/Occ + VOT*Df['AutoTimHOV']/60.0

        # Utilities
        # Auto
        # Auto Utility across all incomes
        DfU['Auto'] = ( 0
                      + p14*Df['GenCostAuto'])


#        ##############################################################################
#        ##       Walk to Transit Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        Tiny=0.000001
        Df['BusIVT'] = util.get_matrix_numpy(eb, 'HbEsBlBusIvtt')
        Df['BusWat'] = util.get_matrix_numpy(eb, 'HbEsBlBusWait')
        Df['BusAux'] = util.get_matrix_numpy(eb, 'HbEsBlBusAux')
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'HbEsBlBusBoard')
        Df['BusFar'] = util.get_matrix_numpy(eb, 'HbEsBlBusFare')
        Df['BusTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux'] + Df['BusBrd'] # Total Bus Travel Time

        Df['RalIVR'] = util.get_matrix_numpy(eb, 'HbPbBlRailIvtt')
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'HbPbBlRailIvttBus')
        Df['RalWat'] = util.get_matrix_numpy(eb, 'HbPbBlRailWait')
        Df['RalAux'] = util.get_matrix_numpy(eb, 'HbPbBlRailAux')
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'HbPbBlRailBoard')
        Df['RalFar'] = util.get_matrix_numpy(eb, 'HbPbBlRailFare')
        Df['RalTot'] = Df['RalIVB'] + Df['RalIVR'] + Df['RalWat'] + Df['RalAux'] + Df['RalBrd'] # Total Bus Travel Time
        Df['RalIBR'] = Df['RalIVB']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Bus IVT to Total Time
        Df['RalIRR'] = Df['RalIVR']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Rail IVT to Total Time

        Df['IntZnl'] = np.identity(NoTAZ)

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
        # Bus Utility across all incomes
        Df['GeUtl'] = ( p4
                      + p14*Df['GenCostBus'])

        # Check Availability conditions
        Df['GeUtl'] = MChM.BusAvail(Df, Df['GeUtl'], AvailDict)

        DfU['Bus'] = Df['GeUtl']

        # Rail Utility
        # Rail Utility across all incomes
        Df['GeUtl'] = ( p4*Df['RalIBR']
                      + p6*Df['RalIRR']
                      + p14*Df['GenCostRal'])
        # Check Availability conditions
        Df['GeUtl'] = MChM.RailAvail(Df, Df['GeUtl'],AvailDict)
        # Add Income parameters
        DfU['Ral'] = Df['GeUtl']

#        ##############################################################################
#        ##       Active Modes
#        ##############################################################################

        Df = {}
        Df['AutoDis'] = util.get_matrix_numpy(eb, 'HbEsBlSovDist')


        # Walk Utility
        DfU['Walk'] = ( p10
                      + p20*Df['AutoDis'])

        # Check Availability conditions
        DfU['Walk'] = MChM.WalkAvail(Df['AutoDis'], DfU['Walk'], AvailDict)

        # Bike Utility
        DfU['Bike'] = ( p11
                      + p20*Df['AutoDis'])

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
               'Auto'  : [DfU['Auto']],
               'WTra' : [DfU['Bus'], DfU['Ral']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }

        A0_Dict = self.Calc_Prob(eb, Dict, "HbEsLSA0", thet)

        ## One Auto
        Dict = {
               'Auto'  : [DfU['Auto'] + p160],
               'WTra' : [DfU['Bus'], DfU['Ral']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }

        A1_Dict = self.Calc_Prob(eb, Dict, "HbEsLSA1", thet)

        ## Two Auto
        Dict = {
               'Auto'  : [DfU['Auto'] + p161],
               'WTra' : [DfU['Bus'], DfU['Ral']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }

        A2_Dict = self.Calc_Prob(eb, Dict, "HbEsLSA2", thet)

#
#       ##############################################################################
#        ##       Trip Distribution
#       ##############################################################################

        Logsum =  [
                  "HbEsLSA0", "HbEsLSA1", "HbEsLSA2",
                  "HbEsLSA0", "HbEsLSA1", "HbEsLSA2",
                  "HbEsLSA0", "HbEsLSA1", "HbEsLSA2"
                   ]

        imp_list = [
                  "P-AFrictionFact1", "P-AFrictionFact2", "P-AFrictionFact3",
                  "P-AFrictionFact4", "P-AFrictionFact5", "P-AFrictionFact6",
                  "P-AFrictionFact7", "P-AFrictionFact8", "P-AFrictionFact9"
                   ]

        mo_list =  [
                    "hbescInc1Au0prd", "hbescInc1Au1prd", "hbescInc1Au2prd",
                    "hbescInc2Au0prd", "hbescInc2Au1prd", "hbescInc2Au2prd",
                    "hbescInc3Au0prd", "hbescInc3Au1prd", "hbescInc3Au2prd"
                   ]

        md_list =  ["hbescatr"]

        out_list = [
                    "HbEsP-AI1A0", "HbEsP-AI1A1", "HbEsP-AI1A2",
                    "HbEsP-AI2A0", "HbEsP-AI2A1", "HbEsP-AI2A2",
                    "HbEsP-AI3A0", "HbEsP-AI3A1", "HbEsP-AI3A2"
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
        MChM.ImpCalc(eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, util.get_matrix_numpy(eb, "HbEsBlSovDist"))
        MChM.two_dim_matrix_balancing(eb, mo_list, md_list, imp_list, out_list, Dist_Iter)


#       ##############################################################################
#        ##       Calculate Demand
#       ##############################################################################

        I1A0_Dict = self.Calc_Demand(A0_Dict, util.get_matrix_numpy(eb,"HbEsP-AI1A0"))
        I1A1_Dict = self.Calc_Demand(A1_Dict, util.get_matrix_numpy(eb,"HbEsP-AI1A1"))
        I1A2_Dict = self.Calc_Demand(A2_Dict, util.get_matrix_numpy(eb,"HbEsP-AI1A2"))
        I2A0_Dict = self.Calc_Demand(A0_Dict, util.get_matrix_numpy(eb,"HbEsP-AI2A0"))
        I2A1_Dict = self.Calc_Demand(A1_Dict, util.get_matrix_numpy(eb,"HbEsP-AI2A1"))
        I2A2_Dict = self.Calc_Demand(A2_Dict, util.get_matrix_numpy(eb,"HbEsP-AI2A2"))
        I3A0_Dict = self.Calc_Demand(A0_Dict, util.get_matrix_numpy(eb,"HbEsP-AI3A0"))
        I3A1_Dict = self.Calc_Demand(A1_Dict, util.get_matrix_numpy(eb,"HbEsP-AI3A1"))
        I3A2_Dict = self.Calc_Demand(A2_Dict, util.get_matrix_numpy(eb,"HbEsP-AI3A2"))

        # Auto Trips
        AutoI1 = I1A0_Dict['Auto'][0] + I1A1_Dict['Auto'][0] + I1A2_Dict['Auto'][0]
        AutoI2 = I2A0_Dict['Auto'][0] + I2A1_Dict['Auto'][0] + I2A2_Dict['Auto'][0]
        AutoI3 = I3A0_Dict['Auto'][0] + I3A1_Dict['Auto'][0] + I3A2_Dict['Auto'][0]

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
        util.set_matrix_numpy(eb, "HbEsSOVI1PerTrips", AutoI1)
        util.set_matrix_numpy(eb, "HbEsSOVI2PerTrips", AutoI2)
        util.set_matrix_numpy(eb, "HbEsSOVI3PerTrips", AutoI3)
        util.set_matrix_numpy(eb, "HbEsBusPerTrips", Bus)
        util.set_matrix_numpy(eb, "HbEsRailPerTrips", Rail)
        util.set_matrix_numpy(eb, "HbEsWalkPerTrips", Walk)
        util.set_matrix_numpy(eb, "HbEsBikePerTrips", Bike)


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
        util.initmat(eb, "mf9060", "HbEsLSA0", " HbEs LogSum A0", 0)
        util.initmat(eb, "mf9061", "HbEsLSA1", " HbEs LogSum A1", 0)
        util.initmat(eb, "mf9062", "HbEsLSA2", " HbEs LogSum A2", 0)

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
        util.initmat(eb, "mf3600", "HbEsSOVI1PerTrips", "HbEs SOV Low Income Per-Trips", 0)
        util.initmat(eb, "mf3601", "HbEsSOVI2PerTrips", "HbEs SOV Med Income Per-Trips", 0)
        util.initmat(eb, "mf3602", "HbEsSOVI3PerTrips", "HbEs SOV High Income Per-Trips", 0)
        util.initmat(eb, "mf3605", "HbEsHV2+I1PerTrips", "HbEs HV2+ Low Income Per-Trips", 0)
        util.initmat(eb, "mf3606", "HbEsHV2+I2PerTrips", "HbEs HV2+ Med Income Per-Trips", 0)
        util.initmat(eb, "mf3607", "HbEsHV2+I3PerTrips", "HbEs HV2+ High Income Per-Trips", 0)
        util.initmat(eb, "mf3615", "HbEsBusPerTrips", "HbEs Bus Per-Trips", 0)
        util.initmat(eb, "mf3620", "HbEsRailPerTrips", "HbEs Rail Per-Trips", 0)
        util.initmat(eb, "mf3630", "HbEsWalkPerTrips", "HbEs Walk Per-Trips", 0)
        util.initmat(eb, "mf3635", "HbEsBikePerTrips", "HbEs Bike Per-Trips", 0)

        ## Initialize P-A Trip Tables from trip distribution
        util.initmat(eb, "mf3650", "HbEsP-AI1A0", " HbEs P-A Trips I1 A0", 0)
        util.initmat(eb, "mf3651", "HbEsP-AI1A1", " HbEs P-A Trips I1 A1", 0)
        util.initmat(eb, "mf3652", "HbEsP-AI1A2", " HbEs P-A Trips I1 A2", 0)
        util.initmat(eb, "mf3653", "HbEsP-AI2A0", " HbEs P-A Trips I1 A0", 0)
        util.initmat(eb, "mf3654", "HbEsP-AI2A1", " HbEs P-A Trips I1 A1", 0)
        util.initmat(eb, "mf3655", "HbEsP-AI2A2", " HbEs P-A Trips I1 A2", 0)
        util.initmat(eb, "mf3656", "HbEsP-AI3A0", " HbEs P-A Trips I1 A0", 0)
        util.initmat(eb, "mf3657", "HbEsP-AI3A1", " HbEs P-A Trips I1 A1", 0)
        util.initmat(eb, "mf3658", "HbEsP-AI3A2", " HbEs P-A Trips I1 A2", 0)












































