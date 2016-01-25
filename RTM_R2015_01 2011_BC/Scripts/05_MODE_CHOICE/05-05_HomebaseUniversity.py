##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step5.modechoicehbuniversity
##--Purpose: HBU Mode Choice Model
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
class ModeChoiceHBUni(_m.Tool()):
    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Mode Choice Model"
        pb.description = "Not to be used directly, module containing methods to calculate mode choice model. (etc)."
        pb.branding_text = "TransLink"
        pb.runnable=False

        return pb.render()


@_m.logbook_trace("Home-base University")
def run_model(scenario, eb, iteration_number, is_last_iteration):
    data_folder = os.path.dirname(eb.path) + "\\"
    matrix_file = os.path.join(data_folder, "05_MODE_CHOICE/Inputs/NonWorkBatchin.txt")
    process_matrix_trans(matrix_file, scenario=scenario)

    calculate_blends(scenario)
    calculate_sov(scenario)
    calculate_hov2(scenario)
    calculate_hov3(scenario)
    calculate_bus(scenario)
    calculate_rail(scenario)
    calculate_walk(scenario)

    utilities.calculate_probabilities(
        scenario, nests=[[0, 1, 2], [3, 4], [5]], theta=0.915891936773)
    utilities.calculate_demand(
        scenario, demand_start=319, probability_start=441, result_start=640)

    ExportModeChoice = _m.Modeller().tool("translink.emme.stage3.step5.exportmodechoice")
    if is_last_iteration:
        purp = 5
        ExportModeChoice.Agg_Exp_Demand(eb, purp, iteration_number)

    aggregate_non_work_demand(scenario)

    #********
    #    Initialize matrices for resulted matrices - this should be done once only. (rs- will confirm with Ali the sequence)
    #********
    folder = os.path.join(data_folder, "TimeSlicingFactors")
    utilities.process_transaction_list(scenario, folder, ['dmMatInitParts'])
    time_slice_home_base_university(scenario, data_folder)
    calculate_final_period_demand(scenario)
    if is_last_iteration:
        utilities.export_matrices_report(data_folder, "Univ", range(773, 843))


## Aggregate nonwork demand in matrices mf568-mf639
@_m.logbook_trace("continue aggregating non work demand, university")
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


