##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step5.modechoicehbuniversity
##--Purpose: HBU Mode Choice Model
##---------------------------------------------------------------------
import inro.modeller as _m

process_matrix_trans = _m.Modeller().tool("inro.emme.data.matrix.matrix_transaction")
compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")
utilities = _m.Modeller().module("translink.emme.stage3.step5.utilities")
build_spec = utilities.build_spec

# TODO: add tool interface to mode choice procedure
class ModeChoiceHBUni(_m.Tool()):
    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Mode Choice Model"
        pb.description = "Not to be used directly, module containing methods to calculate mode choice model. (etc)."
        pb.branding_text = "TransLink"
        pb.runnable = False

        return pb.render()


    @_m.logbook_trace("Home-base University")
    def __call__(self, eb, scenario, is_last_iteration):
        utilities.dmMatInit_NonWork(eb)

        self.calculate_blends(scenario)
        self.calculate_sov(scenario)
        self.calculate_hov2(scenario)
        self.calculate_hov3(scenario)
        self.calculate_bus(scenario)
        self.calculate_rail(scenario)
        self.calculate_walk(scenario)

        utilities.calculate_probabilities(
            scenario, nests=[[0, 1, 2], [3, 4], [5]], theta=0.915891936773)
        utilities.calculate_demand(
            scenario, demand_start=319, probability_start=441, result_start=640)

        ExportModeChoice = _m.Modeller().tool("translink.emme.stage3.step5.exportmodechoice")
        if is_last_iteration:
            purp = 5
            ExportModeChoice.Agg_Exp_Demand(eb, purp)

        self.aggregate_non_work_demand(scenario)

        #********
        #    Initialize matrices for resulted matrices - this should be done once only. (rs- will confirm with Ali the sequence)
        #********
        utilities.dmMatInitParts(eb)
        self.time_slice_home_base_university(eb, scenario)
        self.calculate_final_period_demand(scenario)
        if is_last_iteration:
            utilities.export_matrices_report(eb, "Univ", range(773, 843))


    ## Aggregate nonwork demand in matrices mf568-mf639
    @_m.logbook_trace("continue aggregating non work demand, university")
    def aggregate_non_work_demand(self, scenario):
        ## Aggregate nonwork demand in matrices mf568-mf639
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
    def calculate_walk(self, scenario):
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
                                                         "*((gy(p).ne.3)*(gy(q).ne.3)" \
                                                         "*(gy(p).lt.12)*(gy(q).lt.12))"
        spec_list.append(build_spec(expression_2, "mf926", constraint))

        expression_3 = intra_van + "*((gy(p).eq.4)*(gy(q).eq.4))"
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
            expression = "(mf925 + mf926 + mf927)"
            spec_list.append(build_spec(expression, result, constraint))
        compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_Rail_Utility")
    def calculate_rail(self, scenario):
        # Rail utility stored between matrices mf410-mf418
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
        expression_2 =  van + "*(((gy(p).eq.4)+(gy(q).eq.4)).ge.1)"
        spec_list.append(build_spec(expression_2, "mf926", constraint))

        expression_3 = brn + "*(((gy(p).eq.5)+(gy(q).eq.5)).ge.1)"
        spec_list.append(build_spec(expression_3, "mf927", constraint))

        for i in range(1, 10):
            expression_1 = alt_spec_cons + "+0.2*(((gy(p).eq.4)+(gy(q).eq.4)).ge.1)" \
                                           "+0.2*(((gy(p).eq.5)+(gy(q).eq.5)).ge.1)" \
                                           "+0.3*(gy(p).eq.3)" \
                                           "-0.3*(((gy(p).eq.7)+(gy(q).eq.7)).ge.1)" \
                                           "-0.3*(gy(p).eq.2)"
            if i < 4:
                expression_1 = expression_1 + " + " + lo_inc

            # cost (all incomes) : rail fares for students set at 25% of adult fare
            expression_1 = expression_1 + " + " + cost_all_inc + "*(mf161*0.25)"
            # calibration factors
            expression_1 = expression_1 + " - 0.4* (((gy(p).eq.2)+(gy(q).eq.2)).ge.1) " \
                                          " - 0.6 * (((gy(p).eq.2)+(gy(q).eq.2)).ge.1) " \
                                          " - 0.3*(((gy(p).eq.8)+(gy(q).eq.8)).ge.1)"
            expression_1 = expression_1 + " + 0.4* (gy(p).eq.13) "

            # all incomes: (rt_wait/6) + (rt_aux/6) + (rt_ivtb/12) +  (rt_ivtr/12) +(rt_brd*(5/6))
            expression_1 = expression_1 + " + " + cost_low_high + \
                           "*((mf154/6) + (mf156/6) + (mf152/12) + ((mf153+5*(gy(p).lt.3))/12) + (mf155*5/6))"
            spec_list.append(build_spec(expression_1, "mf925", constraint))


            result = "mf" + str(mode_mf + i)
            emmebank.matrix(result).initialize(-9999)
            expression = "mf925 + mf926 + mf927"
            spec_list.append(build_spec(expression, result, constraint))
        compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_Bus_Utility")
    def calculate_bus(self, scenario):
        # Bus utility stored between matrices mf401-mf409
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
        expression_2 = intra_van + "*((gy(p).eq.4)*(gy(q).eq.4))"
        spec_list.append(build_spec(expression_2, "mf926", constraint))

        for i in range(1, 10):
            expression_1 = alt_spec_cons + "+0.2*(gy(p).eq.3)" \
                                           "-0.2*(gy(p).eq.12)" \
                                           "+0.2*(gy(p).eq.5)" \
                                           "-0.2*(gy(p).eq.9)" \
                                           "-0.2*(((gy(p).eq.7)+(gy(q).eq.7)).ge.1)"

            # cost (all incomes) : bus fares for students set at 25% of adult fare
            expression_1 = expression_1 + " + " + cost_all_inc + "*(mf160*0.25)"
            # all incomes: (bs_wait/6) + (bs_aux/6) + (bs_ivtb/12) + (bs_brd*1.25)
            expression_1 = expression_1 + " + " + cost_low_high + \
                           "*((mf147/6) + (mf150/6) + (mf148/12) + (" + bs_brd + "*1.25))"
            spec_list.append(build_spec(expression_1, "mf925", constraint))

            result = "mf" + str(mode_mf + i)
            emmebank.matrix(result).initialize(-9999)
            expression = "mf925 + mf926"
            spec_list.append(build_spec(expression, result, constraint))
        compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_HOV3_Utility")
    def calculate_hov3(self, scenario):
        # HOV3 utility stored between matrices mf392-mf400
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
        expression_2 = rural + "*((((gy(p).gt.11)*(gy(p).lt.15))+((gy(q).gt.11)*(gy(q).lt.15))).ge.1)"
        # within gy (not rural):  1 if gyo=gyd and (iflt(gyo,12) and iflt(gyd,12))
        expression_2 = expression_2 + " + " + within_gy + "*(gy(p).eq.gy(q))"
        spec_list.append(build_spec(expression_2, "mf926"))

        # dens: min((max((POP11o*10000)/area,0)),100)*(ifne(gyo,3)*ifne(gyo,4))
        expression_3 = dens + "*(((mo20)*10000/(md17)).min.200)*(gy(p).ne.3)*(gy(p).ne.4)"
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
            expression = "mf925 + mf926 + mf927"
            spec_list.append(build_spec(expression, result))
        compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_HOV2_Utility")
    def calculate_hov2(self, scenario):
        # HOV2 utility stored between matrices mf383-mf391
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
        expression_2 = expression_2 + " + " + rural + "*((((gy(p).gt.11)*(gy(p).lt.15))+((gy(q).gt.11)*(gy(q).lt.15))).ge.1)"
        spec_list.append(build_spec(expression_2, "mf926"))

        # within gy :  1 if gyo=gyd
        expression_3 = within_gy + "*(gy(p).eq.gy(q))"
        # dens: min((max((POP11o*10000)/area,0)),100)*(ifne(gyo,3)*ifne(gyo,4))
        expression_3 = expression_3 + " + " + dens + "*(((mo20)*10000/(mo17)).min.100)*(gy(p).ne.3)*(gy(p).ne.4)"
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
            expression = "mf925 + mf926 + mf927"
            spec_list.append(build_spec(expression, result))
        compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_SOV_utility")
    def calculate_sov(self, scenario):
        # SOV utility stored between matrices mf374-mf382
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
        expression_2 = cbd + "*(((gy(p).eq.3)+(gy(q).eq.3)).ge.1)"
        # auto accessibilities: autoempt (i.e auto accessibilities - PS-based)
        expression_2 = expression_2 + " + " + auto_acc + "*(mo48)"
        # rural : 1 if (ifgt(gyo,11) or ifgt(gyd,11))
        expression_2 = expression_2 + " + " + rural + "*((((gy(p).ge.12)*(gy(p).lt.15))+((gy(q).ge.12)*(gy(q).lt.15))).ge.1)"
        spec_list.append(build_spec(expression_2, "mf926"))

        # within gy :  1 if gyo=gyd but not Burrard
        expression_3 = intgy_sov + "*(gy(p).eq.gy(q))*(gy(p).ne.3)*(gy(p).ne.4)*(gy(p).ne.5)"
        spec_list.append(build_spec(expression_3, "mf927"))

        for i in range(1, 10):
            expression_1 = "0"
            # high income and (ifne(gyo,4) and ifne(gyd,4) )
            if i > 6:
                expression_1 = expression_1 + " + " + high_inc + "*(gy(p).ne.4)*(gy(q).ne.4)"
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
            expression = "mf925 + mf926 + mf927"
            spec_list.append(build_spec(expression, result))
        compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_MFs_Additional_Attributes")
    def calculate_blends(self, scenario):

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
    def time_slice_home_base_university(self, eb, scenario):
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

        for files, demand, result in zip(aTSFactor, arDmMatrix, aResultMatrix):
            utilities.process_timeslicing_list(eb, scenario, files)
            spec_list = []
            for time_period in range(0, 7):
                result_name = "mf" + str(result + time_period)
                expression = result_name + "+" + demand + "*mf" + str(703 + time_period)
                spec_list.append(build_spec(expression, result_name))
            compute_matrix(spec_list, scenario)


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

        #
        #    For school and university trips with med/high income should be assigned to SOV-low_inc (mf846)or HOV-low_inc (mf851)
        #
        specs = []
        specs.append(util.matrix_spec("mf846", "mf846+" + "mf777"))
        specs.append(util.matrix_spec("mf846", "mf846+" + "mf798"))
        specs.append(util.matrix_spec("mf851", "mf851+" + "(mf784/2)+(mf791/" + msAutOccUniv3Plus + ")"))
        specs.append(util.matrix_spec("mf851", "mf851+" + "(mf805/2)+(mf812/" + msAutOccUniv3Plus + ")"))
        specs.append(util.matrix_spec("mf853", "mf853+" + "mf819"))
        specs.append(util.matrix_spec("mf854", "mf854+" + "mf826"))
        specs.append(util.matrix_spec("mf855", "mf855+" + "mf833"))
        #
        #    Midday
        #
        specs.append(util.matrix_spec("mf859", "mf859+" + "mf778"))
        specs.append(util.matrix_spec("mf859", "mf859+" + "mf799"))
        specs.append(util.matrix_spec("mf864", "mf864+" + "(mf785/2)+(mf792/" + msAutOccUniv3PlusM + ")"))
        specs.append(util.matrix_spec("mf864", "mf864+" + "(mf806/2)+(mf813/" + msAutOccUniv3PlusM + ")"))
        specs.append(util.matrix_spec("mf866", "mf866+" + "mf820"))
        specs.append(util.matrix_spec("mf867", "mf867+" + "mf827"))
        specs.append(util.matrix_spec("mf868", "mf868+" + "mf834"))
        #
        #    PM peak hour
        #
        specs.append(util.matrix_spec("mf872", "mf872+" + "mf779"))
        specs.append(util.matrix_spec("mf872", "mf872+" + "mf800"))
        specs.append(util.matrix_spec("mf877", "mf877+" + "(mf786/2)+(mf793/" + msAutOccUniv3Plus + ")"))
        specs.append(util.matrix_spec("mf877", "mf877+" + "(mf807/2)+(mf814/" + msAutOccUniv3Plus + ")"))
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
        #    Auto person - 2 income levels & SOV & 2person & 3+person
        #
        specs.append(util.matrix_spec("mf70", "mf70+mf773+mf794+mf780+mf801+mf787+mf808"))
        specs.append(util.matrix_spec("mf71", "mf71+mf815"))
        specs.append(util.matrix_spec("mf72", "mf72+mf822"))
        specs.append(util.matrix_spec("mf73", "mf73+mf829"))

        specs.append(util.matrix_spec("mf75", "mf75+mf774+mf795+mf781+mf802+mf788+mf809"))
        specs.append(util.matrix_spec("mf76", "mf76+mf816"))
        specs.append(util.matrix_spec("mf77", "mf77+mf823"))
        specs.append(util.matrix_spec("mf78", "mf78+mf830"))

        specs.append(util.matrix_spec("mf80", "mf80+mf775+mf796+mf782+mf803+mf789+mf810"))
        specs.append(util.matrix_spec("mf81", "mf81+mf817"))
        specs.append(util.matrix_spec("mf82", "mf82+mf824"))
        specs.append(util.matrix_spec("mf83", "mf83+mf831"))

        specs.append(util.matrix_spec("mf85", "mf85+mf776+mf797+mf783+mf804+mf790+mf811"))
        specs.append(util.matrix_spec("mf86", "mf86+mf818"))
        specs.append(util.matrix_spec("mf87", "mf87+mf825"))
        specs.append(util.matrix_spec("mf88", "mf88+mf832"))

        compute_matrix(specs, scenario)
