##--------------------------------------------------
##--TransLink Phase 2 Regional Transportation Model
##--01-02AutoOwnership.PY
##--Path: translink.emme.autoownership
##--Purpose of 01-02AutoOwnership:
##--------------------------------------------------
##--Last modified 2014-04-07 Kevin Bragg (INRO)
##--Reason: Further code cleanup and PEP 8 compliance
##--Last modified 2014-02-14 Kevin Bragg (INRO)
##--Reason: Update to Emme 4.0 namespaces
##          Code cleanup PEP 8 compliance
##--Last modified 2013-08-29 Rhys Wolff (HDR)
##--Last modification reason - add comments and notes
##--scratch matrix use replaced by compound expressions
##--matrices mo30 to mo43, mo395 to mo403 no longer used.
##---------------------------------------------------
##--Called by: 01-01SocioeconomicSegmentation
##--Calls:     None
##--Accesses:  None
##--Outputs: Auto ownership toolbox txt files
##---------------------------------------------------
##--Status/additional notes:
##--Supersedes all earlier versions of 01-02AutoOwnership.PY
##---------------------------------------------------

import inro.modeller as _m
from datetime import datetime


# TODO: add tool interface
class AutoOwnershipTool(_m.Tool()):
    def page(self):
        pb = _m.ToolPageBuilder(self,
                                       title="The Auto Ownership Modeller -913",
                                       description="Not to be used directly, called from "
                                                   "SocioEconomicSegmentation",
                                       runnable=False)
        return pb.render()


## mo404-mo442 - Store utility value while for AutoOwn=0 for various HHSize, NumWorkers, IncomeCat
def Calculate_AutoOwnership_0Cars(self, AutoOwnCoeff):
    with _m.logbook_trace("Calculate AutoOwnership 0 Cars - Utilities"):
        print "--------Calculate_AutoOwnership_0Cars, " + str(datetime.now().strftime('%H:%M:%S'))
        NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
        compute_matrix = _m.Modeller().tool(NAMESPACE)

        lowinc0 = AutoOwnCoeff.get('lowinc0', [0])[0]
        hiinc0 = AutoOwnCoeff.get('hiinc0', [0])[0]
        traccc0 = AutoOwnCoeff.get('traccc0', [0])[0]
        dens_c0 = AutoOwnCoeff.get('dens_c0', [0])[0]
        wrkr0_c0 = AutoOwnCoeff.get('wrkr0_c0', [0])[0]
        Beta00199 = AutoOwnCoeff.get('Beta00199', [0])[0]

        ##scratch work MO coefficients
        crsh2500l = AutoOwnCoeff.get('crsh2500l', [0])[0]
        crsh2500h = AutoOwnCoeff.get('crsh2500h', [0])[0]
        crsh500p0 = AutoOwnCoeff.get('crsh500p0', [0])[0]
        sen20c0 = AutoOwnCoeff.get('sen20c0', [0])[0]
        sen25c0 = AutoOwnCoeff.get('sen25c0', [0])[0]
        van_c0 = AutoOwnCoeff.get('van_c0', [0])[0]
        cbd_c0l = AutoOwnCoeff.get('cbd_c0l', [0])[0]
        burn_c0 = AutoOwnCoeff.get('burn_c0', [0])[0]

        spec_as_dict = {
            "expression": "EXPRESSION",
            "result": "RESULT",
            "constraint": {
                "by_value": None,
                "by_zone": {
                    "origins": None,
                    "destinations": None
                }
            },
            "aggregation": {
                "origins": None,
                "destinations": None
            },
            "type": "MATRIX_CALCULATION"
        }

        ##crsh2500l
        spec_as_dict["expression"] = "(mo393.gt.0)*(mo16.lt.50)"
        spec_as_dict["result"] = "mo395"
        report = compute_matrix(spec_as_dict)

        ##crsh2500h
        spec_as_dict["expression"] = "(mo393.gt.0)*(mo16.ge.50)"
        spec_as_dict["result"] = "mo396"
        report = compute_matrix(spec_as_dict)

        ##crsh2501
        #mo395 + mo396  (no seperate mo matrix needed)

        ##crsh500p0
        ##crsh500p1
        spec_as_dict["expression"] = "(mo394.gt.1)"
        spec_as_dict["result"] = "mo397"
        report = compute_matrix(spec_as_dict)

        for auto_own_one in range(1, 40):
            expression = ""
            if (1 <= auto_own_one and auto_own_one <= 13):
                expression = str(lowinc0) + " + " + \
                             str(traccc0) + "*mo392 + " + \
                             str(dens_c0) + "*mo16 + " + \
                             str(crsh2500l) + "*(mo393.gt.0)*(mo16.lt.50) + " + \
                             str(crsh2500h) + "*(mo393.gt.0)*(mo16.ge.50) + " + \
                             str(crsh500p0) + "*(mo394.gt.1) + " + \
                             str(sen20c0) + "*(mo18.ge.0.20)*(mo18.lt.0.25) + " + \
                             str(sen25c0) + "*(mo18.ge.0.25) + " + \
                             str(van_c0) + "*(gy(p).eq.4) + " + \
                             str(cbd_c0l) + "*(gy(p).eq.3) + " + \
                             str(burn_c0) + "*(gy(p).eq.5) "

            if (auto_own_one >= 14 and auto_own_one <= 26):
                expression = str(traccc0) + "*mo392 + " + \
                             str(dens_c0) + "*mo16 + " + \
                             str(crsh2500l) + "*(mo393.gt.0)*(mo16.lt.50) + " + \
                             str(crsh2500h) + "*(mo393.gt.0)*(mo16.ge.50) + " + \
                             str(crsh500p0) + "*(mo394.gt.1) + " + \
                             str(sen20c0) + "*(mo18.ge.0.20)*(mo18.lt.0.25) + " + \
                             str(sen25c0) + "*(mo18.ge.0.25) + " + \
                             str(van_c0) + "*(gy(p).eq.4) + " + \
                             str(burn_c0) + "*(gy(p).eq.5) "

            if (auto_own_one >= 27):
                expression = str(hiinc0) + " + " + \
                             str(traccc0) + "*mo392 + " + \
                             str(dens_c0) + "*mo16 + " + \
                             str(crsh2500l) + "*(mo393.gt.0)*(mo16.lt.50) + " + \
                             str(crsh2500h) + "*(mo393.gt.0)*(mo16.ge.50) + " + \
                             str(crsh500p0) + "*(mo394.gt.1) + " + \
                             str(sen20c0) + "*(mo18.ge.0.20)*(mo18.lt.0.25) + " + \
                             str(sen25c0) + "*(mo18.ge.0.25) + " + \
                             str(van_c0) + "*(gy(p).eq.4) + " + \
                             str(burn_c0) + "*(gy(p).eq.5) + " + \
                             str(Beta00199) + "*(gy(p).eq.3)"
            if auto_own_one in [1, 3, 6, 10, 14, 16, 19, 23, 27, 29, 32, 36]:
                expression = expression + " + " + str(wrkr0_c0)

            #            print str(auto_own_one) + " = " + expression
            spec_as_dict["expression"] = expression
            spec_as_dict["result"] = "mo" + str(auto_own_one + 403)

            #            print "result: " + "mo"+str(auto_own_one+403)
            report = compute_matrix(spec_as_dict)


