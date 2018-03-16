import inro.modeller as _m
import inro.emme.desktop as _d
import traceback as _traceback

import os
import re
import copy
import csv as csv
import datetime
from StringIO import StringIO

import sqlite3
import pandas as pd
import numpy as np




def execute_calc(eb, social_optimal):
    # trying to get to home level
    # assume AM is production - Use row totals
    # assume PM is attraction - use column totals
    # for MD, half rows and half columns

    # trip and toll data
    df = trips_tolls_df(eb, 'Am', 'P', social_optimal)
    dfMd = trips_tolls_df(eb, 'Md', 'B', social_optimal)
    dfPm = trips_tolls_df(eb, 'Pm', 'A', social_optimal)
    df = df.append(dfMd).append(dfPm)
    del dfMd, dfPm  

    # accessibility data
    dfAccess = calculate_accessibilities(eb)
    dfAccess = calc_rated_access(dfAccess)   

    df = pd.merge(df, dfAccess, left_on=['TAZ','Period'], right_on=['TAZ','Period'], how='left')
    # using SOV daily volume expansion factors for weighting
    exp_fac = expansion_factors()
    df = pd.merge(df, exp_fac, left_on=['Period'], right_on=['Period'], how='left')       

    # GY 1-12
    df = df[df['TAZ'].between(1000, 69999, inclusive=True)]
    df['alignment'] = df['rated_access'] * df['WaTolls']

    # expand values to daily
    df['trips_exp'] = df['trips'] * df['ExpFac']   

    output_var = (df['alignment'] * df['trips_exp']).sum() / df['trips_exp'].sum()
    return output_var

def calc_rated_access(df):
    dfTotals = df.copy(deep=True)
    dfTotals.drop(['TAZ'], axis = 1, inplace=True)
    dfTotals = dfTotals.groupby(['Period'])
    dfTotals = dfTotals.mean().reset_index()
    dfTotals.rename(columns={'relative_access' : 'mean_rel_access' }, inplace=True)
    df = pd.merge(df, dfTotals, left_on=['Period'], right_on=['Period'], how='left')
    df['rated_access'] = df['relative_access'] - df['mean_rel_access']   

    return df

