##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path:
##--Purpose: Performs two class transit assignment for bus and rail on on AM and PM scenarios
##---------------------------------------------------------------------
import inro.modeller as _m
import os
import traceback as _traceback

class TwoClassTransitAssignment(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    am_scenario = _m.Attribute(_m.InstanceType)
    md_scenario = _m.Attribute(_m.InstanceType)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Two_Class_Transit_Assignment"
        pb.description = "Performs two class transit assignment for bus and rail on on AM and PM scenarios"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        pb.add_select_scenario("am_scenario", title="AM scenario:")
        pb.add_select_scenario("md_scenario", title="MD scenario:")
        return pb.render()

    def run(self):
        with _m.logbook_trace("10-11 - RUN - TWO CLASS TRANSIT ASSIGNMENT"):
            self.tool_run_msg = ""
            try:
                self(self.am_scenario, self.md_scenario)
                run_msg = "Tool completed"
                self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
            except Exception, e:
                self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("10-11 - Two Class Transit Assignment")
    def __call__(self, scenarioam, scenariomd):
        transit_assign = _m.Modeller().tool("inro.emme.transit_assignment.extended_transit_assignment")

        bus_spec = {
            "modes": ["b", "g", "a", "p"],
            "demand": None,                 # demand specified for AM and MD below
            "waiting_time": {
                "headway_fraction": 0.5,
                "effective_headways": "ut1",
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
                "at_nodes": {
                    "penalty": 0,
                    "perception_factor": 1
                },
                "on_lines": None
            },
            "in_vehicle_time": {
                "perception_factor": 1
            },
            "in_vehicle_cost": None,
            "aux_transit_time": {
                "perception_factor": 1.75
            },
            "aux_transit_cost": None,
            "flow_distribution_at_origins": {
                "choices_at_origins": "OPTIMAL_STRATEGY",
                "fixed_proportions_on_connectors": None
            },
            "flow_distribution_at_regular_nodes_with_aux_transit_choices": {
                "choices_at_regular_nodes": "OPTIMAL_STRATEGY"
            },
            "flow_distribution_between_lines": {
                "consider_total_impedance": False
            },
            "connector_to_connector_path_prohibition": None,
            "od_results": {
                "total_impedance": None
            },
            "performance_settings": {
                "number_of_processors": 1
            },
            "type": "EXTENDED_TRANSIT_ASSIGNMENT"
        }

        rail_spec = {
            "modes": ["b", "f", "g", "l", "r", "s", "h", "a", "p"],
            "demand": None,                 # demand specified for AM and MD below
            "waiting_time": {
                "headway_fraction": 0.5,
                "effective_headways": "ut1",
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
                "at_nodes": {
                    "penalty": 0,
                    "perception_factor": 1
                },
                "on_lines": None
            },
            "in_vehicle_time": {
                "perception_factor": "@ivttp"
            },
            "in_vehicle_cost": None,
            "aux_transit_time": {
                "perception_factor": 1.75
            },
            "aux_transit_cost": None,
            "flow_distribution_at_origins": {
                "by_time_to_destination": "BEST_CONNECTOR",
                "by_fixed_proportions": None
            },
            "flow_distribution_between_lines": {
                "consider_travel_time": False
            },
            "connector_to_connector_path_prohibition": None,
            "save_strategies": True,
            "type": "EXTENDED_TRANSIT_ASSIGNMENT"
        }

        demand_list_bus = ["mf853", "mf866"]
        demand_list_rail = ["mf854", "mf867"]
        scenario_list = [scenarioam, scenariomd]
        for bus, rail, scen in zip(demand_list_bus, demand_list_rail, scenario_list):
            bus_spec["demand"] = bus
            transit_assign(
                bus_spec, scenario=scen, add_volumes=False,
                save_strategies=True, class_name="Bus")
            rail_spec["demand"] = rail
            transit_assign(
                rail_spec, scenario=scenarioam, add_volumes=True,
                save_strategies=True, class_name="Rail")
