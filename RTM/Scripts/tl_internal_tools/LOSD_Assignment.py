##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##
##--Purpose: Run an LOS D Assignment for AM, MD and PM
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
        pb.description = "Performs an LOS D Assignment " +\
                         "with 4 classes, SOV, HOV , Light Trucks " +\
                         "and Heavy Trucks. Make sure to create separate AM, MD and PM Scenarios"
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

            self(eb, self.am_scenario, self.md_scenario, self.pm_scenario)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Auto Traffic Assignment")
    def __call__(self, eb, am_scenario, md_scenario, pm_scenario):

        util = _m.Modeller().tool("translink.util")

        # Initialize LOSD Skims by time period
        util.initmat(eb, "mf9650", "AmSovTimeLosDcnst", "SOV Minutes LOSD Constant AM", 0)
        util.initmat(eb, "mf9660", "MdSovTimeLosDcnst", "SOV Minutes LOSD Constant MD", 0)
        util.initmat(eb, "mf9670", "PmSovTimeLosDcnst", "SOV Minutes LOSD Constant PM", 0)
        util.initmat(eb, "mf9655", "AmHovTimeLosDcnst", "HOV Minutes LOSD Constant AM", 0)
        util.initmat(eb, "mf9665", "MdHovTimeLosDcnst", "HOV Minutes LOSD Constant MD", 0)
        util.initmat(eb, "mf9675", "PmHovTimeLosDcnst", "HOV Minutes LOSD Constant PM", 0)
        util.initmat(eb, "mf9680", "AmLgvTimeLosDcnst", "LGV Minutes LOSD Constant AM", 0)
        util.initmat(eb, "mf9681", "MdLgvTimeLosDcnst", "LGV Minutes LOSD Constant MD", 0)
        util.initmat(eb, "mf9682", "PmLgvTimeLosDcnst", "LGV Minutes LOSD Constant PM", 0)
        util.initmat(eb, "mf9690", "AmHgvTimeLosDcnst", "HGV Minutes LOSD Constant AM", 0)
        util.initmat(eb, "mf9691", "MdHgvTimeLosDcnst", "HGV Minutes LOSD Constant MD", 0)
        util.initmat(eb, "mf9692", "PmHgvTimeLosDcnst", "HGV Minutes LOSD Constant PM", 0)

        # AM

        self.assign_scen(am_scenario)
        self.calc_intrazonal_skims(eb)

        am_skims = {"sov":  ["mfAmSovTimeLosDcnst"],
                    "hov":  ["mfAmHovTimeLosDcnst"],
                    "lgv":  ["mfAmLgvTimeLosDcnst"],
                    "hgv":  ["mfAmHgvTimeLosDcnst"]}

        self.store_skims(am_scenario, am_skims)

        # MD

        self.assign_scen(md_scenario)
        self.calc_intrazonal_skims(eb)
        md_skims = {"sov":  ["mfMdSovTimeLosDcnst"],
                    "hov":  ["mfMdHovTimeLosDcnst"],
                    "lgv":  ["mfMdLgvTimeLosDcnst"],
                    "hgv":  ["mfMdHgvTimeLosDcnst"]}

        self.store_skims(md_scenario, md_skims)

        # PM

        self.assign_scen(pm_scenario)
        self.calc_intrazonal_skims(eb)
        pm_skims = {"sov":  ["mfPmSovTimeLosDcnst"],
                    "hov":  ["mfPmHovTimeLosDcnst"],
                    "lgv":  ["mfPmLgvTimeLosDcnst"],
                    "hgv":  ["mfPmHgvTimeLosDcnst"]}

        self.store_skims(pm_scenario, pm_skims)

    def assign_scen(self, scenario):
        assign_traffic = _m.Modeller().tool("inro.emme.traffic_assignment.sola_traffic_assignment")
        util = _m.Modeller().tool("translink.util")
        eb = _m.Modeller().emmebank

        self.init_matrices(scenario.emmebank)

        # undertake a dummy assignment with only background traffic at 85% of the volume (LOS D)
        # Calculate volume = 85% of capacity on the network and store it in ul3

        util.emme_link_calc(scenario, "ul3", "100", sel_link="vdf = 2")
        util.emme_link_calc(scenario, "ul3", "0.85*200*vdf*lanes", sel_link="vdf = 3,7")
        util.emme_link_calc(scenario, "ul3", "0.85*200*vdf*lanes", sel_link="vdf = 3,7")
        util.emme_link_calc(scenario, "ul3", "0.85*200*int(vdf/10)*lanes", sel_link="vdf = 10,79")
        util.emme_link_calc(scenario, "ul3", "0.85*1600*(lanes^1.05)", sel_link="vdf = 85")
        util.emme_link_calc(scenario, "ul3", "0.85*1600*(lanes^1.05)", sel_link="vdf = 88")

        # get truck perception_factor

        hgv_perception = eb.matrix("msVotHgv").data

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
                                        "shortest_paths": "mfHovTimeLosDcnst"
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
                                            "shortest_paths": "mfSovTimeLosDcnst"
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
                                            "shortest_paths": "mfLgvTimeLosDcnst"
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
                                            "shortest_paths": "mfHgvTimeLosDcnst"
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
                                                            "od_values": "mfHgvPenyLosDcnst"
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

        specs.append(util.matrix_spec("mfHgvTimeLosDcnst", "mfHgvTimeLosDcnst - mfHgvPenyLosDcnst"))
        util.compute_matrix(specs, scenario)

    @_m.logbook_trace("Execute Intrazonal Calculation")

    def calc_intrazonal_skims(self, eb):

        # Calculate Intrazonal Analysis 1
        self.calc_intrazonal_skim(eb, "mfSovTimeLosDcnst")
        self.calc_intrazonal_skim(eb, "mfHovTimeLosDcnst")
        self.calc_intrazonal_skim(eb, "mfLgvTimeLosDcnst")
        self.calc_intrazonal_skim(eb, "mfHgvTimeLosDcnst")

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

        specs.append(util.matrix_spec(skim_list["sov"][0], "mfSovTimeLosDcnst"))
        specs.append(util.matrix_spec(skim_list["hov"][0], "mfHovTimeLosDcnst"))
        specs.append(util.matrix_spec(skim_list["lgv"][0], "mfLgvTimeLosDcnst"))
        specs.append(util.matrix_spec(skim_list["hgv"][0], "mfHgvTimeLosDcnst"))

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

        matrices.append(["mf9600", "SovTimeLosDcnst",  "SOV Minutes LOSD Constant", 0])
        matrices.append(["mf9605", "HovTimeLosDcnst",  "HOV Minutes LOSD Constant", 0])
        matrices.append(["mf9630", "LgvTimeLosDcnst",  "LGV Minutes LOSD Constant", 0])
        matrices.append(["mf9640", "HgvTimeLosDcnst",  "HGV Minutes LOSD Constant", 0])
        matrices.append(["mf9641", "HgvPenyLosDcnst",  "HGV TrkPeny LOSD Constant", 0])

        return matrices
