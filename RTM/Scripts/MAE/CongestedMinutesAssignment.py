##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.congestionassignment
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
    assignment_type = _m.Attribute(int)
    attribute_to_skim =  _m.Attribute(str)

    tool_run_msg = _m.Attribute(unicode)

    def __init__(self):
        self.attribute_to_skim = "timau"
        self.relative_gap = 0.0001
        self.best_relative_gap = 0.01
        self.normalized_gap = 0.005
        self.max_iterations = 250
        self.assignment_type = 1

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Auto Assignment"
        pb.description = "Performs a multi-class auto assignment with " +\
                         "14 classes. An analysis is also performed to calculate " +\
                         "travel on congested links."
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        pb.add_select(tool_attribute_name="assignment_type",keyvalues=[[1,"Regular"],[2,"Social_Optimal"]])

        pb.add_text_box("attribute_to_skim", title="Attribute to Skim:", note="use ul1 for social optimal")
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

            self(eb, self.am_scenario, self.md_scenario, self.pm_scenario, self.attribute_to_skim, self.assignment_type)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Auto Traffic Assignment")
    def __call__(self, eb, am_scenario, md_scenario, pm_scenario, attribute_to_skim, assignment_type):

        util = _m.Modeller().tool("translink.util")

        # make sure we don't overwrite existing scenarios
        am_scenario, md_scenario, pm_scenario = self.losdscenarios(eb, am_scenario, md_scenario, pm_scenario)

        # Initialize skim matrices by time period for congested skims
        util.initmat(eb, "mf9700", "AmSovTimeCongVOT1",  "AM SOV Minutes Cong VOT1", 0)
        util.initmat(eb, "mf9701", "AmSovTimeCongVOT2",  "AM SOV Minutes Cong VOT2", 0)
        util.initmat(eb, "mf9702", "AmSovTimeCongVOT3",  "AM SOV Minutes Cong VOT3", 0)
        util.initmat(eb, "mf9703", "AmSovTimeCongVOT4",  "AM SOV Minutes Cong VOT4", 0)
        util.initmat(eb, "mf9705", "AmHovTimeCongVOT1",  "AM HOV Minutes Cong VOT1", 0)
        util.initmat(eb, "mf9706", "AmHovTimeCongVOT2",  "AM HOV Minutes Cong VOT2", 0)
        util.initmat(eb, "mf9707", "AmHovTimeCongVOT3",  "AM HOV Minutes Cong VOT3", 0)
        util.initmat(eb, "mf9708", "AmHovTimeCongVOT4",  "AM HOV Minutes Cong VOT4", 0)
        util.initmat(eb, "mf9710", "AmLgvTimeCong",      "AM LGV Minutes Cong", 0)
        util.initmat(eb, "mf9711", "AmHgvTimeCong",      "AM HGV Minutes Cong", 0)

        util.initmat(eb, "mf9720", "MdSovTimeCongVOT1",  "MD SOV Minutes Cong VOT1", 0)
        util.initmat(eb, "mf9721", "MdSovTimeCongVOT2",  "MD SOV Minutes Cong VOT2", 0)
        util.initmat(eb, "mf9722", "MdSovTimeCongVOT3",  "MD SOV Minutes Cong VOT3", 0)
        util.initmat(eb, "mf9723", "MdSovTimeCongVOT4",  "MD SOV Minutes Cong VOT4", 0)
        util.initmat(eb, "mf9725", "MdHovTimeCongVOT1",  "MD HOV Minutes Cong VOT1", 0)
        util.initmat(eb, "mf9726", "MdHovTimeCongVOT2",  "MD HOV Minutes Cong VOT2", 0)
        util.initmat(eb, "mf9727", "MdHovTimeCongVOT3",  "MD HOV Minutes Cong VOT3", 0)
        util.initmat(eb, "mf9728", "MdHovTimeCongVOT4",  "MD HOV Minutes Cong VOT4", 0)
        util.initmat(eb, "mf9730", "MdLgvTimeCong",      "MD LGV Minutes Cong", 0)
        util.initmat(eb, "mf9731", "MdHgvTimeCong",      "MD HGV Minutes Cong", 0)


        util.initmat(eb, "mf9740", "PmSovTimeCongVOT1",  "PM SOV Minutes Cong VOT1", 0)
        util.initmat(eb, "mf9741", "PmSovTimeCongVOT2",  "PM SOV Minutes Cong VOT2", 0)
        util.initmat(eb, "mf9742", "PmSovTimeCongVOT3",  "PM SOV Minutes Cong VOT3", 0)
        util.initmat(eb, "mf9743", "PmSovTimeCongVOT4",  "PM SOV Minutes Cong VOT4", 0)
        util.initmat(eb, "mf9745", "PmHovTimeCongVOT1",  "PM HOV Minutes Cong VOT1", 0)
        util.initmat(eb, "mf9746", "PmHovTimeCongVOT2",  "PM HOV Minutes Cong VOT2", 0)
        util.initmat(eb, "mf9747", "PmHovTimeCongVOT3",  "PM HOV Minutes Cong VOT3", 0)
        util.initmat(eb, "mf9748", "PmHovTimeCongVOT4",  "PM HOV Minutes Cong VOT4", 0)
        util.initmat(eb, "mf9750", "PmLgvTimeCong",      "PM LGV Minutes Cong", 0)
        util.initmat(eb, "mf9751", "PmHgvTimeCong",      "PM HGV Minutes Cong", 0)


        # Initialize skim matrices by time period for LOSD
        util.initmat(eb, "mf9760", "AmSovTimeLOSDVOT1",  "AM SOV Minutes LOSD VOT1", 0)
        util.initmat(eb, "mf9761", "AmSovTimeLOSDVOT2",  "AM SOV Minutes LOSD VOT2", 0)
        util.initmat(eb, "mf9762", "AmSovTimeLOSDVOT3",  "AM SOV Minutes LOSD VOT3", 0)
        util.initmat(eb, "mf9763", "AmSovTimeLOSDVOT4",  "AM SOV Minutes LOSD VOT4", 0)
        util.initmat(eb, "mf9765", "AmHovTimeLOSDVOT1",  "AM HOV Minutes LOSD VOT1", 0)
        util.initmat(eb, "mf9766", "AmHovTimeLOSDVOT2",  "AM HOV Minutes LOSD VOT2", 0)
        util.initmat(eb, "mf9767", "AmHovTimeLOSDVOT3",  "AM HOV Minutes LOSD VOT3", 0)
        util.initmat(eb, "mf9768", "AmHovTimeLOSDVOT4",  "AM HOV Minutes LOSD VOT4", 0)
        util.initmat(eb, "mf9770", "AmLgvTimeLOSD",      "AM LGV Minutes LOSD", 0)
        util.initmat(eb, "mf9771", "AmHgvTimeLOSD",      "AM HGV Minutes LOSD", 0)

        util.initmat(eb, "mf9780", "MdSovTimeLOSDVOT1",  "MD SOV Minutes LOSD VOT1", 0)
        util.initmat(eb, "mf9781", "MdSovTimeLOSDVOT2",  "MD SOV Minutes LOSD VOT2", 0)
        util.initmat(eb, "mf9782", "MdSovTimeLOSDVOT3",  "MD SOV Minutes LOSD VOT3", 0)
        util.initmat(eb, "mf9783", "MdSovTimeLOSDVOT4",  "MD SOV Minutes LOSD VOT4", 0)
        util.initmat(eb, "mf9785", "MdHovTimeLOSDVOT1",  "MD HOV Minutes LOSD VOT1", 0)
        util.initmat(eb, "mf9786", "MdHovTimeLOSDVOT2",  "MD HOV Minutes LOSD VOT2", 0)
        util.initmat(eb, "mf9787", "MdHovTimeLOSDVOT3",  "MD HOV Minutes LOSD VOT3", 0)
        util.initmat(eb, "mf9788", "MdHovTimeLOSDVOT4",  "MD HOV Minutes LOSD VOT4", 0)
        util.initmat(eb, "mf9790", "MdLgvTimeLOSD",      "MD LGV Minutes LOSD", 0)
        util.initmat(eb, "mf9791", "MdHgvTimeLOSD",      "MD HGV Minutes LOSD", 0)

        util.initmat(eb, "mf9800", "PmSovTimeLOSDVOT1",  "PM SOV Minutes LOSD VOT1", 0)
        util.initmat(eb, "mf9801", "PmSovTimeLOSDVOT2",  "PM SOV Minutes LOSD VOT2", 0)
        util.initmat(eb, "mf9802", "PmSovTimeLOSDVOT3",  "PM SOV Minutes LOSD VOT3", 0)
        util.initmat(eb, "mf9803", "PmSovTimeLOSDVOT4",  "PM SOV Minutes LOSD VOT4", 0)
        util.initmat(eb, "mf9805", "PmHovTimeLOSDVOT1",  "PM HOV Minutes LOSD VOT1", 0)
        util.initmat(eb, "mf9806", "PmHovTimeLOSDVOT2",  "PM HOV Minutes LOSD VOT2", 0)
        util.initmat(eb, "mf9807", "PmHovTimeLOSDVOT3",  "PM HOV Minutes LOSD VOT3", 0)
        util.initmat(eb, "mf9808", "PmHovTimeLOSDVOT4",  "PM HOV Minutes LOSD VOT4", 0)
        util.initmat(eb, "mf9810", "PmLgvTimeLOSD",      "PM LGV Minutes LOSD", 0)
        util.initmat(eb, "mf9811", "PmHgvTimeLOSD",      "PM HGV Minutes LOSD", 0)

        am_demands = {"sov":   ["mfSOV_drvtrp_VOT_1_Am", "mfSOV_drvtrp_VOT_2_Am", "mfSOV_drvtrp_VOT_3_Am", "mfSOV_drvtrp_VOT_4_Am"],
                      "hov":   ["mfHOV_drvtrp_VOT_1_Am", "mfHOV_drvtrp_VOT_2_Am", "mfHOV_drvtrp_VOT_3_Am"],
                      "truck": ["mflgvPceAm", "mfhgvPceAm"]}
        self.assign_scen(am_scenario, am_demands, attribute_to_skim, assignment_type)
        am_skims = {"sovVot1":  ["mfAmSovTimeCongVOT1", "mfAmSovTimeLOSDVOT1"],
                    "sovVot2":  ["mfAmSovTimeCongVOT2", "mfAmSovTimeLOSDVOT2"],
                    "sovVot3":  ["mfAmSovTimeCongVOT3", "mfAmSovTimeLOSDVOT3"],
                    "sovVot4":  ["mfAmSovTimeCongVOT4", "mfAmSovTimeLOSDVOT4"],
                    "hovVot1":  ["mfAmHovTimeCongVOT1", "mfAmHovTimeLOSDVOT1"],
                    "hovVot2":  ["mfAmHovTimeCongVOT2", "mfAmHovTimeLOSDVOT2"],
                    "hovVot3":  ["mfAmHovTimeCongVOT3", "mfAmHovTimeLOSDVOT3"],
                    "lgv":      ["mfAmLgvTimeCong", "mfAmLgvTimeLOSD"],
                    "hgv":      ["mfAmHgvTimeCong", "mfAmHgvTimeLOSD"]}
        self.store_skims(am_scenario, am_skims)

        md_demands = {"sov":   ["mfSOV_drvtrp_VOT_1_Md", "mfSOV_drvtrp_VOT_2_Md", "mfSOV_drvtrp_VOT_3_Md", "mfSOV_drvtrp_VOT_4_Md"],
                      "hov":   ["mfHOV_drvtrp_VOT_1_Md", "mfHOV_drvtrp_VOT_2_Md", "mfHOV_drvtrp_VOT_3_Md"],
                      "truck": ["mflgvPceMd", "mfhgvPceMd"]}
        self.assign_scen(md_scenario, md_demands, attribute_to_skim, assignment_type)
        md_skims = {"sovVot1":  ["mfMdSovTimeCongVOT1", "mfMdSovTimeLOSDVOT1"],
                    "sovVot2":  ["mfMdSovTimeCongVOT2", "mfMdSovTimeLOSDVOT2"],
                    "sovVot3":  ["mfMdSovTimeCongVOT3", "mfMdSovTimeLOSDVOT3"],
                    "sovVot4":  ["mfMdSovTimeCongVOT4", "mfMdSovTimeLOSDVOT4"],
                    "hovVot1":  ["mfMdHovTimeCongVOT1", "mfMdHovTimeLOSDVOT1"],
                    "hovVot2":  ["mfMdHovTimeCongVOT2", "mfMdHovTimeLOSDVOT2"],
                    "hovVot3":  ["mfMdHovTimeCongVOT3", "mfMdHovTimeLOSDVOT3"],
                    "lgv":      ["mfMdLgvTimeCong", "mfMdLgvTimeLOSD"],
                    "hgv":      ["mfMdHgvTimeCong", "mfMdHgvTimeLOSD"]}
        self.store_skims(md_scenario, md_skims)

        pm_demands = {"sov":   ["mfSOV_drvtrp_VOT_1_Pm", "mfSOV_drvtrp_VOT_2_Pm", "mfSOV_drvtrp_VOT_3_Pm", "mfSOV_drvtrp_VOT_4_Pm"],
                      "hov":   ["mfHOV_drvtrp_VOT_1_Pm", "mfHOV_drvtrp_VOT_2_Pm", "mfHOV_drvtrp_VOT_3_Pm"],
                      "truck": ["mflgvPcePm", "mfhgvPcePm"]}
        self.assign_scen(pm_scenario, pm_demands, attribute_to_skim, assignment_type)
        pm_skims = {"sovVot1":  ["mfPmSovTimeCongVOT1", "mfPmSovTimeLOSDVOT1"],
                    "sovVot2":  ["mfPmSovTimeCongVOT2", "mfPmSovTimeLOSDVOT2"],
                    "sovVot3":  ["mfPmSovTimeCongVOT3", "mfPmSovTimeLOSDVOT3"],
                    "sovVot4":  ["mfPmSovTimeCongVOT4", "mfPmSovTimeLOSDVOT4"],
                    "hovVot1":  ["mfPmHovTimeCongVOT1", "mfPmHovTimeLOSDVOT1"],
                    "hovVot2":  ["mfPmHovTimeCongVOT2", "mfPmHovTimeLOSDVOT2"],
                    "hovVot3":  ["mfPmHovTimeCongVOT3", "mfPmHovTimeLOSDVOT3"],
                    "lgv":      ["mfPmLgvTimeCong", "mfPmLgvTimeLOSD"],
                    "hgv":      ["mfPmHgvTimeCong", "mfPmHgvTimeLOSD"]}
        self.store_skims(pm_scenario, pm_skims)

        ## subtract LOS D from congested skims and zero out intrazonals of FVRD

        self.calc_lost_time(eb)
        self.export_lost_time(eb, am_skims, md_skims, pm_skims)

    def calc_lost_time(self, eb):

        util = _m.Modeller().tool("translink.util")
        specs = []

        # AM
        specs.append(util.matrix_spec("mfAmSovTimeCongVOT1", "(mfAmSovTimeCongVOT1 - mfAmSovTimeLOSDVOT1)"))
        specs.append(util.matrix_spec("mfAmSovTimeCongVOT2", "(mfAmSovTimeCongVOT2 - mfAmSovTimeLOSDVOT2)"))
        specs.append(util.matrix_spec("mfAmSovTimeCongVOT3", "(mfAmSovTimeCongVOT3 - mfAmSovTimeLOSDVOT3)"))
        specs.append(util.matrix_spec("mfAmSovTimeCongVOT4", "(mfAmSovTimeCongVOT4 - mfAmSovTimeLOSDVOT4)"))
        specs.append(util.matrix_spec("mfAmHovTimeCongVOT1", "(mfAmHovTimeCongVOT1 - mfAmHovTimeLOSDVOT1)"))
        specs.append(util.matrix_spec("mfAmHovTimeCongVOT2", "(mfAmHovTimeCongVOT2 - mfAmHovTimeLOSDVOT2)"))
        specs.append(util.matrix_spec("mfAmHovTimeCongVOT3", "(mfAmHovTimeCongVOT3 - mfAmHovTimeLOSDVOT3)"))
        specs.append(util.matrix_spec("mfAmLgvTimeCong", "(mfAmLgvTimeCong - mfAmLgvTimeLOSD)"))
        specs.append(util.matrix_spec("mfAmHgvTimeCong", "(mfAmHgvTimeCong - mfAmHgvTimeLOSD)"))

        # MD
        specs.append(util.matrix_spec("mfMdSovTimeCongVOT1", "(mfMdSovTimeCongVOT1 - mfMdSovTimeLOSDVOT1)"))
        specs.append(util.matrix_spec("mfMdSovTimeCongVOT2", "(mfMdSovTimeCongVOT2 - mfMdSovTimeLOSDVOT2)"))
        specs.append(util.matrix_spec("mfMdSovTimeCongVOT3", "(mfMdSovTimeCongVOT3 - mfMdSovTimeLOSDVOT3)"))
        specs.append(util.matrix_spec("mfMdSovTimeCongVOT4", "(mfMdSovTimeCongVOT4 - mfMdSovTimeLOSDVOT4)"))
        specs.append(util.matrix_spec("mfMdHovTimeCongVOT1", "(mfMdHovTimeCongVOT1 - mfMdHovTimeLOSDVOT1)"))
        specs.append(util.matrix_spec("mfMdHovTimeCongVOT2", "(mfMdHovTimeCongVOT2 - mfMdHovTimeLOSDVOT2)"))
        specs.append(util.matrix_spec("mfMdHovTimeCongVOT3", "(mfMdHovTimeCongVOT3 - mfMdHovTimeLOSDVOT3)"))
        specs.append(util.matrix_spec("mfMdLgvTimeCong", "(mfMdLgvTimeCong - mfMdLgvTimeLOSD)"))
        specs.append(util.matrix_spec("mfMdHgvTimeCong", "(mfMdHgvTimeCong - mfMdHgvTimeLOSD)"))

        # PM
        specs.append(util.matrix_spec("mfPmSovTimeCongVOT1", "(mfPmSovTimeCongVOT1 - mfPmSovTimeLOSDVOT1)"))
        specs.append(util.matrix_spec("mfPmSovTimeCongVOT2", "(mfPmSovTimeCongVOT2 - mfPmSovTimeLOSDVOT2)"))
        specs.append(util.matrix_spec("mfPmSovTimeCongVOT3", "(mfPmSovTimeCongVOT3 - mfPmSovTimeLOSDVOT3)"))
        specs.append(util.matrix_spec("mfPmSovTimeCongVOT4", "(mfPmSovTimeCongVOT4 - mfPmSovTimeLOSDVOT4)"))
        specs.append(util.matrix_spec("mfPmHovTimeCongVOT1", "(mfPmHovTimeCongVOT1 - mfPmHovTimeLOSDVOT1)"))
        specs.append(util.matrix_spec("mfPmHovTimeCongVOT2", "(mfPmHovTimeCongVOT2 - mfPmHovTimeLOSDVOT2)"))
        specs.append(util.matrix_spec("mfPmHovTimeCongVOT3", "(mfPmHovTimeCongVOT3 - mfPmHovTimeLOSDVOT3)"))
        specs.append(util.matrix_spec("mfPmLgvTimeCong", "(mfPmLgvTimeCong - mfPmLgvTimeLOSD)"))
        specs.append(util.matrix_spec("mfPmHgvTimeCong", "(mfPmHgvTimeCong - mfPmHgvTimeLOSD)"))

        util.compute_matrix(specs)

    def assign_scen(self, scenario, demands, attribute_to_skim, assignment_type):
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
        util.emme_link_calc(scenario, "@timeval", "(@gvrdbin * %s)" % (attribute_to_skim))

