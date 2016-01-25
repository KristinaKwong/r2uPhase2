##--------------------------------------------------
##--TransLink Phase 2 Regional Transportation Model
##--
##--Path:
##--Purpose:
##--------------------------------------------------
##--Last modified 2014-02-25 Kevin Bragg (INRO)
##         Optimization of matrix calculation expressions:
##          - used matrix multi-calculation feature
##          - moved evaluation of certain expressions
##            outside of for loops which do not change
##          - added constraint.by_value where applicable
##          - optimized probability calculations
##         Moved common functions to
##         05-11_ModeChoiceUtilities tool to improve
##         code reuse
##--Last modified 2014-02-14 Kevin Bragg (INRO)
##--Reason: Update to Emme 4.0 namespaces
##          Code cleanup PEP 8 compliance
##---------------------------------------------------
##--Called by:
##--Calls:
##--Accesses:
##--Outputs:
##---------------------------------------------------
##--Status/additional notes:
##---------------------------------------------------
## 05-09 NHBW Mode Choice Model

import inro.modeller as _modeller
import traceback as _traceback
from datetime import datetime
import os


process_matrix_trans = _modeller.Modeller().tool(
    "inro.emme.data.matrix.matrix_transaction")
compute_matrix = _modeller.Modeller().tool(
    "inro.emme.matrix_calculation.matrix_calculator")

utilities = _modeller.Modeller().module(
    "translink.emme.stage3.step5.utilities")
build_spec = utilities.build_spec


# TODO: add tool interface to mode choice procedure
class ModeChoiceNHBW(_modeller.Tool()):
    tool_run_msg = ""

    def page(self):
        pb = _modeller.ToolPageBuilder(self,
                                       title="Mode Choice Model",
                                       description="Not to be used directly, module containing "
                                                   "methods to calculate mode choice model. (etc).",
                                       runnable=True)
        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)
        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            scenario = _modeller.Modeller().scenario
            PathHeader = os.path.dirname(scenario.emmebank.path) + "\\"
            IterationNumber = 1
            run_model(scenario, PathHeader, IterationNumber, True)
            run_msg = "Tool completed"
            self.tool_run_msg = _modeller.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _modeller.PageBuilder.format_exception(e, _traceback.format_exc(e))
            raise


@_modeller.logbook_trace("Non-home-base work")
def run_model(scenario, data_folder, iteration_number, is_last_iteration):
    matrix_file = os.path.join(data_folder, "05_MODE_CHOICE/Inputs/NonWorkBatchin.txt")
    process_matrix_trans(matrix_file, scenario=scenario)

    calculate_blends(scenario)
    calculate_sov(scenario)
    calculate_hov2(scenario)
    calculate_bus(scenario)
    calculate_rail(scenario)
    calculate_walk(scenario)
    calculate_bike(scenario)
    utilities.calculate_probabilities(
        scenario, nests=[[0, 1], [3, 4], [5, 6]], theta=0.982936463751,
        utility_start_id=377, result_start_id=444, num_segments=3)
    #demand matrices are stored in matrices mf 640-702
    utilities.calculate_demand(
        scenario, demand_start=304, probability_start=444, result_start=643, num_segments=3)

    ExportModeChoice = _modeller.Modeller().module("translink.emme.stage3.step5.exportmodechoice")
    if is_last_iteration:
        purp = 9
        ExportModeChoice.Agg_Exp_Demand(data_folder, purp, iteration_number)

    # KB:   the non-home base WORK appears to be using the same
    #       components as the other NON-work purposes
    #       this may be an error
    aggregate_non_work_demand(scenario)

    # ********
    # Initialize matrices for resulted matrices - this should be done once only. (rs- will confirm with Ali the sequence)
    # ********
    folder = os.path.join(data_folder, "TimeSlicingFactors")
    utilities.process_transaction_list(scenario, folder, ['dmMatInitParts'])

    time_slice_non_home_base_work(scenario, data_folder)
    calculate_final_period_demand(scenario)

    if is_last_iteration:
        utilities.export_matrices_report(data_folder, "nhbw", range(773, 843))


