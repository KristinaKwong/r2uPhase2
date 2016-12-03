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
        VOC = float(util.get_matrix_numpy(eb, 'autoOpCost')) # Veh Op Cost
        Occ = float(util.get_matrix_numpy(eb, 'HOVOccHbw')) # Occupancy
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
        p2   =  -2.857353
        p3   =  -4.645513
        p4   =  -0.579405
        p5   =  -5.308139
        p6   =   1.223910
        p7   =  -3.368593
        p8   =   1.957539
        p9   =  -3.223163
        p10  =   1.936110
        p11  =  -3.033976
        p12  =  -0.275638
        p13  =  -0.178191
        p14  =  -0.150122
        p17  =  -0.154180
        p18  =  -0.101158
        p19  =  -0.499461
        p20  =  -1.468654
        p21  =  -0.426471
        p151 =  -0.072255
        p152 =  -0.079392
        p153 =  -0.072918
        p160 =   1.993120
        p161 =   2.516637
        p162 =   1.189023
        p163 =   1.705081
        p164 =   0.577858
        p505 =  -0.355604
        p506 =  -0.398646
        p601 =   0.107310
        p602 =   0.119214
        p603 =   0.067335
        p701 =   0.251807
        p850 =   1.688004
        p870 =   0.710729
        p991 =  -0.115479
        p992 =   0.001068
        p993 =   1.863282
        p994 =   0.126964
        p995 =  -0.001334
        p996 =   0.615975
        thet =   0.596401
        Tiny=0.000001

