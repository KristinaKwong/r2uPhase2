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

# Define Availability Thresholds
AutDist  = 0.0
WlkDist  = 5.0
BikDist  = 25.0
TranIVT  = 1.0
TranWat  = 30.0
TranAux  = 30.0
TranBrd  = 6.0
BRTotLow = 10.0
BRTotHig = 120.0
WCTotLow = 30.0
WCTotHig = 130.0
PRAutTim = 0.0
LrgU     = -99999.0

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

    @_m.logbook_trace("Impedance Calc")
    def ImpCalc(self, eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, Dist):

        util = _m.Modeller().tool("translink.emme.util")
        input_path = util.get_input_path(eb)

        Distance = util.get_matrix_numpy(eb, Dist)
        for i in range (len(imp_list)):

            A = util.get_matrix_numpy(eb, Logsum[i])
            Imp = LS_Coeff*A+LambdaList[i]*Distance+AlphaList[i]*pow(Distance, 2)+GammaList[i]*pow(Distance, 3)
            Imp = np.exp(Imp)
            util.set_matrix_numpy(eb, imp_list[i], Imp)

        del Distance, A, Imp

    @_m.logbook_trace("Run origin constrained matrix balancing")
    def one_dim_matrix_balancing(self, eb, productions_list, impedance_list, output_demands):
        """Perform a singly-constrained matrix balancing to production totals.

        Calculate an output demand from an input production total and a utility matrix respecting
        the production totals only. Zones with zero productions will have zero origin demand in the
        final matrix. Zones with zero utility to all destinations will have zero demand in the final
        matrix.

        Arguments:
        eb -- the emmebank to calculate in
        productions_list -- a list of production totals (moXX)
        impedance_list -- a list of impendences/utilities to use for balancing (mfXX)
        output_demands -- the list of matrices to hold the output demands (mfXX)
        """
        util = _m.Modeller().tool("translink.emme.util")

        temp_matrices = []

        specs = []
        for i in range(0, len(productions_list)):
            # Initialize a temporary mo to calculate origin totals
            temp_id = eb.available_matrix_identifier("ORIGIN")
            temp_matrices.append(temp_id)
            util.initmat(eb, temp_id, "scratch", "scratch matrix in one-dimensional balancing", 0)

            # Calculate the sum of the impedence list to calculate an alpha factor
            spec = util.matrix_spec(temp_id, impedance_list[i])
            spec["aggregation"] = {"origins": None, "destinations": "+"}
            specs.append(spec)

            # Divide the total impedence into the productions to produce an alpha value
            # Avoid dividing by zero by adding one to origins with utility sum of zero
            spec = util.matrix_spec(temp_id, "%s/(%s+(%s.eq.0))" % (productions_list[i], temp_id, temp_id))
            specs.append(spec)

            # Multiply the alpha value times the impedence to produce an output demand
            spec = util.matrix_spec(output_demands[i], "%s * %s" % (temp_id, impedance_list[i]))
            specs.append(spec)

        util.compute_matrix(specs)

        # Delete the temporary mo-matrices
        for mat_id in temp_matrices:
            util.delmat(eb, mat_id)

    def AutoAvail(self, Distance, Utility):

        return np.where(Distance>AutDist,  Utility ,LrgU)

    def WalkAvail(self, Distance, Utility):

        return np.where(Distance<=WlkDist,  Utility ,LrgU)

    def BikeAvail(self, Distance, Utility):

        return np.where(Distance<=BikDist,  Utility , LrgU)


    def BusAvail(self, Df, Utility):

        return np.where((Df['BusIVT']>TranIVT) &
                        (Df['BusWat']<TranWat) &
                        (Df['BusAux']<TranAux) &
                        (Df['BusBrd']<TranBrd) &
                        (Df['IntZnl']!=1)      &                        
                        (np.logical_and(Df['BusTot']>=BRTotLow, Df['BusTot']<=BRTotHig)),
                         Utility, LrgU)

    def RailAvail(self, Df, Utility):

        return np.where((Df['RalIVR']>TranIVT) &
                        (Df['RalWat']<TranWat) &
                        (Df['RalAux']<TranAux) &
                        (Df['RalBrd']<TranBrd) &
                        (Df['IntZnl']!=1)      &                          
                        (np.logical_and(Df['RalTot']>=BRTotLow, Df['RalTot']<=BRTotHig)),
                         Utility, LrgU)

    def WCEAvail(self, Df, Utility):

        return np.where((Df['WCEIVW']>TranIVT) &
                        (Df['WCEWat']<TranWat) &
                        (Df['WCEAux']<TranAux) &
                        (Df['WCEBrd']<TranBrd) &
                        (Df['IntZnl']!=1)      &                          
                        (np.logical_and(Df['WCETot']>=WCTotLow, Df['WCETot']<=WCTotHig)),
                         Utility, LrgU)

    def BAuAvail(self, Df, Utility):

        return np.where((Df['BusIVT']>TranIVT) &
                        (Df['BusWat']<TranWat) &
                        (Df['BusAux']<TranAux) &
                        (Df['BusBrd']<TranBrd) &
                        (Df['BAuTim']>PRAutTim)&
                        (Df['IntZnl']!=1)      &                         
                        (np.logical_and(Df['BAuTot']>=BRTotLow, Df['BAuTot']<=BRTotHig)),
                         Utility, LrgU)

    def RAuAvail(self, Df, Utility):

        return np.where((Df['RalIVR']>TranIVT) &
                        (Df['RalWat']<TranWat) &
                        (Df['RalAux']<TranAux) &
                        (Df['RalBrd']<TranBrd) &
                        (Df['RAuTim']>PRAutTim)&
                        (Df['IntZnl']!=1)      &                          
                        (np.logical_and(Df['RAuTot']>=BRTotLow, Df['RAuTot']<=BRTotHig)),
                         Utility, LrgU)

    def WAuAvail(self, Df, Utility):

        return np.where((Df['WCEIVW']>TranIVT) &
                        (Df['WCEWat']<TranWat) &
                        (Df['WCEAux']<TranAux) &
                        (Df['WCEBrd']<TranBrd) &
                        (Df['WAuTim']>PRAutTim)&
                        (Df['IntZnl']!=1)      &                          
                        (np.logical_and(Df['WAuTot']>=WCTotLow, Df['WAuTot']<=WCTotHig)),
                         Utility , LrgU)

    @_m.logbook_trace("Run matrix balancing to multiple productions")
    def two_dim_matrix_balancing(self, eb, mo_list, md_list, impedance_list, output_list, max_iterations):
        util = _m.Modeller().tool("translink.emme.util")

        # loops through mo_list for any list items that are expressions
        #  (contains "+") adding mo matrices up for aggregation.
        # Performs calulation and saves result in a scratch matrix.
        # then inserts scratch matrix instead of the initial expresssion
        specs = []
        temp_matrices = []
        for i in range(0, len(mo_list)):
            if "+" in mo_list[i]:
                temp_id = eb.available_matrix_identifier("ORIGIN")
                util.initmat(eb, temp_id, "scratch", "scratch matrix for two-dim balance", 0)
                temp_matrices.append(temp_id)

                specs.append(util.matrix_spec(temp_id, mo_list[i]))
                mo_list[i] = temp_id
        util.compute_matrix(specs)

        #Begin balmprod
        balancing_multiple_productions = _m.Modeller().tool("inro.emme.matrix_calculation.balancing_multiple_productions")
        spec_dict_matbal = {
            "type": "MATRIX_BALANCING_MULTIPLE_PRODUCTIONS",
            "destination_totals": "destinations",
            "classes": [],
            "destination_coefficients": None,
            "max_iterations": max_iterations,
            "max_relative_error": 0.0001
        }

        #assign values for matrix balancing
        spec_dict_matbal["destination_totals"] = md_list[0]
        for mo, output in zip(mo_list, output_list):
            class_spec = {
                "origin_totals": mo,
                "od_values_to_balance": impedance_list[0],
                "results": {
                    "origin_coefficients": None,
                    "od_balanced_values": output
                }
            }
            spec_dict_matbal["classes"].append(class_spec)
        balancing_multiple_productions(spec_dict_matbal)

        # Delete the temporary mo-matrices
        for mat_id in temp_matrices:
            util.delmat(eb, mat_id)