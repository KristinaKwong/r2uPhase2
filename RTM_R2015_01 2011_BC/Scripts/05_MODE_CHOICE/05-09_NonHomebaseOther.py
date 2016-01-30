##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step5.modechoicenhbo
##--Purpose: NHBO Mode Choice Model
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
class ModeChoiceNHBO(_m.Tool()):
    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Mode Choice Model"
        pb.description = "Not to be used directly, module containing methods to calculate mode choice model. (etc)."
        pb.branding_text = "TransLink"
        pb.runnable = False

        return pb.render()


@_m.logbook_trace("Non-home-base other")
def run_model(scenario, eb, iteration_number, is_last_iteration):
    data_folder = os.path.dirname(eb.path) + "\\"
    utilities.dmMatInit_NonWork(eb)

    calculate_blends(scenario)
    calculate_sov(scenario)
    calculate_hov2(scenario)
    calculate_bus(scenario)
    calculate_rail(scenario)
    calculate_walk(scenario)
    calculate_bike(scenario)

    utilities.calculate_probabilities(
        scenario, nests=[[0, 1], [3, 4], [5, 6]], theta=0.95,
        utility_start_id=377, result_start_id=444, num_segments=3)

    #demand matrices are stored in matrices mf 640-702
    utilities.calculate_demand(
        scenario, demand_start=307, probability_start=444, result_start=643, num_segments=3)

    ExportModeChoice = _m.Modeller().tool("translink.emme.stage3.step5.exportmodechoice")
    if is_last_iteration:
        purp = 8
        ExportModeChoice.Agg_Exp_Demand(eb, purp, iteration_number)

    aggregate_non_work_demand(scenario)

    # ********
    # Initialize matrices for resulted matrices - this should be done once only. (rs- will confirm with Ali the sequence)
    # ********
    utilities.dmMatInitParts(eb)
    time_slice_non_home_base_others(scenario, data_folder)
    calculate_final_period_demand(scenario)
    if is_last_iteration:
        utilities.export_matrices_report(data_folder, "nhbo", range(773, 843))


## Aggregate nonwork demand in matrices mf568-mf639
@_m.logbook_trace("continue aggregating non work demand, non-homebase other")
def aggregate_non_work_demand(scenario):
    # KB: why is this function different from every other "aggregate_non_work_demand"?
    print "--------Aggregate Non-work demand, " + str(datetime.now().strftime('%H:%M:%S'))
    spec_list = []
    matrixnum = 643
    resultmat = 571
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


@_m.logbook_trace("Calculate_Bike_Utility")
def calculate_bike(scenario):
    # Bike utility stored in matrices mf428-mf436
    print "--------Calculate_Bike_utility, " + str(datetime.now().strftime('%H:%M:%S'))
    emmebank = scenario.emmebank

    alt_spec_cons = str(-4.06031887359)
    zero_cars = str(2.81807924683)
    #sen20_bk = str(-0.402393576296)
    #bkscr_bk = str(0.582651776309)
    distance = str(-0.158346991589)
    #cbd = str(0.467852445416)
    cs_bk_250 = str(0.671644485599)
    intrazonal = str(0.379715780481)
    #rurl = str(-0.971214188807))

    mode_mf = 430
    spec_list = []
    constraint = {"od_values": "mf159",
                  "interval_min": 0,
                  "interval_max": 0,
                  "condition": "EXCLUDE"}

    #au_dst
    expression_2 = distance + "*mf144"
    #expression_2 = expression_2 + " + " + sen20_bk + "*((mo19/(mo20+0.00001)).gt.(0.19999))"
    spec_list.append(build_spec(expression_2, "mf926", constraint))

    # bk_invan: (ifeq(gyo,4) and ifeq(gyd,4)) + (ifeq(gyo,3) and ifeq(gyd,3))
    #expression_3 = expression_3 + " + " " + cbd + "*(((mo29.eq.3)+(md29.eq.3)).ge.1)"
    expression_3 = cs_bk_250 + "*(((mo395+mo396).gt.0))"
    expression_3 = expression_3 + " + " + intrazonal + "*((q.eq.p))"
    #expression_3 = expression_3 + " + " + rurl + "*((((mo29.ge.11)*(mo29.lt.15))+((md29.ge.11)*(md29.lt.15))).ge.1)"
    spec_list.append(build_spec(expression_3, "mf927", constraint))

    for i in range(1, 4):
        expression_1 = alt_spec_cons
        if i == 1:
            expression_1 = expression_1 + " + " + zero_cars
        spec_list.append(build_spec(expression_1, "mf925", constraint))

        result = "mf" + str(mode_mf + i)
        emmebank.matrix(result).initialize(-9999)
        print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
        expression = "mf925 + mf926 + mf927"
        spec_list.append(build_spec(expression, result, constraint))
    compute_matrix(spec_list, scenario)


