##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step5.utilities
##--Purpose: Contains several common methods to the
##           various mode-choice by purpose sub-models
##---------------------------------------------------------------------
import inro.modeller as _m
import os
import contextlib as _context

compute_matrix = _m.Modeller().tool(
    "inro.emme.matrix_calculation.matrix_calculator")
process_matrix_trans = _m.Modeller().tool(
    "inro.emme.data.matrix.matrix_transaction")
export_matrices = _m.Modeller().tool(
    "inro.emme.data.matrix.export_matrices")


class ModeChoiceUtilities(_m.Tool()):
    tool_run_msg = ""

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Mode Choice Model - Utilities"
        pb.description = "Not to be used directly, module containing methods to calculate mode choice model. (etc)."
        pb.branding_text = "TransLink"
        pb.runnable = False

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


@_m.logbook_trace("Calculate demand")
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



@_m.logbook_trace("Calculate probabilities")
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

# Initialize mf773 - mf842 before slicing demand
def dmMatInitParts(eb):
    util = _m.Modeller().tool("translink.emme.util")

    util.initmat(eb, "mf773", "f2111", "TimeSlicedDemand OtSvLT1", 0)
    util.initmat(eb, "mf774", "f2112", "TimeSlicedDemand OtSvLT2", 0)
    util.initmat(eb, "mf775", "f2113", "TimeSlicedDemand OtSvLT3", 0)
    util.initmat(eb, "mf776", "f2114", "TimeSlicedDemand OtSvLT4", 0)
    util.initmat(eb, "mf777", "f2115", "TimeSlicedDemand OtSvLT5", 0)
    util.initmat(eb, "mf778", "f2116", "TimeSlicedDemand OtSvLT6", 0)
    util.initmat(eb, "mf779", "f2117", "TimeSlicedDemand OtSvLT7", 0)
    util.initmat(eb, "mf780", "f2121", "TimeSlicedDemand OtHvLT1", 0)
    util.initmat(eb, "mf781", "f2122", "TimeSlicedDemand OtHvLT2", 0)
    util.initmat(eb, "mf782", "f2123", "TimeSlicedDemand OtHvLT3", 0)
    util.initmat(eb, "mf783", "f2124", "TimeSlicedDemand OtHvLT4", 0)
    util.initmat(eb, "mf784", "f2125", "TimeSlicedDemand OtHvLT5", 0)
    util.initmat(eb, "mf785", "f2126", "TimeSlicedDemand OtHvLT6", 0)
    util.initmat(eb, "mf786", "f2127", "TimeSlicedDemand OtHvLT7", 0)
    util.initmat(eb, "mf787", "f2131", "TimeSlicedDemand OtH3LT1", 0)
    util.initmat(eb, "mf788", "f2132", "TimeSlicedDemand OtH3LT2", 0)
    util.initmat(eb, "mf789", "f2133", "TimeSlicedDemand OtH3LT3", 0)
    util.initmat(eb, "mf790", "f2134", "TimeSlicedDemand OtH3LT4", 0)
    util.initmat(eb, "mf791", "f2135", "TimeSlicedDemand OtH3LT5", 0)
    util.initmat(eb, "mf792", "f2136", "TimeSlicedDemand OtH3LT6", 0)
    util.initmat(eb, "mf793", "f2137", "TimeSlicedDemand OtH3LT7", 0)
    util.initmat(eb, "mf794", "f2411", "TimeSlicedDemand OtSvMHT1", 0)
    util.initmat(eb, "mf795", "f2412", "TimeSlicedDemand OtSvMHT2", 0)
    util.initmat(eb, "mf796", "f2413", "TimeSlicedDemand OtSvMHT3", 0)
    util.initmat(eb, "mf797", "f2414", "TimeSlicedDemand OtSvMHT4", 0)
    util.initmat(eb, "mf798", "f2415", "TimeSlicedDemand OtSvMHT5", 0)
    util.initmat(eb, "mf799", "f2416", "TimeSlicedDemand OtSvMHT6", 0)
    util.initmat(eb, "mf800", "f2417", "TimeSlicedDemand OtSvMHT7", 0)
    util.initmat(eb, "mf801", "f2421", "TimeSlicedDemand OtHvMHT1", 0)
    util.initmat(eb, "mf802", "f2422", "TimeSlicedDemand OtHvMHT2", 0)
    util.initmat(eb, "mf803", "f2423", "TimeSlicedDemand OtHvMHT3", 0)
    util.initmat(eb, "mf804", "f2424", "TimeSlicedDemand OtHvMHT4", 0)
    util.initmat(eb, "mf805", "f2425", "TimeSlicedDemand OtHvMHT5", 0)
    util.initmat(eb, "mf806", "f2426", "TimeSlicedDemand OtHvMHT6", 0)
    util.initmat(eb, "mf807", "f2427", "TimeSlicedDemand OtHvMHT7", 0)
    util.initmat(eb, "mf808", "f2431", "TimeSlicedDemand OtH3MHT1", 0)
    util.initmat(eb, "mf809", "f2432", "TimeSlicedDemand OtH3MHT2", 0)
    util.initmat(eb, "mf810", "f2433", "TimeSlicedDemand OtH3MHT3", 0)
    util.initmat(eb, "mf811", "f2434", "TimeSlicedDemand OtH3MHT4", 0)
    util.initmat(eb, "mf812", "f2435", "TimeSlicedDemand OtH3MHT5", 0)
    util.initmat(eb, "mf813", "f2436", "TimeSlicedDemand OtH3MHT6", 0)
    util.initmat(eb, "mf814", "f2437", "TimeSlicedDemand OtH3MHT7", 0)
    util.initmat(eb, "mf815", "f3541", "TimeSlicedDemand APrBsAInT1", 0)
    util.initmat(eb, "mf816", "f3542", "TimeSlicedDemand APrBsAInT2", 0)
    util.initmat(eb, "mf817", "f3543", "TimeSlicedDemand APrBsAInT3", 0)
    util.initmat(eb, "mf818", "f3544", "TimeSlicedDemand APrBsAInT4", 0)
    util.initmat(eb, "mf819", "f3545", "TimeSlicedDemand APrBsAInT5", 0)
    util.initmat(eb, "mf820", "f3546", "TimeSlicedDemand APrBsAInT6", 0)
    util.initmat(eb, "mf821", "f3547", "TimeSlicedDemand APrBsAInT7", 0)
    util.initmat(eb, "mf822", "f3551", "TimeSlicedDemand APrRlAInT1", 0)
    util.initmat(eb, "mf823", "f3552", "TimeSlicedDemand APrRlAInT2", 0)
    util.initmat(eb, "mf824", "f3553", "TimeSlicedDemand APrRlAInT3", 0)
    util.initmat(eb, "mf825", "f3554", "TimeSlicedDemand APrRlAInT4", 0)
    util.initmat(eb, "mf826", "f3555", "TimeSlicedDemand APrRlAInT5", 0)
    util.initmat(eb, "mf827", "f3556", "TimeSlicedDemand APrRlAInT6", 0)
    util.initmat(eb, "mf828", "f3557", "TimeSlicedDemand APrRlAInT7", 0)
    util.initmat(eb, "mf829", "f3571", "TimeSlicedDemand APrAcAInT1", 0)
    util.initmat(eb, "mf830", "f3572", "TimeSlicedDemand APrAcAInT2", 0)
    util.initmat(eb, "mf831", "f3573", "TimeSlicedDemand APrAcAInT3", 0)
    util.initmat(eb, "mf832", "f3574", "TimeSlicedDemand APrAcAInT4", 0)
    util.initmat(eb, "mf833", "f3575", "TimeSlicedDemand APrAcAInT5", 0)
    util.initmat(eb, "mf834", "f3576", "TimeSlicedDemand APrAcAInT6", 0)
    util.initmat(eb, "mf835", "f3577", "TimeSlicedDemand APrAcAInT7", 0)
    util.initmat(eb, "mf836", "f3581", "TimeSlicedDemand APrSBAInT1", 0)
    util.initmat(eb, "mf837", "f3582", "TimeSlicedDemand APrSBAInT2", 0)
    util.initmat(eb, "mf838", "f3583", "TimeSlicedDemand APrSBAInT3", 0)
    util.initmat(eb, "mf839", "f3584", "TimeSlicedDemand APrSBAInT4", 0)
    util.initmat(eb, "mf840", "f3585", "TimeSlicedDemand APrSBAInT5", 0)
    util.initmat(eb, "mf841", "f3586", "TimeSlicedDemand APrSBAInT6", 0)
    util.initmat(eb, "mf842", "f3587", "TimeSlicedDemand APrSBAInT7", 0)
    