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

    Year= _m.Attribute(str)
    Sensitivity=_m.Attribute(str)
    ExtGrowth1=_m.Attribute(float)
    ExtGrowth2=_m.Attribute(float)
    AMScenario=_m.Attribute(_m.InstanceType)
    MDScenario=_m.Attribute(_m.InstanceType)
    CascadeGrowth1=_m.Attribute(float)
    CascadeGrowth2=_m.Attribute(float)

    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Full Truck Model Run"
        pb.description = "Run Full Truck Model"
        pb.branding_text = "TransLink"

        pb.add_select_scenario(tool_attribute_name="AMScenario",title="Select AM Scenario")

        pb.add_select_scenario(tool_attribute_name="MDScenario",title="Select MD Scenario")

        pb.add_select(tool_attribute_name="Year",keyvalues=[["1","2011"],["2","2030"],["3","2045"]],
                        title="Choose Analysis Year (2011, 2030 or 2045)")

        pb.add_select(tool_attribute_name="Sensitivity",keyvalues=[["N","No"],["Y","Yes"]],
                        title="Choose whether to modify truck growth rates ")

        with pb.section("Sensitivity options-Future Runs:"):
            pb.add_text_box(tool_attribute_name="ExtGrowth1",
                            size="3",
                            title="Enter External Sector % Growth Assumption 2011-2030 ")

            pb.add_text_box(tool_attribute_name="ExtGrowth2",
                            size="3",
                            title="Enter External Sector % Growth Assumption 2030-2045")

            pb.add_text_box(tool_attribute_name="CascadeGrowth1",
                            size="3",
                            title="Enter Cascade Cross-Border % Growth Assumption 2011-2030")

            pb.add_text_box(tool_attribute_name="CascadeGrowth2",
                            size="3",
                            title="Enter Cascade Cross-Border % Growth Assumption 2030-2045")
        pb.add_html("""
            <script>
                $(document).ready( function ()
                {
                    // indent tool section items
                    $(".t_tool_section")
                        .children(".t_element")
                        .css("padding-left", "70px");

                    $("#Sensitivity").bind("change", function ()
                    {
                        $(this).commit();
                        if ($(this).val() == "N")
                            var disable = true;
                        else
                            var disable = false;
                        $("#ExtGrowth1").prop("disabled", disable);
                        $("#ExtGrowth2").prop("disabled", disable);
                        $("#CascadeGrowth1").prop("disabled", disable);
                        $("#CascadeGrowth2").prop("disabled", disable);
                    }).trigger("change") ;
                });
            </script>""")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):


        try:
            if self.Year=="1":
                AnalysisYear=2011
                self.Sensitivity="N"
                self.ExtGrowth1=""
                self.ExtGrowth2=""
                self.CascadeGrowth1=""
                self.CascadeGrowth2=""
                self.__call__(AnalysisYear,self.Sensitivity,self.AMScenario,self.MDScenario,0,0,0,0,0,0,"")

            if self.Year=="2":
                AnalysisYear=2030
                if self.Sensitivity=="N":
                    self.ExtGrowth1=""
                    self.ExtGrowth2=""
                    self.CascadeGrowth1=""
                    self.CascadeGrowth2=""


                if self.Sensitivity=="Y":
                    self.ExtGrowth2=""
                    self.CascadeGrowth2=""

                self.__call__(AnalysisYear, self.Sensitivity,self.AMScenario,self.MDScenario,self.ExtGrowth1, 0
                , self.CascadeGrowth1, 0, 0, 0, 0)

            if self.Year=="3":
                AnalysisYear=2045
                if self.Sensitivity=="N":
                    self.ExtGrowth1=""
                    self.ExtGrowth2=""
                    self.CascadeGrowth1=""
                    self.CascadeGrowth2=""

                self.__call__(AnalysisYear, self.Sensitivity,self.AMScenario,self.MDScenario,self.ExtGrowth1, self.ExtGrowth2, self.CascadeGrowth1, self.CascadeGrowth2,
                                0, 0, 0)


            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)


        except Exception, e:


                self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))


    @_m.logbook_trace("Full Truck Model Run")
    def __call__(self, Year, Sensitivity, AMScenario,MDScenario, ExtGrowth1, ExtGrowth2, CascadeGrowth1, CascadeGrowth2, RegionalGrowth1, RegionalGrowth2, AsiaPacificGrowth):
        eb = _m.Modeller().emmebank

        ExternalModel=_m.Modeller().tool("translink.emme.stage5.step10.externaltruck")
        ExternalModel(Year,Sensitivity,ExtGrowth1,ExtGrowth2, CascadeGrowth1, CascadeGrowth2)
        AsiaPacificModel=_m.Modeller().tool("translink.emme.stage5.step10.asiapacifictruck")
        AsiaPacificModel(eb, Year)
        RegionalModel=_m.Modeller().tool("translink.emme.stage5.step10.regionaltruck")
        RegionalModel(eb)
        TruckAssign=_m.Modeller().tool("translink.emme.stage5.step10.truckassign")
        TruckAssign(eb, AMScenario, MDScenario)