@_m.logbook_trace("Calculate_Walk_Utility")
def calculate_walk(scenario):
    print "--------Calculate_Walk_Utility, " + str(datetime.now().strftime('%H:%M:%S'))
    # Walk utility stored in matrices mf419-mf427
    emmebank = scenario.emmebank

    alt_spec_cons = str(0.840580230263)
    no_cars = str(0.923152584427)
    one_car = str(0.445377228725)
    sen20_wk = str(-1.33988761782)
    distance = str(-0.434431666177)
    intra_van = str(1.06664292283)
    cs_wlk_250 = str(0.831292275014)
    intrazonal = str(2.01722182977)

    mode_mf = 418
    spec_list = []
    constraint = {"od_values": "mf158",
                  "interval_min": 0,
                  "interval_max": 0,
                  "condition": "EXCLUDE"}

    #au_dst
    expression_2 = distance + "*mf144"
    # senior proportion 20+ *ifne(gyd,3)*ifne(gyo,3)*iflt(gyo,12)*iflt(gyd,12))
    expression_2 = expression_2 + " + " + sen20_wk + "*((mo19/(mo20+0.00001)).gt.(0.19999))" \
                                                     "*((mo29.ne.3)*(md29.ne.3)" \
                                                     "*(mo29.lt.12)*(md29.lt.12))"
    spec_list.append(build_spec(expression_2, "mf926", constraint))

    expression_3 = intra_van + "*((mo29.eq.4)*(md29.eq.4))"
    expression_3 = expression_3 + " + " + cs_wlk_250 + "*(((mo395+mo396).gt.0))"
    expression_3 = expression_3 + " + " + intrazonal + "*((q.eq.p))"
    spec_list.append(build_spec(expression_3, "mf927", constraint))

    for i in range(1, 10):
        expression_1 = alt_spec_cons
        if i in (1, 4, 7):
            expression_1 = expression_1 + " + " + no_cars
        if i in (2, 5, 8):
            expression_1 = expression_1 + " + " + one_car
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
    print "--------Calculate_Rail_Utility, " + str(datetime.now().strftime('%H:%M:%S'))
    emmebank = scenario.emmebank

    alt_spec_cons = str(1.97933584013)
    lo_inc = str(0.312040670114)
    van = str(0.448289983296)
    brn = str(0.635678303112)
    cost_all_inc = str(-0.209777008914)
    rt_fare = "mf161"
    cost_low_high = str(-0.209777008914)
    rt_brd = "mf155"

    mode_mf = 409
    spec_list = []
    constraint = {"od_values": "mf157",
                  "interval_min": 0,
                  "interval_max": 0,
                  "condition": "EXCLUDE"}

    # vancouver: 1 if (ifeq(gyo,4) or ifeq(gyd,4))
    expression_2 =  van + "*(((mo29.eq.4)+(md29.eq.4)).ge.1)"
    spec_list.append(build_spec(expression_2, "mf926", constraint))

    expression_3 = brn + "*(((mo29.eq.5)+(md29.eq.5)).ge.1)"
    spec_list.append(build_spec(expression_3, "mf927", constraint))

    for i in range(1, 10):
        expression_1 = alt_spec_cons + "+0.2*(((mo29.eq.4)+(md29.eq.4)).ge.1)" \
                                       "+0.2*(((mo29.eq.5)+(md29.eq.5)).ge.1)" \
                                       "+0.3*(mo29.eq.3)" \
                                       "-0.3*(((mo29.eq.7)+(md29.eq.7)).ge.1)" \
                                       "-0.3*(mo29.eq.2)"
        if i < 4:
            expression_1 = expression_1 + " + " + lo_inc

        # cost (all incomes) : rail fares for students set at 25% of adult fare
        expression_1 = expression_1 + " + " + cost_all_inc + "*(mf161*0.25)"
        # calibration factors
        expression_1 = expression_1 + " - 0.4* (((mo29.eq.2)+(md29.eq.2)).ge.1) " \
                                      " - 0.6 * (((mo29.eq.2)+(md29.eq.2)).ge.1) " \
                                      " - 0.3*(((mo29.eq.8)+(md29.eq.8)).ge.1)"
        expression_1 = expression_1 + " + 0.4* (mo29.eq.13) "

        # all incomes: (rt_wait/6) + (rt_aux/6) + (rt_ivtb/12) +  (rt_ivtr/12) +(rt_brd*(5/6))
        expression_1 = expression_1 + " + " + cost_low_high + \
                       "*((mf154/6) + (mf156/6) + (mf152/12) + ((mf153+5*(mo29.lt.3))/12) + (mf155*5/6))"
        spec_list.append(build_spec(expression_1, "mf925", constraint))


        result = "mf" + str(mode_mf + i)
        emmebank.matrix(result).initialize(-9999)
        print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
        expression = "mf925 + mf926 + mf927"
        spec_list.append(build_spec(expression, result, constraint))
    compute_matrix(spec_list, scenario)


