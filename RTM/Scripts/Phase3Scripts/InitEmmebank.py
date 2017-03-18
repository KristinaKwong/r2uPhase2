##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.init_emmebank
##--Purpose: initialize a new emmebank from source text files
##---------------------------------------------------------------------
import inro.modeller as _m
import inro.emme as _emme
import traceback as _traceback
import os
import shutil
import pandas as pd

class InitEmmebank(_m.Tool()):
    emme_title = _m.Attribute(_m.InstanceType)
    emme_folder = _m.Attribute(_m.InstanceType)
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Translink Utility Toolbox"
        pb.description = "Initialize a new Emmebank"
        pb.branding_text = "TransLink"

        pb.add_text_box(tool_attribute_name="emme_folder",
                        size=30,
                        title="Enter the Folder Name for the new emmebank")

        pb.add_text_box(tool_attribute_name="emme_title",
                        size=30,
                        title="Enter the Title for the new emmebank")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        try:
            self.__call__()
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Initializing a new emmebank")
    def __call__(self):
        new_path = self.initfolder(self.emme_folder)

        self.initbank(new_path, self.emme_title)
        _m.Modeller().desktop.data_explorer().add_database(new_path).open()
        self.initdatabase(_m.Modeller().emmebank)


    def initbank(self, path, title):
        dim = {"scalar_matrices": 9999,
               "origin_matrices": 9999,
               "destination_matrices": 9999,
               "full_matrices": 9999,
               "scenarios": 30,
               "functions": 99,
               "operators": 5000,
               "centroids": 1750,
               "regular_nodes": 9000,
               "links": 22000,
               "turn_entries": 15000,
               "extra_attribute_values": 2000000,
               "transit_lines": 2000,
               "transit_segments": 60000,
               "transit_vehicles": 600}

        with _emme.database.emmebank.create(path, dim) as eb:
            eb.title = title
            eb.coord_unit_length = 1.0
            eb.unit_of_length = "km"
            eb.unit_of_cost = "$"
            eb.unit_of_energy = "mj"
            eb.use_engineering_notation = True
            eb.node_number_digits = 6

            self.initfunctions(eb)
            self.initscenario(eb, 1000, "2011 Base Network")
            self.initscenario(eb, 2000, "2015 Base Network")
            self.initscenario(eb, 3000, "2030 Base Network")
            self.initscenario(eb, 4000, "2045 Base Network")
            self.initoptions(eb)

    def initfolder(self, emme_folder):
        project = _m.Modeller().desktop.project
        proj_path = os.path.dirname(project.path)

        new_folder = os.path.join(proj_path, emme_folder)
        os.mkdir(new_folder)

        # Populate Inputs folder with required base inputs
        baseInputs = os.path.join(proj_path, "BaseNetworks", "Inputs")
        shutil.copytree(baseInputs, os.path.join(new_folder, "Inputs"))
        # Create an Outputs folder for model results
        os.mkdir(os.path.join(new_folder, "Outputs"))

        return os.path.join(new_folder, "emmebank")

    @_m.logbook_trace("Creating a base scenario")
    def initscenario(self, eb, scen_id, scen_title):
        util = _m.Modeller().tool("translink.util")
        mod = _m.Modeller()
        project = mod.desktop.project
        proj_path = os.path.dirname(project.path)
        scen_trans = mod.tool("inro.emme.data.scenario.create_scenario")
        scen_trans(scenario_id = scen_id, scenario_title = scen_title, emmebank = eb, overwrite=True)

        scen = eb.scenario(scen_id)

        mod_transaction = mod.tool("inro.emme.data.network.mode.mode_transaction")
        data_path = os.path.join(proj_path, "BaseNetworks", "modes.in")
        mod_transaction(transaction_file = data_path,
                        revert_on_error = True,
                        scenario = scen)

        veh_transaction = mod.tool("inro.emme.data.network.transit.vehicle_transaction")
        data_path = os.path.join(proj_path, "BaseNetworks", "tvehicles.in")
        veh_transaction(transaction_file = data_path,
                        revert_on_error = True,
                        scenario = scen)

        data_path = os.path.join(proj_path, "BaseNetworks", "base_network_%d.txt" % scen_id)
        net_transaction = mod.tool("inro.emme.data.network.base.base_network_transaction")
        net_transaction(transaction_file = data_path,
                    revert_on_error = True,
                    scenario = scen)

        data_path = os.path.join(proj_path, "BaseNetworks", "link_shape_%d.txt" % scen_id)
        shape_trans = _m.Modeller().tool("inro.emme.data.network.base.link_shape_transaction")
        shape_trans(transaction_file = data_path,
                    revert_on_error = True,
                    scenario = scen)

        data_path = os.path.join(proj_path, "BaseNetworks", "turns_%d.txt" % scen_id)
        turns_trans = _m.Modeller().tool("inro.emme.data.network.turn.turn_transaction")
        turns_trans(transaction_file = data_path,
                    revert_on_error = True,
                    scenario = scen)

        create_attr = _m.Modeller().tool("inro.emme.data.extra_attribute.create_extra_attribute")
        create_attr("NODE", "@farezone", "Fare Zones by Node/Stop", 0, False, scen)
        create_attr("LINK", "@fareboundary", "Fare Zone Boundary for Transit (0,1)", 0, False, scen)
        create_attr("LINK", "@wcefareboundary", "Fare Zone Boundaries for WCE (13,34,45)", 0, False, scen)
        create_attr("LINK", "@lscid", "Screenline Identifier", 0, False, scen)
        create_attr("LINK", "@lscstn", "Screenline Station Identifier", 0, False, scen)
        create_attr("LINK", "@timeseg", "Travel Time Segment Identifier", 0, False, scen)
        create_attr("LINK", "@posted_speed", "Posted Speed Limit", 0, False, scen)
        create_attr("LINK", "@lanesam", "AM Number of Lanes", 0, False, scen)
        create_attr("LINK", "@lanesmd", "MD Number of Lanes", 0, False, scen)
        create_attr("LINK", "@lanespm", "PM Number of Lanes", 0, False, scen)
        create_attr("LINK", "@vdfam", "AM Volume Delay Function", 0, False, scen)
        create_attr("LINK", "@vdfmd", "MD Volume Delay Function", 0, False, scen)
        create_attr("LINK", "@vdfpm", "PM Volume Delay Function", 0, False, scen)
        create_attr("LINK", "@tollam", "AM Link Toll Value ($)", 0, False, scen)
        create_attr("LINK", "@tollmd", "MD Link Toll Value ($)", 0, False, scen)
        create_attr("LINK", "@tollpm", "PM Link Toll Value ($)", 0, False, scen)
        create_attr("TURN", "@tpfam", "AM Turn Penalty Function", 0, False, scen)
        create_attr("TURN", "@tpfmd", "MD Turn Penalty Function", 0, False, scen)
        create_attr("TURN", "@tpfpm", "PM Turn Penalty Function", 0, False, scen)
        create_attr("TRANSIT_LINE", "@hdwyam", "AM Transit Headway", 0, False, scen)
        create_attr("TRANSIT_LINE", "@hdwymd", "MD Transit Headway", 0, False, scen)
        create_attr("TRANSIT_LINE", "@hdwypm", "PM Transit Headway", 0, False, scen)

        data_path = os.path.join(proj_path, "BaseNetworks", "extra_nodes_%d.txt" % scen_id)
        node_attr = _m.Modeller().tool("inro.emme.data.network.import_attribute_values")
        node_attr(file_path = data_path,
                  field_separator = ' ',
                  column_labels = "FROM_HEADER",
                  revert_on_error = True,
                  scenario = scen,
                  merge_consecutive_separators = True)

        data_path = os.path.join(proj_path, "BaseNetworks", "extra_links_%d.txt" % scen_id)
        link_attr = _m.Modeller().tool("inro.emme.data.network.import_attribute_values")
        link_attr(file_path = data_path,
                  field_separator = ' ',
                  column_labels = "FROM_HEADER",
                  revert_on_error = True,
                  scenario = scen,
                  merge_consecutive_separators = True)

        data_path = os.path.join(proj_path, "BaseNetworks", "extra_turns_%d.txt" % scen_id)
        turn_attr = _m.Modeller().tool("inro.emme.data.network.import_attribute_values")
        turn_attr(file_path = data_path,
                  field_separator = ' ',
                  column_labels = "FROM_HEADER",
                  revert_on_error = True,
                  scenario = scen,
                  merge_consecutive_separators = True)

        data_path = os.path.join(proj_path, "BaseNetworks", "transit_lines_%d.txt" % scen_id)
        lines_trans = _m.Modeller().tool("inro.emme.data.network.transit.transit_line_transaction")
        lines_trans(transaction_file = data_path,
                    revert_on_error = True,
                    scenario = scen)

        data_path = os.path.join(proj_path, "BaseNetworks", "extra_transit_lines_%d.txt" % scen_id)
        line_attr = _m.Modeller().tool("inro.emme.data.network.import_attribute_values")
        line_attr(file_path = data_path,
                  field_separator = ' ',
                  column_labels = "FROM_HEADER",
                  revert_on_error = True,
                  scenario = scen,
                  merge_consecutive_separators = True)

        file = os.path.join(proj_path, "BaseNetworks", "taz1700_ensembles.csv")
        util.read_csv_momd(eb, file)
        self.initEnsembles(eb)

    def initEnsembles(self, eb):
        self.set_ensemble_from_mo(eb, "ga", "mo120")
        self.set_ensemble_from_mo(eb, "gb", "mo121")
        self.set_ensemble_from_mo(eb, "gc", "mo122")
        self.set_ensemble_from_mo(eb, "gd", "mo123")
        self.set_ensemble_from_mo(eb, "ge", "mo124")
        self.set_ensemble_from_mo(eb, "gf", "mo125")
        self.set_ensemble_from_mo(eb, "gg", "mo126")
        self.set_ensemble_from_mo(eb, "gh", "mo127")
        self.set_ensemble_from_mo(eb, "gi", "mo128")
        self.set_ensemble_from_mo(eb, "gj", "mo129")
        self.set_ensemble_from_mo(eb, "gk", "mo130")
        self.set_ensemble_from_mo(eb, "gl", "mo131")
        self.set_ensemble_from_mo(eb, "gm", "mo132")
        self.set_ensemble_from_mo(eb, "gn", "mo133")
        self.set_ensemble_from_mo(eb, "go", "mo134")
        self.set_ensemble_from_mo(eb, "gp", "mo135")
        self.set_ensemble_from_mo(eb, "gq", "mo136")
        self.set_ensemble_from_mo(eb, "gr", "mo137")
        self.set_ensemble_from_mo(eb, "gs", "mo138")
        self.set_ensemble_from_mo(eb, "gt", "mo139")
        self.set_ensemble_from_mo(eb, "gu", "mo140")
        self.set_ensemble_from_mo(eb, "gv", "mo141")
        self.set_ensemble_from_mo(eb, "gw", "mo142")
        self.set_ensemble_from_mo(eb, "gx", "mo143")
        self.set_ensemble_from_mo(eb, "gy", "mo144")
        self.set_ensemble_from_mo(eb, "gz", "mo145")

    def set_ensemble_from_mo(self, eb, part, orig_mat):
        mat = eb.matrix(orig_mat)

        matData = _emme.matrix.MatrixData(mat.get_data().indices, type="I")
        matData.from_numpy(mat.get_numpy_data())

        ensem = eb.partition(part)
        ensem.description = mat.description
        ensem.set_data(matData)



    def initdatabase(self, eb):
        util = _m.Modeller().tool("translink.util")

        # create vector of zones - should this be done elsewhere?
        util.initmat(eb, "mo51", "zoneindex", "Zone numbers")
        spec = util.matrix_spec("mo51", "p")
        util.compute_matrix(spec, _m.Modeller().scenario, 1)

        # get zone list into numpy
        # update with numpy helper if it's available
        df = pd.DataFrame({"TAZ1741": eb.matrix("mozoneindex").get_numpy_data()})

        conn = util.get_rtm_db(eb)
        df.to_sql(name="taz_index", con=conn, flavor="sqlite",index = False, if_exists="replace")
        conn.close()

    def initfunctions(self, eb):
        eb.create_function("fd01", "length * 60 / 40")
        eb.create_function("fd06", "40 + ((volau + volad) - 100) * 60 / (volau + volad) * ((volau +  volad) .ge. 100)")
        eb.create_function("fd22", "0.25 + length * 60 / 20 + .85 * ((volau + volad) / (400 * lanes)) ^ 4")
        eb.create_function("fd23", "0.25 + length * 60 / 30 + .85 * ((volau + volad) / (400 * lanes)) ^ 4")
        eb.create_function("fd24", "0.25 + length * 60 / 40 + .85 * ((volau + volad) / (400 * lanes)) ^ 4")
        eb.create_function("fd25", "0.25 + length * 60 / 50 + .85 * ((volau + volad) / (400 * lanes)) ^ 4")
        eb.create_function("fd26", "0.25 + length * 60 / 60 + .85 * ((volau + volad) / (400 * lanes)) ^ 4")
        eb.create_function("fd27", "0.25 + length * 60 / 70 + .85 * ((volau + volad) / (400 * lanes)) ^ 4")
        eb.create_function("fd28", "0.25 + length * 60 / 80 + .85 * ((volau + volad) / (400 * lanes)) ^ 4")
        eb.create_function("fd29", "0.25 + length * 60 / 90 + .85 * ((volau + volad) / (400 * lanes)) ^ 4")
        eb.create_function("fd30", "0.25 + length * 60 / 100 + .85 * ((volau + volad) / (600 * lanes)) ^ 4")
        eb.create_function("fd31", "0.25 + length * 60 / 110 + .85 * ((volau + volad) / (600 * lanes)) ^ 4")
        eb.create_function("fd32", "0.25 + length * 60 / 20 + .85 * ((volau + volad) / (600 * lanes)) ^ 4")
        eb.create_function("fd33", "0.25 + length * 60 / 30 + .85 * ((volau + volad) / (600 * lanes)) ^ 4")
        eb.create_function("fd34", "0.25 + length * 60 / 40 + .85 * ((volau + volad) / (600 * lanes)) ^ 4")
        eb.create_function("fd35", "0.25 + length * 60 / 50 + .85 * ((volau + volad) / (600 * lanes)) ^ 4")
        eb.create_function("fd36", "0.25 + length * 60 / 60 + .85 * ((volau + volad) / (600 * lanes)) ^ 4")
        eb.create_function("fd37", "0.25 + length * 60 / 70 + .85 * ((volau + volad) / (600 * lanes)) ^ 4")
        eb.create_function("fd38", "0.25 + length * 60 / 80 + .85 * ((volau + volad) / (600 * lanes)) ^ 4")
        eb.create_function("fd39", "0.25 + length * 60 / 90 + .85 * ((volau + volad) / (600 * lanes)) ^ 4")
        eb.create_function("fd40", "0.25 + length * 60 / 100 + .85 * ((volau + volad) / (800 * lanes)) ^ 4")
        eb.create_function("fd41", "0.25 + length * 60 / 110 + .85 * ((volau + volad) / (800 * lanes)) ^ 4")
        eb.create_function("fd42", "0.25 + length * 60 / 20 + .85 * ((volau + volad) / (800 * lanes)) ^ 4")
        eb.create_function("fd43", "0.25 + length * 60 / 30 + .85 * ((volau + volad) / (800 * lanes)) ^ 4")
        eb.create_function("fd44", "0.25 + length * 60 / 40 + .85 * ((volau + volad) / (800 * lanes)) ^ 4")
        eb.create_function("fd45", "0.25 + length * 60 / 50 + .85 * ((volau + volad) / (800 * lanes)) ^ 4")
        eb.create_function("fd46", "0.25 + length * 60 / 60 + .85 * ((volau + volad) / (800 * lanes)) ^ 4")
        eb.create_function("fd47", "0.25 + length * 60 / 70 + .85 * ((volau + volad) / (800 * lanes)) ^ 4")
        eb.create_function("fd48", "0.25 + length * 60 / 80 + .85 * ((volau + volad) / (800 * lanes)) ^ 4")
        eb.create_function("fd49", "0.25 + length * 60 / 90 + .85 * ((volau + volad) / (800 * lanes)) ^ 4")
        eb.create_function("fd50", "0.25 + length * 60 / 100 + .85 * ((volau + volad) / (1000 * lanes)) ^ 4")
        eb.create_function("fd51", "0.25 + length * 60 / 110 + .85 * ((volau + volad) / (1000 * lanes)) ^ 4")
        eb.create_function("fd52", "0.25 + length * 60 / 20 + .85 * ((volau + volad) / (1000 * lanes)) ^ 4")
        eb.create_function("fd53", "0.25 + length * 60 / 30 + .85 * ((volau + volad) / (1000 * lanes)) ^ 4")
        eb.create_function("fd54", "0.25 + length * 60 / 40 + .85 * ((volau + volad) / (1000 * lanes)) ^ 4")
        eb.create_function("fd55", "0.25 + length * 60 / 50 + .85 * ((volau + volad) / (1000 * lanes)) ^ 4")
        eb.create_function("fd56", "0.25 + length * 60 / 60 + .85 * ((volau + volad) / (1000 * lanes)) ^ 4")
        eb.create_function("fd57", "0.25 + length * 60 / 70 + .85 * ((volau + volad) / (1000 * lanes)) ^ 4")
        eb.create_function("fd58", "0.25 + length * 60 / 80 + .85 * ((volau + volad) / (1000 * lanes)) ^ 4")
        eb.create_function("fd59", "0.25 + length * 60 / 90 + .85 * ((volau + volad) / (1000 * lanes)) ^ 4")
        eb.create_function("fd60", "0.25 + length * 60 / 100 + .85 * ((volau + volad) / (1200 * lanes)) ^ 4")
        eb.create_function("fd61", "0.25 + length * 60 / 110 + .85 * ((volau + volad) / (1200 * lanes)) ^ 4")
        eb.create_function("fd62", "0.25 + length * 60 / 20 + .85 * ((volau + volad) / (1200 * lanes)) ^ 4")
        eb.create_function("fd63", "0.25 + length * 60 / 30 + .85 * ((volau + volad) / (1200 * lanes)) ^ 4")
        eb.create_function("fd64", "0.25 + length * 60 / 40 + .85 * ((volau + volad) / (1200 * lanes)) ^ 4")
        eb.create_function("fd65", "0.25 + length * 60 / 50 + .85 * ((volau + volad) / (1200 * lanes)) ^ 4")
        eb.create_function("fd66", "0.25 + length * 60 / 60 + .85 * ((volau + volad) / (1200 * lanes)) ^ 4")
        eb.create_function("fd67", "0.25 + length * 60 / 70 + .85 * ((volau + volad) / (1200 * lanes)) ^ 4")
        eb.create_function("fd68", "0.25 + length * 60 / 80 + .85 * ((volau + volad) / (1200 * lanes)) ^ 4")
        eb.create_function("fd69", "0.25 + length * 60 / 90 + .85 * ((volau + volad) / (1200 * lanes)) ^ 4")
        eb.create_function("fd70", "0.25 + length * 60 / 100 + .85 * ((volau + volad) / (1400 * lanes)) ^ 4")
        eb.create_function("fd71", "0.25 + length * 60 / 110 + .85 * ((volau + volad) / (1400 * lanes)) ^ 4")
        eb.create_function("fd72", "0.25 + length * 60 / 20 + .85 * ((volau + volad) / (1400 * lanes)) ^ 4")
        eb.create_function("fd73", "0.25 + length * 60 / 30 + .85 * ((volau + volad) / (1400 * lanes)) ^ 4")
        eb.create_function("fd74", "0.25 + length * 60 / 40 + .85 * ((volau + volad) / (1400 * lanes)) ^ 4")
        eb.create_function("fd75", "0.25 + length * 60 / 50 + .85 * ((volau + volad) / (1400 * lanes)) ^ 4")
        eb.create_function("fd76", "0.25 + length * 60 / 60 + .85 * ((volau + volad) / (1400 * lanes)) ^ 4")
        eb.create_function("fd77", "0.25 + length * 60 / 70 + .85 * ((volau + volad) / (1400 * lanes)) ^ 4")
        eb.create_function("fd78", "0.25 + length * 60 / 80 + .85 * ((volau + volad) / (1400 * lanes)) ^ 4")
        eb.create_function("fd79", "0.25 + length * 60 / 90 + .85 * ((volau + volad) / (1400 * lanes)) ^ 4")
        eb.create_function("fd80", "length * 60 / (100 * 1.1) * (1 + .6 * .43 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 5.25)")
        eb.create_function("fd81", "length * 60 / (110 * 1.1) * (1 + .6 * .43 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 5.25)")
        eb.create_function("fd82", "length * 60 / 20 * (1 + .6 * .85 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 5)")
        eb.create_function("fd83", "length * 60 / 30 * (1 + .6 * .85 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 5)")
        eb.create_function("fd84", "length * 60 / 40 * (1 + .6 * .85 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 5)")
        eb.create_function("fd85", "length * 60 / 50 * (1 + .6 * .85 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 5)")
        eb.create_function("fd86", "length * 60 / 60 * (1 + .6 * .85 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 5)")
        eb.create_function("fd87", "length * 60 / 70 * (1 + .6 * .85 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 5)")
        eb.create_function("fd88", "length * 60 / (80 * 1.1) * (1 + .6 * .43 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 5.25)")
        eb.create_function("fd89", "length * 60 / (90 * 1.1) * (1 + .6 * .43 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 5.25)")

        # Merge Functions
        eb.create_function("fd03", "length * 60 / 50 + 0.85 * ((volau + volad) / ( 600*lanes))^5")
        eb.create_function("fd04", "length * 60 / 60 + 0.85 * ((volau + volad) / ( 600*lanes))^5")
        eb.create_function("fd05", "length * 60 / 70 + 0.85 * ((volau + volad) / ( 600*lanes))^5")
        eb.create_function("fd92", "length * 60 / 50 + 0.85 * ((volau + volad) / ( 800*lanes))^5")
        eb.create_function("fd93", "length * 60 / 60 + 0.85 * ((volau + volad) / ( 800*lanes))^5")
        eb.create_function("fd94", "length * 60 / 70 + 0.85 * ((volau + volad) / ( 800*lanes))^5")
        eb.create_function("fd07", "length * 60 / 50 + 0.85 * ((volau + volad) / (1000*lanes))^5")
        eb.create_function("fd08", "length * 60 / 60 + 0.85 * ((volau + volad) / (1000*lanes))^5")
        eb.create_function("fd09", "length * 60 / 70 + 0.85 * ((volau + volad) / (1000*lanes))^5")
        eb.create_function("fd10", "length * 60 / 80 + 0.85 * ((volau + volad) / (1000*lanes))^5")
        eb.create_function("fd11", "length * 60 / 90 + 0.85 * ((volau + volad) / (1000*lanes))^5")
        eb.create_function("fd02", "length * 60 / 100+ 0.85 * ((volau + volad) / (1000*lanes))^5")
        eb.create_function("fd17", "length * 60 / 50 + 0.85 * ((volau + volad) / (1200*lanes))^5")
        eb.create_function("fd18", "length * 60 / 60 + 0.85 * ((volau + volad) / (1200*lanes))^5")
        eb.create_function("fd19", "length * 60 / 70 + 0.85 * ((volau + volad) / (1200*lanes))^5")
        eb.create_function("fd20", "length * 60 / 80 + 0.85 * ((volau + volad) / (1200*lanes))^5")
        eb.create_function("fd21", "length * 60 / 90 + 0.85 * ((volau + volad) / (1200*lanes))^5")
        eb.create_function("fd12", "length * 60 / 100+ 0.85 * ((volau + volad) / (1200*lanes))^5")
        eb.create_function("fd95", "length * 60 / 50 + 0.85 * ((volau + volad) / (1400*lanes))^5")
        eb.create_function("fd96", "length * 60 / 60 + 0.85 * ((volau + volad) / (1400*lanes))^5")
        eb.create_function("fd97", "length * 60 / 70 + 0.85 * ((volau + volad) / (1400*lanes))^5")
        eb.create_function("fd98", "length * 60 / 80 + 0.85 * ((volau + volad) / (1400*lanes))^5")
        eb.create_function("fd99", "length * 60 / 90 + 0.85 * ((volau + volad) / (1400*lanes))^5")
        eb.create_function("fd90", "length * 60 / 100+ 0.85 * ((volau + volad) / (1400*lanes))^5")

        # Update FT functions to include dwell time (us1) based on boardings and alightings
        eb.create_function("ft01", "timau + us1")
        eb.create_function("ft02", "timau + us1")
        eb.create_function("ft03", "timau + us1")
        eb.create_function("ft04", "timau + us1")
        eb.create_function("ft05", "timau + us1")
        eb.create_function("ft10", "0.01")
        eb.create_function("ft20", "timau + us1")
        eb.create_function("fp01", "(.1 + pvolau / 100) ^ 4")
        eb.create_function("fp02", "(.1 + pvolau / 200) ^ 4")
        eb.create_function("fp03", "(.1 + pvolau / 300) ^ 4")
        eb.create_function("fp04", "(.1 + pvolau / 400) ^ 4")
        eb.create_function("fp05", "(.1 + pvolau / 500) ^ 4")
        eb.create_function("fp06", "(.1 + pvolau / 600) ^ 4")
        eb.create_function("fp07", "(.1 + pvolau / 700) ^ 4")
        eb.create_function("fp08", "(.1 + pvolau / 800) ^ 4")
        eb.create_function("fp09", "(.1 + pvolau / 900) ^ 4")
        eb.create_function("fp10", "(.1 + pvolau / 1000) ^ 4")
        eb.create_function("fp12", "(.1 + pvolau / 1200) ^ 4")
        eb.create_function("fp16", "(.1 + pvolau / 1600) ^ 4")
        eb.create_function("fp24", "(.1 + pvolau / 2400) ^ 4")
        eb.create_function("fp32", "(.1 + pvolau / 3200) ^ 4")

    def initoptions(self, eb):
        util = _m.Modeller().tool("translink.util")
        # model business
        util.initmat(eb, "ms2", "AmScen", "AMScenario", 21000)
        util.initmat(eb, "ms3", "MdScen", "MDScenario", 22000)
        util.initmat(eb, "ms4", "PmScen", "PMScenario", 23000)
