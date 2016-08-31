##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step5.parkandride
##--Purpose: reassigns transit demand to park and ride
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback
import os

# Mode split coefficients (based on those used in Phase 1 model)
mode1 = str(0.075)  #Exponential coefficient
mode2r = str(988)   #Rail Mode bias mf identifier
mode2b = str(989)   #Bus  Mode bias mf identifier
mode3 = str(0.075)  #Traffic impedance scale factor
mode4 = str(0.075)  #Transit impedance scale factor


class ParkAndRide(_m.Tool()):

    tool_run_msg = ""
    scenario = _m.Attribute(_m.InstanceType)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Park and Ride Module"
        pb.description = "Converts bus and rail demand to park and ride"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        pb.add_select_scenario("scenario", title="AM scenario:",
                               note="For matrix zone system reference.")

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            self(self.scenario)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, error:
            self.tool_run_msg = _m.PageBuilder.format_exception(
                error, _traceback.format_exc(error))
            raise

    @_m.logbook_trace("Calculate P/R impedance and demand for bus and rail", save_arguments=True)
    def __call__(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")
        matrix_txn = _m.Modeller().tool(
            "inro.emme.data.matrix.matrix_transaction")

        with _m.logbook_trace("Initialization"):
            input_path = util.get_input_path(scenario.emmebank)

            self.Matrix_Batchins(scenario.emmebank)
            input_dir = os.path.join(input_path, "PR-setup.311")
            matrix_txn(input_dir, scenario=scenario)

            spec = {
                "expression": "default_expression",
                "result": "defaul_result",
                "constraint": {
                    "by_value": None,
                    "by_zone": None
                },
                "aggregation": {
                    "origins": None,
                    "destinations": None
                },
                "type": "MATRIX_CALCULATION"
            }

            #Type codes: 1=rail work 2= bus work 3= rail nonwork 4= bus nonwork

            #Define number of work spaces
            spec["expression"] = "md60"
            spec["result"] = "md65"
            util.compute_matrix(spec, scenario=scenario)

            #Allow for additional lot overcapacity congestion impedance (set to zero for now)
            #Note that lot charges are included in auto impedance component
            spec["expression"] = "0"
            spec["result"] = "md63"
            util.compute_matrix(spec, scenario=scenario)

        #Run park and ride for rail-access work trips
        with _m.logbook_trace("For rail-access work trips"):
            asg_type = 1
            self.AutoImpedance(asg_type, scenario)
            self.TransitImpedance(asg_type, scenario)
            self.PR_RailImpedance(asg_type, scenario)
            self.PRdemand(asg_type, scenario)
            self.PRutility(asg_type, scenario)
            self.PRmodel(asg_type, scenario)

            spec["expression"] = "md64"
            spec["result"] = "md68"
            util.compute_matrix(spec, scenario=scenario)

            spec["expression"] = "(md60-(md64*md72)).max.1"
            spec["result"] = "md65"
            util.compute_matrix(spec, scenario=scenario)
            # Copy pr model output for auto and transit legs
            spec["expression"] = "mf209*(gm(q).le.24)"
            spec["result"] = "mf194"
            util.compute_matrix(spec, scenario=scenario)
            spec["expression"] = "mf208"
            spec["result"] = "mf196"
            util.compute_matrix(spec, scenario=scenario)
            spec["expression"] = "mf204"
            spec["result"] = "mf192"
            util.compute_matrix(spec, scenario=scenario)

        #Run park and ride for bus-access work trips
        with _m.logbook_trace("For bus-access work trips"):
            asg_type = 2
            self.AutoImpedance(asg_type, scenario)
            self.TransitImpedance(asg_type, scenario)
            self.PR_BusImpedance(asg_type, scenario)
            self.PRdemand(asg_type, scenario)
            self.PRutility(asg_type, scenario)
            self.PRmodel(asg_type, scenario)

            #Store work lot usage
            spec["expression"] = "md64"
            spec["result"] = "md69"
            util.compute_matrix(spec, scenario=scenario)

            #Define number of non-work spaces
            spec["expression"] = "md61"
            spec["result"] = "md65"
            util.compute_matrix(spec, scenario=scenario)
            #Copy pr model output for auto and transit legs
            spec["expression"] = "mf209*(gm(q).le.24)"
            spec["result"] = "mf195"
            util.compute_matrix(spec, scenario=scenario)
            spec["expression"] = "mf208"
            spec["result"] = "mf197"
            util.compute_matrix(spec, scenario=scenario)
            spec["expression"] = "mf204"
            spec["result"] = "mf193"
            util.compute_matrix(spec, scenario=scenario)

        #Run park and ride for rail-access non-work trips
        with _m.logbook_trace("For rail-access non-work trips"):
            asg_type = 3
            self.AutoImpedance(asg_type, scenario)
            self.TransitImpedance(asg_type, scenario)
            self.PR_RailImpedance(asg_type, scenario)
            self.PRdemand(asg_type, scenario)
            self.PRutility(asg_type, scenario)
            self.PRmodel(asg_type, scenario)

            spec["expression"] = "md64"
            spec["result"] = "md70"
            util.compute_matrix(spec, scenario=scenario)
            spec["expression"] = "(md61-(md64*md72)).max.1"
            spec["result"] = "md65"
            util.compute_matrix(spec, scenario=scenario)
            #Copy pr model output for auto and transit legs
            spec["expression"] = "mf194+(mf209*(gm(q).le.24))"
            spec["result"] = "mf194"
            util.compute_matrix(spec, scenario=scenario)
            spec["expression"] = "mf208"
            spec["result"] = "mf198"
            util.compute_matrix(spec, scenario=scenario)
            spec["expression"] = "mf204+mf192"
            spec["result"] = "mf192"
            util.compute_matrix(spec, scenario=scenario)

        # Run park and ride for bus-access non-work trips
        with _m.logbook_trace("For bus-access non-work trips"):
            asg_type = 4
            self.AutoImpedance(asg_type, scenario)
            self.TransitImpedance(asg_type, scenario)
            self.PR_BusImpedance(asg_type, scenario)
            self.PRdemand(asg_type, scenario)
            self.PRutility(asg_type, scenario)
            self.PRmodel(asg_type, scenario)

            spec["expression"] = "md64"
            spec["result"] = "md71"
            util.compute_matrix(spec, scenario=scenario)
            #Copy pr model output for auto and transit legs
            spec["expression"] = "mf195+(mf209*(gm(q).le.24))"
            spec["result"] = "mf195"
            util.compute_matrix(spec, scenario=scenario)
            spec["expression"] = "mf208"
            spec["result"] = "mf199"
            util.compute_matrix(spec, scenario=scenario)
            spec["expression"] = "mf204+mf193"
            spec["result"] = "mf193"
            util.compute_matrix(spec, scenario=scenario)

        #at the end, the demand components should be used to modify original matrices
        #or to create new rail bus and auto matrices
        with _m.logbook_trace("Final rail and bus demand"):
            spec["expression"] = "mf854"
            spec["result"] = "mf986"
            util.compute_matrix(spec, scenario=scenario)
            spec["expression"] = "mf853"
            spec["result"] = "mf987"
            util.compute_matrix(spec, scenario=scenario)

            spec["expression"] = "(mf854-mf192+mf194).max.0"
            spec["result"] = "mf854"
            util.compute_matrix(spec, scenario=scenario)
            spec["expression"] = "(mf853-mf193+mf195).max.0"
            spec["result"] = "mf853"
            util.compute_matrix(spec, scenario=scenario)

            spec["expression"] = "(mf880-mf192'+mf194').max.0"
            spec["result"] = "mf880"
            util.compute_matrix(spec, scenario=scenario)
            spec["expression"] = "(mf879-mf193'+mf195').max.0"
            spec["result"] = "mf879"
            util.compute_matrix(spec, scenario=scenario)

        # Add the leg one park and ride demand to the auto demand
        # adding work demand to SOV, med income (mf844), and non-work to med-high income (mf847)
        with _m.logbook_trace("Final auto demand"):
            spec["expression"] = "mf844+mf196+mf197"
            spec["result"] = "mf844"
            util.compute_matrix(spec, scenario=scenario)
            spec["expression"] = "mf847+mf198+mf199"
            spec["result"] = "mf847"
            util.compute_matrix(spec, scenario=scenario)

            spec["expression"] = "mf870+mf196'+mf197'"
            spec["result"] = "mf870"
            util.compute_matrix(spec, scenario=scenario)
            spec["expression"] = "mf873+mf198'+mf199'"
            spec["result"] = "mf873"
            util.compute_matrix(spec, scenario=scenario)

    @_m.logbook_trace("Calculating park and ride rail impedance")
    def PR_RailImpedance(self, asg_type, scenario):
        #Calculate park and ride impedance by lot using triple index operation
        compute_impedance = _m.Modeller().tool(
            "inro.emme.matrix_calculation.matrix_triple_index_operation")
        init_matrix = _m.Modeller().tool("inro.emme.data.matrix.init_matrix")

        init_matrix(matrix="mf205", init_value=0.0, scenario=scenario)

        spec = {
            "pk_operand": "mf202",
            "kq_operand": "mf203",
            "qk_operand": None,
            "combination_operator": "+",
            "masks": [
                {
                    "operator": "+",
                    "pq_operand": None,
                    "pk_operand": None,
                    "kq_operand": None,
                    "k_operand": "md63",
                    "constant_operand": None
                }
            ],
            "contraction_operator": ".min.",
            "result": "mf205",
            "index_result": None,
            "constraint": {
                "by_zone": {
                    "origins": "gp26",
                    "intermediates": "105",
                    "destinations": "gr1,gr4"
                },
                "by_value": None
            },
            "type": "MATRIX_TRIPLE_INDEX_OPERATION"
        }

        #Determine constraints
        spec["constraint"]["by_zone"]["origins"] = "gp26"
        spec["constraint"]["by_zone"]["intermediates"] = "105"
        spec["constraint"]["by_zone"]["destinations"] = "gr1-gr4;gr6"
        report = compute_impedance(spec, scenario=scenario)
        spec["constraint"]["by_zone"]["origins"] = "gp8-gp14;gp16"
        spec["constraint"]["by_zone"]["intermediates"] = "109"
        spec["constraint"]["by_zone"]["destinations"] = "gr1-gr4"
        report = compute_impedance(spec, scenario=scenario)
        spec["constraint"]["by_zone"]["origins"] = "gp8-gp15"
        spec["constraint"]["by_zone"]["intermediates"] = "111"
        spec["constraint"]["by_zone"]["destinations"] = "gr1-gr4"
        report = compute_impedance(spec, scenario=scenario)
        spec["constraint"]["by_zone"]["origins"] = "gp17-gp20;gp27"
        spec["constraint"]["by_zone"]["intermediates"] = "114"
        spec["constraint"]["by_zone"]["destinations"] = "gr1-gr4"
        report = compute_impedance(spec, scenario=scenario)
        spec["constraint"]["by_zone"]["origins"] = "gp19;gp21;gp27"
        spec["constraint"]["by_zone"]["intermediates"] = "116"
        spec["constraint"]["by_zone"]["destinations"] = "gr1-gr4"
        report = compute_impedance(spec, scenario=scenario)
        spec["constraint"]["by_zone"]["origins"] = "gp18;gp20"
        spec["constraint"]["by_zone"]["intermediates"] = "117"
        spec["constraint"]["by_zone"]["destinations"] = "gr1-gr4"
        report = compute_impedance(spec, scenario=scenario)
        spec["constraint"]["by_zone"]["origins"] = "gp22"
        spec["constraint"]["by_zone"]["intermediates"] = "118"
        spec["constraint"]["by_zone"]["destinations"] = "gr1-gr4"
        report = compute_impedance(spec, scenario=scenario)
        spec["constraint"]["by_zone"]["origins"] = "gp23"
        spec["constraint"]["by_zone"]["intermediates"] = "119"
        spec["constraint"]["by_zone"]["destinations"] = "gr1-gr4"
        report = compute_impedance(spec, scenario=scenario)
        spec["constraint"]["by_zone"]["origins"] = "gp24;gp29"
        spec["constraint"]["by_zone"]["intermediates"] = "120"
        spec["constraint"]["by_zone"]["destinations"] = "gr1"
        report = compute_impedance(spec, scenario=scenario)
        spec["constraint"]["by_zone"]["origins"] = "gp27;gp28"
        spec["constraint"]["by_zone"]["intermediates"] = "127"
        spec["constraint"]["by_zone"]["destinations"] = "gr1;gr4;gr6"
        report = compute_impedance(spec, scenario=scenario)

    @_m.logbook_trace("Calculating park and ride bus impedance")
    def PR_BusImpedance(self, asg_type, scenario):
        #Calculate park and ride impedance by lot using triple index operation
        compute_impedance = _m.Modeller().tool(
            "inro.emme.matrix_calculation.matrix_triple_index_operation")
        init_matrix = _m.Modeller().tool("inro.emme.data.matrix.init_matrix")

        init_matrix(matrix="mf205", init_value=0.0, scenario=scenario)

        spec = {
            "pk_operand": "mf202",
            "kq_operand": "mf203",
            "qk_operand": None,
            "combination_operator": "+",
            "masks": [
                {
                    "operator": "+",
                    "pq_operand": None,
                    "pk_operand": None,
                    "kq_operand": None,
                    "k_operand": "md63",
                    "constant_operand": None
                }
            ],
            "contraction_operator": ".min.",
            "result": "mf205",
            "index_result": None,
            "constraint": {
                "by_zone": {
                    "origins": "gp2",
                    "intermediates": "102",
                    "destinations": "gr1,gr4"
                },
                "by_value": None
            },
            "type": "MATRIX_TRIPLE_INDEX_OPERATION"
        }

        #Determine constraints
        spec["constraint"]["by_zone"]["origins"] = "gp2"
        spec["constraint"]["by_zone"]["intermediates"] = "102"
        spec["constraint"]["by_zone"]["destinations"] = "gr1-gr4"
        report = compute_impedance(spec, scenario=scenario)
        spec["constraint"]["by_zone"]["origins"] = "gp3"
        spec["constraint"]["by_zone"]["intermediates"] = "103"
        spec["constraint"]["by_zone"]["destinations"] = "gr1-gr4"
        report = compute_impedance(spec, scenario=scenario)
        spec["constraint"]["by_zone"]["origins"] = "gp4"
        spec["constraint"]["by_zone"]["intermediates"] = "104"
        spec["constraint"]["by_zone"]["destinations"] = "gr1-gr4"
        report = compute_impedance(spec, scenario=scenario)
        spec["constraint"]["by_zone"]["origins"] = "gp5;gp26"
        spec["constraint"]["by_zone"]["intermediates"] = "105"
        spec["constraint"]["by_zone"]["destinations"] = "gr1-gr4;gr6"
        report = compute_impedance(spec, scenario=scenario)
        spec["constraint"]["by_zone"]["origins"] = "gp6-gp7"
        spec["constraint"]["by_zone"]["intermediates"] = "106"
        spec["constraint"]["by_zone"]["destinations"] = "gr1-gr6"
        report = compute_impedance(spec, scenario=scenario)
        spec["constraint"]["by_zone"]["origins"] = "gp6-gp7"
        spec["constraint"]["by_zone"]["intermediates"] = "107"
        spec["constraint"]["by_zone"]["destinations"] = "gr1-gr6"
        report = compute_impedance(spec, scenario=scenario)
        spec["constraint"]["by_zone"]["origins"] = "gp8"
        spec["constraint"]["by_zone"]["intermediates"] = "109"
        spec["constraint"]["by_zone"]["destinations"] = "gr1-gr4"
        report = compute_impedance(spec, scenario=scenario)
        spec["constraint"]["by_zone"]["origins"] = "gp8-gp15"
        spec["constraint"]["by_zone"]["intermediates"] = "111"
        spec["constraint"]["by_zone"]["destinations"] = "gr1-gr4"
        report = compute_impedance(spec, scenario=scenario)
        spec["constraint"]["by_zone"]["origins"] = "gp11-gp14"
        spec["constraint"]["by_zone"]["intermediates"] = "112"
        spec["constraint"]["by_zone"]["destinations"] = "gr1-gr4"
        report = compute_impedance(spec, scenario=scenario)
        spec["constraint"]["by_zone"]["origins"] = "gp16;gp29"
        spec["constraint"]["by_zone"]["intermediates"] = "113"
        spec["constraint"]["by_zone"]["destinations"] = "gr1-gr4"
        report = compute_impedance(spec, scenario=scenario)
        spec["constraint"]["by_zone"]["origins"] = "gp17-gp20;gp27"
        spec["constraint"]["by_zone"]["intermediates"] = "114"
        spec["constraint"]["by_zone"]["destinations"] = "gr1-gr4"
        report = compute_impedance(spec, scenario=scenario)
        spec["constraint"]["by_zone"]["origins"] = "gp25"
        spec["constraint"]["by_zone"]["intermediates"] = "121"
        spec["constraint"]["by_zone"]["destinations"] = "gr1-gr4;gr6"
        report = compute_impedance(spec, scenario=scenario)
        spec["constraint"]["by_zone"]["origins"] = "gp27-gp28"
        spec["constraint"]["by_zone"]["intermediates"] = "127"
        spec["constraint"]["by_zone"]["destinations"] = "gr3"
        report = compute_impedance(spec, scenario=scenario)

    @_m.logbook_trace("Calculating auto impedance")
    def AutoImpedance(self, asg_type, scenario):
        util = _m.Modeller().tool("translink.emme.util")

        #Calculate auto impedance
        if asg_type < 3:
            variables = {"VOT": "ms37",
                         "parking_cost": "md27",
                         "lot_charge": "ms37*md62"}
        elif asg_type >= 3:
            variables = {"VOT": "ms38",
                         "parking_cost": "md28",
                         "lot_charge": "ms38*md62"}

        expression = ("(mf101+ms19*mf102* %(VOT)s +(ms18+ms17)*mf100* %(VOT)s )"
                      "+ %(parking_cost)s * %(VOT)s "
                      "+ %(lot_charge)s" % variables)
        spec = util.matrix_spec("mf202", expression)
        util.compute_matrix(spec, scenario=scenario)

    @_m.logbook_trace("Calculating transit impedance")
    def TransitImpedance(self, asg_type, scenario):
        util = _m.Modeller().tool("translink.emme.util")

        #Calculate transit impedance
        if asg_type < 3:
            value_time = "ms37"
        elif asg_type >= 3:
            value_time = "ms38*0.5"
        expression = "(mf164+(mf163*2))+mf160*" + value_time
        spec = util.matrix_spec("mf203", expression)
        util.compute_matrix(spec, scenario=scenario)

    @_m.logbook_trace("Calculating park and ride demand by splitting transit into p/r")
    def PRdemand(self, asg_type, scenario):
        util = _m.Modeller().tool("translink.emme.util")
        eb = scenario.emmebank

        triple_index_op = _m.Modeller().tool(
            "inro.emme.matrix_calculation.matrix_triple_index_operation")
        create_matrix = _m.Modeller().tool(
            "inro.emme.data.matrix.create_matrix")

        spec = {
            "expression": "",
            "result": None,
            "constraint": {
                "by_value": {
                    "od_values": "mf995",
                    "interval_min": 1,
                    "interval_max": 999,
                    "condition": "INCLUDE"
                    },
                "by_zone": {
                    "origins": "gp1,gp28",
                    "destinations": "gr1,gr6"
                }
            },
            "aggregation": {
                "origins": None,
                "destinations": None
            },
            "type": "MATRIX_CALCULATION"
        }

        spec_triple_index = {
            "type": "MATRIX_TRIPLE_INDEX_OPERATION",
            "pk_operand": "",
            "kq_operand": "",
            "combination_operator": ".min.",
            "masks": [],
            "constraint": {
                "by_zone": {
                    "origins": "",
                    "intermediates": "",
                    "destinations": ""
                },
            },
            "contraction_operator": ".max.",
            "result": "mf995"
        }
        # Constrain the demand matrix, store feasible O-D pairs in mf995
        if asg_type in (1, 3):
            spec_triple_index["pk_operand"] = "mf201"
            spec_triple_index["kq_operand"] = "mf201"
            spec_triple_index["constraint"]["by_zone"] = {
                "origins": "gp8-gp24;gp26-gp29",
                "intermediates": "105;109;111;114;116;117-120;127",
                "destinations": "gr1,gr4;gr6"}
        else:
            spec_triple_index["pk_operand"] = "mf200"
            spec_triple_index["kq_operand"] = "mf200"
            spec_triple_index["constraint"]["by_zone"] = {
                "origins": "gp2-gp20;gp25-gp29",
                "intermediates": "102-107;109;111,114;121;127",
                "destinations": "gr1-gr6"}

        util.initmat(scenario.emmebank, "mf995", "cPNRdm", "constraint on PNR demand calcs", 0)
        triple_index_op(spec_triple_index, scenario=scenario)

        #Calculate park-and-ride demand
        if asg_type == 1:
            base_demand = "mf997"
            capacity_matrix = "mo932"
            mode2 = mode2r
        elif asg_type == 2:
            base_demand = "mf998"
            capacity_matrix = "mo959"
            mode2 = mode2b
        elif asg_type == 3:
            base_demand = "((mf854-mf997).max.0)"
            capacity_matrix = "mo962"
            mode2 = mode2r
        elif asg_type == 4:
            base_demand = "((mf853-mf998).max.0)"
            capacity_matrix = "mo931"
            mode2 = mode2b

        util.initmat(scenario.emmebank, "mf204", "PRdemd", "Park and ride demand input", 0)
        util.initmat(scenario.emmebank, "mo963", "PRorcp", "PR lot demand by origin gp", 0)
        util.initmat(scenario.emmebank, "mo964", "pzones", "Number of zones in each gp", 0)

        # Added constraint calculation
        specs = []
        spec = util.matrix_spec("mf204", "(%s)/(1+exp(%s*(mf205-mf203+mf%s)))" % (base_demand, mode1, mode2))
        spec["constraint"]["by_value"] = {"od_values": "mf995", "interval_min": 1, "interval_max": 999, "condition": "INCLUDE"}
        specs.append(spec)

        spec = util.matrix_spec("mo963", "mf204")
        spec["aggregation"] = {"origins": None, "destinations": "+"}
        specs.append(spec)

        spec = util.matrix_spec("mo964", "mo964'*0+(gp(p).eq.gp(q))*(gp(p).gt.0)")
        spec["aggregation"] = {"origins": None, "destinations": "+"}
        specs.append(spec)

        #multiply aggregated numbers by the number of zones in each partition
        #reduce mf204 by the ratio of origin demand to catchment area capacity
        # Added constraint calculation
        spec = util.matrix_spec("mf204", "mf204*((%s/((mo963*mo964)+0.001)).min.1)" % capacity_matrix)
        spec["constraint"]["by_value"] = {"od_values": "mf995", "interval_min": 1, "interval_max": 999, "condition": "INCLUDE"}
        specs.append(spec)
        util.compute_matrix(specs, scenario=scenario)

    @_m.logbook_trace("Calculating park and ride utility functions")
    def PRutility(self, asg_type, scenario):
        util = _m.Modeller().tool("translink.emme.util")
        init_matrix = _m.Modeller().tool("inro.emme.data.matrix.init_matrix")
        spec = {
            "expression": "default_expression",
            "result": "defaul_result",
            "constraint": {
                "by_value": {
                    "od_values": "mf201",
                    "interval_min": 1,
                    "interval_max": 1,
                    "condition": "EXCLUDE"
                },
                "by_zone": None
            },
            "aggregation": {
                "origins": None,
                "destinations": None
            },
            "type": "MATRIX_CALCULATION"
        }

        init_matrix(matrix="mf206", init_value=0.0, scenario=scenario)
        init_matrix(matrix="mf207", init_value=0.0, scenario=scenario)

        #Calculate park-and-ride utilities
        #Define filter matrix and capacity matrix
        if asg_type == 1:
            filter_matrix = "mf201"
        elif asg_type == 2:
            filter_matrix = "mf200"
        elif asg_type == 3:
            filter_matrix = "mf201"
        elif asg_type == 4:
            filter_matrix = "mf200"

        #Compute leg 1 utilities (auto leg)
        spec["constraint"]["by_value"]["od_values"] = filter_matrix
        spec["constraint"]["by_value"]["interval_min"] = 1
        spec["constraint"]["by_value"]["interval_max"] = 1
        spec["constraint"]["by_value"]["condition"] = "INCLUDE"

        expression = "exp(-" + mode3 + "*mf202)"
        spec["expression"] = expression
        spec["result"] = "mf206"
        util.compute_matrix(spec, scenario=scenario)

        spec["constraint"]["by_value"]["condition"] = "EXCLUDE"
        expression = "0"
        spec["expression"] = expression
        util.compute_matrix(spec, scenario=scenario)

        #Compute leg 2 utilities (transit leg)
        spec["constraint"]["by_value"]["od_values"] = filter_matrix
        spec["constraint"]["by_value"]["interval_min"] = 2
        spec["constraint"]["by_value"]["interval_max"] = 2
        spec["constraint"]["by_value"]["condition"] = "INCLUDE"

        expression = "exp(-" + mode4 + "*mf203)"
        spec["expression"] = expression
        spec["result"] = "mf207"
        util.compute_matrix(spec, scenario=scenario)

        spec["constraint"]["by_value"]["condition"] = "EXCLUDE"
        expression = "0"
        spec["expression"] = expression
        util.compute_matrix(spec, scenario=scenario)

    @_m.logbook_trace("Run park and ride model")
    def PRmodel(self, asg_type, scenario):
        park_ride = _m.Modeller().tool(
            "inro.emme.choice_model.two_leg_trip_chain")
        if asg_type in (1, 3):
            max_iterations = 20
        else:
            # fewer iterations for bus as there is (almost)
            # no parking lot choice
            max_iterations = 5
        park_ride(
            tour_demand="mf204",
            leg1_pk_utility_spec={"matrix": "mf206", "type": "ZONAL_CHOICE_UTILITY"},
            stop_k_utility_spec={"matrix": "md73", "type": "ZONAL_CHOICE_UTILITY"},
            leg2_kq_utility_spec={"matrix": "mf207", "type": "ZONAL_CHOICE_UTILITY"},
            leg1_demand="mf208",
            stop_usage="md64",
            leg2_demand="mf209",
            stop_capacity="md65",
            constraint={
                "by_zone": {
                    "origins": "gm1-gm24",
                    "intermediates": "101-127",
                    "destinations": "gm1-gm24"
                }
            },
            max_iterations=max_iterations,
            scenario=scenario)

    @_m.logbook_trace("Matrix Batchin")
    def Matrix_Batchins(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        util.initmat(eb, "mf202", "PRaimp", "Auto impedance (input to PR)", 0)
        util.initmat(eb, "mf203", "PRtimp", "Transit impedance (input to PR)", 0)
        util.initmat(eb, "mf205", "PRimp", "Park and ride impedance", 0)
        util.initmat(eb, "mf206", "PRutau", "PR Auto utility", 0)
        util.initmat(eb, "mf207", "PRuttr", "PR Transit utility", 0)
        util.initmat(eb, "mf208", "PRbusd", "PR Bus output demand", 0)
        util.initmat(eb, "mf209", "PRraid", "PR Rail output demand", 0)

        util.initmat(eb, "md63", "PRtemp", "Lot Attractivity (temp)", 1)
        util.initmat(eb, "md64", "PRuse", "Park-ride usage (temp)", 0)
        util.initmat(eb, "md65", "PRremc", "Park-ride remaining capacity", 0)
        util.initmat(eb, "md66", "PRimpw", "Park-ride lot impedance (work)", 0)
        util.initmat(eb, "md67", "PRimpn", "Park-ride lot impedance (nwork)", 0)
        util.initmat(eb, "md68", "PRwrus", "Park-ride usage (work rail)", 0)
        util.initmat(eb, "md69", "PRwbse", "Park-ride usage (work bus)", 0)
        util.initmat(eb, "md70", "PRnrse", "Park-ride usage (nonwork rail)", 0)
        util.initmat(eb, "md71", "PRnbse", "Park-ride usage (nonwork bus)", 0)

        util.initmat(eb, "mf196", "PRrwtd", "Park-ride rail-work auto demand", 0)
        util.initmat(eb, "mf197", "PRbwtd", "Park-ride bus-work auto demand", 0)
        util.initmat(eb, "mf198", "PRrntd", "Park-ride rail-nonwork auto demand", 0)
        util.initmat(eb, "mf199", "PRbntd", "Park-ride bus-nonwork auto demand", 0)
        util.initmat(eb, "mf192", "PRrail", "Park-ride rail demand input", 0)
        util.initmat(eb, "mf193", "PRbus", "Park-ride bus demand input", 0)
        util.initmat(eb, "mf194", "PRRail", "Park-ride rail demand output", 0)
        util.initmat(eb, "mf195", "PRBus", "Park-ride bus demand output", 0)
        util.initmat(eb, "mf986", "NwRail", "T5 ultimate rail demand", 0)
        util.initmat(eb, "mf987", "NewBus", "T5 ultimate bus demand", 0)
