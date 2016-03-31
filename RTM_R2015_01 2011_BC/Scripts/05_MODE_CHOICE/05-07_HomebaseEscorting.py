##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step5.modechoicehbesc
##--Purpose: HBescorting Mode Choice Model
##---------------------------------------------------------------------
import inro.modeller as _m

utilities = _m.Modeller().module("translink.emme.stage3.step5.utilities")
build_spec = utilities.build_spec

# TODO: add tool interface to mode choice procedure
class ModeChoiceHBEsc(_m.Tool()):
    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Mode Choice Model"
        pb.description = "Not to be used directly, module containing methods to calculate mode choice model. (etc)."
        pb.branding_text = "TransLink"
        pb.runnable = False

        return pb.render()


    @_m.logbook_trace("Home-base Escorting")
    def __call__(self, eb, scenario, is_last_iteration):
        utilities.dmMatInit_NonWork(eb)

        self.calculate_blends(scenario)
        self.calculate_sov(scenario)
        self.calculate_hov2(scenario)
        self.calculate_bus(scenario)
        self.calculate_rail(scenario)
        self.calculate_walk(scenario)

        utilities.calculate_probabilities(
            scenario, nests=[[0, 1], [3, 4], [5]], theta=0.75)
        # demand matrices are stored in matrices mf 640-702
        utilities.calculate_demand(
            scenario, demand_start=364, probability_start=441, result_start=640)

        ExportModeChoice = _m.Modeller().tool("translink.emme.stage3.step5.exportmodechoice")
        if is_last_iteration:
            purp = 7
            ExportModeChoice.Agg_Exp_Demand(eb, purp)

        self.aggregate_non_work_demand(scenario)

        #********
        #    Initialize matrices for resulted matrices - this should be done once only. (rs- will confirm with Ali the sequence)
        #********
        utilities.dmMatInitParts(eb)
        self.time_slice_escorting(eb, scenario)
        self.calculate_final_period_demand(scenario)
