#!/usr/bin/env python3
import gi
import os
import subprocess
import pathlib
import hashlib
from glob import glob

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Pango

def hash_name(name):
    clean = name.strip().lower()
    return hashlib.sha256(clean.encode('utf-8')).hexdigest()

class ProjectResetApp(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="projectV")
        self.set_wmclass("projectV", "projectV")
        self.set_border_width(10)
        self.set_default_size(1000, 500)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.add(hbox)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        hbox.pack_start(vbox, False, False, 0)

        btn_reload = Gtk.Button(label="Reload Project")
        btn_reload.connect("clicked", self.on_reload_project_clicked)
        vbox.pack_start(btn_reload, False, False, 0)

        btn_open_spec = Gtk.Button(label="Open Spec")
        btn_open_spec.connect("clicked", self.on_open_spec_clicked)
        vbox.pack_start(btn_open_spec, False, False, 0)

        btn_open_vscode = Gtk.Button(label="Code Editor")
        btn_open_vscode.connect("clicked", self.on_open_vscode_clicked)
        vbox.pack_start(btn_open_vscode, False, False, 0)

        btn_run_gui = Gtk.Button(label="Play The Game")
        btn_run_gui.connect("clicked", self.on_run_gui_clicked)
        vbox.pack_start(btn_run_gui, False, False, 0)

        btn_waveform = Gtk.Button(label="Show Waveform")
        btn_waveform.connect("clicked", self.on_show_waveform_clicked)
        vbox.pack_start(btn_waveform, False, False, 0)

        self.combo = Gtk.ComboBoxText()
        self.combo.set_entry_text_column(0)
        vbox.pack_start(self.combo, False, False, 0)

        danger_label = Gtk.Label()
        danger_label.set_markup('<span foreground="red" weight="bold">Dangerous zone below! Proceed with caution.</span>')
        danger_label.set_name("danger-label")
        
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Enter student name...")
        
        btn_get = Gtk.Button(label="Get Project")
        btn_get.connect("clicked", self.on_get_project_clicked)
        vbox.pack_end(btn_get, False, False, 0)
        vbox.pack_end(self.entry, False, False, 0)
        vbox.pack_end(danger_label, False, False, 0)

        btn_waveform_golden = Gtk.Button(label="Show Waveform (golden)")
        btn_waveform_golden.connect("clicked", self.on_show_waveform_golden_clicked)
        vbox.pack_start(btn_waveform_golden, False, False, 0)

        btn_log_golden = Gtk.Button(label="Show Log (golden)")
        btn_log_golden.connect("clicked", self.on_show_log_golden_clicked)
        vbox.pack_start(btn_log_golden, False, False, 0)

        self.log_buffer = Gtk.TextBuffer()
        self.log_view = Gtk.TextView(buffer=self.log_buffer)
        self.log_view.modify_font(Pango.FontDescription("monospace"))
        self.log_view.set_editable(False)
        self.log_view.set_cursor_visible(False)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_hexpand(True)
        scrolled_window.set_vexpand(True)
        scrolled_window.add(self.log_view)
        hbox.pack_start(scrolled_window, True, True, 0)

        self.current_dlab_path = None

    def on_get_project_clicked(self, widget):
        student_name = self.entry.get_text().strip()
        if not student_name:
            self.show_error("Please enter a student name.")
            return

        DLAB_ROOT = os.environ.get("DLAB_ROOT")
        DEV_ROOT = os.environ.get("PROJECT_DEV_ROOT")
        PUB_ROOT = os.environ.get("PROJECT_PUBLIC_ROOT")
        if not all([DLAB_ROOT, DEV_ROOT, PUB_ROOT]):
            # self.show_error("Missing environment variables.")
            # return
            DLAB_ROOT = "/home/verilog/Desktop/dlab/"
            DEV_ROOT = "/home/verilog/Desktop/dlab/.private/project/"
            PUB_ROOT = "/home/verilog/Desktop/dlab/public/project/"

        hashed_file = os.path.join(DLAB_ROOT, ".private", "projectV_dev", "hashed_students")
        hashed = hash_name(student_name)

        student_id = None
        project_name = None

        if pathlib.Path(hashed_file).exists():
            with open(hashed_file) as f:
                for line in f:
                    parts = line.strip().split("@")
                    if len(parts) == 3:
                        sid, hname, group = parts
                        if hname == hashed:
                            student_id = sid
                            project_name = group
                            break

        if not student_id or not project_name:
            self.show_error(f"Student '{student_name}' not found in hashed_students.")
            return

        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text="Will reset all your project content."
        )
        dialog.format_secondary_text(f"Do you want to continue for: {project_name}?")
        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.OK:
            bash_cmd = f'''
            git -C "$PROJECT_DEV_ROOT" pull
            rm -rf "$PROJECT_PUBLIC_ROOT"/dlab*
            cp -r "$PROJECT_DEV_ROOT"/{project_name} "$PROJECT_PUBLIC_ROOT"/
            '''
            subprocess.run(["bash", "-l", "-c", bash_cmd])

            for sub in os.listdir(PUB_ROOT):
                full_path = os.path.join(PUB_ROOT, sub)
                if os.path.isdir(full_path) and sub.startswith("dlab"):
                    self.current_dlab_path = full_path
                    self.update_golden_list(full_path)
                    break

    def on_reload_project_clicked(self, widget):
        PUB_ROOT = os.environ.get("PROJECT_PUBLIC_ROOT")
        if not PUB_ROOT or not os.path.isdir(PUB_ROOT):
            self.show_error("PROJECT_PUBLIC_ROOT is not set or invalid.")
            return
        for sub in os.listdir(PUB_ROOT):
            full_path = os.path.join(PUB_ROOT, sub)
            if os.path.isdir(full_path) and sub.startswith("dlab"):
                self.current_dlab_path = full_path
                self.update_golden_list(full_path)
                return
        self.show_error("No dlab* project found.")

    def on_run_gui_clicked(self, widget):
        if not self.current_dlab_path:
            self.show_error("No project loaded.")
            return
        try:
            result = subprocess.run(["make", "run-gui"], cwd=self.current_dlab_path,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            self.log_buffer.set_text(result.stdout)
            if result.returncode != 0:
                self.show_error("make run-gui failed. See log for details.")
            else:
                self.update_sim_log(self.current_dlab_path)
        except Exception as e:
            self.show_error(str(e))
        except Exception as e:
            self.show_error(str(e))

    def on_show_waveform_clicked(self, widget):
        if not self.current_dlab_path:
            self.show_error("No project loaded.")
            return
        vcd_path = os.path.join(self.current_dlab_path, "sim_result", "wave.vcd")
        if os.path.isfile(vcd_path):
            subprocess.Popen(["gtkwave", vcd_path])
        else:
            self.show_error("wave.vcd not found.")

    def on_show_waveform_golden_clicked(self, widget):
        if not self.current_dlab_path:
            self.show_error("No project loaded.")
            return
        key = self.combo.get_active_text()
        if not key:
            self.show_error("No golden item selected.")
            return
        vcd_path = os.path.join(self.current_dlab_path, "golden", key + ".vcd")
        if os.path.isfile(vcd_path):
            subprocess.Popen(["gtkwave", vcd_path])
        else:
            self.show_error("Golden waveform not found.")

    def on_show_log_golden_clicked(self, widget):
        if not self.current_dlab_path:
            self.show_error("No project loaded.")
            return
        key = self.combo.get_active_text()
        if not key:
            self.show_error("No golden item selected.")
            return
        log_path = os.path.join(self.current_dlab_path, "golden", key + ".log")
        if os.path.isfile(log_path):
            with open(log_path) as f:
                self.log_buffer.set_text(f.read())
        else:
            self.show_error("Golden log not found.")

    def update_golden_list(self, dlab_folder):
        self.combo.remove_all()
        list_path = os.path.join(dlab_folder, "golden", "list")
        if os.path.isfile(list_path):
            with open(list_path) as f:
                for line in f:
                    item = line.strip()
                    if item:
                        self.combo.append_text(item)
            self.combo.set_active(0)

    def update_sim_log(self, folder):
        sim_path = os.path.join(folder, "sim_result")
        if not os.path.isdir(sim_path):
            self.log_buffer.set_text("[Simulation log not found]")
            return
        log_files = sorted(glob(os.path.join(sim_path, "*.log")), key=os.path.getmtime, reverse=True)
        if not log_files:
            self.log_buffer.set_text("[No .log files found]")
            return
        with open(log_files[0]) as f:
            self.log_buffer.set_text(f.read())

    def on_open_vscode_clicked(self, widget):
        if not self.current_dlab_path:
            self.show_error("No dlab* project loaded. Use Get or Reload Project first.")
            return
        design_path = os.path.join(self.current_dlab_path, "design_src")
        if not os.path.isdir(design_path):
            self.show_error(f"design_src folder not found in {self.current_dlab_path}")
            return
        try:
            subprocess.Popen(["code", design_path, "--goto"] + glob(os.path.join(design_path, "*.v")))
        except Exception as e:
            self.show_error(f"Failed to open VSCode: {str(e)}")

    def on_open_spec_clicked(self, widget):
        if not self.current_dlab_path:
            self.show_error("No project loaded. Use Get or Reload Project first.")
            return
        spec_path = os.path.join(self.current_dlab_path, "ref", "spec.url")
        if not os.path.isfile(spec_path):
            self.show_error("spec.url not found in ref/ folder.")
            return
        with open(spec_path) as f:
            url = f.read().strip()
            if not url.startswith("http"):
                self.show_error("Invalid URL in spec.url")
                return
        try:
            subprocess.Popen(["xdg-open", url])
        except Exception as e:
            self.show_error(f"Failed to open URL: {str(e)}")

    def show_error(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Error"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

def main():
    app = ProjectResetApp()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
