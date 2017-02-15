##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.emme.stage1.step1.segmentation
##--Purpose:
##---------------------------------------------------------------------
import inro.modeller as _m
import csv
import os
import re
import numpy as np
import pandas as pd
import traceback as _traceback

class VehicleAvailability(_m.Tool()):
    ##Create global attributes (referring to dialogue boxes on the pages)

    ##Global attribute for Tool Run Message (successful/not successful)
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Vehicle Availability"
        pb.description = "Runs the Vehicle Availability Model"
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

    @_m.logbook_trace("Vehicle Availability")
    def __call__(self, eb):
        util = _m.Modeller().tool("translink.util")

        ##Batchin File
        # self.Init_Matrices(eb)

        ##Generate Dataframe (Df for short hand) used for Vehicle Availability
        df = self.Generate_Data_Frame(eb)

        ##Calculate vehicles availability levels
        self.Run_VAM(eb=eb, df=df)


    @_m.logbook_trace("Generate Vehicle Availability Dataframe")
    def Run_VAM(self, eb, df):
        util = _m.Modeller().tool("translink.util")

        p1 = 1.020321178
        p2 = -1.955615736
        p3 = -8.74342875
        p41 = 1.295070575
        p42 = 2.974969559
        p43 = 4.238969774
        p51 = -0.752179913
        p52 = -2.750774812
        p53 = -5.444109042
        p61 = 1.026483956
        p62 = 2.391921441
        p63 = 3.450781929
        p71 = 0.737276992
        p72 = 2.156543019
        p73 = 3.647708838
        p81 = -0.405910204
        p82 = -0.815626229
        p83 = -0.877730852
        p91 = -1.206858687
        p92 = -1.746559186
        p93 = -1.927276277
        p101 = 0.522053143
        p102 = 1.204920665
        p103 = 1.771108958
        p111 = 0.10124963
        p112 = 0.171749953
        p113 = 0.166694054
        p121 = 1.71E-02
        p122 = 9.42E-02
        p123 = 0.115117525
        p131 = -0.176021767
        p132 = -0.404430357
        p133 = -0.490921636
        p141 = 4.04E-02
        p142 = 7.18E-02
        p143 = 1.02E-01
        p151 = -0.266010966
        p152 = -0.495224982
        p153 = -0.604797223

        # calculate utility 0 cars - this is reference level
        df['U0c'] = 0

        # calculate utility 1 cars
        df['U1c'] = (  p1
                     + p41 * df['pop024']
                     + p51 * df['pop2554']
                     + p61 * df['HHSize']
                     + p71 * df['HHWorker']
                     + p81 * df['iSzWk']
                     + p91 * df['dLowInc']
                     + p101 * df['dHighInc']
                     + p111 * df['log_dist_cbd']
                     + p121 * df['log_dist_tc']
                     + p131 * df['log_density']
                     + p141 * df['log_accessibility']
                     + p151 * df['car_share_500m'])

        # calculate utility 2 cars
        df['U2c'] = (  p2
                     + p42 * df['pop024']
                     + p52 * df['pop2554']
                     + p62 * df['HHSize']
                     + p72 * df['HHWorker']
                     + p82 * df['iSzWk']
                     + p92 * df['dLowInc']
                     + p102 * df['dHighInc']
                     + p112 * df['log_dist_cbd']
                     + p122 * df['log_dist_tc']
                     + p132 * df['log_density']
                     + p142 * df['log_accessibility']
                     + p152 * df['car_share_500m'])

        # calculate utility 3 or more cars
        df['U3c'] = (  p3
                     + p43 * df['pop024']
                     + p53 * df['pop2554']
                     + p63 * df['HHSize']
                     + p73 * df['HHWorker']
                     + p83 * df['iSzWk']
                     + p93 * df['dLowInc']
                     + p103 * df['dHighInc']
                     + p113 * df['log_dist_cbd']
                     + p123 * df['log_dist_tc']
                     + p133 * df['log_density']
                     + p143 * df['log_accessibility']
                     + p153 * df['car_share_500m'])

        # Calculate the denominator
        df['D'] = np.exp(df['U0c']) + np.exp(df['U1c']) + np.exp(df['U2c']) + np.exp(df['U3c'])

        # calculate shares
        df['P0c'] = np.exp(df['U0c']) / df['D']
        df['P1c'] = np.exp(df['U1c']) / df['D']
        df['P2c'] = np.exp(df['U2c']) / df['D']
        df['P3c'] = np.exp(df['U3c']) / df['D']

        # apply to households

        df['0'] = df['P0c'] * df['CountHHs']
        df['1'] = df['P1c'] * df['CountHHs']
        df['2'] = df['P2c'] * df['CountHHs']
        df['3'] = df['P3c'] * df['CountHHs']

        # subset only remaining data columns
        df = df[['TAZ1741','HHSize','HHWorker','HHInc','0','1','2','3']]
        # move to long form
        df = pd.melt(df, id_vars = ['TAZ1741','HHSize','HHWorker','HHInc'], var_name='HHAuto', value_name='CountHHs')
        # convert to int
        df.HHAuto = df.HHAuto.astype(int)

        conn = util.get_rtm_db(eb)
        df.to_sql(name='segmentedHouseholds', con=conn, flavor='sqlite', index=False, if_exists='replace')
        conn.close()



    @_m.logbook_trace("Generate Vehicle Availability Dataframe")
    def Generate_Data_Frame(self, eb):
        util = _m.Modeller().tool("translink.util")

        hh_sql = """
        SELECT
            TAZ1741
            ,CountHHs
            ,HHSize
            ,HHWorker
            ,HHInc
            ,HHSize * HHWorker AS iSzWk
            ,CASE WHEN HHInc = 1 THEN 1 ELSE 0 END dLowInc
            ,CASE WHEN HHInc = 3 THEN 1 ELSE 0 END dHighInc

        FROM segmentedHouseholds

        ORDER BY
            TAZ1741
            ,HHSize
            ,HHWorker
            ,HHInc
        """

        taz_sql = """
        SELECT
        ti.TAZ1741
            ,IFNULL((d.POP_0to4 + d.POP_5to12 + d.POP_13to17 + d.POP_18to24) / d.POP_Total,0) as pop024
            ,IFNULL((d.POP_25to34 + d.POP_35to54) / d.POP_Total,0) as pop2554
            ,IFNULL(a.dist_cbd_ln, 0) as log_dist_cbd
            ,IFNULL(a.dist_tc_ln, 0) as log_dist_tc
            ,IFNULL(de.combinedensln, 0 ) as log_density
            ,IFNULL(a.auto_acc / IFNULL(a.transit_acc + 0.000001, 0.000001), 0) as accessibility  -- ratio of auto:transit accessibility
            ,IFNULL(g.car_share_500m, 0 ) as car_share_500m

        FROM taz_index ti
          LEFT JOIN demographics d on d.TAZ1700 = ti.TAZ1741
          LEFT JOIN accessibilities a on a.TAZ1741 = ti.TAZ1741
          LEFT JOIN densities de on de.TAZ1700 = ti.TAZ1741
          LEFT JOIN geographics g on g.TAZ1700 = ti.TAZ1741
        """

        conn = util.get_rtm_db(eb)
        hh_df = pd.read_sql(hh_sql, conn)
        taz_df = pd.read_sql(taz_sql, conn)
        conn.close()

        # calculate log combined accessibility
        if taz_df['accessibility'].min() < 1:
            log_trans_const = 1 - taz_df['accessibility'].min()
        else:
            log_trans_const = 0
        taz_df['log_accessibility'] = np.log(taz_df['accessibility'] + log_trans_const)
        taz_df.drop('accessibility', axis=1, inplace=True)

        output_df = pd.merge(hh_df, taz_df, how='left', left_on = ['TAZ1741'], right_on = ['TAZ1741'])

        return output_df
