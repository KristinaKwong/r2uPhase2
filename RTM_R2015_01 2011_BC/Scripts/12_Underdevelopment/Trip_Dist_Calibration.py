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
import sqlite3

class Trip_Dist_Methods(_m.Tool()):

    ##Global attribute for Tool Run Message (successful/not successful)
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Trip_Dist_Methods"
        pb.description = "Trip_Dist_Methods"
        pb.branding_text = "TransLink"
        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()


    @_m.logbook_trace("Run Home Base Work")
    def __call__(self, eb, df, L_S_Mats, imp_list, prod_list, attr_list, P_A_list, Cal_Coef, RunType, Conv_List, sql_tab_name):
        util = _m.Modeller().tool("translink.util")
        input_path = util.get_input_path(eb)
        NoTAZ = len(util.get_matrix_numpy(eb, "mo51"))
        MChM = _m.Modeller().tool("translink.RTM3.stage2.modechoiceutils")

       ##############################################################################
        ##       Trip Distribution Calibration
       ##############################################################################
        # Define Terms

        Avg_tl = df["TripKms"].sum()/df["TotTrips"].sum()
        Distance = util.get_matrix_numpy(eb, "HbWBlSovDist_I1")
        Distance_flat = Distance.flatten()
        LogSumCoeffInit = 0.5
        MaxLogSum =  0.801
        Diff = 999999.0 # used to determine best logsum coefficient

        LambdaInit =  Cal_Coef[0]
        AlphaInit  =  Cal_Coef[1]
        GammaInit  =  Cal_Coef[2]
        NoSeg = len(prod_list)

        LambdaList = np.full(NoSeg, LambdaInit)
        AlphaList  = np.full(NoSeg, AlphaInit)
        GammaList =  np.full(NoSeg,  GammaInit)

        df['Lambda'] = LambdaList

        df['Alpha']  = AlphaList
        df['Gamma']  = GammaList
        TripKmsModLs   = np.empty(NoSeg)
        TripKmsModSqLs = np.empty(NoSeg)
        TripKmsModCuLs = np.empty(NoSeg)

        # Search for best LogSum between 0.5 and 0.8

        while LogSumCoeffInit <= MaxLogSum:

            self.ImpCalcLogSum(eb, imp_list, L_S_Mats, LogSumCoeffInit)

            if RunType[2] == "Doubly-constrained":
                MChM.two_dim_matrix_balancing(eb, prod_list, attr_list, imp_list, P_A_list)

            if RunType[2] == "Singly-constrained":
                MChM.one_dim_matrix_balancing(eb, prod_list, attr_list, imp_list, P_A_list)

            ## Calculate Average Trip Length

            SumTrip = 0
            for i in range (NoSeg):

                TDMat = util.get_matrix_numpy(eb, P_A_list[i]).flatten()
                SumTrip += TDMat

            AvgDistMod = np.sum(np.multiply(Distance_flat,SumTrip))/np.sum(SumTrip)

            if abs(AvgDistMod - Avg_tl) < Diff:
                Diff = abs(AvgDistMod - Avg_tl)
                Best_LS_Coeff = LogSumCoeffInit

            LogSumCoeffInit += 0.05

        df["LogSum_Coeff"] = Best_LS_Coeff
        print Best_LS_Coeff

        # Calibrate Lambda, Alpha and Gamma coefficients based on asserted best logsum

        if RunType[1] == "Lambda":
           iter_range = 1

        if RunType[1] == "Gamma":
           iter_range = 3

        Counter = 1

        while Counter > 0:

            Counter += 1

            for iteration in range (1, iter_range + 1):

                self.ImpCalc(eb, L_S_Mats, imp_list, Best_LS_Coeff, df['Lambda'] , df['Alpha'], df['Gamma'], Distance)

                if RunType[2] == "Doubly-constrained":
                    MChM.two_dim_matrix_balancing(eb, prod_list, attr_list, imp_list, P_A_list)

                if RunType[2] == "Singly-constrained":
                    MChM.one_dim_matrix_balancing(eb, prod_list, attr_list, imp_list, P_A_list)

                Diff_Dist , Diff_Ratio, df = self.Check_Convergence(eb, NoSeg, P_A_list, Distance_flat, TripKmsModLs, TripKmsModSqLs, TripKmsModCuLs, df, RunType)

                if (Diff_Dist < Conv_List[0] and Diff_Ratio<Conv_List[1]):
                    Counter = 0
                    break # exit while loop

                if iteration == 1:
                    df['Lambda'] = df['Lambda']*df['AvgDistMod']/df['avgTL']

                if iteration == 2:
                    df['Alpha'] = df['Alpha']*df['AvgDistModSq']/df['avgTLsqd']

                if iteration == 3:
                    df['Gamma'] = df['Gamma']*df['AvgDistModCu']/df['avgTLcub']

        # Write results back to SQLite Databse

