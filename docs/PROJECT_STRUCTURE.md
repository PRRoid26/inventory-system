# IT Asset Inventory Management System - Project Structure

## 📁 Directory Structure

```
inventory-system/
├── backend/                      # FastAPI backend server
│   ├── main.py                  # Main API application (750+ lines)
│   ├── requirements.txt         # Python dependencies
│   └── Dockerfile              # Backend container configuration
│
├── frontend/                    # PyQt6 desktop application
│   ├── main.py                 # Main GUI application (1100+ lines)
│   └── requirements.txt        # Python dependencies
│
├── database/                    # Database initialization
│   └── init_db.py              # Database setup and sample data
│
├── docker/                      # Docker deployment
│   ├── docker-compose.yml      # Multi-container orchestration
│   └── nginx/
│       └── nginx.conf          # Reverse proxy configuration
│
├── scripts/                     # Utility scripts
│   └── backup_database.sh      # Automated backup script
│
├── tests/                       # Test suite
│   └── test_api.py             # API integration tests
│
├── docs/                        # Documentation
│   └── USER_GUIDE.md           # End-user documentation
│
├── sample_data/                 # Sample files
│   └── equipment_template.csv  # CSV import template
│
├── setup.sh                     # Automated installation script
├── README.md                    # Main documentation
├── .env.template               # Environment variables template
└── .gitignore                  # Git ignore rules
```

## 🔧 Core Components

### Backend API (`backend/main.py`)

**Lines of Code**: ~750

**Key Features**:
- FastAPI REST API server
- PostgreSQL database integration
- JWT authentication
- Role-based access control
- CSV/Excel import with history
- Autocomplete search
- Statistics and analytics
- Audit logging

**Database Models**:
- **User**: Authentication and authorization
- **Equipment**: IT asset records
- **Specification**: Technical specifications
- **WorkLog**: Check-out/check-in tracking
- **CSVImport**: Import history
- **AuditLog**: System audit trail

**API Endpoints** (20+):
```
Authentication:
- POST /api/auth/register
- POST /api/auth/login
- GET  /api/auth/me

Equipment:
- GET    /api/equipment
- POST   /api/equipment
- GET    /api/equipment/{id}
- PUT    /api/equipment/{id}
- DELETE /api/equipment/{id}
- GET    /api/equipment/search/{prefix}

Specifications:
- POST /api/specifications
- GET  /api/specifications/{equipment_id}
- PUT  /api/specifications/{spec_id}

Work Logs:
- GET  /api/worklogs
- POST /api/worklogs
- PUT  /api/worklogs/{id}

Imports:
- POST   /api/import/csv
- GET    /api/imports
- GET    /api/imports/{id}
- DELETE /api/imports/{id}

Statistics:
- GET /api/stats/overview
- GET /api/stats/category
- GET /api/stats/category/{category}
```

### Frontend GUI (`frontend/main.py`)

**Lines of Code**: ~1100

**Key Features**:
- PyQt6 desktop application
- Cross-platform (Linux focus)
- 5 main tabs:
  1. Overview (statistics dashboard)
  2. Inventory (equipment management)
  3. Specifications (technical details)
  4. Work Logs (check-out/check-in)
  5. Import History (CSV import management)

**Components**:
- `APIClient`: Handles all server communication
- `LoginDialog`: Authentication interface
- `MainWindow`: Main application window
- `EquipmentDialog`: Add/edit equipment
- `SpecificationDialog`: Manage specifications
- `WorkLogDialog`: Create work logs
- Multiple table widgets with filtering and sorting

**Features**:
- Real-time autocomplete search
- Color-coded status indicators
- Multi-criteria filtering
- Sortable tables
- Import/export functionality
- Cloud connectivity

### Database Layer (`database/init_db.py`)

**Features**:
- PostgreSQL schema creation
- Default admin user creation
- Sample data generation
- Migration support

**Tables**:
1. **users** - User accounts
2. **equipment** - IT assets
3. **specifications** - Technical specs
4. **work_logs** - Usage tracking
5. **csv_imports** - Import history
6. **audit_logs** - Audit trail

### Deployment (`docker/`)

**Docker Compose Services**:
1. **PostgreSQL Database** (Port 5432)
   - Persistent storage
   - Health checks
   - Auto-restart

2. **Backend API** (Port 8000)
   - FastAPI server
   - File uploads
   - Environment configuration

3. **Nginx Reverse Proxy** (Port 80/443)
   - Load balancing
   - SSL termination
   - Rate limiting

## 🎯 Feature Highlights

### 1. CSV Import with History ✅
- Import from CSV/Excel files
- All imports are saved permanently
- View import details anytime
- Delete imports with/without equipment
- Auto-categorization based on product names

### 2. Autocomplete Search ✅
- Type first few characters
- Real-time suggestions
- Fast asset lookup
- Works across all tabs

### 3. Equipment Specifications ✅
- Detailed technical specs
- Processor, RAM, Storage, etc.
- Custom fields support
- JSON-based flexible schema

### 4. Multi-tab Overview ✅
- Dashboard with statistics
- Category-based breakdown
- Click to see detailed equipment
- Real-time status updates

### 5. Work Log Management ✅
- Track equipment usage
- Check-out/check-in workflow
- Assignment tracking
- Status management

