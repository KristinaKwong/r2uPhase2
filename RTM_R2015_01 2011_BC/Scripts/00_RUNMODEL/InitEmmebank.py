import inro.modeller as _m
import inro.emme as _emme
import os

class InitEmmebank(_m.Tool()):
    emme_title = _m.Attribute(_m.InstanceType)
    emme_folder = _m.Attribute(_m.InstanceType)
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Translink Utility Toolbox"
        pb.description = "Initialize a new Emmebank"
        pb.branding_text = "TransLink"

        pb.add_text_box(tool_attribute_name='emme_folder',
                        size=30,
                        title='Enter the Folder Name for the new emmebank')

        pb.add_text_box(tool_attribute_name='emme_title',
                        size=30,
                        title='Enter the Title for the new emmebank')

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.__call__()

    def __call__(self):
        new_path = initfolder(self.emme_folder)

        eb = initbank(new_path, self.emme_title)
        _m.Modeller().desktop.data_explorer().add_database(new_path)

    def cleanup(self):
        mod = _m.Modeller()
        explorer = mod.desktop.data_explorer()
        explorer.remove_database(explorer.databases()[1])

    def transform_coord(self):
        eb = _m.Modeller().emmebank
        coord_trans = _m.Modeller().tool("inro.emme.data.network.base.adjust_network_coordinates")
        for scen in [1000, 1100, 1200, 2000, 2100, 2200, 3000, 3100, 3200]:
            coord_trans(scenario = eb.scenario(scen),
                        transformation_matrix = "0,0,0.001,0.001,0,0,0,0")

    def fix_shapes(self):
        eb = _m.Modeller().emmebank
        shape_trans = _m.Modeller().tool("inro.emme.data.network.base.link_shape_transaction")

        source_path = "C:/proj/netbuild/EMME_NET_FINAL20160218/mgrant_final/"
        for scen in [1000, 1100, 1200]:
            shape_trans(scenario = eb.scenario(scen),
                        transaction_file = source_path + "2011_shapefixes.txt",
                        revert_on_error = True)
        for scen in [2000, 2100, 2200, 3000, 3100, 3200]:
            shape_trans(scenario = eb.scenario(scen),
                        transaction_file = source_path + "2015_2030_shapefixes.txt",
                        revert_on_error = True)


def initbank(path, title):
    dim = {'scalar_matrices': 9999,
           'origin_matrices': 2000,
           'destination_matrices': 2000,
           'full_matrices': 9999,
           'scenarios': 10,
           'functions': 99,
           'operators': 5000,
           'centroids': 1750,
           'regular_nodes': 9000,
           'links': 22000,
           'turn_entries': 15000,
           'extra_attribute_values': 2000000,
           'transit_lines': 600,
           'transit_segments': 36000,
           'transit_vehicles': 600}

    with _emme.database.emmebank.create(path, dim) as eb:
        eb.title = title
        eb.coord_unit_length = 1.0
        eb.unit_of_length = 'km'
        eb.unit_of_cost = '$'
        eb.unit_of_energy = 'mj'
        eb.use_engineering_notation = True
        eb.node_number_digits = 6

        initfunctions(eb)

        source_path = "C:/proj/netbuild/EMME_NET_FINAL20160218/mgrant_final/"
        initscenario(eb, 1000, "2011 AM Base Import", source_path + "2011AM_map.in", source_path + "2011_netfixes.txt")
        initscenario(eb, 1100, "2011 MD Base Import", source_path + "2011MD_map.in", source_path + "2011_netfixes.txt")
        initscenario(eb, 1200, "2011 PM Base Import", source_path + "2011PM_map.in", source_path + "2011_netfixes.txt")
        initscenario(eb, 2000, "2015 AM Base Import", source_path + "2015AM.in", source_path + "2015_2030_netfixes.txt")
        initscenario(eb, 2100, "2015 MD Base Import", source_path + "2015MD.in", source_path + "2015_2030_netfixes.txt")
        initscenario(eb, 2200, "2015 PM Base Import", source_path + "2015PM.in", source_path + "2015_2030_netfixes.txt")
        initscenario(eb, 3000, "2030 AM Base Import", source_path + "2030AM.in", source_path + "2015_2030_netfixes.txt")
        initscenario(eb, 3100, "2030 MD Base Import", source_path + "2030MD.in", source_path + "2015_2030_netfixes.txt")
        initscenario(eb, 3200, "2030 PM Base Import", source_path + "2030PM.in", source_path + "2015_2030_netfixes.txt")

