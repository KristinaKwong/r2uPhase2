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

        ##############################################################################
        ##       Auto Skims work
        ##############################################################################
        # Initialize Time Distance and Toll Skim Dictionaries
        TimeDict, DistDict, TollDict = {}, {}, {}
        # Generate Skim Dictionaries
        #                                 AM    ,    MD   ,     PM
        self.GenSkimDict(eb, TimeDict, ["mf2031", "mf2034", "mf2037"]) # Time
        self.GenSkimDict(eb, DistDict, ["mf2030", "mf2033", "mf2036"]) # Distance
        self.GenSkimDict(eb, TollDict, ["mf2032", "mf2035", "mf2038"]) # Toll

        # Blend Factors            AM , MD  , PM           AM  ,MD , PM       Where Blended Matrices get stored in same order as above
        BlendDict = {'hbwo':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8000', 'mf8001', 'mf8002']}, # Home-base work
                     'nhbw':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8100', 'mf8101', 'mf8102']}} # Non-home base work

        for keys, values in BlendDict.items():
            Df = {}
            # Calculate blended skim
            Df['AutoTim'] = self.testcalc(values, TimeDict)
            Df['AutoDis'] = self.testcalc(values, DistDict)
            Df['AutoTol'] = self.testcalc(values, TollDict)
        # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['AutoTim'])
            util.set_matrix_numpy(eb, values['Mat'][1], Df['AutoDis'])
            util.set_matrix_numpy(eb, values['Mat'][2], Df['AutoTol'])
        ##############################################################################

        ##       Park and Ride Home-base work Auto-leg
        ##############################################################################

        # Blend Factors                AM , MD  , PM           AM  ,MD , PM    Where Blended Matrices get stored in same order as above
        BlendDictPR = {'hbwprb':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8040', 'mf8041', 'mf8042'], #Bus
                       'BL': BLBsWk},
                       'hbwprr':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8050', 'mf8051', 'mf8052'], #Rail
                       'BL': BLRlWk},
                       'hbwprw':{'PA':[0.4, 0.0, 0.15], 'AP':[0.05, 0.0, 0.4], 'Mat':['mf8060', 'mf8061', 'mf8062'], #WCE
                       'BL': BLWcWk}
                     }

        for keys, values in BlendDictPR.items():

            Df = pd.DataFrame()
            # Generate data frame with Origin Destination and best lot
            Dfmerge = pd.DataFrame({'Or': Or, 'De': De, 'BL': values['BL']})
            # Generate second data frame and attach to it blended
            Df_Auto_Leg = pd.DataFrame({'OrAuto': Or, 'DeAuto': De})
            Df_Auto_Leg['AutoTim'] = self.testcalc(values, TimeDict).flatten()
            Df_Auto_Leg['AutoDis'] = self.testcalc(values, DistDict).flatten()
            Df_Auto_Leg['AutoTol'] = self.testcalc(values, TollDict).flatten()
            # Join the two data frames based on skims from Origin to the Best Lot
            Df = pd.merge(Dfmerge, Df_Auto_Leg, left_on = ['Or', 'BL'],
                     right_on = ['OrAuto', 'DeAuto'], how = 'left')
            # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['AutoTim'].reshape(1741,1741))
            util.set_matrix_numpy(eb, values['Mat'][1], Df['AutoDis'].reshape(1741,1741))
            util.set_matrix_numpy(eb, values['Mat'][2], Df['AutoTol'].reshape(1741,1741))
        # delete data generated to free up memory
        del Df, Dfmerge, Df_Auto_Leg, TimeDict, DistDict, TollDict

        ##############################################################################
        ##       Auto Skims Non-work
        ##############################################################################
        # Initialize Time Distance and Toll Skim Dictionaries
        TimeDict, DistDict, TollDict = {}, {}, {}
        # Generate Skim Dictionaries
        #                                 AM    ,    MD   ,     PM
        self.GenSkimDict(eb, TimeDict, ["mf931", "mf943", "mf2001"]) # Time
        self.GenSkimDict(eb, DistDict, ["mf930", "mf942", "mf2000"]) # Distance
        self.GenSkimDict(eb, TollDict, ["mf932", "mf944", "mf2002"]) # Toll
        #
        # Blend Factors            AM , MD  , PM           AM  ,MD , PM     Where Blended Matrices get stored in same order as above
        BlendDict = {'hbsc':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8200', 'mf8201', 'mf8202']}, # Home-base school
                     'hbsh':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8300', 'mf8301', 'mf8302']}, # Home-base shopping
                     'hbpb':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8400', 'mf8401', 'mf8402']}, # Home-base personal business
                     'hbun':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8500', 'mf8501', 'mf8502']}, # Home-base unitiversity
                     'hbes':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8600', 'mf8601', 'mf8602']}, # Home-base escorting
                     'hbso':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8700', 'mf8701', 'mf8702']}, # Home-base social
                     'nhbo':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8800', 'mf8801', 'mf8802']}} # non-home base other

        for keys, values in BlendDict.items():
            # Calculate blended skim
            Df = {}
            Df['AutoTim'] = self.testcalc(values, TimeDict)
            Df['AutoDis'] = self.testcalc(values, DistDict)
            Df['AutoTol'] = self.testcalc(values, TollDict)
            # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['AutoTim'])
            util.set_matrix_numpy(eb, values['Mat'][1], Df['AutoDis'])
            util.set_matrix_numpy(eb, values['Mat'][2], Df['AutoTol'])

        ##############################################################################
        ##       Park and Ride Home-base Uni/Soc Auto-leg
        ##############################################################################
        #
        # Blend Factors                AM , MD  , PM           AM  ,MD , PM       Where Blended Matrices get stored in same order as above
        BlendDictPR = {'hbunprb':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8540', 'mf8541', 'mf8542'], #HbUni Bus
                       'BL': BLBsNw},
                       'hbunprr':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8550', 'mf8551', 'mf8552'], #HbUni Rail
                       'BL': BLRlNw},
                       'hbunprw':{'PA':[0.4, 0.0, 0.15], 'AP':[0.05, 0.0, 0.4], 'Mat':['mf8560', 'mf8561', 'mf8562'], #HbUni WCE
                       'BL': BLWcNw},
                       'hbsoprb':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8740', 'mf8741', 'mf8742'], #HbSoc Bus
                       'BL': BLBsNw},
                       'hbsoprr':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8750', 'mf8751', 'mf8752'], #HbSoc Rail
                       'BL': BLRlNw},
                       'hbsoprw':{'PA':[0.4, 0.0, 0.15], 'AP':[0.05, 0.0, 0.4], 'Mat':['mf8760', 'mf8761', 'mf8762'], #HbSoc WCE
                       'BL': BLWcNw}
                       }

        for keys, values in BlendDictPR.items():

            Df = pd.DataFrame()
            # Generate data frame with Origin Destination and best lot
            Dfmerge = pd.DataFrame({'Or': Or, 'De': De, 'BL': values['BL']})
            # Generate second data frame and attach to it blended auto skims
            Df_Auto_Leg = pd.DataFrame({'OrAuto': Or, 'DeAuto': De})
            Df_Auto_Leg['AutoTim'] = self.testcalc(values, TimeDict).flatten()
            Df_Auto_Leg['AutoDis'] = self.testcalc(values, DistDict).flatten()
            Df_Auto_Leg['AutoTol'] = self.testcalc(values, TollDict).flatten()
            # Join the two data frames based on skims from Origin to the Best Lot
            Df = pd.merge(Dfmerge, Df_Auto_Leg, left_on = ['Or', 'BL'],
                     right_on = ['OrAuto', 'DeAuto'], how = 'left')
            # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['AutoTim'].reshape(1741,1741))
            util.set_matrix_numpy(eb, values['Mat'][1], Df['AutoDis'].reshape(1741,1741))
            util.set_matrix_numpy(eb, values['Mat'][2], Df['AutoTol'].reshape(1741,1741))
        # delete data generated to free up memory
        del Df, Dfmerge, Df_Auto_Leg, TimeDict, DistDict, TollDict
