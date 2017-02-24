##---------------------------------------------------------------------
##--TransLink Phase 3.0 Regional Transportation Model
##--
##--Path: translink.RTM3.stage2.truckmodel
##--Purpose: Run Full truck Model
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback
import os

class FullTruckModel(_m.Tool()):
    Year = _m.Attribute(int)

    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "Full Truck Model Run"
        pb.description = "Run Full Truck Model"
        pb.branding_text = "TransLink"

        pb.add_select(tool_attribute_name="Year",keyvalues=[[2011,"2011"],[2030,"2030"],[2045,"2045"]],
                        title="Choose Analysis Year (2011, 2030 or 2045)")

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        try:
            self.__call__(_m.Modeller().emmebank, self.Year)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("Full Truck Model Run")
    def __call__(self, eb, Year):
        self.cross_border(eb, Year)

        self.inter_regional(eb, Year)

        return
        AsiaPacificModel=_m.Modeller().tool("translink.emme.stage5.step10.asiapacifictruck")
        AsiaPacificModel(eb, Year)

        RegionalModel=_m.Modeller().tool("translink.emme.stage5.step10.regionaltruck")
        RegionalModel(eb)

        self.aggregate_demand_pce(eb)

    @_m.logbook_trace("Cross Border Demand Market")
    def cross_border(self, eb, Year):
        util = _m.Modeller().tool("translink.util")

        process = _m.Modeller().tool("inro.emme.data.matrix.matrix_transaction")
        root_directory = util.get_input_path(eb)

        util.delmat(eb, "mf8000")
        util.delmat(eb, "mf8001")
        util.delmat(eb, "mf8002")
        util.delmat(eb, "mf8003")
        util.delmat(eb, "mf8010")
        util.delmat(eb, "mf8011")
        util.delmat(eb, "mf8012")
        util.delmat(eb, "mf8013")
        matrix_file1 = os.path.join(root_directory, "TruckBatchFiles", str(Year)+"CrossBorderv1.txt")
        process(transaction_file=matrix_file1, throw_on_error=True)

    @_m.logbook_trace("Inter-Regional Demand Market")
    def inter_regional(self, eb, Year):
        util = _m.Modeller().tool("translink.util")

        process = _m.Modeller().tool("inro.emme.data.matrix.matrix_transaction")
        root_directory = util.get_input_path(eb)

        util.delmat(eb, "mf8020")
        util.delmat(eb, "mf8021")
        matrix_file2 = os.path.join(root_directory, "TruckBatchFiles", "IRBatchIn.txt")
        process(transaction_file=matrix_file2, throw_on_error=True)

        self.ir_generation(eb, Year)
        self.ir_distribution(eb)
        self.ir_timeslicing(eb)

    def ir_generation(self, eb, Year):
        util = _m.Modeller().tool("translink.util")

        ## Regression coefficients:
        # Eastern Gate Heavy Trucks Model (Highway 1 & 7)
        EaHvInt = -553.2835   # Intercept
        EaHvGDP =  0.02199    # BC GDP in millions (2009)
        EaHvQ1  = -59.5213    # Q1 Dummy
        EaHvQ2  = 513.1907    # Q2 Dummy
        EaHvQ3  = 687.1213    # Q3 Dummy
        EaHvRc  = -173.4101   # Q4 Dummy

        # Eastern Gate Light Trucks Model (Highway 1 & 7)
        EaLgInt = 327.5659    # Intercept
        EaLgGDP = 0.0045      # BC GDP in millions (2009)
        EaLgQ1  = -250.5681   # Q1 Dummy
        EaLgQ2  = 489.0382    # Q2 Dummy
        EaLgQ3  = 1217.0917   # Q3 Dummy
        EaLgRc  = 0           # Recession Dummy

        # Western Gate Light+Heavy Trucks Model (Tsawwassen & Horseshoe Bay)
        WsHvInt = 467.5491    # Intercept
        WsHvGDP = 0.0007      # BC GDP in millions (2009)
        WsHvQ1  = -38.0215    # Q1 Dummy
        WsHvQ2  = 168.9189    # Q2 Dummy
        WsHvQ3  = 387.8932    # Q3 Dummy
        WsHvRc  = -46.7124    # Recession Dummy

        ## Regression Variable Assumptions
        IB_Split=[0.5,0.46,0.5] # IB=Towards CBD; IB-OB: Heavy East=0.5, Light East=0.46, All Trucks West=0.5
        Hw1_Split=[0.84,0.85] # Split between Highway 1 and 7 in East: Heavy=0.84, Light=0.85
        TsawassenSplit=0.7
        Wkd_Factor=[1.357,1.102,1.590,1.263,1.184] # Factor to convert from Avg Quarter Monthly Traffic to Typical Fall weekday (East Heavy, East Light, Trucks West)
        TruckConFact=0.35 # % Light Truck in West Area
        Quarter=4

        if Year==2011:
            BC_GDP=172696
            NGrowth1=1
            NGrowth2=1

        if Year==2030:
            BC_GDP=257458.98
            NGrowth1=1.2
            NGrowth2=1.2

        if Year==2045:
            BC_GDP=331079.67
            NGrowth1=1.28
            NGrowth2=1.5

        Q1,Q2,Q3,Rcn=0,0,0,0

        if Quarter==1:
            Q1=1
        if Quarter==2:
            Q2=1
        if Quarter==3:
            Q3=1

        ## Regression Functions

        EastHeavyTrucks=EaHvInt+BC_GDP*EaHvGDP+Q1*EaHvQ1+Q2*EaHvQ2+Q3*EaHvQ3+Rcn*EaHvRc  # East Heavy Total both directions

        EastLightTrucks=EaLgInt+BC_GDP*EaLgGDP+Q1*EaLgQ1+Q2*EaLgQ2+Q3*EaLgQ3+Rcn*EaLgRc  # East Light Total both directions

        WestTrucks=WsHvInt+BC_GDP*WsHvGDP+Q1*WsHvQ1+Q2*WsHvQ2+Q3*WsHvQ3+Rcn*WsHvRc       # West All Trucks Total both directions

        NorthLightTrucks=269*NGrowth1 # Light Trucks per direction (estimated from MOT counts)
        NorthHeavyTrucks=92*NGrowth2  # Heavy Truck  per direction (estimated from MOT counts)

        ## Generate 24 hr mos and mds

        LightTruckSum=EastLightTrucks+0.35*WestTrucks+NorthLightTrucks
        HeavyTruckSum=EastHeavyTrucks+0.65*WestTrucks+NorthHeavyTrucks

        HeavyTrucksFrom=[EastHeavyTrucks*(IB_Split[0])*(1-Hw1_Split[0])*Wkd_Factor[0],
                         EastHeavyTrucks*(IB_Split[0])*(Hw1_Split[0])*Wkd_Factor[0],
                         WestTrucks*(IB_Split[2])*TsawassenSplit*Wkd_Factor[2]*(1-TruckConFact),
                         WestTrucks*(IB_Split[2])*(1-TsawassenSplit)*Wkd_Factor[2]*(1-TruckConFact),
                         NorthHeavyTrucks*Wkd_Factor[3]]

        HeavyTrucksTo=  [EastHeavyTrucks*(1-IB_Split[0])*(1-Hw1_Split[0])*Wkd_Factor[0],
                         EastHeavyTrucks*(1-IB_Split[0])*(Hw1_Split[0])*Wkd_Factor[0],
                         WestTrucks*(1-IB_Split[2])*TsawassenSplit*Wkd_Factor[2]*(1-TruckConFact),
                         WestTrucks*(1-IB_Split[2])*(1-TsawassenSplit)*Wkd_Factor[2]*(1-TruckConFact),
                         NorthHeavyTrucks*Wkd_Factor[3]]

        LightTrucksFrom=[EastLightTrucks*(IB_Split[1])*(1-Hw1_Split[1])*Wkd_Factor[1],
                         EastLightTrucks*(IB_Split[1])*(Hw1_Split[1])*Wkd_Factor[1],
                         WestTrucks*(IB_Split[2])*TsawassenSplit*Wkd_Factor[2]*(TruckConFact),
                         WestTrucks*(IB_Split[2])*(1-TsawassenSplit)*Wkd_Factor[2]*(TruckConFact),
                         NorthLightTrucks*Wkd_Factor[4]]

        LightTrucksTo= [EastLightTrucks*(1-IB_Split[1])*(1-Hw1_Split[1])*Wkd_Factor[1],
                        EastLightTrucks*(1-IB_Split[1])*(Hw1_Split[1])*Wkd_Factor[1],
                        WestTrucks*(1-IB_Split[2])*TsawassenSplit*Wkd_Factor[2]*(TruckConFact),
                        WestTrucks*(1-IB_Split[2])*(1-TsawassenSplit)*Wkd_Factor[2]*(TruckConFact),
                        NorthLightTrucks*Wkd_Factor[4]]

        # Outputs: 24 hours trip generation - (Light From, Heavy From, Light To, Heavy To)
        util.initmat(eb, "mo8020", "IRLgPr", "IR LgTruck Productions", 0)
        util.initmat(eb, "mo8021", "IRHvPr", "IR HvTruck Productions", 0)
        util.initmat(eb, "md8020", "IRLgAt", "IR LgTruck Attractions", 0)
        util.initmat(eb, "md8021", "IRHvAt", "IR HvTruck Attractions", 0)

        matrixlist=["mo8020","mo8021","md8020","md8021"]

        TruckList=[LightTrucksFrom,HeavyTrucksFrom, LightTrucksTo ,HeavyTrucksTo]

        ExtZoneList=[1,2,8,10,11] #[1: Highway 7, 2: Highway 2, 8: Tsawwassen, 10: HoreshoeBay, 11: Highway 99]

        specs = []
        for i in range (0, len(matrixlist)):
            for j in range(0, len(ExtZoneList)):
                spec = util.matrix_spec(matrixlist[i], str(TruckList[i][j]))
                if i < 2:
                    spec["constraint"]["by_zone"] = {"origins": str(ExtZoneList[j]), "destinations": None}
                else:
                    spec["constraint"]["by_zone"] = {"origins": None, "destinations": str(ExtZoneList[j])}
                specs.append(spec)
        util.compute_matrix(specs)

        util.initmat(eb, "mo8022",  "IRLgAdj", "IR Lg Adjustment Calc", 0)
        util.initmat(eb, "md8022",  "IRLgAdj", "IR Lg Adjustment Calc", 0)
        util.initmat(eb, "mo8023",  "IRHvAdj", "IR Hv Adjustment Calc", 0)
        util.initmat(eb, "md8023",  "IRHvAdj", "IR Hv Adjustment Calc", 0)

        specs = []

        spec = util.matrix_spec("mo8022", "mf8000")
        spec["constraint"]["by_zone"] = {"origins": "1;2;8;10;11", "destinations": "*"}
        spec["aggregation"] = {"origins": None, "destinations": "+"}
        specs.append(spec)

        spec = util.matrix_spec("mo8023", "mf8010")
        spec["constraint"]["by_zone"] = {"origins": "1;2;8;10;11", "destinations": "*"}
        spec["aggregation"] = {"origins": None, "destinations": "+"}
        specs.append(spec)

        spec = util.matrix_spec("md8022", "mf8000")
        spec["constraint"]["by_zone"] = {"origins": "*", "destinations": "1;2;8;10;11"}
        spec["aggregation"] = {"origins": "+", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("md8023", "mf8010")
        spec["constraint"]["by_zone"] = {"origins": "*", "destinations": "1;2;8;10;11"}
        spec["aggregation"] = {"origins": "+", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("mo8020", "((mo8020-mo8022).max.0)")
        specs.append(spec)

        spec = util.matrix_spec("md8020", "((md8020-md8022).max.0)")
        specs.append(spec)

        spec = util.matrix_spec("mo8021", "((mo8021-mo8023).max.0)")
        specs.append(spec)

        spec = util.matrix_spec("md8021", "((md8021-md8023).max.0)")
        specs.append(spec)

        util.compute_matrix(specs)

    @_m.logbook_trace("Trip Distribution")
    def ir_distribution(self, eb):
        util = _m.Modeller().tool("translink.util")

        ## Distribute External mo and md trips based on 1999 O-D Survey
        util.initmat(eb, "mf8022", "IRLg24", "IR LgTruck Daily Trips", 0)
        util.initmat(eb, "mf8023", "IRHv24", "IR HvTruck Daily Trips", 0)

        specs = []

        spec = util.matrix_spec("mf8022", "mo8020*mf8020 + md8020*mf8020")
        specs.append(spec)

        spec = util.matrix_spec("mf8023", "mo8021*mf8021 + md8021*mf8021")
        specs.append(spec)

        util.compute_matrix(specs)

    @_m.logbook_trace("Time Slicing")
    def ir_timeslicing(self, eb):
        util = _m.Modeller().tool("translink.util")

        util.initmat(eb, "mf8024", "IRLgAM", "IR LgTruck AM Trips", 0)
        util.initmat(eb, "mf8025", "IRHvAM", "IR HvTruck AM Trips", 0)
        util.initmat(eb, "mf8026", "IRLgMD", "IR LgTruck MD Trips", 0)
        util.initmat(eb, "mf8027", "IRHvMD", "IR HvTruck MD Trips", 0)
        util.initmat(eb, "mf8028", "IRLgPM", "IR LgTruck PM Trips", 0)
        util.initmat(eb, "mf8029", "IRHvPM", "IR HvTruck PM Trips", 0)

        # IB      Light Trucks AM            Light Trucks MD          Light Trucks PM            Heavy Trucks AM         Heavy Trucks MD            Heavy Trucks PM
        FactorIB=[[0.05868,0.04086,0.05086],[0.05868,0.09194,0.10426],[0.05868,0.09194,0.10426],[0.03811,0.09500,0.02912],[0.07470,0.09866,0.11649],[0.07470,0.09866,0.11649]]

        # OB      Light Trucks AM            Light Trucks MD          Light Trucks PM              Heavy Trucks AM         Heavy Trucks MD         Heavy Trucks PM
        FactorOB=[[0.03613,0.02054,0.11882],[0.04517,0.1027,0.07505],[0.04517,0.1027,0.07505], [0.04328,0.05253,0.10976],[0.08743,0.10507,0.08537],[0.08743,0.10507,0.08537]]


        ConstraintList=[[1,2],[8,10],[11]]

                    ## LightAM, LightMD,HeavyAM, HeavyMD
        Matrix_List = ["mf8024", "mf8026", "mf8028", "mf8025", "mf8027", "mf8029"]
        TripDistList= ["mf8022", "mf8023"]

        for i in range (len(TripDistList)) :
            for j in range (int((len(FactorIB)/2))):
                for k in range (len(FactorIB[j])):
                    spec = util.matrix_spec("", TripDistList[i]+"*"+str(FactorIB[3*i+j][k]))
                    for l in range (0, len(ConstraintList[k])):
                        spec["result"] = Matrix_List[3*i+j]
                        spec["constraint"]["by_zone"] = {"origins": str(ConstraintList[k][l]), "destinations": "*"}
                        util.compute_matrix(spec)

        for i in range (len(TripDistList)) :
            for j in range (int((len(FactorIB)/2))):
                for k in range (len(FactorOB[j])):
                    spec = util.matrix_spec("", str(TripDistList[i])+"*"+str(FactorOB[3*i+j][k]))
                    for l in range (0, len(ConstraintList[k])):
                        spec["result"] = Matrix_List[3*i+j]
                        spec["constraint"]["by_zone"] = {"origins": "*", "destinations": str(ConstraintList[k][l])}
                        util.compute_matrix(spec)

    def aggregate_demand_pce(self, eb):
        util = _m.Modeller().tool("translink.util")

        util.initmat(eb, "mf1040", "CBLgAp", "CB LgTruck AM PCE", 0)
        util.initmat(eb, "mf1041", "CBHvAp", "CB HvTruck AM PCE", 0)
        util.initmat(eb, "mf1042", "IRLgAp", "IR LgTruck AM PCE", 0)
        util.initmat(eb, "mf1043", "IRHvAp", "IR HvTruck AM PCE", 0)
        util.initmat(eb, "mf1044", "APHvAp", "AP HvTruck AM PCE", 0)
        util.initmat(eb, "mf1045", "RGLgAp", "RG LgTruck AM PCE", 0)
        util.initmat(eb, "mf1046", "RGHvAp", "RG HvTruck AM PCE", 0)
        util.initmat(eb, "mf1047", "CBLgMp", "CB LgTruck MD PCE", 0)
        util.initmat(eb, "mf1048", "CBHvMp", "CB HvTruck MD PCE", 0)
        util.initmat(eb, "mf1049", "IRLgMp", "IR LgTruck MD PCE", 0)
        util.initmat(eb, "mf1050", "IRHvMp", "IR HvTruck MD PCE", 0)
        util.initmat(eb, "mf1051", "APHvMp", "AP HvTruck MD PCE", 0)
        util.initmat(eb, "mf1052", "RGLgMp", "RG LgTruck MD PCE", 0)
        util.initmat(eb, "mf1053", "RGHvMp", "RG HvTruck MD PCE", 0)

        specs = []
        # AM LGV
        specs.append(util.matrix_spec("mf1040", "mf1002*ms130"))
        specs.append(util.matrix_spec("mf1042", "mf1012*ms130"))
        specs.append(util.matrix_spec("mf1045", "mf1035*ms130"))
        # AM HGV
        specs.append(util.matrix_spec("mf1041", "mf1005*ms131"))
        specs.append(util.matrix_spec("mf1043", "mf1013*ms131"))
        specs.append(util.matrix_spec("mf1044", "mf1021*ms131"))
        specs.append(util.matrix_spec("mf1046", "mf1037*ms131"))
        # MD LGV
        specs.append(util.matrix_spec("mf1047", "mf1003*ms130"))
        specs.append(util.matrix_spec("mf1049", "mf1014*ms130"))
        specs.append(util.matrix_spec("mf1052", "mf1036*ms130"))
        # MD HGV
        specs.append(util.matrix_spec("mf1048", "mf1006*ms131"))
        specs.append(util.matrix_spec("mf1050", "mf1015*ms131"))
        specs.append(util.matrix_spec("mf1051", "mf1022*ms131"))
        specs.append(util.matrix_spec("mf1053", "mf1038*ms131"))

        # Aggregate total LGV and HGV vehicle demand
        specs.append(util.matrix_spec("mf980", "mf1002 + mf1012 + mf1035"))
        specs.append(util.matrix_spec("mf981", "mf1005 + mf1013 + mf1021 + mf1037"))
        specs.append(util.matrix_spec("mf982", "mf1003 + mf1014 + mf1036"))
        specs.append(util.matrix_spec("mf983", "mf1006 + mf1015 + mf1022 + mf1038"))
        util.compute_matrix(specs)
