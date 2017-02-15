##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: ?
##--Purpose: Import Data for RTM Run
##---------------------------------------------------------------------

import inro.modeller as _m

import traceback as _traceback
import os
import csv as csv


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

        self.init_scalars(eb)
        self.import_vectors(eb, demographics_file, geographics_file)

        self.init_seeds(eb, horizon_year=model_year)

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
        util.delmat(eb, "mf10")
        util.delmat(eb, "mf11")
        data_path = os.path.join(proj_path, "BaseNetworks", "Starter_Demand_AM.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

        util.delmat(eb, "mf30")
        util.delmat(eb, "mf31")
        data_path = os.path.join(proj_path, "BaseNetworks", "Starter_Demand_MD.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

        util.delmat(eb, "mf50")
        util.delmat(eb, "mf51")
        data_path = os.path.join(proj_path, "BaseNetworks", "Starter_Demand_PM.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

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

        # Batch in external demand matrices
        util.delmat(eb, "mf70")
        util.delmat(eb, "mf71")
        data_path = os.path.join(proj_path, "BaseNetworks", "External_Demand_AM_%s.in" % model_year)
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

        util.delmat(eb, "mf75")
        util.delmat(eb, "mf76")
        data_path = os.path.join(proj_path, "BaseNetworks", "External_Demand_MD_%s.in" % model_year)
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

		# TODO update external demand
		# Note PM external demand is AM transposed multiplied by a factor
        util.delmat(eb, "mf80")
        util.delmat(eb, "mf81")
        data_path = os.path.join(proj_path, "BaseNetworks", "External_Demand_PM_%s.in" % model_year)
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)


        util.delmat(eb, "mf90")
        data_path = os.path.join(proj_path, "BaseNetworks", "bike_score_skim_%s.in" % model_year)
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
