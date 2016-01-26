##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.stage5.step10.externaltruck
##--Purpose: This module generates external light and heavy truck matrices
##--         Regression functions are used to generate base and future demand
##--         Trip Distribution is conducted using 1999 Truck O-D survey
##---------------------------------------------------------------------
import inro.modeller as _modeller
import os
import traceback as _traceback
from datetime import datetime
eb = _modeller.Modeller().emmebank

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

class ExternalTruckModel(_modeller.Tool()):


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

    #    Analysis_Year = _modeller.Attribute(int)
    #    GDP_CAGR = _modeller.Attribute(float)
    #    Quarter = _modeller.Attribute(int)
    tool_run_msg = _modeller.Attribute(unicode)

    def page(self):
        pb = _modeller.ToolPageBuilder(self)
        pb.title = "External Truck Trips Model"
        pb.description = "Generates base/future forecasts for external light and heavy trucks trips"
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)


        return pb.render()

    def run(self):
        print " Run External Truck Trips Model: " + str(datetime.now().strftime('%H:%M:%S'))
        ##        User start
        self.tool_run_msg = ""
        #GDP FOrecasts: 2011, 2031, 2045 in Real 2009 $ Value

        try:
            self.__call__(Year)
            run_msg = "Tool completed"
            self.tool_run_msg = _modeller.PageBuilder.format_info(run_msg)
        except Exception, e:
            self.tool_run_msg = _modeller.PageBuilder.format_exception(e, _traceback.format_exc(e))

    def __call__(self,Year, Sensitivity, ExtGrowth1,ExtGrowth2, CascadeGrowth1, CascadeGrowth2):

        with _modeller.logbook_trace("External Truck Trips Model"):

        # Call Modules of External Model
            self.CrossBorder(Year, Sensitivity, CascadeGrowth1, CascadeGrowth2) # Import Cascade Cross-Border Matrices
            self.TripGeneration(Year, Sensitivity, ExtGrowth1, ExtGrowth2)
            self.TripDistribution()
            self.TimeSlicing()

    def CrossBorder(self, Year, Sensitivity, CascadeGrowth1, CascadeGrowth2):

        with _modeller.logbook_trace("Import Cascade Cross-Border Matrices"):

            NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
            compute_matrix = _modeller.Modeller().tool(NAMESPACE)
            process = _modeller.Modeller().tool("inro.emme.data.matrix.matrix_transaction")
            root_directory = os.path.dirname(_modeller.Modeller().emmebank.path) + "\\"
            matrix_file1 = os.path.join(root_directory, "TruckBatchFiles", str(Year)+"CrossBorderv1.txt")
            matrix_file2 = os.path.join(root_directory, "TruckBatchFiles", "IRBatchIn.txt")
            process(transaction_file=matrix_file1, throw_on_error=True)
            process(transaction_file=matrix_file2, throw_on_error=True)


            CrossBorderSpec=self.spec_as_dict
            CrossBorderSpec['expression'] = "mf1001"
            CrossBorderSpec['result']='ms151'
            CrossBorderSpec['aggregation']['origins']="+"
            CrossBorderSpec['aggregation']['destinations']="+"
            compute_matrix(CrossBorderSpec)

            CrossBorderSpec['expression'] = "mf1004"
            CrossBorderSpec['result']='ms152'
            compute_matrix(CrossBorderSpec)

            self.ResetSpec(CrossBorderSpec)

            CBLg = eb.matrix("ms151")
            CBHv=eb.matrix("ms152")
            CBLgVal=CBLg.data
            CBHvVal=CBHv.data
            ## Determine growth based on sensitivity inputs
            if Sensitivity=="N":
                RatioL=1
                RatioH=1

            else:

                CAGRLightI=(CBLgVal/CBL11)**(1/float(Year-2011))
                CAGRHeavyI=(CBHvVal/CBH11)**(1/float(Year-2011))
                RatioL=(CBLgVal/CAGRLightI**(Year-2030)*((1+CascadeGrowth1/100)/(CAGRLightI))**(2030-2011)*(1+CascadeGrowth2/100)**(Year-2030))/CBLgVal
                RatioH=(CBHvVal/CAGRHeavyI**(Year-2030)*((1+CascadeGrowth1/100)/(CAGRHeavyI))**(2030-2011)*(1+CascadeGrowth2/100)**(Year-2030))/CBHvVal



            MatrixList=["mf1001","mf1002", "mf1003", "mf1004", "mf1005", "mf1006"]

            for i in range(len(MatrixList)):
                if i<3:
                    CrossBorderSpec['expression'] = MatrixList[i]+"*"+str(RatioL)
                else:
                    CrossBorderSpec['expression'] = MatrixList[i]+"*"+str(RatioH)
                CrossBorderSpec['result']=MatrixList[i]
                compute_matrix(CrossBorderSpec)



    def TripGeneration(self,Year, Sensitivity, ExtGrowth1, ExtGrowth2):

    # Inputs: Regression Functions and directional factors
    # Outputs: 24 hours trip generation - mo4,mo6,md404,md406 (Light From, Heavy From, Light To, Heavy To)

        with _modeller.logbook_trace("Trip Generation"):

            NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"

            compute_matrix = _modeller.Modeller().tool(NAMESPACE)

            TripGenSpec=self.spec_as_dict

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
            ## Determine growth based on sensitivity inputs
            if Sensitivity=="N":
                RatioL=1
                RatioH=1

            else:
                CAGRLightI=(LightTruckSum/ExL11)**(1/float(Year-2011))
                CAGRHeavyI=(HeavyTruckSum/ExH11)**(1/float(Year-2011))
                RatioL=(LightTruckSum/CAGRLightI**(Year-2030)*((1+ExtGrowth1/100)/(CAGRLightI))**(2030-2011)*(1+ExtGrowth2/100)**(Year-2030))/LightTruckSum
                RatioH=(HeavyTruckSum/CAGRHeavyI**(Year-2030)*((1+ExtGrowth1/100)/(CAGRHeavyI))**(2030-2011)*(1+ExtGrowth2/100)**(Year-2030))/HeavyTruckSum


            HeavyTrucksFrom=[RatioH*EastHeavyTrucks*(IB_Split[0])*(1-Hw1_Split[0])*Wkd_Factor[0],
                             RatioH*EastHeavyTrucks*(IB_Split[0])*(Hw1_Split[0])*Wkd_Factor[0],
                               RatioH*WestTrucks*(IB_Split[2])*TsawassenSplit*Wkd_Factor[2]*(1-TruckConFact),
                               RatioH*WestTrucks*(IB_Split[2])*(1-TsawassenSplit)*Wkd_Factor[2]*(1-TruckConFact),
                               RatioH*NorthHeavyTrucks*Wkd_Factor[3]
                               ]

            HeavyTrucksTo=  [RatioH*EastHeavyTrucks*(1-IB_Split[0])*(1-Hw1_Split[0])*Wkd_Factor[0],
                               RatioH*EastHeavyTrucks*(1-IB_Split[0])*(Hw1_Split[0])*Wkd_Factor[0],
                               RatioH*WestTrucks*(1-IB_Split[2])*TsawassenSplit*Wkd_Factor[2]*(1-TruckConFact),
                               RatioH*WestTrucks*(1-IB_Split[2])*(1-TsawassenSplit)*Wkd_Factor[2]*(1-TruckConFact),
                               RatioH*NorthHeavyTrucks*Wkd_Factor[3]
                               ]

            LightTrucksFrom=[RatioL*EastLightTrucks*(IB_Split[1])*(1-Hw1_Split[1])*Wkd_Factor[1],
                              RatioL*EastLightTrucks*(IB_Split[1])*(Hw1_Split[1])*Wkd_Factor[1],
                               RatioL*WestTrucks*(IB_Split[2])*TsawassenSplit*Wkd_Factor[2]*(TruckConFact),
                               RatioL*WestTrucks*(IB_Split[2])*(1-TsawassenSplit)*Wkd_Factor[2]*(TruckConFact),
                               RatioL*NorthLightTrucks*Wkd_Factor[4]]


            LightTrucksTo= [RatioL*EastLightTrucks*(1-IB_Split[1])*(1-Hw1_Split[1])*Wkd_Factor[1],
                               RatioL*EastLightTrucks*(1-IB_Split[1])*(Hw1_Split[1])*Wkd_Factor[1],
                               RatioL*WestTrucks*(1-IB_Split[2])*TsawassenSplit*Wkd_Factor[2]*(TruckConFact),
                               RatioL*WestTrucks*(1-IB_Split[2])*(1-TsawassenSplit)*Wkd_Factor[2]*(TruckConFact),
                               RatioL*NorthLightTrucks*Wkd_Factor[4]
                               ]



            matrixlist=['mo1001','mo1002','md201','md202']

            TruckList=[LightTrucksFrom,HeavyTrucksFrom, LightTrucksTo ,HeavyTrucksTo]

            ExtZoneList=[1,2,8,10,11] #[1: Highway 7, 2: Highway 2, 8: Tsawwassen, 10: HoreshoeBay, 11: Highway 99]


            for i in range (0, len(matrixlist)) :
                for j in range(0, len(ExtZoneList)):
                    TripGenSpec['expression'] = str(TruckList[i][j])
                    if i<2:
                        TripGenSpec['constraint']['by_zone']['origins'] = str(ExtZoneList[j])
                        TripGenSpec['constraint']['by_zone']['destinations'] = None
                    else:
                        TripGenSpec['constraint']['by_zone']['origins'] = None
                        TripGenSpec['constraint']['by_zone']['destinations'] = str(ExtZoneList[j])
                    TripGenSpec['result'] = matrixlist[i]
                    compute_matrix(TripGenSpec)
            self.ResetSpec(TripGenSpec)


            self.AdjustInterCrossBorder("mf1001","mo1001", "md201")
            self.AdjustInterCrossBorder("mf1004","mo1002", "md202")

    def AdjustInterCrossBorder(self, matrix1, matrix2, matrix3):

    #   Adjusts Inter-regional mo and md totals by subtracting Cross-border mo/mds with inter-regional zone end

        with _modeller.logbook_trace("Adjust Inter Regional mos and mds with Cross-Border mos and mds"):
            NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
            compute_matrix = _modeller.Modeller().tool(NAMESPACE)
            AdjustSpec=self.spec_as_dict
            ResultList=["mo1003","md203"]

            AdjustSpec['expression']= matrix1

            for i in range (2):
                if i==0:
                    AdjustSpec['constraint']['by_zone']['origins'] = "1 2 8 10 11"
                    AdjustSpec['constraint']['by_zone']['destinations'] = "*"
                    AdjustSpec['aggregation']['origins'] = None
                    AdjustSpec['aggregation']['destinations'] = "+"
                if i==1:
                    AdjustSpec['constraint']['by_zone']['origins'] = "*"
                    AdjustSpec['constraint']['by_zone']['destinations'] = "1 2 8 10 11"
                    AdjustSpec['aggregation']['origins'] = "+"
                    AdjustSpec['aggregation']['destinations'] = None


                AdjustSpec['result']=ResultList[i]
                compute_matrix(AdjustSpec)

            self.ResetSpec(AdjustSpec)

            AdjustSpec['expression']= "(("+matrix2+"-"+ResultList[0]+").max.0)"
            AdjustSpec['result']=matrix2
            compute_matrix(AdjustSpec)

            AdjustSpec['expression']= "(("+matrix3+"-"+ResultList[1]+").max.0)"
            AdjustSpec['result']=matrix3
            compute_matrix(AdjustSpec)


    def TripDistribution(self):

    ## Distribute External mo and md trips based on 1999 O-D Survey
    # Inputs: mo4, mo6, md404, md406, mf182 (O-D Survey Light Trucks Distribution), mf183 (O-D Survey Heavy Truck Distribution)
    # Outputs: mf184, mf185 (24 hour Light Truck O-D, 24 hour Heavy Truck O-D)

        with _modeller.logbook_trace("Trip Distribution"):

            NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
            compute_matrix = _modeller.Modeller().tool(NAMESPACE)
            TripDistSpec=self.spec_as_dict

            ResultList=['mf1010','mf1011']
            ExpressionList=['mo1001*mf1008+md201*mf1008','mo1002*mf1009+md202*mf1009']

            for i in range (2):
                TripDistSpec['expression'] = ExpressionList[i]
                TripDistSpec['result'] = ResultList[i]
                compute_matrix (TripDistSpec)

    def TimeSlicing(self):

    ## Time Slice 24 hour demands to AM and MD peak hour volumes
    # Inputs: mf184, mf185, Time Slice Factors from Screenline volumes
    # Outputs: Light AM, Light MD, Heavy AM, Heavy MD - mf186, mf188, mf187, mf189

        with _modeller.logbook_trace("Time Slicing"):
            NAMESPACE = "inro.emme.matrix_calculation.matrix_calculator"
            compute_matrix = _modeller.Modeller().tool(NAMESPACE)
            TimeSliceSpec=self.spec_as_dict

    # IB                 Light Trucks AM            Light Trucks MD               Heavy Trucks AM         Heavy Trucks MD
            FactorIB=[[0.05868,0.04086,0.05086],[0.05868,0.09194,0.10426],[0.03811,0.09500,0.02912],[0.07470,0.09866,0.11649]]

    # OB                 Light Trucks AM            Light Trucks MD               Heavy Trucks AM         Heavy Trucks MD
            FactorOB=[[0.03613,0.02054,0.11882],[0.04517,0.1027,0.07505], [0.04328,0.05253,0.10976],[0.08743,0.10507,0.08537]]


            ConstraintList=[[1,2],[8,10],[11]]

                        ## LightAM, LightMD,HeavyAM, HeavyMD
            Matrix_List = ['mf1012','mf1014','mf1013','mf1015']
            TripDistList= ['mf1010', 'mf1011']


            for i in range (len(TripDistList)) :
                for j in range (int((len(FactorIB)/2))):
                    for k in range (len(FactorIB[j])):
                        TimeSliceSpec['expression'] = TripDistList[i]+"*"+str(FactorIB[2*i+j][k])
                        for l in range (0, len(ConstraintList[k])):
                            TimeSliceSpec['constraint']['by_zone']['origins'] = str(ConstraintList[k][l])
                            TimeSliceSpec['constraint']['by_zone']['destinations'] = "*"
                            TimeSliceSpec['result'] = Matrix_List[2*i+j]
                            compute_matrix (TimeSliceSpec)

            TimeSliceSpec['constraint']['by_zone']['origins'] = "*"

            for i in range (len(TripDistList)) :
                for j in range (int((len(FactorIB)/2))):
                    for k in range (len(FactorOB[j])):
                        TimeSliceSpec['expression'] = str(TripDistList[i])+"*"+str(FactorOB[2*i+j][k])
                        for l in range (0, len(ConstraintList[k])):
                            TimeSliceSpec['constraint']['by_zone']['destinations'] = str(ConstraintList[k][l])
                            TimeSliceSpec['result'] = Matrix_List[2*i+j]
                            compute_matrix (TimeSliceSpec)

    def ResetSpec (self, SpecItems):

        SpecItems['constraint']['by_zone']['origins'] = None
        SpecItems['constraint']['by_zone']['destinations'] = None
        SpecItems['aggregation']['origins'] = None
        SpecItems['aggregation']['destinations'] = None
