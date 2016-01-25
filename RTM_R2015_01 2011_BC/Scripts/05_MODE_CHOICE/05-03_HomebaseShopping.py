##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step5.modechoicehbshop
##--Purpose: HBSHOPPING Mode Choice Model
##---------------------------------------------------------------------
import inro.modeller as _m
from datetime import datetime
import os

process_matrix_trans = _m.Modeller().tool(
    "inro.emme.data.matrix.matrix_transaction")
compute_matrix = _m.Modeller().tool(
    "inro.emme.matrix_calculation.matrix_calculator")

utilities = _m.Modeller().module(
    "translink.emme.stage3.step5.utilities")
build_spec = utilities.build_spec


# TODO: add tool interface to mode choice procedure
class ModeChoiceHBShopping(_m.Tool()):
    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Mode Choice Model"
        pb.description = "Not to be used directly, module containing methods to calculate mode choice model. (etc)."
        pb.branding_text = "TransLink"
        pb.runnable=False

        return pb.render()


@_m.logbook_trace("Home-base Shopping")
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
        scenario, nests=[[0, 1], [3, 4], [5, 6]], theta=0.95)
    utilities.calculate_demand(
        scenario, demand_start=337, probability_start=441, result_start=640)


    ExportModeChoice = _m.Modeller().module("translink.emme.stage3.step5.exportmodechoice")
    if is_last_iteration:
        purp = 3
        ExportModeChoice.Agg_Exp_Demand(data_folder, purp, iteration_number)

    aggregate_non_work_demand(scenario)

    #********
    #    Initialize matrices for resulted matrices - this should be done once only. (rs- will confirm with Ali the sequence)
    #********
    folder = os.path.join(data_folder, "TimeSlicingFactors")
    utilities.process_transaction_list(scenario, folder, ['dmMatInitParts'])

    time_slice_shopping(scenario, data_folder)
    calculate_final_period_demand(scenario)
    if is_last_iteration:
        utilities.export_matrices_report(data_folder, "shop", range(773, 843))


@_m.logbook_trace("continue aggregating non work demand, shopping")
def aggregate_non_work_demand(scenario):
    ## Aggregate nonwork demand in matrices mf568-mf639
    print "--------Aggregate Non-work demand, " + str(datetime.now().strftime('%H:%M:%S'))
    spec_list = []
    matrixnum = 640
    resultmat = 568
    for i in range(0, 63):
        expression = "mf" + str(resultmat + i) + "+" + "mf" + str(matrixnum + i)
        result = "mf" + str(resultmat + i)
        spec_list.append(build_spec(expression, result))
    #for i in range(63, 72):
    #    expression = "mf" + str(resultmat + i) + "+" + "0"
    #    spec_list.append(build_spec(expression, result))
    compute_matrix(spec_list, scenario)


@_m.logbook_trace("Calculate_Bike_Utility")
def calculate_bike(scenario):
    # Bike utility stored in matrices mf428-mf436
    print "--------Calculate_Bike_Utility, " + str(datetime.now().strftime('%H:%M:%S'))
    emmebank = scenario.emmebank

    alt_spec_cons = str(-3.91878857801)
    zero_cars = str(2.77462846159)
    sen20_bk = str(0.370186203737)
    bkscr_bk = str(0.549756039150)
    distance = str(-0.222895257743)
    bk_van = str(1.21486435204)
    cs_bk_250 = str(0.909390457053)
    intrazonal = str(0.248136493447)

    mode_mf = 427
    spec_list = []
    constraint = {"od_values": "mf159",
                  "interval_min": 0,
                  "interval_max": 0,
                  "condition": "EXCLUDE"}

    #au_dst
    #ifgt((BKSCRo+bkscrd),5)*iflt(gyo,12)*iflt(gyd,12)*ifne(gyo,3)*ifne(gyd,3)*ifne(gyo,4)*ifne(gyd,4)
    expression_2 = (bkscr_bk +
                    "*((mo13+md13).gt.5)*(mo29.ne.4)*(mo29.ne.3)*(md29.ne.4)*(md29.ne.3)*(mo29.lt.12)*(md29.lt.12)")
    expression_2 = expression_2 + distance + "*mf144"
    expression_2 = expression_2 + " + " + sen20_bk + "*((mo19/(mo20+0.00001)).gt.(0.19999))"
    spec_list.append(build_spec(expression_2, "mf926", constraint))

    # bk_invan: (ifeq(gyo,4) and ifeq(gyd,4)) + (ifeq(gyo,3) and ifeq(gyd,3))
    expression_3 = bk_van + "*(((mo29.eq.4)+(md29.eq.4)).ge.1)"
    expression_3 = expression_3 + " + " + cs_bk_250 + "*(((mo395+mo396).gt.0))"
    expression_3 = expression_3 + " + " + intrazonal + "*((q.eq.p))"
    spec_list.append(build_spec(expression_3, "mf927", constraint))

    for i in range(1, 10):
        expression_1 = alt_spec_cons
        if i in (1, 4, 7):
            expression_1 = expression_1 + " + " + zero_cars
        spec_list.append(build_spec(expression_1, "mf925", constraint))

        result = "mf" + str(mode_mf + i)
        emmebank.matrix(result).initialize(-9999)
        print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
        expression = "mf925 + mf926 + mf927"
        spec_list.append(build_spec(expression, result, constraint))
    compute_matrix(spec_list, scenario)


