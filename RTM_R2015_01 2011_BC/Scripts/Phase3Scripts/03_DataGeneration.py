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

        # place holder run initial assignments and skims


        # auto matrices for intrazonal calcs
        intrazonal_mats = ["AmSovWkDist", "AmSovWkTime", "AmSovNwkDist", "AmSovNwkTime"
        ,"AmHovWkDist", "AmHovWkTime", "AmHovNwkDist", "AmHovNwkTime", "MdSovWkDist"
        ,"MdSovWkTime", "MdSovNwkDist", "MdSovNwkTime", "MdHovWkDist", "MdHovWkTime"
        ,"MdHovNwkDist", "MdHovNwkTime", "PmSovWkDist", "PmSovWkTime", "PmSovNwkDist"
        ,"PmSovNwkTime", "PmHovWkDist", "PmHovWkTime", "PmHovNwkDist", "PmHovNwkTime"]

        for skim in intrazonal_mats:
            mat = "mf{skim}".format(skim=skim)
            self.intra_zonal_calc(eb = eb, matrix = mat)

        # note transit_uni_accessibility has to run before other accessibilities
        # this is where the data table is started
        self.transit_uni_accessibility(eb)
        self.auto_accessibility(eb)
        self.dist_cbd_tc(eb)

    @_m.logbook_trace("Calculate Minimum Distances to CBD and Towncentre")
    def dist_cbd_tc(self, eb):
    	util = _m.Modeller().tool("translink.emme.util")

    	# acquire cbd and TC dummies
    	sql = """
    	SELECT
    	ti.TAZ1741, IFNULL(du.cbd, 0) as cbd, IFNULL(du.towncentre, 0) as tc
    	FROM taz_index ti
    	LEFT JOIN dummies du on du.TAZ1700 = ti.TAZ1741
    	"""
    	db_loc = util.get_eb_path(eb)
    	db_path = os.path.join(db_loc, 'rtm.db')
    	conn = sqlite3.connect(db_path)
    	df = pd.read_sql(sql, conn)
    	conn.close()


    	# get ij matrix and distance skims
    	# currently using non-work
    	# find minimum distance across all times of day
    	ij = util.get_pd_ij_df(eb)

    	ij['distAm'] = util.get_matrix_numpy(eb, "mfAmSovNwkDist").flatten()
    	ij['distMd'] = util.get_matrix_numpy(eb, "mfMdSovNwkDist").flatten()
    	ij['distPm'] = util.get_matrix_numpy(eb, "mfPmSovNwkDist").flatten()
    	ij['dist'] = ij[['distAm','distMd','distPm']].min(axis=1)

    	# join the dummies to the skims
    	ij = pd.merge(ij, df, how='left', left_on=['j'], right_on=['TAZ1741'])


    	# cbd min distance calculation
    	ij_cbd = ij[ij.cbd == 1]
    	ij_cbd = ij['dist'].groupby(ij['i'])
    	ij_cbd = ij_cbd.min()
    	ij_cbd = ij_cbd.reset_index()
    	ij_cbd['dist'] = np.where(ij_cbd['dist'] == 0, 0.5, ij_cbd['dist']) # set a minumimum distance so it isnt nothing

    	# create log transformed version for cbd
    	if ij_cbd['dist'].min() < 1:
    		log_trans_const = 1 - ij_cbd['dist'].min()
    	else:
    		log_trans_const = 0

    	ij_cbd['dist_cbd_ln'] = np.log(ij_cbd['dist'] + log_trans_const)
    	ij_cbd.rename(columns={'dist' : 'dist_cbd'}, inplace=True)

    	# tc min distance calculation
    	ij_tc = ij[ij.tc == 1]
    	ij_tc = ij['dist'].groupby(ij['i'])
    	ij_tc = ij_tc.min()
    	ij_tc = ij_tc.reset_index()
    	ij_tc['dist'] = np.where(ij_tc['dist'] == 0, 0.5, ij_tc['dist']) # set a minumimum distance so it isnt nothing

    	# create log transformed version for tc
    	if ij_tc['dist'].min() < 1:
    		log_trans_const = 1 - ij_tc['dist'].min()
    	else:
    		log_trans_const = 0

    	ij_tc['dist_tc_ln'] = np.log(ij_tc['dist'] + log_trans_const)
    	ij_tc.rename(columns={'dist' : 'dist_tc'}, inplace=True)

    	# one dataframe with both min distances
    	ij_dist = pd.merge(ij_cbd, ij_tc, how='left', left_on=['i'], right_on=['i'])

    	# write to emmebank
    	util.set_matrix_numpy(eb, 'modistCbd', ij_dist['dist_cbd'].reshape(ij_dist['dist_cbd'].shape[0], 1))
    	util.set_matrix_numpy(eb, 'modistCbdLn', ij_dist['dist_cbd_ln'].reshape(ij_dist['dist_cbd_ln'].shape[0], 1))
    	util.set_matrix_numpy(eb, 'modistTc', ij_dist['dist_tc'].reshape(ij_dist['dist_tc'].shape[0], 1))
    	util.set_matrix_numpy(eb, 'modistTcLn', ij_dist['dist_tc_ln'].reshape(ij_dist['dist_tc_ln'].shape[0], 1))

    	# write data to sqlite database
    	db_loc = util.get_eb_path(eb)
    	db_path = os.path.join(db_loc, 'rtm.db')
    	conn = sqlite3.connect(db_path)

    	# read existing accessibilities table from db and append with this data set
    	df = pd.read_sql("select * from accessibilities", conn)
    	df = pd.merge(df, ij_dist, how='left', left_on=['TAZ1741'], right_on = ['i'])
    	df.drop('i', axis=1, inplace=True)

    	# write the data back to database
    	df.to_sql(name='accessibilities', con=conn, flavor='sqlite', index=False, if_exists='replace')
    	conn.close()

    @_m.logbook_trace("Calculate Transit Accessibility")
    def transit_uni_accessibility(self, eb):
    	util = _m.Modeller().tool("translink.emme.util")

    	# define parameters
    	am_weight = 0.20
    	md_weight = 0.41
    	pm_weight = 0.39
    	time_cut = 30
    	time_cut_uni = 30

    	# get zone numbers
    	index = util.get_matrix_numpy(eb, "mozoneindex")
    	index = index.reshape(index.shape[0])

    	# get employment data
    	emp = util.get_matrix_numpy(eb, "moTotEmp")
    	emp = emp.reshape(emp.shape[0])

    	# get post sec FTE enrolment
    	ps = util.get_matrix_numpy(eb, "moEnrolPsFte")
    	ps = ps.reshape(ps.shape[0])

    	# merge employment and zone number
    	emp = pd.DataFrame({"taz": index, "emp": emp, "postsec" : ps}, columns=["taz","emp", "postsec"])

    	# create a long matrix of zone interchanges and join employment data to it
    	ij = util.get_pd_ij_df(eb)
    	ij = pd.merge(ij, emp, how='left', left_on = ['j'], right_on = ['taz'])
    	ij['emp'].fillna(0, inplace=True)
    	ij.drop(['taz'], axis=1, inplace=True)


    	# get bus skims
    	AmBusIvtt = util.get_matrix_numpy(eb, 'mfAmBusIvtt').flatten()
    	AmBusWait = util.get_matrix_numpy(eb, 'mfAmBusIvtt').flatten()
    	AmBusAux = util.get_matrix_numpy(eb, 'mfAmBusIvtt').flatten()

    	MdBusIvtt = util.get_matrix_numpy(eb, 'mfMdBusIvtt').flatten()
    	MdBusWait = util.get_matrix_numpy(eb, 'mfMdBusIvtt').flatten()
    	MdBusAux = util.get_matrix_numpy(eb, 'mfMdBusIvtt').flatten()

    	PmBusIvtt = util.get_matrix_numpy(eb, 'mfPmBusIvtt').flatten()
    	PmBusWait = util.get_matrix_numpy(eb, 'mfPmBusIvtt').flatten()
    	PmBusAux = util.get_matrix_numpy(eb, 'mfPmBusIvtt').flatten()

    	# get rail skims
    	AmRailIvtt = util.get_matrix_numpy(eb, 'mfAmRailIvtt').flatten()
    	AmRailIvttBus = util.get_matrix_numpy(eb, 'mfAmRailIvttBus').flatten()
    	AmRailWait = util.get_matrix_numpy(eb, 'mfAmRailIvtt').flatten()
    	AmRailAux = util.get_matrix_numpy(eb, 'mfAmRailIvtt').flatten()

    	MdRailIvtt = util.get_matrix_numpy(eb, 'mfMdRailIvtt').flatten()
    	MdRailIvttBus = util.get_matrix_numpy(eb, 'mfMdRailIvttBus').flatten()
    	MdRailWait = util.get_matrix_numpy(eb, 'mfMdRailIvtt').flatten()
    	MdRailAux = util.get_matrix_numpy(eb, 'mfMdRailIvtt').flatten()

    	PmRailIvtt = util.get_matrix_numpy(eb, 'mfPmRailIvtt').flatten()
    	PmRailIvttBus = util.get_matrix_numpy(eb, 'mfPmRailIvttBus').flatten()
    	PmRailWait = util.get_matrix_numpy(eb, 'mfPmRailIvtt').flatten()
    	PmRailAux = util.get_matrix_numpy(eb, 'mfPmRailIvtt').flatten()

    	# get Wce Skims
    	AmWceIvtt = util.get_matrix_numpy(eb, 'mfAmWceIvtt').flatten()
    	AmWceIvttRail = util.get_matrix_numpy(eb, 'mfAmWceIvttRail').flatten()
    	AmWceIvttBus = util.get_matrix_numpy(eb, 'mfAmWceIvttBus').flatten()
    	AmWceWait = util.get_matrix_numpy(eb, 'mfAmWceIvtt').flatten()
    	AmWceAux = util.get_matrix_numpy(eb, 'mfAmWceIvtt').flatten()

    	PmWceIvtt = util.get_matrix_numpy(eb, 'mfPmWceIvtt').flatten()
    	PmWceIvttRail = util.get_matrix_numpy(eb, 'mfPmWceIvttRail').flatten()
    	PmWceIvttBus = util.get_matrix_numpy(eb, 'mfPmWceIvttBus').flatten()
    	PmWceWait = util.get_matrix_numpy(eb, 'mfPmWceIvtt').flatten()
    	PmWceAux = util.get_matrix_numpy(eb, 'mfPmWceIvtt').flatten()

    	# calculate total travel time by mode and add to ij matrix
    	ij['AmBusTime'] = AmBusIvtt + AmBusWait + AmBusAux
    	ij['MdBusTime'] = MdBusIvtt + MdBusWait + MdBusAux
    	ij['PmBusTime'] = PmBusIvtt + PmBusWait + PmBusAux

    	ij['AmRailTime'] = AmRailIvtt + AmRailWait + AmRailAux + AmRailIvttBus
    	ij['MdRailTime'] = MdRailIvtt + MdRailWait + MdRailAux + MdRailIvttBus
    	ij['PmRailTime'] = PmRailIvtt + PmRailWait + PmRailAux + PmRailIvttBus

    	ij['AmWceTime'] = AmWceIvtt + AmWceWait + AmWceAux + AmWceIvttBus + AmWceIvttRail
    	ij['PmWceTime'] = PmWceIvtt + PmWceWait + PmWceAux + PmWceIvttBus + PmWceIvttRail

    	# get the minimum of the 3 travel times and call that transit time
    	# conceptually similar to the generic transit skim
    	ij['AmTransitTime'] = ij[['AmBusTime','AmRailTime','AmWceTime']].min(axis=1)
    	ij['MdTransitTime'] = ij[['MdBusTime','MdRailTime']].min(axis=1)
    	ij['PmTransitTime'] = ij[['PmBusTime','PmRailTime','PmWceTime']].min(axis=1)

    	#######################################################################
    	# Calculate and set transit accessibilities
    	#######################################################################

    	# calculate weighted accessibilities
    	ij['transit_acc'] = np.where(ij['AmTransitTime'] <= time_cut, ij['emp'] * am_weight, 0) \
    	+ np.where(ij['MdTransitTime'] <= time_cut, ij['emp'] * md_weight, 0)  \
    	+ np.where(ij['PmTransitTime'] <= time_cut, ij['emp'] * pm_weight, 0)

    	#aggregate to the origin zone
    	ij_acc = ij['transit_acc'].groupby(ij['i'])
    	ij_acc = ij_acc.sum()
    	ij_acc = ij_acc.reset_index()

    	# log transform, floor output at 0
    	if ij_acc['transit_acc'].min() < 1:
    		log_trans_const = 1 - ij_acc['transit_acc'].min()
    	else:
    		log_trans_const = 0

    	ij_acc['transit_acc_ln'] = np.log(ij_acc['transit_acc'] + log_trans_const)

    	# write data back to emmebank
    	# note have to reshape to work with util helper
    	util.set_matrix_numpy(eb, 'motransitAcc', ij_acc['transit_acc'].reshape(ij_acc['transit_acc'].shape[0], 1))
    	util.set_matrix_numpy(eb, 'motransitAccLn', ij_acc['transit_acc_ln'].reshape(ij_acc['transit_acc_ln'].shape[0], 1))


    	#######################################################################
    	# Calculate and set university accessibilities
    	#######################################################################

    	# calculate accessibilities
    	ij['uni_acc'] = np.where(ij['MdTransitTime'] <= time_cut_uni, ij['postsec'], 0)

    	#aggregate to the origin zone
    	ij_acc_u = ij['uni_acc'].groupby(ij['i'])
    	ij_acc_u = ij_acc_u.sum()
    	ij_acc_u = ij_acc_u.reset_index()


    	# log transform, floor output at 0
    	if ij_acc_u['uni_acc'].min() < 1:
    		log_trans_const = 1 - ij_acc_u['uni_acc'].min()
    	else:
    		log_trans_const = 0

    	ij_acc_u['uni_acc_ln'] = np.log(ij_acc_u['uni_acc'] + log_trans_const)


    	# note have to reshape to work with util helper
    	util.set_matrix_numpy(eb, 'mouniAcc', ij_acc_u['uni_acc'].reshape(ij_acc_u['uni_acc'].shape[0], 1))
    	util.set_matrix_numpy(eb, 'mouniAccLn', ij_acc_u['uni_acc_ln'].reshape(ij_acc_u['uni_acc_ln'].shape[0], 1))


    	#######################################################################
    	# Write everything to sqlite database
    	#######################################################################

    	# create index column for table.  name denotes full index
    	ij_acc.rename(columns={'i' : 'TAZ1741'}, inplace=True)
    	# merge both accessibility dataframes and drop addition taz column (i)
    	ij_acc = pd.merge(ij_acc, ij_acc_u, how='left', left_on=['TAZ1741'], right_on=['i'])
    	ij_acc.drop('i', axis=1, inplace=True)

    	# establish connection to db and write out data
    	# note, this table is created in transit accessibilities method and expanded with the methods
    	db_loc = util.get_eb_path(eb)
    	db_path = os.path.join(db_loc, 'rtm.db')
    	conn = sqlite3.connect(db_path)
    	ij_acc.to_sql(name='accessibilities', con=conn, flavor='sqlite', index=False, if_exists='replace')
    	conn.close()

    @_m.logbook_trace("Calculate Auto Accessibility")
    def auto_accessibility(self, eb):
    	util = _m.Modeller().tool("translink.emme.util")

    	# define parameters
    	am_weight = 0.29
    	md_weight = 0.45
    	pm_weight = 0.26
    	time_cut = 30

    	mat_am = 'mfAmSovNwkTime'
    	mat_md = 'mfMdSovNwkTime'
    	mat_pm = 'mfPmSovNwkTime'

    	# get zone numbers
    	index = util.get_matrix_numpy(eb, "mozoneindex")
    	index = index.reshape(index.shape[0])

    	# get employment data
    	emp = util.get_matrix_numpy(eb, "moTotEmp")
    	emp = emp.reshape(emp.shape[0])

    	# merge employment and zone number
    	emp = pd.DataFrame({"taz": index, "emp": emp}, columns=["taz","emp"])

    	# create a long matrix of zone interchanges and join employment data to it
    	ij = util.get_pd_ij_df(eb)
    	ij = pd.merge(ij, emp, how='left', left_on = ['j'], right_on = ['taz'])
    	ij['emp'].fillna(0, inplace=True)
    	ij.drop(['taz'], axis=1, inplace=True)


    	# add skim data to data frame with
    	ij['amtime'] = util.get_matrix_numpy(eb, mat_am).flatten()
    	ij['mdtime'] = util.get_matrix_numpy(eb, mat_md).flatten()
    	ij['pmtime'] = util.get_matrix_numpy(eb, mat_pm).flatten()

    	# create blended accessibility value of jobs meeting the time cutoff criteria
    	ij['auto_acc'] = np.where(ij['amtime'] <= time_cut, ij['emp'] * am_weight, 0) \
    	+ np.where(ij['mdtime'] <= time_cut, ij['emp'] * md_weight, 0)  \
    	+ np.where(ij['pmtime'] <= time_cut, ij['emp'] * pm_weight, 0)

    	#aggregate to the origin zone
    	ij_acc = ij['auto_acc'].groupby(ij['i'])
    	ij_acc = ij_acc.sum()
    	ij_acc = ij_acc.reset_index()

    	# log transform, floor output at 0
    	if ij_acc['auto_acc'].min() < 1:
    		log_trans_const = 1 - ij_acc['auto_acc'].min()
    	else:
    		log_trans_const = 0

    	ij_acc['auto_acc_ln'] = np.log(ij_acc['auto_acc'] + log_trans_const)

    	# write data back to emmebank
    	# note have to reshape to work with util helper
    	util.set_matrix_numpy(eb, 'moautoAcc', ij_acc['auto_acc'].reshape(ij_acc['auto_acc'].shape[0], 1))
    	util.set_matrix_numpy(eb, 'moautoAccLn', ij_acc['auto_acc_ln'].reshape(ij_acc['auto_acc_ln'].shape[0], 1))


    	#######################################################################
    	# Write everything to sqlite database
    	#######################################################################

    	# establish connection to db and write out data
    	# note, this table is created in transit accessibilities method and expanded with the other accessibilities methods
    	db_loc = util.get_eb_path(eb)
    	db_path = os.path.join(db_loc, 'rtm.db')
    	conn = sqlite3.connect(db_path)

    	# read existing accessibilities table from db and append with this data set
    	df = pd.read_sql("select * from accessibilities", conn)
    	df = pd.merge(df, ij_acc, how='left', left_on=['TAZ1741'], right_on = ['i'])
    	df.drop('i', axis=1, inplace=True)

    	# write the data back to database
    	df.to_sql(name='accessibilities', con=conn, flavor='sqlite', index=False, if_exists='replace')
    	conn.close()


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
        length = int(np.sqrt(len(ij['value'])))

        # put back in emmebank with square shape
        util.set_matrix_numpy(eb, matrix, ij['value'].reshape(length,length))



    @_m.logbook_trace("Calculate Densities")
    def calc_density(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        # get data from emmebank
        zones = util.get_matrix_numpy(eb, "mozoneindex")
        totpop = util.get_matrix_numpy(eb, "moTotPop")
        totemp = util.get_matrix_numpy(eb, "moTotEmp")
        combined = totpop + totemp
        area = util.get_matrix_numpy(eb, "moareahc")

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
        util.set_matrix_numpy(eb, 'mopopdens',popdens)
        util.set_matrix_numpy(eb, 'moempdens',empdens)
        util.set_matrix_numpy(eb, 'mocombinedens',combinedens)

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
        # accessibilities
        ########################################################################

        util.initmat(eb, "mo210", "autoAcc", "Auto Accessibility", 0)
        util.initmat(eb, "mo211", "transitAcc", "Transit Accessibility", 0)
        util.initmat(eb, "mo212", "distCbd", "Distance to CBD", 0)
        util.initmat(eb, "mo213", "distTc", "Distance to Town Centre", 0)
        util.initmat(eb, "mo214", "uniAcc", "University Accessibility", 0)

        util.initmat(eb, "mo220", "autoAccLn", "Log Auto Accessibility", 0)
        util.initmat(eb, "mo221", "transitAccLn", "Log Transit Accessibility", 0)
        util.initmat(eb, "mo222", "distCbdLn", "Log Distance to CBD", 0)
        util.initmat(eb, "mo223", "distTcLn", "Log Distance to Town Centre", 0)
        util.initmat(eb, "mo224", "uniAccLn", "Log University Accessibility", 0)


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
        util.initmat(eb, "mf5210", "MdBusIvtt", "Md Bus InVehicle Time", 0)
        util.initmat(eb, "mf5211", "MdBusWait", "Md Bus Waiting Time", 0)
        util.initmat(eb, "mf5212", "MdBusAux", "Md Bus Auxillary Time", 0)
        util.initmat(eb, "mf5213", "MdBusBoard", "Md Bus Boardings", 0)
        util.initmat(eb, "mf5214", "MdBusFare", "Md Bus Fare", 0)

        # PM
        util.initmat(eb, "mf5220", "PmBusIvtt", "Pm Bus InVehicle Time", 0)
        util.initmat(eb, "mf5221", "PmBusWait", "Pm Bus Waiting Time", 0)
        util.initmat(eb, "mf5222", "PmBusAux", "Pm Bus Auxillary Time", 0)
        util.initmat(eb, "mf5223", "PmBusBoard", "Pm Bus Boardings", 0)
        util.initmat(eb, "mf5224", "PmBusFare", "Pm Bus Fare", 0)


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
