##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.stage1.step0.create_scen
##--Purpose: create scenarios
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback

class InputSettings(_m.Tool()):
    am_scenario = _m.Attribute(_m.InstanceType)
    md_scenario = _m.Attribute(_m.InstanceType)

    tool_run_msg = ""

    def page(self):
        pb = _m.ToolPageBuilder(self, title="Create Scenarios")
        pb.title = "Create Scenarios"
        pb.description = "Create AM and Mid-Day Scenarios."
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)
        pb.add_text_box(tool_attribute_name='am_scenario',
                        size=50,
                        title='Enter the Original AM Scenario Number')
        pb.add_text_box(tool_attribute_name='md_scenario',
                        size=50,
                        title='Enter the Original Mid-Day Scenario Number')
        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            self(self.am_scenario, self.md_scenario)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, error:
            self.tool_run_msg = _m.PageBuilder.format_exception(
                error, _traceback.format_exc(error))
            raise

    @_m.logbook_trace("00_00 Create Scenarios")
    def __call__(self, eb, am_scenario, md_scenario):
        copy_scenario = _m.Modeller().tool("inro.emme.data.scenario.copy_scenario")

        am_scenario = eb.scenario(am_scenario)
        md_scenario = eb.scenario(md_scenario)

        # Copy to new am scenarios
        copy_scenario(from_scenario=am_scenario,
                      scenario_id=am_scenario.number + 30,
                      scenario_title=am_scenario.title + ": Final Iteration ",
                      overwrite=True)

        # Copy to new md Scenarios
        copy_scenario(from_scenario=md_scenario,
                      scenario_id=md_scenario.number + 30,
                      scenario_title=md_scenario.title + ": Final Iteration ",
                      overwrite=True)
