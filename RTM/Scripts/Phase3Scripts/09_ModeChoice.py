##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage2.modechoice
##--Purpose:
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback

class ModeChoice(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Mode Choice Model"
        pb.description = "Runs Mode Choice Models"
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

    @_m.logbook_trace("Mode Choice")
    def __call__(self, eb):
        self.matrix_batchins(eb)

        td_mode_choice_hbw = _m.Modeller().tool("translink.RTM3.stage2.hbwork")
        td_mode_choice_hbu = _m.Modeller().tool("translink.RTM3.stage2.hbuniv")
        td_mode_choice_hbsc = _m.Modeller().tool("translink.RTM3.stage2.hbschool")
        td_mode_choice_hbsh = _m.Modeller().tool("translink.RTM3.stage2.hbshop")
        td_mode_choice_hbpb = _m.Modeller().tool("translink.RTM3.stage2.hbperbus")
        td_mode_choice_hbso = _m.Modeller().tool("translink.RTM3.stage2.hbsocial")
        td_mode_choice_hbes = _m.Modeller().tool("translink.RTM3.stage2.hbescorting")
        td_mode_choice_nhbw = _m.Modeller().tool("translink.RTM3.stage2.nhbwork")
        td_mode_choice_nhbo = _m.Modeller().tool("translink.RTM3.stage2.nhbother")

        td_mode_choice_hbw(eb)
        td_mode_choice_hbu(eb)
        td_mode_choice_hbsc(eb)
        td_mode_choice_hbsh(eb)
        td_mode_choice_hbpb(eb)
        td_mode_choice_hbso(eb)
        td_mode_choice_hbes(eb)
        td_mode_choice_nhbw(eb)
        td_mode_choice_nhbo(eb)
        
        # now that all SOV/HOV driver trips have been aggregated, adjust for external deamnd
        # and demand adjust incremental matrices as needed
        self.add_external_demadj_demand()

    def add_external_demadj_demand(self):
        util = _m.Modeller().tool("translink.util")
        specs = []
        # AM
        specs.append(util.matrix_spec("SOV_drvtrp_VOT_3_Am", "SOV_drvtrp_VOT_3_Am + extSovAm"))
        specs.append(util.matrix_spec("HOV_drvtrp_VOT_3_Am", "HOV_drvtrp_VOT_3_Am + extHovAm"))
        # MD
        specs.append(util.matrix_spec("SOV_drvtrp_VOT_3_Md", "((SOV_drvtrp_VOT_3_Md + extSovMd + MD_Demadj).max.0)"))
        specs.append(util.matrix_spec("HOV_drvtrp_VOT_3_Md", "HOV_drvtrp_VOT_3_Md + extHovMd"))
        # PM
        specs.append(util.matrix_spec("SOV_drvtrp_VOT_3_Pm", "SOV_drvtrp_VOT_3_Pm + extSovPm"))
        specs.append(util.matrix_spec("HOV_drvtrp_VOT_3_Pm", "HOV_drvtrp_VOT_3_Pm + extHovPm"))

        util.compute_matrix(specs)

    @_m.logbook_trace("Initialize Matrices")
    def matrix_batchins(self, eb):
        util = _m.Modeller().tool("translink.util")

        # Initialize AM Peak Hour Person Trip Matrices
        util.initmat(eb, "mf200", "SOV_pertrp_VOT_1_Am", "SOV per-trips VOT 1 AM", 0)
        util.initmat(eb, "mf201", "SOV_pertrp_VOT_2_Am", "SOV per-trips VOT 2 AM", 0)
        util.initmat(eb, "mf202", "SOV_pertrp_VOT_3_Am", "SOV per-trips VOT 3 AM", 0)
        util.initmat(eb, "mf203", "SOV_pertrp_VOT_4_Am", "SOV per-trips VOT 4 AM", 0)
        util.initmat(eb, "mf206", "HOV_pertrp_VOT_1_Am", "HOV per-trips VOT 1 AM", 0)
        util.initmat(eb, "mf207", "HOV_pertrp_VOT_2_Am", "HOV per-trips VOT 2 AM", 0)
        util.initmat(eb, "mf208", "HOV_pertrp_VOT_3_Am", "HOV per-trips VOT 3 AM", 0)
        util.initmat(eb, "mf209", "HOV_pertrp_VOT_4_Am", "HOV per-trips VOT 4 AM", 0)
        util.initmat(eb, "mf215", "Wk_pertrp_Am", "Walk per-trips AM", 0)
        util.initmat(eb, "mf216", "Bk_pertrp_Am", "Bike per-trips AM", 0)

        # Initialize MD Peak Hour Person Trip Matrices
        util.initmat(eb, "mf230", "SOV_pertrp_VOT_1_Md", "SOV per-trips VOT 1 MD", 0)
        util.initmat(eb, "mf231", "SOV_pertrp_VOT_2_Md", "SOV per-trips VOT 2 MD", 0)
        util.initmat(eb, "mf232", "SOV_pertrp_VOT_3_Md", "SOV per-trips VOT 3 MD", 0)
        util.initmat(eb, "mf233", "SOV_pertrp_VOT_4_Md", "SOV per-trips VOT 4 MD", 0)
        util.initmat(eb, "mf236", "HOV_pertrp_VOT_1_Md", "HOV per-trips VOT 1 MD", 0)
        util.initmat(eb, "mf237", "HOV_pertrp_VOT_2_Md", "HOV per-trips VOT 2 MD", 0)
        util.initmat(eb, "mf238", "HOV_pertrp_VOT_3_Md", "HOV per-trips VOT 3 MD", 0)
        util.initmat(eb, "mf239", "HOV_pertrp_VOT_4_Md", "HOV per-trips VOT 4 MD", 0)
        util.initmat(eb, "mf245", "Wk_pertrp_Md", "Walk per-trips MD", 0)
        util.initmat(eb, "mf246", "Bk_pertrp_Md", "Bike per-trips MD", 0)

        # Initialize PM Peak Hour Person Trip Matrices
        util.initmat(eb, "mf260", "SOV_pertrp_VOT_1_Pm", "SOV per-trips VOT 1 PM", 0)
        util.initmat(eb, "mf261", "SOV_pertrp_VOT_2_Pm", "SOV per-trips VOT 2 PM", 0)
        util.initmat(eb, "mf262", "SOV_pertrp_VOT_3_Pm", "SOV per-trips VOT 3 PM", 0)
        util.initmat(eb, "mf263", "SOV_pertrp_VOT_4_Pm", "SOV per-trips VOT 4 PM", 0)
        util.initmat(eb, "mf266", "HOV_pertrp_VOT_1_Pm", "HOV per-trips VOT 1 PM", 0)
        util.initmat(eb, "mf267", "HOV_pertrp_VOT_2_Pm", "HOV per-trips VOT 2 PM", 0)
        util.initmat(eb, "mf268", "HOV_pertrp_VOT_3_Pm", "HOV per-trips VOT 3 PM", 0)
        util.initmat(eb, "mf269", "HOV_pertrp_VOT_4_Pm", "HOV per-trips VOT 4 PM", 0)
        util.initmat(eb, "mf275", "Wk_pertrp_Pm", "Walk per-trips PM", 0)
        util.initmat(eb, "mf276", "Bk_pertrp_Pm", "Bike per-trips PM", 0)

        # Initialize AM Peak Hour Driver and Transit Demand Matrices
        util.initmat(eb, "mf300", "SOV_drvtrp_VOT_1_Am", "SOV drv-trips VOT 1 AM", 0)
        util.initmat(eb, "mf301", "SOV_drvtrp_VOT_2_Am", "SOV drv-trips VOT 2 AM", 0)
        util.initmat(eb, "mf302", "SOV_drvtrp_VOT_3_Am", "SOV drv-trips VOT 3 AM", 0)
        util.initmat(eb, "mf303", "SOV_drvtrp_VOT_4_Am", "SOV drv-trips VOT 4 AM", 0)
        util.initmat(eb, "mf306", "HOV_drvtrp_VOT_1_Am", "HOV drv-trips VOT 1 AM", 0)
        util.initmat(eb, "mf307", "HOV_drvtrp_VOT_2_Am", "HOV drv-trips VOT 2 AM", 0)
        util.initmat(eb, "mf308", "HOV_drvtrp_VOT_3_Am", "HOV drv-trips VOT 3 AM", 0)
        util.initmat(eb, "mf309", "HOV_drvtrp_VOT_4_Am", "HOV drv-trips VOT 4 AM", 0)
        util.initmat(eb, "mf314", "busAm", "Bus Person Trips AM", 0)
        util.initmat(eb, "mf315", "railAm", "Rail Person Trips AM", 0)
        util.initmat(eb, "mf316", "WCEAm", "WCE Person Trips AM", 0)

        # Initialize MD Peak Hour Driver and Transit Demand Matrices
        util.initmat(eb, "mf320", "SOV_drvtrp_VOT_1_Md", "SOV drv-trips VOT 1 MD", 0)
        util.initmat(eb, "mf321", "SOV_drvtrp_VOT_2_Md", "SOV drv-trips VOT 2 MD", 0)
        util.initmat(eb, "mf322", "SOV_drvtrp_VOT_3_Md", "SOV drv-trips VOT 3 MD", 0)
        util.initmat(eb, "mf323", "SOV_drvtrp_VOT_4_Md", "SOV drv-trips VOT 4 MD", 0)
        util.initmat(eb, "mf326", "HOV_drvtrp_VOT_1_Md", "HOV drv-trips VOT 1 MD", 0)
        util.initmat(eb, "mf327", "HOV_drvtrp_VOT_2_Md", "HOV drv-trips VOT 2 MD", 0)
        util.initmat(eb, "mf328", "HOV_drvtrp_VOT_3_Md", "HOV drv-trips VOT 3 MD", 0)
        util.initmat(eb, "mf329", "HOV_drvtrp_VOT_4_Md", "HOV drv-trips VOT 4 MD", 0)
        util.initmat(eb, "mf334", "busMd", "Bus Person Trips MD", 0)
        util.initmat(eb, "mf335", "railMd", "Rail Person Trips MD", 0)
        util.initmat(eb, "mf336", "WCEMd", "WCE Person Trips MD", 0)

        # Initialize PM Peak Hour Driver and Transit Demand Matrices
        util.initmat(eb, "mf340", "SOV_drvtrp_VOT_1_Pm", "SOV drv-trips VOT 1 PM", 0)
        util.initmat(eb, "mf341", "SOV_drvtrp_VOT_2_Pm", "SOV drv-trips VOT 2 PM", 0)
        util.initmat(eb, "mf342", "SOV_drvtrp_VOT_3_Pm", "SOV drv-trips VOT 3 PM", 0)
        util.initmat(eb, "mf343", "SOV_drvtrp_VOT_4_Pm", "SOV drv-trips VOT 4 PM", 0)
        util.initmat(eb, "mf346", "HOV_drvtrp_VOT_1_Pm", "HOV drv-trips VOT 1 PM", 0)
        util.initmat(eb, "mf347", "HOV_drvtrp_VOT_2_Pm", "HOV drv-trips VOT 2 PM", 0)
        util.initmat(eb, "mf348", "HOV_drvtrp_VOT_3_Pm", "HOV drv-trips VOT 3 PM", 0)
        util.initmat(eb, "mf349", "HOV_drvtrp_VOT_4_Pm", "HOV drv-trips VOT 4 PM", 0)
        util.initmat(eb, "mf354", "busPm", "Bus Person Trips PM", 0)
        util.initmat(eb, "mf355", "railPm", "Rail Person Trips PM", 0)
        util.initmat(eb, "mf356", "WCEPm", "WCE Person Trips PM", 0)
