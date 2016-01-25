##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step5.modechoicehbw
##--Purpose: HBW Mode Choice Model
##---------------------------------------------------------------------
import inro.modeller as _modeller
from datetime import datetime
import traceback as _traceback
import os


process_matrix_trans = _modeller.Modeller().tool(
    "inro.emme.data.matrix.matrix_transaction")
compute_matrix = _modeller.Modeller().tool(
    "inro.emme.matrix_calculation.matrix_calculator")

utilities = _modeller.Modeller().module(
    "translink.emme.stage3.step5.utilities")
build_spec = utilities.build_spec


class ModeChoiceHBW(_modeller.Tool()):
    tool_run_msg = ""

    def page(self):
        pb = _modeller.ToolPageBuilder(self)
        pb.title = "Mode Choice Model"
        pb.description = ("Not to be used directly, module containing "
                          "methods to calculate mode choice model. (etc).")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        # TODO: add tool interface to mode choice procedure
        root_directory = os.path.dirname(_modeller.Modeller().emmebank.path) + "\\"
        scenario = _modeller.Modeller().scenario
        try:
            run_model(scenario, root_directory, 0, False)
            run_msg = "Tool completed"
            self.tool_run_msg = _modeller.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _modeller.PageBuilder.format_exception(e, _traceback.format_exc(e))


@_modeller.logbook_trace("Home-base work")
def run_model(scenario, data_folder, iteration_number, is_last_iteration):

    # TODO: the transaction deletes and recreates the matrices used in this tool
    #       this may be clearer and faster directly using the API to set the matrix
    #       names and descriptions
    matrix_file = os.path.join(data_folder, "05_MODE_CHOICE/Inputs/WorkBatchin.txt")
    process_matrix_trans(transaction_file=matrix_file, scenario=scenario)

    calculate_blends(scenario)
    calculate_sov(scenario)
    calculate_hov2(scenario)
    calculate_hov3(scenario)
    calculate_bus(scenario)
    calculate_rail(scenario)
    calculate_walk(scenario)
    calculate_bike(scenario)
    utilities.calculate_probabilities(
        scenario, nests=[[0, 1, 2], [3, 4], [5, 6]], theta=0.713222879234)
    utilities.calculate_demand(scenario,
                               demand_start=310,
                               probability_start=441,
                               result_start=505)

    if is_last_iteration:
        ExportModeChoice = _modeller.Modeller().module("translink.emme.stage3.step5.exportmodechoice")
        purp = 1
        ExportModeChoice.Agg_Exp_Demand(data_folder, purp, iteration_number)

    #********
    #    Initialize matrices for resulted matrices
    #    - this should be done once only. (rs- will confirm with Ali the sequence)
    #********
    folder = os.path.join(data_folder, "TimeSlicingFactors")
    utilities.process_transaction_list(scenario, folder, ['dmMatInit'])
    time_slice_home_base_work(data_folder, scenario)
    calculate_final_period_demand(scenario)

    # only export matrix data on the final iteration
    if is_last_iteration:
        utilities.export_matrices_report(data_folder, "work", range(710, 843))


@_modeller.logbook_trace("Calculate_Bike_utility")
def calculate_bike(scenario):
# Bike utility stored in matrices mf428-mf436
    print "--------Calculate_Bike_Utility, " + str(datetime.now().strftime('%H:%M:%S'))

    alt_spec_cons = str(-3.12234881162)
    med_inc = str(0.290849423975)
    zero_cars = str(2.37255548291)
    bkscr_bk = str(0.259554373807)
    distance = str(-0.222470615628)
    bk_invan = str(-0.512465255309)
    cs_bk_500 = str(1.29551741402)
    intrazonal = str(0.816434712579)

    mode_mf = 427

    spec_list = []

    #ifgt((BKSCRo+bkscrd),5)*(iflt(gyo,11) and iflt(gyd,11))
    #au_dst
    expression_2 = (bkscr_bk + "*((mo13+md13).gt.(5))*((mo29.lt.11)*(md29.lt.11))"
                    + distance + "*mf144")
    spec_list.append(build_spec(expression_2, "mf926"))

    # bk_invan: (ifeq(gyo,4) and ifeq(gyd,4)) + (ifeq(gyo,3) and ifeq(gyd,3))
    expression_3 = (bk_invan + "*(((mo29.eq.4)*(md29.eq.4))+((mo29.eq.3)*(md29.eq.3))) + "
                    + cs_bk_500 + "*((mo397.gt.0))"
                    + " + " + intrazonal + "*((q.eq.p))")
    spec_list.append(build_spec(expression_3, "mf927"))

    for i in range(1, 10):
        expression_1 = alt_spec_cons
        if 3 < i < 7:
            expression_1 = expression_1 + " + " + med_inc
        if i == 1 or i == 4 or i == 7:
            expression_1 = expression_1 + " + " + zero_cars

        spec_list.append(build_spec(expression_1, "mf925"))

        result = "mf" + str(mode_mf + i)
        print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
        expression = "(mf925 + mf926 + mf927)" + "*" + "mf159" + "-" + "(9999*(mf159.eq.0))"
        spec_list.append(build_spec(expression, result))

    compute_matrix(spec_list, scenario)


