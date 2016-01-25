##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step4.tripdistribution
##--Purpose: Run distribution component of RTM
##---------------------------------------------------------------------
import inro.modeller as _m

import os
import traceback as _traceback

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


class TripDistributions(_m.Tool()):
    max_iterations = _m.Attribute(int)
    tool_run_msg = _m.Attribute(unicode)

    def __init__(self):
        self.max_iterations = 50

    def page(self):
        pb = _m.ToolPageBuilder(
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
            eb = _m.Modeller().emmebank
            self.__call__(eb, self.max_iterations)
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("04-01 - Trip Distributions")
    def __call__(self, eb, max_iterations):
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
        self.output_results(eb)

    @_m.logbook_trace("Output Results")
    def output_results(self, eb):
        output_path = os.path.join(os.path.dirname(eb.path), "04_TRIP_DISTRIBUTIONS", "Outputs")
        output_file =    os.path.join(output_path, "04-01_OUTPUT_RESULTS.txt")
        output_file_gy = os.path.join(output_path, "04-01_OUTPUT_RESULTS_GY.txt")
        output_file_gu = os.path.join(output_path, "04-01_OUTPUT_RESULTS_GU.txt")
        output_file_csv = os.path.join(output_path, "04-01_OUTPUT_RESULTS_matrices.csv")

        util = _m.Modeller().tool("translink.emme.util")
        list_of_matrices = ["md" + str(i) for i in range(5, 12) + range(20, 26) + range(31, 53)]
        list_of_matrices = list_of_matrices  + ["mo" + str(i) for i in range(915, 927)]
        util.export_csv(eb, list_of_matrices, output_file_csv)

        ##    List to hold matrix objects
        md_value = []

        ##    Loop to append all result matrices onto the variable 'md_value'
        for mo_num in [24, 25] + range(31, 53):
            md_value.append(eb.matrix("md" + str(mo_num)))


        ##    Export matrices using the appended list of md_value matrices
        export_matrices = _m.Modeller().tool("inro.emme.data.matrix.export_matrices")

        ## Export all matrix data
        export_matrices(export_file=output_file,
                        field_separator=' ',
                        matrices=md_value,
                        export_format="PROMPT_DATA_FORMAT",
                        skip_default_values=True,
                        full_matrix_line_format="ONE_ENTRY_PER_LINE")

        ## Export matrix data aggregated to the gy ensemble
        export_matrices(export_file=output_file_gy,
                        field_separator=' ',
                        matrices=md_value,
                        partition_aggregation={'destinations': 'gy', 'operator': 'sum'},
                        export_format="PROMPT_DATA_FORMAT",
                        skip_default_values=True,
                        full_matrix_line_format="ONE_ENTRY_PER_LINE")

        ## Export matrix data aggregated to the gu ensemble
        export_matrices(export_file=output_file_gu,
                        field_separator=' ',
                        matrices=md_value,
                        partition_aggregation={'destinations': 'gu', 'operator': 'sum'},
                        export_format="PROMPT_DATA_FORMAT",
                        skip_default_values=True,
                        full_matrix_line_format="ONE_ENTRY_PER_LINE")

        ## Append the inputted data sources to each of the Output Files
        for Output in [output_file, output_file_gy, output_file_gu]:
            f = open(Output, 'a')
            f.write("c ------Data Sources:\n")
            f.write("c " + output_file + "\n")
            f.close()

            ## Transpose mfs function for mf241 thru

    @_m.logbook_trace("transposemfs")
    def transpose_full_matrices(self):
        util = _m.Modeller().tool("translink.emme.util")
        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

        matrixnum = 241
        newmatnum = 310
        specs = []
        for i in range(63):
            result = "mf%d" % (newmatnum + i)
            expression = "0.5 * mf%d + 0.5 * mf%d'" % (matrixnum + i, matrixnum + i)
            specs.append(util.matrix_spec(result, expression))

        report = compute_matrix(specs)

    @_m.logbook_trace("Run matrix balancing to multiple productions")
    def matrix_balancing(self, mo_list, md_list, impedance_list, output_list, max_iterations):
        util = _m.Modeller().tool("translink.emme.util")
        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

        # Used to allocate results to  the 'scratch' matrices
        num_scratch = 0
        results = ["mo927", "mo928", "mo929", "mo931"]

        # loops through mo_list for any list items that are expressions
        #  (contains '+') adding mo matrices up for aggregation.
        # Performs calulation and saves result in a scratch matrix.
        # then inserts scratch matrix instead of the initial expresssion
        specs = []
        for i in range(0, len(mo_list)):
            if "+" in mo_list[i]:
                specs.append(util.matrix_spec(results[num_scratch], mo_list[i]))
                mo_list[i] = results[num_scratch]
                num_scratch = num_scratch + 1
        report = compute_matrix(specs)

        #Begin balmprod
        balancing_multiple_productions = _m.Modeller().tool("inro.emme.matrix_calculation.balancing_multiple_productions")
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
    @_m.logbook_trace("Calculate impedances")
    def impedance_calcs(self):
        util = _m.Modeller().tool("translink.emme.util")
        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

        _m.logbook_trace("HBWL-Purpose Distribution")
        specs = []

        #Calculate transit impedance
        specs.append(util.matrix_spec("mf925", "((mf164+(mf163*2))*ms50)+(((mf167*2)+mf168)*(1-ms50))"))
        specs.append(util.matrix_spec("mf925", "mf925.max.200"))

        #Calculate overall impedance using distribution by purpose coefficient and AM proportional factor
        specs.append(util.matrix_spec("mf210", "ms50*(mf101+(ms148*ms103)*mf102*ms104+(ms102+ms101*ms145)*mf100*ms104)"))

        #Midday is calculated as (1-AM proportional factor)
        specs.append(util.matrix_spec("mf210", "mf210+((1-ms50)*(mf104+(ms148*ms103)*mf105*ms104+(ms102+ms101*ms145)*mf103*ms104)+(mo27/2+md27/2)*ms104)"))

        #Combine AM and midday expressions
        specs.append(util.matrix_spec("mf210", "exp(" + str(hwld) + "*mf210)"))

        #Multiply by purpose and OD-specific Rij factors
        specs.append(util.matrix_spec("mf210", "(mf210+exp(" + str(hwld) + "*(mf925+ms104*mf160)))*mf169"))

        report = compute_matrix(specs)

        _m.logbook_trace("HBWM-Purpose Distribution")
        specs = []

        specs.append(util.matrix_spec("mf925", "((mf164+(mf163*2))*ms50)+(((mf167*2)+mf168)*(1-ms50))"))
        specs.append(util.matrix_spec("mf925", "mf925.max.200"))

        #Calculate overall impedance using distribution by purpose coefficient and AM proportional factor
        specs.append(util.matrix_spec("mf211", "ms50*(mf101+(ms148*ms103)*mf102*ms105+(ms102+ms101*ms145)*mf100*ms105)"))

        #Midday is calculated as (1-AM proportional factor)
        specs.append(util.matrix_spec("mf211", "mf211+((1-ms50)*(mf104+(ms148*ms103)*mf105*ms105+(ms102+ms101*ms145)*mf103*ms105)+(mo27/2+md27/2)*ms105)"))

        #Combine AM and midday expressions
        specs.append(util.matrix_spec("mf211", "exp(" + str(hwmd) + "*mf211)"))

        #Multiply by purpose and OD-specific Rij factors
        specs.append(util.matrix_spec("mf211", "(mf211+exp(" + str(hwmd) + "*(mf925+ms105*mf160)))*mf170"))

        report = compute_matrix(specs)

        _m.logbook_trace("HBWH-Purpose Distribution")
        specs = []

        specs.append(util.matrix_spec("mf925", "((mf164+(mf163*2))*ms50)+(((mf167*2)+mf168)*(1-ms50))"))
        specs.append(util.matrix_spec("mf925", "mf925.max.200"))

        #Calculate overall impedance using distribution by purpose coefficient and AM proportional factor
        specs.append(util.matrix_spec("mf212", "ms50*(mf101+(ms148*ms103)*mf102*ms106+(ms102+ms101*ms145)*mf100*ms106)"))

        #Midday is calculated as (1-AM proportional factor)
        specs.append(util.matrix_spec("mf212", "mf212+((1-ms50)*(mf104+(ms148*ms103)*mf105*ms106+(ms102+ms101*ms145)*mf103*ms106)+(mo27/2+md27/2)*ms106)"))

        #Combine AM and midday expressions
        specs.append(util.matrix_spec("mf212", "exp(" + str(hwhd) + "*mf212)"))

        #Multiply by purpose and OD-specific Rij factors
        specs.append(util.matrix_spec("mf212", "(mf212+exp(" + str(hwhd) + "*(mf925+ms106*mf160)))*mf171"))

        report = compute_matrix(specs)

        _m.logbook_trace("hbu_-Purpose Distribution")
        specs = []

        specs.append(util.matrix_spec("mf925", "((mf164+(mf163*2))*ms51)+(((mf167*2)+mf168)*(1-ms51))"))
        specs.append(util.matrix_spec("mf925", "mf925.max.200"))

        #Calculate overall impedance using distribution by purpose coefficient and AM proportional factor
        specs.append(util.matrix_spec("mf213", "ms51*(mf101+(ms148*ms103)*mf102*ms107+(ms102+ms101*ms145)*mf100*ms107)"))

        #Midday is calculated as (1-AM proportional factor)
        specs.append(util.matrix_spec("mf213", "mf213+((1-ms51)*(mf104+(ms148*ms103)*mf105*ms107+(ms102+ms101*ms145)*mf103*ms107)+(mo28/2+md28/2)*ms107)"))

        #Combine AM and midday expressions
        specs.append(util.matrix_spec("mf213", "exp(" + str(hund) + "*mf213)"))

        #Multiply by purpose and OD-specific Rij factors
        specs.append(util.matrix_spec("mf213", "(mf213+exp(" + str(hund) + "*(mf925+ms107*mf160*0.25)))*mf172"))

        report = compute_matrix(specs)

        _m.logbook_trace("hbsc-Purpose Distribution")
        specs = []

        specs.append(util.matrix_spec("mf925", "((mf164+(mf163*2))*ms52)+(((mf167*2)+mf168)*(1-ms52))"))
        specs.append(util.matrix_spec("mf925", "mf925.max.200"))

        #Calculate overall impedance using distribution by purpose coefficient and AM proportional factor
        specs.append(util.matrix_spec("mf214", "ms52*(mf101+(ms148*ms103)*mf102*ms108+(ms102+ms101*ms145)*mf100*ms108)"))

        #Midday is calculated as (1-AM proportional factor)
        specs.append(util.matrix_spec("mf214", "mf214+((1-ms52)*(mf104+(ms148*ms103)*mf105*ms108+(ms102+ms101*ms145)*mf103*ms108)+(mo28/2+md28/2)*ms108)"))

        #Combine AM and midday expressions
        specs.append(util.matrix_spec("mf214", "exp(" + str(hscd) + "*mf214)"))

        #Multiply by purpose and OD-specific Rij factors
        specs.append(util.matrix_spec("mf214", "(mf214+exp(" + str(hscd) + "*(mf925+ms108*mf160*0.65)))*mf173"))

        report = compute_matrix(specs)

        _m.logbook_trace("hbsh-Purpose Distribution")
        specs = []

        specs.append(util.matrix_spec("mf925", "((mf164+(mf163*2))*ms53)+(((mf167*2)+mf168)*(1-ms53))"))
        specs.append(util.matrix_spec("mf925", "mf925.max.200"))

        #Calculate overall impedance using distribution by purpose coefficient and AM proportional factor
        specs.append(util.matrix_spec("mf215", "ms53*(mf101+ms103*mf102*ms109+(ms102+ms101)*mf100*ms109)"))

        #Midday is calculated as (1-AM proportional factor)
        specs.append(util.matrix_spec("mf215", "mf215+((1-ms53)*(mf104+ms103*mf105*ms109+(ms102+ms101)*mf103*ms109)+(mo28/2+md28/2)*ms109)"))

        #Combine AM and midday expressions
        specs.append(util.matrix_spec("mf215", "exp(" + str(hshd) + "*mf215)"))

        #Multiply by purpose and OD-specific Rij factors
        specs.append(util.matrix_spec("mf215", "(mf215+exp(" + str(hshd) + "*(mf925+ms109*mf160)))*mf174"))

        report = compute_matrix(specs)

        _m.logbook_trace("hbe_-Purpose Distribution")
        specs = []

        specs.append(util.matrix_spec("mf925", "((mf164+(mf163*2))*ms56)+(((mf167*2)+mf168)*(1-ms56))"))
        specs.append(util.matrix_spec("mf925", "mf925.max.200"))

        #Calculate overall impedance using distribution by purpose coefficient and AM proportional factor
        specs.append(util.matrix_spec("mf218", "ms56*(mf101+ms103*mf102*ms112+(ms102+ms101)*mf100*ms112)"))

        #Midday is calculated as (1-AM proportional factor)
        specs.append(util.matrix_spec("mf218", "mf218+((1-ms56)*(mf104+ms103*mf105*ms112+(ms102+ms101)*mf103*ms112)+(mo28/2+md28/2)*ms112)"))

        #Combine AM and midday expressions
        specs.append(util.matrix_spec("mf218", "exp(" + str(hesd) + "*mf218)"))

        #Multiply by purpose and OD-specific Rij factors
        specs.append(util.matrix_spec("mf218", "(mf218+exp(" + str(hesd) + "*(mf925+ms112*mf160)))*mf177"))

        report = compute_matrix(specs)

        _m.logbook_trace("hbso-Purpose Distribution")
        specs = []

        specs.append(util.matrix_spec("mf925", "((mf164+(mf163*2))*ms55)+(((mf167*2)+mf168)*(1-ms55))"))
        specs.append(util.matrix_spec("mf925", "mf925.max.200"))

        #Calculate overall impedance using distribution by purpose coefficient and AM proportional factor
        specs.append(util.matrix_spec("mf217", "ms55*(mf101+ms103*mf102*ms111+(ms102+ms101)*mf100*ms111)"))

        #Midday is calculated as (1-AM proportional factor)
        specs.append(util.matrix_spec("mf217", "mf217+((1-ms55)*(mf104+ms103*mf105*ms111+(ms102+ms101)*mf103*ms111)+(mo28/2+md28/2)*ms111)"))

        #Combine AM and midday expressions
        specs.append(util.matrix_spec("mf217", "exp(" + str(hsod) + "*mf217)"))

        #Multiply by purpose and OD-specific Rij factors
        specs.append(util.matrix_spec("mf217", "(mf217+exp(" + str(hsod) + "*(mf925+ms111*mf160)))*mf176"))

        report = compute_matrix(specs)

        _m.logbook_trace("hbpb-Purpose Distribution")
        specs = []

        specs.append(util.matrix_spec("mf925", "((mf164+(mf163*2))*ms54)+(((mf167*2)+mf168)*(1-ms54))"))
        specs.append(util.matrix_spec("mf925", "mf925.max.200"))

        #Calculate overall impedance using distribution by purpose coefficient and AM proportional factor
        specs.append(util.matrix_spec("mf216", "ms54*(mf101+ms103*mf102*ms110+(ms102+ms101)*mf100*ms110)"))

        #Midday is calculated as (1-AM proportional factor)
        specs.append(util.matrix_spec("mf216", "mf216+((1-ms54)*(mf104+ms103*mf105*ms110+(ms102+ms101)*mf103*ms110)+(mo28/2+md28/2)*ms110)"))

        #Combine AM and midday expressions
        specs.append(util.matrix_spec("mf216", "exp(" + str(hpbd) + "*mf216)"))

        #Multiply by purpose and OD-specific Rij factors
        specs.append(util.matrix_spec("mf216", "(mf216+exp(" + str(hpbd) + "*(mf925+ms110*mf160)))*mf175"))

        report = compute_matrix(specs)

        _m.logbook_trace("nhbo-Purpose Distribution")
        specs = []

        specs.append(util.matrix_spec("mf925", "((mf164+(mf163*2))*ms58)+(((mf167*2)+mf168)*(1-ms58))"))
        specs.append(util.matrix_spec("mf925", "mf925.max.200"))

        #Calculate overall impedance using distribution by purpose coefficient and AM proportional factor
        specs.append(util.matrix_spec("mf220", "ms58*(mf101+ms103*mf102*ms114+(ms102+ms101)*mf100*ms114)"))

        #Midday is calculated as (1-AM proportional factor)
        specs.append(util.matrix_spec("mf220", "mf220+((1-ms58)*(mf104+ms103*mf105*ms114+(ms102+ms101)*mf103*ms114)+(mo28/2+md28/2)*ms114)"))

        #Combine AM and midday expressions
        specs.append(util.matrix_spec("mf220", "exp(" + str(nhod) + "*mf220)"))

        #Multiply by purpose and OD-specific Rij factors
        specs.append(util.matrix_spec("mf220", "(mf220+exp(" + str(nhod) + "*(mf925+ms114*mf160)))*mf179"))

        report = compute_matrix(specs)

        _m.logbook_trace("nhbw-Purpose Distribution")
        specs = []

        specs.append(util.matrix_spec("mf925", "((mf164+(mf163*2))*ms57)+(((mf167*2)+mf168)*(1-ms57))"))
        specs.append(util.matrix_spec("mf925", "mf925.max.200"))

        #Calculate overall impedance using distribution by purpose coefficient and AM proportional factor
        specs.append(util.matrix_spec("mf219", "ms57*(mf101+ms103*mf102*ms113+(ms102+ms101)*mf100*ms113)"))

        #Midday is calculated as (1-AM proportional factor)
        specs.append(util.matrix_spec("mf219", "mf219+((1-ms57)*(mf104+ms103*mf105*ms113+(ms102+ms101)*mf103*ms113)+(mo27/2+md27/2)*ms113)"))

        #Combine AM and midday expressions
        specs.append(util.matrix_spec("mf219", "exp(" + str(nhwd) + "*mf219)"))

        #Multiply by purpose and OD-specific Rij factors
        specs.append(util.matrix_spec("mf219", "(mf219+exp(" + str(nhwd) + "*(mf925+ms113*mf160)))*mf178"))

        report = compute_matrix(specs)