## mo443-mo481 - Store utility value while for AutoOwn=1 for various HHSize, NumWorkers, IncomeCat
def Calculate_AutoOwnership_1Cars(self, AutoOwnCoeff):
    with _m.logbook_trace("Calculate AutoOwnership 1 Cars - Utilities"):
        print "--------Calculate_AutoOwnership_1Cars, " + str(datetime.now().strftime('%H:%M:%S'))
        NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
        compute_matrix = _m.Modeller().tool(NAMESPACE)

        bias1 = AutoOwnCoeff.get('1bias', [0])[0]
        lowinc1 = AutoOwnCoeff.get('lowinc1', [0])[0]
        hiinc1 = AutoOwnCoeff.get('hiinc1', [0])[0]
        traccc1 = AutoOwnCoeff.get('traccc1', [0])[0]
        dens_c1 = AutoOwnCoeff.get('dens_c1', [0])[0]
        crsh2501 = AutoOwnCoeff.get('crsh2501', [0])[0]
        crsh500p1 = AutoOwnCoeff.get('crsh500p1', [0])[0]
        sen20c1 = AutoOwnCoeff.get('sen20c1', [0])[0]
        sen25c1 = AutoOwnCoeff.get('sen25c1', [0])[0]
        cbd_c1h = AutoOwnCoeff.get('cbd_c1h', [0])[0]
        burn_c1 = AutoOwnCoeff.get('burn_c1', [0])[0]
        wrkr3_c1 = AutoOwnCoeff.get('wrkr3_c1', [0])[0]
        lrg_c1 = AutoOwnCoeff.get('lrg_c1', [0])[0]

        spec_as_dict = {
            "expression": "EXPRESSION",
            "result": "RESULT",
            "constraint": {
                "by_value": None,
                "by_zone": {
                    "origins": None,
                    "destinations": None
                }
            },
            "aggregation": {
                "origins": None,
                "destinations": None
            },
            "type": "MATRIX_CALCULATION"
        }

        for auto_own_one in range(1, 40):
            expression = ""
            if (1 <= auto_own_one and auto_own_one <= 13):
                expression = str(bias1) + " + " + \
                             str(lowinc1) + " + " + \
                             str(traccc1) + "*mo392 + " + \
                             str(dens_c1) + "*mo16 + " + \
                             str(crsh2501) + "*((mo393.gt.0)*(mo16.lt.50)+(mo393.gt.0)*(mo16.ge.50)) + " + \
                             str(crsh500p1) + "*(mo394.gt.1) + " + \
                             str(sen20c1) + "*(mo18.ge.0.20)*(mo18.lt.0.25) + " + \
                             str(sen25c1) + "*(mo18.ge.0.25) + " + \
                             str(burn_c1) + "*(gy(p).eq.5)"

            if (auto_own_one >= 14 and auto_own_one <= 26):
                expression = str(bias1) + " + " + \
                             str(traccc1) + "*mo392 + " + \
                             str(dens_c1) + "*mo16 + " + \
                             str(crsh2501) + "*((mo393.gt.0)*(mo16.lt.50)+(mo393.gt.0)*(mo16.ge.50)) + " + \
                             str(crsh500p1) + "*(mo394.gt.1) + " + \
                             str(sen20c1) + "*(mo18.ge.0.20)*(mo18.lt.0.25) + " + \
                             str(sen25c1) + "*(mo18.ge.0.25) + " + \
                             str(burn_c1) + "*(gy(p).eq.5)"

            if (auto_own_one >= 27):
                expression = str(bias1) + " + " + \
                             str(hiinc1) + " + " + \
                             str(traccc1) + "*mo392 + " + \
                             str(dens_c1) + "*mo16 + " + \
                             str(crsh2501) + "*((mo393.gt.0)*(mo16.lt.50)+(mo393.gt.0)*(mo16.ge.50)) + " + \
                             str(crsh500p1) + "*(mo394.gt.1) + " + \
                             str(sen20c1) + "*(mo18.ge.0.20)*(mo18.lt.0.25) + " + \
                             str(sen25c1) + "*(mo18.ge.0.25) + " + \
                             str(cbd_c1h) + "*(gy(p).eq.3) + " + \
                             str(burn_c1) + "*(gy(p).eq.5)"

            ##wrkr3_c1
            if auto_own_one in [9, 13, 22, 26, 35, 39]:
                expression = expression + " + " + str(wrkr3_c1)

            ##lrg_c1
            if ((auto_own_one - 1) % 13) >= 5:
                expression = expression + " + " + str(lrg_c1)

            spec_as_dict["expression"] = expression
            spec_as_dict["result"] = "mo" + str(auto_own_one + 442)

            report = compute_matrix(spec_as_dict)


