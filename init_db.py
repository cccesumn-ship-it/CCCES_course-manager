#!/usr/bin/env python3
"""
Database initialization script
Works with both SQLite (local) and PostgreSQL (Render)
"""

import os
import sys
from getpass import getpass
from app import create_app, db
from models import Admin
from werkzeug.security import generate_password_hash


def init_database():
    """Initialize the database"""
    print("=" * 50)
    print("Course Management System - Database Initialization")
    print("=" * 50)
    print()
    
    # Create app with appropriate config
    config_name = os.environ.get('FLASK_CONFIG', 'default')
    app = create_app(config_name)
    
    with app.app_context():
        # Check database type
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        is_postgres = 'postgresql' in db_uri
        
        if is_postgres:
            print("✓ PostgreSQL database detected")
            print(f"  Connection: {db_uri.split('@')[1] if '@' in db_uri else 'configured'}")
        else:
            print("✓ SQLite database detected")
            db_path = 'instance/course_management.db'
            
            # Handle existing SQLite database
            if os.path.exists(db_path):
                response = input("\nDatabase already exists. Recreate it? (yes/no): ")
                if response.lower() != 'yes':
                    print("Initialization cancelled.")                  
  return
                
                # Backup existing database
                backup_path = db_path + '.backup'
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                os.rename(db_path, backup_path)
                print(f"✓ Existing database backed up to: {backup_path}")
            
            # Create instance directory if it doesn't exist
            os.makedirs('instance', exist_ok=True)
        
        # Create uploads directory
        os.makedirs('uploads', exist_ok=True)
        print("✓ Upload directory ready")
        
        print("\nCreating database tables...")
        try:
            db.create_all()
            print("✓ Database tables created successfully!")
        except Exception as e:
            print(f"✗ Error creating tables: {e}")
            print("\nTroubleshooting:")
            print("1. Check DATABASE_URL environment variable")
            print("2. Verify PostgreSQL database is accessible")
            print("3. Check network connectivity")
            return
        
        # Create admin user
        print("\n" + "-" * 50)
        print("Create Admin User")
        print("-" * 50)
        
        # Check if admin already exists
        existing_admin = Admin.query.first()
        if existing_admin:
            print(f"\n⚠ Admin user already exists: {existing_admin.username}")
            response = input("Create another admin? (yes/no): ")
            if response.lower() != 'yes':
                print("\n✓ Database initialization complete!")
                return
        
        # Get admin credentials
        print()
        while True:
            username = input("Enter admin username: ").strip()
            if not username:
                print("✗ Username cannot be empty!")
                continue
            
            # Check if username exists
            if Admin.query.filter_by(username=username).first():
                print("✗ Username already exists! Choose a different username.")
                continue
            
            if len(username) < 3:
                print("✗ Username must be at least 3 characters!")
                continue
            
            break
        
        while True:
            email = input("Enter admin email: ").strip()
            if not email or '@' not in email:
                print("✗ Please enter a valid email address!")
                continue
            
            # Check if email exists
            if Admin.query.filter_by(email=email).first():
                print("✗ Email already exists! Choose a different email.")
                continue
            
            break
        
        while True:
            password = getpass("Enter admin password (min 6 characters): ")
            if len(password) < 6:
                print("✗ Password must be at least 6 characters long!")
                continue
            
            password_confirm = getpass("Confirm admin password: ")
            if password != password_confirm:
                print("✗ Passwords do not match!")
                continue
            
            break
        
        # Create admin user
        try:
            admin = Admin(
                username=username,
                email=email,
                password_hash=generate_password_hash(password)
            )
            
            db.session.add(admin)
            db.session.commit()
            
            print("\n" + "=" * 50)
            print("✓ Admin user created successfully!")
            print("=" * 50)
            print(f"  Username: {username}")
            print(f"  Email: {email}")
            print()
            
            if is_postgres:
                print("PostgreSQL Database Ready!")
                print("Your app is ready to deploy on Render")
            else:
                print("SQLite Database Ready!")
                print("You can now run: python run.py")
            
            print()
            print("Admin login URL: /admin/login")
            print("=" * 50)
            print()
            
        except Exception as e:
            print(f"\n✗ Error creating admin user: {e}")
            db.session.rollback()

def reset_admin_password():
    """Reset admin password"""
    print("=" * 50)
    print("Reset Admin Password")
    print("=" * 50)
    print()
    
    # Create app with appropriate config
    config_name = os.environ.get('FLASK_CONFIG', 'default')
    app = create_app(config_name)
    
    with app.app_context():
        # List all admins
        try:
            admins = Admin.query.all()
        except Exception as e:
            print(f"✗ Error connecting to database: {e}")
            print("\nTroubleshooting:")
            print("1. Check DATABASE_URL environment variable")
            print("2. Verify database is accessible")
            return
        
        if not admins:
            print("✗ No admin users found in database!")
            print("Please run: python init_db.py")
            return
        
        print("Available admin users:")
        for i, admin in enumerate(admins, 1):
            print(f"{i}. {admin.username} ({admin.email})")
        
        print()
        choice = input("Enter the number of the admin to reset password (or 'q' to quit): ").strip()
        
        if choice.lower() == 'q':
            print("Password reset cancelled.")
            return
        
        try:
            index = int(choice) - 1
            if index < 0 or index >= len(admins):
                print("✗ Invalid selection!")
                return
            
            admin = admins[index]
        except ValueError:
            print("✗ Invalid input!")
            return
        
        print(f"\nResetting password for: {admin.username}")
        print()
        
        while True:
            password = getpass("Enter new password (min 6 characters): ")
            if len(password) < 6:
                print("✗ Password must be at least 6 characters long!")
                continue
            
            password_confirm = getpass("Confirm new password: ")
            if password != password_confirm:
                print("✗ Passwords do not match!")
                continue
            
            break
        
        try:
            admin.password_hash = generate_password_hash(password)
            db.session.commit()
            
            print("\n✓ Password reset successfully!")
            print()
        except Exception as e:
            print(f"\n✗ Error resetting password: {e}")
            db.session.rollback()


def test_connection():
    """Test database connection"""
    print("=" * 50)
    print("Test Database Connection")
    print("=" * 50)
    print()
    
    config_name = os.environ.get('FLASK_CONFIG', 'default')
    app = create_app(config_name)
    
    with app.app_context():
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        is_postgres = 'postgresql' in db_uri
        
        print(f"Database Type: {'PostgreSQL' if is_postgres else 'SQLite'}")
        print(f"Config: {config_name}")
        print()
        
        try:
            # Test connection
            result = db.session.execute(db.text("SELECT 1")).scalar()
            print("✓ Database connection successful!")
            
            # Check tables
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"✓ Found {len(tables)} tables: {', '.join(tables)}")
            
            # Check admin count
            admin_count = Admin.query.count()
            print(f"✓ Admin users: {admin_count}")
            
            print("\n✓ All checks passed!")
            
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            print("\nTroubleshooting:")
            print("1. Check DATABASE_URL is set correctly")
            print("2. Verify database server is running")            
print("3. Check network connectivity")
            print("4. Verify database credentials")
        
        print()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'reset-password':
            reset_admin_password()
        elif command == 'test':
            test_connection()
        else:
            print("Unknown command. Available commands:")
            print("  python init_db.py              - Initialize database")
            print("  python init_db.py reset-password - Reset admin password")
            print("  python init_db.py test         - Test database connection")
    else:
        init_database()