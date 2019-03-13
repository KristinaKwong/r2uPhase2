##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage2.modechoiceutils
##--Purpose:
##---------------------------------------------------------------------
import inro.modeller as _m
import csv
import numpy as np
import pandas as pd

class ModeChoiceUtilities(_m.Tool()):

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Trip Distribution Model"
        pb.description = "Trip Distribution Model"
        pb.branding_text = "TransLink"
        pb.runnable = False
        return pb.render()

    def __call__(self):
        pass

    @_m.logbook_trace("Run origin constrained matrix balancing")
    def one_dim_matrix_balancing(self, eb, mo_list, md_list, impedance_list, output_demands):
        """Perform a singly-constrained matrix balancing to production totals.

        Calculate an output demand from an input production total and a utility matrix respecting
        the production totals only. Zones with zero productions will have zero origin demand in the
        final matrix. Zones with zero utility to all destinations will have zero demand in the final
        matrix.

        Arguments:
        eb -- the emmebank to calculate in
        mo_list -- a list of production totals (moXX)
        md_list -- a list of attraction totals to bias the impedence matrices(mdXX)
        impedance_list -- a list of impendences/utilities to use for balancing (mfXX)
        output_demands -- the list of matrices to hold the output demands (mfXX)
        """
        util = _m.Modeller().tool("translink.util")

        # calculate the impedences weighted by target attractions
        attractions = util.get_matrix_numpy(eb, md_list[0])
        weighted_imp = []
        for i in range(0, len(mo_list)):
            mf_imp = util.get_matrix_numpy(eb, impedance_list[i])
            weighted_imp.append(mf_imp * attractions)

        #calculate OD-demands for each production type
        demands = []
        for i in range(0, len(weighted_imp)):
            # sum the weighted impedence matrix across all columns
            rowsum = np.sum(weighted_imp[i], axis=1)
            # where the sum of impedence was zero, replace with 1
            rowsum[rowsum == 0.0] = 1.0
            # transpose to be a column vector (mo)
            rowsum = rowsum.reshape(rowsum.shape[0], 1)
            # calculate singly-constrained demand
            productions = util.get_matrix_numpy(eb, mo_list[i])
            demand = productions * weighted_imp[i] / rowsum

            demands.append(demand)

        # write the output demands
        for i in range(0, len(output_demands)):
            util.set_matrix_numpy(eb, output_demands[i], demands[i])

    @_m.logbook_trace("Run matrix balancing to multiple productions")
    def two_dim_matrix_balancing(self, eb, mo_list, md_list, impedance_list, output_demands):
        util = _m.Modeller().tool("translink.util")

        max_iterations = int(util.get_matrix_numpy(eb, "msIterDist"))

        rel_error = eb.matrix("msRelErrDist").data
        # loops through mo_list for any list items that are expressions
        #  (contains "+") adding mo matrices up for aggregation.
        # Performs calulation and saves result in a scratch matrix.
        # then inserts scratch matrix instead of the initial expresssion
#        specs = []
#        temp_matrices = []
#        for i in range(0, len(mo_list)):
#            if "+" in mo_list[i]:
#                temp_id = eb.available_matrix_identifier("ORIGIN")
#                util.initmat(eb, temp_id, "scratch", "scratch matrix for two-dim balance", 0)
#                temp_matrices.append(temp_id)
#
#                specs.append(util.matrix_spec(temp_id, mo_list[i]))
#                mo_list[i] = temp_id
#        util.compute_matrix(specs)

        #Begin balmprod
        balancing_multiple_productions = _m.Modeller().tool("inro.emme.matrix_calculation.balancing_multiple_productions")
        spec_dict_matbal = {
            "type": "MATRIX_BALANCING_MULTIPLE_PRODUCTIONS",
            "destination_totals": "destinations",
            "classes": [],
            "destination_coefficients": None,
            "max_iterations": max_iterations,
            "max_relative_error": rel_error
        }

        #assign values for matrix balancing
        spec_dict_matbal["destination_totals"] = md_list[0]
        for mo, output, mf in zip(mo_list, output_demands, impedance_list):
            class_spec = {
                "origin_totals": mo,
                "od_values_to_balance": mf,
                "results": {
                    "origin_coefficients": None,
                    "od_balanced_values": output
                }
            }
            spec_dict_matbal["classes"].append(class_spec)
        balancing_multiple_productions(spec_dict_matbal)

        # Delete the temporary mo-matrices
