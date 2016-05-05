##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage5.step10.truckassign
##--Purpose: Convert Trucks to PCE
##---------------------------------------------------------------------
import inro.modeller as _m
import os
import traceback as _traceback

import simplejson


class TruckAssign(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Convert Trucks to PCE"
        pb.description = "Tool that converts trucks to pces; lightx1.5; heavy x2.5"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):


        self.tool_run_msg = ""

        try:
            self.__call__(_m.Modeller().emmebank)
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Truck Assignment Tool")
    def __call__(self, eb, AMScenario, MDScenario):
    ### PCE Calculation
        util = _m.Modeller().tool("translink.emme.util")

        util.initmat(eb, "mf1040", "CBLgAp", "CB LgTruck AM PCE", 0)
        util.initmat(eb, "mf1041", "CBHvAp", "CB HvTruck AM PCE", 0)
        util.initmat(eb, "mf1042", "IRLgAp", "IR LgTruck AM PCE", 0)
        util.initmat(eb, "mf1043", "IRHvAp", "IR HvTruck AM PCE", 0)
        util.initmat(eb, "mf1044", "APHvAp", "AP HvTruck AM PCE", 0)
        util.initmat(eb, "mf1045", "RGLgAp", "RG LgTruck AM PCE", 0)
        util.initmat(eb, "mf1046", "RGHvAp", "RG HvTruck AM PCE", 0)
        util.initmat(eb, "mf1047", "CBLgMp", "CB LgTruck MD PCE", 0)
        util.initmat(eb, "mf1048", "CBHvMp", "CB HvTruck MD PCE", 0)
        util.initmat(eb, "mf1049", "IRLgMp", "IR LgTruck MD PCE", 0)
        util.initmat(eb, "mf1050", "IRHvMp", "IR HvTruck MD PCE", 0)
        util.initmat(eb, "mf1051", "APHvMp", "AP HvTruck MD PCE", 0)
        util.initmat(eb, "mf1052", "RGLgMp", "RG LgTruck MD PCE", 0)
        util.initmat(eb, "mf1053", "RGHvMp", "RG HvTruck MD PCE", 0)

        AMList1=["mf1002","mf1012","mf1035","mf1005","mf1013","mf1021","mf1037"]

        AMList2=["mf1040","mf1042","mf1045","mf1041","mf1043","mf1044","mf1046"]

        MDList1=["mf1003","mf1014","mf1036","mf1006","mf1015","mf1022","mf1038"]

        MDList2=["mf1047","mf1049","mf1052","mf1048","mf1050","mf1051","mf1053"]

        Ratios=[1.5,1.5,1.5,2.5,2.5,2.5,2.5]

        specs = []
        for i in range (len(AMList1)):
            specs.append(util.matrix_spec(AMList2[i], AMList1[i] + "*" + str(Ratios[i])))
            specs.append(util.matrix_spec(MDList2[i], MDList1[i] + "*" + str(Ratios[i])))

        util.compute_matrix(specs)

        specs = []
        specs.append(util.matrix_spec("mf980", "mf1002 + mf1012 + mf1035"))
        specs.append(util.matrix_spec("mf981", "mf1005 + mf1013 + mf1021 + mf1037"))
        specs.append(util.matrix_spec("mf982", "mf1003 + mf1014 + mf1036"))
        specs.append(util.matrix_spec("mf983", "mf1006 + mf1015 + mf1022 + mf1038"))
        util.compute_matrix(specs)