def trips_tolls_df(eb, peak, pa_dir, social_optimal=False):
    util = _m.Modeller().tool("translink.util")
    df = util.get_pd_ij_df(eb)

    ####################
    # Trips
    ####################

    df['{}SovDemand1'.format(peak.lower())] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_1_{}".format(peak)).flatten()
    df['{}SovDemand2'.format(peak.lower())] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_2_{}".format(peak)).flatten()
    df['{}SovDemand3'.format(peak.lower())] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_3_{}".format(peak)).flatten()
    df['{}SovDemand4'.format(peak.lower())] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_4_{}".format(peak)).flatten()
    df['{}HovDemand1'.format(peak.lower())] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_1_{}".format(peak)).flatten()
    df['{}HovDemand2'.format(peak.lower())] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_2_{}".format(peak)).flatten()
    df['{}HovDemand3'.format(peak.lower())] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_3_{}".format(peak)).flatten()
    df['{}HovDemand4'.format(peak.lower())] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_4_{}".format(peak)).flatten()

    if social_optimal == False:

        dfToll = util.get_pd_ij_df(eb)
        dfToll['{}SovToll1'.format(peak.lower())] = df['{}SovDemand1'.format(peak.lower())].multiply(util.get_matrix_numpy(eb, "mfSkim{}SovTollVOT1".format(peak)).flatten(), axis = 0)
        dfToll['{}SovToll2'.format(peak.lower())] = df['{}SovDemand2'.format(peak.lower())].multiply(util.get_matrix_numpy(eb, "mfSkim{}SovTollVOT2".format(peak)).flatten(), axis = 0)
        dfToll['{}SovToll3'.format(peak.lower())] = df['{}SovDemand3'.format(peak.lower())].multiply(util.get_matrix_numpy(eb, "mfSkim{}SovTollVOT3".format(peak)).flatten(), axis = 0)
        dfToll['{}SovToll4'.format(peak.lower())] = df['{}SovDemand4'.format(peak.lower())].multiply(util.get_matrix_numpy(eb, "mfSkim{}SovTollVOT4".format(peak)).flatten(), axis = 0)
        dfToll['{}HovToll1'.format(peak.lower())] = df['{}HovDemand1'.format(peak.lower())].multiply(util.get_matrix_numpy(eb, "mfSkim{}HovTollVOT1".format(peak)).flatten(), axis = 0)
        dfToll['{}HovToll2'.format(peak.lower())] = df['{}HovDemand2'.format(peak.lower())].multiply(util.get_matrix_numpy(eb, "mfSkim{}HovTollVOT2".format(peak)).flatten(), axis = 0)
        dfToll['{}HovToll3'.format(peak.lower())] = df['{}HovDemand3'.format(peak.lower())].multiply(util.get_matrix_numpy(eb, "mfSkim{}HovTollVOT3".format(peak)).flatten(), axis = 0)
        dfToll['{}HovToll4'.format(peak.lower())] = df['{}HovDemand4'.format(peak.lower())].multiply(util.get_matrix_numpy(eb, "mfSkim{}HovTollVOT4".format(peak)).flatten(), axis = 0)

    else:

        dfToll = util.get_pd_ij_df(eb)
        dfToll['{}SovToll1'.format(peak.lower())] = df['{}SovDemand1'.format(peak.lower())].multiply(util.get_matrix_numpy(eb, "mfAmSovSocialCost1").flatten(), axis = 0)
        dfToll['{}SovToll2'.format(peak.lower())] = df['{}SovDemand2'.format(peak.lower())].multiply(util.get_matrix_numpy(eb, "mfAmSovSocialCost2").flatten(), axis = 0)
        dfToll['{}SovToll3'.format(peak.lower())] = df['{}SovDemand3'.format(peak.lower())].multiply(util.get_matrix_numpy(eb, "mfAmSovSocialCost3").flatten(), axis = 0)
        dfToll['{}SovToll4'.format(peak.lower())] = df['{}SovDemand4'.format(peak.lower())].multiply(util.get_matrix_numpy(eb, "mfAmSovSocialCost4").flatten(), axis = 0)
        dfToll['{}HovToll1'.format(peak.lower())] = df['{}HovDemand1'.format(peak.lower())].multiply(util.get_matrix_numpy(eb, "mfAmHovSocialCost1").flatten(), axis = 0)
        dfToll['{}HovToll2'.format(peak.lower())] = df['{}HovDemand2'.format(peak.lower())].multiply(util.get_matrix_numpy(eb, "mfAmHovSocialCost2").flatten(), axis = 0)
        dfToll['{}HovToll3'.format(peak.lower())] = df['{}HovDemand3'.format(peak.lower())].multiply(util.get_matrix_numpy(eb, "mfAmHovSocialCost3").flatten(), axis = 0)
        dfToll['{}HovToll4'.format(peak.lower())] = 0

    if pa_dir == 'P':
        df = compress_df(df, pa_dir)
        dfToll = compress_df(dfToll, pa_dir)
    
    elif pa_dir == 'A':
        df = compress_df(df, pa_dir)
        dfToll = compress_df(dfToll, pa_dir)

    else:
        dfP = compress_df(df, 'P')
        dfA = compress_df(df, 'A')
        df = dfP
        df['value'] = 0.5 * (df['value'].add(dfA['value']))

        dfTollP = compress_df(dfToll, 'P')
        dfTollA = compress_df(dfToll, 'A')
        dfToll = dfTollP
        dfToll['value'] = 0.5 * (dfToll['value'].add(dfTollA['value']))

    df.rename(columns={'value' : 'trips'}, inplace = True) 
    dfToll.rename(columns={'value' : 'toll'}, inplace = True) 

    if social_optimal == True:
        # weighted average VOT used in other analysis to convert minutes to dollars
        if peak.lower() == 'am':
            vot = 14.86 / 60 
        elif peak.lower() == 'md':
            vot = 13.59 / 60
        else:
            vot = 14.67 / 60

        dfToll['toll'] = dfToll['toll'] * vot


    df = pd.merge(df, dfToll, left_on=['TAZ'], right_on=['TAZ'], how='left')
    df['WaTolls'] = df['toll'] / (df['trips'] + 0.0000000001)
    df['Period'] = peak.lower()

    return df

