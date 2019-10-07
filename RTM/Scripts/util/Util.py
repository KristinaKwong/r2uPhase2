##---------------------------------------------------------------------
##--TransLink Regional Transportation Model
##--
##--Path: translink.util
##--Purpose: Model Utility Methods
##---------------------------------------------------------------------
import inro.modeller as _m

import os
import csv as csv

import sqlite3
import pandas as pd

import inro.emme as _emme

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
            num_procs_mat = eb.matrix("ms12")
            if num_procs_mat is None:
                num_procs = 1
            else:
                num_procs = int(num_procs_mat.data)

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

    def get_rtm_db(self, eb):
        db_file = os.path.join(self.get_eb_path(eb), "rtm.db")
        return sqlite3.connect(db_file)

    def get_db_byname(self, eb, db_name):
        db_file = os.path.join(self.get_eb_path(eb), db_name)
        return sqlite3.connect(db_file)

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

    @_m.logbook_trace("Reading csv file of ms values", save_arguments=True)
    def read_csv_ms(self, eb, f):
        with open(f, "rb") as sourcefile:
            lines = list(csv.reader(sourcefile, skipinitialspace=True))

        valid_cols = len(lines[0])
        for num in range(len(lines)):
            if len(lines[num]) != valid_cols:
                raise Exception("File: %s Line: %d - expected %d columns, found %d" % (file, num + 1, valid_cols, len(lines[num])))

        for i in range(1, len(lines)):
            self.initmat(eb, lines[i][0], lines[i][1], lines[i][2], float(lines[i][3]))

    def get_matrix_numpy(self, eb, mat_id, reshape=True):
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

        if (reshape):
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
            if (np_arr.ndim != 1):
                np_arr = np_arr.reshape(mat.get_numpy_data().shape)

        if (mat.type == "FULL"):
            if (np_arr.ndim != 2):
                np_arr = np_arr.reshape(mat.get_numpy_data().shape)

        mat.set_numpy_data(np_arr)

    def add_matrix_numpy(self, eb, mat_id, np_arr):
        """Add the numpy array to EMME matrix data. Useful for running sums.

        Data input to Origin (mo) matrices will be reshaped as needed in case
        the numpy array has additional dimensions.

        Arguments:
        eb -- the emmebank containing the matrix data
        mat_id -- a string matrix identifier (msXX, moXX, mdXX, mfXX)
        np_arr -- the numpy array containing data to be added to the given matrix
        """
        mat = self.get_matrix_numpy(eb, mat_id)
        mat += np_arr
        self.set_matrix_numpy(eb, mat_id, mat)

    def get_pd_ij_df(self, eb):
        index_row = self.get_matrix_numpy(eb, "mozoneindex", reshape=False)
        # create a column version of the row array
        index_col = index_row.reshape(index_row.shape[0], 1)

        # expand to a full matrix containing the origin zone number in each cell
        i = index_col + (0 * index_row)

        ij = pd.DataFrame()
        ij["i"] = i.flatten()
        ij["j"] = i.transpose().flatten()
        return ij

    def get_ijensem_df(self, eb, ensem_o, ensem_d=None):
        if ensem_d is None:
            ensem_d = ensem_o

        orig_mat = "mo%s_ensem" % ensem_o
        dest_mat = "mo%s_ensem" % ensem_d

        orig_row = self.get_matrix_numpy(eb, orig_mat, reshape=False)
        orig_col = orig_row.reshape(orig_row.shape[0], 1)

        dest_row = self.get_matrix_numpy(eb, dest_mat, reshape=False)
        dest_col = dest_row.reshape(dest_row.shape[0], 1)

        # Note that the destination ensemble is created transposed (swap row and column)
        orig_full = orig_col + (0 * orig_row)
        dest_full = dest_row + (0 * dest_col)

        ij = pd.DataFrame()
        ij[ensem_o + "_i"] = orig_full.flatten()
        ij[ensem_d + "_j"] = dest_full.flatten()
        return ij

    def sumproduct(self, factors, matrices):
        if (len(factors) != len(matrices)):
            raise Exception("Length of factors and matrices passed to sumproduct must be equal")

        ret = 0
        for i in range(len(factors)):
            ret += factors[i] * matrices[i]
        return ret

    def emme_node_calc(self, scen, result, expression, sel_node="all", aggregate=None):
        calc_link = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")
        spec = { "result": result,
                 "expression": expression,
                 "selections": { "node": sel_node },
                 "aggregation": aggregate,
                 "type": "NETWORK_CALCULATION"
               }
        return calc_link(spec, scenario=scen)

    def emme_link_calc(self, scen, result, expression, sel_link="all", aggregate=None):
        calc_link = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")
        spec = { "result": result,
                 "expression": expression,
                 "selections": { "link": sel_link },
                 "aggregation": aggregate,
                 "type": "NETWORK_CALCULATION"
               }
        return calc_link(spec, scenario=scen)

    def emme_turn_calc(self, scen, result, expression, sel_inlink="all", sel_outlink="all", aggregate=None):
        calc_link = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")
        spec = { "result": result,
                 "expression": expression,
                 "selections": {"incoming_link": sel_inlink, "outgoing_link": sel_outlink},
                 "aggregation": aggregate,
                 "type": "NETWORK_CALCULATION"
               }
        return calc_link(spec, scenario=scen)

    def emme_tline_calc(self, scen, result, expression, sel_line="all", aggregate=None):
        calc_link = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")
        spec = { "result": result,
                 "expression": expression,
                 "selections": {"transit_line": sel_line},
                 "aggregation": aggregate,
                 "type": "NETWORK_CALCULATION"
               }
        return calc_link(spec, scenario=scen)

    def emme_segment_calc(self, scen, result, expression, sel_link="all", sel_line="all", aggregate=None):
        calc_link = _m.Modeller().tool("inro.emme.network_calculation.network_calculator")
        spec = { "result": result,
                 "expression": expression,
                 "selections": {"link": sel_link, "transit_line": sel_line},
                 "aggregation": aggregate,
                 "type": "NETWORK_CALCULATION"
               }
        return calc_link(spec, scenario=scen)

    def overide_network(self, amscen, mdscen, pmscen):

        custom_network = os.path.join(self.get_input_path(amscen.emmebank), 'custom_network.txt')
        if not os.path.isfile(custom_network):
            return

        with open(custom_network, "rb") as sourcefile:
            lines = list(csv.reader(sourcefile, skipinitialspace=True, delimiter='\t'))

        for line in lines:
            # skip commented lines
            if line[0].startswith('#'):
                continue
            # error on short records
            if len(line) < 3:
                raise Exception("Error reading custom network file, less than 3 columns found")

            per = line[0].strip()
            res = line[1].strip()
            exp = line[2].strip()

            sel = "all"
            if len(line) > 3:
                sel = line[3].strip()
            agg = None
            if len(line) > 4:
                agg = line[4].strip()

            if per == "AM" or per == "ALL":
                self.emme_link_calc(amscen, res, exp, sel, agg)

            if per == "MD" or per == "ALL":
                self.emme_link_calc(mdscen, res, exp, sel, agg)

            if per == "PM" or per == "ALL":
                self.emme_link_calc(pmscen, res, exp, sel, agg)

    def custom_tline(self, amscen, mdscen, pmscen):

        custom_network = os.path.join(self.get_input_path(amscen.emmebank), 'custom_tline.txt')
        if not os.path.isfile(custom_network):
            return

        with open(custom_network, "rb") as sourcefile:
            lines = list(csv.reader(sourcefile, skipinitialspace=True, delimiter='\t'))

        for line in lines:
            # skip commented lines
            if line[0].startswith('#'):
                continue
            # error on short records
            if len(line) < 3:
                raise Exception("Error reading custom network file, less than 3 columns found")

            per = line[0].strip()
            res = line[1].strip()
            exp = line[2].strip()

            sel = "all"
            if len(line) > 3:
                sel = line[3].strip()
            agg = None
            if len(line) > 4:
                agg = line[4].strip()

            if per == "AM" or per == "ALL":
                self.emme_tline_calc(amscen, res, exp, sel, agg)

            if per == "MD" or per == "ALL":
                self.emme_tline_calc(mdscen, res, exp, sel, agg)

            if per == "PM" or per == "ALL":
                self.emme_tline_calc(pmscen, res, exp, sel, agg)

    def custom_link_attributes(self, amscen, mdscen, pmscen):

        create_attr = _m.Modeller().tool("inro.emme.data.extra_attribute.create_extra_attribute")
        import_values = _m.Modeller().tool("inro.emme.data.network.import_attribute_values")

        scens = [amscen,mdscen,pmscen]

        custom_attributes = os.path.join(self.get_input_path(amscen.emmebank), 'custom_attributes.txt')
        if not os.path.isfile(custom_attributes):
            return

        with open(custom_attributes) as f:
            reader =csv.reader(f, delimiter ='\t')
            col_labs = reader.next()       

        new_attributes = col_labs[2:]

        for scen in scens:
            for attr in new_attributes:
                create_attr("LINK", attr, attr[1:], 0, False, scen)
            import_values(file_path=custom_attributes,
                            field_separator='TAB', 
                            scenario=scen, 
                            column_labels=col_labs, 
                            revert_on_error=True)

    def get_tod_scenarios(self, eb):
        am_scen = eb.scenario(int(eb.matrix("msAmScen").data))
        md_scen = eb.scenario(int(eb.matrix("msMdScen").data))
        pm_scen = eb.scenario(int(eb.matrix("msPmScen").data))

        return (am_scen, md_scen, pm_scen)

    def set_ensemble_from_mo(self, eb, part, orig_mat):
        mat = eb.matrix(orig_mat)

        matData = _emme.matrix.MatrixData(mat.get_data().indices, type="I")
        matData.from_numpy(mat.get_numpy_data())

        ensem = eb.partition(part)
        ensem.description = mat.description
        ensem.set_data(matData)
