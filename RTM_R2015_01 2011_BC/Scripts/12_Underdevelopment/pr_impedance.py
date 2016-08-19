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



	@_m.logbook_trace("Park and Ride Impedance Calculation")
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

		# transpose best lot matrices for use with the AP direction leg splitting
		specs = []
		# work purposes
		specs.append(util.matrix_spec("mf6300", "1.0 * mf6000'"))
		specs.append(util.matrix_spec("mf6301", "1.0 * mf6001'"))
		specs.append(util.matrix_spec("mf6302", "1.0 * mf6002'"))
		#non-work purposes
		specs.append(util.matrix_spec("mf6430", "1.0 * mf6130'"))
		specs.append(util.matrix_spec("mf6431", "1.0 * mf6131'"))
		specs.append(util.matrix_spec("mf6432", "1.0 * mf6132'"))
		util.compute_matrix(specs)


		########################################################################
		# PA Direction Impedance Splitting
		########################################################################

		# BUS WORK PA
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


		# Bus nonWork PA
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

		self.SplitSecondLegImpedance(eb, imp_dict = ral_imp_am_wk, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = ral_imp_md_wk, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = ral_imp_pm_wk, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = ral_imp_am_nw, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = ral_imp_md_nw, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = ral_imp_pm_nw, year = model_year)


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



		self.SplitSecondLegImpedance(eb, imp_dict = rail_imp_am_wk, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = rail_imp_md_wk, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = rail_imp_pm_wk, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = rail_imp_am_nw, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = rail_imp_md_nw, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = rail_imp_pm_nw, year = model_year)


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
		wce_imp_pm_nw = {"wceIVT" : ["mf5064", "mf6245", "mf6132"],
						"wceWait" : ["mf5065", "mf6246", "mf6132"],
						"railIVT" : ["mf5063", "mf6247", "mf6132"],
						"busIVT" : ["mf5062", "mf6249", "mf6132"],
						"auxTransit" : ["mf5067", "mf6252", "mf6132"],
						"boardings" : ["mf5066", "mf6251", "mf6132"],
						"wceFare" : ["mf161", "mf6253", "mf6132"]}

		self.SplitSecondLegImpedance(eb, imp_dict = wce_imp_am_wk, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = wce_imp_pm_wk, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = wce_imp_am_nw, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = wce_imp_pm_nw, year = model_year)



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


		self.SplitFirstLegImpedance(eb, imp_dict = bus_auto_am_wk, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = bus_auto_md_wk, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = bus_auto_pm_wk, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = bus_auto_am_nw, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = bus_auto_md_nw, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = bus_auto_pm_nw, year = model_year)


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


		self.SplitFirstLegImpedance(eb, imp_dict = ral_auto_am_wk, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = ral_auto_md_wk, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = ral_auto_pm_wk, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = ral_auto_am_nw, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = ral_auto_md_nw, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = ral_auto_pm_nw, year = model_year)


		#spliting auto matrices work - bus mode
		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		wce_auto_am_wk = {"autotime" : ["mf101", "mf6032", "mf6002"],
						  "autotoll" : ["mf102", "mf6033", "mf6002"],
						  "autodist" : ["mf100", "mf6034", "mf6002"] }


		wce_auto_pm_wk = {"autotime" : ["mf2101", "mf6117", "mf6002"],
						  "autotoll" : ["mf2102", "mf6118", "mf6002"],
						  "autodist" : ["mf2100", "mf6119", "mf6002"] }



		#spliting auto matrices non work - bus mode
		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		wce_auto_am_nw = {"autotime" : ["mf101", "mf6162", "mf6132"],
						  "autotoll" : ["mf102", "mf6163", "mf6132"],
						  "autodist" : ["mf100", "mf6164", "mf6132"] }

		wce_auto_pm_nw = {"autotime" : ["mf2101", "mf6242", "mf6132"],
						  "autotoll" : ["mf2102", "mf6243", "mf6132"],
						  "autodist" : ["mf2100", "mf6244", "mf6132"] }


		self.SplitFirstLegImpedance(eb, imp_dict = wce_auto_am_wk, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = wce_auto_pm_wk, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = wce_auto_am_nw, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = wce_auto_pm_nw, year = model_year)


		########################################################################
		# AP Direction Impedance Splitting
		########################################################################

        # BUS WORK AP
        # in the form {skim : [actual skim, output pnr leg skim, best lot]}
		ral_imp_am_wk  =  {"busIVT" : ["mf107", "mf6310", "mf6300"],
		           "busWait" : ["mf106", "mf6311", "mf6300"],
		           "auxTransit" : ["mf109", "mf6313", "mf6300"],
		           "boardings" : ["mf108", "mf6312", "mf6300"],
		           "busFare" : ["mf160", "mf6314", "mf6300"]}

		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		ral_imp_md_wk  =  {"busIVT" : ["mf112", "mf6355", "mf6300"],
		           "busWait" : ["mf111", "mf6356", "mf6300"],
		           "auxTransit" : ["mf114", "mf6358", "mf6300"],
		           "boardings" : ["mf113", "mf6357", "mf6300"],
		           "busFare" : ["mf160", "mf6359", "mf6300"]}

		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		ral_imp_pm_wk  =  {"busIVT" : ["mf2107", "mf6395", "mf6300"],
		           "busWait" : ["mf2106", "mf6396", "mf6300"],
		           "auxTransit" : ["mf2109", "mf6398", "mf6300"],
		           "boardings" : ["mf2108", "mf6397", "mf6300"],
		           "busFare" : ["mf160", "mf6399", "mf6300"]}


		# Bus nonWork AP
		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		ral_imp_am_nw  =  {"busIVT" : ["mf107", "mf6440", "mf6430"],
		           "busWait" : ["mf106", "mf6441", "mf6430"],
		           "auxTransit" : ["mf109", "mf6443", "mf6430"],
		           "boardings" : ["mf108", "mf6442", "mf6430"],
		           "busFare" : ["mf160", "mf6444", "mf6430"]}

		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		ral_imp_md_nw  =  {"busIVT" : ["mf112", "mf6480", "mf6430"],
		           "busWait" : ["mf111", "mf6481", "mf6430"],
		           "auxTransit" : ["mf114", "mf6483", "mf6430"],
		           "boardings" : ["mf113", "mf6482", "mf6430"],
		           "busFare" : ["mf160", "mf6484", "mf6430"]}

		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		ral_imp_pm_nw  =  {"busIVT" : ["mf2107", "mf6520", "mf6430"],
		           "busWait" : ["mf2106", "mf6521", "mf6430"],
		           "auxTransit" : ["mf2109", "mf6523", "mf6430"],
		           "boardings" : ["mf2108", "mf6522", "mf6430"],
		           "busFare" : ["mf160", "mf6524", "mf6430"]}

		self.SplitFirstLegImpedance(eb, imp_dict = ral_imp_am_wk, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = ral_imp_md_wk, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = ral_imp_pm_wk, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = ral_imp_am_nw, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = ral_imp_md_nw, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = ral_imp_pm_nw, year = model_year)



		# Rail impedances to Split
		# work purposes AP
		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		rail_imp_am_wk = {"railIVT" : ["mf5001", "mf6320", "mf6301"],
						  "railWait" : ["mf5002", "mf6321", "mf6301"],
						  "busIVT" : ["mf5000", "mf6322", "mf6301"],
						  "auxTransit" : ["mf5004", "mf6325", "mf6301"],
						  "boardings" : ["mf5003", "mf6324", "mf6301"],
						  "railFare" : ["mf161", "mf6326", "mf6301"]}

		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		rail_imp_md_wk = {"railIVT" : ["mf5006", "mf6365", "mf6301"],
						  "railWait" : ["mf5007", "mf6366", "mf6301"],
						  "busIVT" : ["mf5005", "mf6367", "mf6301"],
						  "auxTransit" : ["mf5009", "mf6370", "mf6301"],
						  "boardings" : ["mf5008", "mf6369", "mf6301"],
						  "railFare" : ["mf161", "mf6371", "mf6301"]}

		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		rail_imp_pm_wk = {"railIVT" : ["mf5011", "mf6405", "mf6301"],
						  "railWait" : ["mf5012", "mf6406", "mf6301"],
						  "busIVT" : ["mf5010", "mf6407", "mf6301"],
						  "auxTransit" : ["mf5014", "mf6410", "mf6301"],
						  "boardings" : ["mf5013", "mf6409", "mf6301"],
						  "railFare" : ["mf161", "mf6411", "mf6301"]}

		# work purposes
		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		rail_imp_am_nw = {"railIVT" : ["mf5001", "mf6450", "mf6431"],
						  "railWait" : ["mf5002", "mf6451", "mf6431"],
						  "busIVT" : ["mf5000", "mf6452", "mf6431"],
						  "auxTransit" : ["mf5004", "mf6455", "mf6431"],
						  "boardings" : ["mf5003", "mf6454", "mf6431"],
						  "railFare" : ["mf161", "mf6456", "mf6431"]}

		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		rail_imp_md_nw = {"railIVT" : ["mf5006", "mf6490", "mf6431"],
						  "railWait" : ["mf5007", "mf6491", "mf6431"],
						  "busIVT" : ["mf5005", "mf6492", "mf6431"],
						  "auxTransit" : ["mf5009", "mf6495", "mf6431"],
						  "boardings" : ["mf5008", "mf6494", "mf6431"],
						  "railFare" : ["mf161", "mf6496", "mf6431"]}

		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		rail_imp_pm_nw = {"railIVT" : ["mf5011", "mf6530", "mf6431"],
						  "railWait" : ["mf5012", "mf6531", "mf6431"],
						  "busIVT" : ["mf5010", "mf6532", "mf6431"],
						  "auxTransit" : ["mf5013", "mf6535", "mf6431"],
						  "boardings" : ["mf5014", "mf6534", "mf6431"],
						  "railFare" : ["mf161", "mf6536", "mf6431"]}



		self.SplitFirstLegImpedance(eb, imp_dict = rail_imp_am_wk, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = rail_imp_md_wk, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = rail_imp_pm_wk, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = rail_imp_am_nw, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = rail_imp_md_nw, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = rail_imp_pm_nw, year = model_year)


		# West Coast Express impedances to split AP direction
		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		wce_imp_am_wk = {"wceIVT" : ["mf5052", "mf6335", "mf6302"],
						"wceWait" : ["mf5053", "mf6336", "mf6302"],
						"railIVT" : ["mf5051", "mf6337", "mf6302"],
						"busIVT" : ["mf5050", "mf6339", "mf6302"],
						"auxTransit" : ["mf5055", "mf6342", "mf6302"],
						"boardings" : ["mf5054", "mf6341", "mf6302"],
						"wceFare" : ["mf161", "mf6343", "mf6302"]}


		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		wce_imp_pm_wk = {"wceIVT" : ["mf5064", "mf6420", "mf6302"],
						"wceWait" : ["mf5065", "mf6421", "mf6302"],
						"railIVT" : ["mf5063", "mf6422", "mf6302"],
						"busIVT" : ["mf5062", "mf6424", "mf6302"],
						"auxTransit" : ["mf5067", "mf6427", "mf6302"],
						"boardings" : ["mf5066", "mf6426", "mf6302"],
						"wceFare" : ["mf161", "mf6428", "mf6302"]}


		# nonwork
		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		wce_imp_am_nw = {"wceIVT" : ["mf5052", "mf6465", "mf6432"],
						"wceWait" : ["mf5053", "mf6466", "mf6432"],
						"railIVT" : ["mf5051", "mf6467", "mf6432"],
						"busIVT" : ["mf5050", "mf6469", "mf6432"],
						"auxTransit" : ["mf5055", "mf6472", "mf6432"],
						"boardings" : ["mf5054", "mf6471", "mf6432"],
						"wceFare" : ["mf161", "mf6473", "mf6432"]}


		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		wce_imp_pm_nw = {"wceIVT" : ["mf5064", "mf6545", "mf6432"],
						"wceWait" : ["mf5065", "mf6546", "mf6432"],
						"railIVT" : ["mf5063", "mf6547", "mf6432"],
						"busIVT" : ["mf5062", "mf6549", "mf6432"],
						"auxTransit" : ["mf5067", "mf6552", "mf6432"],
						"boardings" : ["mf5066", "mf6551", "mf6432"],
						"wceFare" : ["mf161", "mf6553", "mf6432"]}

		self.SplitFirstLegImpedance(eb, imp_dict = wce_imp_am_wk, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = wce_imp_pm_wk, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = wce_imp_am_nw, year = model_year)
		self.SplitFirstLegImpedance(eb, imp_dict = wce_imp_pm_nw, year = model_year)



		#spliting auto matrices work - bus mode AP direction
		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		bus_auto_am_wk = {"autotime" : ["mf101", "mf6307", "mf6300"],
						  "autotoll" : ["mf102", "mf6308", "mf6300"],
						  "autodist" : ["mf100", "mf6309", "mf6300"] }

		bus_auto_md_wk = {"autotime" : ["mf104", "mf6352", "mf6300"],
						  "autotoll" : ["mf105", "mf6353", "mf6300"],
						  "autodist" : ["mf103", "mf6354", "mf6300"] }

		bus_auto_pm_wk = {"autotime" : ["mf2101", "mf6392", "mf6300"],
						  "autotoll" : ["mf2102", "mf6393", "mf6300"],
						  "autodist" : ["mf2100", "mf6394", "mf6300"] }



		#spliting auto matrices non work - bus mode AP direction
		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		bus_auto_am_nw = {"autotime" : ["mf101", "mf6437", "mf6430"],
						  "autotoll" : ["mf102", "mf6438", "mf6430"],
						  "autodist" : ["mf100", "mf6439", "mf6430"] }

		bus_auto_md_nw = {"autotime" : ["mf104", "mf6477", "mf6430"],
						  "autotoll" : ["mf105", "mf6478", "mf6430"],
						  "autodist" : ["mf103", "mf6479", "mf6430"] }

		bus_auto_pm_nw = {"autotime" : ["mf2101", "mf6517", "mf6430"],
						  "autotoll" : ["mf2102", "mf6518", "mf6430"],
						  "autodist" : ["mf2100", "mf6519", "mf6430"] }


		self.SplitSecondLegImpedance(eb, imp_dict = bus_auto_am_wk, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = bus_auto_md_wk, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = bus_auto_pm_wk, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = bus_auto_am_nw, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = bus_auto_md_nw, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = bus_auto_pm_nw, year = model_year)


		#spliting auto matrices work - rail mode AP direction
		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		ral_auto_am_wk = {"autotime" : ["mf101", "mf6317", "mf6301"],
						  "autotoll" : ["mf102", "mf6318", "mf6301"],
						  "autodist" : ["mf100", "mf6319", "mf6301"] }

		ral_auto_md_wk = {"autotime" : ["mf104", "mf6362", "mf6301"],
						  "autotoll" : ["mf105", "mf6363", "mf6301"],
						  "autodist" : ["mf103", "mf6364", "mf6301"] }

		ral_auto_pm_wk = {"autotime" : ["mf2101", "mf6402", "mf6301"],
						  "autotoll" : ["mf2102", "mf6403", "mf6301"],
						  "autodist" : ["mf2100", "mf6404", "mf6301"] }



		#spliting auto matrices non work - rail mode AP direction
		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		ral_auto_am_nw = {"autotime" : ["mf101", "mf6447", "mf6431"],
						  "autotoll" : ["mf102", "mf6448", "mf6431"],
						  "autodist" : ["mf100", "mf6449", "mf6431"] }

		ral_auto_md_nw = {"autotime" : ["mf104", "mf6487", "mf6431"],
						  "autotoll" : ["mf105", "mf6488", "mf6431"],
						  "autodist" : ["mf103", "mf6489", "mf6431"] }

		ral_auto_pm_nw = {"autotime" : ["mf2101", "mf6527", "mf6431"],
						  "autotoll" : ["mf2102", "mf6528", "mf6431"],
						  "autodist" : ["mf2100", "mf6529", "mf6431"] }


		self.SplitSecondLegImpedance(eb, imp_dict = ral_auto_am_wk, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = ral_auto_md_wk, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = ral_auto_pm_wk, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = ral_auto_am_nw, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = ral_auto_md_nw, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = ral_auto_pm_nw, year = model_year)


		#spliting auto matrices work - WCE mode AP direction
		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		wce_auto_am_wk = {"autotime" : ["mf101", "mf6332", "mf6302"],
						  "autotoll" : ["mf102", "mf6333", "mf6302"],
						  "autodist" : ["mf100", "mf6334", "mf6302"] }

		wce_auto_pm_wk = {"autotime" : ["mf2101", "mf6417", "mf6302"],
						  "autotoll" : ["mf2102", "mf6418", "mf6302"],
						  "autodist" : ["mf2100", "mf6419", "mf6302"] }



		#spliting auto matrices non work - wce mode AP direction
		# in the form {skim : [actual skim, output pnr leg skim, best lot]}
		wce_auto_am_nw = {"autotime" : ["mf101", "mf6462", "mf6432"],
						  "autotoll" : ["mf102", "mf6463", "mf6432"],
						  "autodist" : ["mf100", "mf6464", "mf6432"] }



		wce_auto_pm_nw = {"autotime" : ["mf2101", "mf6542", "mf6432"],
						  "autotoll" : ["mf2102", "mf6543", "mf6432"],
						  "autodist" : ["mf2100", "mf6544", "mf6432"] }


		self.SplitSecondLegImpedance(eb, imp_dict = wce_auto_am_wk, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = wce_auto_pm_wk, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = wce_auto_am_nw, year = model_year)
		self.SplitSecondLegImpedance(eb, imp_dict = wce_auto_pm_nw, year = model_year)



	@_m.logbook_trace("Park and Ride - Split First Leg Impedance")
	def SplitFirstLegImpedance(self, eb, imp_dict, year):
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


	@_m.logbook_trace("Park and Ride - Split Second Leg Impedance")
	def SplitSecondLegImpedance(self, eb, imp_dict, year):
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


	@_m.logbook_trace("Park & Ride - Choose Best Lot")
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



	@_m.logbook_trace("Park and Ride Calculate West Coast Express Generalized Time")
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



	@_m.logbook_trace("Park & Ride Calculate Rail Generatized Time")
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



	@_m.logbook_trace("Park & Ride Calculate Bus Generalized Time")
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



	@_m.logbook_trace("Park & Ride Calculate Auto Generalized Time")
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



	@_m.logbook_trace("Park & Ride - Read Input Files")
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



	@_m.logbook_trace("Park & Ride Matrix Batchins")
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
		util.initmat(eb, "mf6000", "buspr-lotChceWkAMPA", "Bus Best PnR Lot - Bus",0)
		util.initmat(eb, "mf6001", "railpr-lotChceWkAMPA", "Rail Best PnR Lot - Rail",0)
		util.initmat(eb, "mf6002", "wcepr-lotChceWkAMPA", "Rail Best PnR Lot -WCE",0)


		# AM Auto generalized Cost same for all modes
		util.initmat(eb, "mf6003", "pr-gtAutoWkAMPA", "PnR Generalized Cost Auto Leg",0)


		# AM bus impedance matrices
		util.initmat(eb, "mf6005", "buspr-GctranWkAMPA", "PnR Generalized Cost Transit Leg - Bus",0)
		util.initmat(eb, "mf6006", "buspr-minGCWkAMPA", "PnR Combined Skim Result - Bus",0)
		util.initmat(eb, "mf6007", "buspr-autimeWkAMPA", "Auto Time - Bus",0)
		util.initmat(eb, "mf6008", "buspr-autollWkAMPA", "Auto Toll - Bus",0)
		util.initmat(eb, "mf6009", "buspr-autdistWkAMPA", "Auto Dist - Bus",0)
		util.initmat(eb, "mf6010", "buspr-busIVTWkAMPA", "Bus IVTT - Bus",0)
		util.initmat(eb, "mf6011", "buspr-busWtWkAMPA", "Bus Wait Time - Bus",0)
		util.initmat(eb, "mf6012", "buspr-bordsWkAMPA", "Boardings - Bus",0)
		util.initmat(eb, "mf6013", "buspr-auxWkAMPA", "Aux - Bus",0)
		util.initmat(eb, "mf6014", "buspr-fareWkAMPA", "Fare - Bus",0)

		# AM rail impedance matrices
		util.initmat(eb, "mf6015", "railpr-GctranWkAMPA", "Rail PnR Generalized Cost Transit Leg - Rail",0)
		util.initmat(eb, "mf6016", "railpr-minGCWkAMPA", "Rail PnR Combined Skim Result - Rail",0)
		util.initmat(eb, "mf6017", "railpr-autimeWkAMPA", "Auto Time - Rail",0)
		util.initmat(eb, "mf6018", "railpr-autollWkAMPA", "Auto Toll - Rail",0)
		util.initmat(eb, "mf6019", "railpr-autdistWkAMPA", "Auto Dist - Rail",0)
		util.initmat(eb, "mf6020", "railpr-railIVTWkAMPA", "Rail IVT - Rail",0)
		util.initmat(eb, "mf6021", "railpr-railWtWkAMPA", "Rail Wait Time - Rail",0)
		util.initmat(eb, "mf6022", "railpr-busIVTWkAMPA", "Bus IVT - Rail",0)
		util.initmat(eb, "mf6023", "railpr-busWtWkAMPA", "Bus Wait Time - Rai",0)
		util.initmat(eb, "mf6024", "railpr-bordsWkAMPA", "Rail Boardings",0)
		util.initmat(eb, "mf6025", "railpr-auxWkAMPA", "Aux - Rail",0)
		util.initmat(eb, "mf6026", "railpr-fareWkAMPA", "Fare - Rail",0)

		# AM WCE impedance matrices
		util.initmat(eb, "mf6030", "wcepr-GctranWkAMPA", "WCE PnR Generalized Cost Transit Leg",0)
		util.initmat(eb, "mf6031", "wcepr-minGCWkAMPA", "WCE PnR Combined Skim Result",0)
		util.initmat(eb, "mf6032", "wcepr-autimeWkAMPA", "Auto Time - WCE",0)
		util.initmat(eb, "mf6033", "wcepr-autollWkAMPA", "Auto Toll - WCE",0)
		util.initmat(eb, "mf6034", "wcepr-autdistWkAMPA", "Auto Dist - WCE",0)
		util.initmat(eb, "mf6035", "wcepr-wceIVTWkAMPA", "WCE IVT - WCE",0)
		util.initmat(eb, "mf6036", "wcepr-wceWtWkAMPA", "WCE Wait Time - WCE",0)
		util.initmat(eb, "mf6037", "wcepr-railIVTWkAMPA", "Rail IVT - WCE",0)
		util.initmat(eb, "mf6038", "wcepr-railWtWkAMPA", "Rail Wait Time - WCE",0)
		util.initmat(eb, "mf6039", "wcepr-busIVTWkAMPA", "Bus IVT - WCE",0)
		util.initmat(eb, "mf6040", "wcepr-busWtWkAMPA", "Bus Wait Time - WCE",0)
		util.initmat(eb, "mf6041", "wcepr-bordsWkAMPA", "Boardings - WCE",0)
		util.initmat(eb, "mf6042", "wcepr-auxWkAMPA", "Aux - WCE",0)
		util.initmat(eb, "mf6043", "wcepr-fareWkAMPA", "Fare - Wce",0)

		# MD Auto generalized Cost same for all modes
		util.initmat(eb, "mf6048", "pr-gtAutoWkMDPA", "PnR Generalized Cost Auto Leg",0)


		# MD bus impedance matrices
		util.initmat(eb, "mf6050", "buspr-GctranWkMDPA", "PnR Generalized Cost Transit Leg - Bus",0)
		util.initmat(eb, "mf6051", "buspr-minGCWkMDPA", "PnR Combined Skim Result - Bus",0)
		util.initmat(eb, "mf6052", "buspr-autimeWkMDPA", "Auto Time - Bus",0)
		util.initmat(eb, "mf6053", "buspr-autollWkMDPA", "Auto Toll - Bus",0)
		util.initmat(eb, "mf6054", "buspr-autdistWkMDPA", "Auto Dist - Bus",0)
		util.initmat(eb, "mf6055", "buspr-busIVTWkMDPA", "Bus IVTT - Bus",0)
		util.initmat(eb, "mf6056", "buspr-busWtWkMDPA", "Bus Wait Time - Bus",0)
		util.initmat(eb, "mf6057", "buspr-bordsWkMDPA", "Boardings - Bus",0)
		util.initmat(eb, "mf6058", "buspr-auxWkMDPA", "Aux - Bus",0)
		util.initmat(eb, "mf6059", "buspr-fareWkMDPA", "Fare - Bus",0)

		# MD rail impedance matrices
		util.initmat(eb, "mf6060", "railpr-GctranWkMDPA", "Rail PnR Generalized Cost Transit Leg - Rail",0)
		util.initmat(eb, "mf6061", "railpr-minGCWkMDPA", "Rail PnR Combined Skim Result - Rail",0)
		util.initmat(eb, "mf6062", "railpr-autimeWkMDPA", "Auto Time - Rail",0)
		util.initmat(eb, "mf6063", "railpr-autollWkMDPA", "Auto Toll - Rail",0)
		util.initmat(eb, "mf6064", "railpr-autdistWkMDPA", "Auto Dist - Rail",0)
		util.initmat(eb, "mf6065", "railpr-railIVTWkMDPA", "Rail IVT - Rail",0)
		util.initmat(eb, "mf6066", "railpr-railWtWkMDPA", "Rail Wait Time - Rail",0)
		util.initmat(eb, "mf6067", "railpr-busIVTWkMDPA", "Bus IVT - Rail",0)
		util.initmat(eb, "mf6068", "railpr-busWtWkMDPA", "Bus Wait Time - Rai",0)
		util.initmat(eb, "mf6069", "railpr-bordsWkMDPA", "Rail Boardings",0)
		util.initmat(eb, "mf6070", "railpr-auxWkMDPA", "Aux - Rail",0)
		util.initmat(eb, "mf6071", "railpr-fareWkMDPA", "Fare - Rail",0)

		# MD WCE impedance matrices
		util.initmat(eb, "mf6075", "wcepr-GctranWkMDPA", "WCE PnR Generalized Cost Transit Leg",0)
		util.initmat(eb, "mf6076", "wcepr-minGCWkMDPA", "WCE PnR Combined Skim Result",0)
		util.initmat(eb, "mf6077", "wcepr-autimeWkMDPA", "Auto Time - WCE",0)
		util.initmat(eb, "mf6078", "wcepr-autollWkMDPA", "Auto Toll - WCE",0)
		util.initmat(eb, "mf6079", "wcepr-autdistWkMDPA", "Auto Dist - WCE",0)
		util.initmat(eb, "mf6080", "wcepr-wceIVTWkMDPA", "WCE IVT - WCE",0)
		util.initmat(eb, "mf6081", "wcepr-wceWtWkMDPA", "WCE Wait Time - WCE",0)
		util.initmat(eb, "mf6082", "wcepr-railIVTWkMDPA", "Rail IVT - WCE",0)
		util.initmat(eb, "mf6083", "wcepr-railWtWkMDPA", "Rail Wait Time - WCE",0)
		util.initmat(eb, "mf6084", "wcepr-busIVTWkMDPA", "Bus IVT - WCE",0)
		util.initmat(eb, "mf6085", "wcepr-busWtWkMDPA", "Bus Wait Time - WCE",0)
		util.initmat(eb, "mf6086", "wcepr-bordsWkMDPA", "Boardings - WCE",0)
		util.initmat(eb, "mf6087", "wcepr-auxWkMDPA", "Aux - WCE",0)
		util.initmat(eb, "mf6088", "wcepr-fareWkMDPA", "Fare - WCE",0)

		# PM Auto generalized Cost same for all modes
		util.initmat(eb, "mf6088", "pr-gtAutoWkPMPA", "PnR Generalized Cost Auto Leg",0)


		# PM bus impedance matrices
		util.initmat(eb, "mf6090", "buspr-GctranWkPMPA", "PnR Generalized Cost Transit Leg - Bus",0)
		util.initmat(eb, "mf6091", "buspr-minGCWkPMPA", "PnR Combined Skim Result - Bus",0)
		util.initmat(eb, "mf6092", "buspr-autimeWkPMPA", "Auto Time - Bus",0)
		util.initmat(eb, "mf6093", "buspr-autollWkPMPA", "Auto Toll - Bus",0)
		util.initmat(eb, "mf6094", "buspr-autdistWkPMPA", "Auto Dist - Bus",0)
		util.initmat(eb, "mf6095", "buspr-busIVTWkPMPA", "Bus IVTT - Bus",0)
		util.initmat(eb, "mf6096", "buspr-busWtWkPMPA", "Bus Wait Time - Bus",0)
		util.initmat(eb, "mf6097", "buspr-bordsWkPMPA", "Boardings - Bus",0)
		util.initmat(eb, "mf6098", "buspr-auxWkPMPA", "Aux - Bus",0)
		util.initmat(eb, "mf6099", "buspr-fareWkPMPA", "Fare - Bus",0)

		# PM rail impedance matrices
		util.initmat(eb, "mf6100", "railpr-GctranWkPMPA", "Rail PnR Generalized Cost Transit Leg - Rail",0)
		util.initmat(eb, "mf6101", "railpr-minGCWkPMPA", "Rail PnR Combined Skim Result - Rail",0)
		util.initmat(eb, "mf6102", "railpr-autimeWkPMPA", "Auto Time - Rail",0)
		util.initmat(eb, "mf6103", "railpr-autollWkPMPA", "Auto Toll - Rail",0)
		util.initmat(eb, "mf6104", "railpr-autdistWkPMPA", "Auto Dist - Rail",0)
		util.initmat(eb, "mf6105", "railpr-railIVTWkPMPA", "Rail IVT - Rail",0)
		util.initmat(eb, "mf6106", "railpr-railWtWkPMPA", "Rail Wait Time - Rail",0)
		util.initmat(eb, "mf6107", "railpr-busIVTWkPMPA", "Bus IVT - Rail",0)
		util.initmat(eb, "mf6108", "railpr-busWtWkPMPA", "Bus Wait Time - Rai",0)
		util.initmat(eb, "mf6109", "railpr-bordsWkPMPA", "Rail Boardings",0)
		util.initmat(eb, "mf6110", "railpr-auxWkPMPA", "Aux - Rail",0)
		util.initmat(eb, "mf6111", "railpr-fareWkPMPA", "Fare - Rail",0)

		# PM WCE impedance matrices
		util.initmat(eb, "mf6115", "wcepr-GctranWkPMPA", "WCE PnR Generalized Cost Transit Leg",0)
		util.initmat(eb, "mf6116", "wcepr-minGCWkPMPA", "WCE PnR Combined Skim Result",0)
		util.initmat(eb, "mf6117", "wcepr-autimeWkPMPA", "Auto Time - WCE",0)
		util.initmat(eb, "mf6118", "wcepr-autollWkPMPA", "Auto Toll - WCE",0)
		util.initmat(eb, "mf6119", "wcepr-autdistWkPMPA", "Auto Dist - WCE",0)
		util.initmat(eb, "mf6120", "wcepr-wceIVTWkPMPA", "WCE IVT - WCE",0)
		util.initmat(eb, "mf6121", "wcepr-wceWtWkPMPA", "WCE Wait Time - WCE",0)
		util.initmat(eb, "mf6122", "wcepr-railIVTWkPMPA", "Rail IVT - WCE",0)
		util.initmat(eb, "mf6123", "wcepr-railWtWkPMPA", "Rail Wait Time - WCE",0)
		util.initmat(eb, "mf6124", "wcepr-busIVTWkPMPA", "Bus IVT - WCE",0)
		util.initmat(eb, "mf6125", "wcepr-busWtWkPMPA", "Bus Wait Time - WCE",0)
		util.initmat(eb, "mf6126", "wcepr-bordsWkPMPA", "Boardings - WCE",0)
		util.initmat(eb, "mf6127", "wcepr-auxWkPMPA", "Aux - WCE",0)
		util.initmat(eb, "mf6128", "wcepr-fareWkPMPA", "Fare - WCE",0)


		# Lot choice using AM impedances, but lot choice fixed for all time periods
		util.initmat(eb, "mf6130", "buspr-lotChceNWkAMPA", "Bus Best PnR Lot - Bus",0)
		util.initmat(eb, "mf6131", "railpr-lotChceNWkAMPA", "Rail Best PnR Lot - Rail",0)
		util.initmat(eb, "mf6132", "wcepr-lotChceNWkAMPA", "Rail Best PnR Lot -WCE",0)


		# AM Auto generalized Cost same for all modes
		util.initmat(eb, "mf6133", "pr-gtAutoNWkAMPA", "PnR Generalized Cost Auto Leg",0)


		# AM bus impedance matrices
		util.initmat(eb, "mf6135", "buspr-GctranNWkAMPA", "PnR Generalized Cost Transit Leg - Bus",0)
		util.initmat(eb, "mf6136", "buspr-minGCNWkAMPA", "PnR Combined Skim Result - Bus",0)
		util.initmat(eb, "mf6137", "buspr-autimeNWkAMPA", "Auto Time - Bus",0)
		util.initmat(eb, "mf6138", "buspr-autollNWkAMPA", "Auto Toll - Bus",0)
		util.initmat(eb, "mf6139", "buspr-autdistNWkAMPA", "Auto Dist - Bus",0)
		util.initmat(eb, "mf6140", "buspr-busIVTNWkAMPA", "Bus IVTT - Bus",0)
		util.initmat(eb, "mf6141", "buspr-busWtNWkAMPA", "Bus Wait Time - Bus",0)
		util.initmat(eb, "mf6142", "buspr-bordsNWkAMPA", "Boardings - Bus",0)
		util.initmat(eb, "mf6143", "buspr-auxNWkAMPA", "Aux - Bus",0)
		util.initmat(eb, "mf6144", "buspr-fareNWkAMPA", "Fare - Bus",0)

		# AM rail impedance matrices
		util.initmat(eb, "mf6145", "railpr-GctranNWkAMPA", "Rail PnR Generalized Cost Transit Leg - Rail",0)
		util.initmat(eb, "mf6146", "railpr-minGCNWkAMPA", "Rail PnR Combined Skim Result - Rail",0)
		util.initmat(eb, "mf6147", "railpr-autimeNWkAMPA", "Auto Time - Rail",0)
		util.initmat(eb, "mf6148", "railpr-autollNWkAMPA", "Auto Toll - Rail",0)
		util.initmat(eb, "mf6149", "railpr-autdistNWkAMPA", "Auto Dist - Rail",0)
		util.initmat(eb, "mf6150", "railpr-railIVTNWkAMPA", "Rail IVT - Rail",0)
		util.initmat(eb, "mf6151", "railpr-railWtNWkAMPA", "Rail Wait Time - Rail",0)
		util.initmat(eb, "mf6152", "railpr-busIVTNWkAMPA", "Bus IVT - Rail",0)
		util.initmat(eb, "mf6153", "railpr-busWtNWkAMPA", "Bus Wait Time - Rai",0)
		util.initmat(eb, "mf6154", "railpr-bordsNWkAMPA", "Rail Boardings",0)
		util.initmat(eb, "mf6155", "railpr-auxNWkAMPA", "Aux - Rail",0)
		util.initmat(eb, "mf6156", "railpr-fareNWkAMPA", "Fare - Rail",0)

		# AM WCE impedance matrices
		util.initmat(eb, "mf6160", "wcepr-GctranNWkAMPA", "WCE PnR Generalized Cost Transit Leg",0)
		util.initmat(eb, "mf6161", "wcepr-minGCNWkAMPA", "WCE PnR Combined Skim Result",0)
		util.initmat(eb, "mf6162", "wcepr-autimeNWkAMPA", "Auto Time - WCE",0)
		util.initmat(eb, "mf6163", "wcepr-autollNWkAMPA", "Auto Toll - WCE",0)
		util.initmat(eb, "mf6164", "wcepr-autdistNWkAMPA", "Auto Dist - WCE",0)
		util.initmat(eb, "mf6165", "wcepr-wceIVTNWkAMPA", "WCE IVT - WCE",0)
		util.initmat(eb, "mf6166", "wcepr-wceWtNWkAMPA", "WCE Wait Time - WCE",0)
		util.initmat(eb, "mf6167", "wcepr-railIVTNWkAMPA", "Rail IVT - WCE",0)
		util.initmat(eb, "mf6168", "wcepr-railWtNWkAMPA", "Rail Wait Time - WCE",0)
		util.initmat(eb, "mf6169", "wcepr-busIVTNWkAMPA", "Bus IVT - WCE",0)
		util.initmat(eb, "mf6170", "wcepr-busWtNWkAMPA", "Bus Wait Time - WCE",0)
		util.initmat(eb, "mf6171", "wcepr-bordsNWkAMPA", "Boardings - WCE",0)
		util.initmat(eb, "mf6172", "wcepr-auxNWkAMPA", "Aux - WCE",0)
		util.initmat(eb, "mf6173", "wcepr-fareNWkAMPA", "Fare - WCE",0)

		# MD Auto generalized Cost same for all modes
		util.initmat(eb, "mf6173", "pr-gtAutoNWkMDPA", "PnR Generalized Cost Auto Leg",0)


		# MD bus impedance matrices
		util.initmat(eb, "mf6175", "buspr-GctranNWkMDPA", "PnR Generalized Cost Transit Leg - Bus",0)
		util.initmat(eb, "mf6176", "buspr-minGCNWkMDPA", "PnR Combined Skim Result - Bus",0)
		util.initmat(eb, "mf6177", "buspr-autimeNWkMDPA", "Auto Time - Bus",0)
		util.initmat(eb, "mf6178", "buspr-autollNWkMDPA", "Auto Toll - Bus",0)
		util.initmat(eb, "mf6179", "buspr-autdistNWkMDPA", "Auto Dist - Bus",0)
		util.initmat(eb, "mf6180", "buspr-busIVTNWkMDPA", "Bus IVTT - Bus",0)
		util.initmat(eb, "mf6181", "buspr-busWtNWkMDPA", "Bus Wait Time - Bus",0)
		util.initmat(eb, "mf6182", "buspr-bordsNWkMDPA", "Boardings - Bus",0)
		util.initmat(eb, "mf6183", "buspr-auxNWkMDPA", "Aux - Bus",0)
		util.initmat(eb, "mf6184", "buspr-fareNWkMDPA", "Fare - Bus",0)

		# MD rail impedance matrices
		util.initmat(eb, "mf6185", "railpr-GctranNWkMDPA", "Rail PnR Generalized Cost Transit Leg - Rail",0)
		util.initmat(eb, "mf6186", "railpr-minGCNWkMDPA", "Rail PnR Combined Skim Result - Rail",0)
		util.initmat(eb, "mf6187", "railpr-autimeNWkMDPA", "Auto Time - Rail",0)
		util.initmat(eb, "mf6188", "railpr-autollNWkMDPA", "Auto Toll - Rail",0)
		util.initmat(eb, "mf6189", "railpr-autdistNWkMDPA", "Auto Dist - Rail",0)
		util.initmat(eb, "mf6190", "railpr-railIVTNWkMDPA", "Rail IVT - Rail",0)
		util.initmat(eb, "mf6191", "railpr-railWtNWkMDPA", "Rail Wait Time - Rail",0)
		util.initmat(eb, "mf6192", "railpr-busIVTNWkMDPA", "Bus IVT - Rail",0)
		util.initmat(eb, "mf6193", "railpr-busWtNWkMDPA", "Bus Wait Time - Rai",0)
		util.initmat(eb, "mf6194", "railpr-bordsNWkMDPA", "Rail Boardings",0)
		util.initmat(eb, "mf6195", "railpr-auxNWkMDPA", "Aux - Rail",0)
		util.initmat(eb, "mf6196", "railpr-fareNWkMDPA", "Fare - Rail",0)

		# MD WCE impedance matrices
		util.initmat(eb, "mf6200", "wcepr-GctranNWkMDPA", "WCE PnR Generalized Cost Transit Leg",0)
		util.initmat(eb, "mf6201", "wcepr-minGCNWkMDPA", "WCE PnR Combined Skim Result",0)
		util.initmat(eb, "mf6202", "wcepr-autimeNWkMDPA", "Auto Time - WCE",0)
		util.initmat(eb, "mf6203", "wcepr-autollNWkMDPA", "Auto Toll - WCE",0)
		util.initmat(eb, "mf6204", "wcepr-autdistNWkMDPA", "Auto Dist - WCE",0)
		util.initmat(eb, "mf6205", "wcepr-wceIVTNWkMDPA", "WCE IVT - WCE",0)
		util.initmat(eb, "mf6206", "wcepr-wceWtNWkMDPA", "WCE Wait Time - WCE",0)
		util.initmat(eb, "mf6207", "wcepr-railIVTNWkMDPA", "Rail IVT - WCE",0)
		util.initmat(eb, "mf6208", "wcepr-railWtNWkMDPA", "Rail Wait Time - WCE",0)
		util.initmat(eb, "mf6209", "wcepr-busIVTNWkMDPA", "Bus IVT - WCE",0)
		util.initmat(eb, "mf6210", "wcepr-busWtNWkMDPA", "Bus Wait Time - WCE",0)
		util.initmat(eb, "mf6211", "wcepr-bordsNWkMDPA", "Boardings - WCE",0)
		util.initmat(eb, "mf6212", "wcepr-auxNWkMDPA", "Aux - WCE",0)
		util.initmat(eb, "mf6213", "wcepr-fareNWkMDPA", "Fare - WCE",0)

		# PM Auto generalized Cost same for all modes
		util.initmat(eb, "mf6213", "pr-gtAutoNWkPMPA", "PnR Generalized Cost Auto Leg",0)


		# PM bus impedance matrices
		util.initmat(eb, "mf6215", "buspr-GctranNWkPMPA", "PnR Generalized Cost Transit Leg - Bus",0)
		util.initmat(eb, "mf6216", "buspr-minGCNWkPMPA", "PnR Combined Skim Result - Bus",0)
		util.initmat(eb, "mf6217", "buspr-autimeNWkPMPA", "Auto Time - Bus",0)
		util.initmat(eb, "mf6218", "buspr-autollNWkPMPA", "Auto Toll - Bus",0)
		util.initmat(eb, "mf6219", "buspr-autdistNWkPMPA", "Auto Dist - Bus",0)
		util.initmat(eb, "mf6220", "buspr-busIVTNWkPMPA", "Bus IVTT - Bus",0)
		util.initmat(eb, "mf6221", "buspr-busWtNWkPMPA", "Bus Wait Time - Bus",0)
		util.initmat(eb, "mf6222", "buspr-bordsNWkPMPA", "Boardings - Bus",0)
		util.initmat(eb, "mf6223", "buspr-auxNWkPMPA", "Aux - Bus",0)
		util.initmat(eb, "mf6224", "buspr-fareNWkPMPA", "Fare - Bus",0)

		# PM rail impedance matrices
		util.initmat(eb, "mf6225", "railpr-GctranNWkPMPA", "Rail PnR Generalized Cost Transit Leg - Rail",0)
		util.initmat(eb, "mf6226", "railpr-minGCNWkPMPA", "Rail PnR Combined Skim Result - Rail",0)
		util.initmat(eb, "mf6227", "railpr-autimeNWkPMPA", "Auto Time - Rail",0)
		util.initmat(eb, "mf6228", "railpr-autollNWkPMPA", "Auto Toll - Rail",0)
		util.initmat(eb, "mf6229", "railpr-autdistNWkPMPA", "Auto Dist - Rail",0)
		util.initmat(eb, "mf6230", "railpr-railIVTNWkPMPA", "Rail IVT - Rail",0)
		util.initmat(eb, "mf6231", "railpr-railWtNWkPMPA", "Rail Wait Time - Rail",0)
		util.initmat(eb, "mf6232", "railpr-busIVTNWkPMPA", "Bus IVT - Rail",0)
		util.initmat(eb, "mf6233", "railpr-busWtNWkPMPA", "Bus Wait Time - Rai",0)
		util.initmat(eb, "mf6234", "railpr-bordsNWkPMPA", "Rail Boardings",0)
		util.initmat(eb, "mf6235", "railpr-auxNWkPMPA", "Aux - Rail",0)
		util.initmat(eb, "mf6236", "railpr-fareNWkPMPA", "Fare - Rail",0)

		# PM WCE impedance matrices
		util.initmat(eb, "mf6240", "wcepr-GctranNWkPMPA", "WCE PnR Generalized Cost Transit Leg",0)
		util.initmat(eb, "mf6241", "wcepr-minGCNWkPMPA", "WCE PnR Combined Skim Result",0)
		util.initmat(eb, "mf6242", "wcepr-autimeNWkPMPA", "Auto Time - WCE",0)
		util.initmat(eb, "mf6243", "wcepr-autollNWkPMPA", "Auto Toll - WCE",0)
		util.initmat(eb, "mf6244", "wcepr-autdistNWkPMPA", "Auto Dist - WCE",0)
		util.initmat(eb, "mf6245", "wcepr-wceIVTNWkPMPA", "WCE IVT - WCE",0)
		util.initmat(eb, "mf6246", "wcepr-wceWtNWkPMPA", "WCE Wait Time - WCE",0)
		util.initmat(eb, "mf6247", "wcepr-railIVTNWkPMPA", "Rail IVT - WCE",0)
		util.initmat(eb, "mf6248", "wcepr-railWtNWkPMPA", "Rail Wait Time - WCE",0)
		util.initmat(eb, "mf6249", "wcepr-busIVTNWkPMPA", "Bus IVT - WCE",0)
		util.initmat(eb, "mf6250", "wcepr-busWtNWkPMPA", "Bus Wait Time - WCE",0)
		util.initmat(eb, "mf6251", "wcepr-bordsNWkPMPA", "Boardings - WCE",0)
		util.initmat(eb, "mf6252", "wcepr-auxNWkPMPA", "Aux - WCE",0)
		util.initmat(eb, "mf6253", "wcepr-fareNWkPMPA", "Fare - WCE",0)



		# Lot choice using AM impedances, but lot choice fixed for all time periods
		util.initmat(eb, "mf6300", "buspr-lotChceWkAMAP", "Bus Best PnR Lot - Bus",0)
		util.initmat(eb, "mf6301", "railpr-lotChceWkAMAP", "Rail Best PnR Lot - Rail",0)
		util.initmat(eb, "mf6302", "wcepr-lotChceWkAMAP", "Rail Best PnR Lot -WCE",0)


		# AM Auto generalized Cost same for all modes
		util.initmat(eb, "mf6303", "pr-gtAutoWkAMAP", "PnR Generalized Cost Auto Leg",0)


		# AM bus impedance matrices
		util.initmat(eb, "mf6305", "buspr-GctranWkAMAP", "PnR Generalized Cost Transit Leg - Bus",0)
		util.initmat(eb, "mf6306", "buspr-minGCWkAMAP", "PnR Combined Skim Result - Bus",0)
		util.initmat(eb, "mf6307", "buspr-autimeWkAMAP", "Auto Time - Bus",0)
		util.initmat(eb, "mf6308", "buspr-autollWkAMAP", "Auto Toll - Bus",0)
		util.initmat(eb, "mf6309", "buspr-autdistWkAMAP", "Auto Dist - Bus",0)
		util.initmat(eb, "mf6310", "buspr-busIVTWkAMAP", "Bus IVTT - Bus",0)
		util.initmat(eb, "mf6311", "buspr-busWtWkAMAP", "Bus Wait Time - Bus",0)
		util.initmat(eb, "mf6312", "buspr-bordsWkAMAP", "Boardings - Bus",0)
		util.initmat(eb, "mf6313", "buspr-auxWkAMAP", "Aux - Bus",0)
		util.initmat(eb, "mf6314", "buspr-fareWkAMAP", "Fare - Bus",0)

		# AM rail impedance matrices
		util.initmat(eb, "mf6315", "railpr-GctranWkAMAP", "Rail PnR Generalized Cost Transit Leg - Rail",0)
		util.initmat(eb, "mf6316", "railpr-minGCWkAMAP", "Rail PnR Combined Skim Result - Rail",0)
		util.initmat(eb, "mf6317", "railpr-autimeWkAMAP", "Auto Time - Rail",0)
		util.initmat(eb, "mf6318", "railpr-autollWkAMAP", "Auto Toll - Rail",0)
		util.initmat(eb, "mf6319", "railpr-autdistWkAMAP", "Auto Dist - Rail",0)
		util.initmat(eb, "mf6320", "railpr-railIVTWkAMAP", "Rail IVT - Rail",0)
		util.initmat(eb, "mf6321", "railpr-railWtWkAMAP", "Rail Wait Time - Rail",0)
		util.initmat(eb, "mf6322", "railpr-busIVTWkAMAP", "Bus IVT - Rail",0)
		util.initmat(eb, "mf6323", "railpr-busWtWkAMAP", "Bus Wait Time - Rai",0)
		util.initmat(eb, "mf6324", "railpr-bordsWkAMAP", "Rail Boardings",0)
		util.initmat(eb, "mf6325", "railpr-auxWkAMAP", "Aux - Rail",0)
		util.initmat(eb, "mf6326", "railpr-fareWkAMAP", "Fare - Rail",0)

		# AM WCE impedance matrices
		util.initmat(eb, "mf6330", "wcepr-GctranWkAMAP", "WCE PnR Generalized Cost Transit Leg",0)
		util.initmat(eb, "mf6331", "wcepr-minGCWkAMAP", "WCE PnR Combined Skim Result",0)
		util.initmat(eb, "mf6332", "wcepr-autimeWkAMAP", "Auto Time - WCE",0)
		util.initmat(eb, "mf6333", "wcepr-autollWkAMAP", "Auto Toll - WCE",0)
		util.initmat(eb, "mf6334", "wcepr-autdistWkAMAP", "Auto Dist - WCE",0)
		util.initmat(eb, "mf6335", "wcepr-wceIVTWkAMAP", "WCE IVT - WCE",0)
		util.initmat(eb, "mf6336", "wcepr-wceWtWkAMAP", "WCE Wait Time - WCE",0)
		util.initmat(eb, "mf6337", "wcepr-railIVTWkAMAP", "Rail IVT - WCE",0)
		util.initmat(eb, "mf6338", "wcepr-railWtWkAMAP", "Rail Wait Time - WCE",0)
		util.initmat(eb, "mf6339", "wcepr-busIVTWkAMAP", "Bus IVT - WCE",0)
		util.initmat(eb, "mf6340", "wcepr-busWtWkAMAP", "Bus Wait Time - WCE",0)
		util.initmat(eb, "mf6341", "wcepr-bordsWkAMAP", "Boardings - WCE",0)
		util.initmat(eb, "mf6342", "wcepr-auxWkAMAP", "Aux - WCE",0)
		util.initmat(eb, "mf6343", "wcepr-fareWkAMAP", "Fare - Wce",0)

		# MD Auto generalized Cost same for all modes
		util.initmat(eb, "mf6348", "pr-gtAutoWkMDAP", "PnR Generalized Cost Auto Leg",0)


		# MD bus impedance matrices
		util.initmat(eb, "mf6350", "buspr-GctranWkMDAP", "PnR Generalized Cost Transit Leg - Bus",0)
		util.initmat(eb, "mf6351", "buspr-minGCWkMDAP", "PnR Combined Skim Result - Bus",0)
		util.initmat(eb, "mf6352", "buspr-autimeWkMDAP", "Auto Time - Bus",0)
		util.initmat(eb, "mf6353", "buspr-autollWkMDAP", "Auto Toll - Bus",0)
		util.initmat(eb, "mf6354", "buspr-autdistWkMDAP", "Auto Dist - Bus",0)
		util.initmat(eb, "mf6355", "buspr-busIVTWkMDAP", "Bus IVTT - Bus",0)
		util.initmat(eb, "mf6356", "buspr-busWtWkMDAP", "Bus Wait Time - Bus",0)
		util.initmat(eb, "mf6357", "buspr-bordsWkMDAP", "Boardings - Bus",0)
		util.initmat(eb, "mf6358", "buspr-auxWkMDAP", "Aux - Bus",0)
		util.initmat(eb, "mf6359", "buspr-fareWkMDAP", "Fare - Bus",0)

		# MD rail impedance matrices
		util.initmat(eb, "mf6360", "railpr-GctranWkMDAP", "Rail PnR Generalized Cost Transit Leg - Rail",0)
		util.initmat(eb, "mf6361", "railpr-minGCWkMDAP", "Rail PnR Combined Skim Result - Rail",0)
		util.initmat(eb, "mf6362", "railpr-autimeWkMDAP", "Auto Time - Rail",0)
		util.initmat(eb, "mf6363", "railpr-autollWkMDAP", "Auto Toll - Rail",0)
		util.initmat(eb, "mf6364", "railpr-autdistWkMDAP", "Auto Dist - Rail",0)
		util.initmat(eb, "mf6365", "railpr-railIVTWkMDAP", "Rail IVT - Rail",0)
		util.initmat(eb, "mf6366", "railpr-railWtWkMDAP", "Rail Wait Time - Rail",0)
		util.initmat(eb, "mf6367", "railpr-busIVTWkMDAP", "Bus IVT - Rail",0)
		util.initmat(eb, "mf6368", "railpr-busWtWkMDAP", "Bus Wait Time - Rai",0)
		util.initmat(eb, "mf6369", "railpr-bordsWkMDAP", "Rail Boardings",0)
		util.initmat(eb, "mf6370", "railpr-auxWkMDAP", "Aux - Rail",0)
		util.initmat(eb, "mf6371", "railpr-fareWkMDAP", "Fare - Rail",0)

		# MD WCE impedance matrices
		util.initmat(eb, "mf6375", "wcepr-GctranWkMDAP", "WCE PnR Generalized Cost Transit Leg",0)
		util.initmat(eb, "mf6376", "wcepr-minGCWkMDAP", "WCE PnR Combined Skim Result",0)
		util.initmat(eb, "mf6377", "wcepr-autimeWkMDAP", "Auto Time - WCE",0)
		util.initmat(eb, "mf6378", "wcepr-autollWkMDAP", "Auto Toll - WCE",0)
		util.initmat(eb, "mf6379", "wcepr-autdistWkMDAP", "Auto Dist - WCE",0)
		util.initmat(eb, "mf6380", "wcepr-wceIVTWkMDAP", "WCE IVT - WCE",0)
		util.initmat(eb, "mf6381", "wcepr-wceWtWkMDAP", "WCE Wait Time - WCE",0)
		util.initmat(eb, "mf6382", "wcepr-railIVTWkMDAP", "Rail IVT - WCE",0)
		util.initmat(eb, "mf6383", "wcepr-railWtWkMDAP", "Rail Wait Time - WCE",0)
		util.initmat(eb, "mf6384", "wcepr-busIVTWkMDAP", "Bus IVT - WCE",0)
		util.initmat(eb, "mf6385", "wcepr-busWtWkMDAP", "Bus Wait Time - WCE",0)
		util.initmat(eb, "mf6386", "wcepr-bordsWkMDAP", "Boardings - WCE",0)
		util.initmat(eb, "mf6387", "wcepr-auxWkMDAP", "Aux - WCE",0)
		util.initmat(eb, "mf6388", "wcepr-fareWkMDAP", "Fare - WCE",0)

		# PM Auto generalized Cost same for all modes
		util.initmat(eb, "mf6388", "pr-gtAutoWkPMAP", "PnR Generalized Cost Auto Leg",0)


		# PM bus impedance matrices
		util.initmat(eb, "mf6390", "buspr-GctranWkPMAP", "PnR Generalized Cost Transit Leg - Bus",0)
		util.initmat(eb, "mf6391", "buspr-minGCWkPMAP", "PnR Combined Skim Result - Bus",0)
		util.initmat(eb, "mf6392", "buspr-autimeWkPMAP", "Auto Time - Bus",0)
		util.initmat(eb, "mf6393", "buspr-autollWkPMAP", "Auto Toll - Bus",0)
		util.initmat(eb, "mf6394", "buspr-autdistWkPMAP", "Auto Dist - Bus",0)
		util.initmat(eb, "mf6395", "buspr-busIVTWkPMAP", "Bus IVTT - Bus",0)
		util.initmat(eb, "mf6396", "buspr-busWtWkPMAP", "Bus Wait Time - Bus",0)
		util.initmat(eb, "mf6397", "buspr-bordsWkPMAP", "Boardings - Bus",0)
		util.initmat(eb, "mf6398", "buspr-auxWkPMAP", "Aux - Bus",0)
		util.initmat(eb, "mf6399", "buspr-fareWkPMAP", "Fare - Bus",0)

		# PM rail impedance matrices
		util.initmat(eb, "mf6400", "railpr-GctranWkPMAP", "Rail PnR Generalized Cost Transit Leg - Rail",0)
		util.initmat(eb, "mf6401", "railpr-minGCWkPMAP", "Rail PnR Combined Skim Result - Rail",0)
		util.initmat(eb, "mf6402", "railpr-autimeWkPMAP", "Auto Time - Rail",0)
		util.initmat(eb, "mf6403", "railpr-autollWkPMAP", "Auto Toll - Rail",0)
		util.initmat(eb, "mf6404", "railpr-autdistWkPMAP", "Auto Dist - Rail",0)
		util.initmat(eb, "mf6405", "railpr-railIVTWkPMAP", "Rail IVT - Rail",0)
		util.initmat(eb, "mf6406", "railpr-railWtWkPMAP", "Rail Wait Time - Rail",0)
		util.initmat(eb, "mf6407", "railpr-busIVTWkPMAP", "Bus IVT - Rail",0)
		util.initmat(eb, "mf6408", "railpr-busWtWkPMAP", "Bus Wait Time - Rai",0)
		util.initmat(eb, "mf6409", "railpr-bordsWkPMAP", "Rail Boardings",0)
		util.initmat(eb, "mf6410", "railpr-auxWkPMAP", "Aux - Rail",0)
		util.initmat(eb, "mf6411", "railpr-fareWkPMAP", "Fare - Rail",0)

		# PM WCE impedance matrices
		util.initmat(eb, "mf6415", "wcepr-GctranWkPMAP", "WCE PnR Generalized Cost Transit Leg",0)
		util.initmat(eb, "mf6416", "wcepr-minGCWkPMAP", "WCE PnR Combined Skim Result",0)
		util.initmat(eb, "mf6417", "wcepr-autimeWkPMAP", "Auto Time - WCE",0)
		util.initmat(eb, "mf6418", "wcepr-autollWkPMAP", "Auto Toll - WCE",0)
		util.initmat(eb, "mf6419", "wcepr-autdistWkPMAP", "Auto Dist - WCE",0)
		util.initmat(eb, "mf6420", "wcepr-wceIVTWkPMAP", "WCE IVT - WCE",0)
		util.initmat(eb, "mf6421", "wcepr-wceWtWkPMAP", "WCE Wait Time - WCE",0)
		util.initmat(eb, "mf6422", "wcepr-railIVTWkPMAP", "Rail IVT - WCE",0)
		util.initmat(eb, "mf6423", "wcepr-railWtWkPMAP", "Rail Wait Time - WCE",0)
		util.initmat(eb, "mf6424", "wcepr-busIVTWkPMAP", "Bus IVT - WCE",0)
		util.initmat(eb, "mf6425", "wcepr-busWtWkPMAP", "Bus Wait Time - WCE",0)
		util.initmat(eb, "mf6426", "wcepr-bordsWkPMAP", "Boardings - WCE",0)
		util.initmat(eb, "mf6427", "wcepr-auxWkPMAP", "Aux - WCE",0)
		util.initmat(eb, "mf6428", "wcepr-fareWkPMAP", "Fare - WCE",0)


		# Lot choice using AM impedances, but lot choice fixed for all time periods
		util.initmat(eb, "mf6430", "buspr-lotChceNWkAMAP", "Bus Best PnR Lot - Bus",0)
		util.initmat(eb, "mf6431", "railpr-lotChceNWkAMAP", "Rail Best PnR Lot - Rail",0)
		util.initmat(eb, "mf6432", "wcepr-lotChceNWkAMAP", "Rail Best PnR Lot -WCE",0)


		# AM Auto generalized Cost same for all modes
		util.initmat(eb, "mf6433", "pr-gtAutoNWkAMAP", "PnR Generalized Cost Auto Leg",0)


		# AM bus impedance matrices
		util.initmat(eb, "mf6435", "buspr-GctranNWkAMAP", "PnR Generalized Cost Transit Leg - Bus",0)
		util.initmat(eb, "mf6436", "buspr-minGCNWkAMAP", "PnR Combined Skim Result - Bus",0)
		util.initmat(eb, "mf6437", "buspr-autimeNWkAMAP", "Auto Time - Bus",0)
		util.initmat(eb, "mf6438", "buspr-autollNWkAMAP", "Auto Toll - Bus",0)
		util.initmat(eb, "mf6439", "buspr-autdistNWkAMAP", "Auto Dist - Bus",0)
		util.initmat(eb, "mf6440", "buspr-busIVTNWkAMAP", "Bus IVTT - Bus",0)
		util.initmat(eb, "mf6441", "buspr-busWtNWkAMAP", "Bus Wait Time - Bus",0)
		util.initmat(eb, "mf6442", "buspr-bordsNWkAMAP", "Boardings - Bus",0)
		util.initmat(eb, "mf6443", "buspr-auxNWkAMAP", "Aux - Bus",0)
		util.initmat(eb, "mf6444", "buspr-fareNWkAMAP", "Fare - Bus",0)

		# AM rail impedance matrices
		util.initmat(eb, "mf6445", "railpr-GctranNWkAMAP", "Rail PnR Generalized Cost Transit Leg - Rail",0)
		util.initmat(eb, "mf6446", "railpr-minGCNWkAMAP", "Rail PnR Combined Skim Result - Rail",0)
		util.initmat(eb, "mf6447", "railpr-autimeNWkAMAP", "Auto Time - Rail",0)
		util.initmat(eb, "mf6448", "railpr-autollNWkAMAP", "Auto Toll - Rail",0)
		util.initmat(eb, "mf6449", "railpr-autdistNWkAMAP", "Auto Dist - Rail",0)
		util.initmat(eb, "mf6450", "railpr-railIVTNWkAMAP", "Rail IVT - Rail",0)
		util.initmat(eb, "mf6451", "railpr-railWtNWkAMAP", "Rail Wait Time - Rail",0)
		util.initmat(eb, "mf6452", "railpr-busIVTNWkAMAP", "Bus IVT - Rail",0)
		util.initmat(eb, "mf6453", "railpr-busWtNWkAMAP", "Bus Wait Time - Rai",0)
		util.initmat(eb, "mf6454", "railpr-bordsNWkAMAP", "Rail Boardings",0)
		util.initmat(eb, "mf6455", "railpr-auxNWkAMAP", "Aux - Rail",0)
		util.initmat(eb, "mf6456", "railpr-fareNWkAMAP", "Fare - Rail",0)

		# AM WCE impedance matrices
		util.initmat(eb, "mf6460", "wcepr-GctranNWkAMAP", "WCE PnR Generalized Cost Transit Leg",0)
		util.initmat(eb, "mf6461", "wcepr-minGCNWkAMAP", "WCE PnR Combined Skim Result",0)
		util.initmat(eb, "mf6462", "wcepr-autimeNWkAMAP", "Auto Time - WCE",0)
		util.initmat(eb, "mf6463", "wcepr-autollNWkAMAP", "Auto Toll - WCE",0)
		util.initmat(eb, "mf6464", "wcepr-autdistNWkAMAP", "Auto Dist - WCE",0)
		util.initmat(eb, "mf6465", "wcepr-wceIVTNWkAMAP", "WCE IVT - WCE",0)
		util.initmat(eb, "mf6466", "wcepr-wceWtNWkAMAP", "WCE Wait Time - WCE",0)
		util.initmat(eb, "mf6467", "wcepr-railIVTNWkAMAP", "Rail IVT - WCE",0)
		util.initmat(eb, "mf6468", "wcepr-railWtNWkAMAP", "Rail Wait Time - WCE",0)
		util.initmat(eb, "mf6469", "wcepr-busIVTNWkAMAP", "Bus IVT - WCE",0)
		util.initmat(eb, "mf6470", "wcepr-busWtNWkAMAP", "Bus Wait Time - WCE",0)
		util.initmat(eb, "mf6471", "wcepr-bordsNWkAMAP", "Boardings - WCE",0)
		util.initmat(eb, "mf6472", "wcepr-auxNWkAMAP", "Aux - WCE",0)
		util.initmat(eb, "mf6473", "wcepr-fareNWkAMAP", "Fare - WCE",0)

		# MD Auto generalized Cost same for all modes
		util.initmat(eb, "mf6473", "pr-gtAutoNWkMDAP", "PnR Generalized Cost Auto Leg",0)


		# MD bus impedance matrices
		util.initmat(eb, "mf6475", "buspr-GctranNWkMDAP", "PnR Generalized Cost Transit Leg - Bus",0)
		util.initmat(eb, "mf6476", "buspr-minGCNWkMDAP", "PnR Combined Skim Result - Bus",0)
		util.initmat(eb, "mf6477", "buspr-autimeNWkMDAP", "Auto Time - Bus",0)
		util.initmat(eb, "mf6478", "buspr-autollNWkMDAP", "Auto Toll - Bus",0)
		util.initmat(eb, "mf6479", "buspr-autdistNWkMDAP", "Auto Dist - Bus",0)
		util.initmat(eb, "mf6480", "buspr-busIVTNWkMDAP", "Bus IVTT - Bus",0)
		util.initmat(eb, "mf6481", "buspr-busWtNWkMDAP", "Bus Wait Time - Bus",0)
		util.initmat(eb, "mf6482", "buspr-bordsNWkMDAP", "Boardings - Bus",0)
		util.initmat(eb, "mf6483", "buspr-auxNWkMDAP", "Aux - Bus",0)
		util.initmat(eb, "mf6484", "buspr-fareNWkMDAP", "Fare - Bus",0)

		# MD rail impedance matrices
		util.initmat(eb, "mf6485", "railpr-GctranNWkMDAP", "Rail PnR Generalized Cost Transit Leg - Rail",0)
		util.initmat(eb, "mf6486", "railpr-minGCNWkMDAP", "Rail PnR Combined Skim Result - Rail",0)
		util.initmat(eb, "mf6487", "railpr-autimeNWkMDAP", "Auto Time - Rail",0)
		util.initmat(eb, "mf6488", "railpr-autollNWkMDAP", "Auto Toll - Rail",0)
		util.initmat(eb, "mf6489", "railpr-autdistNWkMDAP", "Auto Dist - Rail",0)
		util.initmat(eb, "mf6490", "railpr-railIVTNWkMDAP", "Rail IVT - Rail",0)
		util.initmat(eb, "mf6491", "railpr-railWtNWkMDAP", "Rail Wait Time - Rail",0)
		util.initmat(eb, "mf6492", "railpr-busIVTNWkMDAP", "Bus IVT - Rail",0)
		util.initmat(eb, "mf6493", "railpr-busWtNWkMDAP", "Bus Wait Time - Rai",0)
		util.initmat(eb, "mf6494", "railpr-bordsNWkMDAP", "Rail Boardings",0)
		util.initmat(eb, "mf6495", "railpr-auxNWkMDAP", "Aux - Rail",0)
		util.initmat(eb, "mf6496", "railpr-fareNWkMDAP", "Fare - Rail",0)

		# MD WCE impedance matrices
		util.initmat(eb, "mf6500", "wcepr-GctranNWkMDAP", "WCE PnR Generalized Cost Transit Leg",0)
		util.initmat(eb, "mf6501", "wcepr-minGCNWkMDAP", "WCE PnR Combined Skim Result",0)
		util.initmat(eb, "mf6502", "wcepr-autimeNWkMDAP", "Auto Time - WCE",0)
		util.initmat(eb, "mf6503", "wcepr-autollNWkMDAP", "Auto Toll - WCE",0)
		util.initmat(eb, "mf6504", "wcepr-autdistNWkMDAP", "Auto Dist - WCE",0)
		util.initmat(eb, "mf6505", "wcepr-wceIVTNWkMDAP", "WCE IVT - WCE",0)
		util.initmat(eb, "mf6506", "wcepr-wceWtNWkMDAP", "WCE Wait Time - WCE",0)
		util.initmat(eb, "mf6507", "wcepr-railIVTNWkMDAP", "Rail IVT - WCE",0)
		util.initmat(eb, "mf6508", "wcepr-railWtNWkMDAP", "Rail Wait Time - WCE",0)
		util.initmat(eb, "mf6509", "wcepr-busIVTNWkMDAP", "Bus IVT - WCE",0)
		util.initmat(eb, "mf6510", "wcepr-busWtNWkMDAP", "Bus Wait Time - WCE",0)
		util.initmat(eb, "mf6511", "wcepr-bordsNWkMDAP", "Boardings - WCE",0)
		util.initmat(eb, "mf6512", "wcepr-auxNWkMDAP", "Aux - WCE",0)
		util.initmat(eb, "mf6513", "wcepr-fareNWkMDAP", "Fare - WCE",0)

		# PM Auto generalized Cost same for all modes
		util.initmat(eb, "mf6513", "pr-gtAutoNWkPMAP", "PnR Generalized Cost Auto Leg",0)


		# PM bus impedance matrices
		util.initmat(eb, "mf6515", "buspr-GctranNWkPMAP", "PnR Generalized Cost Transit Leg - Bus",0)
		util.initmat(eb, "mf6516", "buspr-minGCNWkPMAP", "PnR Combined Skim Result - Bus",0)
		util.initmat(eb, "mf6517", "buspr-autimeNWkPMAP", "Auto Time - Bus",0)
		util.initmat(eb, "mf6518", "buspr-autollNWkPMAP", "Auto Toll - Bus",0)
		util.initmat(eb, "mf6519", "buspr-autdistNWkPMAP", "Auto Dist - Bus",0)
		util.initmat(eb, "mf6520", "buspr-busIVTNWkPMAP", "Bus IVTT - Bus",0)
		util.initmat(eb, "mf6521", "buspr-busWtNWkPMAP", "Bus Wait Time - Bus",0)
		util.initmat(eb, "mf6522", "buspr-bordsNWkPMAP", "Boardings - Bus",0)
		util.initmat(eb, "mf6523", "buspr-auxNWkPMAP", "Aux - Bus",0)
		util.initmat(eb, "mf6524", "buspr-fareNWkPMAP", "Fare - Bus",0)

		# PM rail impedance matrices
		util.initmat(eb, "mf6525", "railpr-GctranNWkPMAP", "Rail PnR Generalized Cost Transit Leg - Rail",0)
		util.initmat(eb, "mf6526", "railpr-minGCNWkPMAP", "Rail PnR Combined Skim Result - Rail",0)
		util.initmat(eb, "mf6527", "railpr-autimeNWkPMAP", "Auto Time - Rail",0)
		util.initmat(eb, "mf6528", "railpr-autollNWkPMAP", "Auto Toll - Rail",0)
		util.initmat(eb, "mf6529", "railpr-autdistNWkPMAP", "Auto Dist - Rail",0)
		util.initmat(eb, "mf6530", "railpr-railIVTNWkPMAP", "Rail IVT - Rail",0)
		util.initmat(eb, "mf6531", "railpr-railWtNWkPMAP", "Rail Wait Time - Rail",0)
		util.initmat(eb, "mf6532", "railpr-busIVTNWkPMAP", "Bus IVT - Rail",0)
		util.initmat(eb, "mf6533", "railpr-busWtNWkPMAP", "Bus Wait Time - Rai",0)
		util.initmat(eb, "mf6534", "railpr-bordsNWkPMAP", "Rail Boardings",0)
		util.initmat(eb, "mf6535", "railpr-auxNWkPMAP", "Aux - Rail",0)
		util.initmat(eb, "mf6536", "railpr-fareNWkPMAP", "Fare - Rail",0)

		# PM WCE impedance matrices
		util.initmat(eb, "mf6540", "wcepr-GctranNWkPMAP", "WCE PnR Generalized Cost Transit Leg",0)
		util.initmat(eb, "mf6541", "wcepr-minGCNWkPMAP", "WCE PnR Combined Skim Result",0)
		util.initmat(eb, "mf6542", "wcepr-autimeNWkPMAP", "Auto Time - WCE",0)
		util.initmat(eb, "mf6543", "wcepr-autollNWkPMAP", "Auto Toll - WCE",0)
		util.initmat(eb, "mf6544", "wcepr-autdistNWkPMAP", "Auto Dist - WCE",0)
		util.initmat(eb, "mf6545", "wcepr-wceIVTNWkPMAP", "WCE IVT - WCE",0)
		util.initmat(eb, "mf6546", "wcepr-wceWtNWkPMAP", "WCE Wait Time - WCE",0)
		util.initmat(eb, "mf6547", "wcepr-railIVTNWkPMAP", "Rail IVT - WCE",0)
		util.initmat(eb, "mf6548", "wcepr-railWtNWkPMAP", "Rail Wait Time - WCE",0)
		util.initmat(eb, "mf6549", "wcepr-busIVTNWkPMAP", "Bus IVT - WCE",0)
		util.initmat(eb, "mf6550", "wcepr-busWtNWkPMAP", "Bus Wait Time - WCE",0)
		util.initmat(eb, "mf6551", "wcepr-bordsNWkPMAP", "Boardings - WCE",0)
		util.initmat(eb, "mf6552", "wcepr-auxNWkPMAP", "Aux - WCE",0)
		util.initmat(eb, "mf6553", "wcepr-fareNWkPMAP", "Fare - WCE",0)