## Aggregate nonwork demand in matrices mf 505-567 with home-base-work matrices
@_modeller.logbook_trace("Aggregate work demand")
def aggregate_non_work_demand(scenario):
    # KB: why is this function different from every other "aggregate_non_work_demand"?
    #     and this should be part of work demand?
    print "--------Calculate_Demand, " + str(datetime.now().strftime('%H:%M:%S'))
    spec_list = []
    matrixnum = 643
    resultmat = 508
    for i in range(3):
        for k in range(8):
            result = "mf" + str(resultmat + i + 9 * k)
            if k < 7:
                expression = "mf" + str(resultmat + i + k * 9) + "+" + "mf" + str(matrixnum + i + 9 * k)
                spec_list.append(build_spec(expression, result))
            #if k == 7:
            #    expression = "mf" + str(resultmat + i + 9 * k) + "+0"
            #    spec_list.append(build_spec(expression, result))
    compute_matrix(spec_list, scenario)


@_modeller.logbook_trace("Calculate_Bike_utlity")
def calculate_bike(scenario):
    # Bike utility stored in matrices mf428-mf436
    print "--------Calculate_Bike_utlity, " + str(datetime.now().strftime('%H:%M:%S'))
    emmebank = scenario.emmebank

    alt_spec_cons = str(-5.59693336915)
    zero_cars = str(2.60674401989)
    #low_inc = str(0.638580209018)
    #sen20_bk = str(-0.402393576296)
    bkscr_bk = str(1.04700624762)
    distance = str(-0.230231405702)
    #cbd = str(0.467852445416)
    cs_bk_250 = str(0.923417675228)
    #intrazonal = str(0.391849811299)
    van = str(2.24855928839)
    vanx = str(-1.89263746393)

    mode_mf = 430
    spec_list = []
    constraint = {"od_values": "mf159",
                  "interval_min": 0,
                  "interval_max": 0,
                  "condition": "EXCLUDE"}

    # bk_invan: (ifeq(gyo,4) and ifeq(gyd,4)) + (ifeq(gyo,3) and ifeq(gyd,3))
    #expression_3 = expression_3 + " + " " + cbd + "*(((mo29.eq.3)+(md29.eq.3)).ge.1)"
    expression_3 = vanx + "*((mo29.eq.3)*(md29.eq.4).or.(mo29.eq.4)*(md29.eq.3))"
    expression_3 = expression_3 + " + " + cs_bk_250 + "*(((mo395+mo396).gt.0))"
    #expression_3 = expression_3 + " + " + intrazonal + "*((q.eq.p))"
    #expression_3 = expression_3 + " + " + rurl + "*((((mo29.ge.11)*(mo29.lt.15))+((md29.ge.11)*(md29.lt.15))).ge.1)"
    spec_list.append(build_spec(expression_3, "mf927", constraint))

    for i in range(1, 4):
        expression_1 = alt_spec_cons
        if i == 1:
            expression_1 = expression_1 + " + " + zero_cars
        spec_list.append(build_spec(expression_1, "mf925", constraint))

        #au_dst
        expression_2 = distance + "*mf144"
        #expression_2 = expression_2 + " + " + sen20_bk + "*((mo19/(mo20+0.00001)).gt.(0.19999))"
        expression_2 = expression_2 + " + " + van + "*((mo29.eq.4).or.(md29.eq.4))"
        if i < 3:
            # KB: fixed the following expression, was not used properly
            #     the following line should be uncommented
            #expression_2 = expression_2 + " + " + bkscr_bk + "*((mo13+md13).gt.5)"
            pass
        spec_list.append(build_spec(expression_2, "mf926", constraint))

        result = "mf" + str(mode_mf + i)
        emmebank.matrix(result).initialize(-9999)
        print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
        expression = "mf925 + mf926 + mf927"
        spec_list.append(build_spec(expression, result, constraint))
    compute_matrix(spec_list, scenario)