@_m.logbook_trace("Calculate_Bus_Utility")
def calculate_bus(scenario):
    # Bus utility stored between matrices mf401-mf409
    print "--------Calculate_Bus_utility, " + str(datetime.now().strftime('%H:%M:%S'))
    emmebank = scenario.emmebank

    alt_spec_cons = str(2.12500836788)
    cost_all_inc = str(-0.209777008914)
    rt_fare = "mf160"
    cost_low_high = str(-0.209777008914)
    bs_brd = "mf149"
    intra_van = str(0.789325239640)

    mode_mf = 400
    spec_list = []
    constraint = {"od_values": "mf151",
                  "interval_min": 0,
                  "interval_max": 0,
                  "condition": "EXCLUDE"}

    # intra-vancouver
    expression_2 = intra_van + "*((mo29.eq.4)*(md29.eq.4))"
    spec_list.append(build_spec(expression_2, "mf926", constraint))

    for i in range(1, 10):
        expression_1 = alt_spec_cons + "+0.2*(mo29.eq.3)" \
                                       "-0.2*(mo29.eq.12)" \
                                       "+0.2*(mo29.eq.5)" \
                                       "-0.2*(mo29.eq.9)" \
                                       "-0.2*(((mo29.eq.7)+(md29.eq.7)).ge.1)"

        # cost (all incomes) : bus fares for students set at 25% of adult fare
        expression_1 = expression_1 + " + " + cost_all_inc + "*(mf160*0.25)"
        # all incomes: (bs_wait/6) + (bs_aux/6) + (bs_ivtb/12) + (bs_brd*1.25)
        expression_1 = expression_1 + " + " + cost_low_high + \
                       "*((mf147/6) + (mf150/6) + (mf148/12) + (" + bs_brd + "*1.25))"
        spec_list.append(build_spec(expression_1, "mf925", constraint))

        result = "mf" + str(mode_mf + i)
        emmebank.matrix(result).initialize(-9999)
        print result + " : " + expression_1 + ", " + expression_2
        expression = "mf925 + mf926"
        spec_list.append(build_spec(expression, result, constraint))
    compute_matrix(spec_list, scenario)


@_m.logbook_trace("Calculate_HOV3_Utility")
def calculate_hov3(scenario):
    # HOV3 utility stored between matrices mf392-mf400
    print "--------Calculate_HOV3_Utility, " + str(datetime.now().strftime('%H:%M:%S'))
    emmebank = scenario.emmebank

    alt_spec_cons = str(-2.87504697385)
    zero_cars = str(-1.79113388287)
    two_cars = str(0.345515241544)
    dens = str(0.00543414969914)
    cost_all_inc = str(-0.209777008914)
    au_prk = "md27"
    cost_low_high = str(-0.209777008914)
    auto_acc = str(0.0124174662558)
    rural = str(0.638310361953)
    within_gy = str(1.45211355925)

    mode_mf = 391
    spec_list = []

    # rural : 1 if (ifgt(gyo,11) or ifgt(gyd,11))
    expression_2 = rural + "*((((mo29.gt.11)*(mo29.lt.15))+((md29.gt.11)*(md29.lt.15))).ge.1)"
    # within gy (not rural):  1 if gyo=gyd and (iflt(gyo,12) and iflt(gyd,12))
    expression_2 = expression_2 + " + " + within_gy + "*(mo29.eq.md29)"
    spec_list.append(build_spec(expression_2, "mf926"))

    # dens: min((max((POP11o*10000)/area,0)),100)*(ifne(gyo,3)*ifne(gyo,4))
    expression_3 = dens + "*(((mo20)*10000/(md17)).min.200)*(mo29.ne.3)*(mo29.ne.4)"
    # auto accessibilities: autoempt (i.e auto accessibilities - PS-based)
    expression_3 = expression_3 + " + " + auto_acc + "*(mo48)"
    spec_list.append(build_spec(expression_3, "mf927"))

    for i in range(1, 10):
        expression_1 = alt_spec_cons
        if i in (1, 4, 7):
            expression_1 = expression_1 + " + " + zero_cars
        if i in (3, 6, 9):
            expression_1 = expression_1 + " + " + two_cars

        # cost all incomes:
        expression_1 = expression_1 + " + " + cost_all_inc + \
                       "*(((ms18/ms61)*mf144) + 1/ms61*(mo27/2+ md27/2) + ((ms19/ms61)*(ms146*mf146)))"
        # all incomes:
        expression_1 = expression_1 + " + " + cost_low_high + "*(mf145/12)"

        spec_list.append(build_spec(expression_1, "mf925"))

        result = "mf" + str(mode_mf + i)
        print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
        expression = "mf925 + mf926 + mf927"
        spec_list.append(build_spec(expression, result))
    compute_matrix(spec_list, scenario)


