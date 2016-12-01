##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage3.transitassignment
##--Purpose: Transit assignment procedure by Class with Crowding, Capacity, Dwell Time
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback

class TransitAssignment(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    run_congested_transit = _m.Attribute(bool)
    run_capacited_transit = _m.Attribute(bool)
    max_iterations = _m.Attribute(int)
    min_seat_weight = _m.Attribute(float)
    max_seat_weight = _m.Attribute(float)
    power_seat_weight = _m.Attribute(float)
    min_stand_weight = _m.Attribute(float)
    max_stand_weight = _m.Attribute(float)
    power_stand_weight = _m.Attribute(float)
    dwt_board_factor_bus = _m.Attribute(float)
    dwt_alight_factor_bus = _m.Attribute(float)

    am_scenario = _m.Attribute(_m.InstanceType)
    md_scenario = _m.Attribute(_m.InstanceType)
    pm_scenario = _m.Attribute(_m.InstanceType)

    def __init__(self):
        # Maximum Number of Iterations for transit loop
        self.max_iterations = 5
        # Crowding Parameters
        self.min_seat_weight = 1.0
        self.max_seat_weight = 1.2
        self.power_seat_weight = 2.0
        self.min_stand_weight = 1.5
        self.max_stand_weight = 2.0
        self.power_stand_weight = 3.0

        self.num_processors = 1
        # TODO: Update factors and define by multiple modes or vehicle types
        self.dwt_board_factor_bus = 0.025  # 1.5 sec per boarding
        self.dwt_alight_factor_bus = 0.0083 # 0.5 sec per boarding

        self.bus_mode_list = ["b", "g", "a", "p"]
        self.rail_mode_list= ["b", "f", "g", "l", "s", "h", "a", "p"]
        self.wce_mode_list = ["b", "f", "g", "l", "r", "s", "h", "a", "p"]

        # TODO: Assign summary_mode_list based on time period
        self.pk_summary_mode_list =["b", "s", "l", "r"]
        self.op_summary_mode_list = ["b", "s", "l"]

        # Fare Values in Dollars for assignment: TODO - Update
        self.bus_zone1_fare = 2.1
        self.bus_zone_increment = 1.05
        # By Time Period [AM, MD, PM]
        self.wce_bfare_zone1 = [0, 0, 5.03]
        self.wce_bfare_zone3 = [2.12, 0, 2.72]
        self.wce_bfare_zone4 = [2.10, 0, 2.10]
        self.wce_bfare_zone5 = [3.79, 0 , 0]
        self.wce_fare_zone13 = [2.91, 0, 0]
        self.wce_fare_zone34 = [1.69, 0, 1.08]
        self.wce_fare_zone45 = [0, 0, 1.69]

        self.cost_perception_factor = 6 # 1/VOT in min/$, assuming VOT = 10 $/hr

        self.run_congested_transit = False
        self.run_capacited_transit = False

        # Values used to derive individidual transit skims
        # WCE Zonal Fare Values in Dollars For Skimming
        # TODO - Update values
        self.wce_fare_zone = {1: 3.79, 2: 3.79, 3: 5.03, 4: 6.10, 5: 8.39}

        # parameters for Mode availability matrices
        # Minimum IVTT; Disable value: 0
        self.minimum_ivtt_rule = {"Bus": 2, "Rail": 5, "WCE": 5} # TODO look at rail availability
        # IVTT/Auto Time Ratio; Disable value: 10 or any large value
        self.ivtt_auto_ratio = {"Bus": 10, "Rail": 2.5, "WCE": 2} #TODO look at that too - captives
        # Main Mode IVTT/ Total IVTT; Disable value: 0
        self.mivtt_totivt_ratio = {"Bus": 0, "Rail": 0.3, "WCE": 0.3}
        # IVTT - Bus skim IVTT; Not valid for Bus mode; Disable value: 999 or any large value
        self.ivtt_vs_busivtt = {"Bus": 999, "Rail": 30, "WCE": 30}
        # IVTT to Bus skim IVTT ratio; Not valid for Bus mode; Disable value: 10 or any large value
        self.ivtt_busivtt_ratio = {"Bus": 10, "Rail": 2, "WCE": 2}
        # IVTT bus component to Bus skim IVTT ratio; Not valid for Bus mode; Disable value: 10 or any large value
        self.ivttb_busivtt_ratio = {"Bus": 10, "Rail": 1, "WCE": 1}

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Transit Assignment with Crowding and Capacity Constraint"
        pb.description = "Performs Transit Assignments by Class (Bus, Rail, WCE) with Crowding and Capacity Constraint Options"
        pb.branding_text = "TransLink"

        with pb.section("Transit Assignment Options"):
            pb.add_checkbox("run_congested_transit", label="Run Congested Transit Assignment")
            pb.add_checkbox("run_capacited_transit", label="Run Capacited Transit Assignment")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            eb = _m.Modeller().emmebank
            self.am_scenario = _m.Modeller().emmebank.scenario(int(eb.matrix("ms2").data))
            self.md_scenario = _m.Modeller().emmebank.scenario(int(eb.matrix("ms3").data))
            self.pm_scenario = _m.Modeller().emmebank.scenario(int(eb.matrix("ms4").data))

            eb.matrix("ms45").data = int(self.run_congested_transit)
            eb.matrix("ms46").data = int(self.run_capacited_transit)

            self(eb, self.am_scenario, self.md_scenario, self.pm_scenario)
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Transit Assignment")
    def __call__(self, eb, scenarioam, scenariomd, scenariopm):
        self.am_scenario = scenarioam
        self.md_scenario = scenariomd
        self.pm_scenario = scenariopm
        self.matrix_batchins(eb)

        self.num_processors = int(eb.matrix("ms12").data)
        assign_transit = _m.Modeller().tool("inro.emme.transit_assignment.extended_transit_assignment")
        util = _m.Modeller().tool("translink.emme.util")

        run_crowding = int(eb.matrix("ms45").data)
        run_capacity_constraint = int(eb.matrix("ms46").data)

        # No Crowding and Capacity constraint applied
        # Run 2 iterations only to update dwell times
        if run_crowding+run_capacity_constraint ==0:
            self.max_iterations=2

        demand_bus_list = ["mf314", "mf334", "mf354"]
        demand_rail_list = ["mf315", "mf335", "mf355"]
        demand_wce_list = ["mf316", "mf336", "mf356"]

        scenario_list = [scenarioam, scenariomd, scenariopm]
        #TODO: Assignments are done for peak hour
        period_length_list = [1, 1, 1]

        for i, (sc, period_length, demand_bus, demand_rail, demand_wce) in enumerate(zip(scenario_list, period_length_list, demand_bus_list, demand_rail_list, demand_wce_list)):
            self.previous_level = _m.logbook_level()
            print "Scenario: "+sc.title+" ("+sc.id+")"
            report={}
            _m.logbook_level(_m.LogbookLevel.NONE)
            self.calc_network_costs(sc)
            # Initialize Values for first cycle and use updated values from previous cycles later on
            if util.get_cycle(eb) >= 1:  # TODO: Change to util.get_cycle(eb) == 1
                # Calculate headway fraction

                # Intial Assignment of Parameters
                util.emme_segment_calc(sc, "@ivttfac", "1")
                util.emme_segment_calc(sc, "@hdwyeff", "@hfrac")
                util.emme_segment_calc(sc, "@hdwyfac", "1")
                util.emme_segment_calc(sc, "@crowdingfactor", "0")
                util.emme_segment_calc(sc, "us1", "0")  # dwell time
                util.emme_tline_calc(sc, "@seatcapacity", "%s*vcaps*60/hdw" % period_length)
                util.emme_tline_calc(sc, "@totcapacity", "%s*vcapt*60/hdw" % period_length)

                # Fare Calculations

                # Constant Boarding fare For Buses/Skytrain/Seabus by line
                util.emme_tline_calc(sc, "@linefare", str(self.bus_zone1_fare), sel_line="mode=bgsfhl")

                # Different boarding fares for WCE by node
                # For First boarding
                util.emme_node_calc(sc, "@wcestopfare", "%s*(@farezone.eq.10)+%s*(@farezone.eq.30)+"
                                                "%s*(@farezone.eq.40)+%s*(@farezone.eq.50)"
                                            %(self.wce_bfare_zone1[i],self.wce_bfare_zone3[i],
                                              self.wce_bfare_zone4[i], self.wce_bfare_zone5[i]))

                # Transfer from Bus/Skytrain
                util.emme_node_calc(sc, "@wcexferfare", "(@wcestopfare - %s).max.0" % self.bus_zone1_fare)

                # In-vehicle Cost (@fareincrement)
                # For Buses/Skytrain/Seabus
                util.emme_segment_calc(sc, "@fareincrement", "%s*(@fareboundary.eq.1)" %self.bus_zone_increment,
                                             sel_link="all", sel_line="mode=bgsfhl")
                # For WCE
                util.emme_segment_calc(sc, "@fareincrement", "%s*(@wcefareboundary.eq.13) +%s*(@wcefareboundary.eq.34)+"
                                             "%s*(@wcefareboundary.eq.45)" %(self.wce_fare_zone13[i], self.wce_fare_zone34[i], self.wce_fare_zone45[i]),
                                             sel_link="all", sel_line="mode=r")

            # LOOP FOR CROWDING AND CAPACITY CONSTRAINT
            for iteration in xrange(1, self.max_iterations+1):
                # Restore writing to Logbook
                _m.logbook_level(self.previous_level)

                # Set Assignment Parameters
                bus_spec  = self.get_bus_transit_assignment_spec(demand_bus)
                rail_spec = self.get_rail_transit_assignment_spec(demand_rail)
                wce_spec  = self.get_wce_transit_assignment_spec(demand_wce)

                # Run Assignment
                assign_transit(bus_spec, scenario=sc, add_volumes=False, save_strategies=True, class_name= "Bus")
                assign_transit(rail_spec, scenario=sc, add_volumes=True, save_strategies=True, class_name= "Rail")
                if sc is scenarioam or sc is scenariopm:
                    assign_transit(wce_spec, scenario=sc, add_volumes=True, save_strategies=True, class_name= "WCE")

                _m.logbook_level(_m.LogbookLevel.NONE)

                # MSA on Boardings and transit Volumes
                self.averaging_transit_volumes(sc, iteration)

                # Run Crowding and Headway Reports
                if iteration==1:
                    report["  Iter    Mode"] = "     Seat.pass-kms    Stand.pass-kms   Excess.pass-kms  Max.crowd.factor   Min.Hdwy Factor   Max.Hdwy Factor"
                rep = self.crowding_headway_report(sc, iteration)
                report.update(rep)

                # Update Capacity, Crowding Functions
                if run_crowding==1:
                    self.crowding_factor_calc(sc)

                if run_capacity_constraint==1:
                    self.effective_headway_calc(sc)

                # Update Dwell time
                self.dwell_time_calc(sc, period_length)
            # Restore writing to Logbook
            _m.logbook_level(self.previous_level)

            # Write Logbook entries for crowding and Headway
            _m.logbook_write("Crowding and Headway report for Scenario: "+sc.id, attributes=report, value=sc.title)

            # Create Skims
            self.skim_bus(sc)
            self.skim_rail(sc)
            if sc is not scenariomd:
                self.skim_wce(sc)

            if sc is scenarioam:
                self.collect_skims(sc, "AM")
            if sc is scenariomd:
                self.collect_skims(sc, "MD")
            if sc is scenariopm:
                self.collect_skims(sc, "PM")

    def get_common_transit_assignment_spec(self, modes, demand):
        spec = {
            "modes": modes,
            "demand": demand,
            "waiting_time": {
                "headway_fraction": 1,
                "effective_headways": "@hdwyeff",
                "spread_factor": 1,
                "perception_factor": 2.25
            },
            "boarding_time": {
                "at_nodes": {
                    "penalty": 1,
                    "perception_factor": 4
                },
                "on_lines": None
            },
            "boarding_cost": {
                "at_nodes": None,
                "on_lines": {"penalty": "@linefare", "perception_factor": self.cost_perception_factor}
            },
            "in_vehicle_time": {
                "perception_factor": "@ivttfac"
            },
            "in_vehicle_cost": {"penalty": "@fareincrement","perception_factor": self.cost_perception_factor},
            "aux_transit_time": {
                "perception_factor": 1.75
            },
            "aux_transit_cost": None,

            "flow_distribution_between_lines": {
                "consider_total_impedance": True
            },
            "connector_to_connector_path_prohibition": {
                "at_nodes": "ALL",
                "reassign_demand_to_alternate_path": False
            },
            "od_results": {
                "total_impedance": None
            },
            "journey_levels": [],
            "performance_settings": {
                "number_of_processors": self.num_processors
            },
            "type": "EXTENDED_TRANSIT_ASSIGNMENT"
        }
        return spec

    def get_bus_transit_assignment_spec(self, demand):
        spec = self.get_common_transit_assignment_spec(self.bus_mode_list, demand)

        spec["flow_distribution_at_origins"]= {
                "choices_at_origins": "OPTIMAL_STRATEGY",
                "fixed_proportions_on_connectors": None
        }
        spec["flow_distribution_at_regular_nodes_with_aux_transit_choices"]= {
            "choices_at_regular_nodes": "OPTIMAL_STRATEGY"
        }

        spec["journey_levels"] =[
            {
                "description": "Not boarded yet",
                "destinations_reachable": False,
                "transition_rules": [
                    {"mode": "b", "next_journey_level": 1},
                    {"mode": "g", "next_journey_level": 1}
                ],
                "boarding_time": None,
                "boarding_cost": None,
                "waiting_time": None
            },
            {
                "description": "Boarded bus",
                "destinations_reachable": True,
                "transition_rules": [
                    {"mode": "b", "next_journey_level": 1},
                    {"mode": "g", "next_journey_level": 1}
                ],
                "boarding_time": None,
                "boarding_cost": {
                    "at_nodes": None,
                    "on_lines": {"penalty": "@xferlinefare","perception_factor": self.cost_perception_factor}
                },
                "waiting_time": None
            }
        ]
        return spec

    def get_rail_transit_assignment_spec(self, demand):
        spec = self.get_common_transit_assignment_spec(self.rail_mode_list, demand)

        spec["flow_distribution_at_origins"]= {
                "by_time_to_destination": "BEST_CONNECTOR",
                "by_fixed_proportions": None
        }

        spec["journey_levels"] = [
            {
                "description": "Not boarded yet",
                "destinations_reachable": False,
                "transition_rules": [
                    {"mode": "b", "next_journey_level": 1},
                    {"mode": "f", "next_journey_level": 2},
                    {"mode": "g", "next_journey_level": 1},
                    {"mode": "h", "next_journey_level": 2},
                    {"mode": "l", "next_journey_level": 2},
                    {"mode": "s", "next_journey_level": 2}
                ],
                "boarding_time": None,
                "boarding_cost": None,
                "waiting_time": None
            },
            {
                "description": "Boarded bus only",
                "destinations_reachable": False,
                "transition_rules": [
                    {"mode": "b", "next_journey_level": 1},
                    {"mode": "f", "next_journey_level": 2},
                    {"mode": "g", "next_journey_level": 1},
                    {"mode": "h", "next_journey_level": 2},
                    {"mode": "l", "next_journey_level": 2},
                    {"mode": "s", "next_journey_level": 2}
                ],
                "boarding_time": None,
                "boarding_cost": {
                    "at_nodes": None,
                    "on_lines": {"penalty": "@xferlinefare","perception_factor": self.cost_perception_factor}
                },
                "waiting_time": None
            },
            {
                "description": "Boarded rail",
                "destinations_reachable": True,
                "transition_rules": [
                    {"mode": "b", "next_journey_level": 2},
                    {"mode": "f", "next_journey_level": 2},
                    {"mode": "g", "next_journey_level": 2},
                    {"mode": "h", "next_journey_level": 2},
                    {"mode": "l", "next_journey_level": 2},
                    {"mode": "s", "next_journey_level": 2}
                ],
                "boarding_time": None,
                "boarding_cost": {
                    "at_nodes": None,
                    "on_lines": {"penalty": "@xferlinefare", "perception_factor": self.cost_perception_factor}
                },
                "waiting_time": None
            }
        ]
        return spec

    def get_wce_transit_assignment_spec(self, demand):
        spec = self.get_common_transit_assignment_spec(self.wce_mode_list, demand)

        spec["flow_distribution_at_origins"]= {
                "by_time_to_destination": "BEST_CONNECTOR",
                "by_fixed_proportions": None
        }

        spec["boarding_cost"] = {
            "at_nodes": {"penalty": "@wcestopfare", "perception_factor": self.cost_perception_factor},
            "on_lines": {"penalty": "@linefare", "perception_factor": self.cost_perception_factor}
        }

        spec["journey_levels"] = [
            {
                "description": "Not boarded yet",
                "destinations_reachable": False,
                "transition_rules": [
                    {"mode": "b", "next_journey_level": 1},
                    {"mode": "f", "next_journey_level": 1},
                    {"mode": "g", "next_journey_level": 1},
                    {"mode": "h", "next_journey_level": 1},
                    {"mode": "l", "next_journey_level": 1},
                    {"mode": "s", "next_journey_level": 1},
                    {"mode": "r", "next_journey_level": 2}
                ],
                "boarding_time": None,
                "boarding_cost": None,
                "waiting_time": None
            },
            {
                "description": "Boarded bus/skytrain only",
                "destinations_reachable": False,
                "transition_rules": [
                    {"mode": "b", "next_journey_level": 1},
                    {"mode": "f", "next_journey_level": 1},
                    {"mode": "g", "next_journey_level": 1},
                    {"mode": "h", "next_journey_level": 1},
                    {"mode": "l", "next_journey_level": 1},
                    {"mode": "s", "next_journey_level": 1},
                    {"mode": "r", "next_journey_level": 2}
                ],
                "boarding_time": None,
                "boarding_cost": {
                    "at_nodes": {"penalty": "@wcexferfare", "perception_factor": self.cost_perception_factor},
                    "on_lines": {"penalty": "@xferlinefare","perception_factor": self.cost_perception_factor}
                },
                "waiting_time": None
            },
            {
                "description": "Boarded WCE",
                "destinations_reachable": True,
                "transition_rules": [
                    {"mode": "b", "next_journey_level": 2},
                    {"mode": "f", "next_journey_level": 2},
                    {"mode": "g", "next_journey_level": 2},
                    {"mode": "h", "next_journey_level": 2},
                    {"mode": "l", "next_journey_level": 2},
                    {"mode": "s", "next_journey_level": 2},
                    {"mode": "r", "next_journey_level": 2}
                ],
                "boarding_time": None,
                "boarding_cost": {
                    "at_nodes": {"penalty": "@wcexferfare", "perception_factor": self.cost_perception_factor},
                    "on_lines": {"penalty": "@xferlinefare","perception_factor": self.cost_perception_factor}
                },
                "waiting_time": None
            }
        ]
        return spec

    def calc_network_costs(self, sc):
        util = _m.Modeller().tool("translink.emme.util")

        ## Calculate headway fraction based on service frequency
        # Bus Modes
        # TODO: Check applicable Modes
        util.emme_tline_calc(sc, "@hfrac",    "0 + 0.50000*(hdw)", sel_line="hdw=0,10 and mode=bg")
        util.emme_tline_calc(sc, "@hfrac",    "5 + 0.40000*(hdw - 10)", sel_line="hdw=10,20 and mode=bg")
        util.emme_tline_calc(sc, "@hfrac",    "9 + 0.35000*(hdw - 20)", sel_line="hdw=20,30 and mode=bg")
        util.emme_tline_calc(sc, "@hfrac", "12.5 + 0.08333*(hdw - 30)", sel_line="hdw=30,99 and mode=bg")

        # Rail Modes
        util.emme_tline_calc(sc, "@hfrac",    "0 + 0.50000*(hdw)", sel_line="hdw=0,10 and mode=sfrhl")
        util.emme_tline_calc(sc, "@hfrac",    "5 + 0.15000*(hdw - 10)", sel_line="hdw=10,20 and mode=sfrhl")
        util.emme_tline_calc(sc, "@hfrac",  "6.5 + 0.10000*(hdw - 20)", sel_line="hdw=20,30 and mode=sfrhl")
        util.emme_tline_calc(sc, "@hfrac",  "7.5 + 0.03333*(hdw - 30)", sel_line="hdw=30,99 and mode=sfrhl")

        util.emme_segment_calc(sc, "@hdwyeff", "@hfrac")

        # TODO: By Vehicle type or mode
        util.emme_tline_calc(sc, "@dwtboard", str(self.dwt_board_factor_bus), sel_line="mode=bg")
        util.emme_tline_calc(sc, "@dwtalight", str(self.dwt_alight_factor_bus), sel_line="mode=bg")

    def averaging_transit_volumes(self, sc, iteration):
        util = _m.Modeller().tool("translink.emme.util")
        # MSA on Boardings and transit Volumes
        msa_factor = 1.0 / iteration
        util.emme_segment_calc(sc, "@boardavg" , "board*%s + @boardavg*(1-%s)" %(msa_factor, msa_factor))
        util.emme_segment_calc(sc, "@voltravg", "voltr*%s + @voltravg*(1-%s)" % (msa_factor,  msa_factor))

        # Average Alightings
        util.emme_segment_calc(sc, "@alightavgn" ,"@boardavgn + @voltravg - @voltravgn")

        # Update @pseat and @pstand
        util.emme_segment_calc(sc, "@pseat", "@voltravg.min.@seatcapacity")
        util.emme_segment_calc(sc, "@pstand", "(@voltravg - @seatcapacity).max.0")

    def crowding_factor_calc(self, sc):
        util = _m.Modeller().tool("translink.emme.util")
        # In-vehicle Crowding Function
        crowd_spec = ("((((%s + (%s - %s)*(@voltravg/@totcapacity)^%s)* @pseat +"
                      "(%s + (%s - %s)*(@voltravg/@totcapacity)^%s)* @pstand)"
                      "/(@voltravg +0.01).max.1).min.10)-1")%(self.min_seat_weight, self.max_seat_weight, self.min_seat_weight,
                                                       self.power_seat_weight, self.min_stand_weight,
                                                       self.max_stand_weight, self.min_stand_weight, self.power_stand_weight)

        util.emme_segment_calc(sc, "@crowdingfactor", crowd_spec)
        util.emme_segment_calc(sc, "@ivttfac", "1+ @crowdingfactor")

    def effective_headway_calc(self, sc):
        util = _m.Modeller().tool("translink.emme.util")
        # [(Boardings/max(Total Capacity - Transit Volume + Boardings,1)).min.3.0].max.1
        hdwy_spec = "((@boardavg/((@totcapacity-@voltravg+@boardavg).max.1)).min.(3.0)).max.1"
        util.emme_segment_calc(sc, "@hdwyfac", hdwy_spec)
        util.emme_segment_calc(sc, "@hdwyeff", "@hdwyfac*@hfrac")

    def dwell_time_calc(self, sc, period_length):
        util = _m.Modeller().tool("translink.emme.util")
        # Fixed dwell time to account for acceleration and deceleration of vehicle
        min_dwell_time = 0.33 # 20 seconds in minutes
        # Zero Passenger - set us1 =0
        # Boarding and Alighting happens simultaneously (appplicable for most bus lines)
        util.emme_segment_calc(sc, "us1", "(%s*((@boardavg+@alightavg).gt.0) +"
                                                "(((@dwtboard*@boardavg) .max. (@dwtalight*@alightavg))*"
                                                " hdw/(60*%s)))" %(min_dwell_time,period_length), "all","mode=bg")

        # Boarding and Alighting happens sequentially
        # TODO: Identify lines and specify condition
        #util.emme_segment_calc(sc, "us1", "(%s*((@boardavg+@alightavg).gt.0) +"
        #                                        "(((@dwtboard*@boardavg) + (@dwtalight*@alightavg))*"
        #                                        " hdw/(60*%s)))" %(min_dwell_time,period_length), "all","mode=bg")

    def crowding_headway_report(self, sc, iteration):
        if sc is self.am_scenario or sc is self.pm_scenario:
            summary_mode_list = self.pk_summary_mode_list
        if sc is self.md_scenario:
            summary_mode_list = self.op_summary_mode_list

        if iteration==1:
            print "Iter   Mode     Seat.pass-kms    Stand.pass-kms   Excess.pass-kms  Max.crowd.factor   Min.Hdwy.Factor   Max.Hdwy.Factor"
        networkCalcTool = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")
        expression = {
            # Seating passenger Kms
            1:[ "@pseat*length", "sum"],
            # Standing passenger Kms
            2: ["(@pstand.min.(@totcapacity-@seatcapacity))*length", "sum"],
            # Standing passenger Kms
            3: ["((@pstand-@totcapacity+@seatcapacity).max.0)*length", "sum"],
            # Standing passenger kms
            4:["@crowdingfactor", "maximum"],
            # Min Headway factor
            5: ["@hdwyfac", "minimum"],
            #Max Headway Factor
            6: ["@hdwyfac", "maximum"]}
        result={}
        for modes in summary_mode_list:
            rep = ""
            for key in expression:
                spec = {"type": "NETWORK_CALCULATION",
                        "expression": expression[key][0],
                        "result": "@result",
                        "selections": {
                            "link": "all",
                            "transit_line": "mode="+modes}}
                report=networkCalcTool(spec, scenario = sc, full_report = False)
                rep = rep + ("%s"%(report[expression[key][1]])).rjust(18)
                result["%4s"%iteration+"%7s"%modes]=rep
            print "%4s"%iteration+"%7s"%modes+rep
        return result

    def ridership_summary(self, sc):
        print "Line     RiderShip"
        networkCalcTool = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")
        spec = {"type": "NETWORK_CALCULATION",
                "expression": "@boardavg",
                "result" : "@ridership",
                 "aggregate": "+",
                "selections": {
                     "link": "all",
                     "transit_line": "all"}}
        report=networkCalcTool(spec, scenario = sc, full_report = False)
        print report

    def dwell_time_report(self, sc, iteration):
        if sc is self.am_scenario or sc is self.pm_scenario:
            summary_mode_list = self.pk_summary_mode_list
        if sc is self.md_scenario:
            summary_mode_list = self.op_summary_mode_list

        if iteration == 1:
            print "Iter   Mode     Min.Dwell     Max.Dwell"
        networkCalcTool = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")
        expression = {
            # Min Dwell time
            1: ["us1", "minimum"],
            # Max Dwell Time
            2: ["us1", "maximum"]}
        result = {}
        for modes in summary_mode_list:
            rep = ""
            for key in expression:
                spec = {"type": "NETWORK_CALCULATION",
                        "expression": expression[key][0],
                        "result": "@result",
                        "selections": {
                            "link": "all",
                            "transit_line": "mode=" + modes}}
                report = networkCalcTool(spec, scenario=sc, full_report=False)
                rep = rep + ("%s" % (report[expression[key][1]])).rjust(14)
                result["%4s" % iteration + "%7s" % modes] = rep
            print "%4s" % iteration + "%7s" % modes + rep
        return result

    def get_matrix_skim_spec(self, modes):
        spec = {
            "by_mode_subset": { "modes": modes },
            "type": "EXTENDED_TRANSIT_MATRIX_RESULTS"
        }
        return spec

    def get_strategy_skim_spec(self):
        spec = {
            "trip_components": {
                "boarding": None,
                "in_vehicle": None,
                "alighting": None
            },
            "sub_path_combination_operator": ".max.",
            "sub_strategy_combination_operator": ".max.", # take max as opposed to average to get the full fare not the average
            "selected_demand_and_transit_volumes": {
                "sub_strategies_to_retain": "FROM_COMBINATION_OPERATOR",
                "selection_threshold": {"lower": -999999, "upper": 999999}
            },
            "results" : {"strategy_values": None},
            "type": "EXTENDED_TRANSIT_STRATEGY_ANALYSIS"
        }
        return spec

    def skim_bus(self, scenarionumber):
        util = _m.Modeller().tool("translink.emme.util")
        transit_skim = _m.Modeller().tool("inro.emme.transit_assignment.extended.matrix_results")
        strategy_skim = _m.Modeller().tool("inro.emme.transit_assignment.extended.strategy_based_analysis")

        classname = "Bus"
        modelist = self.bus_mode_list
        Travel_Time_List = ["mf9960", "mf9961", "mf9962", "mf9963", "mf9964", "mf9965", "mf9966"]

        spec_as_dict = self.get_matrix_skim_spec(modelist)
        spec_as_dict["actual_total_waiting_times"] = Travel_Time_List[0]
        spec_as_dict["by_mode_subset"]["actual_in_vehicle_times"] = Travel_Time_List[1]
        spec_as_dict["by_mode_subset"]["actual_aux_transit_times"] = Travel_Time_List[2]
        spec_as_dict["by_mode_subset"]["avg_boardings"] = Travel_Time_List[3]
        spec_as_dict["by_mode_subset"]["actual_first_boarding_costs"] = Travel_Time_List[5]
        transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

        # Skim for FareIncrements
        strat_spec = self.get_strategy_skim_spec()
        strat_spec["trip_components"]["in_vehicle"] = "@fareincrement"
        strat_spec["sub_path_combination_operator"]= "+"
        strat_spec["results"]["strategy_values"] = Travel_Time_List[4]
        strategy_skim(strat_spec, scenario=scenarionumber, class_name=classname)

        # Fare Calculation: Boarding Fare + fare Increment
        specs = []
        specs.append(util.matrix_spec(Travel_Time_List[6], Travel_Time_List[5] + " + " + Travel_Time_List[4]))
        util.compute_matrix(specs, scenarionumber)

    def skim_rail(self, scenarionumber):
        util = _m.Modeller().tool("translink.emme.util")
        transit_skim = _m.Modeller().tool("inro.emme.transit_assignment.extended.matrix_results")
        strategy_skim = _m.Modeller().tool("inro.emme.transit_assignment.extended.strategy_based_analysis")

        classname = "Rail"
        modelist = self.rail_mode_list
        Travel_Time_List = ["mf9970", "mf9971", "mf9972", "mf9973", "mf9974", "mf9975", "mf9976", "mf9977"]

        spec_as_dict = self.get_matrix_skim_spec(modelist)
        spec_as_dict["by_mode_subset"]["actual_total_boarding_times"] = Travel_Time_List[0]
        spec_as_dict["by_mode_subset"]["actual_aux_transit_times"] = Travel_Time_List[1]
        spec_as_dict["actual_total_waiting_times"] = Travel_Time_List[2]
        spec_as_dict["by_mode_subset"]["actual_first_boarding_costs"] = Travel_Time_List[6]
        transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

        spec_as_dict = self.get_matrix_skim_spec(modelist)
        spec_as_dict["by_mode_subset"]["modes"] = ["b", "g"]
        spec_as_dict["by_mode_subset"]["actual_in_vehicle_times"] = Travel_Time_List[3]
        transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

        spec_as_dict = self.get_matrix_skim_spec(modelist)
        spec_as_dict["by_mode_subset"]["modes"] = ["s", "l", "r", "f", "h"]
        spec_as_dict["by_mode_subset"]["actual_in_vehicle_times"] = Travel_Time_List[4]
        transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

        # Skim for Fare Increments: In-vehicle costs
        strat_spec = self.get_strategy_skim_spec()
        strat_spec["trip_components"]["in_vehicle"] = "@fareincrement"
        strat_spec["sub_path_combination_operator"]= "+"
        strat_spec["results"]["strategy_values"] = Travel_Time_List[5]
        strategy_skim(strat_spec, scenario=scenarionumber, class_name=classname)

        # Fare Calculation: Boarding Fare + fare Increment
        specs = []
        specs.append(util.matrix_spec(Travel_Time_List[7], Travel_Time_List[5] + " + " + Travel_Time_List[6]))
        util.compute_matrix(specs, scenarionumber)

    def skim_wce(self, scenarionumber):
        util = _m.Modeller().tool("translink.emme.util")
        transit_skim = _m.Modeller().tool("inro.emme.transit_assignment.extended.matrix_results")
        strategy_skim = _m.Modeller().tool("inro.emme.transit_assignment.extended.strategy_based_analysis")

        classname = "WCE"
        modelist = self.wce_mode_list
        Travel_Time_List = ["mf9980", "mf9981", "mf9982", "mf9983", "mf9984", "mf9985","mf9986", "mf9987", "mf9988", "mf9989"]

        spec_as_dict = self.get_matrix_skim_spec(modelist)
        spec_as_dict["by_mode_subset"]["actual_total_boarding_times"] = Travel_Time_List[0]
        spec_as_dict["by_mode_subset"]["actual_aux_transit_times"] = Travel_Time_List[1]
        spec_as_dict["actual_total_waiting_times"] = Travel_Time_List[2]
        transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

        spec_as_dict = self.get_matrix_skim_spec(modelist)
        spec_as_dict["by_mode_subset"]["modes"] = ["b", "g"]
        spec_as_dict["by_mode_subset"]["actual_in_vehicle_times"] = Travel_Time_List[3]
        transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

        spec_as_dict = self.get_matrix_skim_spec(modelist)
        spec_as_dict["by_mode_subset"]["modes"] = ["s", "l", "f", "h"]
        spec_as_dict["by_mode_subset"]["actual_in_vehicle_times"] = Travel_Time_List[4]
        transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

        spec_as_dict = self.get_matrix_skim_spec(modelist)
        spec_as_dict["by_mode_subset"]["modes"] = ["r"]
        spec_as_dict["by_mode_subset"]["actual_in_vehicle_times"] = Travel_Time_List[5]
        transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

        # Fare Increments for only bus/skytrain
        strat_spec = self.get_strategy_skim_spec()
        strat_spec["trip_components"]["in_vehicle"] = "@fareboundary"
        strat_spec["sub_path_combination_operator"]= "+"
        strat_spec["results"]["strategy_values"] = Travel_Time_List[6]
        strategy_skim(strat_spec, scenario=scenarionumber, class_name=classname)

        # Boarding and Alighting Fare Zone for WCE Fare Calculation
        fzone_spec = self.get_strategy_skim_spec()
        fzone_spec["sub_path_combination_operator"] = ".max."
        fzone_spec["trip_components"]["boarding"] = "@farezone"
        fzone_spec["results"]["strategy_values"] = Travel_Time_List[7]
        strategy_skim(fzone_spec, scenario=scenarionumber, class_name=classname)

        fzone_spec2 = self.get_strategy_skim_spec()
        fzone_spec2["sub_path_combination_operator"] = ".max."
        fzone_spec2["trip_components"]["alighting"] = "@farezone"
        fzone_spec2["results"]["strategy_values"] = Travel_Time_List[8]
        strategy_skim(fzone_spec2, scenario=scenarionumber, class_name=classname)

        # TODO : Fare Calculation: Zone to Zone WCE Fare + bus/skytrain fare Increment
        specs = []
        result = Travel_Time_List[9]
        expression1 = "abs(%s-%s)-100*(%s*%s.eq.0)" %(Travel_Time_List[8],Travel_Time_List[7],
                                                      Travel_Time_List[8],Travel_Time_List[7])

        expression2 = "(%s.lt.0)*0 +(%s.eq.0)*%s +(%s.eq.10)*%s + (%s.eq.20)*%s + (%s.eq.30)*%s + (%s.eq.40)*%s " %(
                                                          result, result, self.wce_fare_zone[1],
                                                          result, self.wce_fare_zone[2], result, self.wce_fare_zone[3],
                                                          result, self.wce_fare_zone[4], result, self.wce_fare_zone[5])
        specs.append(util.matrix_spec(result, expression1))
        specs.append(util.matrix_spec(result, expression2))
        util.compute_matrix(specs, scenarionumber)

    @_m.logbook_trace("Move Skims to Time of Day Locations")
    def collect_skims(self, sc, tod):
        util = _m.Modeller().tool("translink.emme.util")

        if tod == "AM":
            bus_skims =  ["mf5200", "mf5201", "mf5202", "mf5203", "mf5204"]
            rail_skims = ["mf5400", "mf5401", "mf5402", "mf5403", "mf5404", "mf5405"]
            wce_skims =  ["mf5600", "mf5601", "mf5602", "mf5603", "mf5604", "mf5605", "mf5606"]
        if tod == "MD":
            bus_skims =  ["mf5210", "mf5211", "mf5212", "mf5213", "mf5214"]
            rail_skims = ["mf5410", "mf5411", "mf5412", "mf5413", "mf5414", "mf5415"]
            wce_skims =  None
        if tod == "PM":
            bus_skims =  ["mf5220", "mf5221", "mf5222", "mf5223", "mf5224"]
            rail_skims = ["mf5420", "mf5421", "mf5422", "mf5423", "mf5424", "mf5425"]
            wce_skims =  ["mf5620", "mf5621", "mf5622", "mf5623", "mf5624", "mf5625", "mf5626"]

        specs = []
        # Bus Skims
        specs.append(util.matrix_spec(bus_skims[0], "mf9961"))
        specs.append(util.matrix_spec(bus_skims[1], "mf9960"))
        specs.append(util.matrix_spec(bus_skims[2], "mf9962"))
        specs.append(util.matrix_spec(bus_skims[3], "mf9963"))
        specs.append(util.matrix_spec(bus_skims[4], "mf9966"))

        # Rail Skims
        specs.append(util.matrix_spec(rail_skims[0], "mf9974"))
        specs.append(util.matrix_spec(rail_skims[1], "mf9973"))
        specs.append(util.matrix_spec(rail_skims[2], "mf9972"))
        specs.append(util.matrix_spec(rail_skims[3], "mf9971"))
        specs.append(util.matrix_spec(rail_skims[4], "mf9970"))
        specs.append(util.matrix_spec(rail_skims[5], "mf9977"))

        # WCE Skims
        if wce_skims is not None:
            specs.append(util.matrix_spec(wce_skims[0], "mf9985"))
            specs.append(util.matrix_spec(wce_skims[1], "mf9984"))
            specs.append(util.matrix_spec(wce_skims[2], "mf9983"))
            specs.append(util.matrix_spec(wce_skims[3], "mf9982"))
            specs.append(util.matrix_spec(wce_skims[4], "mf9981"))
            specs.append(util.matrix_spec(wce_skims[5], "mf9980"))
            specs.append(util.matrix_spec(wce_skims[6], "mf9989"))

        util.compute_matrix(specs)

    @_m.logbook_trace("Initialize Skim Matrices")
    def matrix_batchins(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        # Bus journey-level assignment
        util.initmat(eb, "mf9960", "eBsWt", "Interim Skim BusTotalWait", 0)
        util.initmat(eb, "mf9961", "eBsIv", "Interim Skim BusIVTT", 0)
        util.initmat(eb, "mf9962", "eBsAx", "Interim Skim BusAux", 0)
        util.initmat(eb, "mf9963", "eBsBr", "Interim Skim BusAvgBoard", 0)
        util.initmat(eb, "mf9964", "eBsBrInc", "Interim Skim BusIncrementalCost", 0)
        util.initmat(eb, "mf9965", "eBsBrCst", "Interim Skim BusFirstBoardCost", 0)
        util.initmat(eb, "mf9966", "eBsBrFare", "Interim Skim BusTotalFare", 0)

        # Rail journey-level assignment
        util.initmat(eb, "mf9970", "nRlBr", "Interim-JL Skim RailAvgBoard", 0)
        util.initmat(eb, "mf9971", "nRlAx", "Interim-JL Skim RailAux", 0)
        util.initmat(eb, "mf9972", "nRlWt", "Interim-JL Skim RailTotalWait", 0)
        util.initmat(eb, "mf9973", "nRBIv", "Interim-JL Skim RailBusIVTT", 0)
        util.initmat(eb, "mf9974", "nRRIv", "Interim-JL Skim RailRailIVTT", 0)
        util.initmat(eb, "mf9975", "nRlco", "Interim-JL Skim Rail Invehicle Cost", 0)
        util.initmat(eb, "mf9976", "nRlbo", "Interim-JL Skim Rail Boarding Cost", 0)
        util.initmat(eb, "mf9977", "nRlfa", "Interim-JL Skim Rail Fare", 0)

        # WCE journey-level assignment
        util.initmat(eb, "mf9980", "WClBr", "Interim-JL Skim WCEAvgBoard", 0)
        util.initmat(eb, "mf9981", "WClAx", "Interim-JL Skim WCEAux", 0)
        util.initmat(eb, "mf9982", "WClWt", "Interim-JL Skim WCETotalWait", 0)
        util.initmat(eb, "mf9983", "WCBIv", "Interim-JL Skim WCEBusIVTT", 0)
        util.initmat(eb, "mf9984", "WCRIv", "Interim-JL Skim WCERailIVTT", 0)
        util.initmat(eb, "mf9985", "WCWIv", "Interim-JL Skim WCEWCEIVTT", 0)
        util.initmat(eb, "mf9986", "WClco", "Interim-JL Skim WCE Invehicle Cost", 0)
        util.initmat(eb, "mf9987", "WClbo", "Interim-JL Skim WCE Boarding Zone", 0)
        util.initmat(eb, "mf9988", "WClal", "Interim-JL Skim WCE Alighting Zone", 0)
        util.initmat(eb, "mf9989", "WClfa", "Interim-JL Skim WCE Fare", 0)
