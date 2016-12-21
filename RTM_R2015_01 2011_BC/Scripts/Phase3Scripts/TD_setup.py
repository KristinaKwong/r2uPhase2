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

class TripDistribution(_m.Tool()):

    ##Global attribute for Tool Run Message (successful/not successful)
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Trip Distribution Calibration"
        pb.description = "Trip Distribution Calibration Tool"
        pb.branding_text = "TransLink"
        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            self.__call__(_m.Modeller().emmebank)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Run Home Base Work")
    def __call__(self, eb):

        util = _m.Modeller().tool("translink.emme.util")
        TD_Calib = _m.Modeller().tool("translink.RTM3.tripdistcalib")
        input_path = util.get_input_path(eb)
        self.create_avgtl_database(eb)

       ##############################################################################
        ##       Trip Distribution Calibration
       ##############################################################################
       ################################################ Get tables from database
        db_loc = util.get_eb_path(eb)
        db_path = os.path.join(db_loc, 'tripdist.db')
        conn = sqlite3.connect(db_path)
        df_hbw = pd.read_sql("SELECT * from hbw_tl", conn) # home-base work
        df_hbu = pd.read_sql("SELECT * from hbu_tl_sum", conn)# home-base uni
        df_hbsc = pd.read_sql("SELECT * from hbsch_tl_auto", conn)# home-base school
        df_hbsh = pd.read_sql("SELECT * from hbshop_tl_auto", conn)# home-base shopping
        conn.close()
       ################################################ Home-base work
#        L_S_Mats  = ["HbWLSI1A0", "HbWLSI1A1", "HbWLSI1A2", "HbWLSI2A0", "HbWLSI2A1", "HbWLSI2A2", "HbWLSI3A0", "HbWLSI3A1", "HbWLSI3A2"]
#        imp_list  = ["P-AFrictionFact1", "P-AFrictionFact2", "P-AFrictionFact3","P-AFrictionFact4", "P-AFrictionFact5", "P-AFrictionFact6",
#                     "P-AFrictionFact7", "P-AFrictionFact8", "P-AFrictionFact9"]
#        prod_list = ["hbwInc1Au0prd", "hbwInc1Au1prd", "hbwInc1Au2prd","hbwInc2Au0prd", "hbwInc2Au1prd", "hbwInc2Au2prd",
#                     "hbwInc3Au0prd", "hbwInc3Au1prd", "hbwInc3Au2prd"]
#        attr_list = ["hbwatr"]
#        P_A_list  = ["HbWP-AI1A0", "HbWP-AI1A1", "HbWP-AI1A2", "HbWP-AI2A0", "HbWP-AI2A1", "HbWP-AI2A2",
#                     "HbWP-AI3A0", "HbWP-AI3A1", "HbWP-AI3A2"]
#
#                    #Lambda, Alpha, Gamma
#        Cal_Coef  = [-0.4, 0.01, -0.0006]
#        RunType   = ["Income-Auto", "Gamma", "Doubly-constrained"]
#
#                    #Difference, #Ratio
#        Conv_List = [0.25, 0.1]  # Difference used for average trip_length, Ratio for square and cube terms
#        TD_Calib(eb, df_hbw, L_S_Mats, imp_list, prod_list, attr_list, P_A_list, Cal_Coef, RunType, Conv_List, "hbw_tl")

#       ################################################ Home-base uni
#
#        L_S_Mats  = ["HbULS"]
#        imp_list  = ["P-AFrictionFact1"]
#        prod_list = ["hbuprd"]
#        attr_list = ["hbuatr"]
#        P_A_list  = ["HbUP-A"]
#
#                    #Lambda, Alpha, Gamma
#        Cal_Coef  = [-0.4, 0.01, -0.0006]
#        RunType   = ["Income-Auto", "Gamma", "Doubly-constrained"]
#
#                    #Difference, #Ratio
#        Conv_List = [0.15, 0.1]  # Difference used for average trip_length, Ratio for square and cube terms
#        TD_Calib(eb, df_hbu, L_S_Mats, imp_list, prod_list, attr_list, P_A_list, Cal_Coef, RunType, Conv_List, "hbu_tl_sum")

