##--------------------------------------------------
##--TransLink Phase 2 Regional Transportation Model
##--
##--Path:
##--Purpose:
##--------------------------------------------------
##--Last modified 2014-06-13 Kevin Bragg (INRO)
##--Reason: Adding addition of external demand
##         (moved from AutoAssignment tool)
##--Last modified 2014-02-25 Kevin Bragg (INRO)
##         Optimization of matrix calculation expressions:
##          - used matrix multi-calculation feature
##          - moved evaluation of certain expressions
##            outside of for loops which do not change
##          - added constraint.by_value where applicable
##          - optimized probability calculations
##         Moved common functions to
##         05-11_ModeChoiceUtilities tool to improve
##         code reuse
##--Last modified 2014-02-14 Kevin Bragg (INRO)
##--Reason: Update to Emme 4.0 namespaces
##          Code cleanup PEP 8 compliance
##---------------------------------------------------
##--Called by:
##--Calls:
##--Accesses:
##--Outputs:
##---------------------------------------------------
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

import inro.modeller as _modeller

import os
import traceback as _traceback

utilities = _modeller.Modeller().module(
    "translink.emme.stage3.step5.utilities")
build_spec = utilities.build_spec


class ModeChoice(_modeller.Tool()):
    tool_run_msg = _modeller.Attribute(unicode)
    run_park_and_ride = _modeller.Attribute(bool)

    def page(self):
        start_path = os.path.dirname(_modeller.Modeller().emmebank.path)
        pb = _modeller.ToolPageBuilder(self, title="Mode Choice Model",
                                       description="Tool for running mode choice models on nine purposes and exports results at the gy to gy level",
                                       branding_text="Translink")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)
            
        pb.add_checkbox("run_park_and_ride", label="Run park and ride adjustment")

        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        base_folder = os.path.dirname(_modeller.Modeller().emmebank.path) + "\\"
        try:
            self.__call__(base_folder, 0, 1, self.run_park_and_ride)
            run_msg = "Tool completed"
            self.tool_run_msg = _modeller.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _modeller.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_modeller.logbook_trace("05-00 - Call Mode Choice Modules")
    def __call__(self, root_directory, iteration_number, max_iterations, run_park_and_ride=False):
        ## Matrices used for mode choice are from mf374-mf702,
        ## these store utilities, probabilities and various demands (work vs non work)
        print ("05-00 Run the Mode choice model on nine purposes and export results, iteration number: " + str(
            iteration_number + 1))

        ## Mode Choice Modules
        module_lookup = _modeller.Modeller().module
        home_base_work = module_lookup("translink.emme.stage3.step5.modechoicehbw")
        home_base_school = module_lookup("translink.emme.stage3.step5.modechoicehbschool")
        home_base_shopping = module_lookup("translink.emme.stage3.step5.modechoicehbshop")
        home_base_personal_business = module_lookup("translink.emme.stage3.step5.modechoicehbpersonalbusiness")
        home_base_university = module_lookup("translink.emme.stage3.step5.modechoicehbuniversity")
        home_base_social = module_lookup("translink.emme.stage3.step5.modechoicehbsocial")
        home_base_escort = module_lookup("translink.emme.stage3.step5.modechoicehbesc")
        non_home_base_other = module_lookup("translink.emme.stage3.step5.modechoicenhbo")
        non_home_base_work = module_lookup("translink.emme.stage3.step5.modechoicenhbw")
        park_and_ride = _modeller.Modeller().tool("translink.emme.stage3.step5.parkandride")

        is_last_iteration = (iteration_number == (max_iterations - 1))
        scenario = _modeller.Modeller().scenario

        self.calculate_flag_matrices(scenario)

        home_base_work.run_model(scenario, root_directory, iteration_number, is_last_iteration)
        home_base_school.run_model(scenario, root_directory, iteration_number, is_last_iteration)
        home_base_shopping.run_model(scenario, root_directory, iteration_number, is_last_iteration)
        home_base_personal_business.run_model(scenario, root_directory, iteration_number, is_last_iteration)
        home_base_university.run_model(scenario, root_directory, iteration_number, is_last_iteration)
        home_base_social.run_model(scenario, root_directory, iteration_number, is_last_iteration)
        home_base_escort.run_model(scenario, root_directory, iteration_number, is_last_iteration)
        non_home_base_other.run_model(scenario, root_directory, iteration_number, is_last_iteration)
        non_home_base_work.run_model(scenario, root_directory, iteration_number, is_last_iteration)

        if run_park_and_ride:
            park_and_ride(scenario)

        self.add_external_demand(scenario)

    @_modeller.logbook_trace("Calculate flag matrices")
    def calculate_flag_matrices(self, scenario):
        compute_matrix = _modeller.Modeller().tool(
            "inro.emme.matrix_calculation.matrix_calculator")

        expressions_list = [
            ['(mf107.gt.0)', 'mf110'],
            ['(mf112.gt.0)', 'mf115'],
            ['(mf117.gt.0)', 'mf121'],
            ['(mf125.gt.0)', 'mf129'],
            ['(mf128.lt.50)', 'mf130'],
            ['(mf107.gt.0)*(mf109.lt.60)*((mf106+mf107+mf108+mf109).lt.180)*(mf108.lt.6)', 'mf132'],
            ['(mf112.gt.0)*(mf114.lt.60)*((mf111+mf112+mf113+mf114).lt.180)*(mf113.lt.6)', 'mf133'],
            ['(mf117.gt.0)*(mf120.lt.75)*((mf116+mf117+mf118).lt.150)*(mf119.lt.7)', 'mf134'],
            ['(mf125.gt.0)*(mf128.lt.75)*((mf124+mf125+mf126).lt.150)*(mf127.lt.7)', 'mf135'],
            ['(mf134+mf135).gt.0', 'mf157'],
            ['mf108-(mf110.eq.1)', 'mf136'],
            ['mf113-(mf115.eq.1)', 'mf137'],
            ['mf119-(mf121.eq.1)', 'mf138'],
            ['mf127-(mf129.eq.1)', 'mf139'],
            ['(mf132+mf133).gt.0', 'mf151']]

        spec_list = []
        for expression, result in expressions_list:
            spec_list.append(build_spec(expression, result))

        compute_matrix(spec_list, scenario)

    @_modeller.logbook_trace("Add external demand to non-work SOV / HOV")
    def add_external_demand(self, scenario):
        spec = {
            "expression": "",
            "result": "",
            "constraint": {"by_value": None, "by_zone": None},
            "aggregation": {"origins": None, "destinations": None},
            "type": "MATRIX_CALCULATION"
        }
        ## Add external SOV/HOV matrices to non work med/high matrices
        compute_matrix = _modeller.Modeller().tool(
            "inro.emme.matrix_calculation.matrix_calculator")

        spec["expression"] = "mf847+mf978"
        spec["result"] = "mf847"
        compute_matrix(spec, scenario)

        spec["expression"] = "mf852+mf979"
        spec["result"] = "mf852"
        compute_matrix(spec, scenario)

        spec["expression"] = "mf860+mf984"
        spec["result"] = "mf860"
        compute_matrix(spec, scenario)

        spec["expression"] = "mf865+mf985"
        spec["result"] = "mf865"
        compute_matrix(spec, scenario)
