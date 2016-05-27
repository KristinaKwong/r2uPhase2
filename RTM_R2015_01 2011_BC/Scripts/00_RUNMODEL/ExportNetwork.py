import inro.modeller as _m
import inro.emme as _emme
import os

class InitEmmebank(_m.Tool()):
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
        self.__call__()

    def __call__(self):
        self.export(1000)
        self.export(1100)
        self.export(1200)
        self.export(2000)
        self.export(2100)
        self.export(2200)
        self.export(3000)
        self.export(3100)
        self.export(3200)

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

        data_path = os.path.join(proj_path, "BaseNetworks", "link_shape_%d.txt" % scen_id)
        shp_trans = mod.tool("inro.emme.data.network.base.export_link_shape")
        shp_trans(export_file = data_path,
                  append_to_file = False,
                  scenario = scen)

        data_path = os.path.join(proj_path, "BaseNetworks", "turns_%d.txt" % scen_id)
        trn_trans = mod.tool("inro.emme.data.network.turn.export_turns")
        trn_trans(export_file = data_path,
                  append_to_file = False,
                  export_format = "PROMPT_DATA_FORMAT",
                  scenario = scen)

        data_path = os.path.join(proj_path, "BaseNetworks")
        att_trans = mod.tool("inro.emme.data.extra_attribute.export_extra_attributes")
        attribute_list = ["@lanesam", "@vdfam", "@lanesmd", "@vdfmd", "@lanespm", "@vdfpm", "@tpfam", "@tpfmd", "@tpfpm"]
        att_trans(extra_attributes = attribute_list,
                  export_path = data_path,
                  append_to_file = False,
                  field_separator = ' ',
                  export_format = "PROMPT_DATA_FORMAT",
                  scenario = scen)

        if scen_id > 1200: return
        data_path = os.path.join(proj_path, "BaseNetworks", "transit_lines_%d.txt" % scen_id)
        lin_trans = mod.tool("inro.emme.data.network.transit.export_transit_lines")
        lin_trans(export_file = data_path,
                  append_to_file = False,
                  export_format = "PROMPT_DATA_FORMAT",
                  scenario = scen)
