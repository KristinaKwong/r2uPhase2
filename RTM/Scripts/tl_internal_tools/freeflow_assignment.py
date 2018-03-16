##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.internal_tools.losDass
##--Purpose: Run an LOS D Assignment for AM, MD and PM
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback

class AutoAssignment(_m.Tool()):
    am_scenario = _m.Attribute(_m.InstanceType)
    md_scenario = _m.Attribute(_m.InstanceType)
    pm_scenario = _m.Attribute(_m.InstanceType)
    assignment_type = _m.Attribute(int)

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
        self.assignment_type = 1

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Auto Assignment"
        pb.description = "Performs an LOS D Assignment " +\
                         "with 4 classes, SOV, HOV , Light Trucks " +\
                         "and Heavy Trucks. Creates new copies of input scenarios"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        pb.add_select(tool_attribute_name="assignment_type",keyvalues=[[1,"Regular"],[2,"Social_Optimal"]])
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

            self(eb, self.am_scenario, self.md_scenario, self.pm_scenario, self.assignment_type)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Auto Traffic Assignment")
    def __call__(self, eb, am_scenario, md_scenario, pm_scenario,assignment_type):

        util = _m.Modeller().tool("translink.util")

        # make sure we don't overwrite existing scenarios
        am_scenario, md_scenario, pm_scenario = self.losdscenarios(eb, am_scenario, md_scenario, pm_scenario)

        # Initialize LOSD Skims by time period
        util.initmat(eb, "mf9350", "AmSovTimeFreeflow", "SOV Minutes Freeflow AM", 0)
        util.initmat(eb, "mf9360", "MdSovTimeFreeflow", "SOV Minutes Freeflow MD", 0)
        util.initmat(eb, "mf9370", "PmSovTimeFreeflow", "SOV Minutes Freeflow PM", 0)
        util.initmat(eb, "mf9355", "AmHovTimeFreeflow", "HOV Minutes Freeflow AM", 0)
        util.initmat(eb, "mf9365", "MdHovTimeFreeflow", "HOV Minutes Freeflow MD", 0)
        util.initmat(eb, "mf9375", "PmHovTimeFreeflow", "HOV Minutes Freeflow PM", 0)
        util.initmat(eb, "mf9380", "AmLgvTimeFreeflow", "LGV Minutes Freeflow AM", 0)
        util.initmat(eb, "mf9381", "MdLgvTimeFreeflow", "LGV Minutes Freeflow MD", 0)
        util.initmat(eb, "mf9382", "PmLgvTimeFreeflow", "LGV Minutes Freeflow PM", 0)
        util.initmat(eb, "mf9390", "AmHgvTimeFreeflow", "HGV Minutes Freeflow AM", 0)
        util.initmat(eb, "mf9391", "MdHgvTimeFreeflow", "HGV Minutes Freeflow MD", 0)
        util.initmat(eb, "mf9392", "PmHgvTimeFreeflow", "HGV Minutes Freeflow PM", 0)

        # AM

        self.assign_scen(am_scenario, assignment_type)
        self.calc_intrazonal_skims(eb)

        am_skims = {"sov":  ["mfAmSovTimeFreeflow"],
                    "hov":  ["mfAmHovTimeFreeflow"],
                    "lgv":  ["mfAmLgvTimeFreeflow"],
                    "hgv":  ["mfAmHgvTimeFreeflow"]}

        self.store_skims(am_scenario, am_skims)

        # MD

        self.assign_scen(md_scenario, assignment_type)
        self.calc_intrazonal_skims(eb)
        md_skims = {"sov":  ["mfMdSovTimeFreeflow"],
                    "hov":  ["mfMdHovTimeFreeflow"],
                    "lgv":  ["mfMdLgvTimeFreeflow"],
                    "hgv":  ["mfMdHgvTimeFreeflow"]}

        self.store_skims(md_scenario, md_skims)

        # PM

        self.assign_scen(pm_scenario, assignment_type)
        self.calc_intrazonal_skims(eb)
        pm_skims = {"sov":  ["mfPmSovTimeFreeflow"],
                    "hov":  ["mfPmHovTimeFreeflow"],
                    "lgv":  ["mfPmLgvTimeFreeflow"],
                    "hgv":  ["mfPmHgvTimeFreeflow"]}

        self.store_skims(pm_scenario, pm_skims)

    def assign_scen(self, scenario, assignment_type):
        assign_traffic = _m.Modeller().tool("inro.emme.traffic_assignment.sola_traffic_assignment")
        util = _m.Modeller().tool("translink.util")
        eb = _m.Modeller().emmebank

        self.init_matrices(scenario.emmebank)

        # undertake a dummy assignment with only background traffic at 85% of the volume (LOS D)
        # Calculate volume = 85% of capacity on the network and store it in ul3

        if assignment_type == 1:
            util.emme_link_calc(scenario, "ul3", "0")

        if assignment_type == 2:
            util.emme_link_calc(scenario, "ul3", "0")


        # get truck perception_factor

        hgv_perception = eb.matrix("msVotHgv").data

        # calculate @tkpen
        util.emme_link_calc(scenario, "@tkpen", "0")
        util.emme_link_calc(scenario, "@tkpen", "length * 100", sel_link="mode=n")


        # stopping criteria

        max_iter = int(eb.matrix("ms40").data)
        rel_gap = eb.matrix("ms41").data
        best_rel_gap = eb.matrix("ms42").data
        norm_gap = eb.matrix("ms43").data

        # Assign temporary scenario

        losd_spec = {
                            "type": "SOLA_TRAFFIC_ASSIGNMENT",
                            "classes": [
                                {
                                    "mode": "c",
                                    "demand": "msZero",
                                    "generalized_cost": None,
                                    "results": {
                                        "link_volumes": None,
                                        "turn_volumes": None,
                                        "od_travel_times": {
                                        "shortest_paths": "mfHovTimeFreeflow"
                                        }
                                    },
                                    "path_analyses": None
                                },
                                {
                                    "mode": "d",
                                    "demand": "msZero",
                                    "generalized_cost": None,
                                    "results": {
                                        "link_volumes": None,
                                        "turn_volumes": None,
                                        "od_travel_times": {
                                            "shortest_paths": "mfSovTimeFreeflow"
                                        }
                                    },
                                    "path_analyses": None
                                },
                                {
                                    "mode": "x",
                                    "demand": "msZero",
                                    "generalized_cost": None,
                                    "results": {
                                        "link_volumes": None,
                                        "turn_volumes": None,
                                        "od_travel_times": {
                                            "shortest_paths": "mfLgvTimeFreeflow"
                                        }
                                    },
                                    "path_analyses": None
                                },
                                {
                                    "mode": "t",
                                    "demand": "msZero",
                                    "generalized_cost": {
                                        "link_costs": "@tkpen",
                                        "perception_factor": hgv_perception
                                    },
                                    "results": {
                                        "link_volumes": None,
                                        "turn_volumes": None,
                                        "od_travel_times": {
                                            "shortest_paths": "mfHgvTimeFreeflow"
                                        }
                                    },
                                    "path_analyses": [
                                                    {
                                                        "link_component": "@tkpen",
                                                        "turn_component": None,
                                                        "operator": "+",
                                                        "selection_threshold": {
                                                            "lower": 0,
                                                            "upper": 999999
                                                        },
                                                        "path_to_od_composition": {
                                                            "considered_paths": "ALL",
                                                            "multiply_path_proportions_by": {
                                                                "analyzed_demand": False,
                                                                "path_value": True
                                                            }
                                                        },
                                                        "analyzed_demand": None,
                                                        "results": {
                                                            "selected_link_volumes": None,
                                                            "selected_turn_volumes": None,
                                                            "od_values": "mfHgvPenyFreeflow"
                                                        }
                                                    }
                                                ]
                                }
                            ],
                            "performance_settings": {
                                "number_of_processors": "max"
                            },
                            "background_traffic": {
                                "link_component": "ul3",
                                "turn_component": None,
                                "add_transit_vehicles": False
                            },
                            "stopping_criteria": {
                                "max_iterations": max_iter,
                                "relative_gap": rel_gap,
                                "best_relative_gap": best_rel_gap,
                                "normalized_gap": norm_gap
                            }
                        }

        assign_traffic = _m.Modeller().tool("inro.emme.traffic_assignment.sola_traffic_assignment")
        assign_traffic(losd_spec, scenario=scenario)

        # correct heavy truck travel time matrix
        specs = []

        specs.append(util.matrix_spec("mfHgvTimeFreeflow", "mfHgvTimeFreeflow - mfHgvPenyFreeflow*msVotHgv"))
        util.compute_matrix(specs, scenario)

    @_m.logbook_trace("Execute Intrazonal Calculation")

    def calc_intrazonal_skims(self, eb):

        # Calculate Intrazonal Analysis 1
        self.calc_intrazonal_skim(eb, "mfSovTimeFreeflow")
        self.calc_intrazonal_skim(eb, "mfHovTimeFreeflow")
        self.calc_intrazonal_skim(eb, "mfLgvTimeFreeflow")
        self.calc_intrazonal_skim(eb, "mfHgvTimeFreeflow")

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
        specs = []

        # Analysis 1

        specs.append(util.matrix_spec(skim_list["sov"][0], "mfSovTimeFreeflow"))
        specs.append(util.matrix_spec(skim_list["hov"][0], "mfHovTimeFreeflow"))
        specs.append(util.matrix_spec(skim_list["lgv"][0], "mfLgvTimeFreeflow"))
        specs.append(util.matrix_spec(skim_list["hgv"][0], "mfHgvTimeFreeflow"))

        util.compute_matrix(specs, scenario)

        # now that the skims have been written back, delete the temporary matrices
        for matrix in self.get_temp_matrices():
            util.delmat(scenario.emmebank, matrix[0])


    def init_matrices(self, eb):
        util = _m.Modeller().tool("translink.util")

        for matrix in self.get_temp_matrices():
            util.initmat(eb, matrix[0], matrix[1], matrix[2], matrix[3])

    def get_temp_matrices(self):
        matrices = []

        matrices.append(["mf9300", "SovTimeFreeflow",  "SOV Minutes Freeflow", 0])
        matrices.append(["mf9305", "HovTimeFreeflow",  "HOV Minutes Freeflow", 0])
        matrices.append(["mf9330", "LgvTimeFreeflow",  "LGV Minutes Freeflow", 0])
        matrices.append(["mf9340", "HgvTimeFreeflow",  "HGV Minutes Freeflow", 0])
        matrices.append(["mf9341", "HgvPenyFreeflow",  "HGV TrkPeny Freeflow", 0])

        return matrices


    def losdscenarios(self, eb, am_scenario, md_scenario, pm_scenario):
        copy_scenario = _m.Modeller().tool("inro.emme.data.scenario.copy_scenario")
        # create_scenarios = _m.Modeller().tool("translink.RTM3.stage0.create_scenarios")

         # Copy to new AM Scenarios
        am_scenid = am_scenario.number + 837
        copy_scenario(from_scenario=am_scenario,
                    scenario_id=am_scenid,
                    scenario_title="{} Free flow Assignment".format(am_scenario.title),
                    overwrite=True,
                    copy_strategies=False)
        amscen_out = eb.scenario(am_scenid)


        # Copy to new MD Scenarios
        md_scenid = md_scenario.number + 837
        copy_scenario(from_scenario=md_scenario,
                    scenario_id=md_scenid,
                    scenario_title="{} Free flow Assignment".format(md_scenario.title),
                    overwrite=True,
                    copy_strategies=False)
        mdscen_out = eb.scenario(md_scenid)


        # Copy to new pm Scenarios
        pm_scenid = pm_scenario.number + 837
        copy_scenario(from_scenario=pm_scenario,
                    scenario_id=pm_scenid,
                    scenario_title="{} Free flow Assignment".format(pm_scenario.title),
                    overwrite=True,
                    copy_strategies=False)
        pmscen_out = eb.scenario(pm_scenid)

        return amscen_out, mdscen_out, pmscen_out

