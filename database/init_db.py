"""
Database initialization and migration script
"""

import os
import sys

# Add backend to path to import models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import bcrypt

# Import models to create tables
from main import Base, User, Equipment, Specification, WorkLog, CSVImport, AuditLog

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/inventory_db")

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def init_database():
    """Initialize database with default data"""
    
    engine = create_engine(DATABASE_URL)
    
    print("\n📋 Creating database tables...")
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully")
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Create default admin user
        check_user = session.execute(
            text("SELECT id FROM users WHERE username = 'admin'")
        ).first()
        
        if not check_user:
            session.execute(
                text("""
                    INSERT INTO users (username, email, password_hash, full_name, role)
                    VALUES (:username, :email, :password, :full_name, :role)
                """),
                {
                    "username": "admin",
                    "email": "admin@company.com",
                    "password": hash_password("admin123"),
                    "full_name": "System Administrator",
                    "role": "admin"
                }
            )
            print("✓ Created default admin user (username: admin, password: admin123)")
        
        # Create sample equipment categories
        categories = [
            'Computers', 'Network Equipment', 'Monitors', 'Printers & Scanners',
            'Servers', 'Mobile Devices', 'Tablets', 'Peripherals', 'Power & UPS',
            'Cables & Adapters', 'Other'
        ]
        
        print(f"✓ System supports {len(categories)} equipment categories")
        
        session.commit()
        print("\n✅ Database initialized successfully!")
        print("\nDefault credentials:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\n⚠️  Please change the default password after first login!")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error initializing database: {e}")
        raise
    finally:
        session.close()

def create_sample_data():
    """Create sample equipment data for testing"""
    
    # Import locally to avoid circular dependency
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
    from main import Equipment, Specification, SessionLocal
    
    session = SessionLocal()
    
    try:
        # Check if sample data already exists
        existing = session.query(Equipment).first()
        if existing:
            print("Sample data already exists. Skipping...")
            return
        
        # Sample equipment
        sample_equipment = [
            {
                'asset_no': 'COMP-001',
                'serial_no': 'SN12345678',
                'product_name': 'Dell OptiPlex 7090',
                'category': 'Computers',
                'status': 'Available',
                'location': 'IT Department',
                'supplier': 'Dell Inc.',
                'cost': 1200.00
            },
            {
                'asset_no': 'COMP-002',
                'serial_no': 'SN12345679',
                'product_name': 'HP EliteBook 850 G8',
                'category': 'Computers',
                'status': 'In Service',
                'location': 'Engineering',
                'supplier': 'HP Inc.',
                'cost': 1500.00
            },
            {
                'asset_no': 'NET-001',
                'serial_no': 'SN98765432',
                'product_name': 'Cisco Catalyst 2960-X',
                'category': 'Network Equipment',
                'status': 'Available',
                'location': 'Server Room',
                'supplier': 'Cisco Systems',
                'cost': 800.00
            },
            {
                'asset_no': 'MON-001',
                'serial_no': 'SN11223344',
                'product_name': 'Dell UltraSharp 27" U2720Q',
                'category': 'Monitors',
                'status': 'Available',
                'location': 'IT Department',
                'supplier': 'Dell Inc.',
                'cost': 450.00
            },
            {
                'asset_no': 'PRINT-001',
                'serial_no': 'SN55667788',
                'product_name': 'HP LaserJet Pro M404dn',
                'category': 'Printers & Scanners',
                'status': 'Available',
                'location': 'Office Floor 3',
                'supplier': 'HP Inc.',
                'cost': 350.00
            }
        ]
        
        for eq_data in sample_equipment:
            equipment = Equipment(**eq_data)
            session.add(equipment)
        
        session.commit()
        
        # Add sample specifications for first computer
        comp_1 = session.query(Equipment).filter(Equipment.asset_no == 'COMP-001').first()
        if comp_1:
            spec = Specification(
                equipment_id=comp_1.id,
                processor='Intel Core i7-11700 @ 2.5GHz',
                ram='32GB DDR4 3200MHz',
                storage='512GB NVMe SSD',
                graphics='Intel UHD Graphics 750',
                os='Windows 11 Pro',
                network='Gigabit Ethernet',
                additional_specs='Includes wireless keyboard and mouse'
            )
            session.add(spec)
            session.commit()
        
        print("✅ Sample data created successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error creating sample data: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("IT Asset Inventory Management System - Database Setup")
    print("=" * 60)
    
    init_database()
    
    if "--sample-data" in sys.argv:
        print("\nCreating sample data...")
        create_sample_data()
