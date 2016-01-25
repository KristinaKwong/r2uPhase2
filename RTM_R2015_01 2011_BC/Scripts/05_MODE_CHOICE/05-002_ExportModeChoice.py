##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.stage3.step5.exportmodechoice
##--Purpose: Exporting Mode Choice Out
##---------------------------------------------------------------------
import inro.modeller as _m
from datetime import datetime


# TODO: add tool interface to mode choice procedure
class ModeChoiceHBSchool(_m.Tool()):
    tool_run_msg = ""

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Export Mode Choice Demand"
        pb.description = "Not to be used directly, module containing methods to export mode choice demand"
        pb.branding_text = "TransLink"
        pb.runnable=False

        return pb.render()

    @_m.logbook_trace("Output Results")
    def Export_Demand(self, filename):
        print "--------Output_Results, " + str(datetime.now())
        ##    Create emmebank object
        my_modeller = _m.Modeller()
        my_emmebank = my_modeller.desktop.data_explorer().active_database().core_emmebank

        ##    List to hold matrix objects
        mf_value = []

        ##    Loop to append all result matrices onto the variable 'mf_value'
        # for mf_num in range(870,878):
        for mf_num in range(882, 890):
            # print "mf"+str(mf_num)
            mf_value.append(my_emmebank.matrix("mf" + str(mf_num)))

            ##    Export matrices using the appended list of mf_value matrices
        export_matrices = _m.Modeller().tool(
            "inro.emme.data.matrix.export_matrices")

        ## Export matrix data aggregated to the gy ensemble
        export_matrices(export_file=filename,
                        field_separator=' ',
                        matrices=mf_value,
                        constraint={
                            'by_value': {},
                            'by_zone': {'origins': 'gy1-gy14', 'destinations': 'gy1-gy14'}
                        },
                        partition_aggregation={'origins': 'gy', 'destinations': 'gy', 'operator': 'sum'},
                        export_format="PROMPT_DATA_FORMAT",
                        skip_default_values=False,
                        full_matrix_line_format="ONE_ENTRY_PER_LINE")

    ## Aggregate purpose-level results by mode into matrices mf882 - mf890
    @_m.logbook_trace("Aggregate purpose-level results by mode into matrices mf882 - mf890")
    def Agg_Exp_Demand(self, PathHeader, purp, n):
        purp_list = ['Hbw', 'HbSc', 'HbSh', 'HbPb', 'HbU', 'HbSoc', 'HbEsc', 'NHBO', 'NHBW']
        income = ['lowinc', 'medinc', 'highinc']
        auto = ['_zero_auto', '_one_auto', '_twoplus_auto']
        with _m.logbook_trace("Aggregate Demand " + purp_list[purp - 1]):
            NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
            compute_matrix = _m.Modeller().tool(NAMESPACE)

            matagg = 882
            spec_as_dict = {
                "expression": "1",
                "result": "mf201",
                "constraint": {"by_value": None, "by_zone": None},
                "aggregation": {"origins": None, "destinations": None},
                "type": "MATRIX_CALCULATION"
            }
            if purp == 1:
                startmat = 505
                for p in range(3):
                    for i in range(3):

                        self.Export_Matrix_Batchins(PathHeader, purp)
                        for j in range(7):
                            for k in range(3):
                                if p == 0:
                                    expression1 = "mf" + str(matagg + j) + "+" + "mf" + str(startmat + 9 * j + k + 3 * i)
                                if p == 1:
                                    expression1 = "mf" + str(matagg + j) + "+" + "mf" + str(startmat + 9 * j + 3 * k + i)
                                if p == 2:
                                    expression1 = "mf" + str(matagg + j) + "+" + "mf" + str(
                                        startmat + 9 * j + k) + "+" + "mf" + str(
                                        startmat + 9 * j + 3 + k) + "+" + "mf" + str(startmat + 9 * j + 6 + k)
                                result = "mf" + str(matagg + j)
                                spec_as_dict["expression"] = expression1
                                spec_as_dict["result"] = result
                                report = compute_matrix(spec_as_dict)
                        if p == 0:
                            exportfile = PathHeader + '05_MODE_CHOICE/Outputs/' + purp_list[
                                purp - 1] + '/Overall_Results_' + purp_list[purp - 1] + "_" + income[i] + "_" + str(
                                n) + '.txt'
                        if p == 1:
                            exportfile = PathHeader + '05_MODE_CHOICE/Outputs/' + purp_list[
                                purp - 1] + '/Overall_Results_' + purp_list[purp - 1] + "_" + auto[i] + "_" + str(
                                n) + '.txt'
                        if p == 2:
                            exportfile = PathHeader + '05_MODE_CHOICE/Outputs/' + purp_list[
                                purp - 1] + '/Overall_Results_' + purp_list[purp - 1] + "_" + str(n) + '.txt'
                        self.Export_Demand(exportfile)

            if purp > 1 and purp < 8:
                startmat = 640
                self.Export_Matrix_Batchins(PathHeader, purp)
                for j in range(7):
                    for k in range(9):
                        if purp == 2:
                            if j == 2:
                                expression1 = "mf" + str(matagg + j + 5) + "+" + "mf" + str(startmat + k + 9 * j)
                            else:
                                expression1 = "mf" + str(matagg + j) + "+" + "mf" + str(startmat + k + 9 * j)
                            if j == 2:
                                result = "mf" + str(matagg + j + 5)
                            else:
                                result = "mf" + str(matagg + j)
                            spec_as_dict["expression"] = expression1
                            spec_as_dict["result"] = result
                            report = compute_matrix(spec_as_dict)
                        else:
                            expression1 = "mf" + str(matagg + j) + "+" + "mf" + str(startmat + k + 9 * j)
                            result = "mf" + str(matagg + j)
                            spec_as_dict["expression"] = expression1
                            spec_as_dict["result"] = result
                            report = compute_matrix(spec_as_dict)

                exportfile = PathHeader + '05_MODE_CHOICE/Outputs/' + purp_list[purp - 1] + '/Overall_Results_' + purp_list[
                    purp - 1] + "_" + str(n) + '.txt'
                self.Export_Demand(exportfile)

            if purp > 7:
                self.Export_Matrix_Batchins(PathHeader, purp)
                startmat = 643
                for j in range(7):
                    for k in range(3):
                        expression1 = "mf" + str(matagg + j) + "+" + "mf" + str(startmat + k + 9 * j)
                        result = "mf" + str(matagg + j)
                        spec_as_dict["expression"] = expression1
                        spec_as_dict["result"] = result
                        report = compute_matrix(spec_as_dict)
                exportfile = PathHeader + '05_MODE_CHOICE/Outputs/' + purp_list[purp - 1] + '/Overall_Results_' + purp_list[
                    purp - 1] + "_" + str(n) + '.txt'
                self.Export_Demand(exportfile)
                if purp == 8:
                    nwmat = 568
                    for i in range(3):
                        self.Export_Matrix_Batchins(PathHeader, purp)
                        for j in range(8):
                            for k in range(3):
                                expression1 = "mf" + str(matagg + j) + "+" + "mf" + str(nwmat + 9 * j + k + 3 * i)
                                result = "mf" + str(matagg + j)
                                spec_as_dict["expression"] = expression1
                                spec_as_dict["result"] = result
                                report = compute_matrix(spec_as_dict)

                        exportfile = PathHeader + '05_MODE_CHOICE/Outputs/Nonwork/Overall_Results_' + income[i] + "_" + str(
                            n) + '.txt'
                        self.Export_Demand(exportfile)

    def Export_Matrix_Batchins(self, PathHeader, purp):
        with _m.logbook_trace("Matrix Batchin"):
        ##        Sets up the 'matrix transaction' tool and runs it
            NAMESPACE = "inro.emme.data.matrix.matrix_transaction"
            process = _m.Modeller().tool(NAMESPACE)
            if purp == 1:
                matrix_file = PathHeader + "05_MODE_CHOICE/Inputs/Outputmatrix1.txt"
            else:
                matrix_file = PathHeader + "05_MODE_CHOICE/Inputs/Outputmatrix2.txt"
                ##        Creates process transaction
            process(transaction_file=matrix_file,
                    throw_on_error=True,
                    scenario=_m.Modeller().scenario)
