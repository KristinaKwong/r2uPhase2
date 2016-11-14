##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: ?
##--Purpose: Generate Initial Data for RTM Run
##---------------------------------------------------------------------
import inro.modeller as _m

import traceback as _traceback
import os
import sqlite3
import numpy as np
import pandas as pd

class DataGeneration(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Generate Data for Model Run"
        pb.description = "Generate Densities, Initial Skims, data dependant values"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            eb = _m.Modeller().emmebank
            self.__call__(eb)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Model Data Generation")
    def __call__(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        self.matrix_batchins(eb)
        self.calc_density(eb)



    @_m.logbook_trace("Execute Intrazonal Calculation")
    def intra_zonal_calc(self, eb, matrix):
        util = _m.Modeller().tool("translink.emme.util")

        # get longform index of all zone combinations
        ij = util.get_pd_ij_df(eb)

        # add matrix to dataframe
        ij['value'] = util.get_matrix_numpy(eb, matrix).flatten()

        # calculate the minimum ij value where value > 0
        ijmin = ij[ij.value > 0]
        ijmin = ijmin['value'].groupby(ijmin['i'])
        ijmin = ijmin.min() * 0.5
        ijmin = ijmin.reset_index()

        # attach minimum value to input matrix and replace value for intrazonals
        ij = pd.merge(ij, ijmin, how='left', left_on = ['i','j'], right_on = ['i','i'])
        ij['value'] = np.where(ij['i'] == ij['j'], ij['value_y'], ij['value_x'])
        ij.drop(['value_x', 'value_y'], axis=1, inplace=True)
        ij['value'].fillna(0, inplace=True)

        # get length of array for reshaping database - should always be 1741 in phase 3
        # but allows for sub area models without breaking the calculation
        length = int(np.sqrt(len(test_df['value'])))

        # put back in emmebank with square shape
        util.set_matrix_numpy(eb, matrix, ij['value'].reshape(length,length))



    @_m.logbook_trace("Calculate Densities")
    def calc_density(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        # get data from emmebank
        zones = util.get_matrix_numpy(eb, "mo51")
        totpop = util.get_matrix_numpy(eb, "mo10")
        totemp = util.get_matrix_numpy(eb, "mo20")
        combined = totpop + totemp
        area = util.get_matrix_numpy(eb, "mo50")

        # calculate densities
        # handling divide by zero error and setting to 0
        with np.errstate(divide='ignore', invalid='ignore'):
            popdens = np.true_divide(totpop, area)
            popdens[ ~ np.isfinite( popdens )] = 0

        # handling divide by zero error and setting to 0
        with np.errstate(divide='ignore', invalid='ignore'):
            empdens = np.true_divide(totemp, area)
            empdens[ ~ np.isfinite( empdens )] = 0

        # handling divide by zero error and setting to 0
        with np.errstate(divide='ignore', invalid='ignore'):
            combinedens = np.true_divide(combined, area)
            combinedens[ ~ np.isfinite( combinedens )] = 0

        # write data to emmebank
        util.set_matrix_numpy(eb, 'mo200',popdens)
        util.set_matrix_numpy(eb, 'mo201',empdens)
        util.set_matrix_numpy(eb, 'mo202',combinedens)

        # reshape to create pandas dataframe
        em = empdens.reshape(empdens.shape[0])
        po = popdens.reshape(popdens.shape[0])
        co = combinedens.reshape(combinedens.shape[0])
        zo = zones.reshape(zones.shape[0])
        df = pd.DataFrame({'TAZ1700': zo,
               'popdens': po,
               'empdens': em,
               'combinedens' : co},
               columns=['TAZ1700','popdens','empdens','combinedens'])

        # write data to rtm sqlite database
        db_loc = util.get_eb_path(eb)
        db_path = os.path.join(db_loc, 'rtm.db')
        conn = sqlite3.connect(db_path)
        df.to_sql(name='densities', con=conn, flavor='sqlite', index=False, if_exists='replace')
        conn.close()


    @_m.logbook_trace("Initial Demand and Skim Matrix Creation")
    def matrix_batchins(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        ########################################################################
        # densities
        ########################################################################

        util.initmat(eb, "mo200", "popdens", "Population density (per/hec)", 0)
        util.initmat(eb, "mo201", "empdens", "Employment density (job/hec)", 0)
        util.initmat(eb, "mo202", "combinedens", "Pop + Emp density (per hec)", 0)

        ########################################################################
        # demand matrices
        ########################################################################

        # AM
        util.initmat(eb, "mf300", "sovVhWkLiAm", "SOV veh work lowinc AM", 0)
        util.initmat(eb, "mf301", "sovVhWkMiAm", "SOV veh work medinc AM", 0)
        util.initmat(eb, "mf302", "sovVhWkHiAm", "SOV veh work medinc AM", 0)
        util.initmat(eb, "mf303", "sovVhNwkLiAm", "SOV veh nonwork lowinc AM", 0)
        util.initmat(eb, "mf304", "sovVhNwkMiAm", "SOV veh nonwork medinc AM", 0)
        util.initmat(eb, "mf305", "sovVhNwkHiAm", "SOV veh nonwork medinc AM", 0)
        util.initmat(eb, "mf306", "hovVhWkLiAm", "HOV veh work lowinc AM", 0)
        util.initmat(eb, "mf307", "hovVhWkMiAm", "HOV veh work medinc AM", 0)
        util.initmat(eb, "mf308", "hovVhWkHiAm", "HOV veh work medinc AM", 0)
        util.initmat(eb, "mf309", "hovVhNwkLiAm", "HOV veh nonwork lowinc AM", 0)
        util.initmat(eb, "mf310", "hovVhNwkMiAm", "HOV veh nonwork medinc AM", 0)
        util.initmat(eb, "mf311", "hovVhNwkHiAm", "HOV veh nonwork medinc AM", 0)
        util.initmat(eb, "mf312", "lgvPceAm", "light trucks PCE AM", 0)
        util.initmat(eb, "mf313", "hgvPceAm", "heavy trucks PCE AM", 0)
        # MD
        util.initmat(eb, "mf320", "sovVhWkLiMd", "SOV veh work lowinc MD", 0)
        util.initmat(eb, "mf321", "sovVhWkMiMd", "SOV veh work medinc MD", 0)
        util.initmat(eb, "mf322", "sovVhWkHiMd", "SOV veh work medinc MD", 0)
        util.initmat(eb, "mf323", "sovVhNwkLiMd", "SOV veh nonwork lowinc MD", 0)
        util.initmat(eb, "mf324", "sovVhNwkMiMd", "SOV veh nonwork medinc MD", 0)
        util.initmat(eb, "mf325", "sovVhNwkHiMd", "SOV veh nonwork medinc MD", 0)
        util.initmat(eb, "mf326", "hovVhWkLiMd", "HOV veh work lowinc MD", 0)
        util.initmat(eb, "mf327", "hovVhWkMiMd", "HOV veh work medinc MD", 0)
        util.initmat(eb, "mf328", "hovVhWkHiMd", "HOV veh work medinc MD", 0)
        util.initmat(eb, "mf329", "hovVhNwkLiMd", "HOV veh nonwork lowinc MD", 0)
        util.initmat(eb, "mf330", "hovVhNwkMiMd", "HOV veh nonwork medinc MD", 0)
        util.initmat(eb, "mf331", "hovVhNwkHiMd", "HOV veh nonwork medinc MD", 0)
        util.initmat(eb, "mf332", "lgvPceMd", "light trucks PCE MD", 0)
        util.initmat(eb, "mf333", "hgvPceMd", "heavy trucks PCE MD", 0)
        # PM
        util.initmat(eb, "mf340", "sovVhWkLiPm", "SOV veh work lowinc PM", 0)
        util.initmat(eb, "mf341", "sovVhWkMiPm", "SOV veh work medinc PM", 0)
        util.initmat(eb, "mf342", "sovVhWkHiPm", "SOV veh work medinc PM", 0)
        util.initmat(eb, "mf343", "sovVhNwkLiPm", "SOV veh nonwork lowinc PM", 0)
        util.initmat(eb, "mf344", "sovVhNwkMiPm", "SOV veh nonwork medinc PM", 0)
        util.initmat(eb, "mf345", "sovVhNwkHiPm", "SOV veh nonwork medinc PM", 0)
        util.initmat(eb, "mf346", "hovVhWkLiPm", "HOV veh work lowinc PM", 0)
        util.initmat(eb, "mf347", "hovVhWkMiPm", "HOV veh work medinc PM", 0)
        util.initmat(eb, "mf348", "hovVhWkHiPm", "HOV veh work medinc PM", 0)
        util.initmat(eb, "mf349", "hovVhNwkLiPm", "HOV veh nonwork lowinc PM", 0)
        util.initmat(eb, "mf350", "hovVhNwkMiPm", "HOV veh nonwork medinc PM", 0)
        util.initmat(eb, "mf351", "hovVhNwkHiPm", "HOV veh nonwork medinc PM", 0)
        util.initmat(eb, "mf352", "lgvPcePm", "light trucks PCE PM", 0)
        util.initmat(eb, "mf353", "hgvPcePm", "heavy trucks PCE PM", 0)

        # Move seed demand into Work SOV/HOV Medium Income for AM/MD/PM
        specs = []
        specs.append(util.matrix_spec("mf301", "mf10"))
        specs.append(util.matrix_spec("mf307", "mf11"))
        specs.append(util.matrix_spec("mf321", "mf30"))
        specs.append(util.matrix_spec("mf327", "mf31"))
        specs.append(util.matrix_spec("mf341", "mf50"))
        specs.append(util.matrix_spec("mf347", "mf51"))
        util.compute_matrix(specs)

        ########################################################################
        # skim matrices
        ########################################################################

        #####################
        # Auto
        #####################

        # AM
        util.initmat(eb, "mf5000", "AmSovWkDist", "Am Sov Work Distance", 0)
        util.initmat(eb, "mf5001", "AmSovWkTime", "Am Sov Work Time", 0)
        util.initmat(eb, "mf5002", "AmSovWkToll", "Am Sov Work Toll", 0)
        util.initmat(eb, "mf5003", "AmSovNwkDist", "Am Sov Nonwork Distance", 0)
        util.initmat(eb, "mf5004", "AmSovNwkTime", "Am Sov Nonwork Time", 0)
        util.initmat(eb, "mf5005", "AmSovNwkToll", "Am Sov Nonwork Toll", 0)
        util.initmat(eb, "mf5006", "AmHovWkDist", "Am Hov Work Distance", 0)
        util.initmat(eb, "mf5007", "AmHovWkTime", "Am Hov Work Time", 0)
        util.initmat(eb, "mf5008", "AmHovWkToll", "Am Hov Work Toll", 0)
        util.initmat(eb, "mf5009", "AmHovNwkDist", "Am Hov Nonwork Distance", 0)
        util.initmat(eb, "mf5010", "AmHovNwkTime", "Am Hov Nonwork Time", 0)
        util.initmat(eb, "mf5011", "AmHovNwkToll", "Am Hov Nonwork Toll", 0)

        # MD
        util.initmat(eb, "mf5020", "MdSovWkDist", "Md Sov Work Distance", 0)
        util.initmat(eb, "mf5021", "MdSovWkTime", "Md Sov Work Time", 0)
        util.initmat(eb, "mf5022", "MdSovWkToll", "Md Sov Work Toll", 0)
        util.initmat(eb, "mf5023", "MdSovNwkDist", "Md Sov Nonwork Distance", 0)
        util.initmat(eb, "mf5024", "MdSovNwkTime", "Md Sov Nonwork Time", 0)
        util.initmat(eb, "mf5025", "MdSovNwkToll", "Md Sov Nonwork Toll", 0)
        util.initmat(eb, "mf5026", "MdHovWkDist", "Md Hov Work Distance", 0)
        util.initmat(eb, "mf5027", "MdHovWkTime", "Md Hov Work Time", 0)
        util.initmat(eb, "mf5028", "MdHovWkToll", "Md Hov Work Toll", 0)
        util.initmat(eb, "mf5029", "MdHovNwkDist", "Md Hov Nonwork Distance", 0)
        util.initmat(eb, "mf5030", "MdHovNwkTime", "Md Hov Nonwork Time", 0)
        util.initmat(eb, "mf5031", "MdHovNwkToll", "Md Hov Nonwork Toll", 0)

        # PM
        util.initmat(eb, "mf5040", "PmSovWkDist", "Pm Sov Work Distance", 0)
        util.initmat(eb, "mf5041", "PmSovWkTime", "Pm Sov Work Time", 0)
        util.initmat(eb, "mf5042", "PmSovWkToll", "Pm Sov Work Toll", 0)
        util.initmat(eb, "mf5043", "PmSovNwkDist", "Pm Sov Nonwork Distance", 0)
        util.initmat(eb, "mf5044", "PmSovNwkTime", "Pm Sov Nonwork Time", 0)
        util.initmat(eb, "mf5045", "PmSovNwkToll", "Pm Sov Nonwork Toll", 0)
        util.initmat(eb, "mf5046", "PmHovWkDist", "Pm Hov Work Distance", 0)
        util.initmat(eb, "mf5047", "PmHovWkTime", "Pm Hov Work Time", 0)
        util.initmat(eb, "mf5048", "PmHovWkToll", "Pm Hov Work Toll", 0)
        util.initmat(eb, "mf5049", "PmHovNwkDist", "Pm Hov Nonwork Distance", 0)
        util.initmat(eb, "mf5050", "PmHovNwkTime", "Pm Hov Nonwork Time", 0)
        util.initmat(eb, "mf5051", "PmHovNwkToll", "Pm Hov Nonwork Toll", 0)

        #####################
        # Bus
        #####################

        # AM
        util.initmat(eb, "mf5200", "AmBusIvtt", "Am Bus InVehicle Time", 0)
        util.initmat(eb, "mf5201", "AmBusWait", "Am Bus Waiting Time", 0)
        util.initmat(eb, "mf5202", "AmBusAux", "Am Bus Auxillary Time", 0)
        util.initmat(eb, "mf5203", "AmBusBoard", "Am Bus Boardings", 0)
        util.initmat(eb, "mf5204", "AmBusFare", "Am Bus Fare", 0)

        # MD
        util.initmat(eb, "mf5210", "MdBusWait", "Md Bus Waiting Time", 0)
        util.initmat(eb, "mf5211", "MdBusAux", "Md Bus Auxillary Time", 0)
        util.initmat(eb, "mf5212", "MdBusBoard", "Md Bus Boardings", 0)
        util.initmat(eb, "mf5213", "MdBusFare", "Md Bus Fare", 0)

        # PM
        util.initmat(eb, "mf5220", "PmBusWait", "Pm Bus Waiting Time", 0)
        util.initmat(eb, "mf5221", "PmBusAux", "Pm Bus Auxillary Time", 0)
        util.initmat(eb, "mf5222", "PmBusBoard", "Pm Bus Boardings", 0)
        util.initmat(eb, "mf5223", "PmBusFare", "Pm Bus Fare", 0)

        #####################
        # Rail
        #####################

        # AM
        util.initmat(eb, "mf5400", "AmRailIvtt", "Am Rail Invehicle Time", 0)
        util.initmat(eb, "mf5401", "AmRailIvttBus", "Am Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5402", "AmRailWait", "Am Rail Waiting Time", 0)
        util.initmat(eb, "mf5403", "AmRailAux", "Am Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5405", "AmRailFare", "Am Rail Fare", 0)
        util.initmat(eb, "mf5404", "AmRailBoard", "Am Rail Boardings", 0)

        # MD
        util.initmat(eb, "mf5410", "MdRailIvtt", "Md Rail Invehicle Time", 0)
        util.initmat(eb, "mf5411", "MdRailIvttBus", "Md Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5412", "MdRailWait", "Md Rail Waiting Time", 0)
        util.initmat(eb, "mf5413", "MdRailAux", "Md Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5414", "MdRailBoard", "Md Rail Boardings", 0)
        util.initmat(eb, "mf5415", "MdRailFare", "Md Rail Fare", 0)

        # PM
        util.initmat(eb, "mf5420", "PmRailIvtt", "Pm Rail Invehicle Time", 0)
        util.initmat(eb, "mf5421", "PmRailIvttBus", "Pm Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5422", "PmRailWait", "Pm Rail Waiting Time", 0)
        util.initmat(eb, "mf5423", "PmRailAux", "Pm Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5424", "PmRailBoard", "Pm Rail Boardings", 0)
        util.initmat(eb, "mf5425", "PmRailFare", "Pm Rail Fare", 0)


        #####################
        # WCE
        #####################

        # AM
        util.initmat(eb, "mf5600", "AmWceIvtt", "Am Rail Invehicle Time", 0)
        util.initmat(eb, "mf5601", "AmWceIvttRail", "Am Rail Invehicle Time on Rail", 0)
        util.initmat(eb, "mf5602", "AmWceIvttBus", "Am Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5603", "AmWceWait", "Am Rail Waiting Time", 0)
        util.initmat(eb, "mf5604", "AmWceAux", "Am Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5605", "AmWceBoards", "Am Rail Boardings", 0)
        util.initmat(eb, "mf5606", "AmWceFare", "Am Rail Fare", 0)

        # MD
        util.initmat(eb, "mf5610", "MdWceIvtt", "Md Rail Invehicle Time", 0)
        util.initmat(eb, "mf5611", "MdWceIvttRail", "Md Rail Invehicle Time on Rail", 0)
        util.initmat(eb, "mf5612", "MdWceIvttBus", "Md Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5613", "MdWceWait", "Md Rail Waiting Time", 0)
        util.initmat(eb, "mf5614", "MdWceAux", "Md Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5615", "MdWceBoards", "Md Rail Boardings", 0)
        util.initmat(eb, "mf5616", "MdWceFare", "Md Rail Fare", 0)

        # PM
        util.initmat(eb, "mf5620", "PmWceIvtt", "Pm Rail Invehicle Time", 0)
        util.initmat(eb, "mf5621", "PmWceIvttRail", "Pm Rail Invehicle Time on Rail", 0)
        util.initmat(eb, "mf5622", "PmWceIvttBus", "Pm Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5623", "PmWceWait", "Pm Rail Waiting Time", 0)
        util.initmat(eb, "mf5624", "PmWceAux", "Pm Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5625", "PmWceBoards", "Pm Rail Boardings", 0)
        util.initmat(eb, "mf5626", "PmWceFare", "Pm Rail Fare", 0)
