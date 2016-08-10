##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.stage5.step10.externaltruck
##--Purpose: This module generates external light and heavy truck matrices
##--         Regression functions are used to generate base and future demand
##--         Trip Distribution is conducted using 1999 Truck O-D survey
##---------------------------------------------------------------------
import inro.modeller as _m
import os
import traceback as _traceback

# Regression coefficients:

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

CBL11=446.0
CBH11=3267.0
ExL11=1579.0
ExH11=3718.0

class ExternalTruckModel(_m.Tool()):
    tool_run_msg = _m.Attribute(unicode)

    def page(self):
        pb = _m.ToolPageBuilder(self)
        pb.title = "External Truck Trips Model"
        pb.description = "Generates base/future forecasts for external light and heavy trucks trips"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        return pb.render()

    def run(self):
        try:
            self.__call__(_m.Modeller().emmebank, 2011)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool completed")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    @_m.logbook_trace("External Truck Trips Model")
    def __call__(self, eb, Year):
        # Call Modules of External Model
        self.CrossBorder(eb, Year) # Import Cascade Cross-Border Matrices
        self.TripGeneration(Year)
        self.TripDistribution()
        self.TimeSlicing()

    @_m.logbook_trace("Import Cascade Cross-Border Matrices")
    def CrossBorder(self, eb, Year):
        util = _m.Modeller().tool("translink.emme.util")

        process = _m.Modeller().tool("inro.emme.data.matrix.matrix_transaction")
        root_directory = util.get_input_path(eb)

        util.delmat(eb, "mf1001")
        util.delmat(eb, "mf1002")
        util.delmat(eb, "mf1003")
        util.delmat(eb, "mf1004")
        util.delmat(eb, "mf1005")
        util.delmat(eb, "mf1006")
        matrix_file1 = os.path.join(root_directory, "TruckBatchFiles", str(Year)+"CrossBorderv1.txt")
        process(transaction_file=matrix_file1, throw_on_error=True)

        matrix_file2 = os.path.join(root_directory, "TruckBatchFiles", "IRBatchIn.txt")
        process(transaction_file=matrix_file2, throw_on_error=True)

        util.initmat(eb, "ms151", "ExLgC1", "Cross Border Calc 1", 0)
        util.initmat(eb, "ms152", "ExHvC2", "Cross Border Calc 2", 0)

        specs = []

        spec = util.matrix_spec("ms151", "mf1001")
        spec["aggregation"] = {"origins": "+", "destinations": "+"}
        specs.append(spec)

        spec = util.matrix_spec("ms152", "mf1004")
        spec["aggregation"] = {"origins": "+", "destinations": "+"}
        specs.append(spec)

        util.compute_matrix(specs)

    @_m.logbook_trace("Trip Generation")
    def TripGeneration(self, Year):
        util = _m.Modeller().tool("translink.emme.util")
        # Inputs: Regression Functions and directional factors
        # Outputs: 24 hours trip generation - mo4,mo6,md404,md406 (Light From, Heavy From, Light To, Heavy To)

        ## Adjustments

        IB_Split=[0.5,0.46,0.5] # IB=Towards CBD; IB-OB: Heavy East=0.5, Light East=0.46, All Trucks West=0.5
        Hw1_Split=[0.84,0.85] # Split between Highway 1 and 7 in East: Heavy=0.84, Light=0.85
        TsawassenSplit=0.7
        Wkd_Factor=[1.357,1.102,1.590,1.263,1.184] # Factor to convert from Avg Quarter Monthly Traffic to Typical Fall weekday (East Heavy, East Light, Trucks West)
        TruckConFact=0.35 # % Light Truck in West Area
        Quarter=4

        GDP2011=172696
        GDP2030=257458.98
        GDP2045=331079.67
        if Year==2011:
            BC_GDP=GDP2011
            NGrowth1=1
            NGrowth2=1

        if Year==2030:

            BC_GDP=GDP2030
            NGrowth1=1.2
            NGrowth2=1.2

        if Year==2045:

            BC_GDP=GDP2045
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
                         NorthHeavyTrucks*Wkd_Factor[3]
                           ]

        HeavyTrucksTo=  [EastHeavyTrucks*(1-IB_Split[0])*(1-Hw1_Split[0])*Wkd_Factor[0],
                         EastHeavyTrucks*(1-IB_Split[0])*(Hw1_Split[0])*Wkd_Factor[0],
                         WestTrucks*(1-IB_Split[2])*TsawassenSplit*Wkd_Factor[2]*(1-TruckConFact),
                         WestTrucks*(1-IB_Split[2])*(1-TsawassenSplit)*Wkd_Factor[2]*(1-TruckConFact),
                         NorthHeavyTrucks*Wkd_Factor[3]
                           ]

        LightTrucksFrom=[EastLightTrucks*(IB_Split[1])*(1-Hw1_Split[1])*Wkd_Factor[1],
                         EastLightTrucks*(IB_Split[1])*(Hw1_Split[1])*Wkd_Factor[1],
                         WestTrucks*(IB_Split[2])*TsawassenSplit*Wkd_Factor[2]*(TruckConFact),
                         WestTrucks*(IB_Split[2])*(1-TsawassenSplit)*Wkd_Factor[2]*(TruckConFact),
                         NorthLightTrucks*Wkd_Factor[4]]


        LightTrucksTo= [EastLightTrucks*(1-IB_Split[1])*(1-Hw1_Split[1])*Wkd_Factor[1],
                        EastLightTrucks*(1-IB_Split[1])*(Hw1_Split[1])*Wkd_Factor[1],
                        WestTrucks*(1-IB_Split[2])*TsawassenSplit*Wkd_Factor[2]*(TruckConFact),
                        WestTrucks*(1-IB_Split[2])*(1-TsawassenSplit)*Wkd_Factor[2]*(TruckConFact),
                        NorthLightTrucks*Wkd_Factor[4]
                           ]

        matrixlist=["mo1001","mo1002","md201","md202"]

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

        self.AdjustInterCrossBorder("mf1001", "mo1001", "md201")
        self.AdjustInterCrossBorder("mf1004", "mo1002", "md202")

    @_m.logbook_trace("Adjust Inter Regional mos and mds with Cross-Border mos and mds")
    def AdjustInterCrossBorder(self, matrix1, matrix2, matrix3):
        util = _m.Modeller().tool("translink.emme.util")
        #   Adjusts Inter-regional mo and md totals by subtracting Cross-border mo/mds with inter-regional zone end

        specs = []

        spec = util.matrix_spec("mo1003", matrix1)
        spec["constraint"]["by_zone"] = {"origins": "1;2;8;10;11", "destinations": None}
        spec["aggregation"] = {"origins": None, "destinations": "+"}
        specs.append(spec)

        spec = util.matrix_spec("md203", matrix1)
        spec["constraint"]["by_zone"] = {"origins": None, "destinations": "1;2;8;10;11"}
        spec["aggregation"] = {"origins": "+", "destinations": None}
        specs.append(spec)

        spec = util.matrix_spec(matrix2, "((%s-mo1003).max.0)" % matrix2)
        specs.append(spec)

        spec = util.matrix_spec(matrix3, "((%s-md203).max.0)" % matrix3)
        specs.append(spec)

        util.compute_matrix(specs)

    @_m.logbook_trace("Trip Distribution")
    def TripDistribution(self):
        util = _m.Modeller().tool("translink.emme.util")
        ## Distribute External mo and md trips based on 1999 O-D Survey
        # Inputs: mo4, mo6, md404, md406, mf182 (O-D Survey Light Trucks Distribution), mf183 (O-D Survey Heavy Truck Distribution)
        # Outputs: mf184, mf185 (24 hour Light Truck O-D, 24 hour Heavy Truck O-D)

        specs = []

        spec = util.matrix_spec("mf1010", "mo1001*mf1008+md201*mf1008")
        specs.append(spec)

        spec = util.matrix_spec("mf1011", "mo1002*mf1009+md202*mf1009")
        specs.append(spec)

        util.compute_matrix(specs)

    @_m.logbook_trace("Time Slicing")
    def TimeSlicing(self):
        util = _m.Modeller().tool("translink.emme.util")
        ## Time Slice 24 hour demands to AM and MD peak hour volumes
        # Inputs: mf184, mf185, Time Slice Factors from Screenline volumes
        # Outputs: Light AM, Light MD, Heavy AM, Heavy MD - mf186, mf188, mf187, mf189

