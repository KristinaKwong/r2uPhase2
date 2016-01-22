##--------------------------------------------------
##--TransLink Phase 2 Regional Transportation Model
##--00_00_RUN_ALL.PY
##--Path: translink.emme.runall
##--Purpose of 00_00_RUN_ALL:
##--------------------------------------------------
##--Last modified 2015-01-19 Kevin Bragg (INRO)
##--Reason: Add reference for congested transit assignment
##--Last modified 2014-04-17 Kevin Bragg (INRO)
##          Added stopping_criteria input to all
##          traffic assignments
##          (instead of max_iterations).
##--Last modified 2014-04-07 Kevin Bragg (INRO)
##--Reason: Add parameters for max iterations of
##          distribution and assignment steps
##--Last modified 2014-02-14 Kevin Bragg (INRO)
##--Reason: Update to Emme 4.0 namespaces
##          Code cleanup PEP 8 compliance
##--Last modified 2013-11-05 Rhys Wolff (HDR)
##--Last modification reason - add create scenario check and settings input
##---------------------------------------------------
##--Called by: user
##--Calls:     all model components
##--Accesses:  user-specified
##--Outputs:
##---------------------------------------------------
##--Status/additional notes:
##--Supersedes all earlier versions of 00_00_RUN_ALL.PY
##---------------------------------------------------


import inro.modeller as _modeller
import os
import traceback as _traceback


class FullModelRun(_modeller.Tool()):
    global_iterations = _modeller.Attribute(int)
    land_use_file1 = _modeller.Attribute(_modeller.InstanceType)
    land_use_file2 = _modeller.Attribute(_modeller.InstanceType)
    max_distribution_iterations = _modeller.Attribute(int)
    max_assignment_iterations = _modeller.Attribute(int)

    tool_run_msg = _modeller.Attribute(unicode)

    def __init__(self):
        self.global_iterations = 6
        self.max_distribution_iterations = 60
        self.max_assignment_iterations = 100

    def page(self):
        loc = os.path.dirname(_modeller.Modeller().emmebank.path)
        pb = _modeller.ToolPageBuilder(self)
        pb.title = "Full Model Run"
        pb.description = "Performs a full model run"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        pb.add_text_box(tool_attribute_name="global_iterations",
                        size="3",
                        title="Global model iterations:",
                        note="Use 6 iterations in normal operation")

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
            self.tool_run_msg = _modeller.PageBuilder.format_info(run_msg)
        except Exception, error:
            self.tool_run_msg = _modeller.PageBuilder.format_exception(
                error, _traceback.format_exc(error))

    @_modeller.logbook_trace("Full Model Run")
    def __call__(self, global_iterations, land_use_file1, land_use_file2,
                 max_distribution_iterations=60,
                 max_assignment_iterations=100):
        # TODO: - could check and report on convergence
        #         at each iteration (distribution and auto assignment)
        #       - add global convergence measure
        matrix_txn = _modeller.Modeller().tool(
            "inro.emme.data.matrix.matrix_transaction")
        copy_scenario = _modeller.Modeller().tool(
            "inro.emme.data.scenario.copy_scenario")

        land_use = _modeller.Modeller().tool("translink.emme.stage1.step0.landuse")
        create_scenario = _modeller.Modeller().tool("translink.emme.stage1.step0.create_scen")
        read_settings = _modeller.Modeller().tool("translink.emme.stage1.step0.settings")

        segmentation = _modeller.Modeller().tool("translink.emme.stage1.step1.segmentation")
        trip_productions = _modeller.Modeller().tool("translink.emme.stage2.step2.tripproduction")
        trip_attraction = _modeller.Modeller().tool("translink.emme.stage2.step2.tripattraction")
        factor_trip_attractions = _modeller.Modeller().tool("translink.emme.stage2.step3.factoredtripattraction")
        pre_loops = _modeller.Modeller().tool("translink.emme.stage2.step3.preloops")
        trip_distribution = _modeller.Modeller().tool("translink.emme.stage3.step4.tripdistribution")
        mode_choice = _modeller.Modeller().tool("translink.emme.stage3.step5.modechoice")
        assignment = _modeller.Modeller().tool("translink.emme.stage3.step6.assignment")
        post_assignment = _modeller.Modeller().tool("translink.emme.stage3.step7.postassign")
        demand_adjust = _modeller.Modeller().tool("translink.emme.stage4.step8.demandadjustment")
        congested_transit = _modeller.Modeller().tool("translink.emme.stage5.step11.congested_transit")

        emmebank = _modeller.Modeller().emmebank
        root_directory = os.path.dirname(emmebank.path) + "\\"

        ## Batchin Starter Accessibilities and initialize matrices for landuse inputs and mode settings
        matrix_file = os.path.join(root_directory, "00_RUNMODEL", "LandUse", "Batchins.txt")
        matrix_txn(transaction_file=matrix_file, throw_on_error=True)

        ## Call Model Tools - Socioeconomic segmentation, trip generation, trip distribution, mode choice, assignment
        land_use(land_use_file1, land_use_file2)

        # Settings file
        settings_file = os.path.join(root_directory, "settings.csv")
        settings = read_settings(settings_file)

        #Create scenarios, depending on settings selection
        ##      Return_val = _modeller.Modeller().tool("translink.emme.scalar")

        eb = _modeller.Modeller().emmebank
        scenrun = eb.matrix("ms143")
        amscen = eb.matrix("ms140")
        mdscen = eb.matrix("ms141")

        scenario_run = scenrun.data
        am_scen = amscen.data
        md_scen = mdscen.data

        if scenario_run == 1:
            create_scenario(am_scen, md_scen)

        # Segmentation (including auto ownership)
        segmentation(root_directory)

        # Trip Generation (production, attraction, factors)
        trip_productions(root_directory)
        trip_attraction(root_directory)
        factor_trip_attractions(root_directory)
        pre_loops(emmebank)

        stopping_criteria = {
            "max_iterations": max_assignment_iterations,
            "relative_gap": 0.0,
            "best_relative_gap": 0.01,
            "normalized_gap": 0.01
        }
        run_park_ride = settings.get("park_and_ride")

        #Distribution, mode choice and assignment
        #Iterate distribution, mode choice and assignment steps to indicated number of iterations
        for iteration_number in range(global_iterations):
            trip_distribution(root_directory, max_distribution_iterations)
            mode_choice(root_directory, iteration_number, global_iterations, run_park_ride)
            assignment(root_directory, iteration_number, stopping_criteria)
            post_assignment(root_directory, iteration_number, stopping_criteria)

        demand_adjust(root_directory, am_scen, md_scen, stopping_criteria)

        if settings.get("congested_transit") == 1:
            am_scenario = emmebank.scenario(am_scen)
            congested_transit_am = copy_scenario(
                from_scenario=am_scenario,
                scenario_id=am_scenario.number + 70,
                scenario_title=am_scenario.title + ": cong transit "[:40],
                overwrite=True)
            congested_transit(congested_transit_am, setup_ttfs=True)
