##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage0.create_scenarios
##--Purpose: create scenarios
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback
import os
import csv

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
        util = _m.Modeller().tool("translink.util")
        copy_scenario = _m.Modeller().tool("inro.emme.data.scenario.copy_scenario")

        eb = base_scenario.emmebank

        # Copy to new AM scenarios
        am_scenid = (base_scenario.number * 10) + 1
        #am_scenid = 21000
        util.initmat(eb, "ms2", "AmScen", "AMScenario", am_scenid)
        copy_scenario(from_scenario=base_scenario,
                      scenario_id=am_scenid,
                      scenario_title=base_scenario.title + " AM",
                      overwrite=True)
        amscen = eb.scenario(am_scenid)

        self.attribute_code(amscen, "@lanesam", "@vdfam", "@tpfam", "@hdwyam", "@tollam", "@capacityam")

        # Copy to new MD Scenarios
        md_scenid = (base_scenario.number * 10) + 2
        #md_scenid = 22000
        util.initmat(eb, "ms3", "MdScen", "MDScenario", md_scenid)
        copy_scenario(from_scenario=base_scenario,
                      scenario_id=md_scenid,
                      scenario_title=base_scenario.title + " MD",
                      overwrite=True)
        mdscen = eb.scenario(md_scenid)

        self.attribute_code(mdscen, "@lanesmd", "@vdfmd", "@tpfmd", "@hdwymd", "@tollmd", "@capacitymd")

        # Copy to new PM Scenarios
        pm_scenid = (base_scenario.number * 10) + 3
        #pm_scenid = 23000
        util.initmat(eb, "ms4", "PmScen", "PMScenario", pm_scenid)
        copy_scenario(from_scenario=base_scenario,
                      scenario_id=pm_scenid,
                      scenario_title=base_scenario.title + " PM",
                      overwrite=True)
        pmscen = eb.scenario(pm_scenid)

        self.attribute_code(pmscen, "@lanespm", "@vdfpm", "@tpfpm", "@hdwypm", "@tollpm", "@capacitypm")

        util.custom_link_attributes(amscen, mdscen, pmscen)

        util.overide_network(amscen, mdscen, pmscen)

        util.custom_tline(amscen, mdscen, pmscen)

        util.custom_tseg(amscen, mdscen, pmscen)

    def attribute_code(self, scen, lane_attr, vdf_attr, tpf_attr, hdw_attr, toll_attr, capacity_attr):
        util = _m.Modeller().tool("translink.util")
        create_attr = _m.Modeller().tool("inro.emme.data.extra_attribute.create_extra_attribute")
        delete_attr = _m.Modeller().tool("inro.emme.data.extra_attribute.delete_extra_attribute")

        util.emme_link_calc(scen, "lanes", lane_attr)
        delete_attr("@lanesam", scen)
        delete_attr("@lanesmd", scen)
        delete_attr("@lanespm", scen)

        util.emme_link_calc(scen, "vdf", vdf_attr)
        delete_attr("@vdfam", scen)
        delete_attr("@vdfmd", scen)
        delete_attr("@vdfpm", scen)
        if True: # lookup new VDF coding
            util = _m.Modeller().tool("translink.util")
            util.emme_link_calc(scen, "vdf", "11", sel_link="vdf=1")
            util.emme_link_calc(scen, "vdf", "12", sel_link="vdf=2")
            util.emme_link_calc(scen, "vdf", "13", sel_link="vdf=3,7")
            util.emme_link_calc(scen, "vdf", "14", sel_link="vdf=20,75")
            util.emme_link_calc(scen, "vdf", "15", sel_link="vdf=80,85")
            util.emme_link_calc(scen, "vdf", "16", sel_link="vdf=88")

        util.emme_turn_calc(scen, "tpf", tpf_attr)
        delete_attr("@tpfam", scen)
        delete_attr("@tpfmd", scen)
        delete_attr("@tpfpm", scen)

        util.emme_tline_calc(scen, "hdw", hdw_attr)

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
        util.emme_link_calc(scen, "@tolls", toll_attr)
        delete_attr("@tollam", scen)
        delete_attr("@tollmd", scen)
        delete_attr("@tollpm", scen)

        create_attr("LINK", "@capacity", "Roadway Lane Capacity", 0, True, scen)
        util.emme_link_calc(scen, "@capacity", capacity_attr)
        delete_attr("@capacityam", scen)
        delete_attr("@capacitymd", scen)
        delete_attr("@capacitypm", scen)

        # Add all required extra attibutes used in Auto Assignment
        create_attr("LINK", "@sov1", "SOV Volume VOT1",  0, False, scen)
        create_attr("LINK", "@sov2", "SOV Volume VOT2",  0, False, scen)
        create_attr("LINK", "@sov3", "SOV Volume VOT3",  0, False, scen)
        create_attr("LINK", "@sov4", "SOV Volume VOT4",  0, False, scen)
        create_attr("LINK", "@hov1", "HOV Volume VOT1",  0, False, scen)
        create_attr("LINK", "@hov2", "HOV Volume VOT2",  0, False, scen)
        create_attr("LINK", "@hov3", "HOV Volume VOT3",  0, False, scen)
        create_attr("LINK", "@hov4", "HOV Volume VOT4",  0, False, scen)
        create_attr("LINK", "@wsovl", "SOV Link Volume", 0, False, scen)
        create_attr("LINK", "@whovl", "HOV Link Volume", 0, False, scen)
        create_attr("LINK", "@lgvol", "LGV Link Volume", 0, False, scen)
        create_attr("LINK", "@hgvol", "HGV Link Volume", 0, False, scen)
        create_attr("TURN", "@tsov1", "SOV Turn Volume VOT1", 0, False, scen)
        create_attr("TURN", "@tsov2", "SOV Turn Volume VOT2", 0, False, scen)
        create_attr("TURN", "@tsov3", "SOV Turn Volume VOT3", 0, False, scen)
        create_attr("TURN", "@tsov4", "SOV Turn Volume VOT4", 0, False, scen)
        create_attr("TURN", "@thov1", "HOV Turn Volume VOT1", 0, False, scen)
        create_attr("TURN", "@thov2", "HOV Turn Volume VOT2", 0, False, scen)
        create_attr("TURN", "@thov3", "HOV Turn Volume VOT3", 0, False, scen)
        create_attr("TURN", "@thov4", "HOV Turn Volume VOT4", 0, False, scen)
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
        create_attr("TRANSIT_LINE", "@ivtp",  "In vehicle travel time penalty", 0, False, scen)
        create_attr("TRANSIT_SEGMENT", "@hdwyfac", "Effective Headway Multiplier",1, False, scen)

        # Initialize transit segment boarding penalty to default penalty for the transit line
        create_attr("TRANSIT_SEGMENT", "@brdpeneff", "Effective Boarding Penalty",0, False, scen)
        util.emme_segment_calc(scen, "@brdpeneff", "@brdline")

        create_attr("TRANSIT_SEGMENT", "@hdwyeff",  "Effective Headway", 0, False, scen)
        create_attr("TRANSIT_SEGMENT", "@ivttfac",  "IVTT Perception Factor",1, False, scen)
        create_attr("TRANSIT_SEGMENT", "@pseat", "Number of Seated Passengers", 0, False, scen)
        create_attr("TRANSIT_SEGMENT", "@pstand", "Number of Standing Passengers", 0, False, scen)
        create_attr("TRANSIT_SEGMENT", "@boardavg",  "Average Boardings", 0, False, scen)
        create_attr("TRANSIT_SEGMENT", "@voltravg",  "Average Transit Segment Volume", 0, False, scen)
        create_attr("TRANSIT_SEGMENT", "@alightavg", "Average Alightings", 0, False, scen)
        create_attr("TRANSIT_LINE", "@hfrac", "Headway Fraction", 0, False, scen)
        create_attr("TRANSIT_LINE", "@linefare", "Line Fare (zone1) for bus/skytrain ($)", 0, False, scen)
        create_attr("TRANSIT_LINE", "@xferlinefare", "Transfer Line Fare for bus/skytrain ($)", 0, False, scen)
        create_attr("TRANSIT_SEGMENT", "@fareincrement", "Increment Zone Fare ($)", 0, False, scen)
        create_attr("NODE", "@wcestopfare", "WCE Boarding Fare by Stop ($)", 0, False, scen)
        create_attr("NODE", "@wcexferfare", "Xfer WCE Boarding Fare by Stop($)", 0, False, scen)
