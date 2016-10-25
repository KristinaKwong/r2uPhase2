##------------------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model Development
##--
##--Path: translink.emme.under_dev.auttollskim
##--Purpose: Run Assignment to generate toll skims for work and nonwork
##------------------------------------------------------------------------------
import inro.modeller as _m
import os
import traceback as _traceback

class TollSkim(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Auto Assignment for toll skims"
        pb.description = "Generates skims for tolls"
        pb.branding_text = "TransLink"

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
    def __call__(self, eb, am_scenario, md_scenario, pm_scenario, stopping_criteria):
        eb = am_scenario.emmebank
        assign_traffic = _m.Modeller().tool(
            "inro.emme.traffic_assignment.sola_traffic_assignment")
        translink_auto_assignment = _m.Modeller().tool(
            "translink.emme.stage3.step6.autoassignment")

        util = _m.Modeller().tool("translink.emme.util")
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
        # non-work toll skims. AD: These were left the same but could be chaged
        toll_list_nw = ["mf932", "mf944", "mf2002"]
        # work toll skims
        toll_list_wk = ["mf2032", "mf2035", "mf2038"]        
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

        input_items = zip([am_scenario, md_scenario, pm_scenario], demands_list, toll_list_nw, toll_list_wk)
        for scenario, demands, tolls_nw, tolls_wk in input_items:
            spec = translink_auto_assignment.generate_specification(
                demands, stopping_criteria, num_processors, results=False)
            spec["path_analysis"] = path_analysis
            spec["classes"][4]["analysis"] = {"results": {"od_values": tolls_nw}}
            spec["classes"][1]["analysis"] = {"results": {"od_values": tolls_wk}}            
            assign_traffic(spec, scenario=scenario)