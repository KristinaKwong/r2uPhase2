##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step7.skimaccess
##--Purpose: Generates new weighted skims and accessibilities
##---------------------------------------------------------------------
import inro.modeller as _m
import os
import traceback as _traceback

class SkimsAccessibilities(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Weighted Skims and new accessibilities"
        pb.description = "Generates new weighted skims and calculates new accessibilities"
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

    @_m.logbook_trace("07-04 - Weighted Skims and New Accessibilities")
    def __call__(self, eb):
        self.Matrix_Batchins(eb)
        self.weightedskims(eb)
        self.accessibilities()

    @_m.logbook_trace("Weighted Skims")
    def weightedskims(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        cycle_number = util.get_cycle(eb)
        if cycle_number <= 1:
            j = 1
            k = 1
        else:
            j = 0.5
            k = 1

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
            ["mf931-mf930*6*ms18-mf932*ms19*6", "mf931"],
            ["mf100*(1-" + str(j) + ")+mf930*" + str(j), "mf100"],
            ["mf101*(1-" + str(j) + ")+mf931*" + str(j), "mf101"],
            ["mf102*(1-" + str(j) + ")+mf932*" + str(j), "mf102"],
            ["mf106*(1-" + str(k) + ")+mf933*" + str(k), "mf106"],
            ["mf107*(1-" + str(k) + ")+mf934*" + str(k), "mf107"],
            ["mf108*(1-" + str(k) + ")+mf935*" + str(k), "mf108"],
            ["mf109*(1-" + str(k) + ")+mf936*" + str(k), "mf109"],
            ["mf116*(1-" + str(k) + ")+mf937*(mf938.eq.0)+mf1070*(mf938.gt.0)*" + str(k), "mf116"],
            ["mf117*(1-" + str(k) + ")+mf938*(mf938.eq.0)+mf1071*(mf938.gt.0)*" + str(k), "mf117"],
            ["mf118*(1-" + str(k) + ")+mf939*(mf938.eq.0)+mf1072*(mf938.gt.0)*" + str(k), "mf118"],
            ["mf119*(1-" + str(k) + ")+mf940*(mf938.eq.0)+mf1073*(mf938.gt.0)*" + str(k), "mf119"],
            ["mf120*(1-" + str(k) + ")+mf941*(mf938.eq.0)+mf1074*(mf938.gt.0)*" + str(k), "mf120"],
            ["mf163*(1-" + str(k) + ")+(mf954+mf956+mf957)*" + str(k), "mf163"],
            ["mf164*(1-" + str(k) + ")+mf955*" + str(k), "mf164"]
        ]

        expressions_list_md = [
            ["mf943-mf942*6*ms18-mf944*ms19*6", "mf943"],
            ["mf103*(1-" + str(j) + ")+mf942*" + str(j), "mf103"],
            ["mf104*(1-" + str(j) + ")+mf943*" + str(j), "mf104"],
            ["mf105*(1-" + str(j) + ")+mf944*" + str(j), "mf105"],
            ["mf111*(1-" + str(k) + ")+mf945*" + str(k), "mf111"],
            ["mf112*(1-" + str(k) + ")+mf946*" + str(k), "mf112"],
            ["mf113*(1-" + str(k) + ")+mf947*" + str(k), "mf113"],
            ["mf114*(1-" + str(k) + ")+mf948*" + str(k), "mf114"],
            ["mf124*(1-" + str(k) + ")+mf949*(mf950.eq.0)+mf1075*(mf950.gt.0)*" + str(k), "mf124"],
            ["mf125*(1-" + str(k) + ")+mf950*(mf950.eq.0)+mf1076*(mf950.gt.0)*" + str(k), "mf125"],
            ["mf126*(1-" + str(k) + ")+mf951*(mf950.eq.0)+mf1077*(mf950.gt.0)*" + str(k), "mf126"],
            ["mf127*(1-" + str(k) + ")+mf952*(mf950.eq.0)+mf1078*(mf950.gt.0)*" + str(k), "mf127"],
            ["mf128*(1-" + str(k) + ")+mf953*(mf950.eq.0)+mf1079*(mf950.gt.0)*" + str(k), "mf128"],
            ["mf167*(1-" + str(k) + ")+(mf958+mf960+mf961)*" + str(k), "mf167"],
            ["mf168*(1-" + str(k) + ")+mf959*" + str(k), "mf168"]
        ]

        expressions_list_pm = [
            ["mf2001-mf2000*6*ms18-mf2002*ms19*6", "mf2001"],
            ["mf2100*(1-" + str(j) + ")+mf2000*" + str(j), "mf2100"],
            ["mf2101*(1-" + str(j) + ")+mf2001*" + str(j), "mf2101"],
            ["mf2102*(1-" + str(j) + ")+mf2002*" + str(j), "mf2102"],
            ["mf2106*(1-" + str(k) + ")+mf2003*" + str(k), "mf2106"],
            ["mf2107*(1-" + str(k) + ")+mf2004*" + str(k), "mf2107"],
            ["mf2108*(1-" + str(k) + ")+mf2005*" + str(k), "mf2108"],
            ["mf2109*(1-" + str(k) + ")+mf2006*" + str(k), "mf2109"],
            ["mf2116*(1-" + str(k) + ")+mf2007*(mf2008.eq.0)+mf2016*(mf2008.gt.0)*" + str(k), "mf2116"],
            ["mf2117*(1-" + str(k) + ")+mf2008*(mf2008.eq.0)+mf2017*(mf2008.gt.0)*" + str(k), "mf2117"],
            ["mf2118*(1-" + str(k) + ")+mf2009*(mf2008.eq.0)+mf2018*(mf2008.gt.0)*" + str(k), "mf2118"],
            ["mf2119*(1-" + str(k) + ")+mf2010*(mf2008.eq.0)+mf2019*(mf2008.gt.0)*" + str(k), "mf2119"],
            ["mf2120*(1-" + str(k) + ")+mf2011*(mf2008.eq.0)+mf2020*(mf2008.gt.0)*" + str(k), "mf2120"],
            ["mf2163*(1-" + str(k) + ")+(mf2012+mf2014+mf2015)*" + str(k), "mf2163"],
            ["mf2164*(1-" + str(k) + ")+mf2013*" + str(k), "mf2164"]
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
        Counter_Transit=1

        # AM Auto distance and time
        Auto_AM_Expression= "mf101+mf100*6*ms18+mf102*ms19*6"
        Auto_AM_List=["mf100","mf101"]
        Av_List=["0.5","0.5"]
        self.Calc_Intrazonals(Auto_AM_Expression, Auto_AM_List, Counter_Auto, Av_List)

        # MD Auto distance and time
        Auto_MD_Expression= "mf104+mf103*6*ms18+mf105*ms19*6"
        Auto_MD_List=["mf103","mf104"]
        Av_List=["0.5","0.5"]
        self.Calc_Intrazonals(Auto_MD_Expression, Auto_MD_List, Counter_Auto, Av_List)

        # PM Auto distance and time
        Auto_PM_Expression= "mf2101+mf2100*6*ms18+mf2102*ms19*6"
        Auto_PM_List=["mf2100","mf2101"]
        Av_List=["0.5","0.5"]
        self.Calc_Intrazonals(Auto_PM_Expression, Auto_PM_List, Counter_Auto, Av_List)

        # Transit AM OVTT, IVTT
        Transit_AM_Expression = "2*mf163+mf164"
        Transit_AM_List=["mf163","mf164"]
        Av_List=["1.0","0.5"]
        self.Calc_Intrazonals(Transit_AM_Expression, Transit_AM_List, Counter_Transit, Av_List)

        # Transit MD OVTT, IVTT
        Transit_MD_Expression = "2*mf167+mf168"
        Transit_MD_List=["mf167","mf168"]
        Av_List=["1.0","0.5"]
        self.Calc_Intrazonals(Transit_MD_Expression, Transit_MD_List, Counter_Transit, Av_List)

        # Transit PM OVTT, IVTT
        Transit_PM_Expression = "2*mf2163+mf2164"
        Transit_PM_List=["mf2163","mf2164"]
        Av_List=["1.0","0.5"]
        self.Calc_Intrazonals(Transit_PM_Expression, Transit_PM_List, Counter_Transit, Av_List)

        # Bus AM Wait, IVTT, Board, Walk
        Bus_AM_Expression = "2.25*mf106+mf107+4*mf108+1.75*mf109"
        Bus_AM_List = ["mf106","mf107","mf108","mf109"]
        Av_List=["1.0","0.5", "1.0", "1.0"]
        self.Calc_Intrazonals(Bus_AM_Expression, Bus_AM_List, Counter_Transit, Av_List)

         # Bus MD Wait, IVTT, Board, Walk
        Bus_MD_Expression = "2.25*mf111+mf112+4*mf113+1.75*mf114"
        Bus_MD_List = ["mf111","mf112","mf113","mf114"]
        Av_List=["1.0","0.5", "1.0", "1.0"]
        self.Calc_Intrazonals(Bus_MD_Expression, Bus_MD_List, Counter_Transit, Av_List)

        # Bus PM Wait, IVTT, Board, Walk
        Bus_PM_Expression = "2.25*mf2106+mf2107+4*mf2108+1.75*mf2109"
        Bus_PM_List = ["mf2106","mf2107","mf2108","mf2109"]
        Av_List=["1.0","0.5", "1.0", "1.0"]
        self.Calc_Intrazonals(Bus_PM_Expression, Bus_PM_List, Counter_Transit, Av_List)

    @_m.logbook_trace("Accessibilities Calculation")
    def accessibilities(self):
        util = _m.Modeller().tool("translink.emme.util")

        spec_as_dict = {
                "expression": "EXPRESSION",
                "result": "RESULT",
                "constraint": {
                    "by_value": {
                        "od_values": "mf101",
                        "interval_min": 0,
                        "interval_max": 0,
                        "condition": "EXCLUDE"
                    },
                    "by_zone": None
                },
                "aggregation": {
                    "origins": None,
                    "destinations": "+"
                },
                "type": "MATRIX_CALCULATION"
            }
        expressions_list = [
            ["ln(md12+1*(md12.eq.0))/(mf101*mf101)", "mf101", "mo47"],
            ["ln(md12+1*(md12.eq.0))/((2*(mf954+mf106*(p.eq.q))+mf164)*(2*(mf954+mf106*(p.eq.q))+mf164))", "mf164",
             "mo392"],
            ["ln(md8+1*(md8.eq.0))/(mf101*mf101)", "mf101", "mo954"],
            ["ln(md8+1*(md8.eq.0))/((2*(mf954+mf106*(p.eq.q))+mf164)*(2*(mf954+mf106*(p.eq.q))+mf164))", "mf164",
             "mo955"],
            ["ln(md23+1*(md23.eq.0))/(mf101*mf101)", "mf101", "mo48"],
            ["ln(md23+1*(md23.eq.0))/((2*(mf954+mf106*(p.eq.q))+mf164)*(2*(mf954+mf106*(p.eq.q))+mf164))", "mf164",
             "mo957"],
            ["ln(md8+md9+md10+md11+1*((md8+md9+md10+md11).eq.0))/(mf101*mf101)", "mf101", "mo960"],
            [
                "ln(md8+md9+md10+md11+1*((md8+md9+md10+md11).eq.0))/((2*(mf954+mf106*(p.eq.q))+mf164)*(2*(mf954+mf106*(p.eq.q))+mf164))",
                "mf164", "mo961"]
        ]

        for i in range(0, len(expressions_list)):
            spec_as_dict["expression"] = expressions_list[i][0]
            spec_as_dict["constraint"]["by_value"]["od_values"] = expressions_list[i][1]
            spec_as_dict["result"] = expressions_list[i][2]
            util.compute_matrix(spec_as_dict)

    @_m.logbook_trace("Matrix Batchin")
    def Matrix_Batchins(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        util.initmat(eb, "mo47", "AuAc", "Auto Accessibility", 0)
        util.initmat(eb, "mo954", "ReAuAc", "Retail Auto Accessibility", 0)
        util.initmat(eb, "mo955", "ReTrAc", "Retail Transit Accessibility", 0)
        util.initmat(eb, "mo48", "PsAuAc", "Post-sec Auto Accessibility", 0)
        util.initmat(eb, "mo957", "PSTrAc", "PS Transit Accessibility", 0)
        util.initmat(eb, "mo392", "TrAc", "Transit Accessibility", 0)
        util.initmat(eb, "mo960", "AuSrAc", "Serv Emp Ind Auto Accessibility", 0)
        util.initmat(eb, "mo961", "TrSrAc", "Serv Emp Ind Transit Accessibility", 0)

        # Added matrices for calculating intra-zonals
        util.initmat(eb, "mo1025", "MiGCIZ", "Min Intra-zonal GC", 0)
        util.initmat(eb, "mo1026", "MiGCIn", "Min Intra-zonal GC Zone Index", 0)
        util.initmat(eb, "mo1027", "MiCoIn", "Min Intra-zonal GC Comp. ", 0)
        util.initmat(eb, "mf1095", "TmpCal", "Temp Calc Min Intra-zonal GC", 0)

    @_m.logbook_trace("Calc_Intrazonals")
    def Calc_Intrazonals(self, expression, matrix_list, Counter, Av_List):
        # find nearest neighbour (NN) based on generalized cost (GC), store components of the NN GC in corresponding intrazonals
        util = _m.Modeller().tool("translink.emme.util")

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
            ind_spec["constraint"]["by_zone"] = {"origins": "gm1-gm24", "destinations": "gm1-gm24"}
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