# IB                 Light Trucks AM            Light Trucks MD               Heavy Trucks AM         Heavy Trucks MD
        FactorIB=[[0.05868,0.04086,0.05086],[0.05868,0.09194,0.10426],[0.03811,0.09500,0.02912],[0.07470,0.09866,0.11649]]

# OB                 Light Trucks AM            Light Trucks MD               Heavy Trucks AM         Heavy Trucks MD
        FactorOB=[[0.03613,0.02054,0.11882],[0.04517,0.1027,0.07505], [0.04328,0.05253,0.10976],[0.08743,0.10507,0.08537]]


        ConstraintList=[[1,2],[8,10],[11]]

                    ## LightAM, LightMD,HeavyAM, HeavyMD
        Matrix_List = ["mf1012","mf1014","mf1013","mf1015"]
        TripDistList= ["mf1010", "mf1011"]

        for i in range (len(TripDistList)) :
            for j in range (int((len(FactorIB)/2))):
                for k in range (len(FactorIB[j])):
                    spec = util.matrix_spec("", TripDistList[i]+"*"+str(FactorIB[2*i+j][k]))
                    for l in range (0, len(ConstraintList[k])):
                        spec["result"] = Matrix_List[2*i+j]
                        spec["constraint"]["by_zone"] = {"origins": str(ConstraintList[k][l]), "destinations": None}
                        util.compute_matrix(spec)

        for i in range (len(TripDistList)) :
            for j in range (int((len(FactorIB)/2))):
                for k in range (len(FactorOB[j])):
                    spec = util.matrix_spec("", str(TripDistList[i])+"*"+str(FactorOB[2*i+j][k]))
                    for l in range (0, len(ConstraintList[k])):
                        spec["result"] = Matrix_List[2*i+j]
                        spec["constraint"]["by_zone"] = {"origins": None, "destinations": str(ConstraintList[k][l])}
                        util.compute_matrix(spec)
