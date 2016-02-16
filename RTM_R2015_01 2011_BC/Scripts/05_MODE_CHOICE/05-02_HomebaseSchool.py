##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step5.modechoicehbschool
##--Purpose: HBSCHOOL Mode Choice Model
##---------------------------------------------------------------------
import inro.modeller as _m

process_matrix_trans = _m.Modeller().tool("inro.emme.data.matrix.matrix_transaction")
compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")
utilities = _m.Modeller().module("translink.emme.stage3.step5.utilities")
build_spec = utilities.build_spec

# TODO: add tool interface to mode choice procedure
class ModeChoiceHBSchool(_m.Tool()):
    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Mode Choice Model"
        pb.description = "Not to be used directly, module containing methods to calculate mode choice model. (etc)."
        pb.branding_text = "TransLink"
        pb.runnable = False

        return pb.render()


    @_m.logbook_trace("Home-base School")
    def __call__(self, eb, scenario, iteration_number, is_last_iteration):
        utilities.dmMatInit_NonWork(eb)

        self.calculate_blends(scenario)
        self.calculate_sov(scenario)
        self.calculate_hov2(scenario)
        self.calculate_sbus(scenario)
        self.calculate_bus(scenario)
        self.calculate_rail(scenario)
        self.calculate_walk(scenario)
        self.calculate_bike(scenario)

        utilities.calculate_probabilities(
            scenario, nests=[[0, 1, 2], [3, 4], [5, 6]], theta=0.454424821545)
        utilities.calculate_demand(scenario, demand_start=328, probability_start=441, result_start=640)

        ExportModeChoice = _m.Modeller().tool("translink.emme.stage3.step5.exportmodechoice")
        if is_last_iteration:
            purp = 2
            ExportModeChoice.Agg_Exp_Demand(eb, purp, iteration_number)
        self.aggregate_non_work_demand(scenario)

        #********
        #    Initialize matrices for resulted matrices - this should be done once only. (rs- will confirm with Ali the sequence)
        #********
        utilities.dmMatInitParts(eb)
        self.time_slice_grade_school(eb, scenario)
        self.calculate_final_period_demand(scenario)
        if is_last_iteration:
            utilities.export_matrices_report(eb, "gSch", range(773, 843))


    @_m.logbook_trace("Start Aggregating Nonwork demand")
    def aggregate_non_work_demand(self, scenario):
        ## Aggregate nonwork demand in matrices mf568-mf639
        spec_list = []
        matrixnum = 640
        resultmat = 568
        for i in range(0, 18):
            result = "mf%s" % (resultmat + i)
            expression = "mf%s + %s" % ((matrixnum + i), result)
            spec_list.append(build_spec(expression, result))
        #for i in range(18, 27):
        #    result = "mf%s" % (resultmat + i)
        #    expression = "0 + %s" % (result)
        #    spec_list.append(build_spec(expression, result))
        for i in range(27, 63):
            result = "mf%s" % (resultmat + i)
            expression = "mf%s + mf%s" % ((matrixnum + i), (resultmat + i))
            spec_list.append(build_spec(expression, result))
        for i in range(63, 72):
            result = "mf%s" % (resultmat + i)
            expression = "mf%s + mf%s" % ((matrixnum + i - 45), (resultmat + i))
            spec_list.append(build_spec(expression, result))
        compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_Bike")
    def calculate_bike(self, scenario):
        # Bike utility stored in matrices mf428-mf436
        emmebank = scenario.emmebank
        alt_spec_cons = str(5.73991744842)
        twoplus_cars = str(-1.01874367846)

        distance = str(-0.916483552617)
        bk_invan = str(1.23444506232)
        intrazonal = str(1.34998946563)

        mode_mf = 427
        spec_list = []
        constraint = {"od_values": "mf159",
                      "interval_min": 0,
                      "interval_max": 0,
                      "condition": "EXCLUDE"}

        #au_dst
        expression_2 = distance + "*mf144"
        spec_list.append(build_spec(expression_2, "mf925", constraint))

        # bk_invan: (ifeq(gyo,4) and ifeq(gyd,4))
        expression_3 = bk_invan + "*((mo29.eq.4)*(md29.eq.4))"
        expression_3 = expression_3 + " + " + intrazonal + "*((q.eq.p))"
        spec_list.append(build_spec(expression_3, "mf926", constraint))

        for i in range(1, 10):
            expression_1 = alt_spec_cons
            if i in (3, 6, 9):
                expression_1 = expression_1 + " + " + twoplus_cars

            result = "mf" + str(mode_mf + i)
            emmebank.matrix(result).initialize(-9999)
            expression = expression_1 + " + mf925 + mf926"
            spec_list.append(build_spec(expression, result, constraint))

        compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_Walk")
    def calculate_walk(self, scenario):
        # Walk utility stored in matrices mf419-mf427
        emmebank = scenario.emmebank

        alt_spec_cons = str(9.31387336224)
        one_car_rur = str(0.854655870596)
        twoplus_cars = str(-1.15878323729)
        van = str(0.577600807046)
        sur = str(0.578768787796)
        distance = str(-1.29549013019)
        intrazonal = str(1.36329430778)

        mode_mf = 418
        spec_list = []
        constraint = {"od_values": "mf158",
                      "interval_min": 0,
                      "interval_max": 0,
                      "condition": "EXCLUDE"}

        #au_dst
        expression_2 = distance + "*mf144"
        # vancouver: 1 if (ifeq(gyo,4) or ifeq(gyd,4))
        expression_2 = expression_2 + " + " + van + "*(((mo29.eq.4)+(md29.eq.4)).ge.1)"
        expression_2 = expression_2 + " + " + sur + "*(((mo29.eq.9)+(md29.eq.9)).ge.1)"
        spec_list.append(build_spec(expression_2, "mf926", constraint))

        expression_3 = intrazonal + "*((q.eq.p))"
        spec_list.append(build_spec(expression_3, "mf927", constraint))

        for i in range(1, 10):
            expression_1 = alt_spec_cons
            if i in (3, 6, 9):
                expression_1 = expression_1 + " + " + twoplus_cars
            if i in (2, 5, 8):
                expression_1 = expression_1 + " + " + one_car_rur + "*(((mo29.gt.10)+(md29.gt.10)).ge.1)"
            expression_1 = expression_1 +  ""
            spec_list.append(build_spec(expression_1, "mf925", constraint))

            result = "mf" + str(mode_mf + i)
            emmebank.matrix(result).initialize(-9999)
            spec_list.append(build_spec("mf925 + mf926 + mf927+ 0.2*(mo29.eq.7) + 0.2*(mo29.eq.9)+0.3*(mo29.eq.4)", result, constraint))

        compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_Rail_Utility")
    def calculate_rail(self, scenario):
        # Rail utility stored between matrices mf410-mf418
        emmebank = scenario.emmebank

        alt_spec_cons = str(5.79677751550)
        high_inc = str(-0.855843081563)
        twoplus_cars = str(-2.53116979180)

        cost_all_inc = str(-0.222654527495)
        rt_fare = "mf161"
        cost_low_high = str(-0.222654527495)
        rt_brd = "mf155"

        dens = str(0.0100025363181)
        intra_gy = str(-0.830842708933)

        mode_mf = 409
        spec_list = []
        constraint = {"od_values": "mf157",
                      "interval_min": 0,
                      "interval_max": 0,
                      "condition": "EXCLUDE"}

        # dens: min((max((POP11o*10000)/area,0)),100)*(ifne(gyo,3)*ifne(gyo,4))
        expression_2 = dens + "*((((mo20*10000)/mo17).max.0).min.100)*((mo29.ne.3)*(mo29.ne.4))"
        spec_list.append(build_spec(expression_2, "mf925", constraint))

        #relative accessibilities (auto-transit): (max(autoempt-transit2,0))
        expression_3 = intra_gy + "*((mo29.eq.md29))"
        spec_list.append(build_spec(expression_3, "mf926", constraint))

        for i in range(1, 10):
            expression_1 = alt_spec_cons
            if i > 6:
                expression_1 = expression_1 + " + " + high_inc + "*((mo29.ne.3)*(md29.ne.3))"
            if i in (3, 6, 9):
                expression_1 = expression_1 + " + " + twoplus_cars

            # cost (all incomes) : rail fares for students set at 65% of adult fare
            expression_1 = expression_1 + " + " + cost_all_inc + "*(mf161*0.65)"

            # all incomes: (rt_wait/6) + (rt_aux/6) + (rt_ivtb/12) +  (rt_ivtr/12) +(rt_brd*(5/6))
            expression_1 = (expression_1 + " + " + cost_low_high +
                            "*((mf154/6) + (mf156/6) + (mf152/12) + (mf153/12) + (mf155*5/6))")

            result = "mf" + str(mode_mf + i)
            emmebank.matrix(result).initialize(-9999)
            spec_list.append(build_spec(expression_1 + " + mf925 + mf926", result, constraint))

        compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_Bus_Utility")
    def calculate_bus(self, scenario):
        # Bus utility stored between matrices mf401-mf409
        emmebank = scenario.emmebank

        alt_spec_cons = str(3.79438879130)
        low_inc = str(0.469310125817)
        twoplus_cars = str(-1.17310136785)
        cost_all_inc = str(-0.222654527495)
        rt_fare = "mf160"
        cost_low_high = str(-0.222654527495)
        bs_brd = "mf149"
        intra_van = str(1.50290283836)
        dens = str(0.0100025363181)

        mode_mf = 400
        spec_list = []
        constraint = {"od_values": "mf151",
                      "interval_min": 0,
                      "interval_max": 0,
                      "condition": "EXCLUDE"}

        # dens: min((max((POP11o*10000)/area,0)),100)*(ifne(gyo,3)*ifne(gyo,4))
        expression_2 = dens + "*((((mo20*10000)/mo17).max.0).min.100)*((mo29.ne.3)*(mo29.ne.4))"
        # intra-vancouver
        expression_2 = expression_2 + " + " + intra_van + "*((mo29.eq.4)*(md29.eq.4))"
        spec_list.append(build_spec(expression_2, "mf925", constraint))

        for i in range(1, 10):
            expression_1 = alt_spec_cons

            # low income if low income and (iflt(gyo,11) and ifne(gyd,11)
            if i < 4:
                expression_1 = expression_1 + " + " + low_inc + "*((mo29.lt.11)*(md29.lt.11))"
            if i in (3, 6, 9):
                expression_1 = expression_1 + " + " + twoplus_cars

            # cost (all incomes) : bus fares for students set at 65% of adult fare
            expression_1 = expression_1 + " + " + cost_all_inc + "*(mf160*0.65)"

            # all incomes:  (bs_wait/6) + (bs_aux/6) + (bs_ivtb/12) + (bs_brd*1.25)
            expression_1 =(expression_1 + " + " +
                           cost_low_high + "*((mf147/6) + (mf150/6) + (mf148/12) + (" + bs_brd + "*1.25))")

            result = "mf" + str(mode_mf + i)
            emmebank.matrix(result).initialize(-9999)
            spec_list.append(build_spec(expression_1 + " + mf925", result, constraint))

        compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_SBus_Utility")
    def calculate_sbus(self, scenario):
    # ScBs utility stored between matrices mf392-mf400

        alt_spec_cons = str(5.34380854755)
        one_car = str(0.378742136438)
        dens = str(-0.0314585473936)
        cost_all_inc = str(-0.222654527495)
        au_prk = "md27"
        cost_low_high = str(-0.222654527495)
        rural = str(1.69993207931)
        within_gy_not_rur = str(-0.544273501124)

        mode_mf = 391
        spec_list = []

        # rural : 1 if (ifgt(gyo,11) or ifgt(gyd,11))
        expression_2 = rural + "*((((mo29.gt.11)*(mo29.lt.15))+((md29.gt.11)*(md29.lt.15))).ge.1)"

        # within gy (not rural):  1 if gyo=gyd and (iflt(gyo,12) and iflt(gyd,12))
        expression_2 = expression_2 + " + " + within_gy_not_rur + "*((mo29.eq.md29)*(mo29.lt.12)*(md29.lt.12))"

        # dens: min((max((POP11o*10000)/area,0)),100)*(ifne(gyo,3)*ifne(gyo,4))
        expression_2 = expression_2 + " + " + dens + "*((((mo20*10000)/mo17).max.0).min.100)*((mo29.ne.3)*(mo29.ne.4))"
        spec_list.append(build_spec(expression_2, "mf925"))

        for i in range(1, 10):
            expression_1 = alt_spec_cons

            if i in (2, 5, 8):
                expression_1 = expression_1 + " + " + one_car

            #COST ALL INCOMES: (schbs_ivt_wait/12)
            expression_1 = expression_1 + " + " + cost_low_high + "*((mf162/12)+2*1.5385)"

            # all incomes:     no cost associated with school bus ride        (rt_wait/3) + (rt_aux/3) + (rt_ivtb/6) +  (rt_ivtr/6) +(rt_brd*10/6)
            # expression_1 = expression_1 + " + " + cost_low_high * 0

            result = "mf" + str(mode_mf + i)
            spec_list.append(build_spec(expression_1 + " + mf925", result))

        compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_HOV2_utility")
    def calculate_hov2(self, scenario):
    # HOV2 utility stored between matrices mf383-mf391

        alt_spec_cons = str(5.56388995315)
        zero_cars = str(-1.50888809806)
        cost_all_inc = str(-0.222654527495)
        au_prk = "md27"
        cost_low_high = str(-0.222654527495)
        van = str(0.674951921797)
        rural = str(1.29806606029)
        within_gy = str(0.600663961023)

        mode_mf = 382
        spec_list = []

        # vancouver: 1 if (ifeq(gyo,4) or ifeq(gyd,4))
        expression_2 = van + "*(((mo29.eq.4)+(md29.eq.4)).ge.1)"
        # rural : 1 if (ifgt(gyo,11) or ifgt(gyd,11))
        expression_2 = expression_2 + " + " + rural + "*((((mo29.gt.11)*(mo29.lt.15))+((md29.gt.11)*(md29.lt.15))).ge.1)"
        # within gy :  1 if gyo=gyd
        expression_2 = expression_2 + " + " + within_gy + "*(mo29.eq.md29)"
        spec_list.append(build_spec(expression_2, "mf925"))

        for i in range(1, 10):
            expression_1 = alt_spec_cons
            if i in (1, 4, 7):
                expression_1 = expression_1 + " + " + zero_cars

            #COST ALL INCOMES: (0.0606*au_dst) + (0.841*au_toll) with calibration factors
            expression_1 = (expression_1 + " + " +
                            cost_all_inc + "*(((ms18/ms62)*mf144) + ((ms19/ms62)*(ms146*mf146))) "
                            " - 0.15*(((mo29.gt.2)*(mo29.lt.6).or.(md29.gt.2)*(md29.lt.6)))"
                            " - 0.15*(((mo29.gt.6)*(mo29.lt.11).or.(md29.gt.6)*(md29.lt.11)))"
                            " - 0.15*(((mo29.eq.12).or.(md29.eq.12)))")

            # all incomes:
            expression_1 = expression_1 + " + " + cost_low_high + "*(mf145/12)"

            result = "mf" + str(mode_mf + i)
            spec_list.append(build_spec(expression_1 + " + mf925", result))

        compute_matrix(spec_list, scenario)


    @ _m.logbook_trace("Calculate_SOV_Utility")
    def calculate_sov(self, scenario):
    # SOV utility stored between matrices mf374-mf382

        high_inc = str(0.659336485182)
        zero_cars = str(-1.50888809806)
        twoplus_cars = str(2.03026753860)
        cost_all_inc = str(-0.222654527495)
        au_prk = "md27"
        cost_low_high = str(-0.222654527495)
        vanburn = str(-0.846488461818)
        rural = str(1.78869564961)

        mode_mf = 373
        spec_list = []

        # vancouver: 1 if (ifeq(gyo,4) or ifeq(gyd,4))
        expression_2 = vanburn + "*(((mo29.eq.4)+(md29.eq.4)+(mo29.eq.5)+(md29.eq.5)).ge.1)"
        spec_list.append(build_spec(expression_2, "mf926"))
        # rural : 1 if (ifgt(gyo,11) or ifgt(gyd,11))
        expression_3 = rural + "*((((mo29.ge.12)*(mo29.lt.15))+((md29.ge.12)*(md29.lt.15))).ge.1)"
        spec_list.append(build_spec(expression_3, "mf927"))

        for i in range(1, 10):
            expression_1 = "0"

            if i > 6:
                expression_1 = expression_1 + " + " + high_inc
            if i in (1, 4, 7):
                expression_1 = expression_1 + " + " + zero_cars
            if i in (3, 6, 9):
                expression_1 = expression_1 + " + " + twoplus_cars

            #cost all incomes: (0.18*au_dst) + (2.5*au_toll) + au_prk
            expression_1 = expression_1 + " + " + cost_all_inc + "*((ms18*mf144) + (ms19*(ms146*mf146)) + mo28/2 + md28/2)"

            # all incomes:
            expression_1 = expression_1 + " + " + cost_low_high + "*(mf145/12)"
            spec_list.append(build_spec(expression_1, "mf925"))

            result = "mf" + str(mode_mf + i)
            spec_list.append(build_spec("mf925 + mf926 + mf927", result))

        compute_matrix(spec_list, scenario)


    @_m.logbook_trace("Calculate_Home-base_School_blends")
    def calculate_blends(self, scenario):

        expressions_list = [
            ['(mf110.eq.1)*(ms52+((mf115.eq.0)*(1-ms52)))', 'mf140'],
            ['1-mf140', 'mf141'],
            ['(mf121.eq.1)*(ms52+(((mf129.eq.0)+(mf130.eq.0)).ge.1)*(1-ms52))', 'mf142'],
            ['1-mf142', 'mf143'],
            ['mf100*1', 'mf144'],
            ['mf101*1', 'mf145'],
            ['mf102*1', 'mf146'],
            ['mf106*1', 'mf147'],
            ['mf107*1', 'mf148'],
            ['mf136*1', 'mf149'],
            ['mf109*1', 'mf150'],
            ['mf116*1', 'mf152'],
            ['mf117*1', 'mf153'],
            ['mf118*1', 'mf154'],
            ['mf138*1', 'mf155'],
            ['(mf145*(mf148.le.0)*1.25) + (mf148*(mf148.gt.0)*0.5) + (mf145*(mf148.gt.0)*0.625)', 'mf162'],
            ['mf120*1', 'mf156'],
            ['(mf100.lt.10)', 'mf158'],
            ['(mf100.lt.20)', 'mf159']
        ]

        spec_list = []
        # check if mf149 and mf155 are actually needed and some of the other pre-calculations can probably be skipped
        for expression, result in expressions_list:
            spec_list.append(build_spec(expression, result))

        compute_matrix(spec_list, scenario)


    #********
    #    ADD ON (rs)
    #    Main module time slicing the matrices
    #********
    @_m.logbook_trace("Time slicing grade school")
    def time_slice_grade_school(self, eb, scenario):
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

        # dmHv3LowInc = "("
        # for nCnt1 in range(nBegHv3IncLow,nBegHv3IncLow+2):
        #     dmHv3LowInc = dmHv3LowInc+"mf"+str(nCnt1)+"+"
        # dmHv3LowInc=dmHv3LowInc+"mf"+str(nBegHv3IncLow+2)+")"

        # dmHv3MedHighInc = "("
        # for nCnt1 in range(nBegHv3IncMed,nBegHv3IncMed+5):
        #     dmHv3MedHighInc = dmHv3MedHighInc+"mf"+str(nCnt1)+"+"
        # dmHv3MedHighInc=dmHv3MedHighInc+"mf"+str(nBegHv3IncMed+5)+")"

        dmBus = "("
        for nCnt1 in range(nBegBusIncLow, nBegBusIncLow + 8):
            dmBus = dmBus + "mf" + str(nCnt1) + "+"
        dmBus = dmBus + "mf" + str(nBegBusIncLow + 8) + ")"

        dmRail = "("
        for nCnt1 in range(nBegRailIncLow, nBegRailIncLow + 8): dmRail = dmRail + "mf" + str(nCnt1) + "+"
        dmRail = dmRail + "mf" + str(nBegRailIncLow + 8) + ")"

        dmActive = "("
        for nCnt1 in range(nBegActive, nBegActive + 17): dmActive = dmActive + "mf" + str(nCnt1) + "+"
        dmActive = dmActive + "mf" + str(nBegActive + 17) + ")"

        arDmMatrix = [dmSOVLowInc, dmSOVMedHighInc,
                      dmHv2LowInc, dmHv2MedHighInc,
                      dmBus, dmRail, dmActive]
        #
        #    Since grade school trips are lack of observations for time period T1,T3 and T6, TSF of those time period are borrowed from university/ecorting purpose
        #    PM peak hour -  auto's TSF are provided by Delcan, transit and active modes are from TL
        #
        aTSFactor = [
            ['GSchAutoT1', 'GSchAutoT2', 'GSchAutoT3', 'GSchAutoT4', 'GSchAutoT5', 'GSchAutoT6', 'GSchAutoT8'],
            ['GSchAutoT1', 'GSchAutoT2', 'GSchAutoT3', 'GSchAutoT4', 'GSchAutoT5', 'GSchAutoT6', 'GSchAutoT8'],
            ['GSchAutoT1', 'GSchAutoT2', 'GSchAutoT3', 'GSchAutoT4', 'GSchAutoT5', 'GSchAutoT6', 'GSchAutoT8'],
            ['GSchAutoT1', 'GSchAutoT2', 'GSchAutoT3', 'GSchAutoT4', 'GSchAutoT5', 'GSchAutoT6', 'GSchAutoT8'],
            ['GSchTransitT1', 'GSchTransitT2', 'GSchTransitT3', 'GSchTransitT4', 'GSchTransitT5', 'GSchTransitT6',
             'GSchTransitT7'],
            ['GSchTransitT1', 'GSchTransitT2', 'GSchTransitT3', 'GSchTransitT4', 'GSchTransitT5', 'GSchTransitT6',
             'GSchTransitT7'],
            ['GSchActiveT1', 'GSchActiveT2', 'GSchActiveT3', 'GSchActiveT4', 'GSchActiveT5', 'GSchActiveT6',
             'GSchActiveT7']]
        # aTSFactor=[
        # ['UniEscoAutoT1','GSchAutoT2','UniEscoAutoT3','GSchAutoT4','GSchAutoT5','UniEscoAutoT6'],
        # ['UniEscoAutoT1','GSchAutoT2','UniEscoAutoT3','GSchAutoT4','GSchAutoT5','UniEscoAutoT6'],
        # ['UniEscoAutoT1','GSchAutoT2','UniEscoAutoT3','GSchAutoT4','GSchAutoT5','UniEscoAutoT6'],
        # ['UniEscoAutoT1','GSchAutoT2','UniEscoAutoT3','GSchAutoT4','GSchAutoT5','UniEscoAutoT6'],
        # ['UniEscoAutoT1','GSchAutoT2','UniEscoAutoT3','GSchAutoT4','GSchAutoT5','UniEscoAutoT6'],
        # ['UniEscoAutoT1','GSchAutoT2','UniEscoAutoT3','GSchAutoT4','GSchAutoT5','UniEscoAutoT6'],
        # ['UniEscoTransitT1','GSchTransitT2','UniEscoTransitT3','GSchTransitT4','GSchTransitT5','UniEscoTransitT6'],
        # ['UniEscoTransitT1','GSchTransitT2','UniEscoTransitT3','GSchTransitT4','GSchTransitT5','UniEscoTransitT6'],
        # ['UniEscoActiveT1' ,'GSchActiveT2' ,'UniEscoActiveT3' ,'GSchActiveT4' ,'GSchActiveT5' ,'UniEscoActiveT6' ]]

        #********
        #    Start matrix number to store the demand by TOD
        #********
        aResultMatrix = [773, 794, 780, 801, 815, 822, 829]

        for files, demand, result in zip(aTSFactor, arDmMatrix, aResultMatrix):
            utilities.process_timeslicing_list(eb, scenario, files)
            #    Range was increased to 7 from 6 time period
            spec_list = []
            for time_period in range(0, 7):
                result_name = "mf" + str(result + time_period)
                expression = result_name + "+" + demand + "*mf" + str(703 + time_period)
                spec_list.append(build_spec(expression, result_name))
            compute_matrix(spec_list, scenario)


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
        #    For school and university trips with med/high income should be assigned to SOV-low_inc (mf846)or HOV-low_inc (mf851)
        #    md999 : An adjustment factor for auto person grade school trips (0.9 assigns to GY 4,6,10,13,14, 0.75 assigns to GY 5,7,8,9)
        #    (AM peak hour ONLY)
        #
        specs = []

        specs.append(util.matrix_spec("mf846", "mf846+" + "mf777*md999"))
        specs.append(util.matrix_spec("mf846", "mf846+" + "mf798*md999"))
        specs.append(util.matrix_spec("mf851", "mf851+" + "mf784*md999/" + msAutOccGSch2Plus))
        specs.append(util.matrix_spec("mf851", "mf851+" + "mf805*md999/" + msAutOccGSch2Plus))
        specs.append(util.matrix_spec("mf853", "mf853+" + "mf819*mf996"))
        specs.append(util.matrix_spec("mf854", "mf854+" + "mf826*mf992"))
        specs.append(util.matrix_spec("mf855", "mf855+" + "mf833"))
        #
        #    Midday
        #
        specs.append(util.matrix_spec("mf859", "mf859+" + "mf778"))
        specs.append(util.matrix_spec("mf859", "mf859+" + "mf799"))
        specs.append(util.matrix_spec("mf864", "mf864+" + "mf785/" + msAutOccGSch2PlusM))
        specs.append(util.matrix_spec("mf864", "mf864+" + "mf806/" + msAutOccGSch2PlusM))
        specs.append(util.matrix_spec("mf866", "mf866+" + "mf820"))
        specs.append(util.matrix_spec("mf867", "mf867+" + "mf827"))
        specs.append(util.matrix_spec("mf868", "mf868+" + "mf834"))
        #
        #    PM peak hour
        #
        specs.append(util.matrix_spec("mf872", "mf872+" + "mf779"))
        specs.append(util.matrix_spec("mf872", "mf872+" + "mf800"))
        specs.append(util.matrix_spec("mf877", "mf877+" + "mf786/" + msAutOccGSch2Plus))
        specs.append(util.matrix_spec("mf877", "mf877+" + "mf807/" + msAutOccGSch2Plus))
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

        compute_matrix(specs, scenario)