#### Truck Assignment (for now based on stand-alone assumption)

        AMTruckSpec="""{
                "type": "SOLA_TRAFFIC_ASSIGNMENT",
                "classes": [

                {
                    "mode": "d",
                    "demand": "mf20",
                    "generalized_cost": {
                        "link_costs": "@sovoc",
                        "perception_factor": 6
                    },
                    "results": {
                        "link_volumes": "@sov1",
                        "turn_volumes": "@tsov1",
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": null
                },
                {
                    "mode": "d",
                    "demand": "mf21",
                    "generalized_cost": {
                        "link_costs": "@sovoc",
                        "perception_factor": 3
                    },
                    "results": {
                        "link_volumes": "@sov2",
                        "turn_volumes": "@tsov2",
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": null
                },
                {
                    "mode": "d",
                    "demand": "mf22",
                    "generalized_cost": {
                        "link_costs": "@sovoc",
                        "perception_factor": 3
                    },
                    "results": {
                        "link_volumes": "@sov3",
                        "turn_volumes": "@tsov3",
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": null
                },
                {
                    "mode": "d",
                    "demand": "mf23",
                    "generalized_cost": {
                        "link_costs": "@sovoc",
                        "perception_factor": 12
                    },
                    "results": {
                        "link_volumes": "@sov4",
                        "turn_volumes": "@tsov4",
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": null
                },
                {
                    "mode": "d",
                    "demand": "mf24",
                    "generalized_cost": {
                        "link_costs": "@sovoc",
                        "perception_factor": 6
                    },
                    "results": {
                        "link_volumes": "@sov5",
                        "turn_volumes": "@tsov5",
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": null
                },
                {
                    "mode": "c",
                    "demand": "mf26",
                    "generalized_cost": {
                        "link_costs": "@hovoc",
                        "perception_factor": 6
                    },
                    "results": {
                        "link_volumes": "@hov1",
                        "turn_volumes": "@thov1",
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": null
                },
                {
                    "mode": "c",
                    "demand": "mf27",
                    "generalized_cost": {
                        "link_costs": "@hovoc",
                        "perception_factor": 3
                    },
                    "results": {
                        "link_volumes": "@hov2",
                        "turn_volumes": "@thov2",
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": null
                },
                {
                    "mode": "c",
                    "demand": "mf28",
                    "generalized_cost": {
                        "link_costs": "@hovoc",
                        "perception_factor": 3
                    },
                    "results": {
                        "link_volumes": "@hov3",
                        "turn_volumes": "@thov3",
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": null
                },
                {
                    "mode": "c",
                    "demand": "mf29",
                    "generalized_cost": {
                        "link_costs": "@hovoc",
                        "perception_factor": 12
                    },
                    "results": {
                        "link_volumes": "@hov4",
                        "turn_volumes": "@thov4",
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": null
                },
                {
                    "mode": "c",
                    "demand": "mf30",
                    "generalized_cost": {
                        "link_costs": "@hovoc",
                        "perception_factor": 6
                    },
                    "results": {
                        "link_volumes": "@hov5",
                        "turn_volumes": "@thov5",
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": null
                },

                    {
                        "mode": "x",
                        "demand": "mf1040",
                        "generalized_cost": {
                            "link_costs": "@lgvoc",
                            "perception_factor": 2.03
                        },
                        "results": {
                            "link_volumes": "@llgcb",
                            "turn_volumes": null,
                            "od_travel_times": {
                                "shortest_paths": null
                            }
                        },
                        "analysis": {
                            "analyzed_demand": null,
                            "results": {
                                "od_values": null,
                                "selected_link_volumes": null,
                                "selected_turn_volumes": null
                            }
                        }
                    },
                    {
                        "mode": "x",
                        "demand": "mf1042",
                        "generalized_cost": {
                            "link_costs": "@lgvoc",
                            "perception_factor": 2.03
                        },
                        "results": {
                            "link_volumes": "@llgir",
                            "turn_volumes": null,
                            "od_travel_times": {
                                "shortest_paths": null
                            }
                        },
                        "analysis": {
                            "analyzed_demand": null,
                            "results": {
                                "od_values": null,
                                "selected_link_volumes": null,
                                "selected_turn_volumes": null
                            }
                        }
                    },
                    {
                        "mode": "x",
                        "demand": "mf1045",
                        "generalized_cost": {
                            "link_costs": "@lgvoc",
                            "perception_factor": 2.03
                        },
                        "results": {
                            "link_volumes": "@llgrg",
                            "turn_volumes": null,
                            "od_travel_times": {
                                "shortest_paths": null
                            }
                        },
                        "analysis": {
                            "analyzed_demand": null,
                            "results": {
                                "od_values": null,
                                "selected_link_volumes": null,
                                "selected_turn_volumes": null
                            }
                        }
                    },
                    {
                        "mode": "t",
                        "demand": "mf1041",
                        "generalized_cost": {
                            "link_costs": "@hgvoc",
                            "perception_factor": 1.43
                        },
                        "results": {
                            "link_volumes": "@lhvcb",
                            "turn_volumes": null,
                            "od_travel_times": {
                                "shortest_paths": null
                            }
                        },
                        "analysis": {
                            "analyzed_demand": null,
                            "results": {
                                "od_values": null,
                                "selected_link_volumes": null,
                                "selected_turn_volumes": null
                            }
                        }
                    },
                    {
                        "mode": "t",
                        "demand": "mf1043",
                        "generalized_cost": {
                            "link_costs": "@hgvoc",
                            "perception_factor": 1.43
                        },
                        "results": {
                            "link_volumes": "@lhvir",
                            "turn_volumes": null,
                            "od_travel_times": {
                                "shortest_paths": null
                            }
                        },
                        "analysis": {
                            "analyzed_demand": null,
                            "results": {
                                "od_values": null,
                                "selected_link_volumes": null,
                                "selected_turn_volumes": null
                            }
                        }
                    },
                    {
                        "mode": "t",
                        "demand": "mf1044",
                        "generalized_cost": {
                            "link_costs": "@hgvoc",
                            "perception_factor": 1.43
                        },
                        "results": {
                            "link_volumes": "@lhvap",
                            "turn_volumes": null,
                            "od_travel_times": {
                                "shortest_paths": null
                            }
                        },
                        "analysis": {
                            "analyzed_demand": null,
                            "results": {
                                "od_values": null,
                                "selected_link_volumes": null,
                                "selected_turn_volumes": null
                            }
                        }
                    },
                    {
                        "mode": "t",
                        "demand": "mf1046",
                        "generalized_cost": {
                            "link_costs": "@hgvoc",
                            "perception_factor": 1.43
                        },
                        "results": {
                            "link_volumes": "@lhvrg",
                            "turn_volumes": null,
                            "od_travel_times": {
                                "shortest_paths": null
                            }
                        },
                        "analysis": {
                            "analyzed_demand": null,
                            "results": {
                                "od_values": null,
                                "selected_link_volumes": null,
                                "selected_turn_volumes": null
                            }
                        }
                    }
                ],
                "performance_settings": {
                    "number_of_processors": 4
                },
                "background_traffic": {
                    "link_component": null,
                    "turn_component": null,
                    "add_transit_vehicles": true
                },
                "path_analysis": null,
                "cutoff_analysis": null,
                "traversal_analysis": null,
                "stopping_criteria": {
                    "max_iterations": 100,
                    "relative_gap": 0.0000,
                    "best_relative_gap": 0.01,
                    "normalized_gap": 0.01
                }
            }"""
        MDTruckSpec="""{
            "type": "SOLA_TRAFFIC_ASSIGNMENT",
            "classes": [
            {
                    "mode": "d",
                    "demand": "mf52",
                    "generalized_cost": {
                        "link_costs": "@sovoc",
                        "perception_factor": 6
                    },
                    "results": {
                        "link_volumes": "@sov1",
                        "turn_volumes": "@tsov1",
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": null
                },
                {
                    "mode": "d",
                    "demand": "mf53",
                    "generalized_cost": {
                        "link_costs": "@sovoc",
                        "perception_factor": 3
                    },
                    "results": {
                        "link_volumes": "@sov2",
                        "turn_volumes": "@tsov2",
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": null
                },
                {
                    "mode": "d",
                    "demand": "mf54",
                    "generalized_cost": {
                        "link_costs": "@sovoc",
                        "perception_factor": 3
                    },
                    "results": {
                        "link_volumes": "@sov3",
                        "turn_volumes": "@tsov3",
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": null
                },
                {
                    "mode": "d",
                    "demand": "mf55",
                    "generalized_cost": {
                        "link_costs": "@sovoc",
                        "perception_factor": 12
                    },
                    "results": {
                        "link_volumes": "@sov4",
                        "turn_volumes": "@tsov4",
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": null
                },
                {
                    "mode": "d",
                    "demand": "mf56",
                    "generalized_cost": {
                        "link_costs": "@sovoc",
                        "perception_factor": 6
                    },
                    "results": {
                        "link_volumes": "@sov5",
                        "turn_volumes": "@tsov5",
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": null
                },
                {
                    "mode": "c",
                    "demand": "mf58",
                    "generalized_cost": {
                        "link_costs": "@hovoc",
                        "perception_factor": 6
                    },
                    "results": {
                        "link_volumes": "@hov1",
                        "turn_volumes": "@thov1",
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": null
                },
                {
                    "mode": "c",
                    "demand": "mf59",
                    "generalized_cost": {
                        "link_costs": "@hovoc",
                        "perception_factor": 3
                    },
                    "results": {
                        "link_volumes": "@hov2",
                        "turn_volumes": "@thov2",
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": null
                },
                {
                    "mode": "c",
                    "demand": "mf60",
                    "generalized_cost": {
                        "link_costs": "@hovoc",
                        "perception_factor": 3
                    },
                    "results": {
                        "link_volumes": "@hov3",
                        "turn_volumes": "@thov3",
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": null
                },
                {
                    "mode": "c",
                    "demand": "mf61",
                    "generalized_cost": {
                        "link_costs": "@hovoc",
                        "perception_factor": 12
                    },
                    "results": {
                        "link_volumes": "@hov4",
                        "turn_volumes": "@thov4",
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": null
                },
                {
                    "mode": "c",
                    "demand": "mf62",
                    "generalized_cost": {
                        "link_costs": "@hovoc",
                        "perception_factor": 6
                    },
                    "results": {
                        "link_volumes": "@hov5",
                        "turn_volumes": "@thov5",
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": null
                },

                {
                    "mode": "x",
                    "demand": "mf1047",
                    "generalized_cost": {
                        "link_costs": "@lgvoc",
                        "perception_factor": 2.03
                    },
                    "results": {
                        "link_volumes": "@llgcb",
                        "turn_volumes": null,
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": {
                        "analyzed_demand": null,
                        "results": {
                            "od_values": null,
                            "selected_link_volumes": null,
                            "selected_turn_volumes": null
                        }
                    }
                },
                {
                    "mode": "x",
                    "demand": "mf1049",
                    "generalized_cost": {
                        "link_costs": "@lgvoc",
                        "perception_factor": 2.03
                    },
                    "results": {
                        "link_volumes": "@llgir",
                        "turn_volumes": null,
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": {
                        "analyzed_demand": null,
                        "results": {
                            "od_values": null,
                            "selected_link_volumes": null,
                            "selected_turn_volumes": null
                        }
                    }
                },
                {
                    "mode": "x",
                    "demand": "mf1052",
                    "generalized_cost": {
                        "link_costs": "@lgvoc",
                        "perception_factor": 2.03
                    },
                    "results": {
                        "link_volumes": "@llgrg",
                        "turn_volumes": null,
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": {
                        "analyzed_demand": null,
                        "results": {
                            "od_values": null,
                            "selected_link_volumes": null,
                            "selected_turn_volumes": null
                        }
                    }
                },
                {
                    "mode": "t",
                    "demand": "mf1048",
                    "generalized_cost": {
                        "link_costs": "@hgvoc",
                        "perception_factor": 1.43
                    },
                    "results": {
                        "link_volumes": "@lhvcb",
                        "turn_volumes": null,
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": {
                        "analyzed_demand": null,
                        "results": {
                            "od_values": null,
                            "selected_link_volumes": null,
                            "selected_turn_volumes": null
                        }
                    }
                },
                {
                    "mode": "t",
                    "demand": "mf1050",
                    "generalized_cost": {
                        "link_costs": "@hgvoc",
                        "perception_factor": 1.43
                    },
                    "results": {
                        "link_volumes": "@lhvir",
                        "turn_volumes": null,
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": {
                        "analyzed_demand": null,
                        "results": {
                            "od_values": null,
                            "selected_link_volumes": null,
                            "selected_turn_volumes": null
                        }
                    }
                },
                {
                    "mode": "t",
                    "demand": "mf1051",
                    "generalized_cost": {
                        "link_costs": "@hgvoc",
                        "perception_factor": 1.43
                    },
                    "results": {
                        "link_volumes": "@lhvap",
                        "turn_volumes": null,
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": {
                        "analyzed_demand": null,
                        "results": {
                            "od_values": null,
                            "selected_link_volumes": null,
                            "selected_turn_volumes": null
                        }
                    }
                },
                {
                    "mode": "t",
                    "demand": "mf1053",
                    "generalized_cost": {
                        "link_costs": "@hgvoc",
                        "perception_factor": 1.43
                    },
                    "results": {
                        "link_volumes": "@lhvrg",
                        "turn_volumes": null,
                        "od_travel_times": {
                            "shortest_paths": null
                        }
                    },
                    "analysis": {
                        "analyzed_demand": null,
                        "results": {
                            "od_values": null,
                            "selected_link_volumes": null,
                            "selected_turn_volumes": null
                        }
                    }
                }
            ],
            "performance_settings": {
                "number_of_processors": 4
            },
            "background_traffic": {
                "link_component": null,
                "turn_component": null,
                "add_transit_vehicles": true
            },
            "path_analysis": null,
            "cutoff_analysis": null,
            "traversal_analysis": null,
            "stopping_criteria": {
                "max_iterations": 100,
                    "relative_gap": 0.0000,
                    "best_relative_gap": 0.01,
                    "normalized_gap": 0.01
             }
            }"""

        AMTruckSpec1=simplejson.loads(AMTruckSpec)
        MDTruckSpec1=simplejson.loads(MDTruckSpec)


        ScenAM = eb.scenario(AMScenario)
        ScenMD = eb.scenario(MDScenario)
        # Calculate SOV and HOV as Background Traffic
        calc_att= _m.Modeller().tool("inro.emme.network_calculation.network_calculator")

        spec_dict = {
                "result": None,
                "expression": "@wsovl+@whovl",
                "aggregation": None,
                "selections": {
                    "link": "all"
                },
                "type": "NETWORK_CALCULATION"
            }

        expressions_list = [
        ["0", "all", "@tkpen"],
        ["length*100", "mode=n", "@tkpen"],
        ["length*0.56+@tolls*3+@tkpen", "all", "@hgvoc"],
        ["@wsovl+@whovl","all","ul3"]
        ]

        for expression, selection, result in expressions_list:
            spec_dict["expression"] = expression
            spec_dict["selections"]["link"] = selection
            spec_dict["result"] = result
            calc_att(spec_dict, scenario=ScenAM)
            calc_att(spec_dict, scenario=ScenMD)

        truckcassignment = _m.Modeller().tool("inro.emme.traffic_assignment.sola_traffic_assignment")

        for i in range (10, 17):

            AMTruckSpec1["classes"][i]["demand"]=AMList1[i-10]
            MDTruckSpec1["classes"][i]["demand"]=MDList1[i-10]

        truckcassignment(AMTruckSpec1, scenario=ScenAM)
        truckcassignment(MDTruckSpec1, scenario=ScenMD)
