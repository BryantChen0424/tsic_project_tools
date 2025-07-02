#!/usr/bin/env python3
import gi
import os
import subprocess
import pathlib
from glob import glob

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Pango

class ProjectResetApp(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="projectV")
        self.set_wmclass("projectV", "projectV")
        self.set_border_width(10)
        self.set_default_size(1000, 500)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.add(hbox)

        # === Left side ===
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        hbox.pack_start(vbox, False, False, 0)

        btn_reload = Gtk.Button(label="Reload Project")
        btn_reload.connect("clicked", self.on_reload_project_clicked)
        vbox.pack_start(btn_reload, False, False, 0)

        btn_run_gui = Gtk.Button(label="Run GUI in dlab folders")
        btn_run_gui.connect("clicked", self.on_run_gui_clicked)
        vbox.pack_start(btn_run_gui, False, False, 0)

        btn_waveform = Gtk.Button(label="Show Waveform")
        btn_waveform.connect("clicked", self.on_show_waveform_clicked)
        vbox.pack_start(btn_waveform, False, False, 0)

        # Golden selection section
        self.combo = Gtk.ComboBoxText()
        self.combo.set_entry_text_column(0)
        vbox.pack_start(self.combo, False, False, 0)

        danger_label = Gtk.Label(label="Dangerous zone below! Proceed with caution.")
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

        # === Right side: Simulation log ===
        self.log_buffer = Gtk.TextBuffer()
        self.log_view = Gtk.TextView(buffer=self.log_buffer)
        monospace_font = "monospace"
        self.log_view.modify_font(Pango.FontDescription(monospace_font))
        self.log_view.set_editable(False)
        self.log_view.set_cursor_visible(False)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_hexpand(True)
        scrolled_window.set_vexpand(True)
        scrolled_window.add(self.log_view)
        hbox.pack_start(scrolled_window, True, True, 0)

        # current dlab folder
        self.current_dlab_path = None

    def on_reload_project_clicked(self, widget):
        PUB_ROOT = os.environ.get("PROJECT_PUBLIC_ROOT")
        if not PUB_ROOT or not os.path.isdir(PUB_ROOT):
            self.show_error("PROJECT_PUBLIC_ROOT is not set or is invalid.")
            return
        for sub in os.listdir(PUB_ROOT):
            full_path = os.path.join(PUB_ROOT, sub)
            if os.path.isdir(full_path) and sub.startswith("dlab"):
                self.current_dlab_path = full_path
                self.update_golden_list(full_path)
                return
        self.show_error("No existing dlab* project found to reload.")

    def update_sim_log(self, folder):
        sim_path = os.path.join(folder, "sim_result")
        if not os.path.isdir(sim_path):
            self.log_buffer.set_text("[Simulation log not found]")
            return

        log_files = sorted(glob(os.path.join(sim_path, "*.log")), key=os.path.getmtime, reverse=True)
        if not log_files:
            self.log_buffer.set_text("[No .log files found in sim_result/]")
            return

        latest_log = log_files[0]
        with open(latest_log, "r") as f:
            content = f.read()
            self.log_buffer.set_text(content)

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

    def on_get_project_clicked(self, widget):
        student_name = self.entry.get_text().strip()
        if not student_name:
            self.show_error("Please enter a student name.")
            return

        DLAB_ROOT = os.environ.get("DLAB_ROOT")
        DEV_ROOT = os.environ.get("PROJECT_DEV_ROOT")
        PUB_ROOT = os.environ.get("PROJECT_PUBLIC_ROOT")
        if not all([DLAB_ROOT, DEV_ROOT, PUB_ROOT]):
            self.show_error("Missing environment variables: DLAB_ROOT / PROJECT_DEV_ROOT / PROJECT_PUBLIC_ROOT.")
            return

        students_file = os.path.join(DLAB_ROOT, ".private", "students")
        projects_file = os.path.join(DEV_ROOT, "id-projects")

        student_id = None
        if pathlib.Path(students_file).exists():
            with open(students_file) as f:
                for line in f:
                    if "@" in line:
                        sid, name = line.strip().split("@", 1)
                        if name == student_name:
                            student_id = sid
                            break
        if not student_id:
            self.show_error(f"Student name '{student_name}' not found.")
            return

        project_name = None
        if pathlib.Path(projects_file).exists():
            with open(projects_file) as f:
                for line in f:
                    if "@" in line:
                        sid, pname = line.strip().split("@", 1)
                        if sid == student_id:
                            project_name = pname
                            break
        if not project_name:
            self.show_error(f"No project found for student ID '{student_id}'.")
            return

        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text="Will reset all your project content.",
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

    def on_run_gui_clicked(self, widget):
        if not self.current_dlab_path:
            self.show_error("No dlab* project loaded. Use Get or Reload Project first.")
            return
        try:
            subprocess.run(["make", "run-gui"], cwd=self.current_dlab_path)
            self.update_sim_log(self.current_dlab_path)
        except Exception as e:
            self.show_error(f"Failed to run make: {str(e)}")

    def on_show_waveform_clicked(self, widget):
        if not self.current_dlab_path:
            self.show_error("No dlab* project loaded. Use Get or Reload Project first.")
            return
        wave_file = os.path.join(self.current_dlab_path, "sim_result", "wave.vcd")
        if os.path.isfile(wave_file):
            try:
                subprocess.Popen(["gtkwave", wave_file])
                return
            except Exception as e:
                self.show_error(f"Failed to launch GTKWave: {str(e)}")
        else:
            self.show_error("No waveform file found. Please run simulation first.")

    def on_show_waveform_golden_clicked(self, widget):
        if not self.current_dlab_path:
            self.show_error("No dlab* project loaded.")
            return
        key = self.combo.get_active_text()
        if not key:
            self.show_error("No golden item selected.")
            return
        vcd_path = os.path.join(self.current_dlab_path, "golden", key + ".vcd")
        if not os.path.isfile(vcd_path):
            self.show_error(f"Golden waveform not found: {vcd_path}")
            return
        subprocess.Popen(["gtkwave", vcd_path])

    def on_show_log_golden_clicked(self, widget):
        if not self.current_dlab_path:
            self.show_error("No dlab* project loaded.")
            return
        key = self.combo.get_active_text()
        if not key:
            self.show_error("No golden item selected.")
            return
        log_path = os.path.join(self.current_dlab_path, "golden", key + ".log")
        if not os.path.isfile(log_path):
            self.show_error(f"Golden log not found: {log_path}")
            return
        with open(log_path) as f:
            content = f.read()
            self.log_buffer.set_text(content)

    def show_error(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Error",
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