@_m.logbook_trace("Calculate_Walk_Utility")
def calculate_walk(scenario):
    print "--------Calculate_Walk_Utility, " + str(datetime.now().strftime('%H:%M:%S'))
    # Walk utility stored in matrices mf419-mf427
    emmebank = scenario.emmebank

    alt_spec_cons = str(0.449558652976)
    low_inc = str(0.239931679415)
    zero_cars = str(2.76732528301)
    two_plus_car = str(-0.258542588398)
    sen20_wk = str(0.370186203737)
    distance = str(-0.780772005373)
    vanx = str(-1.05969403054)
    ret_dens = str(0.0171066854068)
    cs_wlk_250 = str(0.505798826512)
    intrazonal = str(0.248136493447)

    mode_mf = 418
    spec_list = []
    constraint = {"od_values": "mf158",
                  "interval_min": 0,
                  "interval_max": 0,
                  "condition": "EXCLUDE"}

    expression_2 = sen20_wk + "*((mo19/(mo20+0.00001)).gt.(0.19999))"
    #au_dst
    expression_2 = expression_2 + distance + "*mf144"
    # auto accessibilities: autoempt (i.e auto accessibilities)
    expression_2 = expression_2 + " + " + ret_dens + "*((((md8*10000)/md17).max.0).min.200)"
    # p725*(vanod*iflt(veh2,2))
    spec_list.append(build_spec(expression_2, "mf926", constraint))

    # intra-vancouver: 1 if (ifeq(gyo,3)*ifeq(gyd,4)) + (ifeq(gyo,4)*ifeq(gyd,3))
    expression_3 = vanx + "*(((mo29.eq.3)*(md29.eq.4) + (mo29.eq.4)*(md29.eq.3)).ge.1)"
    expression_3 = expression_3 + " + " + cs_wlk_250 + "*(((mo395+mo396).gt.0))"
    expression_3 = expression_3 + " + " + intrazonal + "*((q.eq.p))"
    spec_list.append(build_spec(expression_3, "mf927", constraint))

    for i in range(1, 10):
        expression_1 = alt_spec_cons
        expression_1 = expression_1 + " -0.3*(((mo29.eq.6)+(md29.eq.6)).ge.1)"
        if i < 4:
            expression_1 = expression_1 + " + " + low_inc + "*((mo29.ne.3)*(md29.ne.3)*(mo29.lt.12)*(md29.lt.12))"
        if i in (1, 4, 7):
            expression_1 = expression_1 + " + " + zero_cars
        if i in (3, 6, 9):
            #1 (if cars = 2/3) * ifne(gyo,5)*ifne(gyd,5)* ifne(gyo,3)*ifne(gyd,3)* ifne(gyo,4)*ifne(gyd,4)
            expression_1 = expression_1 + " + " + two_plus_car + \
                           "*((mo29.ne.3)*(mo29.ne.4)*(mo29.ne.5)*(md29.ne.3)*(md29.ne.4)*(md29.ne.5))"

        spec_list.append(build_spec(expression_1, "mf925", constraint))

        result = "mf" + str(mode_mf + i)
        emmebank.matrix(result).initialize(-9999)
        print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
        expression = "(mf925 + mf926 + mf927)"
        spec_list.append(build_spec(expression, result, constraint))
    compute_matrix(spec_list, scenario)


