##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage3.transitassignment
##--Purpose: Transit assignment procedure by Class with Crowding, Capacity, Dwell Time
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback
import numpy as np
import pandas as pd

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
        self.max_iterations = 10
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
        self.dwt_alight_factor_bus = 0.0083 # 0.5 sec per alighting

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


        self.cost_perception_factor = 4.90

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
        util = _m.Modeller().tool("translink.util")
        self.tool_run_msg = ""
        try:
            eb = _m.Modeller().emmebank
            am_scen, md_scen, pm_scen = util.get_tod_scenarios(eb)

            eb.matrix("ms45").data = int(self.run_congested_transit)
            eb.matrix("ms46").data = int(self.run_capacited_transit)

            self(eb, am_scen, md_scen, pm_scen)
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Transit Assignment")
    def __call__(self, eb, scenarioam, scenariomd, scenariopm, disable_congestion=False):

        util = _m.Modeller().tool("translink.util")
        self.am_scenario = scenarioam
        self.md_scenario = scenariomd
        self.pm_scenario = scenariopm
        self.init_matrices(eb)

        # update fares from scalar matrices - allow for change of fares
        self.bus_zone1_fare = eb.matrix("oneZoneFare").data
        self.bus_zone_increment = eb.matrix("fareIncrement").data

        # By Time Period [AM, MD, PM]
        # zone_timeperiod 1=AM, 2=MD, 3=PM
        self.wce_bfare_zone1 = [eb.matrix("wce_bfare_zone1_1").data,
                                eb.matrix("wce_bfare_zone1_2").data,
                                eb.matrix("wce_bfare_zone1_3").data]
        self.wce_bfare_zone3 = [eb.matrix("wce_bfare_zone3_1").data,
                                eb.matrix("wce_bfare_zone3_2").data,
                                eb.matrix("wce_bfare_zone3_3").data]
        self.wce_bfare_zone4 = [eb.matrix("wce_bfare_zone4_1").data,
                                eb.matrix("wce_bfare_zone4_2").data,
                                eb.matrix("wce_bfare_zone4_3").data]
        self.wce_bfare_zone5 = [eb.matrix("wce_bfare_zone5_1").data,
                                eb.matrix("wce_bfare_zone5_2").data,
                                eb.matrix("wce_bfare_zone5_3").data]
        self.wce_bfare_zone13 = [eb.matrix("wce_bfare_zone13_1").data,
                                 eb.matrix("wce_bfare_zone13_2").data,
                                 eb.matrix("wce_bfare_zone13_3").data]                
        self.wce_bfare_zone34 = [eb.matrix("wce_bfare_zone34_1").data,
                                 eb.matrix("wce_bfare_zone34_2").data,
                                 eb.matrix("wce_bfare_zone34_3").data]
        self.wce_bfare_zone45 = [eb.matrix("wce_bfare_zone45_1").data,
                                 eb.matrix("wce_bfare_zone45_2").data,
                                 eb.matrix("wce_bfare_zone45_3").data]

        self.wce_fare_zone = {1: eb.matrix("wce_fare_1z").data, 
                              2: eb.matrix("wce_fare_2z").data, 
                              3: eb.matrix("wce_fare_3z").data, 
                              4: eb.matrix("wce_fare_4z").data, 
                              5: eb.matrix("wce_fare_5z").data}

        # TODO fix this numbered matrix reference
        self.num_processors = int(eb.matrix("ms12").data)
        assign_transit = _m.Modeller().tool("inro.emme.transit_assignment.extended_transit_assignment")

        create_attr = _m.Modeller().tool("inro.emme.data.extra_attribute.create_extra_attribute")

        if disable_congestion:
            run_crowding = 0
            run_capacity_constraint = 0
        else:
            run_crowding = int(eb.matrix("ms45").data)
            run_capacity_constraint = int(eb.matrix("ms46").data)

        # No Crowding and Capacity constraint applied
        # Run 2 iterations only to update dwell times
        if run_crowding+run_capacity_constraint ==0:
            self.max_iterations=2

        demand_bus_list  = [ "mfbusAm",  "mfbusMd",  "mfbusPm"]
        demand_rail_list = ["mfrailAm", "mfrailMd", "mfrailPm"]
        demand_wce_list  = [ "mfWCEAm",  "mfWCEMd",  "mfWCEPm"]

        scenario_list = [scenarioam, scenariomd, scenariopm]
        #TODO: Assignments are done for peak hour
        period_length_list = [1, 1, 1]

        for i, (sc, period_length, demand_bus, demand_rail, demand_wce) in enumerate(zip(scenario_list, period_length_list, demand_bus_list, demand_rail_list, demand_wce_list)):
            report={}
            self.calc_network_costs(sc, period_length, i)

            # LOOP FOR CROWDING AND CAPACITY CONSTRAINT
            for iteration in xrange(1, self.max_iterations+1):
                # Set Assignment Parameters
                bus_spec  = self.get_bus_transit_assignment_spec(demand_bus)
                rail_spec = self.get_rail_transit_assignment_spec(demand_rail)
                wce_spec  = self.get_wce_transit_assignment_spec(demand_wce)

                # Run Assignment
                assign_transit(bus_spec, scenario=sc, add_volumes=False, save_strategies=True, class_name= "Bus")
                assign_transit(rail_spec, scenario=sc, add_volumes=True, save_strategies=True, class_name= "Rail")
                if sc is scenarioam or sc is scenariopm:
                    assign_transit(wce_spec, scenario=sc, add_volumes=True, save_strategies=True, class_name= "WCE")

                # MSA on Boardings and transit Volumes
                self.averaging_transit_volumes(sc, iteration, period_length)

                # Run Crowding and Headway Reports
                self.crowding_headway_report(sc, report, iteration)

                # Update Capacity, Crowding Functions
                if run_crowding==1:
                    self.crowding_factor_calc(sc)

                if run_capacity_constraint==1:
                    self.effective_headway_calc(sc)

            # Write Logbook entries for crowding and Headway
            _m.logbook_write("Crowding and Headway report for Scenario: "+sc.id, attributes=report, value=sc.title)

            if sc is scenarioam:
                self.collect_skims(sc, "AM")
            if sc is scenariomd:
                self.collect_skims(sc, "MD")
            if sc is scenariopm:
                self.collect_skims(sc, "PM")

        # now that the skims have been written back, delete the temporary matrices
        for matrix in self.get_temp_matrices():
            util.delmat(eb, matrix[0])

        # add transit volumes and capacity to links for export
        for scenario in scenario_list:

            # transit volume
            create_attr("LINK", "@voltr", "Total Transit Volume on Link", 0, True, scenario)
            create_attr("TRANSIT_SEGMENT", "@alight", "alightings", 0, True, scenario)
            util.emme_segment_calc(scenario, "@voltr", "voltr", sel_link="all",aggregate= "+")
            util.emme_segment_calc(scenario, "@alightn", "(boardn + voltr - voltrn)")

            # transit capacity
            create_attr("LINK", "@tran_cap", "Transit Capacity", 0, True, scenario)
            util.emme_segment_calc(scenario, "@tran_cap", "@totcapacity",aggregate= "+")

    def get_common_transit_assignment_spec(self, modes, demand):
        spec = {
            "modes": modes,
            "demand": demand,
            "waiting_time": {
                "headway_fraction": 1,
                "effective_headways": "@hdwyeff",
                "spread_factor": 1,
                "perception_factor": 2.50
            },
            "boarding_time": {
                "at_nodes": {
                    "penalty": 1,
                    "perception_factor":10.00
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
                "perception_factor": 2.00
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

    @_m.logbook_trace("Calculate Initial Transit Network Costs")
    def calc_network_costs(self, sc, period_length, i):
        util = _m.Modeller().tool("translink.util")

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

        # TODO: By Vehicle type or mode
        util.emme_tline_calc(sc, "@dwtboard", str(self.dwt_board_factor_bus), sel_line="mode=bg")
        util.emme_tline_calc(sc, "@dwtalight", str(self.dwt_alight_factor_bus), sel_line="mode=bg")

        util.emme_tline_calc(sc, "@seatcapacity", "%s*vcaps*60/hdw" % period_length)
        util.emme_tline_calc(sc, "@totcapacity",  "%s*vcapt*60/hdw" % period_length)


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


        # Intial Assignment of Parameters
        util.emme_segment_calc(sc, "us1", "0")  # dwell time
        util.emme_segment_calc(sc, "@ivttfac", "1")
        util.emme_segment_calc(sc, "@hdwyfac", "1")
        util.emme_segment_calc(sc, "@hdwyeff", "@hdwyfac*@hfrac")
        util.emme_tline_calc(sc, "@ivtp", "0.25", sel_line="mode=bg")


        # Initialize volume averaging parameters
        util.emme_segment_calc(sc, "@boardavg", "0")
        util.emme_segment_calc(sc, "@alightavg", "0")
        util.emme_segment_calc(sc, "@voltravg", "0")
        util.emme_segment_calc(sc, "@pseat", "0")
        util.emme_segment_calc(sc, "@pstand", "0")
        util.emme_segment_calc(sc, "@ridership", "@boardavg", aggregate="+")

    @_m.logbook_trace("Transit Volume Averaging")
    def averaging_transit_volumes(self, sc, iteration, period_length):
        util = _m.Modeller().tool("translink.util")

        # MSA on Boardings and transit Volumes
        msa_factor = 1.0 / iteration
        util.emme_segment_calc(sc, "@boardavg" , "board*%s + @boardavg*(1-%s)" %(msa_factor, msa_factor))
        util.emme_segment_calc(sc, "@voltravg", "voltr*%s + @voltravg*(1-%s)" % (msa_factor,  msa_factor))


        # Average Alightings
        util.emme_segment_calc(sc, "@alightavgn" ,"@boardavgn + @voltravg - @voltravgn")

        # Update @pseat and @pstand
        util.emme_segment_calc(sc, "@pseat", "@voltravg.min.@seatcapacity")
        util.emme_segment_calc(sc, "@pstand", "(@voltravg - @seatcapacity).max.0")

        # Update ridership stats
        util.emme_segment_calc(sc, "@ridership", "@boardavg", aggregate="+")

        # Dwell time calculation
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

    @_m.logbook_trace("Calculate Crowding Factor")
    def crowding_factor_calc(self, sc):
        util = _m.Modeller().tool("translink.util")
        # In-vehicle Crowding Function
        crowd_spec = ("((((%s + (%s - %s)*(@voltravg/@totcapacity)^%s)* @pseat +"
                      "(%s + (%s - %s)*(@voltravg/@totcapacity)^%s)* @pstand)"
                      "/(@voltravg +0.01).max.1).min.10)")%(self.min_seat_weight, self.max_seat_weight, self.min_seat_weight,
                                                       self.power_seat_weight, self.min_stand_weight,
                                                       self.max_stand_weight, self.min_stand_weight, self.power_stand_weight)

        util.emme_segment_calc(sc, "@ivttfac", crowd_spec)
        util.emme_segment_calc(sc, "@ivttfac", "@ivttfac + @ivtp")

    @_m.logbook_trace("Calculate Effective Headway for Capacity Constraint")
    def effective_headway_calc(self, sc):
        util = _m.Modeller().tool("translink.util")
        # [(Boardings/max(Total Capacity - Transit Volume + Boardings,1)).min.3.0].max.1
        util.emme_segment_calc(sc, "@hdwyfac", "((@boardavg/((@totcapacity-@voltravg+@boardavg).max.1)).min.(3.0)).max.1")
        util.emme_segment_calc(sc, "@hdwyeff", "@hdwyfac*@hfrac")

    @_m.logbook_trace("Calculate Crowding and Effective Headway report")
    def crowding_headway_report(self, sc, report, iteration):
        util = _m.Modeller().tool("translink.util")

        if sc is self.am_scenario or sc is self.pm_scenario:
            summary_mode_list = self.pk_summary_mode_list
        if sc is self.md_scenario:
            summary_mode_list = self.op_summary_mode_list

        if iteration==1:
            report["Iter   Mode"] = "     Seat.pass-kms    Stand.pass-kms   Excess.pass-kms  Max.crowd.factor   Min.Hdwy Factor   Max.Hdwy Factor         Min.Dwell         Max.Dwell"

        for modes in summary_mode_list:
            rep = ""
            line_selection = "mode=" + modes

            seg_rep = util.emme_segment_calc(sc, None, "@pseat*length", sel_line=line_selection)
            rep += "%18s" % seg_rep["sum"]

            seg_rep = util.emme_segment_calc(sc, None, "(@pstand.min.(@totcapacity-@seatcapacity))*length", sel_line=line_selection)
            rep += "%18s" % seg_rep["sum"]

            seg_rep = util.emme_segment_calc(sc, None, "(((@pstand-@totcapacity+@seatcapacity).max.0)*length)", sel_line=line_selection)
            rep += "%18s" % seg_rep["sum"]

            seg_rep = util.emme_segment_calc(sc, None, "(@ivttfac - 1)", sel_line=line_selection)
            rep += "%18s" % seg_rep["maximum"]

            seg_rep = util.emme_segment_calc(sc, None, "@hdwyfac", sel_line=line_selection)
            rep += "%18s" % seg_rep["minimum"]
            rep += "%18s" % seg_rep["maximum"]

            seg_rep = util.emme_segment_calc(sc, None, "us1", sel_line=line_selection)
            rep += "%18s" % seg_rep["minimum"]
            rep += "%18s" % seg_rep["maximum"]

            iter_label = "%4s%7s" % (iteration, modes)
            report[iter_label] = rep

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

        eb = _m.Modeller().emmebank
        util = _m.Modeller().tool("translink.util")
        transit_skim = _m.Modeller().tool("inro.emme.transit_assignment.extended.matrix_results")
        strategy_skim = _m.Modeller().tool("inro.emme.transit_assignment.extended.strategy_based_analysis")

        classname = "Bus"
        modelist = self.bus_mode_list

        spec_as_dict = self.get_matrix_skim_spec(modelist)
        spec_as_dict["actual_total_waiting_times"] = "mfBusWait"
        spec_as_dict["by_mode_subset"]["actual_in_vehicle_times"] = "mfBusIvtt"
        spec_as_dict["by_mode_subset"]["actual_aux_transit_times"] = "mfBusAux"
        spec_as_dict["by_mode_subset"]["avg_boardings"] = "mfBusBoard"
        spec_as_dict["by_mode_subset"]["actual_first_boarding_costs"] = "mfBusIncFirstCost"
        transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

        # Skim for FareIncrements
        strat_spec = self.get_strategy_skim_spec()
        strat_spec["trip_components"]["in_vehicle"] = "@fareincrement"
        strat_spec["sub_path_combination_operator"]= "+"
        strat_spec["results"]["strategy_values"] = "mfBusIncCst"
        strategy_skim(strat_spec, scenario=scenarionumber, class_name=classname)

        # Fare Calculation: Boarding Fare + fare Increment
        specs = []
        specs.append(util.matrix_spec("mfBusFare", "mfBusIncCst + mfBusIncFirstCost"))
        util.compute_matrix(specs, scenarionumber)

        # Correct skims
        transit_mode = "bus"
        fare_skim = "mfBusFare"
        self.fix_skims(eb, transit_mode, fare_skim)

    def skim_rail(self, scenarionumber):

        eb = _m.Modeller().emmebank
        util = _m.Modeller().tool("translink.util")
        transit_skim = _m.Modeller().tool("inro.emme.transit_assignment.extended.matrix_results")
        strategy_skim = _m.Modeller().tool("inro.emme.transit_assignment.extended.strategy_based_analysis")

        classname = "Rail"
        modelist = self.rail_mode_list

        spec_as_dict = self.get_matrix_skim_spec(modelist)
        spec_as_dict["by_mode_subset"]["actual_total_boarding_times"] = "mfRailBoard"
        spec_as_dict["by_mode_subset"]["actual_aux_transit_times"] = "mfRailAux"
        spec_as_dict["actual_total_waiting_times"] = "mfRailWait"
        spec_as_dict["by_mode_subset"]["actual_first_boarding_costs"] = "mfRailBrdCst"
        transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

        spec_as_dict = self.get_matrix_skim_spec(modelist)
        spec_as_dict["by_mode_subset"]["modes"] = ["b", "g"]
        spec_as_dict["by_mode_subset"]["actual_in_vehicle_times"] = "mfRailIvttBus"
        transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

        spec_as_dict = self.get_matrix_skim_spec(modelist)
        spec_as_dict["by_mode_subset"]["modes"] = ["s", "l", "r", "f", "h"]
        spec_as_dict["by_mode_subset"]["actual_in_vehicle_times"] = "mfRailIvtt"
        transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

        # Skim for Fare Increments: In-vehicle costs
        strat_spec = self.get_strategy_skim_spec()
        strat_spec["trip_components"]["in_vehicle"] = "@fareincrement"
        strat_spec["sub_path_combination_operator"]= "+"
        strat_spec["results"]["strategy_values"] = "mfRailIvCst"
        strategy_skim(strat_spec, scenario=scenarionumber, class_name=classname)

        # Fare Calculation: Boarding Fare + fare Increment
        specs = []
        specs.append(util.matrix_spec("mfRailFare", "mfRailIvCst + mfRailBrdCst"))
        util.compute_matrix(specs, scenarionumber)

        # Correct skims
        transit_mode = "rail"
        fare_skim = "mfRailFare"
        self.fix_skims(eb, transit_mode, fare_skim)

    def skim_wce(self, scenarionumber):

        eb = _m.Modeller().emmebank
        util = _m.Modeller().tool("translink.util")
        transit_skim = _m.Modeller().tool("inro.emme.transit_assignment.extended.matrix_results")
        strategy_skim = _m.Modeller().tool("inro.emme.transit_assignment.extended.strategy_based_analysis")

        classname = "WCE"
        modelist = self.wce_mode_list

        spec_as_dict = self.get_matrix_skim_spec(modelist)
        spec_as_dict["by_mode_subset"]["actual_total_boarding_times"] = "mfWceBoard"
        spec_as_dict["by_mode_subset"]["actual_aux_transit_times"] = "mfWceAux"
        spec_as_dict["actual_total_waiting_times"] = "mfWceWait"
        transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

        spec_as_dict = self.get_matrix_skim_spec(modelist)
        spec_as_dict["by_mode_subset"]["modes"] = ["b", "g"]
        spec_as_dict["by_mode_subset"]["actual_in_vehicle_times"] = "mfWceIvttBus"
        transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

        spec_as_dict = self.get_matrix_skim_spec(modelist)
        spec_as_dict["by_mode_subset"]["modes"] = ["s", "l", "f", "h"]
        spec_as_dict["by_mode_subset"]["actual_in_vehicle_times"] = "mfWceIvttRail"
        transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

        spec_as_dict = self.get_matrix_skim_spec(modelist)
        spec_as_dict["by_mode_subset"]["modes"] = ["r"]
        spec_as_dict["by_mode_subset"]["actual_in_vehicle_times"] = "mfWceIvtt"
        transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

        # Fare Increments for only bus/skytrain
        strat_spec = self.get_strategy_skim_spec()
        strat_spec["trip_components"]["in_vehicle"] = "@fareboundary"
        strat_spec["sub_path_combination_operator"]= "+"
        strat_spec["results"]["strategy_values"] = "mfWceIvCst"
        strategy_skim(strat_spec, scenario=scenarionumber, class_name=classname)

        # Boarding and Alighting Fare Zone for WCE Fare Calculation
        fzone_spec = self.get_strategy_skim_spec()
        fzone_spec["sub_path_combination_operator"] = ".max."
        fzone_spec["trip_components"]["boarding"] = "@farezone"
        fzone_spec["results"]["strategy_values"] = "mfWceBrdZone"
        strategy_skim(fzone_spec, scenario=scenarionumber, class_name=classname)

        fzone_spec2 = self.get_strategy_skim_spec()
        fzone_spec2["sub_path_combination_operator"] = ".max."
        fzone_spec2["trip_components"]["alighting"] = "@farezone"
        fzone_spec2["results"]["strategy_values"] = "mfWceAliZone"
        strategy_skim(fzone_spec2, scenario=scenarionumber, class_name=classname)

        # TODO : Fare Calculation: Zone to Zone WCE Fare + bus/skytrain fare Increment
        specs = []
        result = "mfWceFare"
        expression1 = "abs(mfWceAliZone - mfWceBrdZone)-100*(mfWceAliZone * mfWceBrdZone.eq.0)"

        expression2 = "(%s.lt.0)*0 +(%s.eq.0)*%s +(%s.eq.10)*%s + (%s.eq.20)*%s + (%s.eq.30)*%s + (%s.eq.40)*%s " %(
                                                          result, result, self.wce_fare_zone[1],
                                                          result, self.wce_fare_zone[2], result, self.wce_fare_zone[3],
                                                          result, self.wce_fare_zone[4], result, self.wce_fare_zone[5])
        specs.append(util.matrix_spec(result, expression1))
        specs.append(util.matrix_spec(result, expression2))
        util.compute_matrix(specs, scenarionumber)

    def fix_skims(self, eb, transit_mode, fare_skim):

        util = _m.Modeller().tool("translink.util")

        #  get existing fares zones (matrix based)
        NoTAZ = len(util.get_matrix_numpy(eb, "zoneindex"))
        Fare_Mat = util.get_matrix_numpy(eb, fare_skim)

        Crossed_Zones = util.get_matrix_numpy(eb, "mffare_zones")
        Max_Fare = (Crossed_Zones - 1)*self.bus_zone_increment + self.bus_zone1_fare

        Fare_Mat = np.where(Fare_Mat >= Max_Fare, Max_Fare, Fare_Mat)

        util.set_matrix_numpy(eb, fare_skim, Fare_Mat)

    @_m.logbook_trace("Generate and Move Skims to Time of Day Locations")
    def collect_skims(self, sc, tod):
        util = _m.Modeller().tool("translink.util")

        # Create Skims
        self.skim_bus(sc)
        self.skim_rail(sc)
        if not tod == "MD":
            self.skim_wce(sc)

        if tod == "AM":
            bus_skims =  ["mfAmBusIvtt", "mfAmBusWait", "mfAmBusAux", "mfAmBusBoard", "mfAmBusFare"]
            rail_skims = ["mfAmRailIvtt", "mfAmRailIvttBus", "mfAmRailWait", "mfAmRailAux", "mfAmRailBoard", "mfAmRailFare"]
            wce_skims =  ["mfAmWceIvtt", "mfAmWceIvttRail", "mfAmWceIvttBus", "mfAmWceWait", "mfAmWceAux", "mfAmWceBoard", "mfAmWceFare"]
        if tod == "MD":
            bus_skims =  ["mfMdBusIvtt", "mfMdBusWait", "mfMdBusAux", "mfMdBusBoard", "mfMdBusFare"]
            rail_skims = ["mfMdRailIvtt", "mfMdRailIvttBus", "mfMdRailWait", "mfMdRailAux", "mfMdRailBoard", "mfMdRailFare"]
            wce_skims =  None
        if tod == "PM":
            bus_skims =  ["mfPmBusIvtt", "mfPmBusWait", "mfPmBusAux", "mfPmBusBoard", "mfPmBusFare"]
            rail_skims = ["mfPmRailIvtt", "mfPmRailIvttBus", "mfPmRailWait", "mfPmRailAux", "mfPmRailBoard", "mfPmRailFare"]
            wce_skims =  ["mfPmWceIvtt", "mfPmWceIvttRail", "mfPmWceIvttBus", "mfPmWceWait", "mfPmWceAux", "mfPmWceBoard", "mfPmWceFare"]

        do_averaging = util.get_cycle(sc.emmebank) > 1
        specs = []

        if not do_averaging:
            # Set Bus Skims
            specs.append(util.matrix_spec(bus_skims[0], "mfBusIvtt"))
            specs.append(util.matrix_spec(bus_skims[1], "mfBusWait"))
            specs.append(util.matrix_spec(bus_skims[2], "mfBusAux"))
            specs.append(util.matrix_spec(bus_skims[3], "mfBusBoard"))
            specs.append(util.matrix_spec(bus_skims[4], "mfBusFare"))

            # Set Rail Skims
            specs.append(util.matrix_spec(rail_skims[0], "mfRailIvtt"))
            specs.append(util.matrix_spec(rail_skims[1], "mfRailIvttBus"))
            specs.append(util.matrix_spec(rail_skims[2], "mfRailWait"))
            specs.append(util.matrix_spec(rail_skims[3], "mfRailAux"))
            specs.append(util.matrix_spec(rail_skims[4], "mfRailBoard"))
            specs.append(util.matrix_spec(rail_skims[5], "mfRailFare"))

            # Set WCE Skims
            if wce_skims is not None:
                specs.append(util.matrix_spec(wce_skims[0], "mfWceIvtt"))
                specs.append(util.matrix_spec(wce_skims[1], "mfWceIvttRail"))
                specs.append(util.matrix_spec(wce_skims[2], "mfWceIvttBus"))
                specs.append(util.matrix_spec(wce_skims[3], "mfWceWait"))
                specs.append(util.matrix_spec(wce_skims[4], "mfWceAux"))
                specs.append(util.matrix_spec(wce_skims[5], "mfWceBoard"))
                specs.append(util.matrix_spec(wce_skims[6], "mfWceFare"))
        else:
            # Average Bus Skims
            specs.append(util.matrix_spec(bus_skims[0], "0.5*(mfBusIvtt + %s)"  % bus_skims[0]))
            specs.append(util.matrix_spec(bus_skims[1], "0.5*(mfBusWait + %s)"  % bus_skims[1]))
            specs.append(util.matrix_spec(bus_skims[2], "0.5*(mfBusAux + %s)"   % bus_skims[2]))
            specs.append(util.matrix_spec(bus_skims[3], "0.5*(mfBusBoard + %s)" % bus_skims[3]))
            specs.append(util.matrix_spec(bus_skims[4], "0.5*(mfBusFare + %s)"  % bus_skims[4]))

            # Average Rail Skims
            specs.append(util.matrix_spec(rail_skims[0], "0.5*(mfRailIvtt + %s)"    % rail_skims[0]))
            specs.append(util.matrix_spec(rail_skims[1], "0.5*(mfRailIvttBus + %s)" % rail_skims[1]))
            specs.append(util.matrix_spec(rail_skims[2], "0.5*(mfRailWait + %s)"    % rail_skims[2]))
            specs.append(util.matrix_spec(rail_skims[3], "0.5*(mfRailAux + %s)"     % rail_skims[3]))
            specs.append(util.matrix_spec(rail_skims[4], "0.5*(mfRailBoard + %s)"   % rail_skims[4]))
            specs.append(util.matrix_spec(rail_skims[5], "0.5*(mfRailFare + %s)"    % rail_skims[5]))

            # Average WCE Skims
            if wce_skims is not None:
                specs.append(util.matrix_spec(wce_skims[0], "0.5*(mfWceIvtt + %s)"     % wce_skims[0]))
                specs.append(util.matrix_spec(wce_skims[1], "0.5*(mfWceIvttRail + %s)" % wce_skims[1]))
                specs.append(util.matrix_spec(wce_skims[2], "0.5*(mfWceIvttBus + %s)"  % wce_skims[2]))
                specs.append(util.matrix_spec(wce_skims[3], "0.5*(mfWceWait + %s)"     % wce_skims[3]))
                specs.append(util.matrix_spec(wce_skims[4], "0.5*(mfWceAux + %s)"      % wce_skims[4]))
                specs.append(util.matrix_spec(wce_skims[5], "0.5*(mfWceBoard + %s)"    % wce_skims[5]))
                specs.append(util.matrix_spec(wce_skims[6], "0.5*(mfWceFare + %s)"     % wce_skims[6]))

        util.compute_matrix(specs)

    @_m.logbook_trace("Initialize Skim Matrices")
    def init_matrices(self, eb):
        util = _m.Modeller().tool("translink.util")

        for matrix in self.get_temp_matrices():
            util.initmat(eb, matrix[0], matrix[1], matrix[2], matrix[3])

    def get_temp_matrices(self):
        matrices = []

        # Bus journey-level assignment
        matrices.append(["mf9960", "BusWait", "Interim Skim BusTotalWait", 0])
        matrices.append(["mf9961", "BusIvtt", "Interim Skim BusIVTT", 0])
        matrices.append(["mf9962", "BusAux",  "Interim Skim BusAux", 0])
        matrices.append(["mf9963", "BusBoard", "Interim Skim BusAvgBoard", 0])
        matrices.append(["mf9964", "BusIncCst", "Interim Skim BusIncrementalCost", 0])
        matrices.append(["mf9965", "BusIncFirstCost", "Interim Skim BusFirstBoardCost", 0])
        matrices.append(["mf9966", "BusFare", "Interim Skim BusTotalFare", 0])

        # Rail journey-level assignment
        matrices.append(["mf9970", "RailBoard", "Interim-JL Skim RailAvgBoard", 0])
        matrices.append(["mf9971", "RailAux", "Interim-JL Skim RailAux", 0])
        matrices.append(["mf9972", "RailWait", "Interim-JL Skim RailTotalWait", 0])
        matrices.append(["mf9973", "RailIvttBus", "Interim-JL Skim RailBusIVTT", 0])
        matrices.append(["mf9974", "RailIvtt", "Interim-JL Skim RailRailIVTT", 0])
        matrices.append(["mf9975", "RailIvCst", "Interim-JL Skim Rail Invehicle Cost", 0])
        matrices.append(["mf9976", "RailBrdCst", "Interim-JL Skim Rail Boarding Cost", 0])
        matrices.append(["mf9977", "RailFare", "Interim-JL Skim Rail Fare", 0])

        # WCE journey-level assignment
        matrices.append(["mf9980", "WceBoard", "Interim-JL Skim WCEAvgBoard", 0])
        matrices.append(["mf9981", "WceAux", "Interim-JL Skim WCEAux", 0])
        matrices.append(["mf9982", "WceWait", "Interim-JL Skim WCETotalWait", 0])
        matrices.append(["mf9983", "WceIvttBus", "Interim-JL Skim WCEBusIVTT", 0])
        matrices.append(["mf9984", "WceIvttRail", "Interim-JL Skim WCERailIVTT", 0])
        matrices.append(["mf9985", "WceIvtt", "Interim-JL Skim WCEWCEIVTT", 0])
        matrices.append(["mf9986", "WceIvCst", "Interim-JL Skim WCE Invehicle Cost", 0])
        matrices.append(["mf9987", "WceBrdZone", "Interim-JL Skim WCE Boarding Zone", 0])
        matrices.append(["mf9988", "WceAliZone", "Interim-JL Skim WCE Alighting Zone", 0])
        matrices.append(["mf9989", "WceFare", "Interim-JL Skim WCE Fare", 0])

        return matrices
