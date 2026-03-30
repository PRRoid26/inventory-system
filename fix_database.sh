#!/bin/bash

# Quick fix for database initialization

echo "==========================================="
echo "Database Fix Script"
echo "==========================================="
echo ""

# Get database URL from environment or use default
if [ -z "$DATABASE_URL" ]; then
    echo "Please enter your database connection details:"
    read -p "Database name [fugro]: " DB_NAME
    DB_NAME=${DB_NAME:-fugro}
    read -p "Database user [admin]: " DB_USER
    DB_USER=${DB_USER:-admin}
    read -sp "Database password [admin123]: " DB_PASS
    DB_PASS=${DB_PASS:-admin123}
    echo ""
    export DATABASE_URL="postgresql://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME"
fi

echo "Using DATABASE_URL: $DATABASE_URL"
echo ""

# Navigate to backend and run Python to create tables
cd backend
source venv/bin/activate

echo "Creating database tables..."
python3 << 'PYTHON_SCRIPT'
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import bcrypt

# Import all models
from main import Base, User

DATABASE_URL = os.getenv("DATABASE_URL")

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

print("✓ Connecting to database...")
engine = create_engine(DATABASE_URL)

print("✓ Creating tables...")
Base.metadata.create_all(bind=engine)

print("✓ Creating admin user...")
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Check if admin exists
    existing = session.execute(text("SELECT id FROM users WHERE username = 'admin'")).first()
    
    if not existing:
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
        session.commit()
        print("✓ Admin user created!")
    else:
        print("✓ Admin user already exists")
    
    print("")
    print("==========================================")
    print("✅ Database initialized successfully!")
    print("==========================================")
    print("")
    print("Default credentials:")
    print("  Username: admin")
    print("  Password: admin123")
    print("")
    print("⚠️  Please change the default password after first login!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    session.rollback()
    sys.exit(1)
finally:
    session.close()

PYTHON_SCRIPT

deactivate
cd ..

echo ""
echo "Database is ready!"
echo ""
echo "To start the system:"
echo "  Backend:  ./start_backend.sh"
echo "  Frontend: ./start_frontend.sh"
echo ""
