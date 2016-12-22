##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: ?
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
            self.__call__(self.base_scenario)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Create Scenarios")
    def __call__(self, base_scenario):
        copy_scenario = _m.Modeller().tool("inro.emme.data.scenario.copy_scenario")

        eb = base_scenario.emmebank

        # Copy to new AM scenarios
        am_scenid = int(eb.matrix("ms2").data)
        copy_scenario(from_scenario=base_scenario,
                      scenario_id=am_scenid,
                      scenario_title=base_scenario.title,
                      overwrite=True)
        amscen = eb.scenario(am_scenid)

        self.attribute_code(amscen, "@lanesam", "@vdfam", "@tpfam", "@hdwyam", "@tollam")
        copy_scenario(from_scenario=amscen,
                      scenario_id=am_scenid + 30,
                      scenario_title=amscen.title + ": Final Iteration ",
                      overwrite=True)

        # Copy to new MD Scenarios
        md_scenid = int(eb.matrix("ms3").data)
        copy_scenario(from_scenario=base_scenario,
                      scenario_id=md_scenid,
                      scenario_title=base_scenario.title,
                      overwrite=True)
        mdscen = eb.scenario(md_scenid)

        self.attribute_code(mdscen, "@lanesmd", "@vdfmd", "@tpfmd", "@hdwymd", "@tollmd")
        copy_scenario(from_scenario=mdscen,
                      scenario_id=md_scenid + 30,
                      scenario_title=mdscen.title + ": Final Iteration ",
                      overwrite=True)

        # Copy to new pm Scenarios
        pm_scenid = int(eb.matrix("ms4").data)
        copy_scenario(from_scenario=base_scenario,
                      scenario_id=pm_scenid,
                      scenario_title=base_scenario.title,
                      overwrite=True)
        pmscen = eb.scenario(pm_scenid)

        self.attribute_code(pmscen, "@lanespm", "@vdfpm", "@tpfpm", "@hdwypm", "@tollpm")
        copy_scenario(from_scenario=pmscen,
                      scenario_id=pm_scenid + 30,
                      scenario_title=pmscen.title + ": Final Iteration ",
                      overwrite=True)

    def attribute_code(self, scen, lane_attr, vdf_attr, tpf_attr, hdw_attr, toll_attr):
        net_calc = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")
        create_attr = _m.Modeller().tool("inro.emme.data.extra_attribute.create_extra_attribute")
        delete_attr = _m.Modeller().tool("inro.emme.data.extra_attribute.delete_extra_attribute")

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
        delete_attr("@lanesam", scen)
        delete_attr("@lanesmd", scen)
        delete_attr("@lanespm", scen)

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
        delete_attr("@vdfam", scen)
        delete_attr("@vdfmd", scen)
        delete_attr("@vdfpm", scen)

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
        delete_attr("@tpfam", scen)
        delete_attr("@tpfmd", scen)
        delete_attr("@tpfpm", scen)

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
        delete_attr("@hdwyam", scen)
        delete_attr("@hdwymd", scen)
        delete_attr("@hdwypm", scen)

        create_attr("LINK", "@tolls", "Link Toll Value ($)", 0, False, scen)
        toll_spec = {
            "type": "NETWORK_CALCULATION",
            "result": "@tolls",
            "expression": toll_attr,
            "aggregation": None,
            "selections": {
                "link": "all"
            }
        }
        net_calc(toll_spec, scen, False)
        delete_attr("@tollam", scen)
        delete_attr("@tollmd", scen)
        delete_attr("@tollpm", scen)

        # Add all required extra attibutes used in Auto Assignment
        create_attr("LINK", "@sov1", "SOV Volume VOT1",     0, False, scen)
        create_attr("LINK", "@sov2", "SOV Volume VOT2",     0, False, scen)
        create_attr("LINK", "@sov3", "SOV Volume VOT3",     0, False, scen)
        create_attr("LINK", "@sov4", "SOV Volume VOT4",  0, False, scen)
        create_attr("LINK", "@sov5", "SOV Volume VOT5",  0, False, scen)
        create_attr("LINK", "@sov6", "SOV Volume VOT6",  0, False, scen)
        create_attr("LINK", "@hov1", "HOV Volume VOT1",     0, False, scen)
        create_attr("LINK", "@hov2", "HOV Volume VOT2",     0, False, scen)
        create_attr("LINK", "@hov3", "HOV Volume VOT3",     0, False, scen)
        create_attr("LINK", "@hov4", "HOV Volume VOT4",  0, False, scen)
        create_attr("LINK", "@hov5", "HOV Volume VOT5",  0, False, scen)
        create_attr("LINK", "@hov6", "HOV Volume VOT6",  0, False, scen)
        create_attr("LINK", "@wsovl", "SOV Link Volume", 0, False, scen)
        create_attr("LINK", "@whovl", "HOV Link Volume", 0, False, scen)
        create_attr("LINK", "@lgvol", "LGV Link Volume", 0, False, scen)
        create_attr("LINK", "@hgvol", "HGV Link Volume", 0, False, scen)
        create_attr("TURN", "@tsov1", "SOV Turn Volume VOT1",     0, False, scen)
        create_attr("TURN", "@tsov2", "SOV Turn Volume VOT2",     0, False, scen)
        create_attr("TURN", "@tsov3", "SOV Turn Volume VOT3",     0, False, scen)
        create_attr("TURN", "@tsov4", "SOV Turn Volume VOT4",  0, False, scen)
        create_attr("TURN", "@tsov5", "SOV Turn Volume VOT5",  0, False, scen)
        create_attr("TURN", "@tsov6", "SOV Turn Volume VOT6",  0, False, scen)
        create_attr("TURN", "@thov1", "HOV Turn Volume VOT1",     0, False, scen)
        create_attr("TURN", "@thov2", "HOV Turn Volume VOT2",     0, False, scen)
        create_attr("TURN", "@thov3", "HOV Turn Volume VOT3",     0, False, scen)
        create_attr("TURN", "@thov4", "HOV Turn Volume VOT4",  0, False, scen)
        create_attr("TURN", "@thov5", "HOV Turn Volume VOT5",  0, False, scen)
        create_attr("TURN", "@thov6", "HOV Turn Volume VOT6",  0, False, scen)
        create_attr("TURN", "@wsovt", "SOV Turn Volume", 0, False, scen)
        create_attr("TURN", "@whovt", "HOV Turn Volume", 0, False, scen)
        create_attr("TURN", "@lgvtn", "LGV Turn Volume", 0, False, scen)
        create_attr("TURN", "@hgvtn", "HGV Turn Volume", 0, False, scen)
        create_attr("LINK", "@sovoc", "SOV Operating Cost ($)", 0, False, scen)
        create_attr("LINK", "@hovoc", "HOV Operating Cost ($)", 0, False, scen)
        create_attr("LINK", "@lgvoc", "LGV Operating Cost ($)", 0, False, scen)
        create_attr("LINK", "@hgvoc", "HGV Operating Cost ($)", 0, False, scen)
        create_attr("LINK", "@tkpen", "Truck Penalty", 0, False, scen)

        # Add all required extra attibutes used in Transit Assignment
        create_attr("TRANSIT_LINE", "@seatcapacity", "Seated Line Capacity for time period", 0, False, scen)
        create_attr("TRANSIT_LINE", "@totcapacity", "Total Line Capacity for time period", 0, False, scen)
        create_attr("TRANSIT_LINE", "@dwtboard",  "Dwell Time Boarding Factor", 0, False, scen)
        create_attr("TRANSIT_LINE", "@dwtalight", "Dwell Time Alighting Factor", 0, False, scen)
        create_attr("TRANSIT_LINE", "@ridership", "Average Line Boardings", 0, False, scen)
        create_attr("TRANSIT_SEGMENT", "@hdwyfac", "Effective Headway Multiplier",1, False, scen)
        create_attr("TRANSIT_SEGMENT", "@hdwyeff",  "Effective Headway", 0, False, scen)
        create_attr("TRANSIT_SEGMENT", "@ivttfac",  "IVTT Perception Factor",1, False, scen)
        create_attr("TRANSIT_SEGMENT", "@pseat", "Number of Seated Passengers", 0, False, scen)
        create_attr("TRANSIT_SEGMENT", "@pstand", "Number of Standing Passengers", 0, False, scen)
        create_attr("TRANSIT_SEGMENT", "@boardavg",  "Average Boardings", 0, False, scen)
        create_attr("TRANSIT_SEGMENT", "@voltravg",  "Average Transit Segment Volume", 0, False, scen)
        create_attr("TRANSIT_SEGMENT", "@alightavg", "Average Alightings", 0, False, scen)
        create_attr("TRANSIT_SEGMENT", "@result", "Save temporary results", 0, False, scen)
        create_attr("TRANSIT_LINE", "@hfrac", "Headway Fraction", 0, False, scen)
        create_attr("TRANSIT_LINE", "@linefare", "Line Fare (zone1) for bus/skytrain ($)", 0, False, scen)
        create_attr("TRANSIT_LINE", "@xferlinefare", "Transfer Line Fare for bus/skytrain ($)", 0, False, scen)
        create_attr("TRANSIT_SEGMENT", "@fareincrement", "Increment Zone Fare ($)", 0, False, scen)
        create_attr("NODE", "@wcestopfare", "WCE Boarding Fare by Stop ($)", 0, False, scen)
        create_attr("NODE", "@wcexferfare", "Xfer WCE Boarding Fare by Stop($)", 0, False, scen)
