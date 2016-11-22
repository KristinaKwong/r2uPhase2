##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step6.autoassignment
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
            #TODO: set ms4X matrices based on user input
            self(self.am_scenario, self.md_scenario, self.pm_scenario)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("06-01 - Auto Assignment")
    def __call__(self, scenarioam, scenariomd, scenariopm):
        self.auto_assignment(scenarioam, scenariomd, scenariopm)

    @_m.logbook_trace("Auto Traffic Assignment")
    def auto_assignment(self, am_scenario, md_scenario, pm_scenario):
        am_demands = {"sov":   ["mf300", "mf301", "mf302", "mf303", "mf304", "mf305"],
                      "hov":   ["mf306", "mf307", "mf308", "mf309", "mf310", "mf311"],
                      "truck": ["mf312", "mf313"]}
        self.assign_scen(am_scenario, am_demands)
        am_skims = {"sovWk":  ["mf5000", "mf5001", "mf5002"],
                    "sovNwk": ["mf5003", "mf5004", "mf5005"],
                    "hovWk":  ["mf5006", "mf5007", "mf5008"],
                    "hovNwk": ["mf5009", "mf5010", "mf5011"]}
        self.store_skims(am_scenario, am_skims)

        md_demands = {"sov":   ["mf320", "mf321", "mf322", "mf323", "mf324", "mf325"],
                      "hov":   ["mf326", "mf327", "mf328", "mf329", "mf330", "mf331"],
                      "truck": ["mf332", "mf333"]}
        self.assign_scen(md_scenario, md_demands)
        md_skims = {"sovWk":  ["mf5020", "mf5021", "mf5022"],
                    "sovNwk": ["mf5023", "mf5024", "mf5025"],
                    "hovWk":  ["mf5026", "mf5027", "mf5028"],
                    "hovNwk": ["mf5029", "mf5030", "mf5031"]}
        self.store_skims(md_scenario, md_skims)
        pm_demands = {"sov":   ["mf340", "mf341", "mf342", "mf343", "mf344", "mf345"],
                      "hov":   ["mf346", "mf347", "mf348", "mf349", "mf350", "mf351"],
                      "truck": ["mf352", "mf353"]}
        self.assign_scen(pm_scenario, pm_demands)
        pm_skims = {"sovWk":  ["mf5040", "mf5041", "mf5042"],
                    "sovNwk": ["mf5043", "mf5044", "mf5045"],
                    "hovWk":  ["mf5046", "mf5047", "mf5048"],
                    "hovNwk": ["mf5049", "mf5050", "mf5051"]}
        self.store_skims(pm_scenario, pm_skims)

    def assign_scen(self, scenario, demands):
        assign_traffic = _m.Modeller().tool("inro.emme.traffic_assignment.sola_traffic_assignment")

        self.calc_network_costs(scenario)
        self.calc_transit_costs(scenario)
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
        self.calc_intrazonal_skim(eb, "mf9900")
        self.calc_intrazonal_skim(eb, "mf9901")
        self.calc_intrazonal_skim(eb, "mf9902")
        self.calc_intrazonal_skim(eb, "mf9903")
        self.calc_intrazonal_skim(eb, "mf9904")
        self.calc_intrazonal_skim(eb, "mf9905")
        self.calc_intrazonal_skim(eb, "mf9906")
        self.calc_intrazonal_skim(eb, "mf9907")
        self.calc_intrazonal_skim(eb, "mf9908")
        self.calc_intrazonal_skim(eb, "mf9909")
        self.calc_intrazonal_skim(eb, "mf9910")
        self.calc_intrazonal_skim(eb, "mf9911")
        self.calc_intrazonal_skim(eb, "mf9912")
        self.calc_intrazonal_skim(eb, "mf9913")

        # Calculate Intrazonal Distance
        self.calc_intrazonal_skim(eb, "mf9920")
        self.calc_intrazonal_skim(eb, "mf9921")
        self.calc_intrazonal_skim(eb, "mf9922")
        self.calc_intrazonal_skim(eb, "mf9923")
        self.calc_intrazonal_skim(eb, "mf9924")
        self.calc_intrazonal_skim(eb, "mf9925")
        self.calc_intrazonal_skim(eb, "mf9926")
        self.calc_intrazonal_skim(eb, "mf9927")
        self.calc_intrazonal_skim(eb, "mf9928")
        self.calc_intrazonal_skim(eb, "mf9929")
        self.calc_intrazonal_skim(eb, "mf9930")
        self.calc_intrazonal_skim(eb, "mf9931")
        self.calc_intrazonal_skim(eb, "mf9932")
        self.calc_intrazonal_skim(eb, "mf9933")

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
        specs.append(util.matrix_spec( skim_list["sovWk"][0], "mf9921"))
        specs.append(util.matrix_spec(skim_list["sovNwk"][0], "mf9924"))
        specs.append(util.matrix_spec( skim_list["hovWk"][0], "mf9927"))
        specs.append(util.matrix_spec(skim_list["hovNwk"][0], "mf9930"))
        # Set GC Time Matrices
        specs.append(util.matrix_spec( skim_list["sovWk"][1], "mf9901"))
        specs.append(util.matrix_spec(skim_list["sovNwk"][1], "mf9904"))
        specs.append(util.matrix_spec( skim_list["hovWk"][1], "mf9907"))
        specs.append(util.matrix_spec(skim_list["hovNwk"][1], "mf9910"))
        # Set GC Toll Matrices
        specs.append(util.matrix_spec( skim_list["sovWk"][2], "mf9941"))
        specs.append(util.matrix_spec(skim_list["sovNwk"][2], "mf9944"))
        specs.append(util.matrix_spec( skim_list["hovWk"][2], "mf9947"))
        specs.append(util.matrix_spec(skim_list["hovNwk"][2], "mf9950"))

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
        self.add_mode_specification(all_classes, "d", demand_matrices["sov"][0], "@sovoc", eb.matrix("ms200").data, "mf9900", "@sov1", "@tsov1")
        self.add_mode_specification(all_classes, "d", demand_matrices["sov"][1], "@sovoc", eb.matrix("ms201").data, "mf9901", "@sov2", "@tsov2")
        self.add_mode_specification(all_classes, "d", demand_matrices["sov"][2], "@sovoc", eb.matrix("ms202").data, "mf9902", "@sov3", "@tsov3")
        self.add_mode_specification(all_classes, "d", demand_matrices["sov"][3], "@sovoc", eb.matrix("ms206").data, "mf9903", "@sov4", "@tsov4")
        self.add_mode_specification(all_classes, "d", demand_matrices["sov"][4], "@sovoc", eb.matrix("ms207").data, "mf9904", "@sov5", "@tsov5")
        self.add_mode_specification(all_classes, "d", demand_matrices["sov"][5], "@sovoc", eb.matrix("ms208").data, "mf9905", "@sov6", "@tsov6")
        # HOV Classes
        self.add_mode_specification(all_classes, "c", demand_matrices["hov"][0], "@hovoc", eb.matrix("ms203").data, "mf9906", "@hov1", "@thov1")
        self.add_mode_specification(all_classes, "c", demand_matrices["hov"][1], "@hovoc", eb.matrix("ms204").data, "mf9907", "@hov2", "@thov2")
        self.add_mode_specification(all_classes, "c", demand_matrices["hov"][2], "@hovoc", eb.matrix("ms205").data, "mf9908", "@hov3", "@thov3")
        self.add_mode_specification(all_classes, "c", demand_matrices["hov"][3], "@hovoc", eb.matrix("ms209").data, "mf9909", "@hov4", "@thov4")
        self.add_mode_specification(all_classes, "c", demand_matrices["hov"][4], "@hovoc", eb.matrix("ms210").data, "mf9910", "@hov5", "@thov5")
        self.add_mode_specification(all_classes, "c", demand_matrices["hov"][5], "@hovoc", eb.matrix("ms211").data, "mf9911", "@hov6", "@thov6")
        # Truck Classes
        self.add_mode_specification(all_classes, "x", demand_matrices["truck"][0], "@lgvoc", eb.matrix("ms218").data, "mf9912", "@lgvol", "@lgvtn")
        self.add_mode_specification(all_classes, "t", demand_matrices["truck"][1], "@hgvoc", eb.matrix("ms219").data, "mf9913", "@hgvol", "@hgvtn")

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
        spec["classes"][ 0]["analysis"] = {"results": {"od_values": "mf9920"}}
        spec["classes"][ 1]["analysis"] = {"results": {"od_values": "mf9921"}}
        spec["classes"][ 2]["analysis"] = {"results": {"od_values": "mf9922"}}
        spec["classes"][ 3]["analysis"] = {"results": {"od_values": "mf9923"}}
        spec["classes"][ 4]["analysis"] = {"results": {"od_values": "mf9924"}}
        spec["classes"][ 5]["analysis"] = {"results": {"od_values": "mf9925"}}
        spec["classes"][ 6]["analysis"] = {"results": {"od_values": "mf9926"}}
        spec["classes"][ 7]["analysis"] = {"results": {"od_values": "mf9927"}}
        spec["classes"][ 8]["analysis"] = {"results": {"od_values": "mf9928"}}
        spec["classes"][ 9]["analysis"] = {"results": {"od_values": "mf9929"}}
        spec["classes"][10]["analysis"] = {"results": {"od_values": "mf9930"}}
        spec["classes"][11]["analysis"] = {"results": {"od_values": "mf9931"}}
        spec["classes"][12]["analysis"] = {"results": {"od_values": "mf9932"}}
        spec["classes"][13]["analysis"] = {"results": {"od_values": "mf9933"}}

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
        spec["classes"][ 0]["analysis"] = {"results": {"od_values": "mf9940"}}
        spec["classes"][ 1]["analysis"] = {"results": {"od_values": "mf9941"}}
        spec["classes"][ 2]["analysis"] = {"results": {"od_values": "mf9942"}}
        spec["classes"][ 3]["analysis"] = {"results": {"od_values": "mf9943"}}
        spec["classes"][ 4]["analysis"] = {"results": {"od_values": "mf9944"}}
        spec["classes"][ 5]["analysis"] = {"results": {"od_values": "mf9945"}}
        spec["classes"][ 6]["analysis"] = {"results": {"od_values": "mf9946"}}
        spec["classes"][ 7]["analysis"] = {"results": {"od_values": "mf9947"}}
        spec["classes"][ 8]["analysis"] = {"results": {"od_values": "mf9948"}}
        spec["classes"][ 9]["analysis"] = {"results": {"od_values": "mf9949"}}
        spec["classes"][10]["analysis"] = {"results": {"od_values": "mf9950"}}
        spec["classes"][11]["analysis"] = {"results": {"od_values": "mf9951"}}
        spec["classes"][12]["analysis"] = {"results": {"od_values": "mf9952"}}
        spec["classes"][13]["analysis"] = {"results": {"od_values": "mf9953"}}

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

    @_m.logbook_trace("Calculate Fixed Transit Line Costs")
    def calc_transit_costs(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")

        #TODO Move the headway calculations to the transit assignment module
        # KB: why are the transit heady calculations in the traffic assignment tool ??????

        # Calculate effective headway based on
        # 0-10 minutes 0.5
        # 10-20 minutes 0.4
        # 20-30 minutes 0.3
        # > 30 minutes 0.1
        util.emme_tline_calc(scenario, "ut2", "hdw*0.5", sel_line="hdw=0,10")
        util.emme_tline_calc(scenario, "ut2", "5 +  (hdw-10)*0.4", sel_line="hdw=10,20")
        util.emme_tline_calc(scenario, "ut2", "9 +  (hdw-20)*0.3", sel_line="hdw=20,30")
        util.emme_tline_calc(scenario, "ut2", "12 + (hdw-30)*0.1", sel_line="hdw=30,999")

        #TODO confirm this is the correct approach with INRO
        # doing this explicitly now.  Need to double the headway to use 0.5 headway fraction in assignment
        # for stops with only one service this will return to the effective headway as calculated above
        # for stops with multiple services, this will assume a random arrival of vehicles at the stops
        # it may make more sense to
        util.emme_tline_calc(scenario, "ut2", "ut2*2")

        ## Calculate perception of headways based on following factors:
        ##        "l" rail=0.8,
        ##        "b" bus=1.2,
        ##        "s" seabus=0.67,
        ##        "g" BRT=1.1,
        ##        "f" LRT=1.1,
        ##        "h" Gondola=0.8,
        ##        "r" WCE=0.8
        util.emme_tline_calc(scenario, "ut1", "ut2*1.2",  sel_line="mode=b")
        util.emme_tline_calc(scenario, "ut1", "ut2*0.8",  sel_line="mode=l")
        util.emme_tline_calc(scenario, "ut1", "ut2*0.67", sel_line="mode=s")
        util.emme_tline_calc(scenario, "ut1", "ut2*1.1",  sel_line="mode=f")
        util.emme_tline_calc(scenario, "ut1", "ut2*1.1",  sel_line="mode=g")
        util.emme_tline_calc(scenario, "ut1", "ut2*0.8",  sel_line="mode=h")
        util.emme_tline_calc(scenario, "ut1", "ut2*0.8",  sel_line="mode=r")

        ## Calculate in vehicle traval time perception factors
        util.emme_tline_calc(scenario, "@ivttp", "1")
        util.emme_tline_calc(scenario, "@ivttp", "3.5", sel_line="mode=b")
        util.emme_tline_calc(scenario, "@ivttp", "3.5", sel_line="mode=g")

    def init_matrices(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        util.initmat(eb, "mf9900", "SOVTimeWkL",  "SOV Time Work Low Income",     0)
        util.initmat(eb, "mf9901", "SOVTimeWkM",  "SOV Time Work Med Income",     0)
        util.initmat(eb, "mf9902", "SOVTimeWkH",  "SOV Time Work High Income",    0)
        util.initmat(eb, "mf9903", "SOVTimeNwkL", "SOV Time NonWork Low Income",  0)
        util.initmat(eb, "mf9904", "SOVTimeNwkM", "SOV Time NonWork Med Income",  0)
        util.initmat(eb, "mf9905", "SOVTimeNwkH", "SOV Time NonWork High Income", 0)
        util.initmat(eb, "mf9906", "HOVTimeWkL",  "HOV Time Work Low Income",     0)
        util.initmat(eb, "mf9907", "HOVTimeWkM",  "HOV Time Work Med Income",     0)
        util.initmat(eb, "mf9908", "HOVTimeWkH",  "HOV Time Work High Income",    0)
        util.initmat(eb, "mf9909", "HOVTimeNwkL", "HOV Time NonWork Low Income",  0)
        util.initmat(eb, "mf9910", "HOVTimeNwkM", "HOV Time NonWork Med Income",  0)
        util.initmat(eb, "mf9911", "HOVTimeNwkH", "HOV Time NonWork High Income", 0)
        util.initmat(eb, "mf9912", "LGVTime",     "LGV Time", 0)
        util.initmat(eb, "mf9913", "HGVTime",     "HGV Time", 0)

        util.initmat(eb, "mf9920", "SOVDistWkL",  "SOV Distance Work Low Income",     0)
        util.initmat(eb, "mf9921", "SOVDistWkM",  "SOV Distance Work Med Income",     0)
        util.initmat(eb, "mf9922", "SOVDistWkH",  "SOV Distance Work High Income",    0)
        util.initmat(eb, "mf9923", "SOVDistNwkL", "SOV Distance NonWork Low Income",  0)
        util.initmat(eb, "mf9924", "SOVDistNwkM", "SOV Distance NonWork Med Income",  0)
        util.initmat(eb, "mf9925", "SOVDistNwkH", "SOV Distance NonWork High Income", 0)
        util.initmat(eb, "mf9926", "HOVDistWkL",  "HOV Distance Work Low Income",     0)
        util.initmat(eb, "mf9927", "HOVDistWkM",  "HOV Distance Work Med Income",     0)
        util.initmat(eb, "mf9928", "HOVDistWkH",  "HOV Distance Work High Income",    0)
        util.initmat(eb, "mf9929", "HOVDistNwkL", "HOV Distance NonWork Low Income",  0)
        util.initmat(eb, "mf9930", "HOVDistNwkM", "HOV Distance NonWork Med Income",  0)
        util.initmat(eb, "mf9931", "HOVDistNwkH", "HOV Distance NonWork High Income", 0)
        util.initmat(eb, "mf9932", "LGVDist",     "LGV Distance", 0)
        util.initmat(eb, "mf9933", "HGVDist",     "HGV Distance", 0)

        util.initmat(eb, "mf9940", "SOVTollWkL",  "SOV Toll Work Low Income",     0)
        util.initmat(eb, "mf9941", "SOVTollWkM",  "SOV Toll Work Med Income",     0)
        util.initmat(eb, "mf9942", "SOVTollWkH",  "SOV Toll Work High Income",    0)
        util.initmat(eb, "mf9943", "SOVTollNwkL", "SOV Toll NonWork Low Income",  0)
        util.initmat(eb, "mf9944", "SOVTollNwkM", "SOV Toll NonWork Med Income",  0)
        util.initmat(eb, "mf9945", "SOVTollNwkH", "SOV Toll NonWork High Income", 0)
        util.initmat(eb, "mf9946", "HOVTollWkL",  "HOV Toll Work Low Income",     0)
        util.initmat(eb, "mf9947", "HOVTollWkM",  "HOV Toll Work Med Income",     0)
        util.initmat(eb, "mf9948", "HOVTollWkH",  "HOV Toll Work High Income",    0)
        util.initmat(eb, "mf9949", "HOVTollNwkL", "HOV Toll NonWork Low Income",  0)
        util.initmat(eb, "mf9950", "HOVTollNwkM", "HOV Toll NonWork Med Income",  0)
        util.initmat(eb, "mf9951", "HOVTollNwkH", "HOV Toll NonWork High Income", 0)
        util.initmat(eb, "mf9952", "LGVToll",     "LGV Toll", 0)
        util.initmat(eb, "mf9953", "HGVToll",     "HGV Toll", 0)
