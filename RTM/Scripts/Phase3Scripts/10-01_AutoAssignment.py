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
        self.init_skim_matrices(am_scenario.emmebank)

        am_demands = {"sov":   ["mfSOV_drvtrp_VOT_1_Am", "mfSOV_drvtrp_VOT_2_Am", "mfSOV_drvtrp_VOT_3_Am", "mfSOV_drvtrp_VOT_4_Am"],
                      "hov":   ["mfHOV_drvtrp_VOT_1_Am", "mfHOV_drvtrp_VOT_2_Am", "mfHOV_drvtrp_VOT_3_Am"],
                      "truck": ["mflgvPceAm", "mfhgvPceAm"]}
        self.assign_scen(am_scenario, am_demands)
        am_skims = {"sovVot1":  ["mfAmSovOpCstVOT1", "mfAmSovTimeVOT1", "mfSkimAmSovTimeVOT1", "mfSkimAmSovDistVOT1", "mfSkimAmSovTollVOT1"],
                    "sovVot2":  ["mfAmSovOpCstVOT2", "mfAmSovTimeVOT2", "mfSkimAmSovTimeVOT2", "mfSkimAmSovDistVOT2", "mfSkimAmSovTollVOT2"],
                    "sovVot3":  ["mfAmSovOpCstVOT3", "mfAmSovTimeVOT3", "mfSkimAmSovTimeVOT3", "mfSkimAmSovDistVOT3", "mfSkimAmSovTollVOT3"],
                    "sovVot4":  ["mfAmSovOpCstVOT4", "mfAmSovTimeVOT4", "mfSkimAmSovTimeVOT4", "mfSkimAmSovDistVOT4", "mfSkimAmSovTollVOT4"],
                    "hovVot1":  ["mfAmHovOpCstVOT1", "mfAmHovTimeVOT1", "mfSkimAmHovTimeVOT1", "mfSkimAmHovDistVOT1", "mfSkimAmHovTollVOT1"],
                    "hovVot2":  ["mfAmHovOpCstVOT2", "mfAmHovTimeVOT2", "mfSkimAmHovTimeVOT2", "mfSkimAmHovDistVOT2", "mfSkimAmHovTollVOT2"],
                    "hovVot3":  ["mfAmHovOpCstVOT3", "mfAmHovTimeVOT3", "mfSkimAmHovTimeVOT3", "mfSkimAmHovDistVOT3", "mfSkimAmHovTollVOT3"],
                    "lgv":  ["mfAmLgvOpCst", "mfAmLgvTime", "mfSkimAmLgvTime", "mfSkimAmLgvDist", "mfSkimAmLgvToll"],
                    "hgv":  ["mfAmHgvOpCst", "mfAmHgvTime", "mfSkimAmHgvTime", "mfSkimAmHgvDist", "mfSkimAmHgvToll"]}
        self.store_skims(am_scenario, am_skims)

        md_demands = {"sov":   ["mfSOV_drvtrp_VOT_1_Md", "mfSOV_drvtrp_VOT_2_Md", "mfSOV_drvtrp_VOT_3_Md", "mfSOV_drvtrp_VOT_4_Md"],
                      "hov":   ["mfHOV_drvtrp_VOT_1_Md", "mfHOV_drvtrp_VOT_2_Md", "mfHOV_drvtrp_VOT_3_Md"],
                      "truck": ["mflgvPceMd", "mfhgvPceMd"]}
        self.assign_scen(md_scenario, md_demands)
        md_skims = {"sovVot1":  ["mfMdSovOpCstVOT1", "mfMdSovTimeVOT1", "mfSkimMdSovTimeVOT1", "mfSkimMdSovDistVOT1", "mfSkimMdSovTollVOT1"],
                    "sovVot2":  ["mfMdSovOpCstVOT2", "mfMdSovTimeVOT2", "mfSkimMdSovTimeVOT2", "mfSkimMdSovDistVOT2", "mfSkimMdSovTollVOT2"],
                    "sovVot3":  ["mfMdSovOpCstVOT3", "mfMdSovTimeVOT3", "mfSkimMdSovTimeVOT3", "mfSkimMdSovDistVOT3", "mfSkimMdSovTollVOT3"],
                    "sovVot4":  ["mfMdSovOpCstVOT4", "mfMdSovTimeVOT4", "mfSkimMdSovTimeVOT4", "mfSkimMdSovDistVOT4", "mfSkimMdSovTollVOT4"],
                    "hovVot1":  ["mfMdHovOpCstVOT1", "mfMdHovTimeVOT1", "mfSkimMdHovTimeVOT1", "mfSkimMdHovDistVOT1", "mfSkimMdHovTollVOT1"],
                    "hovVot2":  ["mfMdHovOpCstVOT2", "mfMdHovTimeVOT2", "mfSkimMdHovTimeVOT2", "mfSkimMdHovDistVOT2", "mfSkimMdHovTollVOT2"],
                    "hovVot3":  ["mfMdHovOpCstVOT3", "mfMdHovTimeVOT3", "mfSkimMdHovTimeVOT3", "mfSkimMdHovDistVOT3", "mfSkimMdHovTollVOT3"],
                    "lgv":  ["mfMdLgvOpCst", "mfMdLgvTime", "mfSkimMdLgvTime", "mfSkimMdLgvDist", "mfSkimMdLgvToll"],
                    "hgv":  ["mfMdHgvOpCst", "mfMdHgvTime", "mfSkimMdHgvTime", "mfSkimMdHgvDist", "mfSkimMdHgvToll"]}
        self.store_skims(md_scenario, md_skims)
        pm_demands = {"sov":   ["mfSOV_drvtrp_VOT_1_Pm", "mfSOV_drvtrp_VOT_2_Pm", "mfSOV_drvtrp_VOT_3_Pm", "mfSOV_drvtrp_VOT_4_Pm"],
                      "hov":   ["mfHOV_drvtrp_VOT_1_Pm", "mfHOV_drvtrp_VOT_2_Pm", "mfHOV_drvtrp_VOT_3_Pm"],
                      "truck": ["mflgvPcePm", "mfhgvPcePm"]}
        self.assign_scen(pm_scenario, pm_demands)
        pm_skims = {"sovVot1":  ["mfPmSovOpCstVOT1", "mfPmSovTimeVOT1", "mfSkimPmSovTimeVOT1", "mfSkimPmSovDistVOT1", "mfSkimPmSovTollVOT1"],
                    "sovVot2":  ["mfPmSovOpCstVOT2", "mfPmSovTimeVOT2", "mfSkimPmSovTimeVOT2", "mfSkimPmSovDistVOT2", "mfSkimPmSovTollVOT2"],
                    "sovVot3":  ["mfPmSovOpCstVOT3", "mfPmSovTimeVOT3", "mfSkimPmSovTimeVOT3", "mfSkimPmSovDistVOT3", "mfSkimPmSovTollVOT3"],
                    "sovVot4":  ["mfPmSovOpCstVOT4", "mfPmSovTimeVOT4", "mfSkimPmSovTimeVOT4", "mfSkimPmSovDistVOT4", "mfSkimPmSovTollVOT4"],
                    "hovVot1":  ["mfPmHovOpCstVOT1", "mfPmHovTimeVOT1", "mfSkimPmHovTimeVOT1", "mfSkimPmHovDistVOT1", "mfSkimPmHovTollVOT1"],
                    "hovVot2":  ["mfPmHovOpCstVOT2", "mfPmHovTimeVOT2", "mfSkimPmHovTimeVOT2", "mfSkimPmHovDistVOT2", "mfSkimPmHovTollVOT2"],
                    "hovVot3":  ["mfPmHovOpCstVOT3", "mfPmHovTimeVOT3", "mfSkimPmHovTimeVOT3", "mfSkimPmHovDistVOT3", "mfSkimPmHovTollVOT3"],
                    "lgv":  ["mfPmLgvOpCst", "mfPmLgvTime", "mfSkimPmLgvTime", "mfSkimPmLgvDist", "mfSkimPmLgvToll"],
                    "hgv":  ["mfPmHgvOpCst", "mfPmHgvTime", "mfSkimPmHgvTime", "mfSkimPmHgvDist", "mfSkimPmHgvToll"]}
        self.store_skims(pm_scenario, pm_skims)

    def assign_scen(self, scenario, demands):
        assign_traffic = _m.Modeller().tool("inro.emme.traffic_assignment.sola_traffic_assignment")

        self.calc_network_costs(scenario)
        self.init_matrices(scenario.emmebank)

        # Generate basic specification of modes/VOTs/saved volumes
        spec = self.get_class_specs(scenario.emmebank, demands)

        # skim the vehicle operating costs
        self.add_opcost_path_analysis(spec)

        # conditionally skim the tolls on the final model cycle
        skimToll = int(scenario.emmebank.matrix("mstollSkim").data)
        if skimToll == 1:
            max_cycles = int(scenario.emmebank.matrix("msIterGlobal").data)
            cur_cycles = int(scenario.emmebank.matrix("msCycleNum").data)
            if max_cycles == cur_cycles:
                self.add_toll_path_analysis(spec)
                self.add_distance_path_analysis(spec)


        # run assignment
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

        time = gc - (opcst * vot)
        opcst = opcst * occupancy

        util.set_matrix_numpy(eb, time_mat, time)
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
        #compute social cost after each run
        self.calc_network_social_costs(scenario)
        self.calc_transit_us2(scenario)

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

        # Set Skimmed Time Matrices
        specs.append(util.matrix_spec(skim_list["sovVot1"][2], "mfSOVTimeVOT1"))
        specs.append(util.matrix_spec(skim_list["sovVot2"][2], "mfSOVTimeVOT2"))
        specs.append(util.matrix_spec(skim_list["sovVot3"][2], "mfSOVTimeVOT3"))
        specs.append(util.matrix_spec(skim_list["sovVot4"][2], "mfSOVTimeVOT4"))
        specs.append(util.matrix_spec(skim_list["hovVot1"][2], "mfHOVTimeVOT1"))
        specs.append(util.matrix_spec(skim_list["hovVot2"][2], "mfHOVTimeVOT2"))
        specs.append(util.matrix_spec(skim_list["hovVot3"][2], "mfHOVTimeVOT3"))
        specs.append(util.matrix_spec(skim_list["lgv"][2], "mfLGVTime"))
        specs.append(util.matrix_spec(skim_list["hgv"][2], "mfHGVTime"))

        # Set Skimmed Distance Matrices
        specs.append(util.matrix_spec(skim_list["sovVot1"][3], "mfSOVDistVOT1"))
        specs.append(util.matrix_spec(skim_list["sovVot2"][3], "mfSOVDistVOT2"))
        specs.append(util.matrix_spec(skim_list["sovVot3"][3], "mfSOVDistVOT3"))
        specs.append(util.matrix_spec(skim_list["sovVot4"][3], "mfSOVDistVOT4"))
        specs.append(util.matrix_spec(skim_list["hovVot1"][3], "mfHOVDistVOT1"))
        specs.append(util.matrix_spec(skim_list["hovVot2"][3], "mfHOVDistVOT2"))
        specs.append(util.matrix_spec(skim_list["hovVot3"][3], "mfHOVDistVOT3"))
        specs.append(util.matrix_spec(skim_list["lgv"][3], "mfLGVDist"))
        specs.append(util.matrix_spec(skim_list["hgv"][3], "mfHGVDist"))

        # Set Skimmed Toll Matrices
        specs.append(util.matrix_spec(skim_list["sovVot1"][4], "mfSOVTollVOT1"))
        specs.append(util.matrix_spec(skim_list["sovVot2"][4], "mfSOVTollVOT2"))
        specs.append(util.matrix_spec(skim_list["sovVot3"][4], "mfSOVTollVOT3"))
        specs.append(util.matrix_spec(skim_list["sovVot4"][4], "mfSOVTollVOT4"))
        specs.append(util.matrix_spec(skim_list["hovVot1"][4], "mfHOVTollVOT1"))
        specs.append(util.matrix_spec(skim_list["hovVot2"][4], "mfHOVTollVOT2"))
        specs.append(util.matrix_spec(skim_list["hovVot3"][4], "mfHOVTollVOT3"))
        specs.append(util.matrix_spec(skim_list["lgv"][4], "mfLGVToll"))
        specs.append(util.matrix_spec(skim_list["hgv"][4], "mfHGVToll"))

        util.compute_matrix(specs, scenario)

        # now that the skims have been written back, delete the temporary matrices
        for matrix in self.get_temp_matrices():
            util.delmat(scenario.emmebank, matrix[0])

    def add_mode_specification(self, specs, mode, demand, gc_cost, gc_factor, travel_time, link_vol, turn_vol):
        spec = {"mode": mode,
                "demand": demand,
                "generalized_cost": { "link_costs": gc_cost, "perception_factor": gc_factor },
                "results": { "od_travel_times": {"shortest_paths": travel_time},
                             "link_volumes": link_vol,
                             "turn_volumes": turn_vol },
                "path_analyses": []
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

    def add_opcost_path_analysis(self, spec):
        path_od = { "considered_paths": "ALL",
                    "multiply_path_proportions_by": { "analyzed_demand": False, "path_value": True }
                  }
        spec["classes"][ 0]["path_analyses"].append({"results": {"od_values": "mfSOVOpCstVOT1"}, "link_component": "@sovoc", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 1]["path_analyses"].append({"results": {"od_values": "mfSOVOpCstVOT2"}, "link_component": "@sovoc", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 2]["path_analyses"].append({"results": {"od_values": "mfSOVOpCstVOT3"}, "link_component": "@sovoc", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 3]["path_analyses"].append({"results": {"od_values": "mfSOVOpCstVOT4"}, "link_component": "@sovoc", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 4]["path_analyses"].append({"results": {"od_values": "mfHOVOpCstVOT1"}, "link_component": "@hovoc", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 5]["path_analyses"].append({"results": {"od_values": "mfHOVOpCstVOT2"}, "link_component": "@hovoc", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 6]["path_analyses"].append({"results": {"od_values": "mfHOVOpCstVOT3"}, "link_component": "@hovoc", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 7]["path_analyses"].append({"results": {"od_values": "mfLGVOpCst"},     "link_component": "@lgvoc", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 8]["path_analyses"].append({"results": {"od_values": "mfHGVOpCst"},     "link_component": "@hgvoc", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })

    def add_toll_path_analysis(self, spec):
        path_od = { "considered_paths": "ALL",
                    "multiply_path_proportions_by": { "analyzed_demand": False, "path_value": True }
                  }
        spec["classes"][ 0]["path_analyses"].append({"results": {"od_values": "mfSOVTollVOT1"}, "link_component": "@tolls", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 1]["path_analyses"].append({"results": {"od_values": "mfSOVTollVOT2"}, "link_component": "@tolls", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 2]["path_analyses"].append({"results": {"od_values": "mfSOVTollVOT3"}, "link_component": "@tolls", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 3]["path_analyses"].append({"results": {"od_values": "mfSOVTollVOT4"}, "link_component": "@tolls", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 4]["path_analyses"].append({"results": {"od_values": "mfHOVTollVOT1"}, "link_component": "@tolls", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 5]["path_analyses"].append({"results": {"od_values": "mfHOVTollVOT2"}, "link_component": "@tolls", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 6]["path_analyses"].append({"results": {"od_values": "mfHOVTollVOT3"}, "link_component": "@tolls", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 7]["path_analyses"].append({"results": {"od_values": "mfLGVToll"},     "link_component": "@tolls", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 8]["path_analyses"].append({"results": {"od_values": "mfHGVToll"},     "link_component": "@tolls", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })

    def add_distance_path_analysis(self, spec):
        path_od = { "considered_paths": "ALL",
                    "multiply_path_proportions_by": { "analyzed_demand": False, "path_value": True }
                  }
        spec["classes"][ 0]["path_analyses"].append({"results": {"od_values": "mfSOVDistVOT1"}, "link_component": "length", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 1]["path_analyses"].append({"results": {"od_values": "mfSOVDistVOT2"}, "link_component": "length", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 2]["path_analyses"].append({"results": {"od_values": "mfSOVDistVOT3"}, "link_component": "length", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 3]["path_analyses"].append({"results": {"od_values": "mfSOVDistVOT4"}, "link_component": "length", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 4]["path_analyses"].append({"results": {"od_values": "mfHOVDistVOT1"}, "link_component": "length", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 5]["path_analyses"].append({"results": {"od_values": "mfHOVDistVOT2"}, "link_component": "length", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 6]["path_analyses"].append({"results": {"od_values": "mfHOVDistVOT3"}, "link_component": "length", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 7]["path_analyses"].append({"results": {"od_values": "mfLGVDist"},     "link_component": "length", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 8]["path_analyses"].append({"results": {"od_values": "mfHGVDist"},     "link_component": "length", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })

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

        lgv_tollfac = eb.matrix("mslgvTollFac").data
        hgv_tollfac = eb.matrix("mshgvTollFac").data
        sov_tollfac = eb.matrix("mssovTollFac").data
        hov_tollfac = eb.matrix("mshovTollFac").data

        util.emme_link_calc(scenario, "@tkpen", "0")
        util.emme_link_calc(scenario, "@tkpen", "length * 100", sel_link="mode=n")
        util.emme_link_calc(scenario, "@sovoc", "length * %s + @tolls * %s" % (auto_voc, sov_tollfac))
        #TODO: investigate why occupancy is only applied to tolls and not to fixed link costs
        util.emme_link_calc(scenario, "@hovoc", "(length * %s + @tolls * %s) / %s" % (auto_voc, hov_tollfac, hov_occupancy))
        util.emme_link_calc(scenario, "@lgvoc", "length * %s + %s * @tolls" % (lgv_voc, lgv_tollfac))
        util.emme_link_calc(scenario, "@hgvoc", "length * %s + %s * @tolls + @tkpen" % (hgv_voc, hgv_tollfac))

    def init_skim_matrices(self, eb):
        util = _m.Modeller().tool("translink.util")

        # AM Time Skims
        util.initmat(eb, "mf8100", "SkimAmSovTimeVOT1", "Skim AM SOV VOT1 Time", 0)
        util.initmat(eb, "mf8101", "SkimAmSovTimeVOT2", "Skim AM SOV VOT2 Time", 0)
        util.initmat(eb, "mf8102", "SkimAmSovTimeVOT3", "Skim AM SOV VOT3 Time", 0)
        util.initmat(eb, "mf8103", "SkimAmSovTimeVOT4", "Skim AM SOV VOT4 Time", 0)
        util.initmat(eb, "mf8104", "SkimAmHovTimeVOT1", "Skim AM HOV VOT1 Time", 0)
        util.initmat(eb, "mf8105", "SkimAmHovTimeVOT2", "Skim AM HOV VOT2 Time", 0)
        util.initmat(eb, "mf8106", "SkimAmHovTimeVOT3", "Skim AM HOV VOT3 Time", 0)
        util.initmat(eb, "mf8107", "SkimAmHovTimeVOT4", "Skim AM HOV VOT4 Time", 0)
        util.initmat(eb, "mf8108", "SkimAmLgvTime",     "Skim AM LGV Time",      0)
        util.initmat(eb, "mf8109", "SkimAmHgvTime",     "Skim AM HGV Time",      0)
        # AM Distance Skims
        util.initmat(eb, "mf8110", "SkimAmSovDistVOT1", "Skim AM SOV VOT1 Dist", 0)
        util.initmat(eb, "mf8111", "SkimAmSovDistVOT2", "Skim AM SOV VOT2 Dist", 0)
        util.initmat(eb, "mf8112", "SkimAmSovDistVOT3", "Skim AM SOV VOT3 Dist", 0)
        util.initmat(eb, "mf8113", "SkimAmSovDistVOT4", "Skim AM SOV VOT4 Dist", 0)
        util.initmat(eb, "mf8114", "SkimAmHovDistVOT1", "Skim AM HOV VOT1 Dist", 0)
        util.initmat(eb, "mf8115", "SkimAmHovDistVOT2", "Skim AM HOV VOT2 Dist", 0)
        util.initmat(eb, "mf8116", "SkimAmHovDistVOT3", "Skim AM HOV VOT3 Dist", 0)
        util.initmat(eb, "mf8117", "SkimAmHovDistVOT4", "Skim AM HOV VOT4 Dist", 0)
        util.initmat(eb, "mf8118", "SkimAmLgvDist",     "Skim AM LGV Dist",      0)
        util.initmat(eb, "mf8119", "SkimAmHgvDist",     "Skim AM HGV Dist",      0)
        # AM Toll Skims
        util.initmat(eb, "mf8120", "SkimAmSovTollVOT1", "Skim AM SOV VOT1 Toll", 0)
        util.initmat(eb, "mf8121", "SkimAmSovTollVOT2", "Skim AM SOV VOT2 Toll", 0)
        util.initmat(eb, "mf8122", "SkimAmSovTollVOT3", "Skim AM SOV VOT3 Toll", 0)
        util.initmat(eb, "mf8123", "SkimAmSovTollVOT4", "Skim AM SOV VOT4 Toll", 0)
        util.initmat(eb, "mf8124", "SkimAmHovTollVOT1", "Skim AM HOV VOT1 Toll", 0)
        util.initmat(eb, "mf8125", "SkimAmHovTollVOT2", "Skim AM HOV VOT2 Toll", 0)
        util.initmat(eb, "mf8126", "SkimAmHovTollVOT3", "Skim AM HOV VOT3 Toll", 0)
        util.initmat(eb, "mf8127", "SkimAmHovTollVOT4", "Skim AM HOV VOT4 Toll", 0)
        util.initmat(eb, "mf8128", "SkimAmLgvToll",     "Skim AM LGV Toll",      0)
        util.initmat(eb, "mf8129", "SkimAmHgvToll",     "Skim AM HGV Toll",      0)

        # MD Time Skims
        util.initmat(eb, "mf8130", "SkimMdSovTimeVOT1", "Skim MD SOV VOT1 Time", 0)
        util.initmat(eb, "mf8131", "SkimMdSovTimeVOT2", "Skim MD SOV VOT2 Time", 0)
        util.initmat(eb, "mf8132", "SkimMdSovTimeVOT3", "Skim MD SOV VOT3 Time", 0)
        util.initmat(eb, "mf8133", "SkimMdSovTimeVOT4", "Skim MD SOV VOT4 Time", 0)
        util.initmat(eb, "mf8134", "SkimMdHovTimeVOT1", "Skim MD HOV VOT1 Time", 0)
        util.initmat(eb, "mf8135", "SkimMdHovTimeVOT2", "Skim MD HOV VOT2 Time", 0)
        util.initmat(eb, "mf8136", "SkimMdHovTimeVOT3", "Skim MD HOV VOT3 Time", 0)
        util.initmat(eb, "mf8137", "SkimMdHovTimeVOT4", "Skim MD HOV VOT4 Time", 0)
        util.initmat(eb, "mf8138", "SkimMdLgvTime",     "Skim MD LGV Time",      0)
        util.initmat(eb, "mf8139", "SkimMdHgvTime",     "Skim MD HGV Time",      0)
        # MD Distance Skims
        util.initmat(eb, "mf8140", "SkimMdSovDistVOT1", "Skim MD SOV VOT1 Dist", 0)
        util.initmat(eb, "mf8141", "SkimMdSovDistVOT2", "Skim MD SOV VOT2 Dist", 0)
        util.initmat(eb, "mf8142", "SkimMdSovDistVOT3", "Skim MD SOV VOT3 Dist", 0)
        util.initmat(eb, "mf8143", "SkimMdSovDistVOT4", "Skim MD SOV VOT4 Dist", 0)
        util.initmat(eb, "mf8144", "SkimMdHovDistVOT1", "Skim MD HOV VOT1 Dist", 0)
        util.initmat(eb, "mf8145", "SkimMdHovDistVOT2", "Skim MD HOV VOT2 Dist", 0)
        util.initmat(eb, "mf8146", "SkimMdHovDistVOT3", "Skim MD HOV VOT3 Dist", 0)
        util.initmat(eb, "mf8147", "SkimMdHovDistVOT4", "Skim MD HOV VOT4 Dist", 0)
        util.initmat(eb, "mf8148", "SkimMdLgvDist",     "Skim MD LGV Dist",      0)
        util.initmat(eb, "mf8149", "SkimMdHgvDist",     "Skim MD HGV Dist",      0)
        # MD Toll Skims
        util.initmat(eb, "mf8150", "SkimMdSovTollVOT1", "Skim MD SOV VOT1 Toll", 0)
        util.initmat(eb, "mf8151", "SkimMdSovTollVOT2", "Skim MD SOV VOT2 Toll", 0)
        util.initmat(eb, "mf8152", "SkimMdSovTollVOT3", "Skim MD SOV VOT3 Toll", 0)
        util.initmat(eb, "mf8153", "SkimMdSovTollVOT4", "Skim MD SOV VOT4 Toll", 0)
        util.initmat(eb, "mf8154", "SkimMdHovTollVOT1", "Skim MD HOV VOT1 Toll", 0)
        util.initmat(eb, "mf8155", "SkimMdHovTollVOT2", "Skim MD HOV VOT2 Toll", 0)
        util.initmat(eb, "mf8156", "SkimMdHovTollVOT3", "Skim MD HOV VOT3 Toll", 0)
        util.initmat(eb, "mf8157", "SkimMdHovTollVOT4", "Skim MD HOV VOT4 Toll", 0)
        util.initmat(eb, "mf8158", "SkimMdLgvToll",     "Skim MD LGV Toll",      0)
        util.initmat(eb, "mf8159", "SkimMdHgvToll",     "Skim MD HGV Toll",      0)

        # PM Time Skims
        util.initmat(eb, "mf8160", "SkimPmSovTimeVOT1", "Skim PM SOV VOT1 Time", 0)
        util.initmat(eb, "mf8161", "SkimPmSovTimeVOT2", "Skim PM SOV VOT2 Time", 0)
        util.initmat(eb, "mf8162", "SkimPmSovTimeVOT3", "Skim PM SOV VOT3 Time", 0)
        util.initmat(eb, "mf8163", "SkimPmSovTimeVOT4", "Skim PM SOV VOT4 Time", 0)
        util.initmat(eb, "mf8164", "SkimPmHovTimeVOT1", "Skim PM HOV VOT1 Time", 0)
        util.initmat(eb, "mf8165", "SkimPmHovTimeVOT2", "Skim PM HOV VOT2 Time", 0)
        util.initmat(eb, "mf8166", "SkimPmHovTimeVOT3", "Skim PM HOV VOT3 Time", 0)
        util.initmat(eb, "mf8167", "SkimPmHovTimeVOT4", "Skim PM HOV VOT4 Time", 0)
        util.initmat(eb, "mf8168", "SkimPmLgvTime",     "Skim PM LGV Time",      0)
        util.initmat(eb, "mf8169", "SkimPmHgvTime",     "Skim PM HGV Time",      0)
        # PM Distance Skims
        util.initmat(eb, "mf8170", "SkimPmSovDistVOT1", "Skim PM SOV VOT1 Dist", 0)
        util.initmat(eb, "mf8171", "SkimPmSovDistVOT2", "Skim PM SOV VOT2 Dist", 0)
        util.initmat(eb, "mf8172", "SkimPmSovDistVOT3", "Skim PM SOV VOT3 Dist", 0)
        util.initmat(eb, "mf8173", "SkimPmSovDistVOT4", "Skim PM SOV VOT4 Dist", 0)
        util.initmat(eb, "mf8174", "SkimPmHovDistVOT1", "Skim PM HOV VOT1 Dist", 0)
        util.initmat(eb, "mf8175", "SkimPmHovDistVOT2", "Skim PM HOV VOT2 Dist", 0)
        util.initmat(eb, "mf8176", "SkimPmHovDistVOT3", "Skim PM HOV VOT3 Dist", 0)
        util.initmat(eb, "mf8177", "SkimPmHovDistVOT4", "Skim PM HOV VOT4 Dist", 0)
        util.initmat(eb, "mf8178", "SkimPmLgvDist",     "Skim PM LGV Dist",      0)
        util.initmat(eb, "mf8179", "SkimPmHgvDist",     "Skim PM HGV Dist",      0)
        # PM Toll Skims
        util.initmat(eb, "mf8180", "SkimPmSovTollVOT1", "Skim PM SOV VOT1 Toll", 0)
        util.initmat(eb, "mf8181", "SkimPmSovTollVOT2", "Skim PM SOV VOT2 Toll", 0)
        util.initmat(eb, "mf8182", "SkimPmSovTollVOT3", "Skim PM SOV VOT3 Toll", 0)
        util.initmat(eb, "mf8183", "SkimPmSovTollVOT4", "Skim PM SOV VOT4 Toll", 0)
        util.initmat(eb, "mf8184", "SkimPmHovTollVOT1", "Skim PM HOV VOT1 Toll", 0)
        util.initmat(eb, "mf8185", "SkimPmHovTollVOT2", "Skim PM HOV VOT2 Toll", 0)
        util.initmat(eb, "mf8186", "SkimPmHovTollVOT3", "Skim PM HOV VOT3 Toll", 0)
        util.initmat(eb, "mf8187", "SkimPmHovTollVOT4", "Skim PM HOV VOT4 Toll", 0)
        util.initmat(eb, "mf8188", "SkimPmLgvToll",     "Skim PM LGV Toll",      0)
        util.initmat(eb, "mf8189", "SkimPmHgvToll",     "Skim PM HGV Toll",      0)

    def init_matrices(self, eb):
        util = _m.Modeller().tool("translink.util")

        for matrix in self.get_temp_matrices():
            util.initmat(eb, matrix[0], matrix[1], matrix[2], matrix[3])

    def get_temp_matrices(self):
        matrices = []

        matrices.append(["mf9900", "SOVGCTimeVOT1",  "SOV GC Minutes VOT1", 0])
        matrices.append(["mf9901", "SOVGCTimeVOT2",  "SOV GC Minutes VOT2", 0])
        matrices.append(["mf9902", "SOVGCTimeVOT3",  "SOV GC Minutes VOT3", 0])
        matrices.append(["mf9903", "SOVGCTimeVOT4",  "SOV GC Minutes VOT4", 0])
        matrices.append(["mf9904", "HOVGCTimeVOT1",  "HOV GC Minutes VOT1", 0])
        matrices.append(["mf9905", "HOVGCTimeVOT2",  "HOV GC Minutes VOT2", 0])
        matrices.append(["mf9906", "HOVGCTimeVOT3",  "HOV GC Minutes VOT3", 0])
        matrices.append(["mf9907", "HOVGCTimeVOT4",  "HOV GC Minutes VOT4", 0])
        matrices.append(["mf9908", "LGVGCTime",      "LGV GC Minutes", 0])
        matrices.append(["mf9909", "HGVGCTime",      "HGV GC Minutes", 0])

        matrices.append(["mf9910", "SOVDistVOT1",  "SOV Distance VOT1", 0])
        matrices.append(["mf9911", "SOVDistVOT2",  "SOV Distance VOT2", 0])
        matrices.append(["mf9912", "SOVDistVOT3",  "SOV Distance VOT3", 0])
        matrices.append(["mf9913", "SOVDistVOT4",  "SOV Distance VOT4", 0])
        matrices.append(["mf9914", "HOVDistVOT1",  "HOV Distance VOT1", 0])
        matrices.append(["mf9915", "HOVDistVOT2",  "HOV Distance VOT2", 0])
        matrices.append(["mf9916", "HOVDistVOT3",  "HOV Distance VOT3", 0])
        matrices.append(["mf9917", "HOVDistVOT4",  "HOV Distance VOT4", 0])
        matrices.append(["mf9918", "LGVDist",      "LGV Distance", 0])
        matrices.append(["mf9919", "HGVDist",      "HGV Distance", 0])

        matrices.append(["mf9920", "SOVTollVOT1",  "SOV Toll $ VOT1", 0])
        matrices.append(["mf9921", "SOVTollVOT2",  "SOV Toll $ VOT2", 0])
        matrices.append(["mf9922", "SOVTollVOT3",  "SOV Toll $ VOT3", 0])
        matrices.append(["mf9923", "SOVTollVOT4",  "SOV Toll $ VOT4", 0])
        matrices.append(["mf9924", "HOVTollVOT1",  "HOV Toll $ VOT1", 0])
        matrices.append(["mf9925", "HOVTollVOT2",  "HOV Toll $ VOT2", 0])
        matrices.append(["mf9926", "HOVTollVOT3",  "HOV Toll $ VOT3", 0])
        matrices.append(["mf9927", "HOVTollVOT4",  "HOV Toll $ VOT4", 0])
        matrices.append(["mf9928", "LGVToll",      "LGV Toll $", 0])
        matrices.append(["mf9929", "HGVToll",      "HGV Toll $", 0])

        matrices.append(["mf9930", "SOVOpCstVOT1",  "SOV Operating Cost $ VOT1", 0])
        matrices.append(["mf9931", "SOVOpCstVOT2",  "SOV Operating Cost $ VOT2", 0])
        matrices.append(["mf9932", "SOVOpCstVOT3",  "SOV Operating Cost $ VOT3", 0])
        matrices.append(["mf9933", "SOVOpCstVOT4",  "SOV Operating Cost $ VOT4", 0])
        matrices.append(["mf9934", "HOVOpCstVOT1",  "HOV Operating Cost $ VOT1", 0])
        matrices.append(["mf9935", "HOVOpCstVOT2",  "HOV Operating Cost $ VOT2", 0])
        matrices.append(["mf9936", "HOVOpCstVOT3",  "HOV Operating Cost $ VOT3", 0])
        matrices.append(["mf9937", "HOVOpCstVOT4",  "HOV Operating Cost $ VOT4", 0])
        matrices.append(["mf9938", "LGVOpCst",      "LGV Operating Cost $", 0])
        matrices.append(["mf9939", "HGVOpCst",      "HGV Operating Cost $", 0])

        matrices.append(["mf9940", "SOVTimeVOT1",  "SOV Travel Time VOT1", 0])
        matrices.append(["mf9941", "SOVTimeVOT2",  "SOV Travel Time VOT2", 0])
        matrices.append(["mf9942", "SOVTimeVOT3",  "SOV Travel Time VOT3", 0])
        matrices.append(["mf9943", "SOVTimeVOT4",  "SOV Travel Time VOT4", 0])
        matrices.append(["mf9944", "HOVTimeVOT1",  "HOV Travel Time VOT1", 0])
        matrices.append(["mf9945", "HOVTimeVOT2",  "HOV Travel Time VOT2", 0])
        matrices.append(["mf9946", "HOVTimeVOT3",  "HOV Travel Time VOT3", 0])
        matrices.append(["mf9947", "HOVTimeVOT4",  "HOV Travel Time VOT4", 0])
        matrices.append(["mf9948", "LGVTime",      "LGV Travel Time", 0])
        matrices.append(["mf9949", "HGVTime",      "HGV Travel Time", 0])

        return matrices

    def calc_network_social_costs(self, scenario):
        util = _m.Modeller().tool("translink.util")

        # initialize ul1
        util.emme_link_calc(scenario, "ul1", "0")

        #initialize ul1 to timau where it exists
        util.emme_link_calc(scenario, "ul1", "timau", sel_link="mode=v")

        #ul1 = timau using old VDF calculations
        #ul1 = -1 where mode is not auto or lane = 0
        util.emme_link_calc(scenario, "ul1", "(0.25 + length * 60 / @posted_speed + .85 * ((volau + volad) / ( 400 * lanes)) ^ 4)", sel_link="vdf=26 and mode=v")
        util.emme_link_calc(scenario, "ul1", "(0.25 + length * 60 / @posted_speed + .85 * ((volau + volad) / ( 600 * lanes)) ^ 4)", sel_link="vdf=36 and mode=v")
        util.emme_link_calc(scenario, "ul1", "(0.25 + length * 60 / @posted_speed + .85 * ((volau + volad) / ( 800 * lanes)) ^ 4)", sel_link="vdf=46 and mode=v")
        util.emme_link_calc(scenario, "ul1", "(0.25 + length * 60 / @posted_speed + .85 * ((volau + volad) / (1000 * lanes)) ^ 4)", sel_link="vdf=56 and mode=v")
        util.emme_link_calc(scenario, "ul1", "(0.25 + length * 60 / @posted_speed + .85 * ((volau + volad) / (1200 * lanes)) ^ 4)", sel_link="vdf=66 and mode=v")
        util.emme_link_calc(scenario, "ul1", "(0.25 + length * 60 / @posted_speed + .85 * ((volau + volad) / (1400 * lanes)) ^ 4)", sel_link="vdf=76 and mode=v")
        util.emme_link_calc(scenario, "ul1", "(length * 60 / @posted_speed * (1 + .6 * .85 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 5))", sel_link="vdf=86 and mode=v")
        util.emme_link_calc(scenario, "ul1", "(length * 60 / (@posted_speed * 1.1) * (1 + .6 * .43 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 5.25))", sel_link="vdf=89 and mode=v")
        util.emme_link_calc(scenario, "ul1", "(length * 60 / @posted_speed + 0.85 * ((volau + volad) / ( 600*lanes))^5)", sel_link="vdf=13 and mode=v")
        util.emme_link_calc(scenario, "ul1", "(length * 60 / @posted_speed + 0.85 * ((volau + volad) / ( 800*lanes))^5)", sel_link="vdf=14 and mode=v")
        util.emme_link_calc(scenario, "ul1", "(length * 60 / @posted_speed + 0.85 * ((volau + volad) / (1000*lanes))^5)", sel_link="vdf=15 and mode=v")
        util.emme_link_calc(scenario, "ul1", "(length * 60 / @posted_speed + 0.85 * ((volau + volad) / (1200*lanes))^5)", sel_link="vdf=16 and mode=v")
        util.emme_link_calc(scenario, "ul1", "(length * 60 / @posted_speed + 0.85 * ((volau + volad) / (1400*lanes))^5)", sel_link="vdf=17 and mode=v")
        #ul2 = social cost as travel time
        util.emme_link_calc(scenario, "ul2", "0")
        util.emme_link_calc(scenario, "ul2", "timau-ul1", sel_link="mode=v")

    def calc_transit_us2(self, scenario):
        util = _m.Modeller().tool("translink.util")

        # calculate a default time where timau does not exist
        util.emme_segment_calc(scenario, "us2", "60*length/speed")
        util.emme_segment_calc(scenario, "us2", "timau", sel_link="mode=v")

        #us2=timau where timau exists
        util.emme_segment_calc(scenario, "us2", "(0.25 + length * 60 / @posted_speed + .85 * ((volau + volad) / ( 400 * lanes)) ^ 4)", sel_link="vdf=26 and mode=v")
        util.emme_segment_calc(scenario, "us2", "(0.25 + length * 60 / @posted_speed + .85 * ((volau + volad) / ( 600 * lanes)) ^ 4)", sel_link="vdf=36 and mode=v")
        util.emme_segment_calc(scenario, "us2", "(0.25 + length * 60 / @posted_speed + .85 * ((volau + volad) / ( 800 * lanes)) ^ 4)", sel_link="vdf=46 and mode=v")
        util.emme_segment_calc(scenario, "us2", "(0.25 + length * 60 / @posted_speed + .85 * ((volau + volad) / (1000 * lanes)) ^ 4)", sel_link="vdf=56 and mode=v")
        util.emme_segment_calc(scenario, "us2", "(0.25 + length * 60 / @posted_speed + .85 * ((volau + volad) / (1200 * lanes)) ^ 4)", sel_link="vdf=66 and mode=v")
        util.emme_segment_calc(scenario, "us2", "(0.25 + length * 60 / @posted_speed + .85 * ((volau + volad) / (1400 * lanes)) ^ 4)", sel_link="vdf=76 and mode=v")
        util.emme_segment_calc(scenario, "us2", "(length * 60 / @posted_speed * (1 + .6 * .85 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 5))", sel_link="vdf=86 and mode=v")
        util.emme_segment_calc(scenario, "us2", "(length * 60 / (@posted_speed * 1.1) * (1 + .6 * .43 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 5.25))", sel_link="vdf=89 and mode=v")
        util.emme_segment_calc(scenario, "us2", "(length * 60 / @posted_speed + 0.85 * ((volau + volad) / ( 600*lanes))^5)", sel_link="vdf=13 and mode=v")
        util.emme_segment_calc(scenario, "us2", "(length * 60 / @posted_speed + 0.85 * ((volau + volad) / ( 800*lanes))^5)", sel_link="vdf=14 and mode=v")
        util.emme_segment_calc(scenario, "us2", "(length * 60 / @posted_speed + 0.85 * ((volau + volad) / (1000*lanes))^5)", sel_link="vdf=15 and mode=v")
        util.emme_segment_calc(scenario, "us2", "(length * 60 / @posted_speed + 0.85 * ((volau + volad) / (1200*lanes))^5)", sel_link="vdf=16 and mode=v")
        util.emme_segment_calc(scenario, "us2", "(length * 60 / @posted_speed + 0.85 * ((volau + volad) / (1400*lanes))^5)", sel_link="vdf=17 and mode=v")
