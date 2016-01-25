##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step5.utilities
##--Purpose: Contains several common methods to the
##           various mode-choice by purpose sub-models
##---------------------------------------------------------------------
import inro.modeller as _modeller
import os
import contextlib as _context

compute_matrix = _modeller.Modeller().tool(
    "inro.emme.matrix_calculation.matrix_calculator")
process_matrix_trans = _modeller.Modeller().tool(
    "inro.emme.data.matrix.matrix_transaction")
export_matrices = _modeller.Modeller().tool(
    "inro.emme.data.matrix.export_matrices")


class ModeChoiceUtilities(_modeller.Tool()):
    tool_run_msg = ""

    def page(self):
        pb = _modeller.ToolPageBuilder(self, runnable=False)
        pb.title = "Mode Choice Model - Utilities"
        pb.description = ("Not to be used directly, module containing "
                          "methods to calculate mode choice model. (etc).")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()


def build_spec(expression=None, result=None, by_value=None, origins=None, destinations=None):
    spec = {
        "expression": expression,
        "result": str(result),
        "constraint": {
            "by_value": by_value,
            "by_zone": {"origins": origins, "destinations": destinations}
        },
        "aggregation": {"origins": None, "destinations": None},
        "type": "MATRIX_CALCULATION"
    }
    return spec


@_modeller.logbook_trace("Calculate demand")
def calculate_demand(scenario, demand_start, probability_start, result_start, num_segments=9):
    spec_list = []
    for i in range(num_segments):
        for k in range(7):
            expression1 = "mf" + str(demand_start + i) + "*" + "mf" + str(probability_start + i + k * 9)
            result = "mf" + str(result_start + i + k * 9)
            spec_list.append(build_spec(expression1, result))
    compute_matrix(spec_list, scenario)


def process_transaction_list(scenario, base_folder, file_names):
    for name in file_names:
        process_matrix_trans(transaction_file=os.path.join(base_folder, name + '.311'),
                             scenario=scenario)


def export_matrices_report(data_folder, purpose, full_report_matrices):
    file_name = os.path.join(data_folder, "reporting", purpose + "_fullRep.311")
    matrix_list = []
    for nCnt in full_report_matrices:
        matrix_list.append("mf" + str(nCnt))
    export_matrices(
        export_file=file_name,
        matrices=matrix_list,
        partition_aggregation={"origins": "gy", "destinations": "gy", "operator": "SUM"},
        skip_default_values=True,
        append_to_file=False)

    file_name = os.path.join(data_folder, "reporting", purpose + "_PkHrRep.311")
    matrix_list = []
    for nCnt in range(0, 9):
        matrix_list.append("mf" + str(777 + (nCnt * 7)))
    for nCnt in range(0, 9):
        matrix_list.append("mf" + str(778 + (nCnt * 7)))
    for nCnt in range(0, 9):
        matrix_list.append("mf" + str(779 + (nCnt * 7)))
    for nCnt in range(0, 39):
        matrix_list.append("mf" + str(843 + nCnt))
    export_matrices(
        export_file=file_name,
        matrices=matrix_list,
        partition_aggregation={"origins": "gy", "destinations": "gy", "operator": "SUM"},
        skip_default_values=True,
        append_to_file=False)



@_modeller.logbook_trace("Calculate probabilities")
def calculate_probabilities(scenario, nests, theta, utility_start_id=374, result_start_id=441, num_segments=9):
    ## Specify the mode choice structure and the corresponding matrix ids for inputs
    ## and outputs
    ## nest is a list of lists, indicating the grouping of the utility calculations
    ## E.g. calculate_probabilities(scenario, nests=[[0, 1, 2], [3, 4], [5, 6]], theta=0.45)
    ## Probabilities are usually saved in matrices mf441-mf503
    ## and calculated from utilities stored in matrices mf374-mf436
    ## but this is not required

    emmebank = scenario.emmebank
    tiny = 0.000001
    # determine the number of temporary matrices required
    num_temps = 2 * len(nests) + 1

    with temp_matrices(emmebank, "FULL", num_temps) as temp_mats:
        spec_list = []
        for segment in range(num_segments):
            scratch_mat_ids = temp_mats[:]
            scratch_mat_ids.reverse()
            nest_expression = []
            nest_utility = []

            for i, nest_items in enumerate(nests, start=1):
                exponent_items = []
                for item in nest_items:
                    exponent_items.append("exp(mf%s)" % (utility_start_id + segment + item * 9))

                expression = "(" + " + ".join(exponent_items) + " + %s)" % tiny

                denom_result = scratch_mat_ids.pop()
                denom_result.name = "Ndem%d" % i
                denom_result.description = "Denominator for nest %d (temp)" % i
                spec_list.append(build_spec(expression, denom_result))

                util_result = scratch_mat_ids.pop()
                util_result.name = "Nutil%d" % i
                util_result.description = "Utility for nest %d (temp)" % i
                spec_list.append(build_spec("(%s) ^ %s" % (denom_result.id, theta), util_result))
                nest_utility.append(util_result.id)

                nest_expression.append([nest_items, exponent_items, util_result.id, denom_result.id])

            denominator_expr = " + ".join(nest_utility)
            full_denominator = scratch_mat_ids.pop()
            full_denominator.name = "denom"
            full_denominator.description = "Denominator for total nest"
            spec_list.append(build_spec(denominator_expr, full_denominator))

            for nest_items, exponent_items, utility, nest_denominator in nest_expression:
                for item, item_exp in zip(nest_items, exponent_items):
                    expression = "((%s) / (%s)) * ((%s) / (%s))" % (
                        utility, full_denominator, item_exp, nest_denominator)
                    result = "mf%s" % (result_start_id + segment + item * 9)
                    spec_list.append(build_spec(expression, result))

        compute_matrix(spec_list, scenario)


@_context.contextmanager
def temp_matrices(emmebank, matrix_type, total=1, default_value=0.0):
    matrices = []
    try:
        while len(matrices) != total:
            ident = emmebank.available_matrix_identifier(matrix_type)
            matrices.append(emmebank.create_matrix(ident, default_value))
        yield matrices
    finally:
        for matrix in matrices:
            emmebank.delete_matrix(matrix)