def compress_df(df, pa_dir):

    if pa_dir == 'P':
        df = pd.melt(df, id_vars = ['i','j'], var_name = 'timeModeVot', value_name = 'value')
        df = df.drop(['j', 'timeModeVot'], axis = 1)
        df = df.groupby(['i'])
        df = df.sum().reset_index()
        df.rename(columns={'i' : 'TAZ'}, inplace = True)    
    
    else:
        df = pd.melt(df, id_vars = ['i','j'], var_name = 'timeModeVot', value_name = 'value')
        df = df.drop(['i', 'timeModeVot'], axis = 1)
        df = df.groupby(['j'])
        df = df.sum().reset_index()
        df.rename(columns={'j' : 'TAZ'}, inplace = True)   

    return df

def calculate_accessibilities(eb):

    util = _m.Modeller().tool("translink.util")
    TAZ = util.get_matrix_numpy(eb, 'zoneindex', reshape=False)

    ## Get Auto Travel Times for Employment Accessibilities

    amsovtime_vot3 = util.get_matrix_numpy(eb, "mfAmSovTimeVOT3") # AM
    mdsovtime_vot3 = util.get_matrix_numpy(eb, "mfMdSovTimeVOT3") # MD
    pmsovtime_vot3 = util.get_matrix_numpy(eb, "mfPmSovTimeVOT3") # PM

    ## Get Auto Travel Times for Other Accessibilities

    amsovtime_vot2 = util.get_matrix_numpy(eb, "mfAmSovTimeVOT2") # AM
    mdsovtime_vot2 = util.get_matrix_numpy(eb, "mfMdSovTimeVOT2") # MD
    pmsovtime_vot2 = util.get_matrix_numpy(eb, "mfPmSovTimeVOT2") # PM

    ## Get Transit Travel Times
    # Bus

    ambustime = ( util.get_matrix_numpy(eb, "mfAmBusIvtt") #AM
                + util.get_matrix_numpy(eb, "mfAmBusWait")
                + util.get_matrix_numpy(eb, "mfAmBusAux")
                + util.get_matrix_numpy(eb, "mfAmBusBoard")
                )

    mdbustime = ( util.get_matrix_numpy(eb, "mfMdBusIvtt") #MD
                + util.get_matrix_numpy(eb, "mfMdBusWait")
                + util.get_matrix_numpy(eb, "mfMdBusAux")
                + util.get_matrix_numpy(eb, "mfMdBusBoard")
                )

    pmbustime = ( util.get_matrix_numpy(eb, "mfPmBusIvtt") #PM
                + util.get_matrix_numpy(eb, "mfPmBusWait")
                + util.get_matrix_numpy(eb, "mfPmBusAux")
                + util.get_matrix_numpy(eb, "mfPmBusBoard")
                )

    # Rail

    amrailtime = ( util.get_matrix_numpy(eb, "mfAmRailIvtt") #AM
                    + util.get_matrix_numpy(eb, "mfAmRailIvttBus")
                    + util.get_matrix_numpy(eb, "mfAmRailWait")
                    + util.get_matrix_numpy(eb, "mfAmRailAux")
                    + util.get_matrix_numpy(eb, "mfAmRailBoard")
                    )

    mdrailtime = ( util.get_matrix_numpy(eb, "mfMdRailIvtt") #MD
                    + util.get_matrix_numpy(eb, "mfMdRailIvttBus")
                    + util.get_matrix_numpy(eb, "mfMdRailWait")
                    + util.get_matrix_numpy(eb, "mfMdRailAux")
                    + util.get_matrix_numpy(eb, "mfMdRailBoard")
                    )

    pmrailtime = ( util.get_matrix_numpy(eb, "mfPmRailIvtt") #PM
                    + util.get_matrix_numpy(eb, "mfPmRailIvttBus")
                    + util.get_matrix_numpy(eb, "mfPmRailWait")
                    + util.get_matrix_numpy(eb, "mfPmRailAux")
                    + util.get_matrix_numpy(eb, "mfPmRailBoard")
                    )

    # WCE

    amwcetime =  ( util.get_matrix_numpy(eb, "mfAmWceIvtt") # AM
                    + util.get_matrix_numpy(eb, "mfAmWceIvttRail")
                    + util.get_matrix_numpy(eb, "mfAmWceIvttBus")
                    + util.get_matrix_numpy(eb, "mfAmWceWait")
                    + util.get_matrix_numpy(eb, "mfAmWceAux")
                    + util.get_matrix_numpy(eb, "mfAmWceBoard")
                    )

    pmwcetime =  ( util.get_matrix_numpy(eb, "mfPmWceIvtt") #PM
                    + util.get_matrix_numpy(eb, "mfPmWceIvttRail")
                    + util.get_matrix_numpy(eb, "mfPmWceIvttBus")
                    + util.get_matrix_numpy(eb, "mfPmWceWait")
                    + util.get_matrix_numpy(eb, "mfPmWceAux")
                    + util.get_matrix_numpy(eb, "mfPmWceBoard")
                    )

    ## Calculate Minimum AM, MD and PM Transit Travel Times

    amtrantime = np.minimum(ambustime, amrailtime, amwcetime)
    mdtrantime = np.minimum(mdbustime, mdrailtime)
    pmtrantime = np.minimum(pmbustime, pmrailtime, pmwcetime)

    ## Fill transit intra-zonals with data

    for i in xrange(amtrantime.shape[0]):

        amtrantime[i][i] = amtrantime[i][amtrantime[i] > 0].min() * 0.5
        mdtrantime[i][i] = mdtrantime[i][mdtrantime[i] > 0].min() * 0.5
        pmtrantime[i][i] = pmtrantime[i][pmtrantime[i] > 0].min() * 0.5


    ## Get Employment Data

    totemp = util.get_matrix_numpy(eb, "moTotEmp")

    socemp = ( util.get_matrix_numpy(eb, "moEmpRet")
                + util.get_matrix_numpy(eb, "moEmpBoS")
                + util.get_matrix_numpy(eb, "moEmpAcFoInCu")
                )


    ## Transit Accessibilities

    tran_emp_acc_am = access_calculator(0.078322, 0.069553, amtrantime, totemp) # Transit Employment Accessibilities AM
    tran_emp_acc_md = access_calculator(0.078322, 0.069553, mdtrantime, totemp) # Transit Social Accessibilities MD
    tran_emp_acc_pm = access_calculator(0.078322, 0.069553, pmtrantime, totemp) # Transit Social Accessibilities PM

    ## Auto Accessibilities

    auto_emp_acc_am = access_calculator(0.757971, 0.062315, amsovtime_vot3, totemp) # Auto Employment Accessibilities AM
    auto_emp_acc_md = access_calculator(0.757971, 0.062315, mdsovtime_vot3, totemp) # Auto Social Accessibilities MD
    auto_emp_acc_pm = access_calculator(0.757971, 0.062315, pmsovtime_vot3, totemp) # Auto Social Accessibilities PM

    ## Auto/Transit Accessibility Ratios

    Emp_Acc_Transit_Auto_ratio_am = tran_emp_acc_am/(auto_emp_acc_am + 0.000001)
    Emp_Acc_Transit_Auto_ratio_md = tran_emp_acc_md/(auto_emp_acc_md + 0.000001)
    Emp_Acc_Transit_Auto_ratio_pm = tran_emp_acc_pm/(auto_emp_acc_pm + 0.000001)


    df_access = pd.concat([
                            df_builder('am', TAZ, 'relative_access', Emp_Acc_Transit_Auto_ratio_am),
                            df_builder('md', TAZ, 'relative_access', Emp_Acc_Transit_Auto_ratio_md),
                            df_builder('pm', TAZ, 'relative_access', Emp_Acc_Transit_Auto_ratio_pm)])

    df_access = add_df_descriptors(df_access)
    df_access['Scenario'] = df_access['Alternative']
    df_access['relative_access'] = df_access['Value']
    # df_access = df_access[['Scenario', 'Period', 'TAZ', 'relative_access']]
    df_access = df_access[['Period', 'TAZ', 'relative_access']]
    return df_access