@_m.logbook_trace("Calculate_Rail_Utility")
def calculate_rail(scenario):
    # Rail utility stored between matrices mf410-mf418
    print "--------Calculate_Rail, " + str(datetime.now().strftime('%H:%M:%S'))
    emmebank = scenario.emmebank

    alt_spec_cons = str(0.640799542360)
    high_inc = str(-0.896270603004)
    zero_cars = str(3.51725071283)
    ret_dens = str(0.0149949026169)
    nhi_intrv = str(-1.08147085046)
    cost_all_inc = str(-0.142290239812)
    rt_fare = "mf161"
    cost_low_inc = str(-0.142290239812)
    rt_brd = "mf155"
    cost_med_inc = str(-0.142290239812)
    cost_high_inc = str(-0.142290239812)
    cbd = str(0.309434778360)
    van = str(-0.567324857938)
    tran_acc = str(0.0963732699860)
    within_gy_not_van = str(-1.34153419264)
    rur_locar = str(-1.57464898416)
    delta = str(-0.955000470751)

    mode_mf = 409
    spec_list = []
    constraint = {"od_values": "mf157",
                  "interval_min": 0,
                  "interval_max": 0,
                  "condition": "EXCLUDE"}

    for i in range(1, 10):
        # NOTE: expression_2 and expression_3 expression which change with i
        #       these expression could be re-ordered such that some portion
        #       of the expressions could be pulled out of the loop
        expression_1 = alt_spec_cons
        # calibration factors for gys 4,7,8
        expression_1 = (expression_1 + " -0.2*(((mo29.eq.4).or.(md29.eq.4)))"
                                       " -0.15*(((mo29.eq.7).or.(md29.eq.7)))"
                                       " -0.15*(((mo29.eq.8).or.(md29.eq.8)))")
        if i > 6:
            expression_1 = expression_1 + " + " + high_inc
        if i < 7:
            expression_1 = (expression_1 + " + " + nhi_intrv +
                            "*((mo29.eq.4)*(md29.eq.4))+0.5*(mo29.eq.3)-0.3*(mo29.eq.4)")
        if i in (1, 4, 7):
            expression_1 = expression_1 + " + " + zero_cars

        # cost (all incomes) :
        expression_1 = expression_1 + " + " + cost_all_inc + "*" + rt_fare

        # if low income:  (rt_wait/3) + (rt_aux/3) + (rt_ivtb/6) +  (rt_ivtr/6) +(rt_brd*10/6)
        if i < 4:
            expression_1 = (expression_1 + " + " + cost_low_inc +
                            "*((mf154/6) + (mf156/6) + (mf152/12) + (mf153/12) + (mf155*5/6))")

        # # if med income:  (rt_wait*2/3) + (rt_aux*2/3) + (rt_ivtb/3) +  (rt_ivtr/3) +(rt_brd*10/3)
        if 3 < i < 7:
            expression_1 = (expression_1 + " + " + cost_med_inc +
                            "*((mf154/3) + (mf156/3) + (mf152/6) + (mf153/6) + (mf155*10/6))")

        # # if high income:  (rt_wait*2/3) + (rt_aux*2/3) + (rt_ivtb/6) +  (rt_ivtr/6) +(rt_brd*10/6)
        if i > 6:
            expression_1 = (expression_1 + " + " + cost_high_inc +
                            "*((mf154/3) + (mf156/3) + (mf152/6) + (mf153/6) + (mf155*10/6))")

        # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
        if i != 4 and i != 5 and i != 6:
            expression_2 = cbd + "*(((mo29.eq.3)+(md29.eq.3)).ge.1)"
        else:
            expression_2 = "0"

        # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
        expression_2 = expression_2 + " + " + van + "*(((mo29.eq.4)+(md29.eq.4)).ge.1)"
        # dens: min((max((POP11o*10000)/area,0)),100)*(ifne(gyo,3)*ifne(gyo,4))
        expression_2 = expression_2 + " + " + ret_dens + "*((((md8*10000)/md17).max.0).min.200)"

        #relative accessibilities (auto-transit): (max(autoempt-transit2,0))
        expression_3 = tran_acc + "*((((mo955).min.100)).max.0)*(mo29.ne.3)*(md29.ne.3)*(mo29.lt.11)*(md29.lt.11)"
        expression_3 = expression_3 + " + " + within_gy_not_van + "*((mo29.eq.md29)*(mo29.ne.4))"
        #rur_locar  (ifgt(gyo,10) or ifgt(gyd,10))*iflt(useveh2,2)
        if i <> 3 and i <> 6 and i <> 9:
            expression_3 = expression_3 + " + " + rur_locar + "*((((mo29.ge.11)*(mo29.lt.15))+((md29.ge.11)*(md29.lt.15))).ge.1)"
        expression_3 = expression_3 + " + " + delta + "*(((mo29.eq.8)+(md29.eq.8)).ge.1)"

        spec_list.append(build_spec(expression_1, "mf925", constraint))
        spec_list.append(build_spec(expression_2, "mf926", constraint))
        spec_list.append(build_spec(expression_3, "mf927", constraint))

        result = "mf" + str(mode_mf + i)
        emmebank.matrix(result).initialize(-9999)
        print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
        expression = "mf925 + mf926 + mf927"
        spec_list.append(build_spec(expression, result, constraint))
    compute_matrix(spec_list, scenario)


