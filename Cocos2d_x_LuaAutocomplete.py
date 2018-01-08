import sublime
import sublime_plugin
import re
import os
import traceback


class CocosLuaAutocomplete(sublime_plugin.EventListener):
	
	curProjectProp = {"name": "", "path": ""}

	apis = []
	load_api = True

	# mac/linux/unix - use "/" to split paths
	# windows - use "\\" to split paths
	splitSym = "/"

	# lua api files folder name in package/api folder
	apiFolder = "3.15.1"

	# default start with '.', means the .sublime-project location
	resFolder = "." + splitSym + "Resources" + splitSym + "res"
	srcFolder = "." + splitSym + "Resources" + splitSym + "script"

	resExts = [
		".plist",
		".csb",
		".exportjson",
		".json",
		".png",
		".jpg",
		".gif",
		".bmp",
		".mp3",
		".mp4",
		".wav",
		".pvr",
		".ttf"
	]
	# not used yet
	log_file_path = sublime.packages_path() + splitSym + "Cocos2d_x_LuaAutocomplete" + splitSym + "log.log"
	
	@staticmethod
	def load_cocos_api():
		# print('start loading cocos API...')
		# load cocos api
		api_folder_path =   sublime.packages_path() + CocosLuaAutocomplete.splitSym + \
							"Cocos2d_x_LuaAutocomplete" + CocosLuaAutocomplete.splitSym + \
							"api" + CocosLuaAutocomplete.splitSym + \
							CocosLuaAutocomplete.apiFolder
		_, _, api_files = next(os.walk(api_folder_path))

		for api_files_i in range(len(api_files)):
			fname, ext = os.path.splitext(api_files[api_files_i])
			
			if ext != '.lua':
				continue
			if fname.find('auto_api') != -1:
				continue

			api_file_path = api_folder_path + CocosLuaAutocomplete.splitSym + api_files[api_files_i]
			api_file = open(api_file_path, 'r', encoding='utf-8')
			
			api_file_contains = ''
			try:
				api_file_contains = api_file.read()
			except:
				traceback.print_exc()
				api_file_contains = ''
				print('load api file fail: ' + api_file_path)
			finally:
				api_file.close()

			if api_file_contains.isspace():
				print('api file only has space: ' + api_file_path)
				continue

			# p.s.: if 3rd param eq 0, this class has not extend its super class method
			# in the end of this medthod it will extend its super method and set this param to 1
			api_module = [fname, '', 0, ['.'], [':'], ['field']]

			api_file_strs = api_file_contains.split('\n')

			parent_module = ''
			for api_file_strs_i, api_file_str in enumerate(api_file_strs):
				if api_file_str.isspace() or api_file_str.find("---") != -1:
					continue
				if len(parent_module) == 0:
					if api_file_str.find('@parent_module ') != -1:
						parent_module = api_file_str.split(' ')[2]
						
						api_father_module_index = -1

						for api_father_module_i, api_father_module in enumerate(CocosLuaAutocomplete.apis):
							if api_father_module[0] == parent_module:
								api_father_module_index = api_father_module_i
								break
						if api_father_module_index == -1:
							CocosLuaAutocomplete.apis.append([parent_module, api_module])
						else:
							CocosLuaAutocomplete.apis[api_father_module_index].append(api_module)
						continue
				
				if len(api_module[1]) == 0:
					if api_file_str.find('@extend ') != -1:
						api_module[1] = api_file_str.split(' ')[2]
						continue

				if len(parent_module) > 0:
					if api_file_str.find('@function ') != -1:
						is_have_overload = False

						if api_file_strs[api_file_strs_i-1].find('@overload ') != -1:
							is_have_overload = True
						
						if not is_have_overload:
							func_strs = api_file_str.split(' ')
							api_func = [func_strs[3] + '(', func_strs[3] + '(', ""]

							param_count = 0
							is_dot_func = True
							while api_file_strs[api_file_strs_i+1].find('@param ') != -1:
								api_file_strs_i += 1
								
								if param_count == 0:
									if api_file_strs[api_file_strs_i].find('@param self') != -1:
										is_dot_func = False
										continue

								param_types = api_file_strs[api_file_strs_i].split(' ')
								param_type = param_types[2].split('#')[1]
								if param_type == 'unsigned':
									param_type = 'u' + param_types[3]
								param_str = '${' + str(param_count) + ':' + param_type + '}'
								if param_count > 0:
									param_str = ', ' + param_str
									param_type = ', ' + param_type
								api_func[0] += param_str
								api_func[1] += param_type
								param_count += 1
						
							api_func[0] += ')'
							api_func[1] += ')'

							if is_dot_func:
								api_module[3].append(api_func)
							else:
								api_module[4].append(api_func)

							api_file_strs_i += 1
							if api_file_strs[api_file_strs_i].find('@return ') != -1:
								is_unsigned = False
								return_strs = api_file_strs[api_file_strs_i].split(' ')
								api_return_type = return_strs[2]
								if api_return_type == 'unsigned':
									is_unsigned = True
									api_return_type += return_strs[3].split('#')[0]
								else:
									api_return_type = api_return_type.split('#')[0]

								api_return_extra = return_strs[3]
								if is_unsigned:
									api_return_extra = return_strs[5]
								if api_return_extra == 'self':
									api_return_type = api_return_extra
								api_func[2] = api_return_type
						else:
							temp_api_file_strs_i = api_file_strs_i
							while api_file_strs[api_file_strs_i+1].find('@param ') != -1:
								api_file_strs_i += 1

							api_file_strs_i += 1
							api_return_str = ''
							if api_file_strs[api_file_strs_i].find('@return ') != -1:
								is_unsigned = False
								return_strs = api_file_strs[api_file_strs_i].split(' ')
								api_return_type = return_strs[2]
								if api_return_type == 'unsigned':
									is_unsigned = True
									api_return_type += return_strs[3].split('#')[0]
								else:
									api_return_type = api_return_type.split('#')[0]

								api_return_extra = return_strs[3]
								if is_unsigned:
									api_return_extra = return_strs[5]
								if api_return_extra == 'self':
									api_return_type = api_return_extra
								api_return_str = api_return_type

							while api_file_strs[temp_api_file_strs_i-1].find('@overload ') != -1:
								func_strs = api_file_str.split(' ')
								api_func = [func_strs[3] + '(', func_strs[3] + '(', api_return_str]

								temp_api_file_strs_i -= 1

								param_count = 0
								is_dot_func = True

								all_params = api_file_strs[temp_api_file_strs_i].split(' ')

								next_param_is_u = False
								for param_index in range(2, len(all_params)-1):
									if all_params[param_index] and len(all_params[param_index]) > 0:
										if param_index == 2 and (all_params[param_index] == 'self' or all_params[param_index] == 'self,'):
											is_dot_func = False
											continue
										param_type = all_params[param_index]
										if param_type == 'unsigned':
											next_param_is_u = True
											continue
										if param_type[-1:] == ',':
											param_type = param_type[0:-1]
										if next_param_is_u:
											param_type = 'u' + param_type
											next_param_is_u = False
										param_str = '${' + str(param_count) + ':' + param_type + '}'
										if param_count > 0:
											param_str = ', ' + param_str
											param_type = ', ' + param_type
										api_func[0] += param_str
										api_func[1] += param_type
										param_count += 1

								api_func[0] += ')'
								api_func[1] += ')'

								if is_dot_func:
									api_module[3].append(api_func)
								else:
									api_module[4].append(api_func)

					# if api_file_str.find('@field ') != -1:
					# 	field_strs = api_file_str.split(' ')
					# 	api_field = [field_strs[4], "", ""]
					# 	api_field[1] += field_strs[2].split('#')[1].split(']')[0];
					# 	api_field[2] = field_strs[3].split('#')[1]

					# 	api_module[5].append(api_field)

		def expend_class_method(thisclass, fatherClass):
			for _, module_v in enumerate(CocosLuaAutocomplete.apis):
				for class_i, class_v in enumerate(module_v):
					if class_i == 0:
						continue
					if class_v[0] == fatherClass:
						if class_v[1] != '' and class_v[2] == 0:
							fatherClasses = class_v[1].split(',')
							for _, fatherClass_t in enumerate(fatherClasses):
								expend_class_method(class_v, fatherClass_t)
						for i, method_dot in enumerate(class_v[3]):
							if i == 0:
								continue

							is_same = False
							for method in thisclass[3]:
								if method == '.':
									continue
								if method[1].split('(')[0] == method_dot[1].split('(')[0]:
									is_same = True
									break
							if is_same:
								continue
							thisclass[3].append(method_dot)

						for i, method_column in enumerate(class_v[4]):
							if i == 0:
								continue

							is_same = False
							for method in thisclass[4]:
								if method == ':':
									continue
								# print(method[2].split('(')[0])
								# print(method_column[0].split('(')[0])
								if method[1].split('(')[0] == method_column[1].split('(')[0]:
									is_same = True
									break
							if is_same:
								continue
							thisclass[4].append(method_column)

						# for i, field in enumerate(class_v[5]):
						# 	if i == 0:
						# 		continue
						# 	thisclass[5].append(field)

						thisclass[2] = 1
		for _, module_v in enumerate(CocosLuaAutocomplete.apis):
			for class_i, class_v in enumerate(module_v):
				if class_i == 0:
					continue
				if class_v[1] != '' and class_v[2] == 0:
					fatherClasses = class_v[1].split(',')
					for _, fatherClass_t in enumerate(fatherClasses):
						expend_class_method(class_v, fatherClass_t)

	@staticmethod
	def filter_lua_files(filenames):
		for f in filenames:
			fname, ext = os.path.splitext(f)
			if ext == ".lua" or ext == ".luac" or ext == ".lc":
				yield fname
	
	@staticmethod
	def filter_res_files(filenames):
		for f in filenames:
			fname, ext = os.path.splitext(f)
			ext = ext.lower()
			for resExt in resExts:
				if ext == resExt:
					yield fname + ext

	@staticmethod
	def can_auto_complete(view, location):
		pos = view.find_by_class(location, False, sublime.CLASS_WORD_START)
		if pos == 0:
			return 0
		
		scope_name = view.scope_name(location)
		if "string." in scope_name or "comment." in scope_name:
			# In a string or comment
			# print('autocomplete disabled -- In a string or comment')
			return 4
		
		if "parameter" in scope_name:
			# Specifying parameters
			# print('autocomplete disabled -- Specifying parameters')
			return 1
		
		char = view.substr(pos-1)
		if char == ".":
			# print('local autocomplete -- Index with dot')
			return 2

		if char == ":":
			# print('local autocomplete -- Index with column')
			return 3
		return 0

	def on_query_completions(self, view, prefix, locations):
		# print('start query competions')

		syntax = view.settings().get("syntax")
		if syntax != "Packages/Lua/Lua.sublime-syntax" and syntax != "Packages/LuaExtended/LuaExtended.sublime-syntax":
			# Not Lua, don't do anything.
			# print('not lua syntax, cur syntax: ' + syntax)
			return

		vals = view.window().extract_variables()

		if not vals["project_name"] or vals["project_name"] == "":
			# Not a sublime-project
			# print("not a sublime-project")
			return

		if  (vals["project_name"] and vals["project_name"] != CocosLuaAutocomplete.curProjectProp["name"]) or \
			(vals["project_path"] and vals["project_path"] != CocosLuaAutocomplete.curProjectProp["path"]) and \
			CocosLuaAutocomplete.load_api:
			CocosLuaAutocomplete.apis = []
			try:
				CocosLuaAutocomplete.load_cocos_api()
				CocosLuaAutocomplete.curProjectProp["name"] = vals["project_name"]
				CocosLuaAutocomplete.curProjectProp["path"] = vals["project_path"]
			except:
				traceback.print_exc()
				print("load api failed, check api files and settings")
				CocosLuaAutocomplete.load_api = False
				CocosLuaAutocomplete.apis = []
				CocosLuaAutocomplete.curProjectProp["name"] = ""
				CocosLuaAutocomplete.curProjectProp["path"] = ""
				return

		results = []

		location = locations[0] # TODO: Better multiselect behavior?
		
		index_case = CocosLuaAutocomplete.can_auto_complete(view, location)

		if index_case == 0:
			for _, module in enumerate(CocosLuaAutocomplete.apis):
				results.append(['[module]' + module[0] + '\tModule', module[0]])

		if index_case == 2 and CocosLuaAutocomplete.load_api:
			pos = view.find_by_class(location, False, sublime.CLASS_WORD_START)
			module1 = view.substr(pos-3) + view.substr(pos-2)
			module2 = view.substr(pos-4) + view.substr(pos-3) + view.substr(pos-2)
			module3 = view.substr(pos-5) + view.substr(pos-4) + view.substr(pos-3) + view.substr(pos-2)

			isModule1 = False
			isModule2 = False
			isModule3 = False

			if module1 == 'cc':
				isModule1 = True
				for _, api_father_module in enumerate(CocosLuaAutocomplete.apis):
					if api_father_module[0] != 'cc':
						continue
					for module_index, module in enumerate(api_father_module):
						if module_index == 0:
							continue
						results.extend(map(lambda x: ('[class]'+x+"\tClass", x), [module[0]]))
			if module2 == 'ccs':
				isModule2 = True
				for _, api_father_module in enumerate(CocosLuaAutocomplete.apis):
					if api_father_module[0] != 'ccs':
						continue
					for module_index, module in enumerate(api_father_module):
						if module_index == 0:
							continue
						results.extend(map(lambda x: ('[class]'+x+"\tClass", x), [module[0]]))
			if module3 == 'ccui':
				isModule3 = True
				for _, api_father_module in enumerate(CocosLuaAutocomplete.apis):
					if api_father_module[0] != 'ccui':
						continue
					for module_index, module in enumerate(api_father_module):
						if module_index == 0:
							continue
						results.extend(map(lambda x: ('[class]'+x+"\tClass", x), [module[0]]))

			if (not isModule1) and (not isModule2) and (not isModule3):
				for _, module in enumerate(CocosLuaAutocomplete.apis):
					for class_i, class_v in enumerate(module):
						if class_i == 0:
							continue
						for func_field_index, func_field in enumerate(class_v[3]):
							if func_field_index == 0:
								continue
							class_name = class_v[0]
							if len(class_name) > 9:
								class_name = class_name[0:8] #+ '...'
							results.append(["[" + class_name + "]" + func_field[1] + "\t" + func_field[2], func_field[0]])

						# for func_field_index, func_field in enumerate(class_v[5]):
						# 	if func_field_index == 0:
						# 		continue
						# 	class_name = class_v[0]
						# 	if len(class_name) > 10:
						# 		class_name = class_name[0:6] + '...'
						# 	results.append(["[" + class_name + "]" + func_field[1] + "\t" + func_field[2], func_field[1] + '.' + func_field[0]])

		if index_case == 3:
			for _, module in enumerate(CocosLuaAutocomplete.apis):
				for class_i, class_v in enumerate(module):
					if class_i == 0:
						continue
					for func_field_index, func_field in enumerate(class_v[4]):
						if func_field_index == 0:
							continue
						class_name = class_v[0]
						if len(class_name) > 9:
							class_name = class_name[0:8] #+ '...'
						results.append(["[" + class_name + "]" + func_field[1] + "\t" + func_field[2], func_field[0]])

		if index_case == 4:
			src = view.substr(sublime.Region(view.find_by_class(location, False, sublime.CLASS_LINE_START), location))
			module_match = re.search(r"""require\s*(\(|\s+)['"][\w/\.]*$""", src)
			if module_match:
				# print("match to insert module path")
				src = module_match.group()
				src = src.split(re.search(r"""require\s*(\(|\s+)['"]""", src).group())[1]
				module_path = src.split("/")
				module_path2 = src.split(".")

				len1 = len(module_path)
				len2 = len(module_path2)

				module_split_str = "/"

				if len1 < len2:
					module_path = module_path2
					module_split_str = "."

				results = []
				
				proj_subdir = CocosLuaAutocomplete.srcFolder
				for path in module_path[:-1]:
					proj_subdir += CocosLuaAutocomplete.splitSym + path
					if not os.path.exists(proj_subdir) or not os.path.isdir(proj_subdir):
						# print('module path error')
						return
				
				_, dirs, files = next(os.walk(proj_subdir)) # walk splits directories and regular files for us
				
				results.extend(map(lambda x: (x+"\tdir", x+module_split_str), dirs))
				results.extend(map(lambda x: (x+"\tmodule", x), CocosLuaAutocomplete.filter_lua_files(files)))
				
				return results, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS
			else:
				res = view.substr(sublime.Region(view.find_by_class(location, False, sublime.CLASS_LINE_START), location))
				res_match = re.search(r"""[\w/]*$""", res)
				if res_match:
					# print("match to insert res path")
					res_path = res_match.group(0).split("/")

					results = []
					
					proj_subdir = CocosLuaAutocomplete.resFolder
					for path in res_path[:-1]:
						proj_subdir += CocosLuaAutocomplete.splitSym + path
						if not os.path.exists(proj_subdir) or not os.path.isdir(proj_subdir):
							# print('res path error')
							return
					
					_, dirs, files = next(os.walk(proj_subdir)) # walk splits directories and regular files for us
						
					results.extend(map(lambda x: (x+"\tresDir", x+"/"), dirs))
					results.extend(map(lambda x: (x+"\tres", x), CocosLuaAutocomplete.filter_res_files(files)))
					
					if len(results) != 0:
						result_t = []
						regions = view.find_all(r'\b\w+(\b|$)')
						pos = view.find_by_class(location, False, sublime.CLASS_WORD_START)
						char = view.substr(sublime.Region(pos, location))
						for _, regn in enumerate(regions):
							str_regn = view.substr(regn)
							if str_regn != char:
								result_t.append([str_regn, str_regn])
						result_t = list(set(result_t))
						for x in result_t:
							results.append([x, x])

					return results, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS

		if len(results) != 0:
			result_t = []
			regions = view.find_all(r'\b[a-zA-Z0-9_]+(\b|$)')
			pos = view.find_by_class(location, False, sublime.CLASS_WORD_START)
			char = view.substr(sublime.Region(pos, location))
			for _, regn in enumerate(regions):
				str_regn = view.substr(regn)
				if str_regn != char:
					result_t.append(str_regn)
			result_t = list(set(result_t))
			for x in result_t:
				results.append([x, x])
			return results, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS