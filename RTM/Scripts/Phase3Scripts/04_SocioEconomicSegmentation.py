##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage1.workinc
##--Purpose:
##---------------------------------------------------------------------
import inro.modeller as _m
import re
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

    @_m.logbook_trace("Socio Economic Segmentation")
    def __call__(self, eb):
        util = _m.Modeller().tool("translink.util")

        ##Generate Dataframe (Df for short hand) used for Worker-Income Segmentation
        df = self.Generate_Data_Frame(eb)

        ##Calculate Utilities, Probabilties and Worker-Income Segments for HH1
        self.Calc_Wrkr_Inc(df, eb)

    @_m.logbook_trace("Calculate_Worker-Income Segmentation")
    def Calc_Wrkr_Inc(self, df, eb):

        util = _m.Modeller().tool("translink.util")
        Tiny = 0.000001

        ##Variable Vectors
        ##Demographic Vectors

        Pop18_24_prp = df['Pop18_24_prp'] # Pop18_24/(PopTot + Tiny)
        PopSen_prp = df['PopSen_prp'] #  PopSen/(PopTot + Tiny)
        PopChld_prp = df['PopChld_prp'] # (Pop0_4 + Pop5_12 + Pop13_17)/(PopTot + Tiny)
        LPopDen = df['LPopDen']
        LEmpDen = df['LEmpDen']

        ##Geographic Vectors
        One_Vector = df['One_Vector']
        DTESDum = df['DTESDum']
        UniDum = df['UniDum']
        NShoreDum = df['NShoreDum']
        NCBD = df['NCBD']

        ##Accessibility Vectors
        LDistCBD = df['LDistCBD']
        LDistTC = df['LDistTC']

        ##Interaction Vectors
        PopSen_prp_NShore = PopSen_prp*NShoreDum
        LPopDen_NCBD = LPopDen*NCBD
        LDistTC_NCBD = LDistTC*NCBD

        ##Coefficients:
        ##Bias Terms
        Bias_W0I1 = eb.matrix("msBias_W0I1").data
        Bias_W0I2 = eb.matrix("msBias_W0I2").data
        Bias_W0I3 = eb.matrix("msBias_W0I3").data
        Bias_W1I1 = eb.matrix("msBias_W1I1").data
        Bias_W1I2 = eb.matrix("msBias_W1I2").data
        Bias_W1I3 = eb.matrix("msBias_W1I3").data
        Bias_W2I1 = eb.matrix("msBias_W2I1").data
        Bias_W2I2 = eb.matrix("msBias_W2I2").data
        Bias_W2I3 = eb.matrix("msBias_W2I3").data
        Bias_W3I1 = eb.matrix("msBias_W3I1").data
        Bias_W3I2 = eb.matrix("msBias_W3I2").data
        Bias_W3I3 = eb.matrix("msBias_W3I3").data

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



        #######################################
          ##Calculate probabilities/Segments
        #######################################
        ## Pass Utilities as dictionary nests
        ## Dump segments back into EMME mo matrices
        Mat_Index = 1020 # Location where matrix storage starts


        HH1 = eb.matrix("moHh1p").get_numpy_data()
        HH1_Dict = {
                    'HH1W0' : [[Util_HH1W0I1, Util_HH1W0I2, Util_HH1W0I3],
                               [Mat_Index+0, Mat_Index+1, Mat_Index+2]],
                    'HH1W1' : [[Util_HH1W1I1, Util_HH1W1I2, Util_HH1W1I3],
                               [Mat_Index+3, Mat_Index+4, Mat_Index+5]]
                   }
        HH1_Dict, counter = self.Calc_Prob_Segments(eb, HH1_Dict, HH1, Mat_Index)
        Mat_Index += counter

        HH2 = eb.matrix("moHh2p").get_numpy_data()
        HH2_Dict = {
                    'HH2W0' : [[Util_HH2W0I1, Util_HH2W0I2, Util_HH2W0I3],
                               [Mat_Index+0, Mat_Index+1, Mat_Index+2]],
                    'HH2W1' : [[Util_HH2W1I1, Util_HH2W1I2, Util_HH2W1I3],
                               [Mat_Index+3, Mat_Index+4, Mat_Index+5]],
                    'HH2W2' : [[Util_HH2W2I1, Util_HH2W2I2, Util_HH2W2I3],
                               [Mat_Index+6, Mat_Index+7, Mat_Index+8]]
                   }
        HH2_Dict, counter = self.Calc_Prob_Segments(eb, HH2_Dict, HH2, Mat_Index)
        Mat_Index += counter

        HH3 = eb.matrix("moHh3p").get_numpy_data()
        HH3_Dict = {
                    'HH3W0' : [[Util_HH3W0I1, Util_HH3W0I2, Util_HH3W0I3],
                               [Mat_Index+0, Mat_Index+1, Mat_Index+2]],
                    'HH3W1' : [[Util_HH3W1I1, Util_HH3W1I2, Util_HH3W1I3],
                               [Mat_Index+3, Mat_Index+4, Mat_Index+5]],
                    'HH3W2' : [[Util_HH3W2I1, Util_HH3W2I2, Util_HH3W2I3],
                               [Mat_Index+6, Mat_Index+7, Mat_Index+8]],
                    'HH3W3' : [[Util_HH3W3I1, Util_HH3W3I2, Util_HH3W3I3],
                               [Mat_Index+9, Mat_Index+10, Mat_Index+11]],
                   }
        HH3_Dict, counter = self.Calc_Prob_Segments(eb, HH3_Dict, HH3, Mat_Index)
        Mat_Index += counter

        HH4 = eb.matrix("moHh4pUp").get_numpy_data()
        HH4_Dict = {
                    'HH4W0' : [[Util_HH4W0I1, Util_HH4W0I2, Util_HH4W0I3],
                               [Mat_Index+0, Mat_Index+1, Mat_Index+2]],
                    'HH4W1' : [[Util_HH4W1I1, Util_HH4W1I2, Util_HH4W1I3],
                               [Mat_Index+3, Mat_Index+4, Mat_Index+5]],
                    'HH4W2' : [[Util_HH4W2I1, Util_HH4W2I2, Util_HH4W2I3],
                               [Mat_Index+6, Mat_Index+7, Mat_Index+8]],
                    'HH4W3' : [[Util_HH4W3I1, Util_HH4W3I2, Util_HH4W3I3],
                               [Mat_Index+9, Mat_Index+10, Mat_Index+11]],
                   }
        HH4_Dict, counter = self.Calc_Prob_Segments(eb, HH4_Dict, HH4, Mat_Index)

        # compile data to single table and output to sqlite
        taz = util.get_matrix_numpy(eb, 'zoneindex')
        output_df = pd.DataFrame()

        # extract output data from dictionary
        output_df = self.hh_dataframer(HHDict = HH1_Dict, df = output_df, zonelist = taz)
        output_df = self.hh_dataframer(HHDict = HH2_Dict, df = output_df, zonelist = taz)
        output_df = self.hh_dataframer(HHDict = HH3_Dict, df = output_df, zonelist = taz)
        output_df = self.hh_dataframer(HHDict = HH4_Dict, df = output_df, zonelist = taz)

        # reorder columns to prepare table
        output_df = output_df[['TAZ','HHSize','HHWorker',0L,1L,2L]]
        # change income index to start at 1 instead of 2

        output_df.columns = ['TAZ1741','HHSize','HHWorker',1L,2L,3L]
        # move to long format
        output_df = pd.melt(output_df, id_vars = ['TAZ1741','HHSize','HHWorker'], var_name='HHInc', value_name='CountHHs')

        conn = util.get_rtm_db(eb)
        output_df.to_sql(name='segmentedHouseholds', con=conn, index=False, if_exists='replace')
        conn.close()



    def Calc_Prob_Segments(self, eb, HH_Dict, HHSize, Mat_Index):

        Theta = 0.5637
        Tiny = 0.000001
        Low_Nest_Dict = {key:sum(np.exp(nest_len[0]))+Tiny
                            for key,nest_len in HH_Dict.items()}

        Up_Nest_Dict = {key:pow(sum(np.exp(nest_len[0]))+Tiny,Theta)
                            for key,nest_len in HH_Dict.items()}

        Full_Util = sum(Up_Nest_Dict.values())

        Seg_Dict = {key:HHSize * np.exp(nest_len[0])/Low_Nest_Dict[key]*Up_Nest_Dict[key]/Full_Util
                            for key, nest_len in HH_Dict.items()}

        ## Dump data into mo matrices
        counter = 0
        for key in Seg_Dict:
            for nest_len in range (len(Seg_Dict[key])):
                # eb.matrix("mo"+str(HH_Dict[key][1][nest_len])).set_numpy_data(Seg_Dict[key][nest_len])
                counter = counter + 1
        return (Seg_Dict, counter)


    def hh_dataframer(self, HHDict, df, zonelist):

        k = HHDict.keys()

        for key in k:
            new_df = pd.DataFrame(HHDict[key]).transpose()
            new_df['TAZ'] = zonelist

            cols = re.compile(r'(\w\w)(\d)(\w)(\d)')
            vals = cols.search(key)
            new_df['HHSize'] = int(vals.group(2))
            new_df['HHWorker'] = int(vals.group(4))
            df = df.append(new_df)
        return df


    def Generate_Data_Frame(self, eb):
        util = _m.Modeller().tool("translink.util")

    	sql = """
        SELECT
        ti.TAZ1741
        ,IFNULL(d.POP_18to24/d.POP_Total, 0) as Pop18_24_prp
        ,IFNULL(d.POP_65plus/d.POP_Total, 0) as PopSen_prp
        ,IFNULL((d.POP_0to4 + d.POP_5to12 + d.POP_13to17)/d.POP_Total,0) as PopChld_prp
        ,IFNULL(de.popdensln, 0) as LPopDen
        ,IFNULL(de.empdensln, 0) as LEmpDen
        ,1 as One_Vector
        ,IFNULL(du.dtes, 0) as DTESDum
        ,IFNULL(du.university, 0) as UniDum
        ,IFNULL(du.northshore, 0) as NShoreDum
        ,CASE WHEN du.cbd = 1 THEN 0 ELSE 1 END NCBD
        ,IFNULL(a.dist_cbd_ln, 0) as LDistCBD
        ,IFNULL(a.dist_tc_ln, 0 ) as LDistTC

        FROM taz_index ti
        LEFT JOIN demographics d on d.TAZ1700 = ti.TAZ1741
        LEFT JOIN densities de on de.TAZ1700 = ti.TAZ1741
        LEFT JOIN dummies du on du.TAZ1700 = ti.TAZ1741
        LEFT JOIN accessibilities a on a.TAZ1741 = ti.TAZ1741

        ORDER BY ti.TAZ1741
    	"""
    	conn = util.get_rtm_db(eb)
    	df = pd.read_sql(sql, conn)
    	conn.close()

        return(df)
