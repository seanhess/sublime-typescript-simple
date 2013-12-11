from subprocess import Popen, PIPE, STDOUT
import sublime
# from sublime_plugin import WindowCommand
from sublime_plugin import EventListener, WindowCommand
import os
# import json
import re
from threading import Thread
from .types import BuildError
from .errors import windows

TYPESCRIPT_NPM_PATH = os.path.join(os.path.dirname(__file__), 'node_modules', 'typescript')
LOCAL_TSC_PATH = os.path.join(TYPESCRIPT_NPM_PATH, 'bin', 'tsc.js')


def render_errors(view, errors):
    file = view.file_name()
    matching_errors = [e for e in errors if e.file == file]
    regions = list(map(lambda e: error_region(view, e), matching_errors))
    view.add_regions('typescript-error', regions, 'typescript.error', 'cross', sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE | sublime.DRAW_SOLID_UNDERLINE)

def render_error_status(view, errors):
    sel = view.sel()
    (line, col) = view.rowcol(sel[0].begin())
    line_error = find_error(errors, line, view.file_name())
    if line_error:
        view.set_status("typescript", line_error.text)    
    else:
        view.erase_status("typescript")


def error_region(view, error):
    a = view.text_point(error.start.line-1, error.start.character-1)
    # b = view.text_point(error.end.line-1, error.end.character-1)
    # go to the end of the line instead?
    # region = sublime.Region(a, b)
    # line = view.line(region)
    end = view.find('\W',a) # match this whole word
    return sublime.Region(a, end.a)

def find_error(errors, line, file):
    for error in errors:
        if error.file == file and (line+1 >= error.start.line and line+1 <= error.end.line):
            return error
    return None

class TypescriptBuild(WindowCommand):

    def __init__(self, window):
        WindowCommand.__init__(self, window)
        self.build_errors_by_file = {}
        self.build_errors = []

    def run(self):
        self.build_errors_by_file = {}
        self.build_errors = []

        view = self.window.active_view()
        if not view: 
            return

        # they should be relative to the project

        thread = Thread(target=lambda: self.build(view))
        thread.daemon = True
        thread.start()

    def build(self, view):

        root_folder = active_window_root_folder()
        main_file = project_main(view)
        file = view.file_name()
        files = [file]

        if main_file:
            view.erase_status("typescript-warning")
            files.append(main_file)
        else:
            view.set_status("typescript-warning", "WARNING: set 'typescript_main' in your project settings. See README")
            

        rel_file = os.path.relpath(file, root_folder)

        view.set_status("typescript", "TS BUILD [ " + rel_file + " ]")

        kwargs = {}
        # this is the default, but you can override the path
        print("FILES", files)
        command = ["node", LOCAL_TSC_PATH, "-m", "commonjs"] + files
        process = Popen(command, stdin=PIPE, stdout=PIPE, stderr=STDOUT, **kwargs)
        (stdout, stderr) = process.communicate()

        self.output_create()

        lines = stdout.decode('UTF-8').split("\n")
        error_list = windows.errors_for_view(view)
        (all_errors, extra_lines) = self.parse_errors(lines)
        error_list.set_errors(all_errors)
        error_list.extra_lines = extra_lines

        if (error_list.is_empty()) and (len(extra_lines) == 0):
            # output.run_command('append', {'characters': '[ OK ]'})
            # output.run_command('close', {})
            # view.set_status("typescript", "BUILD OK")
            view.erase_status("typescript")
            self.output_close()
            
        else:
            view.set_status("typescript", " TS ERRORS [ {0} ] ".format(error_list.count))
            self.render_output(error_list)

        render_errors(view, error_list.by_view(view))




    def render_output(self, error_list):
        root_folder = active_window_root_folder()
        self.output.set_read_only(False)

        for line in error_list.extra_lines:
            self.output_append(line + "\n")
    
        # for file in error_list.files():
        #     errors = error_list.by_file(file)
        #     relative_path = os.path.relpath(file, root_folder)
        #     self.output_append(" {0} \n".format(relative_path))
        #     for error in errors:
        #         self.output_append("  Line {0}: {1}\n".format(error.start.line, error.text))
        #     self.output_append("\n")  

        regions = []
        for file in error_list.files():
            errors = error_list.by_file(file)
            if not errors: continue

            relative_path = os.path.relpath(file, root_folder)
            self.output_append(" {0} \n".format(relative_path))

            for error in errors:
                region_text = '  Line {0}:'.format(error.start.line)
                region_start = self.output.size() + 4
                regions.append(sublime.Region(region_start, region_start + len(region_text) - 2))
                self.output_append('  {0} {1}\n'.format(region_text, error.text))

            self.output_append('\n')

        self.output.add_regions('typescript-illegal', regions, 'error.line', '', sublime.DRAW_NO_FILL)
        self.output.set_read_only(True)
        self.output_open()


    def parse_errors(self, lines):
        last_error = None
        extra_lines = []
        all_errors = []
        for line in lines:
            error = self.parse_error(line)
            if error:
                all_errors.append(error)
                last_error = error
            elif line:
                if last_error:
                    last_error.text += "\n" + line
                else:
                    extra_lines.append(line)

        return (all_errors, extra_lines)                   


    def errors_for_file(self, file):
        if not file in self.build_errors_by_file:
            return []
        return self.build_errors_by_file[file]

    def parse_error(self, line):
        # return a string or an error?
        # if it is a string, just print it out
        # "/Users/seanhess/projects/angularjs-bootstrap/server/server.ts(10,10): error TS1005: '=' expected."
        match = re.match('^(.+)\((\d+),(\d+)\): error (\w+): (.+)$', line)
        if not match: return None

        file = match.group(1)
        line = int(match.group(2))
        col = int(match.group(3))
        text = match.group(5)
        error = BuildError(file, line, col, text)

        return error

    def output_create(self):
        self.output = self.window.create_output_panel('typescript_build')
        self.output.settings().set("color_scheme", "Packages/sublime-typescript-simple/theme/TypescriptBuild.tmTheme")         
        self.output.set_syntax_file("Packages/sublime-typescript-simple/theme/TypescriptBuild.tmLanguage")

    def output_open(self):
        self.window.run_command("show_panel", {"panel": "output.typescript_build"}) 
        
    def output_close(self):
        self.window.run_command("hide_panel", {"panel": "output.typescript_build"})        

    def output_append(self, characters):
        self.output.run_command('append', {'characters': characters})


