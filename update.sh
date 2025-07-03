echo "update projectV"
cp $DLAB_ROOT/.private/projectV_dev/projectV.desktop /home/verilog/.local/share/applications/
update-desktop-database ~/.local/share/applications
desktop-file-validate ~/.local/share/applications/projectV.desktop
killall -SIGUSR1 gnome-shell
