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
        self.calcAttrs(1000, 1100, 1200)
        self.calcAttrs(2000, 2100, 2200)
        self.calcAttrs(3000, 3100, 3200)

        self.export(1000)
        self.export(1100)
        self.export(1200)
        self.export(2000)
        self.export(2100)
        self.export(2200)
        self.export(3000)
        self.export(3100)
        self.export(3200)

    def calcAttrs(self, am_scenid, md_scenid, pm_scenid):
        mod = _m.Modeller()
        eb = mod.emmebank
        project = mod.desktop.project
        proj_path = os.path.dirname(project.path)

        scenam = eb.scenario(am_scenid)
        scenmd = eb.scenario(md_scenid)
        scenpm = eb.scenario(pm_scenid)

        net_calc = mod.tool("inro.emme.network_calculation.network_calculator")

        lanesam_spec = {
            "type": "NETWORK_CALCULATION",
            "result": "@lanesam",
            "expression": "lanes",
            "aggregation": None,
            "selections": {
                "link": "all"
            }
        }

        vdfam_spec = {
            "type": "NETWORK_CALCULATION",
            "result": "@vdfam",
            "expression": "vdf",
            "aggregation": None,
            "selections": {
                "link": "all"
            }
        }

        tpfam_spec = {
            "type": "NETWORK_CALCULATION",
            "result": "@tpfam",
            "expression": "tpf",
            "aggregation": None,
            "selections": {
                "incoming_link": "all",
                "outgoing_link": "all"
            }
        }

        lanesmd_spec = {
            "type": "NETWORK_CALCULATION",
            "result": "@lanesmd",
            "expression": "lanes",
            "aggregation": None,
            "selections": {
                "link": "all"
            }
        }

        vdfmd_spec = {
            "type": "NETWORK_CALCULATION",
            "result": "@vdfmd",
            "expression": "vdf",
            "aggregation": None,
            "selections": {
                "link": "all"
            }
        }

        tpfmd_spec = {
            "type": "NETWORK_CALCULATION",
            "result": "@tpfmd",
            "expression": "tpf",
            "aggregation": None,
            "selections": {
                "incoming_link": "all",
                "outgoing_link": "all"
            }
        }

        lanespm_spec = {
            "type": "NETWORK_CALCULATION",
            "result": "@lanespm",
            "expression": "lanes",
            "aggregation": None,
            "selections": {
                "link": "all"
            }
        }

        vdfpm_spec = {
            "type": "NETWORK_CALCULATION",
            "result": "@vdfpm",
            "expression": "vdf",
            "aggregation": None,
            "selections": {
                "link": "all"
            }
        }

        tpfpm_spec = {
            "type": "NETWORK_CALCULATION",
            "result": "@tpfpm",
            "expression": "tpf",
            "aggregation": None,
            "selections": {
                "incoming_link": "all",
                "outgoing_link": "all"
            }
        }

        net_calc(lanesam_spec, scenam, False)
        net_calc(vdfam_spec, scenam, False)
        net_calc(tpfam_spec, scenam, False)

        net_calc(lanesmd_spec, scenmd, False)
        net_calc(vdfmd_spec, scenmd, False)
        net_calc(tpfmd_spec, scenmd, False)

        net_calc(lanespm_spec, scenpm, False)
        net_calc(vdfpm_spec, scenpm, False)
        net_calc(tpfpm_spec, scenpm, False)

        net_copy = mod.tool("inro.emme.data.network.copy_attribute")
        # fill in AM scenario with MD and PM
        net_copy(from_attribute_name="lanes", to_attribute_name="@lanesmd", from_scenario=scenmd, to_scenario=scenam)
        net_copy(from_attribute_name=  "vdf", to_attribute_name=  "@vdfmd", from_scenario=scenmd, to_scenario=scenam)
        net_copy(from_attribute_name=  "tpf", to_attribute_name=  "@tpfmd", from_scenario=scenmd, to_scenario=scenam)
        net_copy(from_attribute_name="lanes", to_attribute_name="@lanespm", from_scenario=scenpm, to_scenario=scenam)
        net_copy(from_attribute_name=  "vdf", to_attribute_name=  "@vdfpm", from_scenario=scenpm, to_scenario=scenam)
        net_copy(from_attribute_name=  "tpf", to_attribute_name=  "@tpfpm", from_scenario=scenpm, to_scenario=scenam)

        # fill in MD scenario with AM and PM
        net_copy(from_attribute_name="lanes", to_attribute_name="@lanesam", from_scenario=scenam, to_scenario=scenmd)
        net_copy(from_attribute_name=  "vdf", to_attribute_name=  "@vdfam", from_scenario=scenam, to_scenario=scenmd)
        net_copy(from_attribute_name=  "tpf", to_attribute_name=  "@tpfam", from_scenario=scenam, to_scenario=scenmd)
        net_copy(from_attribute_name="lanes", to_attribute_name="@lanespm", from_scenario=scenpm, to_scenario=scenmd)
        net_copy(from_attribute_name=  "vdf", to_attribute_name=  "@vdfpm", from_scenario=scenpm, to_scenario=scenmd)
        net_copy(from_attribute_name=  "tpf", to_attribute_name=  "@tpfpm", from_scenario=scenpm, to_scenario=scenmd)

        # fill in PM scenario with AM and MD
        net_copy(from_attribute_name="lanes", to_attribute_name="@lanesam", from_scenario=scenam, to_scenario=scenpm)
        net_copy(from_attribute_name=  "vdf", to_attribute_name=  "@vdfam", from_scenario=scenam, to_scenario=scenpm)
        net_copy(from_attribute_name=  "tpf", to_attribute_name=  "@tpfam", from_scenario=scenam, to_scenario=scenpm)
        net_copy(from_attribute_name="lanes", to_attribute_name="@lanesmd", from_scenario=scenmd, to_scenario=scenpm)
        net_copy(from_attribute_name=  "vdf", to_attribute_name=  "@vdfmd", from_scenario=scenmd, to_scenario=scenpm)
        net_copy(from_attribute_name=  "tpf", to_attribute_name=  "@tpfmd", from_scenario=scenmd, to_scenario=scenpm)

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
