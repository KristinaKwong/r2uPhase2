##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage1.prds
##--Purpose:
##---------------------------------------------------------------------
import inro.modeller as _m
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

        # calculate household level trip productions and export control totals
        self.Calcuate_HH_Level_Trips(eb, hh_c_df=hh_c_df, hh_nc_df=hh_nc_df)

        # get variables for taz level production calculations
        taz_df = self.Generate_TAZ_Trip_Productions_df(eb)

        # calculate taz level trip productions
        self.Calculate_TAZ_Level_Trips(eb, df=taz_df)

    @_m.logbook_trace("Calculate Household Level Trip Productions")
    def Calcuate_HH_Level_Trips(self, eb, hh_c_df, hh_nc_df):
        util = _m.Modeller().tool("translink.util")

        # acquire household level data
        conn = util.get_rtm_db(eb)
        hh_df = pd.read_sql('''SELECT TAZ1741,
                               HHSize,
                               HHWorker,
                               HHInc,
                               HHAuto,
                               CountHHs,
                               e.gm

                               FROM segmentedHouseholds sh

                               LEFT JOIN ensembles e on e.TAZ1700 = sh.TAZ1741''', conn)
        conn.close()



        # Attach commute  trip rates
        hh_df = pd.merge(hh_df, hh_c_df, how = 'left', left_on = ['HHWorker','HHInc'], right_on = ['HHWorker','HHInc'])
        # 0 workers households make no commute trips
        hh_df['hbw_prds'].fillna(0, inplace=True)
        
        # Attach non-commute trip rates
        hh_df = pd.merge(hh_df, hh_nc_df, how = 'left', left_on = ['HHSize','HHInc'], right_on = ['HHSize','HHInc'])

        bowen_adj = 0.40

        hh_df['bowen_adj'] = np.where(hh_df['gm'] == 100, bowen_adj, 1.00)


        # Calculate Productions

        # Commute
        hh_df['hbw'] = hh_df['CountHHs'] * hh_df['hbw_prds'] * hh_df['bowen_adj']
     
        #  Non Commute
        hh_df['hbesc'] = hh_df['CountHHs'] * hh_df['hbesc_prds'] * hh_df['bowen_adj']
        hh_df['hbpb'] = hh_df['CountHHs'] * hh_df['hbpb_prds'] * hh_df['bowen_adj']
        hh_df['hbsch'] = hh_df['CountHHs'] * hh_df['hbsch_prds'] * hh_df['bowen_adj']
        hh_df['hbshop'] = hh_df['CountHHs'] * hh_df['hbshop_prds'] * hh_df['bowen_adj']
        hh_df['hbsoc'] = hh_df['CountHHs'] * hh_df['hbsoc_prds'] * hh_df['bowen_adj']

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
        # Original code (EMME 4.3) -----   df_emme.sort(columns='TAZ1741', inplace=True)
        df_emme.sort_values(by=['TAZ1741'],axis=0,inplace=True)

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
    def Calculate_TAZ_Level_Trips(self, eb, df):
        util = _m.Modeller().tool("translink.util")

        # set coefficents
        c_hbu_int         = eb.matrix("c_hbu_int"        ).data
        c_iPop1824UnAcOth = eb.matrix("c_iPop1824UnAcOth").data
        c_iPop1824UnAcVan = eb.matrix("c_iPop1824UnAcVan").data
        c_iPop1824UnAcSur = eb.matrix("c_iPop1824UnAcSur").data
        c_iP2434UnAc      = eb.matrix("c_iP2434UnAc"     ).data

        ## Add Bowenn Island adjsutment

        bowen_adj = 0.40
        df['gm'] = util.get_matrix_numpy(eb, 'gm_ensem')
        df['bowen_adj'] = np.where(df['gm'] == 100, bowen_adj, 1.00)

        # calculate hbu productions
        df['hbu'] = ( c_hbu_int * df['hbu_intercept']
                    + c_iPop1824UnAcOth * df['iPop1824UnAcOth']
                    + c_iPop1824UnAcVan * df['iPop1824UnAcVan']
                    + c_iPop1824UnAcSur * df['iPop1824UnAcSur']
                    + c_iP2434UnAc * df['iPop2534UnAc'] ) * df['bowen_adj']


        # clear out intercept trips from pnr and external zones
        df['hbu'] = np.where(df['TAZ1741'] < 1000, 0, df['hbu'])

        # export data to sqlite database
        df = df[['TAZ1741','hbu']]

        conn = util.get_rtm_db(eb)
        df.to_sql(name='TripsTazPrds', con=conn, flavor='sqlite', index=False, if_exists='replace')
        conn.close()

        # stuff in emmebank
        util.set_matrix_numpy(eb, 'mohbuprd', df['hbu'].values)


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
        hbw_prods = [
        [1, 1, eb.matrix("hbwprd_1-1").data],
        [2, 1, eb.matrix("hbwprd_2-1").data],
        [3, 1, eb.matrix("hbwprd_3-1").data],
        [1, 2, eb.matrix("hbwprd_1-2").data],
        [2, 2, eb.matrix("hbwprd_2-2").data],
        [3, 2, eb.matrix("hbwprd_3-2").data],
        [1, 3, eb.matrix("hbwprd_1-3").data],
        [2, 3, eb.matrix("hbwprd_2-3").data],
        [3, 3, eb.matrix("hbwprd_3-3").data]
        ]


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

        hbpb_prods = [
        [1, eb.matrix("hbpbprd_1").data],
        [2, eb.matrix("hbpbprd_2").data],
        [3, eb.matrix("hbpbprd_3").data],
        [4, eb.matrix("hbpbprd_4").data]
        ]

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

        hbshop_prods = [
        [1, 1, eb.matrix("hbshop_1-1").data],
        [2, 1, eb.matrix("hbshop_2-1").data],
        [3, 1, eb.matrix("hbshop_3-1").data],
        [4, 1, eb.matrix("hbshop_4-1").data],
        [1, 2, eb.matrix("hbshop_1-2").data],
        [2, 2, eb.matrix("hbshop_2-2").data],
        [3, 2, eb.matrix("hbshop_3-2").data],
        [4, 2, eb.matrix("hbshop_4-2").data],
        [1, 3, eb.matrix("hbshop_1-3").data],
        [2, 3, eb.matrix("hbshop_2-3").data],
        [3, 3, eb.matrix("hbshop_3-3").data],
        [4, 3, eb.matrix("hbshop_4-3").data]
        ]

        hbsoc_prods = [
        [1, 1, eb.matrix("hbsoc_1-1").data],
        [2, 1, eb.matrix("hbsoc_2-1").data],
        [3, 1, eb.matrix("hbsoc_3-1").data],
        [4, 1, eb.matrix("hbsoc_4-1").data],
        [1, 2, eb.matrix("hbsoc_1-2").data],
        [2, 2, eb.matrix("hbsoc_2-2").data],
        [3, 2, eb.matrix("hbsoc_3-2").data],
        [4, 2, eb.matrix("hbsoc_4-2").data],
        [1, 3, eb.matrix("hbsoc_1-3").data],
        [2, 3, eb.matrix("hbsoc_2-3").data],
        [3, 3, eb.matrix("hbsoc_3-3").data],
        [4, 3, eb.matrix("hbsoc_4-3").data]
        ]

        # Generate Commute Trip Rate Data Frame
        hh_commute_prds = pd.DataFrame(hbw_prods, columns =  ['HHWorker','HHInc','hbw_prds'])
    

        # Generate Non Commute Data Frame
        hbesc_prod_df = pd.read_csv(hbesc_prods, sep = ',')
        hbpb_prod_df = pd.DataFrame(hbpb_prods, columns = ['HHSize', 'hbpb_prds'])
        hbsch_prod_df = pd.read_csv(hbsch_prods, sep = ',')
        hbshop_prod_df = pd.DataFrame(hbshop_prods, columns = ['HHSize','HHInc','hbshop_prds'])
        hbsoc_prod_df = pd.DataFrame(hbsoc_prods, columns = ['HHSize','HHInc','hbsoc_prds'])
        df = pd.merge(hbesc_prod_df, hbpb_prod_df, how= 'left', left_on = ['HHSize'], right_on = ['HHSize'])
        df = pd.merge(df, hbsch_prod_df, how= 'left', left_on = ['HHSize', 'HHInc'], right_on = ['HHSize', 'HHInc'])
        df = pd.merge(df, hbshop_prod_df, how= 'left', left_on = ['HHSize', 'HHInc'], right_on = ['HHSize', 'HHInc'])
        hh_noncommute_prds = pd.merge(df, hbsoc_prod_df, how= 'left', left_on = ['HHSize', 'HHInc'], right_on = ['HHSize', 'HHInc'])
        
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