##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step6.assignment
##--Purpose: Run all assignment procedures
##---------------------------------------------------------------------
import inro.modeller as _m
import os
import traceback as _traceback

class Assignment(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Assignment"
        pb.description = "Performs Auto, Transit and Rail Assignments"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        
        stopping_criteria = {
            "max_iterations": 250,
            "relative_gap": 0.0,
            "best_relative_gap": 0.01,
            "normalized_gap": 0.01
        }
        try:
            eb =_m.Modeller().emmebank
            self.__call__(eb, stopping_criteria)
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("06-00 - Assignment")
    def __call__(self, eb, max_iterations):
        util = _m.Modeller().tool("translink.emme.util")
        amscen1 = int(eb.matrix("ms140").data)
        mdscen1 = int(eb.matrix("ms141").data)
        amscen2 = amscen1 + 30
        mdscen2 = mdscen1 + 30

        if util.get_cycle(eb) % 2 == 1:
            scenarioam = eb.scenario(amscen1)
            scenariomd = eb.scenario(mdscen1)
        else:
            scenarioam = eb.scenario(amscen2)
            scenariomd = eb.scenario(mdscen2)

        AutoAssignment = _m.Modeller().tool("translink.emme.stage3.step6.autoassignment")
        BusAssignment = _m.Modeller().tool("translink.emme.stage3.step6.busassignment")
        RailAssignment = _m.Modeller().tool("translink.emme.stage3.step6.railassignment")

        AutoAssignment(eb, scenarioam, scenariomd, max_iterations)
        BusAssignment(scenarioam, scenariomd)
        RailAssignment(scenarioam, scenariomd)
