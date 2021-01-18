#---------------------------------------------------------------------
##--TransLink Regional Transportation Model
##--
##--Path: EconomicAnalysis.fareelasticity
##--Purpose: Fare Revenue
##---------------------------------------------------------------------
import inro.modeller as _m
import inro.emme.desktop as _d
import csv
import os
import multiprocessing
import numpy as np
import pandas as pd
import sqlite3
import traceback as _traceback
import inro.emme.database.emmebank as eb_object

class DataExport(_m.Tool()):

    tool_run_msg = _m.Attribute(unicode)
    BAU_Path = _m.Attribute(str)
    Scen_Path = _m.Attribute(str)

    def __init__(self):
        self.export_csvs = True

    def page(self):

        util = _m.Modeller().tool("translink.util")
        project = _m.Modeller().desktop.project
        input_path = os.path.dirname(project.path)

        pb = _m.ToolPageBuilder(self)
        pb.title = "Generate Fare Model Outputs"
        pb.description = "Generate Fare Model Outputs"
        pb.branding_text = "TransLink"
        pb.add_select_file(tool_attribute_name="BAU_Path",
                           window_type="file",
                           file_filter="emmebank",
                           title="Browse to Base emmebank:",
                           start_path= input_path)

        pb.add_select_file(tool_attribute_name="Scen_Path",
                           window_type="file",
                           file_filter="emmebank",
                           title="Browse to Scenario emmebank:",
                           start_path= input_path)

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:

            self.__call__(self.BAU_Path, self.Scen_Path)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))


    @_m.logbook_trace("Data Export")
    def __call__(self, BAU_Path, Scen_Path):

        util = _m.Modeller().tool("translink.util")
        self.export_transit_data(BAU_Path = BAU_Path, Scen_Path = Scen_Path)

    def export_transit_data(self, BAU_Path, Scen_Path):

        util = _m.Modeller().tool("translink.util")

        fare_dict_b, fare_dict_s = self.get_fare_mat(BAU_Path, Scen_Path)
        df = self.get_demands_and_fares(BAU_Path, Scen_Path, fare_dict_b, fare_dict_s)
        df, df_rev = self.calc_fare_elast(df)

        ## Write out to scenario database
        ## Dump to SQLite DB
        eb_s = eb_object.Emmebank(Scen_Path)
        conn = util.get_db_byname(eb_s, "rts_outputs.db")
        df.to_sql(name='fare_elasticity_table', con=conn, index=False, if_exists='replace')
        df_rev.to_sql(name='fare_revenue_table', con=conn, index=False, if_exists='replace')
        conn.close()
        #print ("Incremental Fare Revenue: %.0f/day"%(df_rev["rev_s"].sum()-df_rev["rev_b"].sum()))
        return(df_rev["rev_s"].sum()-df_rev["rev_b"].sum()) #daily dollar

    def calc_fare_elast(self, df):

        util = _m.Modeller().tool("translink.util")

        df_rev = df.groupby(['mode']).sum().reset_index()
        df_rev = df_rev.rename(columns = {'demxfare_b': 'rev_b'})
        df_rev = df_rev[['mode', 'dem_b', 'dem_s', 'rev_b', 'rev_s']]


        df['fare_b'] = np.where(df['dem_b'] == 0, df['avgfare_b']/df['count'], df['demxfare_b']/df['dem_b'])
        df['fare_s'] = np.where(df['dem_b'] == 0, df['avgfare_s']/df['count'], df['demxfare_s']/df['dem_b'])
        df = df[['gh_i', 'gh_j', 'mode', 'dem_b', 'dem_s', 'fare_b', 'fare_s']]
        df['elasticity'] = np.where((df['dem_b'] > 0 ) & (df['dem_s'] > 0) & (df['fare_b'] != df['fare_s']), (df['dem_s']/df['dem_b'] - 1)/(df['fare_s']/df['fare_b'] - 1), np.nan)

        elas_neg = df.loc[(df['elasticity'] < 0) & (df['elasticity'] >= - 1.0), ['elasticity']].median() # fare x dem
        elas_pos = df.loc[(df['elasticity'] > 0) & (df['elasticity'] <=   1.0), ['elasticity']].median() # fare x dem

        #print elas_neg
        #print elas_pos

        df['elasticity'] = np.where(df['elasticity'] < -1, elas_neg, df['elasticity'])
        df['elasticity'] = np.where(df['elasticity'] >  1, elas_pos, df['elasticity'])
        df['elasticity'] = np.where(df['elasticity'].isnull() , elas_neg, df['elasticity'])
        df['ratio'] = np.where(df['dem_b'] == 0, np.nan, df['dem_s']/df['dem_b'])
        df['diff'] = df['dem_s'] - df['dem_b']

        return df, df_rev

    def get_fare_mat(self, BAU_Path, Scen_Path):

        util = _m.Modeller().tool("translink.util")
        eb_b = eb_object.Emmebank(BAU_Path)
        eb_s = eb_object.Emmebank(Scen_Path)

        fare_dict_b = {'bus' : [util.get_matrix_numpy(eb_b, 'mf5304'), util.get_matrix_numpy(eb_b, 'mf5314'), util.get_matrix_numpy(eb_b, 'mf5324'), eb_b.matrix("ms160").data],
                       'ral' : [util.get_matrix_numpy(eb_b, 'mf5505'), util.get_matrix_numpy(eb_b, 'mf5515'), util.get_matrix_numpy(eb_b, 'mf5525'), eb_b.matrix("ms160").data],
                       'wce' : [util.get_matrix_numpy(eb_b, 'mf5706'), util.get_matrix_numpy(eb_b, 'mf5726')]}

        fare_dict_s = {'bus' : [util.get_matrix_numpy(eb_s, 'mf5304'), util.get_matrix_numpy(eb_s, 'mf5314'), util.get_matrix_numpy(eb_s, 'mf5324'), eb_s.matrix("ms160").data],
                       'ral' : [util.get_matrix_numpy(eb_s, 'mf5505'), util.get_matrix_numpy(eb_s, 'mf5515'), util.get_matrix_numpy(eb_s, 'mf5525'), eb_s.matrix("ms160").data],
                       'wce' : [util.get_matrix_numpy(eb_s, 'mf5706'), util.get_matrix_numpy(eb_s, 'mf5726')]}

        return fare_dict_b, fare_dict_s

    def get_demands_and_fares(self, BAU_Path, Scen_Path, fare_dict_b, fare_dict_s):

        util = _m.Modeller().tool("translink.util")
        eb_b = eb_object.Emmebank(BAU_Path)
        eb_s = eb_object.Emmebank(Scen_Path)

        NoTAZ = len(util.get_matrix_numpy(eb_b, 'mozoneindex', reshape = False))
        i = util.get_matrix_numpy(eb_b, 'mozoneindex')  + np.zeros((1, NoTAZ))
        j = i.transpose()

        Gh_P = util.get_matrix_numpy(eb_b, 'gh_ensem')  + np.zeros((1, NoTAZ))
        Gh_A = Gh_P.transpose()

        full_dict = {

        'hbw_dict':{'pa_demand':['HbWBusPerTrips', 'HbWRailPerTrips'],   'fare_slice_range' : [500, 507]},
        'hbu_dict':{'pa_demand':['HbUBusPerTrips',  'HbURailPerTrips'],  'fare_slice_range' : [510, 517]},
        'hbs_dict':{'pa_demand':['HbScBusPerTrips', 'HbScRailPerTrips'], 'fare_slice_range' : [520, 527]},
        'hbh_dict':{'pa_demand':['HbShBusPerTrips', 'HbShRailPerTrips'], 'fare_slice_range' : [530, 537]},
        'hbp_dict':{'pa_demand':['HbPbBusPerTrips', 'HbPbRailPerTrips'], 'fare_slice_range' : [540, 547]},
        'hbr_dict':{'pa_demand':['HbSoBusPerTrips', 'HbSoRailPerTrips'], 'fare_slice_range' : [550, 557]},
        'hbe_dict':{'pa_demand':['HbEsBusPerTrips', 'HbEsRailPerTrips'], 'fare_slice_range' : [560, 567]},
        'nhw_dict':{'pa_demand':['NHbWBusPerTrips', 'NHbWRailPerTrips'], 'fare_slice_range' : [570, 573]},
        'nho_dict':{'pa_demand':['NHbOBusPerTrips', 'NHbORailPerTrips'], 'fare_slice_range' : [580, 583]}}

        dem_busxfare_b, dem_ralxfare_b, dem_busxfare_s, dem_ralxfare_s = 0, 0, 0, 0
        dem_bus_b, dem_ral_b, dem_bus_s, dem_ral_s = 0, 0, 0, 0
        avg_busfare_b, avg_ralfare_b, avg_busfare_s, avg_ralfare_s = 0, 0, 0, 0
        rev_bus_s, rev_ral_s, rev_wce_s = 0, 0, 0
        dict_len = len(full_dict) + 0.0

        ## Fares

        for keys, values in full_dict.items():

            lng = (1 + values['fare_slice_range'][1] - values['fare_slice_range'][0])/2

            # Get Base Year Demands
            dem1 = util.get_matrix_numpy(eb_b, values['pa_demand'][0])
            dem2 = util.get_matrix_numpy(eb_b, values['pa_demand'][1])

            # Get scenario year Demands
            dem3 = util.get_matrix_numpy(eb_s, values['pa_demand'][0])
            dem4 = util.get_matrix_numpy(eb_s, values['pa_demand'][1])

            for ln in range (lng):

                scal1 = util.get_matrix_numpy(eb_b, 'ms' + str(values['fare_slice_range'][0] + ln))
                scal2 = util.get_matrix_numpy(eb_b, 'ms' + str(values['fare_slice_range'][0] + ln + lng))

                dem_busxfare_b += dem1*scal1*fare_dict_b['bus'][ln] + dem1.transpose()*scal2*fare_dict_b['bus'][ln]
                dem_ralxfare_b += dem2*scal1*fare_dict_b['ral'][ln] + dem2.transpose()*scal2*fare_dict_b['ral'][ln]
                avg_busfare_b  += (scal1*fare_dict_b['bus'][ln] + scal2*fare_dict_b['bus'][ln])/dict_len
                avg_ralfare_b  += (scal1*fare_dict_b['ral'][ln] + scal2*fare_dict_b['ral'][ln])/dict_len

                dem_busxfare_s += dem1*scal1*fare_dict_s['bus'][ln] + dem1.transpose()*scal2*fare_dict_s['bus'][ln]
                dem_ralxfare_s += dem2*scal1*fare_dict_s['ral'][ln] + dem2.transpose()*scal2*fare_dict_s['ral'][ln]
                avg_busfare_s  += (scal1*fare_dict_s['bus'][ln] + scal2*fare_dict_s['bus'][ln])/dict_len
                avg_ralfare_s  += (scal1*fare_dict_s['ral'][ln] + scal2*fare_dict_s['ral'][ln])/dict_len


                dem_bus_b += dem1*scal1 + dem1.transpose()*scal2
                dem_ral_b += dem2*scal1 + dem2.transpose()*scal2

                dem_bus_s += dem3*scal1 + dem3.transpose()*scal2
                dem_ral_s += dem4*scal1 + dem4.transpose()*scal2

                ### revenue bus and rail
                rev_bus_s += dem3*scal1*fare_dict_s['bus'][ln] + dem3.transpose()*scal2*fare_dict_s['bus'][ln]
                rev_ral_s += dem4*scal1*fare_dict_s['ral'][ln] + dem4.transpose()*scal2*fare_dict_s['ral'][ln]


        ## Add WCE trips

        dem5 = util.get_matrix_numpy(eb_b, 'HbWWCEPerTrips')
        dem6 = util.get_matrix_numpy(eb_s, 'HbWWCEPerTrips')
        scal1 = util.get_matrix_numpy(eb_b, 'ms406')
        scal2 = util.get_matrix_numpy(eb_b, 'ms407')
        scal3 = util.get_matrix_numpy(eb_b, 'ms408')

        dem_wce_b = dem5*(scal1 + scal2) + dem5.transpose()*scal3
        dem_wce_s = dem6*(scal1 + scal2) + dem6.transpose()*scal3

        dem_wcexfare_b = dem5*(scal1 + scal2)*fare_dict_b['wce'][0] +  dem5.transpose()*(scal3)*fare_dict_b['wce'][1]
        dem_wcexfare_s = dem5*(scal1 + scal2)*fare_dict_s['wce'][0] +  dem5.transpose()*(scal3)*fare_dict_s['wce'][1]
        avg_wcefare_b = (scal1 + scal2)*fare_dict_b['wce'][0] + (scal3)*fare_dict_b['wce'][1]
        avg_wcefare_s = (scal1 + scal2)*fare_dict_s['wce'][0] + (scal3)*fare_dict_s['wce'][1]

        # revenue wce
        rev_wce_s = dem6*(scal1 + scal2)*fare_dict_s['wce'][0] +  dem6.transpose()*(scal3)*fare_dict_s['wce'][1]

        ## Generate DataFrames
        df_bus = pd.DataFrame({'i': i.flatten(), 'j': j.flatten(), 'gh_i': Gh_P.flatten(), 'gh_j': Gh_A.flatten(), 'mode': 'bus', 'dem_b': dem_bus_b.flatten(),
                              'dem_s': dem_bus_s.flatten(), 'demxfare_b': dem_busxfare_b.flatten(), 'demxfare_s': dem_busxfare_s.flatten(),
                              'avgfare_b': avg_busfare_b.flatten(), 'avgfare_s': avg_busfare_s.flatten(), 'rev_s': rev_bus_s.flatten(),  'count': 1})

        df_ral = pd.DataFrame({'i': i.flatten(), 'j': j.flatten(), 'gh_i': Gh_P.flatten(), 'gh_j': Gh_A.flatten(), 'mode': 'rail', 'dem_b': dem_ral_b.flatten(),
                              'dem_s': dem_ral_s.flatten(), 'demxfare_b': dem_ralxfare_b.flatten(), 'demxfare_s': dem_ralxfare_s.flatten(),
                              'avgfare_b': avg_ralfare_b.flatten(), 'avgfare_s': avg_ralfare_s.flatten(), 'rev_s': rev_ral_s.flatten(),  'count': 1})

        df_wce = pd.DataFrame({'i': i.flatten(), 'j': j.flatten(), 'gh_i': Gh_P.flatten(), 'gh_j': Gh_A.flatten(), 'mode': 'wce', 'dem_b': dem_wce_b.flatten(),
                              'dem_s': dem_wce_s.flatten(), 'demxfare_b': dem_wcexfare_b.flatten(), 'demxfare_s': dem_wcexfare_s.flatten(),
                              'avgfare_b': avg_wcefare_b.flatten(), 'avgfare_s': avg_wcefare_s.flatten(), 'rev_s': rev_wce_s.flatten(), 'count': 1})

        df = pd.concat([df_bus, df_ral, df_wce])
        df = df[(df['i'] != df['j'])]
        df = df.groupby(['gh_i', 'gh_j', 'mode']).sum().reset_index()
        df = df[['gh_i', 'gh_j', 'mode', 'dem_b', 'dem_s', 'demxfare_b', 'demxfare_s', 'avgfare_b', 'avgfare_s', 'rev_s', 'count']]

        return df