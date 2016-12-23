##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step7.transitskim
##--Purpose: Skim Transit times and cost components by class (Bus, Rail, WCE)
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback
from copy import deepcopy as _deepcopy

class TransitSkim(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Transit Skim by Class"
        pb.description = "Calculates Transit Skims by Class (Bus, Rail, WCE)"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def __init__(self):
        # WCE Zonal Fare Values in Dollars For Skimming
        # TODO - Update values
        self.wce_fare_zone = {1: 3.79, 2: 3.79, 3: 5.03, 4: 6.10, 5: 8.39}

        # parameters for Mode availability matrices
        # Minimum IVTT; Disable value: 0
        self.minimum_ivtt_rule = {'Bus': 2, 'Rail': 5, 'WCE': 5} # TODO look at rail availability
        # IVTT/Auto Time Ratio; Disable value: 10 or any large value
        self.ivtt_auto_ratio = {'Bus': 10, 'Rail': 2.5, 'WCE': 2} #TODO look at that too - captives
        # Main Mode IVTT/ Total IVTT; Disable value: 0
        self.mivtt_totivt_ratio = {'Bus': 0, 'Rail': 0.3, 'WCE': 0.3}
        # IVTT - Bus skim IVTT; Not valid for Bus mode; Disable value: 999 or any large value
        self.ivtt_vs_busivtt = {'Bus': 999, 'Rail': 30, 'WCE': 30}
        # IVTT to Bus skim IVTT ratio; Not valid for Bus mode; Disable value: 10 or any large value
        self.ivtt_busivtt_ratio = {'Bus': 10, 'Rail': 2, 'WCE': 2}
        # IVTT bus component to Bus skim IVTT ratio; Not valid for Bus mode; Disable value: 10 or any large value
        self.ivttb_busivtt_ratio = {'Bus': 10, 'Rail': 1, 'WCE': 1}

    def run(self):
        self.tool_run_msg = ""
        try:
            eb = _m.Modeller().emmebank
            self.am_scenario = _m.Modeller().emmebank.scenario(int(eb.matrix("ms140").data))
            self.md_scenario = _m.Modeller().emmebank.scenario(int(eb.matrix("ms141").data))
            self.pm_scenario = _m.Modeller().emmebank.scenario(int(eb.matrix("ms150").data))

            class_list=["Bus","Rail","Ratype0","WCE"]
            scenario_list = [self.am_scenario, self.md_scenario, self.pm_scenario]
            for i, sc in enumerate(scenario_list):
                self(i, sc, class_list[i])
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("07-05 - Transit Skims")
    def __call__(self, i, scenarionumber, classname):
        transit_skim = _m.Modeller().tool("inro.emme.transit_assignment.extended.matrix_results")
        strategy_skim = _m.Modeller().tool("inro.emme.transit_assignment.extended.strategy_based_analysis")
        util = _m.Modeller().tool("translink.util")

        # Note: could remove the None items from the tmplt
        # TODO: Update Matrices mf 7000+ that are used for fare skims and availability of Modes
        # TODO: Initialize matrices - where are the matrices initialized?
        if classname == "Bus":
            modelist = ["b", "g", "a", "p"]
            Travel_Time_List = [["mf933", "mf934", "mf936", "mf935", "mf7000", "mf7001", "mf7002"],
                            ["mf945", "mf946", "mf948", "mf947", "mf7010", "mf7011", "mf7012"],
                            ["mf2003", "mf2004", "mf2006", "mf2005", "mf7020", "mf7021", "mf7022"]]
            Mode_Avail_List = ["mf7003", "mf7013", "mf7023"]

        if classname == "Rail":
            modelist = ["b", "f", "g", "l", "s", "a", "h", "p"]
            Travel_Time_List = [["mf1073", "mf1074", "mf1072", "mf1070", "mf1071", "mf7030", "mf7031", "mf7032"],
                            ["mf1078", "mf1079", "mf1077", "mf1075", "mf1076", "mf7040", "mf7041", "mf7042"],
                            ["mf2019", "mf2020", "mf2018", "mf2016", "mf2017", "mf7050", "mf7051", "mf7052"]]
            Mode_Avail_List = ["mf7033", "mf7043", "mf7053"]

        if classname == "Ratype0":
            modelist = ["b", "f", "g", "l", "s", "a", "h", "p"]
            Travel_Time_List = [["mf940", "mf941", "mf939", "mf937", "mf938"],
                            ["mf952", "mf953", "mf951", "mf949", "mf950"],
                            ["mf2010", "mf2011", "mf2009", "mf2007", "mf2008"]]

        # TODO: Define travel time matrix numbers
        if classname == "WCE":
            modelist = ["b", "f", "g", "l", "r", "s", "a", "h", "p"]
            Travel_Time_List = [[ "mf5050", "mf5051", "mf5052", "mf5053", "mf5054", "mf5055","mf7060", "mf7061", "mf7062", "mf7063"],
                                [ "mf5056", "mf5057", "mf5058", "mf5059", "mf5060", "mf5061", "mf7070", "mf7071", "mf7072", "mf7073"],
                                [ "mf5062", "mf5063", "mf5064", "mf5065", "mf5066", "mf5067", "mf7080", "mf7081", "mf7082", "mf7083"]]
            Mode_Avail_List = ["mf7064", "mf7074", "mf7084"]

        tmplt_spec = {
            "by_mode_subset": {
                "modes": modelist,
                "avg_boardings": None,
                "actual_total_boarding_times": None,
                "actual_in_vehicle_times": None,
                "actual_aux_transit_times": None,
                "actual_first_boarding_costs": None,
                "actual_total_boarding_costs": None,
                "actual_in_vehicle_costs": None
            },
            "type": "EXTENDED_TRANSIT_MATRIX_RESULTS",
            "actual_total_waiting_times": None
        }

        strategy_spec = {
            "type": "EXTENDED_TRANSIT_STRATEGY_ANALYSIS",
            "trip_components": {
                "boarding": None,
                "in_vehicle": None,
                "alighting": None
            },
            "sub_path_combination_operator": ".max.",
            "sub_strategy_combination_operator": ".max.", # take max as opposed to average to get the full fare not the average
            "selected_demand_and_transit_volumes": {
                "sub_strategies_to_retain": "FROM_COMBINATION_OPERATOR",
                "selection_threshold": {"lower": -999999, "upper": 999999}
            },
            "results" : {"strategy_values": None}
        }

        matrix_spec = []

        if classname =="Bus":
            spec_as_dict = _deepcopy(tmplt_spec)
            spec_as_dict["actual_total_waiting_times"] = Travel_Time_List[i][0]
            spec_as_dict["by_mode_subset"]["actual_in_vehicle_times"] = Travel_Time_List[i][1]
            spec_as_dict["by_mode_subset"]["actual_aux_transit_times"] = Travel_Time_List[i][2]
            spec_as_dict["by_mode_subset"]["avg_boardings"] = Travel_Time_List[i][3]
            spec_as_dict["by_mode_subset"]["actual_first_boarding_costs"] = Travel_Time_List[i][5]
            transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

            # Skim for FareIncrements
            strat_spec = _deepcopy(strategy_spec)
            strat_spec["trip_components"]["in_vehicle"] = "@fareincrement"
            strat_spec["sub_path_combination_operator"]= "+"
            strat_spec["results"]["strategy_values"] = Travel_Time_List[i][4]
            strategy_skim(strat_spec, scenario=scenarionumber, class_name=classname)

            # Fare Calculation: Boarding Fare + fare Increment
            expression1 = Travel_Time_List[i][5] + " + " + Travel_Time_List[i][4]
            matrix_spec.append(util.matrix_spec(Travel_Time_List[i][6], expression1))
            util.compute_matrix(matrix_spec, scenarionumber)

            total_invehicle_time = Travel_Time_List[i][1]
            invehicle_bus_time = Travel_Time_List[i][1]
            prem_invehicle_time = Travel_Time_List[i][1]

        if classname == "Rail" :
            spec_as_dict = _deepcopy(tmplt_spec)
            spec_as_dict["by_mode_subset"]["actual_total_boarding_times"] = Travel_Time_List[i][0]
            spec_as_dict["by_mode_subset"]["actual_aux_transit_times"] = Travel_Time_List[i][1]
            spec_as_dict["actual_total_waiting_times"] = Travel_Time_List[i][2]
            spec_as_dict["by_mode_subset"]["actual_first_boarding_costs"] = Travel_Time_List[i][6]
            transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

            spec_as_dict = _deepcopy(tmplt_spec)
            spec_as_dict["by_mode_subset"]["modes"] = ["b", "g"]
            spec_as_dict["by_mode_subset"]["actual_in_vehicle_times"] = Travel_Time_List[i][3]
            transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

            spec_as_dict = _deepcopy(tmplt_spec)
            spec_as_dict["by_mode_subset"]["modes"] = ["s", "l", "r", "f", "h"]
            spec_as_dict["by_mode_subset"]["actual_in_vehicle_times"] = Travel_Time_List[i][4]
            transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

            # Skim for Fare Increments: In-vehicle costs
            strat_spec = _deepcopy(strategy_spec)
            strat_spec["trip_components"]["in_vehicle"] = "@fareincrement"
            strat_spec["sub_path_combination_operator"]= "+"
            strat_spec["results"]["strategy_values"] = Travel_Time_List[i][5]
            strategy_skim(strat_spec, scenario=scenarionumber, class_name=classname)

            # Fare Calculation: Boarding Fare + fare Increment
            expression1 = Travel_Time_List[i][5] + " + " + Travel_Time_List[i][6]
            matrix_spec.append(util.matrix_spec(Travel_Time_List[i][7], expression1))
            util.compute_matrix(matrix_spec, scenarionumber)

            total_invehicle_time = "("+Travel_Time_List[i][3]+"+"+Travel_Time_List[i][4]+")"
            invehicle_bus_time = Travel_Time_List[i][3]
            prem_invehicle_time = Travel_Time_List[i][4]

        if classname  =="Ratype0":
            spec_as_dict = _deepcopy(tmplt_spec)
            spec_as_dict["by_mode_subset"]["actual_total_boarding_times"] = Travel_Time_List[i][0]
            spec_as_dict["by_mode_subset"]["actual_aux_transit_times"] = Travel_Time_List[i][1]
            spec_as_dict["actual_total_waiting_times"] = Travel_Time_List[i][2]
            transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

            spec_as_dict = _deepcopy(tmplt_spec)
            spec_as_dict["by_mode_subset"]["modes"] = ["b", "g"]
            spec_as_dict["by_mode_subset"]["actual_in_vehicle_times"] = Travel_Time_List[i][3]
            transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

            spec_as_dict = _deepcopy(tmplt_spec)
            spec_as_dict["by_mode_subset"]["modes"] = ["s", "l", "r", "f", "h"]
            spec_as_dict["by_mode_subset"]["actual_in_vehicle_times"] = Travel_Time_List[i][4]
            transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

        if classname == "WCE":
            spec_as_dict = _deepcopy(tmplt_spec)
            spec_as_dict["by_mode_subset"]["actual_total_boarding_times"] = Travel_Time_List[i][0]
            spec_as_dict["by_mode_subset"]["actual_aux_transit_times"] = Travel_Time_List[i][1]
            spec_as_dict["actual_total_waiting_times"] = Travel_Time_List[i][2]
            transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

            spec_as_dict = _deepcopy(tmplt_spec)
            spec_as_dict["by_mode_subset"]["modes"] = ["b", "g"]
            spec_as_dict["by_mode_subset"]["actual_in_vehicle_times"] = Travel_Time_List[i][3]
            transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

            spec_as_dict = _deepcopy(tmplt_spec)
            spec_as_dict["by_mode_subset"]["modes"] = ["s", "l", "f", "h"]
            spec_as_dict["by_mode_subset"]["actual_in_vehicle_times"] = Travel_Time_List[i][4]
            transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

            spec_as_dict = _deepcopy(tmplt_spec)
            spec_as_dict["by_mode_subset"]["modes"] = ["r"]
            spec_as_dict["by_mode_subset"]["actual_in_vehicle_times"] = Travel_Time_List[i][5]
            transit_skim(spec_as_dict, scenario=scenarionumber, class_name=classname)

            # Fare Increments for only bus/skytrain
            strat_spec = _deepcopy(strategy_spec)
            strat_spec["trip_components"]["in_vehicle"] = "@fareboundary"
            strat_spec["sub_path_combination_operator"]= "+"
            strat_spec["results"]["strategy_values"] = Travel_Time_List[i][6]
            strategy_skim(strat_spec, scenario=scenarionumber, class_name=classname)

            # Boarding and Alighting Fare Zone for WCE Fare Calculation
            fzone_spec = _deepcopy(strategy_spec)
            fzone_spec["sub_path_combination_operator"] = ".max."
            fzone_spec["trip_components"]["boarding"] = "@farezone"
            fzone_spec["results"]["strategy_values"] = Travel_Time_List[i][7]
            strategy_skim(fzone_spec, scenario=scenarionumber, class_name=classname)

            fzone_spec2 = _deepcopy(strategy_spec)
            fzone_spec2["sub_path_combination_operator"] = ".max."
            fzone_spec2["trip_components"]["alighting"] = "@farezone"
            fzone_spec2["results"]["strategy_values"] = Travel_Time_List[i][8]
            strategy_skim(fzone_spec2, scenario=scenarionumber, class_name=classname)

            # TODO : Fare Calculation: Zone to Zone WCE Fare + bus/skytrain fare Increment
            result = Travel_Time_List[i][9]
            expression1 = "abs(%s-%s)-100*(%s*%s.eq.0)" %(Travel_Time_List[i][8],Travel_Time_List[i][7],
                                                          Travel_Time_List[i][8],Travel_Time_List[i][7])

            expression2 = "(%s.lt.0)*0 +(%s.eq.0)*%s +(%s.eq.10)*%s + (%s.eq.20)*%s + (%s.eq.30)*%s + (%s.eq.40)*%s " %(
                                                              result, result, self.wce_fare_zone[1],
                                                              result, self.wce_fare_zone[2], result, self.wce_fare_zone[3],
                                                              result, self.wce_fare_zone[4], result, self.wce_fare_zone[5])
            matrix_spec.append(util.matrix_spec(result, expression1))
            matrix_spec.append(util.matrix_spec(result, expression2))
            util.compute_matrix(matrix_spec, scenarionumber)

            total_invehicle_time = "(" + Travel_Time_List[i][3] + "+" + Travel_Time_List[i][4]+ "+" + Travel_Time_List[i][5] + ")"
            invehicle_bus_time = Travel_Time_List[i][3]
            prem_invehicle_time = Travel_Time_List[i][5]

        # Mode Availability Rule
        # TODO does this actually belong here
        # TODO remove Ratype0 eventually
        if classname != "Ratype0":
            auto_time = ["mf931", "mf943", "mf2001"]
            bus_invehicle_time = ["mf934",  "mf946",  "mf2004"]

            result = Mode_Avail_List[i]
            expression1 = "(%s .ge. %s)*((%s/%s).le.%s)*((%s/%s).ge.%s)*((%s-%s).le.%s)*((%s/%s).le.%s)*((%s/%s).le.%s)" %(
                total_invehicle_time,self.minimum_ivtt_rule[classname],
                total_invehicle_time, auto_time[i], self.ivtt_auto_ratio[classname],
                prem_invehicle_time, total_invehicle_time,  self.mivtt_totivt_ratio[classname],
                total_invehicle_time,  bus_invehicle_time[i], self.ivtt_vs_busivtt[classname],
                total_invehicle_time, bus_invehicle_time[i], self.ivtt_busivtt_ratio[classname],
                invehicle_bus_time, bus_invehicle_time[i], self.ivttb_busivtt_ratio[classname])

            matrix_spec=[]
            matrix_spec.append(util.matrix_spec(result, expression1))
            util.compute_matrix(matrix_spec, scenarionumber)
