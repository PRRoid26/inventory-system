#!/bin/bash
echo "Starting IT Asset Inventory Management System..."
gnome-terminal --tab --title="Backend API" -- bash -c "./start_backend.sh; exec bash" &
sleep 3
gnome-terminal --tab --title="Frontend GUI" -- bash -c "./start_frontend.sh; exec bash" &