def access_calculator(alpha, beta, time, emp):

    ## Floor Time
    max_time = 300
    time = np.where(time > max_time, max_time, time)
    NoTAZ = time.shape[0]
    emp = emp.reshape(1, NoTAZ) + np.zeros((NoTAZ, 1))
    prob = (1 + alpha)/(1 + alpha*np.exp(beta * (time - 10)))
    access = np.where(prob > 1, 1, prob)*emp
    access = np.sum(access, axis = 1)
    return (access)        

def df_builder(period, zones, measure_name, measure_value):

    df = pd.DataFrame()
    df['TAZ'] = zones
    df['Period'] = period
    df['MeasureName'] = measure_name
    df['Value'] = measure_value

    return df

def add_df_descriptors(df):

    eb = _m.Modeller().emmebank
    util = _m.Modeller().tool("translink.util")
    conn = util.get_db_byname(eb, "rtm.db")

    descriptors = pd.read_sql("SELECT * FROM metadata", conn)
    scen_name = str(descriptors.iloc[0]['scenario'])
    alt_name = str(descriptors.iloc[0]['alternative'])
    conn.close()

    df['Scenario'] = scen_name
    df['Alternative'] = alt_name
    df['Year'] = int(eb.matrix("msYear").data)

    return df

def expansion_factors():
    coefs = StringIO("""Period,ExpFac
    am,3.44
    md,8.41
    pm,3.955""")

    coef_df = pd.read_csv(coefs, sep = ',')
    coef_df.Period = coef_df.Period.str.strip()
    return coef_df