@_m.logbook_trace("Calculate_HOV2_Utility")
def calculate_hov2(scenario):
    # HOV2 utility stored between matrices mf383-mf391
    print "--------Calculate_HOV2_utility, " + str(datetime.now().strftime('%H:%M:%S'))
    emmebank = scenario.emmebank

    alt_spec_cons = str(-1.28728366115)
    zero_cars = str(-1.79113388287)
    two_cars = str(0.345515241544)
    dens = str(0.00543414969914)
    cost_all_inc = str(-0.209777008914)
    au_prk = "md27"
    cost_low_high = str(-0.209777008914)
    auto_acc = str(0.0124174662558)
    rural = str(0.777851798351)
    within_gy = str(0.962512613133)

    mode_mf = 382
    spec_list = []

    # auto accessibilities: autoempt (i.e auto accessibilities - PS-based)
    expression_2 = auto_acc + "*(mo48)"
    # rural : 1 if (ifgt(gyo,11) or ifgt(gyd,11))
    expression_2 = expression_2 + " + " + rural + "*((((mo29.gt.11)*(mo29.lt.15))+((md29.gt.11)*(md29.lt.15))).ge.1)"
    spec_list.append(build_spec(expression_2, "mf926"))

    # within gy :  1 if gyo=gyd
    expression_3 = within_gy + "*(mo29.eq.md29)"
    # dens: min((max((POP11o*10000)/area,0)),100)*(ifne(gyo,3)*ifne(gyo,4))
    expression_3 = expression_3 + " + " + dens + "*(((mo20)*10000/(mo17)).min.100)*(mo29.ne.3)*(mo29.ne.4)"
    spec_list.append(build_spec(expression_3, "mf927"))

    for i in range(1, 10):
        expression_1 = alt_spec_cons
        if i in (1, 4, 7):
            expression_1 = expression_1 + " + " + zero_cars
        if i in (3, 6, 9):
            expression_1 = expression_1 + " + " + two_cars

        #COST ALL INCOMES: (0.09*au_dst) + (1.25*au_toll)
        expression_1 = expression_1 + " + " + cost_all_inc + "*(((ms18/2)*mf144) + ((ms19/2)*(ms146*mf146)) + 0.5*(mo27/2 +md27/2))"
        # all incomes:
        expression_1 = expression_1 + " + " + cost_low_high + "*(mf145/12)"
        spec_list.append(build_spec(expression_1, "mf925"))

        result = "mf" + str(mode_mf + i)
        print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
        expression = "mf925 + mf926 + mf927"
        spec_list.append(build_spec(expression, result))
    compute_matrix(spec_list, scenario)


@_m.logbook_trace("Calculate_SOV_utility")
def calculate_sov(scenario):
    # SOV utility stored between matrices mf374-mf382
    print "--------Calculate_SOV_utility, " + str(datetime.now().strftime('%H:%M:%S'))
    emmebank = scenario.emmebank

    high_inc = str(0.294204778843)
    zero_cars = str(-1.70306793099)
    twoplus_cars = str(0.748939172882)
    cost_all_inc = str(-0.209777008914)
    au_prk = "md27"
    cost_low_high = str(-0.209777008914)
    auto_acc = str(0.0226031907957)
    cbd = str(-0.948011107861)
    rural = str(1.06184664333)
    intgy_sov = str(0.442423590074)

    mode_mf = 373
    spec_list = []

    # cbd: 1 if (ifeq(gyo,4) or ifeq(gyd,4))
    expression_2 = cbd + "*(((mo29.eq.3)+(md29.eq.3)).ge.1)"
    # auto accessibilities: autoempt (i.e auto accessibilities - PS-based)
    expression_2 = expression_2 + " + " + auto_acc + "*(mo48)"
    # rural : 1 if (ifgt(gyo,11) or ifgt(gyd,11))
    expression_2 = expression_2 + " + " + rural + "*((((mo29.ge.12)*(mo29.lt.15))+((md29.ge.12)*(md29.lt.15))).ge.1)"
    spec_list.append(build_spec(expression_2, "mf926"))

    # within gy :  1 if gyo=gyd but not Burrard
    expression_3 = intgy_sov + "*(mo29.eq.md29)*(mo29.ne.3)*(mo29.ne.4)*(mo29.ne.5)"
    spec_list.append(build_spec(expression_3, "mf927"))

    for i in range(1, 10):
        expression_1 = "0"
        # high income and (ifne(gyo,4) and ifne(gyd,4) )
        if i > 6:
            expression_1 = expression_1 + " + " + high_inc + "*(mo29.ne.4)*(md29.ne.4)"
        if i in (1, 4, 7):
            expression_1 = expression_1 + " + " + zero_cars
        if i in (3, 6, 9):
            expression_1 = expression_1 + " + " + twoplus_cars

        #cost all incomes: (0.18*au_dst) + (2.5*au_toll) + au_prk
        expression_1 = expression_1 + " + " + cost_all_inc + "*((ms18*mf144) + (ms19*(ms146*mf146)) + mo27/2 + md27/2)"
        # all incomes:
        expression_1 = expression_1 + " + " + cost_low_high + "*(mf145/12)"
        spec_list.append(build_spec(expression_1, "mf925"))

        result = "mf" + str(mode_mf + i)
        print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
        expression = "mf925 + mf926 + mf927"
        spec_list.append(build_spec(expression, result))
    compute_matrix(spec_list, scenario)


