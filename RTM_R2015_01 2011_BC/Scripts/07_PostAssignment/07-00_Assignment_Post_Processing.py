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
## 07-00 Post Assignment processes

import inro.modeller as _m
import os
import traceback as _traceback


class PostAssignment(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        start_path = os.path.dirname(_m.Modeller().emmebank.path)

        pb = _m.ToolPageBuilder(self, title="Post Assignment",
                                       description=""" Performs Auto, Transit and Rail Assignments
                                        """,
                                       branding_text="TransLink")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            PathHeader = os.path.dirname(_m.Modeller().emmebank.path) + "\\"
            self.__call__(PathHeader, 0)
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("07-00 - RUN - Post Assignment")
    def __call__(self, root_directory, iteration_number, stopping_criteria):
        emmebank = _m.Modeller().emmebank
        am_scenario_id = int(emmebank.matrix("ms140").data)
        md_scenario_id = int(emmebank.matrix("ms141").data)

        am_temp_scenario, md_temp_scenario = self.copy_scenario(
            am_scenario_id, md_scenario_id, iteration_number)

        gen_transit = _m.Modeller().tool(
            "translink.emme.stage3.step7.gentranskim")
        toll_skim = _m.Modeller().tool(
            "translink.emme.stage3.step7.tollskim")
        access_skim = _m.Modeller().tool(
            "translink.emme.stage3.step7.skimaccess")
        delete_scenario = _m.Modeller().tool(
            "translink.emme.stage3.step7.deletescenario")

        gen_transit(am_temp_scenario, md_temp_scenario)
        toll_skim(am_temp_scenario, md_temp_scenario, stopping_criteria)
        access_skim(root_directory, iteration_number)
        delete_scenario(am_temp_scenario, md_temp_scenario)

    @_m.logbook_trace("Copy Scenario")
    def copy_scenario(self, am_scenario_id, md_scenario_id, iteration_number):
        emmebank = _m.Modeller().emmebank

        # TODO: would be easier to always run on the same scenario
        #       and at the beginning of each iteration
        #       make a backup copy of each scenario
        if (iteration_number % 2 == 0 ):
            am_scenario = emmebank.scenario(am_scenario_id)
            md_scenario = emmebank.scenario(md_scenario_id)
        else:
            am_scenario = emmebank.scenario(am_scenario_id + 30)
            md_scenario = emmebank.scenario(md_scenario_id + 30)

        copy_scenario = _m.Modeller().tool(
            "inro.emme.data.scenario.copy_scenario")
        newscenam = copy_scenario(from_scenario=am_scenario,
                                  scenario_id=am_scenario_id + 50000 + iteration_number,
                                  scenario_title="AM scenario copy for various skims",
                                  overwrite=True)
        newscenmd = copy_scenario(from_scenario=md_scenario,
                                  scenario_id=md_scenario_id + 50000 + iteration_number,
                                  scenario_title="MD scenario copy for various skims",
                                  overwrite=True)

        return (newscenam, newscenmd)
