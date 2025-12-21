#!/usr/bin/env python3
"""
Quick setup test for the dashboard implementation
Tests basic imports and structure without database dependencies
"""

import sys
import os
from pathlib import Path

# Add backend src to path
backend_src = Path(__file__).parent / "backend" / "src"
sys.path.insert(0, str(backend_src))

def test_backend_imports():
    """Test if backend modules can be imported"""
    print("🔍 Testing Backend Imports...")
    
    try:
        # Test core imports
        from config.settings import Settings
        print("✅ Settings import successful")
        
        from models.user import User
        print("✅ User model import successful")
        
        from models.metric_data import MetricData  
        print("✅ MetricData model import successful")
        
        from models.dashboard_widget import DashboardWidget
        print("✅ DashboardWidget model import successful")
        
        from services.user_service import UserService
        print("✅ UserService import successful")
        
        from services.metrics_service import MetricsService
        print("✅ MetricsService import successful")
        
        print("\n✅ All backend imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Backend import failed: {e}")
        return False

def test_frontend_structure():
    """Test if frontend files exist"""
    print("🔍 Testing Frontend Structure...")
    
    frontend_path = Path(__file__).parent / "frontend"
    required_files = [
        "package.json",
        "src/App.tsx", 
        "src/components/Dashboard.tsx",
        "src/components/Login.tsx",
        "src/components/MetricWidget.tsx",
        "src/components/MetricsGrid.tsx",
        "src/services/authService.ts",
        "src/services/dashboardService.ts",
        "src/contexts/AuthContext.tsx",
        "src/theme/theme.ts"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = frontend_path / file_path
        if full_path.exists():
            print(f"✅ Found: {file_path}")
        else:
            print(f"❌ Missing: {file_path}")
            missing_files.append(file_path)
    
    if not missing_files:
        print("\n✅ All frontend files found!")
        return True
    else:
        print(f"\n❌ Missing {len(missing_files)} frontend files")
        return False

def test_configuration_files():
    """Test if configuration files exist"""
    print("🔍 Testing Configuration Files...")
    
    root_path = Path(__file__).parent
    config_files = [
        "docker-compose.yml",
        "backend/requirements.txt", 
        "backend/Dockerfile",
        "frontend/package.json",
        "frontend/Dockerfile",
        "backend/pyproject.toml"
    ]
    
    for file_path in config_files:
        full_path = root_path / file_path
        if full_path.exists():
            print(f"✅ Found: {file_path}")
        else:
            print(f"❌ Missing: {file_path}")

def main():
    """Run all tests"""
    print("Dashboard Implementation Test")
    print("=" * 50)
    
    # Test backend
    backend_ok = test_backend_imports()
    print()
    
    # Test frontend
    frontend_ok = test_frontend_structure()
    print()
    
    # Test config
    test_configuration_files()
    print()
    
    # Summary
    if backend_ok and frontend_ok:
        print("🎉 Setup test PASSED!")
        print("\n📋 Next Steps:")
        print("1. Set up PostgreSQL/SQLite database")
        print("2. Run: uvicorn src.main:app --reload (in backend/)")
        print("3. Run: npm start (in frontend/)")
        print("4. Open: http://localhost:3000")
    else:
        print("❌ Setup test FAILED!")
        print("Please check the missing components above.")

if __name__ == "__main__":
    main()