@_modeller.logbook_trace("Calculate_Walk_utility")
def calculate_walk(scenario):
# Walk utility stored in matrices mf419-mf427
    emmebank = scenario.emmebank
    print "--------Calculate_Walk_Utility, " + str(datetime.now().strftime('%H:%M:%S'))

    alt_spec_cons = str(1.40212378940)
    low_inc = str(0.385297511895)
    high_inc = str(-0.593371230302)
    zero_cars = str(2.49105966112)
    wlk_dens = str(0.00370213205887)
    sen20_wk = str(-0.545565473526)
    distance = str(-1.12518437298)
    intra_van = str(-0.558227923242)
    cs_wlk_250 = str(0.524423105796)
    intrazonal = str(0.539985366897)

    mode_mf = 418

    spec_list = []
    constraint = {"od_values": "mf158",
                  "interval_min": 0,
                  "interval_max": 0,
                  "condition": "EXCLUDE"}

    # wlk_dens: min((emp11d*10000)/area),200)
    #au_dst
    expression_2 = (wlk_dens + "*(((md5+md6+md7+md8+md9+md10+md11)*10000/(md17)).min.200)"
                    + " + " + sen20_wk
                    + "*((mo19/(mo20+0.00001)).gt.(0.19999))*((((mo29.lt.3)+(mo29.gt.5)).ge.1)*(mo29.lt.12))"
                    + distance + "*mf144")
    spec_list.append(build_spec(expression_2, "mf926", constraint))

    # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
    expression_3 = (intra_van + "*((mo29.eq.4)*(md29.eq.4))"
                    + " + " + cs_wlk_250 + "*(((mo395+mo396).gt.0))"
                    + " + " + intrazonal + "*((q.eq.p))")
    spec_list.append(build_spec(expression_3, "mf927", constraint))

    for i in range(1, 10):
        expression_1 = alt_spec_cons
        if i < 4:
            expression_1 = (expression_1 + " + " + low_inc
                            + "*((mo29.ne.4)*(mo29.ne.5)*(md29.ne.4)*(md29.ne.5)*(mo29.lt.11)*(md29.lt.11))")
        if i > 6:
            expression_1 = expression_1 + " + " + high_inc
        if i == 1 or i == 4 or i == 7:
            expression_1 = expression_1 + " + " + zero_cars

        spec_list.append(build_spec(expression_1, "mf925", constraint))

        result = "mf" + str(mode_mf + i)
        emmebank.matrix(result).initialize(-9999)
        print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
        expression = "mf925 + mf926 + mf927"
        spec_list.append(build_spec(expression, result, constraint))

    compute_matrix(spec_list, scenario)