#
#       ##############################################################################
#       ##       Bus Skims
#       ##############################################################################
#       # Initialize In-vehicle, Wait, Auxiliary, Boarding and Fare Skim Dictionaries
        BusIVTDict, BusWatDict, BusAuxDict = {}, {}, {}
        BusBrdDict, BusFarDict = {}, {}
        # Generate Skim Dictionaries
        #                                  AM    ,    MD   ,     PM
        self.GenSkimDict(eb, BusIVTDict, ["mf107", "mf112", "mf2107"]) # Bus IVTT
        self.GenSkimDict(eb, BusWatDict, ["mf106", "mf111", "mf2106"]) # Bus Wait
        self.GenSkimDict(eb, BusAuxDict, ["mf109", "mf114", "mf2109"]) # Bus Aux
        self.GenSkimDict(eb, BusBrdDict, ["mf108", "mf113", "mf2108"]) # Bus Boarding
        self.GenSkimDict(eb, BusFarDict, ["mf160", "mf160", "mf160"])  # Bus Fare

       # Blend Factors
        BlendDict = {   #AM,   MD,   PM         AM,   MD,   PM         Where Blended Matrices get stored in same order as above
         'hbwo':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8010', 'mf8011', 'mf8012', 'mf8013', 'mf8014']},  # Home-base work
         'nhbw':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8110', 'mf8111', 'mf8112', 'mf8113', 'mf8114']},  # Non-home base work
         'hbsc':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8210', 'mf8211', 'mf8212', 'mf8213', 'mf8214']},  # Home-base school
         'hbsh':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8310', 'mf8311', 'mf8312', 'mf8313', 'mf8314']},  # Home-base shopping
         'hbpb':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8410', 'mf8411', 'mf8412', 'mf8413', 'mf8414']},  # Home-base personal business
         'hbun':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8510', 'mf8511', 'mf8512', 'mf8513', 'mf8514']},  # Home-base unitiversity
         'hbes':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8610', 'mf8611', 'mf8612', 'mf8613', 'mf8614']},  # Home-base escorting
         'hbso':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8710', 'mf8711', 'mf8712', 'mf8713', 'mf8714']},  # Home-base social
         'nhbo':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8810', 'mf8811', 'mf8812', 'mf8813', 'mf8814']}}  # Non-home base other

        for keys, values in BlendDict.items():
            # Calculate blended skims
            Df = {}
            Df['BusIVT']  = self.testcalc(values, BusIVTDict)
            Df['BusWat']  = self.testcalc(values, BusWatDict)
            Df['BusAux']  = self.testcalc(values, BusAuxDict)
            Df['BusBrd']  = self.testcalc(values, BusBrdDict)
            Df['BusFar']  = self.testcalc(values, BusFarDict)
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
         'hbwo':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8043', 'mf8044', 'mf8045', 'mf8046', 'mf8047'], # Home-base work
         'BL': BLBsWk},
         'hbun':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8543', 'mf8544', 'mf8545', 'mf8546', 'mf8547'], # Home-base unitiversity
         'BL': BLBsNw},
         'hbso':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3], 'Mat':['mf8743', 'mf8744', 'mf8745', 'mf8746', 'mf8747'], # Home-base social
         'BL': BLBsNw}}

        for keys, values in BlendDictPR.items():

            Df = pd.DataFrame()
            # Generate data frame with Origin Destination and best lot
            Dfmerge = pd.DataFrame({'Or': Or, 'De': De, 'BL': values['BL']})
            # Generate second data frame and attach to it bus skims
            Df_Bus_Leg = pd.DataFrame({'OrTran': Or, 'DeTran': De})
            Df_Bus_Leg['BusIVT']  = self.testcalc(values, BusIVTDict).flatten()
            Df_Bus_Leg['BusWat']  = self.testcalc(values, BusWatDict).flatten()
            Df_Bus_Leg['BusAux']  = self.testcalc(values, BusAuxDict).flatten()
            Df_Bus_Leg['BusBrd']  = self.testcalc(values, BusBrdDict).flatten()
            Df_Bus_Leg['BusFar']  = self.testcalc(values, BusFarDict).flatten()
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
        self.GenSkimDict(eb, RalIVBDict, ["mf5000", "mf5005", "mf5010"]) # Rail IVB
        self.GenSkimDict(eb, RalIVRDict, ["mf5001", "mf5006", "mf5011"]) # Rail IVR
        self.GenSkimDict(eb, RalWatDict, ["mf5002", "mf5007", "mf5012"]) # Rail Wait
        self.GenSkimDict(eb, RalAuxDict, ["mf5004", "mf5009", "mf5014"]) # Rail Aux
        self.GenSkimDict(eb, RalBrdDict, ["mf5003", "mf5008", "mf5013"]) # Rail Boarding
        self.GenSkimDict(eb, RalFarDict, ["mf161", "mf161", "mf161"])    # Rail Fare

        # Blend Factors
        BlendDict = {  #AM,   MD,   PM         AM,   MD,   PM
         'hbwo':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3],
                 'Mat':['mf8020', 'mf8021', 'mf8022', 'mf8023', 'mf8024', 'mf8025']}, # Where Blended Matrices get stored in same order as above
         'nhbw':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3],
                 'Mat':['mf8120', 'mf8121', 'mf8122', 'mf8123', 'mf8124', 'mf8125']},
         'hbsc':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3],
                 'Mat':['mf8220', 'mf8221', 'mf8222', 'mf8223', 'mf8224', 'mf8225']},
         'hbsh':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3],
                 'Mat':['mf8320', 'mf8321', 'mf8322', 'mf8323', 'mf8324', 'mf8325']},
         'hbpb':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3],
                 'Mat':['mf8420', 'mf8421', 'mf8422', 'mf8423', 'mf8424', 'mf8425']},
         'hbun':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3],
                 'Mat':['mf8520', 'mf8521', 'mf8522', 'mf8523', 'mf8524', 'mf8525']},
         'hbes':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3],
                 'Mat':['mf8620', 'mf8621', 'mf8622', 'mf8623', 'mf8624', 'mf8625']},
         'hbso':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3],
                 'Mat':['mf8720', 'mf8721', 'mf8722', 'mf8723', 'mf8724', 'mf8725']},
         'nhbo':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3],
                 'Mat':['mf8820', 'mf8821', 'mf8822', 'mf8823', 'mf8824', 'mf8825']}}

        for keys, values in BlendDict.items():
            # Calculate blended skims
            Df = {}
            Df['RalIVB'] = self.testcalc(values, RalIVBDict)
            Df['RalIVR'] = self.testcalc(values, RalIVRDict)
            Df['RalWat'] = self.testcalc(values, RalWatDict)
            Df['RalAux'] = self.testcalc(values, RalAuxDict)
            Df['RalBrd'] = self.testcalc(values, RalBrdDict)
            Df['RalFar'] = self.testcalc(values, RalFarDict)
            # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['RalIVB'])
            util.set_matrix_numpy(eb, values['Mat'][1], Df['RalIVR'])
            util.set_matrix_numpy(eb, values['Mat'][2], Df['RalWat'])
            util.set_matrix_numpy(eb, values['Mat'][3], Df['RalAux'])
            util.set_matrix_numpy(eb, values['Mat'][4], Df['RalBrd'])
            util.set_matrix_numpy(eb, values['Mat'][5], Df['RalFar'])
