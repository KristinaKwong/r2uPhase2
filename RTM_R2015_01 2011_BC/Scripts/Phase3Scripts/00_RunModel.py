##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: ?
##--Purpose: Full model run
##---------------------------------------------------------------------
import inro.modeller as _m
import os
import multiprocessing
import traceback as _traceback


class FullModelRun(_m.Tool()):
    horizon_year = _m.Attribute(int)
    global_iterations = _m.Attribute(int)
    master_scen = _m.Attribute(_m.InstanceType)
    demographics_file = _m.Attribute(_m.InstanceType)
    geographics_file = _m.Attribute(_m.InstanceType)
    max_distribution_iterations = _m.Attribute(int)
    distribution_relative_err = _m.Attribute(float)
    max_assignment_iterations = _m.Attribute(int)
    run_congested_transit = _m.Attribute(bool)
    run_capacited_transit = _m.Attribute(bool)
    num_processors = _m.Attribute(int)

    tool_run_msg = _m.Attribute(unicode)

    def __init__(self):
        self.horizon_year = 2011
        self.global_iterations = 6
        self.max_distribution_iterations = 60
        self.distribution_relative_err = 0.0001
        self.max_assignment_iterations = 200
        self.run_congested_transit = False
        self.run_capacited_transit = False
        self.num_processors = multiprocessing.cpu_count()

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Full Model Run"
        pb.description = "Performs a full model run"
        pb.branding_text = "TransLink"

        util = _m.Modeller().tool("translink.emme.util")
        input_path = util.get_input_path(_m.Modeller().emmebank)
        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        pb.add_text_box(tool_attribute_name="horizon_year",
                        size="4",
                        title="Model horizion year:",
                        note="Should match network scenario")

        pb.add_select_scenario(tool_attribute_name="master_scen",
                        title="Scenario containing network information:",
                        note="This scenario will be copied into individual time of day scenarios.")

        pb.add_text_box(tool_attribute_name="global_iterations",
                        size="3",
                        title="Global model iterations:",
                        note="Use 6 iterations in normal operation")

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

        pb.add_text_box(tool_attribute_name="max_distribution_iterations",
                        size="4",
                        title="Maximum iterations for the trip distribution sub-model:",
                        note="The matrix balancing procedure should reach a "
                             "convergence level of at least 10^-4 relative error "
                             "in the final global iteration in order for the "
                             "model to be considered converged. If this is not "
                             "the case run again with more iterations.")

        pb.add_text_box(tool_attribute_name="distribution_relative_err",
                        size="6",
                        title="Maximum relative error for the trip distribution sub-model:")

        pb.add_text_box(tool_attribute_name="max_assignment_iterations",
                        size="4",
                        title="Maximum iterations for the auto assignment sub-model:",
                        note="The auto assignment should reach a "
                             "convergence level of at least 10^-3 best relative gap "
                             "or 10^-5 relative gap in the final global "
                             "iteration in order for the model to be "
                             "considered converged.  If this is not "
                             "the case run again with more iterations.")

        with pb.section("Transit Assignment Options"):
            pb.add_checkbox("run_congested_transit", label="Run Congested Transit Assignment")
            pb.add_checkbox("run_capacited_transit", label="Run Capacited Transit Assignment")

        pb.add_text_box(tool_attribute_name="num_processors",
                        size="3",
                        title="Number of processors on machine running model:",
                        note="Should be less than or equal to processors on machine")

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            self.__call__(self.horizon_year, self.global_iterations, self.master_scen, self.demographics_file,
                 self.geographics_file, self.max_distribution_iterations,
                 self.max_assignment_iterations, self.run_congested_transit, self.run_capacited_transit,
                 self.num_processors)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Full Model Run")
    def __call__(self, horizon_year, global_iterations, master_scen, demographics_file,
                    geographics_file, max_distribution_iterations,
                    max_assignment_iterations, run_congested_transit, run_capacited_transit, num_processors):
        eb = master_scen.emmebank
        util = _m.Modeller().tool("translink.emme.util")
        self.initoptions(eb=eb, horizon_year=horizon_year, global_iterations=global_iterations,
                        max_distribution_iterations=max_distribution_iterations,
                        max_assignment_iterations=max_assignment_iterations,
                        run_congested_transit=run_congested_transit, run_capacited_transit=run_capacited_transit,
                        num_processors=num_processors)

        self.stage0(eb, master_scen=master_scen, demographics_file=demographics_file, geographics_file=geographics_file)
        self.stage1(eb)

        for cycle in range(0, int(eb.matrix("msIterGlobal").data)):
            util.initmat(eb, "ms1", "CycleNum", "Current Cycle Number", cycle + 1)
            self.stage2(eb)
            self.stage3(eb)

    def stage0(self, eb, master_scen, demographics_file, geographics_file):
        util = _m.Modeller().tool("translink.emme.util")
        create_scenario = _m.Modeller().tool("translink.RTM3.stage0.create_scenarios")
        data_import = _m.Modeller().tool("translink.RTM3.stage0.data_import")
        data_generate = _m.Modeller().tool("translink.RTM3.stage0.data_generate")

        create_scenario(base_scenario=master_scen)
        data_import(eb, demographics_file=demographics_file, geographics_file=geographics_file)
        data_generate(eb)

    def stage1(self, eb):
        util = _m.Modeller().tool("translink.emme.util")
        workers_and_income = _m.Modeller().tool("translink.RTM3.stage1.workinc")
        vehicle_availability = _m.Modeller().tool("translink.RTM3.stage1.vam")
        trip_productions = _m.Modeller().tool("translink.RTM3.stage1.prds")
        trip_attractions = _m.Modeller().tool("translink.RTM3.stage1.atrs")

        workers_and_income(eb)
        vehicle_availability(eb)
        trip_productions(eb)
        trip_attractions(eb)

    def stage2(self, eb):
        util = _m.Modeller().tool("translink.emme.util")
        blended_skims = _m.Modeller().tool("translink.RTM3.stage2.blendedskims")
        td_mode_choice_hbw = _m.Modeller().tool("translink.RTM3.stage2.hbwork")
        td_mode_choice_hbu = _m.Modeller().tool("translink.RTM3.stage2.hbuniv")
        td_mode_choice_hbsc = _m.Modeller().tool("translink.RTM3.stage2.hbschool")
        td_mode_choice_hbsh = _m.Modeller().tool("translink.RTM3.stage2.hbshop")
        td_mode_choice_hbpb = _m.Modeller().tool("translink.RTM3.stage2.hbperbus")
        td_mode_choice_hbso = _m.Modeller().tool("translink.RTM3.stage2.hbsocial")
        td_mode_choice_hbes = _m.Modeller().tool("translink.RTM3.stage2.hbescorting")
        td_mode_choice_nhbw = _m.Modeller().tool("translink.RTM3.stage2.nhbwork")
        td_mode_choice_nhbo = _m.Modeller().tool("translink.RTM3.stage2.nhbother")

        blended_skims(eb)
        td_mode_choice_hbw(eb)
        td_mode_choice_hbu(eb)
        td_mode_choice_hbsc(eb)
        td_mode_choice_hbsh(eb)
        td_mode_choice_hbpb(eb)
        td_mode_choice_hbso(eb)
        td_mode_choice_hbes(eb)
        td_mode_choice_nhbw(eb)
        td_mode_choice_nhbo(eb)


    def stage3(self, eb):
        am_scen = eb.scenario(int(eb.matrix("ms2").data))
        md_scen = eb.scenario(int(eb.matrix("ms3").data))
        pm_scen = eb.scenario(int(eb.matrix("ms4").data))

        auto_assign = _m.Modeller().tool("translink.RTM3.stage3.autoassignment")
        auto_assign(am_scen, md_scen, pm_scen)

        transit_assign = _m.Modeller().tool("translink.RTM3.stage3.transitassignment")
        transit_assign(eb, am_scen, md_scen, pm_scen)


    def initoptions(self, eb, horizon_year, global_iterations,
                    max_distribution_iterations, max_assignment_iterations,
                    run_congested_transit, run_capacited_transit,
                    num_processors):

        util = _m.Modeller().tool("translink.emme.util")
        # model business
        util.initmat(eb, "ms1", "CycleNum", "Current Cycle Number", 0)
        util.initmat(eb, "ms2", "AmScen", "AMScenario", 21000)
        util.initmat(eb, "ms3", "MdScen", "MDScenario", 22000)
        util.initmat(eb, "ms4", "PmScen", "PMScenario", 23000)
        util.initmat(eb, "ms5", "AmScen_p", "AMScenario_Previous", 21030)
        util.initmat(eb, "ms6", "MdScen_p", "MDScenario_Previous", 22030)
        util.initmat(eb, "ms7", "PmScen_p", "PMScenario_Previous", 23030)
        util.initmat(eb, "ms10", "Year", "Horizon Year of Run", horizon_year)
        util.initmat(eb, "ms12", "Processors", "Number of Processors for Computer Running Model", num_processors)
        # overall model
        util.initmat(eb, "ms30", "IterGlobal", "Global Iterations", global_iterations)
        # distribution
        util.initmat(eb, "ms35", "IterDist", "DistributionIterations", max_distribution_iterations)
        util.initmat(eb, "ms36", "RelErrDist", "Distribution Relative Error", self.distribution_relative_err)
        # auto assignment
        util.initmat(eb, "ms40", "IterAss", "Assignment Iterations", max_assignment_iterations)
        util.initmat(eb, "ms41", "ConRelGap", "ConvergenceRelativeGap", 0.0001)
        util.initmat(eb, "ms42", "ConBestRel", "ConvergenceBestRelative", 0.01)
        util.initmat(eb, "ms43", "ConNorm", "ConvergenceNormalized", 0.005)
        util.initmat(eb, "ms44", "AutoOcc", "Standard HOV Occupancy", 2.4)
        util.initmat(eb, "ms45", "tranCongest", "Run Congested Transit Assignment", int(run_congested_transit))
        util.initmat(eb, "ms46", "tranCapac", "Run Capacitated Transit Assignment", int(run_capacited_transit))
