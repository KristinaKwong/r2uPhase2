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
        pb.title = "Home Base University"
        pb.description = "Calculate home base University person trips by mode and time of day"
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

    @_m.logbook_trace("Run Home Base University")
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
                     'AutDist ': 0.0,
                     'WlkDist ': 5.0,
                     'BikDist ': 20.0,
                     'TranIVT ': 1.0,
                     'TranWat ': 20.0,
                     'TranAux ': 40.0,
                     'WCEWat ' : 30.0,
                     'WCEAux ' : 40.0,
                     'TranBrd ': 4.0,
                     'BRTotLow': 10.0,
                     'BRTotHig': 120.0,
                     'WCTotLow': 30.0,
                     'WCTotHig': 130.0,
                     'PRAutTim': 0.0
                    }

        # Declare Utilities Data Frame
        DfU = {}
        # Add Coefficients
		p2   = -2.778773
		p4   =  4.232185
		p6   =  5.306844
		p10  =  5.459996
		p11  = -0.798531
		p12  = -0.620939
		p15  = -0.070561
		p17  = -0.148509
		p18  = -0.103273
		p19  = -0.824006
		p20  = -3.055662
		p21  = -1.189485
		thet =  0.296057

#        ##############################################################################
#        ##       Auto Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        MaxPark = 10.0
        VOC = util.get_matrix_numpy(eb, 'autoOpCost')

		##
        Occ = util.get_matrix_numpy(eb, 'HOVOccHbu')
        Df['ParkCost'] = util.get_matrix_numpy(eb, 'mo61') # 8 hr parking
        Df['ParkCost'][Df['ParkCost']>MaxPark] = MaxPark
        Df['ParkCost'] = Df['ParkCost'].reshape(1, NoTAZ) + np.zeros((NoTAZ, 1))

		##
        Df['AutoDisSOV'] = util.get_matrix_numpy(eb, 'HbUBlSovDist')
        Df['AutoTimSOV'] = util.get_matrix_numpy(eb, 'HbUBlSovTime')
        Df['AutoCosSOV'] = Df['AutoDisSOV']*VOC + util.get_matrix_numpy(eb, 'HbUBlSovToll') + Df['ParkCost']

        Df['AutoDisHOV'] = util.get_matrix_numpy(eb, 'HbUBlHovDist')
        Df['AutoTimHOV'] = util.get_matrix_numpy(eb, 'HbUBlHovTime')
        Df['AutoCosHOV'] = Df['AutoDisHOV']*VOC + util.get_matrix_numpy(eb, 'HbUBlHovToll') + Df['ParkCost']

        # Utilities
        # SOV
        # SOV Utility for all incomes
        Df['GeUtl'] = (0
                      + p15*Df['AutoTimSOV']
                      + p12*Df['AutoCosSOV'])

        # Check SOV Availability
		Df['GeUtl']  = MChM.AutoAvail(Df['AutoDisSOV'], Df['GeUtl'], AvailDict)

		DfU['SOV'] = Df['GeUtl']

        ## 	HOV - 2 and more persons
        # HOV
        # HOV Utility for all incomes

        Df['GeUtl'] = (p2
                      + p15*Df['AutoTimHOV']
                      + p12*Df['AutoCosHOV]/Occ

        # Check HOV Availability
		Df['GeUtl']  = MChM.AutoAvail(Df['AutoDisHOV'], Df['GeUtl'], AvailDict)
		DfU['HOV'] = Df['GeUtl']

#        ##############################################################################
#        ##       Walk to Transit Modes
#        ##############################################################################
        # Generate Dataframe
        Df = {}
        Tiny=0.000001
		##
		##	Bus and rail related variables for University purpose
		##
        Df['BusIVT'] = util.get_matrix_numpy(eb, 'HbUBlBusIvtt')
        Df['BusWat'] = util.get_matrix_numpy(eb, 'HbUBlBusWait')
        Df['BusAux'] = util.get_matrix_numpy(eb, 'HbUBlBusAux')
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'HbUBlBusBoard')
        Df['BusFar'] = util.get_matrix_numpy(eb, 'HbUBlBusFare')
        Df['BusTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux'] + Df['BusBrd'] # Bus Total Travel Time

        Df['RalIVR'] = util.get_matrix_numpy(eb, 'HbUBlRailIvtt')
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'HbUBlRailIvttBus')
        Df['RalWat'] = util.get_matrix_numpy(eb, 'HbUBlRailWait')
        Df['RalAux'] = util.get_matrix_numpy(eb, 'HbUBlRailAux')
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'HbUBlRailBoard')
        Df['RalFar'] = util.get_matrix_numpy(eb, 'HbUBlRailFare')

        Df['RalTot'] = Df['RalIVB'] + Df['RalIVR'] + Df['RalWat'] + Df['RalAux'] + Df['RalBrd'] # Bus Total Travel Time
        Df['RalIBR'] = Df['RalIVB']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Bus IVT to Total Time
        Df['RalIRR'] = Df['RalIVR']/(Df['RalIVB'] + Df['RalIVR'] + Tiny) # Ratio of Rail IVT to Total Time

        Df['TranAccess'] = util.get_matrix_numpy(eb, 'transitAccLn').reshape(NoTAZ,1) + np.zeros((1, NoTAZ))
        Df['IntZnl'] = np.identity(NoTAZ)

        # Utilities
        # Bus Utility
        # Bus Utility for all incomes
        Df['GeUtl'] = ( p4
                      + p12*Df['BusFar']
                      + p15*Df['BusIVT']
                      + p17*Df['BusWat']
                      + p18*Df['BusAux']
                      + p19*Df['BusBrd'])
        # Check Bus Availability
        Df['GeUtl'] = MChM.BusAvail(Df, Df['GeUtl'], AvailDict)
        DfU['Bus'] = Df['GeUtl']

        # 	Rail Utility
		##
        Df['GeUtl'] = ( p4*Df['RalIBR']
                      + p6*Df['RalIRR']
					  + p12*Df['RalFar']
                      + p15*Df['RalIVB']
                      + p15*Df['RalIVR']
                      + p17*Df['RalWat']
                      + p18*Df['RalAux']
                      + p19*Df['RalBrd'])

        # Check Rail Availability
        Df['GeUtl'] = MChM.RailAvail(Df, Df['GeUtl'],AvailDict)
        DfU['Ral'] = (Df['GeUtl']

#        ##############################################################################
#        ##
#        ##		Active Modes
#        ##		rs: HbU SOV distance is used.
#        ##
#        ##############################################################################

		Df = {}
        Df['AutoDis'] = util.get_matrix_numpy(eb, 'HbUBlSovDist')

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
        ## Add SOV Availability Term

        CarShare = util.get_matrix_numpy(eb, 'cs500').reshape(NoTAZ,1) + np.zeros((1, NoTAZ))
        LrgU     = -99999.0
        ## Low Income Zero Autos
        Dict = {
               'SOV'  : [np.where(CarShare>0, DfU['SOV'], LrgU)],
               'HOV'  : [DfU['HOV']],
               'WTra' : [DfU['Bus'], DfU['Ral']],
               'Acti' : [DfU['Walk'], DfU['Bike']]
               }

       Prob_Dict = self.Calc_Prob(eb, Dict, "HbULS", thet)

        del DfU, Dict

       ##############################################################################
        ##       Trip Distribution
       ##############################################################################

        Logsum =  ["HbULS"]

        imp_list = ["P-AFrictionFact1"]

        mo_list =  ["hbuprd"]

        md_list =  ["hbuatr"]

        out_list = ["HbUP-A"]

        LS_Coeff = 0.5

        LambdaList = [-0.2]

        AlphaList =  [0.02]

        GammaList =  [-0.0004]

        Dist_Iter = int(util.get_matrix_numpy(eb, 'IterDist'))
        MChM.ImpCalc(eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, "HbUBlSovDist")
        MChM.two_dim_matrix_balancing(eb, mo_list, md_list, imp_list, out_list, Dist_Iter)


#       ##############################################################################
#        ##       Calculate Demand
#       ##############################################################################

        Demand_Dict = self.Calc_Demand(Prob_Dict, util.get_matrix_numpy(eb,"HbUP-A"))


        SOV =   Demand_Dict['SOV'][0]  + Demand_Dict['SOV'][0]  + Demand_Dict['SOV'][0]

        HOV =   Demand_Dict['HOV'][0]  + Demand_Dict['HOV'][0]  + Demand_Dict['HOV'][0]

        Bus  =  Demand_Dict['WTra'][0] + Demand_Dict['WTra'][0] + Demand_Dict['WTra'][0]

        Rail =  Demand_Dict['WTra'][1] + Demand_Dict['WTra'][1] + Demand_Dict['WTra'][1]

        Walk =  Demand_Dict['Acti'][0] + Demand_Dict['Acti'][0] + Demand_Dict['Acti'][0]

        Bike =  Demand_Dict['Acti'][1] + Demand_Dict['Acti'][1] + Demand_Dict['Acti'][1]


        del Demand_Dict
        del Prob_Dict

#       ##############################################################################
#        ##       Set Demand Matrices
#       ##############################################################################
        util.set_matrix_numpy(eb, "HbUSOVPerTrips", SOV)
        util.set_matrix_numpy(eb, "HbUHV2+PerTrips", HOV)
        util.set_matrix_numpy(eb, "HbUBusPerTrips", Bus)
        util.set_matrix_numpy(eb, "HbURailPerTrips", Rail)
        util.set_matrix_numpy(eb, "HbUWalkPerTrips", Walk)
        util.set_matrix_numpy(eb, "HbUBikePerTrips", Bike)

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
        util.initmat(eb, "mf9010", "HbULS", " HbU LogSum ", 0)

        ## Initialze Friction Factor Matrices
        util.initmat(eb, "mf9100", "P-AFrictionFact1", "Trip Distribution Friction Factor 1", 0)

        ## Initialize P-A Trip Tables by mode
        util.initmat(eb, "mf3100", "HbUSOVPerTrips", "HbU SOV Per-Trips", 0)
        util.initmat(eb, "mf3105", "HbUHV2+PerTrips", "HbU HV2+ Per-Trips", 0)
        util.initmat(eb, "mf3115", "HbUBusPerTrips", "HbU Bus Per-Trips", 0)
        util.initmat(eb, "mf3120", "HbURailPerTrips", "HbU Rail Per-Trips", 0)
        util.initmat(eb, "mf3130", "HbUWalkPerTrips", "HbU Walk Per-Trips", 0)
        util.initmat(eb, "mf3135", "HbUBikePerTrips", "HbU Bike Per-Trips", 0)

        ## Initialize P-A Trip Tables from trip distribution
        util.initmat(eb, "mf3150", "HbUP-A", " HbU P-A Trips ", 0)
