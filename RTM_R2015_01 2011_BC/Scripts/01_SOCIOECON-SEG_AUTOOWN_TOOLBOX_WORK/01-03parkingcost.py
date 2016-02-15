##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.stage1.step1.parkingcost
##--Purpose: Incorporate parking cost for designated horizon year
##---------------------------------------------------------------------
##--Status/additional notes:
## Calculate Parking Cost based on base year variables
## If run on base year, will produce no change in costs
##---------------------------------------------------

import inro.modeller as _m
import traceback as _traceback

##Interactive code - use for running the test (user-input version)
class ParkingCostTool(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Parking Costs"
        pb.description = "Calculates Horizon Parking Costs. Not to be used directly, called from Socioeconomic segmentation"
        pb.branding_text = "TransLink"
        pb.runnable = False

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
            self.tool_run_msg = ""
            try:
                self()
                run_msg = "Tool completed"
                self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
            except Exception, e:
                self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Calculate Parking Costs")
    def __call__(self):
        #*************************************
        # THIS TOOL CURRENTLY DOES NOT RUN
        # It requires that mo15 contains input data
        # but this matrix is not generated or read-in
        # in the preceding steps of the model?
        # md15 also needs to be initialized. - KB
        #*************************************
        compute_matrix = _m.Modeller().tool(
            "inro.emme.matrix_calculation.matrix_calculator")

        spec_as_dict = {
            "expression": "EXPRESSION",
            "result": "RESULT",
            "constraint": {
                "by_value": None,
                "by_zone": {"origins": None, "destinations": None}
            },
            "aggregation": {"origins": None, "destinations": None},
            "type": "MATRIX_CALCULATION"
        }

        #emmebank = _m.Modeller().emmebank
        #emmebank.create_matrix("md15")

        ##Definitions of work and nonwork parking cost coefficients
        work1 = str(0.1322)
        work2 = str(0.0019)
        work3 = str(0.0000005)
        nwk1 = str(0.1325)
        nwk2 = str(0.0006)
        nwk3 = str(0.0000002)
        #Transpose base density
        spec_as_dict["expression"] = "(mo15')"
        spec_as_dict["result"] = "md15"
        report = compute_matrix(spec_as_dict)

        #Calculate horizon density
        spec_as_dict["expression"] = "(mo20' + md12)/(0.000001+(mo17'))*10000"
        spec_as_dict["result"] = "md101"
        report = compute_matrix(spec_as_dict)

        #Recalculate base parking (work)
        spec_as_dict["expression"] = str(work1) + " + (md15*" + str(work2) + ") - (" + str(work3) + "*md15*md15)"
        spec_as_dict["result"] = "md102"
        report = compute_matrix(spec_as_dict)

        #Recalculate base parking (nonwork)
        spec_as_dict["expression"] = str(nwk1) + " + (md15*" + str(nwk2) + ") - (" + str(nwk3) + "*md15*md15)"
        spec_as_dict["result"] = "md103"
        report = compute_matrix(spec_as_dict)

        #Calculate future parking (work)
        spec_as_dict["expression"] = str(work1) + " + (md101*" + str(work2) + ") - (" + str(work3) + "*md101*md101)"
        spec_as_dict["result"] = "md104"
        report = compute_matrix(spec_as_dict)

        #Calculate future parking (nonwork)
        spec_as_dict["expression"] = str(nwk1) + " + (md101*" + str(nwk2) + ") - (" + str(nwk3) + "*md101*md101)"
        spec_as_dict["result"] = "md105"
        report = compute_matrix(spec_as_dict)

        #Work change calculation
        spec_as_dict["expression"] = "(((nint((md104-md102)*20))*0.05).max.0)"
        spec_as_dict["result"] = "md106"
        report = compute_matrix(spec_as_dict)

        #Nonwork change calculation
        spec_as_dict["expression"] = "(((nint((md105-md103)*20))*0.05).max.0)"
        spec_as_dict["result"] = "md107"
        report = compute_matrix(spec_as_dict)

        #Apply work increment
        spec_as_dict["expression"] = "mo27+(md106')"
        spec_as_dict["result"] = "mo27"
        report = compute_matrix(spec_as_dict)

        #Apply nonwork increment
        spec_as_dict["expression"] = "mo28+(md107')"
        spec_as_dict["result"] = "mo28"
        report = compute_matrix(spec_as_dict)

        #Override with zone-specific values
        spec_as_dict["expression"] = "(mo27*(md108'.lt.0))+(md108'*(md108'.ge.0))"
        spec_as_dict["result"] = "mo27"
        report = compute_matrix(spec_as_dict)

        #Override with zone-specific values
        spec_as_dict["expression"] = "(mo28*(md109'.lt.0))+(md109'*(md109'.ge.0))"
        spec_as_dict["result"] = "mo28"
        report = compute_matrix(spec_as_dict)

        #Work transpose
        spec_as_dict["expression"] = "(mo27')"
        spec_as_dict["result"] = "md27"
        report = compute_matrix(spec_as_dict)

        #Nonwork transpose
        spec_as_dict["expression"] = "(mo28')"
        spec_as_dict["result"] = "md28"
        report = compute_matrix(spec_as_dict)