@_modeller.logbook_trace("Calculate_Walk_utlity")
def calculate_walk(scenario):
    # Walk utility stored in matrices mf419-mf427
    print "--------Calculate_Walk_utility, " + str(datetime.now().strftime('%H:%M:%S'))
    emmebank = scenario.emmebank

    alt_spec_cons = str(0.169933759873)

    zero_cars = str(2.2206400954)
    #two_plus_car = str(-0.316113591369)
    #sen20_wk = str(0.380104895856)
    distance = str(-1.11387301871)
    vanx = str(-3.22634801369)
    #intra_van = str(-0.623614268412)
    #dens = str(0.00250030921058)
    van = str(1.0388751981)
    cs_wlk_500 = str(0.494470012597)
    #intrazonal = str(0.391849811299)

    mode_mf = 421
    spec_list = []
    constraint = {"od_values": "mf158",
                  "interval_min": 0,
                  "interval_max": 0,
                  "condition": "EXCLUDE"}

    #expression_2 = expression_2 + " + " + sen20_wk + "*((mo19/(mo20+0.00001)).gt.(0.19999))"
    #au_dst
    expression_2 = distance + "*mf144"
    # auto accessibilities: autoempt (i.e auto accessibilities)
    # p725*(vanod*iflt(veh2,2))
    expression_2 = expression_2 + " + " + van + "*((mo29.eq.4).or.(md29.eq.4))"
    spec_list.append(build_spec(expression_2, "mf926", constraint))

    # intra-vancouver: 1 if (ifeq(gyo,3)*ifeq(gyd,4)) + (ifeq(gyo,4)*ifeq(gyd,3))
    expression_3 = vanx + "*((mo29.eq.3)*(md29.eq.4).or.(mo29.eq.4)*(md29.eq.3))"
    expression_3 = expression_3 + " + " + cs_wlk_500 + "*((mo394.gt.1)*(mo29.ne.3)*(md29.eq.3))"
    #expression_3 = expression_3 + " + " + intrazonal + "*((q.eq.p))"
    spec_list.append(build_spec(expression_3, "mf927", constraint))

    for i in range(1, 4):
        expression_1 = alt_spec_cons
        #if i<4: expression_1 = expression_1 + " + " + low_inc
        #if i>6: expression_1 = expression_1 + " + " + hi_inc
        if i == 1:
            expression_1 = expression_1 + " + " + zero_cars
        #if (i==3 or i ==6 or i==9): expression_1 = expression_1 + " + " + two_plus_car    "*(((mo29.gt.11)+(md29.gt.11)).ge.1)"
        #1 (if cars = 2/3) * ifne(gyo,5)*ifne(gyd,5)* ifne(gyo,3)*ifne(gyd,3)* ifne(gyo,4)*ifne(gyd,4)
        spec_list.append(build_spec(expression_1, "mf925", constraint))

        result = "mf" + str(mode_mf + i)
        emmebank.matrix(result).initialize(-9999)
        print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
        expression = "mf925 + mf926 + mf927"
        spec_list.append(build_spec(expression, result, constraint))
    compute_matrix(spec_list, scenario)


