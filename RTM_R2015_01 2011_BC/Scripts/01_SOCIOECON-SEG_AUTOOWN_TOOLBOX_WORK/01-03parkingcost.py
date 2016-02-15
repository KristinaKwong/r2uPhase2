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
        util = _m.Modeller().tool("translink.emme.util")
        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

        #emmebank = _m.Modeller().emmebank
        #emmebank.create_matrix("md15")

        ##Definitions of work and nonwork parking cost coefficients
        work1 = str(0.1322)
        work2 = str(0.0019)
        work3 = str(0.0000005)
        nwk1 = str(0.1325)
        nwk2 = str(0.0006)
        nwk3 = str(0.0000002)

        specs = []
        #Transpose base density
        specs.append(util.matrix_spec("md15", "(mo15')"))

        #Calculate horizon density
        specs.append(util.matrix_spec("md101", "(mo20' + md12)/(0.000001+(mo17'))*10000"))

        #Recalculate base parking (work)
        specs.append(util.matrix_spec("md102", str(work1) + " + (md15*" + str(work2) + ") - (" + str(work3) + "*md15*md15)"))

        #Recalculate base parking (nonwork)
        specs.append(util.matrix_spec("md103", str(nwk1) + " + (md15*" + str(nwk2) + ") - (" + str(nwk3) + "*md15*md15)"))

        #Calculate future parking (work)
        specs.append(util.matrix_spec("md104", str(work1) + " + (md101*" + str(work2) + ") - (" + str(work3) + "*md101*md101)"))

        #Calculate future parking (nonwork)
        specs.append(util.matrix_spec("md105", str(nwk1) + " + (md101*" + str(nwk2) + ") - (" + str(nwk3) + "*md101*md101)"))

        #Work change calculation
        specs.append(util.matrix_spec("md106", "(((nint((md104-md102)*20))*0.05).max.0)"))

        #Nonwork change calculation
        specs.append(util.matrix_spec("md107", "(((nint((md105-md103)*20))*0.05).max.0)"))

        #Apply work increment
        specs.append(util.matrix_spec("mo27", "mo27+(md106')"))

        #Apply nonwork increment
        specs.append(util.matrix_spec("mo28", "mo28+(md107')"))

        #Override with zone-specific values
        specs.append(util.matrix_spec("mo27", "(mo27*(md108'.lt.0))+(md108'*(md108'.ge.0))"))
        specs.append(util.matrix_spec("mo28", "(mo28*(md109'.lt.0))+(md109'*(md109'.ge.0))"))

        #Create Work and NonWork Transposed Matrices
        specs.append(util.matrix_spec("md27", "(mo27')"))
        specs.append(util.matrix_spec("md28", "(mo28')"))

        #Run Matrix Computations
        report = compute_matrix(specs)
