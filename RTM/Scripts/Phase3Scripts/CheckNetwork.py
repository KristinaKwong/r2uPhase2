##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.emme.checking.checknet
##--Purpose: check and calculate consistent network attributes
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback

class CheckNetwork(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)
    scens = _m.Attribute(list)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Translink Network Utility"
        pb.description = "Calculate Consistent Emme Network Attributes"
        pb.branding_text = "TransLink"

        pb.add_select_scenario(tool_attribute_name="scens",
                        title="Scenarios to Calculate:",
                        note="Each scenario will have u-turns banned, consistent coding for matching Time of Day attributes")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        try:
            self.__call__(self.scens)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    def __call__(self, scens):
        for s in scens:
            self.check_consistency(s.number)

    def check_consistency(self, scen_id):
        util = _m.Modeller().tool("translink.util")

        mod = _m.Modeller()
        eb = mod.emmebank
        project = mod.desktop.project

        scen = eb.scenario(scen_id)

        # Clear the user settable state to zero for anything actually batched out
        util.emme_node_calc(scen, "ui1", "0")
        util.emme_node_calc(scen, "ui2", "0")
        util.emme_node_calc(scen, "ui3", "0")

        util.emme_link_calc(scen, "ul1", "0")
        util.emme_link_calc(scen, "ul2", "0")
        util.emme_link_calc(scen, "ul3", "0")

        util.emme_turn_calc(scen, "up1", "0")
        util.emme_turn_calc(scen, "up2", "0")
        util.emme_turn_calc(scen, "up3", "0")

        util.emme_tline_calc(scen, "ut1", "0")
        util.emme_tline_calc(scen, "ut2", "0")
        util.emme_tline_calc(scen, "ut3", "0")

        util.emme_segment_calc(scen, "us1", "0")
        util.emme_segment_calc(scen, "us2", "0")
        util.emme_segment_calc(scen, "us3", "0")

        # Ban all u-turn movements
        util.emme_turn_calc(scen, "tpf", "(i.ne.k)*tpf")
        util.emme_turn_calc(scen, "@tpfam", "(i.ne.k)*@tpfam")
        util.emme_turn_calc(scen, "@tpfmd", "(i.ne.k)*@tpfmd")
        util.emme_turn_calc(scen, "@tpfpm", "(i.ne.k)*@tpfpm")

        # Calculate Consistent Network Attributes if all TOD values match
        util.emme_link_calc(scen, "ul1", "(@lanesam.eq.@lanesmd).and.(@lanesam.eq.@lanespm)")
        util.emme_link_calc(scen, "lanes", "@lanesam", "ul1=1")

        util.emme_link_calc(scen, "ul1", "(@vdfam.eq.@vdfmd).and.(@vdfam.eq.@vdfpm)")
        util.emme_link_calc(scen, "vdf", "@vdfam", "ul1=1")

        util.emme_turn_calc(scen, "up1", "(@tpfam.eq.@tpfmd).and.(@tpfam.eq.@tpfpm)")
        util.emme_turn_calc(scen, "tpf", "(@tpfam*(up1.eq.1))+(tpf*(up1.ne.1))")
