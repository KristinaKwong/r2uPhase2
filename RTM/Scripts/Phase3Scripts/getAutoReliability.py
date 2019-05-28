##---------------------------------------------------------------------
##--TransLink Phase 3.2 Regional Transportation Model
##--
##--Path: translink.RTM3.getautoreliability
##--Purpose: Run Auto Reliability Assignment
##---------------------------------------------------------------------
import inro.modeller as _m
import inro.emme.desktop as _d
import csv
import os
import multiprocessing
import numpy as np
import pandas as pd
import sqlite3
import datetime
import traceback as _traceback

class getAutoReliability(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)
        
    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Run Auto Reliability Assignment"
        pb.description = "freeflow assignment and export reliability minutes"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)
        
        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            eb = _m.Modeller().emmebank

            self()
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Trip Simulation")
    def __call__(self):
    
        dt = _d.app.connect()
        de = dt.data_explorer()
        db = de.active_database()
        ebs = de.databases()
        util = _m.Modeller().tool("translink.util")
        
        # Re-run reliability assignment and export reliability minutes matrices
        ReliabilityAssignment = _m.Modeller().tool("translink.RTM3.ff_assignment")
        for eb in ebs:
            title = eb.title()
                
            if title == 'Minimal Base Databank':
                continue
            
            eb.open()
            
            current_time = datetime.datetime.now()
            print "\nstarting {} run at {}".format(title, current_time)
            
            try:    
                # reliability assignment
                current_time = datetime.datetime.now() 
                print "running Reliability Assignment for {} at {}".format(title, current_time)
                eb = _m.Modeller().emmebank
                try:
                    am_scen = eb.scenario(int(eb.matrix("msAmScen").data))
                    md_scen = eb.scenario(int(eb.matrix("msMdScen").data))
                    pm_scen = eb.scenario(int(eb.matrix("msPmScen").data))
                    ReliabilityAssignment(eb, am_scen, md_scen, pm_scen, assignment_type=1)
                except Exception as e:
                    print("Scenario {} Reliability Assignment failed.".format(title), e)
            
            except Exception as e:
                current_time = datetime.datetime.now()
                print("Scenario {} run failed at {}.".format(title, current_time), e)
