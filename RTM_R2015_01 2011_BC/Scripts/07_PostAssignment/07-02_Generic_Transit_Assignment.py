##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step7.gentranskim
##--Purpose: Generates a generic transit skim
##---------------------------------------------------------------------
import inro.modeller as _m
import os
import simplejson
import traceback as _traceback

eb = _m.Modeller().emmebank


class Transit_Assignment(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Generic Transit Assignment"
        pb.description = "Generates a generic transit skim"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            self.__call__()
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("07-02 - Generic Transit Skim")
    def __call__(self, scenarioam, scenariomd):
        genskim = _m.Modeller().tool("inro.emme.transit_assignment.standard_transit_assignment")
        spec_as_dict = {
            "modes": ["b", "f", "g", "l", "r", "s", "a", "p", "h"],
            "demand": "mf853",
            "waiting_time": {
                "headway_fraction": 0.5,
                "effective_headways": "ut1",
                "spread_factor": 1,
                "perception_factor": 2.25
            },
            "boarding_time": {
                "penalty": 1,
                "perception_factor": 4
            },
            "aux_transit_time": {
                "perception_factor": 1.75
            },
            "od_results": {
                "transit_times": None,
                "total_waiting_times": "mf954",
                "first_waiting_times": None,
                "boarding_times": None,
                "by_mode_subset": {
                    "modes": ["b", "f", "g", "l", "r", "s", "a", "p", "h"],
                    "in_vehicle_times": "mf955",
                    "aux_transit_times": "mf956",
                    "avg_boardings": "mf957"
                }
            },
            "strategy_analysis": None,
            "type": "STANDARD_TRANSIT_ASSIGNMENT"
        }
        demand_list = ["mf853", "mf866"]
        travel_times_list = [["mf954", "mf955", "mf956", "mf957"], ["mf958", "mf959", "mf960", "mf961"]]
        for j in range(2):
            spec_as_dict["demand"] = demand_list[j]
            spec_as_dict["od_results"]["total_waiting_times"] = travel_times_list[j][0]
            spec_as_dict["od_results"]["by_mode_subset"]["in_vehicle_times"] = travel_times_list[j][1]
            spec_as_dict["od_results"]["by_mode_subset"]["aux_transit_times"] = travel_times_list[j][2]
            spec_as_dict["od_results"]["by_mode_subset"]["avg_boardings"] = travel_times_list[j][3]
            if j == 0:
                genskim(spec_as_dict, scenario=scenarioam)
            if j == 1:
                genskim(spec_as_dict, scenario=scenariomd)