class TypescriptEventListener(EventListener):

    def __init__(self):
        self.view_modified_time = 0
        self.timer = None
        self.completions_delay_done = False

    # called whenever a veiw is focused
    def on_activated_async(self,view): 
        if not is_typescript(view): 
            self.current_view = None
            return
        
        self.current_view = view

        error_list = windows.errors_for_view(view)
        render_errors(view, error_list.by_view(view))

        # Maybe I should run the build here too! It's safer at least :)
        sublime.active_window().run_command("typescript_build", {})

    def on_post_save_async(self, view):
        if not is_typescript(view): return
        sublime.active_window().run_command("typescript_build", {})
 


class SubtypeErrorsListener(EventListener):

    def on_selection_modified_async(self, view):
        if view.settings().get('syntax').lower().endswith('typescriptbuild.tmlanguage'):
            error_regions = []
            error_regions.extend(view.get_regions('typescript-illegal'))
            error_regions.extend(view.get_regions('typescript-warning'))

            sel_point = view.sel()[0].a
            paths = view.substr(sublime.Region(0, view.size())).split('\n')
            root_folder = active_window_root_folder()

            last_file = None
            for x in range(len(paths)):
                if paths[x].startswith('  '):
                    paths[x] = last_file
                else:
                    last_file = paths[x]

            for region in error_regions:
                if region.contains(sel_point):
                    row = view.rowcol(sel_point)[0]

                    line = view.substr(region)[5:-1].strip()
                    file = paths[row].strip()
                    
                    abspath = os.path.join(root_folder, file)
                    pathline = '{0}:{1}'.format(abspath, line)
                    sublime.active_window().open_file(pathline, sublime.ENCODED_POSITION)







def is_typescript(view):
    if view is None:
        view = sublime.active_window().active_view()
    return 'source.ts' in view.scope_name(0)

def completion_item(completion):
    key = completion_key(completion)
    value = completion_value(completion)
    return (key, value)


def completion_key(completion):
    type = completion.type
    if not is_completion_function(completion):
        type = ":" + type
    return completion.name + type

# turn this into a snippet!
def completion_value(completion):

    # (ext: string, fn: Function): ExpressApplication    
    if not is_completion_function(completion):
        return completion.name

    # the regular expressions were slow
    match = re.match('\((.*)\)\:', completion.type)
    if not match: 
        return completion.name

    # make a snippeter target thing for each parameter
    parameters = match.group(1).split(',')
    snippets = []
    for param in parameters:
        snippets.append("${" + str(len(snippets)+1) + ":" + param + "}")

    snippet = completion.name + "(" + ", ".join(snippets) + ")"
    return snippet


def is_completion_valid(completion):
    return completion.type != None

def is_completion_function(completion):
    return (completion.kind == 'method' or completion.kind == 'function')

def relative_file_path(project_file, file):
    if not file:
        return None
    return os.path.join(os.path.dirname(project_file), file)

def relative_file_paths(window, files):
    project_file = window.project_file_name()
    abs_files = list(map(lambda f: relative_file_path(project_file, f), files))
    return abs_files

def project_main(view):
    if not view.window().project_data(): return None
    if not ("typescript_main" in view.window().project_data()): 
        return None
    return view.window().project_data()["typescript_main"]

def active_window_root_folder():
    open_folders = sublime.active_window().folders()
    if (len(open_folders) > 0):
        return open_folders[0]
    else:
        return ""












def plugin_loaded():
    print("TypescriptBuild: Loaded")
