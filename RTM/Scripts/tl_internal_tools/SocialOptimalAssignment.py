##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage3.autoassignment
##--Purpose: Auto assignment - Social Cost Analysis
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
        self.max_iterations = 200

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Auto Assignment"
        pb.description = "Social Cost Analysis" 
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
        self.socialcost_batchin(am_scenario)
        am_demands = {"sov":   ["mfSOV_drvtrp_VOT_1_Am", "mfSOV_drvtrp_VOT_2_Am", "mfSOV_drvtrp_VOT_3_Am", "mfSOV_drvtrp_VOT_4_Am"],
                      "hov":   ["mfHOV_drvtrp_VOT_1_Am", "mfHOV_drvtrp_VOT_2_Am", "mfHOV_drvtrp_VOT_3_Am"],
                      "truck": ["mflgvPceAm", "mfhgvPceAm"]}
        self.assign_scen(am_scenario, am_demands)
        am_skimsSC = {"sovVot1":  ["mfAmSovOriginalTIMAU1", "mfAmSovSocialCost1"],
                      "sovVot2":  ["mfAmSovOriginalTIMAU2", "mfAmSovSocialCost2"],
                      "sovVot3":  ["mfAmSovOriginalTIMAU3", "mfAmSovSocialCost3"],
                      "sovVot4":  ["mfAmSovOriginalTIMAU4", "mfAmSovSocialCost4"],
                      "hovVot1":  ["mfAmHovOriginalTIMAU1", "mfAmHovSocialCost1"],
                      "hovVot2":  ["mfAmHovOriginalTIMAU2", "mfAmHovSocialCost2"],
                      "hovVot3":  ["mfAmHovOriginalTIMAU3", "mfAmHovSocialCost3"],
                      "lgv":  ["mfAmLgvOriginalTIMAU", "mfAmLgvSocialCost"],
                      "hgv":  ["mfAmHgvOriginalTIMAU", "mfAmHgvSocialCost"]}
        self.store_socialcost_skims(am_scenario, am_skimsSC)
        
        md_demands = {"sov":   ["mfSOV_drvtrp_VOT_1_Md", "mfSOV_drvtrp_VOT_2_Md", "mfSOV_drvtrp_VOT_3_Md", "mfSOV_drvtrp_VOT_4_Md"],
                      "hov":   ["mfHOV_drvtrp_VOT_1_Md", "mfHOV_drvtrp_VOT_2_Md", "mfHOV_drvtrp_VOT_3_Md"],
                      "truck": ["mflgvPceMd", "mfhgvPceMd"]}
        self.assign_scen(md_scenario, md_demands)
        md_skimsSC = {"sovVot1":  ["mfMdSovOriginalTIMAU1", "mfMdSovSocialCost1"],
                      "sovVot2":  ["mfMdSovOriginalTIMAU2", "mfMdSovSocialCost2"],
                      "sovVot3":  ["mfMdSovOriginalTIMAU3", "mfMdSovSocialCost3"],
                      "sovVot4":  ["mfMdSovOriginalTIMAU4", "mfMdSovSocialCost4"],
                      "hovVot1":  ["mfMdHovOriginalTIMAU1", "mfMdHovSocialCost1"],
                      "hovVot2":  ["mfMdHovOriginalTIMAU2", "mfMdHovSocialCost2"],
                      "hovVot3":  ["mfMdHovOriginalTIMAU3", "mfMdHovSocialCost3"],
                      "lgv":  ["mfMdLgvOriginalTIMAU", "mfMdLgvSocialCost"],
                      "hgv":  ["mfMdHgvOriginalTIMAU", "mfMdHgvSocialCost"]}
        self.store_socialcost_skims(md_scenario, md_skimsSC)
        
        pm_demands = {"sov":   ["mfSOV_drvtrp_VOT_1_Pm", "mfSOV_drvtrp_VOT_2_Pm", "mfSOV_drvtrp_VOT_3_Pm", "mfSOV_drvtrp_VOT_4_Pm"],
                      "hov":   ["mfHOV_drvtrp_VOT_1_Pm", "mfHOV_drvtrp_VOT_2_Pm", "mfHOV_drvtrp_VOT_3_Pm"],
                      "truck": ["mflgvPcePm", "mfhgvPcePm"]}
        self.assign_scen(pm_scenario, pm_demands)
        pm_skimsSC = {"sovVot1":  ["mfPmSovOriginalTIMAU1", "mfPmSovSocialCost1"],
                      "sovVot2":  ["mfPmSovOriginalTIMAU2", "mfPmSovSocialCost2"],
                      "sovVot3":  ["mfPmSovOriginalTIMAU3", "mfPmSovSocialCost3"],
                      "sovVot4":  ["mfPmSovOriginalTIMAU4", "mfPmSovSocialCost4"],
                      "hovVot1":  ["mfPmHovOriginalTIMAU1", "mfPmHovSocialCost1"],
                      "hovVot2":  ["mfPmHovOriginalTIMAU2", "mfPmHovSocialCost2"],
                      "hovVot3":  ["mfPmHovOriginalTIMAU3", "mfPmHovSocialCost3"],
                      "lgv":  ["mfPmLgvOriginalTIMAU", "mfPmLgvSocialCost"],
                      "hgv":  ["mfPmHgvOriginalTIMAU", "mfPmHgvSocialCost"]}
        self.store_socialcost_skims(pm_scenario, pm_skimsSC)
        
    def assign_scen(self, scenario, demands):
        assign_traffic = _m.Modeller().tool("inro.emme.traffic_assignment.sola_traffic_assignment")

        self.init_matrices(scenario.emmebank)
        #compute social cost 
        self.calc_network_social_costs(scenario)
        self.calc_transit_us2(scenario)

        # Generate basic specification of modes/VOTs/saved volumes
        spec = self.get_class_specs(scenario.emmebank, demands)
        self.add_SocialCost_Path_analysis(spec)
        self.add_origionalVDF_Path_analysis(spec)
        
        # run assignment
        assign_traffic(spec, scenario=scenario)
        
    def store_socialcost_skims(self, scenario, skim_list):

        util = _m.Modeller().tool("translink.util")
        specs = []
        # Set ul1 = Timau from original VDF Matrices
        specs.append(util.matrix_spec(skim_list["sovVot1"][0], "mfSOVOrigTIMAU1"))
        specs.append(util.matrix_spec(skim_list["sovVot2"][0], "mfSOVOrigTIMAU2"))
        specs.append(util.matrix_spec(skim_list["sovVot3"][0], "mfSOVOrigTIMAU3"))
        specs.append(util.matrix_spec(skim_list["sovVot4"][0], "mfSOVOrigTIMAU4"))
        specs.append(util.matrix_spec(skim_list["hovVot1"][0], "mfHOVOrigTIMAU1"))
        specs.append(util.matrix_spec(skim_list["hovVot2"][0], "mfHOVOrigTIMAU2"))
        specs.append(util.matrix_spec(skim_list["hovVot3"][0], "mfHOVOrigTIMAU3"))
        specs.append(util.matrix_spec(skim_list["lgv"][0], "mfLGVOrigTIMAU"))
        specs.append(util.matrix_spec(skim_list["hgv"][0], "mfHGVOrigTIMAU"))
        # Set ul2 = social cost Matrices
        specs.append(util.matrix_spec(skim_list["sovVot1"][1], "mfSOVSocialCost1"))
        specs.append(util.matrix_spec(skim_list["sovVot2"][1], "mfSOVSocialCost2"))
        specs.append(util.matrix_spec(skim_list["sovVot3"][1], "mfSOVSocialCost3"))
        specs.append(util.matrix_spec(skim_list["sovVot4"][1], "mfSOVSocialCost4"))
        specs.append(util.matrix_spec(skim_list["hovVot1"][1], "mfHOVSocialCost1"))
        specs.append(util.matrix_spec(skim_list["hovVot2"][1], "mfHOVSocialCost2"))
        specs.append(util.matrix_spec(skim_list["hovVot3"][1], "mfHOVSocialCost3"))
        specs.append(util.matrix_spec(skim_list["lgv"][1], "mfLGVSocialCost"))
        specs.append(util.matrix_spec(skim_list["hgv"][1], "mfHGVSocialCost"))
        
        util.compute_matrix(specs)

        # now that the skims have been written back, delete the temporary matrices
        for matrix in self.get_temp_SC_matrices():
            util.delmat(scenario.emmebank, matrix[0])
            
            
    def add_mode_specification(self, specs, mode, demand, gc_cost, gc_factor):
        spec = {"mode": mode,
                "demand": demand,
                "generalized_cost": { "link_costs": gc_cost, "perception_factor": gc_factor },
                "results": { "od_travel_times": None,
                             "link_volumes": None,
                             "turn_volumes": None },
                "path_analyses": []
                }
        specs.append(spec)

    def get_class_specs(self, eb, demand_matrices):
        all_classes = []
        # SOV Classes
        self.add_mode_specification(all_classes, "d", demand_matrices["sov"][0], "@sovoc", eb.matrix("msAutoVOT1").data)
        self.add_mode_specification(all_classes, "d", demand_matrices["sov"][1], "@sovoc", eb.matrix("msAutoVOT2").data)
        self.add_mode_specification(all_classes, "d", demand_matrices["sov"][2], "@sovoc", eb.matrix("msAutoVOT3").data)
        self.add_mode_specification(all_classes, "d", demand_matrices["sov"][3], "@sovoc", eb.matrix("msAutoVOT4").data)
        # HOV Classes
        self.add_mode_specification(all_classes, "c", demand_matrices["hov"][0], "@hovoc", eb.matrix("msAutoVOT1").data)
        self.add_mode_specification(all_classes, "c", demand_matrices["hov"][1], "@hovoc", eb.matrix("msAutoVOT2").data)
        self.add_mode_specification(all_classes, "c", demand_matrices["hov"][2], "@hovoc", eb.matrix("msAutoVOT5").data)

        # Truck Classes
        self.add_mode_specification(all_classes, "x", demand_matrices["truck"][0], "@lgvoc", eb.matrix("msVotLgv").data)
        self.add_mode_specification(all_classes, "t", demand_matrices["truck"][1], "@hgvoc", eb.matrix("msVotHgv").data)

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

    def add_SocialCost_Path_analysis(self, spec):
        path_od = { "considered_paths": "ALL",
                    "multiply_path_proportions_by": { "analyzed_demand": False, "path_value": True }
                  }
        spec["classes"][ 0]["path_analyses"].append({"results": {"od_values": "mfSOVSocialCost1",},"link_component": "ul2", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 1]["path_analyses"].append({"results": {"od_values": "mfSOVSocialCost2",},"link_component": "ul2", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 2]["path_analyses"].append({"results": {"od_values": "mfSOVSocialCost3",},"link_component": "ul2", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 3]["path_analyses"].append({"results": {"od_values": "mfSOVSocialCost4",},"link_component": "ul2", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 4]["path_analyses"].append({"results": {"od_values": "mfHOVSocialCost1",},"link_component": "ul2", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 5]["path_analyses"].append({"results": {"od_values": "mfHOVSocialCost2",},"link_component": "ul2", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 6]["path_analyses"].append({"results": {"od_values": "mfHOVSocialCost3",},"link_component": "ul2", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 7]["path_analyses"].append({"results": {"od_values": "mfLGVSocialCost"},  "link_component": "ul2", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 8]["path_analyses"].append({"results": {"od_values": "mfHGVSocialCost"},  "link_component": "ul2", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
                                                                              
    def add_origionalVDF_Path_analysis(self, spec):
        path_od = { "considered_paths": "ALL",
                    "multiply_path_proportions_by": { "analyzed_demand": False, "path_value": True }
                  }
        spec["classes"][ 0]["path_analyses"].append({"results": {"od_values": "mfSOVOrigTIMAU1",}, "link_component": "ul1", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 1]["path_analyses"].append({"results": {"od_values": "mfSOVOrigTIMAU2",}, "link_component": "ul1", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 2]["path_analyses"].append({"results": {"od_values": "mfSOVOrigTIMAU3",}, "link_component": "ul1", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 3]["path_analyses"].append({"results": {"od_values": "mfSOVOrigTIMAU4",}, "link_component": "ul1", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 4]["path_analyses"].append({"results": {"od_values": "mfHOVOrigTIMAU1",}, "link_component": "ul1", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 5]["path_analyses"].append({"results": {"od_values": "mfHOVOrigTIMAU2",}, "link_component": "ul1", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 6]["path_analyses"].append({"results": {"od_values": "mfHOVOrigTIMAU3",}, "link_component": "ul1", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 7]["path_analyses"].append({"results": {"od_values": "mfLGVOrigTIMAU"},   "link_component": "ul1", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 8]["path_analyses"].append({"results": {"od_values": "mfHGVOrigTIMAU"},   "link_component": "ul1", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })


    def init_matrices(self, eb):
        util = _m.Modeller().tool("translink.util")

        for matrix in self.get_temp_SC_matrices():
            util.initmat(eb, matrix[0], matrix[1], matrix[2], matrix[3])
        
    def get_temp_SC_matrices(self):
        matrices = []
        #Original timau = ul1
        matrices.append(["mf9950", "SOVOrigTIMAU1",  "SOV Original VDF Travel Time 1", 0])
        matrices.append(["mf9951", "SOVOrigTIMAU2",  "SOV Original VDF Travel Time 2", 0])
        matrices.append(["mf9952", "SOVOrigTIMAU3",  "SOV Original VDF Travel Time 3", 0])
        matrices.append(["mf9953", "SOVOrigTIMAU4",  "SOV Original VDF Travel Time 4", 0])
        matrices.append(["mf9954", "HOVOrigTIMAU1",  "HOV Original VDF Travel Time 1", 0])
        matrices.append(["mf9955", "HOVOrigTIMAU2",  "HOV Original VDF Travel Time 2", 0])
        matrices.append(["mf9956", "HOVOrigTIMAU3",  "HOV Original VDF Travel Time 3", 0])
        matrices.append(["mf9957", "HOVOrigTIMAU4",  "HOV Original VDF Travel Time 4", 0])
        matrices.append(["mf9958", "LGVOrigTIMAU",   "LGV Original VDF Travel Time", 0])
        matrices.append(["mf9959", "HGVOrigTIMAU",   "HGV Original VDF Travel Time", 0])
        #Social Cost = ul2
        matrices.append(["mf9960", "SOVSocialCost1",  "SOV Social Cost 1", 0])
        matrices.append(["mf9961", "SOVSocialCost2",  "SOV Social Cost 2", 0])
        matrices.append(["mf9962", "SOVSocialCost3",  "SOV Social Cost 3", 0])
        matrices.append(["mf9963", "SOVSocialCost4",  "SOV Social Cost 4", 0])
        matrices.append(["mf9964", "HOVSocialCost1",  "HOV Social Cost 1", 0])
        matrices.append(["mf9965", "HOVSocialCost2",  "HOV Social Cost 2", 0])
        matrices.append(["mf9966", "HOVSocialCost3",  "HOV Social Cost 3", 0])
        matrices.append(["mf9967", "HOVSocialCost4",  "HOV Social Cost 4", 0])
        matrices.append(["mf9968", "LGVSocialCost",   "LGV Social Cost", 0])
        matrices.append(["mf9969", "HGVSocialCost",   "HGV Social Cost", 0])
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

    def socialcost_batchin(self,scen):
        create_matrix = _m.Modeller().tool("inro.emme.data.matrix.create_matrix")
        # creat select link matrices, overwrite if exist
        # Original Timau
        create_matrix("mf5900", "AmSovOriginalTIMAU1", "Am SOV Original timau 1",0, True, scen)
        create_matrix("mf5901", "AmSovOriginalTIMAU2", "Am SOV Original timau 2",0, True, scen)
        create_matrix("mf5902", "AmSovOriginalTIMAU3", "Am SOV Original timau 3",0, True, scen)
        create_matrix("mf5903", "AmSovOriginalTIMAU4", "Am SOV Original timau 4",0, True, scen)
        create_matrix("mf5904", "AmHovOriginalTIMAU1", "Am HOV Original timau 1",0, True, scen)
        create_matrix("mf5905", "AmHovOriginalTIMAU2", "Am HOV Original timau 2",0, True, scen)
        create_matrix("mf5906", "AmHovOriginalTIMAU3", "Am HOV Original timau 3",0, True, scen)
        create_matrix("mf5907", "AmLgvOriginalTIMAU", "Am LGV Original timau",0, True, scen)
        create_matrix("mf5908", "AmHgvOriginalTIMAU", "Am HGV Original timau",0, True, scen)
        # Social Cost
        create_matrix("mf5910", "AmSovSocialCost1", "Am SOV Social Cost 1",0, True, scen)
        create_matrix("mf5911", "AmSovSocialCost2", "Am SOV Social Cost 2",0, True, scen)
        create_matrix("mf5912", "AmSovSocialCost3", "Am SOV Social Cost 3",0, True, scen)
        create_matrix("mf5913", "AmSovSocialCost4", "Am SOV Social Cost 4",0, True, scen)
        create_matrix("mf5914", "AmHovSocialCost1", "Am HOV Social Cost 1",0, True, scen)
        create_matrix("mf5915", "AmHovSocialCost2", "Am HOV Social Cost 2",0, True, scen)
        create_matrix("mf5916", "AmHovSocialCost3", "Am HOV Social Cost 3",0, True, scen)
        create_matrix("mf5917", "AmLgvSocialCost", "Am LGV Social Cost",0, True, scen)
        create_matrix("mf5918", "AmHgvSocialCost", "Am HGV Social Cost",0, True, scen)
        # Original Timau
        create_matrix("mf5920", "MdSovOriginalTIMAU1", "Md SOV Original timau 1",0, True, scen)
        create_matrix("mf5921", "MdSovOriginalTIMAU2", "Md SOV Original timau 2",0, True, scen)
        create_matrix("mf5922", "MdSovOriginalTIMAU3", "Md SOV Original timau 3",0, True, scen)
        create_matrix("mf5923", "MdSovOriginalTIMAU4", "Md SOV Original timau 4",0, True, scen)
        create_matrix("mf5924", "MdHovOriginalTIMAU1", "Md HOV Original timau 1",0, True, scen)
        create_matrix("mf5925", "MdHovOriginalTIMAU2", "Md HOV Original timau 2",0, True, scen)
        create_matrix("mf5926", "MdHovOriginalTIMAU3", "Md HOV Original timau 3",0, True, scen)
        create_matrix("mf5927", "MdLgvOriginalTIMAU", "Md LGV Original timau",0, True, scen)
        create_matrix("mf5928", "MdHgvOriginalTIMAU", "Md HGV Original timau",0, True, scen)
        # Social Cost
        create_matrix("mf5930", "MdSovSocialCost1", "Md SOV Social Cost 1",0, True, scen)
        create_matrix("mf5931", "MdSovSocialCost2", "Md SOV Social Cost 2",0, True, scen)
        create_matrix("mf5932", "MdSovSocialCost3", "Md SOV Social Cost 3",0, True, scen)
        create_matrix("mf5933", "MdSovSocialCost4", "Md SOV Social Cost 4",0, True, scen)
        create_matrix("mf5934", "MdHovSocialCost1", "Md HOV Social Cost 1",0, True, scen)
        create_matrix("mf5935", "MdHovSocialCost2", "Md HOV Social Cost 2",0, True, scen)
        create_matrix("mf5936", "MdHovSocialCost3", "Md HOV Social Cost 3",0, True, scen)
        create_matrix("mf5937", "MdLgvSocialCost", "Md LGV Social Cost",0, True, scen)
        create_matrix("mf5938", "MdHgvSocialCost", "Md HGV Social Cost",0, True, scen)
        # Original Timau
        create_matrix("mf5940", "PmSovOriginalTIMAU1", "Pm SOV Original timau 1",0, True, scen)
        create_matrix("mf5941", "PmSovOriginalTIMAU2", "Pm SOV Original timau 2",0, True, scen)
        create_matrix("mf5942", "PmSovOriginalTIMAU3", "Pm SOV Original timau 3",0, True, scen)
        create_matrix("mf5943", "PmSovOriginalTIMAU4", "Pm SOV Original timau 4",0, True, scen)
        create_matrix("mf5944", "PmHovOriginalTIMAU1", "Pm HOV Original timau 1",0, True, scen)
        create_matrix("mf5945", "PmHovOriginalTIMAU2", "Pm HOV Original timau 2",0, True, scen)
        create_matrix("mf5946", "PmHovOriginalTIMAU3", "Pm HOV Original timau 3",0, True, scen)
        create_matrix("mf5947", "PmLgvOriginalTIMAU", "Pm LGV Original timau",0, True, scen)
        create_matrix("mf5948", "PmHgvOriginalTIMAU", "Pm HGV Original timau",0, True, scen)
        # Social Cost    
        create_matrix("mf5950", "PmSovSocialCost1", "Pm SOV Social Cost 1",0, True, scen)
        create_matrix("mf5951", "PmSovSocialCost2", "Pm SOV Social Cost 2",0, True, scen)
        create_matrix("mf5952", "PmSovSocialCost3", "Pm SOV Social Cost 3",0, True, scen)
        create_matrix("mf5953", "PmSovSocialCost4", "Pm SOV Social Cost 4",0, True, scen)
        create_matrix("mf5954", "PmHovSocialCost1", "Pm HOV Social Cost 1",0, True, scen)
        create_matrix("mf5955", "PmHovSocialCost2", "Pm HOV Social Cost 2",0, True, scen)
        create_matrix("mf5956", "PmHovSocialCost3", "Pm HOV Social Cost 3",0, True, scen)
        create_matrix("mf5957", "PmLgvSocialCost", "Pm LGV Social Cost",0, True, scen)
        create_matrix("mf5958", "PmHgvSocialCost", "Pm HGV Social Cost",0, True, scen)