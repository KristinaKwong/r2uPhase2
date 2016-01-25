#--------------------------------------------------
##--TransLink Phase 2 Regional Transportation Model
##--
##--Path:
##--Purpose:
##--------------------------------------------------
##--Last modified 2014-02-14 Kevin Bragg (INRO)
##--Reason: Update to Emme 4.0 namespaces
##          Code cleanup PEP 8 compliance
##---------------------------------------------------
##--Called by:
##--Calls:
##--Accesses:
##--Outputs:
##---------------------------------------------------
##--Status/additional notes:
##---------------------------------------------------


import inro.modeller as _m
import os
import traceback as _traceback


class Rail_Assignment(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self, title="Rail_Assignment",
                                       description=""" Performs a standard transit assignment with
                                        on rail demand
                                        """,
                                       branding_text="TransLink")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        with _m.logbook_trace("06-03 - RUN - RAIL ASSIGNMENT"):
            self.tool_run_msg = ""
            try:
                # TODO: scenario selectors to page and run method
                eb = _m.Modeller().emmebank
                am_scenario = eb.scenario(21000)
                md_scenario = eb.scenario(22000)
                self(am_scenario, md_scenario)
                run_msg = "Tool completed"
                self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
            except Exception, e:
                self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))
        pass

    @_m.logbook_trace("06-03 - Rail Assignment")
    def __call__(self, scenarioam, scenariomd):
        RailSkim = _m.Modeller().tool("translink.emme.stage3.step7.railskim")
        railassign = _m.Modeller().tool("inro.emme.transit_assignment.extended_transit_assignment")
        # TODO: what does the "skim" do and why is it a separate script?

        spec_as_dict = {
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

        demand_list = ['mf854', 'mf867']
        for i in range(2):
            spec_as_dict['demand'] = demand_list[i]
            if i == 0:
                railassign(spec_as_dict, add_volumes="True", scenario=scenarioam)
                RailSkim(i, scenarioam)
            if i == 1:
                railassign(spec_as_dict, add_volumes="True", scenario=scenariomd)
                RailSkim(i, scenariomd)
