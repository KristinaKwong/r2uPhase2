##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage1.atrs
##--Purpose:
##---------------------------------------------------------------------
import inro.modeller as _m
from StringIO import StringIO
import numpy as np
import pandas as pd
import traceback as _traceback

class TripAttractions(_m.Tool()):
    ##Create global attributes (referring to dialogue boxes on the pages)

    ##Global attribute for Tool Run Message (successful/not successful)
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Trip Attractions"
        pb.description = "Runs the Trip Attraction Model"
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

    @_m.logbook_trace("Trip Attractions")
    def __call__(self, eb):
        util = _m.Modeller().tool("translink.util")

        ##Batchin File
        self.matrix_batchins(eb)

        # get a variables dataframe and control total dataframe to balance Attractions to productions
        df, ct_df = self.Generate_Trip_Attractions_dfs(eb)

        # Calculate and balance trip Attractions
        # Note, HBU productions also get scaled here
        self.Calculate_Trip_Attractions(eb=eb, df=df, ct_df=ct_df)



    @_m.logbook_trace("Calculate Trip Attractions")
    def Calculate_Trip_Attractions(self, eb, df, ct_df):
        util = _m.Modeller().tool("translink.util")

        ########################################################################
        # Set Attraction Model Coefficients
        ########################################################################

        # hbw
        c_hbw_CM = 1.463994
        c_hbw_TW = 1.179233
        c_hbw_BOS = 1.561658
        c_hbw_FIRE = 1.621333
        c_hbw_Ret = 0.587329
        c_hbw_AFIC = 1.285617
        c_hbw_HEPA = 1.300219

        # hbesc
        c_hbesc_int = 176.886252
        c_hbesc_iTWAir = 0.836325
        c_hbesc_AFIC = 0.282008
        c_hbesc_Ret = 0.376091
        c_hbesc_HEPA = 0.23081
        c_hbesc_EE = 0.537972
        c_hbesc_SE = 0.370144
        c_hbesc_PU18 = 0.201655
        c_hbesc_PO65 = 0.106299

        # hbpb
        c_hbpb_Ret = 1.098472
        c_hbpb_AFIC = 0.220152
        c_hbpb_HEPA = 0.501523
        c_hbpb_PoTot = 0.040811

        # hbsch
        c_hbsch_EE = 1.320513
        c_hbsch_SE = 1.238657

        # hbshop
        c_hbshop_Ret = 4.596366

        # hbsoc
        c_hbsoc_int = 89.833668
        c_hbsoc_AFIC = 1.080346
        c_hbsoc_Ret = 1.17569
        c_hbsoc_HEPA = 0.270025
        c_hbsoc_PoTot = 0.131466


        # nhbw
        c_nhbw_int = 62.21822
        c_nhbw_CM = 0.147559
        c_nhbw_TW = 0.123596
        c_nhbw_BOS = 0.286774
        c_nhbw_FIRE = 0.100723
        c_nhbw_Ret = 1.132009
        c_nhbw_AFIC = 0.45005
        c_nhbw_HEPA = 0.390779

        # nhbo
        c_nhbo_Ret = 2.581269
        c_nhbo_AFIC = 0.36586
        c_nhbo_HEPA = 0.295724
        c_nhbo_PoTot = 0.076945
        c_nhbo_EE = 0.208777
        c_nhbo_SE = 0.177848

        # hbu
        c_hbu_iCbdPsfte = 0.287631
        c_hbu_iNotCbdPsfte = 1.411431



        ########################################################################
        # Calculate and Balance Attractions
        ########################################################################

        df['gm'] = util.get_matrix_numpy(eb, 'gm_ensem')
        df['bowen_adj'] = np.where(df['gm'] == 100, 0.4, 1)

        # HBW ##################################################################
        df['hbw'] = ( c_hbw_CM * df['EMP_Construct_Mfg']
                    + c_hbw_TW * df['EMP_TCU_Wholesale']
                    + c_hbw_BOS  * df['EMP_Business_OtherServices']
                    + c_hbw_FIRE * df['EMP_FIRE']
                    + c_hbw_Ret * df['EMP_Retail']
                    + c_hbw_AFIC * df['EMP_AccomFood_InfoCult']
                    + c_hbw_HEPA * df['EMP_Health_Educat_PubAdmin'] )*df['bowen_adj']

        # balance to productions
        scalar = ct_df.get_value(index='hbw', col='control_total')/ df['hbw'].sum()
        df['hbw'] = df['hbw'] * scalar

        # HBESC ################################################################
        df['hbesc'] = ( c_hbesc_int
                       + c_hbesc_iTWAir * df['iTWAir']
                       + c_hbesc_AFIC * df['EMP_AccomFood_InfoCult']
                       + c_hbesc_Ret * df['EMP_Retail']
                       + c_hbesc_HEPA * df['EMP_Health_Educat_PubAdmin']
                       + c_hbesc_EE * df['Elementary_Enrolment']
                       + c_hbesc_SE * df['Secondary_Enrolment']
                       + c_hbesc_PU18 * df['PopU18']
                       + c_hbesc_PO65 * df['POP_65plus'] )*df['bowen_adj']

        # clear out intercept trips from pnr and external zones and balance
        df['hbesc'] = np.where(df['TAZ1741'] < 1000, 0, df['hbesc'])
        scalar = ct_df.get_value(index='hbesc', col='control_total') / df['hbesc'].sum()
        df['hbesc'] = df['hbesc'] * scalar

        # HBPB #################################################################
        df['hbpb'] = ( c_hbpb_Ret * df['EMP_Retail']
                     + c_hbpb_AFIC * df['EMP_AccomFood_InfoCult']
                     + c_hbpb_HEPA * df['EMP_Health_Educat_PubAdmin']
                     + c_hbpb_PoTot * df['POP_Total'] )*df['bowen_adj']

        scalar = ct_df.get_value(index='hbpb', col='control_total')/ df['hbpb'].sum()
        df['hbpb'] = df['hbpb'] * scalar

        # HBSCH ################################################################
        df['hbsch'] = ( c_hbsch_EE * df['Elementary_Enrolment']
                      + c_hbsch_SE * df['Secondary_Enrolment'] )*df['bowen_adj']

        # write school attraction to EMMEbank md2030
        util.set_matrix_numpy(eb, 'mdhbschatr', df['hbsch'].values)

        specs = []
        # production totals by gx
        spec = util.matrix_spec("md2031", "(mo2030+mo2031+mo2032+mo2033+mo2034+mo2035+mo2036+mo2037+mo2038)*(gx(p).eq.gx(q))")
        spec["aggregation"] = {"origins": "+", "destinations": None}
        specs.append(spec)
        # attraction totals by gx
        spec = util.matrix_spec("md2032", "(md2030')*(gx(p).eq.gx(q))")
        spec["aggregation"] = {"origins": "+", "destinations": None}
        specs.append(spec)
        # Normalize the attraction totals
        spec = util.matrix_spec("md2030", "md2030*md2031/md2032")
        spec["constraint"]["by_zone"] = {"destinations": "gx1-gx15"}
        specs.append(spec)

        util.compute_matrix(specs)
        # feed gx-balanced attractions back to dataframe
        df['hbsch'] = util.get_matrix_numpy(eb, 'mdhbschatr')

        # HBSHOP ###############################################################
        df['hbshop'] = c_hbshop_Ret * df['EMP_Retail']*df['bowen_adj']

        scalar = ct_df.get_value(index='hbshop', col='control_total')/ df['hbshop'].sum()
        df['hbshop'] = df['hbshop'] * scalar

        # HBSOC ################################################################
        df['hbsoc'] = ( c_hbsoc_int
              + c_hbsoc_AFIC * df['EMP_AccomFood_InfoCult']
              + c_hbsoc_Ret * df['EMP_Retail']
              + c_hbsoc_HEPA * df['EMP_Health_Educat_PubAdmin']
              + c_hbsoc_PoTot * df['POP_Total'] )*df['bowen_adj']

        df['hbsoc'] = np.where(df['TAZ1741'] < 1000, 0, df['hbsoc'])
        scalar = ct_df.get_value(index='hbsoc', col='control_total') / df['hbsoc'].sum()
        df['hbsoc'] = df['hbsoc'] * scalar

        # NHBW #################################################################
        df['nhbw'] = ( c_nhbw_int
                     + c_nhbw_CM * df['EMP_Construct_Mfg']
                     + c_nhbw_TW * df['EMP_TCU_Wholesale']
                     + c_nhbw_BOS * df['EMP_Business_OtherServices']
                     + c_nhbw_FIRE * df['EMP_FIRE']
                     + c_nhbw_Ret * df['EMP_Retail']
                     + c_nhbw_AFIC * df['EMP_AccomFood_InfoCult']
                     + c_nhbw_HEPA * df['EMP_Health_Educat_PubAdmin'] )*df['bowen_adj']

        df['nhbw'] = np.where(df['TAZ1741'] < 1000, 0, df['nhbw'])
        scalar = ct_df.get_value(index='nhbw', col='control_total') / df['nhbw'].sum()
        df['nhbw'] = df['nhbw'] * scalar

        # NHBO #################################################################
        df['nhbo'] = ( c_nhbo_Ret * df['EMP_Retail']
                     + c_nhbo_AFIC * df['EMP_AccomFood_InfoCult']
                     + c_nhbo_HEPA * df['EMP_Health_Educat_PubAdmin']
                     + c_nhbo_PoTot * df['POP_Total']
                     + c_nhbo_EE * df['Elementary_Enrolment']
                     + c_nhbo_SE * df['Secondary_Enrolment'] )*df['bowen_adj']

        scalar = ct_df.get_value(index='nhbo', col='control_total') / df['nhbo'].sum()
        df['nhbo'] = df['nhbo'] * scalar

        # HBU ##################################################################
        df['hbu'] = ( c_hbu_iCbdPsfte * df['iCbdPsfte']
                    + c_hbu_iNotCbdPsfte * df['iNotCbdPsfte'] )*df['bowen_adj']

        # set control total for hbu in database and get productions to scale
        ct_df_hbu = pd.DataFrame(df['hbu'])
        ct_df_hbu = pd.DataFrame(ct_df_hbu.sum())
        ct_df_hbu.reset_index(inplace=True)
        ct_df_hbu.columns = ['purpose','control_total']

        conn = util.get_rtm_db(eb)
        ct_df_hbu.to_sql(name='TripsBalCts', con=conn, flavor='sqlite', index=False, if_exists='append')
        prd_df = pd.read_sql("SELECT * FROM TripsTazPrds", conn)
        conn.close()

        # scale home-based university productions
        scalar = df['hbu'].sum() / prd_df['hbu'].sum()
        prd_df['hbu'] = prd_df['hbu'] * scalar


        ########################################################################
        # Write out results to sqlite and EMMEbank
        ########################################################################

        # retain only taz index and trip columns
        df = df[['TAZ1741','hbw','hbu','hbesc','hbpb','hbsch','hbshop','hbsoc','nhbw','nhbo']]

        # Write to sqlite
        conn = util.get_rtm_db(eb)
        df.to_sql(name='TripsTazAtrs', con=conn, flavor='sqlite', index=False, if_exists='replace')
        prd_df.to_sql(name='TripsTazPrds', con=conn, flavor='sqlite', index=False, if_exists='replace')
        conn.close()



        # write to EMMEbank
        util.set_matrix_numpy(eb, 'mohbuprd', prd_df['hbu'].values)
        util.set_matrix_numpy(eb, 'mdhbuatr', df['hbu'].values)
        util.set_matrix_numpy(eb, 'mdhbwatr', df['hbw'].values)
        util.set_matrix_numpy(eb, 'mdhbescatr', df['hbesc'].values)
        util.set_matrix_numpy(eb, 'mdhbpbatr', df['hbpb'].values)
        util.set_matrix_numpy(eb, 'mdhbschatr', df['hbsch'].values)
        util.set_matrix_numpy(eb, 'mdhbshopatr', df['hbshop'].values)
        util.set_matrix_numpy(eb, 'mdhbsocatr', df['hbsoc'].values)
        util.set_matrix_numpy(eb, 'mdnhbwatr', df['nhbw'].values)
        util.set_matrix_numpy(eb, 'mdnhboatr', df['nhbo'].values)

    @_m.logbook_trace("Generate Dataframes for Trip Attractions")
    def Generate_Trip_Attractions_dfs(self, eb):
        util = _m.Modeller().tool("translink.util")

        taz_sql = """
            SELECT
                ti.TAZ1741
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
                ,IFNULL(d.POP_0to4 + d.POP_5to12 + d.POP_13to17, 0) as PopU18
                ,IFNULL(d.POP_65plus, 0) as POP_65plus
                ,IFNULL(d.POP_Total, 0) as POP_Total
                -- interaction term for escorting to the airport
                ,IFNULL(d.EMP_TCU_Wholesale * du.airport, 0) as iTWAir
                ,CASE WHEN IFNULL(du.cbd, 0) = 1 THEN IFNULL(PostSecFTE, 0) ELSE 0 END iCbdPsfte
                ,CASE WHEN IFNULL(du.cbd, 1) = 0 THEN IFNULL(PostSecFTE, 0) ELSE 0 END iNotCbdPsfte

            FROM taz_index ti
                LEFT JOIN demographics d on d.TAZ1700 = ti.TAZ1741
                LEFT JOIN accessibilities a on a.TAZ1741 = ti.TAZ1741
                LEFT JOIN dummies du on du.TAZ1700 = ti.TAZ1741


            ORDER BY
                ti.TAZ1741
        """
        conn = util.get_rtm_db(eb)
        taz_df = pd.read_sql(taz_sql, conn)
        ct_df = pd.read_sql('SELECT * FROM TripsBalCts', conn)
        conn.close()

        # reset index to allow grabbing scalar values by name
        ct_df.set_index('purpose', inplace=True)

        return taz_df, ct_df

    @_m.logbook_trace("Initialize Trip Attraction Matrices")
    def matrix_batchins(self, eb):
        util = _m.Modeller().tool("translink.util")
        util.initmat(eb, "md2000", "hbwatr", "hbw Attractions", 0)
        util.initmat(eb, "md2010", "hbescatr", "hbesc Attractions", 0)
        util.initmat(eb, "md2020", "hbpbatr", "hbpb Attractions", 0)
        util.initmat(eb, "md2030", "hbschatr", "hbsch Attractions", 0)
        util.initmat(eb, "md2040", "hbshopatr", "hbshop Attractions", 0)
        util.initmat(eb, "md2050", "hbsocatr", "hbsoc Attractions", 0)
        util.initmat(eb, "md2060", "hbuatr", "hbu Attractions", 0)
        util.initmat(eb, "md2070", "nhbwatr", "nhbw Attractions", 0)
        util.initmat(eb, "md2080", "nhboatr", "nhbo Attractions", 0)

        # initialize md2031 - md2032 for school trip attraction adjustment
        util.initmat(eb, "md2031", "hbschprgx", "hbsch Production Sum by GX", 0)
        util.initmat(eb, "md2032", "hbschsc", "hbsch Attraction by GX", 0)
