##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage0.data_import
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

        self.starter_skims(eb, horizon_year=model_year)
        self.update_ensembles(eb)

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

        util.initmat(eb, "ms150", "lgvTollFac", "LGV toll factor", 2.0)
        util.initmat(eb, "ms151", "hgvTollFac", "HGV toll factor", 3.0)
        util.initmat(eb, "ms152", "sovTollFac", "SOV toll factor", 1.0)
        util.initmat(eb, "ms153", "hovTollFac", "HOV toll factor", 1.0)
        util.initmat(eb, "ms154", "BRTASCFactor", "BRT Percent of Rail ASC", 0.375)
        util.initmat(eb, "ms155", "LRTASCFactor", "LRT Percent of Rail ASC", 0.500)
        util.initmat(eb, "ms156", "BRTIVTFactor", "BRT Percent of Rail IVT", 0.333)
        util.initmat(eb, "ms157", "LRTIVTFactor", "LRT Percent of Rail IVT", 0.666)

        util.initmat(eb, "ms160", "oneZoneFare", "One Zone Fare - FS-SV", 2.1)
        util.initmat(eb, "ms161", "fareIncrement", "Fare Increment", 1.05)

        util.initmat(eb, "ms162", "wce_bfare_zone1_1", "wce_bfare_zone1_1", 0)
        util.initmat(eb, "ms163", "wce_bfare_zone1_2", "wce_bfare_zone1_2", 0)
        util.initmat(eb, "ms164", "wce_bfare_zone1_3", "wce_bfare_zone1_3", 5.03)

        util.initmat(eb, "ms165", "wce_bfare_zone3_1", "wce_bfare_zone3_1", 2.12)
        util.initmat(eb, "ms166", "wce_bfare_zone3_2", "wce_bfare_zone3_2", 0)
        util.initmat(eb, "ms167", "wce_bfare_zone3_3", "wce_bfare_zone3_3", 2.72)

        util.initmat(eb, "ms168", "wce_bfare_zone4_1", "wce_bfare_zone4_1", 2.10)
        util.initmat(eb, "ms169", "wce_bfare_zone4_2", "wce_bfare_zone4_2", 0)
        util.initmat(eb, "ms170", "wce_bfare_zone4_3", "wce_bfare_zone4_3", 2.10)

        util.initmat(eb, "ms171", "wce_bfare_zone5_1", "wce_bfare_zone5_1", 3.79)
        util.initmat(eb, "ms172", "wce_bfare_zone5_2", "wce_bfare_zone5_2", 0)
        util.initmat(eb, "ms173", "wce_bfare_zone5_3", "wce_bfare_zone5_3", 0)

        util.initmat(eb, "ms174", "wce_bfare_zone13_1", "wce_bfare_zone13_1", 2.91)
        util.initmat(eb, "ms175", "wce_bfare_zone13_2", "wce_bfare_zone13_2", 0)
        util.initmat(eb, "ms176", "wce_bfare_zone13_3", "wce_bfare_zone13_3", 0)

        util.initmat(eb, "ms177", "wce_bfare_zone34_1", "wce_bfare_zone34_1", 1.69)
        util.initmat(eb, "ms178", "wce_bfare_zone34_2", "wce_bfare_zone34_2", 0)
        util.initmat(eb, "ms179", "wce_bfare_zone34_3", "wce_bfare_zone34_3", 1.08)

        util.initmat(eb, "ms180", "wce_bfare_zone45_1", "wce_bfare_zone34_1", 1.69)
        util.initmat(eb, "ms181", "wce_bfare_zone45_2", "wce_bfare_zone34_2", 0)
        util.initmat(eb, "ms182", "wce_bfare_zone45_3", "wce_bfare_zone34_3", 1.08)

        util.initmat(eb, "ms190", "wce_fare_1z", "wce_fare_1z", 3.79)
        util.initmat(eb, "ms191", "wce_fare_2z", "wce_fare_2z", 3.79)
        util.initmat(eb, "ms192", "wce_fare_3z", "wce_fare_3z", 5.03)
        util.initmat(eb, "ms193", "wce_fare_4z", "wce_fare_4z", 6.10)
        util.initmat(eb, "ms194", "wce_fare_5z", "wce_fare_5z", 8.39)


        # Used for SOV and HOV
        util.initmat(eb, "ms200", "AutoVOT1", "AutoVOT1", 9.5)
        util.initmat(eb, "ms201", "AutoVOT2", "AutoVOT2", 5.8)

        # Used for SOV only
        util.initmat(eb, "ms202", "AutoVOT3", "AutoVOT3", 3.9)
        util.initmat(eb, "ms203", "AutoVOT4", "AutoVOT4", 3.3)

        # Used for HOV only
        util.initmat(eb, "ms204", "AutoVOT5", "AutoVOT5", 3.6)

        util.initmat(eb, "ms212", "VotBus", "VOT Work", 4.9)
        util.initmat(eb, "ms213", "VotRail", "VOT Work", 4.9)
        util.initmat(eb, "ms214", "VotWce", "VOT Work", 4.9)

        util.initmat(eb, "ms218", "VotLgv", "VOT lgv", 2.03)
        util.initmat(eb, "ms219", "VotHgv", "VOT hgv", 1.43)
        util.initmat(eb, "ms300", "busIVTprcpWk", "bus in-vehicle time perception work", 1.25)
        util.initmat(eb, "ms301", "busWAITprcpWk", "bus wait time perception work", 2.50)
        util.initmat(eb, "ms302", "busWALKprcpWk", "bus walk time perception work", 2.00)
        util.initmat(eb, "ms303", "busBOARDSprcpWk", "bus boarding perception work", 10.00)
        util.initmat(eb, "ms310", "railIVTprcpWk", "rail in-vehicle time perception work", 1.00)
        util.initmat(eb, "ms311", "railWAITprcpWk", "rail wait time perception work", 2.50)  # 3.13
        util.initmat(eb, "ms312", "railWALKprcpWk", "rail walk time perception work", 2.00)  # 2.50
        util.initmat(eb, "ms313", "railBOARDSprcpWk", "rail boarding perception work", 10.00)  # 12.50
        util.initmat(eb, "ms320", "wceIVTprcpWk", "wce in-vehicle time perception work", 1.00)
        util.initmat(eb, "ms321", "wceWAITprcpWk", "wce wait time perception work", 2.50)  # 3.13
        util.initmat(eb, "ms322", "wceWALKprcpWk", "wce walk time perception work", 2.00)  # 2.50
        util.initmat(eb, "ms323", "wceBOARDSprcpWk", "wce boarding perception work", 10.00)  # 12.50
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

        ##      Park and Ride Best Lot Calibration factors
        util.initmat(eb, "ms365", "busIVTpr_cal_railGT", "BusIVT percep RailGT Cal", 1.0)
        util.initmat(eb, "ms366", "transfer_cal_railGT", "transfer percep RailGT Cal", 1.0)



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

        custom_scalars = os.path.join(util.get_input_path(eb), 'custom_scalars.csv')
        if os.path.isfile(custom_scalars):
            util.read_csv_ms(eb, custom_scalars)

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
        transit_adj = os.path.join(file_loc,'transit_adj.csv')

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

        # transit bias adjustments
        df = pd.read_csv(transit_adj, skiprows = 0)
        df.to_sql(name='transit_adj', con=conn, flavor='sqlite', index=False, if_exists='replace')

        conn.close()

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
        util.set_matrix_numpy(eb, "mfAmSovOpCstVOT2", df['AmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmSovTimeVOT2", df['AmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmSovOpCstVOT3", df['AmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmSovTimeVOT3", df['AmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmSovOpCstVOT4", df['AmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmSovTimeVOT4", df['AmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmHovOpCstVOT1",  df['AmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmHovTimeVOT1",  df['AmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmHovOpCstVOT2", df['AmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmHovTimeVOT2", df['AmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmHovOpCstVOT3", df['AmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmHovTimeVOT3", df['AmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmHovOpCstVOT4", df['AmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmHovTimeVOT4", df['AmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmLgvOpCst", df['AmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmLgvTime", df['AmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmHgvOpCst", df['AmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfAmHgvTime", df['AmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        # MD
        util.set_matrix_numpy(eb, "mfMdSovOpCstVOT1", df['MdAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdSovTimeVOT1", df['MdAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdSovOpCstVOT2", df['MdAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdSovTimeVOT2", df['MdAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdSovOpCstVOT3", df['MdAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdSovTimeVOT3", df['MdAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdSovOpCstVOT4", df['MdAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdSovTimeVOT4", df['MdAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdHovOpCstVOT1",  df['MdAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdHovTimeVOT1",  df['MdAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdHovOpCstVOT2", df['MdAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdHovTimeVOT2", df['MdAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdHovOpCstVOT3", df['MdAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdHovTimeVOT3", df['MdAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdHovOpCstVOT4", df['MdAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdHovTimeVOT4", df['MdAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdLgvOpCst", df['MdAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdLgvTime", df['MdAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdHgvOpCst", df['MdAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfMdHgvTime", df['MdAutoTime'].values.reshape(NoTAZ, NoTAZ))
        # PM
        util.set_matrix_numpy(eb, "mfPmSovOpCstVOT1", df['PmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmSovTimeVOT1", df['PmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmSovOpCstVOT2", df['PmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmSovTimeVOT2", df['PmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmSovOpCstVOT3", df['PmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmSovTimeVOT3", df['PmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmSovOpCstVOT4", df['PmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmSovTimeVOT4", df['PmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmHovOpCstVOT1",  df['PmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmHovTimeVOT1",  df['PmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmHovOpCstVOT2", df['PmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmHovTimeVOT2", df['PmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmHovOpCstVOT3", df['PmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmHovTimeVOT3", df['PmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmHovOpCstVOT4", df['PmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmHovTimeVOT4", df['PmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmLgvOpCst", df['PmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmLgvTime", df['PmAutoTime'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmHgvOpCst", df['PmAutoOpCst'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfPmHgvTime", df['PmAutoTime'].values.reshape(NoTAZ, NoTAZ))

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

        # SET demand adjust demand
        util.set_matrix_numpy(eb, "mfMD_Demadj", df_in['md_adj'].values.reshape(NoTAZ, NoTAZ))

        # SET bike score
        util.set_matrix_numpy(eb, "mfbikeskim", df_in['bikeskim'].values.reshape(NoTAZ, NoTAZ))

        del df_in

        # input trip distribution variables
        dfe = util.get_ijensem_df(eb, ensem_o='gy')
        distData = os.path.join(proj_path, "BaseNetworks", "dist_factors_gy.csv.gz")
        dfd = pd.read_csv(distData, compression = 'gzip')
        df = pd.merge(dfe, dfd, how='left', left_on=['gy_i','gy_j'], right_on = ['gy_i','gy_j'])

        # SET trip distribution variables
        util.set_matrix_numpy(eb, "mfKij_hbw", df['Kij_hbw'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfKij_hbu", df['Kij_hbu'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfKij_hbsch", df['Kij_hbsch'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfKij_hbshop", df['Kij_hbshop'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfKij_hbpb", df['Kij_hbpb'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfKij_hbsoc", df['Kij_hbsoc'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfKij_hbesc", df['Kij_hbesc'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfKij_nhbw", df['Kij_nhbw'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfKij_nhbo", df['Kij_nhbo'].values.reshape(NoTAZ, NoTAZ))

        util.set_matrix_numpy(eb, "mfBridge_pen_AM", df['Bridge_pen_AM'].values.reshape(NoTAZ, NoTAZ))
        util.set_matrix_numpy(eb, "mfBridge_pen_PM", df['Bridge_pen_PM'].values.reshape(NoTAZ, NoTAZ))

        # input fare zones travelled data
        dfe = util.get_ijensem_df(eb, ensem_o='gy')
        fareData = os.path.join(proj_path, "BaseNetworks", "fare_zones_travelled.csv.gz")
        dfd = pd.read_csv(fareData, compression = 'gzip')
        df = pd.merge(dfe, dfd, how='left', left_on=['gy_i','gy_j'], right_on = ['gy_i','gy_j'])

        # Set fare zones matrix
        util.set_matrix_numpy(eb, "fare_zones", df['Zones_Travelled'].values.reshape(NoTAZ, NoTAZ))


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
        util.initmat(eb, "mf5003", "AmSovOpCstVOT2", "Am Sov VOT2 Op Cost", 0)
        util.initmat(eb, "mf5004", "AmSovTimeVOT2", "Am Sov VOT2 Time", 0)
        util.initmat(eb, "mf5006", "AmSovOpCstVOT3", "Am Sov VOT3 Op Cost", 0)
        util.initmat(eb, "mf5007", "AmSovTimeVOT3", "Am Sov VOT3 Time", 0)
        util.initmat(eb, "mf5009", "AmSovOpCstVOT4", "Am Sov VOT4 Op Cost", 0)
        util.initmat(eb, "mf5010", "AmSovTimeVOT4", "Am Sov VOT4 Time", 0)
        util.initmat(eb, "mf5012", "AmHovOpCstVOT1", "Am Hov VOT1 Op Cost", 0)
        util.initmat(eb, "mf5013", "AmHovTimeVOT1", "Am Hov VOT1 Time", 0)
        util.initmat(eb, "mf5015", "AmHovOpCstVOT2", "Am Hov VOT2 Op Cost", 0)
        util.initmat(eb, "mf5016", "AmHovTimeVOT2", "Am Hov VOT2 Time", 0)
        util.initmat(eb, "mf5018", "AmHovOpCstVOT3", "Am Hov VOT3 Op Cost", 0)
        util.initmat(eb, "mf5019", "AmHovTimeVOT3", "Am Hov VOT3 Time", 0)
        util.initmat(eb, "mf5021", "AmHovOpCstVOT4", "Am Hov VOT4 Op Cost", 0)
        util.initmat(eb, "mf5022", "AmHovTimeVOT4", "Am Hov VOT4 Time", 0)
        util.initmat(eb, "mf5024", "AmLgvOpCst", "Am LGV Op Cost", 0)
        util.initmat(eb, "mf5025", "AmLgvTime", "Am LGV Time", 0)
        util.initmat(eb, "mf5027", "AmHgvOpCst", "Am HGV Op Cost", 0)
        util.initmat(eb, "mf5028", "AmHgvTime", "Am HGV Time", 0)
        # MD
        util.initmat(eb, "mf5030", "MdSovOpCstVOT1", "Md Sov VOT1 Op Cost", 0)
        util.initmat(eb, "mf5031", "MdSovTimeVOT1", "Md Sov VOT1 Time", 0)
        util.initmat(eb, "mf5033", "MdSovOpCstVOT2", "Md Sov VOT2 Op Cost", 0)
        util.initmat(eb, "mf5034", "MdSovTimeVOT2", "Md Sov VOT2 Time", 0)
        util.initmat(eb, "mf5036", "MdSovOpCstVOT3", "Md Sov VOT3 Op Cost", 0)
        util.initmat(eb, "mf5037", "MdSovTimeVOT3", "Md Sov VOT3 Time", 0)
        util.initmat(eb, "mf5039", "MdSovOpCstVOT4", "Md Sov VOT4 Op Cost", 0)
        util.initmat(eb, "mf5040", "MdSovTimeVOT4", "Md Sov VOT4 Time", 0)
        util.initmat(eb, "mf5042", "MdHovOpCstVOT1", "Md Hov VOT1 Op Cost", 0)
        util.initmat(eb, "mf5043", "MdHovTimeVOT1", "Md Hov VOT1 Time", 0)
        util.initmat(eb, "mf5045", "MdHovOpCstVOT2", "Md Hov VOT2 Op Cost", 0)
        util.initmat(eb, "mf5046", "MdHovTimeVOT2", "Md Hov VOT2 Time", 0)
        util.initmat(eb, "mf5048", "MdHovOpCstVOT3", "Md Hov VOT3 Op Cost", 0)
        util.initmat(eb, "mf5049", "MdHovTimeVOT3", "Md Hov VOT3 Time", 0)
        util.initmat(eb, "mf5051", "MdHovOpCstVOT4", "Md Hov VOT4 Op Cost", 0)
        util.initmat(eb, "mf5052", "MdHovTimeVOT4", "Md Hov VOT4 Time", 0)
        util.initmat(eb, "mf5054", "MdLgvOpCst", "Md LGV Op Cost", 0)
        util.initmat(eb, "mf5055", "MdLgvTime", "Md LGV Time", 0)
        util.initmat(eb, "mf5057", "MdHgvOpCst", "Md HGV Op Cost", 0)
        util.initmat(eb, "mf5058", "MdHgvTime", "Md HGV Time", 0)
        # PM
        util.initmat(eb, "mf5060", "PmSovOpCstVOT1", "Pm Sov VOT1 Op Cost", 0)
        util.initmat(eb, "mf5061", "PmSovTimeVOT1", "Pm Sov VOT1 Time", 0)
        util.initmat(eb, "mf5063", "PmSovOpCstVOT2", "Pm Sov VOT2 Op Cost", 0)
        util.initmat(eb, "mf5064", "PmSovTimeVOT2", "Pm Sov VOT2 Time", 0)
        util.initmat(eb, "mf5066", "PmSovOpCstVOT3", "Pm Sov VOT3 Op Cost", 0)
        util.initmat(eb, "mf5067", "PmSovTimeVOT3", "Pm Sov VOT3 Time", 0)
        util.initmat(eb, "mf5069", "PmSovOpCstVOT4", "Pm Sov VOT4 Op Cost", 0)
        util.initmat(eb, "mf5070", "PmSovTimeVOT4", "Pm Sov VOT4 Time", 0)
        util.initmat(eb, "mf5072", "PmHovOpCstVOT1", "Pm Hov VOT1 Op Cost", 0)
        util.initmat(eb, "mf5073", "PmHovTimeVOT1", "Pm Hov VOT1 Time", 0)
        util.initmat(eb, "mf5075", "PmHovOpCstVOT2", "Pm Hov VOT2 Op Cost", 0)
        util.initmat(eb, "mf5076", "PmHovTimeVOT2", "Pm Hov VOT2 Time", 0)
        util.initmat(eb, "mf5078", "PmHovOpCstVOT3", "Pm Hov VOT3 Op Cost", 0)
        util.initmat(eb, "mf5079", "PmHovTimeVOT3", "Pm Hov VOT3 Time", 0)
        util.initmat(eb, "mf5081", "PmHovOpCstVOT4", "Pm Hov VOT4 Op Cost", 0)
        util.initmat(eb, "mf5082", "PmHovTimeVOT4", "Pm Hov VOT4 Time", 0)
        util.initmat(eb, "mf5084", "PmLgvOpCst", "Pm LGV Op Cost", 0)
        util.initmat(eb, "mf5085", "PmLgvTime", "Pm LGV Time", 0)
        util.initmat(eb, "mf5087", "PmHgvOpCst", "Pm HGV Op Cost", 0)
        util.initmat(eb, "mf5088", "PmHgvTime", "Pm HGV Time", 0)

        #####################
        # Bus
        #####################
        # AM
        util.initmat(eb, "mf5300", "AmBusIvtt", "Am Bus InVehicle Time", 0)
        util.initmat(eb, "mf5301", "AmBusWait", "Am Bus Waiting Time", 0)
        util.initmat(eb, "mf5302", "AmBusAux", "Am Bus Auxillary Time", 0)
        util.initmat(eb, "mf5303", "AmBusBoard", "Am Bus Boardings", 0)
        util.initmat(eb, "mf5304", "AmBusFare", "Am Bus Fare", 0)
        util.initmat(eb, "mf5305", "AmBusIvttBRT", "Am Bus BRT InVehicle Time", 0)
        # MD
        util.initmat(eb, "mf5310", "MdBusIvtt", "Md Bus InVehicle Time", 0)
        util.initmat(eb, "mf5311", "MdBusWait", "Md Bus Waiting Time", 0)
        util.initmat(eb, "mf5312", "MdBusAux", "Md Bus Auxillary Time", 0)
        util.initmat(eb, "mf5313", "MdBusBoard", "Md Bus Boardings", 0)
        util.initmat(eb, "mf5314", "MdBusFare", "Md Bus Fare", 0)
        util.initmat(eb, "mf5315", "MdBusIvttBRT", "Md Bus BRT InVehicle Time", 0)
        # PM
        util.initmat(eb, "mf5320", "PmBusIvtt", "Pm Bus InVehicle Time", 0)
        util.initmat(eb, "mf5321", "PmBusWait", "Pm Bus Waiting Time", 0)
        util.initmat(eb, "mf5322", "PmBusAux", "Pm Bus Auxillary Time", 0)
        util.initmat(eb, "mf5323", "PmBusBoard", "Pm Bus Boardings", 0)
        util.initmat(eb, "mf5324", "PmBusFare", "Pm Bus Fare", 0)
        util.initmat(eb, "mf5325", "PmBusIvttBRT", "Pm Bus BRT InVehicle Time", 0)

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
        util.initmat(eb, "mf5506", "AmRailIvttBRT", "Am Rail Invehicle Time on BRT", 0)
        util.initmat(eb, "mf5507", "AmRailIvttLRT", "Am Rail Invehicle Time on LRT", 0)
        # MD
        util.initmat(eb, "mf5510", "MdRailIvtt", "Md Rail Invehicle Time", 0)
        util.initmat(eb, "mf5511", "MdRailIvttBus", "Md Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5512", "MdRailWait", "Md Rail Waiting Time", 0)
        util.initmat(eb, "mf5513", "MdRailAux", "Md Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5514", "MdRailBoard", "Md Rail Boardings", 0)
        util.initmat(eb, "mf5515", "MdRailFare", "Md Rail Fare", 0)
        util.initmat(eb, "mf5516", "MdRailIvttBRT", "Md Rail Invehicle Time on BRT", 0)
        util.initmat(eb, "mf5517", "MdRailIvttLRT", "Md Rail Invehicle Time on LRT", 0)
        # PM
        util.initmat(eb, "mf5520", "PmRailIvtt", "Pm Rail Invehicle Time", 0)
        util.initmat(eb, "mf5521", "PmRailIvttBus", "Pm Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5522", "PmRailWait", "Pm Rail Waiting Time", 0)
        util.initmat(eb, "mf5523", "PmRailAux", "Pm Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5524", "PmRailBoard", "Pm Rail Boardings", 0)
        util.initmat(eb, "mf5525", "PmRailFare", "Pm Rail Fare", 0)
        util.initmat(eb, "mf5526", "PmRailIvttBRT", "Pm Rail Invehicle Time on BRT", 0)
        util.initmat(eb, "mf5527", "PmRailIvttLRT", "Pm Rail Invehicle Time on LRT", 0)

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

        # External Demand, MD Demand Adjust incremental demand and bikescore
        util.initmat(eb, "mf70", "extSovAm", "External Demand SOV AM", 0)
        util.initmat(eb, "mf71", "extHovAm", "External Demand HOV AM", 0)

        util.initmat(eb, "mf75", "extSovMd", "External Demand SOV MD", 0)
        util.initmat(eb, "mf76", "extHovMd", "External Demand HOV MD", 0)

        util.initmat(eb, "mf80", "extSovPm", "External Demand SOV PM", 0)
        util.initmat(eb, "mf81", "extHovPm", "External Demand HOV PM", 0)

        util.initmat(eb, "mf90", "bikeskim", "Weighted Average IJ bike score", 0)

        util.initmat(eb, "mf85", "MD_Demadj", "MD Incr Calibration Matrix", 0)

        # Trip Distribution Variables
        util.initmat(eb, "mf9200", "Kij_hbw", "Kij_hbw", 0)
        util.initmat(eb, "mf9201", "Kij_hbu", "Kij_hbu", 0)
        util.initmat(eb, "mf9202", "Kij_hbsch", "Kij_hbsch", 0)
        util.initmat(eb, "mf9203", "Kij_hbshop", "Kij_hbshop", 0)
        util.initmat(eb, "mf9204", "Kij_hbpb", "Kij_hbpb", 0)
        util.initmat(eb, "mf9205", "Kij_hbsoc", "Kij_hbsoc", 0)
        util.initmat(eb, "mf9206", "Kij_hbesc", "Kij_hbesc", 0)
        util.initmat(eb, "mf9207", "Kij_nhbw", "Kij_nhbw", 0)
        util.initmat(eb, "mf9208", "Kij_nhbo", "Kij_nhbo", 0)

        util.initmat(eb, "mf92", "Bridge_pen_AM", "Bridge_pen_AM", 0)
        util.initmat(eb, "mf93", "Bridge_pen_PM", "Bridge_pen_PM", 0)

        # Fare Zones Travelled
        util.initmat(eb, "mf95", "fare_zones", "Fare Zones Travelled", 0)
   
    @_m.logbook_trace("Importing custom ensembles if custom ensemble CSV file is available")
    def update_ensembles(self, eb):
        util = _m.Modeller().tool("translink.util")
        
        # Code to check if a custom ensemble file exists and if yes - 
        # replace the values read in the code above       
        custom_ensembles = os.path.join(util.get_input_path(eb), 'custom_ensembles.csv')
        if os.path.isfile(custom_ensembles):
            util.read_csv_momd(eb, custom_ensembles)

            # Read Ensemble MOs .. the function is defined in Utilities script now
            util.set_ensemble_from_mo(eb, "ga", "mo120")
            util.set_ensemble_from_mo(eb, "gb", "mo121")
            util.set_ensemble_from_mo(eb, "gc", "mo122")
            util.set_ensemble_from_mo(eb, "gd", "mo123")
            util.set_ensemble_from_mo(eb, "ge", "mo124")
            util.set_ensemble_from_mo(eb, "gf", "mo125")
            util.set_ensemble_from_mo(eb, "gg", "mo126")
            util.set_ensemble_from_mo(eb, "gh", "mo127")
            util.set_ensemble_from_mo(eb, "gi", "mo128")
            util.set_ensemble_from_mo(eb, "gj", "mo129")
            util.set_ensemble_from_mo(eb, "gk", "mo130")
            util.set_ensemble_from_mo(eb, "gl", "mo131")
            util.set_ensemble_from_mo(eb, "gm", "mo132")
            util.set_ensemble_from_mo(eb, "gn", "mo133")
            util.set_ensemble_from_mo(eb, "go", "mo134")
            util.set_ensemble_from_mo(eb, "gp", "mo135")
            util.set_ensemble_from_mo(eb, "gq", "mo136")
            util.set_ensemble_from_mo(eb, "gr", "mo137")
            util.set_ensemble_from_mo(eb, "gs", "mo138")
            util.set_ensemble_from_mo(eb, "gt", "mo139")
            util.set_ensemble_from_mo(eb, "gu", "mo140")
            util.set_ensemble_from_mo(eb, "gv", "mo141")
            util.set_ensemble_from_mo(eb, "gw", "mo142")
            util.set_ensemble_from_mo(eb, "gx", "mo143")
            util.set_ensemble_from_mo(eb, "gy", "mo144")
            util.set_ensemble_from_mo(eb, "gz", "mo145")    
