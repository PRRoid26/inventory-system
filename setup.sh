#!/bin/bash

# IT Asset Inventory Management System - Setup Script
# This script automates the installation process

set -e

echo "=========================================="
echo "IT Asset Inventory Management System"
echo "Production Setup Script"
echo "=========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}Please do not run this script as root${NC}"
    exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo -e "${RED}Cannot detect OS${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Detected OS: $OS"
echo ""

# Function to install system dependencies
install_system_deps() {
    echo "Installing system dependencies..."
    
    if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib \
            libpq-dev python3-dev build-essential git \
            libxcb-xinerama0 libxcb-cursor0 libxkbcommon-x11-0
    elif [ "$OS" = "fedora" ] || [ "$OS" = "rhel" ] || [ "$OS" = "centos" ]; then
        sudo dnf install -y python3 python3-pip postgresql postgresql-contrib \
            postgresql-devel python3-devel gcc git \
            xcb-util-cursor xcb-util-keysyms xcb-util-wm
    elif [ "$OS" = "arch" ] || [ "$OS" = "manjaro" ]; then
        sudo pacman -Sy --noconfirm python python-pip postgresql git \
            qt6-base
    else
        echo -e "${YELLOW}⚠${NC} Unknown OS. Please install dependencies manually."
        return 1
    fi
    
    echo -e "${GREEN}✓${NC} System dependencies installed"
}

# Function to setup PostgreSQL
setup_postgresql() {
    echo ""
    echo "Setting up PostgreSQL..."
    
    # Start PostgreSQL
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    
    # Create database and user
    read -p "Enter database name [inventory_db]: " DB_NAME
    DB_NAME=${DB_NAME:-inventory_db}
    
    read -p "Enter database username [inventory_user]: " DB_USER
    DB_USER=${DB_USER:-inventory_user}
    
    read -sp "Enter database password: " DB_PASS
    echo ""
    
    # Create database
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || echo "Database already exists"
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" 2>/dev/null || echo "User already exists"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
    
    export DATABASE_URL="postgresql://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME"
    
    echo -e "${GREEN}✓${NC} PostgreSQL configured"
    echo "DATABASE_URL=$DATABASE_URL"
}

# Function to setup Python environment
setup_python_env() {
    echo ""
    echo "Setting up Python environment..."
    
    # Backend
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
    cd ..
    
    # Frontend
    cd frontend
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
    cd ..
    
    echo -e "${GREEN}✓${NC} Python environments created"
}

# Function to initialize database
init_database() {
    echo ""
    echo "Initializing database..."
    
    cd backend
    source venv/bin/activate
    export DATABASE_URL
    cd ../database
    python init_db.py
    
    read -p "Do you want to add sample data? (y/N): " ADD_SAMPLE
    if [ "$ADD_SAMPLE" = "y" ] || [ "$ADD_SAMPLE" = "Y" ]; then
        python init_db.py --sample-data
    fi
    
    deactivate
    cd ..
    
    echo -e "${GREEN}✓${NC} Database initialized"
}

# Function to create startup scripts
create_startup_scripts() {
    echo ""
    echo "Creating startup scripts..."
    
    # Backend startup script
    cat > start_backend.sh << 'EOF'
#!/bin/bash
cd backend
source venv/bin/activate
export DATABASE_URL="${DATABASE_URL}"
export JWT_SECRET_KEY="${JWT_SECRET_KEY:-your-secret-key-change-in-production}"
python main.py
EOF
    chmod +x start_backend.sh
    
    # Frontend startup script
    cat > start_frontend.sh << 'EOF'
#!/bin/bash
cd frontend
source venv/bin/activate
python main.py
EOF
    chmod +x start_frontend.sh
    
    # Combined startup script
    cat > start_all.sh << 'EOF'
#!/bin/bash
echo "Starting IT Asset Inventory Management System..."
gnome-terminal --tab --title="Backend API" -- bash -c "./start_backend.sh; exec bash" &
sleep 3
gnome-terminal --tab --title="Frontend GUI" -- bash -c "./start_frontend.sh; exec bash" &
EOF
    chmod +x start_all.sh
    
    echo -e "${GREEN}✓${NC} Startup scripts created"
}

# Function to create systemd service (optional)
create_systemd_service() {
    echo ""
    read -p "Do you want to create a systemd service for auto-start? (y/N): " CREATE_SERVICE
    
    if [ "$CREATE_SERVICE" = "y" ] || [ "$CREATE_SERVICE" = "Y" ]; then
        CURRENT_DIR=$(pwd)
        CURRENT_USER=$(whoami)
        
        sudo tee /etc/systemd/system/inventory-backend.service > /dev/null << EOF
[Unit]
Description=IT Asset Inventory Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR/backend
Environment="DATABASE_URL=$DATABASE_URL"
Environment="JWT_SECRET_KEY=your-secret-key-change-in-production"
ExecStart=$CURRENT_DIR/backend/venv/bin/python $CURRENT_DIR/backend/main.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        sudo systemctl enable inventory-backend.service
        
        echo -e "${GREEN}✓${NC} Systemd service created"
        echo "Start with: sudo systemctl start inventory-backend"
        echo "Check status: sudo systemctl status inventory-backend"
    fi
}

# Main installation flow
main() {
    echo "This script will install the IT Asset Inventory Management System"
    echo ""
    read -p "Continue with installation? (y/N): " CONTINUE
    
    if [ "$CONTINUE" != "y" ] && [ "$CONTINUE" != "Y" ]; then
        echo "Installation cancelled"
        exit 0
    fi
    
    echo ""
    echo "Starting installation..."
    echo ""
    
    install_system_deps
    setup_postgresql
    setup_python_env
    init_database
    create_startup_scripts
    create_systemd_service
    
    echo ""
    echo "=========================================="
    echo -e "${GREEN}✓ Installation Complete!${NC}"
    echo "=========================================="
    echo ""
    echo "Default credentials:"
    echo "  Username: admin"
    echo "  Password: admin123"
    echo ""
    echo "⚠️  Please change the default password after first login!"
    echo ""
    echo "To start the system:"
    echo "  Backend: ./start_backend.sh"
    echo "  Frontend: ./start_frontend.sh"
    echo "  Both: ./start_all.sh"
    echo ""
    echo "API Documentation: http://localhost:8000/docs"
    echo ""
    echo "For cloud deployment, see README.md"
    echo "=========================================="
}

# Run main installation
main