@_m.logbook_trace("Calculate_Bus_Utility")
def calculate_bus(scenario):
    # Bus utility stored between matrices mf401-mf409
    print "--------Calculate_Bus, " + str(datetime.now().strftime('%H:%M:%S'))
    emmebank = scenario.emmebank

    alt_spec_cons = str(-0.463337085790)
    high_inc = str(-0.869378696585)
    zero_cars = str(3.89544086190)
    cost_all_inc = str(-0.142290239812)
    rt_fare = "mf160"
    cost_low_inc = str(-0.142290239812)
    bs_brd = "mf149"
    cost_med_inc = str(-0.142290239812)
    cost_high_inc = str(-0.142290239812)
    ret_dens = str(0.00492640771932)
    intra_van = str(-1.04655090384)
    tran_acc = str(0.121902229398)
    rural = str(-1.00007527183)
    within_gy_not_van = str(-0.677142510014)
    delta = str(-0.955000470751)

    mode_mf = 400
    spec_list = []
    constraint = {"od_values": "mf151",
                  "interval_min": 0,
                  "interval_max": 0,
                  "condition": "EXCLUDE"}

    # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
    expression_2 = intra_van + "*((mo29.eq.4)*(md29.eq.4))"
    # within gy (not rural):  1 if gyo=gyd and (iflt(gyo,12) and iflt(gyd,12))
    expression_2 = expression_2 + " + " + within_gy_not_van + "*((mo29.eq.md29)*(mo29.ne.4)*(md29.ne.4))"
    spec_list.append(build_spec(expression_2, "mf926", constraint))

    #relative accessibilities (auto-transit): (max(autoempt-transit2,0))
    expression_3 =tran_acc + "*((((mo955).min.100)).max.0)*(mo29.ne.3)*(md29.ne.3)"
    expression_3 = expression_3 + " + " + ret_dens + "*((((md8*10000)/md17).max.0).min.200)"
    # rural : 1 if (ifgt(gyo,10) or ifgt(gyd,10))
    expression_3 = expression_3 + " + " + rural + "*((((mo29.ge.11)*(mo29.lt.15))+((md29.ge.11)*(md29.lt.15))).ge.1)"
    expression_3 = expression_3 + " + " + delta + "*(((mo29.eq.8)+(md29.eq.8)).ge.1)"
    spec_list.append(build_spec(expression_3, "mf927", constraint))

    for i in range(1, 10):
        expression_1 = alt_spec_cons
        # bus calibration factors for gys 8,10,13
        expression_1 = (expression_1 + " -0.15*(((mo29.eq.8).or.(md29.eq.8))) "
                                       " - 0.2*(((mo29.eq.10).or.(md29.eq.10)))"
                                       " + 0.2*(((mo29.eq.13).or.(md29.eq.13)))")
        expression_1 = (expression_1 + " - 0.15*(((mo29.eq.2).or.(md29.eq.2))) "
                                       " - 0.15*(((mo29.eq.4).or.(md29.eq.4)))")
        if i < 7:
            expression_1 = expression_1 + "-0.4*(mo29.eq.2)-0.2*(mo29.eq.6)-0.3*(mo29.eq.4)-0.2*(mo29.eq.7)"
        if i > 6:
            expression_1 = expression_1 + " + " + high_inc
        if i in (1, 4, 7):
            expression_1 = expression_1 + " + " + zero_cars

        # cost (all incomes) :
        expression_1 = expression_1 + " + " + cost_all_inc + "*" + rt_fare

        # if low income: (bs_wait/3) + (bs_aux/3) + (bs_ivtb/6) + (bs_brd*10/6)
        if i < 4:
            expression_1 = expression_1 + " + " + cost_low_inc + "*((mf147/6) + (mf150/6) + (mf148/12) + (" + bs_brd + "*5/6))"

        # if med income: (bs_wait*2/3) + (bs_aux*2/3) + (bs_ivtb/3) + (bs_brd*5)
        if 3 < i < 7:
            expression_1 = expression_1 + " + " + cost_med_inc + "*((mf147/3) + (mf150/3) + (mf148/6) + (" + bs_brd + "*2.5))"

        # if high income: (bs_wait*2/3) + (bs_aux*2/3) + (bs_ivtb/3) + (bs_brd*5)
        if i > 6:
            expression_1 = expression_1 + " + " + cost_high_inc + "*((mf147/3) + (mf150/3) + (mf148/6) + (" + bs_brd + "*2.5))"

        spec_list.append(build_spec(expression_1, "mf925", constraint))

        result = "mf" + str(mode_mf + i)
        emmebank.matrix(result).initialize(-9999)
        print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
        expression = "mf925 + mf926 + mf927"
        spec_list.append(build_spec(expression, result, constraint))
    compute_matrix(spec_list, scenario)