def initfolder(emme_folder):
    project = _m.Modeller().desktop.project
    proj_path = os.path.dirname(project.path)

    new_folder = os.path.join(proj_path, emme_folder)
    os.mkdir(new_folder)

    return os.path.join(new_folder, 'emmebank')

def initscenario(eb, scen_id, scen_title, networkfile, fixesfile):
    mod = _m.Modeller()
    project = mod.desktop.project
    proj_path = os.path.dirname(project.path)
    scen_trans = mod.tool("inro.emme.data.scenario.create_scenario")
    scen_trans(scenario_id = scen_id, scenario_title = scen_title, emmebank = eb)

    scen = eb.scenario(scen_id)

    mod_transaction = mod.tool("inro.emme.data.network.mode.mode_transaction")
    data_path = os.path.join(proj_path, 'Inputs', 'modes.in')
    mod_transaction(transaction_file = data_path,
                    revert_on_error = True,
                    scenario = scen)

    veh_transaction = mod.tool("inro.emme.data.network.transit.vehicle_transaction")
    data_path = os.path.join(proj_path, 'Inputs', 'tvehicles.in')
    veh_transaction(transaction_file = data_path,
                    revert_on_error = True,
                    scenario = scen)

    net_transaction = mod.tool("inro.emme.data.network.base.base_network_transaction")
    net_transaction(transaction_file = networkfile,
                    revert_on_error = True,
                    scenario = scen)
    net_transaction(transaction_file = fixesfile,
                    revert_on_error = True,
                    scenario = scen)

