##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage2.blendedskims
##--Purpose:
##---------------------------------------------------------------------
import inro.modeller as _m
import csv
import os
import numpy as np
import pandas as pd
import traceback as _traceback

class ModeChoiceGenDf(_m.Tool()):

    ##Global attribute for Tool Run Message (successful/not successful)
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Generate Mode Choice Data Frames"
        pb.description = "Generates Mode Choice Data Frames"
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

    @_m.logbook_trace("Generate Data Frame")
    def __call__(self, eb):
        util = _m.Modeller().tool("translink.util")
        input_path = util.get_input_path(eb)
        self.matrix_batchins(eb)
        ## Park and Ride determine best lot
        pnr_costs = os.path.join(input_path, "pnr_inputs.csv")
        model_year = int(util.get_matrix_numpy(eb, "Year"))

        self.AutoGT(eb)
        self.BusGT(eb)
        self.RailGT(eb)
        self.WceGT(eb)
        self.bestlot(eb, model_year)
        ## Calculate Accessibilities
        Acessibilities_Loc = _m.Modeller().tool("translink.RTM3.stage0.data_generate")
        Acessibilities_Loc.calc_all_accessibilities(eb)


        ## General Setup
        BLBsWk = util.get_matrix_numpy(eb, "buspr-lotChceWkAMPA").flatten() #Best Lot Bus Work
        BLBsNw = util.get_matrix_numpy(eb, "buspr-lotChceNWkAMPA").flatten() #Best Lot Bus Non-Work
        BLRlWk = util.get_matrix_numpy(eb, "railpr-lotChceWkAMPA").flatten() #Best Lot Rail Work
        BLRlNw = util.get_matrix_numpy(eb, "railpr-lotChceNWkAMPA").flatten() #Best Lot Rail Non-Work
        BLWcWk = util.get_matrix_numpy(eb, "wcepr-lotChceWkAMPA").flatten() #Best Lot WCE Work
        BLWcNw = util.get_matrix_numpy(eb, "wcepr-lotChceNWkAMPA").flatten() #Best Lot WCE Non-Work
        NoTAZ  = len(util.get_matrix_numpy(eb, "zoneindex")) # Number of TAZs in Model

        # Time component blend factors
        hbwo_fct = self.get_fact(eb, [["HbWBl_AM_P-A", "HbWBl_MD_P-A", "HbWBl_PM_P-A"],
                                ["HbWBl_AM_A-P", "HbWBl_MD_A-P", "HbWBl_PM_A-P"]])

        hbwo_fct_wce = self.get_fact(eb,[["HbWBl_AM_WCE_P-A", "Zero", "HbWBl_PM_WCE_P-A"],
                                     ["Zero", "Zero", "HbWBl_PM_WCE_A-P"]])

        nhbw_fct = self.get_fact(eb, [["NHbWBl_AM_P-A", "NHbWBl_MD_P-A", "NHbWBl_PM_P-A"],
                                 ["Zero", "Zero", "Zero"]])

        hbun_fct = self.get_fact(eb, [["HbUBl_AM_P-A", "HbUBl_MD_P-A", "HbUBl_PM_P-A"],
                                 ["HbUBl_AM_A-P", "HbUBl_MD_A-P", "HbUBl_PM_A-P"]])

        hbsc_fct = self.get_fact(eb, [["HbScBl_AM_P-A", "HbScBl_MD_P-A", "HbScBl_PM_P-A"],
                                 ["HbScBl_AM_A-P", "HbScBl_MD_A-P", "HbScBl_PM_A-P"]])

        hbsh_fct = self.get_fact(eb, [["HbShBl_AM_P-A", "HbShBl_MD_P-A", "HbShBl_PM_P-A"],
                                 ["HbShBl_AM_A-P", "HbShBl_MD_A-P", "HbShBl_PM_A-P"]])

        hbpb_fct = self.get_fact(eb, [["HbPbBl_AM_P-A", "HbPbBl_MD_P-A", "HbPbBl_PM_P-A"],
                                 ["HbPbBl_AM_A-P", "HbPbBl_MD_A-P", "HbPbBl_PM_A-P"]])

        hbso_fct = self.get_fact(eb, [["HbSoBl_AM_P-A", "HbSoBl_MD_P-A", "HbSoBl_PM_P-A"],
                                 ["HbSoBl_AM_A-P", "HbSoBl_MD_A-P", "HbSoBl_PM_A-P"]])

        hbes_fct = self.get_fact(eb, [["HbEsBl_AM_P-A", "HbEsBl_MD_P-A", "HbEsBl_PM_P-A"],
                                 ["HbEsBl_AM_A-P", "HbEsBl_MD_A-P", "HbEsBl_PM_A-P"]])

        nhbo_fct = self.get_fact(eb, [["NHbOBl_AM_P-A", "NHbOBl_MD_P-A", "NHbOBl_PM_P-A"],
                                 ["Zero", "Zero", "Zero"]])

        # Transit fare blend factors
        trfr_hbwo_fct = self.get_fact_fare(eb, [["TrFr_HbWBl_AM_P-A", "TrFr_HbWBl_MD_P-A", "TrFr_HbWBl_PM_P-A", "TrFr_HbWBl_OP_P-A"],
                                ["TrFr_HbWBl_AM_A-P", "TrFr_HbWBl_MD_A-P", "TrFr_HbWBl_PM_A-P", "TrFr_HbWBl_OP_A-P"]])

        trfr_hbun_fct = self.get_fact_fare(eb, [["TrFr_HbUBl_AM_P-A", "TrFr_HbUBl_MD_P-A", "TrFr_HbUBl_PM_P-A", "TrFr_HbUBl_OP_P-A"],
                                ["TrFr_HbUBl_AM_A-P", "TrFr_HbUBl_MD_A-P", "TrFr_HbUBl_PM_A-P", "TrFr_HbUBl_OP_A-P"]])

        trfr_hbsc_fct = self.get_fact_fare(eb, [["TrFr_HbScBl_AM_P-A", "TrFr_HbScBl_MD_P-A", "TrFr_HbScBl_PM_P-A", "TrFr_HbScBl_OP_P-A"],
                                ["TrFr_HbScBl_AM_A-P", "TrFr_HbScBl_MD_A-P", "TrFr_HbScBl_PM_A-P", "TrFr_HbScBl_OP_A-P"]])

        trfr_hbsh_fct = self.get_fact_fare(eb, [["TrFr_HbShBl_AM_P-A", "TrFr_HbShBl_MD_P-A", "TrFr_HbShBl_PM_P-A", "TrFr_HbShBl_OP_P-A"],
                                ["TrFr_HbShBl_AM_A-P", "TrFr_HbShBl_MD_A-P", "TrFr_HbShBl_PM_A-P", "TrFr_HbShBl_OP_A-P"]])


        trfr_hbpb_fct = self.get_fact_fare(eb, [["TrFr_HbPbBl_AM_P-A", "TrFr_HbPbBl_MD_P-A", "TrFr_HbPbBl_PM_P-A", "TrFr_HbPbBl_OP_P-A"],
                                ["TrFr_HbPbBl_AM_A-P", "TrFr_HbPbBl_MD_A-P", "TrFr_HbPbBl_PM_A-P", "TrFr_HbPbBl_OP_A-P"]])

        trfr_hbso_fct = self.get_fact_fare(eb, [["TrFr_HbSoBl_AM_P-A", "TrFr_HbSoBl_MD_P-A", "TrFr_HbSoBl_PM_P-A", "TrFr_HbSoBl_OP_P-A"],
                                ["TrFr_HbSoBl_AM_A-P", "TrFr_HbSoBl_MD_A-P", "TrFr_HbSoBl_PM_A-P", "TrFr_HbSoBl_OP_A-P"]])

        trfr_hbes_fct = self.get_fact_fare(eb, [["TrFr_HbEsBl_AM_P-A", "TrFr_HbEsBl_MD_P-A", "TrFr_HbEsBl_PM_P-A", "TrFr_HbEsBl_OP_P-A"],
                                ["TrFr_HbEsBl_AM_A-P", "TrFr_HbEsBl_MD_A-P", "TrFr_HbEsBl_PM_A-P", "TrFr_HbEsBl_OP_A-P"]])

        trfr_nhbw_fct = self.get_fact_fare(eb, [["TrFr_NHbWBl_AM_P-A", "TrFr_NHbWBl_MD_P-A", "TrFr_NHbWBl_PM_P-A", "TrFr_NHbWBl_OP_P-A"],
                                ["Zero", "Zero", "Zero", "Zero"]])

        trfr_nhbo_fct = self.get_fact_fare(eb, [["TrFr_NHbOBl_AM_P-A", "TrFr_NHbOBl_MD_P-A", "TrFr_NHbOBl_PM_P-A", "TrFr_NHbOBl_OP_P-A"],
                                ["Zero", "Zero", "Zero", "Zero"]])

        ##############################################################################
        ##       Auto Skims SOV VOT 1 NHBO, HbSch, HbU, HbShopLow, HbPBLow
        ##############################################################################
        # Initialize Time Distance and Cost Skim Dictionaries
        # VOT 1 NHBO, HbSch, HbU, HbShopLow, HbPBLow
        TimeDict, CostDict = {}, {}

        # Generate Skim Dictionaries
            #                                 AM    ,       MD   ,            PM
        self.GenSkimDict(eb, CostDict, ["mfAmSovOpCstVOT1", "mfMdSovOpCstVOT1", "mfPmSovOpCstVOT1"]) # Cost
        self.GenSkimDict(eb, TimeDict, ["AmSovTimeVOT1", "MdSovTimeVOT1", "PmSovTimeVOT1"]) # Time

        # Blend Factors            AM , MD  , PM           AM  ,MD , PM       Where Blended Matrices get stored in same order as above
        BlendDict = {'nhbo':{'PA':nhbo_fct[0], 'AP':nhbo_fct[1], 'Mat':['NHbOBlSovCost', 'NHbOBlSovTime']}, # non-home base other
                     'hbun':{'PA':hbun_fct[0], 'AP':hbun_fct[1], 'Mat':['HbUBlSovCost',  'HbUBlSovTime' ]}, # home-base uni
                     'hbsc':{'PA':hbsc_fct[0], 'AP':hbsc_fct[1], 'Mat':['HbScBlSovCost', 'HbScBlSovTime']}, # home-base school
                     'hbsh':{'PA':hbsh_fct[0], 'AP':hbsh_fct[1], 'Mat':['HbShBlSovCost_I1', 'HbShBlSovTime_I1']}, # home-base shopping low
                     'hbpb':{'PA':hbpb_fct[0], 'AP':hbpb_fct[1], 'Mat':['HbPbBlSovCost_I1', 'HbPbBlSovTime_I1']}} # home-base personal business low

        for keys, values in BlendDict.items():
            Df = {}
            # Calculate blended skim
            Df['AutoCos'] = self.calc_blend(values, CostDict)
            Df['AutoTim'] = self.calc_blend(values, TimeDict)


        # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['AutoCos'])
            util.set_matrix_numpy(eb, values['Mat'][1], Df['AutoTim'])


        #
        ##############################################################################
        ##       Auto Skims SOV VOT 2 HbShopMed, HbPBMed, HbEsc, HbSocLow, HbPB High
        ##############################################################################

        TimeDict, CostDict = {}, {}
            #                                 AM    ,       MD   ,            PM
        self.GenSkimDict(eb, CostDict, ["mfAmSovOpCstVOT2", "mfMdSovOpCstVOT2", "mfPmSovOpCstVOT2"]) # Cost
        self.GenSkimDict(eb, TimeDict, ["AmSovTimeVOT2", "MdSovTimeVOT2", "PmSovTimeVOT2"]) # Time


        # Blend Factors            AM , MD  , PM           AM  ,MD , PM       Where Blended Matrices get stored in same order as above
        BlendDict = {'hbsh':{'PA':hbsh_fct[0], 'AP':hbsh_fct[1], 'Mat':['HbShBlSovCost_I2', 'HbShBlSovTime_I2' ]}, # home-base shopping med
                     'hbpbm':{'PA':hbpb_fct[0], 'AP':hbpb_fct[1], 'Mat':['HbPbBlSovCost_I2', 'HbPbBlSovTime_I2']}, # home-base personal business med
                     'hbes':{'PA':hbes_fct[0], 'AP':hbes_fct[1], 'Mat':['HbEsBlSovCost', 'HbEsBlSovTime']}, # home-base escorting
                     'hbso':{'PA':hbso_fct[0], 'AP':hbso_fct[1], 'Mat':['HbSoBlSovCost_I1', 'HbSoBlSovTime_I1' ]}, # home-base social low
                     'hbpbh':{'PA':hbpb_fct[0], 'AP':hbpb_fct[1], 'Mat':['HbPbBlSovCost_I3', 'HbPbBlSovTime_I3']}} # home-base personal business high

        for keys, values in BlendDict.items():
            Df = {}
            # Calculate blended skim
            Df['AutoCos'] = self.calc_blend(values, CostDict)
            Df['AutoTim'] = self.calc_blend(values, TimeDict)

           # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['AutoCos'])
            util.set_matrix_numpy(eb, values['Mat'][1], Df['AutoTim'])

        ##############################################################################
        ##       Auto Skims SOV VOT 3 HbShopHigh, HbW Low, HbSocMed
        ##############################################################################

        TimeDict, CostDict = {}, {}

            #                                 AM    ,       MD   ,            PM
        self.GenSkimDict(eb, CostDict, ["mfAmSovOpCstVOT3", "mfMdSovOpCstVOT3", "mfPmSovOpCstVOT3"]) # Cost
        self.GenSkimDict(eb, TimeDict, ["AmSovTimeVOT3", "MdSovTimeVOT3", "PmSovTimeVOT3"]) # Time


        # Blend Factors            AM , MD  , PM           AM  ,MD , PM       Where Blended Matrices get stored in same order as above
        BlendDict = {'hbsh':{'PA':hbsh_fct[0], 'AP':hbsh_fct[1], 'Mat':['HbShBlSovCost_I3', 'HbShBlSovTime_I3']}, # home-base shopping high
                     'hbwo':{'PA':hbwo_fct[0], 'AP':hbwo_fct[1], 'Mat':['HbWBlSovCost_I1', 'HbWBlSovTime_I1' ]}, # home-base work low
                     'hbso':{'PA':hbso_fct[0], 'AP':hbso_fct[1], 'Mat':['HbSoBlSovCost_I2', 'HbSoBlSovTime_I2']}} # home-base social med

        for keys, values in BlendDict.items():

            Df = {}
            # Calculate blended skim
            Df['AutoCos'] = self.calc_blend(values, CostDict)
            Df['AutoTim'] = self.calc_blend(values, TimeDict)

           # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['AutoCos'])
            util.set_matrix_numpy(eb, values['Mat'][1], Df['AutoTim'])

        #################################################################################
        ##       Auto Skims SOV VOT 4 HbSoc High, NHbW, HbW Med, HbW High + Park and Ride
        #################################################################################

        TimeDict, CostDict = {}, {}

            #                                 AM    ,       MD   ,            PM
        self.GenSkimDict(eb, CostDict, ["mfAmSovOpCstVOT4", "mfMdSovOpCstVOT4", "mfPmSovOpCstVOT4"]) # Cost
        self.GenSkimDict(eb, TimeDict, ["AmSovTimeVOT4", "MdSovTimeVOT4", "PmSovTimeVOT4"]) # Time


        # Blend Factors            AM , MD  , PM           AM  ,MD , PM       Where Blended Matrices get stored in same order as above
        BlendDict = {
                     'hbso':{'PA':hbso_fct[0], 'AP':hbso_fct[1], 'Mat':['HbSoBlSovCost_I3', 'HbSoBlSovTime_I3']}, # home-base social high
                     'nhbw':{'PA': nhbw_fct[0], 'AP':nhbw_fct[1], 'Mat':['NHbWBlSovCost', 'NHbWBlSovTime']}, # non-home base work
                     'hbwom':{'PA':hbwo_fct[0], 'AP':hbwo_fct[1], 'Mat':['HbWBlSovCost_I2', 'HbWBlSovTime_I2']}, # home-base work med
                     'hbwoh':{'PA':hbwo_fct[0], 'AP':hbwo_fct[1], 'Mat':['HbWBlSovCost_I3', 'HbWBlSovTime_I3']}} # home-base work high

        for keys, values in BlendDict.items():

            Df = {}
            # Calculate blended skim
            Df['AutoCos'] = self.calc_blend(values, CostDict)
            Df['AutoTim'] = self.calc_blend(values, TimeDict)

           # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['AutoCos'])
            util.set_matrix_numpy(eb, values['Mat'][1], Df['AutoTim'])

        ##       Park and Ride Home-base work Auto-leg

        # Blend Factors                AM , MD  , PM           AM  ,MD , PM    Where Blended Matrices get stored in same order as above
        BlendDictPR = {'hbwprb':{'PA': hbwo_fct[0], 'AP':hbwo_fct[1],
                       'Mat':['HbWBlBAuPRCost', 'HbWBlBAuPRTime', 'HbWBAuPrkCst', 'HbWBAuTrmTim'], 'BL': BLBsWk}, #Bus
                       'hbwprr':{'PA': hbwo_fct[0], 'AP':hbwo_fct[1],
                       'Mat':['HbWBlRAuPRCost', 'HbWBlRAuPRTime', 'HbWRAuPrkCst', 'HbWRAuTrmTim'], 'BL': BLRlWk}, # Rail
                       'hbwprw':{'PA': hbwo_fct_wce[0], 'AP':hbwo_fct_wce[1],
                       'Mat':['HbWBlWAuPRCost', 'HbWBlWAuPRTime', 'HbWWAuPrkCst', 'HbWWAuTrmTim'], 'BL': BLWcWk} # WCE
                      }

        for keys, values in BlendDictPR.items():

            Df = pd.DataFrame()

            # Generate data frame with Origin Destination and best lot
            Dfmerge = util.get_pd_ij_df(eb)
            Dfmerge['BL'] = values['BL']
            # Generate second data frame and attach to it blended
            Df_Auto_Leg = util.get_pd_ij_df(eb)
            Df_Auto_Leg['AutoCos'] = self.calc_blend(values, CostDict).flatten()
            Df_Auto_Leg['AutoTim'] = self.calc_blend(values, TimeDict).flatten()

            Df_Auto_Leg['Parking'] = (util.get_matrix_numpy(eb, "prcost").reshape(1, NoTAZ) + np.zeros((NoTAZ,1))).flatten()
            Df_Auto_Leg['TermTim'] = (util.get_matrix_numpy(eb, "prtrmt").reshape(1, NoTAZ) + np.zeros((NoTAZ,1))).flatten()

            # Join the two data frames based on skims from Origin to the Best Lot
            Df = pd.merge(Dfmerge, Df_Auto_Leg, left_on = ['i', 'BL'],
                     right_on = ['i', 'j'], how = 'left')
            # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['AutoCos'].reshape(NoTAZ,NoTAZ))
            util.set_matrix_numpy(eb, values['Mat'][1], Df['AutoTim'].reshape(NoTAZ,NoTAZ))

            util.set_matrix_numpy(eb, values['Mat'][2], Df['Parking'].reshape(NoTAZ,NoTAZ))
            util.set_matrix_numpy(eb, values['Mat'][3], Df['TermTim'].reshape(NoTAZ,NoTAZ))

        # delete data generated to free up memory
        del Df, Dfmerge, Df_Auto_Leg, TimeDict, CostDict

        ##############################################################################
        ##       Auto Skims HOV VOT 1 NHBO, HbSch, HbU, HbShopLow, HbPBLow
        ##############################################################################
        # Initialize Time and Cost Skim Dictionaries
        # VOT 1 NHBO, HbSch, HbU, HbShopLow, HbPBLow
        TimeDict, CostDict = {}, {}

        # Generate Skim Dictionaries
            #                                 AM    ,       MD   ,            PM
        self.GenSkimDict(eb, CostDict, ["mfAmHovOpCstVOT1", "mfMdHovOpCstVOT1", "mfPmHovOpCstVOT1"]) # Cost
        self.GenSkimDict(eb, TimeDict, ["AmHovTimeVOT1", "MdHovTimeVOT1", "PmHovTimeVOT1"]) # Time


        # Blend Factors            AM , MD  , PM           AM  ,MD , PM       Where Blended Matrices get stored in same order as above
        BlendDict = {'nhbo':{'PA':nhbo_fct[0], 'AP':nhbo_fct[1], 'Mat':['NHbOBlHovCost', 'NHbOBlHovTime']}, # non-home base other
                     'hbun':{'PA':hbun_fct[0], 'AP':hbun_fct[1], 'Mat':['HbUBlHovCost',  'HbUBlHovTime']}, # home-base uni
                     'hbsc':{'PA':hbsc_fct[0], 'AP':hbsc_fct[1], 'Mat':['HbScBlHovCost', 'HbScBlHovTime']}, # home-base school
                     'hbsh':{'PA':hbsh_fct[0], 'AP':hbsh_fct[1], 'Mat':['HbShBlHovCost_I1', 'HbShBlHovTime_I1']}, # home-base shopping low
                     'hbpb':{'PA':hbpb_fct[0], 'AP':hbpb_fct[1], 'Mat':['HbPbBlHovCost_I1', 'HbPbBlHovTime_I1']}} # home-base personal business low

        for keys, values in BlendDict.items():

            Df = {}
            # Calculate blended skim
            Df['AutoCos'] = self.calc_blend(values, CostDict)
            Df['AutoTim'] = self.calc_blend(values, TimeDict)


        # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['AutoCos'])
            util.set_matrix_numpy(eb, values['Mat'][1], Df['AutoTim'])

        #
        ##############################################################################
        ##       Auto Skims HOV VOT 2 HbShopMed, HbPBMed, HbEsc, HbSocLow, HbPB High
        ##############################################################################

        TimeDict, CostDict = {}, {}

            #                                 AM    ,       MD   ,            PM
        self.GenSkimDict(eb, CostDict, ["mfAmHovOpCstVOT2", "mfMdHovOpCstVOT2", "mfPmHovOpCstVOT2"]) # Cost
        self.GenSkimDict(eb, TimeDict, ["AmHovTimeVOT2", "MdHovTimeVOT2", "PmHovTimeVOT2"]) # Time


        # Blend Factors            AM , MD  , PM           AM  ,MD , PM       Where Blended Matrices get stored in same order as above
        BlendDict = {'hbsh':{'PA':hbsh_fct[0], 'AP':hbsh_fct[1], 'Mat':['HbShBlHovCost_I2', 'HbShBlHovTime_I2']}, # home-base shopping med
                     'hbpbm':{'PA':hbpb_fct[0], 'AP':hbpb_fct[1], 'Mat':['HbPbBlHovCost_I2', 'HbPbBlHovTime_I2']}, # home-base personal business med
                     'hbes':{'PA':hbes_fct[0], 'AP':hbes_fct[1], 'Mat':['HbEsBlHovCost', 'HbEsBlHovTime']}, # home-base escorting
                     'hbso':{'PA':hbso_fct[0], 'AP':hbso_fct[1], 'Mat':['HbSoBlHovCost_I1', 'HbSoBlHovTime_I1']}, # home-base social low
                     'hbpbh':{'PA':hbpb_fct[0], 'AP':hbpb_fct[1], 'Mat':['HbPbBlHovCost_I3', 'HbPbBlHovTime_I3']}} # home-base personal business high

        for keys, values in BlendDict.items():

            Df = {}
            # Calculate blended skim
            Df['AutoCos'] = self.calc_blend(values, CostDict)
            Df['AutoTim'] = self.calc_blend(values, TimeDict)


           # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['AutoCos'])
            util.set_matrix_numpy(eb, values['Mat'][1], Df['AutoTim'])

        ##############################################################################
        ##       Auto Skims Hov VOT 3 HbShopHigh, HbW Low, HbSocMed
        ##############################################################################

        TimeDict, CostDict = {}, {}

            #                                 AM    ,       MD   ,            PM
        self.GenSkimDict(eb, CostDict, ["mfAmHovOpCstVOT3", "mfMdHovOpCstVOT3", "mfPmHovOpCstVOT3"]) # Cost
        self.GenSkimDict(eb, TimeDict, ["AmHovTimeVOT3", "MdHovTimeVOT3", "PmHovTimeVOT3"]) # Time


        # Blend Factors            AM , MD  , PM           AM  ,MD , PM       Where Blended Matrices get stored in same order as above
        BlendDict = {'hbsh':{'PA':hbsh_fct[0], 'AP':hbsh_fct[1], 'Mat':['HbShBlHovCost_I3', 'HbShBlHovTime_I3']}, # home-base shopping high
                     'hbwo':{'PA':hbwo_fct[0], 'AP':hbwo_fct[1], 'Mat':['HbWBlHovCost_I1', 'HbWBlHovTime_I1' ]}, # home-base work low
                     'hbso':{'PA':hbso_fct[0], 'AP':hbso_fct[1], 'Mat':['HbSoBlHovCost_I2', 'HbSoBlHovTime_I2']}} # home-base social med

        for keys, values in BlendDict.items():

            Df = {}
            # Calculate blended skim
            Df['AutoCos'] = self.calc_blend(values, CostDict)
            Df['AutoTim'] = self.calc_blend(values, TimeDict)


           # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['AutoCos'])
            util.set_matrix_numpy(eb, values['Mat'][1], Df['AutoTim'])


        #################################################################################
        ##       Auto Skims Hov VOT 4 HbSoc High, NHbW, HbW Med, HbW High + Park and Ride
        #################################################################################

        TimeDict, CostDict = {}, {}

            #                                 AM    ,       MD   ,            PM
        self.GenSkimDict(eb, CostDict, ["mfAmHovOpCstVOT4", "mfMdHovOpCstVOT4", "mfPmHovOpCstVOT4"]) # Cost
        self.GenSkimDict(eb, TimeDict, ["AmHovTimeVOT4", "MdHovTimeVOT4", "PmHovTimeVOT4"]) # Time


        # Blend Factors            AM , MD  , PM           AM  ,MD , PM       Where Blended Matrices get stored in same order as above
        BlendDict = {
                     'hbso':{'PA':hbso_fct[0], 'AP':hbso_fct[1], 'Mat':['HbSoBlHovCost_I3', 'HbSoBlHovTime_I3']}, # home-base social high
                     'nhbw':{'PA': nhbw_fct[0], 'AP':nhbw_fct[1], 'Mat':['NHbWBlHovCost', 'NHbWBlHovTime']}, # non-home base work
                     'hbwom':{'PA':hbwo_fct[0], 'AP':hbwo_fct[1], 'Mat':['HbWBlHovCost_I2', 'HbWBlHovTime_I2']}, # home-base work med
                     'hbwoh':{'PA':hbwo_fct[0], 'AP':hbwo_fct[1], 'Mat':['HbWBlHovCost_I3', 'HbWBlHovTime_I3']}} # home-base work high

        for keys, values in BlendDict.items():

            Df = {}
            # Calculate blended skim
            Df['AutoCos'] = self.calc_blend(values, CostDict)
            Df['AutoTim'] = self.calc_blend(values, TimeDict)

           # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['AutoCos'])
            util.set_matrix_numpy(eb, values['Mat'][1], Df['AutoTim'])

