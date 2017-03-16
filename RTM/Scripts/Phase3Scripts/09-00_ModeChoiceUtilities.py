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
                        (Df['BAuTim']>AvailDict['PRAutTim'])&
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
                        (Df['RAuTim']>AvailDict['PRAutTim'])&
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
                        (Df['WAuTim']>AvailDict['PRAutTim'])&
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
