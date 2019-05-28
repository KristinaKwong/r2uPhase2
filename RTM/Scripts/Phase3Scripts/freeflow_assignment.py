##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.ff_assignment
##--Purpose: Run an LOS D Assignment for AM, MD and PM
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback
from StringIO import StringIO
import pandas as pd
import numpy as np
import os

class AutoAssignment(_m.Tool()):
    am_scenario = _m.Attribute(_m.InstanceType)
    md_scenario = _m.Attribute(_m.InstanceType)
    pm_scenario = _m.Attribute(_m.InstanceType)
    assignment_type = _m.Attribute(int)

    relative_gap = _m.Attribute(float)
    best_relative_gap = _m.Attribute(float)
    normalized_gap = _m.Attribute(float)
    max_iterations = _m.Attribute(int)

    tool_run_msg = _m.Attribute(unicode)

    def __init__(self):
        self.relative_gap = 0.0001
        self.best_relative_gap = 0
        self.normalized_gap = 0
        self.max_iterations = 300
        self.assignment_type = 1

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Auto Assignment"
        pb.description = "Performs an LOS D Assignment " +\
                         "with 4 classes, SOV, HOV , Light Trucks " +\
                         "and Heavy Trucks. Creates new copies of input scenarios"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        pb.add_select(tool_attribute_name="assignment_type",keyvalues=[[1,"Regular"],[2,"Social_Optimal"]])
        pb.add_select_scenario("am_scenario", title="AM scenario:")
        pb.add_select_scenario("md_scenario", title="MD scenario:")
        pb.add_select_scenario("pm_scenario", title="PM scenario:")

        with pb.section("Stopping criteria:"):
            pb.add_text_box("relative_gap", title="Relative gap:")
            pb.add_text_box("best_relative_gap", title="Best relative gap (%):")
            pb.add_text_box("normalized_gap", title="Normalized gap:")
            pb.add_text_box("max_iterations", title="Maximum iterations:")

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            eb = _m.Modeller().emmebank
            eb.matrix("ms40").data = self.max_iterations
            eb.matrix("ms41").data = self.relative_gap
            eb.matrix("ms42").data = self.best_relative_gap
            eb.matrix("ms43").data = self.normalized_gap

            self(eb, self.am_scenario, self.md_scenario, self.pm_scenario, self.assignment_type)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Auto Traffic Assignment")
    def __call__(self, eb, am_scenario, md_scenario, pm_scenario,assignment_type):

        util = _m.Modeller().tool("translink.util")
        util.initmat(eb, "ms12", "Processors", "Number of Processors for Computer Running Model", 4)
        # make sure we don't overwrite existing scenarios
        am_scenario, md_scenario, pm_scenario = self.losdscenarios(eb, am_scenario, md_scenario, pm_scenario)

        # Initialize LOSD Skims by time period
        util.initmat(eb, "mf9650", "AmSovTimeFreeflow", "SOV Minutes Freeflow AM", 0)
        util.initmat(eb, "mf9660", "MdSovTimeFreeflow", "SOV Minutes Freeflow MD", 0)
        util.initmat(eb, "mf9670", "PmSovTimeFreeflow", "SOV Minutes Freeflow PM", 0)
        util.initmat(eb, "mf9655", "AmHovTimeFreeflow", "HOV Minutes Freeflow AM", 0)
        util.initmat(eb, "mf9665", "MdHovTimeFreeflow", "HOV Minutes Freeflow MD", 0)
        util.initmat(eb, "mf9675", "PmHovTimeFreeflow", "HOV Minutes Freeflow PM", 0)
        util.initmat(eb, "mf9680", "AmLgvTimeFreeflow", "LGV Minutes Freeflow AM", 0)
        util.initmat(eb, "mf9681", "MdLgvTimeFreeflow", "LGV Minutes Freeflow MD", 0)
        util.initmat(eb, "mf9682", "PmLgvTimeFreeflow", "LGV Minutes Freeflow PM", 0)
        util.initmat(eb, "mf9690", "AmHgvTimeFreeflow", "HGV Minutes Freeflow AM", 0)
        util.initmat(eb, "mf9691", "MdHgvTimeFreeflow", "HGV Minutes Freeflow MD", 0)
        util.initmat(eb, "mf9692", "PmHgvTimeFreeflow", "HGV Minutes Freeflow PM", 0)

        # AM

        self.assign_scen(am_scenario, assignment_type)
        self.calc_intrazonal_skims(eb)

        am_skims = {"sov":  ["mfAmSovTimeFreeflow"],
                    "hov":  ["mfAmHovTimeFreeflow"],
                    "lgv":  ["mfAmLgvTimeFreeflow"],
                    "hgv":  ["mfAmHgvTimeFreeflow"]}

        self.store_skims(am_scenario, am_skims)

        # MD

        self.assign_scen(md_scenario, assignment_type)
        self.calc_intrazonal_skims(eb)
        md_skims = {"sov":  ["mfMdSovTimeFreeflow"],
                    "hov":  ["mfMdHovTimeFreeflow"],
                    "lgv":  ["mfMdLgvTimeFreeflow"],
                    "hgv":  ["mfMdHgvTimeFreeflow"]}

        self.store_skims(md_scenario, md_skims)

        # PM

        self.assign_scen(pm_scenario, assignment_type)
        self.calc_intrazonal_skims(eb)
        pm_skims = {"sov":  ["mfPmSovTimeFreeflow"],
                    "hov":  ["mfPmHovTimeFreeflow"],
                    "lgv":  ["mfPmLgvTimeFreeflow"],
                    "hgv":  ["mfPmHgvTimeFreeflow"]}

        self.store_skims(pm_scenario, pm_skims)

        self.calc_all(eb)

    def assign_scen(self, scenario, assignment_type):
        assign_traffic = _m.Modeller().tool("inro.emme.traffic_assignment.sola_traffic_assignment")
        util = _m.Modeller().tool("translink.util")
        eb = _m.Modeller().emmebank

        self.init_matrices(scenario.emmebank)

        # undertake a dummy assignment with only background traffic at 85% of the volume (LOS D)
        # Calculate volume = 85% of capacity on the network and store it in ul3

        if assignment_type == 1:
            util.emme_link_calc(scenario, "ul3", "0")

        if assignment_type == 2:
            util.emme_link_calc(scenario, "ul3", "0")


        # get truck perception_factor

        hgv_perception = eb.matrix("msVotHgv").data

        # calculate @tkpen
        util.emme_link_calc(scenario, "@tkpen", "0")
        util.emme_link_calc(scenario, "@tkpen", "length * 100", sel_link="mode=n")


        # stopping criteria

        max_iter = int(eb.matrix("ms40").data)
        rel_gap = eb.matrix("ms41").data
        best_rel_gap = eb.matrix("ms42").data
        norm_gap = eb.matrix("ms43").data

        # Assign temporary scenario

        losd_spec = {
                            "type": "SOLA_TRAFFIC_ASSIGNMENT",
                            "classes": [
                                {
                                    "mode": "c",
                                    "demand": "msZero",
                                    "generalized_cost": None,
                                    "results": {
                                        "link_volumes": None,
                                        "turn_volumes": None,
                                        "od_travel_times": {
                                        "shortest_paths": "mfHovTimeFreeflow"
                                        }
                                    },
                                    "path_analyses": None
                                },
                                {
                                    "mode": "d",
                                    "demand": "msZero",
                                    "generalized_cost": None,
                                    "results": {
                                        "link_volumes": None,
                                        "turn_volumes": None,
                                        "od_travel_times": {
                                            "shortest_paths": "mfSovTimeFreeflow"
                                        }
                                    },
                                    "path_analyses": None
                                },
                                {
                                    "mode": "x",
                                    "demand": "msZero",
                                    "generalized_cost": None,
                                    "results": {
                                        "link_volumes": None,
                                        "turn_volumes": None,
                                        "od_travel_times": {
                                            "shortest_paths": "mfLgvTimeFreeflow"
                                        }
                                    },
                                    "path_analyses": None
                                },
                                {
                                    "mode": "t",
                                    "demand": "msZero",
                                    "generalized_cost": {
                                        "link_costs": "@tkpen",
                                        "perception_factor": hgv_perception
                                    },
                                    "results": {
                                        "link_volumes": None,
                                        "turn_volumes": None,
                                        "od_travel_times": {
                                            "shortest_paths": "mfHgvTimeFreeflow"
                                        }
                                    },
                                    "path_analyses": [
                                                    {
                                                        "link_component": "@tkpen",
                                                        "turn_component": None,
                                                        "operator": "+",
                                                        "selection_threshold": {
                                                            "lower": 0,
                                                            "upper": 999999
                                                        },
                                                        "path_to_od_composition": {
                                                            "considered_paths": "ALL",
                                                            "multiply_path_proportions_by": {
                                                                "analyzed_demand": False,
                                                                "path_value": True
                                                            }
                                                        },
                                                        "analyzed_demand": None,
                                                        "results": {
                                                            "selected_link_volumes": None,
                                                            "selected_turn_volumes": None,
                                                            "od_values": "mfHgvPenyFreeflow"
                                                        }
                                                    }
                                                ]
                                }
                            ],
                            "performance_settings": {
                                "number_of_processors": "max"
                            },
                            "background_traffic": {
                                "link_component": "ul3",
                                "turn_component": None,
                                "add_transit_vehicles": False
                            },
                            "stopping_criteria": {
                                "max_iterations": max_iter,
                                "relative_gap": rel_gap,
                                "best_relative_gap": best_rel_gap,
                                "normalized_gap": norm_gap
                            }
                        }

        assign_traffic = _m.Modeller().tool("inro.emme.traffic_assignment.sola_traffic_assignment")
        assign_traffic(losd_spec, scenario=scenario)

        # correct heavy truck travel time matrix
        specs = []

        specs.append(util.matrix_spec("mfHgvTimeFreeflow", "mfHgvTimeFreeflow - mfHgvPenyFreeflow*msVotHgv"))
        util.compute_matrix(specs, scenario)

    @_m.logbook_trace("Execute Intrazonal Calculation")

    def calc_intrazonal_skims(self, eb):

        # Calculate Intrazonal Analysis 1
        self.calc_intrazonal_skim(eb, "mfSovTimeFreeflow")
        self.calc_intrazonal_skim(eb, "mfHovTimeFreeflow")
        self.calc_intrazonal_skim(eb, "mfLgvTimeFreeflow")
        self.calc_intrazonal_skim(eb, "mfHgvTimeFreeflow")

    def calc_intrazonal_skim(self, eb, matrix):
        util = _m.Modeller().tool("translink.util")

        np_mat = util.get_matrix_numpy(eb, matrix)

        # calculate the mimimum non-zero value in each row and set half that
        # as the intrazonal value
        for i in xrange(np_mat.shape[0]):
            np_mat[i][i] = np_mat[i][np_mat[i] > 0].min() * 0.5

        # write the updated matrix back to the emmebank
        util.set_matrix_numpy(eb, matrix, np_mat)

    def store_skims(self, scenario, skim_list):
        util = _m.Modeller().tool("translink.util")
        specs = []

        # Analysis 1

        specs.append(util.matrix_spec(skim_list["sov"][0], "mfSovTimeFreeflow"))
        specs.append(util.matrix_spec(skim_list["hov"][0], "mfHovTimeFreeflow"))
        specs.append(util.matrix_spec(skim_list["lgv"][0], "mfLgvTimeFreeflow"))
        specs.append(util.matrix_spec(skim_list["hgv"][0], "mfHgvTimeFreeflow"))

        util.compute_matrix(specs, scenario)

        # now that the skims have been written back, delete the temporary matrices
        for matrix in self.get_temp_matrices():
            util.delmat(scenario.emmebank, matrix[0])


    def init_matrices(self, eb):
        util = _m.Modeller().tool("translink.util")

        for matrix in self.get_temp_matrices():
            util.initmat(eb, matrix[0], matrix[1], matrix[2], matrix[3])

    def get_temp_matrices(self):
        matrices = []

        matrices.append(["mf9600", "SovTimeFreeflow",  "SOV Minutes Freeflow", 0])
        matrices.append(["mf9605", "HovTimeFreeflow",  "HOV Minutes Freeflow", 0])
        matrices.append(["mf9630", "LgvTimeFreeflow",  "LGV Minutes Freeflow", 0])
        matrices.append(["mf9640", "HgvTimeFreeflow",  "HGV Minutes Freeflow", 0])
        matrices.append(["mf9641", "HgvPenyFreeflow",  "HGV TrkPeny Freeflow", 0])

        return matrices


    def losdscenarios(self, eb, am_scenario, md_scenario, pm_scenario):
        copy_scenario = _m.Modeller().tool("inro.emme.data.scenario.copy_scenario")
        # create_scenarios = _m.Modeller().tool("translink.RTM3.stage0.create_scenarios")

         # Copy to new AM Scenarios
        am_scenid = am_scenario.number + 100
        copy_scenario(from_scenario=am_scenario,
                    scenario_id=am_scenid,
                    scenario_title="{} FF".format(am_scenario.title),
                    overwrite=True,
                    copy_strategies=False)
        amscen_out = eb.scenario(am_scenid)


        # Copy to new MD Scenarios
        md_scenid = md_scenario.number + 100
        copy_scenario(from_scenario=md_scenario,
                    scenario_id=md_scenid,
                    scenario_title="{} FF".format(md_scenario.title),
                    overwrite=True,
                    copy_strategies=False)
        mdscen_out = eb.scenario(md_scenid)


        # Copy to new pm Scenarios
        pm_scenid = pm_scenario.number + 100
        copy_scenario(from_scenario=pm_scenario,
                    scenario_id=pm_scenid,
                    scenario_title="{} FF".format(pm_scenario.title),
                    overwrite=True,
                    copy_strategies=False)
        pmscen_out = eb.scenario(pm_scenid)

        return amscen_out, mdscen_out, pmscen_out

    def calc_all(self, eb):
        util = _m.Modeller().tool("translink.util")

        util.initmat(eb, "mf5250", "AmSovRelVot1", "AM SOV Reliability Minutes VoT1")
        util.initmat(eb, "mf5251", "AmSovRelVot2", "AM SOV Reliability Minutes VoT2")
        util.initmat(eb, "mf5252", "AmSovRelVot3", "AM SOV Reliability Minutes VoT3")
        util.initmat(eb, "mf5253", "AmSovRelVot4", "AM SOV Reliability Minutes VoT4")
        util.initmat(eb, "mf5254", "AmHovRelVot1", "AM HOV Reliability Minutes VoT1")
        util.initmat(eb, "mf5255", "AmHovRelVot2", "AM HOV Reliability Minutes VoT2")
        util.initmat(eb, "mf5256", "AmHovRelVot3", "AM HOV Reliability Minutes VoT3")
        util.initmat(eb, "mf5257", "AmLgvRel", "AM LGV Reliability Minutes")
        util.initmat(eb, "mf5258", "AmHgvRel", "AM HGV Reliability Minutes")
        util.initmat(eb, "mf5260", "MdSovRelVot1", "MD SOV Reliability Minutes VoT1")
        util.initmat(eb, "mf5261", "MdSovRelVot2", "MD SOV Reliability Minutes VoT2")
        util.initmat(eb, "mf5262", "MdSovRelVot3", "MD SOV Reliability Minutes VoT3")
        util.initmat(eb, "mf5263", "MdSovRelVot4", "MD SOV Reliability Minutes VoT4")
        util.initmat(eb, "mf5264", "MdHovRelVot1", "MD HOV Reliability Minutes VoT1")
        util.initmat(eb, "mf5265", "MdHovRelVot2", "MD HOV Reliability Minutes VoT2")
        util.initmat(eb, "mf5266", "MdHovRelVot3", "MD HOV Reliability Minutes VoT3")
        util.initmat(eb, "mf5267", "MdLgvRel", "MD LGV Reliability Minutes")
        util.initmat(eb, "mf5268", "MdHgvRel", "MD HGV Reliability Minutes")
        util.initmat(eb, "mf5270", "PmSovRelVot1", "PM SOV Reliability Minutes VoT1")
        util.initmat(eb, "mf5271", "PmSovRelVot2", "PM SOV Reliability Minutes VoT2")
        util.initmat(eb, "mf5272", "PmSovRelVot3", "PM SOV Reliability Minutes VoT3")
        util.initmat(eb, "mf5273", "PmSovRelVot4", "PM SOV Reliability Minutes VoT4")
        util.initmat(eb, "mf5274", "PmHovRelVot1", "PM HOV Reliability Minutes VoT1")
        util.initmat(eb, "mf5275", "PmHovRelVot2", "PM HOV Reliability Minutes VoT2")
        util.initmat(eb, "mf5276", "PmHovRelVot3", "PM HOV Reliability Minutes VoT3")
        util.initmat(eb, "mf5277", "PmLgvRel", "PM LGV Reliability Minutes")
        util.initmat(eb, "mf5278", "PmHgvRel", "PM HGV Reliability Minutes")

        am_coefs = { 'intercept':-3.3737,
                     'logtti':3.55707,
                     'logdist':0.83667,
                     'xing':0.1621,
                     'peak':0.177 }

        md_coefs = { 'intercept':-3.3737,
                     'logtti':3.1192,
                     'logdist':0.83667,
                     'xing':0.1621,
                     'peak':0.00 }

        pm_coefs = { 'intercept':-3.3737,
                     'logtti':3.55707,
                     'logdist':0.83667,
                     'xing':0.1621,
                     'peak':0.177 }

        self.calc_reliability(eb, am_coefs, 'AmSovRelVot1', 'mfAmSovTimeVOT1', 'mfAmSovTimeFreeflow', 'mfAmSovOpCstVOT1', 0.18)
        self.calc_reliability(eb, am_coefs, 'AmSovRelVot2', 'mfAmSovTimeVOT2', 'mfAmSovTimeFreeflow', 'mfAmSovOpCstVOT2', 0.18)
        self.calc_reliability(eb, am_coefs, 'AmSovRelVot3', 'mfAmSovTimeVOT3', 'mfAmSovTimeFreeflow', 'mfAmSovOpCstVOT3', 0.18)
        self.calc_reliability(eb, am_coefs, 'AmSovRelVot4', 'mfAmSovTimeVOT4', 'mfAmSovTimeFreeflow', 'mfAmSovOpCstVOT4', 0.18)
        self.calc_reliability(eb, am_coefs, 'AmHovRelVot1', 'mfAmHovTimeVOT1', 'mfAmHovTimeFreeflow', 'mfAmHovOpCstVOT1', 0.18)
        self.calc_reliability(eb, am_coefs, 'AmHovRelVot2', 'mfAmHovTimeVOT2', 'mfAmHovTimeFreeflow', 'mfAmHovOpCstVOT2', 0.18)
        self.calc_reliability(eb, am_coefs, 'AmHovRelVot3', 'mfAmHovTimeVOT3', 'mfAmHovTimeFreeflow', 'mfAmHovOpCstVOT3', 0.18)
        self.calc_reliability(eb, am_coefs, 'AmLgvRel', 'mfAmLgvTime', 'mfAmLgvTimeFreeflow', 'mfAmLgvOpCst', 0.24)
        self.calc_reliability(eb, am_coefs, 'AmHgvRel', 'mfAmHgvTime', 'mfAmHgvTimeFreeflow', 'mfAmHgvOpCst', 0.56)

        self.calc_reliability(eb, md_coefs, 'MdSovRelVot1', 'mfMdSovTimeVOT1', 'mfMdSovTimeFreeflow', 'mfMdSovOpCstVOT1', 0.18)
        self.calc_reliability(eb, md_coefs, 'MdSovRelVot2', 'mfMdSovTimeVOT2', 'mfMdSovTimeFreeflow', 'mfMdSovOpCstVOT2', 0.18)
        self.calc_reliability(eb, md_coefs, 'MdSovRelVot3', 'mfMdSovTimeVOT3', 'mfMdSovTimeFreeflow', 'mfMdSovOpCstVOT3', 0.18)
        self.calc_reliability(eb, md_coefs, 'MdSovRelVot4', 'mfMdSovTimeVOT4', 'mfMdSovTimeFreeflow', 'mfMdSovOpCstVOT4', 0.18)
        self.calc_reliability(eb, md_coefs, 'MdHovRelVot1', 'mfMdHovTimeVOT1', 'mfMdHovTimeFreeflow', 'mfMdHovOpCstVOT1', 0.18)
        self.calc_reliability(eb, md_coefs, 'MdHovRelVot2', 'mfMdHovTimeVOT2', 'mfMdHovTimeFreeflow', 'mfMdHovOpCstVOT2', 0.18)
        self.calc_reliability(eb, md_coefs, 'MdHovRelVot3', 'mfMdHovTimeVOT3', 'mfMdHovTimeFreeflow', 'mfMdHovOpCstVOT3', 0.18)
        self.calc_reliability(eb, md_coefs, 'MdLgvRel', 'mfMdLgvTime', 'mfMdLgvTimeFreeflow', 'mfMdLgvOpCst', 0.24)
        self.calc_reliability(eb, am_coefs, 'MdHgvRel', 'mfMdHgvTime', 'mfMdHgvTimeFreeflow', 'mfMdHgvOpCst', 0.56)

        self.calc_reliability(eb, pm_coefs, 'PmSovRelVot1', 'mfPmSovTimeVOT1', 'mfPmSovTimeFreeflow', 'mfPmSovOpCstVOT1', 0.18)
        self.calc_reliability(eb, pm_coefs, 'PmSovRelVot2', 'mfPmSovTimeVOT2', 'mfPmSovTimeFreeflow', 'mfPmSovOpCstVOT2', 0.18)
        self.calc_reliability(eb, pm_coefs, 'PmSovRelVot3', 'mfPmSovTimeVOT3', 'mfPmSovTimeFreeflow', 'mfPmSovOpCstVOT3', 0.18)
        self.calc_reliability(eb, pm_coefs, 'PmSovRelVot4', 'mfPmSovTimeVOT4', 'mfPmSovTimeFreeflow', 'mfPmSovOpCstVOT4', 0.18)
        self.calc_reliability(eb, pm_coefs, 'PmHovRelVot1', 'mfPmHovTimeVOT1', 'mfPmHovTimeFreeflow', 'mfPmHovOpCstVOT1', 0.18)
        self.calc_reliability(eb, pm_coefs, 'PmHovRelVot2', 'mfPmHovTimeVOT2', 'mfPmHovTimeFreeflow', 'mfPmHovOpCstVOT2', 0.18)
        self.calc_reliability(eb, pm_coefs, 'PmHovRelVot3', 'mfPmHovTimeVOT3', 'mfPmHovTimeFreeflow', 'mfPmHovOpCstVOT3', 0.18)
        self.calc_reliability(eb, pm_coefs, 'PmLgvRel', 'mfPmLgvTime', 'mfPmLgvTimeFreeflow', 'mfPmLgvOpCst', 0.24)
        self.calc_reliability(eb, pm_coefs, 'PmHgvRel', 'mfPmHgvTime', 'mfPmHgvTimeFreeflow', 'mfPmHgvOpCst', 0.56)
        
        export_dict = {} #intialize empty dictionary for output items
        export_list = ["AmSovRelVot1","MdSovRelVot1","PmSovRelVot1",
                       "AmSovRelVot2","MdSovRelVot2","PmSovRelVot2",
                       "AmSovRelVot3","MdSovRelVot3","PmSovRelVot3",
                       "AmSovRelVot4","MdSovRelVot4","PmSovRelVot4",
                       "AmHovRelVot1","MdHovRelVot1","PmHovRelVot1",
                       "AmHovRelVot2","MdHovRelVot2","PmHovRelVot2",
                       "AmHovRelVot3","MdHovRelVot3","PmHovRelVot3",
                       "AmLgvRel","MdLgvRel","PmLgvRel",
                       "AmHgvRel","MdHgvRel","PmHgvRel"
                       ]
        for matrix_name in export_list:
            matrix = util.get_matrix_numpy(eb, matrix_name)
            matrix_name = matrix_name.replace("Rel","RTIM").upper()
            export_dict[matrix_name] = matrix
        
        out_path = os.path.join(util.get_eb_path(eb), 'EconomicAnalysis') # set output directory
        if not os.path.exists(out_path): # initialize output directory if it does not exist
            os.makedirs(out_path)
        OutputFile = os.path.join(out_path,'RELISKIM.npz') # output file name
        np.savez_compressed(OutputFile, **export_dict) # save output dictionary as npz file


    def calc_reliability(self, eb, coefs, rel_mat, time_mat, fftime_mat, op_cost_mat, op_cost):
        util = _m.Modeller().tool("translink.util")

        df_vars = self.bridge_xings(eb)
        df_vars['time'] = util.get_matrix_numpy(eb, time_mat).flatten()
        df_vars['fftime'] = util.get_matrix_numpy(eb, fftime_mat).flatten()

        # log variables. Ensure min >= 1 before transformation
        # Travel Time Index Calculation
        df_vars['tti'] = df_vars['time'] / df_vars['fftime']
        ltc = self.log_trans_const(df_vars['tti'])
        df_vars['log_tti'] = np.log(df_vars['tti'] + ltc)

        # log distance calc
        df_vars['dist'] = util.get_matrix_numpy(eb, op_cost_mat).flatten() / op_cost
        ltc = self.log_trans_const(df_vars['dist'])
        df_vars['log_dist'] = np.log(df_vars['dist'] + ltc)

        df_vars['sigma'] = ( coefs['intercept']
                                + coefs['logtti'] * df_vars['log_tti']
                                + coefs['logdist'] * df_vars['log_dist']
                                + coefs['xing']  * df_vars['crossing']
                                + coefs['peak'] )
        df_vars['sigma'] = np.exp(df_vars['sigma'])

        util.set_matrix_numpy(eb, rel_mat, df_vars['sigma'])
        return df_vars

    def log_trans_const(self, nparray):
        if nparray.min() < 1:
            const = 1 - nparray.min()
        else:
            const = 0

        return const

    def model_coefs(self):
        coefs = StringIO("""peak,intercept,coef_logTTi,coef_logDist,coef_xing,coef_peak
        am,-3.3737,3.55707,0.83667,0.1621,0.1777
        md,-3.3737,3.1192,0.83667,0.1621,0
        pm,-3.3737,3.55707,0.83667,0.1621,0.1777""")

        coef_df = pd.read_csv(coefs, sep = ',')
        coef_df.peak = coef_df.peak.str.strip()

        return coef_df

    def bridge_xings(self, eb):
        util = _m.Modeller().tool("translink.util")
        df = pd.concat([util.get_pd_ij_df(eb),util.get_ijensem_df(eb, 'gy','gy')], axis=1)

        xings = StringIO("""gy_i,gy_j,crossing
        1,1,0
        1,2,0
        1,3,1
        1,4,1
        1,5,1
        1,6,1
        1,7,1
        1,8,1
        1,9,1
        1,10,1
        1,11,1
        1,12,1
        1,13,1
        1,14,1
        2,1,0
        2,2,0
        2,3,1
        2,4,1
        2,5,1
        2,6,1
        2,7,1
        2,8,1
        2,9,1
        2,10,1
        2,11,1
        2,12,1
        2,13,1
        2,14,1
        3,1,1
        3,2,1
        3,3,0
        3,4,0
        3,5,0
        3,6,0
        3,7,1
        3,8,1
        3,9,1
        3,10,1
        3,11,1
        3,12,1
        3,13,1
        3,14,1
        4,1,1
        4,2,1
        4,3,0
        4,4,0
        4,5,0
        4,6,0
        4,7,1
        4,8,1
        4,9,1
        4,10,1
        4,11,1
        4,12,1
        4,13,1
        4,14,1
        5,1,1
        5,2,1
        5,3,0
        5,4,0
        5,5,0
        5,6,0
        5,7,1
        5,8,1
        5,9,1
        5,10,1
        5,11,1
        5,12,1
        5,13,1
        5,14,1
        6,1,1
        6,2,1
        6,3,0
        6,4,0
        6,5,0
        6,6,0
        6,7,1
        6,8,1
        6,9,1
        6,10,1
        6,11,1
        6,12,1
        6,13,1
        6,14,1
        7,1,1
        7,2,1
        7,3,1
        7,4,1
        7,5,1
        7,6,1
        7,7,0
        7,8,1
        7,9,1
        7,10,1
        7,11,1
        7,12,1
        7,13,1
        7,14,1
        8,1,1
        8,2,1
        8,3,1
        8,4,1
        8,5,1
        8,6,1
        8,7,1
        8,8,0
        8,9,0
        8,10,0
        8,11,1
        8,12,0
        8,13,1
        8,14,0
        9,1,1
        9,2,1
        9,3,1
        9,4,1
        9,5,1
        9,6,1
        9,7,1
        9,8,1
        9,9,0
        9,10,0
        9,11,1
        9,12,0
        9,13,1
        9,14,0
        10,1,1
        10,2,1
        10,3,1
        10,4,1
        10,5,1
        10,6,1
        10,7,1
        10,8,1
        10,9,0
        10,10,0
        10,11,1
        10,12,0
        10,13,0
        10,14,0
        11,1,1
        11,2,1
        11,3,1
        11,4,1
        11,5,1
        11,6,1
        11,7,1
        11,8,1
        11,9,1
        11,10,1
        11,11,0
        11,12,1
        11,13,0
        11,14,1
        12,1,1
        12,2,1
        12,3,1
        12,4,1
        12,5,1
        12,6,1
        12,7,1
        12,8,1
        12,9,0
        12,10,0
        12,11,1
        12,12,0
        12,13,0
        12,14,0
        13,1,1
        13,2,1
        13,3,1
        13,4,1
        13,5,1
        13,6,1
        13,7,1
        13,8,1
        13,9,1
        13,10,0
        13,11,0
        13,12,0
        13,13,0
        13,14,0
        14,1,1
        14,2,1
        14,3,1
        14,4,1
        14,5,1
        14,6,1
        14,7,1
        14,8,1
        14,9,0
        14,10,0
        14,11,0
        14,12,0
        14,13,0
        14,14,0""")

        xings_df = pd.read_csv(xings, sep = ',')

        df_mod = pd.merge(df, xings_df, how='left', left_on=['gy_i','gy_j'], right_on=['gy_i','gy_j'])
        is_nan = np.isnan(df_mod['crossing'])
        df_mod['crossing'][is_nan] = 0
        return df_mod