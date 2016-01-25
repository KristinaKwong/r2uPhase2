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
import traceback as _traceback


class BusAssignment(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self, title="Bus_Assignment",
                                       description=""" Performs a standard transit assignment with
                                        only the "bus" mode selected
                                        """,
                                       branding_text="TransLink")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        scenarioam = _m.Modeller().emmebank.scenario(21060)
        scenariomd = _m.Modeller().emmebank.scenario(22000)
        self.tool_run_msg = ""
        try:
            self.__call__(scenarioam, scenariomd)
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Bus Assignment")
    def __call__(self, scenarioam, scenariomd):
        busassign = _m.Modeller().tool("inro.emme.transit_assignment.standard_transit_assignment")
        ## Rail Excluded from the network
        ## auxiliary weight: 1.75, waiting time factor: 0.5, wait time weight: 2.25, boarding weight: 4
        spec_as_dict = {
            "modes": ["b", "g", "a", "p"],
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
                "total_waiting_times": "mf933",
                "first_waiting_times": None,
                "boarding_times": None,
                "by_mode_subset": {
                    "modes": ["b", "g", "a", "p"],
                    "in_vehicle_times": "mf934",
                    "aux_transit_times": "mf936",
                    "avg_boardings": "mf935"
                }
            },
            "strategy_analysis": None,
            "type": "STANDARD_TRANSIT_ASSIGNMENT"
        }

        demand_list = ['mf853', 'mf866']
        travel_times_list = [['mf933', 'mf934', 'mf936', 'mf935'], ['mf945', 'mf946', 'mf948', 'mf947']]
        # TODO: fix "for case" paradigm
        for i in range(2):
            spec_as_dict['demand'] = demand_list[i]
            spec_as_dict['od_results']['total_waiting_times'] = travel_times_list[i][0]
            spec_as_dict['od_results']['by_mode_subset']['in_vehicle_times'] = travel_times_list[i][1]
            spec_as_dict['od_results']['by_mode_subset']['aux_transit_times'] = travel_times_list[i][2]
            spec_as_dict['od_results']['by_mode_subset']['avg_boardings'] = travel_times_list[i][3]
            if i == 0:
                busassign(spec_as_dict, scenario=scenarioam)
            if i == 1:
                busassign(spec_as_dict, scenario=scenariomd)
