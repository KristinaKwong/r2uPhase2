##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage4.step8.demandadjustment
##--Purpose: Applies adjustments to AM and MD Auto Demand
##---------------------------------------------------------------------
import inro.modeller as _m
import os
import traceback as _traceback

class DemandAdjustment(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Adjust AM and MD Auto Demand"
        pb.description = "Applies adjustments to AM and MD Auto Demand"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            # TODO: add inputs in page and run
            eb = _m.Modeller().emmebank
            am_scenario = eb.scenario(21000)
            md_scenario = eb.scenario(22000)
            stopping_criteria = {
                "max_iterations": 0,
                "relative_gap": 0.0,
                "best_relative_gap": 0.01,
                "normalized_gap": 0.01
            }

            self.__call__(eb, am_scenario, md_scenario, stopping_criteria)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("08-01 - AM and MD Demand Adjustment")
    def __call__(self, eb, am_scenario, md_scenario, stopping_criteria):
        bus_assignment = _m.Modeller().tool(
            "translink.emme.stage3.step6.busassignment")
        rail_assignment = _m.Modeller().tool(
            "translink.emme.stage3.step6.railassignment")
        self.matrix_batchins(eb)
        self.demand_adjustment(am_scenario)
        am_adj_scenario, md_adj_scenario = self.copy_scenarios(am_scenario, md_scenario)
        self.auto_assignment(am_adj_scenario, md_adj_scenario, stopping_criteria)
        bus_assignment(am_adj_scenario, md_adj_scenario)
        rail_assignment(am_adj_scenario, md_adj_scenario)

    def copy_scenarios(self, am_scenario_id, md_scenario_id):
        copy_scenario = _m.Modeller().tool(
            "inro.emme.data.scenario.copy_scenario")
        emmebank = _m.Modeller().emmebank
        am_scenario = emmebank.scenario(am_scenario_id)
        md_scenario = emmebank.scenario(md_scenario_id)

        am_adj_scenario_id = int(am_scenario_id) + 60
        md_adj_scenario_id = int(md_scenario_id) + 60

        am_adj_scenario = copy_scenario(from_scenario=am_scenario,
                                scenario_id=am_adj_scenario_id,
                                scenario_title=am_scenario.title + ": Final Adjusted ",
                                overwrite=True)
        md_adj_scenario = copy_scenario(from_scenario=md_scenario,
                                 scenario_id=md_adj_scenario_id,
                                 scenario_title=md_scenario.title + ": Final Adjusted ",
                                 overwrite=True)
        return am_adj_scenario, md_adj_scenario

    @_m.logbook_trace("Auto Traffic Assignment")
    def auto_assignment(self, am_adj_scenario, md_adj_scenario, stopping_criteria):
        util = _m.Modeller().tool("translink.emme.util")
        create_extra = _m.Modeller().tool(
            "inro.emme.data.extra_attribute.create_extra_attribute")
        del_extra = _m.Modeller().tool(
            "inro.emme.data.extra_attribute.delete_extra_attribute")
        network_calculator = _m.Modeller().tool(
            "inro.emme.network_calculation.network_calculator")
        assign_traffic = _m.Modeller().tool(
            "inro.emme.traffic_assignment.sola_traffic_assignment")
        translink_auto_assignment = _m.Modeller().tool(
            "translink.emme.stage3.step6.autoassignment")
        compute_matrix = _m.Modeller().tool(
            "inro.emme.matrix_calculation.matrix_calculator")

        emmebank = _m.Modeller().emmebank
        num_processors = int(emmebank.matrix("ms142").data)
        del_list = ["@s1cst", "@s2cst", "@s3cst", "@s1vol", "@s2vol", "@s3vol", "@cpen", "@name", "@len", "@trncp",
                    "@hwycl", "@hcst"]
        cr_list = ["sov" + str(i) for i in range(1, 6)] + \
                  ["hov" + str(i) for i in range(1, 6)]
        for scenario in [am_adj_scenario, md_adj_scenario]:
            for attr_name in del_list:
                attrib = scenario.extra_attribute(attr_name)
                if attrib:
                    del_extra(attrib, scenario=scenario)
            for attr_name in cr_list:
                create_extra(extra_attribute_type="LINK",
                             extra_attribute_name="@" + attr_name,
                             extra_attribute_description=attr_name,
                             extra_attribute_default_value=0,
                             overwrite=True, scenario=scenario)
                create_extra(extra_attribute_type="TURN",
                             extra_attribute_name="@t" + attr_name,
                             extra_attribute_description=attr_name,
                             extra_attribute_default_value=0,
                             overwrite=True, scenario=scenario)

        demands_list = [
            {
                "sov": ["mf20", "mf21", "mf22", "mf23", "mf24"],
                "hov": ["mf26", "mf27", "mf28", "mf29", "mf30"],
                "truck": ["mf31", "mf32"]
            },
            {
                "sov": ["mf52", "mf53", "mf54", "mf55", "mf56"],
                "hov": ["mf58", "mf59", "mf60", "mf61", "mf62"],
                "truck": ["mf63", "mf64"]
            }
        ]
        travel_time_list = ["mf68", "mf69"]
        distance_list = ["mf66", "mf67"]

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
        input_items = zip([am_adj_scenario, md_adj_scenario], demands_list,
                          travel_time_list, distance_list)
        for scenario, demands, travel_time, distance in input_items:
            spec = translink_auto_assignment.generate_specification(
                demands, stopping_criteria, num_processors)
            spec["path_analysis"] = path_analysis
            spec["classes"][4]["results"]["od_travel_times"] = {"shortest_paths": travel_time}
            spec["classes"][4]["analysis"] = {"results": {"od_values": distance}}
            assign_traffic(spec, scenario=scenario)

        ###########################################################################
        #### TALLY SOV AND HOV VOLUMES
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
            network_calculator(spec, scenario=am_adj_scenario)
            network_calculator(spec, scenario=md_adj_scenario)

        specs = []
        specs.append(util.matrix_spec("mf66", "mf66 + (p.eq.q)*mf100"))
        specs.append(util.matrix_spec("mf67", "mf67 + (p.eq.q)*mf103"))
        specs.append(util.matrix_spec("mf68", "mf68 - (p.ne.q)*(mf66*6*ms18+mf102*ms19*6) + (p.eq.q)*mf101"))
        specs.append(util.matrix_spec("mf69", "mf69 - (p.ne.q)*(mf67*6*ms18+mf105*ms19*6) + (p.eq.q)*mf104"))
        compute_matrix(specs)

    @_m.logbook_trace("Demand adjustment")
    def demand_adjustment(self, scenario):
        compute_matrix = _m.Modeller().tool(
            "inro.emme.matrix_calculation.matrix_calculator")
        emmebank = _m.Modeller().emmebank
        scenario = emmebank.scenario(scenario)

        spec = {
            "expression": "",
            "result": "",
            "constraint": {
                "by_value": {
                    "od_values": "mf20",
                    "interval_min": -99999,
                    "interval_max": 99999,
                    "condition": "INCLUDE"
                },
                "by_zone": {"origins": "gy1-gy15", "destinations": "gy1-gy15"}
            },
            "aggregation": {"origins": None, "destinations": None},
            "type": "MATRIX_CALCULATION"
        }
        ## External and truck matrix adjustments: hybrid of difference and ratio;
        ## mf993 and mf994 are used to adjust MD trips for 2 screenlines
        expressions_list_am = [
            ["(mf978+mf1+mf978*mf15)/2", "mf19"],
            ["(mf979+mf7+mf979*mf16)/2", "mf25"],
            ["mf980", "mf31"],
            ["mf981", "mf32"]]
        expressions_list_md = [
            ["(mf984+mf33*mf993*mf994+mf984*mf47)/2", "mf51"],
            ["(mf985+mf39*mf993*mf994+mf985*mf48)/2", "mf57"],
            ["mf982", "mf63"],
            ["mf983", "mf64"]]

        for expression, result in expressions_list_am:
            spec["expression"] = expression
            spec["result"] = result
            compute_matrix(spec, scenario=scenario)

        for expression, result in expressions_list_md:
            spec["expression"] = expression
            spec["result"] = result
            compute_matrix(spec, scenario=scenario)

        ## Internal Matrix Adjustments using hybrid mix of difference and ratio factors
        spec["constraint"]["by_zone"]["origins"] = "gy1-gy14"
        spec["constraint"]["by_zone"]["destinations"] = "gy1-gy14"
        expressions_list_am = [
            ["(mf843+mf2+mf843*mf15)/2", "mf20"],
            ["(mf844+mf3+mf844*mf15)/2", "mf21"],
            ["(mf845+mf4+mf845*mf15)/2", "mf22"],
            ["(mf846+mf5+mf846*mf15)/2", "mf23"],
            ["(mf847+mf6+mf847*mf15)/2", "mf24"],
            ["(mf848+mf8+mf848*mf16)/2", "mf26"],
            ["(mf849+mf9+mf849*mf16)/2", "mf27"],
            ["(mf850+mf10+mf850*mf16)/2", "mf28"],
            ["(mf851+mf11+mf851*mf16)/2", "mf29"],
            ["(mf852+mf12+mf852*mf16)/2", "mf30"]]

        expressions_list_md = [
            ["(mf856+mf34*mf993*mf994+mf856*mf47)/2", "mf52"],
            ["(mf857+mf35*mf993*mf994+mf857*mf47)/2", "mf53"],
            ["(mf858+mf36*mf993*mf994+mf858*mf47)/2", "mf54"],
            ["(mf859+mf37*mf993*mf994+mf859*mf47)/2", "mf55"],
            ["(mf860+mf38*mf993*mf994+mf860*mf47)/2", "mf56"],
            ["(mf861+mf40*mf993*mf994+mf861*mf48)/2", "mf58"],
            ["(mf862+mf41*mf993*mf994+mf862*mf48)/2", "mf59"],
            ["(mf863+mf42*mf993*mf994+mf863*mf48)/2", "mf60"],
            ["(mf864+mf43*mf993*mf994+mf864*mf48)/2", "mf61"],
            ["(mf865+mf44*mf993*mf994+mf865*mf48)/2", "mf62"]]

        for expression, result in expressions_list_am:
            spec["expression"] = expression
            spec["result"] = result
            compute_matrix(spec, scenario=scenario)

        for expression, result in expressions_list_md:
            spec["expression"] = expression
            spec["result"] = result
            compute_matrix(spec, scenario=scenario)

        ## Use ratio method only for internal matrices if hybrid results in negatives
        spec["constraint"]["by_zone"]["origins"] = "gy1-gy14"
        spec["constraint"]["by_zone"]["destinations"] = "gy1-gy14"
        spec["constraint"]["by_value"]["interval_min"] = 0
        spec["constraint"]["by_value"]["interval_max"] = 99999
        spec["constraint"]["by_value"]["condition"] = "EXCLUDE"
        expressions_list_am = [
            ["mf843*mf15", "mf20", "mf20"],
            ["mf844*mf15", "mf21", "mf21"],
            ["mf845*mf15", "mf22", "mf22"],
            ["mf846*mf15", "mf23", "mf23"],
            ["mf847*mf15", "mf24", "mf24"],
            ["mf848*mf16", "mf26", "mf26"],
            ["mf849*mf16", "mf27", "mf27"],
            ["mf850*mf16", "mf28", "mf28"],
            ["mf851*mf16", "mf29", "mf29"],
            ["mf852*mf16", "mf30", "mf30"]]

        expressions_list_md = [
            ["mf856*mf47", "mf52", "mf52"],
            ["mf857*mf47", "mf53", "mf53"],
            ["mf858*mf47", "mf54", "mf54"],
            ["mf859*mf47", "mf55", "mf55"],
            ["mf860*mf47", "mf56", "mf56"],
            ["mf861*mf48", "mf58", "mf58"],
            ["mf862*mf48", "mf59", "mf59"],
            ["mf863*mf48", "mf60", "mf60"],
            ["mf864*mf48", "mf61", "mf61"],
            ["mf865*mf48", "mf62", "mf62"]]

        for expression, by_value_mat, result in expressions_list_am:
            spec["expression"] = expression
            spec["result"] = result
            spec["constraint"]["by_value"]["od_values"] = by_value_mat
            compute_matrix(spec, scenario=scenario)

        for expression, by_value_mat, result in expressions_list_md:
            spec["expression"] = expression
            spec["result"] = result
            spec["constraint"]["by_value"]["od_values"] = by_value_mat
            compute_matrix(spec, scenario=scenario)
            ## Use ratio method for externals if hybrid results in negatives
        spec["constraint"]["by_zone"]["origins"] = "gy1-gy15"
        spec["constraint"]["by_zone"]["destinations"] = "gy1-gy15"
        spec["constraint"]["by_value"]["interval_min"] = 0
        spec["constraint"]["by_value"]["interval_max"] = 99999
        spec["constraint"]["by_value"]["condition"] = "EXCLUDE"
        expressions_list_am = [
            ["mf978*mf15", "mf19", "mf19"],
            ["mf979*mf16", "mf25", "mf25"],
            ["mf980", "mf31", "mf31"],
            ["mf981", "mf32", "mf32"]
        ]
        expressions_list_md = [
            ["mf984*mf47", "mf51", "mf51"],
            ["mf985*mf48", "mf57", "mf57"],
            ["mf982", "mf63", "mf63"],
            ["mf983", "mf64", "mf64"]
        ]

        for expression, by_value_mat, result in expressions_list_am:
            spec["expression"] = expression
            spec["result"] = result
            spec["constraint"]["by_value"]["od_values"] = by_value_mat
            compute_matrix(spec, scenario=scenario)
        for expression, by_value_mat, result in expressions_list_md:
            spec["expression"] = expression
            spec["result"] = result
            spec["constraint"]["by_value"]["od_values"] = by_value_mat
            compute_matrix(spec, scenario=scenario)
            ### Aggregate external SOV and HOV with nonwork_med/high SOV (mf24) and nonwork_med/high HOV (mf30)

        spec["constraint"]["by_value"]["interval_min"] = -99999
        spec["constraint"]["by_value"]["interval_max"] = 99999
        spec["constraint"]["by_value"]["condition"] = "INCLUDE"
        expressions_list_am = [
            ["mf19+mf24", "mf24", "mf24"],
            ["mf25+mf30", "mf30", "mf30"]
        ]
        expressions_list_md = [
            ["mf51+mf56", "mf56", "mf56"],
            ["mf57+mf62", "mf62", "mf62"]
        ]

        for expression, by_value_mat, result in expressions_list_am:
            spec["expression"] = expression
            spec["result"] = result
            spec["constraint"]["by_value"]["od_values"] = by_value_mat
            compute_matrix(spec, scenario=scenario)

        for expression, by_value_mat, result in expressions_list_md:
            spec["expression"] = expression
            spec["result"] = result
            spec["constraint"]["by_value"]["od_values"] = by_value_mat
            compute_matrix(spec, scenario=scenario)

    @_m.logbook_trace("Matrix Batchin")
    def matrix_batchins(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        year = util.get_year(eb)
        yr = year[2:]

        util.initmat(eb, "mf19", "AVhD1", yr + "-Veh-AMPH-nonworkext-adjusted-SOV", 0)
        util.initmat(eb, "mf20", "AVhD2", yr + "-Veh-AMPH-worklow-adjusted-SOV", 0)
        util.initmat(eb, "mf21", "AVhD3", yr + "-Veh-AMPH-workmed-adjusted-SOV", 0)
        util.initmat(eb, "mf22", "AVhD4", yr + "-Veh-AMPH-workhigh-adjusted-SOV", 0)
        util.initmat(eb, "mf23", "AVhD5", yr + "-Veh-AMPH-nonworklow-adjusted-SOV", 0)
        util.initmat(eb, "mf24", "AVhD6", yr + "-Veh-AMPH-nonworkmed-high-adjusted-SOV", 0)
        util.initmat(eb, "mf25", "AVhD7", yr + "-Veh-AMPH-nonworkext-adjusted-HOV", 0)
        util.initmat(eb, "mf26", "AVhD8", yr + "-Veh-AMPH-worklow-adjusted-HOV", 0)
        util.initmat(eb, "mf27", "AVhD9", yr + "-Veh-AMPH-workmed-adjusted-HOV", 0)
        util.initmat(eb, "mf28", "AVhD10", yr + "-Veh-AMPH-workhigh-adjusted-HOV", 0)
        util.initmat(eb, "mf29", "AVhD11", yr + "-Veh-AMPH-nonworklow-adjusted-HOV", 0)
        util.initmat(eb, "mf30", "AVhD12", yr + "-Veh-AMPH-nonworkmed-high-adjusted-HOV", 0)
        util.initmat(eb, "mf31", "ALgD13", yr + "-Veh-AMPH-adjusted-Light Trucks", 0)
        util.initmat(eb, "mf32", "AHgD14", yr + "-Veh-AMPH-adjusted-Heavy Trucks", 0)
        util.initmat(eb, "mf51", "MVhD1", yr + "-Veh-MDPH-nonworkext-adjusted-SOV", 0)
        util.initmat(eb, "mf52", "MVhD2", yr + "-Veh-MDPH-worklow-adjusted-SOV", 0)
        util.initmat(eb, "mf53", "MVhD3", yr + "-Veh-MDPH-workmed-adjusted-SOV", 0)
        util.initmat(eb, "mf54", "MVhD4", yr + "-Veh-MDPH-workhigh-adjusted-SOV", 0)
        util.initmat(eb, "mf55", "MVhD5", yr + "-Veh-MDPH-nonworklow-adjusted-SOV", 0)
        util.initmat(eb, "mf56", "MVhD6", yr + "-Veh-MDPH-nonworkmed-high-adjusted-SV", 0)
        util.initmat(eb, "mf57", "MVhD7", yr + "-Veh-MDPH-nonworkext-adjusted-HOV", 0)
        util.initmat(eb, "mf58", "MVhD8", yr + "-Veh-MDPH-worklow-adjusted-HOV", 0)
        util.initmat(eb, "mf59", "MVhD9", yr + "-Veh-MDPH-workmed-adjusted-HOV", 0)
        util.initmat(eb, "mf60", "MVhD10", yr + "-Veh-MDPH-workhigh-adjusted-HOV", 0)
        util.initmat(eb, "mf61", "MVhD11", yr + "-Veh-MDPH-nonworklow-adjusted-HOV", 0)
        util.initmat(eb, "mf62", "MVhD12", yr + "-Veh-MDPH-nonworkmed-high-adjusted-HOV", 0)
        util.initmat(eb, "mf63", "MVhD13", yr + "-Veh-MDPH-adjusted-LGV", 0)
        util.initmat(eb, "mf64", "MVhD14", yr + "-Veh-MDPH-adjusted-HGV", 0)
        util.initmat(eb, "mf66", "jAuDsA", "Adj. Final Skim AutoDistanceAM", 0)
        util.initmat(eb, "mf67", "jAuTmA", "Adj. Final Skim AutoTimeAM", 0)
        util.initmat(eb, "mf68", "jAuDsM", "Adj. Final Skim AutoDistanceMD", 0)
        util.initmat(eb, "mf69", "jAuTmM", "Adj. Final Skim AutoTimeMD", 0)
