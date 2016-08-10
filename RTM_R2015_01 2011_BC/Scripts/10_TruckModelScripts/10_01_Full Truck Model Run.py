##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage5.step10.truckmodel
##--Purpose: Run Full truck Model
##---------------------------------------------------------------------
import inro.modeller as _m
import os
import traceback as _traceback

class FullTruckModel(_m.Tool()):
    Year = _m.Attribute(str)
    AMScenario = _m.Attribute(_m.InstanceType)
    MDScenario = _m.Attribute(_m.InstanceType)

    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Full Truck Model Run"
        pb.description = "Run Full Truck Model"
        pb.branding_text = "TransLink"

        pb.add_select_scenario(tool_attribute_name="AMScenario",title="Select AM Scenario")

        pb.add_select_scenario(tool_attribute_name="MDScenario",title="Select MD Scenario")

        pb.add_select(tool_attribute_name="Year",keyvalues=[[2011,"2011"],[2030,"2030"],[2045,"2045"]],
                        title="Choose Analysis Year (2011, 2030 or 2045)")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        try:
            self.__call__(_m.Modeller().emmebank, self.Year, self.AMScenario, self.MDScenario)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool completed")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Full Truck Model Run")
    def __call__(self, eb, Year, AMScenario, MDScenario):
        ExternalModel=_m.Modeller().tool("translink.emme.stage5.step10.externaltruck")
        ExternalModel(eb, Year)
        AsiaPacificModel=_m.Modeller().tool("translink.emme.stage5.step10.asiapacifictruck")
        AsiaPacificModel(eb, Year)
        RegionalModel=_m.Modeller().tool("translink.emme.stage5.step10.regionaltruck")
        RegionalModel(eb)
        TruckAssign=_m.Modeller().tool("translink.emme.stage5.step10.truckassign")
        TruckAssign(eb, AMScenario, MDScenario)
