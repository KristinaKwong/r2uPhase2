##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step5.modechoicehbsocial
##--Purpose: HBSocRec Mode Choice Model
##---------------------------------------------------------------------
import inro.modeller as _m

utilities = _m.Modeller().module("translink.emme.stage3.step5.utilities")
build_spec = utilities.build_spec

# TODO: add tool interface to mode choice procedure
class ModeChoiceHBSocial(_m.Tool()):
    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Mode Choice Model"
        pb.description = "Not to be used directly, module containing methods to calculate mode choice model. (etc)."
        pb.branding_text = "TransLink"
        pb.runnable = False

        return pb.render()

    @_m.logbook_trace("Home-base social recreation")
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
            scenario, nests=[[0, 1], [3, 4], [5, 6]], theta=0.95)
        utilities.calculate_demand(
            scenario, demand_start=355, probability_start=441, result_start=640)

        ExportModeChoice = _m.Modeller().tool("translink.emme.stage3.step5.exportmodechoice")
        if is_last_iteration:
            purp = 6
            ExportModeChoice.Agg_Exp_Demand(eb, purp)

        self.aggregate_non_work_demand(scenario)
        #********
        #    Initialize matrices for resulted matrices - this should be done once only. (rs- will confirm with Ali the sequence)
        #********
        utilities.dmMatInitParts(eb)
        self.time_slice_social_recreation(eb, scenario)
        self.calculate_final_period_demand(scenario)

