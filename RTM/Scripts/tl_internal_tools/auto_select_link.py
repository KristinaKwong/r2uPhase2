##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage3.autoassignment
##--Purpose: Auto assignment procedure
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback

class AutoAssignment(_m.Tool()):

    sl_scenario = _m.Attribute(_m.InstanceType)

    relative_gap = _m.Attribute(float)
    best_relative_gap = _m.Attribute(float)
    normalized_gap = _m.Attribute(float)
    max_iterations = _m.Attribute(int)
    period = _m.Attribute(int)
    tool_run_msg = _m.Attribute(unicode)

    def __init__(self):
        self.relative_gap = 0.0001
        self.best_relative_gap = 0.01
        self.normalized_gap = 0.005
        self.max_iterations = 250


    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Auto Assignment with Select Link"
        pb.description = "Performs a multi-class auto assignment with " +\
                         "14 classes. An analysis is also performed to calculate " +\
                         "generate select link volumes."
        pb.branding_text = "TransLink"

        pb.add_select(tool_attribute_name="period",keyvalues=[[1,"AM"],[2,"MD"],[3,"PM"]],
                title="AM, MD or PM")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        pb.add_select_scenario("sl_scenario", title="SL_Scenario:")

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

            self(self.sl_scenario, self.period)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Auto Traffic Assignment")
    def __call__(self, sl_scenario, period):

        am_demands = {"sov":   ["mfSOV_drvtrp_VOT_1_Am", "mfSOV_drvtrp_VOT_2_Am", "mfSOV_drvtrp_VOT_3_Am", "mfSOV_drvtrp_VOT_4_Am"],
                      "hov":   ["mfHOV_drvtrp_VOT_1_Am", "mfHOV_drvtrp_VOT_2_Am", "mfHOV_drvtrp_VOT_3_Am"],
                      "truck": ["mflgvPceAm", "mfhgvPceAm"]}



        md_demands = {"sov":   ["mfSOV_drvtrp_VOT_1_Md", "mfSOV_drvtrp_VOT_2_Md", "mfSOV_drvtrp_VOT_3_Md", "mfSOV_drvtrp_VOT_4_Md"],
                      "hov":   ["mfHOV_drvtrp_VOT_1_Md", "mfHOV_drvtrp_VOT_2_Md", "mfHOV_drvtrp_VOT_3_Md"],
                      "truck": ["mflgvPceMd", "mfhgvPceMd"]}



        pm_demands = {"sov":   ["mfSOV_drvtrp_VOT_1_Pm", "mfSOV_drvtrp_VOT_2_Pm", "mfSOV_drvtrp_VOT_3_Pm", "mfSOV_drvtrp_VOT_4_Pm"],
                      "hov":   ["mfHOV_drvtrp_VOT_1_Pm", "mfHOV_drvtrp_VOT_2_Pm", "mfHOV_drvtrp_VOT_3_Pm"],
                      "truck": ["mflgvPcePm", "mfhgvPcePm"]}


        if period == 1:
            demand = am_demands

        if period == 2:
            demand = md_demands

        if period == 3:
            demand = pm_demands

        self.assign_scen(sl_scenario, am_demands)

    def assign_scen(self, scenario, demands):
        assign_traffic = _m.Modeller().tool("inro.emme.traffic_assignment.sola_traffic_assignment")

        self.calc_network_costs(scenario)
        self.tag_link(scenario)
        self.init_matrices(scenario.emmebank)

        # Second assignment to generate distance and time skims
        spec = self.get_class_specs(scenario.emmebank, demands)
        self.add_distance_path_analysis(spec)
        assign_traffic(spec, scenario=scenario)

        # Aggregate network volumes post-assignment and calculate intrazonal skims
        self.calc_network_volumes(scenario)

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
        path_od = { "considered_paths": "SELECTED",
                    "multiply_path_proportions_by": { "analyzed_demand": True, "path_value": False }
                  }
        spec["classes"][ 0]["analysis"] = {"results": {"od_values": "mfSOV_SL_1"}}
        spec["classes"][ 0]["path_analysis"] = {"link_component": "@sltag", "operator": ".max.", "path_to_od_composition": path_od, "selection_threshold": {"lower": 1.0, "upper": 1.0}}
        spec["classes"][ 1]["analysis"] = {"results": {"od_values": "mfSOV_SL_2"}}
        spec["classes"][ 1]["path_analysis"] = {"link_component": "@sltag", "operator": ".max.", "path_to_od_composition": path_od, "selection_threshold": {"lower": 1.0, "upper": 1.0} }
        spec["classes"][ 2]["analysis"] = {"results": {"od_values": "mfSOV_SL_3"}}
        spec["classes"][ 2]["path_analysis"] = {"link_component": "@sltag", "operator": ".max.", "path_to_od_composition": path_od, "selection_threshold": {"lower": 1.0, "upper": 1.0} }
        spec["classes"][ 3]["analysis"] = {"results": {"od_values": "mfSOV_SL_4"}}
        spec["classes"][ 3]["path_analysis"] = {"link_component": "@sltag", "operator": ".max.", "path_to_od_composition": path_od, "selection_threshold": {"lower": 1.0, "upper": 1.0} }
        spec["classes"][ 4]["analysis"] = {"results": {"od_values": "mfHOV_SL_1"}}
        spec["classes"][ 4]["path_analysis"] = {"link_component": "@sltag", "operator": ".max.", "path_to_od_composition": path_od, "selection_threshold": {"lower": 1.0, "upper": 1.0} }
        spec["classes"][ 5]["analysis"] = {"results": {"od_values": "mfHOV_SL_2"}}
        spec["classes"][ 5]["path_analysis"] = {"link_component": "@sltag", "operator": ".max.", "path_to_od_composition": path_od, "selection_threshold": {"lower": 1.0, "upper": 1.0} }
        spec["classes"][ 6]["analysis"] = {"results": {"od_values": "mfHOV_SL_3"}}
        spec["classes"][ 6]["path_analysis"] = {"link_component": "@sltag", "operator": ".max.", "path_to_od_composition": path_od, "selection_threshold": {"lower": 1.0, "upper": 1.0} }
        spec["classes"][ 7]["analysis"] = {"results": {"od_values": "mfLGV_SL"}}
        spec["classes"][ 7]["path_analysis"] = {"link_component": "@sltag", "operator": ".max.", "path_to_od_composition": path_od, "selection_threshold": {"lower": 1.0, "upper": 1.0} }
        spec["classes"][ 8]["analysis"] = {"results": {"od_values": "mfHGV_SL"}}
        spec["classes"][ 8]["path_analysis"] = {"link_component": "@sltag", "operator": ".max.", "path_to_od_composition": path_od, "selection_threshold": {"lower": 1.0, "upper": 1.0} }


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

    @_m.logbook_trace("Tag Select Link")
    def tag_link(self, scenario):
        util = _m.Modeller().tool("translink.util")
        eb = scenario.emmebank
        create_attr = _m.Modeller().tool("inro.emme.data.extra_attribute.create_extra_attribute")

        create_attr("LINK", "@sltag", "Tagged Link", 0, True, scenario)
        selection = """link = 680401, 423614 or link = 423613, 680302 """
        util.emme_link_calc(scenario, "@sltag", "1", sel_link=selection)


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

        # Add Select Link Demands
        matrices.append(["mf9960", "SOV_SL_1", "SOV_SL_1", 0])
        matrices.append(["mf9961", "SOV_SL_2", "SOV_SL_2", 0])
        matrices.append(["mf9962", "SOV_SL_3", "SOV_SL_3", 0])
        matrices.append(["mf9963", "SOV_SL_4", "SOV_SL_4", 0])
        matrices.append(["mf9964", "HOV_SL_1", "HOV_SL_1", 0])
        matrices.append(["mf9965", "HOV_SL_2", "HOV_SL_2", 0])
        matrices.append(["mf9966", "HOV_SL_3", "HOV_SL_3", 0])
        matrices.append(["mf9968", "LGV_SL", "LGV_SL", 0])
        matrices.append(["mf9969", "HGV_SL", "HGV_SL", 0])


        return matrices