#        if is_last_iteration:
#            utilities.export_matrices_report(eb, "esco", range(773, 843))


    @_m.logbook_trace("continue aggregating non work demand, escorting")
    def aggregate_non_work_demand(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")
        spec_list = []
        matrixnum = 640
        resultmat = 568
        for i in range(0, 54):
            expression = "mf" + str(resultmat + i) + "+" + "mf" + str(matrixnum + i)
            result = "mf" + str(resultmat + i)
            spec_list.append(util.matrix_spec(result, expression))
            #for i in range(54, 72):
        #    expression = "mf" + str(resultmat + i) + "+" + "0"
        #    spec_list.append(util.matrix_spec(result, expression))
        util.compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_Walk_utility")
    def calculate_walk(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")
        # Walk utility stored in matrices mf419-mf427

        alt_spec_cons = str(0.0868032781316)
        #low_inc = str(0.257877368791)
        zero_cars_burr = str(1.20153595959)
        two_car_burr = str(-0.406327023170)
        two_car_rur = str(-0.265161293626)

        sen20_wk = str(-0.50655596837)

        distance = str(-0.808065976972)
        #vanx = str(-1.18476492179)
        #ret_dens = str(0.0151755535868)
        #van_locar = str(0.265095647661)
        van = str(-2.80995179012)
        cs_wlk_500 = str(1.01271905833)
        intrazonal = str(1.66402854747)

        mode_mf = 418
        spec_list = []
        constraint = {"od_values": "mf158",
                      "interval_min": 0,
                      "interval_max": 0,
                      "condition": "EXCLUDE"}

        expression_2 = sen20_wk + "*((mo19/(mo20+0.00001)).gt.(0.19999))"
        #au_dst
        expression_2 = expression_2 + distance + "*mf144"
        spec_list.append(build_spec(expression_2, "mf926", constraint))

        expression_3 = van + "*(((gy(p).eq.4).or.(gy(q).eq.4)))"
        expression_3 = expression_3 + " + " + cs_wlk_500 + "*((mo394.gt.1))"
        expression_3 = expression_3 + " + " + intrazonal + "*((q.eq.p))"
        spec_list.append(build_spec(expression_3, "mf927", constraint))

        for i in range(1, 10):
            expression_1 = alt_spec_cons + "+0.2*(((gy(p).eq.2).or.(gy(q).eq.2)))" \
                                           "+0.2*(((gy(p).eq.5).or.(gy(q).eq.5)))" \
                                           "+0.2*(((gy(p).eq.7).or.(gy(q).eq.7)))" \
                                           "+0.2*(((gy(p).eq.9).or.(gy(q).eq.9)))"
            #if i<4: expression_1 = expression_1 + " + " + low_inc + "*((gy(p).ne.3)*(gy(q).ne.3)*(gy(p).lt.12)*(gy(q).lt.12))"
            if i in (4, 7):
                expression_1 = expression_1 + " + " + zero_cars_burr + \
                               "*(((gy(p).eq.3)+(gy(q).eq.3)+(gy(p).eq.4)+(gy(q).eq.4)+(gy(p).eq.5)+(gy(q).eq.5)).ge.1)"
            if i in (3, 6, 9):
                expression_1 = expression_1 + " + " + two_car_burr + \
                               "*(((gy(p).eq.3)+(gy(q).eq.3)+(gy(p).eq.4)+(gy(q).eq.4)+(gy(p).eq.5)+(gy(q).eq.5)).ge.1)"
                expression_1 = expression_1 + " + " + two_car_rur + \
                               "*(((gy(p).gt.10).or.(gy(q).gt.10)))"
                #1 (if cars = 2/3) * ifne(gyo,5)*ifne(gyd,5)* ifne(gyo,3)*ifne(gyd,3)* ifne(gyo,4)*ifne(gyd,4)

            spec_list.append(build_spec(expression_1, "mf925", constraint))

            result = "mf" + str(mode_mf + i)
            spec_list.append(util.matrix_spec(result, "-9999"))
            expression = "(mf925 + mf926 + mf927)"
            spec_list.append(build_spec(expression, result, constraint))
        util.compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_Rail_utility")
    def calculate_rail(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")
        # Rail utility stored between matrices mf410-mf418

        alt_spec_cons = str(-4.67171026411)
        #high_inc = str(-0.893515916582)
        zero_cars = str(2.6410762452)

        #nhi_intrv = str(-0.975916772497)
        cost_all_inc = str(-0.0353037544584)
        rt_fare = "mf161"
        cost_low_inc = str(-0.0353037544584)
        rt_brd = "mf155"
        cost_med_inc = str(-0.0353037544584)
        cost_high_inc = str(-0.0353037544584)

        #cbd = str(0.388989683459)
        intra_van = str(-3.28888407533)
        tran_acc = str(0.263893110819)
        #within_gy_not_van = str(-1.27379087945)
        #rur_locar = str(-1.64295784992)


        mode_mf = 409
        spec_list = []
        constraint = {"od_values": "mf157",
                      "interval_min": 0,
                      "interval_max": 0,
                      "condition": "EXCLUDE"}

        # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
        #expression_2 = expression_2 + " + " + cbd + "*(((gy(p).eq.3)+(gy(q).eq.3)).ge.1)"

        # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
        expression_2 = intra_van + "*((gy(p).eq.4)*(gy(q).eq.4))"
        spec_list.append(build_spec(expression_2, "mf926", constraint))
        # dens: min((max((POP11o*10000)/area,0)),100)*(ifne(gyo,3)*ifne(gyo,4))

        #relative accessibilities (auto-transit): (max(autoempt-transit2,0))
        expression_3 = tran_acc + "*mo392"
        spec_list.append(build_spec(expression_3, "mf927", constraint))

        for i in range(1, 10):
            expression_1 = alt_spec_cons
            #if i>6: expression_1 = expression_1 + " + " + high_inc
            #if i<7: expression_1 = expression_1 + " + " + nhi_intrv + "*((gy(p).eq.4)*(gy(q).eq.4))"
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

            result = "mf" + str(mode_mf + i)
            spec_list.append(util.matrix_spec(result, "-9999"))
            expression = "mf925 + mf926 + mf927"
            spec_list.append(build_spec(expression, result, constraint))
        util.compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_Bus_utlity")
    def calculate_bus(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")
        # Bus utility stored between matrices mf401-mf409

        alt_spec_cons = str(-6.58474918593)

        lo_inc = str(1.53494141797)
        zero_cars = str(2.65268997372)

        cost_all_inc = str(-0.0353037544584)
        rt_fare = "mf160"
        cost_low_inc = str(-0.0353037544584)
        bs_brd = "mf149"
        cost_med_inc = str(-0.0353037544584)
        cost_high_inc = str(-0.0353037544584)
        pop_dens = str(0.0187395661137)

        intra_van = str(-2.5540464046)

        tran_acc = str(0.28330221292)
        #rural = str(-1.10355944177)
        #within_gy_not_van = str(-0.776829172883)

        mode_mf = 400
        spec_list = []
        constraint = {"od_values": "mf151",
                      "interval_min": 0,
                      "interval_max": 0,
                      "condition": "EXCLUDE"}

        # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
        #expression_2 = expression_2 + " + " + cbd + "*(((gy(p).eq.3)+(gy(q).eq.3)).ge.1)"

        # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
        expression_2 = intra_van + "*((gy(p).eq.4)*(gy(q).eq.4))"
        expression_2 = expression_2 + " + " + pop_dens + "*(((mo20*10000/(mo17+0.000001*(p.le.130))).min.100)*(gy(p).ne.3)*(gy(p).ne.4))"
        spec_list.append(build_spec(expression_2, "mf926", constraint))

        #relative accessibilities (auto-transit): (max(autoempt-transit2,0))
        expression_3 = tran_acc + "*mo392"
        spec_list.append(build_spec(expression_3, "mf927", constraint))

        for i in range(1, 10):
            expression_1 = alt_spec_cons

            if i < 4:
                expression_1 = expression_1 + " + " + lo_inc
            if i in (1, 4, 7):
                expression_1 = expression_1 + " + " + zero_cars

            # cost (all incomes) :
            expression_1 = expression_1 + " + " + cost_all_inc + "*" + rt_fare

            # if low income: (bs_wait/3) + (bs_aux/3) + (bs_ivtb/6) + (bs_brd*10/6)
            if i < 4:
                expression_1 = expression_1 + " + " + cost_low_inc + \
                               "*((mf147/6) + (mf150/6) + (mf148/12) + (" + bs_brd + "*5/6))"

            # if med income: (bs_wait*2/3) + (bs_aux*2/3) + (bs_ivtb/3) + (bs_brd*5)
            if (3 < i < 7):
                expression_1 = expression_1 + " + " + cost_med_inc + \
                               "*((mf147/3) + (mf150/3) + (mf148/6) + (" + bs_brd + "*2.5))"

            # if high income: (bs_wait*2/3) + (bs_aux*2/3) + (bs_ivtb/3) + (bs_brd*5)
            if i > 6:
                expression_1 = expression_1 + " + " + cost_high_inc + \
                               "*((mf147/3) + (mf150/3) + (mf148/6) + (" + bs_brd + "*2.5))"

            spec_list.append(build_spec(expression_1, "mf925", constraint))

            result = "mf" + str(mode_mf + i)
            spec_list.append(util.matrix_spec(result, "-9999"))
            expression = "mf925 + mf926 + mf927"
            spec_list.append(build_spec(expression, result, constraint))
        util.compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_HOV2_utility")
    def calculate_hov2(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")
    # HOV2 utility stored between matrices mf383-mf391

        alt_spec_cons = str(0.915606740026)
        low_inc = str(0.375495689886)
        # high_inc = str(-0.708370852764)
        zero_cars = str(-1.03595678065)
        twoplus_cars = str(0.692488573104)

        cost_all_inc = str(-0.0353037544584)
        au_prk = "md28"
        cost_low_inc = str(-0.0353037544584)
        cost_med_inc = str(-0.0353037544584)
        cost_high_inc = str(-0.0353037544584)

        #cbd = str(-1.40582343877)
        auto_acc = str(0.00310884249857)
        intra_van = str(-3.20670830746)
        hov_van = str(-0.333394111314)
        #ret_dens = str(0.00617014015912)
        #rural = str(0.295199509485)
        #within_gy = str(-0.222647811404)
        surwr = str(-0.210694124057)

        mode_mf = 382
        spec_list = []

        # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
        #expression_2 = expression_2 + " + " + cbd + "*(((gy(p).eq.3)+(gy(q).eq.3)).ge.1)"
        expression_2 = hov_van + "*(((gy(p).eq.4).or.(gy(q).eq.4)))"
        # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
        expression_2 = expression_2 + " + " + intra_van + "*((gy(p).eq.4)*(gy(q).eq.4))"
        spec_list.append(build_spec(expression_2, "mf926"))

        for i in range(1, 10):
            expression_1 = alt_spec_cons + "-0.2*(((gy(p).eq.2).or.(gy(q).eq.2)))" \
                                           "-0.2*(((gy(p).eq.4).or.(gy(q).eq.4)))"

            if i < 4:
                expression_1 = expression_1 + " + " + low_inc
            #if i>6: expression_1 = expression_1 + " + " + high_inc
            if i in (1, 4, 7):
                expression_1 = expression_1 + " + " + zero_cars
            if i in (3, 6, 9):
                expression_1 = expression_1 + " + " + twoplus_cars

            #COST ALL INCOMES: (0.09*au_dst) + (1.25*au_toll) + (0.5*au_prk)
            expression_1 = expression_1 + " + " + cost_all_inc + \
                           "*((ms18*mf144/ms66) + (ms19*mf146/ms66) + ((md28/2+mo28/2)/ms66))"

            if i < 4:
                expression_1 = expression_1 + " + " + cost_low_inc + "*(mf145/12)"
            if 3 < i < 7:
                expression_1 = expression_1 + " + " + cost_med_inc + "*(mf145/6)"
            if i > 6:
                expression_1 = expression_1 + " + " + cost_high_inc + "*(mf145/6)"
            spec_list.append(build_spec(expression_1, "mf925"))

            # rural : 1 if (ifgt(gyo,11) or ifgt(gyd,11))
            #expression_2 = expression_2 + " + " + rural + "*((((gy(p).gt.11)*(gy(p).lt.15))+((gy(q).gt.11)*(gy(q).lt.15))).ge.1)"

            # within gy   1 if gyo=gyd
            # auto accessibilities: autoempt (i.e auto accessibilities)
            expression_3 = surwr + "*(((gy(p).eq.9)+(gy(q).eq.9)+(gy(p).eq.10)+(gy(q).eq.10)).ge.1)"
            if i < 7:
                expression_3 = expression_3 + " + " + auto_acc + "*(mo47)"

            spec_list.append(build_spec(expression_3, "mf927"))

            result = "mf" + str(mode_mf + i)
            expression = "mf925 + mf926 + mf927"
            spec_list.append(util.matrix_spec(result, expression))
        util.compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_SOV_utility")
    def calculate_sov(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")
    # SOV utility stored between matrices mf374-mf382

        low_inc = str(0.415284584773)
        twoplus_cars = str(0.657877160143)
        zero_cars = str(-0.816068939745)
        cost_all_inc = str(-0.0353037544584)
        au_prk = "md28"
        cost_low_inc = str(-0.0353037544584)
        cost_med_inc = str(-0.0353037544584)
        cost_high_inc = str(-0.0353037544584)

        #cbd = str(-1.84511404813)
        intra_van = str(-3.18611517432)
        van = str(-0.366890039043)
        brn = str(-0.0899096955036)
        sur = str(-0.286553234706)
        auto_acc = str(0.00619152075145)
        #rural = str(0.246948330828)


        mode_mf = 373
        spec_list = []

        for i in range(1, 10):
            expression = "-0.1*((gy(p).eq.2).or.(gy(q).eq.2))" \
                         "-0.1*((gy(p).eq.4).or.(gy(q).eq.4))"
            if i in (1, 4, 7):
                expression = expression + " + " + zero_cars
            if i in (3, 6, 9):
                expression = expression + " + " + twoplus_cars
            if i < 4:
                expression = expression + " + " + low_inc

            #cost all incomes: (0.18*au_dst) + (2.5*au_toll) + au_prk
            expression = expression + " + " + cost_all_inc + "*((ms18*mf144) + (ms19*mf146) + md28/2 + mo28/2)"

            if i < 4:
                expression = expression + " + " + cost_low_inc + "*(mf145/12)"
            if 3 < i < 7:
                expression = expression + " + " + cost_med_inc + "*(mf145/6)"
            if i > 6:
                expression = expression + " + " + cost_high_inc + "*(mf145/6)"

            # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
            #expression = expression + " + " + cbd + "*(((gy(p).eq.3)+(gy(q).eq.3)).ge.1)"

            # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
            expression = expression + " + " + intra_van + "*((gy(p).eq.4)*(gy(q).eq.4))"
            expression = expression + " + " + van + "*((gy(p).eq.4).or.(gy(q).eq.4))"
            expression = expression + " + " + brn + "*((gy(p).eq.5).or.(gy(q).eq.5))"
            expression = expression + " + " + sur + "*((gy(p).eq.9).or.(gy(q).eq.9))"

            # auto accessibilities: autoempt (i.e auto accessibilities)
            if i < 7: expression = expression + " + " + auto_acc + "*(mo47)"

            # rural : 1 if (ifgt(gyo,11) or ifgt(gyd,11))
            #expression = expression + " + " + rural + "*((((gy(p).gt.11)*(gy(p).lt.15))+((gy(q).gt.11)*(gy(q).lt.15))).ge.1)"

            result = "mf" + str(mode_mf + i)
            spec_list.append(util.matrix_spec(result, expression))
        util.compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_Home-base-escorting Blend Skims")
    def calculate_blends(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")

        specs = []
        specs.append(util.matrix_spec("mf140", "(mf110.eq.1)*(ms56+((mf115.eq.0)*(1-ms56)))"))
        specs.append(util.matrix_spec("mf141", "1-mf140"))
        specs.append(util.matrix_spec("mf142", "(mf121.eq.1)*(ms56+((mf129.eq.0).or.(mf130.eq.0))*(1-ms56))"))
        specs.append(util.matrix_spec("mf143", "1-mf142"))
        specs.append(util.matrix_spec("mf144", "mf100*ms56+mf103*(1-ms56)"))
        specs.append(util.matrix_spec("mf145", "mf101*ms56+mf104*(1-ms56)"))
        specs.append(util.matrix_spec("mf146", "mf102*ms56+mf105*(1-ms56)"))
        specs.append(util.matrix_spec("mf147", "mf106*(mf140+(mf140.eq.1)*0.10)+mf111*mf141"))
        specs.append(util.matrix_spec("mf148", "mf107*mf140+mf112*mf141"))
        specs.append(util.matrix_spec("mf149", "mf136*mf140+mf137*mf141"))
        specs.append(util.matrix_spec("mf150", "mf109*mf140+mf114*mf141"))
        specs.append(util.matrix_spec("mf152", "mf116*mf142+mf124*mf143"))
        specs.append(util.matrix_spec("mf153", "mf117*mf142+mf125*mf143"))
        specs.append(util.matrix_spec("mf154", "mf118*mf142+mf126*mf143"))
        specs.append(util.matrix_spec("mf155", "mf138*mf142+mf139*mf143"))
        specs.append(util.matrix_spec("mf156", "mf120*mf142+mf128*mf143"))
        specs.append(util.matrix_spec("mf158", "(mf100.lt.17.5)"))
        util.compute_matrix(specs, scenario)

    #********
    #    ADD ON (rs)
    #    Main module time slicing the matrices
    #********
    def time_slice_escorting(self, eb, scenario):
        util = _m.Modeller().tool("translink.emme.util")
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

        aTSFactor = [
            ["UniEscoSOVT1", "UniEscoSOVT2", "UniEscoSOVT3", "UniEscoSOVT4", "UniEscoSOVT5", "UniEscoAutoT6",
             "UniEscoSOVT8"],
            ["UniEscoSOVT1", "UniEscoSOVT2", "UniEscoSOVT3", "UniEscoSOVT4", "UniEscoSOVT5", "UniEscoAutoT6",
             "UniEscoSOVT8"],
            ["UniEsco2perT1", "UniEsco2perT2", "UniEsco2perT3", "UniEsco2perT4", "UniEsco2perT5", "UniEscoAutoT6",
             "UniEsco2perT8"],
            ["UniEsco2perT1", "UniEsco2perT2", "UniEsco2perT3", "UniEsco2perT4", "UniEsco2perT5", "UniEscoAutoT6",
             "UniEsco2perT8"],
            ["UniEscoTransitT1", "UniEscoTransitT2", "UniEscoTransitT3", "UniEscoTransitT4", "UniEscoTransitT5",
             "UniEscoTransitT6", "UniEscoTransitT7"],
            ["UniEscoTransitT1", "UniEscoTransitT2", "UniEscoTransitT3", "UniEscoTransitT4", "UniEscoTransitT5",
             "UniEscoTransitT6", "UniEscoTransitT7"],
            ["UniEscoActiveT1", "UniEscoActiveT2", "UniEscoActiveT3", "UniEscoActiveT4", "UniEscoActiveT5",
             "UniEscoActiveT6", "UniEscoActiveT7"]]

        #********
        #    Start matrix number to store the demand by TOD
        #********
        aResultMatrix = [773, 794, 780, 801, 815, 822, 829]

        for files, demand, result in zip(aTSFactor, arDmMatrix, aResultMatrix):
            utilities.process_timeslicing_list(eb, scenario, files)
            spec_list = []
            for time_period in range(0, 7):
                result_name = "mf" + str(result + time_period)
                expression = result_name + "+" + demand + "*mf" + str(703 + time_period)
                spec_list.append(build_spec(expression, result_name))
            util.compute_matrix(spec_list, scenario)



    #********
    #    Module - it is identical to matrix-calculation() (rs)
    #********
    def calculate_final_period_demand(self, scenario):
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

        specs = []

        specs.append(util.matrix_spec("mf846", "mf846+" + "mf777"))
        specs.append(util.matrix_spec("mf847", "mf847+" + "mf798"))
        specs.append(util.matrix_spec("mf851", "mf851+" + "(mf784/" + msAutOccEcor2Plus + ")"))
        specs.append(util.matrix_spec("mf852", "mf852+" + "(mf805/" + msAutOccEcor2Plus + ")"))
        specs.append(util.matrix_spec("mf853", "mf853+" + "mf819"))
        specs.append(util.matrix_spec("mf854", "mf854+" + "mf826"))
        specs.append(util.matrix_spec("mf855", "mf855+" + "mf833"))
        #
        #    Midday
        #
        specs.append(util.matrix_spec("mf859", "mf859+" + "mf778"))
        specs.append(util.matrix_spec("mf860", "mf860+" + "mf799"))
        specs.append(util.matrix_spec("mf864", "mf864+" + "(mf785/" + msAutOccEcor2PlusM + ")"))
        specs.append(util.matrix_spec("mf865", "mf865+" + "(mf806/" + msAutOccEcor2PlusM + ")"))
        specs.append(util.matrix_spec("mf866", "mf866+" + "mf820"))
        specs.append(util.matrix_spec("mf867", "mf867+" + "mf827"))
        specs.append(util.matrix_spec("mf868", "mf868+" + "mf834"))
        #
        #    PM peak hour
        #
        specs.append(util.matrix_spec("mf872", "mf872+" + "mf779"))
        specs.append(util.matrix_spec("mf873", "mf873+" + "mf800"))
        specs.append(util.matrix_spec("mf877", "mf877+" + "(mf786/" + msAutOccEcor2Plus + ")"))
        specs.append(util.matrix_spec("mf878", "mf878+" + "(mf807/" + msAutOccEcor2Plus + ")"))
        specs.append(util.matrix_spec("mf879", "mf879+" + "mf821"))
        specs.append(util.matrix_spec("mf880", "mf880+" + "mf828"))
        specs.append(util.matrix_spec("mf881", "mf881+" + "mf835"))

        #
        #    Accumulated demand matrices of 4 time periods by modes (auto person, bus, rail, active)
        #    mf70-mf73 : T1(before 6am and after 7pm) - auto person, bus, rail, active
        #    mf75-mf78 : T2(6am-10am) - auto person, bus, rail, active
        #    mf80-mf83 : T3(10am-2pm) - auto person, bus, rail, active
        #    mf85-mf88 : T4(2pm-7pm) - auto person, bus, rail, active
        #
        #    Auto person - 2 income levels & SOV & 2+person
        #
        specs.append(util.matrix_spec("mf70", "mf70+mf773+mf794+mf780+mf801"))
        specs.append(util.matrix_spec("mf71", "mf71+mf815"))
        specs.append(util.matrix_spec("mf72", "mf72+mf822"))
        specs.append(util.matrix_spec("mf73", "mf73+mf829"))

        specs.append(util.matrix_spec("mf75", "mf75+mf774+mf795+mf781+mf802"))
        specs.append(util.matrix_spec("mf76", "mf76+mf816"))
        specs.append(util.matrix_spec("mf77", "mf77+mf823"))
        specs.append(util.matrix_spec("mf78", "mf78+mf830"))

        specs.append(util.matrix_spec("mf80", "mf80+mf775+mf796+mf782+mf803"))
        specs.append(util.matrix_spec("mf81", "mf81+mf817"))
        specs.append(util.matrix_spec("mf82", "mf82+mf824"))
        specs.append(util.matrix_spec("mf83", "mf83+mf831"))

        specs.append(util.matrix_spec("mf85", "mf85+mf776+mf797+mf783+mf804"))
        specs.append(util.matrix_spec("mf86", "mf86+mf818"))
        specs.append(util.matrix_spec("mf87", "mf87+mf825"))
        specs.append(util.matrix_spec("mf88", "mf88+mf832"))

        util.compute_matrix(specs, scenario)
