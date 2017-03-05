##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.emme.importnet
##--Purpose: import base networks as text files from BaseNetworks folder
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback
import os

class ImportNetwork(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)
    scen_id = _m.Attribute(int)
    scen_title = _m.Attribute(_m.InstanceType)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Translink Utility Toolbox"
        pb.description = "Export an Emme Network"
        pb.branding_text = "TransLink"

        pb.add_text_box(tool_attribute_name="scen_id",
                        title="Scenario number to Import:",
                        note="Scenario will be input from text files.")

        pb.add_text_box(tool_attribute_name="scen_title",
                        size=30,
                        title="Enter the Title for the new scenario")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        try:
            eb = _m.Modeller().emmebank
            self.__call__(eb, self.scen_id, self.scen_title)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    def __call__(self, eb, scen_id, scen_title):
        initscen = _m.Modeller().tool("translink.RTM3.init_emmebank")
        initscen.initscenario(eb, scen_id, scen_title)
