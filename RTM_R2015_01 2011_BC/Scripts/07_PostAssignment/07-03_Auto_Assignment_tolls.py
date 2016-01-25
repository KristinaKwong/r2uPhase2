#--------------------------------------------------
##--TransLink Phase 2 Regional Transportation Model
##--
##--Path:
##--Purpose:
##--------------------------------------------------
##--Last modified 2014-06-13 Kevin Bragg (INRO)
##--Reason: Changed auto assignment to SOLA assignment
##--Last modified 2014-04-17 Kevin Bragg (INRO)
##--Reason: Restructured auto assignment to
##          generate specification.
##          Centralized generation of spec for use
##          with 07-03_Auto_Assignment_tolls.py
##          Changed inputs to take stopping_criteria
##          instead of max_iterations.
##--Last modified 2014-02-14 Kevin Bragg (INRO)
##--Reason: Update to Emme 4.0 namespaces
##          Code cleanup PEP 8 compliance
##---------------------------------------------------
##--Called by:
##--Calls: 06-01_AutoAssignment.generate_specification
##--Accesses:
##--Outputs:
##---------------------------------------------------
##--Status/additional notes:
##---------------------------------------------------

import inro.modeller as _m
import os
import traceback as _traceback


class TollSkim(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        start_path = os.path.dirname(_m.Modeller().emmebank.path)

        pb = _m.ToolPageBuilder(self, title="Auto Assignment for toll skims",
                                       description=""" Generates skims for tolls
                                        """,
                                       branding_text=" Translink ")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            # TODO: add these inputs to the page
            self.__call__()
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("07-03 - Auto Toll Skim")
    def __call__(self, am_scenario, md_scenario, stopping_criteria):
        eb = am_scenario.emmebank
        assign_traffic = _m.Modeller().tool(
            "inro.emme.traffic_assignment.sola_traffic_assignment")
        translink_auto_assignment = _m.Modeller().tool(
            "translink.emme.stage3.step6.autoassignment")

        num_processors = int(eb.matrix("ms142").data)

        demands_list = [
            {
                "sov": ['mf843', 'mf844', 'mf845', 'mf846', 'mf847'],
                "hov": ['mf848', 'mf849', 'mf850', 'mf851', 'mf852'],
                "truck": ['mf980', 'mf981']
            },
            {
                "sov": ['mf856', 'mf857', 'mf858', 'mf859', 'mf860'],
                "hov": ['mf861', 'mf862', 'mf863', 'mf864', 'mf865'],
                "truck": ['mf982', 'mf983']
            }
        ]
        toll_list = ['mf932', 'mf944']
        path_analysis = {
            "link_component": "@tolls",
            "turn_component": None,
            "operator": "+",
            "selection_threshold": {"lower": 0.85, "upper": 10},
            "path_to_od_composition": {
                "considered_paths": "SELECTED",
                "multiply_path_proportions_by": {
                    "analyzed_demand": False,
                    "path_value": True
                }
            }
        }

        input_items = zip([am_scenario, md_scenario], demands_list, toll_list)
        for scenario, demands, tolls in input_items:
            spec = translink_auto_assignment.generate_specification(
                demands, stopping_criteria, num_processors, results=False)
            spec["path_analysis"] = path_analysis
            spec['classes'][4]['analysis'] = {'results': {'od_values': tolls}}
            assign_traffic(spec, scenario=scenario)
