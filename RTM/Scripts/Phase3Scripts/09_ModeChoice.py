##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage2.modechoice
##--Purpose:
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback

class ModeChoice(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Mode Choice Model"
        pb.description = "Runs Mode Choice Models"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            self.__call__(_m.Modeller().emmebank)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Mode Choice")
    def __call__(self, eb):
        td_mode_choice_hbw = _m.Modeller().tool("translink.RTM3.stage2.hbwork")
        td_mode_choice_hbu = _m.Modeller().tool("translink.RTM3.stage2.hbuniv")
        td_mode_choice_hbsc = _m.Modeller().tool("translink.RTM3.stage2.hbschool")
        td_mode_choice_hbsh = _m.Modeller().tool("translink.RTM3.stage2.hbshop")
        td_mode_choice_hbpb = _m.Modeller().tool("translink.RTM3.stage2.hbperbus")
        td_mode_choice_hbso = _m.Modeller().tool("translink.RTM3.stage2.hbsocial")
        td_mode_choice_hbes = _m.Modeller().tool("translink.RTM3.stage2.hbescorting")
        td_mode_choice_nhbw = _m.Modeller().tool("translink.RTM3.stage2.nhbwork")
        td_mode_choice_nhbo = _m.Modeller().tool("translink.RTM3.stage2.nhbother")

        td_mode_choice_hbw(eb)
        td_mode_choice_hbu(eb)
        td_mode_choice_hbsc(eb)
        td_mode_choice_hbsh(eb)
        td_mode_choice_hbpb(eb)
        td_mode_choice_hbso(eb)
        td_mode_choice_hbes(eb)
        td_mode_choice_nhbw(eb)
        td_mode_choice_nhbo(eb)
