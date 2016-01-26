##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.stage5.step10.asiapacifictruck
##--Purpose: This module generates Asia Pacific Trucks (heavy trucks)
##--         Tables based on Port Metro Vancouver GPS Study
##---------------------------------------------------------------------
import inro.modeller as _m
import os
import traceback as _traceback

class AsiaPacificTruckModel(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Asia Pacific Truck Trips Model"
        pb.description = "Generates base/future forecasts for Asia Pacific trucks trips"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):


        self.tool_run_msg = ""

        try:
            Year=2011
            self.__call__(Year)
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    def __call__(self,Year):

        with _m.logbook_trace("Asia Pacific Truck Model"):
            #Batch input Asia Pacific matrix from TruckBatchFiles (gg ensemble format)
                process = _m.Modeller().tool("inro.emme.data.matrix.matrix_transaction")
                root_directory = os.path.dirname(_m.Modeller().emmebank.path) + "\\"
                matrix_file = os.path.join(root_directory, "TruckBatchFiles", str(Year)+"AsiaPacificv1.txt")
                process(transaction_file=matrix_file, throw_on_error=True)

                NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
            #Distribute Asia Pacific matrix for 'Other locations' based on non-retail employment
                compute_matrix = _m.Modeller().tool(NAMESPACE)


                Spec1={
                    "expression": "(md12-md8)*(gy(q).lt.13)",
                    "result": "ms153",
                    "constraint": {
                        "by_value": None,
                        "by_zone": {
                            "origins": None,
                            "destinations": "gg27"
                        }
                    },
                    "aggregation": {
                        "origins": None,
                        "destinations": "+"
                    },
                    "type": "MATRIX_CALCULATION"
                }


                Spec2={
                    "expression": "(md12-md8)/ms153*(gy(q).lt.13)",
                    "result": "md205",
                    "constraint": {
                        "by_value": None,
                        "by_zone": {
                            "origins": None,
                            "destinations": "gg27"
                        }
                    },
                    "aggregation": {
                        "origins": None,
                        "destinations": None
                    },
                    "type": "MATRIX_CALCULATION"
                }

                Spec3={
                    "expression": "md205'",
                    "result": "mo1005",
                    "constraint": {
                        "by_value": None,
                        "by_zone": None
                    },
                    "aggregation": {
                        "origins": None,
                        "destinations": None
                    },
                    "type": "MATRIX_CALCULATION"
                }

                compute_matrix(Spec1)
                compute_matrix(Spec2)
                compute_matrix(Spec3)

                Spec4={
                    "expression": "mf1017*mo1005*md205",
                    "result": "mf1053",
                    "constraint": {
                        "by_value": None,
                        "by_zone": None
                    },
                    "aggregation": {
                        "origins": None,
                        "destinations": None
                    },
                    "type": "MATRIX_CALCULATION"
                }
                CalcList=['mf1017','mf1018','mf1019']
                ResultList=['mf1020','mf1021','mf1022']

                for i in range (len(CalcList)):

                    Spec4['expression']=CalcList[i]+"*mo1005*md205"
                    Spec4['result']=ResultList[i]
                    compute_matrix(Spec4)
