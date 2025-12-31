#!/usr/bin/env python3
"""
Database initialization script
Creates the database and initial admin user
"""

import os
import sys
from getpass import getpass
from app import app, db
from models import Admin
from werkzeug.security import generate_password_hash


def init_database():
    """Initialize the database"""
    print("=" * 50)
    print("Course Management System - Database Initialization")
    print("=" * 50)
    print()
    
    with app.app_context():
        # Check if database already exists
        db_path = 'instance/course_management.db'
        if os.path.exists(db_path):
            response = input("Database already exists. Do you want to recreate it? (yes/no): ")
            if response.lower() != 'yes':
                print("Initialization cancelled.")
                return
            
            # Backup existing database
            backup_path = db_path + '.backup'
            if os.path.exists(backup_path):
                os.remove(backup_path)
            os.rename(db_path, backup_path)
            print(f"Existing database backed up to: {backup_path}")
        
        # Create instance directory if it doesn't exist
        os.makedirs('instance', exist_ok=True)
        
        # Create uploads directory
        os.makedirs('uploads', exist_ok=True)
        
        print("\nCreating database tables...")
        db.create_all()
        print("✓ Database tables created successfully!")
        
        # Create admin user
        print("\n" + "-" * 50)
        print("Create Admin User")
        print("-" * 50)
        
        # Check if admin already exists
        existing_admin = Admin.query.first()
        if existing_admin:
            print(f"Admin user already exists: {existing_admin.username}")
            response = input("Do you want to create another admin? (yes/no): ")
            if response.lower() != 'yes':
                print("\nDatabase initialization complete!")
                return
        
        # Get admin credentials
        while True:
            username = input("\nEnter admin username: ").strip()
            if not username:
                print("Username cannot be empty!")
                continue
            
            # Check if username exists
            if Admin.query.filter_by(username=username).first():
                print("Username already exists! Choose a different username.")
                continue
            
            break
        
        while True:
            email = input("Enter admin email: ").strip()
            if not email or '@' not in email:
                print("Please enter a valid email address!")
                continue
            
            # Check if email exists
            if Admin.query.filter_by(email=email).first():
                print("Email already exists! Choose a different email.")
                continue
            
            break
        
        while True:
            password = getpass("Enter admin password: ")
            if len(password) < 6:
                print("Password must be at least 6 characters long!")
                continue
            
            password_confirm = getpass("Confirm admin password: ")
            if password != password_confirm:
                print("Passwords do not match!")
                continue
            
            break
        
        # Create admin user
        admin = Admin(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print("\n✓ Admin user created successfully!")
        print(f"  Username: {username}")
        print(f"  Email: {email}")
        
        print("\n" + "=" * 50)
        print("Database initialization complete!")
        print("=" * 50)
        print("\nYou can now run the application with: python run.py")
        print(f"Admin login URL: http://localhost:5000/admin/login")
        print()


def reset_admin_password():
    """Reset admin password"""
    print("=" * 50)
    print("Reset Admin Password")    

print("=" * 50)
    print()
    
    with app.app_context():
        # List all admins
        admins = Admin.query.all()
        if not admins:
            print("No admin users found in database!")
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
                print("Invalid selection!")
                return
            
            admin = admins[index]
        except ValueError:
            print("Invalid input!")
            return
        
        print(f"\nResetting password for: {admin.username}")
        
        while True:
            password = getpass("Enter new password: ")
            if len(password) < 6:
                print("Password must be at least 6 characters long!")
                continue
            
            password_confirm = getpass("Confirm new password: ")
            if password != password_confirm:
                print("Passwords do not match!")
                continue
            
            break
        
        admin.password_hash = generate_password_hash(password)
        db.session.commit()
        
        print("\n✓ Password reset successfully!")
        print()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'reset-password':
        reset_admin_password()
    else:
        init_database()