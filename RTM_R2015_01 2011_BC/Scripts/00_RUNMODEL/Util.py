##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.util
##--Purpose: Model Utility Methods
##---------------------------------------------------------------------
import inro.modeller as _m

import os
import csv as csv

class Util(_m.Tool()):
    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Translink Utility Toolbox"
        pb.description = "Collection of Utility Methods for Model Execution"
        pb.branding_text = "TransLink"
        pb.runnable = False

        return pb.render()

    def __call__(self):
        pass

    def initmat(self, eb, mat_id, name, description, value=0):
        mat = eb.matrix(mat_id)
        if mat:
            mat.read_only = False
            mat.initialize(value)
        else:
            mat = eb.create_matrix(mat_id, value)

        mat.name = name
        mat.description = description
        return mat

    def delmat(self, eb, mat_id):
        mat = eb.matrix(mat_id)
        if mat:
            mat.read_only = False
        eb.delete_matrix(mat_id)

    def matrix_spec(self, result, expression):
        spec = {
            "type": "MATRIX_CALCULATION",
            "result": result,
            "expression": expression
        }
        return spec

    @_m.logbook_trace("Delete Scenarios", save_arguments=True)
    def del_scen(self, scenario):
        delete_scen = _m.Modeller().tool("inro.emme.data.scenario.delete_scenario")
        delete_scen(scenario)

    @_m.logbook_trace("Export Matrices to CSV file", save_arguments=True)
    def export_csv(self, eb, list_of_matrices, output_file):
        scenario = list(eb.scenarios())[0]
        zones = scenario.zone_numbers

        matrix_data = []
        matrix_name = []
        matrix_desc = []
        for matrix_id in list_of_matrices:
            matrix = eb.matrix(matrix_id)
            matrix_data.append(matrix.get_data(scenario.id))
            matrix_name.append(matrix.name)
            matrix_desc.append(matrix.description)

        with open(output_file, 'wb') as f:
            writer = csv.writer(f, dialect='excel')
            writer.writerow(["matrices:"] + list_of_matrices)
            writer.writerow(["name:"] + matrix_name)
            writer.writerow(["description"] + matrix_desc)

            for z in zones:
                writer.writerow([z] + [data.get(z) for data in matrix_data])