def main(eb, scenario_name, social_optimal=False):

    # get results
    output_var = execute_calc(eb, social_optimal)

    # prep output
    op = {'scenario' : scenario_name,
        'transit_access_index' : output_var}
    op = pd.DataFrame(op, index=[0])

    # link to temp sqlite database to store scenario data
    proj_path = os.path.dirname(_m.Modeller().desktop.project.path)
    file_path = os.path.join(proj_path, 'transit_agreement.db')

    conn = sqlite3.connect(file_path)
    op.to_sql(name='results', con=conn, flavor='sqlite', index=False, if_exists='append')
    conn.close()


if __name__ == '__main__':
    eb = _m.Modeller().emmebank
    util = _m.Modeller().tool("translink.util")
    data_export = _m.Modeller().tool("translink.RTM3.stage4.dataexport")

    dt = _d.app.connect()
    de = dt.data_explorer()
    db = de.active_database()
    ebs = de.databases()

    for eb in ebs:
        title = eb.title()
            
        if title == 'Minimal Base Databank':
            continue

        if title == 'mp_t7_so':
            social_optimal = True 
        else:
            social_optimal = False

        eb.open()
        eb = _m.Modeller().emmebank

        current_time = datetime.datetime.now()
        print('Calculating {} at {}\n'.format(title, current_time))

        try:
            main(eb, title, social_optimal=social_optimal)
            print("Scenario {} export complete.\n".format(title))

        except Exception as e:
            print("Scenario {} export failed.\n".format(title), e)

    current_time = datetime.datetime.now()
    print("Scenario Exporting Complete at {} exporting csv".format(current_time))

    proj_path = os.path.dirname(_m.Modeller().desktop.project.path)
    file_path = os.path.join(proj_path, 'transit_agreement.db')

    conn = sqlite3.connect(file_path)
    df = pd.read_sql("SELECT * FROM results ORDER BY scenario", conn)
    conn.close()

    fn = os.path.join(proj_path, 'transit_alignment_output.csv')
    df.to_csv(fn, index=False)

    os.remove(file_path)
    
    current_time = datetime.datetime.now()   
    print("done at {}\n".format(current_time))