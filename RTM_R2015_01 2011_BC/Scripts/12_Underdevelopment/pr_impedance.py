##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model Development
##--
##--Path: translink.emme.?
##--Purpose: Generate Impedance for Park and Ride Access Mode
##---------------------------------------------------------------------
import inro.modeller as _m
import os
import csv
import traceback as _traceback

class PrImpedance(_m.Tool()):
	tool_run_msg = _m.Attribute(unicode)

	def page(self):
		pb = _m.ToolPageBuilder(self)
		pb.title = "Calculate Impedance for Park and Ride Access Mode"
		pb.description = "Calculates Impedance for PnR based on Best Lot"
		pb.branding_text = "TransLink"

		if self.tool_run_msg:
			pb.add_html(self.tool_run_msg)

		return pb.render()

	def run(self):
		with _m.logbook_trace("UNDER DEV - PR Impedance"):
			self.tool_run_msg = ""
			try:
				eb = _m.Modeller().emmebank
				self.__call__(eb)
				self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
			except Exception, e:
				self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))



	@_m.logbook_trace("UNDER DEV - PNR Impedance")
	def __call__(self, eb):

		util = _m.Modeller().tool("translink.emme.util")
		input_path = util.get_input_path(eb)
		pnr_costs = os.path.join(input_path, "pnr_inputs.csv")
		model_year = int(eb.matrix("ms149").data)

		#RailSkim = _m.Modeller().tool("translink.emme.under_dev.wceskim")
		# railassign = _m.Modeller().tool("inro.emme.transit_assignment.extended_transit_assignment")

		self.matrix_batchins(eb)
		self.read_file(eb, pnr_costs)

		self.AutoGT(eb)
		self.BusGT(eb)
		self.RailGT(eb)
		self.WceGT(eb)
		self.bestlot(eb, model_year)

		# BUS WORK
		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		ral_imp_am_wk  =  {"busIVT" : ["mf107", "mf6010", "mf6000"],
						   "busWait" : ["mf106", "mf6011", "mf6000"],
						   "auxTransit" : ["mf109", "mf6013", "mf6000"],
						   "boardings" : ["mf108", "mf6012", "mf6000"],
						   "busFare" : ["mf160", "mf6014", "mf6000"]}

		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		ral_imp_md_wk  =  {"busIVT" : ["mf112", "mf6055", "mf6000"],
						   "busWait" : ["mf111", "mf6056", "mf6000"],
						   "auxTransit" : ["mf114", "mf6058", "mf6000"],
						   "boardings" : ["mf113", "mf6057", "mf6000"],
						   "busFare" : ["mf160", "mf6059", "mf6000"]}

		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		ral_imp_pm_wk  =  {"busIVT" : ["mf2107", "mf6095", "mf6000"],
						   "busWait" : ["mf2106", "mf6096", "mf6000"],
						   "auxTransit" : ["mf2109", "mf6098", "mf6000"],
						   "boardings" : ["mf2108", "mf6097", "mf6000"],
						   "busFare" : ["mf160", "mf6099", "mf6000"]}


		# Bus nonWork
		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		ral_imp_am_nw  =  {"busIVT" : ["mf107", "mf6140", "mf6130"],
						   "busWait" : ["mf106", "mf6141", "mf6130"],
						   "auxTransit" : ["mf109", "mf6143", "mf6130"],
						   "boardings" : ["mf108", "mf6142", "mf6130"],
						   "busFare" : ["mf160", "mf6144", "mf6130"]}

		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		ral_imp_md_nw  =  {"busIVT" : ["mf112", "mf6180", "mf6130"],
						   "busWait" : ["mf111", "mf6181", "mf6130"],
						   "auxTransit" : ["mf114", "mf6183", "mf6130"],
						   "boardings" : ["mf113", "mf6182", "mf6130"],
						   "busFare" : ["mf160", "mf6184", "mf6130"]}

		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		ral_imp_pm_nw  =  {"busIVT" : ["mf2107", "mf6220", "mf6130"],
						   "busWait" : ["mf2106", "mf6221", "mf6130"],
						   "auxTransit" : ["mf2109", "mf6223", "mf6130"],
						   "boardings" : ["mf2108", "mf6222", "mf6130"],
						   "busFare" : ["mf160", "mf6224", "mf6130"]}

		self.SplitTransitImpedance(eb, imp_dict = ral_imp_am_wk, year = model_year)
		self.SplitTransitImpedance(eb, imp_dict = ral_imp_md_wk, year = model_year)
		self.SplitTransitImpedance(eb, imp_dict = ral_imp_pm_wk, year = model_year)
		self.SplitTransitImpedance(eb, imp_dict = ral_imp_am_nw, year = model_year)
		self.SplitTransitImpedance(eb, imp_dict = ral_imp_md_nw, year = model_year)
		self.SplitTransitImpedance(eb, imp_dict = ral_imp_pm_nw, year = model_year)


		# Rail impedances to Split
		# work purposes
		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		rail_imp_am_wk = {"railIVT" : ["mf5001", "mf6020", "mf6001"],
						  "railWait" : ["mf5002", "mf6021", "mf6001"],
						  "busIVT" : ["mf5000", "mf6022", "mf6001"],
						  "auxTransit" : ["mf5004", "mf6025", "mf6001"],
						  "boardings" : ["mf5003", "mf6024", "mf6001"],
						  "railFare" : ["mf161", "mf6026", "mf6001"]}

		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		rail_imp_md_wk = {"railIVT" : ["mf5006", "mf6065", "mf6001"],
						  "railWait" : ["mf5007", "mf6066", "mf6001"],
						  "busIVT" : ["mf5005", "mf6067", "mf6001"],
						  "auxTransit" : ["mf5009", "mf6070", "mf6001"],
						  "boardings" : ["mf5008", "mf6069", "mf6001"],
						  "railFare" : ["mf161", "mf6071", "mf6001"]}

		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		rail_imp_pm_wk = {"railIVT" : ["mf5011", "mf6105", "mf6001"],
						  "railWait" : ["mf5012", "mf6106", "mf6001"],
						  "busIVT" : ["mf5010", "mf6107", "mf6001"],
						  "auxTransit" : ["mf5014", "mf6110", "mf6001"],
						  "boardings" : ["mf5013", "mf6109", "mf6001"],
						  "railFare" : ["mf161", "mf6111", "mf6001"]}

		# work purposes
		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		rail_imp_am_nw = {"railIVT" : ["mf5001", "mf6150", "mf6131"],
						  "railWait" : ["mf5002", "mf6151", "mf6131"],
						  "busIVT" : ["mf5000", "mf6152", "mf6131"],
						  "auxTransit" : ["mf5004", "mf6155", "mf6131"],
						  "boardings" : ["mf5003", "mf6154", "mf6131"],
						  "railFare" : ["mf161", "mf6156", "mf6131"]}

		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		rail_imp_md_nw = {"railIVT" : ["mf5006", "mf6190", "mf6131"],
						  "railWait" : ["mf5007", "mf6191", "mf6131"],
						  "busIVT" : ["mf5005", "mf6192", "mf6131"],
						  "auxTransit" : ["mf5009", "mf6195", "mf6131"],
						  "boardings" : ["mf5008", "mf6194", "mf6131"],
						  "railFare" : ["mf161", "mf6196", "mf6131"]}

		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		rail_imp_pm_nw = {"railIVT" : ["mf5011", "mf6230", "mf6131"],
						  "railWait" : ["mf5012", "mf6231", "mf6131"],
						  "busIVT" : ["mf5010", "mf6232", "mf6131"],
						  "auxTransit" : ["mf5013", "mf6235", "mf6131"],
						  "boardings" : ["mf5014", "mf6234", "mf6131"],
						  "railFare" : ["mf161", "mf6236", "mf6131"]}



		self.SplitTransitImpedance(eb, imp_dict = rail_imp_am_wk, year = model_year)
		self.SplitTransitImpedance(eb, imp_dict = rail_imp_md_wk, year = model_year)
		self.SplitTransitImpedance(eb, imp_dict = rail_imp_pm_wk, year = model_year)
		self.SplitTransitImpedance(eb, imp_dict = rail_imp_am_nw, year = model_year)
		self.SplitTransitImpedance(eb, imp_dict = rail_imp_md_nw, year = model_year)
		self.SplitTransitImpedance(eb, imp_dict = rail_imp_pm_nw, year = model_year)


		# West Coast Express impedances to split
		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		wce_imp_am_wk = {"wceIVT" : ["mf5052", "mf6035", "mf6002"],
						"wceWait" : ["mf5053", "mf6036", "mf6002"],
						"railIVT" : ["mf5051", "mf6037", "mf6002"],
						"busIVT" : ["mf5050", "mf6039", "mf6002"],
						"auxTransit" : ["mf5055", "mf6042", "mf6002"],
						"boardings" : ["mf5054", "mf6041", "mf6002"],
						"wceFare" : ["mf161", "mf6043", "mf6002"]}

		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
