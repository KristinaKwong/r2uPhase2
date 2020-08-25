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
    scen_number = _m.Attribute(int)
    scen_name = _m.Attribute(_m.InstanceType)

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

        #pb.add_text_box(tool_attribute_name="scen_number",
        #                size=10,
        #                title="Enter the Scenario Number to import into the new emmebank")
        #
        #pb.add_text_box(tool_attribute_name="scen_name",
        #                size=60,
        #                title="Enter the Scenario Name for the new scenario")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        try:
            self.__call__(self.emme_folder, self.emme_title)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Initializing a new emmebank")
    def __call__(self, folder_name, title_name, master_scen = 0, master_scen_name = ""):
        new_path = self.initfolder(folder_name)

        self.initbank(new_path, title_name, master_scen, master_scen_name)
        _m.Modeller().desktop.data_explorer().add_database(new_path).open()
        self.initdatabase(_m.Modeller().emmebank)


    def initbank(self, path, title, master_scen, master_scen_name):
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
            if master_scen == 0:
                self.initscenario(eb, 1000, "2011 Base Network")
                self.initscenario(eb, 1700, "2017 Base Network")
                self.initscenario(eb, 3500, "2035 Base Network")
                self.initscenario(eb, 5000, "2050 Base Network")
            else:
                self.initscenario(eb, master_scen, master_scen_name) # Added one scenario init option

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
        create_attr("TRANSIT_LINE", "@brdline", "Line Boarding Penalty", 1, False, scen)
        create_attr("LINK", "@capacityam", "AM Roadway Lane Capacity", 0, False, scen)
        create_attr("LINK", "@capacitymd", "MD Roadway Lane Capacity", 0, False, scen)
        create_attr("LINK", "@capacitypm", "PM Roadway Lane Capacity", 0, False, scen)
        create_attr("LINK", "@signal_delay", "Signal Delay", 0.25, False, scen)

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
        util = _m.Modeller().tool("translink.util")
        
        # Read Ensemble MOs .. the function is defined in Utilities script now
        util.set_ensemble_from_mo(eb, "ga", "mo120")
        util.set_ensemble_from_mo(eb, "gb", "mo121")
        util.set_ensemble_from_mo(eb, "gc", "mo122")
        util.set_ensemble_from_mo(eb, "gd", "mo123")
        util.set_ensemble_from_mo(eb, "ge", "mo124")
        util.set_ensemble_from_mo(eb, "gf", "mo125")
        util.set_ensemble_from_mo(eb, "gg", "mo126")
        util.set_ensemble_from_mo(eb, "gh", "mo127")
        util.set_ensemble_from_mo(eb, "gi", "mo128")
        util.set_ensemble_from_mo(eb, "gj", "mo129")
        util.set_ensemble_from_mo(eb, "gk", "mo130")
        util.set_ensemble_from_mo(eb, "gl", "mo131")
        util.set_ensemble_from_mo(eb, "gm", "mo132")
        util.set_ensemble_from_mo(eb, "gn", "mo133")
        util.set_ensemble_from_mo(eb, "go", "mo134")
        util.set_ensemble_from_mo(eb, "gp", "mo135")
        util.set_ensemble_from_mo(eb, "gq", "mo136")
        util.set_ensemble_from_mo(eb, "gr", "mo137")
        util.set_ensemble_from_mo(eb, "gs", "mo138")
        util.set_ensemble_from_mo(eb, "gt", "mo139")
        util.set_ensemble_from_mo(eb, "gu", "mo140")
        util.set_ensemble_from_mo(eb, "gv", "mo141")
        util.set_ensemble_from_mo(eb, "gw", "mo142")
        util.set_ensemble_from_mo(eb, "gx", "mo143")
        util.set_ensemble_from_mo(eb, "gy", "mo144")
        util.set_ensemble_from_mo(eb, "gz", "mo145")
        
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
        df.to_sql(name="taz_index", con=conn, index = False, if_exists="replace")
        conn.close()

    def initfunctions(self, eb):
        extra_parameters = _m.Modeller().tool("inro.emme.traffic_assignment.set_extra_function_parameters")
        extra_parameters(emmebank=eb, el1="@posted_speed")
        extra_parameters(emmebank=eb, el2="@capacity")
        extra_parameters(emmebank=eb, el3="@signal_delay")
        
        # Simplified Volume Delay Functions
        eb.create_function("fd11", "length * 60 / 40")
        eb.create_function("fd12", "40 + ((volau + volad) - 100) * 60 / (volau + volad) * ((volau +  volad) .ge. 100)")
        eb.create_function("fd13", "length * 60 / el1 + 0.85 * ((volau + volad) / (el2 * lanes))^5")
        eb.create_function("fd14", "el3 + length * 60 / el1 + .85 * ((volau + volad) / (el2 * lanes)) ^ 4")
        eb.create_function("fd15", "length * 60 / el1 * (1 + .6 * .85 * ((volau + volad) / (el2 * lanes ^ 1.05)) ^ 5)")
        eb.create_function("fd16", "length * 60 / (el1 * 1.1) * (1 + .6 * .43 * ((volau + volad) / (el2 * lanes ^ 1.05)) ^ 5.25)")

        eb.create_function("fd23", "length * 60 / el1 + 6 * 0.85 * ((volau + volad) / (el2 * lanes))^5")
        eb.create_function("fd24", "el3 + length * 60 / el1 + 5 * .85 * ((volau + volad) / (el2 * lanes)) ^ 4")
        eb.create_function("fd25", "length * 60 / el1 * (1 + 6 * .6 * .85 * ((volau + volad) / (el2 * lanes ^ 1.05)) ^ 5)")
        eb.create_function("fd26", "length * 60 / (el1 * 1.1) * (1 + 6.25 * .6 * .43 * ((volau + volad) / (el2 * lanes ^ 1.05)) ^ 5.25)")




        # Update FT functions to include dwell time (us1) based on boardings and alightings
        eb.create_function("ft01", "us1 + 1.1 * us2")
        eb.create_function("ft02", "us3") # place holder for transit specific lanes
        eb.create_function("ft10", "0.01")
        
        
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
