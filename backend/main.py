"""
IT Asset Inventory Management System - Backend API
Production-ready FastAPI server with PostgreSQL, authentication, and cloud deployment support

FIXED: Worklog creation no longer overrides equipment status
FIXED: Equipment response now includes csv_import_id for proper Excel filename display
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
import bcrypt
import pandas as pd
import io
import os
from pathlib import Path
import json
import uuid
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/inventory_db")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Database setup
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"sslmode": "disable"}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Security
security = HTTPBearer()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), default="user")  # admin, manager, user
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

class Equipment(Base):
    __tablename__ = "equipment"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_no = Column(String(50), unique=True, nullable=False, index=True)
    serial_no = Column(String(100), index=True)
    product_name = Column(String(200), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    status = Column(String(20), default="Available")  # Available, In Service, Faulty, Retired
    location = Column(String(100))
    purchase_date = Column(DateTime)
    warranty_expiry = Column(DateTime)
    cost = Column(Float)
    supplier = Column(String(100))
    csv_import_id = Column(Integer, ForeignKey("csv_imports.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    specifications = relationship("Specification", back_populates="equipment", cascade="all, delete-orphan")
    work_logs = relationship("WorkLog", back_populates="equipment")
    csv_import = relationship("CSVImport", back_populates="equipment_items")

class Specification(Base):
    __tablename__ = "specifications"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    spec_data = Column(JSON)  # Flexible JSON field for any specifications
    processor = Column(String(100))
    ram = Column(String(50))
    storage = Column(String(100))
    graphics = Column(String(100))
    os = Column(String(100))
    network = Column(String(100))
    additional_specs = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    equipment = relationship("Equipment", back_populates="specifications")

class WorkLog(Base):
    __tablename__ = "work_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    job_name = Column(String(200))
    location = Column(String(100))
    department = Column(String(100))
    designation = Column(String(100))
    check_out_date = Column(DateTime)
    expected_return_date = Column(DateTime)
    actual_return_date = Column(DateTime)
    current_status = Column(String(20), default="In Progress")  # In Progress, Completed, On Hold
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    equipment = relationship("Equipment", back_populates="work_logs")

class CSVImport(Base):
    __tablename__ = "csv_imports"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    import_date = Column(DateTime, default=datetime.utcnow)
    imported_by = Column(Integer, ForeignKey("users.id"))
    total_records = Column(Integer)
    successful_records = Column(Integer)
    failed_records = Column(Integer)
    file_path = Column(String(500))  # Store the file for future reference
    notes = Column(Text)
    
    equipment_items = relationship("Equipment", back_populates="csv_import")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(50))  # CREATE, UPDATE, DELETE, LOGIN, etc.
    entity_type = Column(String(50))  # Equipment, User, WorkLog, etc.
    entity_id = Column(Integer)
    changes = Column(JSON)
    ip_address = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic Models
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    role: str = "user"

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class EquipmentCreate(BaseModel):
    asset_no: str
    serial_no: Optional[str] = None
    product_name: str
    category: str
    status: str = "Available"
    location: Optional[str] = None
    purchase_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    cost: Optional[float] = None
    supplier: Optional[str] = None

class EquipmentUpdate(BaseModel):
    serial_no: Optional[str] = None
    product_name: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    purchase_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    cost: Optional[float] = None
    supplier: Optional[str] = None

class EquipmentResponse(BaseModel):
    id: int
    asset_no: str
    serial_no: Optional[str]
    product_name: str
    category: str
    status: str
    location: Optional[str]
    purchase_date: Optional[datetime]
    warranty_expiry: Optional[datetime]
    cost: Optional[float]
    supplier: Optional[str]
    csv_import_id: Optional[int]  # ADDED: This is the fix!
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ImportResponse(BaseModel):
    id: int
    filename: str
    import_date: Optional[datetime]
    total_records: Optional[int]
    successful_records: Optional[int]
    failed_records: Optional[int]
    notes: Optional[str]

    class Config:
        from_attributes = True

class SpecificationCreate(BaseModel):
    equipment_id: int
    processor: Optional[str] = None
    ram: Optional[str] = None
    storage: Optional[str] = None
    graphics: Optional[str] = None
    os: Optional[str] = None
    network: Optional[str] = None
    additional_specs: Optional[str] = None
    spec_data: Optional[Dict[str, Any]] = None

class SpecificationUpdate(BaseModel):
    processor: Optional[str] = None
    ram: Optional[str] = None
    storage: Optional[str] = None
    graphics: Optional[str] = None
    os: Optional[str] = None
    network: Optional[str] = None
    additional_specs: Optional[str] = None
    spec_data: Optional[Dict[str, Any]] = None

class WorkLogCreate(BaseModel):
    equipment_id: int
    job_name: Optional[str] = ""
    location: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    check_out_date: Optional[datetime] = None
    expected_return_date: Optional[datetime] = None
    current_status: str = "In Progress"
    notes: Optional[str] = None

class WorkLogUpdate(BaseModel):
    job_name: Optional[str] = None
    location: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    expected_return_date: Optional[datetime] = None
    actual_return_date: Optional[datetime] = None
    current_status: Optional[str] = None
    notes: Optional[str] = None

# FastAPI App
app = FastAPI(
    title="IT Asset Inventory Management System",
    description="Production-ready inventory management with cloud deployment support",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authentication helpers
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user

# API Endpoints

@app.get("/")
def root():
    return {"message": "IT Asset Inventory Management System API", "version": "1.0.0"}

@app.post("/api/auth/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    if db.query(User).filter((User.username == user.username) | (User.email == user.email)).first():
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    # Create user
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password),
        full_name=user.full_name,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create token
    access_token = create_access_token(data={"sub": db_user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    if not db_user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")
    
    # Update last login
    db_user.last_login = datetime.utcnow()
    db.commit()
    
    access_token = create_access_token(data={"sub": db_user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role
    }

# Equipment endpoints
@app.post("/api/equipment", response_model=EquipmentResponse)
def create_equipment(
    equipment: EquipmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if asset number already exists
    if db.query(Equipment).filter(Equipment.asset_no == equipment.asset_no).first():
        raise HTTPException(status_code=400, detail="Asset number already exists")
    
    db_equipment = Equipment(**equipment.dict())
    db.add(db_equipment)
    db.commit()
    db.refresh(db_equipment)
    
    logger.info(f"Equipment created: {equipment.asset_no} by user {current_user.username}")
    return db_equipment

@app.get("/api/equipment", response_model=List[EquipmentResponse])
def get_equipment(
    skip: int = 0,
    limit: int = 500,
    category: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    import_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Equipment)

    if import_id is not None:
        # Collect all import IDs with same filename (handles re-imports of same file)
        matched_import = db.query(CSVImport).filter(CSVImport.id == import_id).first()
        if matched_import:
            all_ids = db.query(CSVImport.id).filter(
                CSVImport.filename == matched_import.filename
            ).all()
            all_ids = [r[0] for r in all_ids]
            query = query.filter(Equipment.csv_import_id.in_(all_ids))
        else:
            query = query.filter(Equipment.csv_import_id == import_id)
    if category:
        query = query.filter(Equipment.category == category)
    if status:
        query = query.filter(Equipment.status == status)
    if search:
        query = query.filter(
            (Equipment.asset_no.ilike(f"%{search}%")) |
            (Equipment.product_name.ilike(f"%{search}%")) |
            (Equipment.serial_no.ilike(f"%{search}%"))
        )

    return query.order_by(Equipment.asset_no).offset(skip).limit(limit).all()

@app.get("/api/equipment/search/{asset_prefix}")
def search_equipment_by_asset(
    asset_prefix: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Auto-suggest equipment based on asset number prefix or contains"""
    equipment = db.query(Equipment).filter(
        Equipment.asset_no.ilike(f"%{asset_prefix}%")
    ).limit(10).all()
    
    return [{"asset_no": e.asset_no, "product_name": e.product_name, "id": e.id} for e in equipment]