@_modeller.logbook_trace("Calculate_Rail_utility")
def calculate_rail(scenario):
# Rail utility stored between matrices mf410-mf418
    emmebank = scenario.emmebank
    print "--------Calculate_Rail_Utility, " + str(datetime.now().strftime('%H:%M:%S'))
    alt_spec_cons = str(0.312309200971)
    low_inc = str(-0.256035812912)
    high_inc = str(-0.819321180333)
    zero_cars = str(3.03551309500)
    cost_all_inc = str(-0.0643808590499)
    rt_fare = "mf161"
    cost_low_inc = str(-0.0643808590499)
    rt_brd = "mf155"
    cost_med_inc = str(-0.0643808590499)
    cost_high_inc = str(-0.0643808590499)
    cbd = str(0.418286561926)
    intra_van = str(-1.81991241122)
    tran_acc = str(0.0629736554252)
    delt = str(-0.441930957460)
    nfvrd = str(1.24641214674)

    mode_mf = 409

    spec_list = []
    constraint = {"od_values": "mf157",
                  "interval_min": 0,
                  "interval_max": 0,
                  "condition": "EXCLUDE"}

    expression_2 = "0.2*(md29.eq.13)"
    # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
    expression_2 = expression_2 + " + " + cbd + "*(((mo29.eq.3)+(md29.eq.3)).ge.1)"

    # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
    expression_2 = expression_2 + " + " + intra_van + "*((mo29.eq.4)*(md29.eq.4))"
    spec_list.append(build_spec(expression_2, "mf926", constraint))

    #relative accessibilities (auto-transit): (max(autoempt-transit2,0))
    expression_3 = tran_acc + "*((((mo392).min.100)).max.0)*(mo29.ne.3)*(md29.ne.3)"
    expression_3 = expression_3 + " + " + delt + "*(((mo29.eq.8)+(md29.eq.8)).ge.1)"
    expression_3 = expression_3 + " + " + nfvrd + "*(((mo29.eq.13)+(md29.eq.13)).ge.1)"
    spec_list.append(build_spec(expression_3, "mf927", constraint))

    for i in range(1, 10):
        expression_1 = alt_spec_cons
        if i < 4:
            expression_1 = expression_1 + " + " + low_inc + "*((mo29.ne.4)*(mo29.ne.5)*(md29.ne.4)*(md29.ne.5))"
        if i > 6:
            expression_1 = expression_1 + " + " + high_inc
        if i == 1 or i == 4 or i == 7:
            expression_1 = expression_1 + " + " + zero_cars

        # cost (all incomes) with calibration factors :
        expression_1 = (expression_1 + " + " + cost_all_inc + "*" + rt_fare
                        + "-0.2*(((mo29.eq.2)+(md29.eq.2)).ge.1)"
                        + "-0.2*(((mo29.eq.7)+(md29.eq.7)).ge.1)-0.2*(md29.eq.8)")

        # if low income: (rt_wait/3) + (rt_aux/3) + (rt_ivtb/6) +  (rt_ivtr/6) +(rt_brd*10/6)
        if i < 4:
            expression_1 = (expression_1 + " + " + cost_low_inc +
                            "*((mf154/3)+((mf156+7*(mo29.lt.3)+7*(mo29.eq.7))/3)"
                            "+ ((mf152+7*(mo29.eq.7)*(md29.ne.7))/6)"
                            "+ ((mf153+7*(mo29.lt.3)+7*(mo29.eq.7)*(md29.lt.6))/6)  + (mf155*10/6))")


        # # if med income: (rt_wait*2/3) + (rt_aux*2/3) + (rt_ivtb/3) +  (rt_ivtr/3) +(rt_brd*10/3)
        if 3 < i < 7:
            expression_1 = (expression_1 + " + " + cost_med_inc +
                            "*((mf154*2/3) +((mf156+7*(mo29.lt.3))*2/3) "
                            "+ (mf152/3) + ((mf153+7*(mo29.lt.3))/3) + (mf155*10/3))")

        # # if high income: (rt_wait*2/3) + (rt_aux*2/3) + (rt_ivtb/3) +  (rt_ivtr/3) +(rt_brd*10/3)
        if i > 6:
            expression_1 = (expression_1 + " + " + cost_high_inc +
                            "*((mf154*2/3) +((mf156+7*(mo29.lt.3))*2/3) "
                            "+ (mf152/3) + ((mf153+7*(mo29.lt.3))/3) + (mf155*10/3))")

        spec_list.append(build_spec(expression_1, "mf925", constraint))

        result = "mf" + str(mode_mf + i)
        emmebank.matrix(result).initialize(-9999)
        print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
        expression = "mf925 + mf926 + mf927"
        spec_list.append(build_spec(expression, result, constraint))

    compute_matrix(spec_list, scenario)


