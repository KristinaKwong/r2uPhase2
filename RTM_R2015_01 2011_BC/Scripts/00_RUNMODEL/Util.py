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
        """Fully Initialize a matrix whether it currently exists or not.

        Returns the initialized matrix object.

        Arguments:
        eb -- the emmebank object to initialize the matrix in
        mat_id -- the id of the matrix to initialize, eg ms01
        name -- the name to set for the matrix
        description - the description to set for the matrix
        value -- the initial value for all matrix elements (default 0)
        """
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
        """Delete a matrix whether it currently exists or not or is protected against deletion.

        Arguments:
        eb -- the emmebank object to delete the matrix in
        mat_id -- the id of the matrix to delete, eg ms01
        """
        mat = eb.matrix(mat_id)
        if mat:
            mat.read_only = False
            eb.delete_matrix(mat_id)

    def matrix_spec(self, result, expression):
        """Returns a matrix specification dictionary with a result and expression set.

        Arguments:
        result -- the string stored in the "result" key
        expression -- the string stored in the "expression" key
        """
        spec = {
            "type": "MATRIX_CALCULATION",
            "result": result,
            "expression": expression,
            "constraint": {},
            "aggregation": {}
        }
        return spec

    def matrix_sum(self, matrices):
        """Returns a string representation of a summation expression containing all matrix names passed in.

        Arguments:
        matrices -- a list of matrix names
        """

        sum = "(" + " + ".join(matrices) + ")"
        return sum

    @_m.logbook_trace("Delete Scenarios", save_arguments=True)
    def del_scen(self, scenario):
        """Delete the given scenario.

        Arguments:
        scenario -- the scenario to delete
        """
        delete_scen = _m.Modeller().tool("inro.emme.data.scenario.delete_scenario")
        delete_scen(scenario)

    def get_year(self, eb):
        """Returns a string containing the 4-digit year for the current model.

        Arguments:
        eb -- The emmebank to be queried
        """
        year = str(int(eb.matrix("ms149").data))
        return year

    @_m.logbook_trace("Export Matrices to CSV file", save_arguments=True)
    def export_csv(self, eb, list_of_matrices, output_file):
        """Write individual mo/md matrices including a descriptive header in csv format.

        Arguments:
        eb -- the emmebank containing the matrices to be exported
        list_of_matrices -- a list of matrix identifiers
        output_file -- the fully qualified path to the file to output the matrices to
        """
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
