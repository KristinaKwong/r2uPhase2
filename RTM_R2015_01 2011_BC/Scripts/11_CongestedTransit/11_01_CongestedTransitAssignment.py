##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.stage5.step11.congested_transit
##--Purpose: Performs a two-class (bus and rail) Congested transit
##--         assignment on AM scenario
##---------------------------------------------------------------------
import inro.modeller as _modeller
import traceback as _traceback

class CongestedTransitAssignment(_modeller.Tool()):

    tool_run_msg = _modeller.Attribute(unicode)
    setup_ttfs = _modeller.Attribute(bool)
    am_scenario = _modeller.Attribute(_modeller.InstanceType)
    alpha = _modeller.Attribute(float)
    beta = _modeller.Attribute(float)

    def __init__(self):
        emmebank = _modeller.Modeller().emmebank
        self.am_scenario = emmebank.scenario(21060)
        self.alpha = 5
        self.beta = 4
        self.setup_ttfs = True

    def page(self):
        pb = _modeller.ToolPageBuilder(self)
        pb.title = "Congested Transit Assignment"
        pb.description = """
                Performs a two-class (bus and rail) Congested transit
                assignment on AM scenario.
                Note: make sure there is sufficient space for
                temporary and result extra attributes before running."""
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        pb.add_select_scenario("am_scenario", title="AM scenario:")

        pb.add_checkbox("setup_ttfs", title=" ",
            label="Replace ft0 with ft7",
            note="""Function ft7 will be created as
                "60 * length / speed" in order to account for congestion
                on those segments.""")

        pb.add_text_box("alpha",
            title="Alpha parameter for BPR-style congestion function")
        pb.add_text_box("beta",
            title="Beta parameter for BPR-style congestion function")

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            self(self.am_scenario, self.setup_ttfs, self.alpha, self.beta)
            run_msg = "Tool completed"
            self.tool_run_msg = _modeller.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _modeller.PageBuilder.format_exception(
                e, _traceback.format_exc(e))

    @_modeller.logbook_trace("10-10 - Congested Transit Assignment")
    def __call__(self, scenarioam,  setup_ttfs, alpha=7, beta=3):
        if setup_ttfs:
            self.setup_congestion_ttfs(scenarioam)

        congested_transit_assign = _modeller.Modeller().tool(
            "inro.emme.transit_assignment.congested_transit_assignment")

        spec = [
            {
                "modes": ["b", "g", "a", "p"],
                "demand": "mf853",
                "waiting_time": {
                    "headway_fraction": 0.5,
                    "spread_factor": 1,
                    "perception_factor": 2.25,
                    "effective_headways": "ut1"
                },
                "boarding_time": {
                    "at_nodes": {"penalty": 1, "perception_factor": 4}
                },
                "boarding_cost": {
                    "at_nodes": {"penalty": 0, "perception_factor": 1}
                },
                "aux_transit_time": {"perception_factor": 1.75},
                "in_vehicle_time": {"perception_factor": 1},
                "flow_distribution_between_lines": {
                    "consider_total_impedance": False
                },
                "flow_distribution_at_origins": {
                    "fixed_proportions_on_connectors": None,
                    "choices_at_origins": "OPTIMAL_STRATEGY"
                },
                "flow_distribution_at_regular_nodes_with_aux_transit_choices": {
                    "choices_at_regular_nodes": "OPTIMAL_STRATEGY"
                },
                "connector_to_connector_path_prohibition": None,
                "save_strategies": True,
                "type": "EXTENDED_TRANSIT_ASSIGNMENT"
            },
            {
                "modes": ["b", "f", "g", "l", "r", "s", "h", "a", "p"],
                "demand": "mf854",
                "waiting_time": {
                    "headway_fraction": 0.5,
                    "spread_factor": 1,
                    "perception_factor": 2.25,
                    "effective_headways": "ut1"
                },
                "boarding_time": {
                    "at_nodes": {"penalty": 1, "perception_factor": 4}
                },
                "boarding_cost": {
                    "at_nodes": {"penalty": 0,  "perception_factor": 1}
                },
                "aux_transit_time": {"perception_factor": 1.75},
                "in_vehicle_time": {"perception_factor": "@ivttp"},
                "flow_distribution_between_lines": {
                    "consider_total_impedance": False
                },
                "flow_distribution_at_origins": {
                    "fixed_proportions_on_connectors": None,
                    "choices_at_origins": "OPTIMAL_STRATEGY"
                },
                "flow_distribution_at_regular_nodes_with_aux_transit_choices": {
                    "choices_at_regular_nodes": "OPTIMAL_STRATEGY"
                },
                "connector_to_connector_path_prohibition": None,
                "save_strategies": True,
                "type": "EXTENDED_TRANSIT_ASSIGNMENT"
            }
        ]

        func = {
            "type": "BPR",
            "weight": alpha,
            "exponent": beta,
            "assignment_period": 1,
            "orig_func": False,
            "congestion_attribute": "us3"
        }

        stop = {
            "max_iterations": 15,
            "normalized_gap": 0.01,
            "relative_gap": 0.001
        }

        congested_transit_assign(
            spec, scenario=scenarioam, congestion_function=func,
            stopping_criteria=stop, class_names=["bus", "rail"])

    def setup_congestion_ttfs(self, scenario):
        with _modeller.logbook_trace("Creating congestion function ft7"):
            emmebank = scenario.emmebank
            ft7 = emmebank.function("ft7")
            if not ft7:
                ft7 = emmebank.create_function("ft7", "length")
            ft7.expression = "(60 * length / speed)"

        with _modeller.logbook_trace("Setting transit mode segments to use ft7"):
            network = scenario.get_partial_network(
                ["TRANSIT_SEGMENT"], include_attributes=False)
            values = scenario.get_attribute_values(
                "TRANSIT_SEGMENT", ["transit_time_func"])
            network.set_attribute_values(
                "TRANSIT_SEGMENT", ["transit_time_func"], values)

            for line in network.transit_lines():
                for seg in line.segments():
                    if seg.transit_time_func==0:
                        seg.transit_time_func = 7

            values = network.get_attribute_values(
                "TRANSIT_SEGMENT", ["transit_time_func"])
            scenario.set_attribute_values(
                "TRANSIT_SEGMENT", ["transit_time_func"], values)