#		wce_imp_md_wk = {"wceIVT" : ["mf5058", "mf6080", "mf6002"],
#						"wceWait" : ["mf5059", "mf6081", "mf6002"],
#						"railIVT" : ["mf5057", "mf6082", "mf6002"],
#						"busIVT" : ["mf5056", "mf6084", "mf6002"],
#						"auxTransit" : ["mf5061", "mf6087", "mf6002"],
#						"boardings" : ["mf5060", "mf6086", "mf6002"],
#						"wceFare" : ["mf161", "mf6088", "mf6002"]}

		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		wce_imp_pm_wk = {"wceIVT" : ["mf5064", "mf6120", "mf6002"],
						"wceWait" : ["mf5065", "mf6121", "mf6002"],
						"railIVT" : ["mf5063", "mf6122", "mf6002"],
						"busIVT" : ["mf5062", "mf6124", "mf6002"],
						"auxTransit" : ["mf5067", "mf6127", "mf6002"],
						"boardings" : ["mf5066", "mf6126", "mf6002"],
						"wceFare" : ["mf161", "mf6128", "mf6002"]}


		# nonwork
		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		wce_imp_am_nw = {"wceIVT" : ["mf5052", "mf6165", "mf6132"],
						"wceWait" : ["mf5053", "mf6166", "mf6132"],
						"railIVT" : ["mf5051", "mf6167", "mf6132"],
						"busIVT" : ["mf5050", "mf6169", "mf6132"],
						"auxTransit" : ["mf5055", "mf6172", "mf6132"],
						"boardings" : ["mf5054", "mf6171", "mf6132"],
						"wceFare" : ["mf161", "mf6173", "mf6132"]}

		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
#		wce_imp_md_nw = {"wceIVT" : ["mf5058", "mf6205", "mf6132"],
#						"wceWait" : ["mf5059", "mf6206", "mf6132"],
#						"railIVT" : ["mf5057", "mf6207", "mf6132"],
#						"busIVT" : ["mf5056", "mf6209", "mf6132"],
#						"auxTransit" : ["mf5061", "mf6212", "mf6132"],
#						"boardings" : ["mf5060", "mf6211", "mf6132"],
#						"wceFare" : ["mf161", "mf6213", "mf6132"]}

		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		wce_imp_pm_nw = {"wceIVT" : ["mf5064", "mf6245", "mf6132"],
						"wceWait" : ["mf5065", "mf6246", "mf6132"],
						"railIVT" : ["mf5063", "mf6247", "mf6132"],
						"busIVT" : ["mf5062", "mf6249", "mf6132"],
						"auxTransit" : ["mf5067", "mf6252", "mf6132"],
						"boardings" : ["mf5066", "mf6251", "mf6132"],
						"wceFare" : ["mf161", "mf6253", "mf6132"]}

		self.SplitTransitImpedance(eb, imp_dict = wce_imp_am_wk, year = model_year)
#		self.SplitTransitImpedance(eb, imp_dict = wce_imp_md_wk, year = model_year)
		self.SplitTransitImpedance(eb, imp_dict = wce_imp_pm_wk, year = model_year)
		self.SplitTransitImpedance(eb, imp_dict = wce_imp_am_nw, year = model_year)
#		self.SplitTransitImpedance(eb, imp_dict = wce_imp_md_nw, year = model_year)
		self.SplitTransitImpedance(eb, imp_dict = wce_imp_pm_nw, year = model_year)



		#spliting auto matrices work - bus mode
		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		bus_auto_am_wk = {"autotime" : ["mf101", "mf6007", "mf6000"],
						  "autotoll" : ["mf102", "mf6008", "mf6000"],
						  "autodist" : ["mf100", "mf6009", "mf6000"] }

		bus_auto_md_wk = {"autotime" : ["mf104", "mf6052", "mf6000"],
						  "autotoll" : ["mf105", "mf6053", "mf6000"],
						  "autodist" : ["mf103", "mf6054", "mf6000"] }

		bus_auto_pm_wk = {"autotime" : ["mf2101", "mf6092", "mf6000"],
						  "autotoll" : ["mf2102", "mf6093", "mf6000"],
						  "autodist" : ["mf2100", "mf6094", "mf6000"] }



		#spliting auto matrices non work - bus mode
		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		bus_auto_am_nw = {"autotime" : ["mf101", "mf6137", "mf6130"],
						  "autotoll" : ["mf102", "mf6138", "mf6130"],
						  "autodist" : ["mf100", "mf6139", "mf6130"] }

		bus_auto_md_nw = {"autotime" : ["mf104", "mf6177", "mf6130"],
						  "autotoll" : ["mf105", "mf6178", "mf6130"],
						  "autodist" : ["mf103", "mf6179", "mf6130"] }

		bus_auto_pm_nw = {"autotime" : ["mf2101", "mf6217", "mf6130"],
						  "autotoll" : ["mf2102", "mf6218", "mf6130"],
						  "autodist" : ["mf2100", "mf6219", "mf6130"] }


		self.SplitAutoImpedance(eb, imp_dict = bus_auto_am_wk, year = model_year)
		self.SplitAutoImpedance(eb, imp_dict = bus_auto_md_wk, year = model_year)
		self.SplitAutoImpedance(eb, imp_dict = bus_auto_pm_wk, year = model_year)
		self.SplitAutoImpedance(eb, imp_dict = bus_auto_am_nw, year = model_year)
		self.SplitAutoImpedance(eb, imp_dict = bus_auto_md_nw, year = model_year)
		self.SplitAutoImpedance(eb, imp_dict = bus_auto_pm_nw, year = model_year)


		#spliting auto matrices work - bus mode
		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		ral_auto_am_wk = {"autotime" : ["mf101", "mf6017", "mf6001"],
						  "autotoll" : ["mf102", "mf6018", "mf6001"],
						  "autodist" : ["mf100", "mf6019", "mf6001"] }

		ral_auto_md_wk = {"autotime" : ["mf104", "mf6062", "mf6001"],
						  "autotoll" : ["mf105", "mf6063", "mf6001"],
						  "autodist" : ["mf103", "mf6064", "mf6001"] }

		ral_auto_pm_wk = {"autotime" : ["mf2101", "mf6102", "mf6001"],
						  "autotoll" : ["mf2102", "mf6103", "mf6001"],
						  "autodist" : ["mf2100", "mf6104", "mf6001"] }



		#spliting auto matrices non work - bus mode
		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		ral_auto_am_nw = {"autotime" : ["mf101", "mf6147", "mf6131"],
						  "autotoll" : ["mf102", "mf6148", "mf6131"],
						  "autodist" : ["mf100", "mf6149", "mf6131"] }

		ral_auto_md_nw = {"autotime" : ["mf104", "mf6187", "mf6131"],
						  "autotoll" : ["mf105", "mf6188", "mf6131"],
						  "autodist" : ["mf103", "mf6189", "mf6131"] }

		ral_auto_pm_nw = {"autotime" : ["mf2101", "mf6227", "mf6131"],
						  "autotoll" : ["mf2102", "mf6228", "mf6131"],
						  "autodist" : ["mf2100", "mf6229", "mf6131"] }


		self.SplitAutoImpedance(eb, imp_dict = ral_auto_am_wk, year = model_year)
		self.SplitAutoImpedance(eb, imp_dict = ral_auto_md_wk, year = model_year)
		self.SplitAutoImpedance(eb, imp_dict = ral_auto_pm_wk, year = model_year)
		self.SplitAutoImpedance(eb, imp_dict = ral_auto_am_nw, year = model_year)
		self.SplitAutoImpedance(eb, imp_dict = ral_auto_md_nw, year = model_year)
		self.SplitAutoImpedance(eb, imp_dict = ral_auto_pm_nw, year = model_year)


		#spliting auto matrices work - bus mode
		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		wce_auto_am_wk = {"autotime" : ["mf101", "mf6032", "mf6002"],
						  "autotoll" : ["mf102", "mf6033", "mf6002"],
						  "autodist" : ["mf100", "mf6034", "mf6002"] }

