##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.initeb
##--Purpose: initialize a new emmebank from source text files
##---------------------------------------------------------------------
import inro.modeller as _m
import inro.emme as _emme
import os
import shutil

class InitEmmebank(_m.Tool()):
    emme_title = _m.Attribute(_m.InstanceType)
    emme_folder = _m.Attribute(_m.InstanceType)
    horizon_year = _m.Attribute(_m.InstanceType)
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
                        
        pb.add_text_box(tool_attribute_name="horizon_year",
                        size=4,
                        title="Enter the year to initialize matrices for")

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
        self.initconstants(_m.Modeller().emmebank)
        self.initseeds(_m.Modeller().emmebank)

    def initbank(self, path, title):
        dim = {"scalar_matrices": 9999,
               "origin_matrices": 2000,
               "destination_matrices": 2000,
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
        mod = _m.Modeller()
        project = mod.desktop.project
        proj_path = os.path.dirname(project.path)
        scen_trans = mod.tool("inro.emme.data.scenario.create_scenario")
        scen_trans(scenario_id = scen_id, scenario_title = scen_title, emmebank = eb)

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
        create_attr("LINK", "@lanesam", "AM Number of Lanes", 0, False, scen)
        create_attr("LINK", "@lanesmd", "MD Number of Lanes", 0, False, scen)
        create_attr("LINK", "@lanespm", "PM Number of Lanes", 0, False, scen)
        create_attr("LINK", "@vdfam", "AM Volume Delay Function", 0, False, scen)
        create_attr("LINK", "@vdfmd", "MD Volume Delay Function", 0, False, scen)
        create_attr("LINK", "@vdfpm", "PM Volume Delay Function", 0, False, scen)
        create_attr("TURN", "@tpfam", "AM Turn Penalty Function", 0, False, scen)
        create_attr("TURN", "@tpfmd", "MD Turn Penalty Function", 0, False, scen)
        create_attr("TURN", "@tpfpm", "PM Turn Penalty Function", 0, False, scen)
        create_attr("TRANSIT_LINE", "@hdwyam", "AM Transit Headway", 0, False, scen)
        create_attr("TRANSIT_LINE", "@hdwymd", "MD Transit Headway", 0, False, scen)
        create_attr("TRANSIT_LINE", "@hdwypm", "PM Transit Headway", 0, False, scen)

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

        ensem_trans = _m.Modeller().tool("inro.emme.data.zone_partition.partition_transaction")
        data_path = os.path.join(proj_path, "BaseNetworks", "all_ensem_tz1741.in")
        ensem_trans(transaction_file = data_path,
                    throw_on_error = True,
                    scenario = scen)

    def initconstants(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        util.initmat(eb, "ms17", "adcost", "Additional cost", 0)
        util.initmat(eb, "ms18", "MCOpCs", "Mode Choice operating cost per km", 0.18)
        util.initmat(eb, "ms19", "TlSn1", "Mode Choice Toll Sensitivity", 1)
        util.initmat(eb, "ms20", "StdOcc", "standard auto occupancy", 2.4)
        util.initmat(eb, "ms37", "PRwvot", "PR Work VOT (min/$)", 3.33)
        util.initmat(eb, "ms38", "PRnvot", "PR Nonwork VOT (min/$)", 8.57)
        util.initmat(eb, "ms50", "WkPk", "Wk peak period for blended skims", 0.74)
        util.initmat(eb, "ms51", "UvPk", "Uv peak period for blended skims", 0.59)
        util.initmat(eb, "ms52", "ScPk", "Sc peak period for blended skims", 1)
        util.initmat(eb, "ms53", "ShPk", "Sh peak period for blended skims", 0.39)
        util.initmat(eb, "ms54", "PBPk", "PB peak period for blended skims", 0.4)
        util.initmat(eb, "ms55", "SoPk", "So peak period for blended skims", 0.37)
        util.initmat(eb, "ms56", "EcPk", "Ec peak period for blended skims", 0.69)
        util.initmat(eb, "ms57", "NwPk", "Nw peak period for blended skims", 0.53)
        util.initmat(eb, "ms58", "NoPk", "No peak period for blended skims", 0.47)
        util.initmat(eb, "ms60", "WkOcA", "Wk AM occupancy rate", 3.4555)
        util.initmat(eb, "ms61", "UvOcA", "Uv AM occupancy rate", 3.3107)
        util.initmat(eb, "ms62", "ScOcA", "Sc AM occupancy rate", 2.9718)
        util.initmat(eb, "ms63", "ShOcA", "Sh AM occupancy rate", 2.3631)
        util.initmat(eb, "ms64", "PBOcA", "PB AM occupancy rate", 2.3168)
        util.initmat(eb, "ms65", "SoOcA", "So AM occupancy rate", 2.6185)
        util.initmat(eb, "ms66", "EcOcA", "Ec AM occupancy rate", 2.5902)
        util.initmat(eb, "ms67", "NwOcA", "Nw AM occupancy rate", 2.3179)
        util.initmat(eb, "ms68", "NoOcA", "No AM occupancy rate", 2.5849)
        util.initmat(eb, "ms90", "WkOcM", "Wk MD occupancy rate", 3.15)
        util.initmat(eb, "ms91", "UvOcM", "Uv MD occupancy rate", 3.64)
        util.initmat(eb, "ms92", "ScOcM", "Sc MD occupancy rate", 2.47)
        util.initmat(eb, "ms93", "ShOcM", "Sh MD occupancy rate", 2.33)
        util.initmat(eb, "ms94", "PBOcM", "PB MD occupancy rate", 2.17)
        util.initmat(eb, "ms95", "SoOcM", "So MD occupancy rate", 2.34)
        util.initmat(eb, "ms96", "EcOcM", "Ec MD occupancy rate", 2.29)
        util.initmat(eb, "ms97", "NwOcM", "Nw MD occupancy rate", 2.48)
        util.initmat(eb, "ms98", "NoOcM", "No MD occupancy rate", 2.42)
        util.initmat(eb, "ms101", "TDOpC2", "Trip Dist Add. Operating Cost", 0)
        util.initmat(eb, "ms102", "TDOpC1", "Trip Dist Operating Cost", 0.127)
        util.initmat(eb, "ms103", "TlSn2", "Trip Dist Toll Sensitivity", 1.02)
        util.initmat(eb, "ms104", "WkLVOT", "WkL value of time in min/$", 6)
        util.initmat(eb, "ms105", "WkMVOT", "WkM value of time in min/$", 3)
        util.initmat(eb, "ms106", "WkHVOT", "WkH value of time in min/$", 3)
        util.initmat(eb, "ms107", "UvVOT", "Uv value of time in min/$", 12)
        util.initmat(eb, "ms108", "ScVOT", "Sc value of time in min/$", 12)
        util.initmat(eb, "ms109", "ShVOT", "Sh value of time in min/$", 7.1)
        util.initmat(eb, "ms110", "PBVOT", "PB value of time in min/$", 7.1)
        util.initmat(eb, "ms111", "SoVOT", "So value of time in min/$", 7.1)
        util.initmat(eb, "ms112", "EcVOT", "Ec value of time in min/$", 7.1)
        util.initmat(eb, "ms113", "NwVOT", "Nw value of time in min/$", 3)
        util.initmat(eb, "ms114", "NoVOT", "No value of time in min/$", 6)

    def initseeds(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        mod = _m.Modeller()
        project = mod.desktop.project
        proj_path = os.path.dirname(project.path)

        mat_transaction = mod.tool("inro.emme.data.matrix.matrix_transaction")

        # Batch in zone area in metres square
        util.delmat(eb, "mo17")
        data_path = os.path.join(proj_path, "BaseNetworks", "mo_taz_area.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

        # Batch in starter auto demand used for generating starter skims, demand is aggregated into 4 classes, SOV, HOV, Light Tr, Heavy Tr
        util.delmat(eb, "mf893")
        util.delmat(eb, "mf894")
        data_path = os.path.join(proj_path, "BaseNetworks", "AM_Starter_Demand.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

        util.delmat(eb, "mf895")
        util.delmat(eb, "mf896")
        data_path = os.path.join(proj_path, "BaseNetworks", "MD_Starter_Demand.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

        util.delmat(eb, "mf897")
        util.delmat(eb, "mf898")
        data_path = os.path.join(proj_path, "BaseNetworks", "PM_Starter_Demand.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

        # Batch in truck demand matrices
        util.delmat(eb, "mf980")
        util.delmat(eb, "mf981")
        data_path = os.path.join(proj_path, "BaseNetworks", "Matrices", self.horizon_year, "AM_Truck_Demand.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

        util.delmat(eb, "mf982")
        util.delmat(eb, "mf983")
        data_path = os.path.join(proj_path, "BaseNetworks", "Matrices", self.horizon_year, "MD_Truck_Demand.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

		# TODO PM truck demand is currently transpose AM truck demand multiplied by a factor
		# Factor was created by Parsons
		# Should be updated with actual truck demand
        util.delmat(eb, "mf990")
        util.delmat(eb, "mf991")
        data_path = os.path.join(proj_path, "BaseNetworks", "Matrices", self.horizon_year, "PM_Truck_Demand.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)


        # Batch in external demand matrices
        util.delmat(eb, "mf978")
        util.delmat(eb, "mf979")
        data_path = os.path.join(proj_path, "BaseNetworks", "Matrices", self.horizon_year, "AM_External_Demand.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

        util.delmat(eb, "mf984")
        util.delmat(eb, "mf985")
        data_path = os.path.join(proj_path, "BaseNetworks", "Matrices", self.horizon_year, "MD_External_Demand.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

		# TODO update extnernal demand
		# Note PM external demand is AM transposed multiplied by a factor
        util.delmat(eb, "mf992")
        util.delmat(eb, "mf993")
        data_path = os.path.join(proj_path, "BaseNetworks", "Matrices", self.horizon_year, "PM_External_Demand.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

        util.delmat(eb, "md999")
        data_path = os.path.join(proj_path, "BaseNetworks", "md_Grade_School_Adj.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

        util.delmat(eb, "mf160")
        data_path = os.path.join(proj_path, "BaseNetworks", "mf_Bus_Fare_Matrix.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

        util.delmat(eb, "mf928")
        util.delmat(eb, "mf929")
        data_path = os.path.join(proj_path, "BaseNetworks", "mf_Pk_Prd_Bus_Adj.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

        util.delmat(eb, "mf975")
        util.delmat(eb, "mf976")
        data_path = os.path.join(proj_path, "BaseNetworks", "mf_Pk_Prd_Rail_Adj.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

        util.delmat(eb, "mf161")
        data_path = os.path.join(proj_path, "BaseNetworks", "mf_Rail_Fare_Matrix.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

        util.delmat(eb, "mf169")
        util.delmat(eb, "mf170")
        util.delmat(eb, "mf171")
        util.delmat(eb, "mf172")
        util.delmat(eb, "mf173")
        util.delmat(eb, "mf174")
        util.delmat(eb, "mf175")
        util.delmat(eb, "mf176")
        util.delmat(eb, "mf177")
        util.delmat(eb, "mf178")
        util.delmat(eb, "mf179")
        data_path = os.path.join(proj_path, "BaseNetworks", "mf_TripDist_Rij.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

        util.delmat(eb, "mo58")
        data_path = os.path.join(proj_path, "BaseNetworks", "mo_No_Wrk_Adj.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

    def initfunctions(self, eb):
        eb.create_function("fd01", "length * 60 / 40")
        eb.create_function("fd02", "((volau + volad) / lanes - 1900) * .017 * ((volau + volad) / lanes .ge. 1900) + .01")
        eb.create_function("fd03", "ul3")
        eb.create_function("fd04", "((volau + volad) / lanes - 1600) * .0065 * ((volau + volad) / lanes .ge. 1600) + .25")
        eb.create_function("fd05", "length * 60 / 4 * (1 + .6 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 4) + (volau + volad - 100 * lanes) * (((volau + volad) .ge. 100 * lanes) * .6) / lanes")
        eb.create_function("fd06", "40 + ((volau + volad) - 100) * 60 / (volau + volad) * ((volau +  volad) .ge. 100)")
        eb.create_function("fd22", "length * 60 / 20 + .85 * ((volau + volad) / (400 * lanes)) ^ 5")
        eb.create_function("fd23", "length * 60 / 30 + .85 * ((volau + volad) / (400 * lanes)) ^ 5")
        eb.create_function("fd24", "length * 60 / 40 + .85 * ((volau + volad) / (400 * lanes)) ^ 5")
        eb.create_function("fd25", "length * 60 / 50 + .85 * ((volau + volad) / (400 * lanes)) ^ 5")
        eb.create_function("fd26", "length * 60 / 60 + .85 * ((volau + volad) / (400 * lanes)) ^ 5")
        eb.create_function("fd27", "length * 60 / 70 + .85 * ((volau + volad) / (400 * lanes)) ^ 5")
        eb.create_function("fd28", "length * 60 / 80 + .85 * ((volau + volad) / (400 * lanes)) ^ 5")
        eb.create_function("fd29", "length * 60 / 90 + .85 * ((volau + volad) / (400 * lanes)) ^ 5")
        eb.create_function("fd30", "length * 60 / 100 + .85 * ((volau + volad) / (600 * lanes)) ^ 5")
        eb.create_function("fd31", "length * 60 / 110 + .85 * ((volau + volad) / (600 * lanes)) ^ 5")
        eb.create_function("fd32", "length * 60 / 20 + .85 * ((volau + volad) / (600 * lanes)) ^ 5")
        eb.create_function("fd33", "length * 60 / 30 + .85 * ((volau + volad) / (600 * lanes)) ^ 5")
        eb.create_function("fd34", "length * 60 / 40 + .85 * ((volau + volad) / (600 * lanes)) ^ 5")
        eb.create_function("fd35", "length * 60 / 50 + .85 * ((volau + volad) / (600 * lanes)) ^ 5")
        eb.create_function("fd36", "length * 60 / 60 + .85 * ((volau + volad) / (600 * lanes)) ^ 5")
        eb.create_function("fd37", "length * 60 / 70 + .85 * ((volau + volad) / (600 * lanes)) ^ 5")
        eb.create_function("fd38", "length * 60 / 80 + .85 * ((volau + volad) / (600 * lanes)) ^ 5")
        eb.create_function("fd39", "length * 60 / 90 + .85 * ((volau + volad) / (600 * lanes)) ^ 5")
        eb.create_function("fd40", "length * 60 / 100 + .85 * ((volau + volad) / (800 * lanes)) ^ 5")
        eb.create_function("fd41", "length * 60 / 110 + .85 * ((volau + volad) / (800 * lanes)) ^ 5")
        eb.create_function("fd42", "length * 60 / 20 + .85 * ((volau + volad) / (800 * lanes)) ^ 5")
        eb.create_function("fd43", "length * 60 / 30 + .85 * ((volau + volad) / (800 * lanes)) ^ 5")
        eb.create_function("fd44", "length * 60 / 40 + .85 * ((volau + volad) / (800 * lanes)) ^ 5")
        eb.create_function("fd45", "length * 60 / 50 + .85 * ((volau + volad) / (800 * lanes)) ^ 5")
        eb.create_function("fd46", "length * 60 / 60 + .85 * ((volau + volad) / (800 * lanes)) ^ 5")
        eb.create_function("fd47", "length * 60 / 70 + .85 * ((volau + volad) / (800 * lanes)) ^ 5")
        eb.create_function("fd48", "length * 60 / 80 + .85 * ((volau + volad) / (800 * lanes)) ^ 5")
        eb.create_function("fd49", "length * 60 / 90 + .85 * ((volau + volad) / (800 * lanes)) ^ 5")
        eb.create_function("fd50", "length * 60 / 100 + .85 * ((volau + volad) / (1000 * lanes)) ^ 5")
        eb.create_function("fd51", "length * 60 / 110 + .85 * ((volau + volad) / (1000 * lanes)) ^ 5")
        eb.create_function("fd52", "length * 60 / 20 + .85 * ((volau + volad) / (1000 * lanes)) ^ 5")
        eb.create_function("fd53", "length * 60 / 30 + .85 * ((volau + volad) / (1000 * lanes)) ^ 5")
        eb.create_function("fd54", "length * 60 / 40 + .85 * ((volau + volad) / (1000 * lanes)) ^ 5")
        eb.create_function("fd55", "length * 60 / 50 + .85 * ((volau + volad) / (1000 * lanes)) ^ 5")
        eb.create_function("fd56", "length * 60 / 60 + .85 * ((volau + volad) / (1000 * lanes)) ^ 5")
        eb.create_function("fd57", "length * 60 / 70 + .85 * ((volau + volad) / (1000 * lanes)) ^ 5")
        eb.create_function("fd58", "length * 60 / 80 + .85 * ((volau + volad) / (1000 * lanes)) ^ 5")
        eb.create_function("fd59", "length * 60 / 90 + .85 * ((volau + volad) / (1000 * lanes)) ^ 5")
        eb.create_function("fd60", "length * 60 / 100 + .85 * ((volau + volad) / (1200 * lanes)) ^ 5")
        eb.create_function("fd61", "length * 60 / 110 + .85 * ((volau + volad) / (1200 * lanes)) ^ 5")
        eb.create_function("fd62", "length * 60 / 20 + .85 * ((volau + volad) / (1200 * lanes)) ^ 5")
        eb.create_function("fd63", "length * 60 / 30 + .85 * ((volau + volad) / (1200 * lanes)) ^ 5")
        eb.create_function("fd64", "length * 60 / 40 + .85 * ((volau + volad) / (1200 * lanes)) ^ 5")
        eb.create_function("fd65", "length * 60 / 50 + .85 * ((volau + volad) / (1200 * lanes)) ^ 5")
        eb.create_function("fd66", "length * 60 / 60 + .85 * ((volau + volad) / (1200 * lanes)) ^ 5")
        eb.create_function("fd67", "length * 60 / 70 + .85 * ((volau + volad) / (1200 * lanes)) ^ 5")
        eb.create_function("fd68", "length * 60 / 80 + .85 * ((volau + volad) / (1200 * lanes)) ^ 5")
        eb.create_function("fd69", "length * 60 / 90 + .85 * ((volau + volad) / (1200 * lanes)) ^ 5")
        eb.create_function("fd70", "length * 60 / 100 + .85 * ((volau + volad) / (1400 * lanes)) ^ 5")
        eb.create_function("fd71", "length * 60 / 110 + .85 * ((volau + volad) / (1400 * lanes)) ^ 5")
        eb.create_function("fd72", "length * 60 / 20 + .85 * ((volau + volad) / (1400 * lanes)) ^ 5")
        eb.create_function("fd73", "length * 60 / 30 + .85 * ((volau + volad) / (1400 * lanes)) ^ 5")
        eb.create_function("fd74", "length * 60 / 40 + .85 * ((volau + volad) / (1400 * lanes)) ^ 5")
        eb.create_function("fd75", "length * 60 / 50 + .85 * ((volau + volad) / (1400 * lanes)) ^ 5")
        eb.create_function("fd76", "length * 60 / 60 + .85 * ((volau + volad) / (1400 * lanes)) ^ 5")
        eb.create_function("fd77", "length * 60 / 70 + .85 * ((volau + volad) / (1400 * lanes)) ^ 5")
        eb.create_function("fd78", "length * 60 / 80 + .85 * ((volau + volad) / (1400 * lanes)) ^ 5")
        eb.create_function("fd79", "length * 60 / 90 + .85 * ((volau + volad) / (1400 * lanes)) ^ 5")
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
        eb.create_function("fd99", "length")
        eb.create_function("ft01", "timau + 3 * length")
        eb.create_function("ft02", "timau + 1.8 * length")
        eb.create_function("ft03", "timau + 1 * length")
        eb.create_function("ft04", "timau + .5 * length")
        eb.create_function("ft05", "timau * 1.5")
        eb.create_function("ft06", "length * 1")
        eb.create_function("ft07", "(60 * length / speed)")
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