@_modeller.logbook_trace("Calculate_Bus_utility")
def calculate_bus(scenario):
# Bus utility stored between matrices mf401-mf409
    emmebank = scenario.emmebank
    print "--------Calculate_Bus_Utility, " + str(datetime.now().strftime('%H:%M:%S'))

    alt_spec_cons = str(-1.05896691913)
    low_inc = str(0.345931413405)
    high_inc = str(-0.832896657252)
    zero_cars = str(3.30820571166)
    cost_all_inc = str(-0.0643808590499)
    rt_fare = "mf160"
    cost_low_inc = str(-0.0643808590499)
    bs_brd = "mf149"
    cost_med_inc = str(-0.0643808590499)
    cost_high_inc = str(-0.0643808590499)
    cbd = str(0.376412320791)
    van = str(0.458177040512)
    intra_van = str(-0.493281292077)
    #relative_acc = str(-0.0154768780244)

    mode_mf = 400

    spec_list = []
    constraint = {"od_values": "mf151",
                  "interval_min": 0,
                  "interval_max": 0,
                  "condition": "EXCLUDE"}

    # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
    expression_2 = cbd + "*(((mo29.eq.3)+(md29.eq.3)).ge.1)"
    # vancouver: 1 if (ifeq(gyo,4) or ifeq(gyd,4))
    expression_2 = expression_2 + " + " + van + "*(((mo29.eq.4)+(md29.eq.4)).ge.1)"
    # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
    expression_2 = expression_2 + " + " + intra_van + "*((mo29.eq.4)*(md29.eq.4))"
    spec_list.append(build_spec(expression_2, "mf926", constraint))

    #expression_3 = "0"
    #relative accessibilities (auto-transit): (max(autoempt-transit2,0))
    #expression_3 = expression_3 + " + " + relative_acc + "*((((mo47-mo392).min.100)).max.0)"
    #spec_list.append(build_spec(expression_3, "mf927", constraint))

    for i in range(1, 10):
        expression_1 = alt_spec_cons

        if i < 4:
            expression_1 = expression_1 + " + " + low_inc + "*((mo29.ne.4)*(mo29.ne.3)*(md29.ne.4)*(md29.ne.3))"
        if i > 6:
            expression_1 = expression_1 + " + " + high_inc
        if i in (1, 4, 7):
            expression_1 = expression_1 + " + " + zero_cars

        # cost (all incomes) :
        expression_1 = expression_1 + " + " + cost_all_inc + "*" + rt_fare

        # if low income: (bs_wait/3) + (bs_aux/3) + (bs_ivtb/6) + (bs_brd*10/6)
        if i < 4:
            expression_1 = (expression_1 + " + " + cost_low_inc +
                            "*((mf147/3) + ((mf150+7*(mo29.eq.7))/3) " +
                            "+ ((mf148+7*(mo29.eq.7)*(md29.lt.6))/6) + (" + bs_brd + "*10/6))")

        # if med income: (bs_wait*2/3) + (bs_aux*2/3) + (bs_ivtb/3) + (bs_brd*5)
        if 3 < i < 7:
            expression_1 = (expression_1 + " + " + cost_med_inc
                            + "*((mf147*2/3) + (mf150*2/3) + (mf148/3) + (" + bs_brd + "*5))")

        # if high income: (bs_wait*2/3) + (bs_aux*2/3) + (bs_ivtb/3) + (bs_brd*5)
        if i > 6:
            expression_1 = (expression_1 + " + " + cost_high_inc
                            + "*((mf147*2/3) + (mf150*2/3) + (mf148/3) + (" + bs_brd + "*5))")

        spec_list.append(build_spec(expression_1, "mf925", constraint))

        result = "mf" + str(mode_mf + i)
        emmebank.matrix(result).initialize(-9999)
        print result + " : " + expression_1 + ", " + expression_2 #+ ", " + expression_3
        expression = "mf925 + mf926"    #+  "+ mf927 "
        spec_list.append(build_spec(expression, result, constraint))

    compute_matrix(spec_list, scenario)


@_modeller.logbook_trace("Calculate_HOV3_utility")
def calculate_hov3(scenario):
# HOV3 utility stored between matrices mf392-mf400
    emmebank = scenario.emmebank
    print "--------Calculate_HOV3_utility, " + str(datetime.now().strftime('%H:%M:%S'))

    alt_spec_cons = str(-3.49821743739)
    low_inc = str(0.356656133368)
    high_inc = str(-0.946021806284)
    zero_cars = str(0.919177910150)
    twoplus_cars = str(1.05989036672)
    cost_all_inc = str(-0.0643808590499)
    au_prk = "md27"
    cost_low_inc = str(-0.0643808590499)
    cost_med_inc = str(-0.0643808590499)
    cost_high_inc = str(-0.0643808590499)
    cbd = str(-1.39012977492)
    van = str(0.592424443460)
    intra_van = str(-1.58037375312)
    rural = str(0.693831683879)
    within_gy_not_rural = str(0.414261997087)

    mode_mf = 391

    spec_list = []

    # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
    expression_2 = cbd + "*(((mo29.eq.3)+(md29.eq.3)).ge.1)"
    # vancouver: 1 if (ifeq(gyo,4) or ifeq(gyd,4))
    expression_2 = expression_2 + " + " + van + "*(((mo29.eq.4)+(md29.eq.4)).ge.1)"
    # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
    expression_2 = expression_2 + " + " + intra_van + "*((mo29.eq.4)*(md29.eq.4))"
    # rural : 1 if (ifgt(gyo,11) or ifgt(gyd,11))
    expression_2 = expression_2 + " + " + rural + "*((((mo29.gt.11)*(mo29.lt.15))+((md29.gt.11)*(md29.lt.15))).ge.1)"
    spec_list.append(build_spec(expression_2, "mf926"))

    # within gy (not rural):  1 if gyo=gyd and (iflt(gyo,12) and iflt(gyd,12))
    expression_3 = within_gy_not_rural + "*((mo29.eq.md29)*(mo29.lt.12)*(md29.lt.12))"
    spec_list.append(build_spec(expression_3, "mf927"))

    for i in range(1, 10):
        expression_1 = alt_spec_cons

        if i < 4:
            expression_1 = expression_1 + " + " + low_inc
        if i > 6:
            expression_1 = expression_1 + " + " + high_inc
        if i in (1, 4, 7):
            expression_1 = expression_1 + " + " + zero_cars
        if i in (3, 6, 9):
            expression_1 = expression_1 + " + " + twoplus_cars

        #COST ALL INCOMES: (0.0521*au_dst)+ (0.7235*au_toll) + (0.2894*au_prk)
        expression_1 = (expression_1 + " + " + cost_all_inc
                        + "*(((ms18/ms60)*mf144) + ((ms19/ms60)*(ms146*mf146)) + (1/ms60*(md27/2+mo27/2)))")

        if i < 4:
            expression_1 = expression_1 + " + " + cost_low_inc + "*(mf145/6)"
        if 3 < i < 7:
            expression_1 = expression_1 + " + " + cost_med_inc + "*(mf145/3)"
        if i > 6: expression_1 = \
            expression_1 + " + " + cost_high_inc + "*(mf145/3)"

        spec_list.append(build_spec(expression_1, "mf925"))

        result = "mf" + str(mode_mf + i)
        print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
        expression = "mf925 + mf926 + mf927"
        spec_list.append(build_spec(expression, result))

    compute_matrix(spec_list, scenario)