@_modeller.logbook_trace("Calculate_Rail_utlity")
def calculate_rail(scenario):
    # Rail utility stored between matrices mf410-mf418
    print "--------Calculate_Rail_utility, " + str(datetime.now().strftime('%H:%M:%S'))
    emmebank = scenario.emmebank

    alt_spec_cons = str(-.270380946937)
    zero_cars = str(2.96145717405)
    emp_dens = str(0.00146009527481)
    van = str(-0.336080476573)
    intra_van = str(-0.811588719975)
    cost_all_inc = str(-0.0808320244183)
    rt_fare = "mf161"
    rt_brd = "mf155"
    cbd = str(-1.30989257652)
    tran_acc = str(0.0711864048598)
    within_gy = str(-0.826515173137)

    mode_mf = 412
    spec_list = []
    constraint = {"od_values": "mf157",
                  "interval_min": 0,
                  "interval_max": 0,
                  "condition": "EXCLUDE"}

    # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
    expression_2 = cbd + "*((mo29.eq.3).or.(md29.eq.3))"
    expression_2 = expression_2 + " + " + van + "*((mo29.eq.4).or.(md29.eq.4))"
    #expression_2 = expression_2 + " + " + van + "*(((mo29.eq.4)+(md29.eq.4)).ge.1)"
    #expression_2 = expression_2 + " + " + emp_dens + "*((((md5+md6+md7+md8+md9+md10+md11)*10000/(md17)).min.200)*(md29.ne.3)*(md29.ne.4))"
    spec_list.append(build_spec(expression_2, "mf926", constraint))

    for i in range(1, 4):
        expression_1 = alt_spec_cons + " -0.2*(md29.eq.1)" \
                                       " -0.2*(md29.eq.2) " \
                                       " -0.3*(((mo29.eq.3).or.(md29.eq.3))) " \
                                       " -0.5*(((mo29.eq.4).or.(md29.eq.4)))" \
                                       " -0.5*(((mo29.eq.5).or.(md29.eq.5)))"
        #*(hiin*ifne(cbdod,1)*ifne(rurod,1))
        #if i>6: expression_1 = expression_1 + " + " + hi_inc
        if i == 1: expression_1 = expression_1 + " + " + zero_cars
        #if (i==2 or i==5 or i==8): expression_1 = expression_1 + " + " + one_car

        # cost (all incomes) :
        expression_1 = expression_1 + " + " + cost_all_inc + "*" + rt_fare

        # all incomes: (rt_wait/3) + (rt_aux/3) + (rt_ivtb/6) +  (rt_ivtr/6) +(rt_brd*10/6)
        expression_1 = expression_1 + " + " + cost_all_inc + \
                       "*((mf154/4) + (mf156/4) + (mf152/2) + (mf153/2) + (mf155*3.75))"
        spec_list.append(build_spec(expression_1, "mf925", constraint))

        #rail accessibilities : ((min(transit2,150))*ifne(cbdod,1)*iflt(useveh2,2))
        if i != 3:
            expression_3 = tran_acc + "*(mo392.min.150)*(mo29.ne.3)*(md29.ne.3)"
        else:
            expression_3 = "0"
        expression_3 = expression_3 + " + " + within_gy + "*(mo29.eq.md29)*(mo29.ne.3)*((mo29.ne.4))"
        expression_3 = expression_3 + " + " + intra_van + "*((mo29.eq.4)*(md29.eq.4))"
        spec_list.append(build_spec(expression_3, "mf927", constraint))

        result = "mf" + str(mode_mf + i)
        emmebank.matrix(result).initialize(-9999)
        print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
        expression = "mf925 + mf926 + mf927"
        spec_list.append(build_spec(expression, result, constraint))
    compute_matrix(spec_list, scenario)


@_modeller.logbook_trace("Calculate_Bus_utility")
def calculate_bus(scenario):
    # Bus utility stored between matrices mf401-mf409
    print "--------Calculate_Bus_utility, " + str(datetime.now().strftime('%H:%M:%S'))
    emmebank = scenario.emmebank

    alt_spec_cons = str(-1.74573644783)
    zero_cars = str(3.32735665134)
    #one_car = str(-0.419164918819)
    cost_all_inc = str(-0.0808320244183)
    rt_fare = "mf160"
    bs_brd = "mf149"
    #emp_dens = str(0.0053261980113)
    van = str(0.249444789958)
    cbd = str(-1.78822869622)
    tran_acc = str(0.0532539992096)
    within_gy_not_van = str(-0.74828445222)

    mode_mf = 403
    spec_list = []
    constraint = {"od_values": "mf151",
                  "interval_min": 0,
                  "interval_max": 0,
                  "condition": "EXCLUDE"}

    # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
    expression_2 = van + "*(((mo29.eq.4).or.(md29.eq.4)))"
    # within gy (not rural):  1 if gyo=gyd and (iflt(gyo,12) and iflt(gyd,12))
    #expression_2 = expression_2 + " + " + within_gy_not_van + "*(mo29.eq.md29)*(mo29.ne.3)*((mo29.ne.4))"
    spec_list.append(build_spec(expression_2, "mf926", constraint))

    for i in range(1, 4):
        expression_1 = alt_spec_cons + " - 0.3 * (((mo29.eq.4).or.(md29.eq.4))) " \
                                       " - 0.3 * (mo29.eq.3) " \
                                       " - 0.2 * (md29.eq.2)" \
                                       " - 0.1 * (((mo29.eq.5).or.(md29.eq.5)))"
        if i == 1:
            expression_1 = expression_1 + " + " + zero_cars
        #+ p62*(ifeq(useveh2,1)*ifne(rurod,1))
        #if (i==2 or i==5 or i==8): expression_1 = expression_1 + " + " + one_car

        # cost (all incomes) :
        expression_1 = expression_1 + " + " + cost_all_inc + "*" + rt_fare

        # all incomes: (bs_wait/3) + (bs_aux/3) + (bs_ivtb/6) + (bs_brd*10/6)
        #expression_1 = expression_1 + " + " + cost_all_inc + "*((mf147/4) + (mf150/4) + (mf148/2) + (" + bs_brd + "*2.5))"
        expression_1 = expression_1 + " + " + cost_all_inc + "*((mf147/2) + (mf150/2) + (mf148/4) + (" + bs_brd + "*2.5))"
        spec_list.append(build_spec(expression_1, "mf925", constraint))

        #relative accessibilities: ((min(transit2,150))*ifne(cbdod,1)*iflt(useveh2,2))
        if i != 3:
            expression_3 = tran_acc + "*(mo392.min.150)*(mo29.ne.3)*(md29.ne.3)"
        else:
            expression_3 = "0"
        #expression_3 = expression_3 + " + " + emp_dens + "*((((md5+md6+md7+md8+md9+md10+md11)*10000/(md17)).min.200)*(mo29.ne.3)*(md29.ne.3)*(md29.ne.4))"
        # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
        expression_3 = expression_3 + " + " + cbd + "*((mo29.eq.3).or.(md29.eq.3))"
        expression_3 = expression_3 + " + " + within_gy_not_van + "*(mo29.eq.md29)*(mo29.ne.3)*(mo29.ne.4)"
        spec_list.append(build_spec(expression_3, "mf927", constraint))

        result = "mf" + str(mode_mf + i)
        emmebank.matrix(result).initialize(-9999)
        print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
        expression = "mf925 + mf926 + mf927"
        spec_list.append(build_spec(expression, result, constraint))
    compute_matrix(spec_list, scenario)


