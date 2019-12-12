##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage0.data_generate
##--Purpose: Generate Initial Data for RTM Run
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback
import numpy as np
import pandas as pd

class DataGeneration(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)
    run_parking_model = _m.Attribute(bool)

    def __init__(self):
        self.run_parking_model = True


    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Generate Data for Model Run"
        pb.description = "Generate Densities, Initial Skims, data dependant values"
        pb.branding_text = "TransLink"

        with pb.section("Data Generation Options"):
            pb.add_checkbox("run_parking_model", label="Run Parking Model")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            eb = _m.Modeller().emmebank
            eb.matrix("msparkingModel").data = self.run_parking_model

            self.__call__(eb)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Model Data Generation")
    def __call__(self, eb):
        util = _m.Modeller().tool("translink.util")

        model_year = int(util.get_year(eb))

        cyclenum = util.get_cycle(eb)
        if cyclenum == 1:
            self.matrix_batchins(eb)
            self.calc_density(eb)

            am_scen, md_scen, pm_scen = util.get_tod_scenarios(eb)

            # Run iniitial AON assignment to generate a distance skim
            self.assignAON(am_scen)

            # turn off congested/capacited transit during data generation 0 matrix assignment
            # use default bus speed to populate us2
            util.emme_segment_calc(am_scen, "us2", "60*length/speed")
            util.emme_segment_calc(md_scen, "us2", "60*length/speed")
            util.emme_segment_calc(pm_scen, "us2", "60*length/speed")

            util.emme_segment_calc(am_scen, "us3", "us1 + 60 * length / @posted_speed * 1.1 + @signal_delay")
            util.emme_segment_calc(md_scen, "us3", "us1 + 60 * length / @posted_speed * 1.1 + @signal_delay")
            util.emme_segment_calc(pm_scen, "us3", "us1 + 60 * length / @posted_speed * 1.1 + @signal_delay")
            

            transit_assign = _m.Modeller().tool("translink.RTM3.stage3.transitassignment")

            transit_assign(eb, am_scen, md_scen, pm_scen, disable_congestion=True)


        self.calc_all_accessibilities(eb)


        runParking = int(eb.matrix("msparkingModel").data)

        if model_year > 2016 and cyclenum == 1 and runParking == 1:
            self.parking_model(eb)

    @_m.logbook_trace("Calculate Accessibilites")
    def calc_all_accessibilities(self, eb):
        # note transit_uni_accessibility has to run before other accessibilities
        # this is where the data table is started
        self.transit_uni_accessibility(eb)
        self.auto_accessibility(eb)
        self.dist_cbd_tc(eb)



    @_m.logbook_trace("Calculate Minimum Distances to CBD and Towncentre")
    def dist_cbd_tc(self, eb):
    	util = _m.Modeller().tool("translink.util")

    	# acquire cbd and TC dummies
    	sql = """
    	SELECT
    	ti.TAZ1741, IFNULL(du.cbd, 0) as cbd, IFNULL(du.towncentre, 0) as tc
    	FROM taz_index ti
    	LEFT JOIN dummies du on du.TAZ1700 = ti.TAZ1741
    	"""
    	conn = util.get_rtm_db(eb)
    	df = pd.read_sql(sql, conn)
    	conn.close()


    	# get ij matrix and distance skims
    	# currently using non-work
    	# find minimum distance across all times of day
    	ij = util.get_pd_ij_df(eb)

    	ij['dist'] = util.get_matrix_numpy(eb, "mfdistAON").flatten()

    	# join the dummies to the skims
    	ij = pd.merge(ij, df, how='left', left_on=['j'], right_on=['TAZ1741'])


    	# cbd min distance calculation
    	ij_cbd = ij[ij.cbd == 1]
    	ij_cbd = ij_cbd['dist'].groupby(ij_cbd['i'])
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
    	ij_tc = ij_tc['dist'].groupby(ij_tc['i'])
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
    	util.set_matrix_numpy(eb, 'modistCbd', ij_dist['dist_cbd'].values)
    	util.set_matrix_numpy(eb, 'modistCbdLn', ij_dist['dist_cbd_ln'].values)
    	util.set_matrix_numpy(eb, 'modistTc', ij_dist['dist_tc'].values)
    	util.set_matrix_numpy(eb, 'modistTcLn', ij_dist['dist_tc_ln'].values)

    	# write data to sqlite database
    	conn = util.get_rtm_db(eb)

    	# read existing accessibilities table from db and append with this data set
    	df = pd.read_sql("select * from accessibilities", conn)
    	df = pd.merge(df, ij_dist, how='left', left_on=['TAZ1741'], right_on = ['i'])
    	df.drop('i', axis=1, inplace=True)

    	# write the data back to database
    	df.to_sql(name='accessibilities', con=conn, flavor='sqlite', index=False, if_exists='replace')
    	conn.close()

    @_m.logbook_trace("Calculate Transit Accessibility")
    def transit_uni_accessibility(self, eb):
    	util = _m.Modeller().tool("translink.util")

    	# define parameters
    	am_weight = 0.20
    	md_weight = 0.41
    	pm_weight = 0.39
    	time_cut = 60
    	time_cut_uni = 45
        time_cut_soc = 60
        floor = 0.000001

        emp_sql = """
        SELECT
            ti.TAZ1741 as taz
            ,IFNULL(d.EMP_Total, 0) as emp
            ,IFNULL(d.PostSecFTE, 0) as postsec
            ,IFNULL(d.EMP_AccomFood_InfoCult, 0) as emp_soc
        FROM taz_index ti
            LEFT JOIN demographics d on d.TAZ1700 = ti.TAZ1741
        ORDER BY
            ti.TAZ1741
        """

        conn = util.get_rtm_db(eb)
        emp = pd.read_sql(emp_sql, conn)
        conn.close()

    	# create a long matrix of zone interchanges and join employment data to it
    	ij = util.get_pd_ij_df(eb)
    	ij = pd.merge(ij, emp, how='left', left_on = ['j'], right_on = ['taz'])
    	ij['emp'].fillna(0, inplace=True)
    	ij.drop(['taz'], axis=1, inplace=True)


    	# get bus skims
    	AmBusIvtt = util.get_matrix_numpy(eb, 'mfAmBusIvtt').flatten()
    	AmBusWait = util.get_matrix_numpy(eb, 'mfAmBusWait').flatten()
    	AmBusAux = util.get_matrix_numpy(eb, 'mfAmBusAux').flatten()

    	MdBusIvtt = util.get_matrix_numpy(eb, 'mfMdBusIvtt').flatten()
    	MdBusWait = util.get_matrix_numpy(eb, 'mfMdBusWait').flatten()
    	MdBusAux = util.get_matrix_numpy(eb, 'mfMdBusAux').flatten()

    	PmBusIvtt = util.get_matrix_numpy(eb, 'mfPmBusIvtt').flatten()
    	PmBusWait = util.get_matrix_numpy(eb, 'mfPmBusWait').flatten()
    	PmBusAux = util.get_matrix_numpy(eb, 'mfPmBusAux').flatten()

    	# get rail skims
    	AmRailIvtt = util.get_matrix_numpy(eb, 'mfAmRailIvtt').flatten()
    	AmRailIvttBus = util.get_matrix_numpy(eb, 'mfAmRailIvttBus').flatten()
    	AmRailWait = util.get_matrix_numpy(eb, 'mfAmRailWait').flatten()
    	AmRailAux = util.get_matrix_numpy(eb, 'mfAmRailAux').flatten()

    	MdRailIvtt = util.get_matrix_numpy(eb, 'mfMdRailIvtt').flatten()
    	MdRailIvttBus = util.get_matrix_numpy(eb, 'mfMdRailIvttBus').flatten()
    	MdRailWait = util.get_matrix_numpy(eb, 'mfMdRailWait').flatten()
    	MdRailAux = util.get_matrix_numpy(eb, 'mfMdRailAux').flatten()

    	PmRailIvtt = util.get_matrix_numpy(eb, 'mfPmRailIvtt').flatten()
    	PmRailIvttBus = util.get_matrix_numpy(eb, 'mfPmRailIvttBus').flatten()
    	PmRailWait = util.get_matrix_numpy(eb, 'mfPmRailWait').flatten()
    	PmRailAux = util.get_matrix_numpy(eb, 'mfPmRailAux').flatten()

    	# get Wce Skims
    	AmWceIvtt = util.get_matrix_numpy(eb, 'mfAmWceIvtt').flatten()
    	AmWceIvttRail = util.get_matrix_numpy(eb, 'mfAmWceIvttRail').flatten()
    	AmWceIvttBus = util.get_matrix_numpy(eb, 'mfAmWceIvttBus').flatten()
    	AmWceWait = util.get_matrix_numpy(eb, 'mfAmWceWait').flatten()
    	AmWceAux = util.get_matrix_numpy(eb, 'mfAmWceAux').flatten()

    	PmWceIvtt = util.get_matrix_numpy(eb, 'mfPmWceIvtt').flatten()
    	PmWceIvttRail = util.get_matrix_numpy(eb, 'mfPmWceIvttRail').flatten()
    	PmWceIvttBus = util.get_matrix_numpy(eb, 'mfPmWceIvttBus').flatten()
    	PmWceWait = util.get_matrix_numpy(eb, 'mfPmWceWait').flatten()
    	PmWceAux = util.get_matrix_numpy(eb, 'mfPmWceAux').flatten()

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
    	ij['transit_acc'] = np.where(ij['AmTransitTime'].between(floor, time_cut), ij['emp'] * am_weight, 0) \
    	+ np.where(ij['MdTransitTime'].between(floor, time_cut), ij['emp'] * md_weight, 0)  \
    	+ np.where(ij['PmTransitTime'].between(floor, time_cut), ij['emp'] * pm_weight, 0)

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
    	util.set_matrix_numpy(eb, 'motransitAcc', ij_acc['transit_acc'].values)
    	util.set_matrix_numpy(eb, 'motransitAccLn', ij_acc['transit_acc_ln'].values)


    	#######################################################################
    	# Calculate and set university accessibilities
    	#######################################################################

    	# calculate accessibilities
    	ij['uni_acc'] = np.where(ij['MdTransitTime'].between(floor, time_cut_uni), ij['postsec'], 0)

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


    	# write data back to emmebank
    	util.set_matrix_numpy(eb, 'mouniAcc', ij_acc_u['uni_acc'].values)
    	util.set_matrix_numpy(eb, 'mouniAccLn', ij_acc_u['uni_acc_ln'].values)


    	#######################################################################
    	# Calculate and set social accessibilities
    	#######################################################################

    	# calculate weighted accessibilities
    	ij['soc_acc'] = np.where(ij['AmTransitTime'].between(floor, time_cut_soc), ij['emp_soc'] * am_weight, 0) \
    	+ np.where(ij['MdTransitTime'].between(floor, time_cut_soc), ij['emp_soc'] * md_weight, 0)  \
    	+ np.where(ij['PmTransitTime'].between(floor, time_cut_soc), ij['emp_soc'] * pm_weight, 0)

    	#aggregate to the origin zone
    	ij_acc_s = ij['soc_acc'].groupby(ij['i'])
    	ij_acc_s = ij_acc_s.sum()
    	ij_acc_s = ij_acc_s.reset_index()

    	# log transform, floor output at 0
    	if ij_acc_s['soc_acc'].min() < 1:
    		log_trans_const = 1 - ij_acc_s['soc_acc'].min()
    	else:
    		log_trans_const = 0

    	ij_acc_s['soc_acc_ln'] = np.log(ij_acc_s['soc_acc'] + log_trans_const)

    	# write data back to emmebank
    	util.set_matrix_numpy(eb, 'mosocAcc', ij_acc_s['soc_acc'].values)
    	util.set_matrix_numpy(eb, 'mosocAccLn', ij_acc_s['soc_acc_ln'].values)

    	#######################################################################
    	# Write everything to sqlite database
    	#######################################################################

    	# create index column for table.  name denotes full index
    	ij_acc.rename(columns={'i' : 'TAZ1741'}, inplace=True)
    	# merge accessibility dataframes and drop addition taz column (i)
    	ij_acc = pd.merge(ij_acc, ij_acc_u, how='left', left_on=['TAZ1741'], right_on=['i'])
    	ij_acc.drop('i', axis=1, inplace=True)
    	# merge accessibility dataframes and drop addition taz column (i)
    	ij_acc = pd.merge(ij_acc, ij_acc_s, how='left', left_on=['TAZ1741'], right_on=['i'])
    	ij_acc.drop('i', axis=1, inplace=True)

    	# establish connection to db and write out data
    	# note, this table is created in transit accessibilities method and expanded with the methods
    	conn = util.get_rtm_db(eb)
    	ij_acc.to_sql(name='accessibilities', con=conn, flavor='sqlite', index=False, if_exists='replace')
    	conn.close()

    @_m.logbook_trace("Calculate Auto Accessibility")
    def auto_accessibility(self, eb):
    	util = _m.Modeller().tool("translink.util")

    	# define parameters
    	am_weight = 0.29
    	md_weight = 0.45
    	pm_weight = 0.26
    	time_cut = 30

    	mat_am = "mfAmSovTimeVOT2"
    	mat_md = "mfMdSovTimeVOT2"
    	mat_pm = "mfPmSovTimeVOT2"

        emp_sql = """
        SELECT
            ti.TAZ1741 as taz
            ,IFNULL(d.EMP_Total, 0) as emp
        FROM taz_index ti
            LEFT JOIN demographics d on d.TAZ1700 = ti.TAZ1741
        ORDER BY
            ti.TAZ1741
        """

        conn = util.get_rtm_db(eb)
        emp = pd.read_sql(emp_sql, conn)
        conn.close()

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
    	util.set_matrix_numpy(eb, 'moautoAcc', ij_acc['auto_acc'].values)
    	util.set_matrix_numpy(eb, 'moautoAccLn', ij_acc['auto_acc_ln'].values)


    	#######################################################################
    	# Write everything to sqlite database
    	#######################################################################

    	# establish connection to db and write out data
    	# note, this table is created in transit accessibilities method and expanded with the other accessibilities methods
    	conn = util.get_rtm_db(eb)

    	# read existing accessibilities table from db and append with this data set
    	df = pd.read_sql("select * from accessibilities", conn)
    	df = pd.merge(df, ij_acc, how='left', left_on=['TAZ1741'], right_on = ['i'])
    	df.drop('i', axis=1, inplace=True)

    	# write the data back to database
    	df.to_sql(name='accessibilities', con=conn, flavor='sqlite', index=False, if_exists='replace')
    	conn.close()

    @_m.logbook_trace("Calculate Densities")
    def calc_density(self, eb):
        util = _m.Modeller().tool("translink.util")

        # get data from emmebank
        zones = util.get_matrix_numpy(eb, "mozoneindex", reshape=False)
        totpop = util.get_matrix_numpy(eb, "moTotPop", reshape=False)
        totemp = util.get_matrix_numpy(eb, "moTotEmp", reshape=False)
        combined = totpop + totemp
        area = util.get_matrix_numpy(eb, "moareahc", reshape=False)

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

    	# create log transformed variables
    	if popdens.min() < 1:
    		log_trans_const = 1 - popdens.min()
    	else:
    		log_trans_const = 0
    	popdensln = np.log(popdens + log_trans_const)

    	if empdens.min() < 1:
    		log_trans_const = 1 - empdens.min()
    	else:
    		log_trans_const = 0
    	empdensln = np.log(empdens + log_trans_const)

    	if combinedens.min() < 1:
    		log_trans_const = 1 - combinedens.min()
    	else:
    		log_trans_const = 0
    	combinedensln = np.log(combinedens + log_trans_const)


        # write data to emmebank
        util.set_matrix_numpy(eb, 'mopopdens',popdens)
        util.set_matrix_numpy(eb, 'moempdens',empdens)
        util.set_matrix_numpy(eb, 'mocombinedens',combinedens)

        util.set_matrix_numpy(eb, 'mopopdensln',popdensln)
        util.set_matrix_numpy(eb, 'moempdensln',empdensln)
        util.set_matrix_numpy(eb, 'mocombinedensln',combinedensln)

        # create pandas df to build sqilite table
        df = pd.DataFrame({'TAZ1700': zones,
               'popdens': popdens,
               'empdens': empdens,
               'combinedens' : combinedens,
               'popdensln': popdensln,
               'empdensln': empdensln,
               'combinedensln' : combinedensln },
               columns=['TAZ1700','popdens','empdens','combinedens', 'popdensln','empdensln','combinedensln'])

        # write data to rtm sqlite database
        conn = util.get_rtm_db(eb)
        df.to_sql(name='densities', con=conn, flavor='sqlite', index=False, if_exists='replace')
        conn.close()

    @_m.logbook_trace("Update Parking Rates")
    def parking_model(self, eb):
        """ logit model determines free/paid parking zones
        linear model determines price for paid parking zones
        """
        util = _m.Modeller().tool("translink.util")

        # 2hr logit model
        cl2_intercept = -1.072431
        cl2_empdensln = 0.936057
        cl2_distCbdln = -2.004142
        cl2_d_tc = 1.990859
        cl2_d_rail = 2.464337
        cl2_poi = 5.146076
        cl2_d_dtes = -1.827173
        # 8hr logit model
        cl8_intercept = -3.651998
        cl8_empdensln = 1.196587
        cl8_distCbdln = -1.237187
        cl8_d_rail = 2.405598
        cl8_d_hospital = 2.595522
        cl8_d_uni_all = 5.820835
        cl8_d_tc = 0.88389
        cl8_d_dtes = -1.39608
        # 2hr lm
        cr2_intercept = 1.816834
        cr2_empdens = 0.000493
        cr2_distCbdln = -0.13643
        cr2_poi = 0.246914
        # 8hr lm
        cr8_intercept = 2.004248
        cr8_empdens = 0.000301
        cr8_distCbdln = -0.117159
        cr8_poi = 0.122456

        sql = """
        SELECT
            ti.TAZ1741
            ,IFNULL(dn.empdensln,0) as empdensLn
            ,IFNULL(dn.empdens, 0) as empdens
            ,IFNULL(a.dist_cbd_ln, 0) as distCbdLn
            ,IFNULL(du.towncentre,0) as d_tc
            ,IFNULL(g.rail_stn_dummy,0) as d_railStn
            ,IFNULL(du.airport, 0) as d_air
            ,IFNULL(du.dtes,0) as d_dtes
            ,IFNULL(du.ferry,0) as d_ferry
            ,IFNULL(du.hospital,0) as d_hospital
            ,CASE WHEN IFNULL(dg.PostSecFTE,0) > 1000 THEN 1
                  WHEN IFNULL(du.ubc, 0) > 0 THEN 1
                  WHEN IFNULL(du.sfu, 0) > 0 THEN 1
                  ELSE 0
                  END d_uniAll
            ,CASE WHEN IFNULL(g.parking_two_hr_rate, 0) > 0 THEN 1 ELSE 0 END paid2hr
            ,CASE WHEN IFNULL(g.parking_eight_hr_rate, 0) > 0 THEN 1 ELSE 0 END paid8hr
            ,IFNULL(g.parking_two_hr_rate, 0)  park2hrRate
            ,IFNULL(g.parking_eight_hr_rate, 0) park8hrRate

        FROM taz_index ti
            LEFT JOIN densities dn on dn.TAZ1700 = ti.TAZ1741
            LEFT JOIN accessibilities a on a.TAZ1741 = ti.TAZ1741
            LEFT JOIN dummies du on du.TAZ1700 = ti.TAZ1741
            LEFT JOIN demographics dg on dg.TAZ1700 = ti.TAZ1741
            LEFT JOIN geographics g on g.TAZ1700 = ti.TAZ1741

        """
        conn = util.get_rtm_db(eb)
        df = pd.read_sql(sql, conn)

        # poi = 'points of interest'
        df['poi'] = df[['d_uniAll','d_ferry','d_hospital','d_air']].max(axis = 1)

        # classify 2hr paid/free parking
        df['uF2hr'] = 0
        df['uP2hr'] = ( cl2_intercept
                       + cl2_empdensln * df['empdensLn']
                       + cl2_distCbdln * df['distCbdLn']
                       + cl2_d_tc * df['d_tc']
                       + cl2_d_rail * df['d_railStn']
                       + cl2_poi * df['poi']
                       + cl2_d_dtes * df['d_dtes'])

        # denominator
        df['d2hr'] = np.exp(df['uF2hr']) + np.exp(df['uP2hr'])
        # prob 2 hr paid - free not needed
        df['pP2hr'] = np.exp(df['uP2hr']) / df['d2hr']
        # classify by most likely
        df['paid2hrMod'] = np.where(df['pP2hr'] >= 0.5, 1, 0)
        # ensure previously paid zones remain paid
        df['paid2hrFin'] = df[['paid2hr','paid2hrMod']].max(axis=1)


        # 8hr logit model
        df['uF8hr'] = 0
        df['uP8hr'] = ( cl8_intercept
                      + cl8_empdensln * df['empdensLn']
                      + cl8_distCbdln * df['distCbdLn']
                      + cl8_d_rail * df['d_railStn']
                      + cl8_d_hospital * df['d_hospital']
                      + cl8_d_uni_all * df['d_uniAll']
                      + cl8_d_tc * df['d_tc']
                      + cl8_d_dtes * df['d_dtes'] )
        # denominator
        df['d8hr'] = np.exp(df['uF8hr']) + np.exp(df['uP8hr'])
        # prob 8 hr paid - free not needed
        df['pP8hr'] = np.exp(df['uP8hr']) / df['d8hr']
        # classify by most likely
        df['paid8hrMod'] = np.where(df['pP8hr'] >= 0.5, 1, 0)
        # ensure previously paid zones remain paid
        df['paid8hrFin'] = df[['paid8hr','paid8hrMod']].max(axis=1)

        # 2hr lm
        df['prk2hrRatePred'] = np.exp(  cr2_intercept
                                      + cr2_empdens * df['empdens']
                                      + cr2_distCbdln * df['distCbdLn']
                                      + cr2_poi * df['poi'] )

        # remove parking rates from free zones
        df['prk2hrRatePred'] = df['prk2hrRatePred'] * df['paid2hrFin']
        # floor prediction at observed rate
        df['prk2hrRateFin'] = df[['park2hrRate','prk2hrRatePred']].max(axis=1)

        # 8hr lm
        df['prk8hrRatePred'] = np.exp(  cr8_intercept
                                      + cr8_empdens * df['empdens']
                                      + cr8_distCbdln * df['distCbdLn']
                                      + cr8_poi * df['poi'] )

        # remove parking rates from free zones
        df['prk8hrRatePred'] = df['prk8hrRatePred'] * df['paid8hrFin']
        # floor prediction at observed rate
        df['prk8hrRateFin'] = df[['park8hrRate','prk8hrRatePred']].max(axis=1)

        # update emmebank parking values
        util.set_matrix_numpy(eb, 'moprk2hr', df['prk2hrRateFin'].values)
        util.set_matrix_numpy(eb, 'moprk8hr', df['prk8hrRateFin'].values)

        # update rtm.db
        df = df[['TAZ1741','prk2hrRateFin','prk8hrRateFin']]
        geo = pd.read_sql("SELECT * FROM geographics", conn)
        df = pd.merge(geo, df, how='inner', left_on = ['TAZ1700'], right_on = ['TAZ1741'])
        df = df[['TAZ1700','Hectares','prk2hrRateFin','prk8hrRateFin','rail_stn_dummy','car_share_250m','car_share_500m','bike_score_taz']]
        df.rename(columns={'prk2hrRateFin': 'parking_two_hr_rate', 'prk8hrRateFin': 'parking_eight_hr_rate'}, inplace=True)
        df.to_sql(name='geographics', con=conn, flavor='sqlite', index=False, if_exists='replace')
        conn.close()


    @_m.logbook_trace("All or nothing distance assignment")
    def assignAON(self, sc):
        util = _m.Modeller().tool("translink.util")
        eb = sc.emmebank
        # calculate fixed link opcosts based on SOV travel



        auto_voc = eb.matrix("msautoOpCost").data
        util.emme_link_calc(sc, "@sovoc", "length * %s" % (auto_voc))
        util.initmat(eb, "mf10", "seedSovAm", "AM SOV seed demand", 1)
        util.initmat(eb, "mf91", "distAON", "All or nothing initial distance skim", 0)
        class_spec = []
        class_spec.append({"mode": "d",
                "demand": "mf10",
                "generalized_cost": { "link_costs": "@sovoc", "perception_factor": eb.matrix("msAutoVOT3").data },
                "results": { "od_travel_times": {"shortest_paths": None},
                             "link_volumes": None,
                             "turn_volumes": None },
                "analysis": {"results": {"od_values": "mfdistAON"}},
                "path_analysis": {"link_component": "length",
                                  "operator": "+",
                                  "path_to_od_composition": { "considered_paths": "ALL", "multiply_path_proportions_by": { "analyzed_demand": False, "path_value": True }},
                                  "selection_threshold": {"lower": 0.00, "upper": 99999} }
                })

        assign_traffic = _m.Modeller().tool("inro.emme.traffic_assignment.sola_traffic_assignment")
        spec = {
            "type": "SOLA_TRAFFIC_ASSIGNMENT",
            "background_traffic": {"add_transit_vehicles": True},
            "classes": class_spec,
            "stopping_criteria": { "max_iterations"   : 0,
                                   "relative_gap"     : 0,
                                   "best_relative_gap": 0,
                                   "normalized_gap"   : 0},
            "performance_settings": {"number_of_processors": int(eb.matrix("ms12").data)},
        }
        assign_traffic(spec, scenario=sc)

        # Calculate Intrazonal distance
        np_mat = util.get_matrix_numpy(eb, "mfdistAON")

        # calculate the mimimum non-zero value in each row and set half that
        # as the intrazonal value
        for i in xrange(np_mat.shape[0]):
            np_mat[i][i] = np_mat[i][np_mat[i] > 0].min() * 0.5

        # write the updated matrix back to the emmebank
        util.set_matrix_numpy(eb, "mfdistAON", np_mat)
        util.delmat(eb, 'mf10')

    @_m.logbook_trace("Initial Demand and Skim Matrix Creation")
    def matrix_batchins(self, eb):
        util = _m.Modeller().tool("translink.util")

        ########################################################################
        # densities
        ########################################################################

        util.initmat(eb, "mo200", "popdens", "Population density (per/hec)", 0)
        util.initmat(eb, "mo201", "empdens", "Employment density (job/hec)", 0)
        util.initmat(eb, "mo202", "combinedens", "Pop + Emp density (per hec)", 0)

        util.initmat(eb, "mo205", "popdensln", "Log Population density (per/hec)", 0)
        util.initmat(eb, "mo206", "empdensln", "Log Employment density (job/hec)", 0)
        util.initmat(eb, "mo207", "combinedensln", "Log Pop + Emp density (per hec)", 0)


        ########################################################################
        # accessibilities
        ########################################################################

        util.initmat(eb, "mo210", "autoAcc", "Auto Accessibility", 0)
        util.initmat(eb, "mo211", "transitAcc", "Transit Accessibility", 0)
        util.initmat(eb, "mo212", "distCbd", "Distance to CBD", 0)
        util.initmat(eb, "mo213", "distTc", "Distance to Town Centre", 0)
        util.initmat(eb, "mo214", "uniAcc", "University Accessibility", 0)
        util.initmat(eb, "mo215", "socAcc", "Social Recreational Accessibility", 0)

        util.initmat(eb, "mo220", "autoAccLn", "Log Auto Accessibility", 0)
        util.initmat(eb, "mo221", "transitAccLn", "Log Transit Accessibility", 0)
        util.initmat(eb, "mo222", "distCbdLn", "Log Distance to CBD", 0)
        util.initmat(eb, "mo223", "distTcLn", "Log Distance to Town Centre", 0)
        util.initmat(eb, "mo224", "uniAccLn", "Log University Accessibility", 0)
        util.initmat(eb, "mo225", "socAccLn", "Log Social Recreational Accessibility", 0)
