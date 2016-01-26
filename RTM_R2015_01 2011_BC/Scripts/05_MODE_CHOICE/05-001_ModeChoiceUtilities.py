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

# Initialize mf374 - mf436 Utilities
# Initialize mf441 - mf503 Probabilities
# Initialize mf640 - mf702 Results
def dmMatInit_NonWork(eb):
    util = _m.Modeller().tool("translink.emme.util")

    util.initmat(eb, "mf374", "m110", "Util SvLA0", 0)
    util.initmat(eb, "mf375", "m111", "Util SvLA1", 0)
    util.initmat(eb, "mf376", "m112", "Util SvLA2+", 0)
    util.initmat(eb, "mf377", "m120", "Util SvMA0", 0)
    util.initmat(eb, "mf378", "m121", "Util SvMA1", 0)
    util.initmat(eb, "mf379", "m122", "Util SvMA2+", 0)
    util.initmat(eb, "mf380", "m130", "Util SvHA0", 0)
    util.initmat(eb, "mf381", "m131", "Util SvHA1", 0)
    util.initmat(eb, "mf382", "m132", "Util SvHA2+", 0)
    util.initmat(eb, "mf383", "m210", "Util HvLA0", 0)
    util.initmat(eb, "mf384", "m211", "Util HvLA1", 0)
    util.initmat(eb, "mf385", "m212", "Util HvLA2+", 0)
    util.initmat(eb, "mf386", "m220", "Util HvMA0", 0)
    util.initmat(eb, "mf387", "m221", "Util HvMA1", 0)
    util.initmat(eb, "mf388", "m222", "Util HvMA2+", 0)
    util.initmat(eb, "mf389", "m230", "Util HvHA0", 0)
    util.initmat(eb, "mf390", "m231", "Util HvHA1", 0)
    util.initmat(eb, "mf391", "m232", "Util HvHA2+", 0)
    util.initmat(eb, "mf392", "m310", "Util H3SBLA0", 0)
    util.initmat(eb, "mf393", "m311", "Util H3SBLA1", 0)
    util.initmat(eb, "mf394", "m312", "Util H3SBLA2+", 0)
    util.initmat(eb, "mf395", "m320", "Util H3SBMA0", 0)
    util.initmat(eb, "mf396", "m321", "Util H3SBMA1", 0)
    util.initmat(eb, "mf397", "m322", "Util H3SBMA2+", 0)
    util.initmat(eb, "mf398", "m330", "Util H3SBHA0", 0)
    util.initmat(eb, "mf399", "m331", "Util H3SBHA1", 0)
    util.initmat(eb, "mf400", "m332", "Util H3SBHA2+", 0)
    util.initmat(eb, "mf401", "m410", "Util BsLA0", 0)
    util.initmat(eb, "mf402", "m411", "Util BsLA1", 0)
    util.initmat(eb, "mf403", "m412", "Util BsLA2+", 0)
    util.initmat(eb, "mf404", "m420", "Util BsMA0", 0)
    util.initmat(eb, "mf405", "m421", "Util BsMA1", 0)
    util.initmat(eb, "mf406", "m422", "Util BsMA2+", 0)
    util.initmat(eb, "mf407", "m430", "Util BsHA0", 0)
    util.initmat(eb, "mf408", "m431", "Util BsHA1", 0)
    util.initmat(eb, "mf409", "m432", "Util BsHA2+", 0)
    util.initmat(eb, "mf410", "m510", "Util RlLA0", 0)
    util.initmat(eb, "mf411", "m511", "Util RlLA1", 0)
    util.initmat(eb, "mf412", "m512", "Util RlLA2+", 0)
    util.initmat(eb, "mf413", "m520", "Util RlMA0", 0)
    util.initmat(eb, "mf414", "m521", "Util RlMA1", 0)
    util.initmat(eb, "mf415", "m522", "Util RlMA2+", 0)
    util.initmat(eb, "mf416", "m530", "Util RlHA0", 0)
    util.initmat(eb, "mf417", "m531", "Util RlHA1", 0)
    util.initmat(eb, "mf418", "m532", "Util RlHA2+", 0)
    util.initmat(eb, "mf419", "m610", "Util WaLA0", 0)
    util.initmat(eb, "mf420", "m611", "Util WaLA1", 0)
    util.initmat(eb, "mf421", "m612", "Util WaLA2+", 0)
    util.initmat(eb, "mf422", "m620", "Util WaMA0", 0)
    util.initmat(eb, "mf423", "m621", "Util WaMA1", 0)
    util.initmat(eb, "mf424", "m622", "Util WaMA2+", 0)
    util.initmat(eb, "mf425", "m630", "Util WaHA0", 0)
    util.initmat(eb, "mf426", "m631", "Util WaHA1", 0)
    util.initmat(eb, "mf427", "m632", "Util WaHA2+", 0)
    util.initmat(eb, "mf428", "m710", "Util BkLA0", 0)
    util.initmat(eb, "mf429", "m711", "Util BkLA1", 0)
    util.initmat(eb, "mf430", "m712", "Util BkLA2+", 0)
    util.initmat(eb, "mf431", "m720", "Util BkMA0", 0)
    util.initmat(eb, "mf432", "m721", "Util BkMA1", 0)
    util.initmat(eb, "mf433", "m722", "Util BkMA2+", 0)
    util.initmat(eb, "mf434", "m730", "Util BkHA0", 0)
    util.initmat(eb, "mf435", "m731", "Util BkHA1", 0)
    util.initmat(eb, "mf436", "m732", "Util BkHA2+", 0)

    util.initmat(eb, "mf441", "c110", "Prob SvLA0", 0)
    util.initmat(eb, "mf442", "c111", "Prob SvLA1", 0)
    util.initmat(eb, "mf443", "c112", "Prob SvLA2+", 0)
    util.initmat(eb, "mf444", "c120", "Prob SvMA0", 0)
    util.initmat(eb, "mf445", "c121", "Prob SvMA1", 0)
    util.initmat(eb, "mf446", "c122", "Prob SvMA2+", 0)
    util.initmat(eb, "mf447", "c130", "Prob SvHA0", 0)
    util.initmat(eb, "mf448", "c131", "Prob SvHA1", 0)
    util.initmat(eb, "mf449", "c132", "Prob SvHA2+", 0)
    util.initmat(eb, "mf450", "c210", "Prob HvLA0", 0)
    util.initmat(eb, "mf451", "c211", "Prob HvLA1", 0)
    util.initmat(eb, "mf452", "c212", "Prob HvLA2+", 0)
    util.initmat(eb, "mf453", "c220", "Prob HvMA0", 0)
    util.initmat(eb, "mf454", "c221", "Prob HvMA1", 0)
    util.initmat(eb, "mf455", "c222", "Prob HvMA2+", 0)
    util.initmat(eb, "mf456", "c230", "Prob HvHA0", 0)
    util.initmat(eb, "mf457", "c231", "Prob HvHA1", 0)
    util.initmat(eb, "mf458", "c232", "Prob HvHA2+", 0)
    util.initmat(eb, "mf459", "c310", "Prob H3SBLA0", 0)
    util.initmat(eb, "mf460", "c311", "Prob H3SBLA1", 0)
    util.initmat(eb, "mf461", "c312", "Prob H3SBLA2+", 0)
    util.initmat(eb, "mf462", "c320", "Prob H3SBMA0", 0)
    util.initmat(eb, "mf463", "c321", "Prob H3SBMA1", 0)
    util.initmat(eb, "mf464", "c322", "Prob H3SBMA2+", 0)
    util.initmat(eb, "mf465", "c330", "Prob H3SBHA0", 0)
    util.initmat(eb, "mf466", "c331", "Prob H3SBHA1", 0)
    util.initmat(eb, "mf467", "c332", "Prob H3SBHA2+", 0)
    util.initmat(eb, "mf468", "c410", "Prob BsLA0", 0)
    util.initmat(eb, "mf469", "c411", "Prob BsLA1", 0)
    util.initmat(eb, "mf470", "c412", "Prob BsLA2+", 0)
    util.initmat(eb, "mf471", "c420", "Prob BsMA0", 0)
    util.initmat(eb, "mf472", "c421", "Prob BsMA1", 0)
    util.initmat(eb, "mf473", "c422", "Prob BsMA2+", 0)
    util.initmat(eb, "mf474", "c430", "Prob BsHA0", 0)
    util.initmat(eb, "mf475", "c431", "Prob BsHA1", 0)
    util.initmat(eb, "mf476", "c432", "Prob BsHA2+", 0)
    util.initmat(eb, "mf477", "c510", "Prob RlLA0", 0)
    util.initmat(eb, "mf478", "c511", "Prob RlLA1", 0)
    util.initmat(eb, "mf479", "c512", "Prob RlLA2+", 0)
    util.initmat(eb, "mf480", "c520", "Prob RlMA0", 0)
    util.initmat(eb, "mf481", "c521", "Prob RlMA1", 0)
    util.initmat(eb, "mf482", "c522", "Prob RlMA2+", 0)
    util.initmat(eb, "mf483", "c530", "Prob RlHA0", 0)
    util.initmat(eb, "mf484", "c531", "Prob RlHA1", 0)
    util.initmat(eb, "mf485", "c532", "Prob RlHA2+", 0)
    util.initmat(eb, "mf486", "c610", "Prob WaLA0", 0)
    util.initmat(eb, "mf487", "c611", "Prob WaLA1", 0)
    util.initmat(eb, "mf488", "c612", "Prob WaLA2+", 0)
    util.initmat(eb, "mf489", "c620", "Prob WaMA0", 0)
    util.initmat(eb, "mf490", "c621", "Prob WaMA1", 0)
    util.initmat(eb, "mf491", "c622", "Prob WaMA2+", 0)
    util.initmat(eb, "mf492", "c630", "Prob WaHA0", 0)
    util.initmat(eb, "mf493", "c631", "Prob WaHA1", 0)
    util.initmat(eb, "mf494", "c632", "Prob WaHA2+", 0)
    util.initmat(eb, "mf495", "c710", "Prob BkLA0", 0)
    util.initmat(eb, "mf496", "c711", "Prob BkLA1", 0)
    util.initmat(eb, "mf497", "c712", "Prob BkLA2+", 0)
    util.initmat(eb, "mf498", "c720", "Prob BkMA0", 0)
    util.initmat(eb, "mf499", "c721", "Prob BkMA1", 0)
    util.initmat(eb, "mf500", "c722", "Prob BkMA2+", 0)
    util.initmat(eb, "mf501", "c730", "Prob BkHA0", 0)
    util.initmat(eb, "mf502", "c731", "Prob BkHA1", 0)
    util.initmat(eb, "mf503", "c732", "Prob BkHA2+", 0)

    util.initmat(eb, "mf640", "r2110", "Result OtSvLA0", 0)
    util.initmat(eb, "mf641", "r2111", "Result OtSvLA1", 0)
    util.initmat(eb, "mf642", "r2112", "Result OtSvLA2+", 0)
    util.initmat(eb, "mf643", "r2120", "Result OtSvMA0", 0)
    util.initmat(eb, "mf644", "r2121", "Result OtSvMA1", 0)
    util.initmat(eb, "mf645", "r2122", "Result OtSvMA2+", 0)
    util.initmat(eb, "mf646", "r2130", "Result OtSvHA0", 0)
    util.initmat(eb, "mf647", "r2131", "Result OtSvHA1", 0)
    util.initmat(eb, "mf648", "r2132", "Result OtSvHA2+", 0)
    util.initmat(eb, "mf649", "r2210", "Result OtHvLA0", 0)
    util.initmat(eb, "mf650", "r2211", "Result OtHvLA1", 0)
    util.initmat(eb, "mf651", "r2212", "Result OtHvLA2+", 0)
    util.initmat(eb, "mf652", "r2220", "Result OtHvMA0", 0)
    util.initmat(eb, "mf653", "r2221", "Result OtHvMA1", 0)
    util.initmat(eb, "mf654", "r2222", "Result OtHvMA2+", 0)
    util.initmat(eb, "mf655", "r2230", "Result OtHvHA0", 0)
    util.initmat(eb, "mf656", "r2231", "Result OtHvHA1", 0)
    util.initmat(eb, "mf657", "r2232", "Result OtHvHA2+", 0)
    util.initmat(eb, "mf658", "r2310", "Result OtH3SBLA0", 0)
    util.initmat(eb, "mf659", "r2311", "Result OtH3SBLA1", 0)
    util.initmat(eb, "mf660", "r2312", "Result OtH3SBLA2+", 0)
    util.initmat(eb, "mf661", "r2320", "Result OtH3SBMA0", 0)
    util.initmat(eb, "mf662", "r2321", "Result OtH3SBMA1", 0)
    util.initmat(eb, "mf663", "r2322", "Result OtH3SBMA2+", 0)
    util.initmat(eb, "mf664", "r2330", "Result OtH3SBHA0", 0)
    util.initmat(eb, "mf665", "r2331", "Result OtH3SBHA1", 0)
    util.initmat(eb, "mf666", "r2332", "Result OtH3SBHA2+", 0)
    util.initmat(eb, "mf667", "r2410", "Result OtBsLA0", 0)
    util.initmat(eb, "mf668", "r2411", "Result OtBsLA1", 0)
    util.initmat(eb, "mf669", "r2412", "Result OtBsLA2+", 0)
    util.initmat(eb, "mf670", "r2420", "Result OtBsMA0", 0)
    util.initmat(eb, "mf671", "r2421", "Result OtBsMA1", 0)
    util.initmat(eb, "mf672", "r2422", "Result OtBsMA2+", 0)
    util.initmat(eb, "mf673", "r2430", "Result OtBsHA0", 0)
    util.initmat(eb, "mf674", "r2431", "Result OtBsHA1", 0)
    util.initmat(eb, "mf675", "r2432", "Result OtBsHA2+", 0)
    util.initmat(eb, "mf676", "r2510", "Result OtRlLA0", 0)
    util.initmat(eb, "mf677", "r2511", "Result OtRlLA1", 0)
    util.initmat(eb, "mf678", "r2512", "Result OtRlLA2+", 0)
    util.initmat(eb, "mf679", "r2520", "Result OtRlMA0", 0)
    util.initmat(eb, "mf680", "r2521", "Result OtRlMA1", 0)
    util.initmat(eb, "mf681", "r2522", "Result OtRlMA2+", 0)
    util.initmat(eb, "mf682", "r2530", "Result OtRlHA0", 0)
    util.initmat(eb, "mf683", "r2531", "Result OtRlHA1", 0)
    util.initmat(eb, "mf684", "r2532", "Result OtRlHA2+", 0)
    util.initmat(eb, "mf685", "r2610", "Result OtWaLA0", 0)
    util.initmat(eb, "mf686", "r2611", "Result OtWaLA1", 0)
    util.initmat(eb, "mf687", "r2612", "Result OtWaLA2+", 0)
    util.initmat(eb, "mf688", "r2620", "Result OtWaMA0", 0)
    util.initmat(eb, "mf689", "r2621", "Result OtWaMA1", 0)
    util.initmat(eb, "mf690", "r2622", "Result OtWaMA2+", 0)
    util.initmat(eb, "mf691", "r2630", "Result OtWaHA0", 0)
    util.initmat(eb, "mf692", "r2631", "Result OtWaHA1", 0)
    util.initmat(eb, "mf693", "r2632", "Result OtWaHA2+", 0)
    util.initmat(eb, "mf694", "r2710", "Result OtBkLA0", 0)
    util.initmat(eb, "mf695", "r2711", "Result OtBkLA1", 0)
    util.initmat(eb, "mf696", "r2712", "Result OtBkLA2+", 0)
    util.initmat(eb, "mf697", "r2720", "Result OtBkMA0", 0)
    util.initmat(eb, "mf698", "r2721", "Result OtBkMA1", 0)
    util.initmat(eb, "mf699", "r2722", "Result OtBkMA2+", 0)
    util.initmat(eb, "mf700", "r2730", "Result OtBkHA0", 0)
    util.initmat(eb, "mf701", "r2731", "Result OtBkHA1", 0)
    util.initmat(eb, "mf702", "r2732", "Result OtBkHA2+", 0)