@_modeller.logbook_trace("Calculate_HOV2_utility")
def calculate_hov2(scenario):
    # HOV2 utility stored between matrices mf383-mf391
    print "--------Calculate_HOV2_utility, " + str(datetime.now().strftime('%H:%M:%S'))
    emmebank = scenario.emmebank

    alt_spec_cons = str(-1.50506819449)
    zero_cars = str(1.05426348381)
    twoplus_cars = str(0.584017808338)
    cost_all_inc = str(-0.0808320244183)
    au_prk = "md28"
    cbd = str(-2.29781247732)
    auto_acc = str(0.00294127099292)

    mode_mf = 385
    spec_list = []

    # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
    expression_2 =  cbd + "*((mo29.eq.3).or.(md29.eq.3))"
    spec_list.append(build_spec(expression_2, "mf926"))

    # within gy   1 if gyo=gyd
    #expression_3 = expression_3 + " + " + within_gy_not_rural + "*(mo29.eq.md29)"
    #expression_3 = expression_3 + " + " + ret_dens + "*(min((max((md8*10000)/mo17,0)),200))"
    # auto accessibilities: autoempt (i.e auto accessibilities)
    expression_3 = auto_acc + "*(mo47)"
    spec_list.append(build_spec(expression_3, "mf927"))

    for i in range(1, 4):
        expression_1 = alt_spec_cons

        if i == 1:
            expression_1 = expression_1 + " + " + zero_cars
        if i == 3:
            expression_1 = expression_1 + " + " + twoplus_cars

        #COST ALL INCOMES: (0.09*au_dst) + (1.25*au_toll) + (0.5*au_prk)
        expression_1 = expression_1 + " + " + cost_all_inc + "*((ms18*mf144/ms67) + (ms19*mf146/ms67) + ((mo28/2+md28/2)/ms67))"
        expression_1 = expression_1 + " + " + cost_all_inc + "*(mf145/4)"
        spec_list.append(build_spec(expression_1, "mf925"))

        result = "mf" + str(mode_mf + i)
        print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
        expression = "mf925 + mf926 + mf927"
        spec_list.append(build_spec(expression, result))
    compute_matrix(spec_list, scenario)