## mo482-mo520 - Store utility value while for AutoOwn=2 for various HHSize, NumWorkers, IncomeCat
def Calculate_AutoOwnership_2Cars(self, AutoOwnCoeff):
    with _m.logbook_trace("Calculate AutoOwnership 2 Cars - Utilities"):
        print "--------Calculate_AutoOwnership_2Cars, " + str(datetime.now().strftime('%H:%M:%S'))
        NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
        compute_matrix = _m.Modeller().tool(NAMESPACE)
        bias2 = AutoOwnCoeff.get('2bias', [0])
        wrkr2_c23 = AutoOwnCoeff.get('wrkr2_c23', [0])
        hiinc2 = AutoOwnCoeff.get('hiinc2', [0])[0]
        wrkr0_c2 = AutoOwnCoeff.get('wrkr0_c2', [0])[0]
        wrkr3_c2 = AutoOwnCoeff.get('wrkr3_c2', [0])[0]

        lrg_c2 = AutoOwnCoeff.get('lrg_c2', [0])[0]

        dens_c2 = AutoOwnCoeff.get('dens_c2', [0])[0]
        burn_c2 = AutoOwnCoeff.get('burn_c2', [0])[0]

        van_c3 = AutoOwnCoeff.get('van_c3', [0])[0]

        spec_as_dict = {
            "expression": "EXPRESSION",
            "result": "RESULT",
            "constraint": {
                "by_value": None,
                "by_zone": {
                    "origins": None,
                    "destinations": None
                }
            },
            "aggregation": {
                "origins": None,
                "destinations": None
            },
            "type": "MATRIX_CALCULATION"
        }

        for auto_own_one in range(1, 40):
            expression = str(van_c3) + "*(gy(p).eq.4) + " + str(dens_c2) + "*mo16 + " + str(burn_c2) + "*(gy(p).eq.5) "

            if len(bias2) == 1:
                expression = expression + " + " + bias2[0]
            else:
                for i in range(0, 14):
                    expression = expression + " + " + bias2[i] + "*(mo29.eq." + str(1 + i) + ")"

            if (auto_own_one >= 27):
                expression = expression + " + " + str(hiinc2)

            ##wrkr0_c2
            if auto_own_one in [1, 3, 6, 10, 14, 16, 19, 23]:
                expression = expression + " + " + str(wrkr0_c2)

            ##wrkr3_c2
            if auto_own_one in [9, 13, 22, 26, 35, 39]:
                expression = expression + " + " + str(wrkr3_c2)

            ##wrkr2_c23
            if auto_own_one in [5, 8, 9, 12, 13, 18, 21, 22, 25, 26, 31, 34, 35, 38, 39]:
                if len(wrkr2_c23) == 1:
                    expression = expression + " + " + str(wrkr2_c23)
                else:
                    for i in range(0, 14):
                        expression = expression + " + " + wrkr2_c23[i] + "*(mo29.eq." + str(1 + i) + ")"


            ##lrg_c2
            if (((auto_own_one - 1) % 13) + 1) >= 6:
                expression = expression + " + " + str(lrg_c2)

            third_length = int((expression.count("+") + 1) / 3)
            expression_1 = ("+").join(expression.split("+")[0:third_length]).strip()
            expression_2 = ("+").join(expression.split("+")[third_length:(third_length * 2)]).strip()
            expression_3 = ("+").join(expression.split("+")[(third_length * 2):]).strip()

            #TEMP1
            spec_as_dict["expression"] = expression_1
            spec_as_dict["result"] = "mo44"
            report = compute_matrix(spec_as_dict)

            #TEMP2
            spec_as_dict["expression"] = expression_2
            spec_as_dict["result"] = "mo45"
            report = compute_matrix(spec_as_dict)

            #TEMP3
            spec_as_dict["expression"] = expression_3
            spec_as_dict["result"] = "mo46"
            report = compute_matrix(spec_as_dict)

            spec_as_dict["expression"] = "mo44 + mo45 + mo46"
            spec_as_dict["result"] = "mo" + str(auto_own_one + 481)
            report = compute_matrix(spec_as_dict)

