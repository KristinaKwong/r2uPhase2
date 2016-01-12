import inro.modeller as _m
import inro.emme as _emme
import os

class Util(_m.Tool()):
	tool_run_msg = _m.Attribute(unicode)

	def page(self):
		start_path = os.path.dirname(_m.Modeller().emmebank.path)

		pb = _m.ToolPageBuilder(self)
		pb.title = "Translink Utility Toolbox"
		pb.description = "Collection of Utility Methods for Model Execution"
		pb.branding_text = "TransLink"

		if self.tool_run_msg:
			pb.add_html(self.tool_run_msg)

		return pb.render()

	def run(self):
		pass

	def __call__(self):
		pass

	def initmat(self, eb, mat_id, name, description, value=0):
		mat = eb.matrix(mat_id)
		if mat:
			mat.read_only = False
			mat.initialize(value)
		else:
			mat = eb.create_matrix(mat_id, value)

		mat.name = name
		mat.description = description
		return mat

	def delmat(self, eb, mat_id):
		mat = eb.matrix(mat_id)
		if mat:
			mat.read_only = False
		eb.delete_matrix(mat_id)
