##---------------------------------------------------------------------
##--TransLink Regional Transportation Model
##--
##--Path:
##--Purpose: Output data after run
##---------------------------------------------------------------------
import inro.modeller as _m
import inro.emme.desktop as _d
import traceback as _traceback

import os
import re
import csv as csv

import sqlite3
import pandas as pd
import numpy as np



class DataExport(_m.Tool()):

    export_csvs = _m.Attribute(bool)
    tool_run_msg = _m.Attribute(unicode)


    def __init__(self):
        self.export_csvs = True




    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Export Data from Model Run"
        pb.description = "Exports Results of Model Run"
        pb.branding_text = "TransLink"

        with pb.section("Export Format Options"):
            pb.add_checkbox("export_csvs", label="Export CSVs to Output Folder")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            eb = _m.Modeller().emmebank
            self.__call__(eb)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))


    @_m.logbook_trace("Data Export")
    def __call__(self, eb):
        util = _m.Modeller().tool("translink.util")
        model_year = int(util.get_year(eb))
        am_scen = eb.scenario(int(eb.matrix("ms2").data))
        md_scen = eb.scenario(int(eb.matrix("ms3").data))
        pm_scen = eb.scenario(int(eb.matrix("ms4").data))

        # add trip summary views
        self.addViewDailyModeSharebyPurp(eb)
        self.addViewDailyModeShare(eb)

        # aggreagate network stats
        amDf = self.aggNetDf(am_scen, 'AM')
        mdDf = self.aggNetDf(md_scen, 'MD')
        pmDf = self.aggNetDf(pm_scen, 'PM')
        df = amDf.append(mdDf).append(pmDf)

        conn = util.get_db_byname(eb, "trip_summaries.db")
        df.to_sql(name='aggregateNetResults', con=conn, flavor='sqlite', index=False, if_exists='replace')
        conn.close()

        # average travel time by mode
        transitDf = self.calc_transit_tt(eb)
        autoDf = self.calc_auto_tt(eb)
        df = transitDf.append(autoDf)

        conn = util.get_db_byname(eb, "trip_summaries.db")
        df.to_sql(name='avgTravelTimes', con=conn, flavor='sqlite', index=False, if_exists='replace')
        conn.close()

        # trip generation
        p, a = self.prdsAtrs(eb)
        df = p.append(a)

        conn = util.get_db_byname(eb, "trip_summaries.db")
        df.to_sql(name='tripGeneration', con=conn, flavor='sqlite', index=False, if_exists='replace')
        conn.close()

        # auto network outputs
        dfAuto, dfTransit = self.networkExport(eb)
        conn = util.get_db_byname(eb, 'trip_summaries.db')
    	dfAuto.to_sql(name='netResults', con=conn, flavor='sqlite', index=False, if_exists='replace')
    	dfTransit.to_sql(name='transitResults', con=conn, flavor='sqlite', index=False, if_exists='replace')
    	conn.close()

        self.autoStats(eb)
        if True:
            self.addViewBridgeXings(eb)

        # runs last
        if self.export_csvs:
            self.export_text(eb)




    def export_text(self, eb):
        util = _m.Modeller().tool("translink.util")
        output_loc = util.get_output_path(eb)

        conn = util.get_db_byname(eb, "trip_summaries.db")
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type in ('table', 'view');")
        tabs = c.fetchall()

        for table in tabs:
            ot = table[0]
            sql = "SELECT * FROM {}".format(ot)
            df = pd.read_sql(sql, conn)
            fn = os.path.join(output_loc, '{}.csv'.format(ot))
            df.to_csv(fn, index=False)

        conn.close()

    def autoStats(self, eb):
        util = _m.Modeller().tool("translink.util")
        aonDist = util.get_matrix_numpy(eb, "mfdistAON").flatten()
        df = util.get_ijensem_df(eb, 'gy','gy')

        df['amSovDemand1'] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_1_Am").flatten()
        df['amSovDemand2'] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_2_Am").flatten()
        df['amSovDemand3'] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_3_Am").flatten()
        df['amSovDemand4'] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_4_Am").flatten()

        df['mdSovDemand1'] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_1_Md").flatten()
        df['mdSovDemand2'] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_2_Md").flatten()
        df['mdSovDemand3'] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_3_Md").flatten()
        df['mdSovDemand4'] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_4_Md").flatten()

        df['pmSovDemand1'] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_1_Pm").flatten()
        df['pmSovDemand2'] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_2_Pm").flatten()
        df['pmSovDemand3'] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_3_Pm").flatten()
        df['pmSovDemand4'] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_4_Pm").flatten()


        df['amHovDemand1'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_1_Am").flatten()
        df['amHovDemand2'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_2_Am").flatten()
        df['amHovDemand3'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_3_Am").flatten()
        df['amHovDemand4'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_4_Am").flatten()

        df['mdHovDemand1'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_1_Md").flatten()
        df['mdHovDemand2'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_2_Md").flatten()
        df['mdHovDemand3'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_3_Md").flatten()
        df['mdHovDemand4'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_4_Md").flatten()

        df['pmHovDemand1'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_1_Pm").flatten()
        df['pmHovDemand2'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_2_Pm").flatten()
        df['pmHovDemand3'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_3_Pm").flatten()
        df['pmHovDemand4'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_4_Pm").flatten()
        
        df['amLGVDemand1'] = util.get_matrix_numpy(eb, "mfLGVAM").flatten()
        df['amHGVDemand1'] = util.get_matrix_numpy(eb, "mfHGVAM").flatten()
        df['mdLGVDemand1'] = util.get_matrix_numpy(eb, "mfLGVMD").flatten()
        df['mdHGVDemand1'] = util.get_matrix_numpy(eb, "mfHGVMD").flatten()
        df['pmLGVDemand1'] = util.get_matrix_numpy(eb, "mfLGVPM").flatten()
        df['pmHGVDemand1'] = util.get_matrix_numpy(eb, "mfHGVPM").flatten()

        # create copy of trips and multiply by distance to get simple vkt
        df2 = df.drop(['gy_i','gy_j'], 1).mul(aonDist, axis = 0)
        df2.rename(columns= lambda x: re.sub('Demand', 'Vkt', x), inplace=True)
        # need to bring back ij refs for group by
        df2 = pd.concat([util.get_ijensem_df(eb, 'gy','gy'),df2], axis=1)
        df2 = pd.melt(df2, id_vars = ['gy_i','gy_j'], var_name = 'timeModeVot', value_name='vkt')
        df2Gy =  df2.groupby(['gy_i','gy_j','timeModeVot'])
        df2Gy = df2Gy.sum().reset_index()

        df = pd.melt(df, id_vars = ['gy_i','gy_j'], var_name = 'timeModeVot', value_name = 'trips')
        dfGy = df.groupby(['gy_i','gy_j','timeModeVot'])
        dfGy = dfGy.sum().reset_index()

        # extract toll data
        dfToll = util.get_ijensem_df(eb, 'gy','gy')
        dfToll['amSovToll1'] = util.get_matrix_numpy(eb, "mfAmSovTollVOT1").flatten() * util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_1_Am").flatten()
        dfToll['amSovToll2'] = util.get_matrix_numpy(eb, "mfAmSovTollVOT2").flatten() * util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_2_Am").flatten()
        dfToll['amSovToll3'] = util.get_matrix_numpy(eb, "mfAmSovTollVOT3").flatten() * util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_3_Am").flatten()
        dfToll['amSovToll4'] = util.get_matrix_numpy(eb, "mfAmSovTollVOT4").flatten() * util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_4_Am").flatten()

        dfToll['mdSovToll1'] = util.get_matrix_numpy(eb, "mfMdSovTollVOT1").flatten() * util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_1_Md").flatten()
        dfToll['mdSovToll2'] = util.get_matrix_numpy(eb, "mfMdSovTollVOT2").flatten() * util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_2_Md").flatten()
        dfToll['mdSovToll3'] = util.get_matrix_numpy(eb, "mfMdSovTollVOT3").flatten() * util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_3_Md").flatten()
        dfToll['mdSovToll4'] = util.get_matrix_numpy(eb, "mfMdSovTollVOT4").flatten() * util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_4_Md").flatten()

        dfToll['pmSovToll1'] = util.get_matrix_numpy(eb, "mfPmSovTollVOT1").flatten() * util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_1_Pm").flatten()
        dfToll['pmSovToll2'] = util.get_matrix_numpy(eb, "mfPmSovTollVOT2").flatten() * util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_2_Pm").flatten()
        dfToll['pmSovToll3'] = util.get_matrix_numpy(eb, "mfPmSovTollVOT3").flatten() * util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_3_Pm").flatten()
        dfToll['pmSovToll4'] = util.get_matrix_numpy(eb, "mfPmSovTollVOT4").flatten() * util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_4_Pm").flatten()

        dfToll['amHovToll1'] = util.get_matrix_numpy(eb, "mfAmHovTollVOT1").flatten() * util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_1_Am").flatten()
        dfToll['amHovToll2'] = util.get_matrix_numpy(eb, "mfAmHovTollVOT2").flatten() * util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_2_Am").flatten()
        dfToll['amHovToll3'] = util.get_matrix_numpy(eb, "mfAmHovTollVOT3").flatten() * util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_3_Am").flatten()
        dfToll['amHovToll4'] = util.get_matrix_numpy(eb, "mfAmHovTollVOT4").flatten() * util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_4_Am").flatten()

        dfToll['mdHovToll1'] = util.get_matrix_numpy(eb, "mfMdHovTollVOT1").flatten() * util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_1_Md").flatten()
        dfToll['mdHovToll2'] = util.get_matrix_numpy(eb, "mfMdHovTollVOT2").flatten() * util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_2_Md").flatten()
        dfToll['mdHovToll3'] = util.get_matrix_numpy(eb, "mfMdHovTollVOT3").flatten() * util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_3_Md").flatten()
        dfToll['mdHovToll4'] = util.get_matrix_numpy(eb, "mfMdHovTollVOT4").flatten() * util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_4_Md").flatten()

        dfToll['pmHovToll1'] = util.get_matrix_numpy(eb, "mfPmHovTollVOT1").flatten() * util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_1_Pm").flatten()
        dfToll['pmHovToll2'] = util.get_matrix_numpy(eb, "mfPmHovTollVOT2").flatten() * util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_2_Pm").flatten()
        dfToll['pmHovToll3'] = util.get_matrix_numpy(eb, "mfPmHovTollVOT3").flatten() * util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_3_Pm").flatten()
        dfToll['pmHovToll4'] = util.get_matrix_numpy(eb, "mfPmHovTollVOT4").flatten() * util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_4_Pm").flatten()
        
        dfToll['amLGVToll1'] = util.get_matrix_numpy(eb, "mfAmLgvToll").flatten() * util.get_matrix_numpy(eb, "mfLGVAM").flatten()
        dfToll['amHGVToll1'] = util.get_matrix_numpy(eb, "mfAmHgvToll").flatten() * util.get_matrix_numpy(eb, "mfHGVAM").flatten()
        dfToll['mdLGVToll1'] = util.get_matrix_numpy(eb, "mfMdLgvToll").flatten() * util.get_matrix_numpy(eb, "mfLGVMD").flatten()
        dfToll['mdHGVToll1'] = util.get_matrix_numpy(eb, "mfMdHgvToll").flatten() * util.get_matrix_numpy(eb, "mfHGVMD").flatten()
        dfToll['pmLGVToll1'] = util.get_matrix_numpy(eb, "mfPmLgvToll").flatten() * util.get_matrix_numpy(eb, "mfLGVPM").flatten()
        dfToll['pmHGVToll1'] = util.get_matrix_numpy(eb, "mfPmHgvToll").flatten() * util.get_matrix_numpy(eb, "mfHGVPM").flatten()



        dfToll = pd.melt(dfToll, id_vars = ['gy_i','gy_j'], var_name = 'timeModeVot', value_name = 'tolls')
        dfTollGy = dfToll.groupby(['gy_i','gy_j','timeModeVot'])
        dfTollGy = dfTollGy.sum().reset_index()


        # create categorical fields from original colnames
        dfTimeModeVot = dfGy['timeModeVot'].str.extract(r'(?P<peak>[a|m|p]{1}[m|d])(?P<mode>Sov|Hov|LGV|HGV)Demand(?P<votclass>\d)')
        dfTimeModeVotT = dfTollGy['timeModeVot'].str.extract(r'(?P<peak>[a|m|p]{1}[m|d])(?P<mode>Sov|Hov|LGV|HGV)Toll(?P<votclass>\d)')

        dfGy = pd.concat([dfGy,dfTimeModeVot], axis=1)
        dfGy = dfGy[['gy_i','gy_j','peak','mode','votclass','trips']]

        df2Gy = pd.concat([df2Gy,dfTimeModeVot], axis=1)
        df2Gy = df2Gy[['gy_i','gy_j','peak','mode','votclass','vkt']]

        dfTollGy = pd.concat([dfTollGy,dfTimeModeVotT], axis=1)
        dfTollGy = dfTollGy[['gy_i','gy_j','peak','mode','votclass','tolls']]

        conn = util.get_db_byname(eb, 'trip_summaries.db')
        dfGy.to_sql(name='autoTripsGy', con=conn, flavor='sqlite', index=False, if_exists='replace')
        df2Gy.to_sql(name='autoVktGy', con=conn, flavor='sqlite', index=False, if_exists='replace')
        dfTollGy.to_sql(name='autoTollGy', con=conn, flavor='sqlite', index=False, if_exists='replace')
        conn.close()

    def addViewBridgeXings(self, eb):
        util = _m.Modeller().tool("translink.util")

        conn = util.get_db_byname(eb, "trip_summaries.db")
        c = conn.cursor()

        c.execute("DROP VIEW IF EXISTS vBridgeXings;")
        conn.commit()

        create_view = """
            CREATE VIEW vBridgeXings AS
            SELECT
                nd.Bridge_Name
               ,nd.peakperiod
               ,sum(nd.Tot_Auto_Vol) as Auto
               ,sum(nd.Tot_Tran_Vol) as Transit

            FROM (
                    SELECT
                         i
                        ,j
                        ,peakperiod
                        ,CASE
                             WHEN i = 541808 and j in (541023, 532112) then "Massey"
                             WHEN i in (532111,541024) and j = 541801 then "Massey"
                             WHEN i = 541806 and j = 532112 then "Massey"

                             WHEN i = 541005 or j = 541004  then "Alex_Fraser"

                             WHEN i = 610905 and j = 292013 then "Pattullo"
                             WHEN i = 292604 and j = 610903 then "Pattullo"

                             WHEN i = 611310 and j = 292618 then "Pattullo"
                             WHEN i = 292617 and j = 611309 then "Pattullo"

                             WHEN i = 611407 and j = 292613 then "Sky_Bridge"
                             WHEN i = 292613 and j = 611407 then "Sky_Bridge"

                             WHEN i = 630207 and j = 326317 then "Port_Mann"
                             WHEN i = 630103 and j = 326315 then "Port_Mann"
                             WHEN i = 630104 and j = 325807 then "Port_Mann"
                             WHEN i = 326413 and j = 630705 then "Port_Mann"
                             WHEN i = 326410 and j = 630704 then "Port_Mann"
                             WHEN i = 326411 and j = 610804 then "Port_Mann"

                             WHEN i = 680401 or j = 680302 then "GEB"

                             ELSE "Other"
                             END Bridge_Name

                        ,ROUND(SOV+HOV+Light_Trucks+Heavy_Trucks+Transit_Vehicles) as Tot_Auto_Vol
                        ,ROUND(Transit_Volume) as Tot_Tran_Vol

                FROM netResults
            ) nd

            WHERE 1=1
                and Bridge_Name != 'Other'

            GROUP BY
                nd.Bridge_Name
               ,nd.peakperiod

            """

        c = conn.cursor()
        c.execute(create_view)
        conn.commit()
        conn.close()

    def addViewDailyModeSharebyPurp(self, eb):
        util = _m.Modeller().tool("translink.util")

        conn = util.get_db_byname(eb, "trip_summaries.db")
        c = conn.cursor()

        c.execute("DROP VIEW IF EXISTS vModeShareDailyPurpose;")
        conn.commit()

        create_view = """
            CREATE VIEW vModeShareDailyPurpose AS
            SELECT
                m.purpose
                ,m.mode
                ,m.totPurpMode / p.totPurp AS share

            FROM
               (SELECT
                    purpose
                    ,mode
                    ,SUM(trips) as totPurpMode
                FROM daily_gy
                GROUP BY
                    purpose
                    ,mode) m

            LEFT JOIN
                (SELECT
                    purpose
                    ,SUM(trips) as totPurp
                FROM daily_gy
                GROUP BY purpose) p on p.purpose = m.purpose

            """

        c = conn.cursor()
        c.execute(create_view)
        conn.commit()
        conn.close()

    def addViewDailyModeShare(self, eb):
        util = _m.Modeller().tool("translink.util")

        conn = util.get_db_byname(eb, "trip_summaries.db")
        c = conn.cursor()

        c.execute("DROP VIEW IF EXISTS vModeShareDaily;")
        conn.commit()

        create_view = """
            CREATE VIEW vModeShareDaily AS
            SELECT
                m.mode
                ,m.totMode / p.totTrips AS share

            FROM
               (SELECT
                    mode
                    ,SUM(trips) as totMode
                FROM daily_gy
                GROUP BY
                    mode) m

            LEFT JOIN
                (SELECT
                    SUM(trips) as totTrips
                FROM daily_gy) p

            """

        c = conn.cursor()
        c.execute(create_view)
        conn.commit()
        conn.close()

    def aggNetDf(self, scen, peak):
        util = _m.Modeller().tool("translink.util")
        sel = "ci=0 and cj=0" # do not include centroid connectors
        totVol = "(@wsovl+@whovl+@lgvol/1.5+@hgvol/2.5+volad/2.5)"
        eVkt = "{totVol}*length".format(totVol=totVol)
        eVht = "{totVol}*timau/60".format(totVol=totVol)

        vkt = util.emme_link_calc(scen, None, eVkt, sel_link = sel)['sum']
        vht = rep = util.emme_link_calc(scen, None, eVht, sel_link = sel)['sum']
        avgSpeed = vkt/vht

        df = pd.DataFrame({'measure' : ['vkt','vht','avgSpeed'],
                            'value' : [vkt,vht,avgSpeed]})
        df['period'] = peak
        df['mode'] = 'auto'
        df = df[['period','mode','measure','value']]
        return df

    def calc_transit_tt(self, eb):
        util = _m.Modeller().tool("translink.util")

        aonDist = util.get_matrix_numpy(eb, "mfdistAON").flatten()

        # get bus skims
        AmBusIvtt = util.get_matrix_numpy(eb, 'mfAmBusIvtt').flatten()
        AmBusWait = util.get_matrix_numpy(eb, 'mfAmBusWait').flatten()
        AmBusAux = util.get_matrix_numpy(eb, 'mfAmBusAux').flatten()

        MdBusIvtt = util.get_matrix_numpy(eb, 'mfMdBusIvtt').flatten()
        MdBusWait = util.get_matrix_numpy(eb, 'mfMdBusWait').flatten()
        MdBusAux = util.get_matrix_numpy(eb, 'mfMdBusAux').flatten()

        PmBusIvtt = util.get_matrix_numpy(eb, 'mfPmBusIvtt').flatten()
        PmBusWait = util.get_matrix_numpy(eb, 'mfPmBusWait').flatten()
        PmBusAux = util.get_matrix_numpy(eb, 'mfPmBusAux').flatten()

        # get rail skims
        AmRailIvtt = util.get_matrix_numpy(eb, 'mfAmRailIvtt').flatten()
        AmRailIvttBus = util.get_matrix_numpy(eb, 'mfAmRailIvttBus').flatten()
        AmRailWait = util.get_matrix_numpy(eb, 'mfAmRailWait').flatten()
        AmRailAux = util.get_matrix_numpy(eb, 'mfAmRailAux').flatten()

        MdRailIvtt = util.get_matrix_numpy(eb, 'mfMdRailIvtt').flatten()
        MdRailIvttBus = util.get_matrix_numpy(eb, 'mfMdRailIvttBus').flatten()
        MdRailWait = util.get_matrix_numpy(eb, 'mfMdRailWait').flatten()
        MdRailAux = util.get_matrix_numpy(eb, 'mfMdRailAux').flatten()

        PmRailIvtt = util.get_matrix_numpy(eb, 'mfPmRailIvtt').flatten()
        PmRailIvttBus = util.get_matrix_numpy(eb, 'mfPmRailIvttBus').flatten()
        PmRailWait = util.get_matrix_numpy(eb, 'mfPmRailWait').flatten()
        PmRailAux = util.get_matrix_numpy(eb, 'mfPmRailAux').flatten()

        # get Wce Skims
        AmWceIvtt = util.get_matrix_numpy(eb, 'mfAmWceIvtt').flatten()
        AmWceIvttRail = util.get_matrix_numpy(eb, 'mfAmWceIvttRail').flatten()
        AmWceIvttBus = util.get_matrix_numpy(eb, 'mfAmWceIvttBus').flatten()
        AmWceWait = util.get_matrix_numpy(eb, 'mfAmWceWait').flatten()
        AmWceAux = util.get_matrix_numpy(eb, 'mfAmWceAux').flatten()

        PmWceIvtt = util.get_matrix_numpy(eb, 'mfPmWceIvtt').flatten()
        PmWceIvttRail = util.get_matrix_numpy(eb, 'mfPmWceIvttRail').flatten()
        PmWceIvttBus = util.get_matrix_numpy(eb, 'mfPmWceIvttBus').flatten()
        PmWceWait = util.get_matrix_numpy(eb, 'mfPmWceWait').flatten()
        PmWceAux = util.get_matrix_numpy(eb, 'mfPmWceAux').flatten()


        AmBusTime = AmBusIvtt + AmBusWait + AmBusAux
        MdBusTime = MdBusIvtt + MdBusWait + MdBusAux
        PmBusTime = PmBusIvtt + PmBusWait + PmBusAux

        AmRailTime = AmRailIvtt + AmRailWait + AmRailAux + AmRailIvttBus
        MdRailTime = MdRailIvtt + MdRailWait + MdRailAux + MdRailIvttBus
        PmRailTime = PmRailIvtt + PmRailWait + PmRailAux + PmRailIvttBus

        AmWceTime = AmWceIvtt + AmWceWait + AmWceAux + AmWceIvttBus + AmWceIvttRail
        PmWceTime = PmWceIvtt + PmWceWait + PmWceAux + PmWceIvttBus + PmWceIvttRail

        # demand
        demand_bus_am = util.get_matrix_numpy(eb, "mfbusAm").flatten()
        demand_bus_md = util.get_matrix_numpy(eb, "mfbusMd").flatten()
        demand_bus_pm = util.get_matrix_numpy(eb, "mfbusPm").flatten()

        demand_rail_am = util.get_matrix_numpy(eb, "mfrailAm").flatten()
        demand_rail_md = util.get_matrix_numpy(eb, "mfrailMd").flatten()
        demand_rail_pm = util.get_matrix_numpy(eb, "mfrailPm").flatten()

        demand_wce_am = util.get_matrix_numpy(eb, "mfWCEAm").flatten()
        demand_wce_pm = util.get_matrix_numpy(eb, "mfWCEPm").flatten()

        # travel times
        avgTtBusAm = (AmBusTime * demand_bus_am).sum() / demand_bus_am.sum()
        avgTtBusMd = (MdBusTime * demand_bus_md).sum() / demand_bus_md.sum()
        avgTtBusPm = (PmBusTime * demand_bus_pm).sum() / demand_bus_pm.sum()

        avgTtRailAm = (AmRailTime * demand_rail_am).sum() / demand_rail_am.sum()
        avgTtRailMd = (MdRailTime * demand_rail_md).sum() / demand_rail_md.sum()
        avgTtRailPm = (PmRailTime * demand_rail_pm).sum() / demand_rail_pm.sum()

        avgTtWceAm = (AmWceTime * demand_wce_am).sum() / demand_wce_am.sum()
        avgTtWcePm = (PmWceTime * demand_wce_pm).sum() / demand_wce_pm.sum()

        # travel lengths
        avgTlBusAm = (aonDist * demand_bus_am).sum() / demand_bus_am.sum()
        avgTlBusMd = (aonDist * demand_bus_md).sum() / demand_bus_md.sum()
        avgTlBusPm = (aonDist * demand_bus_pm).sum() / demand_bus_pm.sum()

        avgTlRailAm = (aonDist * demand_rail_am).sum() / demand_rail_am.sum()
        avgTlRailMd = (aonDist * demand_rail_md).sum() / demand_rail_md.sum()
        avgTlRailPm = (aonDist * demand_rail_pm).sum() / demand_rail_pm.sum()

        avgTlWceAm = (aonDist * demand_wce_am).sum() / demand_wce_am.sum()
        avgTlWcePm = (aonDist * demand_wce_pm).sum() / demand_wce_pm.sum()

        # build dataframe
        df1 = pd.DataFrame({'period' : ['AM','MD','PM', 'AM','MD','PM', 'AM','PM'],
              'mode' : ['bus','bus','bus','rail','rail','rail','wce','wce'],
              'measure': ['mins','mins','mins','mins','mins','mins','mins','mins'],
              'value': [avgTtBusAm, avgTtBusMd, avgTtBusPm, avgTtRailAm, avgTtRailMd, avgTtRailPm, avgTtWceAm, avgTtWcePm]})

        df2 = pd.DataFrame({'period' : ['AM','MD','PM', 'AM','MD','PM', 'AM','PM'],
              'mode' : ['bus','bus','bus','rail','rail','rail','wce','wce'],
              'measure': ['kms','kms','kms','kms','kms','kms','kms','kms'],
              'value': [avgTlBusAm, avgTlBusMd, avgTlBusPm, avgTlRailAm, avgTlRailMd, avgTlRailPm, avgTlWceAm, avgTlWcePm]})

        df = df1.append(df2)

        df = df[['period','mode','measure','value']]
        return df

    def calc_auto_tt(self, eb):
        util = _m.Modeller().tool("translink.util")

        aonDist = util.get_matrix_numpy(eb, "mfdistAON").flatten()

        #am
        amSovTime1 = util.get_matrix_numpy(eb, "mfAmSovTimeVOT1").flatten()
        amSovTime2 = util.get_matrix_numpy(eb, "mfAmSovTimeVOT2").flatten()
        amSovTime3 = util.get_matrix_numpy(eb, "mfAmSovTimeVOT3").flatten()
        amSovTime4 = util.get_matrix_numpy(eb, "mfAmSovTimeVOT4").flatten()

        amSovDemand1 = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_1_Am").flatten()
        amSovDemand2 = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_2_Am").flatten()
        amSovDemand3 = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_3_Am").flatten()
        amSovDemand4 = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_4_Am").flatten()

        # calculate average travel time
        amSovDemandTot = amSovDemand1 + amSovDemand2 + amSovDemand3 + amSovDemand4
        amSovTotTime = amSovTime1 * amSovDemand1 + amSovTime2 * amSovDemand2 + amSovTime3 * amSovDemand3 + amSovTime4 * amSovDemand4
        avgTtSovAm = amSovTotTime.sum() / amSovDemandTot.sum()

        # calculate average trip Length
        amSovTotDist = aonDist * amSovDemandTot
        avgTlSovAm = amSovTotDist.sum() / amSovDemandTot.sum()

        # md
        mdSovTime1 = util.get_matrix_numpy(eb, "mfMdSovTimeVOT1").flatten()
        mdSovTime2 = util.get_matrix_numpy(eb, "mfMdSovTimeVOT2").flatten()
        mdSovTime3 = util.get_matrix_numpy(eb, "mfMdSovTimeVOT3").flatten()
        mdSovTime4 = util.get_matrix_numpy(eb, "mfMdSovTimeVOT4").flatten()

        mdSovDemand1 = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_1_Md").flatten()
        mdSovDemand2 = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_2_Md").flatten()
        mdSovDemand3 = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_3_Md").flatten()
        mdSovDemand4 = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_4_Md").flatten()

        # calculate average travel time
        mdSovDemandTot = mdSovDemand1 + mdSovDemand2 + mdSovDemand3 + mdSovDemand4
        mdSovTotTime = mdSovTime1 * mdSovDemand1 + mdSovTime2 * mdSovDemand2 + mdSovTime3 * mdSovDemand3 + mdSovTime4 * mdSovDemand4
        avgTtSovMd = mdSovTotTime.sum() / mdSovDemandTot.sum()

        # calculate average trip Length
        mdSovTotDist = aonDist * mdSovDemandTot
        avgTlSovMd = mdSovTotDist.sum() / mdSovDemandTot.sum()


        #pm
        pmSovTime1 = util.get_matrix_numpy(eb, "mfPmSovTimeVOT1").flatten()
        pmSovTime2 = util.get_matrix_numpy(eb, "mfPmSovTimeVOT2").flatten()
        pmSovTime3 = util.get_matrix_numpy(eb, "mfPmSovTimeVOT3").flatten()
        pmSovTime4 = util.get_matrix_numpy(eb, "mfPmSovTimeVOT4").flatten()

        pmSovDemand1 = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_1_Pm").flatten()
        pmSovDemand2 = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_2_Pm").flatten()
        pmSovDemand3 = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_3_Pm").flatten()
        pmSovDemand4 = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_4_Pm").flatten()

		# calculate average travel time
        pmSovDemandTot = pmSovDemand1 + pmSovDemand2 + pmSovDemand3 + pmSovDemand4
        pmSovTotTime = pmSovTime1 * pmSovDemand1 + pmSovTime2 * pmSovDemand2 + pmSovTime3 * pmSovDemand3 + pmSovTime4 * pmSovDemand4
        avgTtSovPm = pmSovTotTime.sum() / pmSovDemandTot.sum()

        # calculate average trip Length
        pmSovTotDist = aonDist * pmSovDemandTot
        avgTlSovPm = pmSovTotDist.sum() / pmSovDemandTot.sum()

        #am
        amHovTime1 = util.get_matrix_numpy(eb, "mfAmHovTimeVOT1").flatten()
        amHovTime2 = util.get_matrix_numpy(eb, "mfAmHovTimeVOT2").flatten()
        amHovTime3 = util.get_matrix_numpy(eb, "mfAmHovTimeVOT3").flatten()
        amHovTime4 = util.get_matrix_numpy(eb, "mfAmHovTimeVOT4").flatten()

        amHovDemand1 = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_1_Am").flatten()
        amHovDemand2 = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_2_Am").flatten()
        amHovDemand3 = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_3_Am").flatten()
        amHovDemand4 = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_4_Am").flatten()

        # calculate average travel time
        amHovDemandTot = amHovDemand1 + amHovDemand2 + amHovDemand3 + amHovDemand4
        amHovTotTime = amHovTime1 * amHovDemand1 + amHovTime2 * amHovDemand2 + amHovTime3 * amHovDemand3 + amHovTime4 * amHovDemand4
        avgTtHovAm = amHovTotTime.sum() / amHovDemandTot.sum()

        # calculate average trip Length
        amHovTotDist = aonDist * amHovDemandTot
        avgTlHovAm = amHovTotDist.sum() / amHovDemandTot.sum()

        # md
        mdHovTime1 = util.get_matrix_numpy(eb, "mfMdHovTimeVOT1").flatten()
        mdHovTime2 = util.get_matrix_numpy(eb, "mfMdHovTimeVOT2").flatten()
        mdHovTime3 = util.get_matrix_numpy(eb, "mfMdHovTimeVOT3").flatten()
        mdHovTime4 = util.get_matrix_numpy(eb, "mfMdHovTimeVOT4").flatten()

        mdHovDemand1 = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_1_Md").flatten()
        mdHovDemand2 = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_2_Md").flatten()
        mdHovDemand3 = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_3_Md").flatten()
        mdHovDemand4 = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_4_Md").flatten()

		# calculate average travel time
        mdHovDemandTot = mdHovDemand1 + mdHovDemand2 + mdHovDemand3 + mdHovDemand4
        mdHovTotTime = mdHovTime1 * mdHovDemand1 + mdHovTime2 * mdHovDemand2 + mdHovTime3 * mdHovDemand3 + mdHovTime4 * mdHovDemand4
        avgTtHovMd = mdHovTotTime.sum() / mdHovDemandTot.sum()

        # calculate average trip Length
        mdHovTotDist = aonDist * mdHovDemandTot
        avgTlHovMd = mdHovTotDist.sum() / mdHovDemandTot.sum()

        #pm
        pmHovTime1 = util.get_matrix_numpy(eb, "mfPmHovTimeVOT1").flatten()
        pmHovTime2 = util.get_matrix_numpy(eb, "mfPmHovTimeVOT2").flatten()
        pmHovTime3 = util.get_matrix_numpy(eb, "mfPmHovTimeVOT3").flatten()
        pmHovTime4 = util.get_matrix_numpy(eb, "mfPmHovTimeVOT4").flatten()

        pmHovDemand1 = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_1_Pm").flatten()
        pmHovDemand2 = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_2_Pm").flatten()
        pmHovDemand3 = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_3_Pm").flatten()
        pmHovDemand4 = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_4_Pm").flatten()

		# calculate average travel time
        pmHovDemandTot = pmHovDemand1 + pmHovDemand2 + pmHovDemand3 + pmHovDemand4
        pmHovTotTime = pmHovTime1 * pmHovDemand1 + pmHovTime2 * pmHovDemand2 + pmHovTime3 * pmHovDemand3 + pmHovTime4 * pmHovDemand4
        avgTtHovPm = pmHovTotTime.sum() / pmHovDemandTot.sum()

        # calculate average trip Length
        pmHovTotDist = aonDist * pmHovDemandTot
        avgTlHovPm = pmHovTotDist.sum() / pmHovDemandTot.sum()

        df1 = pd.DataFrame({'period' : ['AM','MD','PM', 'AM','MD','PM'],
              'mode' : ['sov','sov','sov','hov','hov','hov'],
              'measure': ['mins','mins','mins','mins','mins','mins'],
              'value': [avgTtSovAm, avgTtSovMd, avgTtSovPm, avgTtHovAm, avgTtHovMd, avgTtHovPm]})

        df2 = pd.DataFrame({'period' : ['AM','MD','PM', 'AM','MD','PM'],
              'mode' : ['sov','sov','sov','hov','hov','hov'],
              'measure': ['kms','kms','kms','kms','kms','kms'],
              'value': [avgTlSovAm, avgTlSovMd, avgTlSovPm, avgTlHovAm, avgTlHovMd, avgTlHovPm]})

        df = df1.append(df2)

        df = df[['period','mode','measure','value']]
        return df

    def prdsAtrs(self, eb):
        util = _m.Modeller().tool("translink.util")

        psql = """
        SELECT
        h.*
        ,t.hbu
        ,t.nhbw
        ,t.nhbo

        FROM
              (SELECT
                e.gy
                ,SUM(tph.hbw) as hbw
                ,SUM(tph.hbesc) as hbesc
                ,SUM(tph.hbpb) as hbpb
                ,SUM(tph.hbsch) as hbsch
                ,SUM(tph.hbshop) as hbshop
                ,SUM(tph.hbsoc) as hbsoc

              FROM TripsHhPrds tph
                LEFT JOIN ensembles e on e.TAZ1700 = tph.TAZ1741

              WHERE 1=1
                and tph.TAZ1741 > 1000

              GROUP BY
                e.gy ) h

        LEFT JOIN
                  (SELECT
                    ee.gy
                    ,SUM(tpt.hbu) as hbu
                    ,SUM(tpt.nhbw) as nhbw
                    ,SUM(tpt.nhbo) as nhbo

                  FROM TripsTazPrds tpt
                    LEFT JOIN ensembles ee on ee.TAZ1700 = tpt.TAZ1741

                  WHERE 1=1
                    and tpt.TAZ1741 > 1000

                  GROUP BY
                    ee.gy) t on t.gy = h.gy
        """

        asql = """
        SELECT
            e.gy
            ,SUM(tat.hbw) as hbw
            ,SUM(tat.hbesc) as hbesc
            ,SUM(tat.hbpb) as hbpb
            ,SUM(tat.hbsch) as hbsch
            ,SUM(tat.hbshop) as hbshop
            ,SUM(tat.hbsoc) as hbsoc
            ,SUM(tat.hbu) as hbu
            ,SUM(tat.nhbw) as nhbw
            ,SUM(tat.nhbo) as nhbo

            FROM TripsTazAtrs tat
                LEFT JOIN ensembles e on e.TAZ1700 = tat.TAZ1741

            WHERE 1=1
                and tat.TAZ1741 > 1000

            GROUP BY
                e.gy
        """
        conn = util.get_rtm_db(eb)

        prDf = pd.read_sql_query(psql, conn)
        prDf = pd.melt(prDf, id_vars = ['gy'], var_name='purpose', value_name='trips')
        prDf['type'] = 'productions'
        prDf = prDf[['gy','type','purpose','trips']]

        arDf = pd.read_sql(asql, conn)
        arDf = pd.melt(arDf, id_vars = ['gy'], var_name='purpose', value_name='trips')
        arDf['type'] = 'attractions'
        arDf = arDf[['gy','type','purpose','trips']]

        conn.close()

        return prDf, arDf

    def networkExport(self, eb):
    	util = _m.Modeller().tool("translink.util")

    	am_scenid = int(eb.matrix("msAmScen").data)
    	md_scenid = int(eb.matrix("msMdScen").data)
    	pm_scenid = int(eb.matrix("msPmScen").data)

    	# get auto and transit data out of eb
    	dfAm = self.get_auto_data(eb, am_scenid)
    	dfMd = self.get_auto_data(eb, md_scenid)
    	dfPm = self.get_auto_data(eb, pm_scenid)

    	dfAmT = self.get_transit_data(eb, am_scenid)
    	dfMdT = self.get_transit_data(eb, md_scenid)
    	dfPmT = self.get_transit_data(eb, pm_scenid)

    	# add time period
    	dfAm['peakperiod'] = 'AM'
    	dfMd['peakperiod'] = 'MD'
    	dfPm['peakperiod'] = 'PM'

    	dfAmT['peakperiod'] = 'AM'
    	dfMdT['peakperiod'] = 'MD'
    	dfPmT['peakperiod'] = 'PM'

    	# clean up transit lines for aggregation.  Extract line and direction from EMME coding
    	dfTransit = dfAmT.append(dfMdT).append(dfPmT)
        dfLineName = dfTransit['Line'].str.extract(r'(?P<newLine>[a-zA-Z]{0,2}_?\d+)(?:[^ioNSEW\d]?)(?P<dir>N|S|E|W|L|[M]2?)')
        dfTransit = pd.concat([dfTransit, dfLineName], axis=1)

        dfAuto = dfAm.append(dfMd).append(dfPm)

    	# connect to output data base and create if not existing
        return dfAuto, dfTransit

    def get_transit_data(self, eb, scenario_id):
        scenario = eb.scenario(scenario_id)
        network = scenario.get_network()
        dfDict = {'Line' : [],
                  'Segment' : [],
                  'Length' : [],
                  'Time' : [],
                  'Speed' : [],
                  'loadFactor' : [],
                  'volume' : [],
                  'transitStop' : [],
                  'boardings' : [],
                  'alightings' : [],
                  'seatProbability' : [],
                  'lineDescription' : [],
                  'vehType' : [],
                  'vehDesc' : [],
                  'seatedPassengers' : [],
                  'standingPassengers' : [],
                  'hdwyfac' : [],
                  'seatedCapacity' : [],
                  'totalCapacity' : [],
                  'mode' : [],
                  'modeDesc' : []}



        for seg in network.transit_segments():
            dfDict['Line'].append(seg.line.id)
            dfDict['Segment'].append("{}-{}".format(seg.i_node, seg.j_node))

            try:
                dfDict['Length'].append(seg.link.length)
            except:
                dfDict['Length'].append(np.nan)
            dfDict['Time'].append(seg.transit_time)

            try:
                dfDict['Speed'].append(seg.link.length / (seg.transit_time / 60))
            except:
                dfDict['Speed'].append(np.nan)

            dfDict['loadFactor'].append(seg.transit_volume / seg.line['@totcapacity'])
            dfDict['volume'].append(seg.transit_volume)

            if (seg.allow_alightings or seg.allow_boardings):
                 dfDict['transitStop'].append(int(seg.i_node))
            else:
                dfDict['transitStop'].append(np.nan)

            dfDict['boardings'].append( seg.transit_boardings)
            dfDict['alightings'].append(seg['@alight']) #TODO update if we can remove the extra attribute calculation
            dfDict['seatProbability'].append(0) # TODO update when alightings becomes available
            dfDict['lineDescription'].append(seg.line.description)
            dfDict['vehType'].append(seg.line.vehicle.number)
            dfDict['vehDesc'].append(seg.line.vehicle.description)
            dfDict['seatedPassengers'].append(seg['@pseat'])
            dfDict['standingPassengers'].append(seg['@pstand'])
            dfDict['hdwyfac'].append(seg['@hdwyfac'])
            dfDict['seatedCapacity'].append(seg.line['@seatcapacity'])
            dfDict['totalCapacity'].append(seg.line['@totcapacity'])
            dfDict['mode'].append(seg.line.mode.id)
            dfDict['modeDesc'].append(seg.line.mode.description)

        df = pd.DataFrame(dfDict)
        df = df[['Line','Segment','Length','Time','Speed','loadFactor','volume','transitStop','boardings','alightings','seatProbability','lineDescription','vehType','vehDesc','seatedPassengers','standingPassengers','hdwyfac','seatedCapacity','totalCapacity','mode','modeDesc']]

        return df

    def get_auto_data(self, eb, scenario_id):
        scenario = eb.scenario(scenario_id)
        network = scenario.get_network()
        dfDict = {'i' : [],
                  'j' : [],
                  'Screenline_ID' : [],
                  'Screenline_Station' : [],
                  'SOV' : [],
                  'HOV' : [],
                  'Light_Trucks' : [],
                  'Heavy_Trucks' : [],
                  'Transit_Vehicles' : [],
                  'Transit_Volume' : [],
                  'Transit_Capacity' : [],
                  'Length' : [],
                  'Auto_Time' : [],
                  'tolls' : [],
                  'speed' : [],
                  'lanes' : [],
                  'func_class' : [],
                  'vdf' : [],
                  'posted_speed' : []}

        for link in network.links():
            dfDict['i'].append(int(link.i_node))
            dfDict['j'].append(int(link.j_node))
            dfDict['Screenline_ID'].append(link['@lscid'])
            dfDict['Screenline_Station'].append(round(link['@lscstn'], 2))
            dfDict['SOV'].append((link['@sov1'] + link['@sov2'] + link['@sov3'] + link['@sov4']))
            dfDict['HOV'].append((link['@hov1'] + link['@hov2'] + link['@hov3'] + link['@hov4']) )
            dfDict['Light_Trucks'].append((link['@lgvol'] / 1.5))
            dfDict['Heavy_Trucks'].append((link['@hgvol'] / 2.5))
            dfDict['Transit_Vehicles'].append((link.additional_volume / 2.5))
            dfDict['Transit_Volume'].append(link['@voltr']) #TODO remove 3 once using different test network
            dfDict['Transit_Capacity'].append(link['@tran_cap'])
            dfDict['Length'].append(link.length)
            dfDict['Auto_Time'].append(np.maximum(link.auto_time, 0))
            dfDict['tolls'].append(link['@tolls'])
            dfDict['speed'].append((link.length / (np.maximum(link.auto_time, 0) / 60)))
            dfDict['lanes'].append(link.num_lanes)
            dfDict['func_class'].append(link.type)
            dfDict['vdf'].append(link.volume_delay_func)
            dfDict['posted_speed'].append(link['@posted_speed'])

        df = pd.DataFrame(dfDict)
        df = df[['i','j','Screenline_ID','Screenline_Station','SOV','HOV','Light_Trucks','Heavy_Trucks','Transit_Vehicles','Transit_Volume','Transit_Capacity','Length','Auto_Time','tolls','speed','lanes','func_class','vdf','posted_speed']]
        return df
