##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
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
        pb = _m.ToolPageBuilder(self)
        pb.title = "Land Use Input Module"
        pb.description = "Enters land use based on specified file input."
        pb.branding_text = "TransLink"

        if self.tool_run_msg:
            pb.add_html(self.tool_run_msg)

        loc = os.path.dirname(_m.Modeller().emmebank.path)

        pb.add_select_file(tool_attribute_name="LandUse1",
                           window_type="file",
                           file_filter="*.csv",
                           start_path=loc + "/00_RUNMODEL/LandUse",
                           title="Select Input LandUse file 1: ",
                           note="File must be csv file.")

        pb.add_select_file(tool_attribute_name="LandUse2",
                           window_type="file",
                           file_filter="*.csv",
                           start_path=loc + "/00_RUNMODEL/LandUse",
                           title="Select Input LandUse file 2: ",
                           note="File must be csv file.")
        return pb.render()

    def run(self):
        self.tool_run_msg = ""
        try:
            self(_m.Modeller().emmebank, self.LandUse1, self.LandUse2)
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, error:
            self.tool_run_msg = _m.PageBuilder.format_exception(
                error, _traceback.format_exc(error))
            raise

    @_m.logbook_trace("Import land use data", save_arguments=True)
    def __call__(self, eb, file1, file2):
        self.read_file(eb, file1)
        self.read_file(eb, file2)

    @_m.logbook_trace("Reading File", save_arguments=True)
    def read_file(self, eb, file):
        util = _m.Modeller().tool("translink.emme.util")
        #Read data from file and check number of lines
        with open(file, "rb") as sourcefile:
            lines = list(csv.reader(sourcefile, skipinitialspace=True))

        # Validate that each line has the same number of caolumns as the first line
        valid_cols = len(lines[0])
        for num in range(len(lines)):
            if len(lines[num]) != valid_cols:
                raise Exception("File: %s Line: %d - expected %d columns, found %d" % (file, num + 1, valid_cols, len(lines[num])))

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