@_modeller.logbook_trace("Calculate_HOV2_utlity")
def calculate_hov2(scenario):
# HOV2 utility stored between matrices mf383-mf391
    print "--------Calculate_HOV2_utility, " + str(datetime.now().strftime('%H:%M:%S'))

    alt_spec_cons = str(-1.93452982905)
    low_inc = str(0.356656133368)
    high_inc = str(-0.651530442559)
    zero_cars = str(0.555800640604)
    twoplus_cars = str(1.05989036672)
    cost_all_inc = str(-0.0643808590499)
    au_prk = "md27"
    cost_low_inc = str(-0.0643808590499)
    cost_med_inc = str(-0.0643808590499)
    cost_high_inc = str(-0.0643808590499)
    cbd = str(-1.34063580368)
    van = str(0.302180076985)
    intra_van = str(-1.44394055862)
    rural = str(0.693831683879)
    within_gy_not_rural = str(0.594288895855)

    mode_mf = 382

    spec_list = []
    # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
    expression_2 = cbd + "*(((mo29.eq.3)+(md29.eq.3)).ge.1)"
    # vancouver: 1 if (ifeq(gyo,4) or ifeq(gyd,4))
    expression_2 = expression_2 + " + " + van + "*(((mo29.eq.4)+(md29.eq.4)).ge.1)"
    # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
    expression_2 = expression_2 + " + " + intra_van + "*((mo29.eq.4)*(md29.eq.4))"
    # rural : 1 if (ifgt(gyo,11) or ifgt(gyd,11))
    expression_2 = expression_2 + " + " + rural + "*((((mo29.gt.11)*(mo29.lt.15))+((md29.gt.11)*(md29.lt.15))).ge.1)"
    spec_list.append(build_spec(expression_2, "mf926"))

    # within gy (not rural):  1 if gyo=gyd and (iflt(gyo,12) and iflt(gyd,12))
    expression_3 = within_gy_not_rural + "*((mo29.eq.md29)*(mo29.lt.12)*(md29.lt.12))"
    spec_list.append(build_spec(expression_3, "mf927"))

    for i in range(1, 10):
        expression_1 = alt_spec_cons

        if i < 4:
            expression_1 = expression_1 + " + " + low_inc
        if i > 6:
            expression_1 = expression_1 + " + " + high_inc
        if i in (1, 4, 7):
            expression_1 = expression_1 + " + " + zero_cars
        if i in (3, 6, 9):
            expression_1 = expression_1 + " + " + twoplus_cars

        #COST ALL INCOMES: (0.09*au_dst) + (1.25*au_toll) + (0.5*au_prk)
        expression_1 = (expression_1 + " + " + cost_all_inc
                        + "*((ms18*mf144/2) + (ms19*(ms146*mf146)/2) + (0.5*(md27/2+mo27/2)))")

        if i < 4:
            expression_1 = expression_1 + " + " + cost_low_inc + "*(mf145/6)"
        if 3 < i < 7:
            expression_1 = expression_1 + " + " + cost_med_inc + "*(mf145/3)"
        if i > 6:
            expression_1 = expression_1 + " + " + cost_high_inc + "*(mf145/3)"

        spec_list.append(build_spec(expression_1, "mf925"))

        result = "mf" + str(mode_mf + i)
        print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
        expression = "mf925 + mf926 + mf927"
        spec_list.append(build_spec(expression, result))

    compute_matrix(spec_list, scenario)


