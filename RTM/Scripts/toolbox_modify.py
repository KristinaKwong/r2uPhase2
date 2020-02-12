#//////////////////////////////////////////////////////////////////////////////
#////                                                                       ///
#////                                                                       ///
#//// toolbox_modify.py                                                     ///
#////                                                                       ///
#////                                                                       ///
#////                                                                       ///
#//// Copyright 2014 INRO.                                                  ///
#////                                                                       ///
#//// Copyright (C) INRO, 2014. All rights reserved.                        ///
#//// The right to use and/or distribute this script, which employs         ///
#//// proprietary INRO programming interfaces, is granted exclusively       ///
#//// to Emme Licensees provided the following conditions are met:          ///
#//// 1.This script cannot be sold for a fee (but it can be used and        ///
#////   distributed without charge within consulting projects).             ///
#//// 2.The user is aware that this script is not a part of the Emme        ///
#////   software licence and there is no explicit or implied warranty       ///
#////   or support provided with this script.                               ///
#//// 3.This copyright notice must be preserved.                            ///
#////                                                                       ///
#//////////////////////////////////////////////////////////////////////////////
#////
#//// This script can be used to modify portions of the absolute paths
#//// in Modeller Toolboxes. The root of the paths can either be changed
#//// explicitly from one root to another using change_root_path(). Or,
#//// the root paths can be set to be the same as the root of the
#//// current directory of the toolbox using set_tools_to_current_root().
#//// The later is what is invoked if this script is run directly from
#//// the command-line.
#////
#//// This can be invoked from the command-line using:
#//// > python "path/to/toolbox_modify.py" "path/to/Scripts/toolbox.mtbx"
#////
#//// This assumes that the relevant toolbox scripts are found in
#//// the same directory (or sub-directories) as the toolbox, and
#//// that the toolbox directory is named "Scripts". If the later is
#//// not the case an alternate root directory may be specified
#//// as a second argument:
#//// > python "path/to/toolbox_modify.py" "path/to/toolbox.mtbx" Scripts
#////


import os
import sqlite3
import sqlite3.dbapi2 as _sql


class ToolboxWrap():
    headers = {'attributes': ('element_id', 'name', 'value'),
               'documents': ('document_id', 'title'),
               'elements': ('element_id', 'parent_id', 'document_id', 'tag', 'text', 'tail')}
    document_dict = {}
    element_dict = {}
    attribute_dict = {}

    def __init__(self, toolbox_path):
		self.toolbox_path = toolbox_path
		self.connection = _sql.connect(self.toolbox_path, isolation_level=None)
		self.cursor = self.connection.cursor()

		self.documents = self.connection.execute('select * from documents').fetchall()
		self.elements = self.connection.execute('select * from elements').fetchall()
		self.attributes = self.connection.execute('select * from attributes').fetchall()

		self.get_tables_as_dict()
		


    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.connection.close()

    def get_tables_as_dict(self):
        document_dict = {}
        for doc in self.documents:
            doc_dict = dict(zip(self.headers['documents'], doc))
            document_dict[doc_dict['document_id']] = doc_dict

        element_dict = {}
        for elem in self.elements:
            elem_dict = dict(zip(self.headers['elements'], elem))
            element_dict[elem_dict['element_id']] = elem_dict

        attribute_dict = {}
        for att in self.attributes:
            att_dict = dict(zip(self.headers['attributes'], att))
            attribute_dict.setdefault(att_dict['element_id'], {})
            attribute_dict[att_dict['element_id']][att_dict['name']] = att_dict['value']

        self.document_dict = document_dict
        self.element_dict = element_dict
        self.attribute_dict = attribute_dict

    def get_all_scripts(self):
        scripts = []
        for elem_id in self.element_dict.keys():
            script_path = self.attribute_dict[elem_id].get('script')
            if script_path is not None:
                scripts.append([elem_id, os.path.normpath(script_path)])
        return scripts

    def set_attribute(self, element_id, name, value):
        self.cursor.execute(
            "INSERT OR REPLACE INTO attributes(element_id, name, value) VALUES(?, ?, ?)",
            (element_id, name, value))


def change_root_path(toolbox_path, tools_root, new_tools_root):
    with ToolboxWrap(toolbox_path) as toolbox:
        tools_root = os.path.normpath(tools_root)
        new_root_path = os.path.normpath(new_tools_root)

        for element_id, script in toolbox.get_all_scripts():
            if not script.startswith(tools_root):
                raise Exception("Script path %s does not contain %s" % (script, tools_root))
            else:
                rel_path_script = os.path.relpath(script, tools_root)
                script_new_path = os.path.realpath(os.path.join(new_root_path, rel_path_script))
                print script, "changed to:\n", script_new_path

                if not os.path.exists(script_new_path):
                    raise Exception('New script path does not exist: %s' % script_new_path)
                toolbox.set_attribute(element_id, "script", script_new_path)


def set_tools_to_current_root(toolbox_path, root_dir_name):
    print """====================\nProcessing toolbox at:\n""", toolbox_path, """\n===================="""
    new_root_path = os.path.dirname(os.path.dirname(toolbox_path))

    with ToolboxWrap(toolbox_path) as toolbox:
        for element_id, script in toolbox.get_all_scripts():
            print script, "changed to:"
            tools_root, name = os.path.split(script)
            while name != root_dir_name:
                tools_root, name = os.path.split(tools_root)
                if not name:
                    raise Exception("Directory '%s' not found in tool script path" % root_dir_name)

            rel_path_script = os.path.relpath(script, tools_root)
            script_new_path = os.path.realpath(os.path.join(new_root_path, rel_path_script))
            print "\t", script_new_path

            if not os.path.exists(script_new_path):
                raise Exception('New script path does not exist: %s' % script_new_path)
            toolbox.set_attribute(element_id, "script", script_new_path)


if __name__ == "__main__":
	try:
		import sys
		args = sys.argv
		toolbox_path = args[1]
		if len(args) > 2:
			root_dir_name = args[2]
		else:
			root_dir_name = "Scripts"
		set_tools_to_current_root(toolbox_path, root_dir_name)	
		
	except sqlite3.OperationalError:
		print "File not found at " + toolbox_path + "."
		pass

