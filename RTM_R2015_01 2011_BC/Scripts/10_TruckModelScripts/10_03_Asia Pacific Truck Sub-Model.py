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
        util = _m.Modeller().tool("translink.emme.util")

        #Batch input Asia Pacific matrix from TruckBatchFiles (gg ensemble format)
        util.delmat(eb, "mf1017")
        util.delmat(eb, "mf1018")
        util.delmat(eb, "mf1019")
        process = _m.Modeller().tool("inro.emme.data.matrix.matrix_transaction")
        root_directory = util.get_input_path(eb)
        matrix_file = os.path.join(root_directory, "TruckBatchFiles", str(Year)+"AsiaPacificv1.txt")
        process(transaction_file=matrix_file, throw_on_error=True)

        util.delmat(eb, "md205")
        matrix_file = os.path.join(root_directory, "TruckBatchFiles", "PMVActivity.txt")
        util.read_csv_momd(eb, matrix_file)

        util.initmat(eb, "ms153", "NonRet", "NonRetail Employment", 0)
        util.initmat(eb, "mf1020", "APHv24", "AP HvTrucks Daily Trips", 0)
        util.initmat(eb, "mf1021", "APHvAM", "AP HvTrucks AM Trips", 0)
        util.initmat(eb, "mf1022", "APHvMD", "AP HvTrucks MD Trips", 0)
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
