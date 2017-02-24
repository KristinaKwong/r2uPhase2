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

        self.asia_pacific(eb, Year)

        self.regional(eb)

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

    @_m.logbook_trace("Asia Pacific Demand Market")
    def asia_pacific(self, eb, Year):
        util = _m.Modeller().tool("translink.util")

        #Batch input Asia Pacific matrix from TruckBatchFiles (gg ensemble format)
        util.delmat(eb, "mf8030")
        util.delmat(eb, "mf8031")
        util.delmat(eb, "mf8032")
        util.delmat(eb, "mf8033")
        process = _m.Modeller().tool("inro.emme.data.matrix.matrix_transaction")
        root_directory = util.get_input_path(eb)
        matrix_file = os.path.join(root_directory, "TruckBatchFiles", str(Year)+"AsiaPacificv1.txt")
        process(transaction_file=matrix_file, throw_on_error=True)

        util.delmat(eb, "mo8030")
        matrix_file = os.path.join(root_directory, "TruckBatchFiles", "PMVActivity.txt")
        util.read_csv_momd(eb, matrix_file)

        #Distribute Asia Pacific matrix for "Other locations" based on non-retail employment
        util.initmat(eb, "ms8030", "gg27nonret", "non-retail employment in gg27", 0)
        util.initmat(eb, "mf8040", "APHv24", "AP HvTrucks Daily Trips", 0)
        util.initmat(eb, "mf8041", "APHvAM", "AP HvTrucks AM Trips", 0)
        util.initmat(eb, "mf8042", "APHvMD", "AP HvTrucks MD Trips", 0)
        util.initmat(eb, "mf8043", "APHvPM", "AP HvTrucks PM Trips", 0)

        specs = []

        spec = util.matrix_spec("ms8030", "(mo20-mo24)*(gy(p).lt.13)")
        spec["constraint"]["by_zone"] = {"origins": "gg27", "destinations": None}
        spec["aggregation"] = {"origins": "+", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("mo8030", "(mo20-mo24)/ms8030*(gy(p).lt.13)")
        spec["constraint"]["by_zone"] = {"origins": "gg27", "destinations": None}
        specs.append(spec)

        specs.append(util.matrix_spec("mf8040", "mf8030*mo8030*mo8030'"))
        specs.append(util.matrix_spec("mf8041", "mf8031*mo8030*mo8030'"))
        specs.append(util.matrix_spec("mf8042", "mf8032*mo8030*mo8030'"))
        specs.append(util.matrix_spec("mf8043", "mf8033*mo8030*mo8030'"))
        util.compute_matrix(specs)

    @_m.logbook_trace("Regional Demand Market")
    def regional(self, eb):
        util = _m.Modeller().tool("translink.util")

        util.delmat(eb, "mf8050")
        util.delmat(eb, "mf8051")
        util.delmat(eb, "mf8052")
        util.delmat(eb, "mf8053")
        util.delmat(eb, "mf8054")
        util.delmat(eb, "mf8055")
        process = _m.Modeller().tool("inro.emme.data.matrix.matrix_transaction")
        root_directory = util.get_input_path(eb)
        matrix_file1 = os.path.join(root_directory, "TruckBatchFiles", "RGBatchIn.txt")
        process(transaction_file=matrix_file1, throw_on_error=True)

        util.initmat(eb, "ms8050", "RGphAM", "Rg Truck Peak Hour Factor AM", .26000)
        util.initmat(eb, "ms8051", "RGphMD", "Rg Truck Peak Hour Factor MD", .24100)
        util.initmat(eb, "ms8052", "RGphPM", "Rg Truck Peak Hour Factor PM", .24100)

        self.regional_generation(eb)
        self.regional_distribution(eb)

    def regional_generation(self, eb):
        util = _m.Modeller().tool("translink.util")

        util.initmat(eb, "mo8050", "RGLgPr", "Rg Daily LgTruck Trip Prod", 0)
        util.initmat(eb, "md8050", "RGLgAt", "Rg Daily LgTruck Trip Att", 0)
        util.initmat(eb, "mo8051", "RGHvPr", "Rg Daily HvTruck Trip Prod", 0)
        util.initmat(eb, "md8051", "RGHvAt", "Rg Daily HvTruck Trip Att", 0)

        specs = []

        # Compute light truck prod/attr (Non-CBD, CBD)
        spec = util.matrix_spec("mo8050", "((.0714)*mo21+(.138)*mo23+.1539*mo24+.0496*(mo22+mo25)+.017*mo27+.0981*mo26+.0077*mo10)*1.0/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy1-gy14", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("mo8050", "((.016)*mo21+(0.044)*mo23+.0845*mo24+.0163*(mo22+mo25)+.0190*mo27+.0645*mo26+.0037*mo10)*1.0/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy2;gy13-gy14", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("mo8050", "((.1235)*mo21+(.277)*mo23+.1390*mo24+.0176*(mo22+mo25)+.0233*mo27+.1596*mo26+.0216*mo10)*1.0/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy1;gy4;gy11", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("mo8050", "(.0378*mo20)*1.0/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy3", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("mo8050", "mo8050*0.75/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy3;gy4;gy5", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("mo8050", "mo8050*1/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy11-gy14", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("md8050", "mo8050'")
        specs.append(spec)

        # Compute heavy truck prod/attr (Non-CBD, CBD)
        spec = util.matrix_spec("mo8051", "((.081708)*mo21+(.049246)*mo23+.03294*mo24+.016721*(mo22+mo25)+.002417*mo27+.046216*mo26+.0006*mo10)*1.0/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy1-gy14", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("mo8051", "((.0534886)*mo21+(.0430371)*mo23+.0277756*mo24+.00141249*(mo22+mo25)+.00362843*mo27+.02071*mo26+.0006*mo10)*1.0/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy4;gy5", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("mo8051", "((.079903)*mo21+(.140189)*mo23+.035748*mo24+.011378*(mo22+mo25)+.006965*mo27+.067798*mo26+.0016*mo10)*1.0/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy6;gy8;gy11;gy12", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("mo8051", "(.0059*mo20)*1.0/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy3", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("mo8051", "mo8051*1/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy1;gy2;gy4-gy14", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("mo8051", "mo8051*1.1/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy7;gy8", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("mo8051", "mo8051*1.25/1+ .00001")
        spec["constraint"]["by_zone"] = {"origins": "gy9;gy10;gy12;gy14", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec("md8051", "mo8051'")
        specs.append(spec)

        util.compute_matrix(specs)

    def regional_distribution(self, eb):
        util = _m.Modeller().tool("translink.util")

        # Trip Distribution - Compute Friction Factors
        util.initmat(eb, "mf8060", "RGLgFc", "Rg Lg Truck Impedance", 0)
        util.initmat(eb, "mf8061", "RGHvFc", "Rg Hv Truck Impedance", 0)

        specs = []

        spec = util.matrix_spec("mf8060", "exp(-.09*mfMdSovTimeVOT4)")
        spec["constraint"]["by_zone"] = {"origins": "gy1-gy14", "destinations": "gy1-gy14"}
        specs.append(spec)

        spec = util.matrix_spec("mf8060", "exp(-.13*mfMdSovTimeVOT4)")
        spec["constraint"]["by_zone"] = {"origins": "gy1-gy11", "destinations": "gy1-gy11"}
        specs.append(spec)

        spec = util.matrix_spec("mf8060", "exp(-.3*mfMdSovTimeVOT4)")
        spec["constraint"]["by_zone"] = {"origins": "gy1-gy4;gy7", "destinations": "gy1-gy4;gy7"}
        specs.append(spec)

        spec = util.matrix_spec("mf8061", "exp(-.07*mfMdSovTimeVOT4)")
        spec["constraint"]["by_zone"] = {"origins": "gy1-gy14", "destinations": "gy1-gy14"}
        specs.append(spec)

        spec = util.matrix_spec("mf8061", "exp(-.11*mfMdSovTimeVOT4)")
        spec["constraint"]["by_zone"] = {"origins": "gy3", "destinations": "gy1-gy14"}
        specs.append(spec)

        spec = util.matrix_spec("mf8061", "exp(-.11*mfMdSovTimeVOT4)")
        spec["constraint"]["by_zone"] = {"origins": "gy1-gy14", "destinations": "gy3"}
        specs.append(spec)

        util.compute_matrix(specs)

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
