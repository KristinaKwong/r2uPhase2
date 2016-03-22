##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step5.modechoicehbw
##--Purpose: HBW Mode Choice Model
##---------------------------------------------------------------------
import inro.modeller as _m

compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")
utilities = _m.Modeller().module("translink.emme.stage3.step5.utilities")
build_spec = utilities.build_spec

class ModeChoiceHBW(_m.Tool()):
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

    @_m.logbook_trace("Home-base work")
    def __call__(self, eb, scenario, is_last_iteration):
        utilities.dmMatInit_Work(eb)

        self.calculate_blends(scenario)
        self.calculate_sov(scenario)
        self.calculate_hov2(scenario)
        self.calculate_hov3(scenario)
        self.calculate_bus(scenario)
        self.calculate_rail(scenario)
        self.calculate_walk(scenario)
        self.calculate_bike(scenario)
        utilities.calculate_probabilities(
            scenario, nests=[[0, 1, 2], [3, 4], [5, 6]], theta=0.713222879234)
        utilities.calculate_demand(scenario,
                                   demand_start=310,
                                   probability_start=441,
                                   result_start=505)

        if is_last_iteration:
            ExportModeChoice = _m.Modeller().tool("translink.emme.stage3.step5.exportmodechoice")
            purp = 1
            ExportModeChoice.Agg_Exp_Demand(eb, purp)

        #********
        #    Initialize matrices for resulted matrices
        #    - this should be done once only. (rs- will confirm with Ali the sequence)
        #********
        utilities.dmMatInit_Full(eb)
        self.time_slice_home_base_work(eb, scenario)
        self.calculate_final_period_demand(scenario)

        # only export matrix data on the final iteration
        if is_last_iteration:
            utilities.export_matrices_report(eb, "work", range(710, 843))


    @_m.logbook_trace("Calculate_Bike_utility")
    def calculate_bike(self, scenario):
    # Bike utility stored in matrices mf428-mf436

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

        expression_area=bkscr_bk + "*((mo13+md13).gt.(5))*((gy(p).lt.11)*(gy(q).lt.11))" + distance + "*mf144"
        expression_area= (expression_area + "+" + bk_invan + "*(((gy(p).eq.4)*(gy(q).eq.4))+((gy(p).eq.3)*(gy(q).eq.3))) + "
                        + cs_bk_500 + "*((mo397.gt.0))" + " + " + intrazonal + "*((q.eq.p))")
        spec_list.append(build_spec(expression_area, "mf1089"))

        expression_Low_High = alt_spec_cons+"+"+"mf1089"
        spec_list.append(build_spec(expression_Low_High, "mf1090"))

        expression_Med = alt_spec_cons+"+"+med_inc+"+" + "mf1089"
        spec_list.append(build_spec(expression_Med, "mf1091"))




        for i in range(1, 10):


            if (i > 3 and i < 7):
                expression = "mf1091"
            else:
                expression = "mf1090"

            if i == 1 or i == 4 or i == 7:

                expression = "("+expression + " + " + zero_cars+")"

            result = "mf" + str(mode_mf + i)
            expression = expression + "*" + "mf159" +"-" + "(9999*(mf159.eq.0))"
            spec_list.append(build_spec(expression, result))

        compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_Walk_utility")
    def calculate_walk(self, scenario):
    # Walk utility stored in matrices mf419-mf427
        emmebank = scenario.emmebank

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
                        + "*((mo19/(mo20+0.00001)).gt.(0.19999))*((((gy(p).lt.3)+(gy(p).gt.5)).ge.1)*(gy(p).lt.12))"
                        + distance + "*mf144")
        spec_list.append(build_spec(expression_2, "mf926", constraint))

        # intra-vancouver: 1 if (ifeq(gyo,4) and ifeq(gyd,4))
        expression_3 = (intra_van + "*((gy(p).eq.4)*(gy(q).eq.4))"
                        + " + " + cs_wlk_250 + "*(((mo395+mo396).gt.0))"
                        + " + " + intrazonal + "*((q.eq.p))")
        spec_list.append(build_spec(expression_3, "mf927", constraint))

        for i in range(1, 10):
            expression_1 = alt_spec_cons
            if i < 4:
                expression_1 = (expression_1 + " + " + low_inc
                                + "*((gy(p).ne.4)*(gy(p).ne.5)*(gy(q).ne.4)*(gy(q).ne.5)*(gy(p).lt.11)*(gy(q).lt.11))")
            if i > 6:
                expression_1 = expression_1 + " + " + high_inc
            if i == 1 or i == 4 or i == 7:
                expression_1 = expression_1 + " + " + zero_cars

            spec_list.append(build_spec(expression_1, "mf925", constraint))

            result = "mf" + str(mode_mf + i)
            emmebank.matrix(result).initialize(-9999)
            expression = "mf925 + mf926 + mf927"
            spec_list.append(build_spec(expression, result, constraint))

        compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_Rail_utility")
    def calculate_rail(self, scenario):
    # Rail utility stored between matrices mf410-mf418
        emmebank = scenario.emmebank
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

        expression_area="0.2*(gy(q).eq.13)+" + cbd + "*(((gy(p).eq.3)+(gy(q).eq.3)).ge.1)"
        expression_area=expression_area + " + " + intra_van + "*((gy(p).eq.4)*(gy(q).eq.4))"
        expression_area=expression_area + " + " + delt + "*(((gy(p).eq.8)+(gy(q).eq.8)).ge.1)"
        expression_area=expression_area + " + " + nfvrd + "*(((gy(p).eq.13)+(gy(q).eq.13)).ge.1)"
        spec_list.append(build_spec(expression_area, "mf926"))
        expression_area2="-0.2*(((gy(p).eq.2)+(gy(q).eq.2)).ge.1)-0.2*(((gy(p).eq.7)+(gy(q).eq.7)).ge.1)-0.2*(gy(q).eq.8)"
        spec_list.append(build_spec(expression_area2, "mf927"))
        expression_area="mf926+mf927"
        spec_list.append(build_spec(expression_area, "mf1089"))


        expression_acc= tran_acc + "*((((mo392).min.100)).max.0)"
        spec_list.append(build_spec(expression_acc, "mo925"))

        expression_Low = (alt_spec_cons+"+mo925*(gy(p).ne.3)*(gy(q).ne.3)+mf1089+"+cost_all_inc +"*((mf154/3)+((mf156+7*(gy(p).lt.3)+7*(gy(p).eq.7))/3)"
                                                    "+ ((mf152+7*(gy(p).eq.7)*(gy(q).ne.7))/6)"
                                                    "+ ((mf153+7*(gy(p).lt.3)+7*(gy(p).eq.7)*(gy(q).lt.6))/6) + (mf155*10/6) +mf161)")
        spec_list.append(build_spec(expression_Low, "mf1090"))

        expression_Low = "mf1090+"+ low_inc + "*((gy(p).ne.4)*(gy(p).ne.5)*(gy(q).ne.4)*(gy(q).ne.5))"
        spec_list.append(build_spec(expression_Low, "mf1090"))


        expression_Med = (alt_spec_cons+"+mo925*(gy(p).ne.3)*(gy(q).ne.3)+mf1089+"+cost_all_inc +"*((mf154*2/3) +((mf156+7*(gy(p).lt.3))*2/3) "
                                                        "+ (mf152/3) + ((mf153+7*(gy(p).lt.3))/3) + (mf155*10/3)+mf161)")
        spec_list.append(build_spec(expression_Med, "mf1091"))

        expression_High= (alt_spec_cons+"+"+high_inc+"+mo925*(gy(p).ne.3)*(gy(q).ne.3)+mf1089+"+cost_all_inc +"*((mf154*2/3) +((mf156+7*(gy(p).lt.3))*2/3) "
                                                        "+ (mf152/3) + ((mf153+7*(gy(p).lt.3))/3) + (mf155*10/3)+mf161)")
        spec_list.append(build_spec(expression_High, "mf1092"))


        for i in range(1, 10):

            if i < 4: expression = "mf1090"
            if (i > 3 and i < 7): expression = "mf1091"
            if i > 6: expression = "mf1092"

            if i in (1, 4, 7):
                expression = expression + " + " + zero_cars

            result = "mf" + str(mode_mf + i)
            emmebank.matrix(result).initialize(-9999)

            spec_list.append(build_spec(expression, result, constraint))


        compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_Bus_utility")
    def calculate_bus(self, scenario):
    # Bus utility stored between matrices mf401-mf409
        emmebank = scenario.emmebank

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

        expression_area=cbd + "*(((gy(p).eq.3)+(gy(q).eq.3)).ge.1)"
        expression_area=expression_area + " + " + van + "*(((gy(p).eq.4)+(gy(q).eq.4)).ge.1)"
        expression_area=expression_area + " + " + intra_van + "*((gy(p).eq.4)*(gy(q).eq.4))"
        spec_list.append(build_spec(expression_area, "mf1089"))

        expression_Low = (alt_spec_cons+"+mf1089+"+cost_all_inc +"*((mf147/3) + ((mf150+7*(gy(p).eq.7))/3) " +
                                                      "+ ((mf148+7*(gy(p).eq.7)*(gy(q).lt.6))/6) + (" + bs_brd + "*10/6) + mf160)")
        spec_list.append(build_spec(expression_Low, "mf1090"))

        expression_Low = "mf1090+"+ low_inc + "*((gy(p).ne.4)*(gy(p).ne.3)*(gy(q).ne.4)*(gy(q).ne.3))"
        spec_list.append(build_spec(expression_Low, "mf1090"))

        expression_Med = alt_spec_cons+"+mf1089+"+cost_all_inc +"*((mf147*2/3) + (mf150*2/3) + (mf148/3) + (" + bs_brd + "*5)+mf160)"
        spec_list.append(build_spec(expression_Med, "mf1091"))

        expression_High= alt_spec_cons+"+"+high_inc+"+mf1089+"+cost_all_inc +"*((mf147*2/3) + (mf150*2/3) + (mf148/3) + (" + bs_brd + "*5)+mf160)"
        spec_list.append(build_spec(expression_High, "mf1092"))


        for i in range(1, 10):
            if i < 4: expression = "mf1090"
            if (i > 3 and i < 7): expression = "mf1091"
            if i > 6: expression = "mf1092"

            if i in (1, 4, 7):
                expression = expression + " + " + zero_cars

            result = "mf" + str(mode_mf + i)
            emmebank.matrix(result).initialize(-9999)

            spec_list.append(build_spec(expression, result, constraint))

        compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_HOV3_utility")
    def calculate_hov3(self, scenario):
    # HOV3 utility stored between matrices mf392-mf400
        emmebank = scenario.emmebank

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

        expression_area=cbd + "*(((gy(p).eq.3)+(gy(q).eq.3)).ge.1)"
        expression_area=expression_area + " + " + van + "*(((gy(p).eq.4)+(gy(q).eq.4)).ge.1)"
        expression_area=expression_area + " + " + intra_van + "*((gy(p).eq.4)*(gy(q).eq.4))"
        expression_area=expression_area + " + " + rural + "*((((gy(p).gt.11)*(gy(p).lt.15))+((gy(q).gt.11)*(gy(q).lt.15))).ge.1)"
        spec_list.append(build_spec(expression_area, "mf926"))

        expression_area2=within_gy_not_rural + "*((gy(p).eq.gy(q))*(gy(p).lt.12)*(gy(q).lt.12))"
        spec_list.append(build_spec(expression_area2, "mf927"))
        expression_area="mf926+mf927"
        spec_list.append(build_spec(expression_area, "mf1089"))

        expression_Low = alt_spec_cons+"+"+low_inc+"+mf1089+"+cost_all_inc +"*(((ms18/ms60)*mf144) + ((ms19/ms60)*(ms146*mf146)) + (1/ms60*(md27/2+mo27/2))+mf145/6)"
        spec_list.append(build_spec(expression_Low, "mf1090"))

        expression_Med = alt_spec_cons+"+mf1089+"+cost_all_inc +"*(((ms18/ms60)*mf144) + ((ms19/ms60)*(ms146*mf146)) + (1/ms60*(md27/2+mo27/2))+mf145/3)"
        spec_list.append(build_spec(expression_Med, "mf1091"))

        expression_High= alt_spec_cons+"+"+high_inc+"+mf1089+"+cost_all_inc +"*(((ms18/ms60)*mf144) + ((ms19/ms60)*(ms146*mf146)) + (1/ms60*(md27/2+mo27/2))+mf145/3)"
        spec_list.append(build_spec(expression_High, "mf1092"))

        for i in range(1, 10):

           if i < 4: expression = "mf1090"
           if (i > 3 and i < 7): expression = "mf1091"
           if i > 6: expression = "mf1092"

           if i in (1, 4, 7):
                expression = expression + " + " + zero_cars

           if i in (3, 6, 9):
                expression = expression + " + " + twoplus_cars

           result = "mf" + str(mode_mf + i)

           spec_list.append(build_spec(expression, result))

        compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_HOV2_utlity")
    def calculate_hov2(self, scenario):
    # HOV2 utility stored between matrices mf383-mf391

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

        expression_area=cbd + "*(((gy(p).eq.3)+(gy(q).eq.3)).ge.1)"
        expression_area=expression_area+ " + " + van + "*(((gy(p).eq.4)+(gy(q).eq.4)).ge.1)"
        expression_area=expression_area+ " + " + intra_van + "*((gy(p).eq.4)*(gy(q).eq.4))"
        expression_area=expression_area+ " + " + rural + "*((((gy(p).gt.11)*(gy(p).lt.15))+((gy(q).gt.11)*(gy(q).lt.15))).ge.1)"
        spec_list.append(build_spec(expression_area, "mf926"))
        expression_area2=within_gy_not_rural + "*((gy(p).eq.gy(q))*(gy(p).lt.12)*(gy(q).lt.12))"
        spec_list.append(build_spec(expression_area2, "mf927"))
        expression_area="mf926+mf927"
        spec_list.append(build_spec(expression_area, "mf1089"))

        expression_Low = alt_spec_cons+"+"+low_inc+"+mf1089+"+cost_all_inc +"*((ms18*mf144/2) + (ms19*(ms146*mf146)/2) + (0.5*(md27/2+mo27/2))+mf145/6)"
        spec_list.append(build_spec(expression_Low, "mf1090"))

        expression_Med = alt_spec_cons+"+mf1089+"+cost_all_inc +"*((ms18*mf144/2) + (ms19*(ms146*mf146)/2) + (0.5*(md27/2+mo27/2))+mf145/3)"
        spec_list.append(build_spec(expression_Med, "mf1091"))

        expression_High= alt_spec_cons+"+"+high_inc+"+mf1089+"+cost_all_inc +"*((ms18*mf144/2) + (ms19*(ms146*mf146)/2) + (0.5*(md27/2+mo27/2))+mf145/3)"
        spec_list.append(build_spec(expression_High, "mf1092"))

        for i in range(1, 10):

            if i < 4: expression = "mf1090"
            if (i > 3 and i < 7): expression = "mf1091"
            if i > 6: expression = "mf1092"

            if i in (1, 4, 7):
                expression = expression + " + " + zero_cars
            if i in (3, 6, 9):
                expression = expression + " + " + twoplus_cars

            result = "mf" + str(mode_mf + i)

            spec_list.append(build_spec(expression, result))

        compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_SOV_utility")
    def calculate_sov(self, scenario):
    # SOV utility stored between matrices mf374-mf382

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
        expression_area=cbd + "*(((gy(p).eq.3)+(gy(q).eq.3)).ge.1)" + " + " + intra_van + "*((gy(p).eq.4)*(gy(q).eq.4))"
        expression_area=expression_area + " + " + rural + "*((((gy(p).ge.12)*(gy(p).lt.15))+((gy(q).ge.12)*(gy(q).lt.15))).ge.1)"
        spec_list.append(build_spec(expression_area, "mf1089"))

        expression_acc= auto_acc + "*(mo47)"
        spec_list.append(build_spec(expression_acc, "mo925"))

        expression_Low = "mf1089+mo925+"+cost_all_inc +"*((ms18*mf144) + (ms19*(ms146*mf146)) + mo27/2 + md27/2 + mf145/6)"
        spec_list.append(build_spec(expression_Low, "mf1090"))

        expression_Med = "mf1089+mo925+"+cost_all_inc +"*((ms18*mf144) + (ms19*(ms146*mf146)) + mo27/2 + md27/2 + mf145/3)"
        spec_list.append(build_spec(expression_Med, "mf1091"))

        expression_High = high_inc+"+mf1089+mo925+"+cost_all_inc +"*((ms18*mf144) + (ms19*(ms146*mf146)) + mo27/2 + md27/2 + mf145/3)+0.2*(gy(p).eq.9)"
        spec_list.append(build_spec(expression_High, "mf1092"))

        for i in range(1, 10):
            if i < 4: expression = "mf1090"
            if (i > 3 and i < 7): expression = "mf1091"
            if i > 6: expression = "mf1092"

            if (i == 3 or i == 6 or i == 9): expression = expression + " + " + twoplus_cars

            result = "mf" + str(mode_mf + i)
            spec_list.append(build_spec(expression, result))

        compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate home-base work blend skims")
    def calculate_blends(self, scenario):
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
    @_m.logbook_trace("Time slicing home-base work")
    def time_slice_home_base_work(self, eb, scenario):
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

        for files, demand, result in zip(arFileName, arDmMatrix, arResultMatrix):
            utilities.process_timeslicing_list(eb, scenario, files)
            #    Range was increased to 7 from 6 time period
            spec_list = []
            for time_period in range(0, 7):
                result_name = "mf" + str(result + time_period)
                expression = result_name + "+" + demand + "*mf" + str(703 + time_period)
                spec_list.append(build_spec(expression, result_name))
            compute_matrix(spec_list, scenario)


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
        #    Generate AM peak hour demand
        #
        specs = []
        specs.append(util.matrix_spec("mf843", "mf714"))
        specs.append(util.matrix_spec("mf844", "mf721"))
        specs.append(util.matrix_spec("mf845", "mf728"))
        specs.append(util.matrix_spec("mf848", "(mf735/2)+(mf756/" + msAutOccWork3Plus + ")"))
        specs.append(util.matrix_spec("mf849", "(mf742/2)+(mf763/" + msAutOccWork3Plus + ")"))
        specs.append(util.matrix_spec("mf850", "(mf749/2)+(mf770/" + msAutOccWork3Plus + ")"))
        specs.append(util.matrix_spec("mf853", "mf819"))
        specs.append(util.matrix_spec("mf854", "mf826"))
        specs.append(util.matrix_spec("mf855", "mf833"))

        # Track work transit demand separately for park and ride model
        specs.append(util.matrix_spec("mf998", "mf819"))
        specs.append(util.matrix_spec("mf997", "mf826"))
        #
        #     Generate midday hour demand
        #
        specs.append(util.matrix_spec("mf856", "mf715"))
        specs.append(util.matrix_spec("mf857", "mf722"))
        specs.append(util.matrix_spec("mf858", "mf729"))
        specs.append(util.matrix_spec("mf861", "(mf736/2)+(mf757/" + msAutOccWork3PlusM + ")"))
        specs.append(util.matrix_spec("mf862", "(mf743/2)+(mf764/" + msAutOccWork3PlusM + ")"))
        specs.append(util.matrix_spec("mf863", "(mf750/2)+(mf771/" + msAutOccWork3PlusM + ")"))
        specs.append(util.matrix_spec("mf866", "mf820"))
        specs.append(util.matrix_spec("mf867", "mf827"))
        specs.append(util.matrix_spec("mf868", "mf834"))
        #
        #     Generate PM peak hour demand
        #
        specs.append(util.matrix_spec("mf869", "mf716"))
        specs.append(util.matrix_spec("mf870", "mf723"))
        specs.append(util.matrix_spec("mf871", "mf730"))
        specs.append(util.matrix_spec("mf874", "(mf737/2)+(mf758/" + msAutOccWork3Plus + ")"))
        specs.append(util.matrix_spec("mf875", "(mf744/2)+(mf765/" + msAutOccWork3Plus + ")"))
        specs.append(util.matrix_spec("mf876", "(mf751/2)+(mf772/" + msAutOccWork3Plus + ")"))
        specs.append(util.matrix_spec("mf879", "mf821"))
        specs.append(util.matrix_spec("mf880", "mf828"))
        specs.append(util.matrix_spec("mf881", "mf835"))
        #
        #    Accumulated demand matrices of 4 time periods by modes (auto person, bus, rail, active)
        #    mf70-mf73 : T1(before 6am and after 7pm) - auto person, bus, rail, active
        #    mf75-mf78 : T2(6am-10am) - auto person, bus, rail, active
        #    mf80-mf83 : T3(10am-2pm) - auto person, bus, rail, active
        #    mf85-mf88 : T4(2pm-7pm) - auto person, bus, rail, active
        #
        specs.append(util.matrix_spec("mf70", "mf710+mf717+mf724+mf731+mf738+mf745+mf752+mf759+mf766"))
        specs.append(util.matrix_spec("mf71", "mf815*mf928"))
        specs.append(util.matrix_spec("mf72", "mf822*mf975"))
        specs.append(util.matrix_spec("mf73", "mf829"))

        specs.append(util.matrix_spec("mf75", "mf711+mf718+mf725+mf732+mf739+mf746+mf753+mf760+mf767"))
        specs.append(util.matrix_spec("mf76", "mf816"))
        specs.append(util.matrix_spec("mf77", "mf823"))
        specs.append(util.matrix_spec("mf78", "mf830"))

        specs.append(util.matrix_spec("mf80", "mf712+mf719+mf726+mf733+mf740+mf747+mf754+mf761+mf768"))
        specs.append(util.matrix_spec("mf81", "mf817*mf929"))
        specs.append(util.matrix_spec("mf82", "mf824*mf976"))
        specs.append(util.matrix_spec("mf83", "mf831"))

        specs.append(util.matrix_spec("mf85", "mf713+mf720+mf727+mf734+mf741+mf748+mf755+mf762+mf769"))
        specs.append(util.matrix_spec("mf86", "mf818"))
        specs.append(util.matrix_spec("mf87", "mf825"))
        specs.append(util.matrix_spec("mf88", "mf832"))

        compute_matrix(specs, scenario)
