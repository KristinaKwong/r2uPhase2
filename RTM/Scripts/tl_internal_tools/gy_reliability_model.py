import inro.modeller as _m
import inro.emme.desktop as _d
import traceback as _traceback

import os
import re
import copy
import multiprocessing
import csv as csv
import datetime

import sqlite3
import pandas as pd
import numpy as np

from StringIO import StringIO



def add_percentile(df, percentile, zscore):
    df['p{}'.format(percentile)] = np.exp((np.log(df['mu']) + zscore * df['temp_sd']))
    return df

def add_temp_sd(df):
    df['temp_sd'] = df.apply(lambda row: temp_sd(row['mu'], row['sigma'], 20000), axis=1)

def temp_sd(mu, sigma, n):
    np.random.seed(55)
    dist = np.random.normal(loc=mu, scale=sigma, size=n)
    ltc = log_trans_const(dist)
    ldist = np.log(dist + ltc)
    new_sd = np.std(ldist)

    return new_sd

def calc_reliability(eb, scenario_name, social_optimal):
    util = _m.Modeller().tool("translink.util")

    var_df = model_df(eb, scenario_name, social_optimal)
    xing_df = bridge_xings()
    coef_df = model_coefs()
    df_mod = pd.merge(var_df, xing_df, left_on=['gy_i','gy_j'], right_on=['gy_i','gy_j'])

    # log variables. Ensure min >= 1 before transformation
    df_mod['tti'] = df_mod['total_mins'] / df_mod['freeflow_mins']
    ltc = log_trans_const(df_mod['tti'])
    df_mod['log_tti'] = np.log(df_mod['tti'] + ltc)

    df_mod['dist'] = df_mod['vkt'] / df_mod['trips']
    ltc = log_trans_const(df_mod['dist'])
    df_mod['log_dist'] = np.log(df_mod['dist'] + ltc)

    df_mod.peak = df_mod.peak.astype(str)
    coef_df.peak = coef_df.peak.astype(str)
    df_mod = pd.merge(df_mod, coef_df, left_on=['peak'], right_on=['peak'], how='left') 

    df_mod['sigma'] = ( df_mod['intercept'] 
                            + df_mod['coef_logTTi'] * df_mod['log_tti']
                            + df_mod['coef_logDist'] * df_mod['log_dist']
                            + df_mod['crossing'] * df_mod['coef_xing'] 
                            + df_mod['coef_peak'] )

    df_mod['sigma'] = np.exp(df_mod['sigma'])  
    df_mod['mu'] = df_mod['total_mins'] / (df_mod['trips'] + 0.0000001)

    df_mod = df_mod[['scenario','peak','mode','gy_i','gy_j','trips','total_mins','freeflow_mins','vkt','crossing','sigma','mu']]

    return df_mod

