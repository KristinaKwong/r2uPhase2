##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step5.modechoicenhbw
##--Purpose: NHBW Mode Choice Model
##---------------------------------------------------------------------
import inro.modeller as _m

utilities = _m.Modeller().module("translink.emme.stage3.step5.utilities")
build_spec = utilities.build_spec

# TODO: add tool interface to mode choice procedure
class ModeChoiceNHBW(_m.Tool()):
    tool_run_msg = ""

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Mode Choice Model"
        pb.description = "Not to be used directly, module containing methods to calculate mode choice model. (etc)."
        pb.branding_text = "TransLink"
        pb.runnable = False

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)
        return pb.render()

    @_m.logbook_trace("Non-home-base work")
    def __call__(self, eb, scenario, is_last_iteration):
        utilities.dmMatInit_NonWork(eb)

        self.calculate_blends(scenario)
        self.calculate_sov(scenario)
        self.calculate_hov2(scenario)
        self.calculate_bus(scenario)
        self.calculate_rail(scenario)
        self.calculate_walk(scenario)
        self.calculate_bike(scenario)
        utilities.calculate_probabilities(
            scenario, nests=[[0, 1], [3, 4], [5, 6]], theta=0.982936463751,
            utility_start_id=377, result_start_id=444, num_segments=3)
        #demand matrices are stored in matrices mf 640-702
        utilities.calculate_demand(
            scenario, demand_start=304, probability_start=444, result_start=643, num_segments=3)

        ExportModeChoice = _m.Modeller().tool("translink.emme.stage3.step5.exportmodechoice")
        if is_last_iteration:
            purp = 9
            ExportModeChoice.Agg_Exp_Demand(eb, purp)

        # KB:   the non-home base WORK appears to be using the same
        #       components as the other NON-work purposes
        #       this may be an error
        self.aggregate_non_work_demand(scenario)

        # ********
        # Initialize matrices for resulted matrices - this should be done once only. (rs- will confirm with Ali the sequence)
        # ********
        utilities.dmMatInitParts(eb)
        self.time_slice_non_home_base_work(eb, scenario)
        self.calculate_final_period_demand(scenario)

