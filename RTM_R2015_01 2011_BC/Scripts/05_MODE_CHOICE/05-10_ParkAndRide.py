##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
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
        matrix_txn = _m.Modeller().tool(
            "inro.emme.data.matrix.matrix_transaction")
        compute_matrix = _m.Modeller().tool(
            "inro.emme.matrix_calculation.matrix_calculator")

        with _m.logbook_trace("Initialization"):
            bank_dir = os.path.dirname(scenario.emmebank.path)
            input_dir = os.path.join(bank_dir, "05_MODE_CHOICE", "Inputs", "ParkAndRide", "PR-setup.311")
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
            report = compute_matrix(spec, scenario=scenario)

            #Allow for additional lot overcapacity congestion impedance (set to zero for now)
            #Note that lot charges are included in auto impedance component
            spec["expression"] = "0"
            spec["result"] = "md63"
            report = compute_matrix(spec, scenario=scenario)

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
            report = compute_matrix(spec, scenario=scenario)

            spec["expression"] = "(md60-(md64*md72)).max.1"
            spec["result"] = "md65"
            report = compute_matrix(spec, scenario=scenario)
            # Copy pr model output for auto and transit legs
            spec["expression"] = "mf209*(q.gt.999)"
            spec["result"] = "mf194"
            report = compute_matrix(spec, scenario=scenario)
            spec["expression"] = "mf208"
            spec["result"] = "mf196"
            report = compute_matrix(spec, scenario=scenario)
            spec["expression"] = "mf204"
            spec["result"] = "mf192"
            report = compute_matrix(spec, scenario=scenario)

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
            report = compute_matrix(spec, scenario=scenario)

            #Define number of non-work spaces
            spec["expression"] = "md61"
            spec["result"] = "md65"
            report = compute_matrix(spec, scenario=scenario)
            #Copy pr model output for auto and transit legs
            spec["expression"] = "mf209*(q.gt.999)"
            spec["result"] = "mf195"
            report = compute_matrix(spec, scenario=scenario)
            spec["expression"] = "mf208"
            spec["result"] = "mf197"
            report = compute_matrix(spec, scenario=scenario)
            spec["expression"] = "mf204"
            spec["result"] = "mf193"
            report = compute_matrix(spec, scenario=scenario)

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
            report = compute_matrix(spec, scenario=scenario)
            spec["expression"] = "(md61-(md64*md72)).max.1"
            spec["result"] = "md65"
            report = compute_matrix(spec, scenario=scenario)
            #Copy pr model output for auto and transit legs
            spec["expression"] = "mf194+(mf209*(q.gt.999))"
            spec["result"] = "mf194"
            report = compute_matrix(spec, scenario=scenario)
            spec["expression"] = "mf208"
            spec["result"] = "mf198"
            report = compute_matrix(spec, scenario=scenario)
            spec["expression"] = "mf204+mf192"
            spec["result"] = "mf192"
            report = compute_matrix(spec, scenario=scenario)

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
            report = compute_matrix(spec, scenario=scenario)
            #Copy pr model output for auto and transit legs
            spec["expression"] = "mf195+(mf209*(q.gt.999))"
            spec["result"] = "mf195"
            report = compute_matrix(spec, scenario=scenario)
            spec["expression"] = "mf208"
            spec["result"] = "mf199"
            report = compute_matrix(spec, scenario=scenario)
            spec["expression"] = "mf204+mf193"
            spec["result"] = "mf193"
            report = compute_matrix(spec, scenario=scenario)

        #at the end, the demand components should be used to modify original matrices
        #or to create new rail bus and auto matrices
        with _m.logbook_trace("Final rail and bus demand"):
            spec["expression"] = "mf854"
            spec["result"] = "mf986"
            report = compute_matrix(spec, scenario=scenario)
            spec["expression"] = "mf853"
            spec["result"] = "mf987"
            report = compute_matrix(spec, scenario=scenario)

            spec["expression"] = "(mf854-mf192+mf194).max.0"
            spec["result"] = "mf854"
            report = compute_matrix(spec, scenario=scenario)
            spec["expression"] = "(mf853-mf193+mf195).max.0"
            spec["result"] = "mf853"
            report = compute_matrix(spec, scenario=scenario)

        # Add the leg one park and ride demand to the auto demand
        # adding work demand to SOV, med income (mf844), and non-work to med-high income (mf847)
        with _m.logbook_trace("Final auto demand"):
            spec["expression"] = "mf844+mf196+mf197"
            spec["result"] = "mf844"
            report = compute_matrix(spec, scenario=scenario)
            spec["expression"] = "mf847+mf198+mf199"
            spec["result"] = "mf847"
            report = compute_matrix(spec, scenario=scenario)

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
        spec["constraint"]["by_zone"]["destinations"] = "gr1,gr4"
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
        compute_matrix = _m.Modeller().tool(
            "inro.emme.matrix_calculation.matrix_calculator")

        spec = {
            "expression": None,
            "result": None,
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

        #Calculate auto impedance
        if asg_type < 3:
            variables = {"VOT": "ms37",
                         "parking_cost": "md27",
                         "lot_charge": "ms37*md62"}
        elif asg_type >= 3:
            variables = {"VOT": "ms38",
                         "parking_cost": "md28",
                         "lot_charge": "ms38*md62"}

        spec["expression"] = ("(mf101+ms19*mf102* %(VOT)s +(ms18+ms17)*mf100* %(VOT)s )"
                              "+ %(parking_cost)s * %(VOT)s "
                              "+ %(lot_charge)s" % variables)
        spec["result"] = "mf202"
        report = compute_matrix(spec, scenario=scenario)

    @_m.logbook_trace("Calculating transit impedance")
    def TransitImpedance(self, asg_type, scenario):
        compute_matrix = _m.Modeller().tool(
            "inro.emme.matrix_calculation.matrix_calculator")

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

        #Calculate transit impedance
        if asg_type < 3:
            value_time = "ms37"
        elif asg_type >= 3:
            value_time = "ms38*0.5"
        expression = "(mf164+(mf163*2))+mf160*" + value_time
        spec["expression"] = expression
        spec["result"] = "mf203"
        report = compute_matrix(spec, scenario=scenario)

    @_m.logbook_trace("Calculating park and ride demand by splitting transit into p/r")
    def PRdemand(self, asg_type, scenario):
        compute_matrix = _m.Modeller().tool(
            "inro.emme.matrix_calculation.matrix_calculator")
        triple_index_op = _m.Modeller().tool(
            "inro.emme.matrix_calculation.matrix_triple_index_operation")
        create_matrix = _m.Modeller().tool(
            "inro.emme.data.matrix.create_matrix")
        init_matrix = _m.Modeller().tool(
            "inro.emme.data.matrix.init_matrix")
        aggr_matrix = _m.Modeller().tool(
            "inro.emme.matrix_calculation.matrix_aggregation")

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
        if scenario.emmebank.matrix("mf995"):
            init_matrix(matrix="mf995", init_value=0.0, scenario=scenario)
        else:
            create_matrix("mf995", "cPNRdm", "constraint on PNR demand calcs",
                          0.0, scenario=scenario)
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

        # Calculate the Park-and-ride demand, given the constraint matrix
        init_matrix(matrix="mf204", init_value=0.0, scenario=scenario)
        init_matrix(matrix="mo963", init_value=0.0, scenario=scenario)
        spec["expression"] = "(%s)/(1+exp(%s*(mf205-mf203+mf%s)))" % (base_demand, mode1, mode2)
        spec["result"] = "mf204"
        report = compute_matrix(spec, scenario=scenario)

        #aggregate mf204 to the mo level
        aggr_matrix("mf204", "mo963", agg_op="+", scenario=scenario)

        #multiply aggregated numbers by the number of zones in each partition
        #reduce mf204 by the ratio of origin demand to catchment area capacity
        spec["expression"] = "mf204*((%s/((mo963*mo964)+0.001)).min.1)" % capacity_matrix
        spec["result"] = "mf204"
        report = compute_matrix(spec, scenario=scenario)

    @_m.logbook_trace("Calculating park and ride utility functions")
    def PRutility(self, asg_type, scenario):
        compute_matrix = _m.Modeller().tool(
            "inro.emme.matrix_calculation.matrix_calculator")
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
        report = compute_matrix(spec, scenario=scenario)

        spec["constraint"]["by_value"]["condition"] = "EXCLUDE"
        expression = "0"
        spec["expression"] = expression
        report = compute_matrix(spec, scenario=scenario)

        #Compute leg 2 utilities (transit leg)
        spec["constraint"]["by_value"]["od_values"] = filter_matrix
        spec["constraint"]["by_value"]["interval_min"] = 2
        spec["constraint"]["by_value"]["interval_max"] = 2
        spec["constraint"]["by_value"]["condition"] = "INCLUDE"

        expression = "exp(-" + mode4 + "*mf203)"
        spec["expression"] = expression
        spec["result"] = "mf207"
        report = compute_matrix(spec, scenario=scenario)

        spec["constraint"]["by_value"]["condition"] = "EXCLUDE"
        expression = "0"
        spec["expression"] = expression
        report = compute_matrix(spec, scenario=scenario)

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
                    "origins": "1000-9999",
                    "intermediates": "101-127",
                    "destinations": "1000-9999"
                }
            },
            max_iterations=max_iterations,
            scenario=scenario)