@_modeller.logbook_trace("Calculate_SOV_utility")
def calculate_sov(scenario):
    # SOV utility stored between matrices mf374-mf382
    print "--------Calculate_SOV_utility, " + str(datetime.now().strftime('%H:%M:%S'))
    emmebank = scenario.emmebank

    twoplus_cars = str(0.725011702685)
    cost_all_inc = str(-0.0808320244183)
    au_prk = "md28"
    cbd = str(-2.64560380326)
    #intra_van = str(-1.60862610719)
    van = str(0.119704408492)

    mode_mf = 376
    spec_list = []

    for i in range(1, 4):
        if i == 3:
            expression = twoplus_cars
        else:
            expression = "0"

        #cost all incomes: (0.18*au_dst) + (2.5*au_toll) + au_prk
        expression = expression + " + " + cost_all_inc + "*((ms18*mf144) + (ms19*mf146) + md28/2 + mo28/2)"

        expression = expression + " + " + cost_all_inc + "*(mf145/4)"

        # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
        expression = expression + " + " + cbd + "*((mo29.eq.3).or.(md29.eq.3))"
        expression = expression + " + " + van + "*((mo29.eq.4).or.(md29.eq.4))"
        # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
        #expression = expression + " + " + intra_van + "*((mo29.eq.4)*(md29.eq.4))"

        # auto accessibilities: autoempt (i.e auto accessibilities)
        #expression = expression + " + " + auto_acc + "*(mo954)"

        # rural : 1 if (ifgt(gyo,11) or ifgt(gyd,11))
        #expression = expression + " + " + rural + "*((((mo29.gt.10)*(mo29.lt.15))+((md29.gt.10)*(md29.lt.15))).ge.1)"

        result = "mf" + str(mode_mf + i)
        print result + " : " + expression
        spec_list.append(build_spec(expression, result))
    compute_matrix(spec_list, scenario)


@_modeller.logbook_trace("Calculate_non_home_base_work_blends")
def calculate_blends(scenario):
    print "--------Calculate_non_home_base_work_blends, " + str(datetime.now().strftime('%H:%M:%S'))
    emmebank = scenario.emmebank

    expressions_list = [
        ['(mf110.eq.1)*(ms57+((mf115.eq.0)*(1-ms57)))', 'mf140'],
        ['1-mf140', 'mf141'],
        ['(mf121.eq.1)*(ms57+((mf129.eq.0).or.(mf130.eq.0))*(1-ms57))', 'mf142'],
        ['1-mf142', 'mf143'],
        ['mf100*ms57+mf103*(1-ms57)', 'mf144'],
        ['mf101*ms57+mf104*(1-ms57)', 'mf145'],
        ['mf102*ms57+mf105*(1-ms57)', 'mf146'],
        ['mf106*(mf140+(mf140.eq.1)*0.10)+mf111*mf141', 'mf147'],
        ['mf107*mf140+mf112*mf141', 'mf148'],
        ['mf136*mf140+mf137*mf141', 'mf149'],
        ['mf109*mf140+mf114*mf141', 'mf150'],
        ['mf116*mf142+mf124*mf143', 'mf152'],
        ['mf117*mf142+mf125*mf143', 'mf153'],
        ['mf118*mf142+mf126*mf143', 'mf154'],
        ['mf138*mf142+mf139*mf143', 'mf155'],
        ['mf120*mf142+mf128*mf143', 'mf156'],
        ['(mf100.lt.10)', 'mf158'],
        ['(mf100.lt.20)', 'mf159']
    ]
    spec_list = []
    for expression, result in expressions_list:
        spec_list.append(build_spec(expression, result))
    compute_matrix(spec_list, scenario)


