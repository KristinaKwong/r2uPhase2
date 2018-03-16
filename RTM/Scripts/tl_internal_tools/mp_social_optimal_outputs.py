
import inro.modeller as _m
import inro.emme.desktop as _d
import traceback as _traceback

import os
import re
import copy
import csv as csv

import sqlite3
import pandas as pd
import numpy as np




def export_auto_social_optimal(eb, scenario_name, use_cong=False):
    util = _m.Modeller().tool("translink.util")
    df = pd.concat([util.get_pd_ij_df(eb),util.get_ijensem_df(eb, 'gy','gy')], axis=1)

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
    df['amHovDemand4'] = 0
    df['mdHovDemand1'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_1_Md").flatten()
    df['mdHovDemand2'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_2_Md").flatten()
    df['mdHovDemand3'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_3_Md").flatten()
    df['mdHovDemand4'] = 0
    df['pmHovDemand1'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_1_Pm").flatten()
    df['pmHovDemand2'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_2_Pm").flatten()
    df['pmHovDemand3'] = util.get_matrix_numpy(eb, "mfHOV_drvtrp_VOT_3_Pm").flatten()
    df['pmHovDemand4'] = 0
    df['amLGVDemand1'] = util.get_matrix_numpy(eb, "mfLGVAM").flatten()
    df['amHGVDemand1'] = util.get_matrix_numpy(eb, "mfHGVAM").flatten()
    df['mdLGVDemand1'] = util.get_matrix_numpy(eb, "mfLGVMD").flatten()
    df['mdHGVDemand1'] = util.get_matrix_numpy(eb, "mfHGVMD").flatten()
    df['pmLGVDemand1'] = util.get_matrix_numpy(eb, "mfLGVPM").flatten()
    df['pmHGVDemand1'] = util.get_matrix_numpy(eb, "mfHGVPM").flatten()
    print 'df created'

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
    print 'dftime created'

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


    dfToll = pd.concat([util.get_pd_ij_df(eb),util.get_ijensem_df(eb, 'gy','gy')], axis=1)
    dfToll['amSovToll1'] = df['amSovDemand1'].multiply(util.get_matrix_numpy(eb, "mfAmSovSocialCost1").flatten(), axis = 0)
    dfToll['amSovToll2'] = df['amSovDemand2'].multiply(util.get_matrix_numpy(eb, "mfAmSovSocialCost2").flatten(), axis = 0)
    dfToll['amSovToll3'] = df['amSovDemand3'].multiply(util.get_matrix_numpy(eb, "mfAmSovSocialCost3").flatten(), axis = 0)
    dfToll['amSovToll4'] = df['amSovDemand4'].multiply(util.get_matrix_numpy(eb, "mfAmSovSocialCost4").flatten(), axis = 0)
    dfToll['mdSovToll1'] = df['mdSovDemand1'].multiply(util.get_matrix_numpy(eb, "mfMdSovSocialCost1").flatten(), axis = 0)
    dfToll['mdSovToll2'] = df['mdSovDemand2'].multiply(util.get_matrix_numpy(eb, "mfMdSovSocialCost2").flatten(), axis = 0)
    dfToll['mdSovToll3'] = df['mdSovDemand3'].multiply(util.get_matrix_numpy(eb, "mfMdSovSocialCost3").flatten(), axis = 0)
    dfToll['mdSovToll4'] = df['mdSovDemand4'].multiply(util.get_matrix_numpy(eb, "mfMdSovSocialCost4").flatten(), axis = 0)
    dfToll['pmSovToll1'] = df['pmSovDemand1'].multiply(util.get_matrix_numpy(eb, "mfPmSovSocialCost1").flatten(), axis = 0)
    dfToll['pmSovToll2'] = df['pmSovDemand2'].multiply(util.get_matrix_numpy(eb, "mfPmSovSocialCost2").flatten(), axis = 0)
    dfToll['pmSovToll3'] = df['pmSovDemand3'].multiply(util.get_matrix_numpy(eb, "mfPmSovSocialCost3").flatten(), axis = 0)
    dfToll['pmSovToll4'] = df['pmSovDemand4'].multiply(util.get_matrix_numpy(eb, "mfPmSovSocialCost4").flatten(), axis = 0)
    dfToll['amHovToll1'] = df['amHovDemand1'].multiply(util.get_matrix_numpy(eb, "mfAmHovSocialCost1").flatten(), axis = 0)
    dfToll['amHovToll2'] = df['amHovDemand2'].multiply(util.get_matrix_numpy(eb, "mfAmHovSocialCost2").flatten(), axis = 0)
    dfToll['amHovToll3'] = df['amHovDemand3'].multiply(util.get_matrix_numpy(eb, "mfAmHovSocialCost3").flatten(), axis = 0)
    dfToll['amHovToll4'] = 0
    dfToll['mdHovToll1'] = df['mdHovDemand1'].multiply(util.get_matrix_numpy(eb, "mfMdHovSocialCost1").flatten(), axis = 0)
    dfToll['mdHovToll2'] = df['mdHovDemand2'].multiply(util.get_matrix_numpy(eb, "mfMdHovSocialCost2").flatten(), axis = 0)
    dfToll['mdHovToll3'] = df['mdHovDemand3'].multiply(util.get_matrix_numpy(eb, "mfMdHovSocialCost3").flatten(), axis = 0)
    dfToll['mdHovToll4'] = 0
    dfToll['pmHovToll1'] = df['pmHovDemand1'].multiply(util.get_matrix_numpy(eb, "mfPmHovSocialCost1").flatten(), axis = 0)
    dfToll['pmHovToll2'] = df['pmHovDemand2'].multiply(util.get_matrix_numpy(eb, "mfPmHovSocialCost2").flatten(), axis = 0)
    dfToll['pmHovToll3'] = df['pmHovDemand3'].multiply(util.get_matrix_numpy(eb, "mfPmHovSocialCost3").flatten(), axis = 0)
    dfToll['pmHovToll4'] = 0
    dfToll['amLGVToll1'] = df['amLGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfAmLgvSocialCost").flatten(), axis = 0)
    dfToll['amHGVToll1'] = df['amHGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfAmHgvSocialCost").flatten(), axis = 0)
    dfToll['mdLGVToll1'] = df['mdLGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfMdLgvSocialCost").flatten(), axis = 0)
    dfToll['mdHGVToll1'] = df['mdHGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfMdHgvSocialCost").flatten(), axis = 0)
    dfToll['pmLGVToll1'] = df['pmLGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfPmLgvSocialCost").flatten(), axis = 0)
    dfToll['pmHGVToll1'] = df['pmHGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfPmHgvSocialCost").flatten(), axis = 0)

    dfToll = pd.melt(dfToll, id_vars = ['i','j','gy_i','gy_j'], var_name = 'timeModeVot', value_name = 'tolls')
    dfToll = dfToll.drop(['i','j'], axis = 1)
    dfToll = dfToll.groupby(['gy_i', 'gy_j', 'timeModeVot'])
    dfToll = dfToll.sum().reset_index()
    dfTimeModeVot = dfToll['timeModeVot'].str.extract(r'(?P<peak>[a|m|p]{1}[m|d])(?P<mode>Sov|Hov|LGV|HGV)Toll(?P<votclass>\d)')
    dfToll = pd.concat([dfTimeModeVot, dfToll], axis = 1)
    dfToll = dfToll.drop('timeModeVot', axis = 1)

    # need to convert from minutes to dollars
    # VOTs per hour and weighted average for the assignment merios
    VOTam = 14.86 / 60 
    VOTmd = 13.59 / 60
    VOTpm = 14.67 / 60
    
    VOTlgv = 29.56 / 60
    VOThgv = 41.95 / 60

    dfToll['tolls'] = np.where((dfToll['peak'] == 'am') & (np.in1d(dfToll['mode'], ['Sov', 'Hov'])), dfToll['tolls'] * VOTam, dfToll['tolls'])       
    dfToll['tolls'] = np.where((dfToll['peak'] == 'md') & (np.in1d(dfToll['mode'], ['Sov', 'Hov'])), dfToll['tolls'] * VOTmd, dfToll['tolls'])
    dfToll['tolls'] = np.where((dfToll['peak'] == 'pm') & (np.in1d(dfToll['mode'], ['Sov', 'Hov'])), dfToll['tolls'] * VOTpm, dfToll['tolls'])
    
    dfToll['tolls'] = np.where(dfToll['mode'] == 'LGV', dfToll['tolls'] * VOTlgv, dfToll['tolls'])
    dfToll['tolls'] = np.where(dfToll['mode'] == 'HGV', dfToll['tolls'] * VOThgv, dfToll['tolls'])     


    if use_cong:

        dfCongTime = pd.concat([util.get_pd_ij_df(eb),util.get_ijensem_df(eb, 'gy','gy')], axis=1)
        dfCongTime['amSovCongTime1'] = df['amSovDemand1'].multiply(util.get_matrix_numpy(eb, "mfAmSovTimeCongVOT1").flatten(), axis = 0)
        dfCongTime['amSovCongTime2'] = df['amSovDemand2'].multiply(util.get_matrix_numpy(eb, "mfAmSovTimeCongVOT2").flatten(), axis = 0)
        dfCongTime['amSovCongTime3'] = df['amSovDemand3'].multiply(util.get_matrix_numpy(eb, "mfAmSovTimeCongVOT3").flatten(), axis = 0)
        dfCongTime['amSovCongTime4'] = df['amSovDemand4'].multiply(util.get_matrix_numpy(eb, "mfAmSovTimeCongVOT4").flatten(), axis = 0)
        dfCongTime['mdSovCongTime1'] = df['mdSovDemand1'].multiply(util.get_matrix_numpy(eb, "mfMdSovTimeCongVOT1").flatten(), axis = 0)
        dfCongTime['mdSovCongTime2'] = df['mdSovDemand2'].multiply(util.get_matrix_numpy(eb, "mfMdSovTimeCongVOT2").flatten(), axis = 0)
        dfCongTime['mdSovCongTime3'] = df['mdSovDemand3'].multiply(util.get_matrix_numpy(eb, "mfMdSovTimeCongVOT3").flatten(), axis = 0)
        dfCongTime['mdSovCongTime4'] = df['mdSovDemand4'].multiply(util.get_matrix_numpy(eb, "mfMdSovTimeCongVOT4").flatten(), axis = 0)
        dfCongTime['pmSovCongTime1'] = df['pmSovDemand1'].multiply(util.get_matrix_numpy(eb, "mfPmSovTimeCongVOT1").flatten(), axis = 0)
        dfCongTime['pmSovCongTime2'] = df['pmSovDemand2'].multiply(util.get_matrix_numpy(eb, "mfPmSovTimeCongVOT2").flatten(), axis = 0)
        dfCongTime['pmSovCongTime3'] = df['pmSovDemand3'].multiply(util.get_matrix_numpy(eb, "mfPmSovTimeCongVOT3").flatten(), axis = 0)
        dfCongTime['pmSovCongTime4'] = df['pmSovDemand4'].multiply(util.get_matrix_numpy(eb, "mfPmSovTimeCongVOT4").flatten(), axis = 0)
        dfCongTime['amHovCongTime1'] = df['amHovDemand1'].multiply(util.get_matrix_numpy(eb, "mfAmHovTimeCongVOT1").flatten(), axis = 0)
        dfCongTime['amHovCongTime2'] = df['amHovDemand2'].multiply(util.get_matrix_numpy(eb, "mfAmHovTimeCongVOT2").flatten(), axis = 0)
        dfCongTime['amHovCongTime3'] = df['amHovDemand3'].multiply(util.get_matrix_numpy(eb, "mfAmHovTimeCongVOT3").flatten(), axis = 0)
        dfCongTime['amHovCongTime4'] = df['amHovDemand4'].multiply(util.get_matrix_numpy(eb, "mfAmHovTimeCongVOT4").flatten(), axis = 0)
        dfCongTime['mdHovCongTime1'] = df['mdHovDemand1'].multiply(util.get_matrix_numpy(eb, "mfMdHovTimeCongVOT1").flatten(), axis = 0)
        dfCongTime['mdHovCongTime2'] = df['mdHovDemand2'].multiply(util.get_matrix_numpy(eb, "mfMdHovTimeCongVOT2").flatten(), axis = 0)
        dfCongTime['mdHovCongTime3'] = df['mdHovDemand3'].multiply(util.get_matrix_numpy(eb, "mfMdHovTimeCongVOT3").flatten(), axis = 0)
        dfCongTime['mdHovCongTime4'] = df['mdHovDemand4'].multiply(util.get_matrix_numpy(eb, "mfMdHovTimeCongVOT4").flatten(), axis = 0)
        dfCongTime['pmHovCongTime1'] = df['pmHovDemand1'].multiply(util.get_matrix_numpy(eb, "mfPmHovTimeCongVOT1").flatten(), axis = 0)
        dfCongTime['pmHovCongTime2'] = df['pmHovDemand2'].multiply(util.get_matrix_numpy(eb, "mfPmHovTimeCongVOT2").flatten(), axis = 0)
        dfCongTime['pmHovCongTime3'] = df['pmHovDemand3'].multiply(util.get_matrix_numpy(eb, "mfPmHovTimeCongVOT3").flatten(), axis = 0)
        dfCongTime['pmHovCongTime4'] = df['pmHovDemand4'].multiply(util.get_matrix_numpy(eb, "mfPmHovTimeCongVOT4").flatten(), axis = 0)
        #TODO add trucks
        dfCongTime['amLGVCongTime1'] = df['amLGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfAmLgvTimeCong").flatten(), axis = 0)
        dfCongTime['amHGVCongTime1'] = df['amHGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfAmHgvTimeCong").flatten(), axis = 0)
        dfCongTime['mdLGVCongTime1'] = df['mdLGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfMdLgvTimeCong").flatten(), axis = 0)
        dfCongTime['mdHGVCongTime1'] = df['mdHGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfMdHgvTimeCong").flatten(), axis = 0)
        dfCongTime['pmLGVCongTime1'] = df['pmLGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfPmLgvTimeCong").flatten(), axis = 0)
        dfCongTime['pmHGVCongTime1'] = df['pmHGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfPmHgvTimeCong").flatten(), axis = 0)   

        dfCongTime = pd.melt(dfCongTime, id_vars = ['i','j','gy_i','gy_j'], var_name = 'timeModeVot', value_name = 'cong_time')
        dfCongTime = dfCongTime.drop(['i','j'], axis = 1)
        dfCongTime = dfCongTime.groupby(['gy_i', 'gy_j', 'timeModeVot'])
        dfCongTime = dfCongTime.sum().reset_index()
        dfTimeModeVot = dfCongTime['timeModeVot'].str.extract(r'(?P<peak>[a|m|p]{1}[m|d])(?P<mode>Sov|Hov|LGV|HGV)CongTime(?P<votclass>\d)')
        dfCongTime = pd.concat([dfTimeModeVot, dfCongTime], axis = 1)
        dfCongTime = dfCongTime.drop('timeModeVot', axis = 1)

            
        dfLosDTime = pd.concat([util.get_pd_ij_df(eb),util.get_ijensem_df(eb, 'gy','gy')], axis=1)
        dfLosDTime['amSovLosDTime1'] = df['amSovDemand1'].multiply(util.get_matrix_numpy(eb, "mfAmSovTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['amSovLosDTime2'] = df['amSovDemand2'].multiply(util.get_matrix_numpy(eb, "mfAmSovTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['amSovLosDTime3'] = df['amSovDemand3'].multiply(util.get_matrix_numpy(eb, "mfAmSovTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['amSovLosDTime4'] = df['amSovDemand4'].multiply(util.get_matrix_numpy(eb, "mfAmSovTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['mdSovLosDTime1'] = df['mdSovDemand1'].multiply(util.get_matrix_numpy(eb, "mfMdSovTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['mdSovLosDTime2'] = df['mdSovDemand2'].multiply(util.get_matrix_numpy(eb, "mfMdSovTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['mdSovLosDTime3'] = df['mdSovDemand3'].multiply(util.get_matrix_numpy(eb, "mfMdSovTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['mdSovLosDTime4'] = df['mdSovDemand4'].multiply(util.get_matrix_numpy(eb, "mfMdSovTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['pmSovLosDTime1'] = df['pmSovDemand1'].multiply(util.get_matrix_numpy(eb, "mfPmSovTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['pmSovLosDTime2'] = df['pmSovDemand2'].multiply(util.get_matrix_numpy(eb, "mfPmSovTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['pmSovLosDTime3'] = df['pmSovDemand3'].multiply(util.get_matrix_numpy(eb, "mfPmSovTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['pmSovLosDTime4'] = df['pmSovDemand4'].multiply(util.get_matrix_numpy(eb, "mfPmSovTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['amHovLosDTime1'] = df['amHovDemand1'].multiply(util.get_matrix_numpy(eb, "mfAmHovTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['amHovLosDTime2'] = df['amHovDemand2'].multiply(util.get_matrix_numpy(eb, "mfAmHovTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['amHovLosDTime3'] = df['amHovDemand3'].multiply(util.get_matrix_numpy(eb, "mfAmHovTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['amHovLosDTime4'] = df['amHovDemand4'].multiply(util.get_matrix_numpy(eb, "mfAmHovTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['mdHovLosDTime1'] = df['mdHovDemand1'].multiply(util.get_matrix_numpy(eb, "mfMdHovTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['mdHovLosDTime2'] = df['mdHovDemand2'].multiply(util.get_matrix_numpy(eb, "mfMdHovTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['mdHovLosDTime3'] = df['mdHovDemand3'].multiply(util.get_matrix_numpy(eb, "mfMdHovTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['mdHovLosDTime4'] = df['mdHovDemand4'].multiply(util.get_matrix_numpy(eb, "mfMdHovTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['pmHovLosDTime1'] = df['pmHovDemand1'].multiply(util.get_matrix_numpy(eb, "mfPmHovTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['pmHovLosDTime2'] = df['pmHovDemand2'].multiply(util.get_matrix_numpy(eb, "mfPmHovTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['pmHovLosDTime3'] = df['pmHovDemand3'].multiply(util.get_matrix_numpy(eb, "mfPmHovTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['pmHovLosDTime4'] = df['pmHovDemand4'].multiply(util.get_matrix_numpy(eb, "mfPmHovTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['amLGVLosDTime1'] = df['amLGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfAmLgvTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['amHGVLosDTime1'] = df['amHGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfAmHgvTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['mdLGVLosDTime1'] = df['mdLGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfMdLgvTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['mdHGVLosDTime1'] = df['mdHGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfMdHgvTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['pmLGVLosDTime1'] = df['pmLGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfPmLgvTimeLosDcnst").flatten(), axis = 0)
        dfLosDTime['pmHGVLosDTime1'] = df['pmHGVDemand1'].multiply(util.get_matrix_numpy(eb, "mfPmHgvTimeLosDcnst").flatten(), axis = 0)           
    

        dfLosDTime = pd.melt(dfLosDTime, id_vars = ['i','j','gy_i','gy_j'], var_name = 'timeModeVot', value_name = 'losd_time')
        dfLosDTime = dfLosDTime.drop(['i','j'], axis = 1)
        dfLosDTime = dfLosDTime.groupby(['gy_i', 'gy_j', 'timeModeVot'])
        dfLosDTime = dfLosDTime.sum().reset_index()
        dfTimeModeVot = dfLosDTime['timeModeVot'].str.extract(r'(?P<peak>[a|m|p]{1}[m|d])(?P<mode>Sov|Hov|LGV|HGV)LosDTime(?P<votclass>\d)')
        dfLosDTime = pd.concat([dfTimeModeVot, dfLosDTime], axis = 1)
        dfLosDTime = dfLosDTime.drop('timeModeVot', axis = 1)   


    # keep i,j to get the right melt then aggregate up to GY
    df = pd.melt(df, id_vars = ['i','j','gy_i','gy_j'], var_name = 'timeModeVot', value_name = 'trips')
    df = df.drop(['i','j'], axis = 1)
    df = df.groupby(['gy_i', 'gy_j', 'timeModeVot'])
    df = df.sum().reset_index()
    dfTimeModeVot = df['timeModeVot'].str.extract(r'(?P<peak>[a|m|p]{1}[m|d])(?P<mode>Sov|Hov|LGV|HGV)Demand(?P<votclass>\d)')
    df = pd.concat([dfTimeModeVot, df], axis = 1)
    df = df.drop('timeModeVot', axis = 1)


    df = pd.merge(df, dfTime, left_on=['peak','mode','votclass','gy_i','gy_j'], right_on=['peak','mode','votclass','gy_i','gy_j'])
    df = pd.merge(df, dfToll, left_on=['peak','mode','votclass','gy_i','gy_j'], right_on=['peak','mode','votclass','gy_i','gy_j'])
    df = pd.merge(df, dfDist, left_on=['peak','mode','votclass','gy_i','gy_j'], right_on=['peak','mode','votclass','gy_i','gy_j'])
    if use_cong:
        df = pd.merge(df, dfCongTime, left_on=['peak','mode','votclass','gy_i','gy_j'], right_on=['peak','mode','votclass','gy_i','gy_j'])
        del dfCongTime
        
        df = pd.merge(df, dfLosDTime, left_on=['peak','mode','votclass','gy_i','gy_j'], right_on=['peak','mode','votclass','gy_i','gy_j'])
        del dfLosDTime
        
    del dfTime, dfToll
    
    df = df.drop('votclass', axis = 1)
    df = df.groupby(['peak','mode','gy_i','gy_j'])
    df = df.sum().reset_index()
    
    
    df['scenario'] = scenario_name 

    if use_cong:
        df = df[['scenario','peak', 'mode', 'gy_i', 'gy_j', 'trips', 'total_mins', 'tolls', 'vkt', 'cong_time', 'losd_time']]
    else:
        df = df[['scenario','peak', 'mode', 'gy_i', 'gy_j', 'trips', 'total_mins', 'tolls', 'vkt']]
    df.gy_i = df.gy_i.astype(int)
    df.gy_j = df.gy_j.astype(int)
    
    proj_path = os.path.dirname(_m.Modeller().desktop.project.path)
    file_path = os.path.join(proj_path, '{}.txt'.format(scenario_name))

    df.to_csv(file_path, sep = '\t', index=False, header=False)
    del df
    




def export_transit(eb, scenario_name, use_cong=False):
    util = _m.Modeller().tool("translink.util")
    
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


    AmBusTime = AmBusIvtt + AmBusWait + AmBusAux
    MdBusTime = MdBusIvtt + MdBusWait + MdBusAux
    PmBusTime = PmBusIvtt + PmBusWait + PmBusAux

    AmRailTime = AmRailIvtt + AmRailWait + AmRailAux + AmRailIvttBus
    MdRailTime = MdRailIvtt + MdRailWait + MdRailAux + MdRailIvttBus
    PmRailTime = PmRailIvtt + PmRailWait + PmRailAux + PmRailIvttBus

    AmWceTime = AmWceIvtt + AmWceWait + AmWceAux + AmWceIvttBus + AmWceIvttRail
    PmWceTime = PmWceIvtt + PmWceWait + PmWceAux + PmWceIvttBus + PmWceIvttRail

  
    del AmBusIvtt, AmBusWait, AmBusAux
    del MdBusIvtt, MdBusWait, MdBusAux
    del PmBusIvtt, PmBusWait, PmBusAux

    del AmRailIvtt, AmRailWait, AmRailAux, AmRailIvttBus
    del MdRailIvtt, MdRailWait, MdRailAux, MdRailIvttBus
    del PmRailIvtt, PmRailWait, PmRailAux, PmRailIvttBus

    del AmWceIvtt, AmWceWait, AmWceAux, AmWceIvttBus, AmWceIvttRail
    del PmWceIvtt, PmWceWait, PmWceAux, PmWceIvttBus, PmWceIvttRail    

    # Fares
    AmBusFare = util.get_matrix_numpy(eb, "AmBusFare").flatten()
    MdBusFare = util.get_matrix_numpy(eb, "MdBusFare").flatten()
    PmBusFare = util.get_matrix_numpy(eb, "PmBusFare").flatten()
    AmRailFare = util.get_matrix_numpy(eb, "AmRailFare").flatten()
    MdRailFare = util.get_matrix_numpy(eb, "MdRailFare").flatten()
    PmRailFare = util.get_matrix_numpy(eb, "PmRailFare").flatten()
    AmWceFare = util.get_matrix_numpy(eb, "AmWceFare").flatten()
    PmWceFare = util.get_matrix_numpy(eb, "PmWceFare").flatten()
    
    # demand

    AmBusDemand = util.get_matrix_numpy(eb, "mfbusAm").flatten()
    MdBusDemand = util.get_matrix_numpy(eb, "mfbusMd").flatten()
    PmBusDemand = util.get_matrix_numpy(eb, "mfbusPm").flatten()
    AmRailDemand = util.get_matrix_numpy(eb, "mfrailAm").flatten()
    MdRailDemand = util.get_matrix_numpy(eb, "mfrailMd").flatten()
    PmRailDemand = util.get_matrix_numpy(eb, "mfrailPm").flatten()
    AmWceDemand = util.get_matrix_numpy(eb, "mfWCEAm").flatten()
    PmWceDemand = util.get_matrix_numpy(eb, "mfWCEPm").flatten()

    ###########
    # Data frames
    ############
 
    df = pd.concat([util.get_pd_ij_df(eb),util.get_ijensem_df(eb, 'gy','gy')], axis=1)
    df['AmBusDemand'] = AmBusDemand
    df['MdBusDemand'] = MdBusDemand
    df['PmBusDemand'] = PmBusDemand
    df['AmRailDemand'] = AmRailDemand
    df['MdRailDemand'] = MdRailDemand
    df['PmRailDemand'] = PmRailDemand
    df['AmWceDemand'] = AmWceDemand
    df['PmWceDemand'] = PmWceDemand

    df = pd.melt(df, id_vars = ['i','j','gy_i','gy_j'], var_name = 'timeMeasure', value_name = 'trips')
    df = df.drop(['i','j'], axis = 1)
    #df.drop(['i','j'], axis = 1, inplace=True)
    df = df.groupby(['gy_i', 'gy_j','timeMeasure'])
    df = df.sum().reset_index()

    dfTimeMode = df['timeMeasure'].str.extract(r'(?P<peak>[A|M|P]{1}[m|d])(?P<mode>Bus|Rail|Wce)Demand')
    df = pd.concat([dfTimeMode, df], axis = 1)
    df.drop(['timeMeasure'], axis = 1, inplace=True)
    del dfTimeMode

    # Time
    dfTime = pd.concat([util.get_pd_ij_df(eb),util.get_ijensem_df(eb, 'gy','gy')], axis=1)
    dfTime['AmBusTime'] =  AmBusTime *  AmBusDemand 
    dfTime['MdBusTime'] =  MdBusTime *  MdBusDemand 
    dfTime['PmBusTime'] =  PmBusTime *  PmBusDemand 
    dfTime['AmRailTime'] = AmRailTime * AmRailDemand
    dfTime['MdRailTime'] = MdRailTime * MdRailDemand
    dfTime['PmRailTime'] = PmRailTime * PmRailDemand
    dfTime['AmWceTime'] =  AmWceTime *  AmWceDemand 
    dfTime['PmWceTime'] =  PmWceTime *  PmWceDemand 

    dfTime = pd.melt(dfTime, id_vars = ['i','j','gy_i','gy_j'], var_name = 'timeMeasure', value_name = 'total_mins')
    dfTime = dfTime.drop(['i','j'], axis = 1)
    #dfTime.drop(['i','j'], axis = 1, inplace=True)
    dfTime = dfTime.groupby(['gy_i', 'gy_j','timeMeasure'])
    dfTime = dfTime.sum().reset_index()

    dfTimeMode = dfTime['timeMeasure'].str.extract(r'(?P<peak>[A|M|P]{1}[m|d])(?P<mode>Bus|Rail|Wce)Time')
    dfTime = pd.concat([dfTimeMode, dfTime], axis = 1)
    dfTime.drop(['timeMeasure'], axis = 1, inplace=True)
    del dfTimeMode

    # Fare
    dfFare = pd.concat([util.get_pd_ij_df(eb),util.get_ijensem_df(eb, 'gy','gy')], axis=1)
    dfFare['AmBusFare'] =  AmBusFare *  AmBusDemand 
    dfFare['MdBusFare'] =  MdBusFare *  MdBusDemand 
    dfFare['PmBusFare'] =  PmBusFare *  PmBusDemand 
    dfFare['AmRailFare'] = AmRailFare * AmRailDemand
    dfFare['MdRailFare'] = MdRailFare * MdRailDemand
    dfFare['PmRailFare'] = PmRailFare * PmRailDemand
    dfFare['AmWceFare'] =  AmWceFare *  AmWceDemand 
    dfFare['PmWceFare'] =  PmWceFare *  PmWceDemand 

    dfFare = pd.melt(dfFare, id_vars = ['i','j','gy_i','gy_j'], var_name = 'timeMeasure', value_name = 'fares')
    dfFare = dfFare.drop(['i','j'], axis = 1)
    #dfFare.drop(['i','j'], axis = 1, inplace=True)
    dfFare = dfFare.groupby(['gy_i', 'gy_j','timeMeasure'])
    dfFare = dfFare.sum().reset_index()

    dfTimeMode = dfFare['timeMeasure'].str.extract(r'(?P<peak>[A|M|P]{1}[m|d])(?P<mode>Bus|Rail|Wce)Fare')
    dfFare = pd.concat([dfTimeMode, dfFare], axis = 1)
    dfFare.drop(['timeMeasure'], axis = 1, inplace=True)
    del dfTimeMode

 
    del AmBusTime, AmRailTime, AmWceTime
    del MdBusTime, MdRailTime
    del PmBusTime, PmRailTime, PmWceTime

    del AmBusFare, AmRailFare, AmWceFare
    del MdBusFare, MdRailFare
    del PmBusFare, PmRailFare, PmWceFare
    
    del AmBusDemand, AmRailDemand, AmWceDemand
    del MdBusDemand, MdRailDemand
    del PmBusDemand, PmRailDemand, PmWceDemand
    
    ###########
    # output
    ############

    # reduce number of records to speed data flow
    df = pd.merge(df, dfTime, left_on=['peak', 'mode', 'gy_i', 'gy_j'], right_on=['peak', 'mode', 'gy_i', 'gy_j'])
    df = pd.merge(df, dfFare, left_on=['peak', 'mode', 'gy_i', 'gy_j'], right_on=['peak', 'mode', 'gy_i', 'gy_j'])

    df['scenario'] = scenario_name

    df = df[['scenario','peak', 'mode', 'gy_i', 'gy_j', 'trips', 'total_mins', 'fares']]
    if use_cong:
        df['vkt'] = 0
        df['cong_time'] = 0
        df['losd_time'] = 0    
    # this was causing problems for sql server upload
    df.gy_i = df.gy_i.astype(int)
    df.gy_j = df.gy_j.astype(int)
    
    proj_path = os.path.dirname(_m.Modeller().desktop.project.path)
    file_path = os.path.join(proj_path, '{}_transit.txt'.format(scenario_name))
    
    df.to_csv(file_path, sep = '\t', index=False, header=False)
    
    del df





if __name__ == '__main__':

    util = _m.Modeller().tool("translink.util")

    dt = _d.app.connect()
    de = dt.data_explorer()
    db = de.active_database()
    ebs = de.databases()

    eb = _m.Modeller().emmebank





    for eb in ebs:
        title = eb.title()
            
        if title == 'Minimal Base Databank':
            continue
        
        eb.open()
        eb = _m.Modeller().emmebank
        try:
            export_auto_social_optimal(eb, title, use_cong=True)
            export_transit(eb, title, use_cong=True)
            print("Scenario {} export complete.".format(title))
        
        except Exception as e:
            print("Scenario {} export failed.".format(title), e)