#        util.emme_link_calc(scenario, "@timeval", "40", sel_link = "vdf = 2")

        # undertake a dummy assignment with only background traffic at 85% of the volume (LOS D)
        # Calculate volume = 85% of capacity on the network and store it in ul3

        if assignment_type == 1:
            util.emme_link_calc(scenario, "ul3", "0")
            util.emme_link_calc(scenario, "ul3", "100", sel_link="vdf = 2")
            util.emme_link_calc(scenario, "ul3", "0.85*200*vdf*lanes", sel_link="vdf = 3,7")
            util.emme_link_calc(scenario, "ul3", "0.85*200*int(vdf/10)*lanes", sel_link="vdf = 20,79")
            util.emme_link_calc(scenario, "ul3", "0.85*1600*(lanes^1.05)", sel_link="vdf = 85")
            util.emme_link_calc(scenario, "ul3", "0.85*1600*(lanes^1.05)", sel_link="vdf = 88")

        if assignment_type == 2:
            util.emme_link_calc(scenario, "ul3", "0")
            util.emme_link_calc(scenario, "ul3", "100", sel_link="vdf = 2")
            util.emme_link_calc(scenario, "ul3", "0.85*200*(vdf-10)*lanes*(1/6)^(1/5)", sel_link="vdf = 13,17")
            util.emme_link_calc(scenario, "ul3", "0.85*200*int(vdf/10)*lanes*(1/5)^(1/4)", sel_link="vdf = 20,79")
            util.emme_link_calc(scenario, "ul3", "0.85*1600*(lanes^1.05)*(1/6)^(1/5)", sel_link="vdf = 86")
            util.emme_link_calc(scenario, "ul3", "0.85*1600*(lanes^1.05)*(1/6.25)^(1/5.25)", sel_link="vdf = 89")

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
                                        "od_travel_times": None
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
#        util.emme_link_calc(scenario, "@timeeff", "40", sel_link = "vdf = 2")


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
        self.calc_intrazonal_skim(eb, "mfSovTimeCongVOT1")
        self.calc_intrazonal_skim(eb, "mfSovTimeCongVOT2")
        self.calc_intrazonal_skim(eb, "mfSovTimeCongVOT3")
        self.calc_intrazonal_skim(eb, "mfSovTimeCongVOT4")
        self.calc_intrazonal_skim(eb, "mfHovTimeCongVOT1")
        self.calc_intrazonal_skim(eb, "mfHovTimeCongVOT2")
        self.calc_intrazonal_skim(eb, "mfHovTimeCongVOT3")
        self.calc_intrazonal_skim(eb, "mfLgvTimeCong")
        self.calc_intrazonal_skim(eb, "mfHgvTimeCong")


        # Calculate Intrazonal Analysis 2
        self.calc_intrazonal_skim(eb, "mfSovTimeLOSDVOT1")
        self.calc_intrazonal_skim(eb, "mfSovTimeLOSDVOT2")
        self.calc_intrazonal_skim(eb, "mfSovTimeLOSDVOT3")
        self.calc_intrazonal_skim(eb, "mfSovTimeLOSDVOT4")
        self.calc_intrazonal_skim(eb, "mfHovTimeLOSDVOT1")
        self.calc_intrazonal_skim(eb, "mfHovTimeLOSDVOT2")
        self.calc_intrazonal_skim(eb, "mfHovTimeLOSDVOT3")
        self.calc_intrazonal_skim(eb, "mfLgvTimeLOSD")
        self.calc_intrazonal_skim(eb, "mfHgvTimeLOSD")



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

        specs.append(util.matrix_spec(skim_list["sovVot1"][0], "mfSovTimeCongVOT1"))
        specs.append(util.matrix_spec(skim_list["sovVot2"][0], "mfSovTimeCongVOT2"))
        specs.append(util.matrix_spec(skim_list["sovVot3"][0], "mfSovTimeCongVOT3"))
        specs.append(util.matrix_spec(skim_list["sovVot4"][0], "mfSovTimeCongVOT4"))
        specs.append(util.matrix_spec(skim_list["hovVot1"][0], "mfHovTimeCongVOT1"))
        specs.append(util.matrix_spec(skim_list["hovVot2"][0], "mfHovTimeCongVOT2"))
        specs.append(util.matrix_spec(skim_list["hovVot3"][0], "mfHovTimeCongVOT3"))
        specs.append(util.matrix_spec(skim_list["lgv"][0], "mfLgvTimeCong"))
        specs.append(util.matrix_spec(skim_list["hgv"][0], "mfHgvTimeCong"))


        # Analysis 2

        specs.append(util.matrix_spec(skim_list["sovVot1"][1], "mfSovTimeLOSDVOT1"))
        specs.append(util.matrix_spec(skim_list["sovVot2"][1], "mfSovTimeLOSDVOT2"))
        specs.append(util.matrix_spec(skim_list["sovVot3"][1], "mfSovTimeLOSDVOT3"))
        specs.append(util.matrix_spec(skim_list["sovVot4"][1], "mfSovTimeLOSDVOT4"))
        specs.append(util.matrix_spec(skim_list["hovVot1"][1], "mfHovTimeLOSDVOT1"))
        specs.append(util.matrix_spec(skim_list["hovVot2"][1], "mfHovTimeLOSDVOT2"))
        specs.append(util.matrix_spec(skim_list["hovVot3"][1], "mfHovTimeLOSDVOT3"))
        specs.append(util.matrix_spec(skim_list["lgv"][1], "mfLgvTimeLOSD"))
        specs.append(util.matrix_spec(skim_list["hgv"][1], "mfHgvTimeLOSD"))

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
        spec["classes"][0]["path_analyses"].append({"results": {"od_values": "mfSovTimeCongVOT1"}, "link_component": "@timeval", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][1]["path_analyses"].append({"results": {"od_values": "mfSovTimeCongVOT2"}, "link_component": "@timeval", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][2]["path_analyses"].append({"results": {"od_values": "mfSovTimeCongVOT3"}, "link_component": "@timeval", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][3]["path_analyses"].append({"results": {"od_values": "mfSovTimeCongVOT4"}, "link_component": "@timeval", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][4]["path_analyses"].append({"results": {"od_values": "mfHovTimeCongVOT1"}, "link_component": "@timeval", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][5]["path_analyses"].append({"results": {"od_values": "mfHovTimeCongVOT2"}, "link_component": "@timeval", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][6]["path_analyses"].append({"results": {"od_values": "mfHovTimeCongVOT3"}, "link_component": "@timeval", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][7]["path_analyses"].append({"results": {"od_values": "mfLgvTimeCong"},     "link_component": "@timeval", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][8]["path_analyses"].append({"results": {"od_values": "mfHgvTimeCong"},     "link_component": "@timeval", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })

    def add_second_analysis(self, spec):
        path_od = { "considered_paths": "ALL",
                    "multiply_path_proportions_by": { "analyzed_demand": False, "path_value": True }
                  }
        spec["classes"][0]["path_analyses"].append({"results": {"od_values": "mfSovTimeLOSDVOT1"}, "link_component": "@timeeff", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][1]["path_analyses"].append({"results": {"od_values": "mfSovTimeLOSDVOT2"}, "link_component": "@timeeff", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][2]["path_analyses"].append({"results": {"od_values": "mfSovTimeLOSDVOT3"}, "link_component": "@timeeff", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][3]["path_analyses"].append({"results": {"od_values": "mfSovTimeLOSDVOT4"}, "link_component": "@timeeff", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][4]["path_analyses"].append({"results": {"od_values": "mfHovTimeLOSDVOT1"}, "link_component": "@timeeff", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][5]["path_analyses"].append({"results": {"od_values": "mfHovTimeLOSDVOT2"}, "link_component": "@timeeff", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][6]["path_analyses"].append({"results": {"od_values": "mfHovTimeLOSDVOT3"}, "link_component": "@timeeff", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][7]["path_analyses"].append({"results": {"od_values": "mfLgvTimeLOSD"},     "link_component": "@timeeff", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })
        spec["classes"][8]["path_analyses"].append({"results": {"od_values": "mfHgvTimeLOSD"},     "link_component": "@timeeff", "operator": "+", "path_to_od_composition": path_od, "selection_threshold": {"lower": 0.00, "upper": 99999} })


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

        matrices.append(["mf9900", "SovTimeCongVOT1",  "SOV Minutes Cong VOT1", 0])
        matrices.append(["mf9901", "SovTimeCongVOT2",  "SOV Minutes Cong VOT2", 0])
        matrices.append(["mf9902", "SovTimeCongVOT3",  "SOV Minutes Cong VOT3", 0])
        matrices.append(["mf9903", "SovTimeCongVOT4",  "SOV Minutes Cong VOT4", 0])
        matrices.append(["mf9904", "HovTimeCongVOT1",  "HOV Minutes Cong VOT1", 0])
        matrices.append(["mf9905", "HovTimeCongVOT2",  "HOV Minutes Cong VOT2", 0])
        matrices.append(["mf9906", "HovTimeCongVOT3",  "HOV Minutes Cong VOT3", 0])
        matrices.append(["mf9907", "HovTimeCongVOT4",  "HOV Minutes Cong VOT4", 0])
        matrices.append(["mf9908", "LgvTimeCong",  "LGV Minutes Cong", 0])
        matrices.append(["mf9909", "HgvTimeCong",  "HGV Minutes Cong", 0])


        matrices.append(["mf9910", "SovTimeLOSDVOT1",  "SOV Minutes LOSD VOT1", 0])
        matrices.append(["mf9911", "SovTimeLOSDVOT2",  "SOV Minutes LOSD VOT2", 0])
        matrices.append(["mf9912", "SovTimeLOSDVOT3",  "SOV Minutes LOSD VOT3", 0])
        matrices.append(["mf9913", "SovTimeLOSDVOT4",  "SOV Minutes LOSD VOT4", 0])
        matrices.append(["mf9914", "HovTimeLOSDVOT1",  "HOV Minutes LOSD VOT1", 0])
        matrices.append(["mf9915", "HovTimeLOSDVOT2",  "HOV Minutes LOSD VOT2", 0])
        matrices.append(["mf9916", "HovTimeLOSDVOT3",  "HOV Minutes LOSD VOT3", 0])
        matrices.append(["mf9917", "HovTimeLOSDVOT4",  "HOV Minutes LOSD VOT4", 0])
        matrices.append(["mf9918", "LgvTimeLOSD",  "LGV Minutes LOSD", 0])
        matrices.append(["mf9919", "HgvTimeLOSD",  "HGV Minutes LOSD", 0])

        return matrices

    def losdscenarios(self, eb, am_scenario, md_scenario, pm_scenario):
        copy_scenario = _m.Modeller().tool("inro.emme.data.scenario.copy_scenario")
        # create_scenarios = _m.Modeller().tool("translink.RTM3.stage0.create_scenarios")

         # Copy to new AM Scenarios
        am_scenid = am_scenario.number + 200
        copy_scenario(from_scenario=am_scenario,
                    scenario_id=am_scenid,
                    scenario_title="{} Los D Assignment".format(am_scenario.title),
                    overwrite=True,
                    copy_strategies=False)
        amscen_out = eb.scenario(am_scenid)


        # Copy to new MD Scenarios
        md_scenid = md_scenario.number + 200
        copy_scenario(from_scenario=md_scenario,
                    scenario_id=md_scenid,
                    scenario_title="{} Los D Assignment".format(md_scenario.title),
                    overwrite=True,
                    copy_strategies=False)
        mdscen_out = eb.scenario(md_scenid)


        # Copy to new pm Scenarios
        pm_scenid = pm_scenario.number + 200
        copy_scenario(from_scenario=pm_scenario,
                    scenario_id=pm_scenid,
                    scenario_title="{} Los D Assignment".format(pm_scenario.title),
                    overwrite=True,
                    copy_strategies=False)
        pmscen_out = eb.scenario(pm_scenid)

        return amscen_out, mdscen_out, pmscen_out

    def export_lost_time(self, eb, am_skims, md_skims, pm_skims):
        import os
        import numpy as np
        util = _m.Modeller().tool("translink.util")
        export_dict = {}
        for skim_list in [am_skims, md_skims, pm_skims]: # iterate through time of day skim_list
            for key in skim_list:
                if "Vot" in key: # filter out LGV and HGV
                    matrix_name = skim_list[key][0][2:].upper() # convert matrix naming to all uppercase
                    export_dict[matrix_name] = util.get_matrix_numpy(eb, skim_list[key][0]) # save numpy array into export dictrionary
        out_path = os.path.join(util.get_eb_path(_m.Modeller().emmebank), 'EconomicAnalysis')
        if not os.path.exists(out_path): #initialize tripsim folder if it does not exist
            os.makedirs(out_path)
        OutputFile = os.path.join(out_path,'TIMECONG.npz') # save export dictionary as npz file on disk
        np.savez_compressed(OutputFile, **export_dict)