@ _m.logbook_trace("Calculate_Walk_utlity")
def calculate_walk(scenario):
    # Walk utility stored in matrices mf419-mf427
    print "--------Calculate_Walk_utility, " + str(datetime.now().strftime('%H:%M:%S'))
    emmebank = scenario.emmebank

    alt_spec_cons = str(0.526142885183)
    zero_cars = str(2.39749417559)
    distance = str(-0.813774047754)
    van = str(-1.14425664675)
    cs_wlk_250 = str(0.438600084157)
    intrazonal = str(0.379715780481)

    mode_mf = 421
    spec_list = []
    constraint = {"od_values": "mf158",
                  "interval_min": 0,
                  "interval_max": 0,
                  "condition": "EXCLUDE"}

    #au_dst
    #expression_2 = expression_2 + " + " + sen20_wk + "*((mo19/(mo20+0.00001)).gt.(0.19999))"
    expression_2 = distance + "*mf144"
    # p725*(vanod*iflt(veh2,2))
    expression_2 = expression_2 + " + " + van + "*((mo29.eq.4).or.(md29.eq.4))"
    spec_list.append(build_spec(expression_2, "mf926", constraint))

    # intra-vancouver: 1 if (ifeq(gyo,3)*ifeq(gyd,4)) + (ifeq(gyo,4)*ifeq(gyd,3))
    #expression_3 = expression_3 + " + " + vanx + "*(((mo29.eq.3)*(md29.eq.4) + (mo29.eq.4)*(md29.eq.3)).ge.1)"
    expression_3 = cs_wlk_250 + "*(((mo395+mo396).gt.0))"
    expression_3 = expression_3 + " + " + intrazonal + "*((q.eq.p))"
    spec_list.append(build_spec(expression_3, "mf927", constraint))

    for i in range(1, 4):
        expression_1 = alt_spec_cons
        if i == 1:
            expression_1 = expression_1 + " + " + zero_cars

        spec_list.append(build_spec(expression_1, "mf925", constraint))

        result = "mf" + str(mode_mf + i)
        emmebank.matrix(result).initialize(-9999)
        print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
        expression = "(mf925 + mf926 + mf927)"
        spec_list.append(build_spec(expression, result, constraint))
    compute_matrix(spec_list, scenario)


