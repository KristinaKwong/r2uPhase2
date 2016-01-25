#--------------------------------------------------
##--TransLink Phase 2 Regional Transportation Model
##--
##--Path:
##--Purpose:
##--------------------------------------------------
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
##---------------------------------------------------

import inro.modeller as _m
import os
import traceback as _traceback


class SkimsAccessibilities(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        start_path = os.path.dirname(_m.Modeller().emmebank.path)
        ##Create various aspects to the page
        pb = _m.ToolPageBuilder(self, title="Weighted Skims and new accessibilities",
                                       description=""" Generates new weighted skims and calculates
                            new accessibilities    """,
                                       branding_text="- Translink - HDR CORPORATION")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        with _m.logbook_trace("07-04 - RUN - Weighted Skims and Accessibilities"):

			self.tool_run_msg = ""
			emmebank = _m.Modeller().emmebank
			PathHeader = os.path.dirname(emmebank.path)
			try:
				self.__call__(PathHeader, 1)
				run_msg = "Tool completed"
				self.tool_run_msg = _m.PageBuilder.format_info(run_msg)
			except Exception, e:
				self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    def __call__(self, PathHeader, IterationNumber):
    ##        Start logging this under a new 'nest'
        with _m.logbook_trace("07-04 - Weighted Skims and New Accessibilities"):
            self.Matrix_Batchins(PathHeader)
            self.weightedskims(IterationNumber)
            self.accessibilities()

    def weightedskims(self, IterationNumber):
        with _m.logbook_trace("Weighted Skims"):
            NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
            compute_matrix = _m.Modeller().tool(NAMESPACE)

            if IterationNumber == 0:
                j = 0.5
                k = 1

            if IterationNumber > 0:
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
                ['mf931-mf930*6*ms18-mf932*ms19*6', 'mf931'],
                ['mf100*(1-' + str(j) + ')+mf930*' + str(j), 'mf100'],
                ['mf101*(1-' + str(j) + ')+mf931*' + str(j), 'mf101'],
                ['mf102*(1-' + str(j) + ')+mf932*' + str(j), 'mf102'],
                ['mf106*(1-' + str(k) + ')+mf933*' + str(k), 'mf106'],
                ['mf107*(1-' + str(k) + ')+mf934*' + str(k), 'mf107'],
                ['mf108*(1-' + str(k) + ')+mf935*' + str(k), 'mf108'],
                ['mf109*(1-' + str(k) + ')+mf936*' + str(k), 'mf109'],
                ['mf116*(1-' + str(k) + ')+mf937*' + str(k), 'mf116'],
                ['mf117*(1-' + str(k) + ')+mf938*' + str(k), 'mf117'],
                ['mf118*(1-' + str(k) + ')+mf939*' + str(k), 'mf118'],
                ['mf119*(1-' + str(k) + ')+mf940*' + str(k), 'mf119'],
                ['mf120*(1-' + str(k) + ')+mf941*' + str(k), 'mf120'],
                ['mf163*(1-' + str(k) + ')+(mf954+mf956+mf957)*' + str(k), 'mf163'],
                ['mf164*(1-' + str(k) + ')+mf955*' + str(k), 'mf164']
            ]

            expressions_list_md = [
                ['mf943-mf942*6*ms18-mf944*ms19*6', 'mf943'],
                ['mf103*(1-' + str(j) + ')+mf942*' + str(j), 'mf103'],
                ['mf104*(1-' + str(j) + ')+mf943*' + str(j), 'mf104'],
                ['mf105*(1-' + str(j) + ')+mf944*' + str(j), 'mf105'],
                ['mf111*(1-' + str(k) + ')+mf945*' + str(k), 'mf111'],
                ['mf112*(1-' + str(k) + ')+mf946*' + str(k), 'mf112'],
                ['mf113*(1-' + str(k) + ')+mf947*' + str(k), 'mf113'],
                ['mf114*(1-' + str(k) + ')+mf948*' + str(k), 'mf114'],
                ['mf124*(1-' + str(k) + ')+mf949*' + str(k), 'mf124'],
                ['mf125*(1-' + str(k) + ')+mf950*' + str(k), 'mf125'],
                ['mf126*(1-' + str(k) + ')+mf951*' + str(k), 'mf126'],
                ['mf127*(1-' + str(k) + ')+mf952*' + str(k), 'mf127'],
                ['mf128*(1-' + str(k) + ')+mf953*' + str(k), 'mf128'],
                ['mf167*(1-' + str(k) + ')+(mf958+mf960+mf961)*' + str(k), 'mf167'],
                ['mf168*(1-' + str(k) + ')+mf959*' + str(k), 'mf168']
            ]

            for n in range(0, len(expressions_list_am)):
                spec_as_dict['expression'] = expressions_list_am[n][0]
                spec_as_dict['result'] = expressions_list_am[n][1]
                compute_matrix(spec_as_dict)
                spec_as_dict['expression'] = expressions_list_md[n][0]
                spec_as_dict['result'] = expressions_list_md[n][1]
                compute_matrix(spec_as_dict)

    def accessibilities(self):
		with _m.logbook_trace("Accessibilities Calculation"):
			NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
			compute_matrix = _m.Modeller().tool(NAMESPACE)
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
				['ln(md12+1*(md12.eq.0))/(mf101*mf101)', 'mf101', 'mo47'],
				['ln(md12+1*(md12.eq.0))/((2*(mf954+mf106*(p.eq.q))+mf164)*(2*(mf954+mf106*(p.eq.q))+mf164))', 'mf164',
				 'mo392'],
				['ln(md8+1*(md8.eq.0))/(mf101*mf101)', 'mf101', 'mo954'],
				['ln(md8+1*(md8.eq.0))/((2*(mf954+mf106*(p.eq.q))+mf164)*(2*(mf954+mf106*(p.eq.q))+mf164))', 'mf164',
				 'mo955'],
				['ln(md23+1*(md23.eq.0))/(mf101*mf101)', 'mf101', 'mo48'],
				['ln(md23+1*(md23.eq.0))/((2*(mf954+mf106*(p.eq.q))+mf164)*(2*(mf954+mf106*(p.eq.q))+mf164))', 'mf164',
				 'mo957'],
				['ln(md8+md9+md10+md11+1*((md8+md9+md10+md11).eq.0))/(mf101*mf101)', 'mf101', 'mo960'],
				[
					'ln(md8+md9+md10+md11+1*((md8+md9+md10+md11).eq.0))/((2*(mf954+mf106*(p.eq.q))+mf164)*(2*(mf954+mf106*(p.eq.q))+mf164))',
					'mf164', 'mo961']
			]

			for i in range(0, len(expressions_list)):
				spec_as_dict['expression'] = expressions_list[i][0]
				spec_as_dict['constraint']['by_value']['od_values'] = expressions_list[i][1]
				spec_as_dict['result'] = expressions_list[i][2]
				compute_matrix(spec_as_dict)

			spec_as_dict = {
			"expression": "EXPRESSION",
			"result": "RESULT",
			"constraint": {
				"by_value": None,
				"by_zone": {"origins": "1000-8999", "destinations": "1000-8999"}
			},
			"aggregation": {"origins": None,"destinations": "+"},
			"type": "MATRIX_CALCULATION"
		}

		expressions_list = [
			['(((1+2.60666873)/(1+2.60666873*exp(0.089779362*(mf66/4.8*60-10)))).min.1)*md12', 'mo980'],
			['(((1+0.370394973)/(1+0.370394973*exp(0.08364252*(mf66/20*60-10)))).min.1)*md12', 'mo981'],
			['(((1+0.078322901)/(1+0.078322901*exp(0.069553623*(mf163+mf164-10)))).min.1)*md12', 'mo982'],
			['(((1+0.757971496)/(1+0.757971496*exp(0.062315134*(mf68-10)))).min.1)*md12', 'mo983'],
			['(((1+25.08837939)/(1+25.08837939*exp(0.095638856*(mf66/4.8*60-10)))).min.1)*(md8+md9+md10+md11)',
			 'mo984'],
			['(((1+712.7262949)/(1+712.7262949*exp(0.078649899*(mf66/20*60-10)))).min.1)*(md8+md9+md10+md11)',
			 'mo985'],
			['(((1+0.64089269)/(1+0.64089269*exp(0.061917065*(mf167+mf168-10)))).min.1)*(md8+md9+md10+md11)',
			 'mo986'],
			['(((1+1021.763665)/(1+1021.763665*exp(0.086254525*(mf68-10)))).min.1)*(md8+md9+md10+md11)', 'mo987'],
			[
			'(((((1+0.078322901)/(1+0.078322901*exp(0.069553623*(mf163+mf164-10)))).min.1)*md12).max.((((1+0.757971496)/(1+0.757971496*exp(0.062315134*(mf68-10)))).min.1)*md12)).max.((((1+0.370394973)/(1+0.370394973*exp(0.08364252*(mf66/20*60-10)))).min.1)*md12)',
			'mo988'],
			[
			'(((((1+0.078322901)/(1+0.078322901*exp(0.069553623*(mf163+mf164-10)))).min.1)*md12).max.((((1+0.370394973)/(1+0.370394973*exp(0.08364252*(mf66/20*60-10)))).min.1)*md12))',
			'mo989'],
			[
			'(((((1+712.7262949)/(1+712.7262949*exp(0.078649899*(mf66/20*60-10)))).min.1)*(md8+md9+md10+md11)).max.((((1+0.64089269)/(1+0.64089269*exp(0.061917065*(mf167+mf168-10)))).min.1)*(md8+md9+md10+md11))).max.((((1+1021.763665)/(1+1021.763665*exp(0.086254525*(mf68-10)))).min.1)*(md8+md9+md10+md11))',
			'mo990']
		]
		for n in range(0, len(expressions_list)):
			spec_as_dict['expression'] = expressions_list[n][0]
			spec_as_dict['result'] = expressions_list[n][1]
			compute_matrix(spec_as_dict)


    def Matrix_Batchins(self, PathHeader):
        with _m.logbook_trace("Matrix Batchin"):
        ##
            NAMESPACE = "inro.emme.data.matrix.matrix_transaction"
            process = _m.Modeller().tool(NAMESPACE)
            matrix_file = PathHeader + "/07_PostAssignment/Inputs/Accessibilities.txt"
            ##        Creates process transaction
            process(transaction_file=matrix_file,
                    throw_on_error=True,
                    scenario=_m.Modeller().scenario)
