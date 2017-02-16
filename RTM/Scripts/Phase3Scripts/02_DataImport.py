##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: ?
##--Purpose: Import Data for RTM Run
##---------------------------------------------------------------------

import inro.modeller as _m
import traceback as _traceback
import os
import numpy as np
import pandas as pd



class DataImport(_m.Tool()):

    demographics_file = _m.Attribute(_m.InstanceType)
    geographics_file = _m.Attribute(_m.InstanceType)

    tool_run_msg = _m.Attribute(unicode)

    # TODO currently this tool is not directly runnable unless run model as been run
    # requires ms10, which is created there.  Need to decide if this is correct
    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Import Data for Model Run"
        pb.description = "Imports Scalars, Vectors, and Seed Matrices for Model Run"
        pb.branding_text = "TransLink"

        util = _m.Modeller().tool("translink.util")
        input_path = util.get_input_path(_m.Modeller().emmebank)

        pb.add_select_file(tool_attribute_name="demographics_file",
                           window_type="file",
                           file_filter="*demographics*.csv",
                           start_path= input_path,
                           title="Demographics File: ",
                           note="File must be csv file.")

        pb.add_select_file(tool_attribute_name="geographics_file",
                           window_type="file",
                           file_filter="*geographics*.csv",
                           start_path= input_path,
                           title="Geographics File: ",
                           note="File must be csv file.")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            eb = _m.Modeller().emmebank
            self.__call__(eb, self.demographics_file, self.geographics_file)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))


    @_m.logbook_trace("Data Import")
    def __call__(self, eb, demographics_file, geographics_file):
        util = _m.Modeller().tool("translink.util")
        model_year = int(util.get_year(eb))

        self.matrix_batchins(eb)
        self.init_scalars(eb)
        self.import_vectors(eb, demographics_file, geographics_file)

        self.init_seeds(eb, horizon_year=model_year)
        self.starter_skims(eb, horizon_year=model_year)


    @_m.logbook_trace("Initializing Scalar Matrices")
    def init_scalars(self, eb):
        util = _m.Modeller().tool("translink.util")

        util.initmat(eb, "ms100", "autoOpCost", "Auto Operating Cost", 0.18)
        util.initmat(eb, "ms101", "lgvOpCost", "Light Truck Operating Cost", 0.24)
        util.initmat(eb, "ms102", "hgvOpCost", "Heavy Truck Operating Cost", 0.56)
        util.initmat(eb, "ms110", "HOVOccHbw", "HOV Occupancy HB Work", 3.51)
        util.initmat(eb, "ms111", "HOVOccHbu", "HOV Occupancy HB University", 2.48)
        util.initmat(eb, "ms112", "HOVOccHbesc", "HOV Occupancy HB Escorting", 2.6)
        util.initmat(eb, "ms113", "HOVOccHbpb", "HOV Occupancy HB Pers Bus", 2.31)
        util.initmat(eb, "ms114", "HOVOccHBsch", "HOV Occupancy HB School", 3.02)
        util.initmat(eb, "ms115", "HOVOccHBshop", "HOV Occupancy HB Shop", 2.35)
        util.initmat(eb, "ms116", "HOVOccHBsoc", "HOV Occupancy HB Social", 2.61)
        util.initmat(eb, "ms117", "HOVOccNHBw", "HOV Occupancy NHB Work", 2.31)
        util.initmat(eb, "ms118", "HOVOccNHBo", "HOV Occupancy NHB Other", 2.58)
        util.initmat(eb, "ms122", "AutoOccHbesc", "Auto Occupancy HB Escorting", 2.14)
        util.initmat(eb, "ms128", "AutoOccNHBo", "Auto Occupancy NHB Other", 2)
        util.initmat(eb, "ms130", "lgvPCE", "Light Truck Passenger Car Equivalent", 1.5)
        util.initmat(eb, "ms131", "hgvPCE", "Heavy Truck Passenger Car Equivalent", 2.5)
        util.initmat(eb, "ms142", "sov_pct_Hbesc", "SOV proportion of Auto HB Escorting", 0.288)
        util.initmat(eb, "ms148", "sov_pct_NHBo", "SOV proportion of Auto NHB Other", 0.365)
        util.initmat(eb, "ms150", "nhbwCt2011", "NHBW HH Production Control Total", 596590.636153)
        util.initmat(eb, "ms151", "nhboCt2011", "NHB0 HH Production Control Total", 852928.057776)

        util.initmat(eb, "ms160", "oneZoneFare", "One Zone Fare - FS-SV", 2.1)

        util.initmat(eb, "ms200", "AutoVOT1", "AutoVOT1", 9.2)
        util.initmat(eb, "ms201", "AutoVOT2", "AutoVOT2", 7.4)
        util.initmat(eb, "ms202", "AutoVOT3", "AutoVOT3", 3.3)
        util.initmat(eb, "ms203", "AutoVOT4", "AutoVOT4", 2.5)
        util.initmat(eb, "ms212", "VotBus", "VOT Work", 3.76)
        util.initmat(eb, "ms213", "VotRail", "VOT Work", 3.76)
        util.initmat(eb, "ms214", "VotWce", "VOT Work", 3.76)

        util.initmat(eb, "ms218", "VotLgv", "VOT lgv", 2.03)
        util.initmat(eb, "ms219", "VotHgv", "VOT hgv", 1.43)
        util.initmat(eb, "ms300", "busIVTprcpWk", "bus in-vehicle time perception work", 1.06)
        util.initmat(eb, "ms301", "busWAITprcpWk", "bus wait time perception work", 1.92)
        util.initmat(eb, "ms302", "busWALKprcpWk", "bus walk time perception work", 1.71)
        util.initmat(eb, "ms303", "busBOARDSprcpWk", "bus boarding perception work", 10.81)
        util.initmat(eb, "ms310", "railIVTprcpWk", "rail in-vehicle time perception work", 1)
        util.initmat(eb, "ms311", "railWAITprcpWk", "rail wait time perception work", 2.03)
        util.initmat(eb, "ms312", "railWALKprcpWk", "rail walk time perception work", 1.8)
        util.initmat(eb, "ms313", "railBOARDSprcpWk", "rail boarding perception work", 11.4)
        util.initmat(eb, "ms320", "wceIVTprcpWk", "wce in-vehicle time perception work", 1)
        util.initmat(eb, "ms321", "wceWAITprcpWk", "wce wait time perception work", 2.03)
        util.initmat(eb, "ms322", "wceWALKprcpWk", "wce walk time perception work", 1.8)
        util.initmat(eb, "ms323", "wceBOARDSprcpWk", "wce boarding perception work", 11.4)
        util.initmat(eb, "ms330", "busIVTprcpNwk", "bus in-vehicle time perception nonwork", 0)
        util.initmat(eb, "ms331", "busWAITprcpNwk", "bus wait time perception nonwork", 0)
        util.initmat(eb, "ms332", "busWALKprcpNwk", "bus walk time perception nonwork", 0)
        util.initmat(eb, "ms333", "busTRANSprcpNwk", "bus transfer perception nonwork", 0)
        util.initmat(eb, "ms334", "busBOARDSprcpNwk", "bus boarding perception nonwork", 0)
        util.initmat(eb, "ms340", "railIVTprcpNwk", "rail in-vehicle time perception nonwork", 0)
        util.initmat(eb, "ms341", "railWAITprcpNwk", "rail wait time perception nonwork", 0)
        util.initmat(eb, "ms342", "railWALKprcpNwk", "rail walk time perception nonwork", 0)
        util.initmat(eb, "ms343", "railTRANSprcpNwk", "rail transfer perception nonwork", 0)
        util.initmat(eb, "ms344", "railBOARDSprcpNwk", "rail boarding perception nonwork", 0)
        util.initmat(eb, "ms350", "wceIVTprcpNwk", "wce in-vehicle time perception nonwork", 0)
        util.initmat(eb, "ms351", "wceWAITprcpNwk", "wce wait time perception nonwork", 0)
        util.initmat(eb, "ms352", "wceWALKprcpNwk", "wce walk time perception nonwork", 0)
        util.initmat(eb, "ms353", "wceTRANSprcpNwk", "wce transfer perception nonwork", 0)
        util.initmat(eb, "ms354", "wceBOARDSprcpNwk", "wce boarding perception nonwork", 0)

        ##      Park and Ride Drive time perception factor
        util.initmat(eb, "ms360", "pr_auto_time_prcp", "Park and Ride Drive time perception factor", 1.2)


        ##      Batch in Blending Factors

        util.initmat(eb, "ms400", "HbWBl_AM_P-A", "HbW Blend AM P-A Factor", 0.391751)
        util.initmat(eb, "ms401", "HbWBl_MD_P-A", "HbW Blend MD P-A Factor", 0.116333)
        util.initmat(eb, "ms402", "HbWBl_PM_P-A", "HbW Blend PM P-A Factor", 0.026389)
        util.initmat(eb, "ms403", "HbWBl_AM_A-P", "HbW Blend AM A-P Factor", 0.006959)
        util.initmat(eb, "ms404", "HbWBl_MD_A-P", "HbW Blend MD A-P Factor", 0.139755)
        util.initmat(eb, "ms405", "HbWBl_PM_A-P", "HbW Blend PM A-P Factor", 0.318813)
        util.initmat(eb, "ms406", "HbWBl_AM_WCE_P-A", "HbW Blend AM WCE P-A Factor", 0.524949)
        util.initmat(eb, "ms407", "HbWBl_PM_WCE_P-A", "HbW Blend PM WCE P-A Factor", 0.002292)
        util.initmat(eb, "ms408", "HbWBl_PM_WCE_A-P", "HbW Blend PM WCE A-P Factor", 0.472759)
        util.initmat(eb, "ms410", "HbUBl_AM_P-A", "HbU Blend AM P-A Factor", 0.344166)
        util.initmat(eb, "ms411", "HbUBl_MD_P-A", "HbU Blend MD P-A Factor", 0.156457)
        util.initmat(eb, "ms412", "HbUBl_PM_P-A", "HbU Blend PM P-A Factor", 0.040057)
        util.initmat(eb, "ms413", "HbUBl_AM_A-P", "HbU Blend AM A-P Factor", 0.038817)
        util.initmat(eb, "ms414", "HbUBl_MD_A-P", "HbU Blend MD A-P Factor", 0.197199)
        util.initmat(eb, "ms415", "HbUBl_PM_A-P", "HbU Blend PM A-P Factor", 0.223304)
        util.initmat(eb, "ms420", "HbScBl_AM_P-A", "HbSc Blend AM P-A Factor", 0.542245)
        util.initmat(eb, "ms421", "HbScBl_MD_P-A", "HbSc Blend MD P-A Factor", 0.021253)
        util.initmat(eb, "ms422", "HbScBl_PM_P-A", "HbSc Blend PM P-A Factor", 0.008573)
        util.initmat(eb, "ms423", "HbScBl_AM_A-P", "HbSc Blend AM A-P Factor", 0.000879)
        util.initmat(eb, "ms424", "HbScBl_MD_A-P", "HbSc Blend MD A-P Factor", 0.120986)
        util.initmat(eb, "ms425", "HbScBl_PM_A-P", "HbSc Blend PM A-P Factor", 0.306064)
        util.initmat(eb, "ms430", "HbShBl_AM_P-A", "HbSh Blend AM P-A Factor", 0.049653)
        util.initmat(eb, "ms431", "HbShBl_MD_P-A", "HbSh Blend MD P-A Factor", 0.250105)
        util.initmat(eb, "ms432", "HbShBl_PM_P-A", "HbSh Blend PM P-A Factor", 0.09939)
        util.initmat(eb, "ms433", "HbShBl_AM_A-P", "HbSh Blend AM A-P Factor", 0.01399)
        util.initmat(eb, "ms434", "HbShBl_MD_A-P", "HbSh Blend MD A-P Factor", 0.330378)
        util.initmat(eb, "ms435", "HbShBl_PM_A-P", "HbSh Blend PM A-P Factor", 0.256484)
        util.initmat(eb, "ms440", "HbPbBl_AM_P-A", "HbPb Blend AM P-A Factor", 0.1377)
        util.initmat(eb, "ms441", "HbPbBl_MD_P-A", "HbPb Blend MD P-A Factor", 0.259251)
        util.initmat(eb, "ms442", "HbPbBl_PM_P-A", "HbPb Blend PM P-A Factor", 0.103013)
        util.initmat(eb, "ms443", "HbPbBl_AM_A-P", "HbPb Blend AM A-P Factor", 0.028271)
        util.initmat(eb, "ms444", "HbPbBl_MD_A-P", "HbPb Blend MD A-P Factor", 0.276689)
        util.initmat(eb, "ms445", "HbPbBl_PM_A-P", "HbPb Blend PM A-P Factor", 0.195075)
        util.initmat(eb, "ms450", "HbSoBl_AM_P-A", "HbSo Blend AM P-A Factor", 0.08467)
        util.initmat(eb, "ms451", "HbSoBl_MD_P-A", "HbSo Blend MD P-A Factor", 0.200775)
        util.initmat(eb, "ms452", "HbSoBl_PM_P-A", "HbSo Blend PM P-A Factor", 0.193507)
        util.initmat(eb, "ms453", "HbSoBl_AM_A-P", "HbSo Blend AM A-P Factor", 0.017456)
        util.initmat(eb, "ms454", "HbSoBl_MD_A-P", "HbSo Blend MD A-P Factor", 0.357924)
        util.initmat(eb, "ms455", "HbSoBl_PM_A-P", "HbSo Blend PM A-P Factor", 0.145669)
        util.initmat(eb, "ms460", "HbEsBl_AM_P-A", "HbEs Blend AM P-A Factor", 0.234921)
        util.initmat(eb, "ms461", "HbEsBl_MD_P-A", "HbEs Blend MD P-A Factor", 0.169469)
        util.initmat(eb, "ms462", "HbEsBl_PM_P-A", "HbEs Blend PM P-A Factor", 0.121543)
        util.initmat(eb, "ms463", "HbEsBl_AM_A-P", "HbEs Blend AM A-P Factor", 0.091506)
        util.initmat(eb, "ms464", "HbEsBl_MD_A-P", "HbEs Blend MD A-P Factor", 0.168692)
        util.initmat(eb, "ms465", "HbEsBl_PM_A-P", "HbEs Blend PM A-P Factor", 0.213869)
        util.initmat(eb, "ms470", "NHbWBl_AM_P-A", "NHbW Blend AM P-A Factor", 0.203601)
        util.initmat(eb, "ms471", "NHbWBl_MD_P-A", "NHbW Blend MD P-A Factor", 0.448225)
        util.initmat(eb, "ms472", "NHbWBl_PM_P-A", "NHbW Blend PM P-A Factor", 0.348174)
        util.initmat(eb, "ms480", "NHbOBl_AM_P-A", "NHbO Blend AM P-A Factor", 0.12017)
        util.initmat(eb, "ms481", "NHbOBl_MD_P-A", "NHbO Blend MD P-A Factor", 0.540629)
        util.initmat(eb, "ms482", "NHbOBl_PM_P-A", "NHbO Blend PM P-A Factor", 0.339201)
        util.initmat(eb, "ms490", "Zero", "Zero", 0)
        util.initmat(eb, "ms500", "TrFr_HbWBl_AM_P-A", "TrFr HbW Blend AM P-A Factor", 0.419497)
        util.initmat(eb, "ms501", "TrFr_HbWBl_MD_P-A", "TrFr HbW Blend MD P-A Factor", 0.079803)
        util.initmat(eb, "ms502", "TrFr_HbWBl_PM_P-A", "TrFr HbW Blend PM P-A Factor", 0.021515)
        util.initmat(eb, "ms503", "TrFr_HbWBl_OP_P-A", "TrFr HbW Blend OP P-A Factor", 0.014547)
        util.initmat(eb, "ms504", "TrFr_HbWBl_AM_A-P", "TrFr HbW Blend AM A-P Factor", 0.005602)
        util.initmat(eb, "ms505", "TrFr_HbWBl_MD_A-P", "TrFr HbW Blend MD A-P Factor", 0.030851)
        util.initmat(eb, "ms506", "TrFr_HbWBl_PM_A-P", "TrFr HbW Blend PM A-P Factor", 0.310605)
        util.initmat(eb, "ms507", "TrFr_HbWBl_OP_A-P", "TrFr HbW Blend OP A-P Factor", 0.117582)
        util.initmat(eb, "ms510", "TrFr_HbUBl_AM_P-A", "TrFr HbU Blend AM P-A Factor", 0.324712)
        util.initmat(eb, "ms511", "TrFr_HbUBl_MD_P-A", "TrFr HbU Blend MD P-A Factor", 0.151295)
        util.initmat(eb, "ms512", "TrFr_HbUBl_PM_P-A", "TrFr HbU Blend PM P-A Factor", 0.028138)
        util.initmat(eb, "ms513", "TrFr_HbUBl_OP_P-A", "TrFr HbU Blend OP P-A Factor", 0.012398)
        util.initmat(eb, "ms514", "TrFr_HbUBl_AM_A-P", "TrFr HbU Blend AM A-P Factor", 0.004201)
        util.initmat(eb, "ms515", "TrFr_HbUBl_MD_A-P", "TrFr HbU Blend MD A-P Factor", 0.09985)
        util.initmat(eb, "ms516", "TrFr_HbUBl_PM_A-P", "TrFr HbU Blend PM A-P Factor", 0.263596)
        util.initmat(eb, "ms517", "TrFr_HbUBl_OP_A-P", "TrFr HbU Blend OP A-P Factor", 0.11581)
        util.initmat(eb, "ms520", "TrFr_HbScBl_AM_P-A", "TrFr HbSc Blend AM P-A Factor", 0.424723)
        util.initmat(eb, "ms521", "TrFr_HbScBl_MD_P-A", "TrFr HbSc Blend MD P-A Factor", 0.018701)
        util.initmat(eb, "ms522", "TrFr_HbScBl_PM_P-A", "TrFr HbSc Blend PM P-A Factor", 0.002993)
        util.initmat(eb, "ms523", "TrFr_HbScBl_OP_P-A", "TrFr HbSc Blend OP P-A Factor", 0.024219)
        util.initmat(eb, "ms524", "TrFr_HbScBl_AM_A-P", "TrFr HbSc Blend AM A-P Factor", 0.000525)
        util.initmat(eb, "ms525", "TrFr_HbScBl_MD_A-P", "TrFr HbSc Blend MD A-P Factor", 0.040182)
        util.initmat(eb, "ms526", "TrFr_HbScBl_PM_A-P", "TrFr HbSc Blend PM A-P Factor", 0.473926)
        util.initmat(eb, "ms527", "TrFr_HbScBl_OP_A-P", "TrFr HbSc Blend OP A-P Factor", 0.014731)
        util.initmat(eb, "ms530", "TrFr_HbShBl_AM_P-A", "TrFr HbSh Blend AM P-A Factor", 0.06879)
        util.initmat(eb, "ms531", "TrFr_HbShBl_MD_P-A", "TrFr HbSh Blend MD P-A Factor", 0.280645)
        util.initmat(eb, "ms532", "TrFr_HbShBl_PM_P-A", "TrFr HbSh Blend PM P-A Factor", 0.067056)
        util.initmat(eb, "ms533", "TrFr_HbShBl_OP_P-A", "TrFr HbSh Blend OP P-A Factor", 0.023859)
        util.initmat(eb, "ms534", "TrFr_HbShBl_AM_A-P", "TrFr HbSh Blend AM A-P Factor", 0.010383)
        util.initmat(eb, "ms535", "TrFr_HbShBl_MD_A-P", "TrFr HbSh Blend MD A-P Factor", 0.199906)
        util.initmat(eb, "ms536", "TrFr_HbShBl_PM_A-P", "TrFr HbSh Blend PM A-P Factor", 0.234326)
        util.initmat(eb, "ms537", "TrFr_HbShBl_OP_A-P", "TrFr HbSh Blend OP A-P Factor", 0.115035)
        util.initmat(eb, "ms540", "TrFr_HbPbBl_AM_P-A", "TrFr HbPb Blend AM P-A Factor", 0.151016)
        util.initmat(eb, "ms541", "TrFr_HbPbBl_MD_P-A", "TrFr HbPb Blend MD P-A Factor", 0.285436)
        util.initmat(eb, "ms542", "TrFr_HbPbBl_PM_P-A", "TrFr HbPb Blend PM P-A Factor", 0.050528)
        util.initmat(eb, "ms543", "TrFr_HbPbBl_OP_P-A", "TrFr HbPb Blend OP P-A Factor", 0.031963)
        util.initmat(eb, "ms544", "TrFr_HbPbBl_AM_A-P", "TrFr HbPb Blend AM A-P Factor", 0.016513)
        util.initmat(eb, "ms545", "TrFr_HbPbBl_MD_A-P", "TrFr HbPb Blend MD A-P Factor", 0.201593)
        util.initmat(eb, "ms546", "TrFr_HbPbBl_PM_A-P", "TrFr HbPb Blend PM A-P Factor", 0.18174)
        util.initmat(eb, "ms547", "TrFr_HbPbBl_OP_A-P", "TrFr HbPb Blend OP A-P Factor", 0.08121)
        util.initmat(eb, "ms550", "TrFr_HbSoBl_AM_P-A", "TrFr HbSo Blend AM P-A Factor", 0.111089)
        util.initmat(eb, "ms551", "TrFr_HbSoBl_MD_P-A", "TrFr HbSo Blend MD P-A Factor", 0.168836)
        util.initmat(eb, "ms552", "TrFr_HbSoBl_PM_P-A", "TrFr HbSo Blend PM P-A Factor", 0.133851)
        util.initmat(eb, "ms553", "TrFr_HbSoBl_OP_P-A", "TrFr HbSo Blend OP P-A Factor", 0.078438)
        util.initmat(eb, "ms554", "TrFr_HbSoBl_AM_A-P", "TrFr HbSo Blend AM A-P Factor", 0.009155)
        util.initmat(eb, "ms555", "TrFr_HbSoBl_MD_A-P", "TrFr HbSo Blend MD A-P Factor", 0.095744)
        util.initmat(eb, "ms556", "TrFr_HbSoBl_PM_A-P", "TrFr HbSo Blend PM A-P Factor", 0.140719)
        util.initmat(eb, "ms557", "TrFr_HbSoBl_OP_A-P", "TrFr HbSo Blend OP A-P Factor", 0.262169)
        util.initmat(eb, "ms560", "TrFr_HbEsBl_AM_P-A", "TrFr HbEs Blend AM P-A Factor", 0.23936)
        util.initmat(eb, "ms561", "TrFr_HbEsBl_MD_P-A", "TrFr HbEs Blend MD P-A Factor", 0.163891)
        util.initmat(eb, "ms562", "TrFr_HbEsBl_PM_P-A", "TrFr HbEs Blend PM P-A Factor", 0.044827)
        util.initmat(eb, "ms563", "TrFr_HbEsBl_OP_P-A", "TrFr HbEs Blend OP P-A Factor", 0.049954)
        util.initmat(eb, "ms564", "TrFr_HbEsBl_AM_A-P", "TrFr HbEs Blend AM A-P Factor", 0.025045)
        util.initmat(eb, "ms565", "TrFr_HbEsBl_MD_A-P", "TrFr HbEs Blend MD A-P Factor", 0.116984)
        util.initmat(eb, "ms566", "TrFr_HbEsBl_PM_A-P", "TrFr HbEs Blend PM A-P Factor", 0.228243)
        util.initmat(eb, "ms567", "TrFr_HbEsBl_OP_A-P", "TrFr HbEs Blend OP A-P Factor", 0.131696)
        util.initmat(eb, "ms570", "TrFr_NHbWBl_AM_P-A", "TrFr NHbW Blend AM P-A Factor", 0.143602)
        util.initmat(eb, "ms571", "TrFr_NHbWBl_MD_P-A", "TrFr NHbW Blend MD P-A Factor", 0.293362)
        util.initmat(eb, "ms572", "TrFr_NHbWBl_PM_P-A", "TrFr NHbW Blend PM P-A Factor", 0.474294)
        util.initmat(eb, "ms573", "TrFr_NHbWBl_OP_P-A", "TrFr NHbW Blend OP P-A Factor", 0.088743)
        util.initmat(eb, "ms580", "TrFr_NHbOBl_AM_P-A", "TrFr NHbO Blend AM P-A Factor", 0.073525)
        util.initmat(eb, "ms581", "TrFr_NHbOBl_MD_P-A", "TrFr NHbO Blend MD P-A Factor", 0.45599)
        util.initmat(eb, "ms582", "TrFr_NHbOBl_PM_P-A", "TrFr NHbO Blend PM P-A Factor", 0.363881)
        util.initmat(eb, "ms583", "TrFr_NHbOBl_OP_P-A", "TrFr NHbO Blend OP P-A Factor", 0.106604)
        util.initmat(eb, "mf314", "busAm", "Bus Person Trips AM", 0)
        util.initmat(eb, "mf315", "railAm", "Rail Person Trips AM", 0)
        util.initmat(eb, "mf316", "WCEAm", "WCE Person Trips AM", 0)
        util.initmat(eb, "mf334", "busMd", "Bus Person Trips MD", 0)
        util.initmat(eb, "mf335", "railMd", "Rail Person Trips MD", 0)
        util.initmat(eb, "mf336", "WCEMd", "WCE Person Trips MD", 0)
        util.initmat(eb, "mf354", "busPm", "Bus Person Trips PM", 0)
        util.initmat(eb, "mf355", "railPm", "Rail Person Trips PM", 0)
        util.initmat(eb, "mf356", "WCEPm", "WCE Person Trips PM", 0)

    @_m.logbook_trace("Importing Vector Data from CSV")
    def import_vectors(self, eb, demographics_file, geographics_file):
        util = _m.Modeller().tool("translink.util")

        mod = _m.Modeller()
        project = mod.desktop.project
        proj_path = os.path.dirname(project.path)


        # set directory locations for csv files and sqlite db
        file_loc= util.get_input_path(eb)

        # point to csv input files
        demo_file = demographics_file
        geo_file = geographics_file
        pnr_file = os.path.join(file_loc, 'taz1700_pnr.csv')
        dummy_file = os.path.join(file_loc,'taz1700_dummies.csv')
        ensem_file = os.path.join(proj_path, "BaseNetworks", "taz1700_ensembles.csv")
        time_slicing_file = os.path.join(file_loc,'time_slicing.csv')
        time_slicing_file_gb = os.path.join(file_loc,'time_slicing_gb.csv')


        # import raw data to mo's in emmebank
        util.read_csv_momd(eb, demo_file)
        util.read_csv_momd(eb, geo_file)
        util.read_csv_momd(eb, pnr_file)
        util.read_csv_momd(eb, dummy_file)

        # setup connection to sqlite database
        conn = util.get_rtm_db(eb)

        # read csvs and export to sqlite database

        # demographics
        df = pd.read_csv(demo_file, skiprows = 3)
        df.to_sql(name='demographics', con=conn, flavor='sqlite', index=False, if_exists='replace')

        # geographics
        df = pd.read_csv(geo_file, skiprows = 3)
        df.to_sql(name='geographics', con=conn, flavor='sqlite', index=False, if_exists='replace')

        # park and ride
        df = pd.read_csv(pnr_file, skiprows = 3)
        df.to_sql(name='parknride', con=conn, flavor='sqlite', index=False, if_exists='replace')

        # dummary variables
        df = pd.read_csv(dummy_file, skiprows = 3)
        df.to_sql(name='dummies', con=conn, flavor='sqlite', index=False, if_exists='replace')

        # ensembles
        df = pd.read_csv(ensem_file, skiprows = 3)
        df.to_sql(name='ensembles', con=conn, flavor='sqlite', index=False, if_exists='replace')

        # time_slicing
        df = pd.read_csv(time_slicing_file, skiprows = 0)
        df.to_sql(name='timeSlicingFactors', con=conn, flavor='sqlite', index=False, if_exists='replace')

        # time_slicing gb
        df = pd.read_csv(time_slicing_file_gb, skiprows = 0)
        df.to_sql(name='timeSlicingFactorsGb', con=conn, flavor='sqlite', index=False, if_exists='replace')

        conn.close()

    @_m.logbook_trace("Importing Seed Matrices")
    def init_seeds(self, eb, horizon_year):
        util = _m.Modeller().tool("translink.util")

        model_year = horizon_year
        mod = _m.Modeller()
        project = mod.desktop.project
        proj_path = os.path.dirname(project.path)


        mat_transaction = mod.tool("inro.emme.data.matrix.matrix_transaction")


        # Batch in starter auto demand used for generating starter skims, demand is aggregated into 4 classes, SOV, HOV, Light Tr, Heavy Tr


        util.delmat(eb, "mf20")
        util.delmat(eb, "mf21")
        data_path = os.path.join(proj_path, "BaseNetworks", "Starter_Demand_Truck_AM_2011.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

        util.delmat(eb, "mf40")
        util.delmat(eb, "mf41")
        data_path = os.path.join(proj_path, "BaseNetworks", "Starter_Demand_Truck_MD_2011.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

        util.delmat(eb, "mf60")
        util.delmat(eb, "mf61")
        data_path = os.path.join(proj_path, "BaseNetworks", "Starter_Demand_Truck_PM_2011.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)



		# Batch in bridge penalties and Kij factors used in trip distribution
		# TODO move the section below to somewhere more logical
        # bridge penalty factors
        util.delmat(eb, "mf92")
        util.delmat(eb, "mf93")
        data_path = os.path.join(proj_path, "BaseNetworks", "Bridge_Cross_Penalties.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

        # Kij Factors
        util.delmat(eb, "mf9200")
        util.delmat(eb, "mf9201")
        util.delmat(eb, "mf9202")
        util.delmat(eb, "mf9203")
        util.delmat(eb, "mf9204")
        util.delmat(eb, "mf9205")
        util.delmat(eb, "mf9206")
        util.delmat(eb, "mf9207")
        util.delmat(eb, "mf9208")

        data_path = os.path.join(proj_path, "BaseNetworks", "Kij_Factors.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

    @_m.logbook_trace("Importing Starter Skims for Warm Start")
    def starter_skims(self, eb, horizon_year):

        util = _m.Modeller().tool("translink.util")
        NoTAZ = len(util.get_matrix_numpy(eb, "zoneindex"))
        model_year = horizon_year
        project = _m.Modeller().desktop.project
        proj_path = os.path.dirname(project.path)

        skimData = os.path.join(proj_path, "BaseNetworks", "starter_skims.csv.gz")
        df = pd.read_csv(skimData, compression = 'gzip')

        # Set auto skims based on SOV VOT skims
        # AM
        util.set_matrix_numpy(eb, "mfAmSovOpCstVOT1", df['AmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmSovTimeVOT1", df['AmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmSovTollVOT1", df['AmAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmSovOpCstVOT2", df['AmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmSovTimeVOT2", df['AmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmSovTollVOT2", df['AmAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmSovOpCstVOT3", df['AmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmSovTimeVOT3", df['AmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmSovTollVOT3", df['AmAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmSovOpCstVOT4", df['AmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmSovTimeVOT4", df['AmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmSovTollVOT4", df['AmAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmHovOpCstVOT1",  df['AmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmHovTimeVOT1",  df['AmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmHovTollVOT1",  df['AmAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmHovOpCstVOT2", df['AmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmHovTimeVOT2", df['AmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmHovTollVOT2", df['AmAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmHovOpCstVOT3", df['AmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmHovTimeVOT3", df['AmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmHovTollVOT3", df['AmAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmHovOpCstVOT4", df['AmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmHovTimeVOT4", df['AmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmHovTollVOT4", df['AmAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmLgvOpCst", df['AmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmLgvTime", df['AmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmLgvToll", df['AmAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmHgvOpCst", df['AmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmHgvTime", df['AmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmHgvToll", df['AmAutoToll'].values.reshape(NoTAZ, NoTAZ))
        # MD
        util.set_matrix_numpy(eb, "mfMdSovOpCstVOT1", df['MdAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdSovTimeVOT1", df['MdAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdSovTollVOT1", df['MdAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdSovOpCstVOT2", df['MdAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdSovTimeVOT2", df['MdAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdSovTollVOT2", df['MdAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdSovOpCstVOT3", df['MdAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdSovTimeVOT3", df['MdAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdSovTollVOT3", df['MdAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdSovOpCstVOT4", df['MdAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdSovTimeVOT4", df['MdAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdSovTollVOT4", df['MdAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdHovOpCstVOT1",  df['MdAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdHovTimeVOT1",  df['MdAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdHovTollVOT1",  df['MdAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdHovOpCstVOT2", df['MdAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdHovTimeVOT2", df['MdAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdHovTollVOT2", df['MdAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdHovOpCstVOT3", df['MdAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdHovTimeVOT3", df['MdAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdHovTollVOT3", df['MdAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdHovOpCstVOT4", df['MdAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdHovTimeVOT4", df['MdAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdHovTollVOT4", df['MdAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdLgvOpCst", df['MdAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdLgvTime", df['MdAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdLgvToll", df['MdAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdHgvOpCst", df['MdAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdHgvTime", df['MdAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdHgvToll", df['MdAutoToll'].values.reshape(NoTAZ, NoTAZ))
        # PM
        util.set_matrix_numpy(eb, "mfPmSovOpCstVOT1", df['PmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmSovTimeVOT1", df['PmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmSovTollVOT1", df['PmAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmSovOpCstVOT2", df['PmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmSovTimeVOT2", df['PmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmSovTollVOT2", df['PmAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmSovOpCstVOT3", df['PmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmSovTimeVOT3", df['PmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmSovTollVOT3", df['PmAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmSovOpCstVOT4", df['PmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmSovTimeVOT4", df['PmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmSovTollVOT4", df['PmAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmHovOpCstVOT1",  df['PmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmHovTimeVOT1",  df['PmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmHovTollVOT1",  df['PmAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmHovOpCstVOT2", df['PmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmHovTimeVOT2", df['PmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmHovTollVOT2", df['PmAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmHovOpCstVOT3", df['PmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmHovTimeVOT3", df['PmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmHovTollVOT3", df['PmAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmHovOpCstVOT4", df['PmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmHovTimeVOT4", df['PmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmHovTollVOT4", df['PmAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmLgvOpCst", df['PmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmLgvTime", df['PmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmLgvToll", df['PmAutoToll'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmHgvOpCst", df['PmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmHgvTime", df['PmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmHgvToll", df['PmAutoToll'].values.reshape(NoTAZ, NoTAZ))

        del df

        # input external demand and bike score
        inData = os.path.join(proj_path, "BaseNetworks", "externals_bikescore_%s.csv.gz" % model_year)
        df_in = pd.read_csv(inData, compression = 'gzip')

        # SET external demand
        util.set_matrix_numpy(eb, "mfextSovAm", df_in['extSovAm'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfextHovAm", df_in['extHovAm'].values.reshape(NoTAZ, NoTAZ))

        util.set_matrix_numpy(eb, "mfextSovMd", df_in['extSovMd'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfextHovMd", df_in['extHovMd'].values.reshape(NoTAZ, NoTAZ))

		# TODO update external demand
		# Note PM external demand is AM transposed multiplied by a factor
        util.set_matrix_numpy(eb, "mfextSovPm", df_in['extSovPm'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfextHovPm", df_in['extHovPm'].values.reshape(NoTAZ, NoTAZ))

        # SET bike score
        util.set_matrix_numpy(eb, "mfbikeskim", df_in['bikeskim'].values.reshape(NoTAZ, NoTAZ))


    @_m.logbook_trace("Matrix Batchins")
    def matrix_batchins(self, eb):
        util = _m.Modeller().tool("translink.util")


        ########################################################################
        # skim matrices
        ########################################################################

        #####################
        # Auto
        #####################
        # AM
        util.initmat(eb, "mf5000", "AmSovOpCstVOT1", "Am Sov VOT1 Op Cost", 0)
        util.initmat(eb, "mf5001", "AmSovTimeVOT1", "Am Sov VOT1 Time", 0)
        util.initmat(eb, "mf5002", "AmSovTollVOT1", "Am Sov VOT1 Toll", 0)
        util.initmat(eb, "mf5003", "AmSovOpCstVOT2", "Am Sov VOT2 Op Cost", 0)
        util.initmat(eb, "mf5004", "AmSovTimeVOT2", "Am Sov VOT2 Time", 0)
        util.initmat(eb, "mf5005", "AmSovTollVOT2", "Am Sov VOT2 Toll", 0)
        util.initmat(eb, "mf5006", "AmSovOpCstVOT3", "Am Sov VOT3 Op Cost", 0)
        util.initmat(eb, "mf5007", "AmSovTimeVOT3", "Am Sov VOT3 Time", 0)
        util.initmat(eb, "mf5008", "AmSovTollVOT3", "Am Sov VOT3 Toll", 0)
        util.initmat(eb, "mf5009", "AmSovOpCstVOT4", "Am Sov VOT4 Op Cost", 0)
        util.initmat(eb, "mf5010", "AmSovTimeVOT4", "Am Sov VOT4 Time", 0)
        util.initmat(eb, "mf5011", "AmSovTollVOT4", "Am Sov VOT4 Toll", 0)
        util.initmat(eb, "mf5012", "AmHovOpCstVOT1", "Am Hov VOT1 Op Cost", 0)
        util.initmat(eb, "mf5013", "AmHovTimeVOT1", "Am Hov VOT1 Time", 0)
        util.initmat(eb, "mf5014", "AmHovTollVOT1", "Am Hov VOT1 Toll", 0)
        util.initmat(eb, "mf5015", "AmHovOpCstVOT2", "Am Hov VOT2 Op Cost", 0)
        util.initmat(eb, "mf5016", "AmHovTimeVOT2", "Am Hov VOT2 Time", 0)
        util.initmat(eb, "mf5017", "AmHovTollVOT2", "Am Hov VOT2 Toll", 0)
        util.initmat(eb, "mf5018", "AmHovOpCstVOT3", "Am Hov VOT3 Op Cost", 0)
        util.initmat(eb, "mf5019", "AmHovTimeVOT3", "Am Hov VOT3 Time", 0)
        util.initmat(eb, "mf5020", "AmHovTollVOT3", "Am Hov VOT3 Toll", 0)
        util.initmat(eb, "mf5021", "AmHovOpCstVOT4", "Am Hov VOT4 Op Cost", 0)
        util.initmat(eb, "mf5022", "AmHovTimeVOT4", "Am Hov VOT4 Time", 0)
        util.initmat(eb, "mf5023", "AmHovTollVOT4", "Am Hov VOT4 Toll", 0)
        util.initmat(eb, "mf5024", "AmLgvOpCst", "Am LGV Op Cost", 0)
        util.initmat(eb, "mf5025", "AmLgvTime", "Am LGV Time", 0)
        util.initmat(eb, "mf5026", "AmLgvToll", "Am LGV Toll", 0)
        util.initmat(eb, "mf5027", "AmHgvOpCst", "Am HGV Op Cost", 0)
        util.initmat(eb, "mf5028", "AmHgvTime", "Am HGV Time", 0)
        util.initmat(eb, "mf5029", "AmHgvToll", "Am HGV Toll", 0)
        # MD
        util.initmat(eb, "mf5030", "MdSovOpCstVOT1", "Md Sov VOT1 Op Cost", 0)
        util.initmat(eb, "mf5031", "MdSovTimeVOT1", "Md Sov VOT1 Time", 0)
        util.initmat(eb, "mf5032", "MdSovTollVOT1", "Md Sov VOT1 Toll", 0)
        util.initmat(eb, "mf5033", "MdSovOpCstVOT2", "Md Sov VOT2 Op Cost", 0)
        util.initmat(eb, "mf5034", "MdSovTimeVOT2", "Md Sov VOT2 Time", 0)
        util.initmat(eb, "mf5035", "MdSovTollVOT2", "Md Sov VOT2 Toll", 0)
        util.initmat(eb, "mf5036", "MdSovOpCstVOT3", "Md Sov VOT3 Op Cost", 0)
        util.initmat(eb, "mf5037", "MdSovTimeVOT3", "Md Sov VOT3 Time", 0)
        util.initmat(eb, "mf5038", "MdSovTollVOT3", "Md Sov VOT3 Toll", 0)
        util.initmat(eb, "mf5039", "MdSovOpCstVOT4", "Md Sov VOT4 Op Cost", 0)
        util.initmat(eb, "mf5040", "MdSovTimeVOT4", "Md Sov VOT4 Time", 0)
        util.initmat(eb, "mf5041", "MdSovTollVOT4", "Md Sov VOT4 Toll", 0)
        util.initmat(eb, "mf5042", "MdHovOpCstVOT1", "Md Hov VOT1 Op Cost", 0)
        util.initmat(eb, "mf5043", "MdHovTimeVOT1", "Md Hov VOT1 Time", 0)
        util.initmat(eb, "mf5044", "MdHovTollVOT1", "Md Hov VOT1 Toll", 0)
        util.initmat(eb, "mf5045", "MdHovOpCstVOT2", "Md Hov VOT2 Op Cost", 0)
        util.initmat(eb, "mf5046", "MdHovTimeVOT2", "Md Hov VOT2 Time", 0)
        util.initmat(eb, "mf5047", "MdHovTollVOT2", "Md Hov VOT2 Toll", 0)
        util.initmat(eb, "mf5048", "MdHovOpCstVOT3", "Md Hov VOT3 Op Cost", 0)
        util.initmat(eb, "mf5049", "MdHovTimeVOT3", "Md Hov VOT3 Time", 0)
        util.initmat(eb, "mf5050", "MdHovTollVOT3", "Md Hov VOT3 Toll", 0)
        util.initmat(eb, "mf5051", "MdHovOpCstVOT4", "Md Hov VOT4 Op Cost", 0)
        util.initmat(eb, "mf5052", "MdHovTimeVOT4", "Md Hov VOT4 Time", 0)
        util.initmat(eb, "mf5053", "MdHovTollVOT4", "Md Hov VOT4 Toll", 0)
        util.initmat(eb, "mf5054", "MdLgvOpCst", "Md LGV Op Cost", 0)
        util.initmat(eb, "mf5055", "MdLgvTime", "Md LGV Time", 0)
        util.initmat(eb, "mf5056", "MdLgvToll", "Md LGV Toll", 0)
        util.initmat(eb, "mf5057", "MdHgvOpCst", "Md HGV Op Cost", 0)
        util.initmat(eb, "mf5058", "MdHgvTime", "Md HGV Time", 0)
        util.initmat(eb, "mf5059", "MdHgvToll", "Md HGV Toll", 0)
        # PM
        util.initmat(eb, "mf5060", "PmSovOpCstVOT1", "Pm Sov VOT1 Op Cost", 0)
        util.initmat(eb, "mf5061", "PmSovTimeVOT1", "Pm Sov VOT1 Time", 0)
        util.initmat(eb, "mf5062", "PmSovTollVOT1", "Pm Sov VOT1 Toll", 0)
        util.initmat(eb, "mf5063", "PmSovOpCstVOT2", "Pm Sov VOT2 Op Cost", 0)
        util.initmat(eb, "mf5064", "PmSovTimeVOT2", "Pm Sov VOT2 Time", 0)
        util.initmat(eb, "mf5065", "PmSovTollVOT2", "Pm Sov VOT2 Toll", 0)
        util.initmat(eb, "mf5066", "PmSovOpCstVOT3", "Pm Sov VOT3 Op Cost", 0)
        util.initmat(eb, "mf5067", "PmSovTimeVOT3", "Pm Sov VOT3 Time", 0)
        util.initmat(eb, "mf5068", "PmSovTollVOT3", "Pm Sov VOT3 Toll", 0)
        util.initmat(eb, "mf5069", "PmSovOpCstVOT4", "Pm Sov VOT4 Op Cost", 0)
        util.initmat(eb, "mf5070", "PmSovTimeVOT4", "Pm Sov VOT4 Time", 0)
        util.initmat(eb, "mf5071", "PmSovTollVOT4", "Pm Sov VOT4 Toll", 0)
        util.initmat(eb, "mf5072", "PmHovOpCstVOT1", "Pm Hov VOT1 Op Cost", 0)
        util.initmat(eb, "mf5073", "PmHovTimeVOT1", "Pm Hov VOT1 Time", 0)
        util.initmat(eb, "mf5074", "PmHovTollVOT1", "Pm Hov VOT1 Toll", 0)
        util.initmat(eb, "mf5075", "PmHovOpCstVOT2", "Pm Hov VOT2 Op Cost", 0)
        util.initmat(eb, "mf5076", "PmHovTimeVOT2", "Pm Hov VOT2 Time", 0)
        util.initmat(eb, "mf5077", "PmHovTollVOT2", "Pm Hov VOT2 Toll", 0)
        util.initmat(eb, "mf5078", "PmHovOpCstVOT3", "Pm Hov VOT3 Op Cost", 0)
        util.initmat(eb, "mf5079", "PmHovTimeVOT3", "Pm Hov VOT3 Time", 0)
        util.initmat(eb, "mf5080", "PmHovTollVOT3", "Pm Hov VOT3 Toll", 0)
        util.initmat(eb, "mf5081", "PmHovOpCstVOT4", "Pm Hov VOT4 Op Cost", 0)
        util.initmat(eb, "mf5082", "PmHovTimeVOT4", "Pm Hov VOT4 Time", 0)
        util.initmat(eb, "mf5083", "PmHovTollVOT4", "Pm Hov VOT4 Toll", 0)
        util.initmat(eb, "mf5084", "PmLgvOpCst", "Pm LGV Op Cost", 0)
        util.initmat(eb, "mf5085", "PmLgvTime", "Pm LGV Time", 0)
        util.initmat(eb, "mf5086", "PmLgvToll", "Pm LGV Toll", 0)
        util.initmat(eb, "mf5087", "PmHgvOpCst", "Pm HGV Op Cost", 0)
        util.initmat(eb, "mf5088", "PmHgvTime", "Pm HGV Time", 0)
        util.initmat(eb, "mf5089", "PmHgvToll", "Pm HGV Toll", 0)

        #####################
        # Bus
        #####################
        # AM
        util.initmat(eb, "mf5300", "AmBusIvtt", "Am Bus InVehicle Time", 0)
        util.initmat(eb, "mf5301", "AmBusWait", "Am Bus Waiting Time", 0)
        util.initmat(eb, "mf5302", "AmBusAux", "Am Bus Auxillary Time", 0)
        util.initmat(eb, "mf5303", "AmBusBoard", "Am Bus Boardings", 0)
        util.initmat(eb, "mf5304", "AmBusFare", "Am Bus Fare", 0)
        # MD
        util.initmat(eb, "mf5310", "MdBusIvtt", "Md Bus InVehicle Time", 0)
        util.initmat(eb, "mf5311", "MdBusWait", "Md Bus Waiting Time", 0)
        util.initmat(eb, "mf5312", "MdBusAux", "Md Bus Auxillary Time", 0)
        util.initmat(eb, "mf5313", "MdBusBoard", "Md Bus Boardings", 0)
        util.initmat(eb, "mf5314", "MdBusFare", "Md Bus Fare", 0)
        # PM
        util.initmat(eb, "mf5320", "PmBusIvtt", "Pm Bus InVehicle Time", 0)
        util.initmat(eb, "mf5321", "PmBusWait", "Pm Bus Waiting Time", 0)
        util.initmat(eb, "mf5322", "PmBusAux", "Pm Bus Auxillary Time", 0)
        util.initmat(eb, "mf5323", "PmBusBoard", "Pm Bus Boardings", 0)
        util.initmat(eb, "mf5324", "PmBusFare", "Pm Bus Fare", 0)

        #####################
        # Rail
        #####################
        # AM
        util.initmat(eb, "mf5500", "AmRailIvtt", "Am Rail Invehicle Time", 0)
        util.initmat(eb, "mf5501", "AmRailIvttBus", "Am Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5502", "AmRailWait", "Am Rail Waiting Time", 0)
        util.initmat(eb, "mf5503", "AmRailAux", "Am Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5504", "AmRailBoard", "Am Rail Boardings", 0)
        util.initmat(eb, "mf5505", "AmRailFare", "Am Rail Fare", 0)
        # MD
        util.initmat(eb, "mf5510", "MdRailIvtt", "Md Rail Invehicle Time", 0)
        util.initmat(eb, "mf5511", "MdRailIvttBus", "Md Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5512", "MdRailWait", "Md Rail Waiting Time", 0)
        util.initmat(eb, "mf5513", "MdRailAux", "Md Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5514", "MdRailBoard", "Md Rail Boardings", 0)
        util.initmat(eb, "mf5515", "MdRailFare", "Md Rail Fare", 0)
        # PM
        util.initmat(eb, "mf5520", "PmRailIvtt", "Pm Rail Invehicle Time", 0)
        util.initmat(eb, "mf5521", "PmRailIvttBus", "Pm Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5522", "PmRailWait", "Pm Rail Waiting Time", 0)
        util.initmat(eb, "mf5523", "PmRailAux", "Pm Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5524", "PmRailBoard", "Pm Rail Boardings", 0)
        util.initmat(eb, "mf5525", "PmRailFare", "Pm Rail Fare", 0)

        #####################
        # WCE
        #####################
        # AM
        util.initmat(eb, "mf5700", "AmWceIvtt", "Am Rail Invehicle Time", 0)
        util.initmat(eb, "mf5701", "AmWceIvttRail", "Am Rail Invehicle Time on Rail", 0)
        util.initmat(eb, "mf5702", "AmWceIvttBus", "Am Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5703", "AmWceWait", "Am Rail Waiting Time", 0)
        util.initmat(eb, "mf5704", "AmWceAux", "Am Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5705", "AmWceBoard", "Am Rail Boardings", 0)
        util.initmat(eb, "mf5706", "AmWceFare", "Am Rail Fare", 0)
        # MD
        util.initmat(eb, "mf5710", "MdWceIvtt", "Md Rail Invehicle Time", 0)
        util.initmat(eb, "mf5711", "MdWceIvttRail", "Md Rail Invehicle Time on Rail", 0)
        util.initmat(eb, "mf5712", "MdWceIvttBus", "Md Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5713", "MdWceWait", "Md Rail Waiting Time", 0)
        util.initmat(eb, "mf5714", "MdWceAux", "Md Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5715", "MdWceBoard", "Md Rail Boardings", 0)
        util.initmat(eb, "mf5716", "MdWceFare", "Md Rail Fare", 0)
        # PM
        util.initmat(eb, "mf5720", "PmWceIvtt", "Pm Rail Invehicle Time", 0)
        util.initmat(eb, "mf5721", "PmWceIvttRail", "Pm Rail Invehicle Time on Rail", 0)
        util.initmat(eb, "mf5722", "PmWceIvttBus", "Pm Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5723", "PmWceWait", "Pm Rail Waiting Time", 0)
        util.initmat(eb, "mf5724", "PmWceAux", "Pm Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5725", "PmWceBoard", "Pm Rail Boardings", 0)
        util.initmat(eb, "mf5726", "PmWceFare", "Pm Rail Fare", 0)

        # External Demand and bikescore
        util.initmat(eb, "mf70", "extSovAm", "External Demand SOV AM", 0)
        util.initmat(eb, "mf71", "extHovAm", "External Demand HOV AM", 0)

        util.initmat(eb, "mf75", "extSovMd", "External Demand SOV MD", 0)
        util.initmat(eb, "mf76", "extHovMd", "External Demand HOV MD", 0)

        util.initmat(eb, "mf80", "extSovPm", "External Demand SOV PM", 0)
        util.initmat(eb, "mf81", "extHovPm", "External Demand HOV PM", 0)

        util.initmat(eb, "mf90", "bikeskim", "Weighted Average IJ bike score", 0)
