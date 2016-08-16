##------------------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model Development
##--
##--Path: translink.emme.under_dev.autoskim
##--Purpose: Run Assignment to generate time and distance skims for work and nonwork
##------------------------------------------------------------------------------
import inro.modeller as _m
import os
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
        self.relative_gap = 0.0
        self.best_relative_gap = 0.01
        self.normalized_gap = 0.01
        self.max_iterations = 200

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
            eb = _m.Modeller().emmebank
            stopping_criteria = {
                "relative_gap": self.relative_gap,
                "best_relative_gap": self.best_relative_gap,
                "normalized_gap": self.normalized_gap,
                "max_iterations": self.max_iterations
            }
            self(eb, self.am_scenario, self.md_scenario, self.pm_scenario, stopping_criteria)
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
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

        specs.append(util.matrix_spec("mf1980", "mf980 * 1.5"))
        specs.append(util.matrix_spec("mf1981", "mf981 * 2.5"))
        specs.append(util.matrix_spec("mf1982", "mf982 * 1.5"))
        specs.append(util.matrix_spec("mf1983", "mf983 * 2.5"))
        specs.append(util.matrix_spec("mf1990", "mf990 * 1.5"))
        specs.append(util.matrix_spec("mf1991", "mf991 * 2.5"))

        util.compute_matrix(specs)


    @_m.logbook_trace("Calculate Auto Cost")
    def calculate_auto_cost(self, am_scenario, md_scenario, pm_scenario):
        eb = am_scenario.emmebank

        voc = str(eb.matrix("ms18").data)
        occ = str(eb.matrix("ms20").data)
        toll_sens = str(eb.matrix("ms147").data)

        # Delete any unused attributes that might pre-exist and create attributes to store SOV and HOV volumes by class
        delete_extra = _m.Modeller().tool("inro.emme.data.extra_attribute.delete_extra_attribute")
        create_extra = _m.Modeller().tool("inro.emme.data.extra_attribute.create_extra_attribute")

        del_list = ["@s1cst", "@s2cst", "@s3cst", "@s1vol", "@s2vol",
                    "@s3vol", "@cpen", "@name", "@len", "@trncp",
                    "@hwycl", "@hcst", "@voltr", "@rail", "@ivtp2"]

        cr_list = ["sov" + str(i) for i in range(1, 6)] + \
                  ["hov" + str(i) for i in range(1, 6)]

        Link_Cost_List=["@hovoc", "@sovoc", "@lgvoc" , "@hgvoc" , "@tkpen", "@tolls"]
        Link_Cost_Desc=["HOV auto op cost", "SOV auto op cost","Lg trk op cost", "Hv trk op cost", "Truck penalty", "Tolls"]
        Link_Vol_List= ["@whovl", "@wsovl", "@lgvol" , "@hgvol"]
        Link_Vol_Desc= ["HOV Vol","SOV Vol","Lg Vol", "Hv Vol"]
        Link_Turn_List=["@whovt", "@wsovt", "@lgvtn" , "@hvgtn"]
        Link_Turn_Desc=["HOV Trn","SOV Trn","Lg Trn", "Hv Trn"]

        for scenario in [am_scenario, md_scenario, pm_scenario]:

            for attr_name in del_list:
                attr = scenario.extra_attribute(attr_name)
                if attr:
                    delete_extra(attr_name, scenario=scenario)

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

            for attribute in range (0, len(Link_Cost_List)):

                create_extra(extra_attribute_type="LINK",
                             extra_attribute_name=Link_Cost_List[attribute],
                             extra_attribute_description=Link_Cost_Desc[attribute],
                             extra_attribute_default_value=0,
                             overwrite=True, scenario=scenario)

            for attribute in range (0, len(Link_Vol_List)):

                create_extra(extra_attribute_type="LINK",
                             extra_attribute_name=Link_Vol_List[attribute],
                             extra_attribute_description=Link_Vol_Desc[attribute],
                             extra_attribute_default_value=0,
                             overwrite=True, scenario=scenario)

            for attribute in range (0, len(Link_Turn_List)):

                create_extra(extra_attribute_type="TURN",
                             extra_attribute_name=Link_Turn_List[attribute],
                             extra_attribute_description=Link_Turn_Desc[attribute],
                             extra_attribute_default_value=0,
                             overwrite=True, scenario=scenario)
            # create bus in-vehicle penalty attribute
            create_extra(extra_attribute_type="TRANSIT_LINE",
                         extra_attribute_name="@ivttp",
                         extra_attribute_description="Bus IVTT Penalty",
                         extra_attribute_default_value=0,
                         overwrite=True, scenario=scenario)

        ## Calculate generalized costs for various classes;
        # @tkpen: truck penalty ;
        # @sovoc: SOV gc;
        # @hovoc: HOV gc;
        # @lgvoc: light truck gc;
        # @hgvoc: heavy truck gc

        # Input Tolls from toll file
        util = _m.Modeller().tool("translink.emme.util")
        input_path = util.get_input_path(eb)
        toll_file = os.path.join(input_path, "tollinput.csv")
        set_tolls = _m.Modeller().tool("translink.emme.stage3.step6.tollset")
        set_tolls(toll_file, am_scenario, md_scenario, pm_scenario)

        calc_extra_attribute = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")
        spec = {
            "result": "",
            "expression": "",
            "selections": {"link": "all"},
            "type": "NETWORK_CALCULATION"
        }

        expressions_list = [
            ["0", "all", "@tkpen"],
            ["length*100", "mode=n", "@tkpen"],
            ["length*" + voc + "+@tolls*" + toll_sens, "all", "@sovoc"],
            ["length*" + voc + "+@tolls*" + toll_sens + "/" + occ, "all", "@hovoc"],
            ["length*0.24+@tolls*2*" + toll_sens, "all", "@lgvoc"],
            ["length*0.56+@tolls*3*" + toll_sens + "+@tkpen", "all", "@hgvoc"]
        ]
        for expression, selection, result in expressions_list:
            spec["expression"] = expression
            spec["selections"]["link"] = selection
            spec["result"] = result
            calc_extra_attribute(spec, scenario=am_scenario)
            calc_extra_attribute(spec, scenario=md_scenario)
            calc_extra_attribute(spec, scenario=pm_scenario)

