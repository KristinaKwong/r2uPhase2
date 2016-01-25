#--------------------------------------------------
##--TransLink Phase 2 Regional Transportation Model
##--
##--Path:
##--Purpose:
##--------------------------------------------------
##--Last modified 2014-04-07 Kevin Bragg (INRO)
##--Reason: Add parameters for max iterations of
##          distribution and assignment steps
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
        try:
            start_path = os.path.dirname(_m.Modeller().emmebank.path) + "\\"
            self.__call__(start_path, 0, 250)
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("06-00 - Assignment")
    def __call__(self, PathHeader, IterationNumber, max_iterations):
        emmebank = _m.Modeller().emmebank
        amscen1 = int(emmebank.matrix("ms140").data)
        mdscen1 = int(emmebank.matrix("ms141").data)
        amscen2 = amscen1 + 30
        mdscen2 = mdscen1 + 30

        if IterationNumber % 2 == 0:
            scenarioam = emmebank.scenario(amscen1)
            scenariomd = emmebank.scenario(mdscen1)
        else:
            scenarioam = emmebank.scenario(amscen2)
            scenariomd = emmebank.scenario(mdscen2)

        AutoAssignment = _m.Modeller().tool("translink.emme.stage3.step6.autoassignment")
        BusAssignment = _m.Modeller().tool("translink.emme.stage3.step6.busassignment")
        RailAssignment = _m.Modeller().tool("translink.emme.stage3.step6.railassignment")

        AutoAssignment(PathHeader, scenarioam, scenariomd, max_iterations)
        BusAssignment(scenarioam, scenariomd)
        RailAssignment(scenarioam, scenariomd)
