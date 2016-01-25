##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.stage5.step10.regionaltruck
##--Purpose: This module generates light and heavy regional truck matrices
##--         Landuse Based Model produces trip light and heavy productions and attractions which are balanced
##--         Trip Distribution is conducted using gravity model
##--         Time Slice Factors used to derive AM and MD truck traffic
##---------------------------------------------------------------------
import inro.modeller as _modeller
import os
import traceback as _traceback
from datetime import datetime
eb = _modeller.Modeller().emmebank

RgL11=107040
RgH11=45950

class RegTruckModel(_modeller.Tool()):

	spec_as_dict = {
			"expression": "EXPRESSION",
			"result": "RESULT",
			"constraint": {
				"by_value": None,
				"by_zone": {"origins": None, "destinations": None}
			},
			"aggregation": {"origins": None, "destinations": None},
			"type": "MATRIX_CALCULATION"
		}


	tool_run_msg = _modeller.Attribute(unicode)

	def page(self):
        pb = _modeller.ToolPageBuilder(self)
        pb.title = "Regional Truck Trips Model"
        pb.description = "Generates base/future forecasts for regional light and heavy trucks trips"
        pb.branding_text = "TransLink"

		if self.tool_run_msg:
			pb.add_html(self.tool_run_msg)

		return pb.render()

	def run(self):


		self.tool_run_msg = ""

		try:
			self.__call__()
			run_msg = "Tool completed"
			self.tool_run_msg = _modeller.PageBuilder.format_info(run_msg)
		except Exception, e:
			self.tool_run_msg = _modeller.PageBuilder.format_exception(e, _traceback.format_exc(e))

	def __call__(self, Year, Sensitivity, RegionalGrowth1, RegionalGrowth2):

		with _modeller.logbook_trace("Regional Truck Model"):

			process = _modeller.Modeller().tool("inro.emme.data.matrix.matrix_transaction")
			root_directory = os.path.dirname(_modeller.Modeller().emmebank.path) + "\\"
			matrix_file1 = os.path.join(root_directory, "TruckBatchFiles", "RGBatchIn.txt")
			process(transaction_file=matrix_file1, throw_on_error=True)

			NAMESPACE="inro.emme.prompt.run_macro"
		# Run regional truck model Macro

			run_macro=_modeller.Modeller().tool(NAMESPACE)
			run_macro(macro_name="trkmodamregv1.mac")

			MATCALC = "inro.emme.matrix_calculation.matrix_calculator"
			compute_matrix = _modeller.Modeller().tool(MATCALC)


			RegSpec=self.spec_as_dict
			RegSpec['expression'] = "mf1031"
			RegSpec['result']='ms151'
			RegSpec['aggregation']['origins']="+"
			RegSpec['aggregation']['destinations']="+"
			compute_matrix(RegSpec)

			RegSpec['expression'] = "mf1034"
			RegSpec['result']='ms152'
			compute_matrix(RegSpec)

			self.ResetSpec(RegSpec)

			RgLg = eb.matrix("ms151")
			RgHv=eb.matrix("ms152")
			RgLgVal=RgLg.data
			RgHvVal=RgHv.data

			# Determine Regional Sector Growth based on user inputs
			if Sensitivity=="N":
				RatioL=1
				RatioH=1

			else:

				CAGRLightI=(RgLgVal/RgL11)**(1/float(Year-2011))
				CAGRHeavyI=(RgHvVal/RgH11)**(1/float(Year-2011))
				RatioL=(RgLgVal/CAGRLightI**(Year-2030)*((1+RegionalGrowth1/100)/(CAGRLightI))**(2030-2011)*(1+RegionalGrowth2/100)**(Year-2030))/RgLgVal
				RatioH=(RgHvVal/CAGRHeavyI**(Year-2030)*((1+RegionalGrowth1/100)/(CAGRHeavyI))**(2030-2011)*(1+RegionalGrowth2/100)**(Year-2030))/RgHvVal


			MatrixList1=["mf1031","mf1035","mf1036"]
			MatrixList2=["mf1034","mf1037","mf1038"]

			for i in range(len(MatrixList1)):

				RegSpec['expression'] = MatrixList1[i]+"*"+str(RatioL)
				RegSpec['result']=MatrixList1[i]
				compute_matrix(RegSpec)

			for i in range(len(MatrixList2)):

				RegSpec['expression'] = MatrixList2[i]+"*"+str(RatioH)
				RegSpec['result']=MatrixList2[i]
				compute_matrix(RegSpec)




	def ResetSpec (self, SpecItems):

		SpecItems['constraint']['by_zone']['origins'] = None
		SpecItems['constraint']['by_zone']['destinations'] = None
		SpecItems['aggregation']['origins'] = None
		SpecItems['aggregation']['destinations'] = None