# Initialize mf374 - mf436 Utilities
# Initialize mf441 - mf503 Probabilities
# Initialize mf505 - mf567 Results
# Initialize mf568 - mf639 Demand
def dmMatInit_Work(eb):
    util = _m.Modeller().tool("translink.emme.util")

    util.initmat(eb, "mf374", "m110", "Util SvLA0", 0)
    util.initmat(eb, "mf375", "m111", "Util SvLA1", 0)
    util.initmat(eb, "mf376", "m112", "Util SvLA2+", 0)
    util.initmat(eb, "mf377", "m120", "Util SvMA0", 0)
    util.initmat(eb, "mf378", "m121", "Util SvMA1", 0)
    util.initmat(eb, "mf379", "m122", "Util SvMA2+", 0)
    util.initmat(eb, "mf380", "m130", "Util SvHA0", 0)
    util.initmat(eb, "mf381", "m131", "Util SvHA1", 0)
    util.initmat(eb, "mf382", "m132", "Util SvHA2+", 0)
    util.initmat(eb, "mf383", "m210", "Util HvLA0", 0)
    util.initmat(eb, "mf384", "m211", "Util HvLA1", 0)
    util.initmat(eb, "mf385", "m212", "Util HvLA2+", 0)
    util.initmat(eb, "mf386", "m220", "Util HvMA0", 0)
    util.initmat(eb, "mf387", "m221", "Util HvMA1", 0)
    util.initmat(eb, "mf388", "m222", "Util HvMA2+", 0)
    util.initmat(eb, "mf389", "m230", "Util HvHA0", 0)
    util.initmat(eb, "mf390", "m231", "Util HvHA1", 0)
    util.initmat(eb, "mf391", "m232", "Util HvHA2+", 0)
    util.initmat(eb, "mf392", "m310", "Util H3SBLA0", 0)
    util.initmat(eb, "mf393", "m311", "Util H3SBLA1", 0)
    util.initmat(eb, "mf394", "m312", "Util H3SBLA2+", 0)
    util.initmat(eb, "mf395", "m320", "Util H3SBMA0", 0)
    util.initmat(eb, "mf396", "m321", "Util H3SBMA1", 0)
    util.initmat(eb, "mf397", "m322", "Util H3SBMA2+", 0)
    util.initmat(eb, "mf398", "m330", "Util H3SBHA0", 0)
    util.initmat(eb, "mf399", "m331", "Util H3SBHA1", 0)
    util.initmat(eb, "mf400", "m332", "Util H3SBHA2+", 0)
    util.initmat(eb, "mf401", "m410", "Util BsLA0", 0)
    util.initmat(eb, "mf402", "m411", "Util BsLA1", 0)
    util.initmat(eb, "mf403", "m412", "Util BsLA2+", 0)
    util.initmat(eb, "mf404", "m420", "Util BsMA0", 0)
    util.initmat(eb, "mf405", "m421", "Util BsMA1", 0)
    util.initmat(eb, "mf406", "m422", "Util BsMA2+", 0)
    util.initmat(eb, "mf407", "m430", "Util BsHA0", 0)
    util.initmat(eb, "mf408", "m431", "Util BsHA1", 0)
    util.initmat(eb, "mf409", "m432", "Util BsHA2+", 0)
    util.initmat(eb, "mf410", "m510", "Util RlLA0", 0)
    util.initmat(eb, "mf411", "m511", "Util RlLA1", 0)
    util.initmat(eb, "mf412", "m512", "Util RlLA2+", 0)
    util.initmat(eb, "mf413", "m520", "Util RlMA0", 0)
    util.initmat(eb, "mf414", "m521", "Util RlMA1", 0)
    util.initmat(eb, "mf415", "m522", "Util RlMA2+", 0)
    util.initmat(eb, "mf416", "m530", "Util RlHA0", 0)
    util.initmat(eb, "mf417", "m531", "Util RlHA1", 0)
    util.initmat(eb, "mf418", "m532", "Util RlHA2+", 0)
    util.initmat(eb, "mf419", "m610", "Util WaLA0", 0)
    util.initmat(eb, "mf420", "m611", "Util WaLA1", 0)
    util.initmat(eb, "mf421", "m612", "Util WaLA2+", 0)
    util.initmat(eb, "mf422", "m620", "Util WaMA0", 0)
    util.initmat(eb, "mf423", "m621", "Util WaMA1", 0)
    util.initmat(eb, "mf424", "m622", "Util WaMA2+", 0)
    util.initmat(eb, "mf425", "m630", "Util WaHA0", 0)
    util.initmat(eb, "mf426", "m631", "Util WaHA1", 0)
    util.initmat(eb, "mf427", "m632", "Util WaHA2+", 0)
    util.initmat(eb, "mf428", "m710", "Util BkLA0", 0)
    util.initmat(eb, "mf429", "m711", "Util BkLA1", 0)
    util.initmat(eb, "mf430", "m712", "Util BkLA2+", 0)
    util.initmat(eb, "mf431", "m720", "Util BkMA0", 0)
    util.initmat(eb, "mf432", "m721", "Util BkMA1", 0)
    util.initmat(eb, "mf433", "m722", "Util BkMA2+", 0)
    util.initmat(eb, "mf434", "m730", "Util BkHA0", 0)
    util.initmat(eb, "mf435", "m731", "Util BkHA1", 0)
    util.initmat(eb, "mf436", "m732", "Util BkHA2+", 0)

    util.initmat(eb, "mf441", "c110", "Prob SvLA0", 0)
    util.initmat(eb, "mf442", "c111", "Prob SvLA1", 0)
    util.initmat(eb, "mf443", "c112", "Prob SvLA2+", 0)
    util.initmat(eb, "mf444", "c120", "Prob SvMA0", 0)
    util.initmat(eb, "mf445", "c121", "Prob SvMA1", 0)
    util.initmat(eb, "mf446", "c122", "Prob SvMA2+", 0)
    util.initmat(eb, "mf447", "c130", "Prob SvHA0", 0)
    util.initmat(eb, "mf448", "c131", "Prob SvHA1", 0)
    util.initmat(eb, "mf449", "c132", "Prob SvHA2+", 0)
    util.initmat(eb, "mf450", "c210", "Prob HvLA0", 0)
    util.initmat(eb, "mf451", "c211", "Prob HvLA1", 0)
    util.initmat(eb, "mf452", "c212", "Prob HvLA2+", 0)
    util.initmat(eb, "mf453", "c220", "Prob HvMA0", 0)
    util.initmat(eb, "mf454", "c221", "Prob HvMA1", 0)
    util.initmat(eb, "mf455", "c222", "Prob HvMA2+", 0)
    util.initmat(eb, "mf456", "c230", "Prob HvHA0", 0)
    util.initmat(eb, "mf457", "c231", "Prob HvHA1", 0)
    util.initmat(eb, "mf458", "c232", "Prob HvHA2+", 0)
    util.initmat(eb, "mf459", "c310", "Prob H3SBLA0", 0)
    util.initmat(eb, "mf460", "c311", "Prob H3SBLA1", 0)
    util.initmat(eb, "mf461", "c312", "Prob H3SBLA2+", 0)
    util.initmat(eb, "mf462", "c320", "Prob H3SBMA0", 0)
    util.initmat(eb, "mf463", "c321", "Prob H3SBMA1", 0)
    util.initmat(eb, "mf464", "c322", "Prob H3SBMA2+", 0)
    util.initmat(eb, "mf465", "c330", "Prob H3SBHA0", 0)
    util.initmat(eb, "mf466", "c331", "Prob H3SBHA1", 0)
    util.initmat(eb, "mf467", "c332", "Prob H3SBHA2+", 0)
    util.initmat(eb, "mf468", "c410", "Prob BsLA0", 0)
    util.initmat(eb, "mf469", "c411", "Prob BsLA1", 0)
    util.initmat(eb, "mf470", "c412", "Prob BsLA2+", 0)
    util.initmat(eb, "mf471", "c420", "Prob BsMA0", 0)
    util.initmat(eb, "mf472", "c421", "Prob BsMA1", 0)
    util.initmat(eb, "mf473", "c422", "Prob BsMA2+", 0)
    util.initmat(eb, "mf474", "c430", "Prob BsHA0", 0)
    util.initmat(eb, "mf475", "c431", "Prob BsHA1", 0)
    util.initmat(eb, "mf476", "c432", "Prob BsHA2+", 0)
    util.initmat(eb, "mf477", "c510", "Prob RlLA0", 0)
    util.initmat(eb, "mf478", "c511", "Prob RlLA1", 0)
    util.initmat(eb, "mf479", "c512", "Prob RlLA2+", 0)
    util.initmat(eb, "mf480", "c520", "Prob RlMA0", 0)
    util.initmat(eb, "mf481", "c521", "Prob RlMA1", 0)
    util.initmat(eb, "mf482", "c522", "Prob RlMA2+", 0)
    util.initmat(eb, "mf483", "c530", "Prob RlHA0", 0)
    util.initmat(eb, "mf484", "c531", "Prob RlHA1", 0)
    util.initmat(eb, "mf485", "c532", "Prob RlHA2+", 0)
    util.initmat(eb, "mf486", "c610", "Prob WaLA0", 0)
    util.initmat(eb, "mf487", "c611", "Prob WaLA1", 0)
    util.initmat(eb, "mf488", "c612", "Prob WaLA2+", 0)
    util.initmat(eb, "mf489", "c620", "Prob WaMA0", 0)
    util.initmat(eb, "mf490", "c621", "Prob WaMA1", 0)
    util.initmat(eb, "mf491", "c622", "Prob WaMA2+", 0)
    util.initmat(eb, "mf492", "c630", "Prob WaHA0", 0)
    util.initmat(eb, "mf493", "c631", "Prob WaHA1", 0)
    util.initmat(eb, "mf494", "c632", "Prob WaHA2+", 0)
    util.initmat(eb, "mf495", "c710", "Prob BkLA0", 0)
    util.initmat(eb, "mf496", "c711", "Prob BkLA1", 0)
    util.initmat(eb, "mf497", "c712", "Prob BkLA2+", 0)
    util.initmat(eb, "mf498", "c720", "Prob BkMA0", 0)
    util.initmat(eb, "mf499", "c721", "Prob BkMA1", 0)
    util.initmat(eb, "mf500", "c722", "Prob BkMA2+", 0)
    util.initmat(eb, "mf501", "c730", "Prob BkHA0", 0)
    util.initmat(eb, "mf502", "c731", "Prob BkHA1", 0)
    util.initmat(eb, "mf503", "c732", "Prob BkHA2+", 0)

    util.initmat(eb, "mf505", "r1110", "Result WrSvLA0", 0)
    util.initmat(eb, "mf506", "r1111", "Result WrSvLA1", 0)
    util.initmat(eb, "mf507", "r1112", "Result WrSvLA2+", 0)
    util.initmat(eb, "mf508", "r1120", "Result WrSvMA0", 0)
    util.initmat(eb, "mf509", "r1121", "Result WrSvMA1", 0)
    util.initmat(eb, "mf510", "r1122", "Result WrSvMA2+", 0)
    util.initmat(eb, "mf511", "r1130", "Result WrSvHA0", 0)
    util.initmat(eb, "mf512", "r1131", "Result WrSvHA1", 0)
    util.initmat(eb, "mf513", "r1132", "Result WrSvHA2+", 0)
    util.initmat(eb, "mf514", "r1210", "Result WrHvLA0", 0)
    util.initmat(eb, "mf515", "r1211", "Result WrHvLA1", 0)
    util.initmat(eb, "mf516", "r1212", "Result WrHvLA2+", 0)
    util.initmat(eb, "mf517", "r1220", "Result WrHvMA0", 0)
    util.initmat(eb, "mf518", "r1221", "Result WrHvMA1", 0)
    util.initmat(eb, "mf519", "r1222", "Result WrHvMA2+", 0)
    util.initmat(eb, "mf520", "r1230", "Result WrHvHA0", 0)
    util.initmat(eb, "mf521", "r1231", "Result WrHvHA1", 0)
    util.initmat(eb, "mf522", "r1232", "Result WrHvHA2+", 0)
    util.initmat(eb, "mf523", "r1310", "Result WrH3LA0", 0)
    util.initmat(eb, "mf524", "r1311", "Result WrH3LA1", 0)
    util.initmat(eb, "mf525", "r1312", "Result WrH3LA2+", 0)
    util.initmat(eb, "mf526", "r1320", "Result WrH3MA0", 0)
    util.initmat(eb, "mf527", "r1321", "Result WrH3MA1", 0)
    util.initmat(eb, "mf528", "r1322", "Result WrH3MA2+", 0)
    util.initmat(eb, "mf529", "r1330", "Result WrH3HA0", 0)
    util.initmat(eb, "mf530", "r1331", "Result WrH3HA1", 0)
    util.initmat(eb, "mf531", "r1332", "Result WrH3HA2+", 0)
    util.initmat(eb, "mf532", "r1410", "Result WrBsLA0", 0)
    util.initmat(eb, "mf533", "r1411", "Result WrBsLA1", 0)
    util.initmat(eb, "mf534", "r1412", "Result WrBsLA2+", 0)
    util.initmat(eb, "mf535", "r1420", "Result WrBsMA0", 0)
    util.initmat(eb, "mf536", "r1421", "Result WrBsMA1", 0)
    util.initmat(eb, "mf537", "r1422", "Result WrBsMA2+", 0)
    util.initmat(eb, "mf538", "r1430", "Result WrBsHA0", 0)
    util.initmat(eb, "mf539", "r1431", "Result WrBsHA1", 0)
    util.initmat(eb, "mf540", "r1432", "Result WrBsHA2+", 0)
    util.initmat(eb, "mf541", "r1510", "Result WrRlLA0", 0)
    util.initmat(eb, "mf542", "r1511", "Result WrRlLA1", 0)
    util.initmat(eb, "mf543", "r1512", "Result WrRlLA2+", 0)
    util.initmat(eb, "mf544", "r1520", "Result WrRlMA0", 0)
    util.initmat(eb, "mf545", "r1521", "Result WrRlMA1", 0)
    util.initmat(eb, "mf546", "r1522", "Result WrRlMA2+", 0)
    util.initmat(eb, "mf547", "r1530", "Result WrRlHA0", 0)
    util.initmat(eb, "mf548", "r1531", "Result WrRlHA1", 0)
    util.initmat(eb, "mf549", "r1532", "Result WrRlHA2+", 0)
    util.initmat(eb, "mf550", "r1610", "Result WrWaLA0", 0)
    util.initmat(eb, "mf551", "r1611", "Result WrWaLA1", 0)
    util.initmat(eb, "mf552", "r1612", "Result WrWaLA2+", 0)
    util.initmat(eb, "mf553", "r1620", "Result WrWaMA0", 0)
    util.initmat(eb, "mf554", "r1621", "Result WrWaMA1", 0)
    util.initmat(eb, "mf555", "r1622", "Result WrWaMA2+", 0)
    util.initmat(eb, "mf556", "r1630", "Result WrWaHA0", 0)
    util.initmat(eb, "mf557", "r1631", "Result WrWaHA1", 0)
    util.initmat(eb, "mf558", "r1632", "Result WrWaHA2+", 0)
    util.initmat(eb, "mf559", "r1710", "Result WrBkLA0", 0)
    util.initmat(eb, "mf560", "r1711", "Result WrBkLA1", 0)
    util.initmat(eb, "mf561", "r1712", "Result WrBkLA2+", 0)
    util.initmat(eb, "mf562", "r1720", "Result WrBkMA0", 0)
    util.initmat(eb, "mf563", "r1721", "Result WrBkMA1", 0)
    util.initmat(eb, "mf564", "r1722", "Result WrBkMA2+", 0)
    util.initmat(eb, "mf565", "r1730", "Result WrBkHA0", 0)
    util.initmat(eb, "mf566", "r1731", "Result WrBkHA1", 0)
    util.initmat(eb, "mf567", "r1732", "Result WrBkHA2+", 0)

    util.initmat(eb, "mf568", "d110", "Demand SvLA0", 0)
    util.initmat(eb, "mf569", "d111", "Demand SvLA1", 0)
    util.initmat(eb, "mf570", "d112", "Demand SvLA2+", 0)
    util.initmat(eb, "mf571", "d120", "Demand SvMA0", 0)
    util.initmat(eb, "mf572", "d121", "Demand SvMA1", 0)
    util.initmat(eb, "mf573", "d122", "Demand SvMA2+", 0)
    util.initmat(eb, "mf574", "d130", "Demand SvHA0", 0)
    util.initmat(eb, "mf575", "d131", "Demand SvHA1", 0)
    util.initmat(eb, "mf576", "d132", "Demand SvHA2+", 0)
    util.initmat(eb, "mf577", "d210", "Demand HvLA0", 0)
    util.initmat(eb, "mf578", "d211", "Demand HvLA1", 0)
    util.initmat(eb, "mf579", "d212", "Demand HvLA2+", 0)
    util.initmat(eb, "mf580", "d220", "Demand HvMA0", 0)
    util.initmat(eb, "mf581", "d221", "Demand HvMA1", 0)
    util.initmat(eb, "mf582", "d222", "Demand HvMA2+", 0)
    util.initmat(eb, "mf583", "d230", "Demand HvHA0", 0)
    util.initmat(eb, "mf584", "d231", "Demand HvHA1", 0)
    util.initmat(eb, "mf585", "d232", "Demand HvHA2+", 0)
    util.initmat(eb, "mf586", "d310", "Demand H3SBLA0", 0)
    util.initmat(eb, "mf587", "d311", "Demand H3SBLA1", 0)
    util.initmat(eb, "mf588", "d312", "Demand H3SBLA2+", 0)
    util.initmat(eb, "mf589", "d320", "Demand H3SBMA0", 0)
    util.initmat(eb, "mf590", "d321", "Demand H3SBMA1", 0)
    util.initmat(eb, "mf591", "d322", "Demand H3SBMA2+", 0)
    util.initmat(eb, "mf592", "d330", "Demand H3SBHA0", 0)
    util.initmat(eb, "mf593", "d331", "Demand H3SBHA1", 0)
    util.initmat(eb, "mf594", "d332", "Demand H3SBHA2+", 0)
    util.initmat(eb, "mf595", "d410", "Demand BsLA0", 0)
    util.initmat(eb, "mf596", "d411", "Demand BsLA1", 0)
    util.initmat(eb, "mf597", "d412", "Demand BsLA2+", 0)
    util.initmat(eb, "mf598", "d420", "Demand BsMA0", 0)
    util.initmat(eb, "mf599", "d421", "Demand BsMA1", 0)
    util.initmat(eb, "mf600", "d422", "Demand BsMA2+", 0)
    util.initmat(eb, "mf601", "d430", "Demand BsHA0", 0)
    util.initmat(eb, "mf602", "d431", "Demand BsHA1", 0)
    util.initmat(eb, "mf603", "d432", "Demand BsHA2+", 0)
    util.initmat(eb, "mf604", "d510", "Demand RlLA0", 0)
    util.initmat(eb, "mf605", "d511", "Demand RlLA1", 0)
    util.initmat(eb, "mf606", "d512", "Demand RlLA2+", 0)
    util.initmat(eb, "mf607", "d520", "Demand RlMA0", 0)
    util.initmat(eb, "mf608", "d521", "Demand RlMA1", 0)
    util.initmat(eb, "mf609", "d522", "Demand RlMA2+", 0)
    util.initmat(eb, "mf610", "d530", "Demand RlHA0", 0)
    util.initmat(eb, "mf611", "d531", "Demand RlHA1", 0)
    util.initmat(eb, "mf612", "d532", "Demand RlHA2+", 0)
    util.initmat(eb, "mf613", "d610", "Demand WaLA0", 0)
    util.initmat(eb, "mf614", "d611", "Demand WaLA1", 0)
    util.initmat(eb, "mf615", "d612", "Demand WaLA2+", 0)
    util.initmat(eb, "mf616", "d620", "Demand WaMA0", 0)
    util.initmat(eb, "mf617", "d621", "Demand WaMA1", 0)
    util.initmat(eb, "mf618", "d622", "Demand WaMA2+", 0)
    util.initmat(eb, "mf619", "d630", "Demand WaHA0", 0)
    util.initmat(eb, "mf620", "d631", "Demand WaHA1", 0)
    util.initmat(eb, "mf621", "d632", "Demand WaHA2+", 0)
    util.initmat(eb, "mf622", "d710", "Demand BkLA0", 0)
    util.initmat(eb, "mf623", "d711", "Demand BkLA1", 0)
    util.initmat(eb, "mf624", "d712", "Demand BkLA2+", 0)
    util.initmat(eb, "mf625", "d720", "Demand BkMA0", 0)
    util.initmat(eb, "mf626", "d721", "Demand BkMA1", 0)
    util.initmat(eb, "mf627", "d722", "Demand BkMA2+", 0)
    util.initmat(eb, "mf628", "d730", "Demand BkHA0", 0)
    util.initmat(eb, "mf629", "d731", "Demand BkHA1", 0)
    util.initmat(eb, "mf630", "d732", "Demand BkHA2+", 0)
    util.initmat(eb, "mf631", "d810", "Demand SBLA0", 0)
    util.initmat(eb, "mf632", "d811", "Demand SBLA1", 0)
    util.initmat(eb, "mf633", "d812", "Demand SBLA2+", 0)
    util.initmat(eb, "mf634", "d820", "Demand SBMA0", 0)
    util.initmat(eb, "mf635", "d821", "Demand SBMA1", 0)
    util.initmat(eb, "mf636", "d822", "Demand SBMA2+", 0)
    util.initmat(eb, "mf637", "d830", "Demand SBHA0", 0)
    util.initmat(eb, "mf638", "d831", "Demand SBHA1", 0)
    util.initmat(eb, "mf639", "d832", "Demand SBHA2+", 0)
