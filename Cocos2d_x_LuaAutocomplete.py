import sublime
import sublime_plugin
import re
import os
import traceback


class CocosLuaAutocomplete(sublime_plugin.EventListener):
    package_name = "Cocos2d_x_LuaAutocomplete"

    apis = []
    load_api = False

    # lua api files folder name in package/api folder
    apiFolder = "3.15.1"

    # default start with '.', means the .sublime-project location
    resFolder = os.path.join("Resources", "res")
    srcFolder = os.path.join("Resources", "script")

    # not used yet
    log_file_path = os.path.join(package_name, "log.log")

    @staticmethod
    def load_cocos_api():
        # print('start loading cocos API...')
        # load cocos api
        api_folder_path = os.path.join(sublime.packages_path(),
                                       CocosLuaAutocomplete.package_name,
                                       'api',
                                       CocosLuaAutocomplete.apiFolder)
        _, _, api_files = next(os.walk(api_folder_path))

        for api_files_i in range(len(api_files)):
            fname, ext = os.path.splitext(api_files[api_files_i])

            if ext != '.lua':
                continue
            if fname.find('auto_api') != -1:
                continue

            api_file_path = os.path.join(api_folder_path, api_files[api_files_i])
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
                        if len(parent_module) == 0:
                            parent_module = '_G'

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

                        if api_file_strs[api_file_strs_i - 1].find('@overload ') != -1:
                            is_have_overload = True

                        if not is_have_overload:
                            func_strs = api_file_str.split(' ')
                            api_func = [func_strs[3] + '(', func_strs[3] + '(', ""]

                            param_count = 0
                            is_dot_func = True
                            while api_file_strs[api_file_strs_i + 1].find('@param ') != -1:
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
                            while api_file_strs[api_file_strs_i + 1].find('@param ') != -1:
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

                            while api_file_strs[temp_api_file_strs_i - 1].find('@overload ') != -1:
                                func_strs = api_file_str.split(' ')
                                api_func = [func_strs[3] + '(', func_strs[3] + '(', api_return_str]

                                temp_api_file_strs_i -= 1

                                param_count = 0
                                is_dot_func = True

                                all_params = api_file_strs[temp_api_file_strs_i].split(' ')

                                next_param_is_u = False
                                for param_index in range(2, len(all_params) - 1):
                                    if all_params[param_index] and len(all_params[param_index]) > 0:
                                        if param_index == 2 and \
                                                (all_params[param_index] == 'self' or
                                                 all_params[param_index] == 'self,'):
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
                    #    field_strs = api_file_str.split(' ')
                    #    api_field = [field_strs[4], "", ""]
                    #    api_field[1] += field_strs[2].split('#')[1].split(']')[0];
                    #    api_field[2] = field_strs[3].split('#')[1]

                    #    api_module[5].append(api_field)

        def expend_class_method(thisclass, fatherClass):
            for _, m_v in enumerate(CocosLuaAutocomplete.apis):
                for c_i, c_v in enumerate(m_v):
                    if c_i == 0:
                        continue
                    if c_v[0] == fatherClass:
                        if c_v[1] != '' and c_v[2] == 0:
                            fcs = c_v[1].split(',')
                            for _, fc_t in enumerate(fcs):
                                expend_class_method(c_v, fc_t)
                        for i, method_dot in enumerate(c_v[3]):
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

                        for i, method_column in enumerate(c_v[4]):
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
                        #    if i == 0:
                        #       continue
                        #    thisclass[5].append(field)

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
            if ext != '.lua' and ext != '.luac' and ext != 'lc':
                yield f

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

        char = view.substr(pos - 1)
        if char == ".":
            # print('local autocomplete -- Index with dot')
            return 2

        if char == ":":
            # print('local autocomplete -- Index with column')
            return 3
        return 0

    def on_query_completions(self, view, prefix, locations):
        # print('start query completions')

        results = []

        file_name = view.file_name()
        if not file_name or file_name == '':
            return

        _, file_ext = os.path.splitext(file_name)

        if file_ext != '.lua' and file_ext != '.luac' and file_ext != '.lc':
            # Not Lua, don't do anything.
            # print('not lua syntax, cur syntax: ' + file_ext)
            return

        vals = view.window().extract_variables()

        is_project = True

        if 'project_path' not in vals or vals['project_path'] == "":
            # Not a sublime-project
            # print("not a sublime-project")
            is_project = False

        if not CocosLuaAutocomplete.load_api:
            CocosLuaAutocomplete.apis = []
            try:
                CocosLuaAutocomplete.load_cocos_api()
            except:
                traceback.print_exc()
                print("load api failed, check api files and settings")
                CocosLuaAutocomplete.apis = []
                return
            CocosLuaAutocomplete.load_api = True

        location = locations[0]  # TODO: Better multi-select behavior?

        index_case = CocosLuaAutocomplete.can_auto_complete(view, location)

        def extend_module(module):
            for mi, m in enumerate(module):
                if mi == 0:
                    continue
                results.extend(map(lambda c: ('[class]' + c + "\tClass", c), [m[0]]))

        if index_case == 0:
            for module in CocosLuaAutocomplete.apis:
                results.append(['[module]' + module[0] + '\tModule', module[0]])
                if module[0] == "_G":
                    extend_module(module)


        if index_case == 2 and CocosLuaAutocomplete.load_api and CocosLuaAutocomplete.apis:
            pos = view.find_by_class(location, False, sublime.CLASS_WORD_START)

            for module in CocosLuaAutocomplete.apis:
                typeModule = ""
                for i in range(len(module[0]) + 1, 1, -1):
                    typeModule += view.substr(pos - i)
                if typeModule == module[0]:
                    extend_module(module)
                    break

            for module in CocosLuaAutocomplete.apis:
                for class_i, class_v in enumerate(module):
                    if class_i == 0:
                        continue
                    for func_field_index, func_field in enumerate(class_v[3]):
                        if func_field_index == 0:
                            continue
                        class_name = class_v[0]
                        if len(class_name) > 9:
                            class_name = class_name[0:8]  # + '...'
                            results.append(["[{}]{}\t{}".format(class_name,
                                                                func_field[1],
                                                                func_field[2]),
                                            func_field[0]])

                    # for func_field_index, func_field in enumerate(class_v[5]):
                    #    if func_field_index == 0:
                    #       continue
                    #    class_name = class_v[0]
                    #    if len(class_name) > 10:
                    #       class_name = class_name[0:6] + '...'
                    #    results.append(["[" + class_name + "]" + \
                    #                    func_field[1] + "\t" + func_field[2],
                    #                    func_field[1] + '.' + func_field[0]])

        if index_case == 3:
            for module in CocosLuaAutocomplete.apis:
                for class_i, class_v in enumerate(module):
                    if class_i == 0:
                        continue
                    for func_field_index, func_field in enumerate(class_v[4]):
                        if func_field_index == 0:
                            continue
                        class_name = class_v[0]
                        if len(class_name) > 9:
                            class_name = class_name[0:8]  # + '...'
                        results.append(["[{}]{}\t{}".format(class_name,
                                                            func_field[1],
                                                            func_field[2]),
                                        func_field[0]])

        if index_case == 4 and is_project:
            src = view.substr(sublime.Region(view.find_by_class(location, False, sublime.CLASS_LINE_START), location))
            module_match = re.search(r"""require\s*(\(|\s+)['"][\w/\.]*$""", src)
            if module_match:
                proj_subdir = os.path.join(vals['project_path'], CocosLuaAutocomplete.srcFolder)
                if not os.path.exists(proj_subdir) or os.path.isfile(proj_subdir):
                    return

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

                for path in module_path[:-1]:
                    proj_subdir = os.path.join(proj_subdir, path)
                    if not os.path.exists(proj_subdir) or not os.path.isdir(proj_subdir):
                        # print('module path error')
                        return

                _, dirs, files = next(os.walk(proj_subdir))  # walk splits directories and regular files for us

                results.extend(map(lambda c: (c + "\tdir", c + module_split_str), dirs))
                results.extend(map(lambda c: (c + "\tlua(c)", c),
                                   CocosLuaAutocomplete.filter_lua_files(files)))

                return results, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS
            else:
                proj_subdir = os.path.join(vals['project_path'], CocosLuaAutocomplete.resFolder)
                if not os.path.exists(proj_subdir) or os.path.isfile(proj_subdir):
                    print(
                        '"{}" not exists or not a dir\ncheck the {}.py'.format(
                            proj_subdir,
                            CocosLuaAutocomplete.package_name))
                    return

                res = view.substr(sublime.Region(view.find_by_class(location,
                                                                    False,
                                                                    sublime.CLASS_LINE_START),
                                                 location))
                res_match = re.search(r"""[\w/]*$""", res)
                if res_match:
                    # print("match to insert res path")
                    res_path = res_match.group(0).split("/")

                    for path in res_path[:-1]:
                        proj_subdir = os.path.join(proj_subdir, path)
                        if not os.path.exists(proj_subdir) or not os.path.isdir(proj_subdir):
                            # print('res path error')
                            print(
                                '"{}" not exists or not a dir\ncheck the {}.py'.format(
                                    proj_subdir,
                                    CocosLuaAutocomplete.package_name))
                            return

                    _, dirs, files = next(os.walk(proj_subdir))  # walk splits directories and regular files for us

                    results.extend(map(lambda c: (c + "\tresDir", c + "/"), dirs))
                    results.extend(map(lambda c: (c + "\tres", c),
                                       CocosLuaAutocomplete.filter_res_files(files)))

                    if len(results) != 0:
                        result_t = []
                        regions = view.find_all(r'\b\w+(\b|$)')
                        print(regions)
                        pos = view.find_by_class(location, False, sublime.CLASS_WORD_START)
                        char = view.substr(sublime.Region(pos, location))
                        for regn in regions:
                            str_regn = view.substr(regn)
                            if str_regn != char:
                                result_t.append([str_regn, str_regn])
                        result_t = list(result_t)
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