@_m.logbook_trace("Calculate_MFs_Additional_Attributes")
def calculate_blends(scenario):
    print "--------Calculate_MFs_Additional_Attributes, " + str(datetime.now().strftime('%H:%M:%S'))

    expressions_list = [
        ['(mf110.eq.1)*(ms51+((mf115.eq.0)*(1-ms51)))', 'mf140'],
        ['1-mf140', 'mf141'],
        ['(mf121.eq.1)*(ms51+(((mf129.eq.0)+(mf130.eq.0)).ge.1)*(1-ms51))', 'mf142'],
        ['1-mf142', 'mf143'],
        ['mf100*ms51+mf103*(1-ms51)', 'mf144'],
        ['mf101*ms51+mf104*(1-ms51)', 'mf145'],
        ['mf102*ms51+mf105*(1-ms51)', 'mf146'],
        ['mf106*(mf140+(mf140.eq.1)*0.10)+mf111*mf141', 'mf147'],
        ['mf107*mf140+mf112*mf141', 'mf148'],
        ['mf136*mf140+mf137*mf141', 'mf149'],
        ['mf109*mf140+mf114*mf141', 'mf150'],
        ['mf116*mf142+mf124*mf143', 'mf152'],
        ['mf117*mf142+mf125*mf143', 'mf153'],
        ['mf118*mf142+mf126*mf143', 'mf154'],
        ['mf138*mf142+mf139*mf143', 'mf155'],
        ['mf120*mf142+mf128*mf143', 'mf156'],
        ['(mf100.lt.15)', 'mf158']
    ]
    spec_list = []
    for expression, result in expressions_list:
        spec_list.append(build_spec(expression, result))
    compute_matrix(spec_list, scenario)