def initfunctions(eb):
    eb.create_function('fd01', 'length * 60 / 40')
    eb.create_function('fd02', '((volau + volad) / lanes - 1900) * .017 * ((volau + volad) / lanes .ge. 1900) + .01')
    eb.create_function('fd03', 'ul3')
    eb.create_function('fd04', '((volau + volad) / lanes - 1600) * .0065 * ((volau + volad) / lanes .ge. 1600) + .25')
    eb.create_function('fd05', 'length * 60 / 4 * (1 + .6 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 4) + (volau + volad - 100 * lanes) * (((volau + volad) .ge. 100 * lanes) * .6) / lanes')
    eb.create_function('fd06', '40 + ((volau + volad) - 100) * 60 / (volau + volad) * ((volau +  volad) .ge. 100)')
    eb.create_function('fd22', 'length * 60 / 20 + .85 * ((volau + volad) / (400 * lanes)) ^ 5')
    eb.create_function('fd23', 'length * 60 / 30 + .85 * ((volau + volad) / (400 * lanes)) ^ 5')
    eb.create_function('fd24', 'length * 60 / 40 + .85 * ((volau + volad) / (400 * lanes)) ^ 5')
    eb.create_function('fd25', 'length * 60 / 50 + .85 * ((volau + volad) / (400 * lanes)) ^ 5')
    eb.create_function('fd26', 'length * 60 / 60 + .85 * ((volau + volad) / (400 * lanes)) ^ 5')
    eb.create_function('fd27', 'length * 60 / 70 + .85 * ((volau + volad) / (400 * lanes)) ^ 5')
    eb.create_function('fd28', 'length * 60 / 80 + .85 * ((volau + volad) / (400 * lanes)) ^ 5')
    eb.create_function('fd29', 'length * 60 / 90 + .85 * ((volau + volad) / (400 * lanes)) ^ 5')
    eb.create_function('fd30', 'length * 60 / 100 + .85 * ((volau + volad) / (600 * lanes)) ^ 5')
    eb.create_function('fd31', 'length * 60 / 110 + .85 * ((volau + volad) / (600 * lanes)) ^ 5')
    eb.create_function('fd32', 'length * 60 / 20 + .85 * ((volau + volad) / (600 * lanes)) ^ 5')
    eb.create_function('fd33', 'length * 60 / 30 + .85 * ((volau + volad) / (600 * lanes)) ^ 5')
    eb.create_function('fd34', 'length * 60 / 40 + .85 * ((volau + volad) / (600 * lanes)) ^ 5')
    eb.create_function('fd35', 'length * 60 / 50 + .85 * ((volau + volad) / (600 * lanes)) ^ 5')
    eb.create_function('fd36', 'length * 60 / 60 + .85 * ((volau + volad) / (600 * lanes)) ^ 5')
    eb.create_function('fd37', 'length * 60 / 70 + .85 * ((volau + volad) / (600 * lanes)) ^ 5')
    eb.create_function('fd38', 'length * 60 / 80 + .85 * ((volau + volad) / (600 * lanes)) ^ 5')
    eb.create_function('fd39', 'length * 60 / 90 + .85 * ((volau + volad) / (600 * lanes)) ^ 5')
    eb.create_function('fd40', 'length * 60 / 100 + .85 * ((volau + volad) / (800 * lanes)) ^ 5')
    eb.create_function('fd41', 'length * 60 / 110 + .85 * ((volau + volad) / (800 * lanes)) ^ 5')
    eb.create_function('fd42', 'length * 60 / 20 + .85 * ((volau + volad) / (800 * lanes)) ^ 5')
    eb.create_function('fd43', 'length * 60 / 30 + .85 * ((volau + volad) / (800 * lanes)) ^ 5')
    eb.create_function('fd44', 'length * 60 / 40 + .85 * ((volau + volad) / (800 * lanes)) ^ 5')
    eb.create_function('fd45', 'length * 60 / 50 + .85 * ((volau + volad) / (800 * lanes)) ^ 5')
    eb.create_function('fd46', 'length * 60 / 60 + .85 * ((volau + volad) / (800 * lanes)) ^ 5')
    eb.create_function('fd47', 'length * 60 / 70 + .85 * ((volau + volad) / (800 * lanes)) ^ 5')
    eb.create_function('fd48', 'length * 60 / 80 + .85 * ((volau + volad) / (800 * lanes)) ^ 5')
    eb.create_function('fd49', 'length * 60 / 90 + .85 * ((volau + volad) / (800 * lanes)) ^ 5')
    eb.create_function('fd50', 'length * 60 / 100 + .85 * ((volau + volad) / (1000 * lanes)) ^ 5')
    eb.create_function('fd51', 'length * 60 / 110 + .85 * ((volau + volad) / (1000 * lanes)) ^ 5')
    eb.create_function('fd52', 'length * 60 / 20 + .85 * ((volau + volad) / (1000 * lanes)) ^ 5')
    eb.create_function('fd53', 'length * 60 / 30 + .85 * ((volau + volad) / (1000 * lanes)) ^ 5')
    eb.create_function('fd54', 'length * 60 / 40 + .85 * ((volau + volad) / (1000 * lanes)) ^ 5')
    eb.create_function('fd55', 'length * 60 / 50 + .85 * ((volau + volad) / (1000 * lanes)) ^ 5')
    eb.create_function('fd56', 'length * 60 / 60 + .85 * ((volau + volad) / (1000 * lanes)) ^ 5')
    eb.create_function('fd57', 'length * 60 / 70 + .85 * ((volau + volad) / (1000 * lanes)) ^ 5')
    eb.create_function('fd58', 'length * 60 / 80 + .85 * ((volau + volad) / (1000 * lanes)) ^ 5')
    eb.create_function('fd59', 'length * 60 / 90 + .85 * ((volau + volad) / (1000 * lanes)) ^ 5')
    eb.create_function('fd60', 'length * 60 / 100 + .85 * ((volau + volad) / (1200 * lanes)) ^ 5')
    eb.create_function('fd61', 'length * 60 / 110 + .85 * ((volau + volad) / (1200 * lanes)) ^ 5')
    eb.create_function('fd62', 'length * 60 / 20 + .85 * ((volau + volad) / (1200 * lanes)) ^ 5')
    eb.create_function('fd63', 'length * 60 / 30 + .85 * ((volau + volad) / (1200 * lanes)) ^ 5')
    eb.create_function('fd64', 'length * 60 / 40 + .85 * ((volau + volad) / (1200 * lanes)) ^ 5')
    eb.create_function('fd65', 'length * 60 / 50 + .85 * ((volau + volad) / (1200 * lanes)) ^ 5')
    eb.create_function('fd66', 'length * 60 / 60 + .85 * ((volau + volad) / (1200 * lanes)) ^ 5')
    eb.create_function('fd67', 'length * 60 / 70 + .85 * ((volau + volad) / (1200 * lanes)) ^ 5')
    eb.create_function('fd68', 'length * 60 / 80 + .85 * ((volau + volad) / (1200 * lanes)) ^ 5')
    eb.create_function('fd69', 'length * 60 / 90 + .85 * ((volau + volad) / (1200 * lanes)) ^ 5')
    eb.create_function('fd70', 'length * 60 / 100 + .85 * ((volau + volad) / (1400 * lanes)) ^ 5')
    eb.create_function('fd71', 'length * 60 / 110 + .85 * ((volau + volad) / (1400 * lanes)) ^ 5')
    eb.create_function('fd72', 'length * 60 / 20 + .85 * ((volau + volad) / (1400 * lanes)) ^ 5')
    eb.create_function('fd73', 'length * 60 / 30 + .85 * ((volau + volad) / (1400 * lanes)) ^ 5')
    eb.create_function('fd74', 'length * 60 / 40 + .85 * ((volau + volad) / (1400 * lanes)) ^ 5')
    eb.create_function('fd75', 'length * 60 / 50 + .85 * ((volau + volad) / (1400 * lanes)) ^ 5')
    eb.create_function('fd76', 'length * 60 / 60 + .85 * ((volau + volad) / (1400 * lanes)) ^ 5')
    eb.create_function('fd77', 'length * 60 / 70 + .85 * ((volau + volad) / (1400 * lanes)) ^ 5')
    eb.create_function('fd78', 'length * 60 / 80 + .85 * ((volau + volad) / (1400 * lanes)) ^ 5')
    eb.create_function('fd79', 'length * 60 / 90 + .85 * ((volau + volad) / (1400 * lanes)) ^ 5')
    eb.create_function('fd80', 'length * 60 / (100 * 1.1) * (1 + .6 * .43 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 5.25)')
    eb.create_function('fd81', 'length * 60 / (110 * 1.1) * (1 + .6 * .43 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 5.25)')
    eb.create_function('fd82', 'length * 60 / 20 * (1 + .6 * .85 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 5)')
    eb.create_function('fd83', 'length * 60 / 30 * (1 + .6 * .85 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 5)')
    eb.create_function('fd84', 'length * 60 / 40 * (1 + .6 * .85 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 5)')
    eb.create_function('fd85', 'length * 60 / 50 * (1 + .6 * .85 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 5)')
    eb.create_function('fd86', 'length * 60 / 60 * (1 + .6 * .85 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 5)')
    eb.create_function('fd87', 'length * 60 / 70 * (1 + .6 * .85 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 5)')
    eb.create_function('fd88', 'length * 60 / (80 * 1.1) * (1 + .6 * .43 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 5.25)')
    eb.create_function('fd89', 'length * 60 / (90 * 1.1) * (1 + .6 * .43 * ((volau + volad) / (1600 * lanes ^ 1.05)) ^ 5.25)')
    eb.create_function('fd99', 'length')
    eb.create_function('ft01', 'timau + 3 * length')
    eb.create_function('ft02', 'timau + 1.8 * length')
    eb.create_function('ft03', 'timau + 1 * length')
    eb.create_function('ft04', 'timau + .5 * length')
    eb.create_function('ft05', 'timau * 1.5')
    eb.create_function('ft06', 'length * 1')
    eb.create_function('ft07', '(60 * length / speed)')
    eb.create_function('fp01', '(.1 + pvolau / 100) ^ 4')
    eb.create_function('fp02', '(.1 + pvolau / 200) ^ 4')
    eb.create_function('fp03', '(.1 + pvolau / 300) ^ 4')
    eb.create_function('fp04', '(.1 + pvolau / 400) ^ 4')
    eb.create_function('fp05', '(.1 + pvolau / 500) ^ 4')
    eb.create_function('fp06', '(.1 + pvolau / 600) ^ 4')
    eb.create_function('fp07', '(.1 + pvolau / 700) ^ 4')
    eb.create_function('fp08', '(.1 + pvolau / 800) ^ 4')
    eb.create_function('fp09', '(.1 + pvolau / 900) ^ 4')
    eb.create_function('fp10', '(.1 + pvolau / 1000) ^ 4')
    eb.create_function('fp12', '(.1 + pvolau / 1200) ^ 4')
    eb.create_function('fp16', '(.1 + pvolau / 1600) ^ 4')
    eb.create_function('fp24', '(.1 + pvolau / 2400) ^ 4')
    eb.create_function('fp32', '(.1 + pvolau / 3200) ^ 4')
