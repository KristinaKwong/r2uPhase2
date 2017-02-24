##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage5.step10.asiapacifictruck
##--Purpose: This module generates Asia Pacific Trucks (heavy trucks)
##--         Tables based on Port Metro Vancouver GPS Study
##---------------------------------------------------------------------
import inro.modeller as _m
import os

class AsiaPacificTruckModel(_m.Tool()):
    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Asia Pacific Truck Trips Model"
        pb.description = "Generates base/future forecasts for Asia Pacific trucks trips"
        pb.branding_text = "TransLink"
        pb.runnable = False

        return pb.render()

    @_m.logbook_trace("Asia Pacific Truck Model")
    def __call__(self, eb, Year):
        util = _m.Modeller().tool("translink.util")

        #Distribute Asia Pacific matrix for "Other locations" based on non-retail employment
        specs = []

        spec = util.matrix_spec("ms153", "(md12-md8)*(gy(q).lt.13)")
        spec["constraint"]["by_zone"] = {"origins": None, "destinations": "gg27"}
        spec["aggregation"] = {"origins": None, "destinations": "+"}
        specs.append(spec)

        spec = util.matrix_spec("md205", "(md12-md8)/ms153*(gy(q).lt.13)")
        spec["constraint"]["by_zone"] = {"origins": None, "destinations": "gg27"}
        specs.append(spec)

        specs.append(util.matrix_spec("mf1020", "mf1017*md205'*md205"))
        specs.append(util.matrix_spec("mf1021", "mf1018*md205'*md205"))
        specs.append(util.matrix_spec("mf1022", "mf1019*md205'*md205"))
        util.compute_matrix(specs)
