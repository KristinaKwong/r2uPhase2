##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage1.step0.create_scen
##--Purpose: create scenarios
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback

class InputSettings(_m.Tool()):
    base_scenario = _m.Attribute(_m.InstanceType)
    tool_run_msg = ""

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Create Scenarios"
        pb.description = "Create Scenarios for Model Run."
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)
        pb.add_select_scenario(tool_attribute_name="base_scenario",
                        title="Enter the Base Scenario Number")
        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            self(self.base_scenario)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, error:
            self.tool_run_msg = _m.PageBuilder.format_exception(
                error, _traceback.format_exc(error))
            raise

    @_m.logbook_trace("00_00 Create Scenarios")
    def __call__(self, base_scenario):
        copy_scenario = _m.Modeller().tool("inro.emme.data.scenario.copy_scenario")

        eb = base_scenario.emmebank

        # Copy to new AM scenarios
        am_scenid = int(eb.matrix("ms140").data)
        copy_scenario(from_scenario=base_scenario,
                      scenario_id=am_scenid,
                      scenario_title=base_scenario.title,
                      overwrite=True)
        amscen = eb.scenario(am_scenid)

        self.attribute_code(amscen, "@lanesam", "@vdfam", "@tpfam", "@hdwyam")
        copy_scenario(from_scenario=amscen,
                      scenario_id=am_scenid + 30,
                      scenario_title=amscen.title + ": Final Iteration ",
                      overwrite=True)

        # Copy to new MD Scenarios
        md_scenid = int(eb.matrix("ms141").data)
        copy_scenario(from_scenario=base_scenario,
                      scenario_id=md_scenid,
                      scenario_title=base_scenario.title,
                      overwrite=True)
        mdscen = eb.scenario(md_scenid)

        self.attribute_code(mdscen, "@lanesmd", "@vdfmd", "@tpfmd", "@hdwymd")
        copy_scenario(from_scenario=mdscen,
                      scenario_id=md_scenid + 30,
                      scenario_title=mdscen.title + ": Final Iteration ",
                      overwrite=True)

        # Copy to new pm Scenarios
        pm_scenid = int(eb.matrix("ms150").data)
        copy_scenario(from_scenario=base_scenario,
                      scenario_id=pm_scenid,
                      scenario_title=base_scenario.title,
                      overwrite=True)
        pmscen = eb.scenario(pm_scenid)

        self.attribute_code(pmscen, "@lanespm", "@vdfpm", "@tpfpm", "@hdwypm")
        copy_scenario(from_scenario=pmscen,
                      scenario_id=pm_scenid + 30,
                      scenario_title=pmscen.title + ": Final Iteration ",
                      overwrite=True)

    def attribute_code(self, scen, lane_attr, vdf_attr, tpf_attr, hdw_attr):
        net_calc = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")

        lane_spec = {
            "type": "NETWORK_CALCULATION",
            "result": "lanes",
            "expression": lane_attr,
            "aggregation": None,
            "selections": {
                "link": "all"
            }
        }
        net_calc(lane_spec, scen, False)

        vdf_spec = {
            "type": "NETWORK_CALCULATION",
            "result": "vdf",
            "expression": vdf_attr,
            "aggregation": None,
            "selections": {
                "link": "all"
            }
        }
        net_calc(vdf_spec, scen, False)

        tpf_spec = {
            "type": "NETWORK_CALCULATION",
            "result": "tpf",
            "expression": tpf_attr,
            "aggregation": None,
            "selections": {
                "incoming_link": "all",
                "outgoing_link": "all"
            }
        }
        net_calc(tpf_spec, scen, False)

        hdw_spec = {
            "type": "NETWORK_CALCULATION",
            "result": "hdw",
            "expression": hdw_attr,
            "aggregation": None,
            "selections": {
                "transit_line": "all"
            }
        }
        net_calc(hdw_spec, scen, False)

        mod_calc = _m.Modeller().tool("inro.emme.data.network.base.change_link_modes")
        mod_calc(modes="v",
                 action="DELETE",
                 selection="lanes=0",
                 scenario=scen)

        del_transit = _m.Modeller().tool("inro.emme.data.network.transit.delete_transit_lines")
        del_transit(selection=hdw_attr+"=0",
                    scenario=scen)
