cp ./projectV.desktop /home/verilog/.local/share/applications/
update-desktop-database ~/.local/share/applications
desktop-file-validate ~/.local/share/applications/projectV.desktop
killall -SIGUSR1 gnome-shell
gtk-launch projectV
