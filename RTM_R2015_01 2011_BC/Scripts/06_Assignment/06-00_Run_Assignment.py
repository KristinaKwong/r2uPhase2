##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
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
            "max_iterations": 500,
            "relative_gap": 0.0,
            "best_relative_gap": 0.01,
            "normalized_gap": 0.01
        }
        try:
            eb =_m.Modeller().emmebank
            self.__call__(eb, True, stopping_criteria)
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("06-00 - Assignment")
    def __call__(self, eb, run_detailed_classes, max_iterations):
        util = _m.Modeller().tool("translink.emme.util")
        amscen1 = int(eb.matrix("ms140").data)
        mdscen1 = int(eb.matrix("ms141").data)
        pmscen1 = int(eb.matrix("ms150").data)
        amscen2 = amscen1 + 30
        mdscen2 = mdscen1 + 30
        pmscen2 = pmscen1 + 30

        if util.get_cycle(eb) % 2 == 1:
            scenarioam = eb.scenario(amscen1)
            scenariomd = eb.scenario(mdscen1)
            scenariopm = eb.scenario(pmscen1)
        else:
            scenarioam = eb.scenario(amscen2)
            scenariomd = eb.scenario(mdscen2)
            scenariopm = eb.scenario(pmscen2)

        # Aggregate demand with same VOT if not running the fully detailed class assignment
        if not run_detailed_classes:
            specs = []
            # AM Demand
            specs.append(util.matrix_spec("mf847", "mf843+mf847"))
            specs.append(util.matrix_spec("mf845", "mf844+mf845"))
            specs.append(util.matrix_spec("mf852", "mf848+mf852"))
            specs.append(util.matrix_spec("mf850", "mf849+mf850"))
            specs.append(util.matrix_spec("mf843", "0"))
            specs.append(util.matrix_spec("mf844", "0"))
            specs.append(util.matrix_spec("mf848", "0"))
            specs.append(util.matrix_spec("mf849", "0"))

            # MD Demand
            specs.append(util.matrix_spec("mf860", "mf856+mf860"))
            specs.append(util.matrix_spec("mf858", "mf857+mf858"))
            specs.append(util.matrix_spec("mf865", "mf861+mf865"))
            specs.append(util.matrix_spec("mf863", "mf862+mf863"))
            specs.append(util.matrix_spec("mf856", "0"))
            specs.append(util.matrix_spec("mf857", "0"))
            specs.append(util.matrix_spec("mf861", "0"))
            specs.append(util.matrix_spec("mf862", "0"))

            # PM Demand
            specs.append(util.matrix_spec("mf873", "mf869+mf873"))
            specs.append(util.matrix_spec("mf871", "mf870+mf871"))
            specs.append(util.matrix_spec("mf878", "mf874+mf878"))
            specs.append(util.matrix_spec("mf876", "mf875+mf876"))
            specs.append(util.matrix_spec("mf869", "0"))
            specs.append(util.matrix_spec("mf870", "0"))
            specs.append(util.matrix_spec("mf874", "0"))
            specs.append(util.matrix_spec("mf875", "0"))
            # specs.append(util.matrix_spec("mf990", "0.79*mf980'")) superceded by intergration into initemmebank
            # specs.append(util.matrix_spec("mf991", "0.55*mf981'"))

            util.compute_matrix(specs)

        AutoAssignment = _m.Modeller().tool("translink.emme.stage3.step6.autoassignment")
        BusAssignment = _m.Modeller().tool("translink.emme.stage3.step6.busassignment")
        RailAssignment = _m.Modeller().tool("translink.emme.stage3.step6.railassignment")

        AutoAssignment(eb, scenarioam, scenariomd, scenariopm, max_iterations)
        BusAssignment(scenarioam, scenariomd, scenariopm)
        RailAssignment(scenarioam, scenariomd, scenariopm)
