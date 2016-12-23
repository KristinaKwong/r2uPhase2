##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step7.postassign
##--Purpose: Post Assignment processes
##---------------------------------------------------------------------
import inro.modeller as _m
import os
import traceback as _traceback

class PostAssignment(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Post Assignment"
        pb.description = "Performs Auto, Transit and Rail Assignments"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        stopping_criteria = {
            "max_iterations": 100,
            "relative_gap": 0.0,
            "best_relative_gap": 0.01,
            "normalized_gap": 0.01
        }
        try:
            self.__call__(_m.Modeller().emmebank, stopping_criteria)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("07-00 - RUN - Post Assignment")
    def __call__(self, eb, stopping_criteria):
        util = _m.Modeller().tool("translink.util")
        am_scenario_id = int(eb.matrix("ms140").data)
        md_scenario_id = int(eb.matrix("ms141").data)
        pm_scenario_id = int(eb.matrix("ms150").data)

        am_temp_scenario, md_temp_scenario, pm_temp_scenario = self.copy_scenario(eb, am_scenario_id, md_scenario_id, pm_scenario_id)
        gen_transit = _m.Modeller().tool("translink.emme.stage3.step7.gentranskim")
        toll_skim = _m.Modeller().tool("translink.emme.stage3.step7.tollskim")
        access_skim = _m.Modeller().tool("translink.emme.stage3.step7.skimaccess")
        gen_transit(am_temp_scenario, md_temp_scenario, pm_temp_scenario)
        toll_skim(am_temp_scenario, md_temp_scenario, pm_temp_scenario, stopping_criteria)
        access_skim(eb)
        util.del_scen(am_temp_scenario)
        util.del_scen(md_temp_scenario)
        util.del_scen(pm_temp_scenario)

    @_m.logbook_trace("Copy Scenario")
    def copy_scenario(self, eb, am_scenario_id, md_scenario_id, pm_scenario_id):
        util = _m.Modeller().tool("translink.util")
        cycle_number = util.get_cycle(eb)
        # TODO: would be easier to always run on the same scenario
        #       and at the beginning of each iteration
        #       make a backup copy of each scenario
        if (cycle_number % 2 == 1):
            am_scenario = eb.scenario(am_scenario_id)
            md_scenario = eb.scenario(md_scenario_id)
            pm_scenario = eb.scenario(pm_scenario_id)
        else:
            am_scenario = eb.scenario(am_scenario_id + 30)
            md_scenario = eb.scenario(md_scenario_id + 30)
            pm_scenario = eb.scenario(pm_scenario_id + 30)

        copy_scenario = _m.Modeller().tool("inro.emme.data.scenario.copy_scenario")
        newscenam = copy_scenario(from_scenario=am_scenario,
                                  scenario_id=am_scenario_id + 50000 + cycle_number,
                                  scenario_title="AM scenario copy for various skims",
                                  overwrite=True)
        newscenmd = copy_scenario(from_scenario=md_scenario,
                                  scenario_id=md_scenario_id + 50000 + cycle_number,
                                  scenario_title="MD scenario copy for various skims",
                                  overwrite=True)
        newscenpm = copy_scenario(from_scenario=pm_scenario,
                                  scenario_id=pm_scenario_id + 50000 + cycle_number,
                                  scenario_title="PM scenario copy for various skims",
                                  overwrite=True)

        return (newscenam, newscenmd, newscenpm)