#        if is_last_iteration:
#            utilities.export_matrices_report(eb, "nhbw", range(773, 843))


    ## Aggregate nonwork demand in matrices mf 505-567 with home-base-work matrices
    @_m.logbook_trace("Aggregate work demand")
    def aggregate_non_work_demand(self, scenario):
        # KB: why is this function different from every other "aggregate_non_work_demand"?
        #     and this should be part of work demand?
        util = _m.Modeller().tool("translink.emme.util")
        spec_list = []
        matrixnum = 643
        resultmat = 508
        for i in range(3):
            for k in range(8):
                result = "mf" + str(resultmat + i + 9 * k)
                if k < 7:
                    expression = "mf" + str(resultmat + i + k * 9) + "+" + "mf" + str(matrixnum + i + 9 * k)
                    spec_list.append(util.matrix_spec(result, expression))
                #if k == 7:
                #    expression = "mf" + str(resultmat + i + 9 * k) + "+0"
                #    spec_list.append(util.matrix_spec(result, expression))
        util.compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_Bike_utlity")
    def calculate_bike(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")
        # Bike utility stored in matrices mf428-mf436

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
        #expression_3 = expression_3 + " + " " + cbd + "*(((gy(p).eq.3)+(gy(q).eq.3)).ge.1)"
        expression_3 = vanx + "*((gy(p).eq.3)*(gy(q).eq.4).or.(gy(p).eq.4)*(gy(q).eq.3))"
        expression_3 = expression_3 + " + " + cs_bk_250 + "*(((mo395+mo396).gt.0))"
        #expression_3 = expression_3 + " + " + intrazonal + "*((q.eq.p))"
        #expression_3 = expression_3 + " + " + rurl + "*((((gy(p).ge.11)*(gy(p).lt.15))+((gy(q).ge.11)*(gy(q).lt.15))).ge.1)"
        spec_list.append(build_spec(expression_3, "mf927", constraint))

        for i in range(1, 4):
            expression_1 = alt_spec_cons
            if i == 1:
                expression_1 = expression_1 + " + " + zero_cars
            spec_list.append(build_spec(expression_1, "mf925", constraint))

            #au_dst
            expression_2 = distance + "*mf144"
            #expression_2 = expression_2 + " + " + sen20_bk + "*((mo19/(mo20+0.00001)).gt.(0.19999))"
            expression_2 = expression_2 + " + " + van + "*((gy(p).eq.4).or.(gy(q).eq.4))"
            if i < 3:
                # KB: fixed the following expression, was not used properly
                #     the following line should be uncommented
                #expression_2 = expression_2 + " + " + bkscr_bk + "*((mo13+md13).gt.5)"
                pass
            spec_list.append(build_spec(expression_2, "mf926", constraint))

            result = "mf" + str(mode_mf + i)
            spec_list.append(util.matrix_spec(result, "-9999"))
            expression = "mf925 + mf926 + mf927"
            spec_list.append(build_spec(expression, result, constraint))
        util.compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_Walk_utlity")
    def calculate_walk(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")
        # Walk utility stored in matrices mf419-mf427

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
        expression_2 = expression_2 + " + " + van + "*((gy(p).eq.4).or.(gy(q).eq.4))"
        spec_list.append(build_spec(expression_2, "mf926", constraint))

        # intra-vancouver: 1 if (ifeq(gyo,3)*ifeq(gyd,4)) + (ifeq(gyo,4)*ifeq(gyd,3))
        expression_3 = vanx + "*((gy(p).eq.3)*(gy(q).eq.4).or.(gy(p).eq.4)*(gy(q).eq.3))"
        expression_3 = expression_3 + " + " + cs_wlk_500 + "*((mo394.gt.1)*(gy(p).ne.3)*(gy(q).eq.3))"
        #expression_3 = expression_3 + " + " + intrazonal + "*((q.eq.p))"
        spec_list.append(build_spec(expression_3, "mf927", constraint))

        for i in range(1, 4):
            expression_1 = alt_spec_cons
            #if i<4: expression_1 = expression_1 + " + " + low_inc
            #if i>6: expression_1 = expression_1 + " + " + hi_inc
            if i == 1:
                expression_1 = expression_1 + " + " + zero_cars
            #if (i==3 or i ==6 or i==9): expression_1 = expression_1 + " + " + two_plus_car    "*(((gy(p).gt.11)+(gy(q).gt.11)).ge.1)"
            #1 (if cars = 2/3) * ifne(gyo,5)*ifne(gyd,5)* ifne(gyo,3)*ifne(gyd,3)* ifne(gyo,4)*ifne(gyd,4)
            spec_list.append(build_spec(expression_1, "mf925", constraint))

            result = "mf" + str(mode_mf + i)
            spec_list.append(util.matrix_spec(result, "-9999"))
            expression = "mf925 + mf926 + mf927"
            spec_list.append(build_spec(expression, result, constraint))
        util.compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_Rail_utlity")
    def calculate_rail(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")
        # Rail utility stored between matrices mf410-mf418

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
        expression_2 = cbd + "*((gy(p).eq.3).or.(gy(q).eq.3))"
        expression_2 = expression_2 + " + " + van + "*((gy(p).eq.4).or.(gy(q).eq.4))"
        #expression_2 = expression_2 + " + " + van + "*(((gy(p).eq.4)+(gy(q).eq.4)).ge.1)"
        #expression_2 = expression_2 + " + " + emp_dens + "*((((md5+md6+md7+md8+md9+md10+md11)*10000/(md17)).min.200)*(gy(q).ne.3)*(gy(q).ne.4))"
        spec_list.append(build_spec(expression_2, "mf926", constraint))

        for i in range(1, 4):
            expression_1 = alt_spec_cons + " -0.2*(gy(q).eq.1)" \
                                           " -0.2*(gy(q).eq.2) " \
                                           " -0.3*(((gy(p).eq.3).or.(gy(q).eq.3))) " \
                                           " -0.5*(((gy(p).eq.4).or.(gy(q).eq.4)))" \
                                           " -0.5*(((gy(p).eq.5).or.(gy(q).eq.5)))"
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
                expression_3 = tran_acc + "*(mo392.min.150)*(gy(p).ne.3)*(gy(q).ne.3)"
            else:
                expression_3 = "0"
            expression_3 = expression_3 + " + " + within_gy + "*(gy(p).eq.gy(q))*(gy(p).ne.3)*((gy(p).ne.4))"
            expression_3 = expression_3 + " + " + intra_van + "*((gy(p).eq.4)*(gy(q).eq.4))"
            spec_list.append(build_spec(expression_3, "mf927", constraint))

            result = "mf" + str(mode_mf + i)
            spec_list.append(util.matrix_spec(result, "-9999"))
            expression = "mf925 + mf926 + mf927"
            spec_list.append(build_spec(expression, result, constraint))
        util.compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_Bus_utility")
    def calculate_bus(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")
        # Bus utility stored between matrices mf401-mf409

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
        expression_2 = van + "*(((gy(p).eq.4).or.(gy(q).eq.4)))"
        # within gy (not rural):  1 if gyo=gyd and (iflt(gyo,12) and iflt(gyd,12))
        #expression_2 = expression_2 + " + " + within_gy_not_van + "*(gy(p).eq.gy(q))*(gy(p).ne.3)*((gy(p).ne.4))"
        spec_list.append(build_spec(expression_2, "mf926", constraint))

        for i in range(1, 4):
            expression_1 = alt_spec_cons + " - 0.3 * (((gy(p).eq.4).or.(gy(q).eq.4))) " \
                                           " - 0.3 * (gy(p).eq.3) " \
                                           " - 0.2 * (gy(q).eq.2)" \
                                           " - 0.1 * (((gy(p).eq.5).or.(gy(q).eq.5)))"
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
                expression_3 = tran_acc + "*(mo392.min.150)*(gy(p).ne.3)*(gy(q).ne.3)"
            else:
                expression_3 = "0"
            #expression_3 = expression_3 + " + " + emp_dens + "*((((md5+md6+md7+md8+md9+md10+md11)*10000/(md17)).min.200)*(gy(p).ne.3)*(gy(q).ne.3)*(gy(q).ne.4))"
            # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
            expression_3 = expression_3 + " + " + cbd + "*((gy(p).eq.3).or.(gy(q).eq.3))"
            expression_3 = expression_3 + " + " + within_gy_not_van + "*(gy(p).eq.gy(q))*(gy(p).ne.3)*(gy(p).ne.4)"
            spec_list.append(build_spec(expression_3, "mf927", constraint))

            result = "mf" + str(mode_mf + i)
            spec_list.append(util.matrix_spec(result, "-9999"))
            expression = "mf925 + mf926 + mf927"
            spec_list.append(build_spec(expression, result, constraint))
        util.compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_HOV2_utility")
    def calculate_hov2(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")
        # HOV2 utility stored between matrices mf383-mf391

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
        expression_2 =  cbd + "*((gy(p).eq.3).or.(gy(q).eq.3))"
        spec_list.append(build_spec(expression_2, "mf926"))

        # within gy   1 if gyo=gyd
        #expression_3 = expression_3 + " + " + within_gy_not_rural + "*(gy(p).eq.gy(q))"
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
            expression = "mf925 + mf926 + mf927"
            spec_list.append(util.matrix_spec(result, expression))
        util.compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_SOV_utility")
    def calculate_sov(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")
        # SOV utility stored between matrices mf374-mf382

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
            expression = expression + " + " + cbd + "*((gy(p).eq.3).or.(gy(q).eq.3))"
            expression = expression + " + " + van + "*((gy(p).eq.4).or.(gy(q).eq.4))"
            # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
            #expression = expression + " + " + intra_van + "*((gy(p).eq.4)*(gy(q).eq.4))"

            # auto accessibilities: autoempt (i.e auto accessibilities)
            #expression = expression + " + " + auto_acc + "*(mo954)"

            # rural : 1 if (ifgt(gyo,11) or ifgt(gyd,11))
            #expression = expression + " + " + rural + "*((((gy(p).gt.10)*(gy(p).lt.15))+((gy(q).gt.10)*(gy(q).lt.15))).ge.1)"

            result = "mf" + str(mode_mf + i)
            spec_list.append(util.matrix_spec(result, expression))
        util.compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_non_home_base_work_blends")
    def calculate_blends(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")

        specs = []
        specs.append(util.matrix_spec("mf140", "(mf110.eq.1)*(ms57+((mf115.eq.0)*(1-ms57)))"))
        specs.append(util.matrix_spec("mf141", "1-mf140"))
        specs.append(util.matrix_spec("mf142", "(mf121.eq.1)*(ms57+((mf129.eq.0).or.(mf130.eq.0))*(1-ms57))"))
        specs.append(util.matrix_spec("mf143", "1-mf142"))
        specs.append(util.matrix_spec("mf144", "mf100*ms57+mf103*(1-ms57)"))
        specs.append(util.matrix_spec("mf145", "mf101*ms57+mf104*(1-ms57)"))
        specs.append(util.matrix_spec("mf146", "mf102*ms57+mf105*(1-ms57)"))
        specs.append(util.matrix_spec("mf147", "mf106*(mf140+(mf140.eq.1)*0.10)+mf111*mf141"))
        specs.append(util.matrix_spec("mf148", "mf107*mf140+mf112*mf141"))
        specs.append(util.matrix_spec("mf149", "mf136*mf140+mf137*mf141"))
        specs.append(util.matrix_spec("mf150", "mf109*mf140+mf114*mf141"))
        specs.append(util.matrix_spec("mf152", "mf116*mf142+mf124*mf143"))
        specs.append(util.matrix_spec("mf153", "mf117*mf142+mf125*mf143"))
        specs.append(util.matrix_spec("mf154", "mf118*mf142+mf126*mf143"))
        specs.append(util.matrix_spec("mf155", "mf138*mf142+mf139*mf143"))
        specs.append(util.matrix_spec("mf156", "mf120*mf142+mf128*mf143"))
        specs.append(util.matrix_spec("mf158", "(mf100.lt.10)"))
        specs.append(util.matrix_spec("mf159", "(mf100.lt.20)"))
        util.compute_matrix(specs, scenario)

    #********
    #    ADD ON (rs)
    #    Main module time slicing the matrices
    #********
    @_m.logbook_trace("Time slice non-home base work")
    def time_slice_non_home_base_work(self, eb, scenario):
        util = _m.Modeller().tool("translink.emme.util")
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
            ["NHBSOVT1", "NHBSOVT2", "NHBSOVT3", "NHBSOVT4", "NHBSOVT5", "NHBSOVT6", "NHBSOVT8"],
            ["NHB2PerT1", "NHB2PerT2", "NHB2PerT3", "NHB2PerT4", "NHB2PerT5", "NHB2PerT6", "NHB2PerT8"],
            ["NHBTransitT1", "NHBTransitT2", "NHBTrnBusT3", "NHBTrnBusT4", "NHBTransitT5", "NHBTransitT6", "NHBTransitT7"],
            ["NHBTransitT1", "NHBTransitT2", "NHBRailT3", "NHBRailT4", "NHBTransitT5", "NHBTransitT6", "NHBTransitT7"],
            ["NHBActiveT1", "NHBActiveT2", "NHBActiveT3", "NHBActiveT4", "NHBActiveT5", "NHBActiveT6", "NHBActiveT7"]]

        aTSFactor=[aTSFactor[i][4:7] for i in range (len(arDmMatrix))]
        #********
        #    Start matrix number to store the demand by TOD
        #********
        aResultMatrix = [794, 801, 815, 822, 829]

        for files, demand, result in zip(aTSFactor, arDmMatrix, aResultMatrix):
            utilities.process_timeslicing_list(eb, scenario, files)
            spec_list = []
            for time_period in range(4, 7):
                result_name = "mf" + str(result + time_period)
                expression = result_name + "+" + demand + "*mf" + str(703 + time_period)
                spec_list.append(build_spec(expression, result_name))
            util.compute_matrix(spec_list, scenario)



    #********
    #    Module - it is identical to matrix-calculation() (rs)
    #********
    @_m.logbook_trace("Calculate final period demands")
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
        #
        #    EXCEPTION - For non home base work trips, they should be assigned SOV hbw-med_inc (mf844) or hbw-med_inc (mf849)
        #
        specs = []

        specs.append(util.matrix_spec("mf844", "mf844+" + "mf798"))
        specs.append(util.matrix_spec("mf849", "mf849+" + "(mf805/" + msAutOccNhbW2Plus + ")"))
        specs.append(util.matrix_spec("mf853", "mf853+" + "mf819"))
        specs.append(util.matrix_spec("mf854", "mf854+" + "mf826"))
        specs.append(util.matrix_spec("mf855", "mf855+" + "mf833"))

        # Track work transit demand separately for park and ride model
        specs.append(util.matrix_spec("mf998", "mf998 + mf819"))
        specs.append(util.matrix_spec("mf997", "mf997 + mf826"))
        #
        #    Midday
        #
        specs.append(util.matrix_spec("mf857", "mf857+" + "mf799"))
        specs.append(util.matrix_spec("mf862", "mf862+" + "(mf806/" + msAutOccNhbW2PlusM + ")"))
        specs.append(util.matrix_spec("mf866", "mf866+" + "mf820"))
        specs.append(util.matrix_spec("mf867", "mf867+" + "mf827"))
        specs.append(util.matrix_spec("mf868", "mf868+" + "mf834"))
        #
        #    PM peak hour
        #
        specs.append(util.matrix_spec("mf870", "mf870+" + "mf800"))
        specs.append(util.matrix_spec("mf875", "mf875+" + "(mf807/" + msAutOccNhbW2Plus + ")"))
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
        #    Auto person - 1 income levels & SOV & 2+person
        #
        specs.append(util.matrix_spec("mf70", "mf70+mf794+mf801"))
        specs.append(util.matrix_spec("mf71", "mf71+mf815"))
        specs.append(util.matrix_spec("mf72", "mf72+mf822"))
        specs.append(util.matrix_spec("mf73", "mf73+mf829"))

        specs.append(util.matrix_spec("mf75", "mf75+mf795+mf802"))
        specs.append(util.matrix_spec("mf76", "mf76+mf816"))
        specs.append(util.matrix_spec("mf77", "mf77+mf823"))
        specs.append(util.matrix_spec("mf78", "mf78+mf830"))

        specs.append(util.matrix_spec("mf80", "mf80+mf796+mf803"))
        specs.append(util.matrix_spec("mf81", "mf81+mf817"))
        specs.append(util.matrix_spec("mf82", "mf82+mf824"))
        specs.append(util.matrix_spec("mf83", "mf83+mf831"))

        specs.append(util.matrix_spec("mf85", "mf85+mf797+mf804"))
        specs.append(util.matrix_spec("mf86", "mf86+mf818"))
        specs.append(util.matrix_spec("mf87", "mf87+mf825"))
        specs.append(util.matrix_spec("mf88", "mf88+mf832"))

        util.compute_matrix(specs, scenario)