#        if is_last_iteration:
#            utilities.export_matrices_report(eb, "soc", range(773, 843))


    @_m.logbook_trace("continue aggregating non work demand, social_recreation")
    def aggregate_non_work_demand(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")

        matrixnum = 640
        resultmat = 568
        spec_list = []
        for i in range(0, 63):
            expression = "mf" + str(resultmat + i) + "+" + "mf" + str(matrixnum + i)
            result = "mf" + str(resultmat + i)
            spec_list.append(util.matrix_spec(result, expression))
        for i in range(63, 72):
            expression = "mf" + str(resultmat + i) + "+" + "0"
            result = "mf" + str(resultmat + i)
            spec_list.append(util.matrix_spec(result, expression))
        util.compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_Bike")
    def calculate_bike(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")
        # Bike utility stored in matrices mf428-mf436

        alt_spec_cons = str(-2.53325416178)
        zero_cars = str(1.89853885412)
        sen20_bk = str(-0.416690093206)
        #bkscr_bk = str(0.582651776309)
        distance = str(-0.197686182484)
        cbd = str(0.563492008694)
        cs_bk_250 = str(0.379405295115)
        intrazonal = str(0.715347142379)
        rurl = str(-1.03145009805)

        mode_mf = 427
        spec_list = []
        constraint = {"od_values": "mf159",
                      "interval_min": 0,
                      "interval_max": 0,
                      "condition": "EXCLUDE"}

        #au_dst
        expression_2 = distance + "*mf144"
        expression_2 = expression_2 + " + " + sen20_bk + "*((mo19/(mo20+0.00001)).gt.(0.19999))"
        spec_list.append(build_spec(expression_2, "mf926", constraint))

        # bk_invan: (ifeq(gyo,4) and ifeq(gyd,4)) + (ifeq(gyo,3) and ifeq(gyd,3))
        expression_3 = cbd + "*(((gy(p).eq.3)+(gy(q).eq.3)).ge.1)"
        expression_3 = expression_3 + " + " + cs_bk_250 + "*(((mo395+mo396).gt.0))"
        expression_3 = expression_3 + " + " + intrazonal + "*((q.eq.p))"
        expression_3 = expression_3 + " + " + rurl + "*((((gy(p).ge.11)*(gy(p).lt.15))+((gy(q).ge.11)*(gy(q).lt.15))).ge.1)"
        spec_list.append(build_spec(expression_3, "mf927", constraint))

        for i in range(1, 10):
            expression_1 = alt_spec_cons
            if i in (1, 4, 7):
                expression_1 = expression_1 + " + " + zero_cars
            spec_list.append(build_spec(expression_1, "mf925", constraint))

            result = "mf" + str(mode_mf + i)
            spec_list.append(util.matrix_spec(result, "-9999"))
            expression = "mf925 + mf926 + mf927"
            spec_list.append(build_spec(expression, result, constraint))
        util.compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_Walk_Utility")
    def calculate_walk(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")
        # Walk utility stored in matrices mf419-mf427

        alt_spec_cons = str(1.04271233749)
        low_inc = str(0.267099150745)
        hi_inc = str(-0.177389220948)
        zero_cars = str(2.1481544522)
        two_plus_car = str(-0.338243374254)
        sen20_wk = str(0.380104895856)
        distance = str(-0.884131228378)
        vanx = str(-1.55201032643)
        intra_van = str(-0.637942362812)
        dens = str(0.00341468189319)
        auto_acc = str(0.00346439336054)
        #van_locar = str(0.265095647661)
        cs_wlk_250 = str(0.379405295115)
        intrazonal = str(0.347798951676)

        mode_mf = 418
        spec_list = []
        constraint = {"od_values": "mf158",
                      "interval_min": 0,
                      "interval_max": 0,
                      "condition": "EXCLUDE"}

        #expression_2 = expression_2 + " + " + sen20_wk + "*((mo19/(mo20+0.00001)).gt.(0.19999))"
        #au_dst
        expression_2 = distance + "*mf144"
        # auto accessibilities: autoempt (i.e auto accessibilities)
        expression_2 = expression_2 + " + " + dens + "*(((md5+md6+md7+md8+md9+md10+md11)*10000/(md17+0.000001*(q.le.130))).min.200)"
        # p725*(vanod*iflt(veh2,2))
        #if (i<>3 and i<>6 and i<>9): expression_2 = expression_2 + " + " + van_locar + "*(((gy(p).eq.4)+(gy(q).eq.4)).ge.1)"
        expression_2 = expression_2 + "+" + auto_acc + "*(mo47)"
        expression_2 = expression_2 + " + " + intra_van + "*((gy(p).eq.4)*(gy(q).eq.4))"
        spec_list.append(build_spec(expression_2, "mf926", constraint))

        # intra-vancouver: 1 if (ifeq(gyo,3)*ifeq(gyd,4)) + (ifeq(gyo,4)*ifeq(gyd,3))
        expression_3 = vanx + "*(((gy(p).eq.3)*(gy(q).eq.4) + (gy(p).eq.4)*(gy(q).eq.3)).ge.1)"
        expression_3 = expression_3 + " + " + cs_wlk_250 + "*(((mo395+mo396).gt.0))"
        expression_3 = expression_3 + " + " + intrazonal + "*((q.eq.p))"
        spec_list.append(build_spec(expression_3, "mf927", constraint))

        for i in range(1, 10):
            expression_1 = alt_spec_cons
            if i < 4:
                expression_1 = expression_1 + " + " + low_inc + "*((gy(p).ne.3)*(gy(q).ne.3))"
            if i > 6:
                expression_1 = expression_1 + " + " + hi_inc
            if i == 1 or i == 4 or i == 7:
                expression_1 = expression_1 + " + " + zero_cars
            if (i == 3 or i == 6 or i == 9):
                expression_1 = expression_1 + " + " + two_plus_car + "*(((gy(p).gt.11)+(gy(q).gt.11)).ge.1)"
            #1 (if cars = 2/3) * ifne(gyo,5)*ifne(gyd,5)* ifne(gyo,3)*ifne(gyd,3)* ifne(gyo,4)*ifne(gyd,4)
            spec_list.append(build_spec(expression_1, "mf925", constraint))

            result = "mf" + str(mode_mf + i)
            spec_list.append(util.matrix_spec(result, "-9999"))
            expression = "(mf925 + mf926 + mf927)"
            spec_list.append(build_spec(expression, result, constraint))
        util.compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_Rail_Utility")
    def calculate_rail(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")
        # Rail utility stored between matrices mf410-mf418

        alt_spec_cons = str(-0.540325242543)
        lo_inc = str(0.653398616963)
        hi_inc = str(-0.33201286203)
        zero_cars = str(2.95272234998)
        pop_dens = str(0.0031043766821)
        emp_dens = str(0.00449241170922)
        van = str(-0.383537913355)
        intra_van = str(-0.840151143718)
        cost_all_inc = str(-0.0702404628224)
        rt_fare = "mf161"
        cost_low_inc = str(-0.0702404628224)
        rt_brd = "mf155"
        cost_med_inc = str(-0.0702404628224)
        cost_high_inc = str(-0.0702404628224)
        cbd = str(0.371564941324)
        tran_acc = str(0.0979125231061)
        within_gy = str(-1.2419229288)

        mode_mf = 409
        spec_list = []
        constraint = {"od_values": "mf157",
                      "interval_min": 0,
                      "interval_max": 0,
                      "condition": "EXCLUDE"}

       # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
        expression_2 = cbd + "*(((gy(p).eq.3)+(gy(q).eq.3)).ge.1)"
        expression_2 = expression_2 + " + " + van + "*(((gy(p).eq.4)+(gy(q).eq.4)).ge.1)"

        # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
        # dens: min((max((POP11o*10000)/area,0)),100)*(ifne(gyo,3)*ifne(gyo,4))
        expression_2 = expression_2 + " + " + pop_dens + "*(((mo20*10000/(mo17+0.000001*(p.le.130))).min.100)*(gy(p).ne.3)*(gy(p).ne.4))"

        expression_2 = expression_2 + " + " + emp_dens + "*((((md5+md6+md7+md8+md9+md10+md11)*10000/(md17+0.000001*(q.le.130))).min.200)*(gy(q).ne.3)*(gy(q).ne.4))"
        spec_list.append(build_spec(expression_2, "mf926", constraint))

        #relative accessibilities (auto-transit): (max(autoempt-transit2,0))
        expression_3 = tran_acc + "*(1*((((mo392).min.200)).max.0))*(gy(p).ne.3)*(gy(q).ne.3)"
        expression_3 = expression_3 + " + " + within_gy + "*(gy(p).eq.gy(q))"
        expression_3 = expression_3 + " + " + intra_van + "*((gy(p).eq.4)*(gy(q).eq.4))"
        spec_list.append(build_spec(expression_3, "mf927", constraint))

        for i in range(1, 10):
            expression_1 = alt_spec_cons + "-0.3*(((gy(p).eq.4)+(gy(q).eq.4)).ge.1)" \
                                           "-0.25*(gy(p).eq.5)" \
                                           "+0.3*(gy(p).eq.3)" \
                                           "-0.2*(gy(p).eq.7)" \
                                           "-0.3*(gy(p).eq.1)"
            if i < 4:
                expression_1 = expression_1 + " + " + lo_inc
            #*(hiin*ifne(cbdod,1)*ifne(rurod,1))
            if i > 6:
                expression_1 = expression_1 + " + " + hi_inc + "*((gy(p).ne.3)*(gy(q).ne.3)*(gy(p).lt.12)*(gy(q).lt.12))"
            if i in (1, 4, 7):
                expression_1 = expression_1 + " + " + zero_cars

            # cost (all incomes) :
            expression_1 = expression_1 + " + " + cost_all_inc + "*" + rt_fare

            # if low income: (rt_wait/3) + (rt_aux/3) + (rt_ivtb/6) +  (rt_ivtr/6) +(rt_brd*10/6)
            if i < 4:
                expression_1 = expression_1 + " + " + cost_low_inc + \
                               "*((mf154/6) + (mf156/6) + (mf152/12) + ((mf153+10*(gy(p).lt.3))/12) + (mf155*5/6))"

            # # if med income: (rt_wait*2/3) + (rt_aux*2/3) + (rt_ivtb/3) +  (rt_ivtr/3) +(rt_brd*10/3)
            if (3 < i < 7):
                expression_1 = expression_1 + " + " + cost_med_inc + \
                               "*((mf154/3) + (mf156/3) + (mf152/6) + ((mf153+10*(gy(p).lt.3))/6) + (mf155*10/6))"

            # # if high income: (rt_wait*2/3) + (rt_aux*2/3) + (rt_ivtb/6) +  (rt_ivtr/6) +(rt_brd*10/6)
            if i > 6:
                expression_1 = expression_1 + " + " + cost_high_inc + \
                               "*((mf154/3) + (mf156/3) + (mf152/6) + ((mf153+5*(gy(p).lt.3))/6) + (mf155*10/6))"

            spec_list.append(build_spec(expression_1, "mf925", constraint))

            result = "mf" + str(mode_mf + i)
            spec_list.append(util.matrix_spec(result, "-9999"))
            expression = "mf925 + mf926 + mf927"
            spec_list.append(build_spec(expression, result, constraint))
        util.compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_Bus_Utility")
    def calculate_bus(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")
        # Bus utility stored between matrices mf401-mf409

        alt_spec_cons = str(-2.00753680078)
        lo_inc = str(0.495461130067)
        high_inc = str(-0.33201286203)
        zero_cars = str(3.38582872719)
        one_car_nr = str(0.282402663756)
        cost_all_inc = str(-0.0702404628224)
        rt_fare = "mf160"
        cost_low_inc = str(-0.0702404628224)
        bs_brd = "mf149"
        cost_med_inc = str(-0.0702404628224)
        cost_high_inc = str(-0.0702404628224)
        emp_dens = str(0.00449241170922)
        intra_van = str(-0.27655078912)
        cbd = str(0.658559660214)
        gy6 = str(-0.362160161639)
        gy1012 = str(-0.572859508218)
        #tran_acc = str(0.0487922576961)
        #within_gy_not_van = str(-0.776829172883)

        mode_mf = 400
        spec_list = []
        constraint = {"od_values": "mf151",
                      "interval_min": 0,
                      "interval_max": 0,
                      "condition": "EXCLUDE"}

        # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
        expression_2 = cbd + "*(((gy(p).eq.3)+(gy(q).eq.3)).ge.1)"
        expression_2 = expression_2 + " + " + gy6 + "*(((gy(p).eq.6)+(gy(q).eq.6)).ge.1)"
        expression_2 = expression_2 + " + " + gy1012 + "*(((gy(p).eq.10)+(gy(q).eq.10)+(gy(p).eq.12)+(gy(q).eq.12)).ge.1)"

        # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
        expression_2 = expression_2 + " + " + intra_van + "*((gy(p).eq.4)*(gy(q).eq.4))"
        spec_list.append(build_spec(expression_2, "mf926", constraint))

        #relative accessibilities (auto-transit): (max(autoempt-transit2,0))
        #expression_3 = expression_3 + " + " + tran_acc + "*((((mo392).min.200)).max.0)*(gy(p).ne.3)*(gy(q).ne.3)*(gy(p).lt.12)*(gy(q).lt.12)"
        expression_3 = emp_dens + "*((((md5+md6+md7+md8+md9+md10+md11)*10000/(md17+0.000001*(q.le.130))).min.200)*(gy(p).ne.3)*(gy(q).ne.3)*(gy(q).ne.4))"
        spec_list.append(build_spec(expression_3, "mf927", constraint))

        for i in range(1, 10):
            expression_1 = alt_spec_cons + "-0.2*(((gy(p).eq.4).or.(gy(q).eq.4)))+0.15*(gy(p).eq.5)"
            if i < 4:
                expression_1 = expression_1 + " + " + lo_inc
            if i > 6:
                expression_1 = expression_1 + " + " + high_inc
            if i in (1, 4, 7):
                expression_1 = expression_1 + " + " + zero_cars
            #+ p62*(ifeq(useveh2,1)*ifne(rurod,1))
            if i in (2, 5, 8):
                expression_1 = expression_1 + " + " + one_car_nr + "*((gy(p).lt.12)*(gy(q).lt.12))"

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
            spec_list.append(util.matrix_spec(result, "-9999"))
            expression = "mf925 + mf926 + mf927"
            spec_list.append(build_spec(expression, result, constraint))
        util.compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_HOV2_utility")
    def calculate_hov2(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")
        # HOV2 utility stored between matrices mf383-mf391

        alt_spec_cons = str(0.211986033176)
        low_inc = str(0.244657517886)
        # high_inc = str(-0.708370852764)
        zero_cars = str(0.613879199084)
        twoplus_cars = str(0.667630550329)
        cost_all_inc = str(-0.0702404628224)
        au_prk = "md28"
        cost_low_inc = str(-0.0702404628224)
        cost_med_inc = str(-0.0702404628224)
        cost_high_inc = str(-0.0702404628224)
        cbd = str(-1.71516378376)
        auto_acc = str(0.00679661389603)
        intra_van = str(-1.4399239065)
        #ret_dens = str(0.00617014015912)
        #rural = str(0.295199509485)
        #within_gy = str(-0.222647811404)


        mode_mf = 382
        spec_list = []

        # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
        expression_2 = cbd + "*(((gy(p).eq.3)+(gy(q).eq.3)).ge.1)"

        # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
        expression_2 = expression_2 + " + " + intra_van + "*((gy(p).eq.4)*(gy(q).eq.4))"
        spec_list.append(build_spec(expression_2, "mf926"))

        # rural : 1 if (ifgt(gyo,11) or ifgt(gyd,11))
        #expression_2 = expression_2 + " + " + rural + "*((((gy(p).gt.11)*(gy(p).lt.15))+((gy(q).gt.11)*(gy(q).lt.15))).ge.1)"

        # within gy   1 if gyo=gyd
        #expression_3 = expression_3 + " + " + within_gy_not_rural + "*(gy(p).eq.gy(q))"
        #expression_3 = expression_3 + " + " + ret_dens + "*(min((max((md8*10000)/mo17,0)),200))"
        # auto accessibilities: autoempt (i.e auto accessibilities)
        expression_3 = auto_acc + "*(mo47)"
        spec_list.append(build_spec(expression_3, "mf927"))

        for i in range(1, 10):
            expression_1 = alt_spec_cons

            if i < 4:
                expression_1 = expression_1 + " + " + low_inc
            #if i>6: expression_1 = expression_1 + " + " + high_inc
            if i in (1, 4, 7):
                expression_1 = expression_1 + " + " + zero_cars
            if i in (3, 6, 9):
                expression_1 = expression_1 + " + " + twoplus_cars

            #COST ALL INCOMES: (0.09*au_dst) + (1.25*au_toll) + (0.5*au_prk)
            expression_1 = expression_1 + " + " + cost_all_inc + \
                           "*((ms18*mf144/ms65) + (ms19*mf146/ms65) + ((mo28/2+md28/2)/ms65))"

            if i < 4:
                expression_1 = expression_1 + " + " + cost_low_inc + "*(mf145/12)"
            if 3 < i < 7:
                expression_1 = expression_1 + " + " + cost_med_inc + "*(mf145/6)"
            if i > 6:
                expression_1 = expression_1 + " + " + cost_high_inc + "*(mf145/6)"

            spec_list.append(build_spec(expression_1, "mf925"))

            result = "mf" + str(mode_mf + i)
            expression = "mf925 + mf926 + mf927"
            spec_list.append(util.matrix_spec(result, expression))
        util.compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_SOV")
    def calculate_sov(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")
        # SOV utility stored between matrices mf374-mf382

        twoplus_cars = str(0.475724860124)
        cost_all_inc = str(-0.0702404628224)
        au_prk = "md28"
        cost_low_inc = str(-0.0702404628224)
        cost_med_inc = str(-0.0702404628224)
        cost_high_inc = str(-0.0702404628224)
        cbd = str(-2.15614616762)
        intra_van = str(-1.77231859435)
        van = str(0.239131352397)
        auto_acc = str(0.00868508007988)
        rural = str(0.118210127524)

        mode_mf = 373
        spec_list = []

        for i in range(1, 10):
            expression = "0"

            if i in (3, 6, 9):
                expression = expression + " + " + twoplus_cars

            #cost all incomes: (0.18*au_dst) + (2.5*au_toll) + au_prk
            expression = expression + " + " + cost_all_inc + "*((ms18*mf144) + (ms19*mf146) + md28/2 + mo28/2)"

            if i < 4:
                expression = expression + " + " + cost_low_inc + "*(mf145/12)"
            if 3 < i < 7:
                expression = expression + " + " + cost_med_inc + "*(mf145/6)"
            if i > 6:
                expression = expression + " + " + cost_high_inc + "*(mf145/6)"

            # cbd: 1 if (ifeq(gyo,3) or ifeq(gyd,3))
            expression = expression + " + " + cbd + "*(((gy(p).eq.3)+(gy(q).eq.3)).ge.1)"
            expression = expression + " + " + van + "*(((gy(p).eq.4)+(gy(q).eq.4)).ge.1)"
            # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
            expression = expression + " + " + intra_van + "*((gy(p).eq.4)*(gy(q).eq.4))"

            # auto accessibilities: autoempt (i.e auto accessibilities)
            expression = expression + " + " + auto_acc + "*(mo47)"

            # rural : 1 if (ifgt(gyo,11) or ifgt(gyd,11))
            expression = expression + " + " + rural + "*((((gy(p).gt.10)*(gy(p).lt.15))+((gy(q).gt.10)*(gy(q).lt.15))).ge.1)"

            result = "mf" + str(mode_mf + i)
            spec_list.append(util.matrix_spec(result, expression))
        util.compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate Blended Skims, social recreational")
    def calculate_blends(self, scenario):
        util = _m.Modeller().tool("translink.emme.util")

        specs = []
        specs.append(util.matrix_spec("mf140", "(mf110.eq.1)*(ms55+((mf115.eq.0)*(1-ms55)))"))
        specs.append(util.matrix_spec("mf141", "1-mf140"))
        specs.append(util.matrix_spec("mf142", "(mf121.eq.1)*(ms55+(((mf129.eq.0)+(mf130.eq.0)).ge.1)*(1-ms55))"))
        specs.append(util.matrix_spec("mf143", "1-mf142"))
        specs.append(util.matrix_spec("mf144", "mf100*ms55+mf103*(1-ms55)"))
        specs.append(util.matrix_spec("mf145", "mf101*ms55+mf104*(1-ms55)"))
        specs.append(util.matrix_spec("mf146", "mf102*ms55+mf105*(1-ms55)"))
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
    @_m.logbook_trace("Time slice social recreation")
    def time_slice_social_recreation(self, eb, scenario):
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
        for nCnt1 in range(nBegBusIncLow, nBegBusIncLow + 8):
            dmBus = dmBus + "mf" + str(nCnt1) + "+"
        dmBus = dmBus + "mf" + str(nBegBusIncLow + 8) + ")"

        dmRail = "("
        for nCnt1 in range(nBegRailIncLow, nBegRailIncLow + 8):
            dmRail = dmRail + "mf" + str(nCnt1) + "+"
        dmRail = dmRail + "mf" + str(nBegRailIncLow + 8) + ")"

        dmActive = "("
        for nCnt1 in range(nBegActive, nBegActive + 17): dmActive = \
            dmActive + "mf" + str(nCnt1) + "+"
        dmActive = dmActive + "mf" + str(nBegActive + 17) + ")"

        arDmMatrix = [dmSOVLowInc, dmSOVMedHighInc,
                      dmHv2LowInc, dmHv2MedHighInc,
                      dmBus, dmRail, dmActive]

        #
        #    Correction - rail applies to time period
        #
        aTSFactor = [
            ["ShpPBSocSOVT1", "ShpPBSocSOVT2", "ShpPBSocSOVT3", "ShpPBSocSOVT4", "ShpPBSocSOVT5", "ShpPBSocAutoT6",
             "ShpPBSocSOVT8"],
            ["ShpPBSocSOVT1", "ShpPBSocSOVT2", "ShpPBSocSOVT3", "ShpPBSocSOVT4", "ShpPBSocSOVT5", "ShpPBSocAutoT6",
             "ShpPBSocSOVT8"],
            ["ShpPBSoc2perT1", "ShpPBSoc2perT2", "ShpPBSoc2perT3", "ShpPBSoc2perT4", "ShpPBSoc2perT5", "ShpPBSocAutoT6",
             "ShpPBSoc2perT8"],
            ["ShpPBSoc2perT1", "ShpPBSoc2perT2", "ShpPBSoc2perT3", "ShpPBSoc2perT4", "ShpPBSoc2perT5", "ShpPBSocAutoT6",
             "ShpPBSoc2perT8"],
            ["ShpPBSocTrnBusT1", "ShpPBSocTrnBusT2", "ShpPBSocTrnBusT3", "ShpPBSocTrnBusT4", "ShpPBSocTransitT5",
             "ShpPBSocTransitT6", "ShpPBSocTransitT7", ],
            ["ShpPBSocRailT1", "ShpPBSocRailT2", "ShpPBSocRailT3", "ShpPBSocRailT4", "ShpPBSocTransitT5",
             "ShpPBSocTransitT6", "ShpPBSocTransitT7", ],
            ["ShpPBSocActiveT1", "ShpPBSocActiveT2", "ShpPBSocActiveT3", "ShpPBSocActiveT4", "ShpPBSocActiveT5",
             "ShpPBSocActiveT6", "ShpPBSocActiveT7"]]

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

        specs = []

        specs.append(util.matrix_spec("mf846", "mf846+" + "mf777"))
        specs.append(util.matrix_spec("mf847", "mf847+" + "mf798"))
        specs.append(util.matrix_spec("mf851", "mf851+" + "(mf784/" + msAutOccSocR2Plus + ")"))
        specs.append(util.matrix_spec("mf852", "mf852+" + "(mf805/" + msAutOccSocR2Plus + ")"))
        specs.append(util.matrix_spec("mf853", "mf853+" + "mf819"))
        specs.append(util.matrix_spec("mf854", "mf854+" + "mf826"))
        specs.append(util.matrix_spec("mf855", "mf855+" + "mf833"))
        #
        #    Midday
        #
        specs.append(util.matrix_spec("mf859", "mf859+" + "mf778"))
        specs.append(util.matrix_spec("mf860", "mf860+" + "mf799"))
        specs.append(util.matrix_spec("mf864", "mf864+" + "(mf785/" + msAutOccSocR2PlusM + ")"))
        specs.append(util.matrix_spec("mf865", "mf865+" + "(mf806/" + msAutOccSocR2PlusM + ")"))
        specs.append(util.matrix_spec("mf866", "mf866+" + "mf820"))
        specs.append(util.matrix_spec("mf867", "mf867+" + "mf827"))
        specs.append(util.matrix_spec("mf868", "mf868+" + "mf834"))
        #
        #    PM peak hour
        #
        specs.append(util.matrix_spec("mf872", "mf872+" + "mf779"))
        specs.append(util.matrix_spec("mf873", "mf873+" + "mf800"))
        specs.append(util.matrix_spec("mf877", "mf877+" + "(mf786/" + msAutOccSocR2Plus + ")"))
        specs.append(util.matrix_spec("mf878", "mf878+" + "(mf807/" + msAutOccSocR2Plus + ")"))
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