#********
#    ADD ON (rs)
#    Main module time slicing the matrices
#********
@_m.logbook_trace("Time slice home-base university")
def time_slice_home_base_university(scenario, data_folder):
    print "Time slicing University trip matrices begin" + str(datetime.now().strftime('%H:%M:%S'))
    #
    #    Preparing expressions for calculation
    #
    nBegSOVIncLow = 640
    nBegSOVIncMed = 643
    nBegSOVIncHigh = 646
    nBegHv2IncLow = 649
    nBegHv2IncMed = 652
    nBegHv2IncHigh = 655
    nBegHv3IncLow = 658
    nBegHv3IncMed = 661
    nBegHv3IncHigh = 664
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

    dmHv3LowInc = "("
    for nCnt1 in range(nBegHv3IncLow, nBegHv3IncLow + 2):
        dmHv3LowInc = dmHv3LowInc + "mf" + str(nCnt1) + "+"
    dmHv3LowInc = dmHv3LowInc + "mf" + str(nBegHv3IncLow + 2) + ")"

    dmHv3MedHighInc = "("
    for nCnt1 in range(nBegHv3IncMed, nBegHv3IncMed + 5):
        dmHv3MedHighInc = dmHv3MedHighInc + "mf" + str(nCnt1) + "+"
    dmHv3MedHighInc = dmHv3MedHighInc + "mf" + str(nBegHv3IncMed + 5) + ")"

    dmBus = "("
    for nCnt1 in range(nBegBusIncLow, nBegBusIncLow + 8):
        dmBus = dmBus + "mf" + str(nCnt1) + "+"
    dmBus = dmBus + "mf" + str(nBegBusIncLow + 8) + ")"

    dmRail = "("
    for nCnt1 in range(nBegRailIncLow, nBegRailIncLow + 8):
        dmRail = dmRail + "mf" + str(nCnt1) + "+"
    dmRail = dmRail + "mf" + str(nBegRailIncLow + 8) + ")"

    dmActive = "("
    for nCnt1 in range(nBegActive, nBegActive + 8):
        dmActive = dmActive + "mf" + str(nCnt1) + "+"
    dmActive = dmActive + "mf" + str(nBegActive + 8) + ")"

    arDmMatrix = [dmSOVLowInc, dmSOVMedHighInc,
                  dmHv2LowInc, dmHv2MedHighInc,
                  dmHv3LowInc, dmHv3MedHighInc,
                  dmBus, dmRail, dmActive]

    aTSFactor = [
        ['UniEscoSOVT1', 'UniEscoSOVT2', 'UniEscoSOVT3', 'UniEscoSOVT4', 'UniEscoSOVT5', 'UniEscoAutoT6',
         'UniEscoSOVT8'],
        ['UniEscoSOVT1', 'UniEscoSOVT2', 'UniEscoSOVT3', 'UniEscoSOVT4', 'UniEscoSOVT5', 'UniEscoAutoT6',
         'UniEscoSOVT8'],
        ['UniEsco2perT1', 'UniEsco2perT2', 'UniEsco2perT3', 'UniEsco2perT4', 'UniEsco2perT5', 'UniEscoAutoT6',
         'UniEsco2perT8'],
        ['UniEsco2perT1', 'UniEsco2perT2', 'UniEsco2perT3', 'UniEsco2perT4', 'UniEsco2perT5', 'UniEscoAutoT6',
         'UniEsco2perT8'],
        ['UniEsco2perT1', 'UniEsco2perT2', 'UniEsco2perT3', 'UniEsco2perT4', 'UniEsco2perT5', 'UniEscoAutoT6',
         'UniEsco2perT8'],
        ['UniEsco2perT1', 'UniEsco2perT2', 'UniEsco2perT3', 'UniEsco2perT4', 'UniEsco2perT5', 'UniEscoAutoT6',
         'UniEsco2perT8'],
        ['UniEscoTransitT1', 'UniEscoTransitT2', 'UniEscoTransitT3', 'UniEscoTransitT4', 'UniEscoTransitT5',
         'UniEscoTransitT6', 'UniEscoTransitT7'],
        ['UniEscoTransitT1', 'UniEscoTransitT2', 'UniEscoTransitT3', 'UniEscoTransitT4', 'UniEscoTransitT5',
         'UniEscoTransitT6', 'UniEscoTransitT7'],
        ['UniEscoActiveT1', 'UniEscoActiveT2', 'UniEscoActiveT3', 'UniEscoActiveT4', 'UniEscoActiveT5',
         'UniEscoActiveT6', 'UniEscoActiveT7']]

    #********
    #    Start matrix number to store the demand by TOD
    #********
    aResultMatrix = [773, 794, 780, 801, 787, 808, 815, 822, 829]
    folder = os.path.join(data_folder, "TimeSlicingFactors")

    for files, demand, result in zip(aTSFactor, arDmMatrix, aResultMatrix):
        utilities.process_transaction_list(scenario, folder, files)
        spec_list = []
        for time_period in range(0, 7):
            result_name = "mf" + str(result + time_period)
            expression = result_name + "+" + demand + "*mf" + str(703 + time_period)
            spec_list.append(build_spec(expression, result_name))
        compute_matrix(spec_list, scenario)

    print "Time slicing University matrices completed." + str(datetime.now().strftime('%H:%M:%S'))