#       ##############################################################################
#       ##       Blended Bridge Crossings
#       ##############################################################################

        ## Get Birgde Penalties
        AM_Penalty = util.get_matrix_numpy(eb, "Bridge_pen_AM")
        PM_Penalty = util.get_matrix_numpy(eb, "Bridge_pen_PM")

        #  Shopping
        Sh_PA_AM_Fct = util.get_matrix_numpy(eb, "HbShBl_AM_P-A")
        Sh_PA_PM_Fct = util.get_matrix_numpy(eb, "HbShBl_PM_P-A")
        Sh_AP_AM_Fct = util.get_matrix_numpy(eb, "HbShBl_AM_A-P")
        Sh_AP_PM_Fct = util.get_matrix_numpy(eb, "HbShBl_PM_A-P")

        Blend_Dist = Sh_PA_AM_Fct*AM_Penalty + Sh_PA_PM_Fct*PM_Penalty + Sh_AP_AM_Fct*AM_Penalty.transpose() + Sh_AP_PM_Fct*PM_Penalty.transpose()
        util.set_matrix_numpy(eb, "HbShBl_BPen", Blend_Dist)

        #  Per-business
        Pb_PA_AM_Fct = util.get_matrix_numpy(eb, "HbPbBl_AM_P-A")
        Pb_PA_PM_Fct = util.get_matrix_numpy(eb, "HbPbBl_PM_P-A")
        Pb_AP_AM_Fct = util.get_matrix_numpy(eb, "HbPbBl_AM_A-P")
        Pb_AP_PM_Fct = util.get_matrix_numpy(eb, "HbPbBl_PM_A-P")

        Blend_Dist = Pb_PA_AM_Fct*AM_Penalty + Pb_PA_PM_Fct*PM_Penalty + Pb_AP_AM_Fct*AM_Penalty.transpose() + Pb_AP_PM_Fct*PM_Penalty.transpose()
        util.set_matrix_numpy(eb, "HbPbBl_BPen", Blend_Dist)

        #  Social
        So_PA_AM_Fct = util.get_matrix_numpy(eb, "HbSoBl_AM_P-A")
        So_PA_PM_Fct = util.get_matrix_numpy(eb, "HbSoBl_PM_P-A")
        So_AP_AM_Fct = util.get_matrix_numpy(eb, "HbSoBl_AM_A-P")
        So_AP_PM_Fct = util.get_matrix_numpy(eb, "HbSoBl_PM_A-P")

        Blend_Dist = So_PA_AM_Fct*AM_Penalty + So_PA_PM_Fct*PM_Penalty + So_AP_AM_Fct*AM_Penalty.transpose() + So_AP_PM_Fct*PM_Penalty.transpose()
        util.set_matrix_numpy(eb, "HbSoBl_BPen", Blend_Dist)

        #  Escort
        Es_PA_AM_Fct = util.get_matrix_numpy(eb, "HbEsBl_AM_P-A")
        Es_PA_PM_Fct = util.get_matrix_numpy(eb, "HbEsBl_PM_P-A")
        Es_AP_AM_Fct = util.get_matrix_numpy(eb, "HbEsBl_AM_A-P")
        Es_AP_PM_Fct = util.get_matrix_numpy(eb, "HbEsBl_PM_A-P")

        Blend_Dist = Es_PA_AM_Fct*AM_Penalty + Es_PA_PM_Fct*PM_Penalty + Es_AP_AM_Fct*AM_Penalty.transpose() + Es_AP_PM_Fct*PM_Penalty.transpose()
        util.set_matrix_numpy(eb, "HbEsBl_BPen", Blend_Dist)

        #  School
        Sc_PA_AM_Fct = util.get_matrix_numpy(eb, "HbScBl_AM_P-A")
        Sc_PA_PM_Fct = util.get_matrix_numpy(eb, "HbScBl_PM_P-A")
        Sc_AP_AM_Fct = util.get_matrix_numpy(eb, "HbScBl_AM_A-P")
        Sc_AP_PM_Fct = util.get_matrix_numpy(eb, "HbScBl_PM_A-P")

        Blend_Dist = Sc_PA_AM_Fct*AM_Penalty + Sc_PA_PM_Fct*PM_Penalty + Sc_AP_AM_Fct*AM_Penalty.transpose() + Sc_AP_PM_Fct*PM_Penalty.transpose()
        util.set_matrix_numpy(eb, "HbScBl_BPen", Blend_Dist)

        #  NHbO
        No_PA_AM_Fct = util.get_matrix_numpy(eb, "NHbOBl_AM_P-A")
        No_PA_PM_Fct = util.get_matrix_numpy(eb, "NHbOBl_PM_P-A")

        Blend_Dist = No_PA_AM_Fct*AM_Penalty + No_PA_PM_Fct*PM_Penalty
        util.set_matrix_numpy(eb, "NHbOBl_BPen", Blend_Dist)

