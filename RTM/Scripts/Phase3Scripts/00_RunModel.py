##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.runmodel
##--Purpose: Full model run
##---------------------------------------------------------------------
import inro.modeller as _m
import multiprocessing
import traceback as _traceback
import pandas as pd

class FullModelRun(_m.Tool()):
    scenario_name = _m.Attribute(_m.InstanceType)
    alternative_name = _m.Attribute(_m.InstanceType)
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
    run_parking_model = _m.Attribute(bool)
    run_toll_skim = _m.Attribute(bool)

    tool_run_msg = _m.Attribute(unicode)

    def __init__(self):
        self.horizon_year = 2011
        self.scenario_name = 'Scenario Name'
        self.alternative_name = 'Alternative Name'
        self.global_iterations = 4
        self.max_distribution_iterations = 60
        self.distribution_relative_err = 0.0001
        self.max_assignment_iterations = 200
        self.run_congested_transit = True
        self.run_capacited_transit = True
        self.num_processors = multiprocessing.cpu_count()
        self.run_parking_model = True
        self.run_toll_skim = False

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Full Model Run"
        pb.description = "Performs a full model run"
        pb.branding_text = "TransLink"

        util = _m.Modeller().tool("translink.util")
        input_path = util.get_input_path(_m.Modeller().emmebank)
        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        pb.add_text_box(tool_attribute_name="scenario_name",
                        size=30,
                        title="Enter the scenario name for the new emmebank.  e.g. Business as Usual")

        pb.add_text_box(tool_attribute_name="alternative_name",
                        size=30,
                        title="Enter the alternative name for the new emmebank.  e.g. Mayor's Plan")

        pb.add_text_box(tool_attribute_name="horizon_year",
                        size="4",
                        title="Model horizon year:",
                        note="Should match current landuse years: 2011, 2030 and 2045")

        pb.add_select_scenario(tool_attribute_name="master_scen",
                        title="Scenario containing network information:",
                        note="This scenario will be copied into individual time of day scenarios.")

        pb.add_text_box(tool_attribute_name="global_iterations",
                        size="3",
                        title="Global model iterations:",
                        note="Use 4 iterations in normal operation")

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

        with pb.section("Data Generation Options"):
            pb.add_checkbox("run_parking_model", label="Run Parking Model",
                                                 note="Parking model should be run "
                                                 "unless parking scenarios are being tested "
                                                 "that are coded in geographics file")

        pb.add_checkbox("run_toll_skim", label="Run toll assignment on final iteration")

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
                 self.num_processors, self.run_parking_model, self.run_toll_skim, self.scenario_name, self.alternative_name)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Full Model Run")
    def __call__(self, horizon_year, global_iterations, master_scen, demographics_file,
                    geographics_file, max_distribution_iterations,
                    max_assignment_iterations, run_congested_transit,
                    run_capacited_transit, num_processors, run_parking_model, run_toll_skim, scenario_name, alternative_name):
        eb = master_scen.emmebank
        util = _m.Modeller().tool("translink.util")

        # add meta data to output datbases
        md = {'scenario' : scenario_name,
              'alternative' : alternative_name,
              'horizon_year' : horizon_year}
        md = pd.DataFrame(md, index=[0])
        conn = util.get_rtm_db(eb)
        md.to_sql(name='metadata', con=conn, flavor='sqlite', index=False, if_exists='replace')
        conn.close()
        conn = util.get_db_byname(eb, 'trip_summaries.db')
        md.to_sql(name='metadata', con=conn, flavor='sqlite', index=False, if_exists='replace')
        conn.close()

        self.initoptions(eb=eb, horizon_year=horizon_year, global_iterations=global_iterations,
                        max_distribution_iterations=max_distribution_iterations,
                        max_assignment_iterations=max_assignment_iterations,
                        run_congested_transit=run_congested_transit, run_capacited_transit=run_capacited_transit,
                        num_processors=num_processors, run_parking_model=run_parking_model, run_toll_skim=run_toll_skim)

        self.stage0(eb, master_scen=master_scen, demographics_file=demographics_file, geographics_file=geographics_file)

        for cycle in range(1, int(eb.matrix("msIterGlobal").data) + 1):
            util.initmat(eb, "ms1", "CycleNum", "Current Cycle Number", cycle)
            with _m.logbook_trace("Run Cycle %d" % cycle):
                self.stage1(eb)
                self.run_one_cycle(eb, horizon_year)

        data_export = _m.Modeller().tool("translink.RTM3.stage4.dataexport")
        data_export(eb)

    def stage0(self, eb, master_scen, demographics_file, geographics_file):
        util = _m.Modeller().tool("translink.util")
        create_scenario = _m.Modeller().tool("translink.RTM3.stage0.create_scenarios")
        data_import = _m.Modeller().tool("translink.RTM3.stage0.data_import")

        create_scenario(base_scenario=master_scen)
        data_import(eb, demographics_file=demographics_file, geographics_file=geographics_file)


    def stage1(self, eb):
        util = _m.Modeller().tool("translink.util")
        data_generate = _m.Modeller().tool("translink.RTM3.stage0.data_generate")
        workers_and_income = _m.Modeller().tool("translink.RTM3.stage1.workinc")
        vehicle_availability = _m.Modeller().tool("translink.RTM3.stage1.vam")
        trip_productions = _m.Modeller().tool("translink.RTM3.stage1.prds")
        trip_attractions = _m.Modeller().tool("translink.RTM3.stage1.atrs")

        data_generate(eb)
        workers_and_income(eb)
        vehicle_availability(eb)
        trip_productions(eb)
        trip_attractions(eb)

    def run_one_cycle(self, eb, horizon_year):
        util = _m.Modeller().tool("translink.util")

        blended_skims = _m.Modeller().tool("translink.RTM3.stage2.blendedskims")
        blended_skims(eb)

        mode_choice = _m.Modeller().tool("translink.RTM3.stage2.modechoice")
        mode_choice(eb)

        truck_model = _m.Modeller().tool("translink.RTM3.stage2.truckmodel")
        truck_model(eb, horizon_year)

        am_scen = eb.scenario(int(eb.matrix("ms2").data))
        md_scen = eb.scenario(int(eb.matrix("ms3").data))
        pm_scen = eb.scenario(int(eb.matrix("ms4").data))

        auto_assign = _m.Modeller().tool("translink.RTM3.stage3.autoassignment")
        auto_assign(am_scen, md_scen, pm_scen)

        transit_assign = _m.Modeller().tool("translink.RTM3.stage3.transitassignment")
        transit_assign(eb, am_scen, md_scen, pm_scen)

        if False:
            copy_scenario = _m.Modeller().tool("inro.emme.data.scenario.copy_scenario")
            cyclenum = int(eb.matrix("ms1").data)

            copy_scenario(from_scenario=am_scen,
                          scenario_id=am_scen.number + cyclenum,
                          scenario_title=am_scen.title + " " + str(cyclenum),
                          overwrite=True)

            copy_scenario(from_scenario=md_scen,
                          scenario_id=md_scen.number + cyclenum,
                          scenario_title=md_scen.title + " " + str(cyclenum),
                          overwrite=True)

            copy_scenario(from_scenario=pm_scen,
                          scenario_id=pm_scen.number + cyclenum,
                          scenario_title=pm_scen.title + " " + str(cyclenum),
                          overwrite=True)


    def initoptions(self, eb, horizon_year, global_iterations,
                    max_distribution_iterations, max_assignment_iterations,
                    run_congested_transit, run_capacited_transit,
                    num_processors, run_parking_model, run_toll_skim):

        util = _m.Modeller().tool("translink.util")
        # model business
        util.initmat(eb, "ms1", "CycleNum", "Current Cycle Number", 0)
        util.initmat(eb, "ms2", "AmScen", "AMScenario", 21000)
        util.initmat(eb, "ms3", "MdScen", "MDScenario", 22000)
        util.initmat(eb, "ms4", "PmScen", "PMScenario", 23000)
        util.initmat(eb, "ms10", "Year", "Horizon Year of Run", horizon_year)
        util.initmat(eb, "ms12", "Processors", "Number of Processors for Computer Running Model", num_processors)
        # data generation
        util.initmat(eb, "ms20", "parkingModel", "Run Parking Model", run_parking_model)
        util.initmat(eb, "ms21", "tollSkim", "Run Toll Skim", run_toll_skim)
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
        util.initmat(eb, "ms44", "AutoOcc", "Standard HOV Occupancy", 2.25)
        util.initmat(eb, "ms45", "tranCongest", "Run Congested Transit Assignment", int(run_congested_transit))
        util.initmat(eb, "ms46", "tranCapac", "Run Capacitated Transit Assignment", int(run_capacited_transit))
