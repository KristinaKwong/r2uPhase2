##---------------------------------------------------------------------
##--TransLink Phase 2.2 Regional Transportation Model
##--
##--Path: translink.emme.example (this path should match the namespace in the RTM toolbox)
##--Purpose: Provide Python Style Examples (a short description of the tools purpose)
##---------------------------------------------------------------------
import inro.modeller as _m # CodingStyle: always import this as _m
import traceback as _traceback

class Example(_m.Tool()):
    # a message used to return run information in the Modeller UI (see run())
    tool_run_msg = _m.Attribute(unicode)

    # Reserved Variable Names:
    # util - an instance of the translink.emme.util tool
    # specs - a list of matrix specifications
    # eb - an emmebank object, usually produced from the current project: _m.Modeller().emmebank
    def page(self):
        # Prefer to initialize the PageBuilder attributes one-per line rather than
        # a call to the multi-argument constructor method
        pb = _m.ToolPageBuilder(self)
        pb.title = "Translink Utility Toolbox"
        pb.description = "Collection of Utility Methods for Model Execution"
        pb.branding_text = "TransLink"
        # If the tool is not intended to be run interactively, set runnable = False to suppress
        # the rendering of the "RUN" button in the Modeller UI. You do not need to define a run()
        # method if runnable = False.
        # pb.runnable = False

        return pb.render()

    # The run method is fairly standardized, all real model work should be performed in __call__
    def run(self):
        self.tool_run_msg = ""
        try:
            # Pass any required arguments to the __call__ method, usually the current emmebank is an argument
            # Other arguments could be prompted for the in the Modeller UI and passed here.

            # Call the main method for the tool
            self.__call__(_m.Modeller().emmebank)

            # Set a success message and display
            self.tool_run_msg = _m.PageBuilder.format_info("Tool complete")
        except Exception, e:
            self.tool_run_msg = _m.PageBuilder.format_exception(e, _traceback.format_exc(e))

    # Modeller tools should have all of the model logic contained in this method to allow it
    # to be used from the Modeller UI and the python prompt, or other tools explcitly pass in the
    # emmebank to be operated on where needed
    #
    # At a minimum, the __call__ method should be decorated with a logbook_trace to assist in tracing
    # the model in the logbook. This will get registered if called from another model procedure, or from
    # an interative session. Consider the optional save_arguments = True if your tool takes user input to
    # ensure useful information in the logbook.
    @_m.logbook_trace("Example Tool", save_arguments = True)
    def __call__(self, eb):
        pass

    # Prefer using instance methods over class methods (self)
    def function_example(self):
        pass

    # Examples of using the matrix calculation utilities
    # Also annotate major subroutines to assist model tracing, it is not required to
    @_m.logbook_trace("Example Tool - Major Section")
    def calculation_example(self):
        # CodingStyle: always use the variable util for this tool at the beginning of the method
        util = _m.Modeller().tool("translink.emme.util")

        # Single calculation
        # The order of the matrix_spec method is meant to follow the assignemtn operator
        # the below is effectively mo01 = mo99
        spec = util.matrix_spec("mo01", "mo99")
        util.compute_matrix(spec)

        # Multiple calculations
        # Use the variable name "specs" to denote a list of matrix specifications and initialize it
        # to define a block of calculation
        specs = []
        for i in range(1, 500):
            # a very long list of calculations setting mo1-mo499 to all equal mo500
            specs.append(util.matrix_spec("mo%d" % i, "mo500"))
        # Pass the list of matrix specs to the computation module, notice how the specs variable
        # is initialized at the same indentation level as the call to compute_matrix, this forms
        # a rough "paragraph" of code - a comment at the beginning will help the reader greatly
        util.compute_matrix(specs)

        # Start a new calculation - using matrix constraints
        specs = []
        for i in range(1, 10):
            spec = util.matrix_spec("mo%d" % i, "mo99")
            # see the details of the constraints schema in the EMME documentation
            spec["constraint"]["by_value"] = {"od_values": "mf158", "interval_min": 0, "interval_max": 0, "condition": "EXCLUDE"}
            spec["constraint"]["by_zone"] = {"origins": "GY1", "destinations": None}

            # If performing a calculation that aggregates
            spec["aggregation"] = {"origins": "+", "destinations": ".max."}

            specs.append(spec)
        util.compute_matrix(specs)