#       ##############################################################################
#       ##       Bus Skims
#       ##############################################################################
#       # Initialize In-vehicle, Wait, Auxiliary, Boarding and Fare Skim Dictionaries
        BusIVTDict, BusWatDict, BusAuxDict = {}, {}, {}
        BusBrdDict, BusFarDict = {}, {}
        # Generate Skim Dictionaries
        #                                  AM    ,    MD   ,     PM
        self.GenSkimDict(eb, BusIVTDict, ["AmBusIvtt", "MdBusIvtt",  "PmBusIvtt"]) # Bus IVTT
        self.GenSkimDict(eb, BusWatDict, ["AmBusWait", "MdBusWait",  "PmBusWait"]) # Bus Wait
        self.GenSkimDict(eb, BusAuxDict, ["AmBusAux",  "MdBusAux",   "PmBusAux"]) # Bus Aux
        self.GenSkimDict(eb, BusBrdDict, ["AmBusBoard","MdBusBoard", "PmBusBoard"]) # Bus Boarding
        self.GenSkimDictFare(eb, BusFarDict, ["AmBusFare", "MdBusFare",  "PmBusFare"]) # Bus Fare

       # Blend Factors
        BlendDict = {   #AM,   MD,   PM         AM,   MD,   PM         Where Blended Matrices get stored in same order as above
         'hbwo':{'PA': hbwo_fct[0], 'AP':hbwo_fct[1], 'Mat':['HbWBlBusIvtt', 'HbWBlBusWait', 'HbWBlBusAux', 'HbWBlBusBoard']},  # Home-base work
         'hbun':{'PA': hbun_fct[0], 'AP':hbun_fct[1], 'Mat':['HbUBlBusIvtt', 'HbUBlBusWait', 'HbUBlBusAux', 'HbUBlBusBoard']},  # Home-base university
         'hbsc':{'PA': hbsc_fct[0], 'AP':hbsc_fct[1], 'Mat':['HbScBlBusIvtt', 'HbScBlBusWait', 'HbScBlBusAux', 'HbScBlBusBoard']},  # Home-base school
         'hbsh':{'PA': hbsh_fct[0], 'AP':hbsh_fct[1], 'Mat':['HbShBlBusIvtt', 'HbShBlBusWait', 'HbShBlBusAux', 'HbShBlBusBoard']},  # Home-base shopping
         'hbpb':{'PA': hbpb_fct[0], 'AP':hbpb_fct[1], 'Mat':['HbPbBlBusIvtt', 'HbPbBlBusWait', 'HbPbBlBusAux', 'HbPbBlBusBoard']},  # Home-base pb
         'hbso':{'PA': hbso_fct[0], 'AP':hbso_fct[1], 'Mat':['HbSoBlBusIvtt', 'HbSoBlBusWait', 'HbSoBlBusAux', 'HbSoBlBusBoard']},  # Home-base social
         'hbes':{'PA': hbes_fct[0], 'AP':hbes_fct[1], 'Mat':['HbEsBlBusIvtt', 'HbEsBlBusWait', 'HbEsBlBusAux', 'HbEsBlBusBoard']},  # Home-base escorting
         'nhbw':{'PA': nhbw_fct[0], 'AP':nhbw_fct[1], 'Mat':['NHbWBlBusIvtt', 'NHbWBlBusWait', 'NHbWBlBusAux', 'NHbWBlBusBoard']},  # Non-home base work
         'nhbo':{'PA': nhbo_fct[0], 'AP':nhbo_fct[1], 'Mat':['NHbOBlBusIvtt', 'NHbOBlBusWait', 'NHbOBlBusAux', 'NHbOBlBusBoard']}}  # Non-home base other

        BlendFareDict = {
         'trfrhbwo':{'PA': trfr_hbwo_fct[0], 'AP':trfr_hbwo_fct[1], 'Mat':['HbWBlBusFare']}, # fare blends
         'trfrhbun':{'PA': trfr_hbun_fct[0], 'AP':trfr_hbun_fct[1], 'Mat':['HbUBlBusFare']},
         'trfrhbsc':{'PA': trfr_hbsc_fct[0], 'AP':trfr_hbsc_fct[1], 'Mat':['HbScBlBusFare']},
         'trfrhbsh':{'PA': trfr_hbsh_fct[0], 'AP':trfr_hbsh_fct[1], 'Mat':['HbShBlBusFare']},
         'trfrhbpb':{'PA': trfr_hbpb_fct[0], 'AP':trfr_hbpb_fct[1], 'Mat':['HbPbBlBusFare']},
         'trfrhbso':{'PA': trfr_hbso_fct[0], 'AP':trfr_hbso_fct[1], 'Mat':['HbSoBlBusFare']},
         'trfrhbes':{'PA': trfr_hbes_fct[0], 'AP':trfr_hbes_fct[1], 'Mat':['HbEsBlBusFare']},
         'trfrnhbw':{'PA': trfr_nhbw_fct[0], 'AP':trfr_nhbw_fct[1], 'Mat':['NHbWBlBusFare']},
         'trfrnhbo':{'PA': trfr_nhbo_fct[0], 'AP':trfr_nhbo_fct[1], 'Mat':['NHbOBlBusFare']}}

        for keys, values in BlendDict.items():
            # Calculate blended skims
            Df = {}
            Df['BusIVT']  = self.calc_blend(values, BusIVTDict)
            Df['BusWat']  = self.calc_blend(values, BusWatDict)
            Df['BusAux']  = self.calc_blend(values, BusAuxDict)
            Df['BusBrd']  = self.calc_blend(values, BusBrdDict)

            # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['BusIVT'])
            util.set_matrix_numpy(eb, values['Mat'][1], Df['BusWat'])
            util.set_matrix_numpy(eb, values['Mat'][2], Df['BusAux'])
            util.set_matrix_numpy(eb, values['Mat'][3], Df['BusBrd'])


        for keys, values in BlendFareDict.items():
            # Calculate blended fares
            Df = {}
            Df['BusFar']  = self.calc_blend(values, BusFarDict)
            if keys == "trfrhbwo":
                Temp_Fare = Df['BusFar'].flatten()

            util.set_matrix_numpy(eb, values['Mat'][0], Df['BusFar'])


       ##############################################################################
       ##       Park and Ride Home-base Work/Uni/Soc Bus-leg
       ##############################################################################
        BlendDictPR = { #AM,   MD,   PM         AM,   MD,   PM         Where Blended Matrices get stored in same order as above
         'hbwo':{'PA': hbwo_fct[0], 'AP':hbwo_fct[1],
         'Mat':['HbWBlBAuBusIvtt', 'HbWBlBAuBusWait', 'HbWBlBAuBusAux', 'HbWBlBAuBusBoard', 'HbWBlBAuBusFare'], 'BL': BLBsWk}
                      }
        for keys, values in BlendDictPR.items():

            Df = pd.DataFrame()
            # Generate data frame with Origin Destination and best lot
            Dfmerge = util.get_pd_ij_df(eb)
            Dfmerge['BL'] = values['BL']
            # Generate second data frame and attach to it blended
            Df_Bus_Leg = util.get_pd_ij_df(eb)
            Df_Bus_Leg['BusIVT'] = self.calc_blend(values, BusIVTDict).flatten()
            Df_Bus_Leg['BusWat'] = self.calc_blend(values, BusWatDict).flatten()
            Df_Bus_Leg['BusAux'] = self.calc_blend(values, BusAuxDict).flatten()
            Df_Bus_Leg['BusBrd'] = self.calc_blend(values, BusBrdDict).flatten()
            Df_Bus_Leg['BusFar'] = Temp_Fare
            # Join the two data frames based on skims from the Best Lot to the destination
            Df = pd.merge(Dfmerge, Df_Bus_Leg, left_on = ['BL', 'j'],
                     right_on = ['i', 'j'], how = 'left')
            # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['BusIVT'].reshape(NoTAZ,NoTAZ))
            util.set_matrix_numpy(eb, values['Mat'][1], Df['BusWat'].reshape(NoTAZ,NoTAZ))
            util.set_matrix_numpy(eb, values['Mat'][2], Df['BusAux'].reshape(NoTAZ,NoTAZ))
            util.set_matrix_numpy(eb, values['Mat'][3], Df['BusBrd'].reshape(NoTAZ,NoTAZ))
            util.set_matrix_numpy(eb, values['Mat'][4], Df['BusFar'].reshape(NoTAZ,NoTAZ))
        # delete data generated to free up memory
        del Df, Dfmerge, Df_Bus_Leg, BusIVTDict, BusWatDict, BusAuxDict, BusBrdDict, BusFarDict, Temp_Fare
