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

            self(eb, self.am_scenario, self.md_scenario, self.pm_scenario)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Auto Traffic Assignment")
    def __call__(self, eb, am_scenario, md_scenario, pm_scenario):

        util = _m.Modeller().tool("translink.util")

        # Initialize skim matrices by time period
        util.initmat(eb, "mf9500", "SOVTimeCongVOT1AM",  "SOV Minutes Cong VOT1 AM", 0)
        util.initmat(eb, "mf9501", "SOVTimeCongVOT2AM",  "SOV Minutes Cong VOT2 AM", 0)
        util.initmat(eb, "mf9502", "SOVTimeCongVOT3AM",  "SOV Minutes Cong VOT3 AM", 0)
        util.initmat(eb, "mf9503", "SOVTimeCongVOT4AM",  "SOV Minutes Cong VOT4 AM", 0)
        util.initmat(eb, "mf9505", "HOVTimeCongVOT1AM",  "HOV Minutes Cong VOT1 AM", 0)
        util.initmat(eb, "mf9506", "HOVTimeCongVOT2AM",  "HOV Minutes Cong VOT2 AM", 0)
        util.initmat(eb, "mf9507", "HOVTimeCongVOT3AM",  "HOV Minutes Cong VOT3 AM", 0)
        util.initmat(eb, "mf9508", "HOVTimeCongVOT4AM",  "HOV Minutes Cong VOT4 AM", 0)

        util.initmat(eb, "mf9510", "SOVTimeCongVOT1MD",  "SOV Minutes Cong VOT1 MD", 0)
        util.initmat(eb, "mf9511", "SOVTimeCongVOT2MD",  "SOV Minutes Cong VOT2 MD", 0)
        util.initmat(eb, "mf9512", "SOVTimeCongVOT3MD",  "SOV Minutes Cong VOT3 MD", 0)
        util.initmat(eb, "mf9513", "SOVTimeCongVOT4MD",  "SOV Minutes Cong VOT4 MD", 0)
        util.initmat(eb, "mf9515", "HOVTimeCongVOT1MD",  "HOV Minutes Cong VOT1 MD", 0)
        util.initmat(eb, "mf9516", "HOVTimeCongVOT2MD",  "HOV Minutes Cong VOT2 MD", 0)
        util.initmat(eb, "mf9517", "HOVTimeCongVOT3MD",  "HOV Minutes Cong VOT3 MD", 0)
        util.initmat(eb, "mf9518", "HOVTimeCongVOT4MD",  "HOV Minutes Cong VOT4 MD", 0)

        util.initmat(eb, "mf9520", "SOVTimeCongVOT1PM",  "SOV Minutes Cong VOT1 PM", 0)
        util.initmat(eb, "mf9521", "SOVTimeCongVOT2PM",  "SOV Minutes Cong VOT2 PM", 0)
        util.initmat(eb, "mf9522", "SOVTimeCongVOT3PM",  "SOV Minutes Cong VOT3 PM", 0)
        util.initmat(eb, "mf9523", "SOVTimeCongVOT4PM",  "SOV Minutes Cong VOT4 PM", 0)
        util.initmat(eb, "mf9525", "HOVTimeCongVOT1PM",  "HOV Minutes Cong VOT1 PM", 0)
        util.initmat(eb, "mf9526", "HOVTimeCongVOT2PM",  "HOV Minutes Cong VOT2 PM", 0)
        util.initmat(eb, "mf9527", "HOVTimeCongVOT3PM",  "HOV Minutes Cong VOT3 PM", 0)
        util.initmat(eb, "mf9528", "HOVTimeCongVOT4PM",  "HOV Minutes Cong VOT4 PM", 0)

        # Initialize skim matrices by time period
        util.initmat(eb, "mf9550", "SOVTimeLOSDVOT1AM",  "SOV Minutes LOSD VOT1 AM", 0)
        util.initmat(eb, "mf9551", "SOVTimeLOSDVOT2AM",  "SOV Minutes LOSD VOT2 AM", 0)
        util.initmat(eb, "mf9552", "SOVTimeLOSDVOT3AM",  "SOV Minutes LOSD VOT3 AM", 0)
        util.initmat(eb, "mf9553", "SOVTimeLOSDVOT4AM",  "SOV Minutes LOSD VOT4 AM", 0)
        util.initmat(eb, "mf9555", "HOVTimeLOSDVOT1AM",  "HOV Minutes LOSD VOT1 AM", 0)
        util.initmat(eb, "mf9556", "HOVTimeLOSDVOT2AM",  "HOV Minutes LOSD VOT2 AM", 0)
        util.initmat(eb, "mf9557", "HOVTimeLOSDVOT3AM",  "HOV Minutes LOSD VOT3 AM", 0)
        util.initmat(eb, "mf9558", "HOVTimeLOSDVOT4AM",  "HOV Minutes LOSD VOT4 AM", 0)

        util.initmat(eb, "mf9560", "SOVTimeLOSDVOT1MD",  "SOV Minutes LOSD VOT1 MD", 0)
        util.initmat(eb, "mf9561", "SOVTimeLOSDVOT2MD",  "SOV Minutes LOSD VOT2 MD", 0)
        util.initmat(eb, "mf9562", "SOVTimeLOSDVOT3MD",  "SOV Minutes LOSD VOT3 MD", 0)
        util.initmat(eb, "mf9563", "SOVTimeLOSDVOT4MD",  "SOV Minutes LOSD VOT4 MD", 0)
        util.initmat(eb, "mf9565", "HOVTimeLOSDVOT1MD",  "HOV Minutes LOSD VOT1 MD", 0)
        util.initmat(eb, "mf9566", "HOVTimeLOSDVOT2MD",  "HOV Minutes LOSD VOT2 MD", 0)
        util.initmat(eb, "mf9567", "HOVTimeLOSDVOT3MD",  "HOV Minutes LOSD VOT3 MD", 0)
        util.initmat(eb, "mf9568", "HOVTimeLOSDVOT4MD",  "HOV Minutes LOSD VOT4 MD", 0)

        util.initmat(eb, "mf9570", "SOVTimeLOSDVOT1PM",  "SOV Minutes LOSD VOT1 PM", 0)
        util.initmat(eb, "mf9571", "SOVTimeLOSDVOT2PM",  "SOV Minutes LOSD VOT2 PM", 0)
        util.initmat(eb, "mf9572", "SOVTimeLOSDVOT3PM",  "SOV Minutes LOSD VOT3 PM", 0)
        util.initmat(eb, "mf9573", "SOVTimeLOSDVOT4PM",  "SOV Minutes LOSD VOT4 PM", 0)
        util.initmat(eb, "mf9575", "HOVTimeLOSDVOT1PM",  "HOV Minutes LOSD VOT1 PM", 0)
        util.initmat(eb, "mf9576", "HOVTimeLOSDVOT2PM",  "HOV Minutes LOSD VOT2 PM", 0)
        util.initmat(eb, "mf9577", "HOVTimeLOSDVOT3PM",  "HOV Minutes LOSD VOT3 PM", 0)
        util.initmat(eb, "mf9578", "HOVTimeLOSDVOT4PM",  "HOV Minutes LOSD VOT4 PM", 0)

        am_demands = {"sov":   ["mfSOV_drvtrp_VOT_1_Am", "mfSOV_drvtrp_VOT_2_Am", "mfSOV_drvtrp_VOT_3_Am", "mfSOV_drvtrp_VOT_4_Am"],
                      "hov":   ["mfHOV_drvtrp_VOT_1_Am", "mfHOV_drvtrp_VOT_2_Am", "mfHOV_drvtrp_VOT_3_Am"],
                      "truck": ["mflgvPceAm", "mfhgvPceAm"]}
        self.assign_scen(am_scenario, am_demands)
        am_skims = {"sovVot1":  ["mfSOVTimeCongVOT1AM", "mfSOVTimeLOSDVOT1AM"],
                    "sovVot2":  ["mfSOVTimeCongVOT2AM", "mfSOVTimeLOSDVOT2AM"],
                    "sovVot3":  ["mfSOVTimeCongVOT3AM", "mfSOVTimeLOSDVOT3AM"],
                    "sovVot4":  ["mfSOVTimeCongVOT4AM", "mfSOVTimeLOSDVOT4AM"],
                    "hovVot1":  ["mfHOVTimeCongVOT1AM", "mfHOVTimeLOSDVOT1AM"],
                    "hovVot2":  ["mfHOVTimeCongVOT2AM", "mfHOVTimeLOSDVOT2AM"],
                    "hovVot3":  ["mfHOVTimeCongVOT3AM", "mfHOVTimeLOSDVOT3AM"]}

        self.store_skims(am_scenario, am_skims)

        md_demands = {"sov":   ["mfSOV_drvtrp_VOT_1_Md", "mfSOV_drvtrp_VOT_2_Md", "mfSOV_drvtrp_VOT_3_Md", "mfSOV_drvtrp_VOT_4_Md"],
                      "hov":   ["mfHOV_drvtrp_VOT_1_Md", "mfHOV_drvtrp_VOT_2_Md", "mfHOV_drvtrp_VOT_3_Md"],
                      "truck": ["mflgvPceMd", "mfhgvPceMd"]}
        self.assign_scen(md_scenario, md_demands)
        md_skims = {"sovVot1":  ["mfSOVTimeCongVOT1MD", "mfSOVTimeLOSDVOT1MD"],
                    "sovVot2":  ["mfSOVTimeCongVOT2MD", "mfSOVTimeLOSDVOT2MD"],
                    "sovVot3":  ["mfSOVTimeCongVOT3MD", "mfSOVTimeLOSDVOT3MD"],
                    "sovVot4":  ["mfSOVTimeCongVOT4MD", "mfSOVTimeLOSDVOT4MD"],
                    "hovVot1":  ["mfHOVTimeCongVOT1MD", "mfHOVTimeLOSDVOT1MD"],
                    "hovVot2":  ["mfHOVTimeCongVOT2MD", "mfHOVTimeLOSDVOT2MD"],
                    "hovVot3":  ["mfHOVTimeCongVOT3MD", "mfHOVTimeLOSDVOT3MD"]}

        self.store_skims(md_scenario, md_skims)
        pm_demands = {"sov":   ["mfSOV_drvtrp_VOT_1_Pm", "mfSOV_drvtrp_VOT_2_Pm", "mfSOV_drvtrp_VOT_3_Pm", "mfSOV_drvtrp_VOT_4_Pm"],
                      "hov":   ["mfHOV_drvtrp_VOT_1_Pm", "mfHOV_drvtrp_VOT_2_Pm", "mfHOV_drvtrp_VOT_3_Pm"],
                      "truck": ["mflgvPcePm", "mfhgvPcePm"]}
        self.assign_scen(pm_scenario, pm_demands)
        pm_skims = {"sovVot1":  ["mfSOVTimeCongVOT1PM", "mfSOVTimeLOSDVOT1PM"],
                    "sovVot2":  ["mfSOVTimeCongVOT2PM", "mfSOVTimeLOSDVOT2PM"],
                    "sovVot3":  ["mfSOVTimeCongVOT3PM", "mfSOVTimeLOSDVOT3PM"],
                    "sovVot4":  ["mfSOVTimeCongVOT4PM", "mfSOVTimeLOSDVOT4PM"],
                    "hovVot1":  ["mfHOVTimeCongVOT1PM", "mfHOVTimeLOSDVOT1PM"],
                    "hovVot2":  ["mfHOVTimeCongVOT2PM", "mfHOVTimeLOSDVOT2PM"],
                    "hovVot3":  ["mfHOVTimeCongVOT3PM", "mfHOVTimeLOSDVOT3PM"]}
        self.store_skims(pm_scenario, pm_skims)

        ## subtract LOS D from congested skims and zero out intrazonals of FVRD

        self.calc_lost_time(eb)


    def calc_lost_time(self, eb):

        util = _m.Modeller().tool("translink.util")
        specs = []

        # AM
        specs.append(util.matrix_spec("mfSOVTimeCongVOT1AM", "(mfSOVTimeCongVOT1AM - mfSOVTimeLOSDVOT1AM)"))
        specs.append(util.matrix_spec("mfSOVTimeCongVOT2AM", "(mfSOVTimeCongVOT2AM - mfSOVTimeLOSDVOT2AM)"))
        specs.append(util.matrix_spec("mfSOVTimeCongVOT3AM", "(mfSOVTimeCongVOT3AM - mfSOVTimeLOSDVOT3AM)"))
        specs.append(util.matrix_spec("mfSOVTimeCongVOT4AM", "(mfSOVTimeCongVOT4AM - mfSOVTimeLOSDVOT4AM)"))
        specs.append(util.matrix_spec("mfHOVTimeCongVOT1AM", "(mfHOVTimeCongVOT1AM - mfHOVTimeLOSDVOT1AM)"))
        specs.append(util.matrix_spec("mfHOVTimeCongVOT2AM", "(mfHOVTimeCongVOT2AM - mfHOVTimeLOSDVOT2AM)"))
        specs.append(util.matrix_spec("mfHOVTimeCongVOT3AM", "(mfHOVTimeCongVOT3AM - mfHOVTimeLOSDVOT3AM)"))

        # MD
        specs.append(util.matrix_spec("mfSOVTimeCongVOT1MD", "(mfSOVTimeCongVOT1MD - mfSOVTimeLOSDVOT1MD)"))
        specs.append(util.matrix_spec("mfSOVTimeCongVOT2MD", "(mfSOVTimeCongVOT2MD - mfSOVTimeLOSDVOT2MD)"))
        specs.append(util.matrix_spec("mfSOVTimeCongVOT3MD", "(mfSOVTimeCongVOT3MD - mfSOVTimeLOSDVOT3MD)"))
        specs.append(util.matrix_spec("mfSOVTimeCongVOT4MD", "(mfSOVTimeCongVOT4MD - mfSOVTimeLOSDVOT4MD)"))
        specs.append(util.matrix_spec("mfHOVTimeCongVOT1MD", "(mfHOVTimeCongVOT1MD - mfHOVTimeLOSDVOT1MD)"))
        specs.append(util.matrix_spec("mfHOVTimeCongVOT2MD", "(mfHOVTimeCongVOT2MD - mfHOVTimeLOSDVOT2MD)"))
        specs.append(util.matrix_spec("mfHOVTimeCongVOT3MD", "(mfHOVTimeCongVOT3MD - mfHOVTimeLOSDVOT3MD)"))

        # PM
        specs.append(util.matrix_spec("mfSOVTimeCongVOT1PM", "(mfSOVTimeCongVOT1PM - mfSOVTimeLOSDVOT1PM)"))
        specs.append(util.matrix_spec("mfSOVTimeCongVOT2PM", "(mfSOVTimeCongVOT2PM - mfSOVTimeLOSDVOT2PM)"))
        specs.append(util.matrix_spec("mfSOVTimeCongVOT3PM", "(mfSOVTimeCongVOT3PM - mfSOVTimeLOSDVOT3PM)"))
        specs.append(util.matrix_spec("mfSOVTimeCongVOT4PM", "(mfSOVTimeCongVOT4PM - mfSOVTimeLOSDVOT4PM)"))
        specs.append(util.matrix_spec("mfHOVTimeCongVOT1PM", "(mfHOVTimeCongVOT1PM - mfHOVTimeLOSDVOT1PM)"))
        specs.append(util.matrix_spec("mfHOVTimeCongVOT2PM", "(mfHOVTimeCongVOT2PM - mfHOVTimeLOSDVOT2PM)"))
        specs.append(util.matrix_spec("mfHOVTimeCongVOT3PM", "(mfHOVTimeCongVOT3PM - mfHOVTimeLOSDVOT3PM)"))

        util.compute_matrix(specs)

    def assign_scen(self, scenario, demands):
        assign_traffic = _m.Modeller().tool("inro.emme.traffic_assignment.sola_traffic_assignment")
        util = _m.Modeller().tool("translink.util")
        eb = _m.Modeller().emmebank

        self.calc_network_costs(scenario)
        self.init_matrices(scenario.emmebank)

        # create attribute to store current travel times from network
        create_attr = _m.Modeller().tool("inro.emme.data.extra_attribute.create_extra_attribute")
        create_attr("LINK", "@timeval", "Link Travel Time", 0, True, scenario)
        create_attr("LINK", "@gvrdbin", "GVRD Binary", 1, True, scenario)
        # util.emme_link_calc(scenario, "@gvrdbin", "1", sel_link = "i = 0, 699999 and j = 0, 699999")
        util.emme_link_calc(scenario, "@timeval", "timau*@gvrdbin")
        util.emme_link_calc(scenario, "@timeval", "40", sel_link = "vdf = 2")

        # undertake a dummy assignment with only background traffic at 85% of the volume (LOS D)
        # Calculate volume = 85% of capacity on the network and store it in ul3
        util.emme_link_calc(scenario, "ul3", "0")
        util.emme_link_calc(scenario, "ul3", "0.85*200*vdf*lanes", sel_link="vdf = 3,7")
        util.emme_link_calc(scenario, "ul3", "0.85*200*int(vdf/10)*lanes", sel_link="vdf = 10,79")
        util.emme_link_calc(scenario, "ul3", "0.85*1600*(lanes^1.05)", sel_link="vdf = 85")
        util.emme_link_calc(scenario, "ul3", "0.85*1600*(lanes^1.05)", sel_link="vdf = 88")

        # Assign temporary scenario

        temp_scen_spec = {
                          "type": "SOLA_TRAFFIC_ASSIGNMENT",
                            "classes": [
                                {
                                    "mode": "c",
                                    "demand": "ms490",
                                    "generalized_cost": None,
                                    "results": {
                                        "link_volumes": None,
                                        "turn_volumes": None,
                                        "od_travel_times": {
                                            "shortest_paths": "mf9300"
                                        }
                                    },
                                    "analysis": {
                                        "analyzed_demand": None,
                                        "results": {
                                            "od_values": None,
                                            "selected_link_volumes": None,
                                            "selected_turn_volumes": None
                                        }
                                    }
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
                            "path_analysis": None,
                            "cutoff_analysis": None,
                            "traversal_analysis": None,
                            "stopping_criteria": {
                                "max_iterations": 100,
                                "relative_gap": 0,
                                "best_relative_gap": 0.1,
                                "normalized_gap": 0.05
                            }
                        }


        assign_traffic = _m.Modeller().tool("inro.emme.traffic_assignment.sola_traffic_assignment")
        assign_traffic(temp_scen_spec, scenario=scenario)

        # store travel time on links based on LOS D assignment
        create_attr("LINK", "@timeeff", "Link Travel Time efficient", 0, True, scenario)
        util.emme_link_calc(scenario, "@timeeff", "timau*@gvrdbin")
        util.emme_link_calc(scenario, "@timeeff", "40", sel_link = "vdf = 2")


        # replace link travel times less than time LOS D with LOS D times
        util.emme_link_calc(scenario, "@timeval", "(@timeeff.max.@timeval)")

        # Generate basic specification of modes/VOTs/saved volumes
        spec = self.get_class_specs(scenario.emmebank, demands)

        # skim the vehicle operating costs
        self.add_first_analysis(spec)
        self.add_second_analysis(spec)

        # run assignment
        assign_traffic(spec, scenario=scenario)

        # Aggregate network volumes post-assignment and calculate intrazonal skims
        self.calc_network_volumes(scenario)
        self.calc_intrazonal_skims(scenario.emmebank)

    @_m.logbook_trace("Execute Intrazonal Calculation")
    def calc_intrazonal_skims(self, eb):
        # Calculate Intrazonal Analysis 1
        self.calc_intrazonal_skim(eb, "mfSOVTimeCongVOT1")
        self.calc_intrazonal_skim(eb, "mfSOVTimeCongVOT2")
        self.calc_intrazonal_skim(eb, "mfSOVTimeCongVOT3")
        self.calc_intrazonal_skim(eb, "mfSOVTimeCongVOT4")
        self.calc_intrazonal_skim(eb, "mfHOVTimeCongVOT1")
        self.calc_intrazonal_skim(eb, "mfHOVTimeCongVOT2")
        self.calc_intrazonal_skim(eb, "mfHOVTimeCongVOT3")

        # Calculate Intrazonal Analysis 2
        self.calc_intrazonal_skim(eb, "mfSOVTimeLOSDVOT1")
        self.calc_intrazonal_skim(eb, "mfSOVTimeLOSDVOT2")
        self.calc_intrazonal_skim(eb, "mfSOVTimeLOSDVOT3")
        self.calc_intrazonal_skim(eb, "mfSOVTimeLOSDVOT4")
        self.calc_intrazonal_skim(eb, "mfHOVTimeLOSDVOT1")
        self.calc_intrazonal_skim(eb, "mfHOVTimeLOSDVOT2")
        self.calc_intrazonal_skim(eb, "mfHOVTimeLOSDVOT3")


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

        specs.append(util.matrix_spec(skim_list["sovVot1"][0], "mfSOVTimeCongVOT1"))
        specs.append(util.matrix_spec(skim_list["sovVot2"][0], "mfSOVTimeCongVOT2"))
        specs.append(util.matrix_spec(skim_list["sovVot3"][0], "mfSOVTimeCongVOT3"))
        specs.append(util.matrix_spec(skim_list["sovVot4"][0], "mfSOVTimeCongVOT4"))
        specs.append(util.matrix_spec(skim_list["hovVot1"][0], "mfHOVTimeCongVOT1"))
        specs.append(util.matrix_spec(skim_list["hovVot2"][0], "mfHOVTimeCongVOT2"))
        specs.append(util.matrix_spec(skim_list["hovVot3"][0], "mfHOVTimeCongVOT3"))

        # Analysis 2

        specs.append(util.matrix_spec(skim_list["sovVot1"][1], "mfSOVTimeLOSDVOT1"))
        specs.append(util.matrix_spec(skim_list["sovVot2"][1], "mfSOVTimeLOSDVOT2"))
        specs.append(util.matrix_spec(skim_list["sovVot3"][1], "mfSOVTimeLOSDVOT3"))
        specs.append(util.matrix_spec(skim_list["sovVot4"][1], "mfSOVTimeLOSDVOT4"))
        specs.append(util.matrix_spec(skim_list["hovVot1"][1], "mfHOVTimeLOSDVOT1"))
        specs.append(util.matrix_spec(skim_list["hovVot2"][1], "mfHOVTimeLOSDVOT2"))
        specs.append(util.matrix_spec(skim_list["hovVot3"][1], "mfHOVTimeLOSDVOT3"))


        util.compute_matrix(specs, scenario)

        # now that the skims have been written back, delete the temporary matrices
        for matrix in self.get_temp_matrices():
            util.delmat(scenario.emmebank, matrix[0])

    def add_mode_specification(self, specs, mode, demand, gc_cost, gc_factor, travel_time, link_vol, turn_vol):
        spec = {"mode": mode,
                "demand": demand,
                "generalized_cost": { "link_costs": gc_cost, "perception_factor": gc_factor },
                "results": { "od_travel_times": None,
                             "link_volumes": link_vol,
                             "turn_volumes": turn_vol },
                "path_analyses": []
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

    def add_first_analysis(self, spec):
        path_od = { "considered_paths": "ALL",
                    "multiply_path_proportions_by": { "analyzed_demand": False, "path_value": True }
                  }
        spec["classes"][ 0]["path_analyses"].append({"results": {"od_values": "mfSOVTimeCongVOT1"}, "link_component": "@timeval", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 1]["path_analyses"].append({"results": {"od_values": "mfSOVTimeCongVOT2"}, "link_component": "@timeval", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 2]["path_analyses"].append({"results": {"od_values": "mfSOVTimeCongVOT3"}, "link_component": "@timeval", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 3]["path_analyses"].append({"results": {"od_values": "mfSOVTimeCongVOT4"}, "link_component": "@timeval", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 4]["path_analyses"].append({"results": {"od_values": "mfHOVTimeCongVOT1"}, "link_component": "@timeval", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 5]["path_analyses"].append({"results": {"od_values": "mfHOVTimeCongVOT2"}, "link_component": "@timeval", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 6]["path_analyses"].append({"results": {"od_values": "mfHOVTimeCongVOT3"}, "link_component": "@timeval", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })


    def add_second_analysis(self, spec):
        path_od = { "considered_paths": "ALL",
                    "multiply_path_proportions_by": { "analyzed_demand": False, "path_value": True }
                  }
        spec["classes"][ 0]["path_analyses"].append({"results": {"od_values": "mfSOVTimeLOSDVOT1"}, "link_component": "@timeeff", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 1]["path_analyses"].append({"results": {"od_values": "mfSOVTimeLOSDVOT2"}, "link_component": "@timeeff", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 2]["path_analyses"].append({"results": {"od_values": "mfSOVTimeLOSDVOT3"}, "link_component": "@timeeff", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 3]["path_analyses"].append({"results": {"od_values": "mfSOVTimeLOSDVOT4"}, "link_component": "@timeeff", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 4]["path_analyses"].append({"results": {"od_values": "mfHOVTimeLOSDVOT1"}, "link_component": "@timeeff", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 5]["path_analyses"].append({"results": {"od_values": "mfHOVTimeLOSDVOT2"}, "link_component": "@timeeff", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][ 6]["path_analyses"].append({"results": {"od_values": "mfHOVTimeLOSDVOT3"}, "link_component": "@timeeff", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })


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

        lgv_tollfac = eb.matrix("mslgvTollFac").data
        hgv_tollfac = eb.matrix("mshgvTollFac").data

        util.emme_link_calc(scenario, "@tkpen", "0")
        util.emme_link_calc(scenario, "@tkpen", "length * 100", sel_link="mode=n")
        util.emme_link_calc(scenario, "@sovoc", "length * %s + @tolls" % (auto_voc))
        #TODO: investigate why occupancy is only applied to tolls and not to fixed link costs
        util.emme_link_calc(scenario, "@hovoc", "(length * %s + @tolls) / %s" % (auto_voc, hov_occupancy))
        util.emme_link_calc(scenario, "@lgvoc", "length * %s + %s * @tolls" % (lgv_voc, lgv_tollfac))
        util.emme_link_calc(scenario, "@hgvoc", "length * %s + %s * @tolls + @tkpen" % (hgv_voc, hgv_tollfac))

    def init_matrices(self, eb):
        util = _m.Modeller().tool("translink.util")

        for matrix in self.get_temp_matrices():
            util.initmat(eb, matrix[0], matrix[1], matrix[2], matrix[3])

    def get_temp_matrices(self):
        matrices = []

        matrices.append(["mf9900", "SOVTimeCongVOT1",  "SOV Minutes Cong VOT1", 0])
        matrices.append(["mf9901", "SOVTimeCongVOT2",  "SOV Minutes Cong VOT2", 0])
        matrices.append(["mf9902", "SOVTimeCongVOT3",  "SOV Minutes Cong VOT3", 0])
        matrices.append(["mf9903", "SOVTimeCongVOT4",  "SOV Minutes Cong VOT4", 0])
        matrices.append(["mf9904", "HOVTimeCongVOT1",  "HOV Minutes Cong VOT1", 0])
        matrices.append(["mf9905", "HOVTimeCongVOT2",  "HOV Minutes Cong VOT2", 0])
        matrices.append(["mf9906", "HOVTimeCongVOT3",  "HOV Minutes Cong VOT3", 0])
        matrices.append(["mf9907", "HOVTimeCongVOT4",  "HOV Minutes Cong VOT4", 0])

        matrices.append(["mf9910", "SOVTimeLOSDVOT1",  "SOV Minutes LOSD VOT1", 0])
        matrices.append(["mf9911", "SOVTimeLOSDVOT2",  "SOV Minutes LOSD VOT2", 0])
        matrices.append(["mf9912", "SOVTimeLOSDVOT3",  "SOV Minutes LOSD VOT3", 0])
        matrices.append(["mf9913", "SOVTimeLOSDVOT4",  "SOV Minutes LOSD VOT4", 0])
        matrices.append(["mf9914", "HOVTimeLOSDVOT1",  "HOV Minutes LOSD VOT1", 0])
        matrices.append(["mf9915", "HOVTimeLOSDVOT2",  "HOV Minutes LOSD VOT2", 0])
        matrices.append(["mf9916", "HOVTimeLOSDVOT3",  "HOV Minutes LOSD VOT3", 0])
        matrices.append(["mf9917", "HOVTimeLOSDVOT4",  "HOV Minutes LOSD VOT4", 0])

        matrices.append(["mf9300", "Shortest_Distance",  "Shortest_Distance", 0])

        return matrices