#********
#    Module - it is identical to matrix-calculation() (rs)
#********
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
    #    For school and university trips with med/high income should be assigned to SOV-low_inc (mf846)or HOV-low_inc (mf851)
    #
    spec_list = []
    spec_list.append(build_spec("mf846+" + "mf777", "mf846"))
    spec_list.append(build_spec("mf846+" + "mf798", "mf846"))
    spec_list.append(build_spec("mf851+" + "(mf784/2)+(mf791/" + msAutOccUniv3Plus + ")", "mf851"))
    spec_list.append(build_spec("mf851+" + "(mf805/2)+(mf812/" + msAutOccUniv3Plus + ")", "mf851"))
    spec_list.append(build_spec("mf853+" + "mf819*mf996", "mf853"))
    spec_list.append(build_spec("mf854+" + "mf826*mf992", "mf854"))
    spec_list.append(build_spec("mf855+" + "mf833", "mf855"))
    #
    #    Midday
    #
    spec_list.append(build_spec("mf859+" + "mf778", "mf859"))
    spec_list.append(build_spec("mf859+" + "mf799", "mf859"))
    spec_list.append(build_spec("mf864+" + "(mf785/2)+(mf792/" + msAutOccUniv3PlusM + ")", "mf864"))
    spec_list.append(build_spec("mf864+" + "(mf806/2)+(mf813/" + msAutOccUniv3PlusM + ")", "mf864"))
    spec_list.append(build_spec("mf866+" + "mf820", "mf866"))
    spec_list.append(build_spec("mf867+" + "mf827", "mf867"))
    spec_list.append(build_spec("mf868+" + "mf834", "mf868"))
    #
    #    PM peak hour
    #
    spec_list.append(build_spec("mf872+" + "mf779", "mf872"))
    spec_list.append(build_spec("mf872+" + "mf800", "mf872"))
    spec_list.append(build_spec("mf877+" + "(mf786/2)+(mf793/" + msAutOccUniv3Plus + ")", "mf877"))
    spec_list.append(build_spec("mf877+" + "(mf807/2)+(mf814/" + msAutOccUniv3Plus + ")", "mf877"))
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
    #    Auto person - 2 income levels & SOV & 2person & 3+person
    #
    spec_list.append(build_spec("mf70+mf773+mf794+mf780+mf801+mf787+mf808", "mf70"))
    spec_list.append(build_spec("mf71+mf815", "mf71"))
    spec_list.append(build_spec("mf72+mf822", "mf72"))
    spec_list.append(build_spec("mf73+mf829", "mf73"))

    spec_list.append(build_spec("mf75+mf774+mf795+mf781+mf802+mf788+mf809", "mf75"))
    spec_list.append(build_spec("mf76+mf816", "mf76"))
    spec_list.append(build_spec("mf77+mf823", "mf77"))
    spec_list.append(build_spec("mf78+mf830", "mf78"))

    spec_list.append(build_spec("mf80+mf775+mf796+mf782+mf803+mf789+mf810", "mf80"))
    spec_list.append(build_spec("mf81+mf817", "mf81"))
    spec_list.append(build_spec("mf82+mf824", "mf82"))
    spec_list.append(build_spec("mf83+mf831", "mf83"))

    spec_list.append(build_spec("mf85+mf776+mf797+mf783+mf804+mf790+mf811", "mf85"))
    spec_list.append(build_spec("mf86+mf818", "mf86"))
    spec_list.append(build_spec("mf87+mf825", "mf87"))
    spec_list.append(build_spec("mf88+mf832", "mf88"))

    compute_matrix(spec_list, scenario)