#       ##############################################################################
#        ##       Park and Ride Home-base Work/Uni/Soc Rail-leg
#        ##############################################################################
        BlendDictPR = { #AM,   MD,   PM         AM,   MD,   PM
         'hbwo':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3],
                 'Mat':['mf8053', 'mf8054', 'mf8055', 'mf8056', 'mf8057', 'mf8058'], 'BL': BLRlWk}, #Where Blended Matrices get stored in same order as above
         'hbun':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3],
                 'Mat':['mf8543', 'mf8544', 'mf8545', 'mf8546', 'mf8557', 'mf8558'], 'BL': BLRlNw},
         'hbso':{'PA':[0.3, 0.1, 0.15], 'AP':[0.05, 0.1, 0.3],
                 'Mat':['mf8743', 'mf8744', 'mf8745', 'mf8746', 'mf8757', 'mf8758'], 'BL': BLRlNw}}

        for keys, values in BlendDictPR.items():

            Df = pd.DataFrame()
            # Generate data frame with Origin Destination and best lot
            Dfmerge = pd.DataFrame({'Or': Or, 'De': De, 'BL': values['BL']})
            # Generate second data frame and attach to it rail skims
            Df_Rail_Leg = pd.DataFrame({'OrTran': Or, 'DeTran': De})
            Df_Rail_Leg['RalIVB'] = self.testcalc(values, RalIVBDict).flatten()
            Df_Rail_Leg['RalIVR'] = self.testcalc(values, RalIVRDict).flatten()
            Df_Rail_Leg['RalWat'] = self.testcalc(values, RalWatDict).flatten()
            Df_Rail_Leg['RalAux'] = self.testcalc(values, RalAuxDict).flatten()
            Df_Rail_Leg['RalBrd'] = self.testcalc(values, RalBrdDict).flatten()
            Df_Rail_Leg['RalFar'] = self.testcalc(values, RalFarDict).flatten()
            # Join the two data frames based on skims from the Best Lot to the destination
            Df = pd.merge(Dfmerge, Df_Rail_Leg, left_on = ['BL', 'De'],
                     right_on = ['OrTran', 'DeTran'], how = 'left')
            # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['RalIVB'].reshape(1741,1741))
            util.set_matrix_numpy(eb, values['Mat'][1], Df['RalIVR'].reshape(1741,1741))
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
        self.GenSkimDictWCE(eb, WCEIVBDict, ["mf5050", "mf5062"]) # WCE IVB
        self.GenSkimDictWCE(eb, WCEIVRDict, ["mf5051", "mf5063"]) # WCE IVR
        self.GenSkimDictWCE(eb, WCEIVWDict, ["mf5052", "mf5064"]) # WCE IVW
        self.GenSkimDictWCE(eb, WCEWatDict, ["mf5053", "mf5065"]) # WCE Wait
        self.GenSkimDictWCE(eb, WCEAuxDict, ["mf5055", "mf5067"]) # WCE Aux
        self.GenSkimDictWCE(eb, WCEBrdDict, ["mf5054", "mf5066"]) # WCE Boarding
        self.GenSkimDictWCE(eb, WCEFarDict, ["mf161", "mf161"])   # WCE Fare

