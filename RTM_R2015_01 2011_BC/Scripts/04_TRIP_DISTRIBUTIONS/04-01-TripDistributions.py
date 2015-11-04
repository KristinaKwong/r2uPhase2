##--------------------------------------------------
##--TransLink Phase 2 Regional Transportation Model - HDR
##--04-01-TripDistributions.PY
##--Path: translink.emme.tripdistributions
##--Purpose of 04-01-TripDistributions: run distribution component of RTM
##--------------------------------------------------
##--Last modified 2014-06-13 Kevin Bragg (INRO)
##--Reason: Changed to use the 4.1.2 namespace of
##          matrix balancing multiple productions
##          Added tool page interface and run
##--Last modified 2014-04-07 Kevin Bragg (INRO)
##--Reason: Add parameters for max iterations of
##          distribution and assignment steps
##--Last modified 2014-02-14 Kevin Bragg (INRO)
##--Reason: Update to Emme 4.0 namespaces
##          Code cleanup PEP 8 compliance
##--Last modified 2013-09-03 Rhys Wolff (HDR)
##--Last modification reason - add comments and notes
##--Added option to include cost/km variation (store in ms101)
##---------------------------------------------------
##--Called by: 00_00_RUN_ALL.PY
##--Calls:     None
##--Accesses:  None
##--Outputs: 04-01_OUTPUT_RESULTS.txt
##---------------------------------------------------
##--Status/additional notes:  Added option to include cost/km variation
##--Supersedes all earlier versions of 04-01-TripDistributions
##---------------------------------------------------

import inro.modeller as _modeller

import os
import traceback as _traceback
from datetime import datetime

# Distribution coefficients and proportions
hwld = str(-0.072)    #Home-based work 1
hwmd = str(-0.077)    #Home-based work 2
hwhd = str(-0.072)    #Home-based work 3
hund = str(-0.049)    #Home-based university
hscd = str(-0.190)    #Home-based school
hshd = str(-0.164)    #Home-based shopping
hpbd = str(-0.120)    #Home-based personal business
hsod = str(-0.117)    #Home-based social
hesd = str(-0.174)    #Home-based escort
nhwd = str(-0.106)    #Non-home-based work
nhod = str(-0.138)    #Non-home-based other