#		wce_auto_md_wk = {"autotime" : ["mf104", "mf6077", "mf6002"],
#						  "autotoll" : ["mf105", "mf6078", "mf6002"],
#						  "autodist" : ["mf103", "mf6079", "mf6002"] }

		wce_auto_pm_wk = {"autotime" : ["mf2101", "mf6117", "mf6002"],
						  "autotoll" : ["mf2102", "mf6118", "mf6002"],
						  "autodist" : ["mf2100", "mf6119", "mf6002"] }



		#spliting auto matrices non work - bus mode
		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		wce_auto_am_nw = {"autotime" : ["mf101", "mf6162", "mf6132"],
						  "autotoll" : ["mf102", "mf6163", "mf6132"],
						  "autodist" : ["mf100", "mf6164", "mf6132"] }

#		wce_auto_md_nw = {"autotime" : ["mf104", "mf6202", "mf6132"],
#						  "autotoll" : ["mf105", "mf6203", "mf6132"],
#						  "autodist" : ["mf103", "mf6204", "mf6132"] }

		wce_auto_pm_nw = {"autotime" : ["mf2101", "mf6242", "mf6132"],
						  "autotoll" : ["mf2102", "mf6243", "mf6132"],
						  "autodist" : ["mf2100", "mf6244", "mf6132"] }


		self.SplitAutoImpedance(eb, imp_dict = wce_auto_am_wk, year = model_year)
#		self.SplitAutoImpedance(eb, imp_dict = wce_auto_md_wk, year = model_year)
		self.SplitAutoImpedance(eb, imp_dict = wce_auto_pm_wk, year = model_year)
		self.SplitAutoImpedance(eb, imp_dict = wce_auto_am_nw, year = model_year)
