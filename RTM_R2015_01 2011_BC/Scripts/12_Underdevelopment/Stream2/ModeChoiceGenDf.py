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
        util = _m.Modeller().tool("translink.emme.util")
        input_path = util.get_input_path(eb)
        #self.matrix_batchins(eb)
        ## Park and Ride determine best lot
        pnr_costs = os.path.join(input_path, "pnr_inputs.csv")
        model_year = int(eb.matrix("ms149").data)
        self.read_file(eb, pnr_costs)
        self.AutoGT(eb)
        self.BusGT(eb)
        self.RailGT(eb)
        self.WceGT(eb)
        self.bestlot(eb, model_year)
        ## General Setup
        Or = util.get_matrix_numpy(eb, "mf1").flatten()  #Store Vector by origin
        De = util.get_matrix_numpy(eb, "mf2").flatten() #Store Vector by destination
        BLBsWk = util.get_matrix_numpy(eb, "mf6000").flatten() #Best Lot Bus Work
        BLBsNw = util.get_matrix_numpy(eb, "mf6130").flatten() #Best Lot Bus Non-Work
        BLRlWk = util.get_matrix_numpy(eb, "mf6001").flatten() #Best Lot Rail Work
        BLRlNw = util.get_matrix_numpy(eb, "mf6131").flatten() #Best Lot Rail Non-Work
        BLWcWk = util.get_matrix_numpy(eb, "mf6002").flatten() #Best Lot WCE Work
        BLWcNw = util.get_matrix_numpy(eb, "mf6132").flatten() #Best Lot WCE Non-Work

        hbwo_fct = self.get_fact[["HbWBl_AM_P-A", "HbWBl_MD_P-A", "HbWBl_PM_P-A"],
                                 ["HbWBl_AM_A-P", "HbWBl_MD_A-P", "HbWBl_PM_A-P"]]

        hbwo_fct_wce = self.get_fact_wce[["HbWBl_AM_P-A_WCE", "Zero",],
                                     ["Zero", "HbWBl_PM_A-P_WCE"]]

        nhbw_fct = self.get_fact[["NHbWBl_AM_P-A", "NHbWBl_MD_P-A", "NHbWBl_PM_P-A"],
                                 ["Zero", "Zero", "Zero"]]

        hbun_fct = self.get_fact[["HbUBl_AM_P-A", "HbUBl_MD_P-A", "HbUBl_PM_P-A"],
                                 ["HbUBl_AM_A-P", "HbUBl_MD_A-P", "HbUBl_PM_A-P"]]

        hbsc_fct = self.get_fact[["HbScBl_AM_P-A", "HbScBl_MD_P-A", "HbScBl_PM_P-A"],
                                 ["HbScBl_AM_A-P", "HbScBl_MD_A-P", "HbScBl_PM_A-P"]]

        hbsh_fct = self.get_fact[["HbShBl_AM_P-A", "HbShBl_MD_P-A", "HbShBl_PM_P-A"],
                                 ["HbShBl_AM_A-P", "HbShBl_MD_A-P", "HbShBl_PM_A-P"]]

        hbpb_fct = self.get_fact[["HbPbBl_AM_P-A", "HbPbBl_MD_P-A", "HbPbBl_PM_P-A"],
                                 ["HbPbBl_AM_A-P", "HbPbBl_MD_A-P", "HbPbBl_PM_A-P"]]

        hbso_fct = self.get_fact[["HbSoBl_AM_P-A", "HbSoBl_MD_P-A", "HbSoBl_PM_P-A"],
                                 ["HbSoBl_AM_A-P", "HbSoBl_MD_A-P", "HbSoBl_PM_A-P"]]

        hbes_fct = self.get_fact[["HbEsBl_AM_P-A", "HbEsBl_MD_P-A", "HbEsBl_PM_P-A"],
                                 ["HbEsBl_AM_A-P", "HbEsBl_MD_A-P", "HbEsBl_PM_A-P"]]

        nhbo_fct = self.get_fact[["NHbOBl_AM_P-A", "NHbOBl_MD_P-A", "NHbOBl_PM_P-A"],
                                 ["Zero", "Zero", "Zero"]]

        ##############################################################################
        ##       Auto Skims work SOV
        ##############################################################################
        # Initialize Time Distance and Toll Skim Dictionaries
        TimeDict, DistDict, TollDict = {}, {}, {}
        # Generate Skim Dictionaries
        #                                 AM    ,    MD   ,     PM
        self.GenSkimDict(eb, DistDict, ["mf5000", "mf5020", "mf5040"]) # Distance
        self.GenSkimDict(eb, TimeDict, ["mf5001", "mf5021", "mf5041"]) # Time
        self.GenSkimDict(eb, TollDict, ["mf5002", "mf5022", "mf5042"]) # Toll

        # Blend Factors            AM , MD  , PM           AM  ,MD , PM       Where Blended Matrices get stored in same order as above
        BlendDict = {'hbwo':{'PA': hbwo_fct[0], 'AP':hbwo_fct[1], 'Mat':['mf5100', 'mf5101', 'mf5102']}, # Home-base work
                     'nhbw':{'PA': nhbw_fct[0], 'AP':nhbw_fct[1], 'Mat':['mf5170', 'mf5171', 'mf5172']}} # Non-home base work

        for keys, values in BlendDict.items():
            Df = {}
            # Calculate blended skim
            Df['AutoDis'] = self.calc_blend(values, DistDict)
            Df['AutoTim'] = self.calc_blend(values, TimeDict)
            Df['AutoTol'] = self.calc_blend(values, TollDict)
        # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['AutoDis'])
            util.set_matrix_numpy(eb, values['Mat'][1], Df['AutoTim'])
            util.set_matrix_numpy(eb, values['Mat'][2], Df['AutoTol'])

        ##############################################################################
        ##       Park and Ride Home-base work Auto-leg
        ##############################################################################

        # Blend Factors                AM , MD  , PM           AM  ,MD , PM    Where Blended Matrices get stored in same order as above
        BlendDictPR = {'hbwprb':{'PA': hbwo_fct[0], 'AP':hbwo_fct[1], 'Mat':['mf6800', 'mf6801', 'mf6802'], #Bus
                       'BL': BLBsWk},
                       'hbwprr':{'PA': hbwo_fct[0], 'AP':hbwo_fct[1], 'Mat':['mf6810', 'mf6811', 'mf6812'], #Rail
                       'BL': BLRlWk},
                       'hbwprw':{'PA': hbwo_fct_wce[0], 'AP':hbwo_fct_wce[1], 'Mat':['mf6820', 'mf6821', 'mf6822'], #WCE
                       'BL': BLWcWk}
                     }

        for keys, values in BlendDictPR.items():

            Df = pd.DataFrame()
            # Generate data frame with Origin Destination and best lot
            Dfmerge = pd.DataFrame({'Or': Or, 'De': De, 'BL': values['BL']})
            # Generate second data frame and attach to it blended
            Df_Auto_Leg = pd.DataFrame({'OrAuto': Or, 'DeAuto': De})
            Df_Auto_Leg['AutoDis'] = self.calc_blend(values, DistDict).flatten()
            Df_Auto_Leg['AutoTim'] = self.calc_blend(values, TimeDict).flatten()
            Df_Auto_Leg['AutoTol'] = self.calc_blend(values, TollDict).flatten()
            # Join the two data frames based on skims from Origin to the Best Lot
            Df = pd.merge(Dfmerge, Df_Auto_Leg, left_on = ['Or', 'BL'],
                     right_on = ['OrAuto', 'DeAuto'], how = 'left')
            # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['AutoDis'].reshape(1741,1741))
            util.set_matrix_numpy(eb, values['Mat'][1], Df['AutoTim'].reshape(1741,1741))
            util.set_matrix_numpy(eb, values['Mat'][2], Df['AutoTol'].reshape(1741,1741))
        # delete data generated to free up memory
        del Df, Dfmerge, Df_Auto_Leg, TimeDict, DistDict, TollDict

        ##############################################################################
        ##       Auto Skims work HOV
        ##############################################################################
        # Initialize Time Distance and Toll Skim Dictionaries
        TimeDict, DistDict, TollDict = {}, {}, {}
        # Generate Skim Dictionaries
        #                                 AM    ,    MD   ,     PM
        self.GenSkimDict(eb, DistDict, ["mf5006", "mf5026", "mf5046"]) # Distance
        self.GenSkimDict(eb, TimeDict, ["mf5007", "mf5027", "mf5047"]) # Time
        self.GenSkimDict(eb, TollDict, ["mf5008", "mf5028", "mf5048"]) # Toll

        # Blend Factors            AM , MD  , PM           AM  ,MD , PM       Where Blended Matrices get stored in same order as above
        BlendDict = {'hbwo':{'PA': hbwo_fct[0], 'AP':hbwo_fct[1], 'Mat':['mf5106', 'mf5107', 'mf5108']}, # Home-base work
                     'nhbw':{'PA': nhbw_fct[0], 'AP':nhbw_fct[1], 'Mat':['mf5176', 'mf5177', 'mf5178']}} # Non-home base work

        for keys, values in BlendDict.items():
            Df = {}
            # Calculate blended skim
            Df['AutoDis'] = self.calc_blend(values, DistDict)
            Df['AutoTim'] = self.calc_blend(values, TimeDict)
            Df['AutoTol'] = self.calc_blend(values, TollDict)
        # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['AutoDis'])
            util.set_matrix_numpy(eb, values['Mat'][1], Df['AutoTim'])
            util.set_matrix_numpy(eb, values['Mat'][2], Df['AutoTol'])

        del Df, TimeDict, DistDict, TollDict

        ##############################################################################
        ##       Auto Skims Non-work SOV
        ##############################################################################
        # Initialize Time Distance and Toll Skim Dictionaries
        TimeDict, DistDict, TollDict = {}, {}, {}
        # Generate Skim Dictionaries
        #                                 AM    ,    MD   ,     PM
        self.GenSkimDict(eb, DistDict, ["mf5003", "mf5023", "mf5043"]) # Distance
        self.GenSkimDict(eb, TimeDict, ["mf5004", "mf5024", "mf5044"]) # Time
        self.GenSkimDict(eb, TollDict, ["mf5005", "mf5025", "mf5045"]) # Toll
        #
        # Blend Factors            AM , MD  , PM           AM  ,MD , PM     Where Blended Matrices get stored in same order as above
        BlendDict = {
                     'hbun':{'PA': hbun_fct[0], 'AP':hbun_fct[1], 'Mat':['mf5110', 'mf5111', 'mf5112']}, # Home-base university
                     'hbsc':{'PA': hbsc_fct[0], 'AP':hbsc_fct[1], 'Mat':['mf5120', 'mf5121', 'mf5122']}, # Home-base school
                     'hbsh':{'PA': hbsh_fct[0], 'AP':hbsh_fct[1], 'Mat':['mf5130', 'mf5131', 'mf5132']}, # Home-base shopping
                     'hbpb':{'PA': hbpb_fct[0], 'AP':hbpb_fct[1], 'Mat':['mf5140', 'mf5141', 'mf5142']}, # Home-base personal business
                     'hbso':{'PA': hbso_fct[0], 'AP':hbso_fct[1], 'Mat':['mf5150', 'mf5151', 'mf5152']}, # Home-base social
                     'hbes':{'PA': hbes_fct[0], 'AP':hbes_fct[1], 'Mat':['mf5160', 'mf5161', 'mf5162']}, # Home-base escorting
                     'nhbo':{'PA': nhbo_fct[0], 'AP':nhbo_fct[1], 'Mat':['mf5180', 'mf5181', 'mf5182']}} # non-home base other

        for keys, values in BlendDict.items():
            # Calculate blended skim
            Df = {}
            Df['AutoDis'] = self.calc_blend(values, DistDict)
            Df['AutoTim'] = self.calc_blend(values, TimeDict)
            Df['AutoTol'] = self.calc_blend(values, TollDict)
            # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['AutoDis'])
            util.set_matrix_numpy(eb, values['Mat'][1], Df['AutoTim'])
            util.set_matrix_numpy(eb, values['Mat'][2], Df['AutoTol'])

        ##############################################################################
        ##       Auto Skims Non-work HOV
        ##############################################################################
        # Initialize Time Distance and Toll Skim Dictionaries
        TimeDict, DistDict, TollDict = {}, {}, {}
        # Generate Skim Dictionaries
        #                                 AM    ,    MD   ,     PM
        self.GenSkimDict(eb, DistDict, ["mf5009", "mf5029", "mf5049"]) # Distance
        self.GenSkimDict(eb, TimeDict, ["mf5010", "mf5030", "mf5050"]) # Time
        self.GenSkimDict(eb, TollDict, ["mf5011", "mf5031", "mf5051"]) # Toll
        #
        # Blend Factors            AM , MD  , PM           AM  ,MD , PM     Where Blended Matrices get stored in same order as above
        BlendDict = {
                     'hbun':{'PA': hbun_fct[0], 'AP':hbun_fct[1], 'Mat':['mf5116', 'mf5117', 'mf5118']}, # Home-base university
                     'hbsc':{'PA': hbsc_fct[0], 'AP':hbsc_fct[1], 'Mat':['mf5126', 'mf5127', 'mf5128']}, # Home-base school
                     'hbsh':{'PA': hbsh_fct[0], 'AP':hbsh_fct[1], 'Mat':['mf5136', 'mf5137', 'mf5138']}, # Home-base shopping
                     'hbpb':{'PA': hbpb_fct[0], 'AP':hbpb_fct[1], 'Mat':['mf5146', 'mf5147', 'mf5148']}, # Home-base personal business
                     'hbso':{'PA': hbso_fct[0], 'AP':hbso_fct[1], 'Mat':['mf5156', 'mf5157', 'mf5158']}, # Home-base social
                     'hbes':{'PA': hbes_fct[0], 'AP':hbes_fct[1], 'Mat':['mf5166', 'mf5167', 'mf5168']}, # Home-base escorting
                     'nhbo':{'PA': nhbo_fct[0], 'AP':nhbo_fct[1], 'Mat':['mf5186', 'mf5187', 'mf5188']}} # non-home base other

        for keys, values in BlendDict.items():
            # Calculate blended skim
            Df = {}
            Df['AutoDis'] = self.calc_blend(values, DistDict)
            Df['AutoTim'] = self.calc_blend(values, TimeDict)
            Df['AutoTol'] = self.calc_blend(values, TollDict)
            # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['AutoDis'])
            util.set_matrix_numpy(eb, values['Mat'][1], Df['AutoTim'])
            util.set_matrix_numpy(eb, values['Mat'][2], Df['AutoTol'])
        # delete data generated to free up memory
        del Df, TimeDict, DistDict, TollDict

