##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.stage1.step0.runall
##--Purpose: Full model run
##---------------------------------------------------------------------
import inro.modeller as _m
import os
import traceback as _traceback

class FullModelRun(_m.Tool()):
    global_iterations = _m.Attribute(int)
    land_use_file1 = _m.Attribute(_m.InstanceType)
    land_use_file2 = _m.Attribute(_m.InstanceType)
    max_distribution_iterations = _m.Attribute(int)
    max_assignment_iterations = _m.Attribute(int)

    tool_run_msg = _m.Attribute(unicode)

    def __init__(self):
        self.global_iterations = 6
        self.max_distribution_iterations = 60
        self.max_assignment_iterations = 100

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Full Model Run"
        pb.description = "Performs a full model run"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        pb.add_text_box(tool_attribute_name="global_iterations",
                        size="3",
                        title="Global model iterations:",
                        note="Use 6 iterations in normal operation")

        loc = os.path.dirname(_m.Modeller().emmebank.path)

        pb.add_select_file(tool_attribute_name="land_use_file1",
                           window_type="file",
                           file_filter='*.csv',
                           start_path=loc + '/00_RUNMODEL/LandUse',
                           title="LandUse file 1: ",
                           note="File must be csv file.")

        pb.add_select_file(tool_attribute_name="land_use_file2",
                           window_type="file",
                           file_filter='*.csv',
                           start_path=loc + '/00_RUNMODEL/LandUse',
                           title="LandUse file 2: ",
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
        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            self(self.global_iterations, self.land_use_file1,
                 self.land_use_file2, self.max_distribution_iterations,
                 self.max_assignment_iterations)
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, error:
            self.tool_run_msg = _m.PageBuilder.format_exception(
                error, _traceback.format_exc(error))

    @_m.logbook_trace("Full Model Run")
    def __call__(self, global_iterations, land_use_file1, land_use_file2,
                 max_distribution_iterations=60,
                 max_assignment_iterations=100):
        eb = _m.Modeller().emmebank
        
        stopping_criteria = {
            "max_iterations": max_assignment_iterations,
            "relative_gap": 0.0,
            "best_relative_gap": 0.01,
            "normalized_gap": 0.01
        }
        # only used for generating starter skims
        stopping_criteria_skim = {
            "max_iterations": 30,
            "relative_gap": 0.0,
            "best_relative_gap": 0.01,
            "normalized_gap": 0.01
        }
        
        
        settings = self.stage1(eb, land_use_file1, land_use_file2)
        
        # This section generates initial skims instead of runn
    #@_m.logbook_trace("Run Seed Assignment and Generate Initial Skims")
        # Pre_Loops is now run before the initial assignment to initialize skim matrices
        
        pre_loops = _m.Modeller().tool("translink.emme.stage2.step3.preloops")
        pre_loops(eb)
        
        assignment = _m.Modeller().tool("translink.emme.stage3.step6.assignment")
        post_assignment = _m.Modeller().tool("translink.emme.stage3.step7.postassign")
        assignment(eb, 0, stopping_criteria_skim)
        post_assignment(eb, 0, stopping_criteria_skim)        
        
    
        self.stage2(eb)

        self.stage3(eb, global_iterations, max_distribution_iterations, stopping_criteria)

        self.stage4(eb, stopping_criteria)

    @_m.logbook_trace("Stage 1 - Define Inputs and Run Intial Assignment")
    def stage1(self, eb, land_use_file1, land_use_file2):
        matrix_txn = _m.Modeller().tool("inro.emme.data.matrix.matrix_transaction")
        lu_file = os.path.join(os.path.dirname(eb.path), "00_RUNMODEL", "LandUse", "Batchins.txt")
        matrix_txn(transaction_file=lu_file, throw_on_error=True)

        util = _m.Modeller().tool("translink.emme.util")

        util.initmat(eb, "mo19", "", "", 0)
        util.initmat(eb, "mo20", "", "", 0)
        util.initmat(eb, "mo23", "", "", 0)
        util.initmat(eb, "mo24", "", "", 0)
        util.initmat(eb, "mo25", "", "", 0)
        util.initmat(eb, "mo26", "", "", 0)
        util.initmat(eb, "mo50", "", "", 0)
        util.initmat(eb, "mo51", "", "", 0)
        util.initmat(eb, "mo52", "", "", 0)
        util.initmat(eb, "mo53", "", "", 0)
        util.initmat(eb, "mo393", "", "", 0)
        util.initmat(eb, "mo394", "", "", 0)
        util.initmat(eb, "mo27", "", "", 0)
        util.initmat(eb, "mo28", "", "", 0)
        util.initmat(eb, "mo13", "", "", 0)

        ## Call Model Tools - Socioeconomic segmentation, trip generation, trip distribution, mode choice, assignment
        land_use = _m.Modeller().tool("translink.emme.stage1.step0.landuse")
        land_use(land_use_file1, land_use_file2)

        ## Read the settings file
        read_settings = _m.Modeller().tool("translink.emme.stage1.step0.settings")
        settings_file = os.path.join(os.path.dirname(eb.path), "settings.csv")
        settings = read_settings(eb, settings_file)

        create_scenario = _m.Modeller().tool("translink.emme.stage1.step0.create_scen")
        scenario_run = eb.matrix("ms143").data
        am_scen = eb.matrix("ms140").data
        md_scen = eb.matrix("ms141").data

        if scenario_run == 1:
            create_scenario(eb, am_scen, md_scen)

        # Segmentation (including auto ownership)
        segmentation = _m.Modeller().tool("translink.emme.stage1.step1.segmentation")
        segmentation(eb)

        return settings

    @_m.logbook_trace("Stage 2 - Trip Generation")
    def stage2(self, eb):
        trip_productions = _m.Modeller().tool("translink.emme.stage2.step2.tripproduction")
        trip_attraction = _m.Modeller().tool("translink.emme.stage2.step2.tripattraction")
        factor_trip_attractions = _m.Modeller().tool("translink.emme.stage2.step3.factoredtripattraction")
        

        # Trip Generation (production, attraction, factors)
        trip_productions(eb)
        trip_attraction(eb)
        factor_trip_attractions(eb)
        

    @_m.logbook_trace("Stage 3 - Model Iteration")
    def stage3(self, eb, global_iterations, max_distribution_iterations, stopping_criteria):
                # TODO: - could check and report on convergence
        #         at each iteration (distribution and auto assignment)
        #       - add global convergence measure
        trip_distribution = _m.Modeller().tool("translink.emme.stage3.step4.tripdistribution")
        mode_choice = _m.Modeller().tool("translink.emme.stage3.step5.modechoice")
        assignment = _m.Modeller().tool("translink.emme.stage3.step6.assignment")
        post_assignment = _m.Modeller().tool("translink.emme.stage3.step7.postassign")

        #Distribution, mode choice and assignment
        #Iterate distribution, mode choice and assignment steps to indicated number of iterations
        for iteration_number in range(global_iterations):
            trip_distribution(eb, max_distribution_iterations)
            mode_choice(eb, iteration_number, global_iterations)
            assignment(eb, iteration_number, stopping_criteria)
            post_assignment(eb, iteration_number, stopping_criteria)

    @_m.logbook_trace("Stage 4 - Post Processing")
    def stage4(self, eb, stopping_criteria):
        demand_adjust = _m.Modeller().tool("translink.emme.stage4.step8.demandadjustment")
        congested_transit = _m.Modeller().tool("translink.emme.stage5.step11.congested_transit")

        am_scen = eb.matrix("ms140").data
        md_scen = eb.matrix("ms141").data
        demand_adjust(eb, am_scen, md_scen, stopping_criteria)

        run_congested = int(eb.matrix("ms138").data)
        if run_congested == 1:
            am_scenario = eb.scenario(am_scen)
            copy_scenario = _m.Modeller().tool("inro.emme.data.scenario.copy_scenario")
            congested_transit_am = copy_scenario(
                from_scenario=am_scenario,
                scenario_id=am_scenario.number + 70,
                scenario_title=am_scenario.title + ": cong transit "[:40],
                overwrite=True)
            congested_transit(congested_transit_am, setup_ttfs=True)