#
#        ##############################################################################
#        ##       Rail Skims
#        ##############################################################################
        # Initialize In-vehicle, Wait, Auxiliary, Boarding and Fare Skim Dictionaries
        RalIVBDict, RalIVRDict, RalWatDict = {}, {}, {}
        RalAuxDict, RalBrdDict, RalFarDict = {}, {}, {}

        # Generate Skim Dictionaries
        #                                  AM    ,    MD   ,     PM
        self.GenSkimDict(eb, RalIVRDict, ["AmRailIvtt",    "MdRailIvtt",    "PmRailIvtt"]) # Rail IVR
        self.GenSkimDict(eb, RalIVBDict, ["AmRailIvttBus", "MdRailIvttBus", "PmRailIvttBus"]) # Rail IVB
        self.GenSkimDict(eb, RalWatDict, ["AmRailWait",    "MdRailWait",    "PmRailWait"]) # Rail Wait
        self.GenSkimDict(eb, RalAuxDict, ["AmRailAux",     "MdRailAux",     "PmRailAux"]) # Rail Aux
        self.GenSkimDict(eb, RalBrdDict, ["AmRailBoard",   "MdRailBoard",   "PmRailBoard"]) # Rail Boarding
        self.GenSkimDictFare(eb, RalFarDict, ["AmRailFare",    "MdRailFare",    "PmRailFare"]) # Rail Fare

        # Blend Factors
        BlendDict = {  #AM,   MD,   PM         AM,   MD,   PM
         'hbwo':{'PA': hbwo_fct[0], 'AP':hbwo_fct[1],
                 'Mat':['HbWBlRailIvtt', 'HbWBlRailIvttBus', 'HbWBlRailWait', 'HbWBlRailAux', 'HbWBlRailBoard']}, # Where Blended Matrices get stored in same order as above
         'hbun':{'PA': hbun_fct[0], 'AP':hbun_fct[1],
                 'Mat':['HbUBlRailIvtt', 'HbUBlRailIvttBus', 'HbUBlRailWait', 'HbUBlRailAux', 'HbUBlRailBoard']},
         'hbsc':{'PA': hbsc_fct[0], 'AP':hbsc_fct[1],
                 'Mat':['HbScBlRailIvtt', 'HbScBlRailIvttBus', 'HbScBlRailWait', 'HbScBlRailAux', 'HbScBlRailBoard']},
         'hbsh':{'PA': hbsh_fct[0], 'AP':hbsh_fct[1],
                 'Mat':['HbShBlRailIvtt', 'HbShBlRailIvttBus', 'HbShBlRailWait', 'HbShBlRailAux', 'HbShBlRailBoard']},
         'hbpb':{'PA': hbpb_fct[0], 'AP':hbpb_fct[1],
                 'Mat':['HbPbBlRailIvtt', 'HbPbBlRailIvttBus', 'HbPbBlRailWait', 'HbPbBlRailAux', 'HbPbBlRailBoard']},
         'hbso':{'PA': hbso_fct[0], 'AP':hbso_fct[1],
                 'Mat':['HbSoBlRailIvtt', 'HbSoBlRailIvttBus', 'HbSoBlRailWait', 'HbSoBlRailAux', 'HbSoBlRailBoard']},
         'hbes':{'PA': hbes_fct[0], 'AP':hbes_fct[1],
                 'Mat':['HbEsBlRailIvtt', 'HbEsBlRailIvttBus', 'HbEsBlRailWait', 'HbEsBlRailAux', 'HbEsBlRailBoard']},
         'nhbw':{'PA': nhbw_fct[0], 'AP':nhbw_fct[1],
                 'Mat':['NHbWBlRailIvtt', 'NHbWBlRailIvttBus', 'NHbWBlRailWait', 'NHbWBlRailAux', 'NHbWBlRailBoard']},
         'nhbo':{'PA': nhbo_fct[0], 'AP':nhbo_fct[1],
                 'Mat':['NHbOBlRailIvtt', 'NHbOBlRailIvttBus', 'NHbOBlRailWait', 'NHbOBlRailAux', 'NHbOBlRailBoard']}}

        BlendFareDict = {
         'trfrhbwo':{'PA': trfr_hbwo_fct[0], 'AP':trfr_hbwo_fct[1], 'Mat':['HbWBlRailFare']}, # fare blends
         'trfrhbun':{'PA': trfr_hbun_fct[0], 'AP':trfr_hbun_fct[1], 'Mat':['HbUBlRailFare']},
         'trfrhbsc':{'PA': trfr_hbsc_fct[0], 'AP':trfr_hbsc_fct[1], 'Mat':['HbScBlRailFare']},
         'trfrhbsh':{'PA': trfr_hbsh_fct[0], 'AP':trfr_hbsh_fct[1], 'Mat':['HbShBlRailFare']},
         'trfrhbpb':{'PA': trfr_hbpb_fct[0], 'AP':trfr_hbpb_fct[1], 'Mat':['HbPbBlRailFare']},
         'trfrhbso':{'PA': trfr_hbso_fct[0], 'AP':trfr_hbso_fct[1], 'Mat':['HbSoBlRailFare']},
         'trfrhbes':{'PA': trfr_hbes_fct[0], 'AP':trfr_hbes_fct[1], 'Mat':['HbEsBlRailFare']},
         'trfrnhbw':{'PA': trfr_nhbw_fct[0], 'AP':trfr_nhbw_fct[1], 'Mat':['NHbWBlRailFare']},
         'trfrnhbo':{'PA': trfr_nhbo_fct[0], 'AP':trfr_nhbo_fct[1], 'Mat':['NHbOBlRailFare']}}

        for keys, values in BlendDict.items():
            # Calculate blended skims
            Df = {}
            Df['RalIVR'] = self.calc_blend(values, RalIVRDict)
            Df['RalIVB'] = self.calc_blend(values, RalIVBDict)
            Df['RalWat'] = self.calc_blend(values, RalWatDict)
            Df['RalAux'] = self.calc_blend(values, RalAuxDict)
            Df['RalBrd'] = self.calc_blend(values, RalBrdDict)
            # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['RalIVR'])
            util.set_matrix_numpy(eb, values['Mat'][1], Df['RalIVB'])
            util.set_matrix_numpy(eb, values['Mat'][2], Df['RalWat'])
            util.set_matrix_numpy(eb, values['Mat'][3], Df['RalAux'])
            util.set_matrix_numpy(eb, values['Mat'][4], Df['RalBrd'])

        for keys, values in BlendFareDict.items():
            # Calculate blended fares
            Df = {}
            Df['RalFar']  = self.calc_blend(values, RalFarDict)
            if keys == "trfrhbwo":
                Temp_Fare = Df['RalFar'].flatten()

            util.set_matrix_numpy(eb, values['Mat'][0], Df['RalFar'])

#       ##############################################################################
#        ##       Park and Ride Home-base Work/Uni/Soc Rail-leg
#        ##############################################################################
        BlendDictPR = { #AM,   MD,   PM         AM,   MD,   PM
           'hbwo':{'PA': hbwo_fct[0], 'AP':hbwo_fct[1],
                 'Mat':['HbWBlRAuRailIvtt', 'HbWBlRAuRailIvttBus', 'HbWBlRAuRailWait', 'HbWBlRAuRailAux', 'HbWBlRAuRailBoard', 'HbWBlRAuRailFare'],
                        'BL': BLRlWk}, #Where Blended Matrices get stored in same order as above
                      }
        for keys, values in BlendDictPR.items():

            Df = pd.DataFrame()
            # Generate data frame with Origin Destination and best lot
            Dfmerge = util.get_pd_ij_df(eb)
            Dfmerge['BL'] = values['BL']
            # Generate second data frame and attach to it blended
            Df_Rail_Leg = util.get_pd_ij_df(eb)
            Df_Rail_Leg['RalIVR'] = self.calc_blend(values, RalIVRDict).flatten()
            Df_Rail_Leg['RalIVB'] = self.calc_blend(values, RalIVBDict).flatten()
            Df_Rail_Leg['RalWat'] = self.calc_blend(values, RalWatDict).flatten()
            Df_Rail_Leg['RalAux'] = self.calc_blend(values, RalAuxDict).flatten()
            Df_Rail_Leg['RalBrd'] = self.calc_blend(values, RalBrdDict).flatten()
            Df_Rail_Leg['RalFar'] = Temp_Fare
            # Join the two data frames based on skims from the Best Lot to the destination
            Df = pd.merge(Dfmerge, Df_Rail_Leg, left_on = ['BL', 'j'],
                     right_on = ['i', 'j'], how = 'left')
            # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['RalIVR'].reshape(NoTAZ,NoTAZ))
            util.set_matrix_numpy(eb, values['Mat'][1], Df['RalIVB'].reshape(NoTAZ,NoTAZ))
            util.set_matrix_numpy(eb, values['Mat'][2], Df['RalWat'].reshape(NoTAZ,NoTAZ))
            util.set_matrix_numpy(eb, values['Mat'][3], Df['RalAux'].reshape(NoTAZ,NoTAZ))
            util.set_matrix_numpy(eb, values['Mat'][4], Df['RalBrd'].reshape(NoTAZ,NoTAZ))
            util.set_matrix_numpy(eb, values['Mat'][5], Df['RalFar'].reshape(NoTAZ,NoTAZ))
        # delete data generated to free up memory
        del Df, Dfmerge, Df_Rail_Leg, RalIVBDict, RalIVRDict, RalWatDict, RalAuxDict, RalBrdDict, RalFarDict, Temp_Fare
#
#        ##############################################################################
#        ##       WCE Skims
#        ##############################################################################
#        # Initialize In-vehicle, Wait, Auxiliary, Boarding and Fare Skim Dictionaries
        WCEIVBDict, WCEIVRDict, WCEIVWDict = {}, {}, {}
        WCEWatDict, WCEAuxDict, WCEBrdDict = {}, {}, {}
        WCEFarDict = {}
#        # Generate Skim Dictionaries
#        #                                        AM ,    PM
        self.GenSkimDict(eb, WCEIVWDict, ["AmWceIvtt",    "MdWceIvtt"     , "PmWceIvtt"]) # WCE IVW
        self.GenSkimDict(eb, WCEIVRDict, ["AmWceIvttRail","MdWceIvttRail" , "PmWceIvttRail"]) # WCE IVR
        self.GenSkimDict(eb, WCEIVBDict, ["AmWceIvttBus", "MdWceIvttBus"  , "PmWceIvttBus"]) # WCE IVB
        self.GenSkimDict(eb, WCEWatDict, ["AmWceWait",    "MdWceWait"     , "PmWceWait"]) # WCE Wait
        self.GenSkimDict(eb, WCEAuxDict, ["AmWceAux",     "MdWceAux"      , "PmWceAux"]) # WCE Aux
        self.GenSkimDict(eb, WCEBrdDict, ["AmWceBoard",  "MdWceBoard"   , "PmWceBoard"]) # WCE Boarding
        self.GenSkimDict(eb, WCEFarDict, ["AmWceFare",    "MdWceFare"     , "PmWceFare"])   # WCE Fare

#        # Blend Factors
        BlendDict = {    #AM,   PM,        AM,   PM,
         'hbwo':{'PA': hbwo_fct_wce[0], 'AP':hbwo_fct_wce[1],
                 'Mat':['HbWBlWceIvtt', 'HbWBlWceIvttRail', 'HbWBlWceIvttBus', 'HbWBlWceWait', 'HbWBlWceAux', 'HbWBlWceBoard', 'HbWBlWceFare']},  # Where Blended Matrices get stored in same order as above
                    }

        for keys, values in BlendDict.items():
            # Calculate blended skims
            Df = {}
            Df['WCEIVW'] = self.calc_blend(values, WCEIVWDict)
            Df['WCEIVR'] = self.calc_blend(values, WCEIVRDict)
            Df['WCEIVB'] = self.calc_blend(values, WCEIVBDict)

            Df['WCEWat'] = self.calc_blend(values, WCEWatDict)
            Df['WCEAux'] = self.calc_blend(values, WCEAuxDict)
            Df['WCEBrd'] = self.calc_blend(values, WCEBrdDict)
            Df['WCEFar'] = self.calc_blend(values, WCEFarDict)
            # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['WCEIVW'])
            util.set_matrix_numpy(eb, values['Mat'][1], Df['WCEIVR'])
            util.set_matrix_numpy(eb, values['Mat'][2], Df['WCEIVB'])
            util.set_matrix_numpy(eb, values['Mat'][3], Df['WCEWat'])
            util.set_matrix_numpy(eb, values['Mat'][4], Df['WCEAux'])
            util.set_matrix_numpy(eb, values['Mat'][5], Df['WCEBrd'])
            util.set_matrix_numpy(eb, values['Mat'][6], Df['WCEFar'])
#        ##############################################################################
#        ##       Park and Ride Home-base Work/Uni/Soc WCE-leg
#        ##############################################################################
        BlendDictPR = { #AM,   PM,        AM,   PM,
         'hbwo':{'PA': hbwo_fct_wce[0], 'AP':hbwo_fct_wce[1],  'BL': BLWcWk,
                 'Mat':['HbWBlWAuWceIvtt', 'HbWBlWAuWceIvttRail', 'HbWBlWAuWceIvttBus',
                        'HbWBlWAuWceWait', 'HbWBlWAuWceAux', 'HbWBlWAuWceBoards', 'HbWBlWAuWceFare']} # Where Blended Matrices get stored in same order as above
                      }

        for keys, values in BlendDictPR.items():

            Df = pd.DataFrame()
            # Generate data frame with Origin Destination and best lot
            Dfmerge = util.get_pd_ij_df(eb)
            Dfmerge['BL'] = values['BL']
            # Generate second data frame and attach to it blended
            Df_WCE_Leg = util.get_pd_ij_df(eb)
            Df_WCE_Leg['WCEIVW'] = self.calc_blend(values, WCEIVWDict).flatten()
            Df_WCE_Leg['WCEIVR'] = self.calc_blend(values, WCEIVRDict).flatten()
            Df_WCE_Leg['WCEIVB'] = self.calc_blend(values, WCEIVBDict).flatten()
            Df_WCE_Leg['WCEWat'] = self.calc_blend(values, WCEWatDict).flatten()
            Df_WCE_Leg['WCEAux'] = self.calc_blend(values, WCEAuxDict).flatten()
            Df_WCE_Leg['WCEBrd'] = self.calc_blend(values, WCEBrdDict).flatten()
            Df_WCE_Leg['WCEFar'] = self.calc_blend(values, WCEFarDict).flatten()
             # Join the two data frames based on skims from the Best Lot to the destination
            Df = pd.merge(Dfmerge, Df_WCE_Leg, left_on = ['BL', 'j'],
                     right_on = ['i', 'j'], how = 'left')
            # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['WCEIVW'].reshape(NoTAZ,NoTAZ))
            util.set_matrix_numpy(eb, values['Mat'][1], Df['WCEIVR'].reshape(NoTAZ,NoTAZ))
            util.set_matrix_numpy(eb, values['Mat'][2], Df['WCEIVB'].reshape(NoTAZ,NoTAZ))
            util.set_matrix_numpy(eb, values['Mat'][3], Df['WCEWat'].reshape(NoTAZ,NoTAZ))
            util.set_matrix_numpy(eb, values['Mat'][4], Df['WCEAux'].reshape(NoTAZ,NoTAZ))
            util.set_matrix_numpy(eb, values['Mat'][5], Df['WCEBrd'].reshape(NoTAZ,NoTAZ))
            util.set_matrix_numpy(eb, values['Mat'][6], Df['WCEFar'].reshape(NoTAZ,NoTAZ))
        # delete data generated to free up memory
        del Df, Dfmerge, Df_WCE_Leg, WCEIVBDict, WCEIVRDict, WCEIVWDict, WCEWatDict, WCEAuxDict, WCEBrdDict, WCEFarDict