#        # Blend Factors
        BlendDict = {    #AM,   PM,        AM,   PM,
         'hbwo':{'PA':[0.4, 0.15], 'AP':[0.1, 0.35],
                 'Mat':['mf8030', 'mf8031', 'mf8032', 'mf8033', 'mf8034', 'mf8035', 'mf8036']},  # Where Blended Matrices get stored in same order as above
         'nhbw':{'PA':[0.4, 0.15], 'AP':[0.1, 0.35],
                 'Mat':['mf8130', 'mf8131', 'mf8132', 'mf8133', 'mf8134', 'mf8135', 'mf8136']},
         'hbsc':{'PA':[0.4, 0.15], 'AP':[0.1, 0.35],
                 'Mat':['mf8230', 'mf8231', 'mf8232', 'mf8233', 'mf8234', 'mf8235', 'mf8236']},
         'hbsh':{'PA':[0.4, 0.15], 'AP':[0.1, 0.35],
                 'Mat':['mf8330', 'mf8331', 'mf8332', 'mf8333', 'mf8334', 'mf8335', 'mf8336']},
         'hbpb':{'PA':[0.4, 0.15], 'AP':[0.1, 0.35],
                 'Mat':['mf8430', 'mf8431', 'mf8432', 'mf8433', 'mf8434', 'mf8435', 'mf8436']},
         'hbun':{'PA':[0.4, 0.15], 'AP':[0.1, 0.35],
                 'Mat':['mf8530', 'mf8531', 'mf8532', 'mf8533', 'mf8534', 'mf8535', 'mf8536']},
         'hbes':{'PA':[0.4, 0.15], 'AP':[0.1, 0.35],
                 'Mat':['mf8630', 'mf8631', 'mf8632', 'mf8633', 'mf8634', 'mf8635', 'mf8636']},
         'hbso':{'PA':[0.4, 0.15], 'AP':[0.1, 0.35],
                 'Mat':['mf8730', 'mf8731', 'mf8732', 'mf8733', 'mf8734', 'mf8735', 'mf8736']},
         'nhbo':{'PA':[0.4, 0.15], 'AP':[0.1, 0.35],
                 'Mat':['mf8830', 'mf8831', 'mf8832', 'mf8833', 'mf8834', 'mf8835', 'mf8836']}}

        for keys, values in BlendDict.items():
            # Calculate blended skims
            Df = {}
            Df['WCEIVB'] = self.testcalc(values, WCEIVBDict)
            Df['WCEIVR'] = self.testcalc(values, WCEIVRDict)
            Df['WCEIVW'] = self.testcalc(values, WCEIVWDict)
            Df['WCEWat'] = self.testcalc(values, WCEWatDict)
            Df['WCEAux'] = self.testcalc(values, WCEAuxDict)
            Df['WCEBrd'] = self.testcalc(values, WCEBrdDict)
            Df['WCEFar'] = self.testcalc(values, WCEFarDict)
            # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['WCEIVB'])
            util.set_matrix_numpy(eb, values['Mat'][1], Df['WCEIVR'])
            util.set_matrix_numpy(eb, values['Mat'][2], Df['WCEIVW'])
            util.set_matrix_numpy(eb, values['Mat'][3], Df['WCEWat'])
            util.set_matrix_numpy(eb, values['Mat'][4], Df['WCEAux'])
            util.set_matrix_numpy(eb, values['Mat'][5], Df['WCEBrd'])
            util.set_matrix_numpy(eb, values['Mat'][6], Df['WCEFar'])