#       ##############################################################################
#       ##       Bus Skims
#       ##############################################################################
#       # Initialize In-vehicle, Wait, Auxiliary, Boarding and Fare Skim Dictionaries
        BusIVTDict, BusWatDict, BusAuxDict = {}, {}, {}
        BusBrdDict, BusFarDict = {}, {}
        # Generate Skim Dictionaries
        #                                  AM    ,    MD   ,     PM
        self.GenSkimDict(eb, BusIVTDict, ["mf5200", "mf5210", "mf5220"]) # Bus IVTT
        self.GenSkimDict(eb, BusWatDict, ["mf5201", "mf5211", "mf5221"]) # Bus Wait
        self.GenSkimDict(eb, BusAuxDict, ["mf5202", "mf5212", "mf5222"]) # Bus Aux
        self.GenSkimDict(eb, BusBrdDict, ["mf5203", "mf5213", "mf5223"]) # Bus Boarding
        self.GenSkimDict(eb, BusFarDict, ["mf5204", "mf5214", "mf5224"]) # Bus Fare

       # Blend Factors
        BlendDict = {   #AM,   MD,   PM         AM,   MD,   PM         Where Blended Matrices get stored in same order as above
         'hbwo':{'PA': hbwo_fct[0], 'AP':hbwo_fct[1], 'Mat':['mf5300', 'mf5301', 'mf5302', 'mf5303', 'mf5304']},  # Home-base work
         'hbun':{'PA': hbun_fct[0], 'AP':hbun_fct[1], 'Mat':['mf5310', 'mf5311', 'mf5312', 'mf5313', 'mf5314']},  # Home-base university
         'hbsc':{'PA': hbsc_fct[0], 'AP':hbsc_fct[1], 'Mat':['mf5320', 'mf5321', 'mf5322', 'mf5323', 'mf5324']},  # Home-base school
         'hbsh':{'PA': hbsh_fct[0], 'AP':hbsh_fct[1], 'Mat':['mf5330', 'mf5331', 'mf5332', 'mf5333', 'mf5334']},  # Home-base shopping
         'hbpb':{'PA': hbpb_fct[0], 'AP':hbpb_fct[1], 'Mat':['mf5340', 'mf5341', 'mf5342', 'mf5343', 'mf5344']},  # Home-base personal business
         'hbso':{'PA': hbso_fct[0], 'AP':hbso_fct[1], 'Mat':['mf5350', 'mf5351', 'mf5352', 'mf5353', 'mf5354']},  # Home-base social
         'hbes':{'PA': hbes_fct[0], 'AP':hbes_fct[1], 'Mat':['mf5360', 'mf5361', 'mf5362', 'mf5363', 'mf5364']},  # Home-base escorting
         'nhbw':{'PA': nhbw_fct[0], 'AP':nhbw_fct[1], 'Mat':['mf5370', 'mf5371', 'mf5372', 'mf5373', 'mf5374']},  # Non-home base work
         'nhbo':{'PA': nhbo_fct[0], 'AP':nhbo_fct[1], 'Mat':['mf5380', 'mf5381', 'mf5382', 'mf5383', 'mf5384']}}  # Non-home base other

        for keys, values in BlendDict.items():
            # Calculate blended skims
            Df = {}
            Df['BusIVT']  = self.calc_blend(values, BusIVTDict)
            Df['BusWat']  = self.calc_blend(values, BusWatDict)
            Df['BusAux']  = self.calc_blend(values, BusAuxDict)
            Df['BusBrd']  = self.calc_blend(values, BusBrdDict)
            Df['BusFar']  = self.calc_blend(values, BusFarDict)
            # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['BusIVT'])
            util.set_matrix_numpy(eb, values['Mat'][1], Df['BusWat'])
            util.set_matrix_numpy(eb, values['Mat'][2], Df['BusAux'])
            util.set_matrix_numpy(eb, values['Mat'][3], Df['BusBrd'])
            util.set_matrix_numpy(eb, values['Mat'][4], Df['BusFar'])

       ##############################################################################
       ##       Park and Ride Home-base Work/Uni/Soc Bus-leg
       ##############################################################################
        BlendDictPR = { #AM,   MD,   PM         AM,   MD,   PM         Where Blended Matrices get stored in same order as above
         'hbwo':{'PA': hbwo_fct[0], 'AP':hbwo_fct[1], 'Mat':['mf6900', 'mf6901', 'mf6902', 'mf6903', 'mf6904'], # Home-base work
         'BL': BLBsWk}
                      }
        for keys, values in BlendDictPR.items():

            Df = pd.DataFrame()
            # Generate data frame with Origin Destination and best lot
            Dfmerge = pd.DataFrame({'Or': Or, 'De': De, 'BL': values['BL']})
            # Generate second data frame and attach to it bus skims
            Df_Bus_Leg = pd.DataFrame({'OrTran': Or, 'DeTran': De})
            Df_Bus_Leg['BusIVT']  = self.calc_blend(values, BusIVTDict).flatten()
            Df_Bus_Leg['BusWat']  = self.calc_blend(values, BusWatDict).flatten()
            Df_Bus_Leg['BusAux']  = self.calc_blend(values, BusAuxDict).flatten()
            Df_Bus_Leg['BusBrd']  = self.calc_blend(values, BusBrdDict).flatten()
            Df_Bus_Leg['BusFar']  = self.calc_blend(values, BusFarDict).flatten()
            # Join the two data frames based on skims from the Best Lot to the destination
            Df = pd.merge(Dfmerge, Df_Bus_Leg, left_on = ['BL', 'De'],
                     right_on = ['OrTran', 'DeTran'], how = 'left')
            # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['BusIVT'].reshape(1741,1741))
            util.set_matrix_numpy(eb, values['Mat'][1], Df['BusWat'].reshape(1741,1741))
            util.set_matrix_numpy(eb, values['Mat'][2], Df['BusAux'].reshape(1741,1741))
            util.set_matrix_numpy(eb, values['Mat'][3], Df['BusBrd'].reshape(1741,1741))
            util.set_matrix_numpy(eb, values['Mat'][4], Df['BusFar'].reshape(1741,1741))
        # delete data generated to free up memory
        del Df, Dfmerge, Df_Bus_Leg, BusIVTDict, BusWatDict, BusAuxDict, BusBrdDict, BusFarDict
