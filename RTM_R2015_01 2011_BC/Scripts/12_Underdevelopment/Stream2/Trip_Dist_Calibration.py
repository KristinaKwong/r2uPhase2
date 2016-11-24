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
        Distance = util.get_matrix_numpy(eb, 'mf5100')
                   
                   
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
                      
        AverageDistLamb = [10.0, 10.0, 10.0,
                           10.0, 10.0, 10.0,
                           10.0, 10.0, 10.0]
                      
        AverageDistAlph = [10.0, 10.0, 10.0,
                           10.0, 10.0, 10.0,
                           10.0, 10.0, 10.0]
                      
        AverageDistAlph = [10.0, 10.0, 10.0,
                           10.0, 10.0, 10.0,
                           10.0, 10.0, 10.0]

                      
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