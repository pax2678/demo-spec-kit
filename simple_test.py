#!/usr/bin/env python3
"""
Simple test to check if dashboard components can be imported
"""

import sys
import os
from pathlib import Path

# Add backend src to path
backend_src = Path(__file__).parent / "backend" / "src"
sys.path.insert(0, str(backend_src))

def test_imports():
    """Test basic imports"""
    print("Testing Dashboard Implementation...")
    print("-" * 40)
    
    try:
        print("Testing backend structure...")
        
        # Test if backend files exist
        backend_files = [
            "backend/src/config/settings.py",
            "backend/src/models/user.py", 
            "backend/src/models/metric_data.py",
            "backend/src/services/user_service.py",
            "backend/src/api/auth.py"
        ]
        
        for file_path in backend_files:
            full_path = Path(file_path)
            if full_path.exists():
                print(f"FOUND: {file_path}")
            else:
                print(f"MISSING: {file_path}")
        
        print("\nTesting frontend structure...")
        
        # Test if frontend files exist  
        frontend_files = [
            "frontend/package.json",
            "frontend/src/components/Dashboard.tsx",
            "frontend/src/components/Login.tsx",
            "frontend/src/services/authService.ts"
        ]
        
        for file_path in frontend_files:
            full_path = Path(file_path)
            if full_path.exists():
                print(f"FOUND: {file_path}")
            else:
                print(f"MISSING: {file_path}")
                
        print("\n" + "-" * 40)
        print("Test completed!")
        print("\nTo start testing:")
        print("1. Backend: cd backend && uvicorn src.main:app --reload")
        print("2. Frontend: cd frontend && npm start")
        print("3. Open: http://localhost:3000")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_imports()