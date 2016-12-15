##------------------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model Development
##--
##--Path: translink.emme.under_dev.runautoskim
##--Purpose: Generate Auto Skims for work and non-work purpose with modified VOT
##------------------------------------------------------------------------------
import inro.modeller as _m
import os
import traceback as _traceback

class PostAssignment(_m.Tool()):

    am_scenario = _m.Attribute(_m.InstanceType)
    md_scenario = _m.Attribute(_m.InstanceType)
    pm_scenario = _m.Attribute(_m.InstanceType)
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Run Auto Assignment with modified skims"
        pb.description = "Performs Auto Assignment"
        pb.branding_text = "TransLink"
		## Scenario selector 
        pb.add_select_scenario("am_scenario", title="AM scenario:")
        pb.add_select_scenario("md_scenario", title="Midday scenario:")
        pb.add_select_scenario("pm_scenario", title="PM scenario:")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        stopping_criteria = {
            "max_iterations": 200,
            "relative_gap": 0.0,
            "best_relative_gap": 0.01,
            "normalized_gap": 0.01
        }
        try:
            eb = _m.Modeller().emmebank
            self.__call__(eb, self.am_scenario, self.md_scenario, self.pm_scenario, stopping_criteria)
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("012-00 - RUN - Run Auto Skims")
    def __call__(self, eb, scenarioam, scenariomd, scenariopm, stopping_criteria):
        util = _m.Modeller().tool("translink.emme.util")

        auto_skim = _m.Modeller().tool("translink.emme.under_dev.autoskim")
        toll_skim = _m.Modeller().tool("translink.emme.under_dev.autotollskim")
        calc_skim = _m.Modeller().tool("translink.emme.under_dev.autocalcskim")
        

        auto_skim(eb, scenarioam, scenariomd, scenariopm, stopping_criteria)        
        toll_skim(eb, scenarioam, scenariomd, scenariopm, stopping_criteria)
        calc_skim(eb)
