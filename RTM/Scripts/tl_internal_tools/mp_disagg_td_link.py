import inro.modeller as _m
import inro.emme.desktop as _d
import traceback as _traceback

import datetime
import os
import re
import copy
import csv as csv

import sqlite3
import pandas as pd
import numpy as np



def export_auto(eb, scenario_name):
    util = _m.Modeller().tool("translink.util")
    
    df = util.get_pd_ij_df(eb)
    df['amSovTime1'] = util.get_matrix_numpy(eb, "mfSkimAmSovTimeVOT1").flatten()
    # df['amSovTime2'] = util.get_matrix_numpy(eb, "mfSkimAmSovTimeVOT2").flatten()
    # df['amSovTime3'] = util.get_matrix_numpy(eb, "mfSkimAmSovTimeVOT3").flatten()
    df['amSovTime4'] = util.get_matrix_numpy(eb, "mfSkimAmSovTimeVOT4").flatten()
    df['mdSovTime1'] = util.get_matrix_numpy(eb, "mfSkimMdSovTimeVOT1").flatten()
    # df['mdSovTime2'] = util.get_matrix_numpy(eb, "mfSkimMdSovTimeVOT2").flatten()
    # df['mdSovTime3'] = util.get_matrix_numpy(eb, "mfSkimMdSovTimeVOT3").flatten()
    df['mdSovTime4'] = util.get_matrix_numpy(eb, "mfSkimMdSovTimeVOT4").flatten()
    df['pmSovTime1'] = util.get_matrix_numpy(eb, "mfSkimPmSovTimeVOT1").flatten()
    # df['pmSovTime2'] = util.get_matrix_numpy(eb, "mfSkimPmSovTimeVOT2").flatten()
    # df['pmSovTime3'] = util.get_matrix_numpy(eb, "mfSkimPmSovTimeVOT3").flatten()
    df['pmSovTime4'] = util.get_matrix_numpy(eb, "mfSkimPmSovTimeVOT4").flatten()
    df['amHovTime1'] = util.get_matrix_numpy(eb, "mfSkimAmHovTimeVOT1").flatten()
    # df['amHovTime2'] = util.get_matrix_numpy(eb, "mfSkimAmHovTimeVOT2").flatten()
    df['amHovTime3'] = util.get_matrix_numpy(eb, "mfSkimAmHovTimeVOT3").flatten()
    # df['amHovTime4'] = util.get_matrix_numpy(eb, "mfSkimAmHovTimeVOT4").flatten()
    df['mdHovTime1'] = util.get_matrix_numpy(eb, "mfSkimMdHovTimeVOT1").flatten()
    # df['mdHovTime2'] = util.get_matrix_numpy(eb, "mfSkimMdHovTimeVOT2").flatten()
    df['mdHovTime3'] = util.get_matrix_numpy(eb, "mfSkimMdHovTimeVOT3").flatten()
    # df['mdHovTime4'] = util.get_matrix_numpy(eb, "mfSkimMdHovTimeVOT4").flatten()
    df['pmHovTime1'] = util.get_matrix_numpy(eb, "mfSkimPmHovTimeVOT1").flatten()
    # df['pmHovTime2'] = util.get_matrix_numpy(eb, "mfSkimPmHovTimeVOT2").flatten()
    df['pmHovTime3'] = util.get_matrix_numpy(eb, "mfSkimPmHovTimeVOT3").flatten()
    # df['pmHovTime4'] = util.get_matrix_numpy(eb, "mfSkimPmHovTimeVOT4").flatten()

    df = pd.melt(df, id_vars = ['i','j'], var_name = 'timeModeVot', value_name = 'total_mins')
    dfTimeModeVot = df['timeModeVot'].str.extract(r'(?P<peak>[a|m|p]{1}[m|d])(?P<mode>Sov|Hov|LGV|HGV)Time(?P<votclass>\d)')
    df = pd.concat([dfTimeModeVot, df], axis = 1)
    df = df.drop('timeModeVot', axis = 1)
    del dfTimeModeVot

    #############
    # Tolls
    #############
    dfToll = util.get_pd_ij_df(eb)
    dfToll['amSovToll1'] = util.get_matrix_numpy(eb, "mfSkimAmSovTollVOT1").flatten()
    #fToll['amSovToll2'] = util.get_matrix_numpy(eb, "mfSkimAmSovTollVOT2").flatten()
    #fToll['amSovToll3'] = util.get_matrix_numpy(eb, "mfSkimAmSovTollVOT3").flatten()
    dfToll['amSovToll4'] = util.get_matrix_numpy(eb, "mfSkimAmSovTollVOT4").flatten()
    dfToll['mdSovToll1'] = util.get_matrix_numpy(eb, "mfSkimMdSovTollVOT1").flatten()
    #fToll['mdSovToll2'] = util.get_matrix_numpy(eb, "mfSkimMdSovTollVOT2").flatten()
    #fToll['mdSovToll3'] = util.get_matrix_numpy(eb, "mfSkimMdSovTollVOT3").flatten()
    dfToll['mdSovToll4'] = util.get_matrix_numpy(eb, "mfSkimMdSovTollVOT4").flatten()
    dfToll['pmSovToll1'] = util.get_matrix_numpy(eb, "mfSkimPmSovTollVOT1").flatten()
    #fToll['pmSovToll2'] = util.get_matrix_numpy(eb, "mfSkimPmSovTollVOT2").flatten()
    #fToll['pmSovToll3'] = util.get_matrix_numpy(eb, "mfSkimPmSovTollVOT3").flatten()
    dfToll['pmSovToll4'] = util.get_matrix_numpy(eb, "mfSkimPmSovTollVOT4").flatten()
    dfToll['amHovToll1'] = util.get_matrix_numpy(eb, "mfSkimAmHovTollVOT1").flatten()
    #fToll['amHovToll2'] = util.get_matrix_numpy(eb, "mfSkimAmHovTollVOT2").flatten()
    dfToll['amHovToll3'] = util.get_matrix_numpy(eb, "mfSkimAmHovTollVOT3").flatten()
    #fToll['amHovToll4'] = util.get_matrix_numpy(eb, "mfSkimAmHovTollVOT4").flatten()
    dfToll['mdHovToll1'] = util.get_matrix_numpy(eb, "mfSkimMdHovTollVOT1").flatten()
    #fToll['mdHovToll2'] = util.get_matrix_numpy(eb, "mfSkimMdHovTollVOT2").flatten()
    dfToll['mdHovToll3'] = util.get_matrix_numpy(eb, "mfSkimMdHovTollVOT3").flatten()
    #fToll['mdHovToll4'] = util.get_matrix_numpy(eb, "mfSkimMdHovTollVOT4").flatten()
    dfToll['pmHovToll1'] = util.get_matrix_numpy(eb, "mfSkimPmHovTollVOT1").flatten()
    #fToll['pmHovToll2'] = util.get_matrix_numpy(eb, "mfSkimPmHovTollVOT2").flatten()
    dfToll['pmHovToll3'] = util.get_matrix_numpy(eb, "mfSkimPmHovTollVOT3").flatten()
    #fToll['pmHovToll4'] = util.get_matrix_numpy(eb, "mfSkimPmHovTollVOT4").flatten()

    dfToll = pd.melt(dfToll, id_vars = ['i','j'], var_name = 'timeModeVot', value_name = 'tolls')
    dfTimeModeVot = dfToll['timeModeVot'].str.extract(r'(?P<peak>[a|m|p]{1}[m|d])(?P<mode>Sov|Hov|LGV|HGV)Toll(?P<votclass>\d)')
    dfToll = pd.concat([dfTimeModeVot, dfToll], axis = 1)
    dfToll = dfToll.drop('timeModeVot', axis = 1)

    df = pd.merge(df, dfToll, left_on=['peak','mode','votclass','i','j'], right_on=['peak','mode','votclass','i','j'])
    del dfToll

    #############
    # Distance
    #############
    dfDist = util.get_pd_ij_df(eb)
    dfDist['amSovDist1'] = util.get_matrix_numpy(eb, "mfSkimAmSovDistVOT1").flatten()
    #fDist['amSovDist2'] = util.get_matrix_numpy(eb, "mfSkimAmSovDistVOT2").flatten()
    #fDist['amSovDist3'] = util.get_matrix_numpy(eb, "mfSkimAmSovDistVOT3").flatten()
    dfDist['amSovDist4'] = util.get_matrix_numpy(eb, "mfSkimAmSovDistVOT4").flatten()
    dfDist['mdSovDist1'] = util.get_matrix_numpy(eb, "mfSkimMdSovDistVOT1").flatten()
    #fDist['mdSovDist2'] = util.get_matrix_numpy(eb, "mfSkimMdSovDistVOT2").flatten()
    #fDist['mdSovDist3'] = util.get_matrix_numpy(eb, "mfSkimMdSovDistVOT3").flatten()
    dfDist['mdSovDist4'] = util.get_matrix_numpy(eb, "mfSkimMdSovDistVOT4").flatten()
    dfDist['pmSovDist1'] = util.get_matrix_numpy(eb, "mfSkimPmSovDistVOT1").flatten()
    #fDist['pmSovDist2'] = util.get_matrix_numpy(eb, "mfSkimPmSovDistVOT2").flatten()
    #fDist['pmSovDist3'] = util.get_matrix_numpy(eb, "mfSkimPmSovDistVOT3").flatten()
    dfDist['pmSovDist4'] = util.get_matrix_numpy(eb, "mfSkimPmSovDistVOT4").flatten()
    dfDist['amHovDist1'] = util.get_matrix_numpy(eb, "mfSkimAmHovDistVOT1").flatten()
    #fDist['amHovDist2'] = util.get_matrix_numpy(eb, "mfSkimAmHovDistVOT2").flatten()
    dfDist['amHovDist3'] = util.get_matrix_numpy(eb, "mfSkimAmHovDistVOT3").flatten()
    #fDist['amHovDist4'] = util.get_matrix_numpy(eb, "mfSkimAmHovDistVOT4").flatten()
    dfDist['mdHovDist1'] = util.get_matrix_numpy(eb, "mfSkimMdHovDistVOT1").flatten()
    #fDist['mdHovDist2'] = util.get_matrix_numpy(eb, "mfSkimMdHovDistVOT2").flatten()
    dfDist['mdHovDist3'] = util.get_matrix_numpy(eb, "mfSkimMdHovDistVOT3").flatten()
    #fDist['mdHovDist4'] = util.get_matrix_numpy(eb, "mfSkimMdHovDistVOT4").flatten()
    dfDist['pmHovDist1'] = util.get_matrix_numpy(eb, "mfSkimPmHovDistVOT1").flatten()
    #fDist['pmHovDist2'] = util.get_matrix_numpy(eb, "mfSkimPmHovDistVOT2").flatten()
    dfDist['pmHovDist3'] = util.get_matrix_numpy(eb, "mfSkimPmHovDistVOT3").flatten()
    #fDist['pmHovDist4'] = util.get_matrix_numpy(eb, "mfSkimPmHovDistVOT4").flatten()

    dfDist = pd.melt(dfDist, id_vars = ['i','j'], var_name = 'timeModeVot', value_name = 'dist')
    dfTimeModeVot = dfDist['timeModeVot'].str.extract(r'(?P<peak>[a|m|p]{1}[m|d])(?P<mode>Sov|Hov|LGV|HGV)Dist(?P<votclass>\d)')
    dfDist = pd.concat([dfTimeModeVot, dfDist], axis = 1)
    dfDist = dfDist.drop('timeModeVot', axis = 1)

    df = pd.merge(df, dfDist, left_on=['peak','mode','votclass','i','j'], right_on=['peak','mode','votclass','i','j'])
    del dfDist


    #############
    # Congested minutes = MAX(time - losdtime, 0) at the link level
    #############

    dfCongTime = util.get_pd_ij_df(eb)
    dfCongTime['amSovCongTime1'] = util.get_matrix_numpy(eb, "mfAmSovTimeCongVOT1").flatten()
    #fCongTime['amSovCongTime2'] = util.get_matrix_numpy(eb, "mfAmSovTimeCongVOT2").flatten()
    #fCongTime['amSovCongTime3'] = util.get_matrix_numpy(eb, "mfAmSovTimeCongVOT3").flatten()
    dfCongTime['amSovCongTime4'] = util.get_matrix_numpy(eb, "mfAmSovTimeCongVOT4").flatten()
    dfCongTime['mdSovCongTime1'] = util.get_matrix_numpy(eb, "mfMdSovTimeCongVOT1").flatten()
    #fCongTime['mdSovCongTime2'] = util.get_matrix_numpy(eb, "mfMdSovTimeCongVOT2").flatten()
    #fCongTime['mdSovCongTime3'] = util.get_matrix_numpy(eb, "mfMdSovTimeCongVOT3").flatten()
    dfCongTime['mdSovCongTime4'] = util.get_matrix_numpy(eb, "mfMdSovTimeCongVOT4").flatten()
    dfCongTime['pmSovCongTime1'] = util.get_matrix_numpy(eb, "mfPmSovTimeCongVOT1").flatten()
    #fCongTime['pmSovCongTime2'] = util.get_matrix_numpy(eb, "mfPmSovTimeCongVOT2").flatten()
    #fCongTime['pmSovCongTime3'] = util.get_matrix_numpy(eb, "mfPmSovTimeCongVOT3").flatten()
    dfCongTime['pmSovCongTime4'] = util.get_matrix_numpy(eb, "mfPmSovTimeCongVOT4").flatten()
    dfCongTime['amHovCongTime1'] = util.get_matrix_numpy(eb, "mfAmHovTimeCongVOT1").flatten()
    #fCongTime['amHovCongTime2'] = util.get_matrix_numpy(eb, "mfAmHovTimeCongVOT2").flatten()
    dfCongTime['amHovCongTime3'] = util.get_matrix_numpy(eb, "mfAmHovTimeCongVOT3").flatten()
    #fCongTime['amHovCongTime4'] = util.get_matrix_numpy(eb, "mfAmHovTimeCongVOT4").flatten()
    dfCongTime['mdHovCongTime1'] = util.get_matrix_numpy(eb, "mfMdHovTimeCongVOT1").flatten()
    #fCongTime['mdHovCongTime2'] = util.get_matrix_numpy(eb, "mfMdHovTimeCongVOT2").flatten()
    dfCongTime['mdHovCongTime3'] = util.get_matrix_numpy(eb, "mfMdHovTimeCongVOT3").flatten()
    #fCongTime['mdHovCongTime4'] = util.get_matrix_numpy(eb, "mfMdHovTimeCongVOT4").flatten()
    dfCongTime['pmHovCongTime1'] = util.get_matrix_numpy(eb, "mfPmHovTimeCongVOT1").flatten()
    #fCongTime['pmHovCongTime2'] = util.get_matrix_numpy(eb, "mfPmHovTimeCongVOT2").flatten()
    dfCongTime['pmHovCongTime3'] = util.get_matrix_numpy(eb, "mfPmHovTimeCongVOT3").flatten()
    #fCongTime['pmHovCongTime4'] = util.get_matrix_numpy(eb, "mfPmHovTimeCongVOT4").flatten()

    dfCongTime = pd.melt(dfCongTime, id_vars = ['i','j'], var_name = 'timeModeVot', value_name = 'cong_time')
    dfTimeModeVot = dfCongTime['timeModeVot'].str.extract(r'(?P<peak>[a|m|p]{1}[m|d])(?P<mode>Sov|Hov|LGV|HGV)CongTime(?P<votclass>\d)')
    dfCongTime = pd.concat([dfTimeModeVot, dfCongTime], axis = 1)
    dfCongTime = dfCongTime.drop('timeModeVot', axis = 1)
    del dfTimeModeVot

    df = pd.merge(df, dfCongTime, left_on=['peak','mode','votclass','i','j'], right_on=['peak','mode','votclass','i','j'])
    del dfCongTime

    #############
    # LOS D Time.  pure minutes shortest path with travel times on link based on V/C = 0.85
    #############

    dfLosDTime = util.get_pd_ij_df(eb)
    dfLosDTime['amSovLosDTime1'] = util.get_matrix_numpy(eb, "mfAmSovTimeLosDcnst").flatten()
    #fLosDTime['amSovLosDTime2'] = util.get_matrix_numpy(eb, "mfAmSovTimeLosDcnst").flatten()
    #fLosDTime['amSovLosDTime3'] = util.get_matrix_numpy(eb, "mfAmSovTimeLosDcnst").flatten()
    dfLosDTime['amSovLosDTime4'] = util.get_matrix_numpy(eb, "mfAmSovTimeLosDcnst").flatten()
    dfLosDTime['mdSovLosDTime1'] = util.get_matrix_numpy(eb, "mfMdSovTimeLosDcnst").flatten()
    #fLosDTime['mdSovLosDTime2'] = util.get_matrix_numpy(eb, "mfMdSovTimeLosDcnst").flatten()
    #fLosDTime['mdSovLosDTime3'] = util.get_matrix_numpy(eb, "mfMdSovTimeLosDcnst").flatten()
    dfLosDTime['mdSovLosDTime4'] = util.get_matrix_numpy(eb, "mfMdSovTimeLosDcnst").flatten()
    dfLosDTime['pmSovLosDTime1'] = util.get_matrix_numpy(eb, "mfPmSovTimeLosDcnst").flatten()
    #fLosDTime['pmSovLosDTime2'] = util.get_matrix_numpy(eb, "mfPmSovTimeLosDcnst").flatten()
    #fLosDTime['pmSovLosDTime3'] = util.get_matrix_numpy(eb, "mfPmSovTimeLosDcnst").flatten()
    dfLosDTime['pmSovLosDTime4'] = util.get_matrix_numpy(eb, "mfPmSovTimeLosDcnst").flatten()
    dfLosDTime['amHovLosDTime1'] = util.get_matrix_numpy(eb, "mfAmHovTimeLosDcnst").flatten()
    #fLosDTime['amHovLosDTime2'] = util.get_matrix_numpy(eb, "mfAmHovTimeLosDcnst").flatten()
    dfLosDTime['amHovLosDTime3'] = util.get_matrix_numpy(eb, "mfAmHovTimeLosDcnst").flatten()
    #fLosDTime['amHovLosDTime4'] = util.get_matrix_numpy(eb, "mfAmHovTimeLosDcnst").flatten()
    dfLosDTime['mdHovLosDTime1'] = util.get_matrix_numpy(eb, "mfMdHovTimeLosDcnst").flatten()
    #fLosDTime['mdHovLosDTime2'] = util.get_matrix_numpy(eb, "mfMdHovTimeLosDcnst").flatten()
    dfLosDTime['mdHovLosDTime3'] = util.get_matrix_numpy(eb, "mfMdHovTimeLosDcnst").flatten()
    #fLosDTime['mdHovLosDTime4'] = util.get_matrix_numpy(eb, "mfMdHovTimeLosDcnst").flatten()
    dfLosDTime['pmHovLosDTime1'] = util.get_matrix_numpy(eb, "mfPmHovTimeLosDcnst").flatten()
    #fLosDTime['pmHovLosDTime2'] = util.get_matrix_numpy(eb, "mfPmHovTimeLosDcnst").flatten()
    dfLosDTime['pmHovLosDTime3'] = util.get_matrix_numpy(eb, "mfPmHovTimeLosDcnst").flatten()
    #fLosDTime['pmHovLosDTime4'] = util.get_matrix_numpy(eb, "mfPmHovTimeLosDcnst").flatten()


    dfLosDTime = pd.melt(dfLosDTime, id_vars = ['i','j'], var_name = 'timeModeVot', value_name = 'losd_time')
    dfTimeModeVot = dfLosDTime['timeModeVot'].str.extract(r'(?P<peak>[a|m|p]{1}[m|d])(?P<mode>Sov|Hov|LGV|HGV)LosDTime(?P<votclass>\d)')
    dfLosDTime = pd.concat([dfTimeModeVot, dfLosDTime], axis = 1)
    dfLosDTime = dfLosDTime.drop('timeModeVot', axis = 1)
    del dfTimeModeVot

    df = pd.merge(df, dfLosDTime, left_on=['peak','mode','votclass','i','j'], right_on=['peak','mode','votclass','i','j'])
    del dfLosDTime


    df['scenario'] = scenario_name 
    df = df[['scenario','peak', 'mode', 'i', 'j', 'total_mins', 'tolls', 'dist','cong_time', 'losd_time']]
    df.i = df.i.astype(int)
    df.j = df.j.astype(int)

    # proj_path = os.path.dirname(_m.Modeller().desktop.project.path)
    proj_path = 'C://Users//rkeller//Desktop//mp_t7_disagg//auto'
    file_path = os.path.join(proj_path, '{}_disagg_auto.txt'.format(scenario_name))
    current_time = datetime.datetime.now()
    print("writing {} at {}".format(file_path, current_time))
    df.to_csv(file_path, sep = '\t', index=False, header=False)
    current_time = datetime.datetime.now()
    print("completed writing {} at {}".format(file_path, current_time))
    del df