#        ##############################################################################
#        ##       Functions
#        ##############################################################################

    def GenSkimDict(self, eb, Dict, Mat):
        util = _m.Modeller().tool("translink.util")
        AM_Mat = util.get_matrix_numpy(eb, Mat[0])
        MD_Mat = util.get_matrix_numpy(eb, Mat[1])
        PM_Mat = util.get_matrix_numpy(eb, Mat[2])
        Dict['PA'] = [AM_Mat, MD_Mat, PM_Mat]
        Dict['AP'] = [AM_Mat.transpose(), MD_Mat.transpose(), PM_Mat.transpose()]
        return (Dict)

    def GenSkimDictFare(self, eb, Dict, Mat):
        util = _m.Modeller().tool("translink.util")
        NoTAZ  = len(util.get_matrix_numpy(eb, "zoneindex")) # Number of TAZs in Model
        AM_Mat = util.get_matrix_numpy(eb, Mat[0])
        MD_Mat = util.get_matrix_numpy(eb, Mat[1])
        PM_Mat = util.get_matrix_numpy(eb, Mat[2])
        OP_Mat = util.get_matrix_numpy(eb, "oneZoneFare")

        Dict['PA'] = [AM_Mat, MD_Mat, PM_Mat, OP_Mat]
        Dict['AP'] = [AM_Mat.transpose(), MD_Mat.transpose(), PM_Mat.transpose(), OP_Mat.transpose()]
        return (Dict)

    def calc_blend(self, Fact, Dict):
        util = _m.Modeller().tool("translink.util")
        Result = util.sumproduct(Fact['PA'], Dict['PA']) + util.sumproduct(Fact['AP'], Dict['AP'])

        return Result

    def get_fact(self, eb, FactList):

        util = _m.Modeller().tool("translink.util")
        PA_List = np.array([
                            float(util.get_matrix_numpy(eb, FactList[0][0])),
                            float(util.get_matrix_numpy(eb, FactList[0][1])),
                            float(util.get_matrix_numpy(eb, FactList[0][2]))
                           ])

        AP_List = np.array([
                            float(util.get_matrix_numpy(eb, FactList[1][0])),
                            float(util.get_matrix_numpy(eb, FactList[1][1])),
                            float(util.get_matrix_numpy(eb, FactList[1][2]))
                           ])
        return np.array([PA_List, AP_List])

    def get_fact_fare(self, eb, FactList):

        util = _m.Modeller().tool("translink.util")
        PA_List = np.array([
                            float(util.get_matrix_numpy(eb, FactList[0][0])),
                            float(util.get_matrix_numpy(eb, FactList[0][1])),
                            float(util.get_matrix_numpy(eb, FactList[0][2])),
                            float(util.get_matrix_numpy(eb, FactList[0][3]))
                           ])

        AP_List = np.array([
                            float(util.get_matrix_numpy(eb, FactList[1][0])),
                            float(util.get_matrix_numpy(eb, FactList[1][1])),
                            float(util.get_matrix_numpy(eb, FactList[1][2])),
                            float(util.get_matrix_numpy(eb, FactList[1][3]))
                           ])
        return np.array([PA_List, AP_List])



    @_m.logbook_trace("Park & Ride - Choose Best Lot")
    def bestlot(self, eb, year):
        compute_lot = _m.Modeller().tool(
            "inro.emme.matrix_calculation.matrix_triple_index_operation")

        # explictly set lot ensemble - will have different lots in 2011 and future
        # gn1 exist in 2011 and future
        # gn2 exist only in 2011
        # gn3 exist only in future

        if year == 2011:
        #    intermediates = 'gn1;gn2'
            intermediates = 'gn1;gn2'
        else:
        #    intermediates = 'gn1;gn3'
            intermediates = 'gn1;gn3'
        # defining dictionaries to keep matrix references explicit
        # matrices needed for calulcation
        # generalized time for auto and transit legs
        # work uses am for all modes
        # non-work uses md for bus and rail and am for WCE (there is no md WCE)

        legs = {
                "work" : {"auto" : "mf6003",
                         "bus" : "mf6005",
                         "rail" : "mf6015",
                         "wce" : "mf6030"},
                "nonwork" : {"auto" : "mf6173",
                             "bus" : "mf6175",
                             "rail" : "mf6185",
                             "wce" : "mf6030"}
                }

        # generalized time of minimum auto-lot-transit route
        # not used, but required by triple index operation
        min_gt = {
                "work" : {"bus" : "mf6006",
                         "rail" : "mf6016",
                         "wce" : "mf6031"},
                "nonwork" : {"bus" : "mf6176",
                             "rail" : "mf6186",
                             "wce" : "mf6201"}
                }
        # lot choice dictionary
        lot_choice = {
                "work" : {"bus" : "mf6000",
                         "rail" : "mf6001",
                         "wce" : "mf6002"},
                "nonwork" : {"bus" : "mf6130",
                             "rail" : "mf6131",
                             "wce" : "mf6132"}
                }

        spec  = {
            "pk_operand": "AutoLeg",
            "kq_operand": "TransitLeg",
            "qk_operand": None,
            "combination_operator": "+",
            "masks": [],
            "contraction_operator": ".min.",
            "result": 'MinGT',
            "index_result": "BestLot",
            "constraint": {
                "by_zone": {
                    "intermediates": intermediates,
                    "origins": "all",
                    "destinations": "all"
                },
                "by_value": None
            },
            "type": "MATRIX_TRIPLE_INDEX_OPERATION"
        }

        # explictly set lot ensemble - will have different lots in 2011 and future
        # gn1 exist in 2011 and future
        # gn2 exist only in 2011
        # gn3 exist only in future


        # work uses AM
        # note, auto skim is same for all transit modes

        # calculate bus best lot work
        spec["pk_operand"] = legs['work']['auto']
        spec["kq_operand"] = legs['work']['bus']
        spec["result"] = min_gt['work']['bus']
        spec["index_result"] = lot_choice['work']['bus']
        compute_lot(spec)

        # calculate rail best lot work
        spec["kq_operand"] = legs['work']['rail']
        spec["result"] = min_gt['work']['rail']
        spec["index_result"] = lot_choice['work']['rail']
        compute_lot(spec)

        # calculate west coast express best lot work
        spec["kq_operand"] = legs['work']['wce']
        spec["result"] = min_gt['work']['wce']
        spec["index_result"] = lot_choice['work']['wce']
        compute_lot(spec)


        # calculate bus best lot nonwork
        spec["pk_operand"] = legs['nonwork']['auto']
        spec["kq_operand"] = legs['nonwork']['bus']
        spec["result"] = min_gt['nonwork']['bus']
        spec["index_result"] = lot_choice['nonwork']['bus']
        compute_lot(spec)

        # calculate rail best lot nonwork
        spec["kq_operand"] = legs['nonwork']['rail']
        spec["result"] = min_gt['nonwork']['rail']
        spec["index_result"] = lot_choice['nonwork']['rail']
        compute_lot(spec)

        # calculate west coast express best lot nonwork
        # west coast express no midday, uses am and needs AM auto skim brought back
        spec["pk_operand"] = legs['work']['auto']
        spec["kq_operand"] = legs['nonwork']['wce']
        spec["result"] = min_gt['nonwork']['wce']
        spec["index_result"] = lot_choice['nonwork']['wce']
        compute_lot(spec)

    @_m.logbook_trace("Park and Ride Calculate West Coast Express Generalized Time")
    def WceGT(self, eb):
        util = _m.Modeller().tool("translink.util")
        # [AM,MD,PM]
        transit_mats = {"wceIVT" : ["AmWceIvtt",  "MdWceIvtt", "PmWceIvtt"],
                        "wceWait" : ["AmWceWait",  "MdWceWait", "PmWceWait"],
                        "railIVT" : ["AmWceIvttRail",  "MdWceIvttRail", "PmWceIvttRail"],
                        "busIVT" : ["AmWceIvttBus",  "MdWceIvttBus", "PmWceIvttBus"],
                        "auxTransit" : ["AmWceAux",  "MdWceAux", "PmWceAux"],
                        "boardings" : ["AmWceBoard",  "MdWceBoard", "PmWceBoard"],
                        "wceFare" : ["AmWceFare",  "MdWceFare", "PmWceFare"]}

        # [Work, non-work]
        vot_mats = ['VotWce', 'VotWce']

        # [[AMWk, MDWk, PMWk],[AMnonWk, MDnonWk, PMnonWk]]
        result_mats = [["mf6030",  "mf6075", "mf6115"],["mf6160",  "mf6200", "mf6240"]]

        #calculate generalized time for bus leg
        specs = []
        for i in range(0,3):
            for j in range(0,2):
                expression = ("{wceIVT} * {wceIVTprcp}"
                              " + {wceWait} * {wceOVTprcp}"
                              " + {railIVT} * {railIVTprcp}"
                              " + {busIVT} * {busIVTprcp}"
                              " + {auxTrans} * {walkprcp}"
                              " + {boardings} * {transferprcp} "
                              " + {fare} * {VOT}"
                              ).format(wceIVT=transit_mats["wceIVT"][i],
                                       wceWait=transit_mats["wceWait"][i],
                                       railIVT=transit_mats["railIVT"][i],
                                       busIVT=transit_mats["busIVT"][i],
                                       auxTrans=transit_mats["auxTransit"][i],
                                       boardings=transit_mats["boardings"][i],
                                       fare=transit_mats["wceFare"][i],
                                       wceIVTprcp="wceIVTprcpWk",
                                       wceOVTprcp="wceWAITprcpWk",
                                       railIVTprcp="railIVTprcpWk",
                                       busIVTprcp="busIVTprcpWk",
                                       walkprcp="wceWALKprcpWk",
                                       transferprcp="wceBOARDSprcpWk",
                                       VOT=vot_mats[j])

                result = ("{wceGT}").format(wceGT=result_mats[j][i])
                specs.append(util.matrix_spec(result, expression))
        util.compute_matrix(specs)

    @_m.logbook_trace("Park & Ride Calculate Rail Generatized Time")
    def RailGT(self, eb):
        util = _m.Modeller().tool("translink.util")
        # [AM,MD,PM]
        transit_mats = {"railIVT" :    ["AmRailIvtt",    "MdRailIvtt", "PmRailIvtt"],
                        "railWait" :   ["AmRailWait",    "MdRailWait", "PmRailWait"],
                        "busIVT" :     ["AmRailIvttBus", "MdRailIvttBus", "PmRailIvttBus"],
                        "auxTransit" : ["AmRailAux",     "MdRailAux", "PmRailAux"],
                        "boardings" :  ["AmRailBoard",   "MdRailBoard", "PmRailBoard"],
                        "railFare" :   ["AmRailFare",    "MdRailFare", "PmRailFare"]}

        # [Work, non-work]
        vot_mats = ['VotRail', 'VotRail']

        # [[AMWk, MDWk, PMWk],[AMnonWk, MDnonWk, PMnonWk]]
        result_mats = [["mf6015", "mf6060", "mf6100"],['mf6145','mf6185','mf6225']]

        #calculate generalized time for bus leg
        specs = []
        for i in range(0,3):
            for j in range(0,2):
                expression = ("{railIVT} * {railIVTprcp}"
                              " + {railWait} * {railOVTprcp}"
                              " + {busIVT} * {busIVTprcp}"
                              " + {auxTrans} * {walkprcp}"
                              " + {boardings} * {transferprcp} "
                              " + {fare} * {VOT}"
                              ).format(railIVT=transit_mats["railIVT"][i],
                                       railWait=transit_mats["railWait"][i],
                                       busIVT=transit_mats["busIVT"][i],
                                       auxTrans=transit_mats["auxTransit"][i],
                                       boardings=transit_mats["boardings"][i],
                                       fare=transit_mats["railFare"][i],
                                       railIVTprcp="railIVTprcpWk",
                                       railOVTprcp="railWAITprcpWk",
                                       busIVTprcp="busIVTprcpWk",
                                       walkprcp="railWALKprcpWk",
                                       transferprcp="railBOARDSprcpWk",
                                       VOT=vot_mats[j])

                result = ("{railGT}").format(railGT=result_mats[j][i])
                specs.append(util.matrix_spec(result, expression))
        util.compute_matrix(specs)

    @_m.logbook_trace("Park & Ride Calculate Bus Generalized Time")
    def BusGT(self, eb):
        util = _m.Modeller().tool("translink.util")
        # [AM,MD,PM]
        transit_mats = {"busIVT" : ["AmBusIvtt",  "MdBusIvtt", "PmBusIvtt"],
                        "busWait" : ["AmBusWait",  "MdBusWait", "PmBusWait"],
                        "auxTransit" : ["AmBusAux", "MdBusAux", "PmBusAux"],
                        "boardings" : ["AmBusBoard", "MdBusBoard", "PmBusBoard"],
                        "busFare" : ["AmBusFare",  "MdBusFare", "PmBusFare"]}

        # [Work, non-work]
        vot_mats = ['VotBus', 'VotBus']

        # [[AMWk, MDWk, PMWk],[AMnonWk, MDnonWk, PMnonWk]]
        result_mats = [["mf6005", "mf6050", "mf6090"],['mf6135','mf6175','mf6215']]

        #calculate generalized time for bus leg
        specs = []
        for i in range(0,3):
            for j in range(0,2):
                expression = ("{busIVT} * {busIVTprcp}"
                              " + {busWait} * {busOVTprcp}"
                              " + {auxTrans} * {walkprcp}"
                              " + {boardings} * {transferprcp} "
                              " + {fare} * {VOT}"
                              ).format(busIVT=transit_mats["busIVT"][i],
                                       busWait=transit_mats["busWait"][i],
                                       auxTrans=transit_mats["auxTransit"][i],
                                       boardings=transit_mats["boardings"][i],
                                       fare=transit_mats["busFare"][i],
                                       busIVTprcp="busIVTprcpWk",
                                       busOVTprcp="busWAITprcpWk",
                                       walkprcp="busWALKprcpWk",
                                       transferprcp="busBOARDSprcpWk",
                                       VOT=vot_mats[j])

                result = ("{busGT}").format(busGT=result_mats[j][i])
                specs.append(util.matrix_spec(result, expression))
        util.compute_matrix(specs)

    @_m.logbook_trace("Park & Ride Calculate Auto Generalized Time")
    def AutoGT(self, eb):
        util = _m.Modeller().tool("translink.util")

        # work trips - not ideal formulation but quick and gets it done
        # [AM,MD,PM]
        auto_mats = {"autotime" : ["AmSovTimeVOT4",  "MdSovTimeVOT4", "PmSovTimeVOT4"],
                    "autocost" : ["mfAmSovOpCstVOT4", "mfMdSovOpCstVOT4", "mfPmSovOpCstVOT4"]}

        # [Work, non-work]
        vot_mat = 'AutoVOT4'
        auto_prcp = 'pr_auto_time_prcp'

        # [AMWk, MDWk, PMWk]
        result_mats = ["mf6003", "mf6048", "mf6088"]

        specs = []
        for i in range(0,3):
            expression = ("{autotime}*{perception} + {termtime}"
                          " + ({autocost} + {lotcost}) * {VOT}"
                          ).format(autotime=auto_mats["autotime"][i],
                                   autocost=auto_mats["autocost"][i],
                                   perception = auto_prcp,
                                   VOT=vot_mat,
                                   lotcost = "mo90'",
                                   termtime = "mo92'")

            result = ("{autoGT}").format(autoGT=result_mats[i])
            specs.append(util.matrix_spec(result, expression))
        util.compute_matrix(specs)



        auto_mats = {"autotime" : ["AmSovTimeVOT3",  "MdSovTimeVOT3", "PmSovTimeVOT3"],
                    "autocost" : ["mfAmSovOpCstVOT3", "mfMdSovOpCstVOT3", "mfPmSovOpCstVOT3"]}

        # [Work, non-work]
        vot_mat = 'AutoVOT3'
        auto_prcp = 'pr_auto_time_prcp'
        # [[AMWk, MDWk, PMWk],[AMnonWk, MDnonWk, PMnonWk]]
        result_mats = ['mf6133','mf6173','mf6213']

        specs = []
        for i in range(0,3):
            expression = ("{autotime}*{perception} + {termtime}"
                          " + ({autocost} + {lotcost}) * {VOT}"
                          ).format(autotime=auto_mats["autotime"][i],
                                   autocost=auto_mats["autocost"][i],
                                   perception = auto_prcp,
                                   VOT=vot_mat,
                                   lotcost = "mo90'",
                                   termtime = "mo92'")

            result = ("{autoGT}").format(autoGT=result_mats[i])
            specs.append(util.matrix_spec(result, expression))
        util.compute_matrix(specs)

    @_m.logbook_trace("Park & Ride - Read Input Files")
    def read_file(self, eb, file):
        util = _m.Modeller().tool("translink.util")
        #Read data from file and check number of lines
        with open(file, "rb") as sourcefile:
            lines = list(csv.reader(sourcefile, skipinitialspace=True))

        matrices = []
        mat_data = []
        # Initialize all matrices with 0-values and store a data reference
        for i in range(1, len(lines[0])):
            mat = util.initmat(eb, lines[0][i], lines[1][i], lines[2][i], 0)
            matrices.append(mat)
            mat_data.append(mat.get_data())

        # loop over each data-containing line in the csv
        for i in range(3, len(lines)):
            line = lines[i]
            # within each line set the data in each matrix
            for j in range(1, len(line)):
                mat_data[j-1].set(int(line[0]), float(line[j]))

        # store the data back into the matrix on disk
        for i in range(len(matrices)):
            matrices[i].set_data(mat_data[i])


    @_m.logbook_trace("Initialize Matrices")
    def matrix_batchins(self, eb):
        util = _m.Modeller().tool("translink.util")

        ###################
        # Blended Skims
        ###################

        util.initmat(eb, "mf5100", "HbWBlSovCost_I1", "HbW Bl Sov Cost_Low_Income", 0)
        util.initmat(eb, "mf5101", "HbWBlSovTime_I1", "HbW Bl Sov Time_Low_Income", 0)
        util.initmat(eb, "mf5102", "HbWBlSovToll_I1", "HbW Bl Sov Toll_Low_Income", 0)
        util.initmat(eb, "mf5103", "HbWBlSovCost_I2", "HbW Bl Sov Cost_Med_Income", 0)
        util.initmat(eb, "mf5104", "HbWBlSovTime_I2", "HbW Bl Sov Time_Med_Income", 0)
        util.initmat(eb, "mf5105", "HbWBlSovToll_I2", "HbW Bl Sov Toll_Med_Income", 0)
        util.initmat(eb, "mf5106", "HbWBlSovCost_I3", "HbW Bl Sov Cost_High_Income", 0)
        util.initmat(eb, "mf5107", "HbWBlSovTime_I3", "HbW Bl Sov Time_High_Income", 0)
        util.initmat(eb, "mf5108", "HbWBlSovToll_I3", "HbW Bl Sov Toll_High_Income", 0)
        util.initmat(eb, "mf5110", "HbWBlHovCost_I1", "HbW Bl Hov Cost_Low_Income", 0)
        util.initmat(eb, "mf5111", "HbWBlHovTime_I1", "HbW Bl Hov Time_Low_Income", 0)
        util.initmat(eb, "mf5112", "HbWBlHovToll_I1", "HbW Bl Hov Toll_Low_Income", 0)
        util.initmat(eb, "mf5113", "HbWBlHovCost_I2", "HbW Bl Hov Cost_Med_Income", 0)
        util.initmat(eb, "mf5114", "HbWBlHovTime_I2", "HbW Bl Hov Time_Med_Income", 0)
        util.initmat(eb, "mf5115", "HbWBlHovToll_I2", "HbW Bl Hov Toll_Med_Income", 0)
        util.initmat(eb, "mf5116", "HbWBlHovCost_I3", "HbW Bl Hov Cost_High_Income", 0)
        util.initmat(eb, "mf5117", "HbWBlHovTime_I3", "HbW Bl Hov Time_High_Income", 0)
        util.initmat(eb, "mf5118", "HbWBlHovToll_I3", "HbW Bl Hov Toll_High_Income", 0)
        util.initmat(eb, "mf5120", "HbShBlSovCost_I1", "HbSh Bl Sov Cost_Low_Income", 0)
        util.initmat(eb, "mf5121", "HbShBlSovTime_I1", "HbSh Bl Sov Time_Low_Income", 0)
        util.initmat(eb, "mf5122", "HbShBlSovToll_I1", "HbSh Bl Sov Toll_Low_Income", 0)
        util.initmat(eb, "mf5123", "HbShBlSovCost_I2", "HbSh Bl Sov Cost_Med_Income", 0)
        util.initmat(eb, "mf5124", "HbShBlSovTime_I2", "HbSh Bl Sov Time_Med_Income", 0)
        util.initmat(eb, "mf5125", "HbShBlSovToll_I2", "HbSh Bl Sov Toll_Med_Income", 0)
        util.initmat(eb, "mf5126", "HbShBlSovCost_I3", "HbSh Bl Sov Cost_High_Income", 0)
        util.initmat(eb, "mf5127", "HbShBlSovTime_I3", "HbSh Bl Sov Time_High_Income", 0)
        util.initmat(eb, "mf5128", "HbShBlSovToll_I3", "HbSh Bl Sov Toll_High_Income", 0)
        util.initmat(eb, "mf5130", "HbShBlHovCost_I1", "HbSh Bl Hov Cost_Low_Income", 0)
        util.initmat(eb, "mf5131", "HbShBlHovTime_I1", "HbSh Bl Hov Time_Low_Income", 0)
        util.initmat(eb, "mf5132", "HbShBlHovToll_I1", "HbSh Bl Hov Toll_Low_Income", 0)
        util.initmat(eb, "mf5133", "HbShBlHovCost_I2", "HbSh Bl Hov Cost_Med_Income", 0)
        util.initmat(eb, "mf5134", "HbShBlHovTime_I2", "HbSh Bl Hov Time_Med_Income", 0)
        util.initmat(eb, "mf5135", "HbShBlHovToll_I2", "HbSh Bl Hov Toll_Med_Income", 0)
        util.initmat(eb, "mf5136", "HbShBlHovCost_I3", "HbSh Bl Hov Cost_High_Income", 0)
        util.initmat(eb, "mf5137", "HbShBlHovTime_I3", "HbSh Bl Hov Time_High_Income", 0)
        util.initmat(eb, "mf5138", "HbShBlHovToll_I3", "HbSh Bl Hov Toll_High_Income", 0)
        util.initmat(eb, "mf5140", "HbPbBlSovCost_I1", "HbPb Bl Sov Cost_Low_Income", 0)
        util.initmat(eb, "mf5141", "HbPbBlSovTime_I1", "HbPb Bl Sov Time_Low_Income", 0)
        util.initmat(eb, "mf5142", "HbPbBlSovToll_I1", "HbPb Bl Sov Toll_Low_Income", 0)
        util.initmat(eb, "mf5143", "HbPbBlSovCost_I2", "HbPb Bl Sov Cost_Med_Income", 0)
        util.initmat(eb, "mf5144", "HbPbBlSovTime_I2", "HbPb Bl Sov Time_Med_Income", 0)
        util.initmat(eb, "mf5145", "HbPbBlSovToll_I2", "HbPb Bl Sov Toll_Med_Income", 0)
        util.initmat(eb, "mf5146", "HbPbBlSovCost_I3", "HbPb Bl Sov Cost_High_Income", 0)
        util.initmat(eb, "mf5147", "HbPbBlSovTime_I3", "HbPb Bl Sov Time_High_Income", 0)
        util.initmat(eb, "mf5148", "HbPbBlSovToll_I3", "HbPb Bl Sov Toll_High_Income", 0)
        util.initmat(eb, "mf5150", "HbPbBlHovCost_I1", "HbPb Bl Hov Cost_Low_Income", 0)
        util.initmat(eb, "mf5151", "HbPbBlHovTime_I1", "HbPb Bl Hov Time_Low_Income", 0)
        util.initmat(eb, "mf5152", "HbPbBlHovToll_I1", "HbPb Bl Hov Toll_Low_Income", 0)
        util.initmat(eb, "mf5153", "HbPbBlHovCost_I2", "HbPb Bl Hov Cost_Med_Income", 0)
        util.initmat(eb, "mf5154", "HbPbBlHovTime_I2", "HbPb Bl Hov Time_Med_Income", 0)
        util.initmat(eb, "mf5155", "HbPbBlHovToll_I2", "HbPb Bl Hov Toll_Med_Income", 0)
        util.initmat(eb, "mf5156", "HbPbBlHovCost_I3", "HbPb Bl Hov Cost_High_Income", 0)
        util.initmat(eb, "mf5157", "HbPbBlHovTime_I3", "HbPb Bl Hov Time_High_Income", 0)
        util.initmat(eb, "mf5158", "HbPbBlHovToll_I3", "HbPb Bl Hov Toll_High_Income", 0)
        util.initmat(eb, "mf5160", "HbSoBlSovCost_I1", "HbSo Bl Sov Cost_Low_Income", 0)
        util.initmat(eb, "mf5161", "HbSoBlSovTime_I1", "HbSo Bl Sov Time_Low_Income", 0)
        util.initmat(eb, "mf5162", "HbSoBlSovToll_I1", "HbSo Bl Sov Toll_Low_Income", 0)
        util.initmat(eb, "mf5163", "HbSoBlSovCost_I2", "HbSo Bl Sov Cost_Med_Income", 0)
        util.initmat(eb, "mf5164", "HbSoBlSovTime_I2", "HbSo Bl Sov Time_Med_Income", 0)
        util.initmat(eb, "mf5165", "HbSoBlSovToll_I2", "HbSo Bl Sov Toll_Med_Income", 0)
        util.initmat(eb, "mf5166", "HbSoBlSovCost_I3", "HbSo Bl Sov Cost_High_Income", 0)
        util.initmat(eb, "mf5167", "HbSoBlSovTime_I3", "HbSo Bl Sov Time_High_Income", 0)
        util.initmat(eb, "mf5168", "HbSoBlSovToll_I3", "HbSo Bl Sov Toll_High_Income", 0)
        util.initmat(eb, "mf5170", "HbSoBlHovCost_I1", "HbSo Bl Hov Cost_Low_Income", 0)
        util.initmat(eb, "mf5171", "HbSoBlHovTime_I1", "HbSo Bl Hov Time_Low_Income", 0)
        util.initmat(eb, "mf5172", "HbSoBlHovToll_I1", "HbSo Bl Hov Toll_Low_Income", 0)
        util.initmat(eb, "mf5173", "HbSoBlHovCost_I2", "HbSo Bl Hov Cost_Med_Income", 0)
        util.initmat(eb, "mf5174", "HbSoBlHovTime_I2", "HbSo Bl Hov Time_Med_Income", 0)
        util.initmat(eb, "mf5175", "HbSoBlHovToll_I2", "HbSo Bl Hov Toll_Med_Income", 0)
        util.initmat(eb, "mf5176", "HbSoBlHovCost_I3", "HbSo Bl Hov Cost_High_Income", 0)
        util.initmat(eb, "mf5177", "HbSoBlHovTime_I3", "HbSo Bl Hov Time_High_Income", 0)
        util.initmat(eb, "mf5178", "HbSoBlHovToll_I3", "HbSo Bl Hov Toll_High_Income", 0)
        util.initmat(eb, "mf5200", "HbUBlSovCost", "HbU Bl Sov Cost", 0)
        util.initmat(eb, "mf5201", "HbUBlSovTime", "HbU Bl Sov Time", 0)
        util.initmat(eb, "mf5202", "HbUBlSovToll", "HbU Bl Sov Toll", 0)
        util.initmat(eb, "mf5205", "HbUBlHovCost", "HbU Bl Hov Cost", 0)
        util.initmat(eb, "mf5206", "HbUBlHovTime", "HbU Bl Hov Time", 0)
        util.initmat(eb, "mf5207", "HbUBlHovToll", "HbU Bl Hov Toll", 0)
        util.initmat(eb, "mf5210", "HbScBlSovCost", "HbSc Bl Sov Cost", 0)
        util.initmat(eb, "mf5211", "HbScBlSovTime", "HbSc Bl Sov Time", 0)
        util.initmat(eb, "mf5212", "HbScBlSovToll", "HbSc Bl Sov Toll", 0)
        util.initmat(eb, "mf5215", "HbScBlHovCost", "HbSc Bl Hov Cost", 0)
        util.initmat(eb, "mf5216", "HbScBlHovTime", "HbSc Bl Hov Time", 0)
        util.initmat(eb, "mf5217", "HbScBlHovToll", "HbSc Bl Hov Toll", 0)
        util.initmat(eb, "mf5220", "HbEsBlSovCost", "HbEs Bl Sov Cost", 0)
        util.initmat(eb, "mf5221", "HbEsBlSovTime", "HbEs Bl Sov Time", 0)
        util.initmat(eb, "mf5222", "HbEsBlSovToll", "HbEs Bl Sov Toll", 0)
        util.initmat(eb, "mf5225", "HbEsBlHovCost", "HbEs Bl Hov Cost", 0)
        util.initmat(eb, "mf5226", "HbEsBlHovTime", "HbEs Bl Hov Time", 0)
        util.initmat(eb, "mf5227", "HbEsBlHovToll", "HbEs Bl Hov Toll", 0)
        util.initmat(eb, "mf5230", "NHbWBlSovCost", "NHbW Bl Sov Cost", 0)
        util.initmat(eb, "mf5231", "NHbWBlSovTime", "NHbW Bl Sov Time", 0)
        util.initmat(eb, "mf5232", "NHbWBlSovToll", "NHbW Bl Sov Toll", 0)
        util.initmat(eb, "mf5235", "NHbWBlHovCost", "NHbW Bl Hov Cost", 0)
        util.initmat(eb, "mf5236", "NHbWBlHovTime", "NHbW Bl Hov Time", 0)
        util.initmat(eb, "mf5237", "NHbWBlHovToll", "NHbW Bl Hov Toll", 0)
        util.initmat(eb, "mf5240", "NHbOBlSovCost", "NHbO Bl Sov Cost", 0)
        util.initmat(eb, "mf5241", "NHbOBlSovTime", "NHbO Bl Sov Time", 0)
        util.initmat(eb, "mf5242", "NHbOBlSovToll", "NHbO Bl Sov Toll", 0)
        util.initmat(eb, "mf5245", "NHbOBlHovCost", "NHbO Bl Hov Cost", 0)
        util.initmat(eb, "mf5246", "NHbOBlHovTime", "NHbO Bl Hov Time", 0)
        util.initmat(eb, "mf5247", "NHbOBlHovToll", "NHbO Bl Hov Toll", 0)

        # Bridge Crossings

        util.initmat(eb, "mf5139", "HbShBl_BPen", "HbShopping Bridge Penalty", 0)
        util.initmat(eb, "mf5159", "HbPbBl_BPen", "HbPerBus Bridge Penalty", 0)
        util.initmat(eb, "mf5179", "HbSoBl_BPen", "HbSocial Bridge Penalty", 0)
        util.initmat(eb, "mf5249", "NHbOBl_BPen", "NHbO Bridge Penalty", 0)
        util.initmat(eb, "mf5219", "HbScBl_BPen", "HbSchool Bridge Penalty", 0)
        util.initmat(eb, "mf5229", "HbEsBl_BPen", "HbEscort Bridge Penalty", 0)
        # Transit

        util.initmat(eb, "mf5400", "HbWBlBusIvtt", "HbW Bl Bus InVehicle Time", 0)
        util.initmat(eb, "mf5401", "HbWBlBusWait", "HbW Bl Bus Waiting Time", 0)
        util.initmat(eb, "mf5402", "HbWBlBusAux", "HbW Bl Bus Auxillary Time", 0)
        util.initmat(eb, "mf5403", "HbWBlBusBoard", "HbW Bl Bus Boardings", 0)
        util.initmat(eb, "mf5404", "HbWBlBusFare", "HbW Bl Bus Fare", 0)
        util.initmat(eb, "mf5410", "HbUBlBusIvtt", "HbU Bl Bus InVehicle Time", 0)
        util.initmat(eb, "mf5411", "HbUBlBusWait", "HbU Bl Bus Waiting Time", 0)
        util.initmat(eb, "mf5412", "HbUBlBusAux", "HbU Bl Bus Auxillary Time", 0)
        util.initmat(eb, "mf5413", "HbUBlBusBoard", "HbU Bl Bus Boardings", 0)
        util.initmat(eb, "mf5414", "HbUBlBusFare", "HbU Bl Bus Fare", 0)
        util.initmat(eb, "mf5420", "HbScBlBusIvtt", "HbSc Bl Bus InVehicle Time", 0)
        util.initmat(eb, "mf5421", "HbScBlBusWait", "HbSc Bl Bus Waiting Time", 0)
        util.initmat(eb, "mf5422", "HbScBlBusAux", "HbSc Bl Bus Auxillary Time", 0)
        util.initmat(eb, "mf5423", "HbScBlBusBoard", "HbSc Bl Bus Boardings", 0)
        util.initmat(eb, "mf5424", "HbScBlBusFare", "HbSc Bl Bus Fare", 0)
        util.initmat(eb, "mf5430", "HbShBlBusIvtt", "HbSh Bl Bus InVehicle Time", 0)
        util.initmat(eb, "mf5431", "HbShBlBusWait", "HbSh Bl Bus Waiting Time", 0)
        util.initmat(eb, "mf5432", "HbShBlBusAux", "HbSh Bl Bus Auxillary Time", 0)
        util.initmat(eb, "mf5433", "HbShBlBusBoard", "HbSh Bl Bus Boardings", 0)
        util.initmat(eb, "mf5434", "HbShBlBusFare", "HbSh Bl Bus Fare", 0)
        util.initmat(eb, "mf5440", "HbPbBlBusIvtt", "HbPb Bl Bus InVehicle Time", 0)
        util.initmat(eb, "mf5441", "HbPbBlBusWait", "HbPb Bl Bus Waiting Time", 0)
        util.initmat(eb, "mf5442", "HbPbBlBusAux", "HbPb Bl Bus Auxillary Time", 0)
        util.initmat(eb, "mf5443", "HbPbBlBusBoard", "HbPb Bl Bus Boardings", 0)
        util.initmat(eb, "mf5444", "HbPbBlBusFare", "HbPb Bl Bus Fare", 0)
        util.initmat(eb, "mf5450", "HbSoBlBusIvtt", "HbSo Bl Bus InVehicle Time", 0)
        util.initmat(eb, "mf5451", "HbSoBlBusWait", "HbSo Bl Bus Waiting Time", 0)
        util.initmat(eb, "mf5452", "HbSoBlBusAux", "HbSo Bl Bus Auxillary Time", 0)
        util.initmat(eb, "mf5453", "HbSoBlBusBoard", "HbSo Bl Bus Boardings", 0)
        util.initmat(eb, "mf5454", "HbSoBlBusFare", "HbSo Bl Bus Fare", 0)
        util.initmat(eb, "mf5460", "HbEsBlBusIvtt", "HbEs Bl Bus InVehicle Time", 0)
        util.initmat(eb, "mf5461", "HbEsBlBusWait", "HbEs Bl Bus Waiting Time", 0)
        util.initmat(eb, "mf5462", "HbEsBlBusAux", "HbEs Bl Bus Auxillary Time", 0)
        util.initmat(eb, "mf5463", "HbEsBlBusBoard", "HbEs Bl Bus Boardings", 0)
        util.initmat(eb, "mf5464", "HbEsBlBusFare", "HbEs Bl Bus Fare", 0)
        util.initmat(eb, "mf5470", "NHbWBlBusIvtt", "NHbW Bl Bus InVehicle Time", 0)
        util.initmat(eb, "mf5471", "NHbWBlBusWait", "NHbW Bl Bus Waiting Time", 0)
        util.initmat(eb, "mf5472", "NHbWBlBusAux", "NHbW Bl Bus Auxillary Time", 0)
        util.initmat(eb, "mf5473", "NHbWBlBusBoard", "NHbW Bl Bus Boardings", 0)
        util.initmat(eb, "mf5474", "NHbWBlBusFare", "NHbW Bl Bus Fare", 0)
        util.initmat(eb, "mf5480", "NHbOBlBusIvtt", "NHbO Bl Bus InVehicle Time", 0)
        util.initmat(eb, "mf5481", "NHbOBlBusWait", "NHbO Bl Bus Waiting Time", 0)
        util.initmat(eb, "mf5482", "NHbOBlBusAux", "NHbO Bl Bus Auxillary Time", 0)
        util.initmat(eb, "mf5483", "NHbOBlBusBoard", "NHbO Bl Bus Boardings", 0)
        util.initmat(eb, "mf5484", "NHbOBlBusFare", "NHbO Bl Bus Fare", 0)
        util.initmat(eb, "mf5600", "HbWBlRailIvtt", "HbW Bl Rail Invehicle Time", 0)
        util.initmat(eb, "mf5601", "HbWBlRailIvttBus", "HbW Bl Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5602", "HbWBlRailWait", "HbW Bl Rail Waiting Time", 0)
        util.initmat(eb, "mf5603", "HbWBlRailAux", "HbW Bl Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5604", "HbWBlRailBoard", "HbW Bl Rail Boardings", 0)
        util.initmat(eb, "mf5605", "HbWBlRailFare", "HbW Bl Rail Fare", 0)
        util.initmat(eb, "mf5610", "HbUBlRailIvtt", "HbU Bl Rail Invehicle Time", 0)
        util.initmat(eb, "mf5611", "HbUBlRailIvttBus", "HbU Bl Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5612", "HbUBlRailWait", "HbU Bl Rail Waiting Time", 0)
        util.initmat(eb, "mf5613", "HbUBlRailAux", "HbU Bl Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5614", "HbUBlRailBoard", "HbU Bl Rail Boardings", 0)
        util.initmat(eb, "mf5615", "HbUBlRailFare", "HbU Bl Rail Fare", 0)
        util.initmat(eb, "mf5620", "HbScBlRailIvtt", "HbSc Bl Rail Invehicle Time", 0)
        util.initmat(eb, "mf5621", "HbScBlRailIvttBus", "HbSc Bl Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5622", "HbScBlRailWait", "HbSc Bl Rail Waiting Time", 0)
        util.initmat(eb, "mf5623", "HbScBlRailAux", "HbSc Bl Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5624", "HbScBlRailBoard", "HbSc Bl Rail Boardings", 0)
        util.initmat(eb, "mf5625", "HbScBlRailFare", "HbSc Bl Rail Fare", 0)
        util.initmat(eb, "mf5630", "HbShBlRailIvtt", "HbSh Bl Rail Invehicle Time", 0)
        util.initmat(eb, "mf5631", "HbShBlRailIvttBus", "HbSh Bl Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5632", "HbShBlRailWait", "HbSh Bl Rail Waiting Time", 0)
        util.initmat(eb, "mf5633", "HbShBlRailAux", "HbSh Bl Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5634", "HbShBlRailBoard", "HbSh Bl Rail Boardings", 0)
        util.initmat(eb, "mf5635", "HbShBlRailFare", "HbSh Bl Rail Fare", 0)
        util.initmat(eb, "mf5640", "HbPbBlRailIvtt", "HbPb Bl Rail Invehicle Time", 0)
        util.initmat(eb, "mf5641", "HbPbBlRailIvttBus", "HbPb Bl Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5642", "HbPbBlRailWait", "HbPb Bl Rail Waiting Time", 0)
        util.initmat(eb, "mf5643", "HbPbBlRailAux", "HbPb Bl Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5644", "HbPbBlRailBoard", "HbPb Bl Rail Boardings", 0)
        util.initmat(eb, "mf5645", "HbPbBlRailFare", "HbPb Bl Rail Fare", 0)
        util.initmat(eb, "mf5650", "HbSoBlRailIvtt", "HbSo Bl Rail Invehicle Time", 0)
        util.initmat(eb, "mf5651", "HbSoBlRailIvttBus", "HbSo Bl Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5652", "HbSoBlRailWait", "HbSo Bl Rail Waiting Time", 0)
        util.initmat(eb, "mf5653", "HbSoBlRailAux", "HbSo Bl Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5654", "HbSoBlRailBoard", "HbSo Bl Rail Boardings", 0)
        util.initmat(eb, "mf5655", "HbSoBlRailFare", "HbSo Bl Rail Fare", 0)
        util.initmat(eb, "mf5660", "HbEsBlRailIvtt", "HbEs Bl Rail Invehicle Time", 0)
        util.initmat(eb, "mf5661", "HbEsBlRailIvttBus", "HbEs Bl Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5662", "HbEsBlRailWait", "HbEs Bl Rail Waiting Time", 0)
        util.initmat(eb, "mf5663", "HbEsBlRailAux", "HbEs Bl Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5664", "HbEsBlRailBoard", "HbEs Bl Rail Boardings", 0)
        util.initmat(eb, "mf5665", "HbEsBlRailFare", "HbEs Bl Rail Fare", 0)
        util.initmat(eb, "mf5670", "NHbWBlRailIvtt", "NHbW Bl Rail Invehicle Time", 0)
        util.initmat(eb, "mf5671", "NHbWBlRailIvttBus", "NHbW Bl Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5672", "NHbWBlRailWait", "NHbW Bl Rail Waiting Time", 0)
        util.initmat(eb, "mf5673", "NHbWBlRailAux", "NHbW Bl Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5674", "NHbWBlRailBoard", "NHbW Bl Rail Boardings", 0)
        util.initmat(eb, "mf5675", "NHbWBlRailFare", "NHbW Bl Rail Fare", 0)
        util.initmat(eb, "mf5680", "NHbOBlRailIvtt", "NHbO Bl Rail Invehicle Time", 0)
        util.initmat(eb, "mf5681", "NHbOBlRailIvttBus", "NHbO Bl Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5682", "NHbOBlRailWait", "NHbO Bl Rail Waiting Time", 0)
        util.initmat(eb, "mf5683", "NHbOBlRailAux", "NHbO Bl Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5684", "NHbOBlRailBoard", "NHbO Bl Rail Boardings", 0)
        util.initmat(eb, "mf5685", "NHbOBlRailFare", "NHbO Bl Rail Fare", 0)
        util.initmat(eb, "mf5800", "HbWBlWceIvtt", "HbW Bl WCE Invehicle Time", 0)
        util.initmat(eb, "mf5801", "HbWBlWceIvttRail", "HbW Bl WCE Invehicle Time on WCE", 0)
        util.initmat(eb, "mf5802", "HbWBlWceIvttBus", "HbW Bl WCE Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5803", "HbWBlWceWait", "HbW Bl WCE Waiting Time", 0)
        util.initmat(eb, "mf5804", "HbWBlWceAux", "HbW Bl WCE Auxilliary Time", 0)
        util.initmat(eb, "mf5805", "HbWBlWceBoard", "HbW Bl WCE Boardings", 0)
        util.initmat(eb, "mf5806", "HbWBlWceFare", "HbW Bl WCE Fare", 0)
        util.initmat(eb, "mf6800", "HbWBlBAuPRCost", "HbW Bl Bus-Auto PR Cost", 0)
        util.initmat(eb, "mf6801", "HbWBlBAuPRTime", "HbW Bl Bus-Auto PR Time", 0)
        util.initmat(eb, "mf6802", "HbWBlBAuPRToll", "HbW Bl Bus-Auto PR Toll", 0)
        util.initmat(eb, "mf6803", "HbWBAuPrkCst", "HbW Bus-Auto PR Parking Cost", 0)
        util.initmat(eb, "mf6804", "HbWBAuTrmTim", "HbW Bus-Auto PR Terminal Time", 0)
        util.initmat(eb, "mf6810", "HbWBlRAuPRCost", "HbW Bl Rail-Auto PR Cost", 0)
        util.initmat(eb, "mf6811", "HbWBlRAuPRTime", "HbW Bl Rail-Auto PR Time", 0)
        util.initmat(eb, "mf6812", "HbWBlRAuPRToll", "HbW Bl Rail-Auto PR Toll", 0)
        util.initmat(eb, "mf6813", "HbWRAuPrkCst", "HbW Rail-Auto PR Parking Cost", 0)
        util.initmat(eb, "mf6814", "HbWRAuTrmTim", "HbW Rail-Auto PR Terminal Time", 0)
        util.initmat(eb, "mf6820", "HbWBlWAuPRCost", "HbW Bl WCE-Auto PR Cost", 0)
        util.initmat(eb, "mf6821", "HbWBlWAuPRTime", "HbW Bl WCE-Auto PR Time", 0)
        util.initmat(eb, "mf6822", "HbWBlWAuPRToll", "HbW Bl WCE-Auto PR Toll", 0)
        util.initmat(eb, "mf6823", "HbWWAuPrkCst", "HbW WCE-Auto PR Parking Cost", 0)
        util.initmat(eb, "mf6824", "HbWWAuTrmTim", "HbW WCE-Auto PR Terminal Time", 0)
        util.initmat(eb, "mf6900", "HbWBlBAuBusIvtt", "HbW Bl Bus-Auto PR InVehicle Time", 0)
        util.initmat(eb, "mf6901", "HbWBlBAuBusWait", "HbW Bl Bus-Auto PR Bus Waiting Time", 0)
        util.initmat(eb, "mf6902", "HbWBlBAuBusAux", "HbW Bl Bus-Auto PR Bus Auxillary Time", 0)
        util.initmat(eb, "mf6903", "HbWBlBAuBusBoard", "HbW Bl Bus-Auto PR Bus Boardings", 0)
        util.initmat(eb, "mf6904", "HbWBlBAuBusFare", "HbW Bl Bus-Auto PR Bus Fare", 0)
        util.initmat(eb, "mf6910", "HbWBlRAuRailIvtt", "HbW Bl Rail-Auto Rail Invehicle Time", 0)
        util.initmat(eb, "mf6911", "HbWBlRAuRailIvttBus", "HbW Bl Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf6912", "HbWBlRAuRailWait", "HbW Bl Rail-Auto Rail Waiting Time", 0)
        util.initmat(eb, "mf6913", "HbWBlRAuRailAux", "HbW Bl Rail-Auto Rail Auxilliary Time", 0)
        util.initmat(eb, "mf6914", "HbWBlRAuRailBoard", "HbW Bl Rail-Auto Rail Boardings", 0)
        util.initmat(eb, "mf6915", "HbWBlRAuRailFare", "HbW Bl Rail-Auto Rail Fare", 0)
        util.initmat(eb, "mf6920", "HbWBlWAuWceIvtt", "HbW Bl WCE-Auto WCE Invehicle Time", 0)
        util.initmat(eb, "mf6921", "HbWBlWAuWceIvttRail", "HbW Bl WCE-Auto WCE Invehicle Time on Rail", 0)
        util.initmat(eb, "mf6922", "HbWBlWAuWceIvttBus", "HbW Bl WCE-Auto WCE Invehicle Time on Bus", 0)
        util.initmat(eb, "mf6923", "HbWBlWAuWceWait", "HbW Bl WCE-Auto WCE Waiting Time", 0)
        util.initmat(eb, "mf6924", "HbWBlWAuWceAux", "HbW Bl WCE-Auto WCE Auxilliary Time", 0)
        util.initmat(eb, "mf6925", "HbWBlWAuWceBoards", "HbW Bl WCE-Auto WCE Boardings", 0)
        util.initmat(eb, "mf6926", "HbWBlWAuWceFare", "HbW Bl WCE-Auto WCE Fare", 0)

        ####################
        # PnR Batch-in files
        ####################

        # Lot choice using AM impedances, but lot choice fixed for all time periods
        util.initmat(eb, "mf6000", "buspr-lotChceWkAMPA", "Bus Best PnR Lot - Bus",0)
        util.initmat(eb, "mf6001", "railpr-lotChceWkAMPA", "Rail Best PnR Lot - Rail",0)
        util.initmat(eb, "mf6002", "wcepr-lotChceWkAMPA", "Rail Best PnR Lot -WCE",0)
        # AM Auto generalized Cost same for all modes
        util.initmat(eb, "mf6003", "pr-gtAutoWkAMPA", "PnR Generalized Cost Auto Leg",0)
        # AM bus impedance matrices
        util.initmat(eb, "mf6005", "buspr-GctranWkAMPA", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6006", "buspr-minGCWkAMPA", "PnR Combined Skim Result - Bus",0)
        # AM rail impedance matrices
        util.initmat(eb, "mf6015", "railpr-GctranWkAMPA", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6016", "railpr-minGCWkAMPA", "Rail PnR Combined Skim Result - Rail",0)
        # AM WCE impedance matrices
        util.initmat(eb, "mf6030", "wcepr-GctranWkAMPA", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6031", "wcepr-minGCWkAMPA", "WCE PnR Combined Skim Result",0)
        # MD Auto generalized Cost same for all modes
        util.initmat(eb, "mf6048", "pr-gtAutoWkMDPA", "PnR Generalized Cost Auto Leg",0)
        # MD bus impedance matrices
        util.initmat(eb, "mf6050", "buspr-GctranWkMDPA", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6051", "buspr-minGCWkMDPA", "PnR Combined Skim Result - Bus",0)
        # MD rail impedance matrices
        util.initmat(eb, "mf6060", "railpr-GctranWkMDPA", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6061", "railpr-minGCWkMDPA", "Rail PnR Combined Skim Result - Rail",0)
        # MD WCE impedance matrices
        util.initmat(eb, "mf6075", "wcepr-GctranWkMDPA", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6076", "wcepr-minGCWkMDPA", "WCE PnR Combined Skim Result",0)
        # PM Auto generalized Cost same for all modes
        util.initmat(eb, "mf6088", "pr-gtAutoWkPMPA", "PnR Generalized Cost Auto Leg",0)
        # PM bus impedance matrices
        util.initmat(eb, "mf6090", "buspr-GctranWkPMPA", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6091", "buspr-minGCWkPMPA", "PnR Combined Skim Result - Bus",0)
        # PM rail impedance matrices
        util.initmat(eb, "mf6100", "railpr-GctranWkPMPA", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6101", "railpr-minGCWkPMPA", "Rail PnR Combined Skim Result - Rail",0)
        # PM WCE impedance matrices
        util.initmat(eb, "mf6115", "wcepr-GctranWkPMPA", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6116", "wcepr-minGCWkPMPA", "WCE PnR Combined Skim Result",0)
        # Lot choice using AM impedances, but lot choice fixed for all time periods
        util.initmat(eb, "mf6130", "buspr-lotChceNWkAMPA", "Bus Best PnR Lot - Bus",0)
        util.initmat(eb, "mf6131", "railpr-lotChceNWkAMPA", "Rail Best PnR Lot - Rail",0)
        util.initmat(eb, "mf6132", "wcepr-lotChceNWkAMPA", "Rail Best PnR Lot -WCE",0)
        # AM Auto generalized Cost same for all modes
        util.initmat(eb, "mf6133", "pr-gtAutoNWkAMPA", "PnR Generalized Cost Auto Leg",0)
        # AM bus impedance matrices
        util.initmat(eb, "mf6135", "buspr-GctranNWkAMPA", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6136", "buspr-minGCNWkAMPA", "PnR Combined Skim Result - Bus",0)
        # AM rail impedance matrices
        util.initmat(eb, "mf6145", "railpr-GctranNWkAMPA", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6146", "railpr-minGCNWkAMPA", "Rail PnR Combined Skim Result - Rail",0)
        # AM WCE impedance matrices
        util.initmat(eb, "mf6160", "wcepr-GctranNWkAMPA", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6161", "wcepr-minGCNWkAMPA", "WCE PnR Combined Skim Result",0)
        # MD Auto generalized Cost same for all modes
        util.initmat(eb, "mf6173", "pr-gtAutoNWkMDPA", "PnR Generalized Cost Auto Leg",0)
        # MD bus impedance matrices
        util.initmat(eb, "mf6175", "buspr-GctranNWkMDPA", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6176", "buspr-minGCNWkMDPA", "PnR Combined Skim Result - Bus",0)
        # MD rail impedance matrices
        util.initmat(eb, "mf6185", "railpr-GctranNWkMDPA", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6186", "railpr-minGCNWkMDPA", "Rail PnR Combined Skim Result - Rail",0)
        # MD WCE impedance matrices
        util.initmat(eb, "mf6200", "wcepr-GctranNWkMDPA", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6201", "wcepr-minGCNWkMDPA", "WCE PnR Combined Skim Result",0)
        # PM Auto generalized Cost same for all modes
        util.initmat(eb, "mf6213", "pr-gtAutoNWkPMPA", "PnR Generalized Cost Auto Leg",0)
        # PM bus impedance matrices
        util.initmat(eb, "mf6215", "buspr-GctranNWkPMPA", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6216", "buspr-minGCNWkPMPA", "PnR Combined Skim Result - Bus",0)
        # PM rail impedance matrices
        util.initmat(eb, "mf6225", "railpr-GctranNWkPMPA", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6226", "railpr-minGCNWkPMPA", "Rail PnR Combined Skim Result - Rail",0)
        # PM WCE impedance matrices
        util.initmat(eb, "mf6240", "wcepr-GctranNWkPMPA", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6241", "wcepr-minGCNWkPMPA", "WCE PnR Combined Skim Result",0)
        # AM Auto generalized Cost same for all modes
        util.initmat(eb, "mf6303", "pr-gtAutoWkAMAP", "PnR Generalized Cost Auto Leg",0)
        # AM bus impedance matrices
        util.initmat(eb, "mf6305", "buspr-GctranWkAMAP", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6306", "buspr-minGCWkAMAP", "PnR Combined Skim Result - Bus",0)
        # AM rail impedance matrices
        util.initmat(eb, "mf6315", "railpr-GctranWkAMAP", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6316", "railpr-minGCWkAMAP", "Rail PnR Combined Skim Result - Rail",0)
        # AM WCE impedance matrices
        util.initmat(eb, "mf6330", "wcepr-GctranWkAMAP", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6331", "wcepr-minGCWkAMAP", "WCE PnR Combined Skim Result",0)
        # MD Auto generalized Cost same for all modes
        util.initmat(eb, "mf6348", "pr-gtAutoWkMDAP", "PnR Generalized Cost Auto Leg",0)
        # MD bus impedance matrices
        util.initmat(eb, "mf6350", "buspr-GctranWkMDAP", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6351", "buspr-minGCWkMDAP", "PnR Combined Skim Result - Bus",0)
        # MD rail impedance matrices
        util.initmat(eb, "mf6360", "railpr-GctranWkMDAP", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6361", "railpr-minGCWkMDAP", "Rail PnR Combined Skim Result - Rail",0)
        # MD WCE impedance matrices
        util.initmat(eb, "mf6375", "wcepr-GctranWkMDAP", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6376", "wcepr-minGCWkMDAP", "WCE PnR Combined Skim Result",0)
        # PM Auto generalized Cost same for all modes
        util.initmat(eb, "mf6388", "pr-gtAutoWkPMAP", "PnR Generalized Cost Auto Leg",0)
        # PM bus impedance matrices
        util.initmat(eb, "mf6390", "buspr-GctranWkPMAP", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6391", "buspr-minGCWkPMAP", "PnR Combined Skim Result - Bus",0)
        # PM rail impedance matrices
        util.initmat(eb, "mf6400", "railpr-GctranWkPMAP", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6401", "railpr-minGCWkPMAP", "Rail PnR Combined Skim Result - Rail",0)
        # PM WCE impedance matrices
        util.initmat(eb, "mf6415", "wcepr-GctranWkPMAP", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6416", "wcepr-minGCWkPMAP", "WCE PnR Combined Skim Result",0)
        # AM Auto generalized Cost same for all modes
        util.initmat(eb, "mf6433", "pr-gtAutoNWkAMAP", "PnR Generalized Cost Auto Leg",0)
        # AM bus impedance matrices
        util.initmat(eb, "mf6435", "buspr-GctranNWkAMAP", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6436", "buspr-minGCNWkAMAP", "PnR Combined Skim Result - Bus",0)
        # AM rail impedance matrices
        util.initmat(eb, "mf6445", "railpr-GctranNWkAMAP", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6446", "railpr-minGCNWkAMAP", "Rail PnR Combined Skim Result - Rail",0)
        # AM WCE impedance matrices
        util.initmat(eb, "mf6460", "wcepr-GctranNWkAMAP", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6461", "wcepr-minGCNWkAMAP", "WCE PnR Combined Skim Result",0)
        # MD Auto generalized Cost same for all modes
        util.initmat(eb, "mf6473", "pr-gtAutoNWkMDAP", "PnR Generalized Cost Auto Leg",0)
        # MD bus impedance matrices
        util.initmat(eb, "mf6475", "buspr-GctranNWkMDAP", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6476", "buspr-minGCNWkMDAP", "PnR Combined Skim Result - Bus",0)
        # MD rail impedance matrices
        util.initmat(eb, "mf6485", "railpr-GctranNWkMDAP", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6486", "railpr-minGCNWkMDAP", "Rail PnR Combined Skim Result - Rail",0)
        # MD WCE impedance matrices
        util.initmat(eb, "mf6500", "wcepr-GctranNWkMDAP", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6501", "wcepr-minGCNWkMDAP", "WCE PnR Combined Skim Result",0)
        # PM Auto generalized Cost same for all modes
        util.initmat(eb, "mf6513", "pr-gtAutoNWkPMAP", "PnR Generalized Cost Auto Leg",0)
        # PM bus impedance matrices
        util.initmat(eb, "mf6515", "buspr-GctranNWkPMAP", "PnR Generalized Cost Transit Leg - Bus",0)
        util.initmat(eb, "mf6516", "buspr-minGCNWkPMAP", "PnR Combined Skim Result - Bus",0)
        # PM rail impedance matrices
        util.initmat(eb, "mf6525", "railpr-GctranNWkPMAP", "Rail PnR Generalized Cost Transit Leg - Rail",0)
        util.initmat(eb, "mf6526", "railpr-minGCNWkPMAP", "Rail PnR Combined Skim Result - Rail",0)
        # PM WCE impedance matrices
        util.initmat(eb, "mf6540", "wcepr-GctranNWkPMAP", "WCE PnR Generalized Cost Transit Leg",0)
        util.initmat(eb, "mf6541", "wcepr-minGCNWkPMAP", "WCE PnR Combined Skim Result",0)