## mo521-mo559 - Store utility value while for AutoOwn=3 for various HHSize, NumWorkers, IncomeCat
def Calculate_AutoOwnership_3Cars(self, AutoOwnCoeff):
    with _m.logbook_trace("Calculate AutoOwnership 3 Cars - Utilities"):
        print "--------Calculate_AutoOwnership_3Cars, " + str(datetime.now().strftime('%H:%M:%S'))
        NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
        compute_matrix = _m.Modeller().tool(NAMESPACE)

        bias3 = AutoOwnCoeff.get('3bias', [0])
        wrkrs_c3 = AutoOwnCoeff.get('wrkrs_c3', [0])

        dens_c3 = AutoOwnCoeff.get('dens_c3', [0])[0]
        van_c3 = AutoOwnCoeff.get('van_c3', [0])[0]
        rur_c3 = AutoOwnCoeff.get('rur_c3', [0])[0]
        lrg_c3 = AutoOwnCoeff.get('lrg_c3', [0])[0]
        crsh500p3 = AutoOwnCoeff.get('crsh500p3', [0])[0]

        spec_as_dict = {
            "expression": "EXPRESSION",
            "result": "RESULT",
            "constraint": {
                "by_value": None,
                "by_zone": {
                    "origins": None,
                    "destinations": None
                }
            },
            "aggregation": {
                "origins": None,
                "destinations": None
            },
            "type": "MATRIX_CALCULATION"
        }

        for auto_own_one in range(1, 40):

            expression = str(dens_c3) + "*mo16 + " + \
                         str(van_c3) + "*(gy(p).eq.4) + " + \
                         str(rur_c3) + "*(gy(p).gt.10)*(gy(p).lt.15) + " + \
                         str(crsh500p3) + "*(mo394.gt.1)"

            if len(bias3) == 1:
                expression = expression + " + " + bias3[0]
            else:
                for i in range(0, 14):
                    expression = expression + " + " + bias3[i] + "*(gy(p).eq." + str(1 + i) + ")"

            ##wrkrs_c3
            if (((auto_own_one - 1) % 13) + 1) in [2, 4, 7, 11]:
                if len(wrkrs_c3) == 1:
                    expression = expression + " + " + \
                                 str(wrkrs_c3)
                else:
                    for i in range(0, 14):
                        expression = expression + " + " + wrkrs_c3[i] + "*(gy(p).eq." + str(1 + i) + ")"

            if (((auto_own_one - 1) % 13) + 1) in [5, 8, 12]:
                if len(wrkrs_c3) == 1:
                    expression = expression + " + " + \
                                 str(wrkrs_c3) + "*2"
                else:
                    for i in range(0, 14):
                        expression = expression + " + " + wrkrs_c3[i] + "*2*(gy(p).eq." + str(1 + i) + ")"

            if (((auto_own_one - 1) % 13) + 1) in [9, 13]:
                if len(wrkrs_c3) == 1:
                    expression = expression + " + " + \
                                 str(wrkrs_c3) + "*3"
                else:
                    for i in range(0, 14):
                        expression = expression + " + " + wrkrs_c3[i] + "*3*(gy(p).eq." + str(1 + i) + ")"


            ##lrg_c2
            if (((auto_own_one - 1) % 13) + 1) >= 6:
                #print ((auto_own_one-1)%13),auto_own_one
                expression = expression + " + " + str(lrg_c3)

            third_length = int((expression.count("+") + 1) / 3)
            expression_1 = ("+").join(expression.split("+")[0:third_length]).strip()
            expression_2 = ("+").join(expression.split("+")[third_length:(third_length * 2)]).strip()
            expression_3 = ("+").join(expression.split("+")[(third_length * 2):]).strip()

            spec_as_dict["expression"] = expression_1
            spec_as_dict["result"] = "mo44"
            report = compute_matrix(spec_as_dict)

            spec_as_dict["expression"] = expression_2
            spec_as_dict["result"] = "mo45"
            report = compute_matrix(spec_as_dict)

            spec_as_dict["expression"] = expression_3
            spec_as_dict["result"] = "mo46"
            report = compute_matrix(spec_as_dict)

            spec_as_dict["expression"] = "mo44 + mo45 + mo46"
            spec_as_dict["result"] = "mo" + str(auto_own_one + 520)
            report = compute_matrix(spec_as_dict)