### 6. Cloud Deployment ✅
- Docker containerization
- Nginx reverse proxy
- SSL/HTTPS support
- Remote access ready

### 7. Production-Ready ✅
- PostgreSQL database
- JWT authentication
- Role-based access
- Audit logging
- Automated backups
- Error handling

## 🔐 Security Features

1. **Authentication**
   - JWT tokens
   - Bcrypt password hashing
   - Session management

2. **Authorization**
   - Role-based access (Admin/Manager/User)
   - Endpoint-level permissions
   - Resource ownership validation

3. **Data Protection**
   - SQL injection prevention (SQLAlchemy ORM)
   - CORS configuration
   - Rate limiting
   - Input validation

4. **Audit Trail**
   - All changes logged
   - User tracking
   - IP address logging
   - Timestamp recording

## 📊 Statistics & Analytics

### Overview Dashboard
- Total equipment count
- Status breakdown (Available/In Service/Faulty/Retired)
- Category distribution
- Real-time updates

### Category Analytics
- Equipment per category
- Status per category
- Product-level breakdown
- Clickable drill-down

### Work Log Analytics
- Active work logs
- Completion tracking
- Department-wise distribution

## 🚀 Deployment Options

### 1. Local Development
```bash
./setup.sh
./start_all.sh
```

### 2. Docker (Single Server)
```bash
cd docker
docker-compose up -d
```

### 3. Cloud (Production)
- AWS EC2/Lightsail
- Azure VM
- Google Cloud Compute
- DigitalOcean Droplet
- Any VPS with Docker support

## 🔄 Data Flow

```
Desktop Client (Qt6)
    ↓ HTTP/HTTPS
API Server (FastAPI)
    ↓ SQLAlchemy
Database (PostgreSQL)
```

### Import Workflow
```
CSV/Excel File
    ↓ Upload
Backend Parser
    ↓ Validation
Auto-categorization
    ↓ Save
Database + Import History
    ↓ Response
Desktop Client Update
```

### Search Workflow
```
User Types "COMP"
    ↓ API Call
Backend Search
    ↓ Query
Database ILIKE Search
    ↓ Results
Autocomplete Suggestions
```

## 📈 Performance

### Database Optimization
- Indexed columns: asset_no, serial_no, category, status
- Foreign key relationships
- Efficient queries with SQLAlchemy

### API Performance
- Connection pooling
- Async I/O (FastAPI/Uvicorn)
- Response caching opportunities
- Rate limiting

### Client Performance
- Lazy loading
- Pagination support
- Efficient table rendering
- Minimal API calls

## 🧪 Testing

### Test Coverage
- Authentication tests
- Equipment CRUD tests
- Search functionality tests
- Statistics endpoint tests
- Import functionality tests

### Running Tests
```bash
cd tests
pip install pytest requests
pytest test_api.py -v
```

## 📦 Dependencies

### Backend
- FastAPI - Web framework
- SQLAlchemy - ORM
- PostgreSQL - Database
- Pandas - CSV processing
- PyJWT - Authentication
- Bcrypt - Password hashing

### Frontend
- PyQt6 - GUI framework
- Requests - HTTP client

### Infrastructure
- Docker - Containerization
- Docker Compose - Orchestration
- Nginx - Reverse proxy
- PostgreSQL - Database

## 🛠️ Maintenance

### Daily
- Monitor logs: `docker-compose logs`
- Check disk space
- Review error rates

### Weekly
- Database backup: `./scripts/backup_database.sh`
- Review work logs
- Check import history

### Monthly
- Update dependencies
- Review security patches
- Analyze usage statistics
- Cleanup old data

## 📋 Checklists

### Before Production
- [ ] Change default admin password
- [ ] Configure secure JWT secret
- [ ] Set up SSL certificates
- [ ] Configure firewall rules
- [ ] Set up automated backups
- [ ] Test disaster recovery
- [ ] Configure monitoring
- [ ] Review security settings

### Regular Maintenance
- [ ] Check backup integrity
- [ ] Monitor disk usage
- [ ] Review audit logs
- [ ] Update system packages
- [ ] Test restore procedures
- [ ] Verify SSL certificates

## 🎓 Training Resources

1. **User Guide**: `docs/USER_GUIDE.md`
2. **API Documentation**: `http://server:8000/docs`
3. **README**: Main project documentation
4. **Sample Data**: CSV template in `sample_data/`

## 🔮 Future Enhancements

Potential additions:
- Email notifications
- Barcode scanning
- Mobile app
- Advanced reporting
- Integration with Active Directory
- Warranty tracking
- Maintenance scheduling
- Cost analytics
- Multi-location support
- Asset lifecycle management

## 📞 Support

For issues:
1. Check logs: `docker-compose logs backend`
2. Review user guide
3. Check API documentation
4. Verify configuration
5. Test database connection

## 📄 License

Production-grade application for internal IT asset management.

---

**Project Statistics**:
- Total Lines of Code: ~2000+
- Number of Files: 15+
- API Endpoints: 20+
- Database Tables: 6
- Features: 30+
- Documentation Pages: 3

**Technology Stack**:
- Backend: Python 3.11, FastAPI, SQLAlchemy
- Frontend: Python 3.11, PyQt6
- Database: PostgreSQL 15
- Deployment: Docker, Nginx
- Testing: Pytest