"""			
        spec = {
            "result": "",
            "expression": "",
            "aggregation": None,
            "selections": {
                "transit_line": "all"
            },
            "type": "NETWORK_CALCULATION"
        }

        # KB: why are the transit heady calculations in the traffic assignment tool ??????
        # Calculate effective headways based on following factors:
        #        "l" rail=0.8,
        #        "b" bus=1.2,
        #        "s" seabus=0.67,
        #        "g" BRT=1.1,
        #        "f" LRT=1.1,
        #        "h" Gondola=0.8,
        #        "r" WCE=0.8
	
        expressions_list = [["hdw*1.2", "mode=b", "ut1"],
                            ["hdw*0.8", "mode=l", "ut1"],
                            ["hdw*0.67", "mode=s", "ut1"],
                            ["hdw*1.1", "mode=f", "ut1"],
                            ["hdw*1.1", "mode=g", "ut1"],
                            ["hdw*0.8", "mode=h", "ut1"],
                            ["hdw*0.8", "mode=r", "ut1"],
                            ["1", "all", "@ivttp"],
                            ["3.5", "mode=b", "@ivttp"],
                            ["3.5", "mode=g", "@ivttp"]]

        for expression, selection, result in expressions_list:
            spec["expression"] = expression
            spec["selections"]["transit_line"] = selection
            spec["result"] = result
            calc_extra_attribute(spec, scenario=am_scenario)
            calc_extra_attribute(spec, scenario=md_scenario)
            calc_extra_attribute(spec, scenario=pm_scenario)

		"""
			
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
		# Non-work Medium Income Skims
		# AD: I kept the non-work skims the same for now, however these could be changed
        travel_time_list_nw = ["mf931", "mf943", "mf2001"]
        distance_list_nw = ["mf930", "mf942", "mf2000"]
        # Work Medium Income Skims 
        travel_time_list_wk = ["mf2031", "mf2034", "mf2037"]
        distance_list_wk = ["mf2030", "mf2033", "mf2036"]        

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
                          travel_time_list_nw, distance_list_nw, travel_time_list_wk, distance_list_wk)
        for scenario, demands, travel_time_nw, distance_nw, travel_time_wk, distance_wk  in input_items:
            spec = self.generate_specification(
                demands, stopping_criteria, num_processors)
            spec["path_analysis"] = path_analysis
            spec["classes"][4]["results"]["od_travel_times"] = {"shortest_paths": travel_time_nw}
            spec["classes"][4]["analysis"] = {"results": {"od_values": distance_nw}}
            spec["classes"][1]["results"]["od_travel_times"] = {"shortest_paths": travel_time_wk}
            spec["classes"][1]["analysis"] = {"results": {"od_values": distance_wk}}            
            
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
		# Replace existing for work with $10/hr (6 min/dollar), $15/hr (4 min/dollar), $20/hr (3 min/dollar) instead
        #perception_factors = [6, 3, 3, 12, 6]

        perception_factors = [6, 4, 3, 12, 6]
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
                    "link_volumes": "@hgvol", "turn_volumes": "@hvgtn"}
            })
        spec = {
            "type": "SOLA_TRAFFIC_ASSIGNMENT",
            "background_traffic": {"add_transit_vehicles": True},
            "classes": all_classes,
            "stopping_criteria": stopping_criteria,
            "performance_settings": {"number_of_processors": num_processors},
        }
        return spec

    @_m.logbook_trace("Matrix Batchin")
    def matrix_batchins(self, eb):
        util = _m.Modeller().tool("translink.emme.util")
        #TODO initialize matrices for bus and rail skims inside those tools rather then here in auto assignment
        util.initmat(eb, "mf930", "eADANW", "Interim Skim AutoDistanceAM NW", 0)
        util.initmat(eb, "mf931", "eATANW", "Interim Skim AutoTimeAM NW", 0)
        util.initmat(eb, "mf932", "eALANW", "Interim Skim AutoTollAM NW", 0)
 
 """
        util.initmat(eb, "mf933", "eBsWtA", "Interim Skim BusTotalWaitAM", 0)
        util.initmat(eb, "mf934", "eBsIvA", "Interim Skim BusIVTTAM", 0)
        util.initmat(eb, "mf935", "eBsBrA", "Interim Skim BusAvgBoardAM", 0)
        util.initmat(eb, "mf936", "eBsAxA", "Interim Skim BusAuxAM", 0)
        util.initmat(eb, "mf937", "eRBIvA", "Interim Skim RailBusIVTTAM", 0)
        util.initmat(eb, "mf938", "eRRIvA", "Interim Skim RailRailIVTTAM", 0)
        util.initmat(eb, "mf939", "eRlWtA", "Interim Skim RailTotalWaitAM", 0)
        util.initmat(eb, "mf940", "eRlBrA", "Interim Skim RailAvgBoardAM", 0)
        util.initmat(eb, "mf941", "eRlAxA", "Interim Skim RailAuxAM", 0)

"""
        util.initmat(eb, "mf942", "eADMNW", "Interim Skim AutoDistanceMD NW", 0)
        util.initmat(eb, "mf943", "eATMNW", "Interim Skim AutoTimeMD NW", 0)
        util.initmat(eb, "mf944", "eALMNW", "Interim Skim AutoTollMD NW", 0)
