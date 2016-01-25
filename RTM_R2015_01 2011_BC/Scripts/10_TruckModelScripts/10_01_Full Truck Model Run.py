##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.stage5.step10.truckmodel
##--Purpose: Run Full truck Model
##---------------------------------------------------------------------
import inro.modeller as _modeller
import os
import traceback as _traceback
from datetime import datetime

class FullTruckModel(_modeller.Tool()):

	Year= _modeller.Attribute(str)
	Sensitivity=_modeller.Attribute(str)
	ExtGrowth1=_modeller.Attribute(float)
	ExtGrowth2=_modeller.Attribute(float)
	AMScenario=_modeller.Attribute(_modeller.InstanceType)
	MDScenario=_modeller.Attribute(_modeller.InstanceType)
	CascadeGrowth1=_modeller.Attribute(float)
	CascadeGrowth2=_modeller.Attribute(float)
	RegionalGrowth1=_modeller.Attribute(float)
	RegionalGrowth2=_modeller.Attribute(float)
	AsiaPacificGrowth=_modeller.Attribute(str)




	tool_run_msg = _modeller.Attribute(unicode)

	def page(self):
        pb = _modeller.ToolPageBuilder(self)
        pb.title = "Full Truck Model Run"
        pb.description = "Run Full Truck Model"
        pb.branding_text = "TransLink"

		pb.add_select_scenario(tool_attribute_name="AMScenario",title="Select AM Scenario")

		pb.add_select_scenario(tool_attribute_name="MDScenario",title="Select MD Scenario")

		pb.add_select(tool_attribute_name="Year",keyvalues=[['1','2011'],['2','2030'],['3','2045']],
						title="Choose Analysis Year (2011, 2030 or 2045)")

		pb.add_select(tool_attribute_name="Sensitivity",keyvalues=[['N','No'],['Y','Yes']],
						title="Choose whether to modify truck growth rates ")

		with pb.section("Sensitivity options-Future Runs:"):
			pb.add_text_box(tool_attribute_name="ExtGrowth1",
							size="3",
							title="Enter External Sector % Growth Assumption 2011-2030 ")

			pb.add_text_box(tool_attribute_name="ExtGrowth2",
							size="3",
							title="Enter External Sector % Growth Assumption 2030-2045")

			pb.add_text_box(tool_attribute_name="CascadeGrowth1",
							size="3",
							title="Enter Cascade Cross-Border % Growth Assumption 2011-2030")

			pb.add_text_box(tool_attribute_name="CascadeGrowth2",
							size="3",
							title="Enter Cascade Cross-Border % Growth Assumption 2030-2045")

			pb.add_text_box(tool_attribute_name="RegionalGrowth1",
							size="3",
							title="Enter Regional Sector Growth % Assumption 2011-2030")

			pb.add_text_box(tool_attribute_name="RegionalGrowth2",
							size="3",
							title="Enter Regional Sector Growth % Assumption 2030-2045")

			pb.add_select(tool_attribute_name="AsiaPacificGrowth",
							keyvalues=[['B','Base'],['L','Low'],['M','Med'],['H','High']],
							title="Enter Asia Pacific Growth Assumption")
		pb.add_html("""
			<script>
				$(document).ready( function ()
				{
					// indent tool section items
					$(".t_tool_section")
						.children('.t_element')
						.css('padding-left', '70px');

					$('#Sensitivity').bind('change', function ()
					{
						$(this).commit();
						if ($(this).val() == 'N')
							var disable = true;
						else
							var disable = false;
						$('#ExtGrowth1').prop('disabled', disable);
						$('#ExtGrowth2').prop('disabled', disable);
						$('#CascadeGrowth1').prop('disabled', disable);
						$('#CascadeGrowth2').prop('disabled', disable);
						$('#RegionalGrowth1').prop('disabled', disable);
						$('#RegionalGrowth2').prop('disabled', disable);
						$('#AsiaPacificGrowth').prop('disabled', disable);
					}).trigger('change') ;
				});
			</script>""")

		if self.tool_run_msg:
			pb.add_html(self.tool_run_msg)

		return pb.render()

	def run(self):


		try:
			if self.Year=="1":
				AnalysisYear=2011
				self.Sensitivity="N"
				self.ExtGrowth1=""
				self.ExtGrowth2=""
				self.CascadeGrowth1=""
				self.CascadeGrowth2=""
				self.RegionalGrowth1=""
				self.RegionalGrowth2=""
				self.AsiaPacificGrowth="B"
				self.__call__(AnalysisYear,self.Sensitivity,self.AMScenario,self.MDScenario,0,0,0,0,0,0,"")

			if self.Year=="2":
				AnalysisYear=2030
				if self.Sensitivity=="N":
					self.ExtGrowth1=""
					self.ExtGrowth2=""
					self.CascadeGrowth1=""
					self.CascadeGrowth2=""
					self.RegionalGrowth1=""
					self.RegionalGrowth2=""
					self.AsiaPacificGrowth="B"


				if self.Sensitivity=="Y":
					self.ExtGrowth2=""
					self.CascadeGrowth2=""
					self.RegionalGrowth2=""

				self.__call__(AnalysisYear, self.Sensitivity,self.AMScenario,self.MDScenario,self.ExtGrowth1, 0
				, self.CascadeGrowth1, 0, self.RegionalGrowth1, 0, self.AsiaPacificGrowth)

			if self.Year=="3":
				AnalysisYear=2045
				if self.Sensitivity=="N":
					self.ExtGrowth1=""
					self.ExtGrowth2=""
					self.CascadeGrowth1=""
					self.CascadeGrowth2=""
					self.RegionalGrowth1=""
					self.RegionalGrowth2=""
					self.AsiaPacificGrowth="B"



				self.__call__(AnalysisYear, self.Sensitivity,self.AMScenario,self.MDScenario,self.ExtGrowth1, self.ExtGrowth2, self.CascadeGrowth1, self.CascadeGrowth2,
								self.RegionalGrowth1, self.RegionalGrowth2, self.AsiaPacificGrowth)


			run_msg = "Tool completed"
			self.tool_run_msg = _modeller.PageBuilder.format_info(run_msg)


		except Exception, e:


				self.tool_run_msg = _modeller.PageBuilder.format_exception(e, _traceback.format_exc(e))



	def __call__(self, Year, Sensitivity, AMScenario,MDScenario, ExtGrowth1, ExtGrowth2, CascadeGrowth1, CascadeGrowth2, RegionalGrowth1, RegionalGrowth2, AsiaPacificGrowth):



		with _modeller.logbook_trace("Full Truck Model Run"):

			ExternalModel=_modeller.Modeller().tool("translink.emme.stage5.step10.externaltruck")
			ExternalModel(Year,Sensitivity,ExtGrowth1,ExtGrowth2, CascadeGrowth1, CascadeGrowth2)
			AsiaPacificModel=_modeller.Modeller().tool("translink.emme.stage5.step10.asiapacifictruck")
			AsiaPacificModel(Year)
			RegionalModel=_modeller.Modeller().tool("translink.emme.stage5.step10.regionaltruck")
			RegionalModel(Year,Sensitivity,RegionalGrowth1, RegionalGrowth2)
			TruckAssign=_modeller.Modeller().tool("translink.emme.stage5.step10.truckassign")
			TruckAssign(AMScenario,MDScenario)
