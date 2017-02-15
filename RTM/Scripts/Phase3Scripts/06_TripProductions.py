##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path:
##--Purpose:
##---------------------------------------------------------------------
import inro.modeller as _m
import csv
import os
import re
from StringIO import StringIO
import numpy as np
import pandas as pd
import traceback as _traceback

class TripProductions(_m.Tool()):
    ##Create global attributes (referring to dialogue boxes on the pages)

    ##Global attribute for Tool Run Message (successful/not successful)
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Trip Productions"
        pb.description = "Runs the Trip Production Model"
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

    @_m.logbook_trace("Trip Productions")
    def __call__(self, eb):
        util = _m.Modeller().tool("translink.util")

        ##Batchin File
        self.matrix_batchins(eb)

        ##Generate Dataframe (Df for short hand) used for trip production rates
        hh_c_df, hh_nc_df = self.Generate_HH_Trip_Productions_dfs(eb)

        # calculate household level trip productions and export nhb control totals
        nhbw_ct, nhbo_ct = self.Calcuate_HH_Level_Trips(eb, hh_c_df=hh_c_df, hh_nc_df=hh_nc_df)

        # get variables for taz level production calculations
        taz_df = self.Generate_TAZ_Trip_Productions_df(eb)

        # calculate taz level trip productions
        self.Calculate_TAZ_Level_Trips(eb, df=taz_df, nhbw_ct=nhbw_ct, nhbo_ct=nhbo_ct)

    @_m.logbook_trace("Calculate Household Level Trip Productions")
    def Calcuate_HH_Level_Trips(self, eb, hh_c_df, hh_nc_df):
        util = _m.Modeller().tool("translink.util")

        # acquire household level data
        conn = util.get_rtm_db(eb)
        hh_df = pd.read_sql("SELECT * FROM segmentedHouseholds", conn)
        conn.close()

        # Attach commute  trip rates
        hh_df = pd.merge(hh_df, hh_c_df, how = 'left', left_on = ['HHWorker','HHInc'], right_on = ['HHWorker','HHInc'])
        # 0 workers households make no commute trips
        hh_df['hbw_prds'].fillna(0, inplace=True)
        hh_df['nhbw_ct_prds'].fillna(0, inplace=True)

        # Attach non-commute trip rates
        hh_df = pd.merge(hh_df, hh_nc_df, how = 'left', left_on = ['HHSize','HHInc'], right_on = ['HHSize','HHInc'])

        # Calculate Productions

        # Commute
        hh_df['hbw'] = hh_df['CountHHs'] * hh_df['hbw_prds']
        hh_df['nhbw_ct'] = hh_df['CountHHs'] * hh_df['nhbw_ct_prds']
        #  Non Commute
        hh_df['hbesc'] = hh_df['CountHHs'] * hh_df['hbesc_prds']
        hh_df['hbpb'] = hh_df['CountHHs'] * hh_df['hbpb_prds']
        hh_df['hbsch'] = hh_df['CountHHs'] * hh_df['hbsch_prds']
        hh_df['hbshop'] = hh_df['CountHHs'] * hh_df['hbshop_prds']
        hh_df['hbsoc'] = hh_df['CountHHs'] * hh_df['hbsoc_prds']
        hh_df['nhbo_ct'] = hh_df['CountHHs'] * hh_df['nhbo_ct_prds']

        # Calculate NHB trip control totals
        nhbw_ct = hh_df['nhbw_ct'].sum()
        nhbo_ct = hh_df['nhbo_ct'].sum()

        # Set Balancing Control Totals
        ct_df = hh_df[['hbw','hbesc','hbpb','hbsch','hbshop', 'hbsoc']]
        ct_df = pd.DataFrame(ct_df.sum())
        ct_df.reset_index(inplace=True)
        ct_df.columns = ['purpose','control_total']

        # prep data frame for output
        hh_df = hh_df[['TAZ1741','HHSize','HHWorker','HHInc','HHAuto','CountHHs','hbw','hbesc','hbpb','hbsch','hbshop','hbsoc']]

        # write data to sqlite database
        conn = util.get_rtm_db(eb)
        hh_df.to_sql(name='TripsHhPrds', con=conn, flavor='sqlite', index=False, if_exists='replace')
        ct_df.to_sql(name='TripsBalCts', con=conn, flavor='sqlite', index=False, if_exists='replace')
        conn.close()

        # collapse 2 and 3 Auto
        hh_df.ix[hh_df.HHAuto == 3, 'HHAuto'] = 2

        # Summarize trips at Income/Auto level
        df_emme = hh_df
        df_emme['HHInc'] = df_emme['HHInc'].astype(str)
        df_emme['HHAuto'] = df_emme['HHAuto'].astype(str)
        df_emme = df_emme.drop(['HHSize','HHWorker','CountHHs'], axis=1)
        df_emme = df_emme.groupby(['TAZ1741','HHInc','HHAuto'])
        df_emme = df_emme.sum()
        df_emme = df_emme.reset_index()

        # pivot to vectors of length 1741 to stuff in emmebank
        df_emme = df_emme.pivot_table(index='TAZ1741', columns=['HHInc','HHAuto'], values=['hbw','hbesc','hbpb','hbsch','hbshop','hbsoc'])
        df_emme.columns = [' '.join(col).strip() for col in df_emme.columns.values]
        df_emme = pd.DataFrame(df_emme.to_records())
        df_emme.sort(columns='TAZ1741', inplace=True)

        # loop across these to set the matrices
        Pur = ['hbw','hbesc','hbpb','hbsch','hbshop','hbsoc']
        Inc = [1,2,3]
        Aut = [0,1,2]

        # stuff data
        for purpose in Pur:
            for income in Inc:
                for auto in Aut:
                    mo = "mo{purpose}Inc{income}Au{auto}prd".format(purpose=purpose, income=income, auto=auto)
                    vec = "{purpose} {income} {auto}".format(purpose=purpose, income=income, auto=auto)
                    util.set_matrix_numpy(eb, mo, df_emme[vec].values)

        return np.round(nhbw_ct,6), np.round(nhbo_ct,6)


        @_m.logbook_trace("Import TAZ level Data")
        def Generate_TAZ_Trip_Productions_df(self, eb):
            util = _m.Modeller().tool("translink.util")

            taz_sql = """
            SELECT
                ti.TAZ1741
                -- hbu variables
                ,IFNULL(d.POP_18to24 * a.uni_acc_ln, 0) as iPop1824UnAc
                ,IFNULL(d.POP_25to34 * a.uni_acc_ln, 0) as iPop2534UnAc
                -- employment variables
                ,IFNULL(d.EMP_Construct_Mfg, 0) as EMP_Construct_Mfg
                ,IFNULL(d.EMP_TCU_Wholesale, 0) as EMP_TCU_Wholesale
                ,IFNULL(d.EMP_FIRE, 0) as EMP_FIRE
                ,IFNULL(d.EMP_Business_OtherServices, 0) as EMP_Business_OtherServices
                ,IFNULL(d.EMP_AccomFood_InfoCult, 0) as EMP_AccomFood_InfoCult
                ,IFNULL(d.EMP_Retail, 0) as EMP_Retail
                ,IFNULL(d.EMP_Health_Educat_PubAdmin, 0) as EMP_Health_Educat_PubAdmin
                -- school enrolment variables
                ,IFNULL(d.Elementary_Enrolment, 0) as Elementary_Enrolment
                ,IFNULL(d.Secondary_Enrolment, 0) as Secondary_Enrolment
                ,IFNULL(d.PostSecFTE, 0) as PostSecFTE
                -- household variables
                ,IFNULL(d.HH_Total,0) as HH_Total

            FROM taz_index ti
                LEFT JOIN demographics d on d.TAZ1700 = ti.TAZ1741
                LEFT JOIN accessibilities a on a.TAZ1741 = ti.TAZ1741

            ORDER BY
                ti.TAZ1741
            """
            conn = util.get_rtm_db(eb)
            taz_df = pd.read_sql(taz_sql, conn)
            conn.close()

            return taz_df




    @_m.logbook_trace("Calculate TAZ Level Trip Productions")
    def Calculate_TAZ_Level_Trips(self, eb, df, nhbw_ct, nhbo_ct):
        util = _m.Modeller().tool("translink.util")

        # set coefficents
        c_hbu_int = 20.617679
        c_iPop1824UnAcOth = 0.079319
        c_iPop1824UnAcVan = 0.086291
        c_iPop1824UnAcSur = 0.070245
        c_iP2434UnAc = 0.009762

        c_nhbw_int = 11.09161
        c_nhbw_CM = 0.313161
        c_nhbw_TW = 0.180534
        c_nhbw_FIRE = 0.296122
        c_nhbw_BOS = 0.412223
        c_nhbw_AFIC = 0.252867
        c_nhbw_Ret = 0.679641
        c_nhbw_HEPA = 0.420215
        c_nhbw_EE = 0.059015
        c_nhbw_SE = 0.093358
        c_nhbw_HHs = 0.055688

        c_nhbo_int = 12.878959
        c_nhbo_AFIC = 0.505787
        c_nhbo_Ret = 1.828427
        c_nhbo_HEPA = 0.361545
        c_nhbo_EE = 0.38903
        c_nhbo_SE = 0.230765
        c_nhbo_PS = 0.040261
        c_nhbo_HHs = 0.175705

        nhbw_ct_2011 = (eb.matrix("msnhbwCt2011").data)
        nhbo_ct_2011 = (eb.matrix("msnhboCt2011").data)

        # calculate hbu productions
        df['hbu'] = ( c_hbu_int * df['hbu_intercept']
                    + c_iPop1824UnAcOth * df['iPop1824UnAcOth']
                    + c_iPop1824UnAcVan * df['iPop1824UnAcVan']
                    + c_iPop1824UnAcSur * df['iPop1824UnAcSur']                    
                    + c_iP2434UnAc * df['iPop2534UnAc'] )

        # calculate non-home based work productions
        df['nhbw'] = ( c_nhbw_int
                     + c_nhbw_CM * df['EMP_Construct_Mfg']
                     + c_nhbw_TW * df['EMP_TCU_Wholesale']
                     + c_nhbw_FIRE * df['EMP_FIRE']
                     + c_nhbw_BOS * df['EMP_Business_OtherServices']
                     + c_nhbw_AFIC * df['EMP_AccomFood_InfoCult']
                     + c_nhbw_Ret * df['EMP_Retail']
                     + c_nhbw_HEPA * df['EMP_Health_Educat_PubAdmin']
                     + c_nhbw_EE * df['Elementary_Enrolment']
                     + c_nhbw_SE * df['Secondary_Enrolment']
                     + c_nhbw_HHs * df['HH_Total'] )

        # calculate non-home based other productions
        df['nhbo'] = ( c_nhbo_int
                     + c_nhbo_AFIC * df['EMP_AccomFood_InfoCult']
                     + c_nhbo_Ret * df['EMP_Retail']
                     + c_nhbo_HEPA * df['EMP_Health_Educat_PubAdmin']
                     + c_nhbo_EE * df['Elementary_Enrolment']
                     + c_nhbo_SE * df['Secondary_Enrolment']
                     + c_nhbo_PS * df['PostSecFTE']
                     + c_nhbo_HHs * df['HH_Total'] )

        # clear out intercept trips from pnr and external zones
        df['hbu'] = np.where(df['TAZ1741'] < 1000, 0, df['hbu'])
        df['nhbw'] = np.where(df['TAZ1741'] < 1000, 0, df['nhbw'])
        df['nhbo'] = np.where(df['TAZ1741'] < 1000, 0, df['nhbo'])

        # scale based on houseold productions
        nhbw_scalar = nhbw_ct / nhbw_ct_2011
        nhbo_scalar = nhbo_ct / nhbo_ct_2011
        df['nhbw'] = df['nhbw'] * nhbw_scalar
        df['nhbo'] = df['nhbo'] * nhbo_scalar

        # export data to sqlite database
        ct_df = df[['nhbw','nhbo']]
        ct_df = pd.DataFrame(ct_df.sum())
        ct_df.reset_index(inplace=True)
        ct_df.columns = ['purpose','control_total']

        # export data to sqlite database
        df = df[['TAZ1741','hbu','nhbw','nhbo']]

        conn = util.get_rtm_db(eb)
        df.to_sql(name='TripsTazPrds', con=conn, flavor='sqlite', index=False, if_exists='replace')
        ct_df.to_sql(name='TripsBalCts', con=conn, flavor='sqlite', index=False, if_exists='append')
        conn.close()

        # stuff in emmebank
        util.set_matrix_numpy(eb, 'mohbuprd', df['hbu'].values)
        util.set_matrix_numpy(eb, 'monhbwprd', df['nhbw'].values)
        util.set_matrix_numpy(eb, 'monhboprd', df['nhbo'].values)


    @_m.logbook_trace("Generate TAZ Level Trip Production Variables Dataframe")
    def Generate_TAZ_Trip_Productions_df(self, eb):
        util = _m.Modeller().tool("translink.util")

        taz_sql = """
        SELECT
            ti.TAZ1741
            -- hbu variables
            --,IFNULL(d.POP_18to24 * a.uni_acc_ln, 0) as iPop1824UnAc
            ,CASE WHEN IFNULL(d.POP_Total, 0) >  0 THEN 1 ELSE 0 END hbu_intercept
            ,CASE WHEN IFNULL(e.gy, 0) = 4 THEN IFNULL(d.POP_18to24 * a.uni_acc_ln, 0) ELSE 0 END iPop1824UnAcVan
            ,CASE WHEN IFNULL(e.gy, 0) = 9 THEN IFNULL(d.POP_18to24 * a.uni_acc_ln, 0) ELSE 0 END iPop1824UnAcSur
            ,CASE WHEN IFNULL(e.gy, 0) NOT IN (4,9) THEN IFNULL(d.POP_18to24 * a.uni_acc_ln, 0) ELSE 0 END iPop1824UnAcOth
            ,IFNULL(d.POP_25to34 * a.uni_acc_ln, 0) as iPop2534UnAc
            -- employment variables
            ,IFNULL(d.EMP_Construct_Mfg, 0) as EMP_Construct_Mfg
            ,IFNULL(d.EMP_TCU_Wholesale, 0) as EMP_TCU_Wholesale
            ,IFNULL(d.EMP_FIRE, 0) as EMP_FIRE
            ,IFNULL(d.EMP_Business_OtherServices, 0) as EMP_Business_OtherServices
            ,IFNULL(d.EMP_AccomFood_InfoCult, 0) as EMP_AccomFood_InfoCult
            ,IFNULL(d.EMP_Retail, 0) as EMP_Retail
            ,IFNULL(d.EMP_Health_Educat_PubAdmin, 0) as EMP_Health_Educat_PubAdmin
            -- school enrolment variables
            ,IFNULL(d.Elementary_Enrolment, 0) as Elementary_Enrolment
            ,IFNULL(d.Secondary_Enrolment, 0) as Secondary_Enrolment
            ,IFNULL(d.PostSecFTE, 0) as PostSecFTE
            -- household variables
            ,IFNULL(d.HH_Total,0) as HH_Total


        FROM taz_index ti
            LEFT JOIN demographics d on d.TAZ1700 = ti.TAZ1741
            LEFT JOIN accessibilities a on a.TAZ1741 = ti.TAZ1741
            LEFT JOIN ensembles e on e.TAZ1700 = ti.TAZ1741

        ORDER BY
            ti.TAZ1741
        """
        conn = util.get_rtm_db(eb)
        taz_df = pd.read_sql(taz_sql, conn)
        conn.close()

        return taz_df

    @_m.logbook_trace("Import and Summarize Household Level Trip Rates")
    def Generate_HH_Trip_Productions_dfs(self, eb):
        util = _m.Modeller().tool("translink.util")

        # define Coefficients from model estimation
        hbw_prods = StringIO("""HHWorker,HHInc,hbw_prds
        1,1,1.142723
        2,1,2.044779
        3,1,3.488924
        1,2,1.280331
        2,2,2.426104
        3,2,3.812845
        1,3,1.38898
        2,3,2.390059
        3,3,4.163671
        """)

        nhbw_ct_prods = StringIO("""HHWorker,HHInc,nhbw_ct_prds
        1,1,0.377038
        2,1,0.732431
        3,1,0.714433
        1,2,0.548288
        2,2,0.845521
        3,2,0.896147
        1,3,0.706515
        2,3,1.161107
        3,3,1.113165
        """)

        hbesc_prods = StringIO("""HHSize,HHInc,hbesc_prds
        1,1,0.062889
        2,1,0.30258
        3,1,0.682318
        4,1,1.549849
        1,2,0.09731
        2,2,0.271858
        3,2,0.71941
        4,2,1.713166
        1,3,0.062455
        2,3,0.227354
        3,3,0.73346
        4,3,1.535946
        """)

        hbpb_prods = StringIO("""HHSize,hbpb_prds
        1,0.334523
        2,0.520753
        3,0.52108
        4,0.499412
        """)

        hbsch_prods = StringIO("""HHSize,HHInc,hbsch_prds
        1,1,0
        2,1,0.074779
        3,1,0.684717
        4,1,1.782312
        1,2,0
        2,2,0.018304
        3,2,0.42979
        4,2,1.715844
        1,3,0
        2,3,0.007462
        3,3,0.358231
        4,3,1.490737
        """)

        hbshop_prods = StringIO("""HHSize,HHInc,hbshop_prds
        1,1,0.530045
        2,1,0.89068
        3,1,0.743733
        4,1,0.780986
        1,2,0.466144
        2,2,0.690868
        3,2,0.723615
        4,2,0.711063
        1,3,0.265136
        2,3,0.537008
        3,3,0.598171
        4,3,0.62543
        """)

        hbsoc_prods = StringIO("""HHSize,HHInc,hbsoc_prds
        1,1,0.47585
        2,1,0.865361
        3,1,0.995139
        4,1,1.06819
        1,2,0.58349
        2,2,0.961634
        3,2,0.9654
        4,2,1.445937
        1,3,0.503203
        2,3,0.855158
        3,3,1.074033
        4,3,1.567024
        """)

        nhbo_ct_prods = StringIO("""HHSize,HHInc,nhbo_ct_prds
        1,1,0.523913
        2,1,0.918434
        3,1,0.865844
        4,1,1.317712
        1,2,0.58403
        2,2,0.740073
        3,2,0.921248
        4,2,1.291335
        1,3,0.382194
        2,3,0.598365
        3,3,0.747529
        4,3,1.183577
        """)

        # Generate Commute Trip Rate Data Frome
        hbw_prod_df = pd.read_csv(hbw_prods, sep = ',')
        nhbw_ct_prod_df = pd.read_csv(nhbw_ct_prods, sep = ',')
        hh_commute_prds = pd.merge(hbw_prod_df, nhbw_ct_prod_df, how= 'left',left_on = ['HHWorker','HHInc'], right_on = ['HHWorker','HHInc'])

        # Generate Non Commute Data Frame
        hbesc_prod_df = pd.read_csv(hbesc_prods, sep = ',')
        hbpb_prod_df = pd.read_csv(hbpb_prods, sep = ',')
        hbsch_prod_df = pd.read_csv(hbsch_prods, sep = ',')
        hbshop_prod_df = pd.read_csv(hbshop_prods, sep = ',')
        hbsoc_prod_df = pd.read_csv(hbsoc_prods, sep = ',')
        nhbo_ct_prod_df = pd.read_csv(nhbo_ct_prods, sep = ',')
        df = pd.merge(hbesc_prod_df, hbpb_prod_df, how= 'left', left_on = ['HHSize'], right_on = ['HHSize'])
        df = pd.merge(df, hbsch_prod_df, how= 'left', left_on = ['HHSize', 'HHInc'], right_on = ['HHSize', 'HHInc'])
        df = pd.merge(df, hbshop_prod_df, how= 'left', left_on = ['HHSize', 'HHInc'], right_on = ['HHSize', 'HHInc'])
        df = pd.merge(df, hbsoc_prod_df, how= 'left', left_on = ['HHSize', 'HHInc'], right_on = ['HHSize', 'HHInc'])
        hh_noncommute_prds = pd.merge(df, nhbo_ct_prod_df, how= 'left', left_on = ['HHSize', 'HHInc'], right_on = ['HHSize', 'HHInc'])

        return hh_commute_prds, hh_noncommute_prds


    @_m.logbook_trace("Initialize Trip Production Matrices")
    def matrix_batchins(self, eb):
        util = _m.Modeller().tool("translink.util")

        util.initmat(eb, "mo2000", "hbwInc1Au0prd", "hbwInc1Au0 Productions", 0)
        util.initmat(eb, "mo2001", "hbwInc2Au0prd", "hbwInc2Au0 Productions", 0)
        util.initmat(eb, "mo2002", "hbwInc3Au0prd", "hbwInc3Au0 Productions", 0)
        util.initmat(eb, "mo2003", "hbwInc1Au1prd", "hbwInc1Au1 Productions", 0)
        util.initmat(eb, "mo2004", "hbwInc2Au1prd", "hbwInc2Au1 Productions", 0)
        util.initmat(eb, "mo2005", "hbwInc3Au1prd", "hbwInc3Au1 Productions", 0)
        util.initmat(eb, "mo2006", "hbwInc1Au2prd", "hbwInc1Au2 Productions", 0)
        util.initmat(eb, "mo2007", "hbwInc2Au2prd", "hbwInc2Au2 Productions", 0)
        util.initmat(eb, "mo2008", "hbwInc3Au2prd", "hbwInc3Au2 Productions", 0)

        util.initmat(eb, "mo2010", "hbescInc1Au0prd", "hbescInc1Au0 Productions", 0)
        util.initmat(eb, "mo2011", "hbescInc2Au0prd", "hbescInc2Au0 Productions", 0)
        util.initmat(eb, "mo2012", "hbescInc3Au0prd", "hbescInc3Au0 Productions", 0)
        util.initmat(eb, "mo2013", "hbescInc1Au1prd", "hbescInc1Au1 Productions", 0)
        util.initmat(eb, "mo2014", "hbescInc2Au1prd", "hbescInc2Au1 Productions", 0)
        util.initmat(eb, "mo2015", "hbescInc3Au1prd", "hbescInc3Au1 Productions", 0)
        util.initmat(eb, "mo2016", "hbescInc1Au2prd", "hbescInc1Au2 Productions", 0)
        util.initmat(eb, "mo2017", "hbescInc2Au2prd", "hbescInc2Au2 Productions", 0)
        util.initmat(eb, "mo2018", "hbescInc3Au2prd", "hbescInc3Au2 Productions", 0)

        util.initmat(eb, "mo2020", "hbpbInc1Au0prd", "hbpbInc1Au0 Productions", 0)
        util.initmat(eb, "mo2021", "hbpbInc2Au0prd", "hbpbInc2Au0 Productions", 0)
        util.initmat(eb, "mo2022", "hbpbInc3Au0prd", "hbpbInc3Au0 Productions", 0)
        util.initmat(eb, "mo2023", "hbpbInc1Au1prd", "hbpbInc1Au1 Productions", 0)
        util.initmat(eb, "mo2024", "hbpbInc2Au1prd", "hbpbInc2Au1 Productions", 0)
        util.initmat(eb, "mo2025", "hbpbInc3Au1prd", "hbpbInc3Au1 Productions", 0)
        util.initmat(eb, "mo2026", "hbpbInc1Au2prd", "hbpbInc1Au2 Productions", 0)
        util.initmat(eb, "mo2027", "hbpbInc2Au2prd", "hbpbInc2Au2 Productions", 0)
        util.initmat(eb, "mo2028", "hbpbInc3Au2prd", "hbpbInc3Au2 Productions", 0)

        util.initmat(eb, "mo2030", "hbschInc1Au0prd", "hbschInc1Au0 Productions", 0)
        util.initmat(eb, "mo2031", "hbschInc2Au0prd", "hbschInc2Au0 Productions", 0)
        util.initmat(eb, "mo2032", "hbschInc3Au0prd", "hbschInc3Au0 Productions", 0)
        util.initmat(eb, "mo2033", "hbschInc1Au1prd", "hbschInc1Au1 Productions", 0)
        util.initmat(eb, "mo2034", "hbschInc2Au1prd", "hbschInc2Au1 Productions", 0)
        util.initmat(eb, "mo2035", "hbschInc3Au1prd", "hbschInc3Au1 Productions", 0)
        util.initmat(eb, "mo2036", "hbschInc1Au2prd", "hbschInc1Au2 Productions", 0)
        util.initmat(eb, "mo2037", "hbschInc2Au2prd", "hbschInc2Au2 Productions", 0)
        util.initmat(eb, "mo2038", "hbschInc3Au2prd", "hbschInc3Au2 Productions", 0)

        util.initmat(eb, "mo2040", "hbshopInc1Au0prd", "hbshopInc1Au0 Productions", 0)
        util.initmat(eb, "mo2041", "hbshopInc2Au0prd", "hbshopInc2Au0 Productions", 0)
        util.initmat(eb, "mo2042", "hbshopInc3Au0prd", "hbshopInc3Au0 Productions", 0)
        util.initmat(eb, "mo2043", "hbshopInc1Au1prd", "hbshopInc1Au1 Productions", 0)
        util.initmat(eb, "mo2044", "hbshopInc2Au1prd", "hbshopInc2Au1 Productions", 0)
        util.initmat(eb, "mo2045", "hbshopInc3Au1prd", "hbshopInc3Au1 Productions", 0)
        util.initmat(eb, "mo2046", "hbshopInc1Au2prd", "hbshopInc1Au2 Productions", 0)
        util.initmat(eb, "mo2047", "hbshopInc2Au2prd", "hbshopInc2Au2 Productions", 0)
        util.initmat(eb, "mo2048", "hbshopInc3Au2prd", "hbshopInc3Au2 Productions", 0)

        util.initmat(eb, "mo2050", "hbsocInc1Au0prd", "hbsocInc1Au0 Productions", 0)
        util.initmat(eb, "mo2051", "hbsocInc2Au0prd", "hbsocInc2Au0 Productions", 0)
        util.initmat(eb, "mo2052", "hbsocInc3Au0prd", "hbsocInc3Au0 Productions", 0)
        util.initmat(eb, "mo2053", "hbsocInc1Au1prd", "hbsocInc1Au1 Productions", 0)
        util.initmat(eb, "mo2054", "hbsocInc2Au1prd", "hbsocInc2Au1 Productions", 0)
        util.initmat(eb, "mo2055", "hbsocInc3Au1prd", "hbsocInc3Au1 Productions", 0)
        util.initmat(eb, "mo2056", "hbsocInc1Au2prd", "hbsocInc1Au2 Productions", 0)
        util.initmat(eb, "mo2057", "hbsocInc2Au2prd", "hbsocInc2Au2 Productions", 0)
        util.initmat(eb, "mo2058", "hbsocInc3Au2prd", "hbsocInc3Au2 Productions", 0)

        util.initmat(eb, "mo2060", "hbuprd", "hbu productions", 0)

        util.initmat(eb, "mo2070", "nhbwprd", "nhbw productions", 0)

        util.initmat(eb, "mo2080", "nhboprd", "nhbo productions", 0)
