##---------------------------------------------------------------------
##--TransLink Regional Transportation Model
##--
##--Path:
##--Purpose: Output data after run
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback

import os
import csv as csv

import sqlite3
import pandas as pd



class DataExport(_m.Tool()):

    export_csvs = _m.Attribute(bool)
    tool_run_msg = _m.Attribute(unicode)


    def __init__(self):
        self.export_csvs = False




    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Export Data from Model Run"
        pb.description = "Exports Results of Model Run"
        pb.branding_text = "TransLink"

        util = _m.Modeller().tool("translink.util")
        input_path = util.get_input_path(_m.Modeller().emmebank)

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


    @_m.logbook_trace("Data Import")
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

        # runs last
        if self.export_csvs:
            self.export_text(eb)




    def export_text(self, eb):
        pass

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

        # build dataframe
        df = pd.DataFrame({'period' : ['AM','MD','PM', 'AM','MD','PM', 'AM','PM'],
              'mode' : ['bus','bus','bus','rail','rail','rail','wce','wce'],
              'measure': ['mins','mins','mins','mins','mins','mins','mins','mins'],
              'value': [avgTtBusAm, avgTtBusMd, avgTtBusPm, avgTtRailAm, avgTtRailMd, avgTtRailPm, avgTtWceAm, avgTtWcePm]})

        df = df[['period','mode','measure','value']]
        return df


    def calc_auto_tt(self, eb):
        util = _m.Modeller().tool("translink.util")
        #am
        amSovTime1 = util.get_matrix_numpy(eb, "mfAmSovTimeVOT1").flatten()
        amSovTime2 = util.get_matrix_numpy(eb, "mfAmSovTimeVOT2").flatten()
        amSovTime3 = util.get_matrix_numpy(eb, "mfAmSovTimeVOT3").flatten()
        amSovTime4 = util.get_matrix_numpy(eb, "mfAmSovTimeVOT4").flatten()

        amSovDemand1 = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_1_Am").flatten()
        amSovDemand2 = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_2_Am").flatten()
        amSovDemand3 = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_3_Am").flatten()
        amSovDemand4 = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_4_Am").flatten()

        amSovTotTime = amSovTime1 * amSovDemand1 + amSovTime2 * amSovDemand2 + amSovTime3 * amSovDemand3 + amSovTime4 * amSovDemand4

        avgTtSovAm = amSovTotTime.sum() / (amSovDemand1 + amSovDemand2 + amSovDemand3 + amSovDemand4).sum()

        # md
        mdSovTime1 = util.get_matrix_numpy(eb, "mfMdSovTimeVOT1").flatten()
        mdSovTime2 = util.get_matrix_numpy(eb, "mfMdSovTimeVOT2").flatten()
        mdSovTime3 = util.get_matrix_numpy(eb, "mfMdSovTimeVOT3").flatten()
        mdSovTime4 = util.get_matrix_numpy(eb, "mfMdSovTimeVOT4").flatten()

        mdSovDemand1 = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_1_Md").flatten()
        mdSovDemand2 = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_2_Md").flatten()
        mdSovDemand3 = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_3_Md").flatten()
        mdSovDemand4 = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_4_Md").flatten()

        mdSovTotTime = mdSovTime1 * mdSovDemand1 + mdSovTime2 * mdSovDemand2 + mdSovTime3 * mdSovDemand3 + mdSovTime4 * mdSovDemand4

        avgTtSovMd = mdSovTotTime.sum() / (mdSovDemand1 + mdSovDemand2 + mdSovDemand3 + mdSovDemand4).sum()

        #pm
        pmSovTime1 = util.get_matrix_numpy(eb, "mfPmSovTimeVOT1").flatten()
        pmSovTime2 = util.get_matrix_numpy(eb, "mfPmSovTimeVOT2").flatten()
        pmSovTime3 = util.get_matrix_numpy(eb, "mfPmSovTimeVOT3").flatten()
        pmSovTime4 = util.get_matrix_numpy(eb, "mfPmSovTimeVOT4").flatten()

        pmSovDemand1 = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_1_Pm").flatten()
        pmSovDemand2 = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_2_Pm").flatten()
        pmSovDemand3 = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_3_Pm").flatten()
        pmSovDemand4 = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_4_Pm").flatten()

        pmSovTotTime = pmSovTime1 * pmSovDemand1 + pmSovTime2 * pmSovDemand2 + pmSovTime3 * pmSovDemand3 + pmSovTime4 * pmSovDemand4

        avgTtSovPm = pmSovTotTime.sum() / (pmSovDemand1 + pmSovDemand2 + pmSovDemand3 + pmSovDemand4).sum()

        #am
        amHovTime1 = util.get_matrix_numpy(eb, "mfAmHovTimeVOT1").flatten()
        amHovTime2 = util.get_matrix_numpy(eb, "mfAmHovTimeVOT2").flatten()
        amHovTime3 = util.get_matrix_numpy(eb, "mfAmHovTimeVOT3").flatten()
        amHovTime4 = util.get_matrix_numpy(eb, "mfAmHovTimeVOT4").flatten()

        amHovDemand1 = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_1_Am").flatten()
        amHovDemand2 = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_2_Am").flatten()
        amHovDemand3 = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_3_Am").flatten()
        amHovDemand4 = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_4_Am").flatten()

        amHovTotTime = amHovTime1 * amHovDemand1 + amHovTime2 * amHovDemand2 + amHovTime3 * amHovDemand3 + amHovTime4 * amHovDemand4

        avgTtHovAm = amHovTotTime.sum() / (amHovDemand1 + amHovDemand2 + amHovDemand3 + amHovDemand4).sum()

        # md
        mdHovTime1 = util.get_matrix_numpy(eb, "mfMdHovTimeVOT1").flatten()
        mdHovTime2 = util.get_matrix_numpy(eb, "mfMdHovTimeVOT2").flatten()
        mdHovTime3 = util.get_matrix_numpy(eb, "mfMdHovTimeVOT3").flatten()
        mdHovTime4 = util.get_matrix_numpy(eb, "mfMdHovTimeVOT4").flatten()

        mdHovDemand1 = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_1_Md").flatten()
        mdHovDemand2 = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_2_Md").flatten()
        mdHovDemand3 = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_3_Md").flatten()
        mdHovDemand4 = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_4_Md").flatten()

        mdHovTotTime = mdHovTime1 * mdHovDemand1 + mdHovTime2 * mdHovDemand2 + mdHovTime3 * mdHovDemand3 + mdHovTime4 * mdHovDemand4

        avgTtHovMd = mdHovTotTime.sum() / (mdHovDemand1 + mdHovDemand2 + mdHovDemand3 + mdHovDemand4).sum()

        #pm
        pmHovTime1 = util.get_matrix_numpy(eb, "mfPmHovTimeVOT1").flatten()
        pmHovTime2 = util.get_matrix_numpy(eb, "mfPmHovTimeVOT2").flatten()
        pmHovTime3 = util.get_matrix_numpy(eb, "mfPmHovTimeVOT3").flatten()
        pmHovTime4 = util.get_matrix_numpy(eb, "mfPmHovTimeVOT4").flatten()

        pmHovDemand1 = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_1_Pm").flatten()
        pmHovDemand2 = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_2_Pm").flatten()
        pmHovDemand3 = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_3_Pm").flatten()
        pmHovDemand4 = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_4_Pm").flatten()

        pmHovTotTime = pmHovTime1 * pmHovDemand1 + pmHovTime2 * pmHovDemand2 + pmHovTime3 * pmHovDemand3 + pmHovTime4 * pmHovDemand4

        avgTtHovPm = pmHovTotTime.sum() / (pmHovDemand1 + pmHovDemand2 + pmHovDemand3 + pmHovDemand4).sum()


        df = pd.DataFrame({'period' : ['AM','MD','PM', 'AM','MD','PM'],
              'mode' : ['sov','sov','sov','hov','hov','hov'],
              'measure': ['mins','mins','mins','mins','mins','mins'],
              'value': [avgTtSovAm, avgTtSovMd, avgTtSovPm, avgTtHovAm, avgTtHovMd, avgTtHovPm]})

        df = df[['period','mode','measure','value']]
        return df
