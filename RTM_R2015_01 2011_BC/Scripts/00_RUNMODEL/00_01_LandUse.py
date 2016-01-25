##---------------------------------------------------------------------
##--TransLink Phase 3 Regional Transportation Model
##--
##--Path: translink.emme.stage1.step0.landuse
##--Purpose: input land use from external files
##---------------------------------------------------------------------
import inro.modeller as _m
import traceback as _traceback
import csv
import os

class InputLandUse(_m.Tool()):
    LandUse1 = _m.Attribute(unicode)
    LandUse2 = _m.Attribute(unicode)

    tool_run_msg = ""

    def page(self):
        loc = os.path.dirname(_m.Modeller().emmebank.path)
        pb = _m.ToolPageBuilder(self, title="Land Use Input Module")
        pb.title = "Import year-specific land use information to the databank"
        pb.description = """Enters land use based on specified file input.
                         """
        pb.branding_text = "TransLink"
        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        pb.add_select_file(tool_attribute_name="LandUse1",
                           window_type="file",
                           file_filter='*.csv',
                           start_path=loc + '/00_RUNMODEL/LandUse',
                           title="Select Input LandUse file 1: ",
                           note="File must be csv file.")

        pb.add_select_file(tool_attribute_name="LandUse2",
                           window_type="file",
                           file_filter='*.csv',
                           start_path=loc + '/00_RUNMODEL/LandUse',
                           title="Select Input LandUse file 2: ",
                           note="File must be csv file.")
        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            self(self.LandUse1, self.LandUse2)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, error:
            self.tool_run_msg = _m.PageBuilder.format_exception(
                error, _traceback.format_exc(error))
            raise

    @_m.logbook_trace("Import land use data", save_arguments=True)
    def __call__(self, file1, file2):
        init_mat = _m.Modeller().tool("inro.emme.data.matrix.init_matrix")
        # Define matrices for storage (must pre-exist)
        inputmats = []
        #Define matrices for POP04, POP512, POP1317, POP1824, POP2444, POP4564, POP65p, totpop
        inputmats.extend(['mo23', 'md21', 'md22', 'mo24', 'mo25', 'mo26', 'mo19', 'mo20'])
        #Define matrices for tothhs, hh1, hh2, hh3, hh4, Construction-Mfg, FIRE, TCU-Wholesale, Retail
        inputmats.extend(['mo01', 'mo50', 'mo51', 'mo52', 'mo53', 'md05', 'md06', 'md07', 'md08'])
        #Define matrices for Business-OtherServices, AccomFood-InfoCult, Health-Educat-PubAdmin, totemp
        inputmats.extend(['md09', 'md10', 'md11', 'md12'])
        #Define matrices for 250CS, 500CS, WPRK45, NWPRK45, bike_score
        inputmats.extend(['mo393', 'mo394', 'mo27', 'mo28', 'mo13'])

        with _m.logbook_trace("Initializing matrices to zero"):
            # TODO: create matrices if they do not already exist
            num_inits = len(inputmats)
            eb = _m.Modeller().emmebank
            for x in xrange(0, num_inits):
                inputval = eb.matrix(inputmats[x])
                init_mat(matrix=inputval, init_value=0)

        # TODO: change the file reading to use the normal design pattern
        with _m.logbook_trace("Read new matrices from csv file1 and file2"):
            #Read data from file and check number of lines
            with open(file1, 'rb') as mainpop:
                data1 = list(csv.reader(mainpop, skipinitialspace=True))
                data1 = [i for i in data1 if i]

            file = open(file1, 'r')
            getlines = file.readlines()
            file1size = len(getlines)
            file.close()
            #Repeat process for second land use file
            with open(file2, 'rb') as secondpop:
                data2 = list(csv.reader(secondpop, skipinitialspace=True))
                data2 = [j for j in data2 if j]
            file = open(file2, 'r')
            getlines = file.readlines()
            file2size = len(getlines)
            file.close()
            #Get number of matrices in each input file
            file1_matnum = len(data1[0]) - 1

            file2_matnum = len(data2[0]) - 1
            # TODO: create report with number of matrices imported
            #_m.logbook_write(file1_matnum)
            #_m.logbook_write(file2_matnum)

        with _m.logbook_trace("Copy numbers from first list into corresponding matrices"):
            #Assuming first column holds zone numbers, other columns hold matrix values in order above
            eb = _m.Modeller().emmebank
            #Input values from first file
            for x in xrange(0, file1_matnum):
                y = x + 1   #first column in matrix list corresponds to second column in data list, and so on
                active_mat = eb.matrix(inputmats[x])
                #change_matrix(matrix = active_mat,matrix_name=data1[0][y],matrix_description=data1[1][y])
                active_mat.name = data1[0][y]
                active_mat.description = data1[1][y]
                active_mat_data = active_mat.get_data()
                # TODO: create report on mactices imported
                #_m.logbook_write(inputmats[x])

                for z in xrange(2, file1size):
                    index = int(data1[z][0])
                    value = float(data1[z][y])
                    active_mat_data.set(index, value)
                    active_mat.set_data(active_mat_data)
                q = x     #preserve counter of matrix input list

        with _m.logbook_trace("Copy numbers from second list into corresponding matrices"):
            for x in xrange(0, file2_matnum):
                q = q + 1   #increment matrix input list counter
                y = x + 1   #first column in matrix list corresponds to second column in data list, and so on
                active_mat = eb.matrix(inputmats[q])
                #change_matrix(matrix = active_mat,matrix_name=data2[0][y],matrix_description=data2[1][y])
                active_mat.name = data2[0][y]
                active_mat.description = data2[1][y]
                active_mat_data = active_mat.get_data()
                # TODO: create report on mactices imported
                #_m.logbook_write(inputmats[q])
                for z in xrange(2, file2size):
                    index = int(data2[z][0])
                    if data2[z][y] == " -   " or data2[z][y] == "":
                        value = 0
                    else:
                        value = float(data2[z][y])
                    active_mat_data.set(index, value)
                    active_mat.set_data(active_mat_data)
