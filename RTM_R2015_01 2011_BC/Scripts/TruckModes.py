##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.truckmodes
##--Purpose: Code mode=n on a subset of link types
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback

class TruckModes(_m.Tool()):
    base_scenario = _m.Attribute(_m.InstanceType)
    tool_run_msg = ""

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Code mode=n on a subset of link types"
        pb.description = "Code mode=n on a subset of link types"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)
        pb.add_text_box(tool_attribute_name="base_scenario",
                        size=4,
                        title="Enter the Base Scenario Number")
        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            eb = _m.Modeller().emmebank
            self(eb, self.base_scenario)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, error:
            self.tool_run_msg = _m.PageBuilder.format_exception(
                error, _traceback.format_exc(error))
            raise

    @_m.logbook_trace("00_00 Create Scenarios")
    def __call__(self, eb, base_scenario):
        base_scenario = eb.scenario(base_scenario)

        mod_calc = _m.Modeller().tool("inro.emme.data.network.base.change_link_modes")
        mod_calc(modes="n",
                 action="DELETE",
                 selection="all",
                 scenario=base_scenario)

        not_truck_network_types = [303,304,310]
        not_truck_types ="| ".join(["type={} ".format(link_type) for link_type in not_truck_network_types]).rstrip()
        mod_calc(modes="n",
                 action="ADD",
                 selection=not_truck_types,
                 scenario=base_scenario)