@_m.logbook_trace("Calculate_HOV2_Utility")
def calculate_hov2(scenario):
    # HOV2 utility stored between matrices mf383-mf391
    print "--------Calculate_HOV2_utility, " + str(datetime.now().strftime('%H:%M:%S'))
    emmebank = scenario.emmebank

    alt_spec_cons = str(-0.324483112286)
    low_inc = str(0.431568807761)
    zero_cars = str(0.756375019402)
    twoplus_cars = str(0.782870634893)
    cost_all_inc = str(-0.142290239812)
    au_prk = "md28"
    cost_low_inc = str(-0.142290239812)
    cost_med_inc = str(-0.142290239812)
    cost_high_inc = str(-0.142290239812)
    cbd = str(-1.55635523739)
    auto_acc = str(0.00955548818747)
    intra_van = str(-0.861729981998)
    ret_dens = str(0.00492640771932)
    rural = str(0.294506660329)
    within_gy = str(-0.219305935017)

    mode_mf = 382
    spec_list = []
    # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
    expression_2 = cbd + "*(((mo29.eq.3)+(md29.eq.3)).ge.1)"
    # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
    expression_2 = expression_2 + " + " + intra_van + "*((mo29.eq.4)*(md29.eq.4))"
    # rural : 1 if (ifgt(gyo,11) or ifgt(gyd,11))
    expression_2 = expression_2 + " + " + rural + "*((((mo29.gt.11)*(mo29.lt.15))+((md29.gt.11)*(md29.lt.15))).ge.1)"
    spec_list.append(build_spec(expression_2, "mf926"))

    # within gy   1 if gyo=gyd
    expression_3 = within_gy + "*(mo29.eq.md29)"
    expression_3 = expression_3 + " + " + ret_dens + "*((((md8*10000)/md17).max.0).min.200)"
    # auto accessibilities: autoempt (i.e auto accessibilities)
    expression_3 = expression_3 + " + " + auto_acc + "*(mo954)"
    spec_list.append(build_spec(expression_3, "mf927"))

    for i in range(1, 10):
        expression_1 = alt_spec_cons

        if i < 4:
            expression_1 = expression_1 + " + " + low_inc
        if i in (1, 4, 7):
            expression_1 = expression_1 + " + " + zero_cars
        if i in (3, 6, 9):
            expression_1 = expression_1 + " + " + twoplus_cars

        #COST ALL INCOMES: (0.09*au_dst) + (1.25*au_toll) + (0.5*au_prk)
        expression_1 = (expression_1 + " + " + cost_all_inc +
                        "*((ms18*mf144/ms63) + (ms19*mf146/ms63) + 1/ms63*(mo28/2 +md28/2))")

        if i < 4:
            expression_1 = expression_1 + " + " + cost_low_inc + "*(mf145/12)"
        if 3 < i < 7:
            expression_1 = expression_1 + " + " + cost_med_inc + "*(mf145/6)"
        if i > 6:
            expression_1 = expression_1 + " + " + cost_high_inc + "*(mf145/6)"

        spec_list.append(build_spec(expression_1, "mf925"))

        result = "mf" + str(mode_mf + i)
        print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
        expression = "mf925 + mf926 + mf927"
        spec_list.append(build_spec(expression, result))
    compute_matrix(spec_list, scenario)