#        ##############################################################################
#        ##       Park and Ride Home-base Work/Uni/Soc WCE-leg
#        ##############################################################################
        BlendDictPR = { #AM,   PM,        AM,   PM,
         'hbwo':{'PA':[0.4, 0.15], 'AP':[0.1, 0.35],  'BL': BLWcWk,
                 'Mat':['mf8063', 'mf8064', 'mf8065', 'mf8066', 'mf8067', 'mf8068', 'mf8069']}, # Where Blended Matrices get stored in same order as above
         'hbun':{'PA':[0.4, 0.15], 'AP':[0.1, 0.35],  'BL': BLWcNw,
                 'Mat':['mf8563', 'mf8564', 'mf8565', 'mf8566', 'mf8567', 'mf8568', 'mf8569']},
         'hbso':{'PA':[0.4, 0.15], 'AP':[0.1, 0.35],  'BL': BLWcNw,
                 'Mat':['mf8763', 'mf8764', 'mf8765', 'mf8766', 'mf8767', 'mf8768', 'mf8769']}}

        for keys, values in BlendDictPR.items():

            Df = pd.DataFrame()
            # Generate data frame with Origin Destination and best lot
            Dfmerge = pd.DataFrame({'Or': Or, 'De': De, 'BL': values['BL']})
            # Generate second data frame and attach to it wce skims
            Df_WCE_Leg = pd.DataFrame({'OrTran': Or, 'DeTran': De})
            Df_WCE_Leg['WCEIVB'] = self.testcalc(values, WCEIVBDict).flatten()
            Df_WCE_Leg['WCEIVR'] = self.testcalc(values, WCEIVRDict).flatten()
            Df_WCE_Leg['WCEIVW'] = self.testcalc(values, WCEIVWDict).flatten()
            Df_WCE_Leg['WCEWat'] = self.testcalc(values, WCEWatDict).flatten()
            Df_WCE_Leg['WCEAux'] = self.testcalc(values, WCEAuxDict).flatten()
            Df_WCE_Leg['WCEBrd'] = self.testcalc(values, WCEBrdDict).flatten()
            Df_WCE_Leg['WCEFar'] = self.testcalc(values, WCEFarDict).flatten()
             # Join the two data frames based on skims from the Best Lot to the destination
            Df = pd.merge(Dfmerge, Df_WCE_Leg, left_on = ['BL', 'De'],
                     right_on = ['OrTran', 'DeTran'], how = 'left')
            # Put results back in the Emmebank
            util.set_matrix_numpy(eb, values['Mat'][0], Df['WCEIVB'].reshape(1741,1741))
            util.set_matrix_numpy(eb, values['Mat'][1], Df['WCEIVR'].reshape(1741,1741))
            util.set_matrix_numpy(eb, values['Mat'][2], Df['WCEIVW'].reshape(1741,1741))
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
        Dict['AP'] = [AM_Mat.transpose(), MD_Mat.transpose(),PM_Mat.transpose()]
        return (Dict)

    def GenSkimDictWCE(self, eb, Dict, Mat):
        util = _m.Modeller().tool("translink.emme.util")
        AM_Mat = util.get_matrix_numpy(eb, Mat[0])
        PM_Mat = util.get_matrix_numpy(eb, Mat[1])

        Dict['PA'] = [AM_Mat, PM_Mat]
        Dict['AP'] = [AM_Mat.transpose(), PM_Mat.transpose()]
        return (Dict)

    def testcalc(self, Fact, Dict):
        util = _m.Modeller().tool("translink.emme.util")
        Result = util.sumproduct(Fact['PA'], Dict['PA']) + util.sumproduct(Fact['AP'], Dict['AP'])

        return Result

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
        transit_mats = {"wceIVT" : ["mf5052",  "mf5058", "mf5064"],
                        "wceWait" : ["mf5053",  "mf5059", "mf5065"],
                        "railIVT" : ["mf5051",  "mf5057", "mf5063"],
                        "busIVT" : ["mf5050",  "mf5056", "mf5062"],
                        "auxTransit" : ["mf5055",  "mf5061", "mf5067"],
                        "boardings" : ["mf5054",  "mf5060", "mf5066"],
                        "wceFare" : ["mf161",  "mf161", "mf161"]}

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
        transit_mats = {"railIVT" : ["mf5001",  "mf5006", "mf5011"],
                        "railWait" : ["mf5002",  "mf5007", "mf5012"],
                        "busIVT" : ["mf5000",  "mf5005", "mf5010"],
                        "auxTransit" : ["mf5004", "mf5009", "mf5014"],
                        "boardings" : ["mf5003", "mf5008", "mf5013"],
                        "railFare" : ["mf161",  "mf161", "mf161"]}

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
        transit_mats = {"busIVT" : ["mf107",  "mf112", "mf2107"],
                        "busWait" : ["mf106",  "mf111", "mf2106"],
                        "auxTransit" : ["mf109", "mf114", "mf2109"],
                        "boardings" : ["mf108", "mf113", "mf2108"],
                        "busFare" : ["mf160",  "mf160", "mf160"]}

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
        auto_mats = {"autotime" : ["mf2031",  "mf2034", "mf2037"],
                    "autotoll" : ["mf2032", "mf2035", "mf2038"],
                    "autodist" : ["mf2030", "mf2033", "mf2036"]}

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



        auto_mats = {"autotime" : ["mf931",  "mf943", "mf2001"],
                    "autotoll" : ["mf932", "mf944", "mf2002"],
                    "autodist" : ["mf930", "mf942", "mf2000"] }

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

        util.initmat(eb, "mf8000", "HwAuTi", "HwAuTi", 0)
        util.initmat(eb, "mf8001", "HwAuDi", "HwAuDi", 0)
        util.initmat(eb, "mf8002", "HwAuTo", "HwAuTo", 0)
        util.initmat(eb, "mf8010", "HwBsIB", "HwBsIB", 0)
        util.initmat(eb, "mf8011", "HwBsWB", "HwBsWB", 0)
        util.initmat(eb, "mf8012", "HwBsAB", "HwBsAB", 0)
        util.initmat(eb, "mf8013", "HwBsBB", "HwBsBB", 0)
        util.initmat(eb, "mf8014", "HwBsFB", "HwBsFB", 0)
        util.initmat(eb, "mf8020", "HwRlIB", "HwRlIB", 0)
        util.initmat(eb, "mf8021", "HwRlIR", "HwRlIR", 0)
        util.initmat(eb, "mf8022", "HwRlWR", "HwRlWR", 0)
        util.initmat(eb, "mf8023", "HwRlAR", "HwRlAR", 0)
        util.initmat(eb, "mf8024", "HwRlBR", "HwRlBR", 0)
        util.initmat(eb, "mf8025", "HwRlFR", "HwRlFR", 0)
        util.initmat(eb, "mf8030", "HwWcIB", "HwWcIB", 0)
        util.initmat(eb, "mf8031", "HwWcIR", "HwWcIR", 0)
        util.initmat(eb, "mf8032", "HwWcIW", "HwWcIW", 0)
        util.initmat(eb, "mf8033", "HwWcWW", "HwWcWW", 0)
        util.initmat(eb, "mf8034", "HwWcAW", "HwWcAW", 0)
        util.initmat(eb, "mf8035", "HwWcBW", "HwWcBW", 0)
        util.initmat(eb, "mf8036", "HwWcFW", "HwWcFW", 0)
        util.initmat(eb, "mf8040", "HwPRBAti", "HwPRBAti", 0)
        util.initmat(eb, "mf8041", "HwPRBAdi", "HwPRBAdi", 0)
        util.initmat(eb, "mf8042", "HwPRBAto", "HwPRBAto", 0)
        util.initmat(eb, "mf8043", "HwPRBIB", "HwPRBIB", 0)
        util.initmat(eb, "mf8044", "HwPRBWB", "HwPRBWB", 0)
        util.initmat(eb, "mf8045", "HwPRBAB", "HwPRBAB", 0)
        util.initmat(eb, "mf8046", "HwPRBBB", "HwPRBBB", 0)
        util.initmat(eb, "mf8047", "HwPRBFB", "HwPRBFB", 0)
        util.initmat(eb, "mf8050", "HwPRRAti", "HwPRRAti", 0)
        util.initmat(eb, "mf8051", "HwPRRAdi", "HwPRRAdi", 0)
        util.initmat(eb, "mf8052", "HwPRRAto", "HwPRRAto", 0)
        util.initmat(eb, "mf8053", "HwPRRIB", "HwPRRIB", 0)
        util.initmat(eb, "mf8054", "HwPRRIR", "HwPRRIR", 0)
        util.initmat(eb, "mf8055", "HwPRRWR", "HwPRRWR", 0)
        util.initmat(eb, "mf8056", "HwPRRAR", "HwPRRAR", 0)
        util.initmat(eb, "mf8057", "HwPRRBR", "HwPRRBR", 0)
        util.initmat(eb, "mf8058", "HwPRRFR", "HwPRRFR", 0)
        util.initmat(eb, "mf8060", "HwPRWAti", "HwPRWAti", 0)
        util.initmat(eb, "mf8061", "HwPRWAdi", "HwPRWAdi", 0)
        util.initmat(eb, "mf8062", "HwPRWAto", "HwPRWAto", 0)
        util.initmat(eb, "mf8063", "HwPRWIB", "HwPRWIB", 0)
        util.initmat(eb, "mf8064", "HwPRWIR", "HwPRWIR", 0)
        util.initmat(eb, "mf8065", "HwPRWIW", "HwPRWIW", 0)
        util.initmat(eb, "mf8066", "HwPRWWW", "HwPRWWW", 0)
        util.initmat(eb, "mf8067", "HwPRWAW", "HwPRWAW", 0)
        util.initmat(eb, "mf8068", "HwPRWBW", "HwPRWBW", 0)
        util.initmat(eb, "mf8069", "HwPRWFW", "HwPRWFW", 0)
        util.initmat(eb, "mf8100", "NhwAuTi", "NhwAuTi", 0)
        util.initmat(eb, "mf8101", "NhwAuDi", "NhwAuDi", 0)
        util.initmat(eb, "mf8102", "NhwAuTo", "NhwAuTo", 0)
        util.initmat(eb, "mf8110", "NhwBsIB", "NhwBsIB", 0)
        util.initmat(eb, "mf8111", "NhwBsWB", "NhwBsWB", 0)
        util.initmat(eb, "mf8112", "NhwBsAB", "NhwBsAB", 0)
        util.initmat(eb, "mf8113", "NhwBsBB", "NhwBsBB", 0)
        util.initmat(eb, "mf8114", "NhwBsFB", "NhwBsFB", 0)
        util.initmat(eb, "mf8120", "NhwRlIB", "NhwRlIB", 0)
        util.initmat(eb, "mf8121", "NhwRlIR", "NhwRlIR", 0)
        util.initmat(eb, "mf8122", "NhwRlWR", "NhwRlWR", 0)
        util.initmat(eb, "mf8123", "NhwRlAR", "NhwRlAR", 0)
        util.initmat(eb, "mf8124", "NhwRlBR", "NhwRlBR", 0)
        util.initmat(eb, "mf8125", "NhwRlFR", "NhwRlFR", 0)
        util.initmat(eb, "mf8130", "NhwWcIB", "NhwWcIB", 0)
        util.initmat(eb, "mf8131", "NhwWcIR", "NhwWcIR", 0)
        util.initmat(eb, "mf8132", "NhwWcIW", "NhwWcIW", 0)
        util.initmat(eb, "mf8133", "NhwWcWW", "NhwWcWW", 0)
        util.initmat(eb, "mf8134", "NhwWcAW", "NhwWcAW", 0)
        util.initmat(eb, "mf8135", "NhwWcBW", "NhwWcBW", 0)
        util.initmat(eb, "mf8136", "NhwWcFW", "NhwWcFW", 0)
        util.initmat(eb, "mf8140", "NhwPRBAti", "NhwPRBAti", 0)
        util.initmat(eb, "mf8141", "NhwPRBAdi", "NhwPRBAdi", 0)
        util.initmat(eb, "mf8142", "NhwPRBAto", "NhwPRBAto", 0)
        util.initmat(eb, "mf8143", "NhwPRBIB", "NhwPRBIB", 0)
        util.initmat(eb, "mf8144", "NhwPRBWB", "NhwPRBWB", 0)
        util.initmat(eb, "mf8145", "NhwPRBAB", "NhwPRBAB", 0)
        util.initmat(eb, "mf8146", "NhwPRBBB", "NhwPRBBB", 0)
        util.initmat(eb, "mf8147", "NhwPRBFB", "NhwPRBFB", 0)
        util.initmat(eb, "mf8150", "NhwPRRAti", "NhwPRRAti", 0)
        util.initmat(eb, "mf8151", "NhwPRRAdi", "NhwPRRAdi", 0)
        util.initmat(eb, "mf8152", "NhwPRRAto", "NhwPRRAto", 0)
        util.initmat(eb, "mf8153", "NhwPRRIB", "NhwPRRIB", 0)
        util.initmat(eb, "mf8154", "NhwPRRIR", "NhwPRRIR", 0)
        util.initmat(eb, "mf8155", "NhwPRRWR", "NhwPRRWR", 0)
        util.initmat(eb, "mf8156", "NhwPRRAR", "NhwPRRAR", 0)
        util.initmat(eb, "mf8157", "NhwPRRBR", "NhwPRRBR", 0)
        util.initmat(eb, "mf8158", "NhwPRRFR", "NhwPRRFR", 0)
        util.initmat(eb, "mf8160", "NhwPRWAti", "NhwPRWAti", 0)
        util.initmat(eb, "mf8161", "NhwPRWAdi", "NhwPRWAdi", 0)
        util.initmat(eb, "mf8162", "NhwPRWAto", "NhwPRWAto", 0)
        util.initmat(eb, "mf8163", "NhwPRWIB", "NhwPRWIB", 0)
        util.initmat(eb, "mf8164", "NhwPRWIR", "NhwPRWIR", 0)
        util.initmat(eb, "mf8165", "NhwPRWIW", "NhwPRWIW", 0)
        util.initmat(eb, "mf8166", "NhwPRWWW", "NhwPRWWW", 0)
        util.initmat(eb, "mf8167", "NhwPRWAW", "NhwPRWAW", 0)
        util.initmat(eb, "mf8168", "NhwPRWBW", "NhwPRWBW", 0)
        util.initmat(eb, "mf8169", "NhwPRWFW", "NhwPRWFW", 0)
        util.initmat(eb, "mf8200", "HSchAuTi", "HSchAuTi", 0)
        util.initmat(eb, "mf8201", "HSchAuDi", "HSchAuDi", 0)
        util.initmat(eb, "mf8202", "HSchAuTo", "HSchAuTo", 0)
        util.initmat(eb, "mf8210", "HSchBsIB", "HSchBsIB", 0)
        util.initmat(eb, "mf8211", "HSchBsWB", "HSchBsWB", 0)
        util.initmat(eb, "mf8212", "HSchBsAB", "HSchBsAB", 0)
        util.initmat(eb, "mf8213", "HSchBsBB", "HSchBsBB", 0)
        util.initmat(eb, "mf8214", "HSchBsFB", "HSchBsFB", 0)
        util.initmat(eb, "mf8220", "HSchRlIB", "HSchRlIB", 0)
        util.initmat(eb, "mf8221", "HSchRlIR", "HSchRlIR", 0)
        util.initmat(eb, "mf8222", "HSchRlWR", "HSchRlWR", 0)
        util.initmat(eb, "mf8223", "HSchRlAR", "HSchRlAR", 0)
        util.initmat(eb, "mf8224", "HSchRlBR", "HSchRlBR", 0)
        util.initmat(eb, "mf8225", "HSchRlFR", "HSchRlFR", 0)
        util.initmat(eb, "mf8230", "HSchWcIB", "HSchWcIB", 0)
        util.initmat(eb, "mf8231", "HSchWcIR", "HSchWcIR", 0)
        util.initmat(eb, "mf8232", "HSchWcIW", "HSchWcIW", 0)
        util.initmat(eb, "mf8233", "HSchWcWW", "HSchWcWW", 0)
        util.initmat(eb, "mf8234", "HSchWcAW", "HSchWcAW", 0)
        util.initmat(eb, "mf8235", "HSchWcBW", "HSchWcBW", 0)
        util.initmat(eb, "mf8236", "HSchWcFW", "HSchWcFW", 0)
        util.initmat(eb, "mf8300", "HShpAuTi", "HShpAuTi", 0)
        util.initmat(eb, "mf8301", "HShpAuDi", "HShpAuDi", 0)
        util.initmat(eb, "mf8302", "HShpAuTo", "HShpAuTo", 0)
        util.initmat(eb, "mf8310", "HShpBsIB", "HShpBsIB", 0)
        util.initmat(eb, "mf8311", "HShpBsWB", "HShpBsWB", 0)
        util.initmat(eb, "mf8312", "HShpBsAB", "HShpBsAB", 0)
        util.initmat(eb, "mf8313", "HShpBsBB", "HShpBsBB", 0)
        util.initmat(eb, "mf8314", "HShpBsFB", "HShpBsFB", 0)
        util.initmat(eb, "mf8320", "HShpRlIB", "HShpRlIB", 0)
        util.initmat(eb, "mf8321", "HShpRlIR", "HShpRlIR", 0)
        util.initmat(eb, "mf8322", "HShpRlWR", "HShpRlWR", 0)
        util.initmat(eb, "mf8323", "HShpRlAR", "HShpRlAR", 0)
        util.initmat(eb, "mf8324", "HShpRlBR", "HShpRlBR", 0)
        util.initmat(eb, "mf8325", "HShpRlFR", "HShpRlFR", 0)
        util.initmat(eb, "mf8330", "HShpWcIB", "HShpWcIB", 0)
        util.initmat(eb, "mf8331", "HShpWcIR", "HShpWcIR", 0)
        util.initmat(eb, "mf8332", "HShpWcIW", "HShpWcIW", 0)
        util.initmat(eb, "mf8333", "HShpWcWW", "HShpWcWW", 0)
        util.initmat(eb, "mf8334", "HShpWcAW", "HShpWcAW", 0)
        util.initmat(eb, "mf8335", "HShpWcBW", "HShpWcBW", 0)
        util.initmat(eb, "mf8336", "HShpWcFW", "HShpWcFW", 0)
        util.initmat(eb, "mf8400", "HPBAuTi", "HPBAuTi", 0)
        util.initmat(eb, "mf8401", "HPBAuDi", "HPBAuDi", 0)
        util.initmat(eb, "mf8402", "HPBAuTo", "HPBAuTo", 0)
        util.initmat(eb, "mf8410", "HPBBsIB", "HPBBsIB", 0)
        util.initmat(eb, "mf8411", "HPBBsWB", "HPBBsWB", 0)
        util.initmat(eb, "mf8412", "HPBBsAB", "HPBBsAB", 0)
        util.initmat(eb, "mf8413", "HPBBsBB", "HPBBsBB", 0)
        util.initmat(eb, "mf8414", "HPBBsFB", "HPBBsFB", 0)
        util.initmat(eb, "mf8420", "HPBRlIB", "HPBRlIB", 0)
        util.initmat(eb, "mf8421", "HPBRlIR", "HPBRlIR", 0)
        util.initmat(eb, "mf8422", "HPBRlWR", "HPBRlWR", 0)
        util.initmat(eb, "mf8423", "HPBRlAR", "HPBRlAR", 0)
        util.initmat(eb, "mf8424", "HPBRlBR", "HPBRlBR", 0)
        util.initmat(eb, "mf8425", "HPBRlFR", "HPBRlFR", 0)
        util.initmat(eb, "mf8430", "HPBWcIB", "HPBWcIB", 0)
        util.initmat(eb, "mf8431", "HPBWcIR", "HPBWcIR", 0)
        util.initmat(eb, "mf8432", "HPBWcIW", "HPBWcIW", 0)
        util.initmat(eb, "mf8433", "HPBWcWW", "HPBWcWW", 0)
        util.initmat(eb, "mf8434", "HPBWcAW", "HPBWcAW", 0)
        util.initmat(eb, "mf8435", "HPBWcBW", "HPBWcBW", 0)
        util.initmat(eb, "mf8436", "HPBWcFW", "HPBWcFW", 0)
        util.initmat(eb, "mf8500", "HUniAuTi", "HUniAuTi", 0)
        util.initmat(eb, "mf8501", "HUniAuDi", "HUniAuDi", 0)
        util.initmat(eb, "mf8502", "HUniAuTo", "HUniAuTo", 0)
        util.initmat(eb, "mf8510", "HUniBsIB", "HUniBsIB", 0)
        util.initmat(eb, "mf8511", "HUniBsWB", "HUniBsWB", 0)
        util.initmat(eb, "mf8512", "HUniBsAB", "HUniBsAB", 0)
        util.initmat(eb, "mf8513", "HUniBsBB", "HUniBsBB", 0)
        util.initmat(eb, "mf8514", "HUniBsFB", "HUniBsFB", 0)
        util.initmat(eb, "mf8520", "HUniRlIB", "HUniRlIB", 0)
        util.initmat(eb, "mf8521", "HUniRlIR", "HUniRlIR", 0)
        util.initmat(eb, "mf8522", "HUniRlWR", "HUniRlWR", 0)
        util.initmat(eb, "mf8523", "HUniRlAR", "HUniRlAR", 0)
        util.initmat(eb, "mf8524", "HUniRlBR", "HUniRlBR", 0)
        util.initmat(eb, "mf8525", "HUniRlFR", "HUniRlFR", 0)
        util.initmat(eb, "mf8530", "HUniWcIB", "HUniWcIB", 0)
        util.initmat(eb, "mf8531", "HUniWcIR", "HUniWcIR", 0)
        util.initmat(eb, "mf8532", "HUniWcIW", "HUniWcIW", 0)
        util.initmat(eb, "mf8533", "HUniWcWW", "HUniWcWW", 0)
        util.initmat(eb, "mf8534", "HUniWcAW", "HUniWcAW", 0)
        util.initmat(eb, "mf8535", "HUniWcBW", "HUniWcBW", 0)
        util.initmat(eb, "mf8536", "HUniWcFW", "HUniWcFW", 0)
        util.initmat(eb, "mf8540", "HUniPRBAti", "HUniPRBAti", 0)
        util.initmat(eb, "mf8541", "HUniPRBAdi", "HUniPRBAdi", 0)
        util.initmat(eb, "mf8542", "HUniPRBAto", "HUniPRBAto", 0)
        util.initmat(eb, "mf8543", "HUniPRBIB", "HUniPRBIB", 0)
        util.initmat(eb, "mf8544", "HUniPRBWB", "HUniPRBWB", 0)
        util.initmat(eb, "mf8545", "HUniPRBAB", "HUniPRBAB", 0)
        util.initmat(eb, "mf8546", "HUniPRBBB", "HUniPRBBB", 0)
        util.initmat(eb, "mf8547", "HUniPRBFB", "HUniPRBFB", 0)
        util.initmat(eb, "mf8550", "HUniPRRAti", "HUniPRRAti", 0)
        util.initmat(eb, "mf8551", "HUniPRRAdi", "HUniPRRAdi", 0)
        util.initmat(eb, "mf8552", "HUniPRRAto", "HUniPRRAto", 0)
        util.initmat(eb, "mf8553", "HUniPRRIB", "HUniPRRIB", 0)
        util.initmat(eb, "mf8554", "HUniPRRIR", "HUniPRRIR", 0)
        util.initmat(eb, "mf8555", "HUniPRRWR", "HUniPRRWR", 0)
        util.initmat(eb, "mf8556", "HUniPRRAR", "HUniPRRAR", 0)
        util.initmat(eb, "mf8557", "HUniPRRBR", "HUniPRRBR", 0)
        util.initmat(eb, "mf8558", "HUniPRRFR", "HUniPRRFR", 0)
        util.initmat(eb, "mf8560", "HUniPRWAti", "HUniPRWAti", 0)
        util.initmat(eb, "mf8561", "HUniPRWAdi", "HUniPRWAdi", 0)
        util.initmat(eb, "mf8562", "HUniPRWAto", "HUniPRWAto", 0)
        util.initmat(eb, "mf8563", "HUniPRWIB", "HUniPRWIB", 0)
        util.initmat(eb, "mf8564", "HUniPRWIR", "HUniPRWIR", 0)
        util.initmat(eb, "mf8565", "HUniPRWIW", "HUniPRWIW", 0)
        util.initmat(eb, "mf8566", "HUniPRWWW", "HUniPRWWW", 0)
        util.initmat(eb, "mf8567", "HUniPRWAW", "HUniPRWAW", 0)
        util.initmat(eb, "mf8568", "HUniPRWBW", "HUniPRWBW", 0)
        util.initmat(eb, "mf8569", "HUniPRWFW", "HUniPRWFW", 0)
        util.initmat(eb, "mf8600", "HescAuTi", "HescAuTi", 0)
        util.initmat(eb, "mf8601", "HescAuDi", "HescAuDi", 0)
        util.initmat(eb, "mf8602", "HescAuTo", "HescAuTo", 0)
        util.initmat(eb, "mf8610", "HescBsIB", "HescBsIB", 0)
        util.initmat(eb, "mf8611", "HescBsWB", "HescBsWB", 0)
        util.initmat(eb, "mf8612", "HescBsAB", "HescBsAB", 0)
        util.initmat(eb, "mf8613", "HescBsBB", "HescBsBB", 0)
        util.initmat(eb, "mf8614", "HescBsFB", "HescBsFB", 0)
        util.initmat(eb, "mf8620", "HescRlIB", "HescRlIB", 0)
        util.initmat(eb, "mf8621", "HescRlIR", "HescRlIR", 0)
        util.initmat(eb, "mf8622", "HescRlWR", "HescRlWR", 0)
        util.initmat(eb, "mf8623", "HescRlAR", "HescRlAR", 0)
        util.initmat(eb, "mf8624", "HescRlBR", "HescRlBR", 0)
        util.initmat(eb, "mf8625", "HescRlFR", "HescRlFR", 0)
        util.initmat(eb, "mf8630", "HescWcIB", "HescWcIB", 0)
        util.initmat(eb, "mf8631", "HescWcIR", "HescWcIR", 0)
        util.initmat(eb, "mf8632", "HescWcIW", "HescWcIW", 0)
        util.initmat(eb, "mf8633", "HescWcWW", "HescWcWW", 0)
        util.initmat(eb, "mf8634", "HescWcAW", "HescWcAW", 0)
        util.initmat(eb, "mf8635", "HescWcBW", "HescWcBW", 0)
        util.initmat(eb, "mf8636", "HescWcFW", "HescWcFW", 0)
        util.initmat(eb, "mf8700", "HsoAuTi", "HsoAuTi", 0)
        util.initmat(eb, "mf8701", "HsoAuDi", "HsoAuDi", 0)
        util.initmat(eb, "mf8702", "HsoAuTo", "HsoAuTo", 0)
        util.initmat(eb, "mf8710", "HsoBsIB", "HsoBsIB", 0)
        util.initmat(eb, "mf8711", "HsoBsWB", "HsoBsWB", 0)
        util.initmat(eb, "mf8712", "HsoBsAB", "HsoBsAB", 0)
        util.initmat(eb, "mf8713", "HsoBsBB", "HsoBsBB", 0)
        util.initmat(eb, "mf8714", "HsoBsFB", "HsoBsFB", 0)
        util.initmat(eb, "mf8720", "HsoRlIB", "HsoRlIB", 0)
        util.initmat(eb, "mf8721", "HsoRlIR", "HsoRlIR", 0)
        util.initmat(eb, "mf8722", "HsoRlWR", "HsoRlWR", 0)
        util.initmat(eb, "mf8723", "HsoRlAR", "HsoRlAR", 0)
        util.initmat(eb, "mf8724", "HsoRlBR", "HsoRlBR", 0)
        util.initmat(eb, "mf8725", "HsoRlFR", "HsoRlFR", 0)
        util.initmat(eb, "mf8730", "HsoWcIB", "HsoWcIB", 0)
        util.initmat(eb, "mf8731", "HsoWcIR", "HsoWcIR", 0)
        util.initmat(eb, "mf8732", "HsoWcIW", "HsoWcIW", 0)
        util.initmat(eb, "mf8733", "HsoWcWW", "HsoWcWW", 0)
        util.initmat(eb, "mf8734", "HsoWcAW", "HsoWcAW", 0)
        util.initmat(eb, "mf8735", "HsoWcBW", "HsoWcBW", 0)
        util.initmat(eb, "mf8736", "HsoWcFW", "HsoWcFW", 0)
        util.initmat(eb, "mf8800", "NHOAuTi", "NHOAuTi", 0)
        util.initmat(eb, "mf8801", "NHOAuDi", "NHOAuDi", 0)
        util.initmat(eb, "mf8802", "NHOAuTo", "NHOAuTo", 0)
        util.initmat(eb, "mf8810", "NHOBsIB", "NHOBsIB", 0)
        util.initmat(eb, "mf8811", "NHOBsWB", "NHOBsWB", 0)
        util.initmat(eb, "mf8812", "NHOBsAB", "NHOBsAB", 0)
        util.initmat(eb, "mf8813", "NHOBsBB", "NHOBsBB", 0)
        util.initmat(eb, "mf8814", "NHOBsFB", "NHOBsFB", 0)
        util.initmat(eb, "mf8820", "NHORlIB", "NHORlIB", 0)
        util.initmat(eb, "mf8821", "NHORlIR", "NHORlIR", 0)
        util.initmat(eb, "mf8822", "NHORlWR", "NHORlWR", 0)
        util.initmat(eb, "mf8823", "NHORlAR", "NHORlAR", 0)
        util.initmat(eb, "mf8824", "NHORlBR", "NHORlBR", 0)
        util.initmat(eb, "mf8825", "NHORlFR", "NHORlFR", 0)
        util.initmat(eb, "mf8830", "NHOWcIB", "NHOWcIB", 0)
        util.initmat(eb, "mf8831", "NHOWcIR", "NHOWcIR", 0)
        util.initmat(eb, "mf8832", "NHOWcIW", "NHOWcIW", 0)
        util.initmat(eb, "mf8833", "NHOWcWW", "NHOWcWW", 0)
        util.initmat(eb, "mf8834", "NHOWcAW", "NHOWcAW", 0)
        util.initmat(eb, "mf8835", "NHOWcBW", "NHOWcBW", 0)
        util.initmat(eb, "mf8836", "NHOWcFW", "NHOWcFW", 0)

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