class TripDistributions(_modeller.Tool()):
    max_iterations = _modeller.Attribute(int)
    tool_run_msg = _modeller.Attribute(unicode)

    def __init__(self):
        self.max_iterations = 50

    def page(self):
        start_path = os.path.dirname(_modeller.Modeller().emmebank.path)
        pb = _modeller.ToolPageBuilder(
            self, title="Trip Distributions",
            description="""Inputs matrices, calculates impedances and
            balances matrices
            <br>Data Needed from a prior Module:
            <br>mo161-mo265, md42-md52""",
            branding_text="TransLink")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        pb.add_text_box("max_iterations", size=10,
                        title="Max iterations:")

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            root_directory = os.path.dirname(_modeller.Modeller().emmebank.path)
            self.__call__(root_directory, self.max_iterations)
            run_msg = "Tool completed"
            self.tool_run_msg = _modeller.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _modeller.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_modeller.logbook_trace("04-01 - Trip Distributions")
    def __call__(self, root_directory, max_iterations):
        print "----04-01 - Trip Distributions: " + str(datetime.now().strftime('%H:%M:%S'))

        output_file = os.path.join(root_directory, "04_TRIP_DISTRIBUTIONS/Outputs/04-01_OUTPUT_RESULTS.txt")

        # Matrix Impedance Calculation
        self.impedance_calcs()

        # Matrix Balancing
        # Lists need to be in a consistent order:
        # HBWL, HBWM, HBWH, HBU, HBSCHOOL, HBSHOP, HBPB, HBSOC, HBESC, NHBW, NHBO

        ## NOTE THE DIFFERENT RANGE OF NUMBERS FOR THE HBU BALANCING MO_LIST BECAUSE
        mo_list = [
            ["mo161", "mo164", "mo167+mo170"], #HBWL
            ["mo162", "mo165", "mo168+mo171"], #HBWM
            ["mo163", "mo166", "mo169+mo172"], #HBWH
            ["mo915", "mo918", "mo921+mo924", "mo916", "mo919", "mo922+mo925", "mo917", "mo920", "mo923+mo926"],
            #HBU
            ["mo197", "mo200", "mo203+mo206", "mo198", "mo201", "mo204+mo207", "mo199", "mo202", "mo205+mo208"],
            #HBSCHOOL
            ["mo209", "mo212", "mo215+mo218", "mo210", "mo213", "mo216+mo219", "mo211", "mo214", "mo217+mo220"],
            #HBSHOP
            ["mo221", "mo224", "mo227+mo230", "mo222", "mo225", "mo228+mo231", "mo223", "mo226", "mo229+mo232"],
            #HBPB
            ["mo233", "mo236", "mo239+mo242", "mo234", "mo237", "mo240+mo243", "mo235", "mo238", "mo241+mo244"],
            #HBSOC
            ["mo245", "mo248", "mo251+mo254", "mo246", "mo249", "mo252+mo255", "mo247", "mo250", "mo253+mo256"],
            #HBESCORT
            ["mo173+mo174+mo175", "mo176+mo177+mo178", "mo179+mo182+mo180+mo183+mo181+mo184"], #NHBW
            ["mo257+mo258+mo259", "mo260+mo261+mo262", "mo263+mo266+mo264+mo267+mo265+mo268"] #NHBO
        ]

        md_list = [
            ["md42"], #HBWL
            ["md43"], #HBWM
            ["md44"], #HBWH
            ["md46"], #HBU
            ["md47"], #HBSCHOOL
            ["md48"], #HBSHOP
            ["md49"], #HBPB
            ["md50"], #HBSOC
            ["md51"], #HBESC
            ["md45"], #NHBW
            ["md52"] #NHBO
        ]

        impedance_list = [
            ["mf210"], #HBWL
            ["mf211"], #HBWM
            ["mf212"], #HBWH
            ["mf213"], #HBU
            ["mf214"], #HBSCHOOL
            ["mf215"], #HBSHOP
            ["mf216"], #HBPB
            ["mf217"], #HBSOC
            ["mf218"], #HBESC
            ["mf219"], #NHBW
            ["mf220"]  #NHBO
        ]

        output_list = [
            ["mf241", "mf242", "mf243"], #HBWL
            ["mf244", "mf245", "mf246"], #HBWM
            ["mf247", "mf248", "mf249"], #HBWH
            ["mf250", "mf251", "mf252", "mf253", "mf254", "mf255", "mf256", "mf257", "mf258"], #HBU
            ["mf259", "mf260", "mf261", "mf262", "mf263", "mf264", "mf265", "mf266", "mf267"], #HBSCHOOL
            ["mf268", "mf269", "mf270", "mf271", "mf272", "mf273", "mf274", "mf275", "mf276"], #HBSHOP
            ["mf277", "mf278", "mf279", "mf280", "mf281", "mf282", "mf283", "mf284", "mf285"], #HBPB
            ["mf286", "mf287", "mf288", "mf289", "mf290", "mf291", "mf292", "mf293", "mf294"], #HBSOC
            ["mf295", "mf296", "mf297", "mf298", "mf299", "mf300", "mf301", "mf302", "mf303"], #HBESCORT
            ["mf304", "mf305", "mf306"], #NHBW
            ["mf307", "mf308", "mf309"] #NHBO
        ]

        for i in range(0, 11):
            self.matrix_balancing(mo_list[i], md_list[i], impedance_list[i], output_list[i], max_iterations)

        # Transpose Matrices mfs 241 thru 303 and store in mfs 310 thru 372

        self.transpose_full_matrices()

        ##EXPORT OR OUTPUT MATRICES AS DESIRED:
        # ## Output results
        self.output_results(output_file)

        # ## Export Matrices to CSV
        self.export_matrices(output_file)

    #Export all mo matrices to CSV
    def export_matrices(self, output_file):
        with _modeller.logbook_trace("Export_Matrices"):
            print "--------Export_Matrices, " + str(datetime.now().strftime('%H:%M:%S'))
            ExportToCSV = _modeller.Modeller().tool("translink.emme.stage4.step9.exporttocsv")
            list_of_matrices = ["md" + str(i) for i in range(5, 12) + range(20, 26) + range(31, 53)] + ["mo" + str(i)
                                                                                                        for i in
                                                                                                        range(915, 927)]
            ExportToCSV(list_of_matrices, output_file)

            ##    Outputs results matrix to a file

    def output_results(self, output_file):
        with _modeller.logbook_trace("Output Results"):
            print "--------Output_Results, " + str(datetime.now().strftime('%H:%M:%S'))
            ##    Create emmebank object
            my_modeller = _modeller.Modeller()
            my_emmebank = my_modeller.desktop.data_explorer().active_database().core_emmebank

            Output_File = output_file.replace(",", "")
            Output_File_GY = output_file.replace(",", "").replace(".", "_GY.")
            Output_File_GU = output_file.replace(",", "").replace(".", "_GU.")

            ##    List to hold matrix objects
            md_value = []

            ##    Loop to append all result matrices onto the variable 'md_value'
            for mo_num in [24, 25] + range(31, 53):
                md_value.append(my_emmebank.matrix("md" + str(mo_num)))


            ##    Export matrices using the appended list of md_value matrices
            export_matrices = _modeller.Modeller().tool(
                "inro.emme.data.matrix.export_matrices")

            ## Export all matrix data
            export_matrices(export_file=Output_File,
                            field_separator=' ',
                            matrices=md_value,
                            export_format="PROMPT_DATA_FORMAT",
                            skip_default_values=True,
                            full_matrix_line_format="ONE_ENTRY_PER_LINE")

            ## Export matrix data aggregated to the gy ensemble
            export_matrices(export_file=Output_File_GY,
                            field_separator=' ',
                            matrices=md_value,
                            partition_aggregation={'destinations': 'gy', 'operator': 'sum'},
                            export_format="PROMPT_DATA_FORMAT",
                            skip_default_values=True,
                            full_matrix_line_format="ONE_ENTRY_PER_LINE")

            ## Export matrix data aggregated to the gu ensemble
            export_matrices(export_file=Output_File_GU,
                            field_separator=' ',
                            matrices=md_value,
                            partition_aggregation={'destinations': 'gu', 'operator': 'sum'},
                            export_format="PROMPT_DATA_FORMAT",
                            skip_default_values=True,
                            full_matrix_line_format="ONE_ENTRY_PER_LINE")

            ## Append the inputted data sources to each of the Output Files
            for Output in [Output_File, Output_File_GY, Output_File_GU]:
                f = open(Output, 'a')
                f.write("c ------Data Sources:\n")
                f.write("c " + Output_File + "\n")
                f.close()

                ##    Open up window with the OutputFile Selected
                # No, no random pop-up explorer.
                #print "----------------OutputFile: ", Output_File
                #subprocess.Popen(r'explorer /select, ' + OutputFile.replace("/","\\").replace(",","") + '"')

                ## Transpose mfs function for mf241 thru

    def transpose_full_matrices(self):
        with _modeller.logbook_trace("transposemfs"):
            print "--------transposemfs, " + str(datetime.now())
            NAMESPACE = "inro.emme.data.matrix.copy_matrix"
            TRANNAMESPACE = "inro.emme.data.matrix.transpose_matrix"
            copy_matrix = _modeller.Modeller().tool(NAMESPACE)
            transpose_matrix = _modeller.Modeller().tool(TRANNAMESPACE)
            eb = _modeller.Modeller().emmebank
            matrixnum = 241
            newmatnum = 310
            for i in range(63):
                matrix_one = eb.matrix("mf" + str(matrixnum + i))
                matrix_two = copy_matrix(from_matrix=matrix_one, matrix_id="mf" + str(newmatnum + i))
                matrix_three = eb.matrix("mf" + str(newmatnum + i))
                transpose_matrix(matrix=matrix_three)
                # matrix transpose calculation
            NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
            compute_matrix = _modeller.Modeller().tool(NAMESPACE)

            spec_dict = {
                "expression": "1",
                "result": "mf201",
                "constraint": {"by_value": None, "by_zone": None},
                "aggregation": {"origins": None, "destinations": None},
                "type": "MATRIX_CALCULATION"
            }
            matrixnum = 241
            newmatnum = 310
            for i in range(63):
                expression1 = "0.5*mf" + str(newmatnum + i) + "+0.5*mf" + str(matrixnum + i)
                result = "mf" + str(newmatnum + i)
                spec_dict["expression"] = expression1
                spec_dict["result"] = result
                report = compute_matrix(spec_dict)


                ##     Matrix balancing. Need list of input mo, md and impedance (mf) matrices, as well as output matrices

    @_modeller.logbook_trace("Run matrix balancing to multiple productions")
    def matrix_balancing(self, mo_list, md_list, impedance_list, output_list, max_iterations):
        print "--------balmprod, " + str(datetime.now())

        # Perform matrix calculation to aggregate matrices.
        compute_matrix = _modeller.Modeller().tool(
            "inro.emme.matrix_calculation.matrix_calculator")
        spec_dict_matcalc = {
            "expression": "",
            "result": "",
            "constraint": {
                "by_value": None,
                "by_zone": {"origins": None, "destinations": None}
            },
            "aggregation": {"origins": None, "destinations": None},
            "type": "MATRIX_CALCULATION"
        }

        # Used to allocate results to  the 'scratch' matrices
        num_scratch = 0
        results = ["mo927", "mo928", "mo929", "mo931"]

        # loops through mo_list for any list items that are expressions
        #  (contains '+') adding mo matrices up for aggregation.
        # Performs calulation and saves result in a scratch matrix.
        # then inserts scratch matrix instead of the initial expresssion
        for i in range(0, len(mo_list)):
            if "+" in mo_list[i]:
                spec_dict_matcalc["expression"] = mo_list[i]
                spec_dict_matcalc["result"] = results[num_scratch]
                report = compute_matrix(spec_dict_matcalc)
                mo_list[i] = results[num_scratch]
                num_scratch = num_scratch + 1

        #Begin balmprod
        # Prior to Emme 4.1.2 Matrix balancing to multiple productions
        # was distributed as a separate toolbox with namespace:
        # "inro.support.case6163.matrix_balancing_multiple_productions"
        balancing_multiple_productions = _modeller.Modeller().tool(
            "inro.emme.matrix_calculation.balancing_multiple_productions")

        spec_dict_matbal = {
            "type": "MATRIX_BALANCING_MULTIPLE_PRODUCTIONS",
            "destination_totals": "destinations",
            "classes": [],
            "destination_coefficients": None,
            "max_iterations": max_iterations,
            "max_relative_error": 0.0001
        }

        #assign values for matrix balancing
        spec_dict_matbal["destination_totals"] = md_list[0]
        for mo, output in zip(mo_list, output_list):
            class_spec = {
                "origin_totals": mo,
                "od_values_to_balance": impedance_list[0],
                "results": {
                    "origin_coefficients": None,
                    "od_balanced_values": output
                }
            }
            spec_dict_matbal["classes"].append(class_spec)
        balancing_multiple_productions(spec_dict_matbal)

    #Calculate impedances for each purpose based on the original distribution macro distestall.mac
    @_modeller.logbook_trace("Calculate impedances")
    def impedance_calcs(self):
        print "--------Impedance_Calcs, " + str(datetime.now().strftime('%H:%M:%S'))
        NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"

        compute_matrix = _modeller.Modeller().tool(NAMESPACE)

        print "--------Impedance_Calcs, " + str(datetime.now().strftime('%H:%M:%S'))
        spec_dict = {
            "expression": "EXPRESSION",
            "result": "RESULT",
            "constraint": {
                "by_value": None,
                "by_zone": {"origins": None, "destinations": None}
            },
            "aggregation": {"origins": None, "destinations": None},
            "type": "MATRIX_CALCULATION"
        }

        print "--------Impedance_Calcs, " + str(datetime.now().strftime('%H:%M:%S'))

        print "--------HBWL-Purpose Distribution, " + str(datetime.now().strftime('%H:%M:%S'))
        #Calculate transit impedance
        expression = "((mf164+(mf163*2))*ms50)+(((mf167*2)+mf168)*(1-ms50))"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf925"
        report = compute_matrix(spec_dict)
        #Apply transit impedance constraint
        self.Impedance_Transit()
        #Calculate overall impedance using distribution by purpose coefficient and AM proportional factor
        amexpression = "ms50*(mf101+(ms148*ms103)*mf102*ms104+(ms102+ms101*ms145)*mf100*ms104)"
        spec_dict["expression"] = amexpression
        spec_dict["result"] = "mf210"
        report = compute_matrix(spec_dict)
        #Midday is calculated as (1-AM proportional factor)
        mdexpression = "mf210+((1-ms50)*(mf104+(ms148*ms103)*mf105*ms104+(ms102+ms101*ms145)*mf103*ms104)+(mo27/2+md27/2)*ms104)"
        spec_dict["expression"] = mdexpression
        spec_dict["result"] = "mf210"
        report = compute_matrix(spec_dict)
        #Combine AM and midday expressions
        expression = "exp(" + str(hwld) + "*mf210)"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf210"
        report = compute_matrix(spec_dict)
        #Multiply by purpose and OD-specific Rij factors
        expression = "(mf210+exp(" + str(hwld) + "*(mf925+ms104*mf160)))*mf169"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf210"
        report = compute_matrix(spec_dict)

        print "--------HBWM-Purpose Distribution, " + str(datetime.now().strftime('%H:%M:%S'))
        expression = "((mf164+(mf163*2))*ms50)+(((mf167*2)+mf168)*(1-ms50))"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf925"
        report = compute_matrix(spec_dict)
        #Apply transit impedance constraint
        self.Impedance_Transit()
        #Calculate overall impedance using distribution by purpose coefficient and AM proportional factor
        amexpression = "ms50*(mf101+(ms148*ms103)*mf102*ms105+(ms102+ms101*ms145)*mf100*ms105)"
        spec_dict["expression"] = amexpression
        spec_dict["result"] = "mf211"
        report = compute_matrix(spec_dict)
        #Midday is calculated as (1-AM proportional factor)
        mdexpression = "mf211+((1-ms50)*(mf104+(ms148*ms103)*mf105*ms105+(ms102+ms101*ms145)*mf103*ms105)+(mo27/2+md27/2)*ms105)"
        spec_dict["expression"] = mdexpression
        spec_dict["result"] = "mf211"
        report = compute_matrix(spec_dict)
        #Combine AM and midday expressions
        expression = "exp(" + str(hwmd) + "*mf211)"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf211"
        report = compute_matrix(spec_dict)
        #Multiply by purpose and OD-specific Rij factors
        expression = "(mf211+exp(" + str(hwmd) + "*(mf925+ms105*mf160)))*mf170"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf211"
        report = compute_matrix(spec_dict)

        print "--------hbwh-Purpose Distribution, " + str(datetime.now().strftime('%H:%M:%S'))
        expression = "((mf164+(mf163*2))*ms50)+(((mf167*2)+mf168)*(1-ms50))"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf925"
        report = compute_matrix(spec_dict)
        #Apply transit impedance constraint
        self.Impedance_Transit()
        #Calculate overall impedance using distribution by purpose coefficient and AM proportional factor
        amexpression = "ms50*(mf101+(ms148*ms103)*mf102*ms106+(ms102+ms101*ms145)*mf100*ms106)"
        spec_dict["expression"] = amexpression
        spec_dict["result"] = "mf212"
        report = compute_matrix(spec_dict)
        #Midday is calculated as (1-AM proportional factor)
        mdexpression = "mf212+((1-ms50)*(mf104+(ms148*ms103)*mf105*ms106+(ms102+ms101*ms145)*mf103*ms106)+(mo27/2+md27/2)*ms106)"
        spec_dict["expression"] = mdexpression
        spec_dict["result"] = "mf212"
        report = compute_matrix(spec_dict)
        #Combine AM and midday expressions
        expression = "exp(" + str(hwhd) + "*mf212)"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf212"
        report = compute_matrix(spec_dict)
        #Multiply by purpose and OD-specific Rij factors
        expression = "(mf212+exp(" + str(hwhd) + "*(mf925+ms106*mf160)))*mf171"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf212"
        report = compute_matrix(spec_dict)

        print "--------hbu_-Purpose Distribution, " + str(datetime.now().strftime('%H:%M:%S'))
        expression = "((mf164+(mf163*2))*ms51)+(((mf167*2)+mf168)*(1-ms51))"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf925"
        report = compute_matrix(spec_dict)
        #Apply transit impedance constraint
        self.Impedance_Transit()
        #Calculate overall impedance using distribution by purpose coefficient and AM proportional factor
        amexpression = "ms51*(mf101+(ms148*ms103)*mf102*ms107+(ms102+ms101*ms145)*mf100*ms107)"
        spec_dict["expression"] = amexpression
        spec_dict["result"] = "mf213"
        report = compute_matrix(spec_dict)
        #Midday is calculated as (1-AM proportional factor)
        mdexpression = "mf213+((1-ms51)*(mf104+(ms148*ms103)*mf105*ms107+(ms102+ms101*ms145)*mf103*ms107)+(mo28/2+md28/2)*ms107)"
        spec_dict["expression"] = mdexpression
        spec_dict["result"] = "mf213"
        report = compute_matrix(spec_dict)
        #Combine AM and midday expressions
        expression = "exp(" + str(hund) + "*mf213)"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf213"
        report = compute_matrix(spec_dict)
        #Multiply by purpose and OD-specific Rij factors
        expression = "(mf213+exp(" + str(hund) + "*(mf925+ms107*mf160*0.25)))*mf172"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf213"
        report = compute_matrix(spec_dict)

        print "--------hbsc-Purpose Distribution, " + str(datetime.now().strftime('%H:%M:%S'))
        expression = "((mf164+(mf163*2))*ms52)+(((mf167*2)+mf168)*(1-ms52))"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf925"
        report = compute_matrix(spec_dict)
        #Apply transit impedance constraint
        self.Impedance_Transit()
        #Calculate overall impedance using distribution by purpose coefficient and AM proportional factor
        amexpression = "ms52*(mf101+(ms148*ms103)*mf102*ms108+(ms102+ms101*ms145)*mf100*ms108)"
        spec_dict["expression"] = amexpression
        spec_dict["result"] = "mf214"
        report = compute_matrix(spec_dict)
        #Midday is calculated as (1-AM proportional factor)
        mdexpression = "mf214+((1-ms52)*(mf104+(ms148*ms103)*mf105*ms108+(ms102+ms101*ms145)*mf103*ms108)+(mo28/2+md28/2)*ms108)"
        spec_dict["expression"] = mdexpression
        spec_dict["result"] = "mf214"
        report = compute_matrix(spec_dict)
        #Combine AM and midday expressions
        expression = "exp(" + str(hscd) + "*mf214)"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf214"
        report = compute_matrix(spec_dict)
        #Multiply by purpose and OD-specific Rij factors
        expression = "(mf214+exp(" + str(hscd) + "*(mf925+ms108*mf160*0.65)))*mf173"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf214"
        report = compute_matrix(spec_dict)

        print "--------hbsh-Purpose Distribution, " + str(datetime.now().strftime('%H:%M:%S'))
        expression = "((mf164+(mf163*2))*ms53)+(((mf167*2)+mf168)*(1-ms53))"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf925"
        report = compute_matrix(spec_dict)
        #Apply transit impedance constraint
        self.Impedance_Transit()
        #Calculate overall impedance using distribution by purpose coefficient and AM proportional factor
        amexpression = "ms53*(mf101+ms103*mf102*ms109+(ms102+ms101)*mf100*ms109)"
        spec_dict["expression"] = amexpression
        spec_dict["result"] = "mf215"
        report = compute_matrix(spec_dict)
        #Midday is calculated as (1-AM proportional factor)
        mdexpression = "mf215+((1-ms53)*(mf104+ms103*mf105*ms109+(ms102+ms101)*mf103*ms109)+(mo28/2+md28/2)*ms109)"
        spec_dict["expression"] = mdexpression
        spec_dict["result"] = "mf215"
        report = compute_matrix(spec_dict)
        #Combine AM and midday expressions
        expression = "exp(" + str(hshd) + "*mf215)"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf215"
        report = compute_matrix(spec_dict)
        #Multiply by purpose and OD-specific Rij factors
        expression = "(mf215+exp(" + str(hshd) + "*(mf925+ms109*mf160)))*mf174"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf215"
        report = compute_matrix(spec_dict)

        print "--------hbe_-Purpose Distribution, " + str(datetime.now().strftime('%H:%M:%S'))
        expression = "((mf164+(mf163*2))*ms56)+(((mf167*2)+mf168)*(1-ms56))"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf925"
        report = compute_matrix(spec_dict)
        #Apply transit impedance constraint
        self.Impedance_Transit()
        #Calculate overall impedance using distribution by purpose coefficient and AM proportional factor
        amexpression = "ms56*(mf101+ms103*mf102*ms112+(ms102+ms101)*mf100*ms112)"
        spec_dict["expression"] = amexpression
        spec_dict["result"] = "mf218"
        report = compute_matrix(spec_dict)
        #Midday is calculated as (1-AM proportional factor)
        mdexpression = "mf218+((1-ms56)*(mf104+ms103*mf105*ms112+(ms102+ms101)*mf103*ms112)+(mo28/2+md28/2)*ms112)"
        spec_dict["expression"] = mdexpression
        spec_dict["result"] = "mf218"
        report = compute_matrix(spec_dict)
        #Combine AM and midday expressions
        expression = "exp(" + str(hesd) + "*mf218)"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf218"
        report = compute_matrix(spec_dict)
        #Multiply by purpose and OD-specific Rij factors
        expression = "(mf218+exp(" + str(hesd) + "*(mf925+ms112*mf160)))*mf177"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf218"
        report = compute_matrix(spec_dict)

        print "--------hbso-Purpose Distribution, " + str(datetime.now().strftime('%H:%M:%S'))
        expression = "((mf164+(mf163*2))*ms55)+(((mf167*2)+mf168)*(1-ms55))"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf925"
        report = compute_matrix(spec_dict)
        #Apply transit impedance constraint
        self.Impedance_Transit()
        #Calculate overall impedance using distribution by purpose coefficient and AM proportional factor
        amexpression = "ms55*(mf101+ms103*mf102*ms111+(ms102+ms101)*mf100*ms111)"
        spec_dict["expression"] = amexpression
        spec_dict["result"] = "mf217"
        report = compute_matrix(spec_dict)
        #Midday is calculated as (1-AM proportional factor)
        mdexpression = "mf217+((1-ms55)*(mf104+ms103*mf105*ms111+(ms102+ms101)*mf103*ms111)+(mo28/2+md28/2)*ms111)"
        spec_dict["expression"] = mdexpression
        spec_dict["result"] = "mf217"
        report = compute_matrix(spec_dict)
        #Combine AM and midday expressions
        expression = "exp(" + str(hsod) + "*mf217)"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf217"
        report = compute_matrix(spec_dict)
        #Multiply by purpose and OD-specific Rij factors
        expression = "(mf217+exp(" + str(hsod) + "*(mf925+ms111*mf160)))*mf176"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf217"
        report = compute_matrix(spec_dict)

        print "--------hbpb-Purpose Distribution, " + str(datetime.now().strftime('%H:%M:%S'))
        expression = "((mf164+(mf163*2))*ms54)+(((mf167*2)+mf168)*(1-ms54))"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf925"
        report = compute_matrix(spec_dict)
        #Apply transit impedance constraint
        self.Impedance_Transit()
        #Calculate overall impedance using distribution by purpose coefficient and AM proportional factor
        amexpression = "ms54*(mf101+ms103*mf102*ms110+(ms102+ms101)*mf100*ms110)"
        spec_dict["expression"] = amexpression
        spec_dict["result"] = "mf216"
        report = compute_matrix(spec_dict)
        #Midday is calculated as (1-AM proportional factor)
        mdexpression = "mf216+((1-ms54)*(mf104+ms103*mf105*ms110+(ms102+ms101)*mf103*ms110)+(mo28/2+md28/2)*ms110)"
        spec_dict["expression"] = mdexpression
        spec_dict["result"] = "mf216"
        report = compute_matrix(spec_dict)
        #Combine AM and midday expressions
        expression = "exp(" + str(hpbd) + "*mf216)"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf216"
        report = compute_matrix(spec_dict)
        #Multiply by purpose and OD-specific Rij factors
        expression = "(mf216+exp(" + str(hpbd) + "*(mf925+ms110*mf160)))*mf175"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf216"
        report = compute_matrix(spec_dict)

        print "--------nhbo-Purpose Distribution, " + str(datetime.now().strftime('%H:%M:%S'))
        expression = "((mf164+(mf163*2))*ms58)+(((mf167*2)+mf168)*(1-ms58))"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf925"
        report = compute_matrix(spec_dict)
        #Apply transit impedance constraint
        self.Impedance_Transit()
        #Calculate overall impedance using distribution by purpose coefficient and AM proportional factor
        amexpression = "ms58*(mf101+ms103*mf102*ms114+(ms102+ms101)*mf100*ms114)"
        spec_dict["expression"] = amexpression
        spec_dict["result"] = "mf220"
        report = compute_matrix(spec_dict)
        #Midday is calculated as (1-AM proportional factor)
        mdexpression = "mf220+((1-ms58)*(mf104+ms103*mf105*ms114+(ms102+ms101)*mf103*ms114)+(mo28/2+md28/2)*ms114)"
        spec_dict["expression"] = mdexpression
        spec_dict["result"] = "mf220"
        report = compute_matrix(spec_dict)
        #Combine AM and midday expressions
        expression = "exp(" + str(nhod) + "*mf220)"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf220"
        report = compute_matrix(spec_dict)
        #Multiply by purpose and OD-specific Rij factors
        expression = "(mf220+exp(" + str(nhod) + "*(mf925+ms114*mf160)))*mf179"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf220"
        report = compute_matrix(spec_dict)

        print "--------nhbw-Purpose Distribution, " + str(datetime.now().strftime('%H:%M:%S'))
        expression = "((mf164+(mf163*2))*ms57)+(((mf167*2)+mf168)*(1-ms57))"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf925"
        report = compute_matrix(spec_dict)
        #Apply transit impedance constraint
        self.Impedance_Transit()
        #Calculate overall impedance using distribution by purpose coefficient and AM proportional factor
        amexpression = "ms57*(mf101+ms103*mf102*ms113+(ms102+ms101)*mf100*ms113)"
        spec_dict["expression"] = amexpression
        spec_dict["result"] = "mf219"
        report = compute_matrix(spec_dict)
        #Midday is calculated as (1-AM proportional factor)
        mdexpression = "mf219+((1-ms57)*(mf104+ms103*mf105*ms113+(ms102+ms101)*mf103*ms113)+(mo27/2+md27/2)*ms113)"
        spec_dict["expression"] = mdexpression
        spec_dict["result"] = "mf219"
        report = compute_matrix(spec_dict)
        #Combine AM and midday expressions
        expression = "exp(" + str(nhwd) + "*mf219)"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf219"
        report = compute_matrix(spec_dict)
        #Multiply by purpose and OD-specific Rij factors
        expression = "(mf219+exp(" + str(nhwd) + "*(mf925+ms113*mf160)))*mf178"
        spec_dict["expression"] = expression
        spec_dict["result"] = "mf219"
        report = compute_matrix(spec_dict)

    #Calculate transit impedances (separate procedure because the spec is different - including constraint values)
    @_modeller.logbook_trace("Calculate transit impedances")
    def Impedance_Transit(self):
        print "--------Transit Impedance_Calcs, " + str(datetime.now().strftime('%H:%M:%S'))
        compute_matrix = _modeller.Modeller().tool(
            "inro.emme.matrix_calculation.matrix_calculator")

        spec_dict = {
            "expression": "mf925.max.200",
            "result": "mf925",
            "constraint": {
                "by_value": {
                    "od_values": "mf925",
                    "interval_min": 0.1,
                    "interval_max": 120,
                    "condition": "EXCLUDE"
                },
                "by_zone": None
            },
            "aggregation": {"origins": None, "destinations": None},
            "type": "MATRIX_CALCULATION"
        }
        report = compute_matrix(spec_dict)