#********
#    ADD ON (rs)
#    Main module time slicing the matrices
#********
@_modeller.logbook_trace("Time slice non-home base work")
def time_slice_non_home_base_work(scenario, data_folder):
    print "Time slicing NON-HOME BASE WORK trip matrices begin" + str(datetime.now().strftime('%H:%M:%S'))
    #
    #    Preparing expressions for calculation
    #
    # nBegSOVIncLow  = 640
    nBegSOV = 643
    # nBegSOVIncHigh = 646
    # nBegHv2IncLow  = 649
    nBegHOV = 652
    # nBegHv2IncHigh = 655
    # nBegHv3IncLow  = 658
    # nBegHv3IncMed  = 661
    # nBegHv3IncHigh = 664
    # nBegBusIncLow  = 667
    nBegTrnBus = 670
    # nBegBusIncHigh = 673
    # nBegRailIncLow  = 676
    nBegRail = 679
    nBegWalk = 688
    nBegBike = 697

    dmSOV = "("
    for nCnt1 in range(nBegSOV, nBegSOV + 2):
        dmSOV = dmSOV + "mf" + str(nCnt1) + "+"
    dmSOV = dmSOV + "mf" + str(nBegSOV + 2) + ")"

    dmHOV = "("
    for nCnt1 in range(nBegHOV, nBegHOV + 2):
        dmHOV = dmHOV + "mf" + str(nCnt1) + "+"
    dmHOV = dmHOV + "mf" + str(nBegHOV + 2) + ")"

    dmTrnBus = "("
    for nCnt1 in range(nBegTrnBus, nBegTrnBus + 2):
        dmTrnBus = dmTrnBus + "mf" + str(nCnt1) + "+"
    dmTrnBus = dmTrnBus + "mf" + str(nBegTrnBus + 2) + ")"

    dmRail = "("
    for nCnt1 in range(nBegRail, nBegRail + 2):
        dmRail = dmRail + "mf" + str(nCnt1) + "+"
    dmRail = dmRail + "mf" + str(nBegRail + 2) + ")"

    dmBike = "("
    for nCnt1 in range(nBegBike, nBegBike + 2):
        dmBike = dmBike + "mf" + str(nCnt1) + "+"
    dmBike = dmBike + "mf" + str(nBegBike + 2) + ")"

    dmWalk = "("
    for nCnt1 in range(nBegWalk, nBegWalk + 2):
        dmWalk = dmWalk + "mf" + str(nCnt1) + "+"
    dmWalk = dmWalk + "mf" + str(nBegWalk + 2) + ")"

    dmActive = "(" + dmBike + "+" + dmWalk + ")"

    arDmMatrix = [dmSOV, dmHOV, dmTrnBus, dmRail, dmActive]

    aTSFactor = [
        ['NHBSOVT1', 'NHBSOVT2', 'NHBSOVT3', 'NHBSOVT4', 'NHBSOVT5', 'NHBSOVT6', 'NHBSOVT8'],
        ['NHB2PerT1', 'NHB2PerT2', 'NHB2PerT3', 'NHB2PerT4', 'NHB2PerT5', 'NHB2PerT6', 'NHB2PerT8'],
        ['NHBTransitT1', 'NHBTransitT2', 'NHBTrnBusT3', 'NHBTrnBusT4', 'NHBTransitT5', 'NHBTransitT6', 'NHBTransitT7'],
        ['NHBTransitT1', 'NHBTransitT2', 'NHBRailT3', 'NHBRailT4', 'NHBTransitT5', 'NHBTransitT6', 'NHBTransitT7'],
        ['NHBActiveT1', 'NHBActiveT2', 'NHBActiveT3', 'NHBActiveT4', 'NHBActiveT5', 'NHBActiveT6', 'NHBActiveT7']]

    #********
    #    Start matrix number to store the demand by TOD
    #********
    aResultMatrix = [794, 801, 815, 822, 829]
    folder = os.path.join(data_folder, "TimeSlicingFactors")

    for files, demand, result in zip(aTSFactor, arDmMatrix, aResultMatrix):
        utilities.process_transaction_list(scenario, folder, files)
        spec_list = []
        for time_period in range(0, 7):
            result_name = "mf" + str(result + time_period)
            expression = result_name + "+" + demand + "*mf" + str(703 + time_period)
            spec_list.append(build_spec(expression, result_name))
        compute_matrix(spec_list, scenario)

    print "Time slicing NON-HOME BASE WORK matrices completed." + str(datetime.now().strftime('%H:%M:%S'))