#       ################################################ Home-base school
#
#        L_S_Mats  = ["HbScLSA0", "HbScLSA1", "HbScLSA2","HbScLSA0", "HbScLSA1", "HbScLSA2", "HbScLSA0", "HbScLSA1", "HbScLSA2"]
#
#        imp_list  = ["P-AFrictionFact1", "P-AFrictionFact2", "P-AFrictionFact3","P-AFrictionFact4", "P-AFrictionFact5", "P-AFrictionFact6",
#                     "P-AFrictionFact7", "P-AFrictionFact8", "P-AFrictionFact9"]
#
#        prod_list = ["hbschInc1Au0prd", "hbschInc1Au1prd", "hbschInc1Au2prd","hbschInc2Au0prd", "hbschInc2Au1prd", "hbschInc2Au2prd",
#                     "hbschInc3Au0prd", "hbschInc3Au1prd", "hbschInc3Au2prd"]
#
#        attr_list = ["hbschatr"]
#        P_A_list  = ["HbScP-AI1A0", "HbScP-AI1A1", "HbScP-AI1A2","HbScP-AI2A0", "HbScP-AI2A1", "HbScP-AI2A2",
#                     "HbScP-AI3A0", "HbScP-AI3A1", "HbScP-AI3A2"]
#
#                    #Lambda, Alpha, Gamma
#        Cal_Coef  = [-0.4, 0.0, 0.0]
#        RunType   = ["Auto", "Lambda", "Doubly-constrained"]
#
#                    #Difference, #Ratio
#        Conv_List = [0.05, 0.1]  # Difference used for average trip_length, Ratio for square and cube terms
#        TD_Calib(eb, df_hbsc, L_S_Mats, imp_list, prod_list, attr_list, P_A_list, Cal_Coef, RunType, Conv_List, "hbsch_tl_auto")

       ################################################ Home-base shopping

        L_S_Mats  = ["HbShLSI1A0", "HbShLSI1A1", "HbShLSI1A2", "HbShLSI2A0", "HbShLSI2A1", "HbShLSI2A2", "HbShLSI3A0", "HbShLSI3A1", "HbShLSI3A2"]


        imp_list  = ["P-AFrictionFact1", "P-AFrictionFact2", "P-AFrictionFact3", "P-AFrictionFact4", "P-AFrictionFact5", "P-AFrictionFact6",
                     "P-AFrictionFact7", "P-AFrictionFact8", "P-AFrictionFact9"]


        prod_list = ["hbshopInc1Au0prd", "hbshopInc1Au1prd", "hbshopInc1Au2prd", "hbshopInc2Au0prd", "hbshopInc2Au1prd", "hbshopInc2Au2prd",
                    "hbshopInc3Au0prd", "hbshopInc3Au1prd", "hbshopInc3Au2prd"]


        attr_list = ["hbshopatr"]
        P_A_list  = ["HbShP-AI1A0", "HbShP-AI1A1", "HbShP-AI1A2", "HbShP-AI2A0", "HbShP-AI2A1", "HbShP-AI2A2",
                    "HbShP-AI3A0", "HbShP-AI3A1", "HbShP-AI3A2"]

                    #Lambda, Alpha, Gamma
        Cal_Coef  = [-0.4, 0.01, -0.0006]
        RunType   = ["Auto", "Gamma", "Singly-constrained"]

                    #Difference, #Ratio
        Conv_List = [0.25, 0.1]  # Difference used for average trip_length, Ratio for square and cube terms
        TD_Calib(eb, df_hbsh, L_S_Mats, imp_list, prod_list, attr_list, P_A_list, Cal_Coef, RunType, Conv_List, "hbshop_tl_auto")


    def create_avgtl_database(self, eb):

        util = _m.Modeller().tool("translink.emme.util")

        Path = "U:/Projects/Development/Phase 3/TripDistribution/Targets/TripLengths/"
        PurpList = ["hbw", "hbpb", "hbesc", "hbsoc", "hbu", "hbshop", "nhbw", "nhbo", "hbsch"]

        for i in range (len(PurpList)):
            Loc = os.path.join(Path, PurpList[i]) + "_tl.csv"
            ## read average trip lengths by income and auto
            df = pd.DataFrame(pd.read_csv(Loc, sep = ","))

            ## create a single row table by purpose code
            df_Sum = df.copy(deep=True)
            df_Sum = df_Sum.groupby(["purp_code"]).sum().reset_index()
            df_Sum.drop(['income_cat', 'adj_vehicles'], axis=1, inplace = True)
            df_Sum['avgTL'] = df_Sum["TripKms"]/ df_Sum["TotTrips"]
            df_Sum['avgTLsqd'] = df_Sum["TripKmsSquared"]/ df_Sum["TotTrips"]
            df_Sum['avgTLcub'] = df_Sum["TripKmsCubed"]/ df_Sum["TotTrips"]

            ## create a nine-row table by purp, income and auto ownership but summed across all incomes
            df_All = df.copy(deep=True)
            Avg_TL = df_All["TripKms"].sum()/df_All["TotTrips"].sum()
            Avg_TL_sqd = df_All["TripKmsSquared"].sum()/df_All["TotTrips"].sum()
            Avg_TL_cub = df_All["TripKmsCubed"].sum()/df_All["TotTrips"].sum()
            df_All['avgTL'] = Avg_TL
            df_All['avgTLsqd'] = Avg_TL_sqd
            df_All['avgTLcub'] = Avg_TL_cub

            ## create a nine-row table by purp, income and auto ownership summed across income
            Df_Income = df.copy(deep=True)
            income_grouped_df = Df_Income.groupby(["income_cat"]).sum().reset_index()
            income_grouped_df['avgTL'] = income_grouped_df["TripKms"]/ income_grouped_df["TotTrips"]
            income_grouped_df['avgTLsqd'] = income_grouped_df["TripKmsSquared"]/ income_grouped_df["TotTrips"]
            income_grouped_df['avgTLcub'] = income_grouped_df["TripKmsCubed"]/ income_grouped_df["TotTrips"]
            income_grouped_df = income_grouped_df[["income_cat", "avgTL", "avgTLsqd", "avgTLcub"]]
            income_grouped_df = income_grouped_df.rename(columns = {'income_cat': 'i_c'})
            Df_Income.drop(['avgTL', 'avgTLsqd', 'avgTLcub'], axis = 1, inplace = True)
            Df_Income = pd.merge(Df_Income, income_grouped_df, left_on = 'income_cat',
            right_on = 'i_c', how = 'left')
            Df_Income.drop('i_c', axis = 1, inplace = True)

            ## create a nine-row table by purp, income and auto ownership summed across auto-ownership
            Df_Auto = df.copy(deep=True)
            autos_grouped_df = Df_Auto.groupby(["adj_vehicles"]).sum().reset_index()
            autos_grouped_df['avgTL'] = autos_grouped_df["TripKms"]/ autos_grouped_df["TotTrips"]
            autos_grouped_df['avgTLsqd'] = autos_grouped_df["TripKmsSquared"]/ autos_grouped_df["TotTrips"]
            autos_grouped_df['avgTLcub'] = autos_grouped_df["TripKmsCubed"]/ autos_grouped_df["TotTrips"]
            autos_grouped_df = autos_grouped_df[["adj_vehicles", "avgTL", "avgTLsqd", "avgTLcub"]]
            autos_grouped_df = autos_grouped_df.rename(columns = {'adj_vehicles': 'a_v'})
            Df_Auto.drop(['avgTL', 'avgTLsqd', 'avgTLcub'], axis = 1, inplace = True)
            Df_Auto = pd.merge(Df_Auto, autos_grouped_df, left_on = 'adj_vehicles',
            right_on = 'a_v', how = 'left')
            Df_Auto.drop('a_v', axis = 1, inplace = True)


            # Write tables to sqlite
            db_loc = util.get_eb_path(eb)
            db_path = os.path.join(db_loc, 'tripdist.db')
            conn = sqlite3.connect(db_path)
            df.to_sql(name=PurpList[i]+'_tl', con=conn, flavor='sqlite', index=False, if_exists='replace')
            df_Sum.to_sql(name=PurpList[i]+'_tl_sum', con=conn, flavor='sqlite', index=False, if_exists='replace')
            df_All.to_sql(name=PurpList[i]+'_tl_all', con=conn, flavor='sqlite', index=False, if_exists='replace')
            Df_Income.to_sql(name=PurpList[i]+'_tl_income', con=conn, flavor='sqlite', index=False, if_exists='replace')
            Df_Auto.to_sql(name=PurpList[i]+'_tl_auto', con=conn, flavor='sqlite', index=False, if_exists='replace')
            conn.close()

