##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.emme.xxxx
##--Purpose:
##---------------------------------------------------------------------
import inro.modeller as _m
import csv
import os
import numpy as np
import pandas as pd
import traceback as _traceback

class ModeChoiceUtilities(_m.Tool()):
    tool_run_msg = ""

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Trip Distribution Model"
        pb.description = "Trip Distribution Model"
        pb.branding_text = "TransLink"
        pb.runnable = False

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

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
        util = _m.Modeller().tool("translink.emme.util")

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
        util = _m.Modeller().tool("translink.emme.util")

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


    def AutoAvail(self, Distance, Utility, AvailDict):
        LrgU     = -99999.0
        return np.where(Distance>AvailDict['AutDist'], Utility , LrgU)

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
                        (Df['BusBrd']<AvailDict['TranBrd']) &
                        (Df['IntZnl']!=1)                   &
                        (np.logical_and(Df['BusTot']>=AvailDict['BRTotLow'], Df['BusTot']<=AvailDict['BRTotHig'])),
                         Utility, LrgU)

    def RailAvail(self, Df, Utility, AvailDict):

        LrgU     = -99999.0
        return np.where((Df['RalIVR']>AvailDict['TranIVT']) &
                        (Df['RalWat']<AvailDict['TranWat']) &
                        (Df['RalAux']<AvailDict['TranAux']) &
                        (Df['RalBrd']<AvailDict['TranBrd']) &
                        (Df['IntZnl']!=1)                   &
                        (np.logical_and(Df['RalTot']>=AvailDict['BRTotLow'], Df['RalTot']<=AvailDict['BRTotHig'])),
                         Utility, LrgU)

    def WCEAvail(self, Df, Utility, AvailDict):

        LrgU     = -99999.0
        return np.where((Df['WCEIVW']>AvailDict['TranIVT']) &
                        (Df['WCEWat']<AvailDict['WCEWat'])  &
                        (Df['WCEAux']<AvailDict['WCEAux'])  &
                        (Df['WCEBrd']<AvailDict['TranBrd']) &
                        (Df['IntZnl']!=1)                   &
                        (np.logical_and(Df['WCETot']>=AvailDict['WCTotLow'], Df['WCETot']<=AvailDict['WCTotHig'])),
                         Utility, LrgU)

    def BAuAvail(self, Df, Utility, AvailDict):

        LrgU     = -99999.0
        return np.where((Df['BusIVT']>AvailDict['TranIVT']) &
                        (Df['BusWat']<AvailDict['TranWat']) &
                        (Df['BusAux']<AvailDict['TranAux']) &
                        (Df['BusBrd']<AvailDict['TranBrd']) &
                        (Df['BAuTim']>AvailDict['PRAutTim'])&
                        (Df['IntZnl']!=1)                   &
                        (np.logical_and(Df['BAuTot']>=AvailDict['BRTotLow'], Df['BAuTot']<=AvailDict['BRTotHig'])),
                         Utility, LrgU)

    def RAuAvail(self, Df, Utility, AvailDict):

        LrgU     = -99999.0
        return np.where((Df['RalIVR']>AvailDict['TranIVT']) &
                        (Df['RalWat']<AvailDict['TranWat']) &
                        (Df['RalAux']<AvailDict['TranAux']) &
                        (Df['RalBrd']<AvailDict['TranBrd']) &
                        (Df['RAuTim']>AvailDict['PRAutTim'])&
                        (Df['IntZnl']!=1)                   &
                        (np.logical_and(Df['RAuTot']>=AvailDict['BRTotLow'], Df['RAuTot']<=AvailDict['BRTotHig'])),
                         Utility, LrgU)

    def WAuAvail(self, Df, Utility, AvailDict):

        LrgU     = -99999.0
        return np.where((Df['WCEIVW']>AvailDict['TranIVT']) &
                        (Df['WCEWat']<AvailDict['WCEWat'])  &
                        (Df['WCEAux']<AvailDict['WCEAux'])  &
                        (Df['WCEBrd']<AvailDict['TranBrd']) &
                        (Df['WAuTim']>AvailDict['PRAutTim'])&
                        (Df['IntZnl']!=1)                   &
                        (np.logical_and(Df['WAuTot']>=AvailDict['WCTotLow'], Df['WAuTot']<=AvailDict['WCTotHig'])),
                         Utility , LrgU)

    @_m.logbook_trace("Impedance Calc")
    def ImpCalc(self, eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, Distance):

        util = _m.Modeller().tool("translink.emme.util")
        input_path = util.get_input_path(eb)

        for i in range (len(imp_list)):

            A = util.get_matrix_numpy(eb, Logsum[i])

            Imp = (LS_Coeff*A+LambdaList[i]*Distance
                  +AlphaList[i]*pow(Distance, 2)
                  +GammaList[i]*pow(Distance, 3))


            Imp = np.exp(Imp)
            util.set_matrix_numpy(eb, imp_list[i], Imp)

        del Distance, A, Imp

    @_m.logbook_trace("Check Convergence")
    def Check_Convergence(self, eb, NoSeg, out_list, Distance_flat, AvgDistMod, AvgDistModSq, AvgDistModCu, df, RunType):

        util = _m.Modeller().tool("translink.emme.util")
        SumTrip = 0

        for i in range (NoSeg):


            TDMat = util.get_matrix_numpy(eb, out_list[i]).flatten()
            AvgDistMod[i]   = np.sum(np.multiply(Distance_flat,TDMat))/np.sum(TDMat)
            AvgDistModSq[i] = np.sum(np.multiply(np.power(Distance_flat,2),TDMat))/np.sum(TDMat)
            AvgDistModCu[i] = np.sum(np.multiply(np.power(Distance_flat,3),TDMat))/np.sum(TDMat)
            SumTrip += TDMat

        df['AvgDistMod']   = AvgDistMod
        df['AvgDistModSq'] = AvgDistModSq
        df['AvgDistModCu'] = AvgDistModCu
        AvgDistTot = np.sum(np.multiply(Distance_flat,SumTrip))/np.sum(SumTrip)


        # Check convergence
        Df_DistRat = pd.DataFrame({'AvgDistRat' :   abs(df['AvgDistMod']/df['avgTL'] - 1),
                                   'AvgDistsqdRat': abs(df['AvgDistModSq']/df['avgTLsqd'] - 1),
                                   'AvgDistcubRat': abs(df['AvgDistModCu']/df['avgTLcub'] - 1)})

        if RunType == 1:

            MaxValue = np.max(abs(df['AvgDistMod']/df['avgTL'] - 1))

        if RunType == 2:

            MaxValue = max(np.max(abs(df['AvgDistMod']/df['avgTL'] - 1)),
                           np.max(abs(df['AvgDistModSq']/df['avgTLsqd'] - 1)))


        if RunType == 3:

            MaxValue = max(np.max(abs(df['AvgDistMod']/df['avgTL'] - 1)),
                           np.max(abs(df['AvgDistModSq']/df['avgTLsqd'] - 1)),
                           np.max(abs(df['AvgDistModCu']/df['avgTLcub'] - 1)))

        print MaxValue
        return AvgDistTot, MaxValue, df