@_m.logbook_trace("Calculate_Rail_utlity")
def calculate_rail(scenario):
    # Rail utility stored between matrices mf410-mf418
    print "--------Calculate_Rail_utility, " + str(datetime.now().strftime('%H:%M:%S'))
    emmebank = scenario.emmebank

    alt_spec_cons = str(-0.13451104037)
    zero_cars = str(2.53529052309)
    one_car = str(-0.615297379921)
    #pop_dens = str(0.00422033459459)
    emp_dens = str(0.00453561089011)
    van = str(-0.50712212889)
    intra_van = str(-1.8684715424)
    cost_all_inc = str(-0.101645666576)
    rt_fare = "mf161"
    rt_brd = "mf155"
    #cbd = str(0.283351662675)
    tran_acc = str(0.160089279023)
    within_gy_not_van = str(-1.11817184871)

    mode_mf = 412
    spec_list = []
    constraint = {"od_values": "mf157",
                  "interval_min": 0,
                  "interval_max": 0,
                  "condition": "EXCLUDE"}

    # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
    #expression_2 = expression_2 + " + " + cbd + "*(((mo29.eq.3)+(md29.eq.3)).ge.1)"
    #expression_2 = expression_2 + " + " + van + "*(((mo29.eq.4)+(md29.eq.4)).ge.1)"

    # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
    # dens: min((max((POP11o*10000)/area,0)),100)*(ifne(gyo,3)*ifne(gyo,4))
    #expression_2 = expression_2 + " + " + pop_dens + "*(((md20*10000/(md17)).min.100)*(mo29.ne.3)*(mo29.ne.4))"

    expression_2 = emp_dens + "*((((md5+md6+md7+md8+md9+md10+md11)*10000/(md17)).min.200)*(md29.ne.3)*(md29.ne.4))"
    spec_list.append(build_spec(expression_2, "mf926", constraint))

    expression_3 = van + "*((mo29.eq.4).or.(md29.eq.4))"
    #relative accessibilities: ((min(transit2,100))*ifne(cbdod,1))
    expression_3 = expression_3 + " + " + tran_acc + "*(mo392.min.100)*(mo29.ne.3)*(md29.ne.3)"
    expression_3 = expression_3 + " + " + within_gy_not_van + "*(mo29.eq.md29)*(mo29.ne.3)*((mo29.ne.4))"
    expression_3 = expression_3 + " + " + intra_van + "*((mo29.eq.4)*(md29.eq.4))"
    spec_list.append(build_spec(expression_3, "mf927", constraint))

    for i in range(1, 4):
        expression_1 = alt_spec_cons + "- 0.3*((mo29.eq.3).or.(md29.eq.3)) " \
                                       "- 0.3*((mo29.eq.4).or.(md29.eq.4))"

        if i == 1:
            expression_1 = expression_1 + " + " + zero_cars
        if i == 2:
            expression_1 = expression_1 + " + " + one_car

        # cost (all incomes) :
        expression_1 = expression_1 + " + " + cost_all_inc + "*" + rt_fare

        # all incomes: (rt_wait/3) + (rt_aux/3) + (rt_ivtb/6) +  (rt_ivtr/6) +(rt_brd*10/6)
        expression_1 = expression_1 + " + " + cost_all_inc + \
                       "*((mf154*17/60) + (mf156*17/60) + (mf152*8.5/60) + (mf153*8.5/60) + (mf155*85/60))"

        spec_list.append(build_spec(expression_1, "mf925", constraint))

        result = "mf" + str(mode_mf + i)
        emmebank.matrix(result).initialize(-9999)
        print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
        expression = "(mf925 + mf926 + mf927)"
        spec_list.append(build_spec(expression, result, constraint))
    compute_matrix(spec_list, scenario)


