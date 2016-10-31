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
    max_assignment_iterations = _m.Attribute(int)
    num_processors = _m.Attribute(int)

    tool_run_msg = _m.Attribute(unicode)

    def __init__(self):
        self.horizon_year = 2011
        self.global_iterations = 6
        self.max_distribution_iterations = 60
        self.max_assignment_iterations = 200
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
                        size="3",
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

        pb.add_text_box(tool_attribute_name="max_assignment_iterations",
                        size="4",
                        title="Maximum iterations for the auto assignment sub-model:",
                        note="The auto assignment should reach a "
                             "convergence level of at least 10^-3 best relative gap "
                             "or 10^-5 relative gap in the final global "
                             "iteration in order for the model to be "
                             "considered converged.  If this is not "
                             "the case run again with more iterations.")

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
                 self.max_assignment_iterations, self.num_processors)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Full Model Run")
    def __call__(self, horizon_year, global_iterations, master_scen, demographics_file,
                    geographics_file, max_distribution_iterations,
                    max_assignment_iterations, num_processors):
        eb = master_scen.emmebank
        util = _m.Modeller().tool("translink.emme.util")
        self.initoptions(eb=eb, horizon_year=horizon_year, global_iterations=global_iterations,
                        max_distribution_iterations=max_distribution_iterations,
                        max_assignment_iterations=max_assignment_iterations, num_processors=num_processors)

        self.stage0(eb, demographics_file, geographics_file)

    def stage0(self, eb, demographics_file, geographics_file):
        util = _m.Modeller().tool("translink.emme.util")
        data_import = _m.Modeller().tool("translink.emme.stage0.data_import")


        data_import(eb, demographics_file, geographics_file)




    def initoptions(self, eb, horizon_year, global_iterations,
                    max_distribution_iterations, max_assignment_iterations, num_processors):

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
        # auto assignment
        util.initmat(eb, "ms40", "IterAss", "Assignment Iterations", max_assignment_iterations)
        util.initmat(eb, "ms41", "ConRelGap", "ConvergenceRelativeGap", 0.0001)
        util.initmat(eb, "ms42", "ConBestRel", "ConvergenceBestRelative", 0.01)
        util.initmat(eb, "ms43", "ConNorm", "ConvergaenceNormalized", 0.005)