# 🚀 QUICK START GUIDE

## Get Running in 5 Minutes!

### Option 1: Automated Setup (Recommended)

```bash
cd inventory-system
chmod +x setup.sh
./setup.sh
```

Follow the prompts. The script will:
✅ Install all system dependencies
✅ Setup PostgreSQL database
✅ Create Python virtual environments
✅ Initialize database with admin user
✅ Create startup scripts

Then run:
```bash
./start_all.sh
```

### Option 2: Docker (Fastest)

```bash
cd inventory-system/docker
docker-compose up -d
docker-compose exec backend python /app/../database/init_db.py
```

Then launch the desktop client:
```bash
cd ../frontend
pip install -r requirements.txt
python main.py
```

### Default Credentials
- **Username**: admin
- **Password**: admin123
- ⚠️ **Change this immediately!**

### What You Get

✅ **Backend API** running on http://localhost:8000
✅ **PostgreSQL Database** with complete schema
✅ **Qt Desktop Client** with full GUI
✅ **API Documentation** at http://localhost:8000/docs

### Key Features Ready to Use

1. **Import Equipment**: Drop your CSV/Excel files
2. **Search Assets**: Type first few letters for autocomplete
3. **Track Work**: Check out/in equipment
4. **View Statistics**: Real-time dashboard
5. **Manage Specs**: Add detailed specifications
6. **Import History**: All imports saved permanently

### Quick Test

1. Login with admin credentials
2. Go to Inventory tab
3. Click "Import CSV/Excel"
4. Select `sample_data/equipment_template.csv`
5. See 15 sample items imported!

### Files You Need

```
inventory-system/
├── setup.sh              ← Run this first
├── README.md            ← Full documentation
├── docs/
│   ├── USER_GUIDE.md    ← How to use the system
│   └── PROJECT_STRUCTURE.md  ← Technical details
├── backend/main.py      ← API server (750 lines)
├── frontend/main.py     ← Desktop app (1100 lines)
└── sample_data/         ← CSV template
```

### Troubleshooting

**PostgreSQL not starting?**
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Desktop client won't connect?**
- Check backend is running: `curl http://localhost:8000`
- Verify server URL in client settings

**Import fails?**
- Check CSV format matches template
- Ensure required columns: asset_no, product_name

### Next Steps

1. ✅ Change default password
2. ✅ Import your equipment data
3. ✅ Add specifications to key equipment
4. ✅ Create work logs for tracking
5. ✅ Deploy to cloud for remote access

### For Cloud Deployment

See README.md section "Cloud Deployment" for:
- AWS/Azure/GCP setup
- SSL certificate configuration
- Domain setup
- Remote access

### Getting Help

- 📖 User Guide: `docs/USER_GUIDE.md`
- 🔧 API Docs: http://localhost:8000/docs
- 📋 Project Info: `docs/PROJECT_STRUCTURE.md`

---

**You're all set!** 🎉

Your production-grade IT asset management system is ready to use.
