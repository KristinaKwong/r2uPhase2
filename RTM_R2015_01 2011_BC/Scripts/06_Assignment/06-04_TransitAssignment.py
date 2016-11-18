##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step6.transitassignment
##--Purpose: Transit assignment procedure by Class with Crowding, Capacity, Dwell Time
##---------------------------------------------------------------------

import inro.modeller as _m
import traceback as _traceback

class TransitAssignment(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

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

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Transit Assignment with Crowding and Capacity Constraint"
        pb.description = "Performs Transit Assignments by Class (Bus, Rail, WCE) with Crowding and Capacity Constraint Options"
        pb.branding_text = "TransLink"

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

            self(eb, self.am_scenario, self.md_scenario, self.pm_scenario)
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    _m.logbook_trace("06-04 - Transit Assignment")
    def __call__(self, eb, scenarioam, scenariomd, scenariopm):
        self.matrix_batchins(eb)

        assign_transit = _m.Modeller().tool("inro.emme.transit_assignment.extended_transit_assignment")
        util = _m.Modeller().tool("translink.emme.util")

        run_crowding = 0
        run_capacity_constraint = 0

        # No Crowding and Capacity constraint applied
        # Run 2 iterations only to update dwell times
        if run_crowding+run_capacity_constraint ==0:
            self.max_iterations=2

        # TODO: Select final option and remove this variable
        select_hfrac = 2 # 1 - RTM effective headway fractions, 2 -Non-Linear curves by frequency of service

        demand_bus_list = ["mf218", "mf248", "mf278"]
        demand_rail_list = ["mf219", "mf249", "mf279"]
        # Used for RaType0 assignments
        # TODO add this initialization and allocate final matrix location
        util.initmat(eb, "ms160", "small", "small transit demand", 0.001)
        zero_demand_list = ["ms160", "ms160", "ms160"]
        demand_wce_list = ["mf220", "mf250", "mf280"]

        scenario_list = [scenarioam, scenariomd, scenariopm]
        #TODO: Assignments are done for peak hour
        period_length_list = [1, 1, 1]

        for i, (sc, period_length, demand_bus, demand_rail, demand_wce) in enumerate(zip(scenario_list, period_length_list, demand_bus_list, demand_rail_list, demand_wce_list)):
            self.previous_level = _m.logbook_level()
            print "Scenario: "+sc.title+" ("+sc.id+")"
            report={}
            _m.logbook_level(_m.LogbookLevel.NONE)
            # Initialize Values for first cycle and use updated values from previous cycles later on
            if util.get_cycle(eb) >= 1:  # TODO: Change to util.get_cycle(eb) == 1
                # Calculate headway fraction
                self.headway_fraction_calc(sc, select_hfrac)

                # Intial Assignment of Parameters
                self.update_extra_attributes(sc, '@ivttfac', "1")
                self.update_extra_attributes(sc, '@ivttp_ratype0', "@ivttp")   # Making bus modes more onerous
                self.update_extra_attributes(sc, '@hdwyeff', "hdw*@hfrac")
                self.update_extra_attributes(sc, '@hdwyfac', "1")
                self.update_extra_attributes(sc, '@crowdingfactor', "0")
                self.update_extra_attributes(sc, 'us1', '0')  # dwell time
                self.update_transit_line_attributes(sc, '@seatcapacity', "%s*vcaps*60/hdw" % period_length)
                self.update_transit_line_attributes(sc, '@totcapacity', "%s*vcapt*60/hdw" % period_length)

                # TODO: By Vehicle type or mode
                self.update_transit_line_attributes(sc, '@dwtboard', str(self.dwt_board_factor_bus), "mode=bg")
                self.update_transit_line_attributes(sc, '@dwtalight', str(self.dwt_alight_factor_bus), "mode=bg")

                # Fare Calculations

                # Constant Boarding fare For Buses/Skytrain/Seabus by line
                self.update_transit_line_attributes(sc, '@linefare', str(self.bus_zone1_fare), "mode=bgsfhl")

                # Different boarding fares for WCE by node
                # For First boarding
                self.update_node_attributes(sc, "@wcestopfare", "%s*(@farezone.eq.10)+%s*(@farezone.eq.30)+"
                                                "%s*(@farezone.eq.40)+%s*(@farezone.eq.50)"
                                            %(self.wce_bfare_zone1[i],self.wce_bfare_zone3[i],
                                              self.wce_bfare_zone4[i], self.wce_bfare_zone5[i]))

                # Transfer from Bus/Skytrain
                self.update_node_attributes(sc, "@wcexferfare", "(@wcestopfare - %s).max.0" % self.bus_zone1_fare)

                # In-vehicle Cost (@fareincrement)
                # For Buses/Skytrain/Seabus
                self.update_extra_attributes(sc, '@fareincrement', "%s*(@fareboundary.eq.1)" %self.bus_zone_increment,
                                             nlinks ="all", nlines="mode=bgsfhl")
                # For WCE
                self.update_extra_attributes(sc, '@fareincrement', "%s*(@wcefareboundary.eq.13) +%s*(@wcefareboundary.eq.34)+"
                                             "%s*(@wcefareboundary.eq.45)" %(self.wce_fare_zone13[i], self.wce_fare_zone34[i], self.wce_fare_zone45[i]),
                                             nlinks="all", nlines="mode=r")

            # LOOP FOR CROWDING AND CAPACITY CONSTRAINT
            for iteration in xrange(1, self.max_iterations+1):
                # Restore writing to Logbook
                _m.logbook_level(self.previous_level)

                # Set Assignment Parameters
                bus_spec = self.set_extended_transit_assignment_spec("Bus", demand_bus)
                rail_spec = self.set_extended_transit_assignment_spec("Rail", demand_rail)
                ratype0_spec = self.set_extended_transit_assignment_spec("Ratype0", zero_demand_list[i])
                wce_spec = self.set_extended_transit_assignment_spec("WCE", demand_wce)

                # Run Assignment
                assign_transit(bus_spec, scenario=sc, add_volumes=False, save_strategies=True, class_name= 'Bus')
                assign_transit(rail_spec, scenario=sc, add_volumes=True, save_strategies=True, class_name= 'Rail')
                assign_transit(ratype0_spec, scenario=sc, add_volumes=True, save_strategies=True, class_name='Ratype0')
                if sc is scenarioam or sc is scenariopm:
                    assign_transit(wce_spec, scenario=sc, add_volumes=True, save_strategies=True, class_name= 'WCE')

                _m.logbook_level(_m.LogbookLevel.NONE)

                # MSA on Boardings and transit Volumes
                self.averaging_transit_volumes(sc, iteration)

                # Run Crowding and Headway Reports
                if iteration==1:
                    report['  Iter    Mode'] = "     Seat.pass-kms    Stand.pass-kms   Excess.pass-kms  Max.crowd.factor   Min.Hdwy Factor   Max.Hdwy Factor"
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
            TransitSkim = _m.Modeller().tool("translink.emme.stage3.step7.transitskim")
            TransitSkim(i, sc, classname="Bus")
            TransitSkim(i, sc, classname="Rail")
            TransitSkim(i, sc, classname="Ratype0")
            if sc is not scenariomd:
                TransitSkim(i, sc, classname="WCE")

    def set_extended_transit_assignment_spec(self, assign_mode, triptable):
        ## auxiliary weight: 1.75, waiting time factor: 0.5, wait time weight: 2.25, boarding weight: 4
        if assign_mode == "Bus":
            boarding_time_penalty = 0
            mode_list = self.bus_mode_list
            ivtt_perception = "@ivttfac"

        if assign_mode == "Rail":
            boarding_time_penalty = 1
            mode_list = self.rail_mode_list
            ivtt_perception = "@ivttfac"

        if assign_mode == "Ratype0":
            boarding_time_penalty = 1
            mode_list = self.rail_mode_list
            ivtt_perception = "@ivttp_ratype0"

        if assign_mode == "WCE":
            boarding_time_penalty = 1
            mode_list = self.wce_mode_list
            ivtt_perception = "@ivttfac"

        spec = {
            "modes": mode_list,
            "demand": triptable,
            "waiting_time": {
                "headway_fraction": 1,
                "effective_headways": "@hdwyeff",
                "spread_factor": 1,
                "perception_factor": 2.25
            },
            "boarding_time": {
                "at_nodes": {
                    "penalty": boarding_time_penalty,
                    "perception_factor": 4
                },
                "on_lines": None
            },
            "boarding_cost": {
                "at_nodes": None,
                "on_lines": {"penalty": "@linefare", "perception_factor": self.cost_perception_factor}
            },
            "in_vehicle_time": {
                "perception_factor": ivtt_perception
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
                "number_of_processors": 2
            },
            "type": "EXTENDED_TRANSIT_ASSIGNMENT"
        }

        # Define Flow Distribution settings
        if assign_mode=="Bus":
            spec["flow_distribution_at_origins"]= {
                "choices_at_origins": "OPTIMAL_STRATEGY",
                "fixed_proportions_on_connectors": None
            }
            spec["flow_distribution_at_regular_nodes_with_aux_transit_choices"]= {
                "choices_at_regular_nodes": "OPTIMAL_STRATEGY"
            }

        if assign_mode == "Rail" or assign_mode == "Ratype0" or assign_mode == "WCE":
            spec["flow_distribution_at_origins"]= {
                                            "by_time_to_destination": "BEST_CONNECTOR",
                                            "by_fixed_proportions": None
                                        }
        # Define Journey Levels
        # Journey Level for Bus to account for free transfers between buses
        if assign_mode == "Bus":
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
        # Journey Level for Rail to account for free transfers and must use mode
        if assign_mode == "Rail":
            spec["journey_levels"] =[
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

        # Journey Level for WCE to account for free/reduced transfers and must use mode
        # Free transfers from WCE to Bus/Skytrain
        # Upgrade from Bus/Skytrain to WCE
        if assign_mode == "WCE":
            spec["boarding_cost"] = {
                "at_nodes": {"penalty": "@wcestopfare", "perception_factor": self.cost_perception_factor},
                "on_lines": {"penalty": "@linefare", "perception_factor": self.cost_perception_factor}
            }

            spec["journey_levels"] =[
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

    def update_extra_attributes(self, sc, attr_id, condition, nlinks ="all", nlines="all", aggregate=None):
        networkCalcTool = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")
        spec = {
            "type" : "NETWORK_CALCULATION",
            "result": attr_id,
            "expression": condition,
            "aggregation": aggregate,
            "selections": {"link": nlinks, "transit_line": nlines}
        }
        networkCalcTool(spec, full_report=False, scenario=sc)

    def update_transit_line_attributes(self, sc, attr_id, condition, nlines="all"):
        networkCalcTool = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")
        spec = {
            "type" : "NETWORK_CALCULATION",
            "result": attr_id,
            "expression": condition,
            "aggregation": None,
            "selections": {"transit_line": nlines}
        }
        networkCalcTool(spec, full_report=False, scenario = sc)

    def update_node_attributes(self, sc, attr_id, condition, nodes="all"):
        networkCalcTool = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")
        spec = {
            "type" : "NETWORK_CALCULATION",
            "result": attr_id,
            "expression": condition,
            "aggregation": None,
            "selections": {"node": nodes}
        }
        networkCalcTool(spec, full_report=False, scenario = sc)

    def headway_fraction_calc(self, sc, select_hfrac):
        if select_hfrac ==1:
            ## Option 1: Calculate headway fraction based on following factors:
            ##        "l" rail=0.8,
            ##        "b" bus=1.2,
            ##        "s" seabus=0.67,
            ##        "g" BRT=1.1,
            ##        "f" LRT=1.1,
            ##        "h" Gondola=0.8,
            ##        "r" WCE=0.8
            self.update_extra_attributes(sc, '@hfrac', "1.2*0.5", "all", "mode=b")
            self.update_extra_attributes(sc, '@hfrac', "1.1*0.5", "all", "mode=gf")
            self.update_extra_attributes(sc, '@hfrac', "0.67*0.5", "all", "mode=s")
            self.update_extra_attributes(sc, '@hfrac', "0.8*0.5", "all", "mode=rlh")

        if select_hfrac == 2:
            ## Option 2: Calculate headway fraction based on service frequency
            # Bus Modes
            slope_bus_seg1 = 0.5  #slope for 1st segment (high frequency) bus
            slope_bus_seg2 = 0.40000 # slope for 2nd segemnt (med frequency)  bus
            slope_bus_seg3 = 0.35000 # slope for 3rd segment (low frequency)  bus
            slope_bus_seg4 = 0.08333 # slope for 4th segment (very low freq)  bus
            len_bus_seg1 = 10  # length for 1st segment, bus
            len_bus_seg2 = 10 # length for 2nd segment, bus
            len_bus_seg3 = 10 # length for 3rd segment, bus
            wait_bus_seg1 = len_bus_seg1*slope_bus_seg1   # wait at end of 1st segment, bus
            wait_bus_seg2 = wait_bus_seg1+len_bus_seg2*slope_bus_seg2 # wait at end of 2nd segment, bus
            wait_bus_seg3 = wait_bus_seg2+len_bus_seg3*slope_bus_seg3  # wait at end of 3rd segment, bus
            # TODO: Check applicable Modes
            self.update_extra_attributes(sc, '@hfrac', "((%s*hdw).min.(%s+%s*(hdw-%s)).min."
                                                       "(%s+ %s*(hdw-%s-%s)).min.(%s+%s*(hdw-%s-%s-%s)))/hdw" %(slope_bus_seg1,
                                                        wait_bus_seg1,slope_bus_seg2,len_bus_seg1,
                                                        wait_bus_seg2,slope_bus_seg3, len_bus_seg2,len_bus_seg1,
                                                        wait_bus_seg3,slope_bus_seg4, len_bus_seg3,len_bus_seg2,len_bus_seg1),
                                                        "all", "mode=bg")
            # Rail Modes
            slope_rail_seg1 = 0.50000  # slope for 1st segment (high frequency) rail
            slope_rail_seg2 = 0.15000  # slope for 2nd segemnt (med frequency)  rail
            slope_rail_seg3 = 0.10000  # slope for 3rd segment (low frequency)  rail
            slope_rail_seg4 = 0.03333  # slope for 4th segment (very low freq)  rail
            len_rail_seg1 = 10  # length for 1st segment, rail
            len_rail_seg2 = 10  # length for 2nd segment, rail
            len_rail_seg3 = 10  # length for 3rd segment, rail
            wait_rail_seg1 = len_rail_seg1 * slope_rail_seg1  # wait at end of 1st segment, rail
            wait_rail_seg2 = wait_rail_seg1 + len_rail_seg2 * slope_rail_seg2  # wait at end of 2nd segment, rail
            wait_rail_seg3 = wait_rail_seg2 + len_rail_seg3 * slope_rail_seg3  # wait at end of 3rd segment, rail
            # TODO: Check applicable Modes
            self.update_extra_attributes(sc, '@hfrac', "((%s*hdw).min.(%s+%s*(hdw-%s)).min."
                                                       "(%s+%s*(hdw-%s-%s)).min.(%s+%s*(hdw-%s-%s-%s)))/hdw" % (slope_rail_seg1,
                                                        wait_rail_seg1, slope_rail_seg2, len_rail_seg1,
                                                        wait_rail_seg2, slope_rail_seg3, len_rail_seg2,len_rail_seg1,
                                                        wait_rail_seg3, slope_rail_seg4, len_rail_seg3,len_rail_seg2, len_rail_seg1),
                                                        "all", "mode=sfrhl")

    def averaging_transit_volumes(self, sc, iteration):
        # MSA on Boardings and transit Volumes
        msa_factor = 1.0 / iteration
        self.update_extra_attributes(sc, '@boardavg' , "board*%s + @boardavg*(1-%s)" %(msa_factor, msa_factor))
        self.update_extra_attributes(sc, '@voltravg', "voltr*%s + @voltravg*(1-%s)" % (msa_factor,  msa_factor))

        # Average Alightings
        self.update_extra_attributes(sc, '@alightavgn' ,"@boardavgn + @voltravg - @voltravgn")

        # Update @pseat and @pstand
        self.update_extra_attributes(sc, '@pseat', "@voltravg.min.@seatcapacity")
        self.update_extra_attributes(sc, '@pstand', "(@voltravg - @seatcapacity).max.0")

    def crowding_factor_calc(self, sc):
        # In-vehicle Crowding Function
        crowd_spec = ("((((%s + (%s - %s)*(@voltravg/@totcapacity)^%s)* @pseat +"
                      "(%s + (%s - %s)*(@voltravg/@totcapacity)^%s)* @pstand)"
                      "/(@voltravg +0.01).max.1).min.10)-1")%(self.min_seat_weight, self.max_seat_weight, self.min_seat_weight,
                                                       self.power_seat_weight, self.min_stand_weight,
                                                       self.max_stand_weight, self.min_stand_weight, self.power_stand_weight)

        self.update_extra_attributes(sc, '@crowdingfactor', crowd_spec)
        self.update_extra_attributes(sc, '@ivttfac', "1+ @crowdingfactor")
        #self.update_extra_attributes(sc, '@ivttp_ratype0', "@ivttp*(1+ @crowdingfactor)")

    def effective_headway_calc(self, sc):
        # [(Boardings/max(Total Capacity - Transit Volume + Boardings,1)).min.3.0].max.1
        hdwy_spec = "((@boardavg/((@totcapacity-@voltravg+@boardavg).max.1)).min.(3.0)).max.1"
        self.update_extra_attributes(sc, '@hdwyfac', hdwy_spec)
        self.update_extra_attributes(sc, '@hdwyeff', "hdw*@hdwyfac*@hfrac")

    def dwell_time_calc(self, sc, period_length):
        # Fixed dwell time to account for acceleration and deceleration of vehicle
        min_dwell_time = 0.33 # 20 seconds in minutes
        # Zero Passenger - set us1 =0
        # Boarding and Alighting happens simultaneously (appplicable for most bus lines)
        self.update_extra_attributes(sc, 'us1', "(%s*((@boardavg+@alightavg).gt.0) +"
                                                "(((@dwtboard*@boardavg) .max. (@dwtalight*@alightavg))*"
                                                " hdw/(60*%s)))" %(min_dwell_time,period_length), "all","mode=bg")

        # Boarding and Alighting happens sequentially
        # TODO: Identify lines and specify condition
        #self.update_extra_attributes(sc, 'us1', "(%s*((@boardavg+@alightavg).gt.0) +"
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
                        "result": '@result',
                        "selections": {
                            "link": "all",
                            "transit_line": "mode="+modes}}
                report=networkCalcTool(spec, scenario = sc, full_report = False)
                rep = rep + ("%s"%(report[expression[key][1]])).rjust(18)
                result['%4s'%iteration+'%7s'%modes]=rep
            print '%4s'%iteration+'%7s'%modes+rep
        return result

    def ridership_summary(self, sc):
        print "Line     RiderShip"
        networkCalcTool = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")
        spec = {"type": "NETWORK_CALCULATION",
                "expression": "@boardavg",
                "result" : '@ridership',
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
                        "result": '@result',
                        "selections": {
                            "link": "all",
                            "transit_line": "mode=" + modes}}
                report = networkCalcTool(spec, scenario=sc, full_report=False)
                rep = rep + ("%s" % (report[expression[key][1]])).rjust(14)
                result['%4s' % iteration + '%7s' % modes] = rep
            print '%4s' % iteration + '%7s' % modes + rep
        return result

    @_m.logbook_trace("Matrix Batchin")
    def matrix_batchins(self, eb):
        util = _m.Modeller().tool("translink.emme.util")
        #TODO initialize matrices for bus and rail skims- remove the initialization from auto assignment
        #TODO: Update matrix numbers
        util.initmat(eb, "mf933", "eBsWtA", "Interim Skim BusTotalWaitAM", 0)
        util.initmat(eb, "mf934", "eBsIvA", "Interim Skim BusIVTTAM", 0)
        util.initmat(eb, "mf935", "eBsBrA", "Interim Skim BusAvgBoardAM", 0)
        util.initmat(eb, "mf936", "eBsAxA", "Interim Skim BusAuxAM", 0)
        util.initmat(eb, "mf945", "eBsWtM", "Interim Skim BusTotalWaitMD", 0)
        util.initmat(eb, "mf946", "eBsIvM", "Interim Skim BusIVTTMD", 0)
        util.initmat(eb, "mf947", "eBsBrM", "Interim Skim BusAvgBoardMD", 0)
        util.initmat(eb, "mf948", "eBsAxM", "Interim Skim BusAuxMD", 0)
        util.initmat(eb, "mf2003", "eBsWtP", "Interim Skim BusTotalWaitPM", 0)
        util.initmat(eb, "mf2004", "eBsIvP", "Interim Skim BusIVTTPM", 0)
        util.initmat(eb, "mf2005", "eBsBrP", "Interim Skim BusAvgBoardPM", 0)
        util.initmat(eb, "mf2006", "eBsAxP", "Interim Skim BusAuxPM", 0)

        ## Initialize new block used for journey-level assignment
        util.initmat(eb, "mf1070", "nRBIvA", "Interim-JL Skim RailBusIVTTAM", 0)
        util.initmat(eb, "mf1071", "nRRIvA", "Interim-JL Skim RailRailIVTTAM", 0)
        util.initmat(eb, "mf1072", "nRlWtA", "Interim-JL Skim RailTotalWaitAM", 0)
        util.initmat(eb, "mf1073", "nRlBrA", "Interim-JL Skim RailAvgBoardAM", 0)
        util.initmat(eb, "mf1074", "nRlAxA", "Interim-JL Skim RailAuxAM", 0)
        util.initmat(eb, "mf7030", "nRlcoA", "Interim-JL Skim Rail Invehicle Cost AM", 0)
        util.initmat(eb, "mf7031", "nRlboA", "Interim-JL Skim Rail Boarding Cost AM", 0)
        util.initmat(eb, "mf7032", "nRlfaA", "Interim-JL Skim Rail Fare AM", 0)

        util.initmat(eb, "mf1075", "nRBIvM", "Interim-JL Skim RailBusIVTTMD", 0)
        util.initmat(eb, "mf1076", "nRRIvM", "Interim-JL Skim RailRailIVTTMD", 0)
        util.initmat(eb, "mf1077", "nRlWtM", "Interim-JL Skim RailTotalWaitMD", 0)
        util.initmat(eb, "mf1078", "nRlBrM", "Interim-JL Skim RailAvgBoardMD", 0)
        util.initmat(eb, "mf1079", "nRlAxM", "Interim-JL Skim RailAuxMD", 0)
        util.initmat(eb, "mf7040", "nRlcoM", "Interim-JL Skim Rail Invehicle Cost MD", 0)
        util.initmat(eb, "mf7041", "nRlboM", "Interim-JL Skim Rail Boarding Cost MD", 0)
        util.initmat(eb, "mf7042", "nRlfaM", "Interim-JL Skim Rail Fare MD", 0)

        util.initmat(eb, "mf2016", "nRBIvP", "Interim-JL Skim RailBusIVTTPM", 0)
        util.initmat(eb, "mf2017", "nRRIvP", "Interim-JL Skim RailRailIVTTPM", 0)
        util.initmat(eb, "mf2018", "nRlWtP", "Interim-JL Skim RailTotalWaitPM", 0)
        util.initmat(eb, "mf2019", "nRlBrP", "Interim-JL Skim RailAvgBoardPM", 0)
        util.initmat(eb, "mf2020", "nRlAxP", "Interim-JL Skim RailAuxPM", 0)
        util.initmat(eb, "mf7050", "nRlcoP", "Interim-JL Skim Rail Invehicle Cost PM", 0)
        util.initmat(eb, "mf7051", "nRlboP", "Interim-JL Skim Rail Boarding Cost PM", 0)
        util.initmat(eb, "mf7052", "nRlfaP", "Interim-JL Skim Rail Fare PM", 0)

        ## Initialize new block used for WCE journey-level assignment
        util.initmat(eb, "mf5050", "WClBrA", "Interim-JL Skim WCEAvgBoardAM", 0)
        util.initmat(eb, "mf5051", "WClAxA", "Interim-JL Skim WCEAuxAM", 0)
        util.initmat(eb, "mf5052", "WClWtA", "Interim-JL Skim WCETotalWaitAM", 0)
        util.initmat(eb, "mf5053", "WCBIvA", "Interim-JL Skim WCEBusIVTTAM", 0)
        util.initmat(eb, "mf5054", "WCRIvA", "Interim-JL Skim WCERailIVTTAM", 0)
        util.initmat(eb, "mf5055", "WCWIvA", "Interim-JL Skim WCEWCEIVTTAM", 0)
        util.initmat(eb, "mf7060", "WClcoA", "Interim-JL Skim WCE Invehicle Cost AM", 0)
        util.initmat(eb, "mf7061", "WClboA", "Interim-JL Skim WCE Boarding Zone AM", 0)
        util.initmat(eb, "mf7062", "WClalA", "Interim-JL Skim WCE Alighting Zone AM", 0)
        util.initmat(eb, "mf7063", "WClfaA", "Interim-JL Skim WCE Fare AM", 0)

        util.initmat(eb, "mf5056", "WClBrM", "Interim-JL Skim WCEAvgBoardMD", 0)
        util.initmat(eb, "mf5057", "WClAxM", "Interim-JL Skim WCEAuxMD", 0)
        util.initmat(eb, "mf5058", "WClWtM", "Interim-JL Skim WCETotalWaitMD", 0)
        util.initmat(eb, "mf5059", "WCBIvM", "Interim-JL Skim WCEBusIVTTMD", 0)
        util.initmat(eb, "mf5060", "WCRIvM", "Interim-JL Skim WCERailIVTTMD", 0)
        util.initmat(eb, "mf5061", "WCWIvM", "Interim-JL Skim WCEWCEIVTTMD", 0)
        util.initmat(eb, "mf7070", "WClcoM", "Interim-JL Skim WCE Invehicle Cost MD", 0)
        util.initmat(eb, "mf7071", "WClboM", "Interim-JL Skim WCE Boarding Zone MD", 0)
        util.initmat(eb, "mf7072", "WClalM", "Interim-JL Skim WCE Alighting Zone MD", 0)
        util.initmat(eb, "mf7073", "WClfaM", "Interim-JL Skim WCE Fare MD", 0)

        util.initmat(eb, "mf5062", "WClBrP", "Interim-JL Skim WCEAvgBoardPM", 0)
        util.initmat(eb, "mf5063", "WClAxP", "Interim-JL Skim WCEAuxPM", 0)
        util.initmat(eb, "mf5064", "WClWtP", "Interim-JL Skim WCETotalWaitPM", 0)
        util.initmat(eb, "mf5065", "WCBIvP", "Interim-JL Skim WCEBusIVTTPM", 0)
        util.initmat(eb, "mf5066", "WCRIvP", "Interim-JL Skim WCERailIVTTPM", 0)
        util.initmat(eb, "mf5067", "WCWIvP", "Interim-JL Skim WCEWCEIVTTPM", 0)
        util.initmat(eb, "mf7080", "WClcoP", "Interim-JL Skim WCE Invehicle Cost PM", 0)
        util.initmat(eb, "mf7081", "WClboP", "Interim-JL Skim WCE Boarding Zone PM", 0)
        util.initmat(eb, "mf7082", "WClalP", "Interim-JL Skim WCE Alighting Zone PM", 0)
        util.initmat(eb, "mf7083", "WClfaP", "Interim-JL Skim WCE Fare PM", 0)

        # Intialize Mode Availability Matrices
        util.initmat(eb, "mf7003", "BsAvailAM", "Bus Availability Matrix AM", 1)
        util.initmat(eb, "mf7013", "BsAvailMD", "Bus Availability Matrix MD", 1)
        util.initmat(eb, "mf7023", "BsAvailPM", "Bus Availability Matrix PM", 1)
        util.initmat(eb, "mf7033", "RlAvailAM", "Rail Availability Matrix AM", 1)
        util.initmat(eb, "mf7043", "RlAvailMD", "Rail Availability Matrix MD", 1)
        util.initmat(eb, "mf7053", "RlAvailPM", "Rail Availability Matrix PM", 1)
        util.initmat(eb, "mf7064", "WCAvailAM", "WCE Availability Matrix AM", 1)
        util.initmat(eb, "mf7074", "WCAvailMD", "WCE Availability Matrix MD", 1)
        util.initmat(eb, "mf7084", "WCAvailPM", "WCE Availability Matrix PM", 1)