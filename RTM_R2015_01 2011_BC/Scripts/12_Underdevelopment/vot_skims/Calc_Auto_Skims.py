##------------------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model Development
##--
##--Path: translink.emme.under_dev.autocalcskim
##--Purpose: Generate Auto Skims and generate intra-zonals
##------------------------------------------------------------------------------
import inro.modeller as _m
import os
import traceback as _traceback

class AutoSkims(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Calculate Auto Skims (time, distance and cost) and generate intra-zonals"
        pb.description = "Calculate Auto Skims (time, distance and cost) and generate intra-zonals"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        eb = _m.Modeller().emmebank
        try:
            self.__call__(eb)
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("012- - Weighted Skims and New Accessibilities")
    def __call__(self, eb):
        self.Matrix_Batchins(eb)
        self.autoskims(eb)


    @_m.logbook_trace("Weighted Skims")
    def autoskims(self, eb):
        util = _m.Modeller().tool("translink.util")
        VOTNW = str(8.0) # non-Work-purpose VOT
        VOTWK = str(4.0) # Work purpose VOT
        spec_as_dict = {
                "expression": "EXPRESSION",
                "result": "RESULT",
                "constraint": {
                    "by_value": {
                        "od_values": "mf970",
                        "interval_min": 1,
                        "interval_max": 1,
                        "condition": "EXCLUDE"
                    },
                    "by_zone": None
                },
                "aggregation": {"origins": None, "destinations": None},
                "type": "MATRIX_CALCULATION"
            }

        expressions_list_am = [
            ["mf931-mf930*ms18*"+VOTNW+"-mf932*ms19*"+VOTNW, "mf931"],
            ["mf2031-mf2030*ms18*"+VOTWK+"-mf2032*ms19*"+VOTWK, "mf2031"]
        ]

        expressions_list_md = [
            ["mf943-mf942*ms18*"+VOTNW+"-mf944*ms19*"+VOTNW, "mf943"],
            ["mf2034-mf2033*ms18*"+VOTWK+"-mf2035*ms19*"+VOTWK, "mf2034"]
        ]

        expressions_list_pm = [
            ["mf2001-mf2000*ms18*"+VOTNW+"-mf2002*ms19*"+VOTNW, "mf2001"],
            ["mf2037-mf2036*ms18*"+VOTWK+"-mf2038*ms19*"+VOTWK, "mf2037"]
        ]

        for n in range(0, len(expressions_list_am)):
            spec_as_dict["expression"] = expressions_list_am[n][0]
            spec_as_dict["result"] = expressions_list_am[n][1]
            util.compute_matrix(spec_as_dict)
            spec_as_dict["expression"] = expressions_list_md[n][0]
            spec_as_dict["result"] = expressions_list_md[n][1]
            util.compute_matrix(spec_as_dict)
            spec_as_dict["expression"] = expressions_list_pm[n][0]
            spec_as_dict["result"] = expressions_list_pm[n][1]
            util.compute_matrix(spec_as_dict)

        # Calculate Intra-zonals, based on generalized cost-minutes of closest neighbour
        # for auto take 1/2 the distance and time, for transit only x1/2 of IVTT and x1 OVTT
        Counter_Auto=1  # >1 if more than 1 nearest neighbour is used

# Non-work

        # AM Auto distance and time
        Auto_AM_Expression= "mf931+mf930*ms18*"+VOTNW+"+mf932*ms19*"+VOTNW
        Auto_AM_List=["mf930","mf931"]
        Av_List=["0.5","0.5"]
        self.Calc_Intrazonals(Auto_AM_Expression, Auto_AM_List, Counter_Auto, Av_List)

        # MD Auto distance and time
        Auto_MD_Expression= "mf943+mf942*ms18*"+VOTNW+"+mf944*ms19*"+VOTNW
        Auto_MD_List=["mf942","mf943"]
        Av_List=["0.5","0.5"]
        self.Calc_Intrazonals(Auto_MD_Expression, Auto_MD_List, Counter_Auto, Av_List)

        # PM Auto distance and time
        Auto_PM_Expression= "mf2001+mf2000*ms18*"+VOTNW+"+mf2002*ms19*"+VOTNW
        Auto_PM_List=["mf2000","mf2001"]
        Av_List=["0.5","0.5"]
        self.Calc_Intrazonals(Auto_PM_Expression, Auto_PM_List, Counter_Auto, Av_List)

# Work

        # AM Auto distance and time
        Auto_AM_Expression= "mf2031+mf2030*ms18*"+VOTWK+"+mf2032*ms19*"+VOTWK
        Auto_AM_List=["mf2030","mf2031"]
        Av_List=["0.5","0.5"]
        self.Calc_Intrazonals(Auto_AM_Expression, Auto_AM_List, Counter_Auto, Av_List)

        # MD Auto distance and time
        Auto_MD_Expression= "mf2034+mf2033*ms18*"+VOTWK+"+mf2035*ms19*"+VOTWK
        Auto_MD_List=["mf2033","mf2034"]
        Av_List=["0.5","0.5"]
        self.Calc_Intrazonals(Auto_MD_Expression, Auto_MD_List, Counter_Auto, Av_List)

        # PM Auto distance and time
        Auto_PM_Expression= "mf2037+mf2036*ms18*"+VOTWK+"+mf2038*ms19*"+VOTWK
        Auto_PM_List=["mf2036","mf2037"]
        Av_List=["0.5","0.5"]
        self.Calc_Intrazonals(Auto_PM_Expression, Auto_PM_List, Counter_Auto, Av_List)


    @_m.logbook_trace("Matrix Batchin")
    def Matrix_Batchins(self, eb):
        util = _m.Modeller().tool("translink.util")


        # Added matrices for calculating intra-zonals
        util.initmat(eb, "mo1025", "MiGCIZ", "Min Intra-zonal GC", 0)
        util.initmat(eb, "mo1026", "MiGCIn", "Min Intra-zonal GC Zone Index", 0)
        util.initmat(eb, "mo1027", "MiCoIn", "Min Intra-zonal GC Comp. ", 0)
        util.initmat(eb, "mf1095", "TmpCal", "Temp Calc Min Intra-zonal GC", 0)

    @_m.logbook_trace("Calc_Intrazonals")
    def Calc_Intrazonals(self, expression, matrix_list, Counter, Av_List):
        # find nearest neighbour (NN) based on generalized cost (GC), store components of the NN GC in corresponding intrazonals
        util = _m.Modeller().tool("translink.util")

        specs=[]

        # Initialize inta-zonals to 0
        for matrix in range(0, len(matrix_list)):
            izod_spec=util.matrix_spec(matrix_list[matrix],"0")
            izod_spec["constraint"]["by_value"] = {"od_values": "mf970", "interval_min": 1, "interval_max": 1, "condition": "INCLUDE"}
            specs.append(izod_spec)

        specs.append(util.matrix_spec("mf1095", expression))


        for count in range (0, Counter):

            iz_spec= util.matrix_spec("mo1025", "mf1095")
            iz_spec["constraint"]["by_value"] = {"od_values": "mf970", "interval_min": 1, "interval_max": 1, "condition": "EXCLUDE"}
            iz_spec["constraint"]["by_zone"] = {"origins": "gm1-gm24", "destinations": "gm1-gm24"}
            iz_spec["aggregation"] = {"origins": None, "destinations": ".min."}
            specs.append(iz_spec)

            ind_spec=util.matrix_spec("mo1026", "q*(abs(mo1025-mf1095)<0.0001)")
            ind_spec["constraint"]["by_value"] = {"od_values": "mf970", "interval_min": 1, "interval_max": 1, "condition": "EXCLUDE"}
            ind_spec["constraint"]["by_zone"] = {"origins": "gm1,gm24", "destinations": "gm1,gm24"}
            ind_spec["aggregation"] = {"origins": None, "destinations": ".max."}
            specs.append(ind_spec)

            for matrix in range(0, len(matrix_list)):

                ind_spec=util.matrix_spec("mo1027", matrix_list[matrix]+"*(q.eq.mo1026)")
                ind_spec["constraint"]["by_value"] = {"od_values": "mf970", "interval_min": 1, "interval_max": 1, "condition": "EXCLUDE"}
                ind_spec["constraint"]["by_zone"] = {"origins": "gm1-gm24", "destinations": "gm1-gm24"}
                ind_spec["aggregation"] = {"origins": None, "destinations": ".max."}
                specs.append(ind_spec)


                izod_spec=util.matrix_spec(matrix_list[matrix],Av_List[matrix]+"*mo1027/"+str(Counter)+"+"+ matrix_list[matrix])
                izod_spec["constraint"]["by_value"] = {"od_values": "mf970", "interval_min": 1, "interval_max": 1, "condition": "INCLUDE"}
                specs.append(izod_spec)

            specs.append(util.matrix_spec("mf1095","mf1095*(q.ne.mo1026) +99999*(q.eq.mo1026)"))

        util.compute_matrix(specs)
