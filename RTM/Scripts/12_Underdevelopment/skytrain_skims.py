##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step7.railskim
##--Purpose: Skim Rail costs
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback
from copy import deepcopy as _deepcopy


class RailAssignment(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Sytrain Skim"
        pb.description = "Calculates Skytrain Skims"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            self.__call__()
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("07-01 - Rail Skims")
    def __call__(self, i, scenarionumber, RaType):
        railskim = _m.Modeller().tool("inro.emme.transit_assignment.extended.matrix_results")


        # Note: could remove the None items from the tmplt
        tmplt_spec = {
            "by_mode_subset": {
                "modes": ["b", "f", "g", "l" "s", "a", "h", "p" ],
                "distance": None,
                "avg_boardings": None,
                "actual_first_boarding_times": None,
                "actual_total_boarding_times": None,
                "actual_in_vehicle_times": None,
                "actual_aux_transit_times": None,
                "actual_first_boarding_costs": None,
                "actual_total_boarding_costs": None,
                "actual_in_vehicle_costs": None,
                "actual_aux_transit_costs": None,
                "perceived_first_boarding_times": None,
                "perceived_total_boarding_times": None,
                "perceived_in_vehicle_times": None,
                "perceived_aux_transit_times": None,
                "perceived_first_boarding_costs": None,
                "perceived_total_boarding_costs": None,
                "perceived_in_vehicle_costs": None,
                "perceived_aux_transit_costs": None
            },
            "type": "EXTENDED_TRANSIT_MATRIX_RESULTS",
            "total_impedance": None,
            "actual_first_waiting_times": None,
            "actual_total_waiting_times": None,
            "perceived_first_waiting_times": None,
            "perceived_total_waiting_times": None
        }
        ## if RaType==0:

        if RaType==1:
            Travel_Time_List = [["mf5003", "mf5004", "mf5002", "mf5000", "mf5001"],
                                ["mf5008", "mf5009", "mf5007", "mf5005", "mf5006"],
                                ["mf5013", "mf5014", "mf5012", "mf5010", "mf5011"]]
        """
            Travel_Time_List = [["mf5023", "mf5024", "mf5022", "mf5020", "mf5021"],
                                ["mf5028", "mf5029", "mf5027", "mf5025", "mf5026"],
                                ["mf5033", "mf5034", "mf5032", "mf5030", "mf5031"]]
        """
        spec_as_dict = _deepcopy(tmplt_spec)
        spec_as_dict["by_mode_subset"]["modes"] = ["b", "f", "g", "l", "s", "a", "p", "h"]
        spec_as_dict["by_mode_subset"]["actual_total_boarding_times"] = Travel_Time_List[i][0]
        spec_as_dict["by_mode_subset"]["actual_aux_transit_times"] = Travel_Time_List[i][1]
        spec_as_dict["actual_total_waiting_times"] = Travel_Time_List[i][2]

        railskim(spec_as_dict, scenario=scenarionumber)

        spec_as_dict = _deepcopy(tmplt_spec)
        spec_as_dict["by_mode_subset"]["modes"] = ["b", "g"]
        spec_as_dict["by_mode_subset"]["actual_in_vehicle_times"] = Travel_Time_List[i][3]

        railskim(spec_as_dict, scenario=scenarionumber)

        spec_as_dict = _deepcopy(tmplt_spec)
        spec_as_dict["by_mode_subset"]["modes"] = ["s", "l", "f", "h"]
        spec_as_dict["by_mode_subset"]["actual_in_vehicle_times"] = Travel_Time_List[i][4]

        railskim(spec_as_dict, scenario=scenarionumber)
