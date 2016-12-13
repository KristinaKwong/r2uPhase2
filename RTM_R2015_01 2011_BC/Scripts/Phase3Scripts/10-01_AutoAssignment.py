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
        am_demands = {"sov":   ["mf300", "mf301", "mf302", "mf303"],
                      "hov":   ["mf306", "mf307", "mf308", "mf309"],
                      "truck": ["mf312", "mf313"]}
        self.assign_scen(am_scenario, am_demands)
        am_skims = {"sovVot1":  ["mfAmSovDistVOT1", "mfAmSovTimeVOT1", "mfAmSovTollVOT1"],
                    "sovVot2":  ["mfAmSovDistVOT2", "mfAmSovTimeVOT2", "mfAmSovTollVOT2"],
                    "sovVot3":  ["mfAmSovDistVOT3", "mfAmSovTimeVOT3", "mfAmSovTollVOT3"],
                    "sovVot4":  ["mfAmSovDistVOT4", "mfAmSovTimeVOT4", "mfAmSovTollVOT4"],
                    "hovVot1":  ["mfAmHovDistVOT1", "mfAmHovTimeVOT1", "mfAmHovTollVOT1"],
                    "hovVot2":  ["mfAmHovDistVOT2", "mfAmHovTimeVOT2", "mfAmHovTollVOT2"],
                    "hovVot3":  ["mfAmHovDistVOT3", "mfAmHovTimeVOT3", "mfAmHovTollVOT3"],
                    "hovVot4":  ["mfAmHovDistVOT4", "mfAmHovTimeVOT4", "mfAmHovTollVOT4"],
                    "lgv":  ["mfAmLgvDist", "mfAmLgvTime", "mfAmLgvToll"],
                    "hgv":  ["mfAmHgvDist", "mfAmHgvTime", "mfAmHgvToll"]}
        self.store_skims(am_scenario, am_skims)

        md_demands = {"sov":   ["mf320", "mf321", "mf322", "mf323"],
                      "hov":   ["mf326", "mf327", "mf328", "mf329"],
                      "truck": ["mf332", "mf333"]}
        self.assign_scen(md_scenario, md_demands)
        md_skims = {"sovVot1":  ["mfMdSovDistVOT1", "mfMdSovTimeVOT1", "mfMdSovTollVOT1"],
                    "sovVot2":  ["mfMdSovDistVOT2", "mfMdSovTimeVOT2", "mfMdSovTollVOT2"],
                    "sovVot3":  ["mfMdSovDistVOT3", "mfMdSovTimeVOT3", "mfMdSovTollVOT3"],
                    "sovVot4":  ["mfMdSovDistVOT4", "mfMdSovTimeVOT4", "mfMdSovTollVOT4"],
                    "hovVot1":  ["mfMdHovDistVOT1", "mfMdHovTimeVOT1", "mfMdHovTollVOT1"],
                    "hovVot2":  ["mfMdHovDistVOT2", "mfMdHovTimeVOT2", "mfMdHovTollVOT2"],
                    "hovVot3":  ["mfMdHovDistVOT3", "mfMdHovTimeVOT3", "mfMdHovTollVOT3"],
                    "hovVot4":  ["mfMdHovDistVOT4", "mfMdHovTimeVOT4", "mfMdHovTollVOT4"],
                    "lgv":  ["mfMdLgvDist", "mfMdLgvTime", "mfMdLgvToll"],
                    "hgv":  ["mfMdHgvDist", "mfMdHgvTime", "mfMdHgvToll"]}
        self.store_skims(md_scenario, md_skims)
        pm_demands = {"sov":   ["mf340", "mf341", "mf342", "mf343"],
                      "hov":   ["mf346", "mf347", "mf348", "mf349"],
                      "truck": ["mf352", "mf353"]}
        self.assign_scen(pm_scenario, pm_demands)
        pm_skims = {"sovVot1":  ["mfPmSovDistVOT1", "mfPmSovTimeVOT1", "mfPmSovTollVOT1"],
                    "sovVot2":  ["mfPmSovDistVOT2", "mfPmSovTimeVOT2", "mfPmSovTollVOT2"],
                    "sovVot3":  ["mfPmSovDistVOT3", "mfPmSovTimeVOT3", "mfPmSovTollVOT3"],
                    "sovVot4":  ["mfPmSovDistVOT4", "mfPmSovTimeVOT4", "mfPmSovTollVOT4"],
                    "hovVot1":  ["mfPmHovDistVOT1", "mfPmHovTimeVOT1", "mfPmHovTollVOT1"],
                    "hovVot2":  ["mfPmHovDistVOT2", "mfPmHovTimeVOT2", "mfPmHovTollVOT2"],
                    "hovVot3":  ["mfPmHovDistVOT3", "mfPmHovTimeVOT3", "mfPmHovTollVOT3"],
                    "hovVot4":  ["mfPmHovDistVOT4", "mfPmHovTimeVOT4", "mfPmHovTollVOT4"],
                    "lgv":  ["mfPmLgvDist", "mfPmLgvTime", "mfPmLgvToll"],
                    "hgv":  ["mfPmHgvDist", "mfPmHgvTime", "mfPmHgvToll"]}
        self.store_skims(pm_scenario, pm_skims)

    def assign_scen(self, scenario, demands):
        assign_traffic = _m.Modeller().tool("inro.emme.traffic_assignment.sola_traffic_assignment")

        self.calc_network_costs(scenario)
        self.init_matrices(scenario.emmebank)

        # First assignment to generate toll skims
        spec = self.get_class_specs(scenario.emmebank, demands)
        self.add_toll_path_analysis(spec)
        assign_traffic(spec, scenario=scenario)

        # Second assignment to generate distance and time skims
        spec = self.get_class_specs(scenario.emmebank, demands)
        self.add_distance_path_analysis(spec)
        assign_traffic(spec, scenario=scenario)

        # Aggregate network volumes post-assignment and calculate intrazonal skims
        self.calc_network_volumes(scenario)
        self.calc_intrazonal_skims(scenario.emmebank)

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
        self.calc_intrazonal_skim(eb, "mfHOVTimeVOT4")
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
        self.calc_intrazonal_skim(eb, "mfHOVDistVOT4")
        self.calc_intrazonal_skim(eb, "mfLGVDist")
        self.calc_intrazonal_skim(eb, "mfHGVDist")

    def calc_intrazonal_skim(self, eb, matrix):
        util = _m.Modeller().tool("translink.emme.util")

        np_mat = util.get_matrix_numpy(eb, matrix)

        # calculate the mimimum non-zero value in each row and set half that
        # as the intrazonal value
        for i in xrange(np_mat.shape[0]):
            np_mat[i][i] = np_mat[i][np_mat[i] > 0].min() * 0.5

        # write the updated matrix back to the emmebank
        util.set_matrix_numpy(eb, matrix, np_mat)

    def store_skims(self, scenario, skim_list):
        util = _m.Modeller().tool("translink.emme.util")

        specs = []
        # Set Distance Matrices
        specs.append(util.matrix_spec(skim_list["sovVot1"][0], "mfSOVDistVOT1"))
        specs.append(util.matrix_spec(skim_list["sovVot2"][0], "mfSOVDistVOT2"))
        specs.append(util.matrix_spec(skim_list["sovVot3"][0], "mfSOVDistVOT3"))
        specs.append(util.matrix_spec(skim_list["sovVot4"][0], "mfSOVDistVOT4"))
        specs.append(util.matrix_spec(skim_list["hovVot1"][0], "mfHOVDistVOT1"))
        specs.append(util.matrix_spec(skim_list["hovVot2"][0], "mfHOVDistVOT2"))
        specs.append(util.matrix_spec(skim_list["hovVot3"][0], "mfHOVDistVOT3"))
        specs.append(util.matrix_spec(skim_list["hovVot4"][0], "mfHOVDistVOT4"))
        specs.append(util.matrix_spec(skim_list["lgv"][0], "mfLGVDist"))
        specs.append(util.matrix_spec(skim_list["hgv"][0], "mfHGVDist"))
        # Set GC Time Matrices
        specs.append(util.matrix_spec(skim_list["sovVot1"][1], "mfSOVTimeVOT1"))
        specs.append(util.matrix_spec(skim_list["sovVot2"][1], "mfSOVTimeVOT2"))
        specs.append(util.matrix_spec(skim_list["sovVot3"][1], "mfSOVTimeVOT3"))
        specs.append(util.matrix_spec(skim_list["sovVot4"][1], "mfSOVTimeVOT4"))
        specs.append(util.matrix_spec(skim_list["hovVot1"][1], "mfHOVTimeVOT1"))
        specs.append(util.matrix_spec(skim_list["hovVot2"][1], "mfHOVTimeVOT2"))
        specs.append(util.matrix_spec(skim_list["hovVot3"][1], "mfHOVTimeVOT3"))
        specs.append(util.matrix_spec(skim_list["hovVot4"][1], "mfHOVTimeVOT4"))
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
        specs.append(util.matrix_spec(skim_list["hovVot4"][2], "mfHOVTollVOT4"))
        specs.append(util.matrix_spec(skim_list["lgv"][2], "mfLGVToll"))
        specs.append(util.matrix_spec(skim_list["hgv"][2], "mfHGVToll"))

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
        self.add_mode_specification(all_classes, "d", demand_matrices["sov"][0], "@sovoc", eb.matrix("msAutoVOT1").data, "mfSOVTimeVOT1", "@sov1", "@tsov1")
        self.add_mode_specification(all_classes, "d", demand_matrices["sov"][1], "@sovoc", eb.matrix("msAutoVOT2").data, "mfSOVTimeVOT2", "@sov2", "@tsov2")
        self.add_mode_specification(all_classes, "d", demand_matrices["sov"][2], "@sovoc", eb.matrix("msAutoVOT3").data, "mfSOVTimeVOT3", "@sov3", "@tsov3")
        self.add_mode_specification(all_classes, "d", demand_matrices["sov"][3], "@sovoc", eb.matrix("msAutoVOT4").data, "mfSOVTimeVOT4", "@sov4", "@tsov4")
        # HOV Classes
        self.add_mode_specification(all_classes, "c", demand_matrices["hov"][0], "@hovoc", eb.matrix("msAutoVOT1").data, "mfHOVTimeVOT1", "@hov1", "@thov1")
        self.add_mode_specification(all_classes, "c", demand_matrices["hov"][1], "@hovoc", eb.matrix("msAutoVOT2").data, "mfHOVTimeVOT2", "@hov2", "@thov2")
        self.add_mode_specification(all_classes, "c", demand_matrices["hov"][2], "@hovoc", eb.matrix("msAutoVOT3").data, "mfHOVTimeVOT3", "@hov3", "@thov3")
        self.add_mode_specification(all_classes, "c", demand_matrices["hov"][3], "@hovoc", eb.matrix("msAutoVOT4").data, "mfHOVTimeVOT4", "@hov4", "@thov4")
        # Truck Classes
        self.add_mode_specification(all_classes, "x", demand_matrices["truck"][0], "@lgvoc", eb.matrix("msVotLgv").data, "mfLGVTime", "@lgvol", "@lgvtn")
        self.add_mode_specification(all_classes, "t", demand_matrices["truck"][1], "@hgvoc", eb.matrix("msVotHgv").data, "mfHGVTime", "@hgvol", "@hgvtn")

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
        spec["path_analysis"] = {"link_component": "length",
                                 "operator": "+",
                                 "selection_threshold": {"lower": -999999, "upper": 999999},
                                 "path_to_od_composition": {
                                     "considered_paths": "ALL",
                                     "multiply_path_proportions_by": {
                                         "analyzed_demand": False,
                                         "path_value": True
                                     }
                                 }
                                }
        spec["classes"][ 0]["analysis"] = {"results": {"od_values": "mfSOVDistVOT1"}}
        spec["classes"][ 1]["analysis"] = {"results": {"od_values": "mfSOVDistVOT2"}}
        spec["classes"][ 2]["analysis"] = {"results": {"od_values": "mfSOVDistVOT3"}}
        spec["classes"][ 3]["analysis"] = {"results": {"od_values": "mfSOVDistVOT4"}}
        spec["classes"][ 4]["analysis"] = {"results": {"od_values": "mfHOVDistVOT1"}}
        spec["classes"][ 5]["analysis"] = {"results": {"od_values": "mfHOVDistVOT2"}}
        spec["classes"][ 6]["analysis"] = {"results": {"od_values": "mfHOVDistVOT3"}}
        spec["classes"][ 7]["analysis"] = {"results": {"od_values": "mfHOVDistVOT4"}}
        spec["classes"][ 8]["analysis"] = {"results": {"od_values": "mfLGVDist"}}
        spec["classes"][ 9]["analysis"] = {"results": {"od_values": "mfHGVDist"}}

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
        spec["classes"][ 7]["analysis"] = {"results": {"od_values": "mfHOVTollVOT4"}}
        spec["classes"][ 8]["analysis"] = {"results": {"od_values": "mfLGVToll"}}
        spec["classes"][ 9]["analysis"] = {"results": {"od_values": "mfHGVToll"}}

    @_m.logbook_trace("Calculate Link and Turn Aggregate Volumes")
    def calc_network_volumes(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")

        util.emme_link_calc(scenario, "@wsovl", "@sov1+@sov2+@sov3+@sov4+@sov5+@sov6")
        util.emme_link_calc(scenario, "@whovl", "@hov1+@hov2+@hov3+@hov4+@hov5+@hov6")
        util.emme_turn_calc(scenario, "@wsovt", "@tsov1+@tsov2+@tsov3+@tsov4+@tsov5+@tsov6")
        util.emme_turn_calc(scenario, "@whovt", "@thov1+@thov2+@thov3+@thov4+@thov5+@thov6")

    @_m.logbook_trace("Calculate Fixed Network Costs")
    def calc_network_costs(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")
        eb = scenario.emmebank

        hov_occupancy = eb.matrix("ms44").data
        auto_voc = eb.matrix("ms100").data
        lgv_voc = eb.matrix("ms101").data
        hgv_voc = eb.matrix("ms102").data

        util.emme_link_calc(scenario, "@tkpen", "0")
        util.emme_link_calc(scenario, "@tkpen", "length * 100", sel_link="mode=n")
        util.emme_link_calc(scenario, "@sovoc", "length * %s + @tolls" % (auto_voc))
        #TODO: investigate why occupancy is only applied to tolls and not to fixed link costs
        util.emme_link_calc(scenario, "@hovoc", "length * %s + @tolls / %s" % (auto_voc, hov_occupancy))
        util.emme_link_calc(scenario, "@lgvoc", "length * %s + 2 * @tolls" % (lgv_voc))
        util.emme_link_calc(scenario, "@hgvoc", "length * %s + 3 * @tolls + @tkpen" % (hgv_voc))

    def init_matrices(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        util.initmat(eb, "mf9900", "SOVTimeVOT1",  "SOV Time VOT1", 0)
        util.initmat(eb, "mf9901", "SOVTimeVOT2",  "SOV Time VOT2", 0)
        util.initmat(eb, "mf9902", "SOVTimeVOT3",  "SOV Time VOT3", 0)
        util.initmat(eb, "mf9903", "SOVTimeVOT4",  "SOV Time VOT4", 0)
        util.initmat(eb, "mf9904", "HOVTimeVOT1",  "HOV Time VOT1", 0)
        util.initmat(eb, "mf9905", "HOVTimeVOT2",  "HOV Time VOT2", 0)
        util.initmat(eb, "mf9906", "HOVTimeVOT3",  "HOV Time VOT3", 0)
        util.initmat(eb, "mf9907", "HOVTimeVOT4",  "HOV Time VOT4", 0)
        util.initmat(eb, "mf9908", "LGVTime",      "LGV Time", 0)
        util.initmat(eb, "mf9909", "HGVTime",      "HGV Time", 0)

        util.initmat(eb, "mf9920", "SOVDistVOT1",  "SOV Distance VOT1", 0)
        util.initmat(eb, "mf9921", "SOVDistVOT2",  "SOV Distance VOT2", 0)
        util.initmat(eb, "mf9922", "SOVDistVOT3",  "SOV Distance VOT3", 0)
        util.initmat(eb, "mf9923", "SOVDistVOT4",  "SOV Distance VOT4", 0)
        util.initmat(eb, "mf9924", "HOVDistVOT1",  "HOV Distance VOT1", 0)
        util.initmat(eb, "mf9925", "HOVDistVOT2",  "HOV Distance VOT2", 0)
        util.initmat(eb, "mf9926", "HOVDistVOT3",  "HOV Distance VOT3", 0)
        util.initmat(eb, "mf9927", "HOVDistVOT4",  "HOV Distance VOT4", 0)
        util.initmat(eb, "mf9928", "LGVDist",      "LGV Distance", 0)
        util.initmat(eb, "mf9929", "HGVDist",      "HGV Distance", 0)

        util.initmat(eb, "mf9940", "SOVTollVOT1",  "SOV Toll VOT1", 0)
        util.initmat(eb, "mf9941", "SOVTollVOT2",  "SOV Toll VOT2", 0)
        util.initmat(eb, "mf9942", "SOVTollVOT3",  "SOV Toll VOT3", 0)
        util.initmat(eb, "mf9943", "SOVTollVOT4",  "SOV Toll VOT4", 0)
        util.initmat(eb, "mf9944", "HOVTollVOT1",  "HOV Toll VOT1", 0)
        util.initmat(eb, "mf9945", "HOVTollVOT2",  "HOV Toll VOT2", 0)
        util.initmat(eb, "mf9946", "HOVTollVOT3",  "HOV Toll VOT3", 0)
        util.initmat(eb, "mf9947", "HOVTollVOT4",  "HOV Toll VOT4", 0)
        util.initmat(eb, "mf9948", "LGVToll",      "LGV Toll", 0)
        util.initmat(eb, "mf9949", "HGVToll",      "HGV Toll", 0)