def export_transit(eb, scenario_name):
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

    df = util.get_pd_ij_df(eb)
    df['AmBusTime'] = AmBusIvtt + AmBusWait + AmBusAux
    df['MdBusTime'] = MdBusIvtt + MdBusWait + MdBusAux
    df['PmBusTime'] = PmBusIvtt + PmBusWait + PmBusAux
    df['AmRailTime'] = AmRailIvtt + AmRailWait + AmRailAux + AmRailIvttBus
    df['MdRailTime'] = MdRailIvtt + MdRailWait + MdRailAux + MdRailIvttBus
    df['PmRailTime'] = PmRailIvtt + PmRailWait + PmRailAux + PmRailIvttBus
    df['AmWceTime'] = AmWceIvtt + AmWceWait + AmWceAux + AmWceIvttBus + AmWceIvttRail
    df['PmWceTime'] = PmWceIvtt + PmWceWait + PmWceAux + PmWceIvttBus + PmWceIvttRail
    print "built df time"


    del AmBusIvtt, AmBusWait, AmBusAux
    del MdBusIvtt, MdBusWait, MdBusAux
    del PmBusIvtt, PmBusWait, PmBusAux

    del AmRailIvtt, AmRailWait, AmRailAux, AmRailIvttBus
    del MdRailIvtt, MdRailWait, MdRailAux, MdRailIvttBus
    del PmRailIvtt, PmRailWait, PmRailAux, PmRailIvttBus

    del AmWceIvtt, AmWceWait, AmWceAux, AmWceIvttBus, AmWceIvttRail
    del PmWceIvtt, PmWceWait, PmWceAux, PmWceIvttBus, PmWceIvttRail    

    df = pd.melt(df, id_vars = ['i','j'], var_name = 'timeMeasure', value_name = 'time_min')
    dfTimeMode = df['timeMeasure'].str.extract(r'(?P<peak>[A|M|P]{1}[m|d])(?P<mode>Bus|Rail|Wce)Time')
    df = pd.concat([dfTimeMode, df], axis = 1)
    df.drop(['timeMeasure'], axis = 1, inplace=True)
    del dfTimeMode


    # Fares
    dfFare = util.get_pd_ij_df(eb)
    dfFare['AmBusFare'] = util.get_matrix_numpy(eb, "AmBusFare").flatten()
    dfFare['MdBusFare'] = util.get_matrix_numpy(eb, "MdBusFare").flatten()
    dfFare['PmBusFare'] = util.get_matrix_numpy(eb, "PmBusFare").flatten()
    dfFare['AmRailFare'] = util.get_matrix_numpy(eb, "AmRailFare").flatten()
    dfFare['MdRailFare'] = util.get_matrix_numpy(eb, "MdRailFare").flatten()
    dfFare['PmRailFare'] = util.get_matrix_numpy(eb, "PmRailFare").flatten()
    dfFare['AmWceFare'] = util.get_matrix_numpy(eb, "AmWceFare").flatten()
    dfFare['PmWceFare'] = util.get_matrix_numpy(eb, "PmWceFare").flatten()

    dfFare = pd.melt(dfFare, id_vars = ['i','j'], var_name = 'timeMeasure', value_name = 'fare')
    dfTimeMode = dfFare['timeMeasure'].str.extract(r'(?P<peak>[A|M|P]{1}[m|d])(?P<mode>Bus|Rail|Wce)Fare')
    dfFare = pd.concat([dfTimeMode, dfFare], axis = 1)
    dfFare.drop('timeMeasure', axis = 1, inplace=True)
    del dfTimeMode

    ###########
    # Prep Output
    ############
 
    df = pd.merge(df, dfFare, left_on=['peak','mode','i','j'], right_on=['peak','mode','i','j'])


    # df = df[['scenario','peak', 'mode', 'i', 'j', 'total_mins', 'tolls', 'dist','cong_time', 'losd_time']]
    df['scenario'] = scenario_name 
    df = df[['scenario','peak', 'mode', 'i', 'j', 'time_min', 'fare']]
    # add blank fields to match with auto formate
    # makes upload to sql server easier
    df['dist'] = ''
    df['cong_time'] = ''
    df['losd_time'] = ''


    df.i = df.i.astype(int)
    df.j = df.j.astype(int)

    proj_path = 'C://Users//rkeller//Desktop//mp_t7_disagg//transit'
    file_path = os.path.join(proj_path, '{}_disagg_transit.txt'.format(scenario_name))
    current_time = datetime.datetime.now()
    print("writing {} at {}".format(file_path, current_time))
    df.to_csv(file_path, sep = '\t', index=False, header=False)

    del df



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
        
        eb.open()
        eb = _m.Modeller().emmebank
        current_time = datetime.datetime.now()
        print('Starting export of {} at {}\n'.format(title, current_time))

        try:
            # export_auto(eb, title)
            export_transit(eb, title)
            print("Scenario {} export complete.".format(title))
        
        except Exception as e:
            print("Scenario {} export failed.".format(title), e)