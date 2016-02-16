##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step5.modechoicehbpersonalbusiness
##--Purpose: HBPERBBUS Mode Choice Model
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
class ModeChoiceHBPB(_m.Tool()):
    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Mode Choice Model"
        pb.description = "Not to be used directly, module containing methods to calculate mode choice model. (etc)."
        pb.branding_text = "TransLink"
        pb.runnable = False

        return pb.render()


    @_m.logbook_trace("Home-base Personal Business")
    def run_model(self, scenario, eb, iteration_number, is_last_iteration):
        data_folder = os.path.dirname(eb.path) + "\\"
        utilities.dmMatInit_NonWork(eb)

        self.calculate_blends(scenario)
        self.calculate_sov(scenario)
        self.calculate_hov2(scenario)
        self.calculate_bus(scenario)
        self.calculate_rail(scenario)
        self.calculate_walk(scenario)
        utilities.calculate_probabilities(
            scenario, nests=[[0, 1], [3, 4], [5]], theta=0.668590582584)
        utilities.calculate_demand(
            scenario, demand_start=346, probability_start=441, result_start=640)

        ExportModeChoice = _m.Modeller().tool("translink.emme.stage3.step5.exportmodechoice")
        if is_last_iteration:
            purp = 4
            ExportModeChoice.Agg_Exp_Demand(eb, purp, iteration_number)

        self.aggregate_non_work_demand(scenario)

        # ********
        # Initialize matrices for resulted matrices - this should be done once only. (rs- will confirm with Ali the sequence)
        # ********
        utilities.dmMatInitParts(eb)
        self.time_slice_personal_business(scenario, data_folder)
        self.calculate_final_period_demand(scenario)

        if is_last_iteration:
            utilities.export_matrices_report(data_folder, "pBusi", range(773, 843))


    @_m.logbook_trace("continue aggregating non work demand, personal business")
    def aggregate_non_work_demand(self, scenario):
        spec_list = []
        matrixnum = 640
        resultmat = 568
        for i in range(0, 54):
            expression1 = "mf" + str(resultmat + i) + "+" + "mf" + str(matrixnum + i)
            result = "mf" + str(resultmat + i)
            spec_list.append(build_spec(expression1, result))
            #for i in range(54, 72):
        #    expression1 = "mf" + str(resultmat + i) + "+" + "0"
        #    result = "mf" + str(resultmat + i)
        #    spec_list.append(build_spec(expression1, result))
        compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_Walk_Utility")
    def calculate_walk(self, scenario):
        print "--------Calculate_Walk_Utility, " + str(datetime.now().strftime('%H:%M:%S'))
        # Walk utility stored in matrices mf419-mf427
        emmebank = scenario.emmebank

        alt_spec_cons = str(-0.269955290825)
        zero_cars = str(1.79155719207)
        zero_cars_br = str(1.83736582046)
        zero_cars_rur = str(2.02320737265)
        sen20_wk = str(0.436535436905)
        distance = str(-0.861507918134)
        # intra_van = str(-0.985909561561)
        cs_wlk_250 = str(0.915544970839)
        intrazonal = str(0.654142414865)

        mode_mf = 418
        spec_list = []
        constraint = {"od_values": "mf158",
                      "interval_min": 0,
                      "interval_max": 0,
                      "condition": "EXCLUDE"}

        # wlk_dens: min((emp11d*10000)/area),200)
        expression_2 = sen20_wk + "*((mo19/(mo20+0.00001)).gt.(0.19999))" \
                                  "*(((mo29.lt.3).or.(mo29.gt.5))) * (((md29 .lt. 3).or.(md29 .gt. 5)))"
        #expression_2 = expression_2 + " + " + wlk_dens + "*(((md5+md6+md7+md8+md9+md10+md11)*10000/(md17)).min.200)"
        #au_dst
        expression_2 = expression_2 + distance + "*mf144"
        spec_list.append(build_spec(expression_2, "mf926", constraint))

        expression_3 = cs_wlk_250 + "*(((mo395+mo396).gt.0))"
        # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
        #expression_3 = expression_3 + " + " + intra_van + "*((mo29.eq.4)*(md29.eq.4))"
        expression_3 = expression_3 + " + " + intrazonal + "*((q.eq.p))"
        spec_list.append(build_spec(expression_3, "mf927", constraint))

        for i in range(1, 10):
            expression_1 = alt_spec_cons
            if i in (1, 4, 7):
                expression_1 = expression_1 + " + " + zero_cars_br + \
                               "*(((mo29.eq.3)+(md29.eq.3)" \
                               "+(mo29.eq.4)+(md29.eq.4)" \
                               "+(mo29.eq.5)+(md29.eq.5)).ge.1)"
                expression_1 = expression_1 + " + " + zero_cars_rur + \
                               "*((((mo29.gt.10)*(mo29.lt.15))+((md29.gt.10)*(md29.lt.15))).ge.1)"
                expression_1 = expression_1 + " + " + zero_cars
                # rur - ifgt(gyo,10) or ifgt(gyd,10)
            spec_list.append(build_spec(expression_1, "mf925", constraint))

            result = "mf" + str(mode_mf + i)
            emmebank.matrix(result).initialize(-9999)
            print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
            expression = "mf925 + mf926 + mf927"
            spec_list.append(build_spec(expression, result, constraint))
        compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_Rail_Utility")
    def calculate_rail(self, scenario):
        # Rail utility stored between matrices mf410-mf418
        print "--------Calculate_Rail_Utility, " + str(datetime.now().strftime('%H:%M:%S'))
        emmebank = scenario.emmebank

        alt_spec_cons = str(-0.626765631797)

        high_inc = str(-0.376058555875)
        zero_cars = str(4.83722075833)
        cost_all_inc = str(-0.136002265554)
        rt_fare = "mf161"
        cost_low_inc = str(-0.136002265554)
        rt_brd = "mf155"
        cost_med_inc = str(-0.136002265554)
        cost_high_inc = str(-0.136002265554)
        bnw = str(-0.163796688846)
        rural = str(-1.33179969630)
        intra_van = str(-0.971572152619)
        tran_acc = str(0.183926615020)
        emp_dens = str(0.00428863330348)
        within_gy = str(-1.83226913261)

        mode_mf = 409
        spec_list = []
        constraint = None
        #constraint = {"od_values": "mf157",
        #              "interval_min": 0,
        #              "interval_max": 0,
        #              "condition": "EXCLUDE"}

        #relative accessibilities (auto-transit): (max(autoempt-transit2,0))
        expression_3 = tran_acc + "*((((mo392).min.100)).max.0)*(mo29.ne.3)*(md29.ne.3)"
        expression_3 = expression_3 + " + " + within_gy + "*(mo29.eq.md29)"
        spec_list.append(build_spec(expression_3, "mf927", constraint))

        for i in range(1, 10):
            #expression_1 = alt_spec_cons + "-0.25*(((mo29.eq.5)+(md29.eq.5)).ge.1)"
            expression_1 = alt_spec_cons + "-0.2*(((mo29.eq.1).or.(md29.eq.1))) " \
                                           "-0.1*(((mo29.eq.2).or.(md29.eq.2)))"

            if i == 9:
                expression_1 = expression_1 + " + " + high_inc
            if i in (1, 4, 7):
                expression_1 = expression_1 + " + " + zero_cars

            # cost (all incomes) :
            expression_1 = expression_1 + " + " + cost_all_inc + "*" + rt_fare

            # if low income: (rt_wait/3) + (rt_aux/3) + (rt_ivtb/6) +  (rt_ivtr/6) +(rt_brd*10/6)
            if i < 4:
                expression_1 = expression_1 + " + " + cost_low_inc + \
                               "*((mf154/6) + (mf156/6) + (mf152/12) + (mf153/12) + (mf155*5/6))"

            # # if med income: (rt_wait*2/3) + (rt_aux*2/3) + (rt_ivtb/3) +  (rt_ivtr/3) +(rt_brd*10/3)
            if 3 < i < 7:
                expression_1 = expression_1 + " + " + cost_med_inc + \
                               "*((mf154/3) + (mf156/3) + (mf152/6) + (mf153/6) + (mf155*10/6))"

            # # if high income: (rt_wait*2/3) + (rt_aux*2/3) + (rt_ivtb/6) +  (rt_ivtr/6) +(rt_brd*10/6)
            if i > 6:
                expression_1 = expression_1 + " + " + cost_high_inc + \
                               "*((mf154/3) + (mf156/3) + (mf152/6) + (mf153/6) + (mf155*10/6))"
            spec_list.append(build_spec(expression_1, "mf925", constraint))

            # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
            expression_2 = rural + "*(((mo29.gt.10).or.(md29.gt.10)))"
            #ifgt(gyo,10) or ifgt(gyd,10)
            expression_2 = expression_2 + " + " + emp_dens + "*(((((md5+md6+md7+md8+md9+md10+md11)*10000)/md17).max.0).min.200)" \
                                                             "*(md29.ne.3)*(md29.ne.4)"
            expression_2 = expression_2 + " + " + bnw + "*(((mo29.eq.5)+(md29.eq.5)).ge.1)"

            # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
            if 3 != i or i != 6 or i != 9:
                expression_2 = expression_2 + " + " + intra_van + "*((mo29.eq.4)*(md29.eq.4))"

            spec_list.append(build_spec(expression_2, "mf926", constraint))

            result = "mf" + str(mode_mf + i)
            #emmebank.matrix(result).initialize(-9999)
            print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
            expression = "(mf925 + mf926 + mf927) * mf157 - 9999 * (mf157.eq.0)"
            spec_list.append(build_spec(expression, result, constraint))
        compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_Bus_Utility")
    def calculate_bus(self, scenario):
        emmebank = scenario.emmebank
        # Bus utility stored between matrices mf401-mf409
        print "--------Calculate_Bus_Utility, " + str(datetime.now().strftime('%H:%M:%S'))

        alt_spec_cons = str(-2.02794061163)
        low_inc = str(0.572560379470)
        high_inc = str(-0.376058555875)
        zero_cars = str(5.06803177536)
        cost_all_inc = str(-0.136002265554)
        rt_fare = "mf160"
        cost_low_inc = str(-0.136002265554)
        bs_brd = "mf149"
        cost_med_inc = str(-0.136002265554)
        cost_high_inc = str(-0.136002265554)
        #cbd = str(1.03826642036)
        van = str(0.590266347796)
        rural = str(-1.31050147307)
        intra_van = str(-0.5)
        within_gy = str(-0.687293980540)
        #relative_acc = str(-0.0101711111056)

        mode_mf = 400
        spec_list = []
        constraint = {"od_values": "mf151",
                      "interval_min": 0,
                      "interval_max": 0,
                      "condition": "EXCLUDE"}

        # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
        #expression_2 = expression_2 + " + " + cbd + "*(((mo29.eq.3)+(md29.eq.3)).ge.1)"
        # vancouver: 1 if (ifeq(gyo,4) or ifeq(gyd,4))
        expression_2 = van + "*(((mo29.eq.4)+(md29.eq.4)).ge.1)*((mo395+mo396).gt.0)"

        # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
        expression_2 = expression_2 + " + " + intra_van + "*((mo29.eq.4)*(md29.eq.4))"
        expression_2 = expression_2 + " + " + rural + "*(((mo29.gt.11)+(md29.gt.11)).ge.1)"
        spec_list.append(build_spec(expression_2, "mf926", constraint))

        #relative accessibilities (auto-transit): (max(autoempt-transit2,0))
        #expression_3 = expression_3 + " + " + relative_acc + "*(((mo47-mo392.min.200)).max.0)"
        expression_3 = within_gy + "*(mo29.eq.md29)"
        spec_list.append(build_spec(expression_3, "mf927", constraint))

        for i in range(1, 10):
            expression_1 = alt_spec_cons + "-0.3*(((mo29.eq.2)+(md29.eq.2)).ge.1)"
            expression_1 = alt_spec_cons + "-0.2*(((mo29.eq.1)+(md29.eq.1)).ge.1) -0.1*(((mo29.eq.2)+(md29.eq.2)).ge.1)"
            if i < 4:
                expression_1 = expression_1 + " + " + low_inc
            if i > 6:
                expression_1 = expression_1 + " + " + high_inc
            if i in (1, 4, 7):
                expression_1 = expression_1 + " + " + zero_cars

            # cost (all incomes) :
            expression_1 = expression_1 + " + " + cost_all_inc + "*" + rt_fare

            # if low income: (bs_wait/3) + (bs_aux/3) + (bs_ivtb/6) + (bs_brd*10/6)
            if i < 4:
                expression_1 = expression_1 + " + " + cost_low_inc + \
                               "*((mf147/6) + (mf150/6) + (mf148/12) + (" + bs_brd + "*5/6))"

            # if med income: (bs_wait*2/3) + (bs_aux*2/3) + (bs_ivtb/3) + (bs_brd*5)
            if 3 < i < 7:
                expression_1 = expression_1 + " + " + cost_med_inc + \
                               "*((mf147/3) + (mf150/3) + (mf148/6) + (" + bs_brd + "*2.5))"

            # if high income: (bs_wait*2/3) + (bs_aux*2/3) + (bs_ivtb/3) + (bs_brd*5)
            if i > 6:
                expression_1 = expression_1 + " + " + cost_high_inc + \
                               "*((mf147/3) + (mf150/3) + (mf148/6) + (" + bs_brd + "*2.5))"
            spec_list.append(build_spec(expression_1, "mf925", constraint))

            result = "mf" + str(mode_mf + i)
            emmebank.matrix(result).initialize(-9999)
            print result + " : " + expression_1 + ", " + expression_2 + ", " + expression_3
            expression = "mf925 + mf926 + mf927"
            spec_list.append(build_spec(expression, result, constraint))
        compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_HOV2_Utility")
    def calculate_hov2(self, scenario):
        # HOV2 utility stored between matrices mf383-mf391
        print "--------Calculate_HOV2_Utility, " + str(datetime.now().strftime('%H:%M:%S'))
        emmebank = scenario.emmebank

        alt_spec_cons = str(-0.695547125211)
        low_inc = str(0.347068816842)
        #high_inc=str(-0.698808149272)
        zero_cars = str(0.865671628008)
        twoplus_cars = str(1.28299671092)
        cost_all_inc = str(-0.136002265554)
        au_prk = "md28"
        cost_low_inc = str(-0.136002265554)
        cost_med_inc = str(-0.136002265554)
        cost_high_inc = str(-0.136002265554)
        cbd = str(-2.85912122719)
        #van = str(0.233904269832)
        intra_van = str(-1.09107066606)
        auto_acc = str(0.00611891733763)
        #rural = str(0.819489034972)
        #within_gy_not_rural = str(0.569310414035)
        vanx = str(0.487912882498)

        mode_mf = 382
        spec_list = []

        # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
        expression_2 = cbd + "*(((mo29.eq.3)+(md29.eq.3)).ge.1)"
        # vancouver: 1 if (ifeq(gyo,4) or ifeq(gyd,4))
        #expression_2 = expression_2 + " + " + van + "*(((mo29.eq.4)+(md29.eq.4)).ge.1)"
        # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
        expression_2 = expression_2 + " + " + intra_van + "*((mo29.eq.4)*(md29.eq.4))"
        # rural : 1 if (ifgt(gyo,11) or ifgt(gyd,11))
        #expression_2 = expression_2 + " + " + rural + "*((((mo29.gt.11)*(mo29.lt.15))+((md29.gt.11)*(md29.lt.15))).ge.1)"
        expression_2 = expression_2 + " + " + auto_acc + "*(mo47)"
        spec_list.append(build_spec(expression_2, "mf926"))

        # within gy (not rural):  1 if gyo=gyd and (iflt(gyo,12) and iflt(gyd,12))
        #expression_3 = expression_3 + " + " + within_gy_not_rural + "*((mo29.eq.md29)*(mo29.lt.12)*(md29.lt.12))"
        expression_3 = vanx + "*2.5*(((mo29.eq.3)*(md29.eq.4) + (mo29.eq.4)*(md29.eq.3)).ge.1)"
        spec_list.append(build_spec(expression_3, "mf927"))

        for i in range(1, 10):
            expression_1 = alt_spec_cons

            if i < 4:
                expression_1 = expression_1 + " + " + low_inc
            if i == 1 or i == 4 or i == 7:
                expression_1 = expression_1 + " + " + zero_cars
            if i == 3 or i == 6 or i == 9:
                expression_1 = expression_1 + " + " + twoplus_cars

            #COST ALL INCOMES: (0.09*au_dst) + (1.25*au_toll) + (0.5*au_prk)
            expression_1 = expression_1 + " + " + cost_all_inc + "*((ms18*mf144/ms64) + (ms19*mf146/ms64) + 1/ms64*(mo28/2 + md28/2))"

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
    def calculate_sov(self, scenario):
        # SOV utility stored between matrices mf374-mf382
        print "--------Calculate_SOV_Utility, " + str(datetime.now().strftime('%H:%M:%S'))
        emmebank = scenario.emmebank

        twoplus_cars = str(1.20451543082)
        cost_all_inc = str(-0.136002265554)
        au_prk = "md27"
        cost_low_inc = str(-0.136002265554)
        cost_med_inc = str(-0.136002265554)
        cost_high_inc = str(-0.136002265554)
        cbd = str(-2.67226215547)
        intra_van = str(-1.07074365359)
        van = str(-0.116474948571)
        auto_acc = str(0.00611891733763)
        #rural = str(0.669415368781)
        vanx = str(0.487912882498)

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
            expression = expression + " + " + auto_acc + "*(mo47)"

            # rural : 1 if (ifgt(gyo,11) or ifgt(gyd,11))
            #expression = expression + " + " + rural + "*((((mo29.gt.11)*(mo29.lt.15))+((md29.gt.11)*(md29.lt.15))).ge.1)"
            expression = expression + " + " + vanx + "*(((mo29.eq.3)*(md29.eq.4) + (mo29.eq.4)*(md29.eq.3)).ge.1)"
            expression = expression + " + " + van + "*(((mo29.eq.4)+(md29.eq.4)).ge.1)"

            result = "mf" + str(mode_mf + i)
            print result + " : " + expression
            spec_list.append(build_spec(expression, result))
        compute_matrix(spec_list, scenario)

    @_m.logbook_trace("Calculate Blended Skims, personal business")
    def calculate_blends(self, scenario):
        print "--------Calculate_Home-base_PersonalBusiness_blends, " + str(datetime.now().strftime('%H:%M:%S'))

        expressions_list = [
            ['(mf110.eq.1)*(ms54+((mf115.eq.0)*(1-ms54)))', 'mf140'],
            ['1-mf140', 'mf141'],
            ['(mf121.eq.1)*(ms54+(((mf129.eq.0)+(mf130.eq.0)).ge.1)*(1-ms54))', 'mf142'],
            ['1-mf142', 'mf143'],
            ['mf100*ms54+mf103*(1-ms54)', 'mf144'],
            ['mf101*ms54+mf104*(1-ms54)', 'mf145'],
            ['mf102*ms54+mf105*(1-ms54)', 'mf146'],
            ['mf106*(mf140+(mf140.eq.1)*0.10)+mf111*mf141', 'mf147'],
            ['mf107*mf140+mf112*mf141', 'mf148'],
            ['mf136*mf140+mf137*mf141', 'mf149'],
            ['mf109*mf140+mf114*mf141', 'mf150'],
            ['mf116*mf142+mf124*mf143', 'mf152'],
            ['mf117*mf142+mf125*mf143', 'mf153'],
            ['mf118*mf142+mf126*mf143', 'mf154'],
            ['mf138*mf142+mf139*mf143', 'mf155'],
            ['mf120*mf142+mf128*mf143', 'mf156'],
            ['(mf100.lt.17.5)', 'mf158']
        ]
        spec_list = []
        for expression, result in expressions_list:
            spec_list.append(build_spec(expression, result))
        compute_matrix(spec_list, scenario)


    #********
    #    ADD ON (rs)
    #    Main module time slicing the matrices
    #********
    @_m.logbook_trace("Time slice personal business")
    def time_slice_personal_business(self, scenario, data_folder):
        print "Time slicing PERSONAL BUSINESS trip matrices begin" + str(datetime.now().strftime('%H:%M:%S'))
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
        for nCnt1 in range(nBegSOVIncLow, nBegSOVIncLow + 2): dmSOVLowInc = dmSOVLowInc + "mf" + str(nCnt1) + "+"
        dmSOVLowInc = dmSOVLowInc + "mf" + str(nBegSOVIncLow + 2) + ")"

        dmSOVMedHighInc = "("
        for nCnt1 in range(nBegSOVIncMed, nBegSOVIncMed + 5): dmSOVMedHighInc = dmSOVMedHighInc + "mf" + str(nCnt1) + "+"
        dmSOVMedHighInc = dmSOVMedHighInc + "mf" + str(nBegSOVIncMed + 5) + ")"

        dmHv2LowInc = "("
        for nCnt1 in range(nBegHv2IncLow, nBegHv2IncLow + 2): dmHv2LowInc = dmHv2LowInc + "mf" + str(nCnt1) + "+"
        dmHv2LowInc = dmHv2LowInc + "mf" + str(nBegHv2IncLow + 2) + ")"

        dmHv2MedHighInc = "("
        for nCnt1 in range(nBegHv2IncMed, nBegHv2IncMed + 5): dmHv2MedHighInc = dmHv2MedHighInc + "mf" + str(nCnt1) + "+"
        dmHv2MedHighInc = dmHv2MedHighInc + "mf" + str(nBegHv2IncMed + 5) + ")"

        # dmHv3LowInc = "("
        # for nCnt1 in range(nBegHv3IncLow,nBegHv3IncLow+2): dmHv3LowInc = dmHv3LowInc+"mf"+str(nCnt1)+"+"
        # dmHv3LowInc=dmHv3LowInc+"mf"+str(nBegHv3IncLow+2)+")"

        # dmHv3MedHighInc = "("
        # for nCnt1 in range(nBegHv3IncMed,nBegHv3IncMed+5): dmHv3MedHighInc = dmHv3MedHighInc+"mf"+str(nCnt1)+"+"
        # dmHv3MedHighInc=dmHv3MedHighInc+"mf"+str(nBegHv3IncMed+5)+")"

        dmBus = "("
        for nCnt1 in range(nBegBusIncLow, nBegBusIncLow + 8): dmBus = dmBus + "mf" + str(nCnt1) + "+"
        dmBus = dmBus + "mf" + str(nBegBusIncLow + 8) + ")"

        dmRail = "("
        for nCnt1 in range(nBegRailIncLow, nBegRailIncLow + 8): dmRail = dmRail + "mf" + str(nCnt1) + "+"
        dmRail = dmRail + "mf" + str(nBegRailIncLow + 8) + ")"

        dmActive = "("
        for nCnt1 in range(nBegActive, nBegActive + 8): dmActive = dmActive + "mf" + str(nCnt1) + "+"
        dmActive = dmActive + "mf" + str(nBegActive + 8) + ")"

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

        print "Time slicing PERSONAL BUSINESS matrices completed." + str(datetime.now().strftime('%H:%M:%S'))


    #********
    #    Module - it is identical to matrix-calculation() (rs)
    #********
    @_m.logbook_trace("Calculate final period demand")
    def calculate_final_period_demand(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")

        # KB: most of these variables are unused
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

        specs = []

        specs.append(build_spec("mf846+" + "mf777", "mf846"))
        specs.append(build_spec("mf847+" + "mf798", "mf847"))
        specs.append(build_spec("mf851+" + "(mf784/" + msAutOccPerB2Plus + ")", "mf851"))
        specs.append(build_spec("mf852+" + "(mf805/" + msAutOccPerB2Plus + ")", "mf852"))
        specs.append(build_spec("mf853+" + "mf819*mf996", "mf853"))
        specs.append(build_spec("mf854+" + "mf826*mf992", "mf854"))
        specs.append(build_spec("mf855+" + "mf833", "mf855"))
        #
        #    Midday
        #
        specs.append(build_spec("mf859+" + "mf778", "mf859"))
        specs.append(build_spec("mf860+" + "mf799", "mf860"))
        specs.append(build_spec("mf864+" + "(mf785/" + msAutOccPerB2PlusM + ")", "mf864"))
        specs.append(build_spec("mf865+" + "(mf806/" + msAutOccPerB2PlusM + ")", "mf865"))
        specs.append(build_spec("mf866+" + "mf820", "mf866"))
        specs.append(build_spec("mf867+" + "mf827", "mf867"))
        specs.append(build_spec("mf868+" + "mf834", "mf868"))
        #
        #    PM peak hour
        #
        specs.append(build_spec("mf872+" + "mf779", "mf872"))
        specs.append(build_spec("mf873+" + "mf800", "mf873"))
        specs.append(build_spec("mf877+" + "(mf786/" + msAutOccPerB2Plus + ")", "mf877"))
        specs.append(build_spec("mf878+" + "(mf807/" + msAutOccPerB2Plus + ")", "mf878"))
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
        #    Auto person - 2 income levels & SOV & 2+person
        #
        specs.append(build_spec("mf70+mf773+mf794+mf780+mf801", "mf70"))
        specs.append(build_spec("mf71+mf815", "mf71"))
        specs.append(build_spec("mf72+mf822", "mf72"))
        specs.append(build_spec("mf73+mf829", "mf73"))

        specs.append(build_spec("mf75+mf774+mf795+mf781+mf802", "mf75"))
        specs.append(build_spec("mf76+mf816", "mf76"))
        specs.append(build_spec("mf77+mf823", "mf77"))
        specs.append(build_spec("mf78+mf830", "mf78"))

        specs.append(build_spec("mf80+mf775+mf796+mf782+mf803", "mf80"))
        specs.append(build_spec("mf81+mf817", "mf81"))
        specs.append(build_spec("mf82+mf824", "mf82"))
        specs.append(build_spec("mf83+mf831", "mf83"))

        specs.append(build_spec("mf85+mf776+mf797+mf783+mf804", "mf85"))
        specs.append(build_spec("mf86+mf818", "mf86"))
        specs.append(build_spec("mf87+mf825", "mf87"))
        specs.append(build_spec("mf88+mf832", "mf88"))

        compute_matrix(specs, scenario)