@_m.logbook_trace("Calculate_SOV_Utility")
def calculate_sov(scenario):
    # SOV utility stored between matrices mf374-mf382
    print "--------Calculate_SOV_utility, " + str(datetime.now().strftime('%H:%M:%S'))

    twoplus_cars = str(0.751973661453)
    cost_all_inc = str(-0.142290239812)
    au_prk = "md28"
    cost_low_inc = str(-0.142290239812)
    cost_med_inc = str(-0.142290239812)
    cost_high_inc = str(-0.142290239812)
    cbd = str(-1.99354155989)
    intra_van = str(-0.652446321142)
    auto_acc = str(0.0132255229331)
    rural = str(0.242561421966)

    mode_mf = 373
    spec_list = []

    for i in range(1, 10):
        expression = "0"

        if i in (3, 6, 9):
            expression = expression + " + " + twoplus_cars

        #cost all incomes: (0.18*au_dst) + (2.5*au_toll) + au_prk
        expression = expression + " + " + cost_all_inc + "*((ms18*mf144) + (ms19*mf146) + mo28/2 + md28/2)"

        if i < 4:
            expression = expression + " + " + cost_low_inc + "*(mf145/12)"
        if 3 < i < 7:
            expression = expression + " + " + cost_med_inc + "*(mf145/6)"
        if i > 6:
            expression = expression + " + " + cost_high_inc + "*(mf145/6)"

        # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
        expression = expression + " + " + cbd + "*(((mo29.eq.3)+(md29.eq.3)).ge.1)"

        # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
        expression = expression + " + " + intra_van + "*((mo29.eq.4)*(md29.eq.4))"

        # auto accessibilities: autoempt (i.e auto accessibilities)
        expression = expression + " + " + auto_acc + "*(mo954)"

        # rural : 1 if (ifgt(gyo,11) or ifgt(gyd,11))
        expression = expression + " + " + rural + "*((((mo29.gt.11)*(mo29.lt.15))+((md29.gt.11)*(md29.lt.15))).ge.1)"

        result = "mf" + str(mode_mf + i)
        print result + " : " + expression
        spec_list.append(build_spec(expression, result))
    compute_matrix(spec_list, scenario)