def model_df(eb, scenario_name, social_optimal=False):
    util = _m.Modeller().tool("translink.util")
    df = pd.concat([util.get_pd_ij_df(eb),util.get_ijensem_df(eb, 'gy','gy')], axis=1)

    ####################
    # Trips
    ####################

    df['amSovDemand1'] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_1_Am").flatten()
    df['amSovDemand2'] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_2_Am").flatten()
    df['amSovDemand3'] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_3_Am").flatten()
    df['amSovDemand4'] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_4_Am").flatten()
    df['mdSovDemand1'] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_1_Md").flatten()
    df['mdSovDemand2'] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_2_Md").flatten()
    df['mdSovDemand3'] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_3_Md").flatten()
    df['mdSovDemand4'] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_4_Md").flatten()
    df['pmSovDemand1'] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_1_Pm").flatten()
    df['pmSovDemand2'] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_2_Pm").flatten()
    df['pmSovDemand3'] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_3_Pm").flatten()
    df['pmSovDemand4'] = util.get_matrix_numpy(eb, "mfSOV_drvtrp_VOT_4_Pm").flatten()
    df['amHovDemand1'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_1_Am").flatten()
    df['amHovDemand2'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_2_Am").flatten()
    df['amHovDemand3'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_3_Am").flatten()
    df['amHovDemand4'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_4_Am").flatten()
    df['mdHovDemand1'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_1_Md").flatten()
    df['mdHovDemand2'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_2_Md").flatten()
    df['mdHovDemand3'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_3_Md").flatten()
    df['mdHovDemand4'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_4_Md").flatten()
    df['pmHovDemand1'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_1_Pm").flatten()
    df['pmHovDemand2'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_2_Pm").flatten()
    df['pmHovDemand3'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_3_Pm").flatten()
    df['pmHovDemand4'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_4_Pm").flatten()
    df['amLGVDemand1'] = util.get_matrix_numpy(eb, "mfLGVAM").flatten()
    df['amHGVDemand1'] = util.get_matrix_numpy(eb, "mfHGVAM").flatten()
    df['mdLGVDemand1'] = util.get_matrix_numpy(eb, "mfLGVMD").flatten()
    df['mdHGVDemand1'] = util.get_matrix_numpy(eb, "mfHGVMD").flatten()
    df['pmLGVDemand1'] = util.get_matrix_numpy(eb, "mfLGVPM").flatten()
    df['pmHGVDemand1'] = util.get_matrix_numpy(eb, "mfHGVPM").flatten()

    ####################
    # Scenario Travel Time
    ####################

    if social_optimal == True:

        dfTime = pd.concat([util.get_pd_ij_df(eb),util.get_ijensem_df(eb, 'gy','gy')], axis=1)
        dfTime['amSovTime1'] = df['amSovDemand1'].multiply(util.get_matrix_numpy(eb, "mfSkimAmSovTimeVOT1").flatten(), axis = 0)
        dfTime['amSovTime2'] = df['amSovDemand2'].multiply(util.get_matrix_numpy(eb, "mfSkimAmSovTimeVOT2").flatten(), axis = 0)
        dfTime['amSovTime3'] = df['amSovDemand3'].multiply(util.get_matrix_numpy(eb, "mfSkimAmSovTimeVOT3").flatten(), axis = 0)
        dfTime['amSovTime4'] = df['amSovDemand4'].multiply(util.get_matrix_numpy(eb, "mfSkimAmSovTimeVOT4").flatten(), axis = 0)
        dfTime['mdSovTime1'] = df['mdSovDemand1'].multiply(util.get_matrix_numpy(eb, "mfSkimMdSovTimeVOT1").flatten(), axis = 0)
        dfTime['mdSovTime2'] = df['mdSovDemand2'].multiply(util.get_matrix_numpy(eb, "mfSkimMdSovTimeVOT2").flatten(), axis = 0)
        dfTime['mdSovTime3'] = df['mdSovDemand3'].multiply(util.get_matrix_numpy(eb, "mfSkimMdSovTimeVOT3").flatten(), axis = 0)
        dfTime['mdSovTime4'] = df['mdSovDemand4'].multiply(util.get_matrix_numpy(eb, "mfSkimMdSovTimeVOT4").flatten(), axis = 0)
        dfTime['pmSovTime1'] = df['pmSovDemand1'].multiply(util.get_matrix_numpy(eb, "mfSkimPmSovTimeVOT1").flatten(), axis = 0)
        dfTime['pmSovTime2'] = df['pmSovDemand2'].multiply(util.get_matrix_numpy(eb, "mfSkimPmSovTimeVOT2").flatten(), axis = 0)
        dfTime['pmSovTime3'] = df['pmSovDemand3'].multiply(util.get_matrix_numpy(eb, "mfSkimPmSovTimeVOT3").flatten(), axis = 0)
        dfTime['pmSovTime4'] = df['pmSovDemand4'].multiply(util.get_matrix_numpy(eb, "mfSkimPmSovTimeVOT4").flatten(), axis = 0)
        dfTime['amHovTime1'] = df['amHovDemand1'].multiply(util.get_matrix_numpy(eb, "mfSkimAmHovTimeVOT1").flatten(), axis = 0)
        dfTime['amHovTime2'] = df['amHovDemand2'].multiply(util.get_matrix_numpy(eb, "mfSkimAmHovTimeVOT2").flatten(), axis = 0)
        dfTime['amHovTime3'] = df['amHovDemand3'].multiply(util.get_matrix_numpy(eb, "mfSkimAmHovTimeVOT3").flatten(), axis = 0)
        dfTime['amHovTime4'] = df['amHovDemand4'].multiply(util.get_matrix_numpy(eb, "mfSkimAmHovTimeVOT4").flatten(), axis = 0)
        dfTime['mdHovTime1'] = df['mdHovDemand1'].multiply(util.get_matrix_numpy(eb, "mfSkimMdHovTimeVOT1").flatten(), axis = 0)
        dfTime['mdHovTime2'] = df['mdHovDemand2'].multiply(util.get_matrix_numpy(eb, "mfSkimMdHovTimeVOT2").flatten(), axis = 0)
        dfTime['mdHovTime3'] = df['mdHovDemand3'].multiply(util.get_matrix_numpy(eb, "mfSkimMdHovTimeVOT3").flatten(), axis = 0)
        dfTime['mdHovTime4'] = df['mdHovDemand4'].multiply(util.get_matrix_numpy(eb, "mfSkimMdHovTimeVOT4").flatten(), axis = 0)
        dfTime['pmHovTime1'] = df['pmHovDemand1'].multiply(util.get_matrix_numpy(eb, "mfSkimPmHovTimeVOT1").flatten(), axis = 0)
        dfTime['pmHovTime2'] = df['pmHovDemand2'].multiply(util.get_matrix_numpy(eb, "mfSkimPmHovTimeVOT2").flatten(), axis = 0)
        dfTime['pmHovTime3'] = df['pmHovDemand3'].multiply(util.get_matrix_numpy(eb, "mfSkimPmHovTimeVOT3").flatten(), axis = 0)
        dfTime['pmHovTime4'] = df['pmHovDemand4'].multiply(util.get_matrix_numpy(eb, "mfSkimPmHovTimeVOT4").flatten(), axis = 0)
        dfTime['amLGVTime1'] = df['amLGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfSkimAmLgvTime").flatten(), axis = 0)
        dfTime['amHGVTime1'] = df['amHGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfSkimAmHgvTime").flatten(), axis = 0)
        dfTime['mdLGVTime1'] = df['mdLGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfSkimMdLgvTime").flatten(), axis = 0)
        dfTime['mdHGVTime1'] = df['mdHGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfSkimMdHgvTime").flatten(), axis = 0)
        dfTime['pmLGVTime1'] = df['pmLGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfSkimPmLgvTime").flatten(), axis = 0)
        dfTime['pmHGVTime1'] = df['pmHGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfSkimPmHgvTime").flatten(), axis = 0)

    else:
        dfTime = pd.concat([util.get_pd_ij_df(eb),util.get_ijensem_df(eb, 'gy','gy')], axis=1)
        dfTime['amSovTime1'] = df['amSovDemand1'].multiply(util.get_matrix_numpy(eb, "mfAmSovOriginalTIMAU1").flatten(), axis = 0)
        dfTime['amSovTime2'] = df['amSovDemand2'].multiply(util.get_matrix_numpy(eb, "mfAmSovOriginalTIMAU2").flatten(), axis = 0)
        dfTime['amSovTime3'] = df['amSovDemand3'].multiply(util.get_matrix_numpy(eb, "mfAmSovOriginalTIMAU3").flatten(), axis = 0)
        dfTime['amSovTime4'] = df['amSovDemand4'].multiply(util.get_matrix_numpy(eb, "mfAmSovOriginalTIMAU4").flatten(), axis = 0)
        dfTime['mdSovTime1'] = df['mdSovDemand1'].multiply(util.get_matrix_numpy(eb, "mfMdSovOriginalTIMAU1").flatten(), axis = 0)
        dfTime['mdSovTime2'] = df['mdSovDemand2'].multiply(util.get_matrix_numpy(eb, "mfMdSovOriginalTIMAU2").flatten(), axis = 0)
        dfTime['mdSovTime3'] = df['mdSovDemand3'].multiply(util.get_matrix_numpy(eb, "mfMdSovOriginalTIMAU3").flatten(), axis = 0)
        dfTime['mdSovTime4'] = df['mdSovDemand4'].multiply(util.get_matrix_numpy(eb, "mfMdSovOriginalTIMAU4").flatten(), axis = 0)
        dfTime['pmSovTime1'] = df['pmSovDemand1'].multiply(util.get_matrix_numpy(eb, "mfPmSovOriginalTIMAU1").flatten(), axis = 0)
        dfTime['pmSovTime2'] = df['pmSovDemand2'].multiply(util.get_matrix_numpy(eb, "mfPmSovOriginalTIMAU2").flatten(), axis = 0)
        dfTime['pmSovTime3'] = df['pmSovDemand3'].multiply(util.get_matrix_numpy(eb, "mfPmSovOriginalTIMAU3").flatten(), axis = 0)
        dfTime['pmSovTime4'] = df['pmSovDemand4'].multiply(util.get_matrix_numpy(eb, "mfPmSovOriginalTIMAU4").flatten(), axis = 0)
        dfTime['amHovTime1'] = df['amHovDemand1'].multiply(util.get_matrix_numpy(eb, "mfAmHovOriginalTIMAU1").flatten(), axis = 0)
        dfTime['amHovTime2'] = df['amHovDemand2'].multiply(util.get_matrix_numpy(eb, "mfAmHovOriginalTIMAU2").flatten(), axis = 0)
        dfTime['amHovTime3'] = df['amHovDemand3'].multiply(util.get_matrix_numpy(eb, "mfAmHovOriginalTIMAU3").flatten(), axis = 0)
        dfTime['amHovTime4'] = 0
        dfTime['mdHovTime1'] = df['mdHovDemand1'].multiply(util.get_matrix_numpy(eb, "mfMdHovOriginalTIMAU1").flatten(), axis = 0)
        dfTime['mdHovTime2'] = df['mdHovDemand2'].multiply(util.get_matrix_numpy(eb, "mfMdHovOriginalTIMAU2").flatten(), axis = 0)
        dfTime['mdHovTime3'] = df['mdHovDemand3'].multiply(util.get_matrix_numpy(eb, "mfMdHovOriginalTIMAU3").flatten(), axis = 0)
        dfTime['mdHovTime4'] = 0
        dfTime['pmHovTime1'] = df['pmHovDemand1'].multiply(util.get_matrix_numpy(eb, "mfPmHovOriginalTIMAU1").flatten(), axis = 0)
        dfTime['pmHovTime2'] = df['pmHovDemand2'].multiply(util.get_matrix_numpy(eb, "mfPmHovOriginalTIMAU2").flatten(), axis = 0)
        dfTime['pmHovTime3'] = df['pmHovDemand3'].multiply(util.get_matrix_numpy(eb, "mfPmHovOriginalTIMAU3").flatten(), axis = 0)
        dfTime['pmHovTime4'] = 0
        dfTime['amLGVTime1'] = df['amLGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfAmLgvOriginalTIMAU").flatten(), axis = 0)
        dfTime['amHGVTime1'] = df['amHGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfAmHgvOriginalTIMAU").flatten(), axis = 0)
        dfTime['mdLGVTime1'] = df['mdLGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfMdLgvOriginalTIMAU").flatten(), axis = 0)
        dfTime['mdHGVTime1'] = df['mdHGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfMdHgvOriginalTIMAU").flatten(), axis = 0)
        dfTime['pmLGVTime1'] = df['pmLGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfPmLgvOriginalTIMAU").flatten(), axis = 0)
        dfTime['pmHGVTime1'] = df['pmHGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfPmHgvOriginalTIMAU").flatten(), axis = 0)


    dfTime = pd.melt(dfTime, id_vars = ['i','j','gy_i','gy_j'], var_name = 'timeModeVot', value_name = 'total_mins')
    dfTime = dfTime.drop(['i','j'], axis = 1)
    dfTime = dfTime.groupby(['gy_i', 'gy_j', 'timeModeVot'])
    dfTime = dfTime.sum().reset_index()
    dfTimeModeVot = dfTime['timeModeVot'].str.extract(r'(?P<peak>[a|m|p]{1}[m|d])(?P<mode>Sov|Hov|LGV|HGV)Time(?P<votclass>\d)')
    dfTime = pd.concat([dfTimeModeVot, dfTime], axis = 1)
    dfTime = dfTime.drop('timeModeVot', axis = 1)

    ####################
    # Scenario VKT
    ####################

    dfDist = pd.concat([util.get_pd_ij_df(eb),util.get_ijensem_df(eb, 'gy','gy')], axis=1)
    dfDist['amSovDist1'] = df['amSovDemand1'].multiply(util.get_matrix_numpy(eb, "mfSkimAmSovDistVOT1").flatten(), axis = 0)
    dfDist['amSovDist2'] = df['amSovDemand2'].multiply(util.get_matrix_numpy(eb, "mfSkimAmSovDistVOT2").flatten(), axis = 0)
    dfDist['amSovDist3'] = df['amSovDemand3'].multiply(util.get_matrix_numpy(eb, "mfSkimAmSovDistVOT3").flatten(), axis = 0)
    dfDist['amSovDist4'] = df['amSovDemand4'].multiply(util.get_matrix_numpy(eb, "mfSkimAmSovDistVOT4").flatten(), axis = 0)
    dfDist['mdSovDist1'] = df['mdSovDemand1'].multiply(util.get_matrix_numpy(eb, "mfSkimMdSovDistVOT1").flatten(), axis = 0)
    dfDist['mdSovDist2'] = df['mdSovDemand2'].multiply(util.get_matrix_numpy(eb, "mfSkimMdSovDistVOT2").flatten(), axis = 0)
    dfDist['mdSovDist3'] = df['mdSovDemand3'].multiply(util.get_matrix_numpy(eb, "mfSkimMdSovDistVOT3").flatten(), axis = 0)
    dfDist['mdSovDist4'] = df['mdSovDemand4'].multiply(util.get_matrix_numpy(eb, "mfSkimMdSovDistVOT4").flatten(), axis = 0)
    dfDist['pmSovDist1'] = df['pmSovDemand1'].multiply(util.get_matrix_numpy(eb, "mfSkimPmSovDistVOT1").flatten(), axis = 0)
    dfDist['pmSovDist2'] = df['pmSovDemand2'].multiply(util.get_matrix_numpy(eb, "mfSkimPmSovDistVOT2").flatten(), axis = 0)
    dfDist['pmSovDist3'] = df['pmSovDemand3'].multiply(util.get_matrix_numpy(eb, "mfSkimPmSovDistVOT3").flatten(), axis = 0)
    dfDist['pmSovDist4'] = df['pmSovDemand4'].multiply(util.get_matrix_numpy(eb, "mfSkimPmSovDistVOT4").flatten(), axis = 0)
    dfDist['amHovDist1'] = df['amHovDemand1'].multiply(util.get_matrix_numpy(eb, "mfSkimAmHovDistVOT1").flatten(), axis = 0)
    dfDist['amHovDist2'] = df['amHovDemand2'].multiply(util.get_matrix_numpy(eb, "mfSkimAmHovDistVOT2").flatten(), axis = 0)
    dfDist['amHovDist3'] = df['amHovDemand3'].multiply(util.get_matrix_numpy(eb, "mfSkimAmHovDistVOT3").flatten(), axis = 0)
    dfDist['amHovDist4'] = df['amHovDemand4'].multiply(util.get_matrix_numpy(eb, "mfSkimAmHovDistVOT4").flatten(), axis = 0)
    dfDist['mdHovDist1'] = df['mdHovDemand1'].multiply(util.get_matrix_numpy(eb, "mfSkimMdHovDistVOT1").flatten(), axis = 0)
    dfDist['mdHovDist2'] = df['mdHovDemand2'].multiply(util.get_matrix_numpy(eb, "mfSkimMdHovDistVOT2").flatten(), axis = 0)
    dfDist['mdHovDist3'] = df['mdHovDemand3'].multiply(util.get_matrix_numpy(eb, "mfSkimMdHovDistVOT3").flatten(), axis = 0)
    dfDist['mdHovDist4'] = df['mdHovDemand4'].multiply(util.get_matrix_numpy(eb, "mfSkimMdHovDistVOT4").flatten(), axis = 0)
    dfDist['pmHovDist1'] = df['pmHovDemand1'].multiply(util.get_matrix_numpy(eb, "mfSkimPmHovDistVOT1").flatten(), axis = 0)
    dfDist['pmHovDist2'] = df['pmHovDemand2'].multiply(util.get_matrix_numpy(eb, "mfSkimPmHovDistVOT2").flatten(), axis = 0)
    dfDist['pmHovDist3'] = df['pmHovDemand3'].multiply(util.get_matrix_numpy(eb, "mfSkimPmHovDistVOT3").flatten(), axis = 0)
    dfDist['pmHovDist4'] = df['pmHovDemand4'].multiply(util.get_matrix_numpy(eb, "mfSkimPmHovDistVOT4").flatten(), axis = 0)
    dfDist['amLGVDist1'] = df['amLGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfSkimAmLgvDist").flatten(), axis = 0)
    dfDist['amHGVDist1'] = df['amHGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfSkimAmHgvDist").flatten(), axis = 0)
    dfDist['mdLGVDist1'] = df['mdLGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfSkimMdLgvDist").flatten(), axis = 0)
    dfDist['mdHGVDist1'] = df['mdHGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfSkimMdHgvDist").flatten(), axis = 0)
    dfDist['pmLGVDist1'] = df['pmLGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfSkimPmLgvDist").flatten(), axis = 0)
    dfDist['pmHGVDist1'] = df['pmHGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfSkimPmHgvDist").flatten(), axis = 0)

    dfDist = pd.melt(dfDist, id_vars = ['i','j','gy_i','gy_j'], var_name = 'timeModeVot', value_name = 'vkt')
    dfDist = dfDist.drop(['i','j'], axis = 1)
    dfDist = dfDist.groupby(['gy_i', 'gy_j', 'timeModeVot'])
    dfDist = dfDist.sum().reset_index()
    dfTimeModeVot = dfDist['timeModeVot'].str.extract(r'(?P<peak>[a|m|p]{1}[m|d])(?P<mode>Sov|Hov|LGV|HGV)Dist(?P<votclass>\d)')
    dfDist = pd.concat([dfTimeModeVot, dfDist], axis = 1)
    dfDist = dfDist.drop('timeModeVot', axis = 1)

    ####################
    # Scenario Freeflow minutes
    ####################

    dfTimeFF = pd.concat([util.get_pd_ij_df(eb),util.get_ijensem_df(eb, 'gy','gy')], axis=1)
    dfTimeFF['amSovTimeFF1'] = df['amSovDemand1'].multiply(util.get_matrix_numpy(eb, "mfAmSovTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['amSovTimeFF2'] = df['amSovDemand2'].multiply(util.get_matrix_numpy(eb, "mfAmSovTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['amSovTimeFF3'] = df['amSovDemand3'].multiply(util.get_matrix_numpy(eb, "mfAmSovTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['amSovTimeFF4'] = df['amSovDemand4'].multiply(util.get_matrix_numpy(eb, "mfAmSovTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['mdSovTimeFF1'] = df['mdSovDemand1'].multiply(util.get_matrix_numpy(eb, "mfMdSovTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['mdSovTimeFF2'] = df['mdSovDemand2'].multiply(util.get_matrix_numpy(eb, "mfMdSovTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['mdSovTimeFF3'] = df['mdSovDemand3'].multiply(util.get_matrix_numpy(eb, "mfMdSovTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['mdSovTimeFF4'] = df['mdSovDemand4'].multiply(util.get_matrix_numpy(eb, "mfMdSovTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['pmSovTimeFF1'] = df['pmSovDemand1'].multiply(util.get_matrix_numpy(eb, "mfPmSovTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['pmSovTimeFF2'] = df['pmSovDemand2'].multiply(util.get_matrix_numpy(eb, "mfPmSovTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['pmSovTimeFF3'] = df['pmSovDemand3'].multiply(util.get_matrix_numpy(eb, "mfPmSovTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['pmSovTimeFF4'] = df['pmSovDemand4'].multiply(util.get_matrix_numpy(eb, "mfPmSovTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['amHovTimeFF1'] = df['amHovDemand1'].multiply(util.get_matrix_numpy(eb, "mfAmHovTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['amHovTimeFF2'] = df['amHovDemand2'].multiply(util.get_matrix_numpy(eb, "mfAmHovTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['amHovTimeFF3'] = df['amHovDemand3'].multiply(util.get_matrix_numpy(eb, "mfAmHovTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['amHovTimeFF4'] = df['amHovDemand4'].multiply(util.get_matrix_numpy(eb, "mfAmHovTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['mdHovTimeFF1'] = df['mdHovDemand1'].multiply(util.get_matrix_numpy(eb, "mfMdHovTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['mdHovTimeFF2'] = df['mdHovDemand2'].multiply(util.get_matrix_numpy(eb, "mfMdHovTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['mdHovTimeFF3'] = df['mdHovDemand3'].multiply(util.get_matrix_numpy(eb, "mfMdHovTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['mdHovTimeFF4'] = df['mdHovDemand4'].multiply(util.get_matrix_numpy(eb, "mfMdHovTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['pmHovTimeFF1'] = df['pmHovDemand1'].multiply(util.get_matrix_numpy(eb, "mfPmHovTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['pmHovTimeFF2'] = df['pmHovDemand2'].multiply(util.get_matrix_numpy(eb, "mfPmHovTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['pmHovTimeFF3'] = df['pmHovDemand3'].multiply(util.get_matrix_numpy(eb, "mfPmHovTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['pmHovTimeFF4'] = df['pmHovDemand4'].multiply(util.get_matrix_numpy(eb, "mfPmHovTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['amLGVTimeFF1'] = df['amLGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfAmLgvTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['amHGVTimeFF1'] = df['amHGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfAmHgvTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['mdLGVTimeFF1'] = df['mdLGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfMdLgvTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['mdHGVTimeFF1'] = df['mdHGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfMdHgvTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['pmLGVTimeFF1'] = df['pmLGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfPmLgvTimeFreeflow").flatten(), axis = 0)
    dfTimeFF['pmHGVTimeFF1'] = df['pmHGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfPmHgvTimeFreeflow").flatten(), axis = 0)

    dfTimeFF = pd.melt(dfTimeFF, id_vars = ['i','j','gy_i','gy_j'], var_name = 'timeModeVot', value_name = 'freeflow_mins')
    dfTimeFF = dfTimeFF.drop(['i','j'], axis = 1)
    dfTimeFF = dfTimeFF.groupby(['gy_i', 'gy_j', 'timeModeVot'])
    dfTimeFF = dfTimeFF.sum().reset_index()
    dfTimeModeVot = dfTimeFF['timeModeVot'].str.extract(r'(?P<peak>[a|m|p]{1}[m|d])(?P<mode>Sov|Hov|LGV|HGV)TimeFF(?P<votclass>\d)')
    dfTimeFF = pd.concat([dfTimeModeVot, dfTimeFF], axis = 1)
    dfTimeFF = dfTimeFF.drop('timeModeVot', axis = 1)

    ####################
    # Prep output
    ####################

    df = pd.melt(df, id_vars = ['i','j','gy_i','gy_j'], var_name = 'timeModeVot', value_name = 'trips')
    df = df.drop(['i','j'], axis = 1)
    df = df.groupby(['gy_i', 'gy_j', 'timeModeVot'])
    df = df.sum().reset_index()
    dfTimeModeVot = df['timeModeVot'].str.extract(r'(?P<peak>[a|m|p]{1}[m|d])(?P<mode>Sov|Hov|LGV|HGV)Demand(?P<votclass>\d)')
    df = pd.concat([dfTimeModeVot, df], axis = 1)
    df = df.drop('timeModeVot', axis = 1)


    ####################
    # Compile Variables
    ####################

    df = pd.merge(df, dfTime, left_on=['peak','mode','votclass','gy_i','gy_j'], right_on=['peak','mode','votclass','gy_i','gy_j'])
    df = pd.merge(df, dfTimeFF, left_on=['peak','mode','votclass','gy_i','gy_j'], right_on=['peak','mode','votclass','gy_i','gy_j'])
    df = pd.merge(df, dfDist, left_on=['peak','mode','votclass','gy_i','gy_j'], right_on=['peak','mode','votclass','gy_i','gy_j'])
    
    df = df.drop('votclass', axis = 1)
    df = df.groupby(['peak','mode','gy_i','gy_j'])
    df = df.sum().reset_index()
    
    df['scenario'] = scenario_name 

    df.gy_i = df.gy_i.astype(int)
    df.gy_j = df.gy_j.astype(int)

    df = df[['scenario','peak', 'mode', 'gy_i', 'gy_j', 'trips', 'total_mins', 'freeflow_mins',  'vkt']]

    return df

def freeflow_skim(eb, amscenid, mdscenid, pmscenid):

    ff_assignment = _m.Modeller().tool("translink.internal_tools.ff_assignment")

    am_scen = eb.scenario(amscenid)
    md_scen = eb.scenario(mdscenid)
    pm_scen = eb.scenario(pmscenid)

    ff_assignment(eb, am_scen, md_scen, pm_scen,assignment_type=1)

def bridge_xings():
    xings = StringIO("""gy_i,gy_j,crossing
    1,1,0
    1,2,0
    1,3,1
    1,4,1
    1,5,1
    1,6,1
    1,7,1
    1,8,1
    1,9,1
    1,10,1
    1,11,1
    1,12,1
    1,13,1
    1,14,1
    2,1,0
    2,2,0
    2,3,1
    2,4,1
    2,5,1
    2,6,1
    2,7,1
    2,8,1
    2,9,1
    2,10,1
    2,11,1
    2,12,1
    2,13,1
    2,14,1
    3,1,1
    3,2,1
    3,3,0
    3,4,0
    3,5,0
    3,6,0
    3,7,1
    3,8,1
    3,9,1
    3,10,1
    3,11,1
    3,12,1
    3,13,1
    3,14,1
    4,1,1
    4,2,1
    4,3,0
    4,4,0
    4,5,0
    4,6,0
    4,7,1
    4,8,1
    4,9,1
    4,10,1
    4,11,1
    4,12,1
    4,13,1
    4,14,1
    5,1,1
    5,2,1
    5,3,0
    5,4,0
    5,5,0
    5,6,0
    5,7,1
    5,8,1
    5,9,1
    5,10,1
    5,11,1
    5,12,1
    5,13,1
    5,14,1
    6,1,1
    6,2,1
    6,3,0
    6,4,0
    6,5,0
    6,6,0
    6,7,1
    6,8,1
    6,9,1
    6,10,1
    6,11,1
    6,12,1
    6,13,1
    6,14,1
    7,1,1
    7,2,1
    7,3,1
    7,4,1
    7,5,1
    7,6,1
    7,7,0
    7,8,1
    7,9,1
    7,10,1
    7,11,1
    7,12,1
    7,13,1
    7,14,1
    8,1,1
    8,2,1
    8,3,1
    8,4,1
    8,5,1
    8,6,1
    8,7,1
    8,8,0
    8,9,0
    8,10,0
    8,11,1
    8,12,0
    8,13,1
    8,14,0
    9,1,1
    9,2,1
    9,3,1
    9,4,1
    9,5,1
    9,6,1
    9,7,1
    9,8,1
    9,9,0
    9,10,0
    9,11,1
    9,12,0
    9,13,1
    9,14,0
    10,1,1
    10,2,1
    10,3,1
    10,4,1
    10,5,1
    10,6,1
    10,7,1
    10,8,1
    10,9,0
    10,10,0
    10,11,1
    10,12,0
    10,13,0
    10,14,0
    11,1,1
    11,2,1
    11,3,1
    11,4,1
    11,5,1
    11,6,1
    11,7,1
    11,8,1
    11,9,1
    11,10,1
    11,11,0
    11,12,1
    11,13,0
    11,14,1
    12,1,1
    12,2,1
    12,3,1
    12,4,1
    12,5,1
    12,6,1
    12,7,1
    12,8,1
    12,9,0
    12,10,0
    12,11,1
    12,12,0
    12,13,0
    12,14,0
    13,1,1
    13,2,1
    13,3,1
    13,4,1
    13,5,1
    13,6,1
    13,7,1
    13,8,1
    13,9,1
    13,10,0
    13,11,0
    13,12,0
    13,13,0
    13,14,0
    14,1,1
    14,2,1
    14,3,1
    14,4,1
    14,5,1
    14,6,1
    14,7,1
    14,8,1
    14,9,0
    14,10,0
    14,11,0
    14,12,0
    14,13,0
    14,14,0""")

    xings_df = pd.read_csv(xings, sep = ',')
    return xings_df

def model_coefs():


    coefs = StringIO("""peak,intercept,coef_logTTi,coef_logDist,coef_xing,coef_peak
    am,-3.3737,3.55707,0.83667,0.1621,0.1777
    md,-3.3737,3.1192,0.83667,0.1621,0
    pm,-3.3737,3.55707,0.83667,0.1621,0.1777""")

    coef_df = pd.read_csv(coefs, sep = ',')
    coef_df.peak = coef_df.peak.str.strip()

    return coef_df

def log_trans_const(nparray):
    if nparray.min() < 1:
        const = 1 - nparray.min()
    else:
        const = 0
    
    return const

def main(eb, scenario_name, amscenid, mdscenid, pmscenid):
     freeflow_skim(eb, amscenid, mdscenid, pmscenid)

    #TODO switch this off when not export social optimal
     df = calc_reliability(eb, scenario_name, social_optimal=False)   

     add_temp_sd(df)

     add_percentile(df, 80, 0.842)
     add_percentile(df, 85, 1.036)
     add_percentile(df, 90, 1.282)
     add_percentile(df, 95, 1.645)

     return df




if __name__ == '__main__':
    eb = _m.Modeller().emmebank
    util = _m.Modeller().tool("translink.util")

    dt = _d.app.connect()
    de = dt.data_explorer()
    db = de.active_database()
    ebs = de.databases()

    for eb in ebs:
        title = eb.title()
            
        if title == 'Minimal Base Databank':
            continue
        
        if title == 'mp_t7_dbc_r':
            title = 'mp_t7_dbc_r_010'

        if title == 'mp_t7_dbc8':
            title = 'mp_t7_dbc8_100'

        if title == 'mp_t7_dbctr':
            title = 'mp_t7_dbctr_100'

        eb.open()
        eb = _m.Modeller().emmebank

        current_time = datetime.datetime.now()
        print('Starting export of {} at {}\n'.format(title, current_time))

        try:
            df = main(eb, title, 21000, 22000, 23000)

            proj_path = os.path.dirname(_m.Modeller().desktop.project.path)
            file_path = os.path.join(proj_path, 'reliability_output' ,'{}_reliability.txt'.format(title))
            
            df.to_csv(file_path, sep = '\t', index=False, header=False)

            print("Scenario {} export complete.".format(title))

        except Exception as e:
            print("Scenario {} export failed.".format(title), e)    
