##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: ?
##--Purpose: Import Data for RTM Run
##---------------------------------------------------------------------

import inro.modeller as _m

import traceback as _traceback
import os
import sqlite3
import csv as csv


import numpy as np
import pandas as pd



class DataImport(_m.Tool()):

    demographics_file = _m.Attribute(_m.InstanceType)
    geographics_file = _m.Attribute(_m.InstanceType)

    tool_run_msg = _m.Attribute(unicode)

    # TODO currently this tool is not directly runnable unless run model as been run
    # requires ms10, which is created there.  Need to decide if this is correct
    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Import Data for Model Run"
        pb.description = "Imports Scalars, Vectors, and Seed Matrices for Model Run"
        pb.branding_text = "TransLink"

        util = _m.Modeller().tool("translink.emme.util")
        input_path = util.get_input_path(_m.Modeller().emmebank)

        pb.add_select_file(tool_attribute_name="demographics_file",
                           window_type="file",
                           file_filter="*demographics*.csv",
                           start_path= input_path,
                           title="Demographics File: ",
                           note="File must be csv file.")

        pb.add_select_file(tool_attribute_name="geographics_file",
                           window_type="file",
                           file_filter="*geographics*.csv",
                           start_path= input_path,
                           title="Geographics File: ",
                           note="File must be csv file.")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            eb = _m.Modeller().emmebank
            self.__call__(eb, self.demographics_file, self.geographics_file)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))


    @_m.logbook_trace("Data Import")
    def __call__(self, eb, demographics_file, geographics_file):
        util = _m.Modeller().tool("translink.emme.util")
        model_year = int(util.get_year(eb))

        self.init_scalars(eb)
        self.import_vectors(eb, demographics_file, geographics_file)

        self.init_seeds(eb, horizon_year=model_year)

    @_m.logbook_trace("Initializing Scalar Matrices")
    def init_scalars(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        util.initmat(eb, "ms100", "autoOpCost", "Auto Operating Cost", 0.18)
        util.initmat(eb, "ms101", "lgvOpCost", "Light Truck Operating Cost", 0.24)
        util.initmat(eb, "ms102", "hgvOpCost", "Heavy Truck Operating Cost", 0.56)
        util.initmat(eb, "ms110", "HOV3OccHbw", "HOV3 Occupancy HB Work", 3.51)
        util.initmat(eb, "ms111", "HOV3OccHbu", "HOV3 Occupancy HB University", 3.43)
        util.initmat(eb, "ms112", "HOV3OccHbesc", "HOV3 Occupancy HB Escorting", 3.51)
        util.initmat(eb, "ms113", "HOV3OccHbpb", "HOV3 Occupancy HB Pers Bus", 3.45)
        util.initmat(eb, "ms114", "HOV3OccHBsch", "HOV3 Occupancy HB School", 3.58)
        util.initmat(eb, "ms115", "HOV3OccHBshop", "HOV3 Occupancy HB Shop", 3.43)
        util.initmat(eb, "ms116", "HOV3OccHBsoc", "HOV3 Occupancy HB Social", 3.68)
        util.initmat(eb, "ms117", "HOV3OccNHBw", "HOV3 Occupancy NHB Work", 3.47)
        util.initmat(eb, "ms118", "HOV3OccNHBo", "HOV3 Occupancy NHB Other", 3.63)
        util.initmat(eb, "ms130", "lgvPCE", "Light Truck Passenger Car Equivalent", 1.5)
        util.initmat(eb, "ms131", "hgvPCE", "Heavy Truck Passenger Car Equivalent", 2.5)
        util.initmat(eb, "ms200", "VotWkLowIncSov", "VOTSOV Work Low"      , 6.58)
        util.initmat(eb, "ms201", "VotWkMedIncSov", "VOTSOV Work Med"      , 4.12)
        util.initmat(eb, "ms202", "VotWkHighIncSov", "VOTSOV Work High"    , 3.38)
        util.initmat(eb, "ms203", "VotWkLowIncHov", "VOTHOV Work Low"      , 6.58)
        util.initmat(eb, "ms204", "VotWkMedIncHov", "VOTHOV Work Med"      , 4.12)
        util.initmat(eb, "ms205", "VotWkHighIncHov", "VOTHOV Work High"    , 3.38)
        util.initmat(eb, "ms206", "VotNwkLowIncSov", "VOTSOV Nonwork Low"  , 6.58)
        util.initmat(eb, "ms207", "VotNwkMedIncSov", "VOTSOV Nonwork Med"  , 4.12)
        util.initmat(eb, "ms208", "VotNwkHighIncSov", "VOTSOV Nonwork High", 3.38)
        util.initmat(eb, "ms209", "VotNwkLowIncHov", "VOTHOV Nonwork Low"  , 6.58)
        util.initmat(eb, "ms210", "VotNwkMedIncHov", "VOTHOV Nonwork Med"  , 4.12)
        util.initmat(eb, "ms211", "VotNwkHighIncHov", "VOTHOV Nonwork High", 3.38)
        util.initmat(eb, "ms212", "VotWkBus", "VOT Bus Work", 3.06)
        util.initmat(eb, "ms213", "VotWkRail", "VOT Rail Work", 3.35)
        util.initmat(eb, "ms214", "VotWkWce", "VOT WCE Work", 3.35)
        util.initmat(eb, "ms215", "VotNwkBus", "VOT Bus Nonwork", 0)
        util.initmat(eb, "ms216", "VotNwkRail", "VOT Rail Nonwork", 0)
        util.initmat(eb, "ms217", "VotNwkWce", "VOT WCE Nonwork", 0)
        util.initmat(eb, "ms218", "VotLgv", "VOT lgv", 2.03)
        util.initmat(eb, "ms219", "VotHgv", "VOT hgv", 1.43)
        util.initmat(eb, "ms300", "busIVTprcpWk", "bus in-vehicle time perception work", 1.0922)
        util.initmat(eb, "ms301", "busWAITprcpWk", "bus wait time perception work", 1.6543)
        util.initmat(eb, "ms302", "busWALKprcpWk", "bus walk time perception work", 1.3765)
        util.initmat(eb, "ms303", "busTRANSprcpWk", "bus transfer perception work", 10.939)
        util.initmat(eb, "ms304", "busBOARDSprcpWk", "bus boarding perception work", 0)
        util.initmat(eb, "ms310", "railIVTprcpWk", "rail in-vehicle time perception work", 1)
        util.initmat(eb, "ms311", "railWAITprcpWk", "rail wait time perception work", 1.8068)
        util.initmat(eb, "ms312", "railWALKprcpWk", "rail walk time perception work", 1.5035)
        util.initmat(eb, "ms313", "railTRANSprcpWk", "rail transfer perception work", 11.948)
        util.initmat(eb, "ms314", "railBOARDSprcpWk", "rail boarding perception work", 0)
        util.initmat(eb, "ms320", "wceIVTprcpWk", "wce in-vehicle time perception work", 1)
        util.initmat(eb, "ms321", "wceWAITprcpWk", "wce wait time perception work", 1.8068)
        util.initmat(eb, "ms322", "wceWALKprcpWk", "wce walk time perception work", 1.5035)
        util.initmat(eb, "ms323", "wceTRANSprcpWk", "wce transfer perception work", 11.948)
        util.initmat(eb, "ms324", "wceBOARDSprcpWk", "wce boarding perception work", 0)
        util.initmat(eb, "ms330", "busIVTprcpNwk", "bus in-vehicle time perception nonwork", 0)
        util.initmat(eb, "ms331", "busWAITprcpNwk", "bus wait time perception nonwork", 0)
        util.initmat(eb, "ms332", "busWALKprcpNwk", "bus walk time perception nonwork", 0)
        util.initmat(eb, "ms333", "busTRANSprcpNwk", "bus transfer perception nonwork", 0)
        util.initmat(eb, "ms334", "busBOARDSprcpNwk", "bus boarding perception nonwork", 0)
        util.initmat(eb, "ms340", "railIVTprcpNwk", "rail in-vehicle time perception nonwork", 0)
        util.initmat(eb, "ms341", "railWAITprcpNwk", "rail wait time perception nonwork", 0)
        util.initmat(eb, "ms342", "railWALKprcpNwk", "rail walk time perception nonwork", 0)
        util.initmat(eb, "ms343", "railTRANSprcpNwk", "rail transfer perception nonwork", 0)
        util.initmat(eb, "ms344", "railBOARDSprcpNwk", "rail boarding perception nonwork", 0)
        util.initmat(eb, "ms350", "wceIVTprcpNwk", "wce in-vehicle time perception nonwork", 0)
        util.initmat(eb, "ms351", "wceWAITprcpNwk", "wce wait time perception nonwork", 0)
        util.initmat(eb, "ms352", "wceWALKprcpNwk", "wce walk time perception nonwork", 0)
        util.initmat(eb, "ms353", "wceTRANSprcpNwk", "wce transfer perception nonwork", 0)
        util.initmat(eb, "ms354", "wceBOARDSprcpNwk", "wce boarding perception nonwork", 0)
        util.initmat(eb, "ms400", "HbWBl_AM_P-A", "HbW Blend AM P-A Factor", 0.387)
        util.initmat(eb, "ms401", "HbWBl_MD_P-A", "HbW Blend MD P-A Factor", 0.13)
        util.initmat(eb, "ms402", "HbWBl_PM_P-A", "HbW Blend PM P-A Factor", 0.024)
        util.initmat(eb, "ms403", "HbWBl_AM_A-P", "HbW Blend AM A-P Factor", 0.007)
        util.initmat(eb, "ms404", "HbWBl_MD_A-P", "HbW Blend MD A-P Factor", 0.181)
        util.initmat(eb, "ms405", "HbWBl_PM_A-P", "HbW Blend PM A-P Factor", 0.271)
        util.initmat(eb, "ms406", "HbWBl_AM_WCE_P-A", "HbW Blend AM WCE P-A Factor", 0.516)
        util.initmat(eb, "ms407", "HbWBl_PM_WCE_A-P", "HbW Blend PM WCE P-A Factor", 0.484)
        util.initmat(eb, "ms410", "HbUBl_AM_P-A", "HbU Blend AM P-A Factor", 0.36)
        util.initmat(eb, "ms411", "HbUBl_MD_P-A", "HbU Blend MD P-A Factor", 0.159)
        util.initmat(eb, "ms412", "HbUBl_PM_P-A", "HbU Blend PM P-A Factor", 0.031)
        util.initmat(eb, "ms413", "HbUBl_AM_A-P", "HbU Blend AM A-P Factor", 0.035)
        util.initmat(eb, "ms414", "HbUBl_MD_A-P", "HbU Blend MD A-P Factor", 0.229)
        util.initmat(eb, "ms415", "HbUBl_PM_A-P", "HbU Blend PM A-P Factor", 0.187)
        util.initmat(eb, "ms420", "HbScBl_AM_P-A", "HbSc Blend AM P-A Factor", 0.547)
        util.initmat(eb, "ms421", "HbScBl_MD_P-A", "HbSc Blend MD P-A Factor", 0.038)
        util.initmat(eb, "ms422", "HbScBl_PM_P-A", "HbSc Blend PM P-A Factor", 0.024)
        util.initmat(eb, "ms423", "HbScBl_AM_A-P", "HbSc Blend AM A-P Factor", 0.001)
        util.initmat(eb, "ms424", "HbScBl_MD_A-P", "HbSc Blend MD A-P Factor", 0.129)
        util.initmat(eb, "ms425", "HbScBl_PM_A-P", "HbSc Blend PM A-P Factor", 0.261)
        util.initmat(eb, "ms430", "HbShBl_AM_P-A", "HbSh Blend AM P-A Factor", 0.053)
        util.initmat(eb, "ms431", "HbShBl_MD_P-A", "HbSh Blend MD P-A Factor", 0.282)
        util.initmat(eb, "ms432", "HbShBl_PM_P-A", "HbSh Blend PM P-A Factor", 0.083)
        util.initmat(eb, "ms433", "HbShBl_AM_A-P", "HbSh Blend AM A-P Factor", 0.014)
        util.initmat(eb, "ms434", "HbShBl_MD_A-P", "HbSh Blend MD A-P Factor", 0.368)
        util.initmat(eb, "ms435", "HbShBl_PM_A-P", "HbSh Blend PM A-P Factor", 0.201)
        util.initmat(eb, "ms440", "HbPbBl_AM_P-A", "HbPb Blend AM P-A Factor", 0.146)
        util.initmat(eb, "ms441", "HbPbBl_MD_P-A", "HbPb Blend MD P-A Factor", 0.288)
        util.initmat(eb, "ms442", "HbPbBl_PM_P-A", "HbPb Blend PM P-A Factor", 0.083)
        util.initmat(eb, "ms443", "HbPbBl_AM_A-P", "HbPb Blend AM A-P Factor", 0.031)
        util.initmat(eb, "ms444", "HbPbBl_MD_A-P", "HbPb Blend MD A-P Factor", 0.296)
        util.initmat(eb, "ms445", "HbPbBl_PM_A-P", "HbPb Blend PM A-P Factor", 0.157)
        util.initmat(eb, "ms450", "HbSoBl_AM_P-A", "HbSo Blend AM P-A Factor", 0.088)
        util.initmat(eb, "ms451", "HbSoBl_MD_P-A", "HbSo Blend MD P-A Factor", 0.29)
        util.initmat(eb, "ms452", "HbSoBl_PM_P-A", "HbSo Blend PM P-A Factor", 0.115)
        util.initmat(eb, "ms453", "HbSoBl_AM_A-P", "HbSo Blend AM A-P Factor", 0.017)
        util.initmat(eb, "ms454", "HbSoBl_MD_A-P", "HbSo Blend MD A-P Factor", 0.392)
        util.initmat(eb, "ms455", "HbSoBl_PM_A-P", "HbSo Blend PM A-P Factor", 0.098)
        util.initmat(eb, "ms460", "HbEsBl_AM_P-A", "HbEs Blend AM P-A Factor", 0.242)
        util.initmat(eb, "ms461", "HbEsBl_MD_P-A", "HbEs Blend MD P-A Factor", 0.21)
        util.initmat(eb, "ms462", "HbEsBl_PM_P-A", "HbEs Blend PM P-A Factor", 0.101)
        util.initmat(eb, "ms463", "HbEsBl_AM_A-P", "HbEs Blend AM A-P Factor", 0.086)
        util.initmat(eb, "ms464", "HbEsBl_MD_A-P", "HbEs Blend MD A-P Factor", 0.196)
        util.initmat(eb, "ms465", "HbEsBl_PM_A-P", "HbEs Blend PM A-P Factor", 0.165)
        util.initmat(eb, "ms470", "NHbWBl_AM_P-A", "NHbW Blend AM P-A Factor", 0.209)
        util.initmat(eb, "ms471", "NHbWBl_MD_P-A", "NHbW Blend MD P-A Factor", 0.489)
        util.initmat(eb, "ms472", "NHbWBl_PM_P-A", "NHbW Blend PM P-A Factor", 0.302)
        util.initmat(eb, "ms480", "NHbOBl_AM_P-A", "NHbO Blend AM P-A Factor", 0.122)
        util.initmat(eb, "ms481", "NHbOBl_MD_P-A", "NHbO Blend MD P-A Factor", 0.6)
        util.initmat(eb, "ms482", "NHbOBl_PM_P-A", "NHbO Blend PM P-A Factor", 0.278)

    @_m.logbook_trace("Importing Vector Data from CSV")
    def import_vectors(self, eb, demographics_file, geographics_file):
        util = _m.Modeller().tool("translink.emme.util")

        # set directory locations for csv files and sqlite db
        file_loc= util.get_input_path(eb)
        db_loc = util.get_eb_path(eb)

        # point to csv input files
        demo_file = demographics_file
        geo_file = geographics_file
        pnr_file = os.path.join(file_loc, 'taz1700_pnr.csv')
        dummy_file = os.path.join(file_loc,'taz1700_dummies.csv')

        # import raw data to mo's in emmebank
        util.read_csv_momd(eb, demo_file)
        util.read_csv_momd(eb, geo_file)
        util.read_csv_momd(eb, pnr_file)
        util.read_csv_momd(eb, dummy_file)

        # setup connection to sqlite database
        db_path = os.path.join(db_loc, 'rtm.db')
        conn = sqlite3.connect(db_path)
        # read csvs and export to sqlite database

        # demographics
        df = pd.read_csv(demo_file, skiprows = 3)
        df.to_sql(name='demographics', con=conn, flavor='sqlite', index=False, if_exists='replace')

        # geographics
        df = pd.read_csv(geo_file, skiprows = 3)
        df.to_sql(name='geographics', con=conn, flavor='sqlite', index=False, if_exists='replace')

        # park and ride
        df = pd.read_csv(pnr_file, skiprows = 3)
        df.to_sql(name='parknride', con=conn, flavor='sqlite', index=False, if_exists='replace')

        # dummary variables
        df = pd.read_csv(dummy_file, skiprows = 3)
        df.to_sql(name='dummies', con=conn, flavor='sqlite', index=False, if_exists='replace')

        conn.close()

    @_m.logbook_trace("Importing Seed Matrices")
    def init_seeds(self, eb, horizon_year):
        util = _m.Modeller().tool("translink.emme.util")

        model_year = horizon_year
        mod = _m.Modeller()
        project = mod.desktop.project
        proj_path = os.path.dirname(project.path)


        mat_transaction = mod.tool("inro.emme.data.matrix.matrix_transaction")


        # Batch in starter auto demand used for generating starter skims, demand is aggregated into 4 classes, SOV, HOV, Light Tr, Heavy Tr
        util.delmat(eb, "mf10")
        util.delmat(eb, "mf11")
        data_path = os.path.join(proj_path, "BaseNetworks", "Starter_Demand_AM.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

        util.delmat(eb, "mf30")
        util.delmat(eb, "mf31")
        data_path = os.path.join(proj_path, "BaseNetworks", "Starter_Demand_MD.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

        util.delmat(eb, "mf50")
        util.delmat(eb, "mf51")
        data_path = os.path.join(proj_path, "BaseNetworks", "Starter_Demand_PM.in")
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

        # Batch in external demand matrices
        util.delmat(eb, "mf70")
        util.delmat(eb, "mf71")
        data_path = os.path.join(proj_path, "BaseNetworks", "External_Demand_AM_%s.in" % model_year)
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

        util.delmat(eb, "mf75")
        util.delmat(eb, "mf76")
        data_path = os.path.join(proj_path, "BaseNetworks", "External_Demand_MD_%s.in" % model_year)
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)

		# TODO update external demand
		# Note PM external demand is AM transposed multiplied by a factor
        util.delmat(eb, "mf80")
        util.delmat(eb, "mf81")
        data_path = os.path.join(proj_path, "BaseNetworks", "External_Demand_PM_%s.in" % model_year)
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)


        util.delmat(eb, "mf90")
        data_path = os.path.join(proj_path, "BaseNetworks", "bike_score_skim_%s.in" % model_year)
        mat_transaction(transaction_file = data_path,
                        throw_on_error = True)
