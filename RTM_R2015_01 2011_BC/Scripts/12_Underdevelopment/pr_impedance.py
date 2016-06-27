##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model Development
##--
##--Path: translink.emme.?
##--Purpose: Generate Impedance for Park and Ride Access Mode 
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
