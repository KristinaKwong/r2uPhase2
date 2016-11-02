##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: ?
##--Purpose: Generate Initial Data for RTM Run
##---------------------------------------------------------------------
import inro.modeller as _m

import traceback as _traceback

class DataGeneration(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Generate Data for Model Run"
        pb.description = "Generate Densities, Initial Skims, data dependant values"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            eb = _m.Modeller().emmebank
            self.__call__(eb)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Model Data Generation")
    def __call__(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