#        if RunType[1] == "Lambda":
#            df.drop(['Alpha', 'Gamma'], axis = 1, inplace = True)

        db_loc = util.get_eb_path(eb)
        db_path = os.path.join(db_loc, 'tripdist.db')
        conn = sqlite3.connect(db_path)
        df.to_sql(name=sql_tab_name, con=conn, flavor='sqlite', index=False, if_exists='replace')
        conn.close()

    @_m.logbook_trace("Check Convergence")
    def Check_Convergence(self, eb, NoSeg, out_list, Distance_flat, TripKmsModLs, TripKmsModSqLs, TripKmsModCuLs, df, RunType):

        util = _m.Modeller().tool("translink.util")
        TDTrips = np.empty(NoSeg)
        df['AvgDistMod']   = np.empty(NoSeg)
        df['AvgDistModSq'] = np.empty(NoSeg)
        df['AvgDistModCu'] = np.empty(NoSeg)
        df['ModTrips'] = np.empty(NoSeg)

        for i in range (NoSeg):

            TDMat = util.get_matrix_numpy(eb, out_list[i]).flatten()
            TripKmsModLs[i]   = np.sum(np.multiply(Distance_flat,TDMat))
            TripKmsModSqLs[i] = np.sum(np.multiply(np.power(Distance_flat,2),TDMat))
            TripKmsModCuLs[i] = np.sum(np.multiply(np.power(Distance_flat,3),TDMat))
            TDTrips[i] = np.sum(TDMat)

        if RunType[0] == "Income-Auto":
            df['ModTrips'] = TDTrips
            df['AvgDistMod']   = TripKmsModLs/TDTrips
            df['AvgDistModSq'] = TripKmsModSqLs/TDTrips
            df['AvgDistModCu'] = TripKmsModCuLs/TDTrips

        if RunType[0] == "Auto":

            autos_grouped_df = df.copy(deep=True)
            autos_grouped_df = autos_grouped_df[["adj_vehicles"]]
            autos_grouped_df = autos_grouped_df.rename(columns = {'adj_vehicles': 'a_v'})
            autos_grouped_df["TripKms"] = TripKmsModLs
            autos_grouped_df["TripKmsSquared"] = TripKmsModSqLs
            autos_grouped_df["TripKmsCubed"] = TripKmsModCuLs
            autos_grouped_df["ModTrips"] = TDTrips
            autos_grouped_df = autos_grouped_df.groupby(["a_v"]).sum().reset_index()
            autos_grouped_df['AvgDistMod'] = autos_grouped_df["TripKms"]/autos_grouped_df["ModTrips"]
            autos_grouped_df['AvgDistModSq'] = autos_grouped_df["TripKmsSquared"]/autos_grouped_df["ModTrips"]
            autos_grouped_df['AvgDistModCu'] = autos_grouped_df["TripKmsCubed"]/autos_grouped_df["ModTrips"]
            autos_grouped_df = autos_grouped_df[["a_v", "AvgDistMod", "AvgDistModSq", "AvgDistModCu", "ModTrips"]]
            df.drop(["AvgDistMod", "AvgDistModSq", "AvgDistModCu", "ModTrips"], axis = 1, inplace = True)
            df = pd.merge(df, autos_grouped_df, left_on = 'adj_vehicles',
            right_on = 'a_v', how = 'left')
            df.drop('a_v', axis = 1, inplace = True)

        df.to_csv("F:/Scratch/auto.csv")

        if RunType[0] == "All":
           df['AvgDistMod'] = TripKmsModLs.sum()/TDTrips.sum()
           df['AvgDistModSq'] = TripKmsModSqLs.sum()/TDTrips.sum()
           df['AvgDistModCu'] = TripKmsModCuLs.sum()/TDTrips.sum()

        # Check convergence
        Df_DistRat = pd.DataFrame({'AvgDistRat' :   abs(df['AvgDistMod'] - df['avgTL']),
                                   'AvgDistsqdRat': abs(df['AvgDistModSq']/df['avgTLsqd'] - 1),
                                   'AvgDistcubRat': abs(df['AvgDistModCu']/df['avgTLcub'] - 1)})
        if RunType[1] == "Lambda":
            Dist_Diff = np.max(abs(df['AvgDistMod'] - df['avgTL']))
            Rat_Diff = 0

        if RunType[1] == "Gamma":
            Dist_Diff = np.max(abs(df['AvgDistMod'] - df['avgTL']))
            Rat_Diff = max(
                           np.max(abs(df['AvgDistModSq']/df['avgTLsqd'] - 1)),
                           np.max(abs(df['AvgDistModCu']/df['avgTLcub'] - 1)))

        print Dist_Diff, Rat_Diff

        return Dist_Diff, Rat_Diff, df

    @_m.logbook_trace("Impedance Calc")
    def ImpCalc(self, eb, Logsum, imp_list, LS_Coeff, LambdaList ,AlphaList, GammaList, Distance):

        util = _m.Modeller().tool("translink.util")
        input_path = util.get_input_path(eb)

        for i in range (len(imp_list)):

            A = util.get_matrix_numpy(eb, Logsum[i])

            Imp = (LS_Coeff*A+LambdaList[i]*Distance
                  +AlphaList[i]*pow(Distance, 2)
                  +GammaList[i]*pow(Distance, 3))


            Imp = np.exp(Imp)
            util.set_matrix_numpy(eb, imp_list[i], Imp)

        del Distance, A, Imp

    def ImpCalcLogSum(self, eb, imp_list, Logsum, LS_Coeff):

        util = _m.Modeller().tool("translink.util")
        input_path = util.get_input_path(eb)

        for i in range (len(imp_list)):

            A = util.get_matrix_numpy(eb, Logsum[i])

            Imp = (LS_Coeff*A)


            Imp = np.exp(Imp)
            util.set_matrix_numpy(eb, imp_list[i], Imp)

        del A, Imp