#		self.SplitAutoImpedance(eb, imp_dict = wce_auto_md_nw, year = model_year)
		self.SplitAutoImpedance(eb, imp_dict = wce_auto_pm_nw, year = model_year)



	@_m.logbook_trace("UNDER DEV - PNR Impedance")
	def SplitAutoImpedance(self, eb, imp_dict, year):
		leg_impedances= _m.Modeller().tool(
			"inro.emme.choice_model.pr.best_lot_step.leg_impedances")


		# explictly set lot ensemble - will have different lots in 2011 and future
		# gn1 exist in 2011 and future
		# gn2 exist only in 2011
		# gn3 exist only in future
		if year == 2011:
			#intermediates = 'gn1;gn2', modified intermediates as using the ensembles was giving wrong results
			intermediates = '100,130'			
		else:
			#intermediates = 'gn1;gn3'
			intermediates = '100,130'	
		spec = {
			"impedances": {
				"auto": "AutoIn",
				"transit": None},
			"best_parking_lots": "BestLot",
			"constraint": {
				"by_zone": {
					"origins": "all",
					"intermediates": intermediates,
					"destinations": "all"},
				"by_value": None},
			"results": {
				"auto_leg_impedances": "AutoOut",
				"transit_leg_impedances": None}
			}

		for skim, matrixlist in imp_dict.items():
			#update spec
			spec["impedances"]["auto"] = matrixlist[0]
			spec['results']['auto_leg_impedances'] = matrixlist[1]
			spec["best_parking_lots"] = matrixlist[2]
			# split matrix
			leg_impedances(spec)


	@_m.logbook_trace("UNDER DEV - PNR Impedance")
	def SplitTransitImpedance(self, eb, imp_dict, year):
		leg_impedances= _m.Modeller().tool(
			"inro.emme.choice_model.pr.best_lot_step.leg_impedances")


		# explictly set lot ensemble - will have different lots in 2011 and future
		# gn1 exist in 2011 and future
		# gn2 exist only in 2011
		# gn3 exist only in future
		if year == 2011:
			#intermediates = 'gn1;gn2'
			intermediates = 'gn1;gn2'			
		else:
			#intermediates = 'gn1;gn3'
			intermediates = 'gn1;gn2'				

		spec = {
			"impedances": {
				"auto": None,
				"transit": "TransitIn"},
			"best_parking_lots": "BestLot",
			"constraint": {
				"by_zone": {
					"origins": "all",
					"intermediates": intermediates,
					"destinations": "all"},
				"by_value": None},
			"results": {
				"auto_leg_impedances": None,
				"transit_leg_impedances": "Transit_out"}
			}

		for skim, matrixlist in imp_dict.items():
			#update spec
			spec["impedances"]["transit"] = matrixlist[0]
			spec['results']['transit_leg_impedances'] = matrixlist[1]
			spec["best_parking_lots"] = matrixlist[2]
			# split matrix
			leg_impedances(spec)


	@_m.logbook_trace("UNDER DEV - PNR Impedance")
	def bestlot(self, eb, year):
		compute_lot = _m.Modeller().tool(
			"inro.emme.matrix_calculation.matrix_triple_index_operation")

		# explictly set lot ensemble - will have different lots in 2011 and future
		# gn1 exist in 2011 and future
		# gn2 exist only in 2011
		# gn3 exist only in future


		if year == 2011:
		#	intermediates = 'gn1;gn2'
			intermediates = 'gn1;gn2'		
		else:
		#	intermediates = 'gn1;gn3'
			intermediates = 'gn1;gn3'
		# defining dictionaries to keep matrix references explicit
		# matrices needed for calulcation
		# generalized time for auto and transit legs
		# work uses am for all modes
		# non-work uses md for bus and rail and am for WCE (there is no md WCE)

		legs = {
				"work" : {"auto" : "mf6003",
						 "bus" : "mf6005",
						 "rail" : "mf6015",
						 "wce" : "mf6030"},
				"nonwork" : {"auto" : "mf6173",
							 "bus" : "mf6175",
							 "rail" : "mf6185",
							 "wce" : "mf6030"}
				}

		# generalized time of minimum auto-lot-transit route
		# not used, but required by triple index operation
		min_gt = {
				"work" : {"bus" : "mf6006",
						 "rail" : "mf6016",
						 "wce" : "mf6031"},
				"nonwork" : {"bus" : "mf6176",
							 "rail" : "mf6186",
							 "wce" : "mf6201"}
				}
		# lot choice dictionary
		lot_choice = {
				"work" : {"bus" : "mf6000",
						 "rail" : "mf6001",
						 "wce" : "mf6002"},
				"nonwork" : {"bus" : "mf6130",
							 "rail" : "mf6131",
							 "wce" : "mf6132"}
				}

		spec  = {
			"pk_operand": "AutoLeg",
			"kq_operand": "TransitLeg",
			"qk_operand": None,
			"combination_operator": "+",
			"masks": [],
			"contraction_operator": ".min.",
			"result": 'MinGT',
			"index_result": "BestLot",
			"constraint": {
				"by_zone": {
					"intermediates": intermediates,
					"origins": "all",
					"destinations": "all"
				},
				"by_value": None
			},
			"type": "MATRIX_TRIPLE_INDEX_OPERATION"
		}

		# explictly set lot ensemble - will have different lots in 2011 and future
		# gn1 exist in 2011 and future
		# gn2 exist only in 2011
		# gn3 exist only in future


		# work uses AM
		# note, auto skim is same for all transit modes

		# calculate bus best lot work
		spec["pk_operand"] = legs['work']['auto']
		spec["kq_operand"] = legs['work']['bus']
		spec["result"] = min_gt['work']['bus']
		spec["index_result"] = lot_choice['work']['bus']
		compute_lot(spec)

		# calculate rail best lot work
		spec["kq_operand"] = legs['work']['rail']
		spec["result"] = min_gt['work']['rail']
		spec["index_result"] = lot_choice['work']['rail']
		compute_lot(spec)

		# calculate west coast express best lot work
		spec["kq_operand"] = legs['work']['wce']
		spec["result"] = min_gt['work']['wce']
		spec["index_result"] = lot_choice['work']['wce']
		compute_lot(spec)


		# calculate bus best lot nonwork
		spec["pk_operand"] = legs['nonwork']['auto']
		spec["kq_operand"] = legs['nonwork']['bus']
		spec["result"] = min_gt['nonwork']['bus']
		spec["index_result"] = lot_choice['nonwork']['bus']
		compute_lot(spec)

		# calculate rail best lot nonwork
		spec["kq_operand"] = legs['nonwork']['rail']
		spec["result"] = min_gt['nonwork']['rail']
		spec["index_result"] = lot_choice['nonwork']['rail']
		compute_lot(spec)

		# calculate west coast express best lot nonwork
		# west coast express no midday, uses am and needs AM auto skim brought back
		spec["pk_operand"] = legs['work']['auto']
		spec["kq_operand"] = legs['nonwork']['wce']
		spec["result"] = min_gt['nonwork']['wce']
		spec["index_result"] = lot_choice['nonwork']['wce']
		compute_lot(spec)



	@_m.logbook_trace("UNDER DEV - PNR Impedance")
	def WceGT(self, eb):
		util = _m.Modeller().tool("translink.emme.util")
		# [AM,MD,PM]
		transit_mats = {"wceIVT" : ["mf5052",  "mf5058", "mf5064"],
						"wceWait" : ["mf5053",  "mf5059", "mf5065"],
						"railIVT" : ["mf5051",  "mf5057", "mf5063"],
						"busIVT" : ["mf5050",  "mf5056", "mf5062"],
						"auxTransit" : ["mf5055",  "mf5061", "mf5067"],
						"boardings" : ["mf5054",  "mf5060", "mf5066"],
						"wceFare" : ["mf161",  "mf161", "mf161"]}

		# [Work, non-work]
		vot_mats = ['msvotWkmed', 'msvotNWkmed']

		# [[AMWk, MDWk, PMWk],[AMnonWk, MDnonWk, PMnonWk]]
		result_mats = [["mf6030",  "mf6075", "mf6115"],["mf6160",  "mf6200", "mf6240"]]

		#calculate generalized time for bus leg
		specs = []
		for i in range(0,3):
			for j in range(0,2):
				expression = ("{wceIVT} * {wceIVTprcp}"
							  " + {wceWait} * {wceOVTprcp}"
							  " + {railIVT} * {railIVTprcp}"
							  " + {busIVT} * {busIVTprcp}"
							  " + {auxTrans} * {walkprcp}"
							  " + {boardings} * {transferprcp} "
							  " + {fare} * {VOT}"
							  ).format(wceIVT=transit_mats["wceIVT"][i],
									   wceWait=transit_mats["wceWait"][i],
									   railIVT=transit_mats["railIVT"][i],
									   busIVT=transit_mats["busIVT"][i],
									   auxTrans=transit_mats["auxTransit"][i],
									   boardings=transit_mats["boardings"][i],
									   fare=transit_mats["wceFare"][i],
									   wceIVTprcp="mswceIVTprcp",
									   wceOVTprcp="mswceOVTprcp",
									   railIVTprcp="msrailIVTprcp",
									   busIVTprcp="msbusIVTprcp",
									   walkprcp="mswalkprcp",
									   transferprcp="mswceTRANSprcp",
									   VOT=vot_mats[j])

				result = ("{wceGT}").format(wceGT=result_mats[j][i])
				specs.append(util.matrix_spec(result, expression))
		util.compute_matrix(specs)



	@_m.logbook_trace("UNDER DEV - PNR Impedance")
	def RailGT(self, eb):
		util = _m.Modeller().tool("translink.emme.util")
		# [AM,MD,PM]
		transit_mats = {"railIVT" : ["mf5001",  "mf5006", "mf5011"],
						"railWait" : ["mf5002",  "mf5007", "mf5012"],
						"busIVT" : ["mf5000",  "mf5005", "mf5010"],
						"auxTransit" : ["mf5004", "mf5009", "mf5014"],
						"boardings" : ["mf5003", "mf5008", "mf5013"],
						"railFare" : ["mf161",  "mf161", "mf161"]}

		# [Work, non-work]
		vot_mats = ['msvotWkmed', 'msvotNWkmed']

		# [[AMWk, MDWk, PMWk],[AMnonWk, MDnonWk, PMnonWk]]
		result_mats = [["mf6015", "mf6060", "mf6100"],['mf6145','mf6185','mf6225']]

		#calculate generalized time for bus leg
		specs = []
		for i in range(0,3):
			for j in range(0,2):
				expression = ("{railIVT} * {railIVTprcp}"
							  " + {railWait} * {railOVTprcp}"
							  " + {busIVT} * {busIVTprcp}"
							  " + {auxTrans} * {walkprcp}"
							  " + {boardings} * {transferprcp} "
							  " + {fare} * {VOT}"
							  ).format(railIVT=transit_mats["railIVT"][i],
									   railWait=transit_mats["railWait"][i],
									   busIVT=transit_mats["busIVT"][i],
									   auxTrans=transit_mats["auxTransit"][i],
									   boardings=transit_mats["boardings"][i],
									   fare=transit_mats["railFare"][i],
									   railIVTprcp="msrailIVTprcp",
									   railOVTprcp="msrailOVTprcp",
									   busIVTprcp="msbusIVTprcp",
									   walkprcp="mswalkprcp",
									   transferprcp="msrailTRANSprcp",
									   VOT=vot_mats[j])

				result = ("{railGT}").format(railGT=result_mats[j][i])
				specs.append(util.matrix_spec(result, expression))
		util.compute_matrix(specs)



	@_m.logbook_trace("UNDER DEV - PNR Impedance")
	def BusGT(self, eb):
		util = _m.Modeller().tool("translink.emme.util")
		# [AM,MD,PM]
		transit_mats = {"busIVT" : ["mf107",  "mf112", "mf2107"],
						"busWait" : ["mf106",  "mf111", "mf2106"],
						"auxTransit" : ["mf109", "mf114", "mf2109"],
						"boardings" : ["mf108", "mf113", "mf2108"],
						"busFare" : ["mf160",  "mf160", "mf160"]}

		# [Work, non-work]
		vot_mats = ['msvotWkmed', 'msvotNWkmed']

		# [[AMWk, MDWk, PMWk],[AMnonWk, MDnonWk, PMnonWk]]
		result_mats = [["mf6005", "mf6050", "mf6090"],['mf6135','mf6175','mf6215']]

		#calculate generalized time for bus leg
		specs = []
		for i in range(0,3):
			for j in range(0,2):
				expression = ("{busIVT} * {busIVTprcp}"
							  " + {busWait} * {busOVTprcp}"
							  " + {auxTrans} * {walkprcp}"
							  " + {boardings} * {transferprcp} "
							  " + {fare} * {VOT}"
							  ).format(busIVT=transit_mats["busIVT"][i],
									   busWait=transit_mats["busWait"][i],
									   auxTrans=transit_mats["auxTransit"][i],
									   boardings=transit_mats["boardings"][i],
									   fare=transit_mats["busFare"][i],
									   busIVTprcp="msbusIVTprcp",
									   busOVTprcp="msbusOVTprcp",
									   walkprcp="mswalkprcp",
									   transferprcp="msbusTRANSprcp",
									   VOT=vot_mats[j])

				result = ("{busGT}").format(busGT=result_mats[j][i])
				specs.append(util.matrix_spec(result, expression))
		util.compute_matrix(specs)



	@_m.logbook_trace("UNDER DEV - PNR Impedance")
	def AutoGT(self, eb):
		util = _m.Modeller().tool("translink.emme.util")
		# [AM,MD,PM]
		auto_mats = {"autotime" : ["mf101",  "mf104", "mf2101"],
					"autotoll" : ["mf102", "mf105", "mf2102"],
					"autodist" : ["mf100", "mf103", "mf2100"] }

		# [Work, non-work]
		vot_mats = ['msvotWkmed', 'msvotNWkmed']

		# [[AMWk, MDWk, PMWk],[AMnonWk, MDnonWk, PMnonWk]]
		result_mats = [["mf6003", "mf6048", "mf6088"],['mf6133','mf6173','mf6213']]

		specs = []
		for i in range(0,3):
			for j in range(0,2):
				expression = ("{autotime} + {termtime}"
							  " + (({VOC} * {autodist}) + {autotoll} + {lotcost}) * {VOT}"
							  ).format(autotime=auto_mats["autotime"][i],
									   autotoll=auto_mats["autotoll"][i],
									   autodist=auto_mats["autodist"][i],
									   VOT=vot_mats[j],
									   VOC="msVOC",
									   lotcost = "mdPRcost",
									   termtime = "mdPRtermtime")

				result = ("{autoGT}").format(autoGT=result_mats[j][i])
				specs.append(util.matrix_spec(result, expression))
		util.compute_matrix(specs)



	@_m.logbook_trace("UNDER DEV - PNR Impedance")
	def read_file(self, eb, file):
		util = _m.Modeller().tool("translink.emme.util")
		#Read data from file and check number of lines
		with open(file, "rb") as sourcefile:
			lines = list(csv.reader(sourcefile, skipinitialspace=True))

		#TODO - validate each line has the same number of entries

		matrices = []
		mat_data = []
		# Initialize all matrices with 0-values and store a data reference
		for i in range(1, len(lines[0])):
			mat = util.initmat(eb, lines[0][i], lines[1][i], lines[2][i], 0)
			matrices.append(mat)
			mat_data.append(mat.get_data())

		# loop over each data-containing line in the csv
		for i in range(3, len(lines)):
			line = lines[i]
			# within each line set the data in each matrix
			for j in range(1, len(line)):
				mat_data[j-1].set(int(line[0]), float(line[j]))

		# store the data back into the matrix on disk
		for i in range(len(matrices)):
			matrices[i].set_data(mat_data[i])



	@_m.logbook_trace("UNDER DEV - PNR Impedance")
	def matrix_batchins(self, eb):
		util = _m.Modeller().tool("translink.emme.util")

		#TODO move the VOT to actual file Batchin -
		util.initmat(eb,"ms120","votWklow", "work VOT low income in min/$", 6)
		util.initmat(eb,"ms121","votWkmed", "work VOT med income in min/$", 4)
		util.initmat(eb,"ms122","votWkhigh", "work VOT high income in min/$", 3)
		util.initmat(eb,"ms123","votNWklow", "non-work VOT low income in min/$", 12)
		util.initmat(eb,"ms124","votNWkmed", "non-work VOT med income in min/$", 8)
		util.initmat(eb,"ms125","votNWkhigh", "non-work VOT high income in min/$", 6)

		util.initmat(eb,"ms130", "VOC", "Vehicle Operating Variable Cost (/km)", 0.18) # CAA includes fuel, tires, maintence

		# transit scalars
		#TODO update these factors to actual values
		util.initmat(eb, "ms199", "walkprcp", "walk time perception factor", 1)

		util.initmat(eb, "ms200", "busIVTprcp", "bus IVT perception factor", 1)
		util.initmat(eb, "ms201", "busOVTprcp", "bus OVT perception factor", 1.5)
		util.initmat(eb, "ms202", "busTRANSprcp", "bus transfer perception factor", 5)

		util.initmat(eb, "ms205", "railIVTprcp", "rail IVT perception factor", 1)
		util.initmat(eb, "ms206", "railOVTprcp", "rail OVT perception factor", 1.5)
		util.initmat(eb, "ms207", "railTRANSprcp", "rail transfer perception factor", 5)

		util.initmat(eb, "ms210", "wceIVTprcp", "wce IVT perception factor", 1)
		util.initmat(eb, "ms211", "wceOVTprcp", "wce OVT perception factor", 1.5)
		util.initmat(eb, "ms212", "wceTRANSprcp", "wce transfer perception factor", 5)



		# Lot choice using AM impedances, but lot choice fixed for all time periods
		util.initmat(eb, "mf6000", "buspr-lotChceWkAM", "Bus Best PnR Lot - Bus",0)
		util.initmat(eb, "mf6001", "railpr-lotChceWkAM", "Rail Best PnR Lot - Rail",0)
		util.initmat(eb, "mf6002", "wcepr-lotChceWkAM", "Rail Best PnR Lot -WCE",0)


		# AM Auto generalized Cost same for all modes
		util.initmat(eb, "mf6003", "pr-gtAutoWkAM", "PnR Generalized Cost Auto Leg",0)


		# AM bus impedance matrices
		util.initmat(eb, "mf6005", "buspr-GctranWkAM", "PnR Generalized Cost Transit Leg - Bus",0)
		util.initmat(eb, "mf6006", "buspr-minGCWkAM", "PnR Combined Skim Result - Bus",0)
		util.initmat(eb, "mf6007", "buspr-autimeWkAM", "Auto Time - Bus",0)
		util.initmat(eb, "mf6008", "buspr-autollWkAM", "Auto Toll - Bus",0)
		util.initmat(eb, "mf6009", "buspr-autdistWkAM", "Auto Dist - Bus",0)
		util.initmat(eb, "mf6010", "buspr-busIVTWkAM", "Bus IVTT - Bus",0)
		util.initmat(eb, "mf6011", "buspr-busWtWkAM", "Bus Wait Time - Bus",0)
		util.initmat(eb, "mf6012", "buspr-bordsWkAM", "Boardings - Bus",0)
		util.initmat(eb, "mf6013", "buspr-auxWkAM", "Aux - Bus",0)
		util.initmat(eb, "mf6014", "buspr-fareWkAM", "Fare - Bus",0)

		# AM rail impedance matrices
		util.initmat(eb, "mf6015", "railpr-GctranWkAM", "Rail PnR Generalized Cost Transit Leg - Rail",0)
		util.initmat(eb, "mf6016", "railpr-minGCWkAM", "Rail PnR Combined Skim Result - Rail",0)
		util.initmat(eb, "mf6017", "railpr-autimeWkAM", "Auto Time - Rail",0)
		util.initmat(eb, "mf6018", "railpr-autollWkAM", "Auto Toll - Rail",0)
		util.initmat(eb, "mf6019", "railpr-autdistWkAM", "Auto Dist - Rail",0)
		util.initmat(eb, "mf6020", "railpr-railIVTWkAM", "Rail IVT - Rail",0)
		util.initmat(eb, "mf6021", "railpr-railWtWkAM", "Rail Wait Time - Rail",0)
		util.initmat(eb, "mf6022", "railpr-busIVTWkAM", "Bus IVT - Rail",0)
		util.initmat(eb, "mf6023", "railpr-busWtWkAM", "Bus Wait Time - Rai",0)
		util.initmat(eb, "mf6024", "railpr-bordsWkAM", "Rail Boardings",0)
		util.initmat(eb, "mf6025", "railpr-auxWkAM", "Aux - Rail",0)
		util.initmat(eb, "mf6026", "railpr-fareWkAM", "Fare - Rail",0)

		# AM WCE impedance matrices
		util.initmat(eb, "mf6030", "wcepr-GctranWkAM", "WCE PnR Generalized Cost Transit Leg",0)
		util.initmat(eb, "mf6031", "wcepr-minGCWkAM", "WCE PnR Combined Skim Result",0)
		util.initmat(eb, "mf6032", "wcepr-autimeWkAM", "Auto Time - WCE",0)
		util.initmat(eb, "mf6033", "wcepr-autollWkAM", "Auto Toll - WCE",0)
		util.initmat(eb, "mf6034", "wcepr-autdistWkAM", "Auto Dist - WCE",0)
		util.initmat(eb, "mf6035", "wcepr-wceIVTWkAM", "WCE IVT - WCE",0)
		util.initmat(eb, "mf6036", "wcepr-wceWtWkAM", "WCE Wait Time - WCE",0)
		util.initmat(eb, "mf6037", "wcepr-railIVTWkAM", "Rail IVT - WCE",0)
		util.initmat(eb, "mf6038", "wcepr-railWtWkAM", "Rail Wait Time - WCE",0)
		util.initmat(eb, "mf6039", "wcepr-busIVTWkAM", "Bus IVT - WCE",0)
		util.initmat(eb, "mf6040", "wcepr-busWtWkAM", "Bus Wait Time - WCE",0)
		util.initmat(eb, "mf6041", "wcepr-bordsWkAM", "Boardings - WCE",0)
		util.initmat(eb, "mf6042", "wcepr-auxWkAM", "Aux - WCE",0)
		util.initmat(eb, "mf6043", "wcepr-fareWkAM", "Fare - Wce",0)

		# MD Auto generalized Cost same for all modes
		util.initmat(eb, "mf6048", "pr-gtAutoWkMD", "PnR Generalized Cost Auto Leg",0)


		# MD bus impedance matrices
		util.initmat(eb, "mf6050", "buspr-GctranWkMD", "PnR Generalized Cost Transit Leg - Bus",0)
		util.initmat(eb, "mf6051", "buspr-minGCWkMD", "PnR Combined Skim Result - Bus",0)
		util.initmat(eb, "mf6052", "buspr-autimeWkMD", "Auto Time - Bus",0)
		util.initmat(eb, "mf6053", "buspr-autollWkMD", "Auto Toll - Bus",0)
		util.initmat(eb, "mf6054", "buspr-autdistWkMD", "Auto Dist - Bus",0)
		util.initmat(eb, "mf6055", "buspr-busIVTWkMD", "Bus IVTT - Bus",0)
		util.initmat(eb, "mf6056", "buspr-busWtWkMD", "Bus Wait Time - Bus",0)
		util.initmat(eb, "mf6057", "buspr-bordsWkMD", "Boardings - Bus",0)
		util.initmat(eb, "mf6058", "buspr-auxWkMD", "Aux - Bus",0)
		util.initmat(eb, "mf6059", "buspr-fareWkMD", "Fare - Bus",0)

		# MD rail impedance matrices
		util.initmat(eb, "mf6060", "railpr-GctranWkMD", "Rail PnR Generalized Cost Transit Leg - Rail",0)
		util.initmat(eb, "mf6061", "railpr-minGCWkMD", "Rail PnR Combined Skim Result - Rail",0)
		util.initmat(eb, "mf6062", "railpr-autimeWkMD", "Auto Time - Rail",0)
		util.initmat(eb, "mf6063", "railpr-autollWkMD", "Auto Toll - Rail",0)
		util.initmat(eb, "mf6064", "railpr-autdistWkMD", "Auto Dist - Rail",0)
		util.initmat(eb, "mf6065", "railpr-railIVTWkMD", "Rail IVT - Rail",0)
		util.initmat(eb, "mf6066", "railpr-railWtWkMD", "Rail Wait Time - Rail",0)
		util.initmat(eb, "mf6067", "railpr-busIVTWkMD", "Bus IVT - Rail",0)
		util.initmat(eb, "mf6068", "railpr-busWtWkMD", "Bus Wait Time - Rai",0)
		util.initmat(eb, "mf6069", "railpr-bordsWkMD", "Rail Boardings",0)
		util.initmat(eb, "mf6070", "railpr-auxWkMD", "Aux - Rail",0)
		util.initmat(eb, "mf6071", "railpr-fareWkMD", "Fare - Rail",0)

		# MD WCE impedance matrices
		util.initmat(eb, "mf6075", "wcepr-GctranWkMD", "WCE PnR Generalized Cost Transit Leg",0)
		util.initmat(eb, "mf6076", "wcepr-minGCWkMD", "WCE PnR Combined Skim Result",0)
		util.initmat(eb, "mf6077", "wcepr-autimeWkMD", "Auto Time - WCE",0)
		util.initmat(eb, "mf6078", "wcepr-autollWkMD", "Auto Toll - WCE",0)
		util.initmat(eb, "mf6079", "wcepr-autdistWkMD", "Auto Dist - WCE",0)
		util.initmat(eb, "mf6080", "wcepr-wceIVTWkMD", "WCE IVT - WCE",0)
		util.initmat(eb, "mf6081", "wcepr-wceWtWkMD", "WCE Wait Time - WCE",0)
		util.initmat(eb, "mf6082", "wcepr-railIVTWkMD", "Rail IVT - WCE",0)
		util.initmat(eb, "mf6083", "wcepr-railWtWkMD", "Rail Wait Time - WCE",0)
		util.initmat(eb, "mf6084", "wcepr-busIVTWkMD", "Bus IVT - WCE",0)
		util.initmat(eb, "mf6085", "wcepr-busWtWkMD", "Bus Wait Time - WCE",0)
		util.initmat(eb, "mf6086", "wcepr-bordsWkMD", "Boardings - WCE",0)
		util.initmat(eb, "mf6087", "wcepr-auxWkMD", "Aux - WCE",0)
		util.initmat(eb, "mf6088", "wcepr-fareWkMD", "Fare - WCE",0)

		# PM Auto generalized Cost same for all modes
		util.initmat(eb, "mf6088", "pr-gtAutoWkPM", "PnR Generalized Cost Auto Leg",0)


		# PM bus impedance matrices
		util.initmat(eb, "mf6090", "buspr-GctranWkPM", "PnR Generalized Cost Transit Leg - Bus",0)
		util.initmat(eb, "mf6091", "buspr-minGCWkPM", "PnR Combined Skim Result - Bus",0)
		util.initmat(eb, "mf6092", "buspr-autimeWkPM", "Auto Time - Bus",0)
		util.initmat(eb, "mf6093", "buspr-autollWkPM", "Auto Toll - Bus",0)
		util.initmat(eb, "mf6094", "buspr-autdistWkPM", "Auto Dist - Bus",0)
		util.initmat(eb, "mf6095", "buspr-busIVTWkPM", "Bus IVTT - Bus",0)
		util.initmat(eb, "mf6096", "buspr-busWtWkPM", "Bus Wait Time - Bus",0)
		util.initmat(eb, "mf6097", "buspr-bordsWkPM", "Boardings - Bus",0)
		util.initmat(eb, "mf6098", "buspr-auxWkPM", "Aux - Bus",0)
		util.initmat(eb, "mf6099", "buspr-fareWkPM", "Fare - Bus",0)

		# PM rail impedance matrices
		util.initmat(eb, "mf6100", "railpr-GctranWkPM", "Rail PnR Generalized Cost Transit Leg - Rail",0)
		util.initmat(eb, "mf6101", "railpr-minGCWkPM", "Rail PnR Combined Skim Result - Rail",0)
		util.initmat(eb, "mf6102", "railpr-autimeWkPM", "Auto Time - Rail",0)
		util.initmat(eb, "mf6103", "railpr-autollWkPM", "Auto Toll - Rail",0)
		util.initmat(eb, "mf6104", "railpr-autdistWkPM", "Auto Dist - Rail",0)
		util.initmat(eb, "mf6105", "railpr-railIVTWkPM", "Rail IVT - Rail",0)
		util.initmat(eb, "mf6106", "railpr-railWtWkPM", "Rail Wait Time - Rail",0)
		util.initmat(eb, "mf6107", "railpr-busIVTWkPM", "Bus IVT - Rail",0)
		util.initmat(eb, "mf6108", "railpr-busWtWkPM", "Bus Wait Time - Rai",0)
		util.initmat(eb, "mf6109", "railpr-bordsWkPM", "Rail Boardings",0)
		util.initmat(eb, "mf6110", "railpr-auxWkPM", "Aux - Rail",0)
		util.initmat(eb, "mf6111", "railpr-fareWkPM", "Fare - Rail",0)

		# PM WCE impedance matrices
		util.initmat(eb, "mf6115", "wcepr-GctranWkPM", "WCE PnR Generalized Cost Transit Leg",0)
		util.initmat(eb, "mf6116", "wcepr-minGCWkPM", "WCE PnR Combined Skim Result",0)
		util.initmat(eb, "mf6117", "wcepr-autimeWkPM", "Auto Time - WCE",0)
		util.initmat(eb, "mf6118", "wcepr-autollWkPM", "Auto Toll - WCE",0)
		util.initmat(eb, "mf6119", "wcepr-autdistWkPM", "Auto Dist - WCE",0)
		util.initmat(eb, "mf6120", "wcepr-wceIVTWkPM", "WCE IVT - WCE",0)
		util.initmat(eb, "mf6121", "wcepr-wceWtWkPM", "WCE Wait Time - WCE",0)
		util.initmat(eb, "mf6122", "wcepr-railIVTWkPM", "Rail IVT - WCE",0)
		util.initmat(eb, "mf6123", "wcepr-railWtWkPM", "Rail Wait Time - WCE",0)
		util.initmat(eb, "mf6124", "wcepr-busIVTWkPM", "Bus IVT - WCE",0)
		util.initmat(eb, "mf6125", "wcepr-busWtWkPM", "Bus Wait Time - WCE",0)
		util.initmat(eb, "mf6126", "wcepr-bordsWkPM", "Boardings - WCE",0)
		util.initmat(eb, "mf6127", "wcepr-auxWkPM", "Aux - WCE",0)
		util.initmat(eb, "mf6128", "wcepr-fareWkPM", "Fare - WCE",0)


		# Lot choice using AM impedances, but lot choice fixed for all time periods
		util.initmat(eb, "mf6130", "buspr-lotChceNWkAM", "Bus Best PnR Lot - Bus",0)
		util.initmat(eb, "mf6131", "railpr-lotChceNWkAM", "Rail Best PnR Lot - Rail",0)
		util.initmat(eb, "mf6132", "wcepr-lotChceNWkAM", "Rail Best PnR Lot -WCE",0)


		# AM Auto generalized Cost same for all modes
		util.initmat(eb, "mf6133", "pr-gtAutoNWkAM", "PnR Generalized Cost Auto Leg",0)


		# AM bus impedance matrices
		util.initmat(eb, "mf6135", "buspr-GctranNWkAM", "PnR Generalized Cost Transit Leg - Bus",0)
		util.initmat(eb, "mf6136", "buspr-minGCNWkAM", "PnR Combined Skim Result - Bus",0)
		util.initmat(eb, "mf6137", "buspr-autimeNWkAM", "Auto Time - Bus",0)
		util.initmat(eb, "mf6138", "buspr-autollNWkAM", "Auto Toll - Bus",0)
		util.initmat(eb, "mf6139", "buspr-autdistNWkAM", "Auto Dist - Bus",0)
		util.initmat(eb, "mf6140", "buspr-busIVTNWkAM", "Bus IVTT - Bus",0)
		util.initmat(eb, "mf6141", "buspr-busWtNWkAM", "Bus Wait Time - Bus",0)
		util.initmat(eb, "mf6142", "buspr-bordsNWkAM", "Boardings - Bus",0)
		util.initmat(eb, "mf6143", "buspr-auxNWkAM", "Aux - Bus",0)
		util.initmat(eb, "mf6144", "buspr-fareNWkAM", "Fare - Bus",0)

		# AM rail impedance matrices
		util.initmat(eb, "mf6145", "railpr-GctranNWkAM", "Rail PnR Generalized Cost Transit Leg - Rail",0)
		util.initmat(eb, "mf6146", "railpr-minGCNWkAM", "Rail PnR Combined Skim Result - Rail",0)
		util.initmat(eb, "mf6147", "railpr-autimeNWkAM", "Auto Time - Rail",0)
		util.initmat(eb, "mf6148", "railpr-autollNWkAM", "Auto Toll - Rail",0)
		util.initmat(eb, "mf6149", "railpr-autdistNWkAM", "Auto Dist - Rail",0)
		util.initmat(eb, "mf6150", "railpr-railIVTNWkAM", "Rail IVT - Rail",0)
		util.initmat(eb, "mf6151", "railpr-railWtNWkAM", "Rail Wait Time - Rail",0)
		util.initmat(eb, "mf6152", "railpr-busIVTNWkAM", "Bus IVT - Rail",0)
		util.initmat(eb, "mf6153", "railpr-busWtNWkAM", "Bus Wait Time - Rai",0)
		util.initmat(eb, "mf6154", "railpr-bordsNWkAM", "Rail Boardings",0)
		util.initmat(eb, "mf6155", "railpr-auxNWkAM", "Aux - Rail",0)
		util.initmat(eb, "mf6156", "railpr-fareNWkAM", "Fare - Rail",0)

		# AM WCE impedance matrices
		util.initmat(eb, "mf6160", "wcepr-GctranNWkAM", "WCE PnR Generalized Cost Transit Leg",0)
		util.initmat(eb, "mf6161", "wcepr-minGCNWkAM", "WCE PnR Combined Skim Result",0)
		util.initmat(eb, "mf6162", "wcepr-autimeNWkAM", "Auto Time - WCE",0)
		util.initmat(eb, "mf6163", "wcepr-autollNWkAM", "Auto Toll - WCE",0)
		util.initmat(eb, "mf6164", "wcepr-autdistNWkAM", "Auto Dist - WCE",0)
		util.initmat(eb, "mf6165", "wcepr-wceIVTNWkAM", "WCE IVT - WCE",0)
		util.initmat(eb, "mf6166", "wcepr-wceWtNWkAM", "WCE Wait Time - WCE",0)
		util.initmat(eb, "mf6167", "wcepr-railIVTNWkAM", "Rail IVT - WCE",0)
		util.initmat(eb, "mf6168", "wcepr-railWtNWkAM", "Rail Wait Time - WCE",0)
		util.initmat(eb, "mf6169", "wcepr-busIVTNWkAM", "Bus IVT - WCE",0)
		util.initmat(eb, "mf6170", "wcepr-busWtNWkAM", "Bus Wait Time - WCE",0)
		util.initmat(eb, "mf6171", "wcepr-bordsNWkAM", "Boardings - WCE",0)
		util.initmat(eb, "mf6172", "wcepr-auxNWkAM", "Aux - WCE",0)
		util.initmat(eb, "mf6173", "wcepr-fareNWkAM", "Fare - WCE",0)

		# MD Auto generalized Cost same for all modes
		util.initmat(eb, "mf6173", "pr-gtAutoNWkMD", "PnR Generalized Cost Auto Leg",0)


		# MD bus impedance matrices
		util.initmat(eb, "mf6175", "buspr-GctranNWkMD", "PnR Generalized Cost Transit Leg - Bus",0)
		util.initmat(eb, "mf6176", "buspr-minGCNWkMD", "PnR Combined Skim Result - Bus",0)
		util.initmat(eb, "mf6177", "buspr-autimeNWkMD", "Auto Time - Bus",0)
		util.initmat(eb, "mf6178", "buspr-autollNWkMD", "Auto Toll - Bus",0)
		util.initmat(eb, "mf6179", "buspr-autdistNWkMD", "Auto Dist - Bus",0)
		util.initmat(eb, "mf6180", "buspr-busIVTNWkMD", "Bus IVTT - Bus",0)
		util.initmat(eb, "mf6181", "buspr-busWtNWkMD", "Bus Wait Time - Bus",0)
		util.initmat(eb, "mf6182", "buspr-bordsNWkMD", "Boardings - Bus",0)
		util.initmat(eb, "mf6183", "buspr-auxNWkMD", "Aux - Bus",0)
		util.initmat(eb, "mf6184", "buspr-fareNWkMD", "Fare - Bus",0)

		# MD rail impedance matrices
		util.initmat(eb, "mf6185", "railpr-GctranNWkMD", "Rail PnR Generalized Cost Transit Leg - Rail",0)
		util.initmat(eb, "mf6186", "railpr-minGCNWkMD", "Rail PnR Combined Skim Result - Rail",0)
		util.initmat(eb, "mf6187", "railpr-autimeNWkMD", "Auto Time - Rail",0)
		util.initmat(eb, "mf6188", "railpr-autollNWkMD", "Auto Toll - Rail",0)
		util.initmat(eb, "mf6189", "railpr-autdistNWkMD", "Auto Dist - Rail",0)
		util.initmat(eb, "mf6190", "railpr-railIVTNWkMD", "Rail IVT - Rail",0)
		util.initmat(eb, "mf6191", "railpr-railWtNWkMD", "Rail Wait Time - Rail",0)
		util.initmat(eb, "mf6192", "railpr-busIVTNWkMD", "Bus IVT - Rail",0)
		util.initmat(eb, "mf6193", "railpr-busWtNWkMD", "Bus Wait Time - Rai",0)
		util.initmat(eb, "mf6194", "railpr-bordsNWkMD", "Rail Boardings",0)
		util.initmat(eb, "mf6195", "railpr-auxNWkMD", "Aux - Rail",0)
		util.initmat(eb, "mf6196", "railpr-fareNWkMD", "Fare - Rail",0)

		# MD WCE impedance matrices
		util.initmat(eb, "mf6200", "wcepr-GctranNWkMD", "WCE PnR Generalized Cost Transit Leg",0)
		util.initmat(eb, "mf6201", "wcepr-minGCNWkMD", "WCE PnR Combined Skim Result",0)
		util.initmat(eb, "mf6202", "wcepr-autimeNWkMD", "Auto Time - WCE",0)
		util.initmat(eb, "mf6203", "wcepr-autollNWkMD", "Auto Toll - WCE",0)
		util.initmat(eb, "mf6204", "wcepr-autdistNWkMD", "Auto Dist - WCE",0)
		util.initmat(eb, "mf6205", "wcepr-wceIVTNWkMD", "WCE IVT - WCE",0)
		util.initmat(eb, "mf6206", "wcepr-wceWtNWkMD", "WCE Wait Time - WCE",0)
		util.initmat(eb, "mf6207", "wcepr-railIVTNWkMD", "Rail IVT - WCE",0)
		util.initmat(eb, "mf6208", "wcepr-railWtNWkMD", "Rail Wait Time - WCE",0)
		util.initmat(eb, "mf6209", "wcepr-busIVTNWkMD", "Bus IVT - WCE",0)
		util.initmat(eb, "mf6210", "wcepr-busWtNWkMD", "Bus Wait Time - WCE",0)
		util.initmat(eb, "mf6211", "wcepr-bordsNWkMD", "Boardings - WCE",0)
		util.initmat(eb, "mf6212", "wcepr-auxNWkMD", "Aux - WCE",0)
		util.initmat(eb, "mf6213", "wcepr-fareNWkMD", "Fare - WCE",0)

		# PM Auto generalized Cost same for all modes
		util.initmat(eb, "mf6213", "pr-gtAutoNWkPM", "PnR Generalized Cost Auto Leg",0)


		# PM bus impedance matrices
		util.initmat(eb, "mf6215", "buspr-GctranNWkPM", "PnR Generalized Cost Transit Leg - Bus",0)
		util.initmat(eb, "mf6216", "buspr-minGCNWkPM", "PnR Combined Skim Result - Bus",0)
		util.initmat(eb, "mf6217", "buspr-autimeNWkPM", "Auto Time - Bus",0)
		util.initmat(eb, "mf6218", "buspr-autollNWkPM", "Auto Toll - Bus",0)
		util.initmat(eb, "mf6219", "buspr-autdistNWkPM", "Auto Dist - Bus",0)
		util.initmat(eb, "mf6220", "buspr-busIVTNWkPM", "Bus IVTT - Bus",0)
		util.initmat(eb, "mf6221", "buspr-busWtNWkPM", "Bus Wait Time - Bus",0)
		util.initmat(eb, "mf6222", "buspr-bordsNWkPM", "Boardings - Bus",0)
		util.initmat(eb, "mf6223", "buspr-auxNWkPM", "Aux - Bus",0)
		util.initmat(eb, "mf6224", "buspr-fareNWkPM", "Fare - Bus",0)

		# PM rail impedance matrices
		util.initmat(eb, "mf6225", "railpr-GctranNWkPM", "Rail PnR Generalized Cost Transit Leg - Rail",0)
		util.initmat(eb, "mf6226", "railpr-minGCNWkPM", "Rail PnR Combined Skim Result - Rail",0)
		util.initmat(eb, "mf6227", "railpr-autimeNWkPM", "Auto Time - Rail",0)
		util.initmat(eb, "mf6228", "railpr-autollNWkPM", "Auto Toll - Rail",0)
		util.initmat(eb, "mf6229", "railpr-autdistNWkPM", "Auto Dist - Rail",0)
		util.initmat(eb, "mf6230", "railpr-railIVTNWkPM", "Rail IVT - Rail",0)
		util.initmat(eb, "mf6231", "railpr-railWtNWkPM", "Rail Wait Time - Rail",0)
		util.initmat(eb, "mf6232", "railpr-busIVTNWkPM", "Bus IVT - Rail",0)
		util.initmat(eb, "mf6233", "railpr-busWtNWkPM", "Bus Wait Time - Rai",0)
		util.initmat(eb, "mf6234", "railpr-bordsNWkPM", "Rail Boardings",0)
		util.initmat(eb, "mf6235", "railpr-auxNWkPM", "Aux - Rail",0)
		util.initmat(eb, "mf6236", "railpr-fareNWkPM", "Fare - Rail",0)

		# PM WCE impedance matrices
		util.initmat(eb, "mf6240", "wcepr-GctranNWkPM", "WCE PnR Generalized Cost Transit Leg",0)
		util.initmat(eb, "mf6241", "wcepr-minGCNWkPM", "WCE PnR Combined Skim Result",0)
		util.initmat(eb, "mf6242", "wcepr-autimeNWkPM", "Auto Time - WCE",0)
		util.initmat(eb, "mf6243", "wcepr-autollNWkPM", "Auto Toll - WCE",0)
		util.initmat(eb, "mf6244", "wcepr-autdistNWkPM", "Auto Dist - WCE",0)
		util.initmat(eb, "mf6245", "wcepr-wceIVTNWkPM", "WCE IVT - WCE",0)
		util.initmat(eb, "mf6246", "wcepr-wceWtNWkPM", "WCE Wait Time - WCE",0)
		util.initmat(eb, "mf6247", "wcepr-railIVTNWkPM", "Rail IVT - WCE",0)
		util.initmat(eb, "mf6248", "wcepr-railWtNWkPM", "Rail Wait Time - WCE",0)
		util.initmat(eb, "mf6249", "wcepr-busIVTNWkPM", "Bus IVT - WCE",0)
		util.initmat(eb, "mf6250", "wcepr-busWtNWkPM", "Bus Wait Time - WCE",0)
		util.initmat(eb, "mf6251", "wcepr-bordsNWkPM", "Boardings - WCE",0)
		util.initmat(eb, "mf6252", "wcepr-auxNWkPM", "Aux - WCE",0)
		util.initmat(eb, "mf6253", "wcepr-fareNWkPM", "Fare - WCE",0)