@_m.logbook_trace("Calculate_Bus_utility")
def calculate_bus(scenario):
    # Bus utility stored between matrices mf401-mf409
    print "--------Calculate_Bus_utility, " + str(datetime.now().strftime('%H:%M:%S'))
    emmebank = scenario.emmebank

    alt_spec_cons = str(-0.427497504543)
    zero_cars = str(2.81558891255)
    one_car = str(-0.690263477266)
    cost_all_inc = str(-0.101645666576)
    rt_fare = "mf160"
    bs_brd = "mf149"
    intra_van = str(-1.67428276794)
    cbd = str(-0.831639657818)
    van = str(-0.176246014653)
    tran_acc = str(0.144086313602)
    within_gy_not_van = str(-1.0324943983)

    mode_mf = 403
    spec_list = []
    constraint = {"od_values": "mf151",
                  "interval_min": 0,
                  "interval_max": 0,
                  "condition": "EXCLUDE"}

    # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
    expression_2 = intra_van + "*((mo29.eq.4)*(md29.eq.4))"
    # within gy (not rural):  1 if gyo=gyd and (iflt(gyo,12) and iflt(gyd,12))
    #expression_2 = expression_2 + " + " + within_gy_not_van + "*(mo29.eq.md29)*(mo29.ne.3)*((mo29.ne.4))"
    spec_list.append(build_spec(expression_2, "mf926", constraint))

    for i in range(1, 4):
        expression_1 = alt_spec_cons + "- 0.3 *((mo29.eq.3).or.(md29.eq.3)) " \
                                       "- 0.3 *((mo29.eq.4).or.(md29.eq.4))"
        if i == 1:
            expression_1 = expression_1 + " + " + zero_cars
            #+ p62*(ifeq(useveh2,1)*ifne(rurod,1))
        if i == 2:
            expression_1 = expression_1 + " + " + one_car

        # cost (all incomes) :
        expression_1 = expression_1 + " + " + cost_all_inc + "*" + rt_fare

        # all incomes: (bs_wait/3) + (bs_aux/3) + (bs_ivtb/6) + (bs_brd*10/6)
        expression_1 = expression_1 + " + " + cost_all_inc + "*((mf147*17/60) + (mf150*17/60) + (mf148*8.5/60) + (" + bs_brd + "*2.125))"
        spec_list.append(build_spec(expression_1, "mf925", constraint))

        #relative accessibilities: ((min(transit2,100))*ifne(cbdod,1)*iflt(useveh2,2))
        if i != 3:
            expression_3 = tran_acc + "*(mo392.min.100)*(mo29.ne.3)*(md29.ne.3)"
        else:
            expression_3 = "0"
            #expression_3 = expression_3 + " + " + emp_dens + "*((((md5+md6+md7+md8+md9+md10+md11)*10000/(md17)).min.200)*(mo29.ne.3)*(md29.ne.3)*(md29.ne.4))"
        # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
        expression_3 = expression_3 + " + " + cbd + "*((mo29.eq.3).or.(md29.eq.3))"
        expression_3 = expression_3 + " + " + van + "*((mo29.eq.4).or.(md29.eq.4))"
        expression_3 = expression_3 + " + " + within_gy_not_van + "*(mo29.eq.md29)*(mo29.ne.3)*(mo29.ne.4)"
        spec_list.append(build_spec(expression_3, "mf927", constraint))

        result = "mf" + str(mode_mf + i)
        emmebank.matrix(result).initialize(-9999)
        print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
        expression = "(mf925 + mf926 + mf927)"
        spec_list.append(build_spec(expression, result, constraint))
    compute_matrix(spec_list, scenario)