#
#        ##############################################################################
#        ##       Rail Skims
#        ##############################################################################
        # Initialize In-vehicle, Wait, Auxiliary, Boarding and Fare Skim Dictionaries
        RalIVBDict, RalIVRDict, RalWatDict = {}, {}, {}
        RalAuxDict, RalBrdDict, RalFarDict = {}, {}, {}

        # Generate Skim Dictionaries
        #                                  AM    ,    MD   ,     PM
        self.GenSkimDict(eb, RalIVRDict, ["mf5400", "mf5410", "mf5420"]) # Rail IVR
        self.GenSkimDict(eb, RalIVBDict, ["mf5401", "mf5411", "mf5421"]) # Rail IVB
        self.GenSkimDict(eb, RalWatDict, ["mf5402", "mf5412", "mf5422"]) # Rail Wait
        self.GenSkimDict(eb, RalAuxDict, ["mf5403", "mf5413", "mf5423"]) # Rail Aux
        self.GenSkimDict(eb, RalBrdDict, ["mf5404", "mf5414", "mf5424"]) # Rail Boarding
        self.GenSkimDict(eb, RalFarDict, ["mf5405", "mf5415", "mf5425"]) # Rail Fare

        # Blend Factors
        BlendDict = {  #AM,   MD,   PM         AM,   MD,   PM
         'hbwo':{'PA': hbwo_fct[0], 'AP':hbwo_fct[1],
                 'Mat':['mf5500', 'mf5501', 'mf5502', 'mf5503', 'mf5504', 'mf5505']}, # Where Blended Matrices get stored in same order as above
         'hbun':{'PA': hbun_fct[0], 'AP':hbun_fct[1],
                 'Mat':['mf5510', 'mf5511', 'mf5512', 'mf5513', 'mf5514', 'mf5515']},
         'hbsc':{'PA': hbsc_fct[0], 'AP':hbsc_fct[1],
                 'Mat':['mf5520', 'mf5521', 'mf5522', 'mf5523', 'mf5524', 'mf5525']},
         'hbsh':{'PA': hbsh_fct[0], 'AP':hbsh_fct[1],
                 'Mat':['mf5530', 'mf5531', 'mf5532', 'mf5533', 'mf5534', 'mf5535']},
         'hbpb':{'PA': hbpb_fct[0], 'AP':hbpb_fct[1],
                 'Mat':['mf5540', 'mf5541', 'mf5542', 'mf5543', 'mf5544', 'mf5545']},
         'hbso':{'PA': hbso_fct[0], 'AP':hbso_fct[1],
                 'Mat':['mf5550', 'mf5551', 'mf5552', 'mf5553', 'mf5554', 'mf5555']},
         'hbes':{'PA': hbes_fct[0], 'AP':hbes_fct[1],
                 'Mat':['mf5560', 'mf5561', 'mf5562', 'mf5563', 'mf5564', 'mf5565']},
         'nhbw':{'PA': nhbw_fct[0], 'AP':nhbw_fct[1],
                 'Mat':['mf5570', 'mf5571', 'mf5572', 'mf5573', 'mf5574', 'mf5575']},
         'nhbo':{'PA': nhbo_fct[0], 'AP':nhbo_fct[1],
                 'Mat':['mf5580', 'mf5581', 'mf5582', 'mf5583', 'mf5584', 'mf5585']}}

        for keys, values in BlendDict.items():
            # Calculate blended skims
            Df = {}
            Df['RalIVR'] = self.calc_blend(values, RalIVRDict)
            Df['RalIVB'] = self.calc_blend(values, RalIVBDict)
            Df['RalWat'] = self.calc_blend(values, RalWatDict)
            Df['RalAux'] = self.calc_blend(values, RalAuxDict)
            Df['RalBrd'] = self.calc_blend(values, RalBrdDict)
            Df['RalFar'] = self.calc_blend(values, RalFarDict)
            # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['RalIVR'])
            util.set_matrix_numpy(eb, values['Mat'][1], Df['RalIVB'])
            util.set_matrix_numpy(eb, values['Mat'][2], Df['RalWat'])
            util.set_matrix_numpy(eb, values['Mat'][3], Df['RalAux'])
            util.set_matrix_numpy(eb, values['Mat'][4], Df['RalBrd'])
            util.set_matrix_numpy(eb, values['Mat'][5], Df['RalFar'])