#        ##############################################################################
#        ##       Auto Modes
#        ##############################################################################
        # Generate Dataframe
        Df = util.get_pd_ij_df(eb)

        ParkCost = eb.matrix('prk8hr').get_numpy_data() # 8hr Parking
        ParkCost = ParkCost.reshape(1, NoTAZ) + np.zeros((NoTAZ, 1)) # Broadcast parking from vector to matrix
        Df['ParkCost'] = ParkCost.flatten()

        AutoAccess = eb.matrix('autoAccLn').get_numpy_data() # 8hr Parking
        AutoAccess = AutoAccess.reshape(NoTAZ,1) + np.zeros((1, NoTAZ)) # Broadcast Log accessibility from vector to matrix
        Df['AutoAccess'] = AutoAccess.flatten()


        Df['AutoDisSOV'] = util.get_matrix_numpy(eb, 'HbWBlSovDist').flatten() #SOV Distance
        Df['AutoTimSOV'] = util.get_matrix_numpy(eb, 'HbWBlSovTime').flatten() #SOV Time
        AutoCosSOV = util.get_matrix_numpy(eb, 'mf5102').flatten()
        Df['AutoCosSOV'] = AutoCosSOV + Df['AutoDisSOV']*VOC + Df['ParkCost']


        Df['AutoDisHOV'] = util.get_matrix_numpy(eb, 'mf5106').flatten() #HOV Distance
        Df['AutoTimHOV'] = util.get_matrix_numpy(eb, 'mf5107').flatten() #hOV Time
        AutoCosHOV = util.get_matrix_numpy(eb, 'mf5108').flatten()
        Df['AutoCosHOV'] = AutoCosHOV + Df['AutoDisHOV']*VOC + Df['ParkCost']

        Df['BusIVT'] = util.get_matrix_numpy(eb, 'HbWBlBusIvtt').flatten() #In vehicle Bus time
        Df['BusWat'] = util.get_matrix_numpy(eb, 'HbWBlBusWait').flatten() #Wait Bus time
        Df['BusAux'] = util.get_matrix_numpy(eb, 'HbWBlBusAux').flatten() #Walk Time
        Df['BusBrd'] = util.get_matrix_numpy(eb, 'HbWBlBusBoard').flatten() #Boarding time
        Df['BusFar'] = util.get_matrix_numpy(eb, 'HbWBlBusFare').flatten() #Fare
        Df['BusTot'] = Df['BusIVT'] + Df['BusWat'] + Df['BusAux'] + Df['BusBrd'] #Total travel Time

        Df['RalIVR'] = util.get_matrix_numpy(eb, 'HbWBlRailIvtt').flatten() #In vehicle Rail time on rail
        Df['RalIVB'] = util.get_matrix_numpy(eb, 'HbWBlRailIvttBus').flatten() #In vehicle Rail time on bus
        Df['RalWat'] = util.get_matrix_numpy(eb, 'HbWBlRailWait').flatten() # Wait Rail Time
        Df['RalAux'] = util.get_matrix_numpy(eb, 'HbWBlRailAux').flatten() # Auxiliary Time
        Df['RalBrd'] = util.get_matrix_numpy(eb, 'HbWBlRailBoard').flatten()
        Df['RalFar'] = util.get_matrix_numpy(eb, 'HbWBlRailFare').flatten()


        Df['WCEIVW'] = util.get_matrix_numpy(eb, 'HbWBlWceIvtt').flatten() #In vehicle Rail time on wce
        Df['WCEIVR'] = util.get_matrix_numpy(eb, 'HbWBlWceIvttRail').flatten() #In vehicle Rail time on rail
        Df['WCEIVB'] = util.get_matrix_numpy(eb, 'HbWBlWceIvttBus').flatten() #In vehicle Rail time on bus
        Df['WCEWat'] = util.get_matrix_numpy(eb, 'HbWBlWceWait').flatten() # wait time
        Df['WCEAux'] = util.get_matrix_numpy(eb, 'HbWBlWceAux').flatten() # walk time
        Df['WCEBrd'] = util.get_matrix_numpy(eb, 'HbWBlWceBoards').flatten() # board time
        Df['WCEFar'] = util.get_matrix_numpy(eb, 'HbWBlWceFare').flatten() # wce fare

        TranAccess = eb.matrix('transitAccLn').get_numpy_data() # 8hr Parking
        TranAccess = TranAccess.reshape(NoTAZ,1) + np.zeros((1, NoTAZ)) # Broadcast Log accessibility from vector to matrix
        Df['TranAccess'] = TranAccess.flatten()

        Df['PRBAuDis'] = util.get_matrix_numpy(eb, 'HbWBlBAuPRDist').flatten() #Bus PR Drive Distance
        Df['PRBAuTim'] = util.get_matrix_numpy(eb, 'HbWBlBAuPRTime').flatten() # Bus PR Drive Time
        Df['PRBAuCos'] = Df['PRBAuDis']*VOC + util.get_matrix_numpy(eb, 'HbWBlBAuPRToll').flatten() + util.get_matrix_numpy(eb, 'HbWBAuPrkCst').flatten() # Bus PR Drive Cost
        Df['PRBAuTrm'] = util.get_matrix_numpy(eb, 'HbWBAuTrmTim').flatten() #Bus PR Terminal Time
        Df['PRBusIVT'] = util.get_matrix_numpy(eb, 'HbWBlBAuBusIvtt').flatten() #Bus IVTT
        Df['PRBusWat'] = util.get_matrix_numpy(eb, 'HbWBlBAuBusWait').flatten() #Bus Wait Time
        Df['PRBusAux'] = util.get_matrix_numpy(eb, 'HbWBlBAuBusAux').flatten() # Bus Walk Time
        Df['PRBusBrd'] = util.get_matrix_numpy(eb, 'HbWBlBAuBusBoard').flatten() # Bus Boarding Time
        Df['PRBusFar'] = util.get_matrix_numpy(eb, 'HbWBlBAuBusFare').flatten() # Bus Fare

        Df['PRRAuDis'] = util.get_matrix_numpy(eb, 'HbWBlRAuPRDist').flatten() #Rail PR Drive Distance
        Df['PRRAuTim'] = util.get_matrix_numpy(eb, 'HbWBlRAuPRTime').flatten() #Rail PR Drive Time
        Df['PRRAuCos'] = Df['PRRAuDis']*VOC + util.get_matrix_numpy(eb, 'HbWBlRAuPRToll').flatten() + util.get_matrix_numpy(eb, 'HbWRAuPrkCst').flatten() # Rail PR Drive Cost
        Df['PRRAuTrm'] = util.get_matrix_numpy(eb, 'HbWRAuTrmTim').flatten() #Rail PR Terminal Time
        Df['PRRalIVR'] = util.get_matrix_numpy(eb, 'HbWBlRAuRailIvtt').flatten() #IVT on Rail
        Df['PRRalIVB'] = util.get_matrix_numpy(eb, 'HbWBlRAuRailIvttBus').flatten() #IVT on Bus
        Df['PRRalWat'] = util.get_matrix_numpy(eb, 'HbWBlRAuRailWait').flatten() #Rail Wait Time
        Df['PRRalAux'] = util.get_matrix_numpy(eb, 'HbWBlRAuRailAux').flatten() #Rail Walk Time
        Df['PRRalBrd'] = util.get_matrix_numpy(eb, 'HbWBlRAuRailBoard').flatten() #Rail Board Time
        Df['PRRalFar'] = util.get_matrix_numpy(eb, 'HbWBlRAuRailFare').flatten() #Rail Fare


        Df['PRWAuDis'] = util.get_matrix_numpy(eb, 'HbWBlWAuPRDist').flatten() #WCE PR Drive Distance
        Df['PRWAuTim'] = util.get_matrix_numpy(eb, 'HbWBlWAuPRTime').flatten() #WCE PR Drive Time
        Df['PRWAuCos'] = Df['PRWAuDis']*VOC + util.get_matrix_numpy(eb, 'HbWBlWAuPRToll').flatten() + util.get_matrix_numpy(eb, 'HbWWAuPrkCst').flatten() # WCE PR Drive Cost
        Df['PRWAuTrm'] = util.get_matrix_numpy(eb, 'HbWWAuTrmTim').flatten() #WCE PR Terminal Time
        Df['PRWCEIVW'] = util.get_matrix_numpy(eb, 'HbWBlWAuWceIvtt').flatten() #IVT on WCE
        Df['PRWCEIVR'] = util.get_matrix_numpy(eb, 'HbWBlWAuWceIvttRail').flatten() #IVT on Rail
        Df['PRWCEIVB'] = util.get_matrix_numpy(eb, 'HbWBlWAuWceIvttBus').flatten() #IVT on Bus
        Df['PRWCEWat'] = util.get_matrix_numpy(eb, 'HbWBlWAuWceWait').flatten() #WCE Wait Time
        Df['PRWCEAux'] = util.get_matrix_numpy(eb, 'HbWBlWAuWceAux').flatten()  #WCE Walk Time
        Df['PRWCEBrd'] = util.get_matrix_numpy(eb, 'HbWBlWAuWceBoards').flatten() #WCE Board Time
        Df['PRWCEFar'] = util.get_matrix_numpy(eb, 'HbWBlWAuWceFare').flatten() #WCE Fare



        IntraCBD = util.get_matrix_numpy(eb, 'd_cbd') #Intra-CBD
        IntraCBD = IntraCBD.reshape(NoTAZ, 1)*IntraCBD.reshape(1, NoTAZ) #Broadcast intra-CBD
        Df['IntraCBD'] = IntraCBD.flatten()

        PopEmpDen = util.get_matrix_numpy(eb, 'popdens') + util.get_matrix_numpy(eb, 'empdens') #Pop+Emp Density at Prod and Attr Zones
        PopEmpDen = PopEmpDen.reshape(NoTAZ, 1) + PopEmpDen.reshape(1, NoTAZ) #Broadcast Density
        PopEmpDen[PopEmpDen<1.0] = 1.0 #Control density to a minimum of 1 to avoid negative
        PopEmpDen = np.log(PopEmpDen) #Log Density
        Df['PopEmpDen'] = PopEmpDen.flatten()

        PopSen = util.get_matrix_numpy(eb, 'Pop55t64') + util.get_matrix_numpy(eb, 'Pop65Up') #Senior Proportion
        PopTot = util.get_matrix_numpy(eb, 'TotEmp')
        PopSPr = np.log(PopSen/(PopTot + Tiny) + 0.0001)
        PopSPr = PopSPr.reshape(NoTAZ, 1) + np.zeros((1, NoTAZ))
        Df['PopSPr'] = PopSPr.flatten()
        Df['BikScr'] = util.get_matrix_numpy(eb, 'bikeskim').flatten() # Bike Score

        Df[500000:550000].to_csv("F:/Scratch/MC_Df.csv")

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