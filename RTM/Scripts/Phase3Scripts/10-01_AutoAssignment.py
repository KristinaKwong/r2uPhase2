##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage3.autoassignment
##--Purpose: Auto assignment procedure
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback

class AutoAssignment(_m.Tool()):
    am_scenario = _m.Attribute(_m.InstanceType)
    md_scenario = _m.Attribute(_m.InstanceType)
    pm_scenario = _m.Attribute(_m.InstanceType)

    relative_gap = _m.Attribute(float)
    best_relative_gap = _m.Attribute(float)
    normalized_gap = _m.Attribute(float)
    max_iterations = _m.Attribute(int)

    tool_run_msg = _m.Attribute(unicode)

    def __init__(self):
        self.relative_gap = 0.0001
        self.best_relative_gap = 0.01
        self.normalized_gap = 0.005
        self.max_iterations = 250

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Auto Assignment"
        pb.description = "Performs a multi-class auto assignment with " +\
                         "14 classes. An analysis is also performed to calculate " +\
                         "auto distance and auto time."
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        pb.add_select_scenario("am_scenario", title="AM scenario:")
        pb.add_select_scenario("md_scenario", title="MD scenario:")
        pb.add_select_scenario("pm_scenario", title="PM scenario:")

        with pb.section("Stopping criteria:"):
            pb.add_text_box("relative_gap", title="Relative gap:")
            pb.add_text_box("best_relative_gap", title="Best relative gap (%):")
            pb.add_text_box("normalized_gap", title="Normalized gap:")
            pb.add_text_box("max_iterations", title="Maximum iterations:")

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            eb = _m.Modeller().emmebank
            eb.matrix("ms40").data = self.max_iterations
            eb.matrix("ms41").data = self.relative_gap
            eb.matrix("ms42").data = self.best_relative_gap
            eb.matrix("ms43").data = self.normalized_gap

            self(self.am_scenario, self.md_scenario, self.pm_scenario)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Auto Traffic Assignment")
    def __call__(self, am_scenario, md_scenario, pm_scenario):

        ## Add External Demand to SOV and HOV VOT3 Segment and Demand Adjust Inc Demand for MD SOV VOT3 only
        self.add_external_demadj_demand()

        ## Set Attribute containing merge speeds into el1
        set_extra_function_parameters = _m.Modeller().tool("inro.emme.traffic_assignment.set_extra_function_parameters")
        set_extra_function_parameters(el1 = "@mspeed")


        am_demands = {"sov":   ["mfSOV_drvtrp_VOT_1_Am", "mfSOV_drvtrp_VOT_2_Am", "mfSOV_drvtrp_VOT_3_Am", "mfSOV_drvtrp_VOT_4_Am"],
                      "hov":   ["mfHOV_drvtrp_VOT_1_Am", "mfHOV_drvtrp_VOT_2_Am", "mfHOV_drvtrp_VOT_3_Am"],
                      "truck": ["mflgvPceAm", "mfhgvPceAm"]}
        self.assign_scen(am_scenario, am_demands)
        am_skims = {"sovVot1":  ["mfAmSovOpCstVOT1", "mfAmSovTimeVOT1", "mfAmSovTollVOT1"],
                    "sovVot2":  ["mfAmSovOpCstVOT2", "mfAmSovTimeVOT2", "mfAmSovTollVOT2"],
                    "sovVot3":  ["mfAmSovOpCstVOT3", "mfAmSovTimeVOT3", "mfAmSovTollVOT3"],
                    "sovVot4":  ["mfAmSovOpCstVOT4", "mfAmSovTimeVOT4", "mfAmSovTollVOT4"],
                    "hovVot1":  ["mfAmHovOpCstVOT1", "mfAmHovTimeVOT1", "mfAmHovTollVOT1"],
                    "hovVot2":  ["mfAmHovOpCstVOT2", "mfAmHovTimeVOT2", "mfAmHovTollVOT2"],
                    "hovVot3":  ["mfAmHovOpCstVOT3", "mfAmHovTimeVOT3", "mfAmHovTollVOT3"],
                    "lgv":  ["mfAmLgvOpCst", "mfAmLgvTime", "mfAmLgvToll"],
                    "hgv":  ["mfAmHgvOpCst", "mfAmHgvTime", "mfAmHgvToll"]}
        self.store_skims(am_scenario, am_skims)

        md_demands = {"sov":   ["mfSOV_drvtrp_VOT_1_Md", "mfSOV_drvtrp_VOT_2_Md", "mfSOV_drvtrp_VOT_3_Md", "mfSOV_drvtrp_VOT_4_Md"],
                      "hov":   ["mfHOV_drvtrp_VOT_1_Md", "mfHOV_drvtrp_VOT_2_Md", "mfHOV_drvtrp_VOT_3_Md"],
                      "truck": ["mflgvPceMd", "mfhgvPceMd"]}
        self.assign_scen(md_scenario, md_demands)
        md_skims = {"sovVot1":  ["mfMdSovOpCstVOT1", "mfMdSovTimeVOT1", "mfMdSovTollVOT1"],
                    "sovVot2":  ["mfMdSovOpCstVOT2", "mfMdSovTimeVOT2", "mfMdSovTollVOT2"],
                    "sovVot3":  ["mfMdSovOpCstVOT3", "mfMdSovTimeVOT3", "mfMdSovTollVOT3"],
                    "sovVot4":  ["mfMdSovOpCstVOT4", "mfMdSovTimeVOT4", "mfMdSovTollVOT4"],
                    "hovVot1":  ["mfMdHovOpCstVOT1", "mfMdHovTimeVOT1", "mfMdHovTollVOT1"],
                    "hovVot2":  ["mfMdHovOpCstVOT2", "mfMdHovTimeVOT2", "mfMdHovTollVOT2"],
                    "hovVot3":  ["mfMdHovOpCstVOT3", "mfMdHovTimeVOT3", "mfMdHovTollVOT3"],
                    "lgv":  ["mfMdLgvOpCst", "mfMdLgvTime", "mfMdLgvToll"],
                    "hgv":  ["mfMdHgvOpCst", "mfMdHgvTime", "mfMdHgvToll"]}
        self.store_skims(md_scenario, md_skims)
        pm_demands = {"sov":   ["mfSOV_drvtrp_VOT_1_Pm", "mfSOV_drvtrp_VOT_2_Pm", "mfSOV_drvtrp_VOT_3_Pm", "mfSOV_drvtrp_VOT_4_Pm"],
                      "hov":   ["mfHOV_drvtrp_VOT_1_Pm", "mfHOV_drvtrp_VOT_2_Pm", "mfHOV_drvtrp_VOT_3_Pm"],
                      "truck": ["mflgvPcePm", "mfhgvPcePm"]}
        self.assign_scen(pm_scenario, pm_demands)
        pm_skims = {"sovVot1":  ["mfPmSovOpCstVOT1", "mfPmSovTimeVOT1", "mfPmSovTollVOT1"],
                    "sovVot2":  ["mfPmSovOpCstVOT2", "mfPmSovTimeVOT2", "mfPmSovTollVOT2"],
                    "sovVot3":  ["mfPmSovOpCstVOT3", "mfPmSovTimeVOT3", "mfPmSovTollVOT3"],
                    "sovVot4":  ["mfPmSovOpCstVOT4", "mfPmSovTimeVOT4", "mfPmSovTollVOT4"],
                    "hovVot1":  ["mfPmHovOpCstVOT1", "mfPmHovTimeVOT1", "mfPmHovTollVOT1"],
                    "hovVot2":  ["mfPmHovOpCstVOT2", "mfPmHovTimeVOT2", "mfPmHovTollVOT2"],
                    "hovVot3":  ["mfPmHovOpCstVOT3", "mfPmHovTimeVOT3", "mfPmHovTollVOT3"],
                    "lgv":  ["mfPmLgvOpCst", "mfPmLgvTime", "mfPmLgvToll"],
                    "hgv":  ["mfPmHgvOpCst", "mfPmHgvTime", "mfPmHgvToll"]}
        self.store_skims(pm_scenario, pm_skims)

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

    def assign_scen(self, scenario, demands):
        assign_traffic = _m.Modeller().tool("inro.emme.traffic_assignment.sola_traffic_assignment")

        self.calc_network_costs(scenario)
        self.init_matrices(scenario.emmebank)

        # First assignment to generate toll skims
        #spec = self.get_class_specs(scenario.emmebank, demands)
        #self.add_toll_path_analysis(spec)
        #assign_traffic(spec, scenario=scenario)

        # Second assignment to generate distance and time skims
        spec = self.get_class_specs(scenario.emmebank, demands)
        self.add_distance_path_analysis(spec)
        assign_traffic(spec, scenario=scenario)

        # Aggregate network volumes post-assignment and calculate intrazonal skims
        self.calc_network_volumes(scenario)
        self.calc_timedist_skims(scenario.emmebank)
        self.calc_intrazonal_skims(scenario.emmebank)

    @_m.logbook_trace("Calculate Time and Distance Skims")
    def calc_timedist_skims(self, eb):
        self.calc_timedist_skim(eb, "msAutoVOT1", "msautoOpCost", "mfSOVGCTimeVOT1", "mfSOVOpCstVOT1", "mfSOVTollVOT1", "mfSOVTimeVOT1", "mfSOVDistVOT1", 1.0)
        self.calc_timedist_skim(eb, "msAutoVOT2", "msautoOpCost", "mfSOVGCTimeVOT2", "mfSOVOpCstVOT2", "mfSOVTollVOT2", "mfSOVTimeVOT2", "mfSOVDistVOT2", 1.0)
        self.calc_timedist_skim(eb, "msAutoVOT3", "msautoOpCost", "mfSOVGCTimeVOT3", "mfSOVOpCstVOT3", "mfSOVTollVOT3", "mfSOVTimeVOT3", "mfSOVDistVOT3", 1.0)
        self.calc_timedist_skim(eb, "msAutoVOT4", "msautoOpCost", "mfSOVGCTimeVOT4", "mfSOVOpCstVOT4", "mfSOVTollVOT4", "mfSOVTimeVOT4", "mfSOVDistVOT4", 1.0)

        hov_occupancy = eb.matrix("msAutoOcc").data
        self.calc_timedist_skim(eb, "msAutoVOT1", "msautoOpCost", "mfHOVGCTimeVOT1", "mfHOVOpCstVOT1", "mfHOVTollVOT1", "mfHOVTimeVOT1", "mfHOVDistVOT1", hov_occupancy)
        self.calc_timedist_skim(eb, "msAutoVOT2", "msautoOpCost", "mfHOVGCTimeVOT2", "mfHOVOpCstVOT2", "mfHOVTollVOT2", "mfHOVTimeVOT2", "mfHOVDistVOT2", hov_occupancy)
        self.calc_timedist_skim(eb, "msAutoVOT5", "msautoOpCost", "mfHOVGCTimeVOT3", "mfHOVOpCstVOT3", "mfHOVTollVOT3", "mfHOVTimeVOT3", "mfHOVDistVOT3", hov_occupancy)


        self.calc_timedist_skim(eb, "msVotLgv", "mslgvOpCost", "mfLGVGCTime", "mfLGVOpCst", "mfLGVToll", "mfLGVTime", "mfLGVDist", 1.0)
        self.calc_timedist_skim(eb, "msVotHgv", "mshgvOpCost", "mfHGVGCTime", "mfHGVOpCst", "mfHGVToll", "mfHGVTime", "mfHGVDist", 1.0)

    def calc_timedist_skim(self, eb, vot_mat, voc_mat, gc_mat, opcst_mat, toll_mat, time_mat, dist_mat, occupancy):
        util = _m.Modeller().tool("translink.util")

        vot = eb.matrix(vot_mat).data
        voc = eb.matrix(voc_mat).data

        gc = util.get_matrix_numpy(eb, gc_mat)
        opcst = util.get_matrix_numpy(eb, opcst_mat)
        toll = util.get_matrix_numpy(eb, toll_mat)

        time = gc - (opcst * vot)
        opcst = opcst * occupancy
        dist = (opcst - toll) / voc

        util.set_matrix_numpy(eb, time_mat, time)
        util.set_matrix_numpy(eb, dist_mat, dist)
        util.set_matrix_numpy(eb, opcst_mat, opcst)

    @_m.logbook_trace("Execute Intrazonal Calculation")
    def calc_intrazonal_skims(self, eb):
        # Calculate Intrazonal GC Minutes
        self.calc_intrazonal_skim(eb, "mfSOVTimeVOT1")
        self.calc_intrazonal_skim(eb, "mfSOVTimeVOT2")
        self.calc_intrazonal_skim(eb, "mfSOVTimeVOT3")
        self.calc_intrazonal_skim(eb, "mfSOVTimeVOT4")
        self.calc_intrazonal_skim(eb, "mfHOVTimeVOT1")
        self.calc_intrazonal_skim(eb, "mfHOVTimeVOT2")
        self.calc_intrazonal_skim(eb, "mfHOVTimeVOT3")
        self.calc_intrazonal_skim(eb, "mfLGVTime")
        self.calc_intrazonal_skim(eb, "mfHGVTime")

        # Calculate Intrazonal Distance
        self.calc_intrazonal_skim(eb, "mfSOVDistVOT1")
        self.calc_intrazonal_skim(eb, "mfSOVDistVOT2")
        self.calc_intrazonal_skim(eb, "mfSOVDistVOT3")
        self.calc_intrazonal_skim(eb, "mfSOVDistVOT4")
        self.calc_intrazonal_skim(eb, "mfHOVDistVOT1")
        self.calc_intrazonal_skim(eb, "mfHOVDistVOT2")
        self.calc_intrazonal_skim(eb, "mfHOVDistVOT3")
        self.calc_intrazonal_skim(eb, "mfLGVDist")
        self.calc_intrazonal_skim(eb, "mfHGVDist")

        # Calculate Intrazonal Op Cost
        self.calc_intrazonal_skim(eb, "mfSOVOpCstVOT1")
        self.calc_intrazonal_skim(eb, "mfSOVOpCstVOT2")
        self.calc_intrazonal_skim(eb, "mfSOVOpCstVOT3")
        self.calc_intrazonal_skim(eb, "mfSOVOpCstVOT4")
        self.calc_intrazonal_skim(eb, "mfHOVOpCstVOT1")
        self.calc_intrazonal_skim(eb, "mfHOVOpCstVOT2")
        self.calc_intrazonal_skim(eb, "mfHOVOpCstVOT3")
        self.calc_intrazonal_skim(eb, "mfLGVOpCst")
        self.calc_intrazonal_skim(eb, "mfHGVOpCst")

        # Calculate Intrazonal Generalized Cost
        self.calc_intrazonal_skim(eb, "mfSOVGCTimeVOT1")
        self.calc_intrazonal_skim(eb, "mfSOVGCTimeVOT2")
        self.calc_intrazonal_skim(eb, "mfSOVGCTimeVOT3")
        self.calc_intrazonal_skim(eb, "mfSOVGCTimeVOT4")
        self.calc_intrazonal_skim(eb, "mfHOVGCTimeVOT1")
        self.calc_intrazonal_skim(eb, "mfHOVGCTimeVOT2")
        self.calc_intrazonal_skim(eb, "mfHOVGCTimeVOT3")
        self.calc_intrazonal_skim(eb, "mfLGVGCTime")
        self.calc_intrazonal_skim(eb, "mfHGVGCTime")

    def calc_intrazonal_skim(self, eb, matrix):
        util = _m.Modeller().tool("translink.util")

        np_mat = util.get_matrix_numpy(eb, matrix)

        # calculate the mimimum non-zero value in each row and set half that
        # as the intrazonal value
        for i in xrange(np_mat.shape[0]):
            np_mat[i][i] = np_mat[i][np_mat[i] > 0].min() * 0.5

        # write the updated matrix back to the emmebank
        util.set_matrix_numpy(eb, matrix, np_mat)

    def store_skims(self, scenario, skim_list):
        util = _m.Modeller().tool("translink.util")

        do_averaging = util.get_cycle(scenario.emmebank) > 1
        specs = []

        if not do_averaging:
            # Set Distance Matrices
            specs.append(util.matrix_spec(skim_list["sovVot1"][0], "mfSOVOpCstVOT1"))
            specs.append(util.matrix_spec(skim_list["sovVot2"][0], "mfSOVOpCstVOT2"))
            specs.append(util.matrix_spec(skim_list["sovVot3"][0], "mfSOVOpCstVOT3"))
            specs.append(util.matrix_spec(skim_list["sovVot4"][0], "mfSOVOpCstVOT4"))
            specs.append(util.matrix_spec(skim_list["hovVot1"][0], "mfHOVOpCstVOT1"))
            specs.append(util.matrix_spec(skim_list["hovVot2"][0], "mfHOVOpCstVOT2"))
            specs.append(util.matrix_spec(skim_list["hovVot3"][0], "mfHOVOpCstVOT3"))
            specs.append(util.matrix_spec(skim_list["lgv"][0], "mfLGVOpCst"))
            specs.append(util.matrix_spec(skim_list["hgv"][0], "mfHGVOpCst"))
            # Set GC Time Matrices
            specs.append(util.matrix_spec(skim_list["sovVot1"][1], "mfSOVTimeVOT1"))
            specs.append(util.matrix_spec(skim_list["sovVot2"][1], "mfSOVTimeVOT2"))
            specs.append(util.matrix_spec(skim_list["sovVot3"][1], "mfSOVTimeVOT3"))
            specs.append(util.matrix_spec(skim_list["sovVot4"][1], "mfSOVTimeVOT4"))
            specs.append(util.matrix_spec(skim_list["hovVot1"][1], "mfHOVTimeVOT1"))
            specs.append(util.matrix_spec(skim_list["hovVot2"][1], "mfHOVTimeVOT2"))
            specs.append(util.matrix_spec(skim_list["hovVot3"][1], "mfHOVTimeVOT3"))
            specs.append(util.matrix_spec(skim_list["lgv"][1], "mfLGVTime"))
            specs.append(util.matrix_spec(skim_list["hgv"][1], "mfHGVTime"))
            # Set GC Toll Matrices
            specs.append(util.matrix_spec(skim_list["sovVot1"][2], "mfSOVTollVOT1"))
            specs.append(util.matrix_spec(skim_list["sovVot2"][2], "mfSOVTollVOT2"))
            specs.append(util.matrix_spec(skim_list["sovVot3"][2], "mfSOVTollVOT3"))
            specs.append(util.matrix_spec(skim_list["sovVot4"][2], "mfSOVTollVOT4"))
            specs.append(util.matrix_spec(skim_list["hovVot1"][2], "mfHOVTollVOT1"))
            specs.append(util.matrix_spec(skim_list["hovVot2"][2], "mfHOVTollVOT2"))
            specs.append(util.matrix_spec(skim_list["hovVot3"][2], "mfHOVTollVOT3"))
            specs.append(util.matrix_spec(skim_list["lgv"][2], "mfLGVToll"))
            specs.append(util.matrix_spec(skim_list["hgv"][2], "mfHGVToll"))
        else:
            # Average Distance Matrices
            specs.append(util.matrix_spec(skim_list["sovVot1"][0], "0.5*(mfSOVOpCstVOT1 + %s)" % skim_list["sovVot1"][0]))
            specs.append(util.matrix_spec(skim_list["sovVot2"][0], "0.5*(mfSOVOpCstVOT2 + %s)" % skim_list["sovVot2"][0]))
            specs.append(util.matrix_spec(skim_list["sovVot3"][0], "0.5*(mfSOVOpCstVOT3 + %s)" % skim_list["sovVot3"][0]))
            specs.append(util.matrix_spec(skim_list["sovVot4"][0], "0.5*(mfSOVOpCstVOT4 + %s)" % skim_list["sovVot4"][0]))
            specs.append(util.matrix_spec(skim_list["hovVot1"][0], "0.5*(mfHOVOpCstVOT1 + %s)" % skim_list["hovVot1"][0]))
            specs.append(util.matrix_spec(skim_list["hovVot2"][0], "0.5*(mfHOVOpCstVOT2 + %s)" % skim_list["hovVot2"][0]))
            specs.append(util.matrix_spec(skim_list["hovVot3"][0], "0.5*(mfHOVOpCstVOT3 + %s)" % skim_list["hovVot3"][0]))
            specs.append(util.matrix_spec(skim_list["lgv"][0], "0.5*(mfLGVOpCst + %s)" % skim_list["lgv"][0]))
            specs.append(util.matrix_spec(skim_list["hgv"][0], "0.5*(mfHGVOpCst + %s)" % skim_list["hgv"][0]))
            # Average GC Time Matrices
            specs.append(util.matrix_spec(skim_list["sovVot1"][1], "0.5*(mfSOVTimeVOT1 + %s)" % skim_list["sovVot1"][1]))
            specs.append(util.matrix_spec(skim_list["sovVot2"][1], "0.5*(mfSOVTimeVOT2 + %s)" % skim_list["sovVot2"][1]))
            specs.append(util.matrix_spec(skim_list["sovVot3"][1], "0.5*(mfSOVTimeVOT3 + %s)" % skim_list["sovVot3"][1]))
            specs.append(util.matrix_spec(skim_list["sovVot4"][1], "0.5*(mfSOVTimeVOT4 + %s)" % skim_list["sovVot4"][1]))
            specs.append(util.matrix_spec(skim_list["hovVot1"][1], "0.5*(mfHOVTimeVOT1 + %s)" % skim_list["hovVot1"][1]))
            specs.append(util.matrix_spec(skim_list["hovVot2"][1], "0.5*(mfHOVTimeVOT2 + %s)" % skim_list["hovVot2"][1]))
            specs.append(util.matrix_spec(skim_list["hovVot3"][1], "0.5*(mfHOVTimeVOT3 + %s)" % skim_list["hovVot3"][1]))

            specs.append(util.matrix_spec(skim_list["lgv"][1], "0.5*(mfLGVTime + %s)" % skim_list["lgv"][1]))
            specs.append(util.matrix_spec(skim_list["hgv"][1], "0.5*(mfHGVTime + %s)" % skim_list["hgv"][1]))
            # Average GC Toll Matrices
            specs.append(util.matrix_spec(skim_list["sovVot1"][2], "0.5*(mfSOVTollVOT1 + %s)" % skim_list["sovVot1"][2]))
            specs.append(util.matrix_spec(skim_list["sovVot2"][2], "0.5*(mfSOVTollVOT2 + %s)" % skim_list["sovVot2"][2]))
            specs.append(util.matrix_spec(skim_list["sovVot3"][2], "0.5*(mfSOVTollVOT3 + %s)" % skim_list["sovVot3"][2]))
            specs.append(util.matrix_spec(skim_list["sovVot4"][2], "0.5*(mfSOVTollVOT4 + %s)" % skim_list["sovVot4"][2]))
            specs.append(util.matrix_spec(skim_list["hovVot1"][2], "0.5*(mfHOVTollVOT1 + %s)" % skim_list["hovVot1"][2]))
            specs.append(util.matrix_spec(skim_list["hovVot2"][2], "0.5*(mfHOVTollVOT2 + %s)" % skim_list["hovVot2"][2]))
            specs.append(util.matrix_spec(skim_list["hovVot3"][2], "0.5*(mfHOVTollVOT3 + %s)" % skim_list["hovVot3"][2]))

            specs.append(util.matrix_spec(skim_list["lgv"][2], "0.5*(mfLGVToll + %s)" % skim_list["lgv"][2]))
            specs.append(util.matrix_spec(skim_list["hgv"][2], "0.5*(mfHGVToll + %s)" % skim_list["hgv"][2]))

        util.compute_matrix(specs, scenario)

    def add_mode_specification(self, specs, mode, demand, gc_cost, gc_factor, travel_time, link_vol, turn_vol):
        spec = {"mode": mode,
                "demand": demand,
                "generalized_cost": { "link_costs": gc_cost, "perception_factor": gc_factor },
                "results": { "od_travel_times": {"shortest_paths": travel_time},
                             "link_volumes": link_vol,
                             "turn_volumes": turn_vol }

                }
        specs.append(spec)

    def get_class_specs(self, eb, demand_matrices):
        all_classes = []
        # SOV Classes
        self.add_mode_specification(all_classes, "d", demand_matrices["sov"][0], "@sovoc", eb.matrix("msAutoVOT1").data, "mfSOVGCTimeVOT1", "@sov1", "@tsov1")
        self.add_mode_specification(all_classes, "d", demand_matrices["sov"][1], "@sovoc", eb.matrix("msAutoVOT2").data, "mfSOVGCTimeVOT2", "@sov2", "@tsov2")
        self.add_mode_specification(all_classes, "d", demand_matrices["sov"][2], "@sovoc", eb.matrix("msAutoVOT3").data, "mfSOVGCTimeVOT3", "@sov3", "@tsov3")
        self.add_mode_specification(all_classes, "d", demand_matrices["sov"][3], "@sovoc", eb.matrix("msAutoVOT4").data, "mfSOVGCTimeVOT4", "@sov4", "@tsov4")
        # HOV Classes
        self.add_mode_specification(all_classes, "c", demand_matrices["hov"][0], "@hovoc", eb.matrix("msAutoVOT1").data, "mfHOVGCTimeVOT1", "@hov1", "@thov1")
        self.add_mode_specification(all_classes, "c", demand_matrices["hov"][1], "@hovoc", eb.matrix("msAutoVOT2").data, "mfHOVGCTimeVOT2", "@hov2", "@thov2")
        self.add_mode_specification(all_classes, "c", demand_matrices["hov"][2], "@hovoc", eb.matrix("msAutoVOT5").data, "mfHOVGCTimeVOT3", "@hov3", "@thov3")

        # Truck Classes
        self.add_mode_specification(all_classes, "x", demand_matrices["truck"][0], "@lgvoc", eb.matrix("msVotLgv").data, "mfLGVGCTime", "@lgvol", "@lgvtn")
        self.add_mode_specification(all_classes, "t", demand_matrices["truck"][1], "@hgvoc", eb.matrix("msVotHgv").data, "mfHGVGCTime", "@hgvol", "@hgvtn")

        stopping_criteria = { "max_iterations"   : int(eb.matrix("ms40").data),
                              "relative_gap"     : eb.matrix("ms41").data,
                              "best_relative_gap": eb.matrix("ms42").data,
                              "normalized_gap"   : eb.matrix("ms43").data
                            }
        spec = {
            "type": "SOLA_TRAFFIC_ASSIGNMENT",
            "background_traffic": {"add_transit_vehicles": True},
            "classes": all_classes,
            "stopping_criteria": stopping_criteria,
            "performance_settings": {"number_of_processors": int(eb.matrix("ms12").data)},
        }
        return spec

    def add_distance_path_analysis(self, spec):
        path_od = { "considered_paths": "ALL",
                    "multiply_path_proportions_by": { "analyzed_demand": False, "path_value": True }
                  }
        spec["classes"][ 0]["analysis"] = {"results": {"od_values": "mfSOVOpCstVOT1"}}
        spec["classes"][ 0]["path_analysis"] = {"link_component": "@sovoc", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999}}
        spec["classes"][ 1]["analysis"] = {"results": {"od_values": "mfSOVOpCstVOT2"}}
        spec["classes"][ 1]["path_analysis"] = {"link_component": "@sovoc", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} }
        spec["classes"][ 2]["analysis"] = {"results": {"od_values": "mfSOVOpCstVOT3"}}
        spec["classes"][ 2]["path_analysis"] = {"link_component": "@sovoc", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} }
        spec["classes"][ 3]["analysis"] = {"results": {"od_values": "mfSOVOpCstVOT4"}}
        spec["classes"][ 3]["path_analysis"] = {"link_component": "@sovoc", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} }
        spec["classes"][ 4]["analysis"] = {"results": {"od_values": "mfHOVOpCstVOT1"}}
        spec["classes"][ 4]["path_analysis"] = {"link_component": "@hovoc", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} }
        spec["classes"][ 5]["analysis"] = {"results": {"od_values": "mfHOVOpCstVOT2"}}
        spec["classes"][ 5]["path_analysis"] = {"link_component": "@hovoc", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} }
        spec["classes"][ 6]["analysis"] = {"results": {"od_values": "mfHOVOpCstVOT3"}}
        spec["classes"][ 6]["path_analysis"] = {"link_component": "@hovoc", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} }
        spec["classes"][ 7]["analysis"] = {"results": {"od_values": "mfLGVOpCst"}}
        spec["classes"][ 7]["path_analysis"] = {"link_component": "@lgvoc", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} }
        spec["classes"][ 8]["analysis"] = {"results": {"od_values": "mfHGVOpCst"}}
        spec["classes"][ 8]["path_analysis"] = {"link_component": "@hgvoc", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} }

    def add_toll_path_analysis(self, spec):
        spec["path_analysis"] = {"link_component": "@tolls",
                                 "turn_component": None,
                                 "operator": "+",
                                 "selection_threshold": {"lower": 0.01, "upper": 100},
                                 "path_to_od_composition": {
                                     "considered_paths": "SELECTED",
                                     "multiply_path_proportions_by": {
                                         "analyzed_demand": False,
                                         "path_value": True
                                     }
                                 }
                                }
        spec["classes"][ 0]["analysis"] = {"results": {"od_values": "mfSOVTollVOT1"}}
        spec["classes"][ 1]["analysis"] = {"results": {"od_values": "mfSOVTollVOT2"}}
        spec["classes"][ 2]["analysis"] = {"results": {"od_values": "mfSOVTollVOT3"}}
        spec["classes"][ 3]["analysis"] = {"results": {"od_values": "mfSOVTollVOT4"}}
        spec["classes"][ 4]["analysis"] = {"results": {"od_values": "mfHOVTollVOT1"}}
        spec["classes"][ 5]["analysis"] = {"results": {"od_values": "mfHOVTollVOT2"}}
        spec["classes"][ 6]["analysis"] = {"results": {"od_values": "mfHOVTollVOT3"}}
        spec["classes"][ 7]["analysis"] = {"results": {"od_values": "mfLGVToll"}}
        spec["classes"][ 8]["analysis"] = {"results": {"od_values": "mfHGVToll"}}

    @_m.logbook_trace("Calculate Link and Turn Aggregate Volumes")
    def calc_network_volumes(self, scenario):
        util = _m.Modeller().tool("translink.util")

        util.emme_link_calc(scenario, "@wsovl", "@sov1+@sov2+@sov3+@sov4")
        util.emme_link_calc(scenario, "@whovl", "@hov1+@hov2+@hov3+@hov4")
        util.emme_turn_calc(scenario, "@wsovt", "@tsov1+@tsov2+@tsov3+@tsov4")
        util.emme_turn_calc(scenario, "@whovt", "@thov1+@thov2+@thov3+@thov4")

    @_m.logbook_trace("Calculate Fixed Network Costs")
    def calc_network_costs(self, scenario):
        util = _m.Modeller().tool("translink.util")
        eb = scenario.emmebank

        hov_occupancy = eb.matrix("msAutoOcc").data
        auto_voc = eb.matrix("msautoOpCost").data
        lgv_voc = eb.matrix("mslgvOpCost").data
        hgv_voc = eb.matrix("mshgvOpCost").data

        util.emme_link_calc(scenario, "@tkpen", "0")
        util.emme_link_calc(scenario, "@tkpen", "length * 100", sel_link="mode=n")
        util.emme_link_calc(scenario, "@sovoc", "length * %s + @tolls" % (auto_voc))
        #TODO: investigate why occupancy is only applied to tolls and not to fixed link costs
        util.emme_link_calc(scenario, "@hovoc", "(length * %s + @tolls) / %s" % (auto_voc, hov_occupancy))
        util.emme_link_calc(scenario, "@lgvoc", "length * %s + 2 * @tolls" % (lgv_voc))
        util.emme_link_calc(scenario, "@hgvoc", "length * %s + 3 * @tolls + @tkpen" % (hgv_voc))

    def init_matrices(self, eb):
        util = _m.Modeller().tool("translink.util")

        util.initmat(eb, "mf9900", "SOVGCTimeVOT1",  "SOV GC Minutes VOT1", 0)
        util.initmat(eb, "mf9901", "SOVGCTimeVOT2",  "SOV GC Minutes VOT2", 0)
        util.initmat(eb, "mf9902", "SOVGCTimeVOT3",  "SOV GC Minutes VOT3", 0)
        util.initmat(eb, "mf9903", "SOVGCTimeVOT4",  "SOV GC Minutes VOT4", 0)
        util.initmat(eb, "mf9904", "HOVGCTimeVOT1",  "HOV GC Minutes VOT1", 0)
        util.initmat(eb, "mf9905", "HOVGCTimeVOT2",  "HOV GC Minutes VOT2", 0)
        util.initmat(eb, "mf9906", "HOVGCTimeVOT3",  "HOV GC Minutes VOT3", 0)
        util.initmat(eb, "mf9907", "HOVGCTimeVOT4",  "HOV GC Minutes VOT4", 0)
        util.initmat(eb, "mf9908", "LGVGCTime",      "LGV GC Minutes", 0)
        util.initmat(eb, "mf9909", "HGVGCTime",      "HGV GC Minutes", 0)

        util.initmat(eb, "mf9910", "SOVDistVOT1",  "SOV Distance VOT1", 0)
        util.initmat(eb, "mf9911", "SOVDistVOT2",  "SOV Distance VOT2", 0)
        util.initmat(eb, "mf9912", "SOVDistVOT3",  "SOV Distance VOT3", 0)
        util.initmat(eb, "mf9913", "SOVDistVOT4",  "SOV Distance VOT4", 0)
        util.initmat(eb, "mf9914", "HOVDistVOT1",  "HOV Distance VOT1", 0)
        util.initmat(eb, "mf9915", "HOVDistVOT2",  "HOV Distance VOT2", 0)
        util.initmat(eb, "mf9916", "HOVDistVOT3",  "HOV Distance VOT3", 0)
        util.initmat(eb, "mf9917", "HOVDistVOT4",  "HOV Distance VOT4", 0)
        util.initmat(eb, "mf9918", "LGVDist",      "LGV Distance", 0)
        util.initmat(eb, "mf9919", "HGVDist",      "HGV Distance", 0)

        util.initmat(eb, "mf9920", "SOVTollVOT1",  "SOV Toll $ VOT1", 0)
        util.initmat(eb, "mf9921", "SOVTollVOT2",  "SOV Toll $ VOT2", 0)
        util.initmat(eb, "mf9922", "SOVTollVOT3",  "SOV Toll $ VOT3", 0)
        util.initmat(eb, "mf9923", "SOVTollVOT4",  "SOV Toll $ VOT4", 0)
        util.initmat(eb, "mf9924", "HOVTollVOT1",  "HOV Toll $ VOT1", 0)
        util.initmat(eb, "mf9925", "HOVTollVOT2",  "HOV Toll $ VOT2", 0)
        util.initmat(eb, "mf9926", "HOVTollVOT3",  "HOV Toll $ VOT3", 0)
        util.initmat(eb, "mf9927", "HOVTollVOT4",  "HOV Toll $ VOT4", 0)
        util.initmat(eb, "mf9928", "LGVToll",      "LGV Toll $", 0)
        util.initmat(eb, "mf9929", "HGVToll",      "HGV Toll $", 0)

        util.initmat(eb, "mf9930", "SOVOpCstVOT1",  "SOV Operating Cost $ VOT1", 0)
        util.initmat(eb, "mf9931", "SOVOpCstVOT2",  "SOV Operating Cost $ VOT2", 0)
        util.initmat(eb, "mf9932", "SOVOpCstVOT3",  "SOV Operating Cost $ VOT3", 0)
        util.initmat(eb, "mf9933", "SOVOpCstVOT4",  "SOV Operating Cost $ VOT4", 0)
        util.initmat(eb, "mf9934", "HOVOpCstVOT1",  "HOV Operating Cost $ VOT1", 0)
        util.initmat(eb, "mf9935", "HOVOpCstVOT2",  "HOV Operating Cost $ VOT2", 0)
        util.initmat(eb, "mf9936", "HOVOpCstVOT3",  "HOV Operating Cost $ VOT3", 0)
        util.initmat(eb, "mf9937", "HOVOpCstVOT4",  "HOV Operating Cost $ VOT4", 0)
        util.initmat(eb, "mf9938", "LGVOpCst",      "LGV Operating Cost $", 0)
        util.initmat(eb, "mf9939", "HGVOpCst",      "HGV Operating Cost $", 0)

        util.initmat(eb, "mf9940", "SOVTimeVOT1",  "SOV Travel Time VOT1", 0)
        util.initmat(eb, "mf9941", "SOVTimeVOT2",  "SOV Travel Time VOT2", 0)
        util.initmat(eb, "mf9942", "SOVTimeVOT3",  "SOV Travel Time VOT3", 0)
        util.initmat(eb, "mf9943", "SOVTimeVOT4",  "SOV Travel Time VOT4", 0)
        util.initmat(eb, "mf9944", "HOVTimeVOT1",  "HOV Travel Time VOT1", 0)
        util.initmat(eb, "mf9945", "HOVTimeVOT2",  "HOV Travel Time VOT2", 0)
        util.initmat(eb, "mf9946", "HOVTimeVOT3",  "HOV Travel Time VOT3", 0)
        util.initmat(eb, "mf9947", "HOVTimeVOT4",  "HOV Travel Time VOT4", 0)
        util.initmat(eb, "mf9948", "LGVTime",      "LGV Travel Time", 0)
        util.initmat(eb, "mf9949", "HGVTime",      "HGV Travel Time", 0)