#********
#    Module - it is identical to matrix-calculation() (rs)
#********
@_modeller.logbook_trace("Calculate final period demands")
def calculate_final_period_demand(scenario):
    msAutOccWork3Plus = "ms60"
    msAutOccUniv3Plus = "ms61"
    msAutOccGSch2Plus = "ms62"
    msAutOccShop2Plus = "ms63"
    msAutOccPerB2Plus = "ms64"
    msAutOccSocR2Plus = "ms65"
    msAutOccEcor2Plus = "ms66"
    msAutOccNhbW2Plus = "ms67"
    msAutOccNhbO2Plus = "ms68"

    msAutOccWork3PlusM = "ms90"
    msAutOccUniv3PlusM = "ms91"
    msAutOccGSch2PlusM = "ms92"
    msAutOccShop2PlusM = "ms93"
    msAutOccPerB2PlusM = "ms94"
    msAutOccSocR2PlusM = "ms95"
    msAutOccEcor2PlusM = "ms96"
    msAutOccNhbW2PlusM = "ms97"
    msAutOccNhbO2PlusM = "ms98"
    #
    #    EXCEPTION - For non home base work trips, they should be assigned SOV hbw-med_inc (mf844) or hbw-med_inc (mf849)
    #
    spec_list = []

    spec_list.append(build_spec("mf844+" + "mf798", "mf844"))
    spec_list.append(build_spec("mf849+" + "(mf805/" + msAutOccNhbW2Plus + ")", "mf849"))
    spec_list.append(build_spec("mf853+" + "mf819*mf996", "mf853"))
    spec_list.append(build_spec("mf854+" + "mf826*mf992", "mf854"))
    spec_list.append(build_spec("mf855+" + "mf833", "mf855"))

    # Track work transit demand separately for park and ride model
    spec_list.append(build_spec("mf998 + mf819*mf996", "mf998"))
    spec_list.append(build_spec("mf997 + mf826*mf992", "mf997"))
    #
    #    Midday
    #
    spec_list.append(build_spec("mf857+" + "mf799", "mf857"))
    spec_list.append(build_spec("mf862+" + "(mf806/" + msAutOccNhbW2PlusM + ")", "mf862"))
    spec_list.append(build_spec("mf866+" + "mf820", "mf866"))
    spec_list.append(build_spec("mf867+" + "mf827", "mf867"))
    spec_list.append(build_spec("mf868+" + "mf834", "mf868"))
    #
    #    PM peak hour
    #
    spec_list.append(build_spec("mf870+" + "mf800", "mf870"))
    spec_list.append(build_spec("mf875+" + "(mf807/" + msAutOccNhbW2Plus + ")", "mf875"))
    spec_list.append(build_spec("mf879+" + "mf821", "mf879"))
    spec_list.append(build_spec("mf880+" + "mf828", "mf880"))
    spec_list.append(build_spec("mf881+" + "mf835", "mf881"))

    #
    #    Accumulated demand matrices of 4 time periods by modes (auto person, bus, rail, active)
    #    mf70-mf73 : T1(before 6am and after 7pm) - auto person, bus, rail, active
    #    mf75-mf78 : T2(6am-10am) - auto person, bus, rail, active
    #    mf80-mf83 : T3(10am-2pm) - auto person, bus, rail, active
    #    mf85-mf88 : T4(2pm-7pm) - auto person, bus, rail, active
    #
    #    Auto person - 1 income levels & SOV & 2+person
    #
    spec_list.append(build_spec("mf70+mf794+mf801", "mf70"))
    spec_list.append(build_spec("mf71+mf815", "mf71"))
    spec_list.append(build_spec("mf72+mf822", "mf72"))
    spec_list.append(build_spec("mf73+mf829", "mf73"))

    spec_list.append(build_spec("mf75+mf795+mf802", "mf75"))
    spec_list.append(build_spec("mf76+mf816", "mf76"))
    spec_list.append(build_spec("mf77+mf823", "mf77"))
    spec_list.append(build_spec("mf78+mf830", "mf78"))

    spec_list.append(build_spec("mf80+mf796+mf803", "mf80"))
    spec_list.append(build_spec("mf81+mf817", "mf81"))
    spec_list.append(build_spec("mf82+mf824", "mf82"))
    spec_list.append(build_spec("mf83+mf831", "mf83"))

    spec_list.append(build_spec("mf85+mf797+mf804", "mf85"))
    spec_list.append(build_spec("mf86+mf818", "mf86"))
    spec_list.append(build_spec("mf87+mf825", "mf87"))
    spec_list.append(build_spec("mf88+mf832", "mf88"))

    compute_matrix(spec_list, scenario)