@_modeller.logbook_trace("Calculate_SOV_utility")
def calculate_sov(scenario):
# SOV utility stored between matrices mf374-mf382
    print "--------Calculate_SOV_Utility, " + str(datetime.now().strftime('%H:%M:%S'))

    high_inc = str(-0.613941251950)
    twoplus_cars = str(1.55180600932)
    cost_all_inc = str(-0.0643808590499)
    au_prk = "md27"
    cost_low_inc = str(-0.0643808590499)
    cost_med_inc = str(-0.0643808590499)
    cost_high_inc = str(-0.0643808590499)
    cbd = str(-2.20528861762)
    intra_van = str(-1.29840612094)
    auto_acc = str(0.00829908545924)
    rural = str(0.554132781574)

    mode_mf = 373

    spec_list = []
    for i in range(1, 10):
        expression = "0"

        if i > 6: expression = expression + " + " + high_inc
        if (i == 3 or i == 6 or i == 9): expression = expression + " + " + twoplus_cars

        #cost all incomes: (0.18*au_dst) + (2.5*au_toll) + au_prk
        expression = expression + " + " + cost_all_inc + "*((ms18*mf144) + (ms19*(ms146*mf146)) + mo27/2 + md27/2)"

        if i < 4: expression = expression + " + " + cost_low_inc + "*(mf145/6)"
        if (i > 3 and i < 7): expression = expression + " + " + cost_med_inc + "*(mf145/3)"
        if i > 6: expression = expression + " + " + cost_high_inc + "*(mf145/3)" + "+0.2*(mo29.eq.9)"

        # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
        expression = expression + " + " + cbd + "*(((mo29.eq.3)+(md29.eq.3)).ge.1)"

        # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
        expression = expression + " + " + intra_van + "*((mo29.eq.4)*(md29.eq.4))"

        # auto accessibilities: autoempt (i.e auto accessibilities)
        expression = expression + " + " + auto_acc + "*(mo47)"

        # rural : 1 if (ifgt(gyo,11) or ifgt(gyd,11))
        expression = expression + " + " + rural + "*((((mo29.ge.12)*(mo29.lt.15))+((md29.ge.12)*(md29.lt.15))).ge.1)"

        result = "mf" + str(mode_mf + i)
        print result + " : " + expression
        spec_list.append(build_spec(expression, result))

    compute_matrix(spec_list, scenario)