## mo560-mo715 - Calculated probabilities of having a AutoOwnership 0-3 for HHSize, NumWorkers, IncomeCat
def Calculate_Probabilities(self, AutoOwnCoeff):
    with _m.logbook_trace("Calculate_Probabilities"):
        print "--------Calculate_Probabilities, " + str(datetime.now().strftime('%H:%M:%S'))
        NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
        compute_matrix = _m.Modeller().tool(NAMESPACE)

        spec_as_dict = {
            "expression": "EXPRESSION",
            "result": "RESULT",
            "constraint": {
                "by_value": None,
                "by_zone": {
                    "origins": None,
                    "destinations": None
                }
            },
            "aggregation": {
                "origins": None,
                "destinations": None
            },
            "type": "MATRIX_CALCULATION"
        }

        theta = AutoOwnCoeff.get('theta1', [0])[0]
        utility_mo_num = 404
        result_mo_num = 560
        tiny = str(0.0000001)
        e = str(2.71828182846)

        for x in range(0,39):
            auto = [0*39 + 404 + x, 1*39 + 404 + x, 2*39 + 404 + x, 3*39 + 404 + x]
            expression = [
                            "(" + e + "^(mo"+ str(auto[0]) +")/(" + e + "^(mo" + str(auto[0]) + ") + " + tiny + " )) * ((" + e + "^(mo" + str(auto[0]) + "))^" + theta + " / ( (" + e + "^mo" + str(auto[0]) + ")^" + theta + " + (" + e + "^(mo" + str(auto[1]) + ") + " + e + "^(mo" + str(auto[2]) + ") + " + e + "^(mo" + str(auto[3]) + "))^" + theta + " ) )",
                            "(" + e + "^(mo"+ str(auto[1]) +")/(" + e + "^mo" + str(auto[1]) + " + " + e + "^mo" + str(auto[2]) + " + " + e + "^mo" + str(auto[3]) + " + " + tiny + " )) *(((" + e + "^(mo" + str(auto[1]) + ") + " + e + "^(mo" + str(auto[2]) + ") + " + e + "^(mo" + str(auto[3]) + "))^" + theta + " ) / ( (" + e + "^mo" + str(auto[0]) + ")^" + theta + " + (" + e + "^(mo" + str(auto[1]) + ") + " + e + "^(mo" + str(auto[2]) + ") + " + e + "^(mo" + str(auto[3]) + "))^" + theta + " ) )",
                            "(" + e + "^(mo"+ str(auto[2]) +")/(" + e + "^mo" + str(auto[1]) + " + " + e + "^mo" + str(auto[2]) + " + " + e + "^mo" + str(auto[3]) + " + " + tiny + " )) *(((" + e + "^(mo" + str(auto[1]) + ") + " + e + "^(mo" + str(auto[2]) + ") + " + e + "^(mo" + str(auto[3]) + "))^" + theta + " ) / ( (" + e + "^mo" + str(auto[0]) + ")^" + theta + " + (" + e + "^(mo" + str(auto[1]) + ") + " + e + "^(mo" + str(auto[2]) + ") + " + e + "^(mo" + str(auto[3]) + "))^" + theta + " ) )",
                            "(" + e + "^(mo"+ str(auto[3]) +")/(" + e + "^mo" + str(auto[1]) + " + " + e + "^mo" + str(auto[2]) + " + " + e + "^mo" + str(auto[3]) + " + " + tiny + " )) *(((" + e + "^(mo" + str(auto[1]) + ") + " + e + "^(mo" + str(auto[2]) + ") + " + e + "^(mo" + str(auto[3]) + "))^" + theta + " ) / ( (" + e + "^mo" + str(auto[0]) + ")^" + theta + " + (" + e + "^(mo" + str(auto[1]) + ") + " + e + "^(mo" + str(auto[2]) + ") + " + e + "^(mo" + str(auto[3]) + "))^" + theta + " ) )",
                            ]

            for x in range(0,4):
                spec_as_dict["expression"] = expression[x]
                spec_as_dict["result"] = "mo" + str(result_mo_num)
                report = compute_matrix(spec_as_dict)
                result_mo_num = result_mo_num + 1


