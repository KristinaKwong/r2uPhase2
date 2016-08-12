##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model Development
##--
##--Path: translink.emme.stage3.step6.railassignment
##--Purpose: Assign skytrain trips to get skims
##---------------------------------------------------------------------
import inro.modeller as _m
import os
import traceback as _traceback

class Rail_Assignment(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "West Coast Express Assignment"
        pb.description = "Performs a standard transit assignment with WCE demand"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        with _m.logbook_trace("UNDER DEV - WCE ASSIGNMENT"):
            self.tool_run_msg = ""
            try:
                # TODO: scenario selectors to page and run method
                eb = _m.Modeller().emmebank
                am_scenario = eb.scenario(21000)
                md_scenario = eb.scenario(22000)
                pm_scenario = eb.scenario(23000)
                self(am_scenario, md_scenario, pm_scenario)
                run_msg = "Tool completed"
                self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
            except Exception, e:
                self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))
        pass

    @_m.logbook_trace("UNDER DEV - WCE Assignment")
    def __call__(self, scenarioam, scenariomd, scenariopm):
        RailSkim = _m.Modeller().tool("translink.emme.under_dev.wceskim")
        railassign = _m.Modeller().tool("inro.emme.transit_assignment.extended_transit_assignment")
        eb = _m.Modeller().emmebank
        self.matrix_batchins(eb)
        # TODO: what does the "skim" do and why is it a separate script?


        ## Journey Level SPEC
        spec_as_dict_JL = {
                "modes": ["r","b", "f", "g", "l", "s", "h", "a", "p"],
                "demand": None,                 # demand specified for AM, MD, PM below
                "waiting_time": {
                    "headway_fraction": 1.0,
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
                    "by_time_to_destination": "BEST_CONNECTOR",
                    "by_fixed_proportions": None
                },
                    "journey_levels": [
                {
                    "description": "One",
                    "destinations_reachable": False,
                    "transition_rules": [
                        { "mode": "b", "next_journey_level": 0 },
                        { "mode": "f", "next_journey_level": 0 },
                        { "mode": "g", "next_journey_level": 0 },
                        { "mode": "h", "next_journey_level": 0 },
                        { "mode": "l", "next_journey_level": 0 },
                        { "mode": "s", "next_journey_level": 0 },
                        { "mode": "r", "next_journey_level": 1 }

                    ],
                    "boarding_time": {
                        "at_nodes": {
                            "penalty": 1,
                            "perception_factor": 4
                        },
                        "on_lines": None
                    },
                    "boarding_cost": None,
                    "waiting_time": {
                        "headway_fraction": 1.0,
                        "effective_headways": "ut1",
                        "spread_factor": 1,
                        "perception_factor": 2.25
                    }
                },
                {
                    "description": "Two",
                    "destinations_reachable": True,
                    "transition_rules": [
                        { "mode": "b", "next_journey_level": 1 },
                        { "mode": "f", "next_journey_level": 1 },
                        { "mode": "g", "next_journey_level": 1 },
                        { "mode": "h", "next_journey_level": 1 },
                        { "mode": "l", "next_journey_level": 1 },
                        { "mode": "s", "next_journey_level": 1 },
                        { "mode": "r", "next_journey_level": 1 }
                    ],
                    "boarding_time": {
                        "at_nodes": {
                            "penalty": 1,
                            "perception_factor": 4
                        },
                        "on_lines": None
                    },
                    "boarding_cost": None,
                    "waiting_time": {
                        "headway_fraction": 1.0,
                        "effective_headways": "ut1",
                        "spread_factor": 1,
                        "perception_factor": 2.25
                    }
                }
            ],


                    "flow_distribution_between_lines": {
                        "consider_travel_time": False
                    },
                    "connector_to_connector_path_prohibition": None,
                    "save_strategies": True,
                    "type": "EXTENDED_TRANSIT_ASSIGNMENT"
                }

        small_demand_list = ["ms160", "ms160", "ms160"]
        # demand_list = ["mf854", "mf867", "mf880"]

        ## added a third parameter to distinguish between Rail Assignments, RaType0 skims with "3.5" factor, RaType1 skims with JLA
        RaType0=0
        RaType1=1
        for i in range(3):
            # spec_as_dict["demand"] = small_demand_list[i]
            spec_as_dict_JL["demand"] = small_demand_list[i]
            if i == 0:
                #railassign(spec_as_dict, add_volumes="True", scenario=scenarioam)
                #RailSkim(i, scenarioam, RaType0)
                railassign(spec_as_dict_JL, add_volumes="True", scenario=scenarioam)
                RailSkim(i, scenarioam, RaType1)
            if i == 1:
                #railassign(spec_as_dict, add_volumes="True", scenario=scenariomd)
                #RailSkim(i, scenariomd,  RaType0)
                railassign(spec_as_dict_JL, add_volumes="True", scenario=scenariomd)
                RailSkim(i, scenariomd,  RaType1)
            if i == 2:
                #railassign(spec_as_dict, add_volumes="True", scenario=scenariopm)
                #RailSkim(i, scenariopm,  RaType0)
                railassign(spec_as_dict_JL, add_volumes="True", scenario=scenariopm)
                RailSkim(i, scenariopm,  RaType1)


    def matrix_batchins(self, eb):
        util = _m.Modeller().tool("translink.emme.util")



        ## WCE

        util.initmat(eb, "mf5050", "nWBIvA", "Interim-JL Skim WCEBusIVTTAM", 0)
        util.initmat(eb, "mf5051", "nWRIvA", "Interim-JL Skim WCERailIVTTAM", 0)
        util.initmat(eb, "mf5052", "nWWIvA", "Interim-JL Skim WCEWCEIVTTAM", 0)
        util.initmat(eb, "mf5053", "bunWlWtA", "Interim-JL Skim WCETotalWaitAM", 0)
        util.initmat(eb, "mf5054", "nWlBrA", "Interim-JL Skim WCEAvgBoardAM", 0)
        util.initmat(eb, "mf5055", "nWlAxA", "Interim-JL Skim WCEAuxAM", 0)


        util.initmat(eb, "mf5056", "nWBIvM", "Interim-JL Skim WCEBusIVTTMD", 0)
        util.initmat(eb, "mf5057", "nWRIvM", "Interim-JL Skim WCERailIVTTMD", 0)
        util.initmat(eb, "mf5058", "nWWIvM", "Interim-JL Skim WCEWCEIVTTMD", 0)
        util.initmat(eb, "mf5059", "nWlWtM", "Interim-JL Skim WCETotalWaitMD", 0)
        util.initmat(eb, "mf5060", "nWlBrM", "Interim-JL Skim WCEAvgBoardMD", 0)
        util.initmat(eb, "mf5061", "nWlAxM", "Interim-JL Skim WCEAuxMD", 0)


        util.initmat(eb, "mf5062", "nWBIvP", "Interim-JL Skim WCEBusIVTTPM", 0)
        util.initmat(eb, "mf5063", "nWRIvP", "Interim-JL Skim WCERailIVTTPM", 0)
        util.initmat(eb, "mf5064", "nWRIvP", "Interim-JL Skim WCEWCEIVTTPM", 0)
        util.initmat(eb, "mf5065", "nRlWtP", "Interim-JL Skim WCETotalWaitPM", 0)
        util.initmat(eb, "mf5066", "nRlBrP", "Interim-JL Skim WCEAvgBoardPM", 0)
        util.initmat(eb, "mf5067", "nRlAxP", "Interim-JL Skim WCEAuxPM", 0)