@app.get("/api/equipment/{equipment_id}", response_model=EquipmentResponse)
def get_equipment_by_id(
    equipment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return equipment

@app.put("/api/equipment/{equipment_id}", response_model=EquipmentResponse)
def update_equipment(
    equipment_id: int,
    equipment: EquipmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not db_equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    update_data = equipment.dict(exclude_unset=True)
    old_status = db_equipment.status
    
    for field, value in update_data.items():
        setattr(db_equipment, field, value)
    
    db.commit()
    db.refresh(db_equipment)
    
    new_status = db_equipment.status
    if old_status != new_status:
        logger.info(f"Equipment {db_equipment.asset_no} status changed: {old_status} -> {new_status} by {current_user.username}")
    
    return db_equipment

@app.delete("/api/equipment/{equipment_id}")
def delete_equipment(
    equipment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not db_equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    asset_no = db_equipment.asset_no
    db.delete(db_equipment)
    db.commit()
    
    logger.info(f"Equipment deleted: {asset_no} by user {current_user.username}")
    return {"message": "Equipment deleted successfully"}

# Specifications endpoints
@app.post("/api/specifications")
def create_specification(
    spec: SpecificationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if equipment exists
    equipment = db.query(Equipment).filter(Equipment.id == spec.equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    db_spec = Specification(**spec.dict())
    db.add(db_spec)
    db.commit()
    db.refresh(db_spec)
    return db_spec

@app.get("/api/specifications/{equipment_id}")
def get_specifications(
    equipment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    specs = db.query(Specification).filter(Specification.equipment_id == equipment_id).all()
    return specs

@app.put("/api/specifications/{spec_id}")
def update_specification(
    spec_id: int,
    spec: SpecificationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_spec = db.query(Specification).filter(Specification.id == spec_id).first()
    if not db_spec:
        raise HTTPException(status_code=404, detail="Specification not found")
    
    update_data = spec.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_spec, field, value)
    
    db.commit()
    db.refresh(db_spec)
    return db_spec

# Work logs endpoints
@app.post("/api/worklogs")
def create_worklog(
    worklog: WorkLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a work log entry.
    
    IMPORTANT: This endpoint does NOT automatically change equipment status.
    Equipment status should be managed separately via the equipment update endpoint.
    The worklog is purely a historical record of device usage and status changes.
    """
    equipment = db.query(Equipment).filter(Equipment.id == worklog.equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    db_worklog = WorkLog(**worklog.dict(), created_by=current_user.id)
    
    db.add(db_worklog)
    db.commit()
    db.refresh(db_worklog)
    
    logger.info(f"Worklog created for equipment {equipment.asset_no}: {worklog.job_name} by {current_user.username}")
    return db_worklog

@app.get("/api/worklogs")
def get_worklogs(
    skip: int = 0,
    limit: int = 100,
    equipment_id: Optional[int] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(WorkLog)
    
    if equipment_id:
        query = query.filter(WorkLog.equipment_id == equipment_id)
    if status:
        query = query.filter(WorkLog.current_status == status)
    
    return query.order_by(WorkLog.created_at.desc()).offset(skip).limit(limit).all()

@app.put("/api/worklogs/{worklog_id}")
def update_worklog(
    worklog_id: int,
    worklog: WorkLogUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a work log entry.
    
    Note: This endpoint updates the worklog record only.
    If you need to change equipment status, use the equipment update endpoint.
    """
    db_worklog = db.query(WorkLog).filter(WorkLog.id == worklog_id).first()
    if not db_worklog:
        raise HTTPException(status_code=404, detail="Work log not found")
    
    update_data = worklog.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_worklog, field, value)
    
    db.commit()
    db.refresh(db_worklog)
    
    logger.info(f"Worklog {worklog_id} updated by {current_user.username}")
    return db_worklog

# CSV Import endpoints
@app.post("/api/import/csv")
async def import_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Import equipment from CSV or Excel (.xlsx/.xls).

    Handles real-world files:
    - Multiple sheets in one workbook (all non-empty sheets are processed)
    - Headers like 'Asset no.', 'Serial No', 'Product Name' (dots, spaces, mixed case)
    - Serial numbers that look numeric (e.g. '37,507') — kept as strings
    - Missing optional columns (status, location, supplier, cost) → sensible defaults
    - Sheet4-style extended columns: 'Current status', 'job name', 'IN', 'OUT'
    - CSV with any common encoding (UTF-8, Latin-1, cp1252)
    """
    fname = (file.filename or "").strip()
    if not fname.lower().endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400,
            detail="Only CSV and Excel files are supported (.csv, .xlsx, .xls)")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # Save original file for import history
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    file_path = upload_dir / f"{uuid.uuid4()}_{fname}"
    file_path.write_bytes(content)

    # Column alias table
    ALIASES: Dict[str, List[str]] = {
        'asset_no':       ['assetno', 'asset_no', 'assetnumber', 'assetnum',
                           'assettag', 'tag', 'asset#', 'asset'],
        'serial_no':      ['serialno', 'serial_no', 'serialnumber', 'serialnum',
                           'serial#', 'sn'],
        'product_name':   ['productname', 'product_name', 'name', 'itemname',
                           'item_name', 'description', 'model', 'product',
                           'equipment', 'item'],
        'status':         ['status', 'condition', 'state', 'currentstatus',
                           'current_status'],
        'category':       ['category', 'type', 'equipmenttype', 'itemtype'],
        'location':       ['location', 'loc', 'site', 'room', 'department', 'dept'],
        'supplier':       ['supplier', 'vendor', 'manufacturer', 'brand'],
        'cost':           ['cost', 'price', 'value', 'purchaseprice'],
        'job_name':       ['jobname', 'job_name', 'job', 'jobname'],
        'check_out_date': ['date', 'checkoutdate', 'checkout_date', 'outdate', 'out'],
        'in_date':        ['in', 'indate', 'in_date', 'returndate', 'return_date'],
    }

    def normalise_header(h: str) -> str:
        """Strip, lowercase, remove dots/spaces/underscores/hashes."""
        import re
        return re.sub(r'[\s._#]+', '', str(h).strip().lower())

    def build_col_map(columns) -> Dict[str, Optional[str]]:
        """Return {std_name: actual_column_name_in_df} for every alias match."""
        norm2actual = {normalise_header(c): c for c in columns}
        result = {}
        for std, aliases in ALIASES.items():
            result[std] = None
            for alias in aliases:
                if alias in norm2actual:
                    result[std] = norm2actual[alias]
                    break
        return result

    def safe_cell(row, col_map: Dict, std_name: str, default: str = '') -> str:
        col = col_map.get(std_name)
        if col is None:
            return default
        val = row.get(col, default)
        if pd.isna(val) if not isinstance(val, str) else False:
            return default
        s = str(val).strip()
        return default if s.lower() in ('nan', 'none', '') else s

    # Load all sheets into a list of DataFrames
    sheet_frames: List[pd.DataFrame] = []
    try:
        if fname.lower().endswith('.csv'):
            for enc in ('utf-8', 'utf-8-sig', 'latin-1', 'cp1252'):
                try:
                    df_single = pd.read_csv(io.BytesIO(content), encoding=enc, dtype=str)
                    sheet_frames.append(df_single)
                    break
                except UnicodeDecodeError:
                    continue
            if not sheet_frames:
                raise ValueError("Could not decode CSV. Try saving as UTF-8.")
        else:
            # Excel — load every sheet; keep only sheets that have data rows
            all_sheets: Dict[str, pd.DataFrame] = pd.read_excel(
                io.BytesIO(content),
                sheet_name=None,
                dtype=str,
                header=0
            )
            for sheet_name, sdf in all_sheets.items():
                sdf = sdf.dropna(how='all')
                sdf = sdf.loc[:, sdf.notna().any()]
                if sdf.empty:
                    continue
                norm_cols = [normalise_header(c) for c in sdf.columns]
                has_asset = any(a in norm_cols for a in ALIASES['asset_no'])
                has_product = any(a in norm_cols for a in ALIASES['product_name'])
                if has_asset or has_product:
                    sheet_frames.append(sdf)

    except Exception as e:
        logger.error(f"CSV import error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Could not read file: {str(e)}")

    if not sheet_frames:
        raise HTTPException(status_code=400,
            detail="No usable sheets found. Expected columns like "
                   "'Asset no.', 'Serial No', 'Product Name'.")

    # Create one import record for the whole file
    total_rows = sum(len(f) for f in sheet_frames)
    csv_import = CSVImport(
        filename=fname,
        imported_by=current_user.id,
        total_records=total_rows,
        file_path=str(file_path)
    )
    db.add(csv_import)
    db.commit()
    db.refresh(csv_import)

    # Process every sheet
    successful = 0
    failed = 0
    errors: List[str] = []
    VALID_STATUSES = {'Available', 'In Service', 'Faulty', 'Retired'}

    for sdf in sheet_frames:
        col_map = build_col_map(sdf.columns)

        if not col_map.get('asset_no') and not col_map.get('product_name'):
            errors.append(f"Sheet skipped — no asset_no or product_name column found. "
                          f"Columns: {list(sdf.columns)}")
            failed += len(sdf)
            continue

        for idx, row in sdf.iterrows():
            try:
                asset_no = safe_cell(row, col_map, 'asset_no')
                if not asset_no:
                    asset_no = safe_cell(row, col_map, 'product_name')
                if not asset_no:
                    errors.append(f"Row {idx + 2}: no asset_no, skipped")
                    failed += 1
                    continue

                product_name = safe_cell(row, col_map, 'product_name') or asset_no

                explicit_cat = safe_cell(row, col_map, 'category')
                category = explicit_cat if explicit_cat else categorize_equipment(product_name)

                raw_status = safe_cell(row, col_map, 'status', 'Available')
                status_norm = raw_status.strip().title()
                STATUS_MAP = {
                    'In Service': ['In Service', 'Inservice', 'In-Service', 'In Use',
                                   'Checked Out', 'Deployed'],
                    'Faulty':     ['Faulty', 'Fault', 'Broken', 'Damaged', 'Repair',
                                   'Under Repair'],
                    'Retired':    ['Retired', 'Decommissioned', 'Disposed', 'Written Off'],
                    'Available':  ['Available', 'Free', 'In Stock', 'Ready'],
                }
                mapped_status = 'Available'
                for canonical, variants in STATUS_MAP.items():
                    if any(raw_status.lower() == v.lower() for v in variants):
                        mapped_status = canonical
                        break

                equipment_data: Dict[str, Any] = {
                    'asset_no':      asset_no,
                    'serial_no':     safe_cell(row, col_map, 'serial_no'),
                    'product_name':  product_name,
                    'category':      category,
                    'status':        mapped_status,
                    'location':      safe_cell(row, col_map, 'location'),
                    'supplier':      safe_cell(row, col_map, 'supplier'),
                    'csv_import_id': csv_import.id,
                }

                cost_str = safe_cell(row, col_map, 'cost')
                if cost_str:
                    try:
                        equipment_data['cost'] = float(
                            cost_str.replace(',', '').replace('$', '').strip()
                        )
                    except ValueError:
                        pass

                # Upsert: update if already exists, insert if new
                existing = db.query(Equipment).filter(
                    Equipment.asset_no == asset_no
                ).first()
                if existing:
                    for key, value in equipment_data.items():
                        if key != 'csv_import_id' and value not in ('', None):
                            setattr(existing, key, value)
                else:
                    db.add(Equipment(**equipment_data))

                successful += 1

            except Exception as e:
                failed += 1
                errors.append(f"Row {idx + 2}: {str(e)}")
                logger.error(f"Import error on row {idx + 2}: {str(e)}")

    csv_import.successful_records = successful
    csv_import.failed_records = failed
    db.commit()

    logger.info(f"CSV import completed: {fname} by {current_user.username} - {successful} successful, {failed} failed")

    return {
        "message": "Import completed",
        "import_id": csv_import.id,
        "total_records": total_rows,
        "successful": successful,
        "failed": failed,
        "errors": errors[:20]
    }

@app.get("/api/imports", response_model=List[ImportResponse])
def get_imports(
    skip: int = 0,
    limit: int = 200,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all CSV import history"""
    imports = db.query(CSVImport).order_by(CSVImport.import_date.desc()).offset(skip).limit(limit).all()
    return imports

@app.get("/api/imports/{import_id}")
def get_import_details(
    import_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific CSV import"""
    csv_import = db.query(CSVImport).filter(CSVImport.id == import_id).first()
    if not csv_import:
        raise HTTPException(status_code=404, detail="Import not found")
    
    # Get equipment imported from this CSV
    equipment = db.query(Equipment).filter(Equipment.csv_import_id == import_id).all()
    
    return {
        "import_info": csv_import,
        "equipment_count": len(equipment),
        "equipment": equipment
    }

@app.delete("/api/imports/{import_id}")
def delete_import(
    import_id: int,
    delete_equipment: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete CSV import record and optionally its equipment"""
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    csv_import = db.query(CSVImport).filter(CSVImport.id == import_id).first()
    if not csv_import:
        raise HTTPException(status_code=404, detail="Import not found")
    
    if delete_equipment:
        # Delete all equipment from this import
        db.query(Equipment).filter(Equipment.csv_import_id == import_id).delete()
    else:
        # Just remove the link
        db.query(Equipment).filter(Equipment.csv_import_id == import_id).update({"csv_import_id": None})
    
    db.delete(csv_import)
    db.commit()
    
    logger.info(f"Import deleted: {csv_import.filename} by {current_user.username}")
    return {"message": "Import deleted successfully"}

# Statistics endpoints
@app.get("/api/stats/overview")
def get_overview_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overall inventory statistics"""
    total = db.query(Equipment).count()
    available = db.query(Equipment).filter(Equipment.status == "Available").count()
    in_service = db.query(Equipment).filter(Equipment.status == "In Service").count()
    faulty = db.query(Equipment).filter(Equipment.status == "Faulty").count()
    retired = db.query(Equipment).filter(Equipment.status == "Retired").count()
    
    return {
        "total": total,
        "available": available,
        "in_service": in_service,
        "faulty": faulty,
        "retired": retired
    }

@app.get("/api/stats/category")
def get_category_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get statistics by category"""
    from sqlalchemy import func, case
    
    stats = db.query(
        Equipment.category,
        func.count(Equipment.id).label('total'),
        func.sum(case((Equipment.status == 'Available', 1), else_=0)).label('available'),
        func.sum(case((Equipment.status == 'In Service', 1), else_=0)).label('in_service'),
        func.sum(case((Equipment.status == 'Faulty', 1), else_=0)).label('faulty'),
        func.sum(case((Equipment.status == 'Retired', 1), else_=0)).label('retired')
    ).group_by(Equipment.category).all()
    
    return [
        {
            "category": s.category,
            "total": s.total,
            "available": s.available or 0,
            "in_service": s.in_service or 0,
            "faulty": s.faulty or 0,
            "retired": s.retired or 0
        }
        for s in stats
    ]

@app.get("/api/stats/category/{category}")
def get_category_equipment_stats(
    category: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get equipment breakdown for a specific category"""
    from sqlalchemy import func, case
    
    stats = db.query(
        Equipment.product_name,
        func.count(Equipment.id).label('total'),
        func.sum(case((Equipment.status == 'Available', 1), else_=0)).label('available'),
        func.sum(case((Equipment.status == 'In Service', 1), else_=0)).label('in_service'),
        func.sum(case((Equipment.status == 'Faulty', 1), else_=0)).label('faulty'),
        func.sum(case((Equipment.status == 'Retired', 1), else_=0)).label('retired')
    ).filter(Equipment.category == category).group_by(Equipment.product_name).all()
    
    return [
        {
            "product_name": s.product_name,
            "total": s.total,
            "available": s.available or 0,
            "in_service": s.in_service or 0,
            "faulty": s.faulty or 0,
            "retired": s.retired or 0
        }
        for s in stats
    ]

# Helper functions
def categorize_equipment(name: str) -> str:
    """
    Auto-categorize equipment based on product name.
    Handles verbose names like 'COMPUTER DESKTOP DELL OPTIPLEX 7050 I7'
    or 'VGA SPLITTER/MULTIPLIER'.
    """
    n = name.lower()

    # Computers / laptops / workstations
    if any(w in n for w in ['computer', 'laptop', 'notebook', 'desktop', 'workstation',
                             'pc ', 'optiplex', 'elitebook', 'thinkpad', 'inspiron',
                             'latitude', 'probook', 'all-in-one', 'nuc', 'mini tower',
                             'micro tower', 'pro mini']):
        return 'Computers'

    # Servers
    if any(w in n for w in ['server', 'poweredge', 'proliant', 'rack', 'blade']):
        return 'Servers'

    # Network equipment
    if any(w in n for w in ['switch', 'router', 'firewall', 'access point', ' ap ',
                             'wifi', 'wi-fi', 'wireless', 'gateway', 'modem', 'hub',
                             'patch panel', 'sfp', 'transceiver']):
        return 'Network Equipment'

    # Monitors / displays
    if any(w in n for w in ['monitor', 'display', 'screen', 'lcd', 'led monitor',
                             'ultrasharp', 'flat panel']):
        return 'Monitors'

    # Printers / scanners
    if any(w in n for w in ['printer', 'scanner', 'copier', 'mfp', 'laserjet',
                             'deskjet', 'inkjet', 'plotter', 'multifunction']):
        return 'Printers & Scanners'

    # Mobile devices
    if any(w in n for w in ['phone', 'mobile', 'smartphone', 'iphone', 'android',
                             'handset', 'cellular']):
        return 'Mobile Devices'

    # Tablets
    if any(w in n for w in ['tablet', 'ipad', 'surface ']):
        return 'Tablets'

    # Peripherals
    if any(w in n for w in ['keyboard', 'mouse', 'webcam', 'headset', 'speaker',
                             'microphone', 'numpad', 'trackpad', 'stylus']):
        return 'Peripherals'

    # AV / Video
    if any(w in n for w in ['splitter', 'vga', 'dvi', 'hdmi', 'displayport',
                             'video splitter', 'multiplier', 'extender', 'kvm',
                             'converter', 'adapter', 'av ']):
        return 'AV & Video Equipment'

    # Cables & Adapters
    if any(w in n for w in ['cable', 'dongle', 'usb hub', 'docking', 'dock']):
        return 'Cables & Adapters'

    # Power / UPS
    if any(w in n for w in ['ups', 'battery', 'power supply', 'pdu', 'surge']):
        return 'Power & UPS'

    # Storage
    if any(w in n for w in ['hard disk', 'hdd', 'ssd', 'nas', 'storage', 'drive',
                             'flash', 'pendrive', 'pen drive', 'usb drive']):
        return 'Storage Devices'

    return 'Other'

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)