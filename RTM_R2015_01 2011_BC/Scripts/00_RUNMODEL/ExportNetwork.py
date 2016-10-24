##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.exportnet
##--Purpose: export base networks as text files in BaseNetworks folder
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback
import os

class ExportNetwork(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Translink Utility Toolbox"
        pb.description = "Export an Emme Network"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        try:
            self.__call__()
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    def __call__(self):
        self.export(1000)
        self.export(2000)
        self.export(3000)
        self.export(4000)

    def export(self, scen_id):
        mod = _m.Modeller()
        eb = mod.emmebank
        project = mod.desktop.project
        proj_path = os.path.dirname(project.path)

        scen = eb.scenario(scen_id)

        data_path = os.path.join(proj_path, "BaseNetworks", "base_network_%d.txt" % scen_id)
        net_trans = mod.tool("inro.emme.data.network.base.export_base_network")
        net_trans(export_file = data_path,
                  append_to_file = False,
                  export_format = "PROMPT_DATA_FORMAT",
                  scenario = scen)
        self.remove_file_header(data_path)

        data_path = os.path.join(proj_path, "BaseNetworks", "link_shape_%d.txt" % scen_id)
        shp_trans = mod.tool("inro.emme.data.network.base.export_link_shape")
        shp_trans(export_file = data_path,
                  append_to_file = False,
                  scenario = scen)
        self.remove_file_header(data_path)

        data_path = os.path.join(proj_path, "BaseNetworks", "turns_%d.txt" % scen_id)
        trn_trans = mod.tool("inro.emme.data.network.turn.export_turns")
        trn_trans(export_file = data_path,
                  append_to_file = False,
                  export_format = "PROMPT_DATA_FORMAT",
                  scenario = scen)
        self.remove_file_header(data_path)

        data_path = os.path.join(proj_path, "BaseNetworks")
        att_trans = mod.tool("inro.emme.data.extra_attribute.export_extra_attributes")
        attribute_list = ["@lanesam", "@vdfam", "@tollam",
                          "@lanesmd", "@vdfmd", "@tollmd",
                          "@lanespm", "@vdfpm", "@tollpm",
                          "@tpfam", "@tpfmd", "@tpfpm",
                          "@hdwyam", "@hdwymd", "@hdwypm"]
        att_trans(extra_attributes = attribute_list,
                  export_path = data_path,
                  append_to_file = False,
                  field_separator = ' ',
                  export_format = "PROMPT_DATA_FORMAT",
                  scenario = scen)

        data_path = os.path.join(proj_path, "BaseNetworks", "transit_lines_%d.txt" % scen_id)
        lin_trans = mod.tool("inro.emme.data.network.transit.export_transit_lines")
        lin_trans(export_file = data_path,
                  append_to_file = False,
                  export_format = "PROMPT_DATA_FORMAT",
                  scenario = scen)
        self.remove_file_header(data_path)

    # Remove the Date and Project comments from the output files
    # These headers can change even if no network elements have changed, increasing the
    # size of the changes requiring review.
    def remove_file_header(self, file):
        lines = [ line for line in open(file) if not line.startswith(('c Date:', 'c Project:'))]
        open(file,'w').writelines(lines)