## mo113-mo268 - Calculated Number of Households Per Worker, Per Income and Per Auto Ownership Category
def Calculate_AutoOwnership_PerHH(self):
    with _m.logbook_trace("Calculate AutoOwnership Categories"):
        print "--------Calculate_AutoOwnership, " + str(datetime.now().strftime('%H:%M:%S'))
        NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
        compute_matrix = _m.Modeller().tool(NAMESPACE)

        spec_as_dict = {
            "expression": "EXPRESSION",
            "result": "RESULT",
            "constraint": {
                "by_value": None,
                "by_zone": {
                    "origins": None,
                    "destinations": None
                }
            },
            "aggregation": {
                "origins": None,
                "destinations": None
            },
            "type": "MATRIX_CALCULATION"
        }

        count = 0
        for i in range(0, 39):
            for j in range(0, 4):
                spec_as_dict["expression"] = "mo" + str(74 + i) + "* mo" + str(560 + count)
                spec_as_dict["result"] = "mo" + str(113 + i + 39 * j)
                report = compute_matrix(spec_as_dict)
                count = count + 1

## mo716-mo718 - Calculated Number of Auto Per HH Size
def Autos_PerHHSize(self):
    with _m.logbook_trace("Autos_PerHHSize"):
        print "--------Autos_PerHHSize, " + str(datetime.now().strftime('%H:%M:%S'))
        NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
        compute_matrix = _m.Modeller().tool(NAMESPACE)

        spec_as_dict = {
            "expression": "EXPRESSION",
            "result": "RESULT",
            "constraint": {
                "by_value": None,
                "by_zone": {
                    "origins": None,
                    "destinations": None
                }
            },
            "aggregation": {
                "origins": None,
                "destinations": None
            },
            "type": "MATRIX_CALCULATION"
        }

        ## Loop each set of Auto Ownership classification and perform summation.
        for x in range(0, 3):
            expression = ""
            for i in range(281 + x * 12, 281 + x * 12 + 12):
                expression = expression + "mo" + str(i) + " + "
            expression = expression + " 0"
            spec_as_dict["expression"] = expression
            spec_as_dict["result"] = "mo" + str(x + 716)
            report = compute_matrix(spec_as_dict)
