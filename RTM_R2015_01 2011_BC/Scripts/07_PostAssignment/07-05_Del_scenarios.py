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
## 05-01 Mode Choice - HDR
import inro.modeller as _m
import traceback as _traceback

class DeleteScenario(_m.Tool()):

    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self, title="Delete Skim Scenarios",
                    description=""" Deletes scenarios used for skim generation""",
                    branding_text=" Translink ")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)
        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            self.__call__()
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Delete Scenarios")
    def __call__(self, TempScenAM, TempScenMD):
        NAMESPACE="inro.emme.data.scenario.delete_scenario"
        delete_scenario=_m.Modeller().tool(NAMESPACE)

        delete_scenario(TempScenAM)
        delete_scenario(TempScenMD)
