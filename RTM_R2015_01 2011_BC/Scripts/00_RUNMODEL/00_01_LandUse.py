##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage1.step0.landuse
##--Purpose: input land use from external files
##---------------------------------------------------------------------
import inro.modeller as _m
import os
import traceback as _traceback

class InputLandUse(_m.Tool()):
    LandUse1 = _m.Attribute(unicode)
    LandUse2 = _m.Attribute(unicode)

    tool_run_msg = ""

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Land Use Input Module"
        pb.description = "Enters land use based on specified file input."
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        loc = os.path.dirname(_m.Modeller().emmebank.path)

        pb.add_select_file(tool_attribute_name="LandUse1",
                           window_type="file",
                           file_filter="*.csv",
                           start_path=loc + "/Inputs",
                           title="Select Input LandUse file 1: ",
                           note="File must be csv file.")

        pb.add_select_file(tool_attribute_name="LandUse2",
                           window_type="file",
                           file_filter="*.csv",
                           start_path=loc + "/Inputs",
                           title="Select Input LandUse file 2: ",
                           note="File must be csv file.")
        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            self(_m.Modeller().emmebank, self.LandUse1, self.LandUse2)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Import land use data", save_arguments=True)
    def __call__(self, eb, file1, file2):
        util = _m.Modeller().tool("translink.util")
        util.read_csv_momd(eb, file1)
        util.read_csv_momd(eb, file2)