@_m.logbook_trace("Calculate_HOV2_utility")
def calculate_hov2(scenario):
    # HOV2 utility stored between matrices mf383-mf391
    print "--------Calculate_HOV2_utility, " + str(datetime.now().strftime('%H:%M:%S'))
    emmebank = scenario.emmebank

    alt_spec_cons = str(0.348474531589)
    zero_cars = str(0.517592113433)
    twoplus_cars = str(0.728618314326)
    cost_all_inc = str(-0.101645666576)
    au_prk = "md28"
    cbd = str(-1.83757330873)
    auto_acc = str(0.00341294833567)
    intra_van = str(-1.52580795394)
    #ret_dens = str(0.00617014015912)
    rural = str(0.580684626715)
    #within_gy = str(-0.222647811404)



    mode_mf = 385
    spec_list = []

    # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
    expression_2 = cbd + "*((mo29.eq.3).or.(md29.eq.3))"
    # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
    expression_2 = expression_2 + " + " + intra_van + "*((mo29.eq.4)*(md29.eq.4))"
    # rural : 1 if (ifgt(gyo,11) or ifgt(gyd,11))
    expression_2 = expression_2 + " + " + rural + "*(((mo29.gt.10)*(mo29.lt.15)).or.((md29.gt.10)*(md29.lt.15)))"
    spec_list.append(build_spec(expression_2, "mf926"))

    expression_3 = auto_acc + "*(mo47)"
    spec_list.append(build_spec(expression_3, "mf927"))

    for i in range(1, 4):
        expression_1 = alt_spec_cons
        if i == 1:
            expression_1 = expression_1 + " + " + zero_cars
        if i == 3:
            expression_1 = expression_1 + " + " + twoplus_cars
            #COST ALL INCOMES: (0.09*au_dst) + (1.25*au_toll) + (0.5*au_prk)
        expression_1 = expression_1 + " + " + cost_all_inc + "*((ms18*mf144/ms68) + (ms19*mf146/ms68) + (0.5*(mo28+md28)/ms68))"
        expression_1 = expression_1 + " + " + cost_all_inc + "*(mf145*8.5/60)"

        spec_list.append(build_spec(expression_1, "mf925"))

        result = "mf" + str(mode_mf + i)
        print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
        expression = "(mf925 + mf926 + mf927)"
        spec_list.append(build_spec(expression, result))
    compute_matrix(spec_list, scenario)


@_m.logbook_trace("Calculate_SOV_utility")
def calculate_sov(scenario):
    # SOV utility stored between matrices mf374-mf382
    print "--------Calculate_SOV_utility, " + str(datetime.now().strftime('%H:%M:%S'))
    emmebank = scenario.emmebank

    twoplus_cars = str(0.56109775482)
    cost_all_inc = str(-0.101645666576)
    au_prk = "md28"
    cbd = str(-2.2410813254)
    intra_van = str(-1.69551468879)
    van = str(0.124780151199)
    auto_acc = str(0.00341294833567)
    rural = str(0.580684626715)

    mode_mf = 376
    spec_list = []

    for i in range(1, 4):
        if i == 3:
            expression = twoplus_cars
        else:
            expression = "0"

        #cost all incomes: (0.18*au_dst) + (2.5*au_toll) + au_prk
        expression = expression + " + " + cost_all_inc + "*((ms18*mf144) + (ms19*mf146) + 0.5*(md28 + mo28))"

        expression = expression + " + " + cost_all_inc + "*(mf145*8.5/60)"

        # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
        expression = expression + " + " + cbd + "*((mo29.eq.3).or.(md29.eq.3))"
        expression = expression + " + " + van + "*((mo29.eq.4).or.(md29.eq.4))"
        # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
        expression = expression + " + " + intra_van + "*((mo29.eq.4)*(md29.eq.4))"

        # auto accessibilities: autoempt (i.e auto accessibilities)
        expression = expression + " + " + auto_acc + "*(mo47)"

        # rural : 1 if (ifgt(gyo,11) or ifgt(gyd,11))
        expression = expression + " + " + rural + "*(((mo29.gt.10)*(mo29.lt.15)).or.((md29.gt.10)*(md29.lt.15)))"

        result = "mf" + str(mode_mf + i)
        print result + " : " + expression
        spec_list.append(build_spec(expression, result))
    compute_matrix(spec_list, scenario)


