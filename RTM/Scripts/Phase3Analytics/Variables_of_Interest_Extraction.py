##---------------------------------------------------------------------
##--TransLink Regional Transportation Model
##--
##--Path:
##--Purpose: Export data for Machine Learning Algorithm Exploration
##---------------------------------------------------------------------
import inro.modeller as _m
import inro.emme.desktop as _d
import traceback as _traceback

import os
import re
import csv as csv

import sqlite3
import pandas as pd
import numpy as np



class ExploreML(_m.Tool()):

    ExcelSheetName = _m.Attribute(str)
    tool_run_msg = _m.Attribute(unicode)
    
    def __init__(self):
        self.ExcelSheetName = "Sheet1"
    
    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Export Data from Model Run"
        pb.description = "Please make sure mf9999 and mo9999 are not in use."
        pb.branding_text = "TransLink"
        
        pb.add_text_box(tool_attribute_name="ExcelSheetName", size=30, title="Worksheet Name for Variables of Interest ")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            eb = _m.Modeller().emmebank
            self.__call__(eb, self.ExcelSheetName)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))
            
        util = _m.Modeller().tool("translink.util")
        util.delmat(eb, "mf9999")
        util.delmat(eb, "mo9999")


    @_m.logbook_trace("Data Export")
    def __call__(self, eb, ExcelSheetName):
        util = _m.Modeller().tool("translink.util")
        
        VOI_df = pd.read_excel("Phase3Analytics/Variables_of_Interest.xlsx",sheetname=ExcelSheetName)
        
        self.get_ML_DataExport(eb, VOI_df)

        
    def get_ML_DataExport(self, eb, VOI_df):
        util = _m.Modeller().tool("translink.util")
        
        #initialize temporary matrix for data export
        util.initmat(eb, "mf9999", "tempExportMatrix", "temp matrix to Export", 0) #for matrix data
        util.initmat(eb, "mo9999", "tempExportVector", "temp vector to Export", 0) #for vector data
        
        conn = sqlite3.connect("Phase3Analytics/Variables_of_Interest_Results.db")
        
        #iterate through table and add mf data
        SQL_TableList = list(set(VOI_df["Category"].tolist())) #get unique sql table names
        for SQL_Table in SQL_TableList:
            
            #look up SQL table type: matrix or vector
            TableType = VOI_df.loc[VOI_df.Category==SQL_Table,"Dimension"].tolist()[0]
            
            #initialize an empty mf long dataframe
            if TableType == "matrix":
                df = util.get_pd_ij_df(eb).astype(int)
                tempmatrix = "mf9999"
            elif TableType == "vector":
                df = pd.DataFrame()
                df["TAZ"] = util.get_matrix_numpy(eb, "mozoneindex", reshape=False).astype(int)
                tempmatrix = "mo9999"
            else:
                raise Exception("Table dimension is not recognized for Category: %s"%SQL_Table)
            
            Attribute_df = VOI_df[VOI_df.Category==SQL_Table]
            for index,row in Attribute_df.iterrows():
            
                #compute matrix expression into temp matrix
                specs = []
                specs.append(util.matrix_spec(tempmatrix, row["MatrixExpression"]))
                util.compute_matrix(specs)
                df[row["Attributes"]] = util.get_matrix_numpy(eb, tempmatrix).flatten()
                
            df.to_sql(name=SQL_Table, con=conn, flavor='sqlite', index=False, if_exists='replace')
        conn.close()