#       ##############################################################################
#        ##       Park and Ride Home-base Work/Uni/Soc Rail-leg
#        ##############################################################################
        BlendDictPR = { #AM,   MD,   PM         AM,   MD,   PM
           'hbwo':{'PA': hbwo_fct[0], 'AP':hbwo_fct[1],
                 'Mat':['mf6910', 'mf6911', 'mf6912', 'mf6913', 'mf6914', 'mf6915'], 'BL': BLRlWk}, #Where Blended Matrices get stored in same order as above
                      }
        for keys, values in BlendDictPR.items():

            Df = pd.DataFrame()
            # Generate data frame with Origin Destination and best lot
            Dfmerge = pd.DataFrame({'Or': Or, 'De': De, 'BL': values['BL']})
            # Generate second data frame and attach to it rail skims
            Df_Rail_Leg = pd.DataFrame({'OrTran': Or, 'DeTran': De})
            Df_Rail_Leg['RalIVR'] = self.calc_blend(values, RalIVRDict).flatten()
            Df_Rail_Leg['RalIVB'] = self.calc_blend(values, RalIVBDict).flatten()
            Df_Rail_Leg['RalWat'] = self.calc_blend(values, RalWatDict).flatten()
            Df_Rail_Leg['RalAux'] = self.calc_blend(values, RalAuxDict).flatten()
            Df_Rail_Leg['RalBrd'] = self.calc_blend(values, RalBrdDict).flatten()
            Df_Rail_Leg['RalFar'] = self.calc_blend(values, RalFarDict).flatten()
            # Join the two data frames based on skims from the Best Lot to the destination
            Df = pd.merge(Dfmerge, Df_Rail_Leg, left_on = ['BL', 'De'],
                     right_on = ['OrTran', 'DeTran'], how = 'left')
            # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['RalIVR'].reshape(1741,1741))
            util.set_matrix_numpy(eb, values['Mat'][1], Df['RalIVB'].reshape(1741,1741))
            util.set_matrix_numpy(eb, values['Mat'][2], Df['RalWat'].reshape(1741,1741))
            util.set_matrix_numpy(eb, values['Mat'][3], Df['RalAux'].reshape(1741,1741))
            util.set_matrix_numpy(eb, values['Mat'][4], Df['RalBrd'].reshape(1741,1741))
            util.set_matrix_numpy(eb, values['Mat'][5], Df['RalFar'].reshape(1741,1741))
        # delete data generated to free up memory
        del Df, Dfmerge, Df_Rail_Leg, RalIVBDict, RalIVRDict, RalWatDict, RalAuxDict, RalBrdDict, RalFarDict
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
        self.GenSkimDictWCE(eb, WCEIVWDict, ["mf5600", "mf5620"]) # WCE IVW
        self.GenSkimDictWCE(eb, WCEIVRDict, ["mf5601", "mf5621"]) # WCE IVR
        self.GenSkimDictWCE(eb, WCEIVBDict, ["mf5602", "mf5622"]) # WCE IVB
        self.GenSkimDictWCE(eb, WCEWatDict, ["mf5603", "mf5623"]) # WCE Wait
        self.GenSkimDictWCE(eb, WCEAuxDict, ["mf5604", "mf5624"]) # WCE Aux
        self.GenSkimDictWCE(eb, WCEBrdDict, ["mf5605", "mf5625"]) # WCE Boarding
        self.GenSkimDictWCE(eb, WCEFarDict, ["mf5606", "mf5626"])   # WCE Fare

#        # Blend Factors
        BlendDict = {    #AM,   PM,        AM,   PM,
         'hbwo':{'PA': hbwo_fct[0], 'AP':hbwo_fct[1],
                 'Mat':['mf5700', 'mf5701', 'mf5702', 'mf5703', 'mf5704', 'mf5705', 'mf5706']},  # Where Blended Matrices get stored in same order as above
         'hbun':{'PA': hbun_fct[0], 'AP':hbun_fct[1],
                 'Mat':['mf5710', 'mf5711', 'mf5712', 'mf5713', 'mf5714', 'mf5715', 'mf5716']},
         'hbsc':{'PA': hbsc_fct[0], 'AP':hbsc_fct[1],
                 'Mat':['mf5720', 'mf5721', 'mf5722', 'mf5723', 'mf5724', 'mf5725', 'mf5726']},
         'hbsh':{'PA': hbsh_fct[0], 'AP':hbsh_fct[1],
                 'Mat':['mf5730', 'mf5731', 'mf5732', 'mf5733', 'mf5734', 'mf5735', 'mf5736']},
         'hbpb':{'PA': hbpb_fct[0], 'AP':hbpb_fct[1],
                 'Mat':['mf5740', 'mf5741', 'mf5742', 'mf5743', 'mf5744', 'mf5745', 'mf5746']},
         'hbso':{'PA': hbso_fct[0], 'AP':hbso_fct[1],
                 'Mat':['mf5750', 'mf5751', 'mf5752', 'mf5753', 'mf5754', 'mf5755', 'mf5756']},
         'hbes':{'PA': hbes_fct[0], 'AP':hbes_fct[1],
                 'Mat':['mf5760', 'mf5761', 'mf5762', 'mf5763', 'mf5764', 'mf5765', 'mf5766']},
         'nhbw':{'PA': nhbw_fct[0], 'AP':nhbw_fct[1],
                 'Mat':['mf5770', 'mf5771', 'mf5772', 'mf5773', 'mf5774', 'mf5775', 'mf5776']},
         'nhbo':{'PA': nhbo_fct[0], 'AP':nhbo_fct[1],
                 'Mat':['mf5780', 'mf5781', 'mf5782', 'mf5783', 'mf5784', 'mf5785', 'mf5786']}}

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
                 'Mat':['mf6920', 'mf6921', 'mf6922', 'mf6923', 'mf6924', 'mf6925', 'mf6926']} # Where Blended Matrices get stored in same order as above
                      }

        for keys, values in BlendDictPR.items():

            Df = pd.DataFrame()
            # Generate data frame with Origin Destination and best lot
            Dfmerge = pd.DataFrame({'Or': Or, 'De': De, 'BL': values['BL']})
            # Generate second data frame and attach to it wce skims
            Df_WCE_Leg = pd.DataFrame({'OrTran': Or, 'DeTran': De})
            Df_WCE_Leg['WCEIVW'] = self.calc_blend(values, WCEIVWDict).flatten()
            Df_WCE_Leg['WCEIVR'] = self.calc_blend(values, WCEIVRDict).flatten()
            Df_WCE_Leg['WCEIVB'] = self.calc_blend(values, WCEIVBDict).flatten()
            Df_WCE_Leg['WCEWat'] = self.calc_blend(values, WCEWatDict).flatten()
            Df_WCE_Leg['WCEAux'] = self.calc_blend(values, WCEAuxDict).flatten()
            Df_WCE_Leg['WCEBrd'] = self.calc_blend(values, WCEBrdDict).flatten()
            Df_WCE_Leg['WCEFar'] = self.calc_blend(values, WCEFarDict).flatten()
             # Join the two data frames based on skims from the Best Lot to the destination
            Df = pd.merge(Dfmerge, Df_WCE_Leg, left_on = ['BL', 'De'],
                     right_on = ['OrTran', 'DeTran'], how = 'left')
            # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['WCEIVW'].reshape(1741,1741))
            util.set_matrix_numpy(eb, values['Mat'][1], Df['WCEIVR'].reshape(1741,1741))
            util.set_matrix_numpy(eb, values['Mat'][2], Df['WCEIVB'].reshape(1741,1741))
            util.set_matrix_numpy(eb, values['Mat'][3], Df['WCEWat'].reshape(1741,1741))
            util.set_matrix_numpy(eb, values['Mat'][4], Df['WCEAux'].reshape(1741,1741))
            util.set_matrix_numpy(eb, values['Mat'][5], Df['WCEBrd'].reshape(1741,1741))
            util.set_matrix_numpy(eb, values['Mat'][6], Df['WCEFar'].reshape(1741,1741))
        # delete data generated to free up memory
        del Df, Dfmerge, Df_WCE_Leg, WCEIVBDict, WCEIVRDict, WCEIVWDict, WCEWatDict, WCEAuxDict, WCEBrdDict, WCEFarDict

