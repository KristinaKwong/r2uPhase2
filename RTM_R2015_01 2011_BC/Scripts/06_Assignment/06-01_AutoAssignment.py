##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
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
                         "12 classes. An analysis is also performed to calculate " +\
                         "auto distance and auto time."
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        pb.add_select_scenario("am_scenario", title="AM scenario:")
        pb.add_select_scenario("md_scenario", title="Midday scenario:")
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
            stopping_criteria = {
                "relative_gap": self.relative_gap,
                "best_relative_gap": self.best_relative_gap,
                "normalized_gap": self.normalized_gap,
                "max_iterations": self.max_iterations
            }
            self(_m.Modeller().emmebank, self.am_scenario, self.md_scenario, self.pm_scenario, stopping_criteria)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("06-01 - Auto Assignment")
    def __call__(self, eb, scenarioam, scenariomd, scenariopm, stopping_criteria):

        self.matrix_batchins(eb)
        self.calculate_truck_pce(eb)
        self.calculate_auto_cost(scenarioam, scenariomd, scenariopm)
        self.auto_assignment(scenarioam, scenariomd, scenariopm, stopping_criteria)

    @_m.logbook_trace("Calculate Truck PCE")
    def calculate_truck_pce(self, eb):
        util = _m.Modeller().tool("translink.emme.util")
        specs = []
        #TODO move PCE factors to scalar matrix and initiate from InitEmmebank
        specs.append(util.matrix_spec("mf1980", "mf980 * 1.5"))
        specs.append(util.matrix_spec("mf1981", "mf981 * 2.5"))
        specs.append(util.matrix_spec("mf1982", "mf982 * 1.5"))
        specs.append(util.matrix_spec("mf1983", "mf983 * 2.5"))
        specs.append(util.matrix_spec("mf1990", "mf990 * 1.5"))
        specs.append(util.matrix_spec("mf1991", "mf991 * 2.5"))

        util.compute_matrix(specs)


    @_m.logbook_trace("Calculate Auto Cost")
    def calculate_auto_cost(self, am_scenario, md_scenario, pm_scenario):
        self.calculate_network_costs(am_scenario)
        self.calc_transit_costs(am_scenario)
        self.calculate_network_costs(md_scenario)
        self.calc_transit_costs(md_scenario)
        self.calculate_network_costs(pm_scenario)
        self.calc_transit_costs(pm_scenario)

    @_m.logbook_trace("Auto Traffic Assignment")
    def auto_assignment(self, am_scenario, md_scenario, pm_scenario, stopping_criteria):
        # 12 assignment classes: SOV: work by income (low, med, high) nonwork by income (low, med/high);
        #    HOV work by income (low, med, high) nonwork by income (low, med/high), light trucks, heavy trucks
        eb = am_scenario.emmebank
        network_calculator = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")
        assign_traffic = _m.Modeller().tool("inro.emme.traffic_assignment.sola_traffic_assignment")

        num_processors = int(eb.matrix("ms142").data)

        demands_list = [
            {
                "sov": ["mf843", "mf844", "mf845", "mf846", "mf847"],
                "hov": ["mf848", "mf849", "mf850", "mf851", "mf852"],
                "truck": ["mf1980", "mf1981"]
            },
            {
                "sov": ["mf856", "mf857", "mf858", "mf859", "mf860"],
                "hov": ["mf861", "mf862", "mf863", "mf864", "mf865"],
                "truck": ["mf1982", "mf1983"]
            },
            {
                "sov": ["mf869", "mf870", "mf871", "mf872", "mf873"],
                "hov": ["mf874", "mf875", "mf876", "mf877", "mf878"],
                "truck": ["mf1990", "mf1991"]
            }
        ]

        travel_time_list = ["mf931", "mf943", "mf2001"]
        distance_list = ["mf930", "mf942", "mf2000"]

        path_analysis = {
            "link_component": "length",
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
        input_items = zip([am_scenario, md_scenario, pm_scenario], demands_list,
                          travel_time_list, distance_list)
        for scenario, demands, travel_time, distance in input_items:
            spec = self.generate_specification(
                demands, stopping_criteria, num_processors)
            spec["path_analysis"] = path_analysis
            spec["classes"][4]["results"]["od_travel_times"] = {"shortest_paths": travel_time}
            spec["classes"][4]["analysis"] = {"results": {"od_values": distance}}
            assign_traffic(spec, scenario=scenario)

        spec = {
            "result": "",
            "expression": "",
            "aggregation": None,
            "selections": {},
            "type": "NETWORK_CALCULATION"
        }
        selection_type = {
            "link": {"link": "all"},
            "turn": {"incoming_link": "all", "outgoing_link": "all"}}
        expressions_list = [["link", "@sov1+@sov2+@sov3+@sov4+@sov5", "@wsovl"],
                            ["link", "@hov1+@hov2+@hov3+@hov4+@hov5", "@whovl"],
                            ["turn", "@tsov1+@tsov2+@tsov3+@tsov4+@tsov5", "@wsovt"],
                            ["turn", "@thov1+@thov2+@thov3+@thov4+@thov5", "@whovt"]]
        for kind, expression, result in expressions_list:
            spec["expression"] = expression
            spec["selections"] = selection_type[kind]
            spec["result"] = result
            network_calculator(spec, scenario=am_scenario)
            network_calculator(spec, scenario=md_scenario)
            network_calculator(spec, scenario=pm_scenario)

    def generate_specification(self, demand_matrices, stopping_criteria, num_processors, results=True):
        all_classes = []
        perception_factors = [6, 3, 3, 12, 6]
        class_details = [
            (zip(demand_matrices["sov"], perception_factors), "d", "@sovoc", "sov"),
            (zip(demand_matrices["hov"], perception_factors), "c", "@hovoc", "hov")
        ]
        for details, mode, cost, name in class_details:
            for i, (demand, perception) in enumerate(details, start=1):
                result_sub_spec = {
                    "link_volumes": "@" + name + str(i),
                    "turn_volumes": "@t" + name + str(i),
                }
                all_classes.append({
                    "mode": mode,
                    "demand": demand,
                    "generalized_cost": {
                        "link_costs": cost,
                        "perception_factor": perception
                    },
                    "results": result_sub_spec if results else {}
                })
        all_classes.append(
            {
                "mode": "x",
                "demand": demand_matrices["truck"][0],
                "generalized_cost": {
                    "link_costs": "@lgvoc", "perception_factor": 2.03},
                "results": {
                    "link_volumes": "@lgvol", "turn_volumes": "@lgvtn"}
            })
        all_classes.append(
            {
                "mode": "t",
                "demand": demand_matrices["truck"][1],
                "generalized_cost": {
                    "link_costs": "@hgvoc", "perception_factor": 1.43},
                "results": {
                    "link_volumes": "@hgvol", "turn_volumes": "@hgvtn"}
            })
        spec = {
            "type": "SOLA_TRAFFIC_ASSIGNMENT",
            "background_traffic": {"add_transit_vehicles": True},
            "classes": all_classes,
            "stopping_criteria": stopping_criteria,
            "performance_settings": {"number_of_processors": num_processors},
        }
        return spec

    @_m.logbook_trace("Calculate Fixed Network Costs")
    def calculate_network_costs(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")
        eb = scenario.emmebank

        auto_voc = eb.matrix("ms100").data
        lgv_voc = eb.matrix("ms101").data
        hgv_voc = eb.matrix("ms102").data

        util.emme_link_calc(scenario, "@tkpen", 0)
        util.emme_link_calc(scenario, "@tkpen", "length * 100", sel_link="mode=n")
        util.emme_link_calc(scenario, "@sovoc", "length * %s + @tolls" % (auto_voc))
        util.emme_link_calc(scenario, "@hovoc", "length * %s + @tolls / %s" % (auto_voc, 2.5))
        util.emme_link_calc(scenario, "@lgvoc", "length * %s + 2 * @tolls" % (lgv_voc))
        util.emme_link_calc(scenario, "@hgvoc", "length * %s + 3 * @tolls + @tkpen" % (hgv_voc))

    def calc_transit_costs(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")

        #TODO Move the headway calculations to the transit assignment module
        # KB: why are the transit heady calculations in the traffic assignment tool ??????

        # Calculate effective headway based on
        # 0-10 minutes 0.5
        # 10-20 minutes 0.4
        # 20-30 minutes 0.3
        # > 30 minutes 0.1
        util.emme_tline_calc(scenario, "ut2", "(hdw.le.10)*(hdw*.5)+(hdw.gt.10)*(hdw.le.20)*(5+(hdw-10)*.4)+(hdw.gt.20)*(hdw.le.30)*(5+4+(hdw-20)*.3)+(hdw.gt.30)*(5+4+3+(hdw-30)*.1)")


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

    @_m.logbook_trace("Matrix Batchin")
    def matrix_batchins(self, eb):
        util = _m.Modeller().tool("translink.emme.util")
        #TODO initialize matrices for bus and rail skims inside those tools rather then here in auto assignment
        util.initmat(eb, "mf930", "eAuDsA", "Interim Skim AutoDistanceAM", 0)
        util.initmat(eb, "mf931", "eAuTmA", "Interim Skim AutoTimeAM", 0)
        util.initmat(eb, "mf932", "eAuTlA", "Interim Skim AutoTollAM", 0)
        util.initmat(eb, "mf933", "eBsWtA", "Interim Skim BusTotalWaitAM", 0)
        util.initmat(eb, "mf934", "eBsIvA", "Interim Skim BusIVTTAM", 0)
        util.initmat(eb, "mf935", "eBsBrA", "Interim Skim BusAvgBoardAM", 0)
        util.initmat(eb, "mf936", "eBsAxA", "Interim Skim BusAuxAM", 0)
        util.initmat(eb, "mf937", "eRBIvA", "Interim Skim RailBusIVTTAM", 0)
        util.initmat(eb, "mf938", "eRRIvA", "Interim Skim RailRailIVTTAM", 0)
        util.initmat(eb, "mf939", "eRlWtA", "Interim Skim RailTotalWaitAM", 0)
        util.initmat(eb, "mf940", "eRlBrA", "Interim Skim RailAvgBoardAM", 0)
        util.initmat(eb, "mf941", "eRlAxA", "Interim Skim RailAuxAM", 0)
        util.initmat(eb, "mf942", "eAuDsM", "Interim Skim AutoDistanceMD", 0)
        util.initmat(eb, "mf943", "eAuTmM", "Interim Skim AutoTimeMD", 0)
        util.initmat(eb, "mf944", "eAuTlM", "Interim Skim AutoTollMD", 0)
        util.initmat(eb, "mf945", "eBsWtM", "Interim Skim BusTotalWaitMD", 0)
        util.initmat(eb, "mf946", "eBsIvM", "Interim Skim BusIVTTMD", 0)
        util.initmat(eb, "mf947", "eBsBrM", "Interim Skim BusAvgBoardMD", 0)
        util.initmat(eb, "mf948", "eBsAxM", "Interim Skim BusAuxMD", 0)
        util.initmat(eb, "mf949", "eRBIvM", "Interim Skim RailBusIVTTMD", 0)
        util.initmat(eb, "mf950", "eRRIvM", "Interim Skim RailRailIVTTMD", 0)
        util.initmat(eb, "mf951", "eRlWtM", "Interim Skim RailTotalWaitMD", 0)
        util.initmat(eb, "mf952", "eRlBrM", "Interim Skim RailAvgBoardMD", 0)
        util.initmat(eb, "mf953", "eRlAxM", "Interim Skim RailAuxMD", 0)
        util.initmat(eb, "mf2000", "eAuDsP", "Interim Skim AutoDistancePM", 0)
        util.initmat(eb, "mf2001", "eAuTmP", "Interim Skim AutoTimePM", 0)
        util.initmat(eb, "mf2002", "eAuTlP", "Interim Skim AutoTollPM", 0)
        util.initmat(eb, "mf2003", "eBsWtP", "Interim Skim BusTotalWaitPM", 0)
        util.initmat(eb, "mf2004", "eBsIvP", "Interim Skim BusIVTTPM", 0)
        util.initmat(eb, "mf2005", "eBsBrP", "Interim Skim BusAvgBoardPM", 0)
        util.initmat(eb, "mf2006", "eBsAxP", "Interim Skim BusAuxPM", 0)
        util.initmat(eb, "mf2007", "eRBIvP", "Interim Skim RailBusIVTTPM", 0)
        util.initmat(eb, "mf2008", "eRRIvP", "Interim Skim RailRailIVTTPM", 0)
        util.initmat(eb, "mf2009", "eRlWtP", "Interim Skim RailTotalWaitPM", 0)
        util.initmat(eb, "mf2010", "eRlBrP", "Interim Skim RailAvgBoardPM", 0)
        util.initmat(eb, "mf2011", "eRlAxP", "Interim Skim RailAuxPM", 0)
        util.initmat(eb, "mf954", "eTrWtA", "Interim Skim TransitTotalWaitAM", 0)
        util.initmat(eb, "mf955", "eTrIvA", "Interim Skim TransitIVTTAM", 0)
        util.initmat(eb, "mf956", "eTrAxA", "Interim Skim TransitAuxAM", 0)
        util.initmat(eb, "mf957", "eTrBrA", "Interim Skim TransitBoardAM", 0)
        util.initmat(eb, "mf958", "eTrWtM", "Interim Skim TransitTotalWaitMD", 0)
        util.initmat(eb, "mf959", "eTrIvM", "Interim Skim TransitIVTTMD", 0)
        util.initmat(eb, "mf960", "eTrAxM", "Interim Skim TransitAuxMD", 0)
        util.initmat(eb, "mf961", "eTrBrM", "Interim Skim TransitBoardMD", 0)
        util.initmat(eb, "mf2012", "eTrWtP", "Interim Skim TransitTotalWaitPM", 0)
        util.initmat(eb, "mf2013", "eTrIvP", "Interim Skim TransitIVTTPM", 0)
        util.initmat(eb, "mf2014", "eTrAxP", "Interim Skim TransitAuxPM", 0)
        util.initmat(eb, "mf2015", "eTrBrP", "Interim Skim TransitBoardPM", 0)

        ## Initialize new block used for journey-level assignment
        util.initmat(eb, "mf1070", "nRBIvA", "Interim-JL Skim RailBusIVTTAM", 0)
        util.initmat(eb, "mf1071", "nRRIvA", "Interim-JL Skim RailRailIVTTAM", 0)
        util.initmat(eb, "mf1072", "nRlWtA", "Interim-JL Skim RailTotalWaitAM", 0)
        util.initmat(eb, "mf1073", "nRlBrA", "Interim-JL Skim RailAvgBoardAM", 0)
        util.initmat(eb, "mf1074", "nRlAxA", "Interim-JL Skim RailAuxAM", 0)
        util.initmat(eb, "mf1075", "nRBIvM", "Interim-JL Skim RailBusIVTTMD", 0)
        util.initmat(eb, "mf1076", "nRRIvM", "Interim-JL Skim RailRailIVTTMD", 0)
        util.initmat(eb, "mf1077", "nRlWtM", "Interim-JL Skim RailTotalWaitMD", 0)
        util.initmat(eb, "mf1078", "nRlBrM", "Interim-JL Skim RailAvgBoardMD", 0)
        util.initmat(eb, "mf1079", "nRlAxM", "Interim-JL Skim RailAuxMD", 0)
        util.initmat(eb, "mf2016", "nRBIvP", "Interim-JL Skim RailBusIVTTPM", 0)
        util.initmat(eb, "mf2017", "nRRIvP", "Interim-JL Skim RailRailIVTTPM", 0)
        util.initmat(eb, "mf2018", "nRlWtP", "Interim-JL Skim RailTotalWaitPM", 0)
        util.initmat(eb, "mf2019", "nRlBrP", "Interim-JL Skim RailAvgBoardPM", 0)
        util.initmat(eb, "mf2020", "nRlAxP", "Interim-JL Skim RailAuxPM", 0)

        ## add matrices for truck PCE
        util.initmat(eb, "mf1980", "lgAMpce", "Veh-AMPH-PCE-LGV", 0)
        util.initmat(eb, "mf1981", "hgAMpce", "Veh-AMPH-PCE-HGV", 0)
        util.initmat(eb, "mf1982", "lgMDpce", "Veh-MDPH-PCE-LGV", 0)
        util.initmat(eb, "mf1983", "hgMDpce", "Veh-MDPH-PCE-HGV", 0)
        util.initmat(eb, "mf1990", "lgPMpce", "Veh-PMPH-PCE-LGV", 0)
        util.initmat(eb, "mf1991", "hgPMpce", "Veh-PMPH-PCE-HGV", 0)
