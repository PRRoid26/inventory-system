# IT Asset Inventory Management System

Production-ready inventory management system with Qt desktop client and cloud-capable backend.

## 🌟 Features

### Core Features
- **Complete Asset Tracking**: Track all IT equipment with asset numbers, serial numbers, specifications
- **CSV Import with History**: Import equipment from CSV/Excel files, all imports are saved and can be reviewed
- **Smart Auto-categorization**: Automatically categorizes equipment based on product names
- **Autocomplete Search**: Fast asset search with autocomplete suggestions
- **Equipment Specifications**: Detailed technical specifications for each equipment
- **Work Log Management**: Track equipment check-out/check-in, assignments, and job tracking
- **Multi-tab Overview**: Separate tabs for each equipment category with detailed statistics
- **User Authentication**: Secure login system with role-based access (Admin, Manager, User)
- **Cloud Ready**: Deploy on any cloud platform with Docker support

### Technical Features
- **RESTful API**: FastAPI backend with automatic API documentation
- **PostgreSQL Database**: Robust, production-grade database with relationships
- **Qt6 Desktop Client**: Native cross-platform desktop application for Linux
- **Docker Deployment**: Complete containerization for easy deployment
- **Remote Access**: Access from anywhere with cloud deployment
- **Real-time Statistics**: Live dashboard with equipment status breakdown
- **Import History**: Never lose data - all CSV imports are preserved
- **Audit Logging**: Track all system changes and user activities

## 📋 Prerequisites

### For Local Development
- Python 3.9 or higher
- PostgreSQL 13 or higher
- Qt6 dependencies for GUI

### For Docker Deployment
- Docker 20.10+
- Docker Compose 2.0+

## 🚀 Quick Start

### Option 1: Local Development Setup

#### 1. Clone and Setup

```bash
# Navigate to the project directory
cd inventory-system

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
pip install -r requirements.txt
```

#### 2. Setup Database

```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database
sudo -u postgres psql
CREATE DATABASE inventory_db;
CREATE USER inventory_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE inventory_db TO inventory_user;
\q
```

#### 3. Initialize Database

```bash
cd database
export DATABASE_URL="postgresql://inventory_user:your_secure_password@localhost:5432/inventory_db"
python init_db.py

# Optionally add sample data
python init_db.py --sample-data
```

#### 4. Start Backend Server

```bash
cd ../backend
export DATABASE_URL="postgresql://inventory_user:your_secure_password@localhost:5432/inventory_db"
export JWT_SECRET_KEY="your-very-secret-key-change-this"

# Run the server
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000
API Documentation: http://localhost:8000/docs

#### 5. Launch Desktop Client

```bash
cd ../frontend
python main.py
```

Default credentials:
- Username: `admin`
- Password: `admin123`

**⚠️ Change the default password immediately after first login!**

### Option 2: Docker Deployment (Recommended for Production)

#### 1. Configure Environment

Create a `.env` file in the `docker` directory:

```env
DB_PASSWORD=your_secure_db_password
JWT_SECRET_KEY=your_very_secret_jwt_key_minimum_32_characters
```

#### 2. Deploy with Docker Compose

```bash
cd docker

# Build and start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Initialize database
docker-compose exec backend python /app/../database/init_db.py

# Stop services
docker-compose down

# Stop and remove all data
docker-compose down -v
```

Services will be available at:
- API: http://localhost:8000
- Nginx (production): http://localhost:80

#### 3. Cloud Deployment

For cloud deployment (AWS, Azure, GCP, DigitalOcean, etc.):

1. **Set up a cloud VM** (Ubuntu 20.04/22.04 recommended)

2. **Install Docker and Docker Compose**:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

3. **Configure domain and SSL** (for HTTPS):
```bash
# Install certbot
sudo apt install certbot

# Get SSL certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem docker/nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem docker/nginx/ssl/key.pem
```

4. **Update Nginx configuration**:
Edit `docker/nginx/nginx.conf` and uncomment the HTTPS section

5. **Configure firewall**:
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

6. **Deploy**:
```bash
cd docker
docker-compose up -d
```

7. **Update desktop client**:
In the desktop application, change the server URL to: `https://your-domain.com`

## 🔧 Configuration

### Backend Configuration

Edit `backend/main.py` or set environment variables:

```python
DATABASE_URL = "postgresql://user:password@host:port/database"
JWT_SECRET_KEY = "your-secret-key"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours
```

### Frontend Configuration

Edit `frontend/main.py`:

```python
API_BASE_URL = "http://your-server:8000"  # Change to your server URL
```

## 📊 Using the System

### Import Equipment Data