#        for mat_id in temp_matrices:
#            util.delmat(eb, mat_id)

    @_m.logbook_trace("Impedance Calc")
    def ImpCalc(self, eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, Distance, Kij, Bridge_Pen, Bridge_Factor):
        util = _m.Modeller().tool("translink.util")

        Bridge_Pen_Mat = util.get_matrix_numpy(eb, Bridge_Pen)

        Distance = Distance + Bridge_Factor*Bridge_Pen_Mat

        for i in range (len(imp_list)):

            A = util.get_matrix_numpy(eb, Logsum[i])

            Imp = (LS_Coeff*A+LambdaList[i]*Distance
                  +AlphaList[i]*pow(Distance, 2)
                  +GammaList[i]*pow(Distance, 3))


            Imp = (np.exp(Imp))*Kij
            util.set_matrix_numpy(eb, imp_list[i], Imp)

        del Distance, A, Imp

    def AutoAvail(self, Cost, Utility, AvailDict):
        LrgU     = -99999.0
        return np.where(Cost>AvailDict['AutCost'], Utility , LrgU)

    def WalkAvail(self, Distance, Utility, AvailDict):
        LrgU     = -99999.0
        return np.where(Distance<=AvailDict['WlkDist'], Utility , LrgU)

    def BikeAvail(self, Distance, Utility, AvailDict):
        LrgU     = -99999.0
        return np.where(Distance<=AvailDict['BikDist'], Utility , LrgU)


    def BusAvail(self, Df, Utility, AvailDict):

        LrgU     = -99999.0
        return np.where((Df['BusIVT']>AvailDict['TranIVT']) &
                        (Df['BusWat']<AvailDict['TranWat']) &
                        (Df['BusAux']<AvailDict['TranAux']) &
                        (Df['BusBrd']<=AvailDict['TranBrd']) &
                        (Df['IntZnl']!=1)                   &
                        (np.logical_and(Df['BusTot']>=AvailDict['BRTotLow'], Df['BusTot']<=AvailDict['BRTotHig'])),
                         Utility, LrgU)

    def RailAvail(self, Df, Utility, AvailDict):

        Tiny = 0.0000001
        LrgU     = -99999.0
        return np.where((Df['RalIVR']>AvailDict['TranIVT']) &
                        (Df['RalWat']<AvailDict['TranWat']) &
                        (Df['RalAux']<AvailDict['TranAux']) &
                        (Df['RalBrd']<=AvailDict['TranBrd']) &
                        (Df['IntZnl']!=1)                   &
                        (np.logical_or(Df['RalTot']<AvailDict['r_time'], Df['RalTot']/(Df['BusTot'] + Tiny)<AvailDict['br_ratio'])) &
                        (np.logical_and(Df['RalTot']>=AvailDict['BRTotLow'], Df['RalTot']<=AvailDict['BRTotHig'])),
                         Utility, LrgU)

    def WCEAvail(self, Df, Utility, AvailDict):

        Tiny = 0.0000001
        LrgU     = -99999.0
        return np.where((Df['WCEIVW']>AvailDict['TranIVT']) &
                        (Df['WCEWat']<AvailDict['WCEWat'])  &
                        (Df['WCEAux']<AvailDict['WCEAux'])  &
                        (Df['WCEBrd']<=AvailDict['TranBrd']) &
                        (Df['IntZnl']!=1)                   &
                        (np.logical_and(Df['WCETot']/(Df['BusTot'] + Tiny)<AvailDict['brw_ratio'], Df['WCETot']/(Df['RalTot'] + Tiny)<AvailDict['brw_ratio'])) &
                        (np.logical_and(Df['WCETot']>=AvailDict['WCTotLow'], Df['WCETot']<=AvailDict['WCTotHig'])),
                         Utility, LrgU)

    def BAuAvail(self, Df, Utility, AvailDict):

        Tiny = 0.0000001
        LrgU     = -99999.0
        return np.where((Df['BusIVT']>AvailDict['TranIVT']) &
                        (Df['BusWat']<AvailDict['TranWat']) &
                        (Df['BusAux']<AvailDict['TranAux']) &
                        (Df['BusBrd']<=AvailDict['TranBrd']) &
                        (Df['BAuTim']>AvailDict['PRAutTim_min'])&
                        (Df['BAuTim']<=AvailDict['PRAutTim_max'])&
                        (np.logical_or(Df['BusFar']<=1.05*Df['WBusFar'], Df['WBusFar']==0))&
                        (Df['BAuTim']/(Df['BusIVT']+Tiny)<=AvailDict['pr_ratio'])&
                        (Df['IntZnl']!=1)                   &
                        (np.logical_and(Df['BAuTot']>=AvailDict['BRTotLow'], Df['BAuTot']<=AvailDict['BRTotHig'])),
                         Utility, LrgU)

    def RAuAvail(self, Df, Utility, AvailDict):

        Tiny = 0.0000001
        LrgU     = -99999.0
        return np.where((Df['RalIVR']>AvailDict['TranIVT']) &
                        (Df['RalWat']<AvailDict['TranWat']) &
                        (Df['RalAux']<AvailDict['TranAux']) &
                        (Df['RalBrd']<=AvailDict['TranBrd']) &
                        (Df['RAuTim']>AvailDict['PRAutTim_min'])&
                        (Df['RAuTim']<=AvailDict['PRAutTim_max'])&
                        (np.logical_or(Df['RalFar']<=1.05*Df['WRalFar'], Df['WRalFar']==0))&
                        (np.logical_or(Df['WRalIVR'] == 0, Df['RAuTot'] <= 1.5*Df['RalTot']))&
                        (np.logical_or(Df['BusIVT'] == 0, Df['RAuTot'] <= 1.5*Df['BusTot']))&
                        (Df['RAuTim']/(Df['RalIVB']+ Df['RalIVR'] + Tiny)<=AvailDict['pr_ratio'])&
                        (Df['IntZnl']!=1)                   &
                        (np.logical_and(Df['RAuTot']>=AvailDict['BRTotLow'], Df['RAuTot']<=AvailDict['BRTotHig'])),
                         Utility, LrgU)

    def WAuAvail(self, Df, Utility, AvailDict):
        Tiny = 0.0000001
        LrgU     = -99999.0
        return np.where((Df['WCEIVW']>AvailDict['TranIVT']) &
                        (Df['WCEWat']<AvailDict['WCEWat'])  &
                        (Df['WCEAux']<AvailDict['WCEAux'])  &
                        (Df['WCEBrd']<=AvailDict['TranBrd']) &
                        (Df['WAuTim']>AvailDict['PRAutTim_min'])&
                        (Df['WAuTim']<=AvailDict['PRAutTim_max'])&
                        (np.logical_or(Df['WCEFar']<=1.05*Df['WWCEFar'], Df['WWCEFar']==0))&
                        (np.logical_or(Df['WWCEIVW'] == 0, Df['WAuTot'] <= 1.5*Df['WCETot']))&
                        (np.logical_or(Df['WRalIVR'] == 0, Df['WAuTot'] <= 1.5*Df['RalTot']))&
                        (np.logical_or(Df['BusIVT'] == 0, Df['WAuTot'] <= 1.5*Df['BusTot']))&
                        (Df['WAuTim']/(Df['WCEIVB']+ Df['WCEIVR'] + Df['WCEIVW'] + Tiny)<=AvailDict['pr_ratio'])&
                        (Df['IntZnl']!=1)                   &
                        (np.logical_and(Df['WAuTot']>=AvailDict['WCTotLow'], Df['WAuTot']<=AvailDict['WCTotHig'])),
                         Utility , LrgU)

    def Demand_Summary(self, df, purp, period, demand_list, mode_list):


        for mode in range (len(demand_list)):

            df[mode_list[mode]] = demand_list[mode].flatten()


        df_gy = df.groupby(['gy_i', 'gy_j']).sum().reset_index()
        df_gy = pd.melt(df_gy, id_vars=['gy_i', 'gy_j'] , value_vars =mode_list)
        df_gy.rename(columns={'variable': 'mode', 'value': 'trips'}, inplace=True)
        df_gy["period"] = period
        df_gy["purpose"] = purp

        return df_gy

    def AP_PA_Factor(self, eb, purpose, mode, peakperiod, geo='A',minimum_value=0):
        util = _m.Modeller().tool("translink.util")
        sql = "SELECT * from timeSlicingFactors WHERE purpose = '{purp}' and mode = '{mde}' and peakperiod = '{peak}' and geo = '{g}' ".format(purp = purpose,
                                                                                                                          mde=mode,
                                                                                                                         peak=peakperiod,
                                                                                                                         g=geo)
        conn = util.get_rtm_db(eb)
        ts_df = pd.read_sql(sql, conn)
        conn.close()

        Fct_PA = self.factor_floor(ts_df.loc[(ts_df['direction'] == 'PtoA'), 'shares'].values, minimum_value)
        Fct_AP = self.factor_floor(ts_df.loc[(ts_df['direction'] == 'AtoP'), 'shares'].values, minimum_value)

        return Fct_PA, Fct_AP

    def factor_floor(self, factor, minimum_value):
        if len(factor) == 0:
            # this is to return a numpy float 64 object to ensure numpy error handling
            x = np.arange(1, dtype=np.float)
            x[0] = minimum_value
            return x[0]
        else:
            return factor[0]

    def ts_mat(self, df, factors, min_val, purp, time_period, paap, notaz):
        fac_sub = factors[(factors.purpose == purp) & (factors.peakperiod == time_period) & (factors.direction == paap)]
        dfa = pd.merge(df, fac_sub, how='left', left_on = ['gb_i','IX'], right_on = ['gb_i','IX'], suffixes=('','fac'))
        dfa['shares'].fillna(min_val, inplace = True)
        mat = dfa['shares'].values.reshape(notaz,notaz)
        del dfa
        return mat

    def Calc_Prob(self, eb, Dict, Logsum, Th, trip_attr, LS_Coeff, modes_dict, taz_list):

        util = _m.Modeller().tool("translink.util")
        Tiny=0.000001
        NoTAZ = len(util.get_matrix_numpy(eb, "zoneindex"))
        attr_mat = util.get_matrix_numpy(eb, trip_attr).reshape(1, NoTAZ) + np.zeros((NoTAZ, 1))
        df_final = pd.DataFrame()

        L_Nst = {key:sum(np.exp(nest)) for key,nest in Dict.items()}
        U_Nst  = {key:pow(nest,Th) for key,nest in L_Nst.items()}
        L_Nst = {key:np.where(value == 0, Tiny, value) for key,value in L_Nst.items()}

        for ls in modes_dict.items():
            temp_dict ={x: U_Nst[x] for x in ls[1] if x in U_Nst}
            F_Utl = sum(temp_dict.values())
            F_Utl = np.where(F_Utl == 0, Tiny, F_Utl)

            if ls[0] == 'All':
                util.set_matrix_numpy(eb, Logsum, np.log(F_Utl))
                Prob_Dict = {key:np.exp(nest)/L_Nst[key]*temp_dict[key]/F_Utl for key, nest in Dict.items()}

        ### Calculate accessibilities
            F_Utl = LS_Coeff*np.log(F_Utl)
            access = np.log(np.sum(attr_mat*np.exp(F_Utl), axis = 1))
            df = pd.DataFrame()
            df['TZ'], df['mode'], df['Accessibility_Value']  = taz_list, ls[0], access
            df_final = pd.concat([df_final, df])

        prp, sg = Logsum.split('LS')
        df_final['purpose'] = prp
        dct1 = {'income':['I', 1], 'autos':['A', 1]}

        for keys, values in dct1.items():
            if sg.find(values[0]) == -1:
                df_final[keys] = 9
            else:
                df_final[keys] = sg[sg.find(values[0]) + values[1]]

        if sg.find('I') == -1:
            df_final['income'] = 1
            df_temp = df_final.copy()

            for i in range (2, 4):
                df_temp['income'] = i
                df_final = pd.concat([df_final, df_temp])

        conn = util.get_db_byname(eb, "rtm.db")

        if Logsum == 'HbWLSI1A0':
            write_type = 'replace'
        else:
            write_type = 'append'

        df_final.to_sql(name='logsum_accessibilities', con=conn, flavor='sqlite', index=False, if_exists=write_type)
        conn.close()

        return Prob_Dict

    def Calc_Demand(self, eb, Dict, mat_name, write_att_demand = True):

        util = _m.Modeller().tool("translink.util")
        Dem = util.get_matrix_numpy(eb, mat_name)
        taz_list = util.get_matrix_numpy(eb, 'zoneindex', reshape = False)
        Seg_Dict = {key:Dem*nest_len for key, nest_len in Dict.items()}

        dfnames, df_att = pd.DataFrame(), pd.DataFrame()

        dfnames['md1'] = ['SOV','HOV','HOV','WTra','WTra','WTra','DTra','DTra','DTra',
                     'KTra','KTra','KTra','TTra','TTra','TTra','Acti','Acti','TNC', 'Auto']
        dfnames['md2'] = [0,0,1,0,1,2,0,1,2,0,1,2,0,1,2,0,1,0,0]
        dfnames['mode'] = ['SOV','HV2','HV3','Bus','Rail','WCE','BAu','RAu','WAu',
                    'BKr','RKr','WKr','BTnc','RTnc','WTnc','Walk','Bike','TNC', 'Auto']
        dfnames['mode_agg'] = ['Auto','Auto','Auto','Transit','Transit','Transit','Transit','Transit','Transit',
                    'Transit','Transit','Transit','Transit','Transit','Transit','Active','Active','TNC', 'Auto']

        for keys in Seg_Dict.items():
            for i in range(len(keys[1])):
                mod1 = keys[0]
                mod2 = i
                df_j = pd.DataFrame()
                df_j['tz'], df_j['mode1'], df_j['mode2'], df_j['trips'] = taz_list, mod1, mod2, np.sum(keys[1][i], axis = 0)
                df_att = pd.concat([df_att, df_j])

        df_att = pd.merge(df_att, dfnames, how = 'left', left_on = ['mode1', 'mode2'], right_on = ['md1', 'md2'])
        purp_name, segment = mat_name.split('-')
        df_att['purp'] = purp_name[:-1]
        df_att['segment'] = segment[1:]

        df_triptots = df_att.groupby(['purp', 'segment', 'mode']).sum().reset_index()
        df_triptots = df_triptots[['purp', 'segment', 'mode', 'trips']]
        df_att = df_att[['tz', 'purp', 'mode_agg', 'trips']]

        prp = 'hbo'
        sg  = 0

        if purp_name[:-1] == 'HbW':
            prp = 'hbw'


        df_att['purp'] = prp


        conn = util.get_db_byname(eb, "trip_summaries.db")

        if mat_name == 'HbWP-AI1A0':

            write_type = 'replace'

        else:

            write_type = 'append'

        df_triptots.to_sql(name='trip_tots', con=conn, flavor='sqlite', index=False, if_exists=write_type)

        if write_att_demand == True:
            df_att.to_sql(name='trip_att_tots', con=conn, flavor='sqlite', index=False, if_exists=write_type)

        conn.close()

        return Seg_Dict
