##---------------------------------------------------------------------
##--TransLink Phase 3.3 Regional Transportation Model
##--
##--Path: translink.RTM3Analytics.UpdateScenarioVDF
##--Purpose: Update Scenarios to the RTM3.3 VDFs
##---------------------------------------------------------------------
import inro.modeller as _m
import inro.emme.database as _d
import traceback as _traceback

class UpdateScenarioVDF(_m.Tool()):
    scenarioList = _m.Attribute(_m.ListType)
    scenarioInc = _m.Attribute(int)
    capacitydefinition = _m.Attribute(str)
    tool_run_msg = _m.Attribute(unicode)

    def __init__(self):
        self.scenarioInc = 0

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Update Network VDF (Scenario)"
        pb.description = "<object align='left'>Convert RTM3.2 Network to RTM3.3 Network: Update VDF </object><br>" \
                         "<object align='left'>RTM3.2 VDF: 1, 3-7, 25-88 </object><br>"\
                         "<object align='left'>RTM3.3 VDF: 11-16</object>"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        pb.add_select_scenario("scenarioList", title="List of scenarios:")

        pb.add_text_box(tool_attribute_name="scenarioInc",
                        size="5",
                        title="Increment Updated Scenario ID by:",
                        note="Replace selected scenarios if increment = 0")

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            eb = _m.Modeller().emmebank

            self(self.scenarioList, self.scenarioInc)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    def __call__(self, scenarioList, scenarioInc):
        util = _m.Modeller().tool("translink.util")
        
        for scenario in scenarioList:
            #copy oginal scenario into target scenario (and apply increment)
            target_scenario_id = scenario.number+int(scenarioInc)
            if int(scenarioInc)!=0:
                copy_scenario = _m.Modeller().tool("inro.emme.data.scenario.copy_scenario")
                copy_scenario(from_scenario=scenario,
                              scenario_id=target_scenario_id,
                              scenario_title=scenario.title,
                              overwrite=True)
            scenario = scenario.emmebank.scenario(target_scenario_id)
            
            #calculate capacity into new attributes
            self.calculatecapacity(scenario)
            
            #add signal delay if the attribute does not exist
            signal_delay_exists = scenario.extra_attribute("@signal_delay")
            if not(signal_delay_exists):
                create_attr = _m.Modeller().tool("inro.emme.data.extra_attribute.create_extra_attribute")
                create_attr("LINK", "@signal_delay", "Signal Delay", 0, True, scenario)
                util.emme_link_calc(scenario, "@signal_delay", "0.25", sel_link="vdf=20,75")
            
            #lookup new vdf
            BaseNetworkScenario = scenario.extra_attribute("@vdfam")
            if BaseNetworkScenario:
                print("Base Network Scenario")
                # this is the new VDF lookup for base network scenario
                self.mapvdf(scenario, "@vdfam", "@vdfam")
                self.mapvdf(scenario, "@vdfmd", "@vdfmd")
                self.mapvdf(scenario, "@vdfpm", "@vdfpm")
                self.mapvdf(scenario, "vdf", "vdf")
            else:
                self.mapvdf(scenario, "vdf", "vdf")

    def mapvdf(self, scenario, output_attr, vdf_attr):
        util = _m.Modeller().tool("translink.util")

        util.emme_link_calc(scenario, output_attr, "11", sel_link=vdf_attr+"=1")
        util.emme_link_calc(scenario, output_attr, "12", sel_link=vdf_attr+"=2")
        util.emme_link_calc(scenario, output_attr, "13", sel_link=vdf_attr+"=3,7")
        util.emme_link_calc(scenario, output_attr, "14", sel_link=vdf_attr+"=20,75")
        util.emme_link_calc(scenario, output_attr, "15", sel_link=vdf_attr+"=80,85")
        util.emme_link_calc(scenario, output_attr, "16", sel_link=vdf_attr+"=88")

    def calculatecapacity(self, scenario, capacitydefinition="Nominal"):

        # define capacity per lane per function class digit
        CapacityUnit = {"Nominal":200, "Absolute":250}[capacitydefinition]
        StrCapacityUnit = str(CapacityUnit)
        StrConnectorCapacity = str(2000)

        create_attr = _m.Modeller().tool("inro.emme.data.extra_attribute.create_extra_attribute")
        util = _m.Modeller().tool("translink.util")

        BaseNetworkScenario = scenario.extra_attribute("@vdfam")
        if BaseNetworkScenario:
            print("Base Network Scenario")

            # initialize with centroid connector capacity
            create_attr("LINK", "@capacityam", "AM Roadway Lane Capacity", StrConnectorCapacity, True, scenario)
            create_attr("LINK", "@capacitymd", "MD Roadway Lane Capacity", StrConnectorCapacity, True, scenario)
            create_attr("LINK", "@capacitypm", "PM Roadway Lane Capacity", StrConnectorCapacity, True, scenario)

            # calculate merge lane capacity
            util.emme_link_calc(scenario, "@capacityam", StrCapacityUnit+"*@vdfam", sel_link="@vdfam=3,7")
            util.emme_link_calc(scenario, "@capacitymd", StrCapacityUnit+"*@vdfmd", sel_link="@vdfmd=3,7")
            util.emme_link_calc(scenario, "@capacitypm", StrCapacityUnit+"*@vdfpm", sel_link="@vdfpm=3,7")
            # calculate controlled intersection capacity
            util.emme_link_calc(scenario, "@capacityam", StrCapacityUnit+"*(@vdfam-@vdfam.mod.10)/10", sel_link="@vdfam=20,75")
            util.emme_link_calc(scenario, "@capacitymd", StrCapacityUnit+"*(@vdfmd-@vdfmd.mod.10)/10", sel_link="@vdfmd=20,75")
            util.emme_link_calc(scenario, "@capacitypm", StrCapacityUnit+"*(@vdfpm-@vdfpm.mod.10)/10", sel_link="@vdfpm=20,75")
            # calculate freeway capacity
            util.emme_link_calc(scenario, "@capacityam", StrCapacityUnit+"*8", sel_link="@vdfam=80,88")
            util.emme_link_calc(scenario, "@capacitymd", StrCapacityUnit+"*8", sel_link="@vdfmd=80,88")
            util.emme_link_calc(scenario, "@capacitypm", StrCapacityUnit+"*8", sel_link="@vdfpm=80,88")
        else:
            print("Time of Day Scenario")

            # initialize with centroid connector capacity
            create_attr("LINK", "@capacity", "Capacity", StrConnectorCapacity, True, scenario)

            # calculate merge lane capacity
            util.emme_link_calc(scenario, "@capacity", StrCapacityUnit+"*vdf", sel_link="vdf=3,7")
            # calculate controlled intersection capacity
            util.emme_link_calc(scenario, "@capacity", StrCapacityUnit+"*(vdf-vdf.mod.10)/10", sel_link="vdf=20,75")
            # calculate freeway capacity
            util.emme_link_calc(scenario, "@capacity", StrCapacityUnit+"*8", sel_link="vdf=80,88")
