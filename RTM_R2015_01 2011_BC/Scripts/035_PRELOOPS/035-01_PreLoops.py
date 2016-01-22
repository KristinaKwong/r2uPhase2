## Trip Production model - HDR
import inro.modeller as _m

import os
import simplejson
import traceback as _traceback
from datetime import datetime


class PreLoop(_m.Tool()):
    ##Create global attributes (referring to dialogue boxes on the pages)
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        start_path = os.path.dirname(_m.Modeller().emmebank.path)
        ##Create various aspects to the page
        pb = _m.ToolPageBuilder(self, title="Pre Loops",
                                       description="Batches in required matrices for distribution and mode choice and copies initial skims ",
                                       branding_text="TransLink")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        with _m.logbook_trace("035-01 - RUN - PRELOOPS"):
            print "--------035-01 - RUN - TRIP PRELOOPS: " + str(datetime.now().strftime('%H:%M:%S'))
            ##        This gets executed when someone presses the big 'Start this Tool' button
            self.tool_run_msg = ""

            try:
                self.__call__()
                run_msg = "Tool completed"
                self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
            except Exception, e:
                self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))
        pass

    def __call__(self, PathHeader):
    ##        Start logging this under a new 'nest'
        with _m.logbook_trace("035-01 - PRELOOPS"):
            print "----035-01 - PRELOOPS: " + str(datetime.now().strftime('%H:%M:%S'))
            ##      Batches in trip distribution ij factors, trip distribution related matrices and intrazonal identity matrices
            self.Matrix_Batchins(PathHeader)
            ##        Copies starter skims mf893-mf920 to appropriate locations between mf100 and mf170
            self.Copy_Starter_Skims_Fares()

        pass


    def Matrix_Batchins(self, PathHeader):
        with _m.logbook_trace("Matrix Batchin"):
            print "--------Matrix_Batchins, " + str(datetime.now().strftime('%H:%M:%S'))
            NAMESPACE = "inro.emme.data.matrix.matrix_transaction"
            process = _m.Modeller().tool(NAMESPACE)
            matrix_file = PathHeader + "035_PRELOOPS/Inputs/MatrixTransactionFile.txt"

            ##        Creates process transaction
            process(transaction_file=matrix_file,
                    throw_on_error=True,
                    scenario=_m.Modeller().scenario)
        pass

    ##      Copy Starter Skims to appropriate locations
    def Copy_Starter_Skims_Fares(self):

        NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
        compute_matrix = _m.Modeller().tool(NAMESPACE)

        spec = """{
                "expression": "1",
                "result": "mf201",
                "constraint": {
                    "by_value": null,
                    "by_zone": null
                },
                "aggregation": {
                    "origins": null,
                    "destinations": null
                },
                "type": "MATRIX_CALCULATION"
            }"""
        spec_as_dict = simplejson.loads(spec)
        matrix1 = 100
        matrix2 = 893
        matrix3 = 160
        matrix4 = 161
        for i in range(28):
            if i < 10:
                expression = "mf" + str(matrix2 + i)
                result = "mf" + str(matrix1 + i)
            if i > 9 and i < 14:
                expression = "mf" + str(matrix2 + i)
                result = "mf" + str(matrix1 + i + 1)
            if i > 13 and i < 19:
                expression = "mf" + str(matrix2 + i)
                result = "mf" + str(matrix1 + i + 2)
            if i > 18 and i < 24:
                expression = "mf" + str(matrix2 + i)
                result = "mf" + str(matrix1 + i + 5)
            if i > 23 and i < 26:
                expression = "mf" + str(matrix2 + i)
                result = "mf" + str(matrix1 + i + 39)
            if i > 25 and i < 28:
                expression = "mf" + str(matrix2 + i)
                result = "mf" + str(matrix1 + i + 41)
            spec_as_dict["expression"] = expression
            spec_as_dict["result"] = result
            report = compute_matrix(spec_as_dict)

        expression = "mf" + str(matrix3)
        result = "mf" + str(matrix4)
        spec_as_dict["expression"] = expression
        spec_as_dict["result"] = result
        report = compute_matrix(spec_as_dict)