@_m.logbook_trace("Calculate_non_home_base_other")
def calculate_blends(scenario):
    print "--------Calculate_non_home_base_other_blends, " + str(datetime.now().strftime('%H:%M:%S'))
    emmebank = scenario.emmebank

    expressions_list = [
        ['(mf110.eq.1)*(ms58+((mf115.eq.0)*(1-ms58)))', 'mf140'],
        ['1-mf140', 'mf141'],
        ['(mf121.eq.1)*(ms58+((mf129.eq.0).or.(mf130.eq.0))*(1-ms58))', 'mf142'],
        ['1-mf142', 'mf143'],
        ['mf100*ms58+mf103*(1-ms58)', 'mf144'],
        ['mf101*ms58+mf104*(1-ms58)', 'mf145'],
        ['mf102*ms58+mf105*(1-ms58)', 'mf146'],
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
@_m.logbook_trace("Time slice non-home base others")
def time_slice_non_home_base_others(scenario, data_folder):
    print "Time slicing NON-HOME BASE OTHERS trip matrices begin" + str(datetime.now().strftime('%H:%M:%S'))
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

    print "Time slicing NON-HOME BASE OTHERS matrices completed." + str(datetime.now().strftime('%H:%M:%S'))


#********
#    Module - it is identical to matrix-calculation() (rs)
#********
@_m.logbook_trace("Calculate final period demands")
def calculate_final_period_demand(scenario):
    util = _m.Modeller().tool("translink.emme.util")

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
    #    EXCEPTION - For non home base other trips,
    #                they should be assigned SOV nonWonk med&high_inc (mf847)
    #                or HOV nonWonk med&high_inc (mf852)
    #
    specs = []

    specs.append(build_spec("mf847+" + "mf798", "mf847"))
    specs.append(build_spec("mf852+" + "(mf805/" + msAutOccNhbO2Plus + ")", "mf852"))
    specs.append(build_spec("mf853+" + "mf819*mf996", "mf853"))
    specs.append(build_spec("mf854+" + "mf826*mf992", "mf854"))
    specs.append(build_spec("mf855+" + "mf833", "mf855"))
    #
    #    Midday
    #
    specs.append(build_spec("mf860+" + "mf799", "mf860"))
    specs.append(build_spec("mf865+" + "(mf806/" + msAutOccNhbO2PlusM + ")", "mf865"))
    specs.append(build_spec("mf866+" + "mf820", "mf866"))
    specs.append(build_spec("mf867+" + "mf827", "mf867"))
    specs.append(build_spec("mf868+" + "mf834", "mf868"))
    #
    #    PM peak hour
    #
    specs.append(build_spec("mf873+" + "mf800", "mf873"))
    specs.append(build_spec("mf878+" + "(mf807/" + msAutOccNhbO2Plus + ")", "mf878"))
    specs.append(build_spec("mf879+" + "mf821", "mf879"))
    specs.append(build_spec("mf880+" + "mf828", "mf880"))
    specs.append(build_spec("mf881+" + "mf835", "mf881"))

    #
    #    Accumulated demand matrices of 4 time periods by modes (auto person, bus, rail, active)
    #    mf70-mf73 : T1(before 6am and after 7pm) - auto person, bus, rail, active
    #    mf75-mf78 : T2(6am-10am) - auto person, bus, rail, active
    #    mf80-mf83 : T3(10am-2pm) - auto person, bus, rail, active
    #    mf85-mf88 : T4(2pm-7pm) - auto person, bus, rail, active
    #
    #    Auto person - 1 income levels & SOV & 2+person
    #
    specs.append(build_spec("mf70+mf794+mf801", "mf70"))
    specs.append(build_spec("mf71+mf815", "mf71"))
    specs.append(build_spec("mf72+mf822", "mf72"))
    specs.append(build_spec("mf73+mf829", "mf73"))

    specs.append(build_spec("mf75+mf795+mf802", "mf75"))
    specs.append(build_spec("mf76+mf816", "mf76"))
    specs.append(build_spec("mf77+mf823", "mf77"))
    specs.append(build_spec("mf78+mf830", "mf78"))

    specs.append(build_spec("mf80+mf796+mf803", "mf80"))
    specs.append(build_spec("mf81+mf817", "mf81"))
    specs.append(build_spec("mf82+mf824", "mf82"))
    specs.append(build_spec("mf83+mf831", "mf83"))

    specs.append(build_spec("mf85+mf797+mf804", "mf85"))
    specs.append(build_spec("mf86+mf818", "mf86"))
    specs.append(build_spec("mf87+mf825", "mf87"))
    specs.append(build_spec("mf88+mf832", "mf88"))

    compute_matrix(specs, scenario)
