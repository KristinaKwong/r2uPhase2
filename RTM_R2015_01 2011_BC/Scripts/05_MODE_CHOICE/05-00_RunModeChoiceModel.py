##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step5.modechoice
##--Purpose: Run mode choice component of RTM
##---------------------------------------------------------------------
##--Status/additional notes:
## Number of mode choices for each trip type:
# work 7
# school 7
# shopping 6
# PB 5
# university 6
# social recreation 6
# escorting 5
# NHB other 6
# NHB work 6
##---------------------------------------------------
import inro.modeller as _m

import os
import traceback as _traceback

class ModeChoice(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)
    run_park_and_ride = _m.Attribute(bool)
    preserve_matrices = _m.Attribute(bool)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Mode Choice Model"
        pb.description = "Tool for running mode choice models on nine purposes and exports results at the gy to gy level"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        pb.add_checkbox("run_park_and_ride", label="Run park and ride adjustment")
        pb.add_checkbox("preserve_matrices", label="Preserve Intermediate Matrix results")

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            eb = _m.Modeller().emmebank
            self.__call__(eb, 0, 1, self.run_park_and_ride, self.preserve_matrices)
            run_msg = "Tool completed"
            self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("05-00 - Call Mode Choice Modules")
    def __call__(self, eb, iteration_number, max_iterations, run_park_and_ride=False, preserve_matrices=False):
        ## Matrices used for mode choice are from mf374-mf702,
        ## these store utilities, probabilities and various demands (work vs non work)
        print ("05-00 Run the Mode choice model on nine purposes and export results, iteration number: " + str(
            iteration_number + 1))

        ## Mode Choice Modules
        module_lookup = _m.Modeller().module
        home_base_work = _m.Modeller().tool("translink.emme.stage3.step5.modechoicehbw")
        home_base_school = _m.Modeller().tool("translink.emme.stage3.step5.modechoicehbschool")
        home_base_shopping = _m.Modeller().tool("translink.emme.stage3.step5.modechoicehbshop")
        home_base_personal_business = _m.Modeller().tool("translink.emme.stage3.step5.modechoicehbpersonalbusiness")
        home_base_university = _m.Modeller().tool("translink.emme.stage3.step5.modechoicehbuniversity")
        home_base_social = _m.Modeller().tool("translink.emme.stage3.step5.modechoicehbsocial")
        home_base_escort = _m.Modeller().tool("translink.emme.stage3.step5.modechoicehbesc")
        non_home_base_other = _m.Modeller().tool("translink.emme.stage3.step5.modechoicenhbo")
        non_home_base_work = module_lookup("translink.emme.stage3.step5.modechoicenhbw")
        park_and_ride = _m.Modeller().tool("translink.emme.stage3.step5.parkandride")

        is_last_iteration = (iteration_number == (max_iterations - 1))

        self.calculate_flag_matrices()

        scenario = _m.Modeller().scenario
        home_base_work.run_model(scenario, eb, iteration_number, is_last_iteration)
        home_base_school.run_model(scenario, eb, iteration_number, is_last_iteration)
        home_base_shopping.run_model(scenario, eb, iteration_number, is_last_iteration)
        home_base_personal_business.run_model(scenario, eb, iteration_number, is_last_iteration)
        home_base_university.run_model(scenario, eb, iteration_number, is_last_iteration)
        home_base_social.run_model(scenario, eb, iteration_number, is_last_iteration)
        home_base_escort.run_model(scenario, eb, iteration_number, is_last_iteration)
        non_home_base_other.run_model(scenario, eb, iteration_number, is_last_iteration)
        non_home_base_work.run_model(scenario, eb, iteration_number, is_last_iteration)

        if run_park_and_ride:
            park_and_ride(scenario)

        self.add_external_demand()

        if not preserve_matrices:
            self.clean_matrices(eb)

    @_m.logbook_trace("Calculate flag matrices")
    def calculate_flag_matrices(self):
        util = _m.Modeller().tool("translink.emme.util")
        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

        specs = []
        specs.append(util.matrix_spec("mf110", "(mf107.gt.0)"))
        specs.append(util.matrix_spec("mf115", "(mf112.gt.0)"))
        specs.append(util.matrix_spec("mf121", "(mf117.gt.0)"))
        specs.append(util.matrix_spec("mf129", "(mf125.gt.0)"))
        specs.append(util.matrix_spec("mf130", "(mf128.lt.50)"))
        specs.append(util.matrix_spec("mf132", "(mf107.gt.0)*(mf109.lt.60)*((mf106+mf107+mf108+mf109).lt.180)*(mf108.lt.6)"))
        specs.append(util.matrix_spec("mf133", "(mf112.gt.0)*(mf114.lt.60)*((mf111+mf112+mf113+mf114).lt.180)*(mf113.lt.6)"))
        specs.append(util.matrix_spec("mf134", "(mf117.gt.0)*(mf120.lt.75)*((mf116+mf117+mf118).lt.150)*(mf119.lt.7)"))
        specs.append(util.matrix_spec("mf135", "(mf125.gt.0)*(mf128.lt.75)*((mf124+mf125+mf126).lt.150)*(mf127.lt.7)"))
        specs.append(util.matrix_spec("mf157", "(mf134+mf135).gt.0"))
        specs.append(util.matrix_spec("mf136", "mf108-(mf110.eq.1)"))
        specs.append(util.matrix_spec("mf137", "mf113-(mf115.eq.1)"))
        specs.append(util.matrix_spec("mf138", "mf119-(mf121.eq.1)"))
        specs.append(util.matrix_spec("mf139", "mf127-(mf129.eq.1)"))
        specs.append(util.matrix_spec("mf151", "(mf132+mf133).gt.0"))

        compute_matrix(specs)

    @_m.logbook_trace("Add external demand to non-work SOV / HOV")
    def add_external_demand(self):
        util = _m.Modeller().tool("translink.emme.util")
        compute_matrix = _m.Modeller().tool("inro.emme.matrix_calculation.matrix_calculator")

        specs = []
        specs.append(util.matrix_spec("mf847", "mf847+mf978"))
        specs.append(util.matrix_spec("mf852", "mf852+mf979"))
        specs.append(util.matrix_spec("mf860", "mf860+mf984"))
        specs.append(util.matrix_spec("mf865", "mf865+mf985"))

        compute_matrix(specs)

    def clean_matrices(self, eb):
        util = _m.Modeller().tool("translink.emme.util")

        # Delete mf374-mf436 (Utilities)
        for i in range(374, 437):
            util.delmat(eb, "mf%d" % i)

        # Delete mf441 - mf503 (Probabilities)
        for i in range(441, 504):
            util.delmat(eb, "mf%d" % i)

        # Delete mf568 - mf639 (Demand)
        for i in range(568, 640):
            util.delmat(eb, "mf%d" % i)