#        ##############################################################################
#        ##       Functions
#        ##############################################################################

    def GenSkimDict(self, eb, Dict, Mat):
        util = _m.Modeller().tool("translink.emme.util")
        AM_Mat = util.get_matrix_numpy(eb, Mat[0])
        MD_Mat = util.get_matrix_numpy(eb, Mat[1])
        PM_Mat = util.get_matrix_numpy(eb, Mat[2])
        Dict['PA'] = [AM_Mat, MD_Mat, PM_Mat]
        Dict['AP'] = [AM_Mat.transpose(), MD_Mat.transpose(), PM_Mat.transpose()]
        return (Dict)

    def GenSkimDictWCE(self, eb, Dict, Mat):
        util = _m.Modeller().tool("translink.emme.util")
        AM_Mat = util.get_matrix_numpy(eb, Mat[0])
        PM_Mat = util.get_matrix_numpy(eb, Mat[1])

        Dict['PA'] = [AM_Mat, PM_Mat]
        Dict['AP'] = [AM_Mat.transpose(), PM_Mat.transpose()]
        return (Dict)

    def calc_blend(self, Fact, Dict):
        util = _m.Modeller().tool("translink.emme.util")
        Result = util.sumproduct(Fact['PA'], Dict['PA']) + util.sumproduct(Fact['AP'], Dict['AP'])

        return Result

    def get_fact(self, eb, FactList):

        util = _m.Modeller().tool("translink.emme.util")
        PA_List = np.array([
                            util.get_matrix_numpy(FactList[0][0]),
                            util.get_matrix_numpy(FactList[0][1]),
                            util.get_matrix_numpy(FactList[0][2])
                           ])

        AP_List = np.array([
                            util.get_matrix_numpy(FactList[1][0]),
                            util.get_matrix_numpy(FactList[1][1]),
                            util.get_matrix_numpy(FactList[1][2])
                           ])
        return np.array([PAList, AP_List])

    def get_fact_wce(self, eb, FactList):

        util = _m.Modeller().tool("translink.emme.util")
        PA_List = np.array([
                            util.get_matrix_numpy(FactList[0][0]),
                            util.get_matrix_numpy(FactList[0][1]),
                           ])

        AP_List = np.array([
                            util.get_matrix_numpy(FactList[1][0]),
                            util.get_matrix_numpy(FactList[1][1]),
                           ])
        return np.array([PAList, AP_List])

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
        util = _m.Modeller().tool("translink.emme.util")
        # [AM,MD,PM]
        transit_mats = {"wceIVT" : ["mf5600",  "mf5610", "mf5620"],
                        "wceWait" : ["mf5603",  "mf5613", "mf5623"],
                        "railIVT" : ["mf5601",  "mf5611", "mf5621"],
                        "busIVT" : ["mf5602",  "mf5612", "mf5622"],
                        "auxTransit" : ["mf5604",  "mf5614", "mf5624"],
                        "boardings" : ["mf5605",  "mf5615", "mf5625"],
                        "wceFare" : ["mf5606",  "mf5616", "mf5626"]}

        # [Work, non-work]
        vot_mats = ['msvotWkmed', 'msvotNWkmed']

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
                                       wceIVTprcp="mswceIVTprcp",
                                       wceOVTprcp="mswceOVTprcp",
                                       railIVTprcp="msrailIVTprcp",
                                       busIVTprcp="msbusIVTprcp",
                                       walkprcp="mswalkprcp",
                                       transferprcp="mswceTRANSprcp",
                                       VOT=vot_mats[j])

                result = ("{wceGT}").format(wceGT=result_mats[j][i])
                specs.append(util.matrix_spec(result, expression))
        util.compute_matrix(specs)

    @_m.logbook_trace("Park & Ride Calculate Rail Generatized Time")
    def RailGT(self, eb):
        util = _m.Modeller().tool("translink.emme.util")
        # [AM,MD,PM]
        transit_mats = {"railIVT" : ["mf5400",  "mf5410", "mf5420"],
                        "railWait" : ["mf5402",  "mf5412", "mf5422"],
                        "busIVT" : ["mf5401",  "mf5411", "mf5421"],
                        "auxTransit" : ["mf5403", "mf5413", "mf5423"],
                        "boardings" : ["mf5404", "mf5414", "mf5424"],
                        "railFare" : ["mf5405",  "mf5415", "mf5425"]}

        # [Work, non-work]
        vot_mats = ['msvotWkmed', 'msvotNWkmed']

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
                                       railIVTprcp="msrailIVTprcp",
                                       railOVTprcp="msrailOVTprcp",
                                       busIVTprcp="msbusIVTprcp",
                                       walkprcp="mswalkprcp",
                                       transferprcp="msrailTRANSprcp",
                                       VOT=vot_mats[j])

                result = ("{railGT}").format(railGT=result_mats[j][i])
                specs.append(util.matrix_spec(result, expression))
        util.compute_matrix(specs)

    @_m.logbook_trace("Park & Ride Calculate Bus Generalized Time")
    def BusGT(self, eb):
        util = _m.Modeller().tool("translink.emme.util")
        # [AM,MD,PM]
        transit_mats = {"busIVT" : ["mf5200",  "mf5210", "mf5220"],
                        "busWait" : ["mf5201",  "mf5211", "mf5221"],
                        "auxTransit" : ["mf5202", "mf5212", "mf5222"],
                        "boardings" : ["mf5203", "mf5213", "mf5223"],
                        "busFare" : ["mf5204",  "mf5214", "mf5224"]}

        # [Work, non-work]
        vot_mats = ['msvotWkmed', 'msvotNWkmed']

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
                                       busIVTprcp="msbusIVTprcp",
                                       busOVTprcp="msbusOVTprcp",
                                       walkprcp="mswalkprcp",
                                       transferprcp="msbusTRANSprcp",
                                       VOT=vot_mats[j])

                result = ("{busGT}").format(busGT=result_mats[j][i])
                specs.append(util.matrix_spec(result, expression))
        util.compute_matrix(specs)

    @_m.logbook_trace("Park & Ride Calculate Auto Generalized Time")
    def AutoGT(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        # work trips - not ideal formulation but quick and gets it done
        # [AM,MD,PM]
        auto_mats = {"autotime" : ["mf5001",  "mf5021", "mf5041"],
                    "autotoll" : ["mf5002", "mf5022", "mf5042"],
                    "autodist" : ["mf5000", "mf5020", "mf5040"]}

        # [Work, non-work]
        vot_mat = 'msvotWkmed'

        # [AMWk, MDWk, PMWk]
        result_mats = ["mf6003", "mf6048", "mf6088"]

        specs = []
        for i in range(0,3):
            expression = ("{autotime} + {termtime}"
                          " + (({VOC} * {autodist}) + {autotoll} + {lotcost}) * {VOT}"
                          ).format(autotime=auto_mats["autotime"][i],
                                   autotoll=auto_mats["autotoll"][i],
                                   autodist=auto_mats["autodist"][i],
                                   VOT=vot_mat,
                                   VOC="msVOC",
                                   lotcost = "mdPRcost",
                                   termtime = "mdPRtermtime")

            result = ("{autoGT}").format(autoGT=result_mats[i])
            specs.append(util.matrix_spec(result, expression))
        util.compute_matrix(specs)



        auto_mats = {"autotime" : ["mf5004",  "mf5024", "mf5044"],
                    "autotoll" : ["mf5005", "mf5025", "mf5045"],
                    "autodist" : ["mf5003", "mf5023", "mf5043"] }

        # [Work, non-work]
        vot_mat = 'msvotNWkmed'

        # [[AMWk, MDWk, PMWk],[AMnonWk, MDnonWk, PMnonWk]]
        result_mats = ['mf6133','mf6173','mf6213']

        specs = []
        for i in range(0,3):
            expression = ("{autotime} + {termtime}"
                          " + (({VOC} * {autodist}) + {autotoll} + {lotcost}) * {VOT}"
                          ).format(autotime=auto_mats["autotime"][i],
                                   autotoll=auto_mats["autotoll"][i],
                                   autodist=auto_mats["autodist"][i],
                                   VOT=vot_mat,
                                   VOC="msVOC",
                                   lotcost = "mdPRcost",
                                   termtime = "mdPRtermtime")

            result = ("{autoGT}").format(autoGT=result_mats[i])
            specs.append(util.matrix_spec(result, expression))
        util.compute_matrix(specs)

    @_m.logbook_trace("Park & Ride - Read Input Files")
    def read_file(self, eb, file):
        util = _m.Modeller().tool("translink.emme.util")
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
        util = _m.Modeller().tool("translink.emme.util")

        ###################
        # Blended Skims
        ###################

        util.initmat(eb, "mf5100", "HbWBlSovDist", "HbW Bl Sov Distance", 0)
        util.initmat(eb, "mf5101", "HbWBlSovTime", "HbW Bl Sov Time", 0)
        util.initmat(eb, "mf5102", "HbWBlSovToll", "HbW Bl Sov Toll", 0)
        util.initmat(eb, "mf5106", "HbWBlHovDist", "HbW Bl Hov Distance", 0)
        util.initmat(eb, "mf5107", "HbWBlHovTime", "HbW Bl Hov Time", 0)
        util.initmat(eb, "mf5108", "HbWBlHovToll", "HbW Bl Hov Toll", 0)
        util.initmat(eb, "mf5110", "HbUBlSovDist", "HbU Bl Sov Distance", 0)
        util.initmat(eb, "mf5111", "HbUBlSovTime", "HbU Bl Sov Time", 0)
        util.initmat(eb, "mf5112", "HbUBlSovToll", "HbU Bl Sov Toll", 0)
        util.initmat(eb, "mf5116", "HbUBlHovDist", "HbU Bl Hov Distance", 0)
        util.initmat(eb, "mf5117", "HbUBlHovTime", "HbU Bl Hov Time", 0)
        util.initmat(eb, "mf5118", "HbUBlHovToll", "HbU Bl Hov Toll", 0)
        util.initmat(eb, "mf5120", "HbScBlSovDist", "HbSc Bl Sov Distance", 0)
        util.initmat(eb, "mf5121", "HbScBlSovTime", "HbSc Bl Sov Time", 0)
        util.initmat(eb, "mf5122", "HbScBlSovToll", "HbSc Bl Sov Toll", 0)
        util.initmat(eb, "mf5126", "HbScBlHovDist", "HbSc Bl Hov Distance", 0)
        util.initmat(eb, "mf5127", "HbScBlHovTime", "HbSc Bl Hov Time", 0)
        util.initmat(eb, "mf5128", "HbScBlHovToll", "HbSc Bl Hov Toll", 0)
        util.initmat(eb, "mf5130", "HbShBlSovDist", "HbSh Bl Sov Distance", 0)
        util.initmat(eb, "mf5131", "HbShBlSovTime", "HbSh Bl Sov Time", 0)
        util.initmat(eb, "mf5132", "HbShBlSovToll", "HbSh Bl Sov Toll", 0)
        util.initmat(eb, "mf5136", "HbShBlHovDist", "HbSh Bl Hov Distance", 0)
        util.initmat(eb, "mf5137", "HbShBlHovTime", "HbSh Bl Hov Time", 0)
        util.initmat(eb, "mf5138", "HbShBlHovToll", "HbSh Bl Hov Toll", 0)
        util.initmat(eb, "mf5140", "HbPbBlSovDist", "HbPb Bl Sov Distance", 0)
        util.initmat(eb, "mf5141", "HbPbBlSovTime", "HbPb Bl Sov Time", 0)
        util.initmat(eb, "mf5142", "HbPbBlSovToll", "HbPb Bl Sov Toll", 0)
        util.initmat(eb, "mf5146", "HbPbBlHovDist", "HbPb Bl Hov Distance", 0)
        util.initmat(eb, "mf5147", "HbPbBlHovTime", "HbPb Bl Hov Time", 0)
        util.initmat(eb, "mf5148", "HbPbBlHovToll", "HbPb Bl Hov Toll", 0)
        util.initmat(eb, "mf5150", "HbSoBlSovDist", "HbSo Bl Sov Distance", 0)
        util.initmat(eb, "mf5151", "HbSoBlSovTime", "HbSo Bl Sov Time", 0)
        util.initmat(eb, "mf5152", "HbSoBlSovToll", "HbSo Bl Sov Toll", 0)
        util.initmat(eb, "mf5156", "HbSoBlHovDist", "HbSo Bl Hov Distance", 0)
        util.initmat(eb, "mf5157", "HbSoBlHovTime", "HbSo Bl Hov Time", 0)
        util.initmat(eb, "mf5158", "HbSoBlHovToll", "HbSo Bl Hov Toll", 0)
        util.initmat(eb, "mf5160", "HbEsBlSovDist", "HbEs Bl Sov Distance", 0)
        util.initmat(eb, "mf5161", "HbEsBlSovTime", "HbEs Bl Sov Time", 0)
        util.initmat(eb, "mf5162", "HbEsBlSovToll", "HbEs Bl Sov Toll", 0)
        util.initmat(eb, "mf5166", "HbEsBlHovDist", "HbEs Bl Hov Distance", 0)
        util.initmat(eb, "mf5167", "HbEsBlHovTime", "HbEs Bl Hov Time", 0)
        util.initmat(eb, "mf5168", "HbEsBlHovToll", "HbEs Bl Hov Toll", 0)
        util.initmat(eb, "mf5170", "NHbWBlSovDist", "NHbW Bl Sov Distance", 0)
        util.initmat(eb, "mf5171", "NHbWBlSovTime", "NHbW Bl Sov Time", 0)
        util.initmat(eb, "mf5172", "NHbWBlSovToll", "NHbW Bl Sov Toll", 0)
        util.initmat(eb, "mf5176", "NHbWBlHovDist", "NHbW Bl Hov Distance", 0)
        util.initmat(eb, "mf5177", "NHbWBlHovTime", "NHbW Bl Hov Time", 0)
        util.initmat(eb, "mf5178", "NHbWBlHovToll", "NHbW Bl Hov Toll", 0)
        util.initmat(eb, "mf5180", "NHbOBlSovDist", "NHbO Bl Sov Distance", 0)
        util.initmat(eb, "mf5181", "NHbOBlSovTime", "NHbO Bl Sov Time", 0)
        util.initmat(eb, "mf5182", "NHbOBlSovToll", "NHbO Bl Sov Toll", 0)
        util.initmat(eb, "mf5186", "NHbOBlHovDist", "NHbO Bl Hov Distance", 0)
        util.initmat(eb, "mf5187", "NHbOBlHovTime", "NHbO Bl Hov Time", 0)
        util.initmat(eb, "mf5188", "NHbOBlHovToll", "NHbO Bl Hov Toll", 0)
        util.initmat(eb, "mf5300", "HbWBlBusIvtt", "HbW Bl Bus InVehicle Time", 0)
        util.initmat(eb, "mf5301", "HbWBlBusWait", "HbW Bl Bus Waiting Time", 0)
        util.initmat(eb, "mf5302", "HbWBlBusAux", "HbW Bl Bus Auxillary Time", 0)
        util.initmat(eb, "mf5303", "HbWBlBusBoard", "HbW Bl Bus Boardings", 0)
        util.initmat(eb, "mf5304", "HbWBlBusFare", "HbW Bl Bus Fare", 0)
        util.initmat(eb, "mf5310", "HbUBlBusIvtt", "HbU Bl Bus InVehicle Time", 0)
        util.initmat(eb, "mf5311", "HbUBlBusWait", "HbU Bl Bus Waiting Time", 0)
        util.initmat(eb, "mf5312", "HbUBlBusAux", "HbU Bl Bus Auxillary Time", 0)
        util.initmat(eb, "mf5313", "HbUBlBusBoard", "HbU Bl Bus Boardings", 0)
        util.initmat(eb, "mf5314", "HbUBlBusFare", "HbU Bl Bus Fare", 0)
        util.initmat(eb, "mf5320", "HbScBlBusIvtt", "HbSc Bl Bus InVehicle Time", 0)
        util.initmat(eb, "mf5321", "HbScBlBusWait", "HbSc Bl Bus Waiting Time", 0)
        util.initmat(eb, "mf5322", "HbScBlBusAux", "HbSc Bl Bus Auxillary Time", 0)
        util.initmat(eb, "mf5323", "HbScBlBusBoard", "HbSc Bl Bus Boardings", 0)
        util.initmat(eb, "mf5324", "HbScBlBusFare", "HbSc Bl Bus Fare", 0)
        util.initmat(eb, "mf5330", "HbShBlBusIvtt", "HbSh Bl Bus InVehicle Time", 0)
        util.initmat(eb, "mf5331", "HbShBlBusWait", "HbSh Bl Bus Waiting Time", 0)
        util.initmat(eb, "mf5332", "HbShBlBusAux", "HbSh Bl Bus Auxillary Time", 0)
        util.initmat(eb, "mf5333", "HbShBlBusBoard", "HbSh Bl Bus Boardings", 0)
        util.initmat(eb, "mf5334", "HbShBlBusFare", "HbSh Bl Bus Fare", 0)
        util.initmat(eb, "mf5340", "HbPbBlBusIvtt", "HbPb Bl Bus InVehicle Time", 0)
        util.initmat(eb, "mf5341", "HbPbBlBusWait", "HbPb Bl Bus Waiting Time", 0)
        util.initmat(eb, "mf5342", "HbPbBlBusAux", "HbPb Bl Bus Auxillary Time", 0)
        util.initmat(eb, "mf5343", "HbPbBlBusBoard", "HbPb Bl Bus Boardings", 0)
        util.initmat(eb, "mf5344", "HbPbBlBusFare", "HbPb Bl Bus Fare", 0)
        util.initmat(eb, "mf5350", "HbSoBlBusIvtt", "HbSo Bl Bus InVehicle Time", 0)
        util.initmat(eb, "mf5351", "HbSoBlBusWait", "HbSo Bl Bus Waiting Time", 0)
        util.initmat(eb, "mf5352", "HbSoBlBusAux", "HbSo Bl Bus Auxillary Time", 0)
        util.initmat(eb, "mf5353", "HbSoBlBusBoard", "HbSo Bl Bus Boardings", 0)
        util.initmat(eb, "mf5354", "HbSoBlBusFare", "HbSo Bl Bus Fare", 0)
        util.initmat(eb, "mf5360", "HbEsBlBusIvtt", "HbEs Bl Bus InVehicle Time", 0)
        util.initmat(eb, "mf5361", "HbEsBlBusWait", "HbEs Bl Bus Waiting Time", 0)
        util.initmat(eb, "mf5362", "HbEsBlBusAux", "HbEs Bl Bus Auxillary Time", 0)
        util.initmat(eb, "mf5363", "HbEsBlBusBoard", "HbEs Bl Bus Boardings", 0)
        util.initmat(eb, "mf5364", "HbEsBlBusFare", "HbEs Bl Bus Fare", 0)
        util.initmat(eb, "mf5370", "NHbWBlBusIvtt", "NHbW Bl Bus InVehicle Time", 0)
        util.initmat(eb, "mf5371", "NHbWBlBusWait", "NHbW Bl Bus Waiting Time", 0)
        util.initmat(eb, "mf5372", "NHbWBlBusAux", "NHbW Bl Bus Auxillary Time", 0)
        util.initmat(eb, "mf5373", "NHbWBlBusBoard", "NHbW Bl Bus Boardings", 0)
        util.initmat(eb, "mf5374", "NHbWBlBusFare", "NHbW Bl Bus Fare", 0)
        util.initmat(eb, "mf5380", "NHbOBlBusIvtt", "NHbO Bl Bus InVehicle Time", 0)
        util.initmat(eb, "mf5381", "NHbOBlBusWait", "NHbO Bl Bus Waiting Time", 0)
        util.initmat(eb, "mf5382", "NHbOBlBusAux", "NHbO Bl Bus Auxillary Time", 0)
        util.initmat(eb, "mf5383", "NHbOBlBusBoard", "NHbO Bl Bus Boardings", 0)
        util.initmat(eb, "mf5384", "NHbOBlBusFare", "NHbO Bl Bus Fare", 0)
        util.initmat(eb, "mf5500", "HbWBlRailIvtt", "HbW Bl Rail Invehicle Time", 0)
        util.initmat(eb, "mf5501", "HbWBlRailIvttBus", "HbW Bl Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5502", "HbWBlRailWait", "HbW Bl Rail Waiting Time", 0)
        util.initmat(eb, "mf5503", "HbWBlRailAux", "HbW Bl Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5504", "HbWBlRailBoard", "HbW Bl Rail Boardings", 0)
        util.initmat(eb, "mf5505", "HbWBlRailFare", "HbW Bl Rail Fare", 0)
        util.initmat(eb, "mf5510", "HbUBlRailIvtt", "HbU Bl Rail Invehicle Time", 0)
        util.initmat(eb, "mf5511", "HbUBlRailIvttBus", "HbU Bl Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5512", "HbUBlRailWait", "HbU Bl Rail Waiting Time", 0)
        util.initmat(eb, "mf5513", "HbUBlRailAux", "HbU Bl Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5514", "HbUBlRailBoard", "HbU Bl Rail Boardings", 0)
        util.initmat(eb, "mf5515", "HbUBlRailFare", "HbU Bl Rail Fare", 0)
        util.initmat(eb, "mf5520", "HbScBlRailIvtt", "HbSc Bl Rail Invehicle Time", 0)
        util.initmat(eb, "mf5521", "HbScBlRailIvttBus", "HbSc Bl Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5522", "HbScBlRailWait", "HbSc Bl Rail Waiting Time", 0)
        util.initmat(eb, "mf5523", "HbScBlRailAux", "HbSc Bl Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5524", "HbScBlRailBoard", "HbSc Bl Rail Boardings", 0)
        util.initmat(eb, "mf5525", "HbScBlRailFare", "HbSc Bl Rail Fare", 0)
        util.initmat(eb, "mf5530", "HbShBlRailIvtt", "HbSh Bl Rail Invehicle Time", 0)
        util.initmat(eb, "mf5531", "HbShBlRailIvttBus", "HbSh Bl Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5532", "HbShBlRailWait", "HbSh Bl Rail Waiting Time", 0)
        util.initmat(eb, "mf5533", "HbShBlRailAux", "HbSh Bl Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5534", "HbShBlRailBoard", "HbSh Bl Rail Boardings", 0)
        util.initmat(eb, "mf5535", "HbShBlRailFare", "HbSh Bl Rail Fare", 0)
        util.initmat(eb, "mf5540", "HbPbBlRailIvtt", "HbPb Bl Rail Invehicle Time", 0)
        util.initmat(eb, "mf5541", "HbPbBlRailIvttBus", "HbPb Bl Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5542", "HbPbBlRailWait", "HbPb Bl Rail Waiting Time", 0)
        util.initmat(eb, "mf5543", "HbPbBlRailAux", "HbPb Bl Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5544", "HbPbBlRailBoard", "HbPb Bl Rail Boardings", 0)
        util.initmat(eb, "mf5545", "HbPbBlRailFare", "HbPb Bl Rail Fare", 0)
        util.initmat(eb, "mf5550", "HbSoBlRailIvtt", "HbSo Bl Rail Invehicle Time", 0)
        util.initmat(eb, "mf5551", "HbSoBlRailIvttBus", "HbSo Bl Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5552", "HbSoBlRailWait", "HbSo Bl Rail Waiting Time", 0)
        util.initmat(eb, "mf5553", "HbSoBlRailAux", "HbSo Bl Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5554", "HbSoBlRailBoard", "HbSo Bl Rail Boardings", 0)
        util.initmat(eb, "mf5555", "HbSoBlRailFare", "HbSo Bl Rail Fare", 0)
        util.initmat(eb, "mf5560", "HbEsBlRailIvtt", "HbEs Bl Rail Invehicle Time", 0)
        util.initmat(eb, "mf5561", "HbEsBlRailIvttBus", "HbEs Bl Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5562", "HbEsBlRailWait", "HbEs Bl Rail Waiting Time", 0)
        util.initmat(eb, "mf5563", "HbEsBlRailAux", "HbEs Bl Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5564", "HbEsBlRailBoard", "HbEs Bl Rail Boardings", 0)
        util.initmat(eb, "mf5565", "HbEsBlRailFare", "HbEs Bl Rail Fare", 0)
        util.initmat(eb, "mf5570", "NHbWBlRailIvtt", "NHbW Bl Rail Invehicle Time", 0)
        util.initmat(eb, "mf5571", "NHbWBlRailIvttBus", "NHbW Bl Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5572", "NHbWBlRailWait", "NHbW Bl Rail Waiting Time", 0)
        util.initmat(eb, "mf5573", "NHbWBlRailAux", "NHbW Bl Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5574", "NHbWBlRailBoard", "NHbW Bl Rail Boardings", 0)
        util.initmat(eb, "mf5575", "NHbWBlRailFare", "NHbW Bl Rail Fare", 0)
        util.initmat(eb, "mf5580", "NHbOBlRailIvtt", "NHbO Bl Rail Invehicle Time", 0)
        util.initmat(eb, "mf5581", "NHbOBlRailIvttBus", "NHbO Bl Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5582", "NHbOBlRailWait", "NHbO Bl Rail Waiting Time", 0)
        util.initmat(eb, "mf5583", "NHbOBlRailAux", "NHbO Bl Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5584", "NHbOBlRailBoard", "NHbO Bl Rail Boardings", 0)
        util.initmat(eb, "mf5585", "NHbOBlRailFare", "NHbO Bl Rail Fare", 0)
        util.initmat(eb, "mf5700", "HbWBlWceIvtt", "HbW Bl WCE Invehicle Time", 0)
        util.initmat(eb, "mf5701", "HbWBlWceIvttRail", "HbW Bl WCE Invehicle Time on WCE", 0)
        util.initmat(eb, "mf5702", "HbWBlWceIvttBus", "HbW Bl WCE Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5703", "HbWBlWceWait", "HbW Bl WCE Waiting Time", 0)
        util.initmat(eb, "mf5704", "HbWBlWceAux", "HbW Bl WCE Auxilliary Time", 0)
        util.initmat(eb, "mf5705", "HbWBlWceBoards", "HbW Bl WCE Boardings", 0)
        util.initmat(eb, "mf5706", "HbWBlWceFare", "HbW Bl WCE Fare", 0)
        util.initmat(eb, "mf6800", "HbWBlBAuPRDist", "HbW Bl Bus-Auto PR Distance", 0)
        util.initmat(eb, "mf6801", "HbWBlBAuPRTime", "HbW Bl Bus-Auto PR Time", 0)
        util.initmat(eb, "mf6802", "HbWBlBAuPRToll", "HbW Bl Bus-Auto PR Toll", 0)
        util.initmat(eb, "mf6810", "HbWBlRAuPRDist", "HbW Bl Rail-Auto PR Distance", 0)
        util.initmat(eb, "mf6811", "HbWBlRAuPRTime", "HbW Bl Rail-Auto PR Time", 0)
        util.initmat(eb, "mf6812", "HbWBlRAuPRToll", "HbW Bl Rail-Auto PR Toll", 0)
        util.initmat(eb, "mf6820", "HbWBlWAuPRDist", "HbW Bl WCE-Auto PR Distance", 0)
        util.initmat(eb, "mf6821", "HbWBlWAuPRTime", "HbW Bl WCE-Auto PR Time", 0)
        util.initmat(eb, "mf6822", "HbWBlWAuPRToll", "HbW Bl WCE-Auto PR Toll", 0)
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

        #TODO move the VOT to actual file Batchin -
        util.initmat(eb,"ms120","votWklow", "work VOT low income in min/$", 6)
        util.initmat(eb,"ms121","votWkmed", "work VOT med income in min/$", 4)
        util.initmat(eb,"ms122","votWkhigh", "work VOT high income in min/$", 3)
        util.initmat(eb,"ms123","votNWklow", "non-work VOT low income in min/$", 12)
        util.initmat(eb,"ms124","votNWkmed", "non-work VOT med income in min/$", 8)
        util.initmat(eb,"ms125","votNWkhigh", "non-work VOT high income in min/$", 6)
        util.initmat(eb,"ms130", "VOC", "Vehicle Operating Variable Cost (/km)", 0.18) # CAA includes fuel, tires, maintence
        # transit scalars
        #TODO update these factors to actual values
        util.initmat(eb, "ms199", "walkprcp", "walk time perception factor", 1)
        util.initmat(eb, "ms200", "busIVTprcp", "bus IVT perception factor", 1)
        util.initmat(eb, "ms201", "busOVTprcp", "bus OVT perception factor", 1.5)
        util.initmat(eb, "ms202", "busTRANSprcp", "bus transfer perception factor", 5)
        util.initmat(eb, "ms205", "railIVTprcp", "rail IVT perception factor", 1)
        util.initmat(eb, "ms206", "railOVTprcp", "rail OVT perception factor", 1.5)
        util.initmat(eb, "ms207", "railTRANSprcp", "rail transfer perception factor", 5)
        util.initmat(eb, "ms210", "wceIVTprcp", "wce IVT perception factor", 1)
        util.initmat(eb, "ms211", "wceOVTprcp", "wce OVT perception factor", 1.5)
        util.initmat(eb, "ms212", "wceTRANSprcp", "wce transfer perception factor", 5)
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