1. Prepare CSV/Excel file with columns:
   - `asset_no` (required)
   - `serial_no`
   - `product_name` (required)
   - `status` (Available/In Service/Faulty/Retired)

2. In the desktop app:
   - Go to **Inventory** tab
   - Click **Import CSV/Excel**
   - Select your file
   - View import results

3. View import history:
   - Go to **Import History** tab
   - See all past imports
   - View details of each import
   - Delete import records (optionally with equipment)

### Search Equipment

- **Quick search**: Type first few characters in the Asset No field
- **Autocomplete**: Suggestions appear as you type
- **Filter by category**: Select category from dropdown
- **Filter by status**: Select status from dropdown

### Add Specifications

1. Go to **Specifications** tab
2. Search for equipment by asset number (autocomplete enabled)
3. Click **Load Specifications**
4. Click **Add/Edit Specifications**
5. Fill in details:
   - Processor, RAM, Storage
   - Graphics, OS, Network
   - Additional notes

### Track Work Logs

1. Go to **Work Logs** tab
2. Click **Create Work Log**
3. Search for equipment
4. Fill in:
   - Job/Project name
   - Assigned person
   - Department
   - Check out date
   - Expected return date
   - Notes

## 📈 System Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Qt Desktop Client                  │
│             (Cross-platform Linux GUI)              │
└───────────────────┬─────────────────────────────────┘
                    │
                    │ HTTPS/REST API
                    │
┌───────────────────▼─────────────────────────────────┐
│                    Nginx Proxy                      │
│              (Load Balancer + SSL)                  │
└───────────────────┬─────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────┐
│                 FastAPI Backend                     │
│         (Authentication + Business Logic)           │
└───────────────────┬─────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────┐
│               PostgreSQL Database                   │
│         (Equipment, Users, Work Logs, etc.)         │
└─────────────────────────────────────────────────────┘
```

## 🗄️ Database Schema

### Main Tables

- **users**: User accounts and authentication
- **equipment**: All IT assets
- **specifications**: Technical specs for each equipment
- **work_logs**: Check-out/check-in tracking
- **csv_imports**: History of all CSV imports
- **audit_logs**: System audit trail

### Relationships

- Equipment → Specifications (One-to-Many)
- Equipment → Work Logs (One-to-Many)
- CSV Import → Equipment (One-to-Many)
- Users → Work Logs (One-to-Many)

## 🔒 Security Features

- JWT-based authentication
- Password hashing with bcrypt
- Role-based access control (Admin, Manager, User)
- SQL injection prevention (SQLAlchemy ORM)
- CORS configuration
- Rate limiting (Nginx)
- Audit logging

## 📡 API Endpoints

Full API documentation available at: http://your-server:8000/docs

### Key Endpoints

- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/equipment` - List all equipment
- `POST /api/equipment` - Add equipment
- `GET /api/equipment/search/{prefix}` - Autocomplete search
- `POST /api/import/csv` - Import CSV file
- `GET /api/imports` - View import history
- `GET /api/stats/overview` - Get statistics
- `POST /api/worklogs` - Create work log

## 🛠️ Maintenance

### Backup Database

```bash
# Manual backup
docker-compose exec db pg_dump -U postgres inventory_db > backup.sql

# Automated daily backup (add to crontab)
0 2 * * * docker-compose exec db pg_dump -U postgres inventory_db > /backups/inventory_$(date +\%Y\%m\%d).sql
```

### Restore Database

```bash
docker-compose exec -T db psql -U postgres inventory_db < backup.sql
```

### Update System

```bash
# Pull latest changes
git pull

# Rebuild containers
docker-compose down
docker-compose build
docker-compose up -d

# Run migrations if needed
docker-compose exec backend python ../database/init_db.py
```

### Monitor Logs

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f backend
docker-compose logs -f db
```

## 🐛 Troubleshooting

### Desktop client can't connect to server

1. Check if backend is running: `curl http://localhost:8000`
2. Verify firewall allows port 8000
3. Check server URL in desktop client settings

### Database connection error

1. Verify PostgreSQL is running: `docker-compose ps`
2. Check database credentials in environment variables
3. Test connection: `psql -h localhost -U postgres -d inventory_db`

### Import fails

1. Check CSV format (required columns: asset_no, product_name)
2. Verify file encoding is UTF-8
3. Check backend logs: `docker-compose logs backend`

## 📝 License

This is a production-grade application for IT asset management.

## 🤝 Support

For issues and feature requests, check the application logs and API documentation.

## 🎯 Future Enhancements

- Mobile app (iOS/Android)
- Barcode/QR code scanning
- Email notifications for warranty expiry
- Advanced reporting and analytics
- Integration with Active Directory
- Asset lifecycle management
- Maintenance scheduling
- Cost tracking and budgeting
