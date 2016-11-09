##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
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

    def compute_matrix(self, specs, scenario=None, num_procs=None):
        comp = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

        if scenario is None:
            scenario = _m.Modeller().scenario

        if num_procs is None:
            eb = scenario.emmebank
            num_procs = int(eb.matrix("ms12").data)

        return comp(specs, scenario, num_procs)

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
        year = str(int(eb.matrix("ms10").data))
        return year

    def get_cycle(self, eb):
        """Returns the current model cycle number

        Arguments:
        eb -- The emmebank to be queried
        """
        return int(eb.matrix("ms01").data)

    def get_eb_path(self, eb):
        """Returns the directory containing the given databank

        Arguments:
        eb -- The emmebank to be queried
        """
        return os.path.dirname(eb.path)

    def get_output_path(self, eb):
        """Returns the outputs directory for the given databank

        Arguments:
        eb -- The emmebank to be queried
        """
        return os.path.join(os.path.dirname(eb.path), "Outputs")

    def get_input_path(self, eb):
        """Returns the inputs directory for the given databank

        Arguments:
        eb -- The emmebank to be queried
        """
        return os.path.join(os.path.dirname(eb.path), "Inputs")

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

        with open(output_file, "wb") as f:
            writer = csv.writer(f, dialect="excel")
            writer.writerow(["matrices:"] + list_of_matrices)
            writer.writerow(["name:"] + matrix_name)
            writer.writerow(["description"] + matrix_desc)

            for z in zones:
                writer.writerow([z] + [data.get(z) for data in matrix_data])


    @_m.logbook_trace("Reading csv file of mo/md values", save_arguments=True)
    def read_csv_momd(self, eb, file):
        #Read data from file and check number of lines
        with open(file, "rb") as sourcefile:
            lines = list(csv.reader(sourcefile, skipinitialspace=True))

        # Validate that each line has the same number of caolumns as the first line
        valid_cols = len(lines[0])
        for num in range(len(lines)):
            if len(lines[num]) != valid_cols:
                raise Exception("File: %s Line: %d - expected %d columns, found %d" % (file, num + 1, valid_cols, len(lines[num])))

        matrices = []
        mat_data = []
        # Initialize all matrices with 0-values and store a data reference
        for i in range(1, len(lines[0])):
            mat = self.initmat(eb, lines[0][i], lines[1][i], lines[2][i], 0)
            matrices.append(mat)
            mat_data.append(mat.get_data())

        # loop over each data-containing line in the csv
        for i in range(4, len(lines)):
            line = lines[i]
            # within each line set the data in each matrix
            for j in range(1, len(line)):
                mat_data[j-1].set(int(line[0]), float(line[j]))

        # store the data back into the matrix on disk
        for i in range(len(matrices)):
            matrices[i].set_data(mat_data[i])

    def get_matrix_numpy(self, eb, mat_id):
        """Get EMME matrix data as a numpy array

        Origin (mo) matrices will be reshaped to allow calculations to expand
        in a similar fashion to the EMME matrix calculator

        Arguments:
        eb -- the emmebank containing the matrix data
        mat_id -- a string matrix identifier (msXX, moXX, mdXX, mfXX)
        """
        mat = eb.matrix(mat_id)
        if (mat is None):
            return mat

        np_array = mat.get_numpy_data()

        if (mat.type == "ORIGIN"):
            np_array = np_array.reshape(np_array.shape[0], 1)

        return np_array

    def set_matrix_numpy(self, eb, mat_id, np_arr):
        """Set EMME matrix data from a numpy array

        Data input to Origin (mo) matrices will be reshaped as needed in case
        the numpy array has additional dimensions.

        Arguments:
        eb -- the emmebank containing the matrix data
        mat_id -- a string matrix identifier (msXX, moXX, mdXX, mfXX)
        np_arr -- the numpy array containing data to be written back
        """
        mat = eb.matrix(mat_id)

        if (mat.type == "ORIGIN" or mat.type == "DESTINATION"):
            if (np_arr.ndim == 2):
                np_arr = np_arr.reshape(np_arr.shape[0])

        mat.set_numpy_data(np_arr)

    def sumproduct(self, factors, matrices):
        if (len(factors) != len(matrices)):
            raise Exception("Length of factors and matrices passed to sumproduct must be equal")

        ret = 0
        for i in range(len(factors)):
            ret += factors[i] * matrices[i]
        return ret

    def emme_node_calc(self, scen, result, expression, sel_node="all"):
        calc_link = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")
        spec = { "result": result,
                 "expression": expression,
                 "selections": { "node": sel_node },
                 "type": "NETWORK_CALCULATION"
               }
        calc_link(spec, scenario=scen)

    def emme_link_calc(self, scen, result, expression, sel_link="all"):
        calc_link = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")
        spec = { "result": result,
                 "expression": expression,
                 "selections": { "link": sel_link },
                 "type": "NETWORK_CALCULATION"
               }
        calc_link(spec, scenario=scen)

    def emme_turn_calc(self, scen, result, expression, sel_inlink="all", sel_outlink="all"):
        calc_link = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")
        spec = { "result": result,
                 "expression": expression,
                 "selections": {"incoming_link": sel_inlink, "outgoing_link": sel_outlink},
                 "type": "NETWORK_CALCULATION"
               }
        calc_link(spec, scenario=scen)

    def emme_tline_calc(self, scen, result, expression, sel_line="all"):
        calc_link = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")
        spec = { "result": result,
                 "expression": expression,
                 "selections": {"transit_line": sel_line},
                 "type": "NETWORK_CALCULATION"
               }
        calc_link(spec, scenario=scen)

    def emme_segment_calc(self, scen, result, expression, sel_link="all", sel_line="all"):
        calc_link = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")
        spec = { "result": result,
                 "expression": expression,
                 "selections": {"link": sel_link, "transit_line": sel_line},
                 "type": "NETWORK_CALCULATION"
               }
        calc_link(spec, scenario=scen)
