##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.emme.stage1.step1.segmentation
##--Purpose:
##---------------------------------------------------------------------
import inro.modeller as _m
import csv
import os
import numpy as np
import pandas as pd
import traceback as _traceback

class SocioEconomicSegmentation(_m.Tool()):
    ##Create global attributes (referring to dialogue boxes on the pages)

    ##Global attribute for Tool Run Message (successful/not successful)
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Socio-economic Segmentation"
        pb.description = "Runs the Household Worker-Income Segmentation Model"
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

    @_m.logbook_trace("01-01 - Socio Economic Segmentation")
    def __call__(self, eb):
        util = _m.Modeller().tool("translink.emme.util")
        input_path = util.get_input_path(eb)

        ##Batchin File
        self.Init_Matrices(eb)

        ##Generate Dataframe (Df for short hand) used for Worker-Income Segmentation
        df = self.Generate_Data_Frame(eb)

        ##Calculate Utilities, Probabilties and Worker-Income Segments for HH1
        self.Calc_Wrkr_Inc(df, eb)

    @_m.logbook_trace("Calculate_Worker-Income Segmentation")
    def Calc_Wrkr_Inc(self, df, eb):

        util = _m.Modeller().tool("translink.emme.util")
        input_path = util.get_input_path(eb)
        Tiny = 0.000001

        ##Variable Vectors
        ##Demographic Vectors

        Pop18_24_prp = df['Pop18_24_prp']
        PopSen_prp = df['PopSen_prp']
        PopChld_prp = df['PopChld_prp']
        LPopDen = df['LPopDen']
        LEmpDen = df['LEmpDen']

        ##Geographic Vectors
        One_Vector = df['One_Vector']
        DTESDum = df['DTESDum']
        UniDum = df['UniDum']
        NShoreDum = df['NShoreDum']
        NCBD = 1-df['CBDDum']

        ##Accessibility Vectors
        LDistCBD = df['LDistCBD']
        LDistTC = df['LDistTC']

        ##Interaction Vectors
        PopSen_prp_NShore = PopSen_prp*NShoreDum
        LPopDen_NCBD = LPopDen*NCBD
        LDistTC_NCBD = LDistTC*NCBD

        ##Coefficients:
        ##TODO: Figure out a more efficient way to transfer this from Mohammed's estimation files
        ##Bias Terms
        Bias_W0I1 =  0.0000
        Bias_W0I2 = -0.5543
        Bias_W0I3 = -2.1514
        Bias_W1I1 = 1.1678
        Bias_W1I2 = 1.9228
        Bias_W1I3 = 1.2631
        Bias_W2I1 = 3.0504
        Bias_W2I2 = 3.5171
        Bias_W2I3 = 3.9325
        Bias_W3I1 = 1.2604
        Bias_W3I2 = 2.1688
        Bias_W3I3 = 3.1593

        ##Demographic Terms
        Pop18_24_W0 = 3.8961
        Pop18_24_I1 = 3.1809
        Pop18_24_W23 = -3.9375
        HHSize_3p_W2 = 0.8681
        HHSize_4p_W3I23 = 0.6029
        HHSize_4p_W0 = -2.9334
        EmpDen_W1 = 0.0958
        EmpDen_W3 = -0.2320
        PopChld_W2I0 = -7.2687
        PopChld_W2I23 = -3.2566
        PopSen_W1 = -8.2181
        PopSen_W2 = -11.1883
        PopSen_W3 = -8.48692

        ##Geographic Terms
        DTES_I1 = 0.9349
        Uni_W01 = 1.8469
        NShore_I1 = -0.2379
        NShore_W3 = -0.6226

        ##Accessibility Terms
        LDistCBD_W1 = -0.0991

        ##Interaction Terms
        LDistTC_NCBD_W1 = -0.0574
        PopSen_Nshore_I3 = 3.1651
        LPopDen_NCBD_I3 = -0.0834
        LDistTC_NCBD_I3 = 0.1016

        ####################
          ##Zero Workers
        ####################

        ##Utility W0I1
        Coeff_Array = np.array(
                      [
                      Bias_W0I1,
                      Pop18_24_W0,
                      Pop18_24_I1,
                      DTES_I1,
                      Uni_W01,
                      NShore_I1
                      ])
        Var_Array =   np.column_stack((
                       One_Vector,
                       Pop18_24_prp,
                       Pop18_24_prp,
                       DTESDum,
                       UniDum,
                       NShoreDum
                       ))
        Util_W0I1 = np.dot(Var_Array, Coeff_Array)

        ##Utility W0I2
        Coeff_Array = np.array(
                       [
                       Bias_W0I2,
                       Pop18_24_W0,
                       Uni_W01
                       ])
        Var_Array =   np.column_stack((
                       One_Vector,
                       Pop18_24_prp,
                       UniDum
                       ))
        Util_W0I2 = np.dot(Var_Array, Coeff_Array)

        ##Utility W0I3
        Coeff_Array = np.array(
                       [
                       Bias_W0I3,
                       Pop18_24_W0,
                       PopSen_Nshore_I3,
                       Uni_W01,
                       LPopDen_NCBD_I3,
                       LDistTC_NCBD_I3
                       ])
        Var_Array =   np.column_stack((
                       One_Vector,
                       Pop18_24_prp,
                       PopSen_prp_NShore,
                       UniDum,
                       LPopDen_NCBD,
                       LDistTC_NCBD
                       ))
        Util_W0I3 = np.dot(Var_Array, Coeff_Array)

        ##Add Household terms to utilities
        Util_HH1W0I1 = Util_W0I1
        Util_HH1W0I2 = Util_W0I2
        Util_HH1W0I3 = Util_W0I3
        Util_HH2W0I1 = Util_W0I1
        Util_HH2W0I2 = Util_W0I2
        Util_HH2W0I3 = Util_W0I3
        Util_HH3W0I1 = Util_W0I1
        Util_HH3W0I2 = Util_W0I2
        Util_HH3W0I3 = Util_W0I3
        Util_HH4W0I1 = Util_W0I1 + HHSize_4p_W0
        Util_HH4W0I2 = Util_W0I2 + HHSize_4p_W0
        Util_HH4W0I3 = Util_W0I3 + HHSize_4p_W0


        df["Util_HH1W0I1"] = Util_HH1W0I1
        df["Util_HH1W0I2"] = Util_HH1W0I2
        df["Util_HH1W0I3"] = Util_HH1W0I3
        df["Util_HH2W0I1"] = Util_HH2W0I1
        df["Util_HH2W0I2"] = Util_HH2W0I2
        df["Util_HH2W0I3"] = Util_HH2W0I3
        df["Util_HH3W0I1"] = Util_HH3W0I1
        df["Util_HH3W0I2"] = Util_HH3W0I2
        df["Util_HH3W0I3"] = Util_HH3W0I3
        df["Util_HH4W0I1"] = Util_HH4W0I1
        df["Util_HH4W0I2"] = Util_HH4W0I2
        df["Util_HH4W0I3"] = Util_HH4W0I3       


        ####################
          ##One Worker
        ####################

        ##Utility W1I1
        Coeff_Array = np.array(
                      [
                      Bias_W1I1,
                      Pop18_24_I1,
                      LDistTC_NCBD_W1,
                      DTES_I1,
                      EmpDen_W1,
                      PopSen_W1,
                      LDistCBD_W1,
                      Uni_W01,
                      NShore_I1
                      ])
        Var_Array =   np.column_stack((
                       One_Vector,
                       Pop18_24_prp,
                       LDistTC_NCBD,
                       DTESDum,
                       LEmpDen,
                       PopSen_prp,
                       LDistCBD,
                       UniDum,
                       NShoreDum
                       ))
        Util_W1I1 = np.dot(Var_Array, Coeff_Array)

        ##Utility W1I2
        Coeff_Array = np.array(
                       [
                       Bias_W1I2,
                       LDistTC_NCBD_W1,
                       EmpDen_W1,
                       PopSen_W1,
                       LDistCBD_W1,
                       Uni_W01
                       ])
        Var_Array =   np.column_stack((
                       One_Vector,
                       LDistTC_NCBD,
                       LEmpDen,
                       PopSen_prp,
                       LDistCBD,
                       UniDum
                       ))
        Util_W1I2 = np.dot(Var_Array, Coeff_Array)

        ##Utility W1I3
        Coeff_Array = np.array(
                       [
                       Bias_W1I3,
                       LDistTC_NCBD_W1,
                       PopSen_Nshore_I3,
                       EmpDen_W1,
                       PopSen_W1,
                       LDistCBD_W1,
                       Uni_W01,
                       LPopDen_NCBD_I3,
                       LDistTC_NCBD_I3
                       ])

        Var_Array =   np.column_stack((
                       One_Vector,
                       LDistTC_NCBD,
                       PopSen_prp_NShore,
                       LEmpDen,
                       PopSen_prp,
                       LDistCBD,
                       UniDum,
                       LPopDen_NCBD,
                       LDistTC_NCBD
                       ))

        Util_W1I3 = np.dot(Var_Array, Coeff_Array)

        ##Add Household terms to utilities - none in the case of 1-per households
        Util_HH1W1I1 = Util_W1I1
        Util_HH1W1I2 = Util_W1I2
        Util_HH1W1I3 = Util_W1I3
        Util_HH2W1I1 = Util_W1I1
        Util_HH2W1I2 = Util_W1I2
        Util_HH2W1I3 = Util_W1I3
        Util_HH3W1I1 = Util_W1I1
        Util_HH3W1I2 = Util_W1I2
        Util_HH3W1I3 = Util_W1I3
        Util_HH4W1I1 = Util_W1I1
        Util_HH4W1I2 = Util_W1I2
        Util_HH4W1I3 = Util_W1I3

        df["Util_HH1W1I1"] = Util_HH1W1I1
        df["Util_HH1W1I2"] = Util_HH1W1I2
        df["Util_HH1W1I3"] = Util_HH1W1I3
        df["Util_HH2W1I1"] = Util_HH2W1I1
        df["Util_HH2W1I2"] = Util_HH2W1I2
        df["Util_HH2W1I3"] = Util_HH2W1I3
        df["Util_HH3W1I1"] = Util_HH3W1I1
        df["Util_HH3W1I2"] = Util_HH3W1I2
        df["Util_HH3W1I3"] = Util_HH3W1I3
        df["Util_HH4W1I1"] = Util_HH4W1I1
        df["Util_HH4W1I2"] = Util_HH4W1I2
        df["Util_HH4W1I3"] = Util_HH4W1I3        

        ####################
          ##Two Workers
        ####################

        ##Utility W2I1
        Coeff_Array = np.array(
                      [
                       Bias_W2I1,
                       Pop18_24_I1,
                       Pop18_24_W23,
                       DTES_I1,
                       PopChld_W2I0,
                       PopSen_W2,
                       NShore_I1
                      ])
        Var_Array =   np.column_stack((
                       One_Vector,
                       Pop18_24_prp,
                       Pop18_24_prp,
                       DTESDum,
                       PopChld_prp,
                       PopSen_prp,
                       NShoreDum
                       ))
        Util_W2I1 = np.dot(Var_Array, Coeff_Array)

        ##Utility W2I2
        Coeff_Array = np.array(
                      [
                       Bias_W2I2,
                       Pop18_24_W23,
                       PopChld_W2I23,
                       PopSen_W2
                       ])
        Var_Array =   np.column_stack((
                       One_Vector,
                       Pop18_24_prp,
                       PopChld_prp,
                       PopSen_prp
                       ))
        Util_W2I2 = np.dot(Var_Array, Coeff_Array)

        ##Utility W2I3
        Coeff_Array = np.array(
                       [
                       Bias_W2I3,
                       Pop18_24_W23,
                       PopSen_Nshore_I3,
                       PopChld_W2I23,
                       PopSen_W2,
                       LPopDen_NCBD_I3,
                       LDistTC_NCBD_I3
                       ])
        Var_Array =   np.column_stack((
                       One_Vector,
                       Pop18_24_prp,
                       PopSen_prp_NShore,
                       PopChld_prp,
                       PopSen_prp,
                       LPopDen_NCBD,
                       LDistTC_NCBD
                       ))
        Util_W2I3 = np.dot(Var_Array, Coeff_Array)

        ##Add Household terms to utilities
        Util_HH2W2I1 = Util_W2I1
        Util_HH2W2I2 = Util_W2I2
        Util_HH2W2I3 = Util_W2I3
        Util_HH3W2I1 = Util_W2I1 + HHSize_3p_W2
        Util_HH3W2I2 = Util_W2I2 + HHSize_3p_W2
        Util_HH3W2I3 = Util_W2I3 + HHSize_3p_W2
        Util_HH4W2I1 = Util_W2I1 + HHSize_3p_W2
        Util_HH4W2I2 = Util_W2I2 + HHSize_3p_W2
        Util_HH4W2I3 = Util_W2I3 + HHSize_3p_W2

        df["Util_HH2W2I1"] = Util_HH2W2I1
        df["Util_HH2W2I2"] = Util_HH2W2I2
        df["Util_HH2W2I3"] = Util_HH2W2I3
        df["Util_HH3W2I1"] = Util_HH3W2I1
        df["Util_HH3W2I2"] = Util_HH3W2I2
        df["Util_HH3W2I3"] = Util_HH3W2I3
        df["Util_HH4W2I1"] = Util_HH4W2I1
        df["Util_HH4W2I2"] = Util_HH4W2I2
        df["Util_HH4W2I3"] = Util_HH4W2I3         
        
        

        ####################
          ##Three Workers
        ####################

        ##Utility W3I1
        Coeff_Array = np.array(
                      [
                       Bias_W3I1,
                       Pop18_24_I1,
                       Pop18_24_W23,
                       DTES_I1,
                       EmpDen_W3,
                       PopSen_W3,
                       NShore_I1,
                       NShore_W3
                      ])
        Var_Array =   np.column_stack((
                       One_Vector,
                       Pop18_24_prp,
                       Pop18_24_prp,
                       DTESDum,
                       LEmpDen,
                       PopSen_prp,
                       NShoreDum,
                       NShoreDum
                       ))
        Util_W3I1 = np.dot(Var_Array, Coeff_Array)

        ##Utility W3I2
        Coeff_Array = np.array(
                       [
                       Bias_W3I2,
                       Pop18_24_W23,
                       EmpDen_W3,
                       PopSen_W3,
                       NShore_W3
                       ])
        Var_Array =   np.column_stack((
                       One_Vector,
                       Pop18_24_prp,
                       LEmpDen,
                       PopSen_prp,
                       NShoreDum
                       ))
        Util_W3I2 = np.dot(Var_Array, Coeff_Array)

        ##Utility W3I3
        Coeff_Array = np.array(
                       [
                       Bias_W3I3,
                       Pop18_24_W23,
                       PopSen_Nshore_I3,
                       EmpDen_W3,
                       PopSen_W3,
                       LPopDen_NCBD_I3,
                       LDistTC_NCBD_I3,
                       NShore_W3
                       ])
        Var_Array =   np.column_stack((
                       One_Vector,
                       Pop18_24_prp,
                       PopSen_prp_NShore,
                       LEmpDen,
                       PopSen_prp,
                       LPopDen_NCBD,
                       LDistTC_NCBD,
                       NShoreDum
                       ))
        Util_W3I3 = np.dot(Var_Array, Coeff_Array)

        ##Add Household terms to utilities
        Util_HH3W3I1 = Util_W3I1
        Util_HH3W3I2 = Util_W3I2
        Util_HH3W3I3 = Util_W3I3
        Util_HH4W3I1 = Util_W3I1
        Util_HH4W3I2 = Util_W3I2 + HHSize_4p_W3I23
        Util_HH4W3I3 = Util_W3I3 + HHSize_4p_W3I23
        
        df["Util_HH3W3I1"] = Util_HH3W3I1
        df["Util_HH3W3I2"] = Util_HH3W3I2
        df["Util_HH3W3I3"] = Util_HH3W3I3
        df["Util_HH4W3I1"] = Util_HH4W3I1
        df["Util_HH4W3I2"] = Util_HH4W3I2
        df["Util_HH4W3I3"] = Util_HH4W3I3 

        df.to_csv("C:/Users/adarwich/Desktop/dfout.csv")


        
        #######################################
          ##Calculate probabilities/Segments
        #######################################
        ## Pass Utilities as dictionary nests
        ## Dump segments back into EMME mo matrices
        Mat_Index = 120 # Location where matrix storage starts

        HH1 = eb.matrix("mo21").get_numpy_data()
        HH1_Dict = {
                    'Nest1' : [[Util_HH1W0I1, Util_HH1W0I2, Util_HH1W0I3],
                               [Mat_Index+0, Mat_Index+1, Mat_Index+2]],
                    'Nest2' : [[Util_HH1W1I1, Util_HH1W1I2, Util_HH1W1I3],
                               [Mat_Index+3, Mat_Index+4, Mat_Index+5]]
                   }
        HH1_Dict, counter = self.Calc_Prob_Segments(eb, HH1_Dict, HH1, Mat_Index)
        Mat_Index += counter

        HH2 = eb.matrix("mo22").get_numpy_data()
        HH2_Dict = {
                    'Nest1' : [[Util_HH2W0I1, Util_HH2W0I2, Util_HH2W0I3],
                               [Mat_Index+0, Mat_Index+1, Mat_Index+2]],
                    'Nest2' : [[Util_HH2W1I1, Util_HH2W1I2, Util_HH2W1I3],
                               [Mat_Index+3, Mat_Index+4, Mat_Index+5]],
                    'Nest3' : [[Util_HH2W2I1, Util_HH2W2I2, Util_HH2W2I3],
                               [Mat_Index+6, Mat_Index+7, Mat_Index+8]]
                   }
        HH2_Dict, counter = self.Calc_Prob_Segments(eb, HH2_Dict, HH2, Mat_Index)
        Mat_Index += counter

        HH3 = eb.matrix("mo23").get_numpy_data()
        HH3_Dict = {
                    'Nest1' : [[Util_HH3W0I1, Util_HH3W0I2, Util_HH3W0I3],
                               [Mat_Index+0, Mat_Index+1, Mat_Index+2]],
                    'Nest2' : [[Util_HH3W1I1, Util_HH3W1I2, Util_HH3W1I3],
                               [Mat_Index+3, Mat_Index+4, Mat_Index+5]],
                    'Nest3' : [[Util_HH3W2I1, Util_HH3W2I2, Util_HH3W2I3],
                               [Mat_Index+6, Mat_Index+7, Mat_Index+8]],
                    'Nest4' : [[Util_HH3W3I1, Util_HH3W3I2, Util_HH3W3I3],
                               [Mat_Index+9, Mat_Index+10, Mat_Index+11]],
                   }
        HH3_Dict, counter = self.Calc_Prob_Segments(eb, HH3_Dict, HH3, Mat_Index)
        Mat_Index += counter

        HH4 = eb.matrix("mo24").get_numpy_data()
        HH4_Dict = {
                    'Nest1' : [[Util_HH4W0I1, Util_HH4W0I2, Util_HH4W0I3],
                               [Mat_Index+0, Mat_Index+1, Mat_Index+2]],
                    'Nest2' : [[Util_HH4W1I1, Util_HH4W1I2, Util_HH4W1I3],
                               [Mat_Index+3, Mat_Index+4, Mat_Index+5]],
                    'Nest3' : [[Util_HH4W2I1, Util_HH4W2I2, Util_HH4W2I3],
                               [Mat_Index+6, Mat_Index+7, Mat_Index+8]],
                    'Nest4' : [[Util_HH4W3I1, Util_HH4W3I2, Util_HH4W3I3],
                               [Mat_Index+9, Mat_Index+10, Mat_Index+11]],
                   }
        HH4_Dict, counter = self.Calc_Prob_Segments(eb, HH4_Dict, HH4, Mat_Index)

    def Calc_Prob_Segments(self, eb, HH_Dict, HHSize, Mat_Index):

        Theta = 0.5637
        Tiny = 0.000001
        Low_Nest_Dict = {key:sum(np.exp(nest_len[0]))+Tiny
                            for key,nest_len in HH_Dict.items()}

        Up_Nest_Dict = {key:pow(sum(np.exp(nest_len[0]))+Tiny,Theta)
                            for key,nest_len in HH_Dict.items()}

        Full_Util = sum(Up_Nest_Dict.values())

        Seg_Dict = {key:np.exp(nest_len[0])/Low_Nest_Dict[key]*Up_Nest_Dict[key]/Full_Util
                            for key, nest_len in HH_Dict.items()}

        ## Dump data into mo matrices
        counter = 0
        for key in Seg_Dict:
            for nest_len in range (len(Seg_Dict[key])):
                eb.matrix("mo"+str(HH_Dict[key][1][nest_len])).set_numpy_data(Seg_Dict[key][nest_len])
                counter = counter + 1
        return (Seg_Dict, counter)

    def Generate_Data_Frame(self, eb):
        util = _m.Modeller().tool("translink.emme.util")
        input_path = util.get_input_path(eb)

        util.initmat(eb, "mo1600", "TempCalc1", "TempCalc1", 0)
        util.initmat(eb, "mo1601", "TempCalc2", "TempCalc2", 0)
        util.initmat(eb, "mo1602", "TempCalc3", "TempCalc3", 0)
        util.initmat(eb, "mo3000", "TempCalc4", "TempCalc3", 0)
        specs=[]

        ##Calculate Gy Each Zone Belongs to
        specs.append(util.matrix_spec("mo1600", "gy(p)"))

        ##Calculate ID of Zone Belongs to
        specs.append(util.matrix_spec("mo3000", "p"))

        ##Calculate Geographic Level Dummy Variables and Store in Temp Calcs
        ##University Zones: UBC+SFU
        Uni_spec = util.matrix_spec("mo1601", "1")
        Uni_spec["constraint"]["by_zone"] = {"origins": "21010-21030;21060;21070;21100;21120;21130;27170", "destinations": None}
        specs.append(Uni_spec)

        ##Downtown East Side Zones
        DTES_spec = util.matrix_spec("mo1602", "1")
        DTES_spec["constraint"]["by_zone"] = {"origins": "22480;22620;25020;25090-25130;25160-25230", "destinations": None}
        specs.append(DTES_spec)

        ###################################################
        ##THIS BLOCK IS TEMPORARY FOR CALCULATING DENSITIES
        ###################################################

        util.initmat(eb, "mo41", "PopDen", "Population Density", 0)
        util.initmat(eb, "mo42", "EmpDen", "Employment Density", 0)

        ##Population Density (per hectares)
        Pop_Den_spec = util.matrix_spec("mo41", "mo10/(mo40/10000.0)")
        Pop_Den_spec["constraint"]["by_zone"] = {"origins": "gm1-gm24", "destinations": None}
        specs.append(Pop_Den_spec)

        ##Population Density (per hectares)
        Emp_Den_spec = util.matrix_spec("mo42", "mo30/(mo40/10000.0)")
        Emp_Den_spec["constraint"]["by_zone"] = {"origins": "gm1-gm24", "destinations": None}
        specs.append(Emp_Den_spec)

        util.compute_matrix(specs)

        #################################################
        ##END OF DENSITY CALCULATION
        #################################################

        ##Generate Data Frame for Workers-Income Model Using Numpy+Pandas
        ZoneID = eb.matrix("mo3000").get_numpy_data()
        Gy = eb.matrix("mo1600").get_numpy_data()
        UniDum = eb.matrix("mo1601").get_numpy_data() #Uni Zone Dummy
        DTESDum = eb.matrix("mo1602").get_numpy_data() # DTES Dummy
        Pop18_24 = eb.matrix("mo4").get_numpy_data() # Population Age 18-24
        PopTot = eb.matrix("mo10").get_numpy_data() # Total Population
        PopSen = eb.matrix("mo7").get_numpy_data() # Senior Population (Age>65)
        PopDen = eb.matrix("mo41").get_numpy_data() # Population Density
        EmpDen = eb.matrix("mo42").get_numpy_data() # Employment Density
        Pop0_4 = eb.matrix("mo1").get_numpy_data() # Population Age 0-4
        Pop5_12 = eb.matrix("mo2").get_numpy_data() # Population Age 5-12
        Pop13_17 = eb.matrix("mo3").get_numpy_data() # Population Age 5-12
        EmpDen = eb.matrix("mo42").get_numpy_data() # Employment Density
        DistCBD = eb.matrix("mo45").get_numpy_data() # Distance to CBD
        DistTC =  eb.matrix("mo46").get_numpy_data() # Distance to Closest Town Centre

        ##Calculate Proportions
        Tiny = 0.000001
        Pop18_24_prp = Pop18_24/(PopTot + Tiny)
        PopSen_prp = PopSen/(PopTot + Tiny)
        PopChld_prp = (Pop0_4 + Pop5_12 + Pop13_17)/(PopTot + Tiny)

        LPopDen = np.log(PopDen + Tiny)
        LEmpDen = np.log(EmpDen + Tiny)
        LDistCBD = np.log(DistCBD + Tiny)
        LDistTC = np.log(DistTC + Tiny)

        NShoreDum = np.where(Gy<=2, 1, 0)
        CBDDum = np.where(Gy==3, 1, 0)

        Data_Dict = {
                    'ZoneID': ZoneID,
                    'Gy': Gy,
                    'NShoreDum': NShoreDum,
                    'CBDDum': CBDDum,
                    'UniDum': UniDum,
                    'DTESDum': DTESDum,
                    'PopChld_prp': PopChld_prp,
                    'Pop18_24_prp': Pop18_24_prp,
                    'PopSen_prp': PopSen_prp,
                    'PopTot': PopTot,
                    'LPopDen': LPopDen,
                    'LEmpDen': LEmpDen,
                    'LDistCBD': LDistCBD,
                    'LDistTC': LDistTC}

        ##Calculate Geographic Dummies


        df = pd.DataFrame(Data_Dict, columns= [
                                              'ZoneID',
                                              'Gy',
                                              'NShoreDum',
                                              'CBDDum',
                                              'UniDum',
                                              'DTESDum',
                                              'PopChld_prp',
                                              'Pop18_24_prp',
                                              'PopSen_prp',
                                              'PopTot',
                                              'LPopDen',
                                              'LEmpDen',
                                              'LDistCBD',
                                              'LDistTC'])
        df['One_Vector'] = 1
        return (df)

    @_m.logbook_trace("Init_Matrices")
    def Init_Matrices(self, eb):
        util = _m.Modeller().tool("translink.emme.util")
        ##HHxWorkers
        util.initmat(eb, "mo100", "H1W0", "Segment_H1W0", 0)
        util.initmat(eb, "mo101", "H1W1", "Segment_H1W1", 0)
        util.initmat(eb, "mo102", "H2W0", "Segment_H2W0", 0)
        util.initmat(eb, "mo103", "H2W1", "Segment_H2W1", 0)
        util.initmat(eb, "mo104", "H2W2", "Segment_H2W2", 0)
        util.initmat(eb, "mo105", "H3W0", "Segment_H3W0", 0)
        util.initmat(eb, "mo106", "H3W1", "Segment_H3W1", 0)
        util.initmat(eb, "mo107", "H3W2", "Segment_H3W2", 0)
        util.initmat(eb, "mo108", "H3W3", "Segment_H3W3", 0)
        util.initmat(eb, "mo109", "H4W0", "Segment_H4W0", 0)
        util.initmat(eb, "mo110", "H4W1", "Segment_H4W1", 0)
        util.initmat(eb, "mo111", "H4W2", "Segment_H4W2", 0)
        util.initmat(eb, "mo112", "H4W3", "Segment_H4W3", 0)
        ##HHxWorkersxIncome
        util.initmat(eb, "mo120", "H1W0I1", "Segment_H1W0I1", 0)
        util.initmat(eb, "mo121", "H1W0I2", "Segment_H1W0I2", 0)
        util.initmat(eb, "mo122", "H1W0I3", "Segment_H1W0I3", 0)
        util.initmat(eb, "mo123", "H1W1I1", "Segment_H1W1I1", 0)
        util.initmat(eb, "mo124", "H1W1I2", "Segment_H1W1I2", 0)
        util.initmat(eb, "mo125", "H1W1I3", "Segment_H1W1I3", 0)
        util.initmat(eb, "mo126", "H2W0I1", "Segment_H2W0I1", 0)
        util.initmat(eb, "mo127", "H2W0I2", "Segment_H2W0I2", 0)
        util.initmat(eb, "mo128", "H2W0I3", "Segment_H2W0I3", 0)
        util.initmat(eb, "mo129", "H2W1I1", "Segment_H2W1I1", 0)
        util.initmat(eb, "mo130", "H2W1I2", "Segment_H2W1I2", 0)
        util.initmat(eb, "mo131", "H2W1I3", "Segment_H2W1I3", 0)
        util.initmat(eb, "mo132", "H2W2I1", "Segment_H2W2I1", 0)
        util.initmat(eb, "mo133", "H2W2I2", "Segment_H2W2I2", 0)
        util.initmat(eb, "mo134", "H2W2I3", "Segment_H2W2I3", 0)
        util.initmat(eb, "mo135", "H3W0I1", "Segment_H3W0I1", 0)
        util.initmat(eb, "mo136", "H3W0I2", "Segment_H3W0I2", 0)
        util.initmat(eb, "mo137", "H3W0I3", "Segment_H3W0I3", 0)
        util.initmat(eb, "mo138", "H3W1I1", "Segment_H3W1I1", 0)
        util.initmat(eb, "mo139", "H3W1I2", "Segment_H3W1I2", 0)
        util.initmat(eb, "mo140", "H3W1I3", "Segment_H3W1I3", 0)
        util.initmat(eb, "mo141", "H3W2I1", "Segment_H3W2I1", 0)
        util.initmat(eb, "mo142", "H3W2I2", "Segment_H3W2I2", 0)
        util.initmat(eb, "mo143", "H3W2I3", "Segment_H3W2I3", 0)
        util.initmat(eb, "mo144", "H3W3I1", "Segment_H3W3I1", 0)
        util.initmat(eb, "mo145", "H3W3I2", "Segment_H3W3I2", 0)
        util.initmat(eb, "mo146", "H3W3I3", "Segment_H3W3I3", 0)
        util.initmat(eb, "mo147", "H4W0I1", "Segment_H4W0I1", 0)
        util.initmat(eb, "mo148", "H4W0I2", "Segment_H4W0I2", 0)
        util.initmat(eb, "mo149", "H4W0I3", "Segment_H4W0I3", 0)
        util.initmat(eb, "mo150", "H4W1I1", "Segment_H4W1I1", 0)
        util.initmat(eb, "mo151", "H4W1I2", "Segment_H4W1I2", 0)
        util.initmat(eb, "mo152", "H4W1I3", "Segment_H4W1I3", 0)
        util.initmat(eb, "mo153", "H4W2I1", "Segment_H4W2I1", 0)
        util.initmat(eb, "mo154", "H4W2I2", "Segment_H4W2I2", 0)
        util.initmat(eb, "mo155", "H4W2I3", "Segment_H4W2I3", 0)
        util.initmat(eb, "mo156", "H4W3I1", "Segment_H4W3I1", 0)
        util.initmat(eb, "mo157", "H4W3I2", "Segment_H4W3I2", 0)
        util.initmat(eb, "mo158", "H4W3I3", "Segment_H4W3I3", 0)
        ##HHxWorkersxIncomexAutos
        util.initmat(eb, "mo170", "H1W0I1A0", "Segment_H1W0I1A0", 0)
        util.initmat(eb, "mo171", "H1W0I1A1", "Segment_H1W0I1A1", 0)
        util.initmat(eb, "mo172", "H1W0I1A2", "Segment_H1W0I1A2", 0)
        util.initmat(eb, "mo173", "H1W0I1A3", "Segment_H1W0I1A3", 0)
        util.initmat(eb, "mo174", "H1W0I2A0", "Segment_H1W0I2A0", 0)
        util.initmat(eb, "mo175", "H1W0I2A1", "Segment_H1W0I2A1", 0)
        util.initmat(eb, "mo176", "H1W0I2A2", "Segment_H1W0I2A2", 0)
        util.initmat(eb, "mo177", "H1W0I2A3", "Segment_H1W0I2A3", 0)
        util.initmat(eb, "mo178", "H1W0I3A0", "Segment_H1W0I3A0", 0)
        util.initmat(eb, "mo179", "H1W0I3A1", "Segment_H1W0I3A1", 0)
        util.initmat(eb, "mo180", "H1W0I3A2", "Segment_H1W0I3A2", 0)
        util.initmat(eb, "mo181", "H1W0I3A3", "Segment_H1W0I3A3", 0)
        util.initmat(eb, "mo182", "H1W1I1A0", "Segment_H1W1I1A0", 0)
        util.initmat(eb, "mo183", "H1W1I1A1", "Segment_H1W1I1A1", 0)
        util.initmat(eb, "mo184", "H1W1I1A2", "Segment_H1W1I1A2", 0)
        util.initmat(eb, "mo185", "H1W1I1A3", "Segment_H1W1I1A3", 0)
        util.initmat(eb, "mo186", "H1W1I2A0", "Segment_H1W1I2A0", 0)
        util.initmat(eb, "mo187", "H1W1I2A1", "Segment_H1W1I2A1", 0)
        util.initmat(eb, "mo188", "H1W1I2A2", "Segment_H1W1I2A2", 0)
        util.initmat(eb, "mo189", "H1W1I2A3", "Segment_H1W1I2A3", 0)
        util.initmat(eb, "mo190", "H1W1I3A0", "Segment_H1W1I3A0", 0)
        util.initmat(eb, "mo191", "H1W1I3A1", "Segment_H1W1I3A1", 0)
        util.initmat(eb, "mo192", "H1W1I3A2", "Segment_H1W1I3A2", 0)
        util.initmat(eb, "mo193", "H1W1I3A3", "Segment_H1W1I3A3", 0)
        util.initmat(eb, "mo194", "H2W0I1A0", "Segment_H2W0I1A0", 0)
        util.initmat(eb, "mo195", "H2W0I1A1", "Segment_H2W0I1A1", 0)
        util.initmat(eb, "mo196", "H2W0I1A2", "Segment_H2W0I1A2", 0)
        util.initmat(eb, "mo197", "H2W0I1A3", "Segment_H2W0I1A3", 0)
        util.initmat(eb, "mo198", "H2W0I2A0", "Segment_H2W0I2A0", 0)
        util.initmat(eb, "mo199", "H2W0I2A1", "Segment_H2W0I2A1", 0)
        util.initmat(eb, "mo200", "H2W0I2A2", "Segment_H2W0I2A2", 0)
        util.initmat(eb, "mo201", "H2W0I2A3", "Segment_H2W0I2A3", 0)
        util.initmat(eb, "mo202", "H2W0I3A0", "Segment_H2W0I3A0", 0)
        util.initmat(eb, "mo203", "H2W0I3A1", "Segment_H2W0I3A1", 0)
        util.initmat(eb, "mo204", "H2W0I3A2", "Segment_H2W0I3A2", 0)
        util.initmat(eb, "mo205", "H2W0I3A3", "Segment_H2W0I3A3", 0)
        util.initmat(eb, "mo206", "H2W1I1A0", "Segment_H2W1I1A0", 0)
        util.initmat(eb, "mo207", "H2W1I1A1", "Segment_H2W1I1A1", 0)
        util.initmat(eb, "mo208", "H2W1I1A2", "Segment_H2W1I1A2", 0)
        util.initmat(eb, "mo209", "H2W1I1A3", "Segment_H2W1I1A3", 0)
        util.initmat(eb, "mo210", "H2W1I2A0", "Segment_H2W1I2A0", 0)
        util.initmat(eb, "mo211", "H2W1I2A1", "Segment_H2W1I2A1", 0)
        util.initmat(eb, "mo212", "H2W1I2A2", "Segment_H2W1I2A2", 0)
        util.initmat(eb, "mo213", "H2W1I2A3", "Segment_H2W1I2A3", 0)
        util.initmat(eb, "mo214", "H2W1I3A0", "Segment_H2W1I3A0", 0)
        util.initmat(eb, "mo215", "H2W1I3A1", "Segment_H2W1I3A1", 0)
        util.initmat(eb, "mo216", "H2W1I3A2", "Segment_H2W1I3A2", 0)
        util.initmat(eb, "mo217", "H2W1I3A3", "Segment_H2W1I3A3", 0)
        util.initmat(eb, "mo218", "H2W2I1A0", "Segment_H2W2I1A0", 0)
        util.initmat(eb, "mo219", "H2W2I1A1", "Segment_H2W2I1A1", 0)
        util.initmat(eb, "mo220", "H2W2I1A2", "Segment_H2W2I1A2", 0)
        util.initmat(eb, "mo221", "H2W2I1A3", "Segment_H2W2I1A3", 0)
        util.initmat(eb, "mo222", "H2W2I2A0", "Segment_H2W2I2A0", 0)
        util.initmat(eb, "mo223", "H2W2I2A1", "Segment_H2W2I2A1", 0)
        util.initmat(eb, "mo224", "H2W2I2A2", "Segment_H2W2I2A2", 0)
        util.initmat(eb, "mo225", "H2W2I2A3", "Segment_H2W2I2A3", 0)
        util.initmat(eb, "mo226", "H2W2I3A0", "Segment_H2W2I3A0", 0)
        util.initmat(eb, "mo227", "H2W2I3A1", "Segment_H2W2I3A1", 0)
        util.initmat(eb, "mo228", "H2W2I3A2", "Segment_H2W2I3A2", 0)
        util.initmat(eb, "mo229", "H2W2I3A3", "Segment_H2W2I3A3", 0)
        util.initmat(eb, "mo230", "H3W0I1A0", "Segment_H3W0I1A0", 0)
        util.initmat(eb, "mo231", "H3W0I1A1", "Segment_H3W0I1A1", 0)
        util.initmat(eb, "mo232", "H3W0I1A2", "Segment_H3W0I1A2", 0)
        util.initmat(eb, "mo233", "H3W0I1A3", "Segment_H3W0I1A3", 0)
        util.initmat(eb, "mo234", "H3W0I2A0", "Segment_H3W0I2A0", 0)
        util.initmat(eb, "mo235", "H3W0I2A1", "Segment_H3W0I2A1", 0)
        util.initmat(eb, "mo236", "H3W0I2A2", "Segment_H3W0I2A2", 0)
        util.initmat(eb, "mo237", "H3W0I2A3", "Segment_H3W0I2A3", 0)
        util.initmat(eb, "mo238", "H3W0I3A0", "Segment_H3W0I3A0", 0)
        util.initmat(eb, "mo239", "H3W0I3A1", "Segment_H3W0I3A1", 0)
        util.initmat(eb, "mo240", "H3W0I3A2", "Segment_H3W0I3A2", 0)
        util.initmat(eb, "mo241", "H3W0I3A3", "Segment_H3W0I3A3", 0)
        util.initmat(eb, "mo242", "H3W1I1A0", "Segment_H3W1I1A0", 0)
        util.initmat(eb, "mo243", "H3W1I1A1", "Segment_H3W1I1A1", 0)
        util.initmat(eb, "mo244", "H3W1I1A2", "Segment_H3W1I1A2", 0)
        util.initmat(eb, "mo245", "H3W1I1A3", "Segment_H3W1I1A3", 0)
        util.initmat(eb, "mo246", "H3W1I2A0", "Segment_H3W1I2A0", 0)
        util.initmat(eb, "mo247", "H3W1I2A1", "Segment_H3W1I2A1", 0)
        util.initmat(eb, "mo248", "H3W1I2A2", "Segment_H3W1I2A2", 0)
        util.initmat(eb, "mo249", "H3W1I2A3", "Segment_H3W1I2A3", 0)
        util.initmat(eb, "mo250", "H3W1I3A0", "Segment_H3W1I3A0", 0)
        util.initmat(eb, "mo251", "H3W1I3A1", "Segment_H3W1I3A1", 0)
        util.initmat(eb, "mo252", "H3W1I3A2", "Segment_H3W1I3A2", 0)
        util.initmat(eb, "mo253", "H3W1I3A3", "Segment_H3W1I3A3", 0)
        util.initmat(eb, "mo254", "H3W2I1A0", "Segment_H3W2I1A0", 0)
        util.initmat(eb, "mo255", "H3W2I1A1", "Segment_H3W2I1A1", 0)
        util.initmat(eb, "mo256", "H3W2I1A2", "Segment_H3W2I1A2", 0)
        util.initmat(eb, "mo257", "H3W2I1A3", "Segment_H3W2I1A3", 0)
        util.initmat(eb, "mo258", "H3W2I2A0", "Segment_H3W2I2A0", 0)
        util.initmat(eb, "mo259", "H3W2I2A1", "Segment_H3W2I2A1", 0)
        util.initmat(eb, "mo260", "H3W2I2A2", "Segment_H3W2I2A2", 0)
        util.initmat(eb, "mo261", "H3W2I2A3", "Segment_H3W2I2A3", 0)
        util.initmat(eb, "mo262", "H3W2I3A0", "Segment_H3W2I3A0", 0)
        util.initmat(eb, "mo263", "H3W2I3A1", "Segment_H3W2I3A1", 0)
        util.initmat(eb, "mo264", "H3W2I3A2", "Segment_H3W2I3A2", 0)
        util.initmat(eb, "mo265", "H3W2I3A3", "Segment_H3W2I3A3", 0)
        util.initmat(eb, "mo266", "H3W3I1A0", "Segment_H3W3I1A0", 0)
        util.initmat(eb, "mo267", "H3W3I1A1", "Segment_H3W3I1A1", 0)
        util.initmat(eb, "mo268", "H3W3I1A2", "Segment_H3W3I1A2", 0)
        util.initmat(eb, "mo269", "H3W3I1A3", "Segment_H3W3I1A3", 0)
        util.initmat(eb, "mo270", "H3W3I2A0", "Segment_H3W3I2A0", 0)
        util.initmat(eb, "mo271", "H3W3I2A1", "Segment_H3W3I2A1", 0)
        util.initmat(eb, "mo272", "H3W3I2A2", "Segment_H3W3I2A2", 0)
        util.initmat(eb, "mo273", "H3W3I2A3", "Segment_H3W3I2A3", 0)
        util.initmat(eb, "mo274", "H3W3I3A0", "Segment_H3W3I3A0", 0)
        util.initmat(eb, "mo275", "H3W3I3A1", "Segment_H3W3I3A1", 0)
        util.initmat(eb, "mo276", "H3W3I3A2", "Segment_H3W3I3A2", 0)
        util.initmat(eb, "mo277", "H3W3I3A3", "Segment_H3W3I3A3", 0)
        util.initmat(eb, "mo278", "H4W0I1A0", "Segment_H4W0I1A0", 0)
        util.initmat(eb, "mo279", "H4W0I1A1", "Segment_H4W0I1A1", 0)
        util.initmat(eb, "mo280", "H4W0I1A2", "Segment_H4W0I1A2", 0)
        util.initmat(eb, "mo281", "H4W0I1A3", "Segment_H4W0I1A3", 0)
        util.initmat(eb, "mo282", "H4W0I2A0", "Segment_H4W0I2A0", 0)
        util.initmat(eb, "mo283", "H4W0I2A1", "Segment_H4W0I2A1", 0)
        util.initmat(eb, "mo284", "H4W0I2A2", "Segment_H4W0I2A2", 0)
        util.initmat(eb, "mo285", "H4W0I2A3", "Segment_H4W0I2A3", 0)
        util.initmat(eb, "mo286", "H4W0I3A0", "Segment_H4W0I3A0", 0)
        util.initmat(eb, "mo287", "H4W0I3A1", "Segment_H4W0I3A1", 0)
        util.initmat(eb, "mo288", "H4W0I3A2", "Segment_H4W0I3A2", 0)
        util.initmat(eb, "mo289", "H4W0I3A3", "Segment_H4W0I3A3", 0)
        util.initmat(eb, "mo290", "H4W1I1A0", "Segment_H4W1I1A0", 0)
        util.initmat(eb, "mo291", "H4W1I1A1", "Segment_H4W1I1A1", 0)
        util.initmat(eb, "mo292", "H4W1I1A2", "Segment_H4W1I1A2", 0)
        util.initmat(eb, "mo293", "H4W1I1A3", "Segment_H4W1I1A3", 0)
        util.initmat(eb, "mo294", "H4W1I2A0", "Segment_H4W1I2A0", 0)
        util.initmat(eb, "mo295", "H4W1I2A1", "Segment_H4W1I2A1", 0)
        util.initmat(eb, "mo296", "H4W1I2A2", "Segment_H4W1I2A2", 0)
        util.initmat(eb, "mo297", "H4W1I2A3", "Segment_H4W1I2A3", 0)
        util.initmat(eb, "mo298", "H4W1I3A0", "Segment_H4W1I3A0", 0)
        util.initmat(eb, "mo299", "H4W1I3A1", "Segment_H4W1I3A1", 0)
        util.initmat(eb, "mo300", "H4W1I3A2", "Segment_H4W1I3A2", 0)
        util.initmat(eb, "mo301", "H4W1I3A3", "Segment_H4W1I3A3", 0)
        util.initmat(eb, "mo302", "H4W2I1A0", "Segment_H4W2I1A0", 0)
        util.initmat(eb, "mo303", "H4W2I1A1", "Segment_H4W2I1A1", 0)
        util.initmat(eb, "mo304", "H4W2I1A2", "Segment_H4W2I1A2", 0)
        util.initmat(eb, "mo305", "H4W2I1A3", "Segment_H4W2I1A3", 0)
        util.initmat(eb, "mo306", "H4W2I2A0", "Segment_H4W2I2A0", 0)
        util.initmat(eb, "mo307", "H4W2I2A1", "Segment_H4W2I2A1", 0)
        util.initmat(eb, "mo308", "H4W2I2A2", "Segment_H4W2I2A2", 0)
        util.initmat(eb, "mo309", "H4W2I2A3", "Segment_H4W2I2A3", 0)
        util.initmat(eb, "mo310", "H4W2I3A0", "Segment_H4W2I3A0", 0)
        util.initmat(eb, "mo311", "H4W2I3A1", "Segment_H4W2I3A1", 0)
        util.initmat(eb, "mo312", "H4W2I3A2", "Segment_H4W2I3A2", 0)
        util.initmat(eb, "mo313", "H4W2I3A3", "Segment_H4W2I3A3", 0)
        util.initmat(eb, "mo314", "H4W3I1A0", "Segment_H4W3I1A0", 0)
        util.initmat(eb, "mo315", "H4W3I1A1", "Segment_H4W3I1A1", 0)
        util.initmat(eb, "mo316", "H4W3I1A2", "Segment_H4W3I1A2", 0)
        util.initmat(eb, "mo317", "H4W3I1A3", "Segment_H4W3I1A3", 0)
        util.initmat(eb, "mo318", "H4W3I2A0", "Segment_H4W3I2A0", 0)
        util.initmat(eb, "mo319", "H4W3I2A1", "Segment_H4W3I2A1", 0)
        util.initmat(eb, "mo320", "H4W3I2A2", "Segment_H4W3I2A2", 0)
        util.initmat(eb, "mo321", "H4W3I2A3", "Segment_H4W3I2A3", 0)
        util.initmat(eb, "mo322", "H4W3I3A0", "Segment_H4W3I3A0", 0)
        util.initmat(eb, "mo323", "H4W3I3A1", "Segment_H4W3I3A1", 0)
        util.initmat(eb, "mo324", "H4W3I3A2", "Segment_H4W3I3A2", 0)
        util.initmat(eb, "mo325", "H4W3I3A3", "Segment_H4W3I3A3", 0)
        ##HHxIncomexAutos
        util.initmat(eb, "mo400", "H1I1A0", "Segment_H1I1A0", 0)
        util.initmat(eb, "mo401", "H1I1A1", "Segment_H1I1A1", 0)
        util.initmat(eb, "mo402", "H1I1A2", "Segment_H1I1A2", 0)
        util.initmat(eb, "mo403", "H1I1A3", "Segment_H1I1A3", 0)
        util.initmat(eb, "mo404", "H1I2A0", "Segment_H1I2A0", 0)
        util.initmat(eb, "mo405", "H1I2A1", "Segment_H1I2A1", 0)
        util.initmat(eb, "mo406", "H1I2A2", "Segment_H1I2A2", 0)
        util.initmat(eb, "mo407", "H1I2A3", "Segment_H1I2A3", 0)
        util.initmat(eb, "mo408", "H1I3A0", "Segment_H1I3A0", 0)
        util.initmat(eb, "mo409", "H1I3A1", "Segment_H1I3A1", 0)
        util.initmat(eb, "mo410", "H1I3A2", "Segment_H1I3A2", 0)
        util.initmat(eb, "mo411", "H1I3A3", "Segment_H1I3A3", 0)
        util.initmat(eb, "mo412", "H2I1A0", "Segment_H2I1A0", 0)
        util.initmat(eb, "mo413", "H2I1A1", "Segment_H2I1A1", 0)
        util.initmat(eb, "mo414", "H2I1A2", "Segment_H2I1A2", 0)
        util.initmat(eb, "mo415", "H2I1A3", "Segment_H2I1A3", 0)
        util.initmat(eb, "mo416", "H2I2A0", "Segment_H2I2A0", 0)
        util.initmat(eb, "mo417", "H2I2A1", "Segment_H2I2A1", 0)
        util.initmat(eb, "mo418", "H2I2A2", "Segment_H2I2A2", 0)
        util.initmat(eb, "mo419", "H2I2A3", "Segment_H2I2A3", 0)
        util.initmat(eb, "mo420", "H2I3A0", "Segment_H2I3A0", 0)
        util.initmat(eb, "mo421", "H2I3A1", "Segment_H2I3A1", 0)
        util.initmat(eb, "mo422", "H2I3A2", "Segment_H2I3A2", 0)
        util.initmat(eb, "mo423", "H2I3A3", "Segment_H2I3A3", 0)
        util.initmat(eb, "mo424", "H3I1A0", "Segment_H3I1A0", 0)
        util.initmat(eb, "mo425", "H3I1A1", "Segment_H3I1A1", 0)
        util.initmat(eb, "mo426", "H3I1A2", "Segment_H3I1A2", 0)
        util.initmat(eb, "mo427", "H3I1A3", "Segment_H3I1A3", 0)
        util.initmat(eb, "mo428", "H3I2A0", "Segment_H3I2A0", 0)
        util.initmat(eb, "mo429", "H3I2A1", "Segment_H3I2A1", 0)
        util.initmat(eb, "mo430", "H3I2A2", "Segment_H3I2A2", 0)
        util.initmat(eb, "mo431", "H3I2A3", "Segment_H3I2A3", 0)
        util.initmat(eb, "mo432", "H3I3A0", "Segment_H3I3A0", 0)
        util.initmat(eb, "mo433", "H3I3A1", "Segment_H3I3A1", 0)
        util.initmat(eb, "mo434", "H3I3A2", "Segment_H3I3A2", 0)
        util.initmat(eb, "mo435", "H3I3A3", "Segment_H3I3A3", 0)
        util.initmat(eb, "mo436", "H4I1A0", "Segment_H4I1A0", 0)
        util.initmat(eb, "mo437", "H4I1A1", "Segment_H4I1A1", 0)
        util.initmat(eb, "mo438", "H4I1A2", "Segment_H4I1A2", 0)
        util.initmat(eb, "mo439", "H4I1A3", "Segment_H4I1A3", 0)
        util.initmat(eb, "mo440", "H4I2A0", "Segment_H4I2A0", 0)
        util.initmat(eb, "mo441", "H4I2A1", "Segment_H4I2A1", 0)
        util.initmat(eb, "mo442", "H4I2A2", "Segment_H4I2A2", 0)
        util.initmat(eb, "mo443", "H4I2A3", "Segment_H4I2A3", 0)
        util.initmat(eb, "mo444", "H4I3A0", "Segment_H4I3A0", 0)
        util.initmat(eb, "mo445", "H4I3A1", "Segment_H4I3A1", 0)
        util.initmat(eb, "mo446", "H4I3A2", "Segment_H4I3A2", 0)
        util.initmat(eb, "mo447", "H4I3A3", "Segment_H4I3A3", 0)
        ##WorkersxIncomexAutos
        util.initmat(eb, "mo450", "W0I1A0", "Segment_W0I1A0", 0)
        util.initmat(eb, "mo451", "W0I1A1", "Segment_W0I1A1", 0)
        util.initmat(eb, "mo452", "W0I1A2", "Segment_W0I1A2", 0)
        util.initmat(eb, "mo453", "W0I1A3", "Segment_W0I1A3", 0)
        util.initmat(eb, "mo454", "W0I2A0", "Segment_W0I2A0", 0)
        util.initmat(eb, "mo455", "W0I2A1", "Segment_W0I2A1", 0)
        util.initmat(eb, "mo456", "W0I2A2", "Segment_W0I2A2", 0)
        util.initmat(eb, "mo457", "W0I2A3", "Segment_W0I2A3", 0)
        util.initmat(eb, "mo458", "W0I3A0", "Segment_W0I3A0", 0)
        util.initmat(eb, "mo459", "W0I3A1", "Segment_W0I3A1", 0)
        util.initmat(eb, "mo460", "W0I3A2", "Segment_W0I3A2", 0)
        util.initmat(eb, "mo461", "W0I3A3", "Segment_W0I3A3", 0)
        util.initmat(eb, "mo462", "W1I1A0", "Segment_W1I1A0", 0)
        util.initmat(eb, "mo463", "W1I1A1", "Segment_W1I1A1", 0)
        util.initmat(eb, "mo464", "W1I1A2", "Segment_W1I1A2", 0)
        util.initmat(eb, "mo465", "W1I1A3", "Segment_W1I1A3", 0)
        util.initmat(eb, "mo466", "W1I2A0", "Segment_W1I2A0", 0)
        util.initmat(eb, "mo467", "W1I2A1", "Segment_W1I2A1", 0)
        util.initmat(eb, "mo468", "W1I2A2", "Segment_W1I2A2", 0)
        util.initmat(eb, "mo469", "W1I2A3", "Segment_W1I2A3", 0)
        util.initmat(eb, "mo470", "W1I3A0", "Segment_W1I3A0", 0)
        util.initmat(eb, "mo471", "W1I3A1", "Segment_W1I3A1", 0)
        util.initmat(eb, "mo472", "W1I3A2", "Segment_W1I3A2", 0)
        util.initmat(eb, "mo473", "W1I3A3", "Segment_W1I3A3", 0)
        util.initmat(eb, "mo474", "W2I1A0", "Segment_W2I1A0", 0)
        util.initmat(eb, "mo475", "W2I1A1", "Segment_W2I1A1", 0)
        util.initmat(eb, "mo476", "W2I1A2", "Segment_W2I1A2", 0)
        util.initmat(eb, "mo477", "W2I1A3", "Segment_W2I1A3", 0)
        util.initmat(eb, "mo478", "W2I2A0", "Segment_W2I2A0", 0)
        util.initmat(eb, "mo479", "W2I2A1", "Segment_W2I2A1", 0)
        util.initmat(eb, "mo480", "W2I2A2", "Segment_W2I2A2", 0)
        util.initmat(eb, "mo481", "W2I2A3", "Segment_W2I2A3", 0)
        util.initmat(eb, "mo482", "W2I3A0", "Segment_W2I3A0", 0)
        util.initmat(eb, "mo483", "W2I3A1", "Segment_W2I3A1", 0)
        util.initmat(eb, "mo484", "W2I3A2", "Segment_W2I3A2", 0)
        util.initmat(eb, "mo485", "W2I3A3", "Segment_W2I3A3", 0)
        util.initmat(eb, "mo486", "W3I1A0", "Segment_W3I1A0", 0)
        util.initmat(eb, "mo487", "W3I1A1", "Segment_W3I1A1", 0)
        util.initmat(eb, "mo488", "W3I1A2", "Segment_W3I1A2", 0)
        util.initmat(eb, "mo489", "W3I1A3", "Segment_W3I1A3", 0)
        util.initmat(eb, "mo490", "W3I2A0", "Segment_W3I2A0", 0)
        util.initmat(eb, "mo491", "W3I2A1", "Segment_W3I2A1", 0)
        util.initmat(eb, "mo492", "W3I2A2", "Segment_W3I2A2", 0)
        util.initmat(eb, "mo493", "W3I2A3", "Segment_W3I2A3", 0)
        util.initmat(eb, "mo494", "W3I3A0", "Segment_W3I3A0", 0)
        util.initmat(eb, "mo495", "W3I3A1", "Segment_W3I3A1", 0)
        util.initmat(eb, "mo496", "W3I3A2", "Segment_W3I3A2", 0)
        util.initmat(eb, "mo497", "W3I3A3", "Segment_W3I3A3", 0)
        ##HHxIncome
        util.initmat(eb, "mo500", "H1I1", "Segment_H1I1", 0)
        util.initmat(eb, "mo501", "H1I2", "Segment_H1I2", 0)
        util.initmat(eb, "mo502", "H1I3", "Segment_H1I3", 0)
        util.initmat(eb, "mo503", "H2I1", "Segment_H2I1", 0)
        util.initmat(eb, "mo504", "H2I2", "Segment_H2I2", 0)
        util.initmat(eb, "mo505", "H2I3", "Segment_H2I3", 0)
        util.initmat(eb, "mo506", "H3I1", "Segment_H3I1", 0)
        util.initmat(eb, "mo507", "H3I2", "Segment_H3I2", 0)
        util.initmat(eb, "mo508", "H3I3", "Segment_H3I3", 0)
        util.initmat(eb, "mo509", "H4I1", "Segment_H4I1", 0)
        util.initmat(eb, "mo510", "H4I2", "Segment_H4I2", 0)
        util.initmat(eb, "mo511", "H4I3", "Segment_H4I3", 0)
        ##WorkersxIncome
        util.initmat(eb, "mo520", "W0I1", "Segment_W0I1", 0)
        util.initmat(eb, "mo521", "W0I2", "Segment_W0I2", 0)
        util.initmat(eb, "mo522", "W0I3", "Segment_W0I3", 0)
        util.initmat(eb, "mo523", "W1I1", "Segment_W1I1", 0)
        util.initmat(eb, "mo524", "W1I2", "Segment_W1I2", 0)
        util.initmat(eb, "mo525", "W1I3", "Segment_W1I3", 0)
        util.initmat(eb, "mo526", "W2I1", "Segment_W2I1", 0)
        util.initmat(eb, "mo527", "W2I2", "Segment_W2I2", 0)
        util.initmat(eb, "mo528", "W2I3", "Segment_W2I3", 0)
        util.initmat(eb, "mo529", "W3I1", "Segment_W3I1", 0)
        util.initmat(eb, "mo530", "W3I2", "Segment_W3I2", 0)
        util.initmat(eb, "mo531", "W3I3", "Segment_W3I3", 0)
        ##Employed Labour Force
        ###TODO Add Year to Matrix Name
        util.initmat(eb, "mo540", "ELF", "Employed Labour Force", 0)
        ##Household distribution by number of workers
        util.initmat(eb, "mo541", "W0_HHs", "0-worker households", 0)
        util.initmat(eb, "mo542", "W1_HHs", "1-worker households", 0)
        util.initmat(eb, "mo543", "W2_HHs", "2-worker households", 0)
        util.initmat(eb, "mo544", "W3_HHs", "3-worker households", 0)
        ##Woker Distribution by Income
        util.initmat(eb, "mo546", "I1_Wrks", "Total Low Income Workers", 0)
        util.initmat(eb, "mo547", "I2_Wrks", "Total Med Income Workers", 0)
        util.initmat(eb, "mo548", "I3_Wrks", "Total High Income Workers", 0)
        ## Total Vehicle Availability
        ###TODO Add Year to Matrix Name
        util.initmat(eb, "mo550", "Autos", "Total Autos Available", 0)
        ##Household distribution by number of Autos
        util.initmat(eb, "mo551", "A0_HHs", "0-vehicle households", 0)
        util.initmat(eb, "mo552", "A1_HHs", "1-vehicle households", 0)
        util.initmat(eb, "mo553", "A2_HHs", "2-vehicle households", 0)
        util.initmat(eb, "mo554", "A3_HHs", "3-vehicle households", 0)