@_modeller.logbook_trace("Calculate home-base work blend skims")
def calculate_blends(scenario):
    print "--------Calculate_Home-base_Work_blends, " + str(datetime.now().strftime('%H:%M:%S'))
    expressions_list = [
        ['(mf110.eq.1)*(ms50+((mf115.eq.0)*(1-ms50)))', 'mf140'],
        ['1-mf140', 'mf141'],
        ['(mf121.eq.1)*(ms50+(((mf129.eq.0)+(mf130.eq.0)).ge.1)*(1-ms50))', 'mf142'],
        ['1-mf142', 'mf143'],
        ['mf100*ms50+mf103*(1-ms50)', 'mf144'],
        ['mf101*ms50+mf104*(1-ms50)', 'mf145'],
        ['mf102*ms50+mf105*(1-ms50)', 'mf146'],
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
@_modeller.logbook_trace("Time slicing home-base work")
def time_slice_home_base_work(data_folder, scenario):
    print "Time slicing HBW matrices begins" + str(datetime.now().strftime('%H:%M:%S'))

    file_name = os.path.join(data_folder, "TimeSlicingFactors", 'dmMatInit.311')
    process_matrix_trans(file_name, scenario=scenario)

    #
    #    Preparing expressions for calculation
    #
    nBegSOVIncLow = 505
    nBegSOVIncMed = 508
    nBegSOVIncHigh = 511
    nBegHv2IncLow = 514
    nBegHv2IncMed = 517
    nBegHv2IncHigh = 520
    nBegHv3IncLow = 523
    nBegHv3IncMed = 526
    nBegHv3IncHigh = 529
    nBegBusIncLow = 532
    nBegBusIncMed = 535
    nBegBusIncHigh = 538
    nBegRailIncLow = 541
    nBegRailIncMed = 544
    nBegRailIncHigh = 547
    nBegActive = 550

    dmSOVIncLow = "(mf" + str(nBegSOVIncLow) + "+mf" + str(nBegSOVIncLow + 1) + "+mf" + str(nBegSOVIncLow + 2) + ")"
    dmSOVIncMed = "(mf" + str(nBegSOVIncMed) + "+mf" + str(nBegSOVIncMed + 1) + "+mf" + str(nBegSOVIncMed + 2) + ")"
    dmSOVIncHigh = "(mf" + str(nBegSOVIncHigh) + "+mf" + str(nBegSOVIncHigh + 1) + "+mf" + str(nBegSOVIncHigh + 2) + ")"
    dmHv2IncLow = "(mf" + str(nBegHv2IncLow) + "+mf" + str(nBegHv2IncLow + 1) + "+mf" + str(nBegHv2IncLow + 2) + ")"
    dmHv2IncMed = "(mf" + str(nBegHv2IncMed) + "+mf" + str(nBegHv2IncMed + 1) + "+mf" + str(nBegHv2IncMed + 2) + ")"
    dmHv2IncHigh = "(mf" + str(nBegHv2IncHigh) + "+mf" + str(nBegHv2IncHigh + 1) + "+mf" + str(nBegHv2IncHigh + 2) + ")"
    dmHv3IncLow = "(mf" + str(nBegHv3IncLow) + "+mf" + str(nBegHv3IncLow + 1) + "+mf" + str(nBegHv3IncLow + 2) + ")"
    dmHv3IncMed = "(mf" + str(nBegHv3IncMed) + "+mf" + str(nBegHv3IncMed + 1) + "+mf" + str(nBegHv3IncMed + 2) + ")"
    dmHv3IncHigh = "(mf" + str(nBegHv3IncHigh) + "+mf" + str(nBegHv3IncHigh + 1) + "+mf" + str(nBegHv3IncHigh + 2) + ")"

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

    arDmMatrix = [dmSOVIncLow, dmSOVIncMed, dmSOVIncHigh,
                  dmHv2IncLow, dmHv2IncMed, dmHv2IncHigh,
                  dmHv3IncLow, dmHv3IncMed, dmHv3IncHigh,
                  dmBus, dmRail, dmActive]

    # for nCnt1 in range(0,6): print arDmMatrix[nCnt1]
    #
    #    PM peak hour TSF was generated by Delcan. T7 Active mode was prepared at TransLink.
    #    SOV and 2-per by income range,
    #
    arFileName = [
        ['wkSOV1T1', 'wkSOV1T2', 'wkSOV1T3', 'wkSOV1T4', 'wkSOV1T5', 'wkAutoT6', 'wkSOV1T8'],
        ['wkSOV2T1', 'wkSOV2T2', 'wkSOV2T3', 'wkSOV2T4', 'wkSOV2T5', 'wkAutoT6', 'wkSOV2T8'],
        ['wkSOV3T1', 'wkSOV3T2', 'wkSOV3T3', 'wkSOV3T4', 'wkSOV3T5', 'wkAutoT6', 'wkSOV3T8'],
        ['wk2perT1', 'wk2perT2', 'wk2perT3', 'wk2perT4', 'wk2perT5', 'wkAutoT6', 'wk2perT8'],
        ['wk2perT1', 'wk2perT2', 'wk2perT3', 'wk2perT4', 'wk2perT5', 'wkAutoT6', 'wk2perT8'],
        ['wk2perT1', 'wk2perT2', 'wk2perT3', 'wk2perT4', 'wk2perT5', 'wkAutoT6', 'wk2perT8'],
        ['wk2perT1', 'wk2perT2', 'wk2perT3', 'wk2perT4', 'wk2perT5', 'wkAutoT6', 'wk2perT8'],
        ['wk2perT1', 'wk2perT2', 'wk2perT3', 'wk2perT4', 'wk2perT5', 'wkAutoT6', 'wk2perT8'],
        ['wk2perT1', 'wk2perT2', 'wk2perT3', 'wk2perT4', 'wk2perT5', 'wkAutoT6', 'wk2perT8'],
        ['wkTransitT1', 'wkTrnBusT2', 'wkTransitT3', 'wkTrnBusT4', 'wkTrnBusT5', 'wkTransitT6', 'wkTrnBusT8'],
        ['wkTransitT1', 'wkRailT2', 'wkTransitT3', 'wkRailT4', 'wkRailT5', 'wkTransitT6', 'wkRailT8'],
        ['wkActiveT1', 'wkActiveT2', 'wkActiveT3', 'wkActiveT4', 'wkActiveT5', 'wkActiveT6', 'wkActiveT7'],
    ]
    #********
    #    Start matrix number to store the demand by TOD
    #********
    arResultMatrix = [710, 717, 724, 731, 738, 745, 752, 759, 766, 815, 822, 829]
    folder = os.path.join(data_folder, "TimeSlicingFactors")

    for files, demand, result in zip(arFileName, arDmMatrix, arResultMatrix):
        utilities.process_transaction_list(scenario, folder, files)
        #    Range was increased to 7 from 6 time period
        spec_list = []
        for time_period in range(0, 7):
            result_name = "mf" + str(result + time_period)
            expression = result_name + "+" + demand + "*mf" + str(703 + time_period)
            spec_list.append(build_spec(expression, result_name))
        compute_matrix(spec_list, scenario)

    print "Time slicing HBW matrices completed." + str(datetime.now().strftime('%H:%M:%S'))


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
    #    Generate AM peak hour demand
    #
    spec_list = []
    spec_list.append(build_spec("mf714", "mf843"))
    spec_list.append(build_spec("mf721", "mf844"))
    spec_list.append(build_spec("mf728", "mf845"))
    spec_list.append(build_spec("(mf735/2)+(mf756/" + msAutOccWork3Plus + ")", "mf848"))
    spec_list.append(build_spec("(mf742/2)+(mf763/" + msAutOccWork3Plus + ")", "mf849"))
    spec_list.append(build_spec("(mf749/2)+(mf770/" + msAutOccWork3Plus + ")", "mf850"))
    spec_list.append(build_spec("mf819", "mf853"))
    spec_list.append(build_spec("mf826", "mf854"))
    spec_list.append(build_spec("mf833", "mf855"))

    # Track work transit demand separately for park and ride model
    spec_list.append(build_spec("mf819", "mf998"))
    spec_list.append(build_spec("mf826", "mf997"))
    #
    #     Generate midday hour demand
    #
    spec_list.append(build_spec("mf715", "mf856"))
    spec_list.append(build_spec("mf722", "mf857"))
    spec_list.append(build_spec("mf729", "mf858"))
    spec_list.append(build_spec("(mf736/2)+(mf757/" + msAutOccWork3PlusM + ")", "mf861"))
    spec_list.append(build_spec("(mf743/2)+(mf764/" + msAutOccWork3PlusM + ")", "mf862"))
    spec_list.append(build_spec("(mf750/2)+(mf771/" + msAutOccWork3PlusM + ")", "mf863"))
    spec_list.append(build_spec("mf820", "mf866"))
    spec_list.append(build_spec("mf827", "mf867"))
    spec_list.append(build_spec("mf834", "mf868"))
    #
    #     Generate PM peak hour demand
    #
    spec_list.append(build_spec("mf716", "mf869"))
    spec_list.append(build_spec("mf723", "mf870"))
    spec_list.append(build_spec("mf730", "mf871"))
    spec_list.append(build_spec("(mf737/2)+(mf758/" + msAutOccWork3Plus + ")", "mf874"))
    spec_list.append(build_spec("(mf744/2)+(mf765/" + msAutOccWork3Plus + ")", "mf875"))
    spec_list.append(build_spec("(mf751/2)+(mf772/" + msAutOccWork3Plus + ")", "mf876"))
    spec_list.append(build_spec("mf821", "mf879"))
    spec_list.append(build_spec("mf828", "mf880"))
    spec_list.append(build_spec("mf835", "mf881"))
    #
    #    Accumulated demand matrices of 4 time periods by modes (auto person, bus, rail, active)
    #    mf70-mf73 : T1(before 6am and after 7pm) - auto person, bus, rail, active
    #    mf75-mf78 : T2(6am-10am) - auto person, bus, rail, active
    #    mf80-mf83 : T3(10am-2pm) - auto person, bus, rail, active
    #    mf85-mf88 : T4(2pm-7pm) - auto person, bus, rail, active
    #
    spec_list.append(build_spec("mf710+mf717+mf724+mf731+mf738+mf745+mf752+mf759+mf766", "mf70"))
    spec_list.append(build_spec("mf815*mf928", "mf71"))
    spec_list.append(build_spec("mf822*mf975", "mf72"))
    spec_list.append(build_spec("mf829", "mf73"))

    spec_list.append(build_spec("mf711+mf718+mf725+mf732+mf739+mf746+mf753+mf760+mf767", "mf75"))
    spec_list.append(build_spec("mf816", "mf76"))
    spec_list.append(build_spec("mf823", "mf77"))
    spec_list.append(build_spec("mf830", "mf78"))

    spec_list.append(build_spec("mf712+mf719+mf726+mf733+mf740+mf747+mf754+mf761+mf768", "mf80"))
    spec_list.append(build_spec("mf817*mf929", "mf81"))
    spec_list.append(build_spec("mf824*mf976", "mf82"))
    spec_list.append(build_spec("mf831", "mf83"))

    spec_list.append(build_spec("mf713+mf720+mf727+mf734+mf741+mf748+mf755+mf762+mf769", "mf85"))
    spec_list.append(build_spec("mf818", "mf86"))
    spec_list.append(build_spec("mf825", "mf87"))
    spec_list.append(build_spec("mf832", "mf88"))

    compute_matrix(spec_list, scenario)
