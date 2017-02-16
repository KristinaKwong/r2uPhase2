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
        util = _m.Modeller().tool("translink.util")

        cyclenum = util.get_cycle(eb)
        if cyclenum == 1:
            self.matrix_batchins(eb)
            self.calc_density(eb)

            am_scen = eb.scenario(int(eb.matrix("ms2").data))
            md_scen = eb.scenario(int(eb.matrix("ms3").data))
            pm_scen = eb.scenario(int(eb.matrix("ms4").data))

            # Run iniitial AON assignment to generate a distance skim
            self.assignAON(am_scen)

            # Run Initial Assignment to generate skims from seed demands
            auto_assign = _m.Modeller().tool("translink.RTM3.stage3.autoassignment")
            auto_assign(am_scen, md_scen, pm_scen)

            transit_assign = _m.Modeller().tool("translink.RTM3.stage3.transitassignment")
            transit_assign(eb, am_scen, md_scen, pm_scen)

        self.calc_all_accessibilities(eb)



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


    @_m.logbook_trace("All or nothing distance assignment")
    def assignAON(self, sc):
        util = _m.Modeller().tool("translink.util")
        eb = sc.emmebank
        # calculate fixed link opcosts based on SOV travel
        auto_voc = eb.matrix("msautoOpCost").data
        util.emme_link_calc(sc, "@sovoc", "length * %s" % (auto_voc))
        util.initmat(eb, "mf91", "distAON", "All or nothing initial distance skim", )
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


        ########################################################################
        # demand matrices
        ########################################################################

        # AM
        util.initmat(eb, "mf300", "SOV_drvtrp_VOT_1_Am", "SOV drv-trips VOT 1 AM", 0)
        util.initmat(eb, "mf301", "SOV_drvtrp_VOT_2_Am", "SOV drv-trips VOT 2 AM", 0)
        util.initmat(eb, "mf302", "SOV_drvtrp_VOT_3_Am", "SOV drv-trips VOT 3 AM", 0)
        util.initmat(eb, "mf303", "SOV_drvtrp_VOT_4_Am", "SOV drv-trips VOT 4 AM", 0)
        util.initmat(eb, "mf306", "HOV_drvtrp_VOT_1_Am", "HOV drv-trips VOT 1 AM", 0)
        util.initmat(eb, "mf307", "HOV_drvtrp_VOT_2_Am", "HOV drv-trips VOT 2 AM", 0)
        util.initmat(eb, "mf308", "HOV_drvtrp_VOT_3_Am", "HOV drv-trips VOT 3 AM", 0)
        util.initmat(eb, "mf309", "HOV_drvtrp_VOT_4_Am", "HOV drv-trips VOT 4 AM", 0)
        util.initmat(eb, "mf312", "lgvPceAm", "light trucks PCE AM", 0)
        util.initmat(eb, "mf313", "hgvPceAm", "heavy trucks PCE AM", 0)
        #TODO: this should initialize the person trips matrices for assignment instead
        # MD
        util.initmat(eb, "mf320", "SOV_drvtrp_VOT_1_Md", "SOV drv-trips VOT 1 MD", 0)
        util.initmat(eb, "mf321", "SOV_drvtrp_VOT_2_Md", "SOV drv-trips VOT 2 MD", 0)
        util.initmat(eb, "mf322", "SOV_drvtrp_VOT_3_Md", "SOV drv-trips VOT 3 MD", 0)
        util.initmat(eb, "mf323", "SOV_drvtrp_VOT_4_Md", "SOV drv-trips VOT 4 MD", 0)
        util.initmat(eb, "mf326", "HOV_drvtrp_VOT_1_Md", "HOV drv-trips VOT 1 MD", 0)
        util.initmat(eb, "mf327", "HOV_drvtrp_VOT_2_Md", "HOV drv-trips VOT 2 MD", 0)
        util.initmat(eb, "mf328", "HOV_drvtrp_VOT_3_Md", "HOV drv-trips VOT 3 MD", 0)
        util.initmat(eb, "mf329", "HOV_drvtrp_VOT_4_Md", "HOV drv-trips VOT 4 MD", 0)
        util.initmat(eb, "mf332", "lgvPceMd", "light trucks PCE MD", 0)
        util.initmat(eb, "mf333", "hgvPceMd", "heavy trucks PCE MD", 0)
        #TODO: this should initialize the person trips matrices for assignment instead

        # PM
        util.initmat(eb, "mf340", "SOV_drvtrp_VOT_1_Pm", "SOV drv-trips VOT 1 PM", 0)
        util.initmat(eb, "mf341", "SOV_drvtrp_VOT_2_Pm", "SOV drv-trips VOT 2 PM", 0)
        util.initmat(eb, "mf342", "SOV_drvtrp_VOT_3_Pm", "SOV drv-trips VOT 3 PM", 0)
        util.initmat(eb, "mf343", "SOV_drvtrp_VOT_4_Pm", "SOV drv-trips VOT 4 PM", 0)
        util.initmat(eb, "mf346", "HOV_drvtrp_VOT_1_Pm", "HOV drv-trips VOT 1 PM", 0)
        util.initmat(eb, "mf347", "HOV_drvtrp_VOT_2_Pm", "HOV drv-trips VOT 2 PM", 0)
        util.initmat(eb, "mf348", "HOV_drvtrp_VOT_3_Pm", "HOV drv-trips VOT 3 PM", 0)
        util.initmat(eb, "mf349", "HOV_drvtrp_VOT_4_Pm", "HOV drv-trips VOT 4 PM", 0)
        util.initmat(eb, "mf352", "lgvPcePm", "light trucks PCE PM", 0)
        util.initmat(eb, "mf353", "hgvPcePm", "heavy trucks PCE PM", 0)
        #TODO: this should initialize the person trips matrices for assignment instead

        # Move seed demand into Work SOV/HOV Medium Income for AM/MD/PM
        specs = []
        specs.append(util.matrix_spec("mf301", "mf10"))
        specs.append(util.matrix_spec("mf307", "mf11"))
        specs.append(util.matrix_spec("mf312", "mf20*lgvPCE"))
        specs.append(util.matrix_spec("mf313", "mf21*hgvPCE"))
        specs.append(util.matrix_spec("mf321", "mf30"))
        specs.append(util.matrix_spec("mf327", "mf31"))
        specs.append(util.matrix_spec("mf332", "mf40*lgvPCE"))
        specs.append(util.matrix_spec("mf333", "mf41*hgvPCE"))
        specs.append(util.matrix_spec("mf341", "mf50"))
        specs.append(util.matrix_spec("mf347", "mf51"))
        specs.append(util.matrix_spec("mf352", "mf60*lgvPCE"))
        specs.append(util.matrix_spec("mf353", "mf61*hgvPCE"))
        util.compute_matrix(specs)

        ########################################################################
        # skim matrices
        ########################################################################

        #####################
        # Auto
        #####################
        # AM
        util.initmat(eb, "mf5000", "AmSovOpCstVOT1", "Am Sov VOT1 Op Cost", 0)
        util.initmat(eb, "mf5001", "AmSovTimeVOT1", "Am Sov VOT1 Time", 0)
        util.initmat(eb, "mf5002", "AmSovTollVOT1", "Am Sov VOT1 Toll", 0)
        util.initmat(eb, "mf5003", "AmSovOpCstVOT2", "Am Sov VOT2 Op Cost", 0)
        util.initmat(eb, "mf5004", "AmSovTimeVOT2", "Am Sov VOT2 Time", 0)
        util.initmat(eb, "mf5005", "AmSovTollVOT2", "Am Sov VOT2 Toll", 0)
        util.initmat(eb, "mf5006", "AmSovOpCstVOT3", "Am Sov VOT3 Op Cost", 0)
        util.initmat(eb, "mf5007", "AmSovTimeVOT3", "Am Sov VOT3 Time", 0)
        util.initmat(eb, "mf5008", "AmSovTollVOT3", "Am Sov VOT3 Toll", 0)
        util.initmat(eb, "mf5009", "AmSovOpCstVOT4", "Am Sov VOT4 Op Cost", 0)
        util.initmat(eb, "mf5010", "AmSovTimeVOT4", "Am Sov VOT4 Time", 0)
        util.initmat(eb, "mf5011", "AmSovTollVOT4", "Am Sov VOT4 Toll", 0)
        util.initmat(eb, "mf5012", "AmHovOpCstVOT1", "Am Hov VOT1 Op Cost", 0)
        util.initmat(eb, "mf5013", "AmHovTimeVOT1", "Am Hov VOT1 Time", 0)
        util.initmat(eb, "mf5014", "AmHovTollVOT1", "Am Hov VOT1 Toll", 0)
        util.initmat(eb, "mf5015", "AmHovOpCstVOT2", "Am Hov VOT2 Op Cost", 0)
        util.initmat(eb, "mf5016", "AmHovTimeVOT2", "Am Hov VOT2 Time", 0)
        util.initmat(eb, "mf5017", "AmHovTollVOT2", "Am Hov VOT2 Toll", 0)
        util.initmat(eb, "mf5018", "AmHovOpCstVOT3", "Am Hov VOT3 Op Cost", 0)
        util.initmat(eb, "mf5019", "AmHovTimeVOT3", "Am Hov VOT3 Time", 0)
        util.initmat(eb, "mf5020", "AmHovTollVOT3", "Am Hov VOT3 Toll", 0)
        util.initmat(eb, "mf5021", "AmHovOpCstVOT4", "Am Hov VOT4 Op Cost", 0)
        util.initmat(eb, "mf5022", "AmHovTimeVOT4", "Am Hov VOT4 Time", 0)
        util.initmat(eb, "mf5023", "AmHovTollVOT4", "Am Hov VOT4 Toll", 0)
        util.initmat(eb, "mf5024", "AmLgvOpCst", "Am LGV Op Cost", 0)
        util.initmat(eb, "mf5025", "AmLgvTime", "Am LGV Time", 0)
        util.initmat(eb, "mf5026", "AmLgvToll", "Am LGV Toll", 0)
        util.initmat(eb, "mf5027", "AmHgvOpCst", "Am HGV Op Cost", 0)
        util.initmat(eb, "mf5028", "AmHgvTime", "Am HGV Time", 0)
        util.initmat(eb, "mf5029", "AmHgvToll", "Am HGV Toll", 0)
        # MD
        util.initmat(eb, "mf5030", "MdSovOpCstVOT1", "Md Sov VOT1 Op Cost", 0)
        util.initmat(eb, "mf5031", "MdSovTimeVOT1", "Md Sov VOT1 Time", 0)
        util.initmat(eb, "mf5032", "MdSovTollVOT1", "Md Sov VOT1 Toll", 0)
        util.initmat(eb, "mf5033", "MdSovOpCstVOT2", "Md Sov VOT2 Op Cost", 0)
        util.initmat(eb, "mf5034", "MdSovTimeVOT2", "Md Sov VOT2 Time", 0)
        util.initmat(eb, "mf5035", "MdSovTollVOT2", "Md Sov VOT2 Toll", 0)
        util.initmat(eb, "mf5036", "MdSovOpCstVOT3", "Md Sov VOT3 Op Cost", 0)
        util.initmat(eb, "mf5037", "MdSovTimeVOT3", "Md Sov VOT3 Time", 0)
        util.initmat(eb, "mf5038", "MdSovTollVOT3", "Md Sov VOT3 Toll", 0)
        util.initmat(eb, "mf5039", "MdSovOpCstVOT4", "Md Sov VOT4 Op Cost", 0)
        util.initmat(eb, "mf5040", "MdSovTimeVOT4", "Md Sov VOT4 Time", 0)
        util.initmat(eb, "mf5041", "MdSovTollVOT4", "Md Sov VOT4 Toll", 0)
        util.initmat(eb, "mf5042", "MdHovOpCstVOT1", "Md Hov VOT1 Op Cost", 0)
        util.initmat(eb, "mf5043", "MdHovTimeVOT1", "Md Hov VOT1 Time", 0)
        util.initmat(eb, "mf5044", "MdHovTollVOT1", "Md Hov VOT1 Toll", 0)
        util.initmat(eb, "mf5045", "MdHovOpCstVOT2", "Md Hov VOT2 Op Cost", 0)
        util.initmat(eb, "mf5046", "MdHovTimeVOT2", "Md Hov VOT2 Time", 0)
        util.initmat(eb, "mf5047", "MdHovTollVOT2", "Md Hov VOT2 Toll", 0)
        util.initmat(eb, "mf5048", "MdHovOpCstVOT3", "Md Hov VOT3 Op Cost", 0)
        util.initmat(eb, "mf5049", "MdHovTimeVOT3", "Md Hov VOT3 Time", 0)
        util.initmat(eb, "mf5050", "MdHovTollVOT3", "Md Hov VOT3 Toll", 0)
        util.initmat(eb, "mf5051", "MdHovOpCstVOT4", "Md Hov VOT4 Op Cost", 0)
        util.initmat(eb, "mf5052", "MdHovTimeVOT4", "Md Hov VOT4 Time", 0)
        util.initmat(eb, "mf5053", "MdHovTollVOT4", "Md Hov VOT4 Toll", 0)
        util.initmat(eb, "mf5054", "MdLgvOpCst", "Md LGV Op Cost", 0)
        util.initmat(eb, "mf5055", "MdLgvTime", "Md LGV Time", 0)
        util.initmat(eb, "mf5056", "MdLgvToll", "Md LGV Toll", 0)
        util.initmat(eb, "mf5057", "MdHgvOpCst", "Md HGV Op Cost", 0)
        util.initmat(eb, "mf5058", "MdHgvTime", "Md HGV Time", 0)
        util.initmat(eb, "mf5059", "MdHgvToll", "Md HGV Toll", 0)
        # PM
        util.initmat(eb, "mf5060", "PmSovOpCstVOT1", "Pm Sov VOT1 Op Cost", 0)
        util.initmat(eb, "mf5061", "PmSovTimeVOT1", "Pm Sov VOT1 Time", 0)
        util.initmat(eb, "mf5062", "PmSovTollVOT1", "Pm Sov VOT1 Toll", 0)
        util.initmat(eb, "mf5063", "PmSovOpCstVOT2", "Pm Sov VOT2 Op Cost", 0)
        util.initmat(eb, "mf5064", "PmSovTimeVOT2", "Pm Sov VOT2 Time", 0)
        util.initmat(eb, "mf5065", "PmSovTollVOT2", "Pm Sov VOT2 Toll", 0)
        util.initmat(eb, "mf5066", "PmSovOpCstVOT3", "Pm Sov VOT3 Op Cost", 0)
        util.initmat(eb, "mf5067", "PmSovTimeVOT3", "Pm Sov VOT3 Time", 0)
        util.initmat(eb, "mf5068", "PmSovTollVOT3", "Pm Sov VOT3 Toll", 0)
        util.initmat(eb, "mf5069", "PmSovOpCstVOT4", "Pm Sov VOT4 Op Cost", 0)
        util.initmat(eb, "mf5070", "PmSovTimeVOT4", "Pm Sov VOT4 Time", 0)
        util.initmat(eb, "mf5071", "PmSovTollVOT4", "Pm Sov VOT4 Toll", 0)
        util.initmat(eb, "mf5072", "PmHovOpCstVOT1", "Pm Hov VOT1 Op Cost", 0)
        util.initmat(eb, "mf5073", "PmHovTimeVOT1", "Pm Hov VOT1 Time", 0)
        util.initmat(eb, "mf5074", "PmHovTollVOT1", "Pm Hov VOT1 Toll", 0)
        util.initmat(eb, "mf5075", "PmHovOpCstVOT2", "Pm Hov VOT2 Op Cost", 0)
        util.initmat(eb, "mf5076", "PmHovTimeVOT2", "Pm Hov VOT2 Time", 0)
        util.initmat(eb, "mf5077", "PmHovTollVOT2", "Pm Hov VOT2 Toll", 0)
        util.initmat(eb, "mf5078", "PmHovOpCstVOT3", "Pm Hov VOT3 Op Cost", 0)
        util.initmat(eb, "mf5079", "PmHovTimeVOT3", "Pm Hov VOT3 Time", 0)
        util.initmat(eb, "mf5080", "PmHovTollVOT3", "Pm Hov VOT3 Toll", 0)
        util.initmat(eb, "mf5081", "PmHovOpCstVOT4", "Pm Hov VOT4 Op Cost", 0)
        util.initmat(eb, "mf5082", "PmHovTimeVOT4", "Pm Hov VOT4 Time", 0)
        util.initmat(eb, "mf5083", "PmHovTollVOT4", "Pm Hov VOT4 Toll", 0)
        util.initmat(eb, "mf5084", "PmLgvOpCst", "Pm LGV Op Cost", 0)
        util.initmat(eb, "mf5085", "PmLgvTime", "Pm LGV Time", 0)
        util.initmat(eb, "mf5086", "PmLgvToll", "Pm LGV Toll", 0)
        util.initmat(eb, "mf5087", "PmHgvOpCst", "Pm HGV Op Cost", 0)
        util.initmat(eb, "mf5088", "PmHgvTime", "Pm HGV Time", 0)
        util.initmat(eb, "mf5089", "PmHgvToll", "Pm HGV Toll", 0)

        #####################
        # Bus
        #####################
        # AM
        util.initmat(eb, "mf5300", "AmBusIvtt", "Am Bus InVehicle Time", 0)
        util.initmat(eb, "mf5301", "AmBusWait", "Am Bus Waiting Time", 0)
        util.initmat(eb, "mf5302", "AmBusAux", "Am Bus Auxillary Time", 0)
        util.initmat(eb, "mf5303", "AmBusBoard", "Am Bus Boardings", 0)
        util.initmat(eb, "mf5304", "AmBusFare", "Am Bus Fare", 0)
        # MD
        util.initmat(eb, "mf5310", "MdBusIvtt", "Md Bus InVehicle Time", 0)
        util.initmat(eb, "mf5311", "MdBusWait", "Md Bus Waiting Time", 0)
        util.initmat(eb, "mf5312", "MdBusAux", "Md Bus Auxillary Time", 0)
        util.initmat(eb, "mf5313", "MdBusBoard", "Md Bus Boardings", 0)
        util.initmat(eb, "mf5314", "MdBusFare", "Md Bus Fare", 0)
        # PM
        util.initmat(eb, "mf5320", "PmBusIvtt", "Pm Bus InVehicle Time", 0)
        util.initmat(eb, "mf5321", "PmBusWait", "Pm Bus Waiting Time", 0)
        util.initmat(eb, "mf5322", "PmBusAux", "Pm Bus Auxillary Time", 0)
        util.initmat(eb, "mf5323", "PmBusBoard", "Pm Bus Boardings", 0)
        util.initmat(eb, "mf5324", "PmBusFare", "Pm Bus Fare", 0)

        #####################
        # Rail
        #####################
        # AM
        util.initmat(eb, "mf5500", "AmRailIvtt", "Am Rail Invehicle Time", 0)
        util.initmat(eb, "mf5501", "AmRailIvttBus", "Am Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5502", "AmRailWait", "Am Rail Waiting Time", 0)
        util.initmat(eb, "mf5503", "AmRailAux", "Am Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5504", "AmRailBoard", "Am Rail Boardings", 0)
        util.initmat(eb, "mf5505", "AmRailFare", "Am Rail Fare", 0)
        # MD
        util.initmat(eb, "mf5510", "MdRailIvtt", "Md Rail Invehicle Time", 0)
        util.initmat(eb, "mf5511", "MdRailIvttBus", "Md Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5512", "MdRailWait", "Md Rail Waiting Time", 0)
        util.initmat(eb, "mf5513", "MdRailAux", "Md Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5514", "MdRailBoard", "Md Rail Boardings", 0)
        util.initmat(eb, "mf5515", "MdRailFare", "Md Rail Fare", 0)
        # PM
        util.initmat(eb, "mf5520", "PmRailIvtt", "Pm Rail Invehicle Time", 0)
        util.initmat(eb, "mf5521", "PmRailIvttBus", "Pm Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5522", "PmRailWait", "Pm Rail Waiting Time", 0)
        util.initmat(eb, "mf5523", "PmRailAux", "Pm Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5524", "PmRailBoard", "Pm Rail Boardings", 0)
        util.initmat(eb, "mf5525", "PmRailFare", "Pm Rail Fare", 0)

        #####################
        # WCE
        #####################
        # AM
        util.initmat(eb, "mf5700", "AmWceIvtt", "Am Rail Invehicle Time", 0)
        util.initmat(eb, "mf5701", "AmWceIvttRail", "Am Rail Invehicle Time on Rail", 0)
        util.initmat(eb, "mf5702", "AmWceIvttBus", "Am Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5703", "AmWceWait", "Am Rail Waiting Time", 0)
        util.initmat(eb, "mf5704", "AmWceAux", "Am Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5705", "AmWceBoard", "Am Rail Boardings", 0)
        util.initmat(eb, "mf5706", "AmWceFare", "Am Rail Fare", 0)
        # MD
        util.initmat(eb, "mf5710", "MdWceIvtt", "Md Rail Invehicle Time", 0)
        util.initmat(eb, "mf5711", "MdWceIvttRail", "Md Rail Invehicle Time on Rail", 0)
        util.initmat(eb, "mf5712", "MdWceIvttBus", "Md Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5713", "MdWceWait", "Md Rail Waiting Time", 0)
        util.initmat(eb, "mf5714", "MdWceAux", "Md Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5715", "MdWceBoard", "Md Rail Boardings", 0)
        util.initmat(eb, "mf5716", "MdWceFare", "Md Rail Fare", 0)
        # PM
        util.initmat(eb, "mf5720", "PmWceIvtt", "Pm Rail Invehicle Time", 0)
        util.initmat(eb, "mf5721", "PmWceIvttRail", "Pm Rail Invehicle Time on Rail", 0)
        util.initmat(eb, "mf5722", "PmWceIvttBus", "Pm Rail Invehicle Time on Bus", 0)
        util.initmat(eb, "mf5723", "PmWceWait", "Pm Rail Waiting Time", 0)
        util.initmat(eb, "mf5724", "PmWceAux", "Pm Rail Auxilliary Time", 0)
        util.initmat(eb, "mf5725", "PmWceBoard", "Pm Rail Boardings", 0)
        util.initmat(eb, "mf5726", "PmWceFare", "Pm Rail Fare", 0)