@_m.logbook_trace("Calculate_Home-base_Shopping_blends")
def calculate_blends(scenario):
    print "--------Calculate_Home-base_Shopping_blends, " + str(datetime.now().strftime('%H:%M:%S'))

    expressions_list = [
        ['(mf110.eq.1)*(ms53+((mf115.eq.0)*(1-ms53)))', 'mf140'],
        ['1-mf140', 'mf141'],
        ['(mf121.eq.1)*(ms53+(((mf129.eq.0)+(mf130.eq.0)).ge.1)*(1-ms53))', 'mf142'],
        ['1-mf142', 'mf143'],
        ['mf100*ms53+mf103*(1-ms53)', 'mf144'],
        ['mf101*ms53+mf104*(1-ms53)', 'mf145'],
        ['mf102*ms53+mf105*(1-ms53)', 'mf146'],
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
@_m.logbook_trace("Time slice home base shopping")
def time_slice_shopping(scenario, data_folder):
    print "Time slicing SHOPPING trip matrices begin" + str(datetime.now().strftime('%H:%M:%S'))
    #
    #    Preparing expressions for calculation
    #
    nBegSOVIncLow = 640
    nBegSOVIncMed = 643
    nBegSOVIncHigh = 646
    nBegHv2IncLow = 649
    nBegHv2IncMed = 652
    nBegHv2IncHigh = 655
    # nBegHv3IncLow  = 658
    # nBegHv3IncMed  = 661
    # nBegHv3IncHigh = 664
    nBegBusIncLow = 667
    nBegBusIncMed = 670
    nBegBusIncHigh = 673
    nBegRailIncLow = 676
    nBegRailIncMed = 679
    nBegRailIncHigh = 682
    nBegActive = 685

    dmSOVLowInc = "("
    for nCnt1 in range(nBegSOVIncLow, nBegSOVIncLow + 2):
        dmSOVLowInc = dmSOVLowInc + "mf" + str(nCnt1) + "+"
    dmSOVLowInc = dmSOVLowInc + "mf" + str(nBegSOVIncLow + 2) + ")"

    dmSOVMedHighInc = "("
    for nCnt1 in range(nBegSOVIncMed, nBegSOVIncMed + 5):
        dmSOVMedHighInc = dmSOVMedHighInc + "mf" + str(nCnt1) + "+"
    dmSOVMedHighInc = dmSOVMedHighInc + "mf" + str(nBegSOVIncMed + 5) + ")"

    dmHv2LowInc = "("
    for nCnt1 in range(nBegHv2IncLow, nBegHv2IncLow + 2):
        dmHv2LowInc = dmHv2LowInc + "mf" + str(nCnt1) + "+"
    dmHv2LowInc = dmHv2LowInc + "mf" + str(nBegHv2IncLow + 2) + ")"

    dmHv2MedHighInc = "("
    for nCnt1 in range(nBegHv2IncMed, nBegHv2IncMed + 5):
        dmHv2MedHighInc = dmHv2MedHighInc + "mf" + str(nCnt1) + "+"
    dmHv2MedHighInc = dmHv2MedHighInc + "mf" + str(nBegHv2IncMed + 5) + ")"

    # dmHv3LowInc = "("
    # for nCnt1 in range(nBegHv3IncLow,nBegHv3IncLow+2): dmHv3LowInc = dmHv3LowInc+"mf"+str(nCnt1)+"+"
    # dmHv3LowInc=dmHv3LowInc+"mf"+str(nBegHv3IncLow+2)+")"

    # dmHv3MedHighInc = "("
    # for nCnt1 in range(nBegHv3IncMed,nBegHv3IncMed+5): dmHv3MedHighInc = dmHv3MedHighInc+"mf"+str(nCnt1)+"+"
    # dmHv3MedHighInc=dmHv3MedHighInc+"mf"+str(nBegHv3IncMed+5)+")"

    dmBus = "("
    for nCnt1 in range(nBegBusIncLow, nBegBusIncLow + 8):
        dmBus = dmBus + "mf" + str(nCnt1) + "+"
    dmBus = dmBus + "mf" + str(nBegBusIncLow + 8) + ")"

    dmRail = "("
    for nCnt1 in range(nBegRailIncLow, nBegRailIncLow + 8):
        dmRail = dmRail + "mf" + str(nCnt1) + "+"
    dmRail = dmRail + "mf" + str(nBegRailIncLow + 8) + ")"

    dmActive = "("
    for nCnt1 in range(nBegActive, nBegActive + 17):
        dmActive = dmActive + "mf" + str(nCnt1) + "+"
    dmActive = dmActive + "mf" + str(nBegActive + 17) + ")"

    arDmMatrix = [dmSOVLowInc, dmSOVMedHighInc,
                  dmHv2LowInc, dmHv2MedHighInc,
                  dmBus, dmRail, dmActive]

    #
    #    Correction - rail applies to time period
    #
    aTSFactor = [
        ['ShpPBSocSOVT1', 'ShpPBSocSOVT2', 'ShpPBSocSOVT3', 'ShpPBSocSOVT4', 'ShpPBSocSOVT5', 'ShpPBSocAutoT6',
         'ShpPBSocSOVT8'],
        ['ShpPBSocSOVT1', 'ShpPBSocSOVT2', 'ShpPBSocSOVT3', 'ShpPBSocSOVT4', 'ShpPBSocSOVT5', 'ShpPBSocAutoT6',
         'ShpPBSocSOVT8'],
        ['ShpPBSoc2perT1', 'ShpPBSoc2perT2', 'ShpPBSoc2perT3', 'ShpPBSoc2perT4', 'ShpPBSoc2perT5', 'ShpPBSocAutoT6',
         'ShpPBSoc2perT8'],
        ['ShpPBSoc2perT1', 'ShpPBSoc2perT2', 'ShpPBSoc2perT3', 'ShpPBSoc2perT4', 'ShpPBSoc2perT5', 'ShpPBSocAutoT6',
         'ShpPBSoc2perT8'],
        ['ShpPBSocTrnBusT1', 'ShpPBSocTrnBusT2', 'ShpPBSocTrnBusT3', 'ShpPBSocTrnBusT4', 'ShpPBSocTransitT5',
         'ShpPBSocTransitT6', 'ShpPBSocTransitT7', ],
        ['ShpPBSocRailT1', 'ShpPBSocRailT2', 'ShpPBSocRailT3', 'ShpPBSocRailT4', 'ShpPBSocTransitT5',
         'ShpPBSocTransitT6', 'ShpPBSocTransitT7', ],
        ['ShpPBSocActiveT1', 'ShpPBSocActiveT2', 'ShpPBSocActiveT3', 'ShpPBSocActiveT4', 'ShpPBSocActiveT5',
         'ShpPBSocActiveT6', 'ShpPBSocActiveT7']]

    #********
    #    Start matrix number to store the demand by TOD
    #********
    aResultMatrix = [773, 794, 780, 801, 815, 822, 829]
    folder = os.path.join(data_folder, "TimeSlicingFactors")

    for files, demand, result in zip(aTSFactor, arDmMatrix, aResultMatrix):
        utilities.process_transaction_list(scenario, folder, files)
        spec_list = []
        for time_period in range(0, 7):
            result_name = "mf" + str(result + time_period)
            expression = result_name + "+" + demand + "*mf" + str(703 + time_period)
            spec_list.append(build_spec(expression, result_name))
        compute_matrix(spec_list, scenario)

    print "Time slicing SHOPPING matrices completed." + str(datetime.now().strftime('%H:%M:%S'))


#********
#    Module - it is identical to matrix-calculation() (rs)
#********
@_m.logbook_trace("Calculate final period demands")
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
    #    For shopping's TSF was blended with social and recreation, it over-estimates the shopping trip during amph.
    #    An adjustment factor,35%, is used to factor down the demand.
    #
    spec_list = []

    spec_list.append(build_spec("mf846+" + "mf777*.35", "mf846"))
    spec_list.append(build_spec("mf847+" + "mf798*.35", "mf847"))
    spec_list.append(build_spec("mf851+" + "(mf784*.35/" + msAutOccShop2Plus + ")", "mf851"))
    spec_list.append(build_spec("mf852+" + "(mf805*.35/" + msAutOccShop2Plus + ")", "mf852"))
    spec_list.append(build_spec("mf853+" + "mf819*mf996", "mf853"))
    spec_list.append(build_spec("mf854+" + "mf826*mf992", "mf854"))
    spec_list.append(build_spec("mf855+" + "mf833", "mf855"))
    #
    #    Midday
    #
    spec_list.append(build_spec("mf859+" + "mf778", "mf859"))
    spec_list.append(build_spec("mf860+" + "mf799", "mf860"))
    spec_list.append(build_spec("mf864+" + "(mf785/" + msAutOccShop2PlusM + ")", "mf864"))
    spec_list.append(build_spec("mf865+" + "(mf806/" + msAutOccShop2PlusM + ")", "mf865"))
    spec_list.append(build_spec("mf866+" + "mf820", "mf866"))
    spec_list.append(build_spec("mf867+" + "mf827", "mf867"))
    spec_list.append(build_spec("mf868+" + "mf834", "mf868"))
    #
    #    PM peak hour
    #
    spec_list.append(build_spec("mf872+" + "mf779", "mf872"))
    spec_list.append(build_spec("mf873+" + "mf800", "mf873"))
    spec_list.append(build_spec("mf877+" + "(mf786/" + msAutOccShop2Plus + ")", "mf877"))
    spec_list.append(build_spec("mf878+" + "(mf807/" + msAutOccShop2Plus + ")", "mf878"))
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
    #    Auto person - 2 income levels & SOV & 2+person
    #
    spec_list.append(build_spec("mf70+mf773+mf794+mf780+mf801", "mf70"))
    spec_list.append(build_spec("mf71+mf815", "mf71"))
    spec_list.append(build_spec("mf72+mf822", "mf72"))
    spec_list.append(build_spec("mf73+mf829", "mf73"))

    spec_list.append(build_spec("mf75+mf774+mf795+mf781+mf802", "mf75"))
    spec_list.append(build_spec("mf76+mf816", "mf76"))
    spec_list.append(build_spec("mf77+mf823", "mf77"))
    spec_list.append(build_spec("mf78+mf830", "mf78"))

    spec_list.append(build_spec("mf80+mf775+mf796+mf782+mf803", "mf80"))
    spec_list.append(build_spec("mf81+mf817", "mf81"))
    spec_list.append(build_spec("mf82+mf824", "mf82"))
    spec_list.append(build_spec("mf83+mf831", "mf83"))

    spec_list.append(build_spec("mf85+mf776+mf797+mf783+mf804", "mf85"))
    spec_list.append(build_spec("mf86+mf818", "mf86"))
    spec_list.append(build_spec("mf87+mf825", "mf87"))
    spec_list.append(build_spec("mf88+mf832", "mf88"))

    compute_matrix(spec_list, scenario)