"""		
        util.initmat(eb, "mf945", "eBsWtM", "Interim Skim BusTotalWaitMD", 0)
        util.initmat(eb, "mf946", "eBsIvM", "Interim Skim BusIVTTMD", 0)
        util.initmat(eb, "mf947", "eBsBrM", "Interim Skim BusAvgBoardMD", 0)
        util.initmat(eb, "mf948", "eBsAxM", "Interim Skim BusAuxMD", 0)
        util.initmat(eb, "mf949", "eRBIvM", "Interim Skim RailBusIVTTMD", 0)
        util.initmat(eb, "mf950", "eRRIvM", "Interim Skim RailRailIVTTMD", 0)
        util.initmat(eb, "mf951", "eRlWtM", "Interim Skim RailTotalWaitMD", 0)
        util.initmat(eb, "mf952", "eRlBrM", "Interim Skim RailAvgBoardMD", 0)
        util.initmat(eb, "mf953", "eRlAxM", "Interim Skim RailAuxMD", 0)
"""		
        util.initmat(eb, "mf2000", "eADPNW", "Interim Skim AutoDistancePM NW", 0)
        util.initmat(eb, "mf2001", "eATPNW", "Interim Skim AutoTimePM NW", 0)
        util.initmat(eb, "mf2002", "eALPNW", "Interim Skim AutoTollPM NW", 0)
 
"""
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

"""
        ## add matrices for truck PCE
        util.initmat(eb, "mf1980", "lgAMpce", "Veh-AMPH-PCE-LGV", 0)
        util.initmat(eb, "mf1981", "hgAMpce", "Veh-AMPH-PCE-HGV", 0)
        util.initmat(eb, "mf1982", "lgMDpce", "Veh-MDPH-PCE-LGV", 0)
        util.initmat(eb, "mf1983", "hgMDpce", "Veh-MDPH-PCE-HGV", 0)
        util.initmat(eb, "mf1990", "lgPMpce", "Veh-PMPH-PCE-LGV", 0)
        util.initmat(eb, "mf1991", "hgPMpce", "Veh-PMPH-PCE-HGV", 0)

        ## initialze new batch of matrices to skim work and non-work auto (medium income class)
        util.initmat(eb, "mf2030", "eADAWK", "Interim Skim AutoDistanceAM WK", 0)
        util.initmat(eb, "mf2031", "eATAWK", "Interim Skim AutoTimeAM WK", 0)
        util.initmat(eb, "mf2032", "eALAWK", "Interim Skim AutoTollAM WK", 0)
        
        util.initmat(eb, "mf2033", "eADMWK", "Interim Skim AutoDistanceMD WK", 0)
        util.initmat(eb, "mf2034", "eATMWK", "Interim Skim AutoTimeMD WK", 0)
        util.initmat(eb, "mf2035", "eALMWK", "Interim Skim AutoTollMD WK", 0)

        util.initmat(eb, "mf2036", "eADPWK", "Interim Skim AutoDistancePM WK", 0)
        util.initmat(eb, "mf2037", "eATPWK", "Interim Skim AutoTimePM WK", 0)
        util.initmat(eb, "mf2038", "eALPWK", "Interim Skim AutoTollPM WK", 0)        