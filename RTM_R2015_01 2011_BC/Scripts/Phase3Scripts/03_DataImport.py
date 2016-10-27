##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: ?
##--Purpose: Import Data for RTM Run
##---------------------------------------------------------------------

import inro.modeller as _m

import os
import sqlite3
import csv as csv


import numpy as np
import pandas as pd



class DataImport(_m.Tool()):
	tool_run_msg = _m.Attribute(unicode)

	def page(self):
		pb = _m.ToolPageBuilder(self)
		pb.title = "Import Data for Model Run"
		pb.description = "Imports Scalar and Vector Data for Model Run"
		pb.branding_text = "TransLink"

		if self.tool_run_msg:
			pb.add_html(self.tool_run_msg)

		return pb.render()

	def run(self):
		with _m.logbook_trace("UNDER DEV - PR Impedance"):
			self.tool_run_msg = ""
			try:
				eb = _m.Modeller().emmebank
				self.__call__(eb)
				self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
			except Exception, e:
				self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))






	@_m.logbook_trace("Data Import")
	def __call__(self, eb):

		util = _m.Modeller().tool("translink.emme.util")

	@_m.logbook_trace("Initializing Scalar Matrices")
    def init_scalars(self, eb):


	@_m.logbook_trace("Importing Vector Data from CSV")
    def import_vectors(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        # set directory locations for csv files and sqlite db
        model_year = int(eb.matrix("ms10").data)
        file_loc= util.get_input_path(eb)
        db_loc = util.get_eb_path(eb)

        # point to csv input files
        demo_file = os.path.join(file_loc, 'taz1700_demographics_%s.csv' % model_year)
        geo_file = os.path.join(file_loc, 'taz1700_geographics_%s.csv' % model_year)
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


    def import_full_matrices():
