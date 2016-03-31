##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage5.step10.regionaltruck
##--Purpose: This module generates light and heavy regional truck matrices
##--         Landuse Based Model produces trip light and heavy productions and attractions which are balanced
##--         Trip Distribution is conducted using gravity model
##--         Time Slice Factors used to derive AM and MD truck traffic
##---------------------------------------------------------------------
import inro.modeller as _m
import os
import traceback as _traceback

eb = _m.Modeller().emmebank

RgL11=107040
RgH11=45950

class RegTruckModel(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Regional Truck Trips Model"
        pb.description = "Generates base/future forecasts for regional light and heavy trucks trips"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):


        self.tool_run_msg = ""

        try:
            self.__call__()
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Regional Truck Model"):
    def __call__(self, Year, Sensitivity, RegionalGrowth1, RegionalGrowth2):
        util = _m.Modeller().tool("translink.emme.util")
        process = _m.Modeller().tool("inro.emme.data.matrix.matrix_transaction")
        root_directory = util.get_input_path(_m.Modeller().emmebank)
        matrix_file1 = os.path.join(root_directory, "TruckBatchFiles", "RGBatchIn.txt")
        process(transaction_file=matrix_file1, throw_on_error=True)

        # Run regional truck model Macro
        run_macro=_m.Modeller().tool("inro.emme.prompt.run_macro")
        run_macro(macro_name="../Scripts/10_TruckModelScripts/trkmodamregv1.mac")

        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

        spec = util.matrix_spec("ms151", "mf1031")
        spec["aggregation"]["origins"] = "+"
        spec["aggregation"]["destinations"] = "+"
        compute_matrix(spec)

        spec = util.matrix_spec("ms152", "mf1034")
        spec["aggregation"]["origins"] = "+"
        spec["aggregation"]["destinations"] = "+"
        compute_matrix(spec)

        RgLg = eb.matrix("ms151")
        RgHv=eb.matrix("ms152")
        RgLgVal=RgLg.data
        RgHvVal=RgHv.data

        # Determine Regional Sector Growth based on user inputs
        if Sensitivity=="N":
            RatioL=1
            RatioH=1

        else:

            CAGRLightI=(RgLgVal/RgL11)**(1/float(Year-2011))
            CAGRHeavyI=(RgHvVal/RgH11)**(1/float(Year-2011))
            RatioL=(RgLgVal/CAGRLightI**(Year-2030)*((1+RegionalGrowth1/100)/(CAGRLightI))**(2030-2011)*(1+RegionalGrowth2/100)**(Year-2030))/RgLgVal
            RatioH=(RgHvVal/CAGRHeavyI**(Year-2030)*((1+RegionalGrowth1/100)/(CAGRHeavyI))**(2030-2011)*(1+RegionalGrowth2/100)**(Year-2030))/RgHvVal


        MatrixList1=["mf1031","mf1035","mf1036"]
        MatrixList2=["mf1034","mf1037","mf1038"]

        for i in range(len(MatrixList1)):
            spec = util.matrix_spec(MatrixList1[i], MatrixList1[i] + "*" + str(RatioL))
            compute_matrix(spec)

        for i in range(len(MatrixList2)):
            spec = util.matrix_spec(MatrixList2[i], MatrixList2[i] + "*" + str(RatioH))
            compute_matrix(spec)
