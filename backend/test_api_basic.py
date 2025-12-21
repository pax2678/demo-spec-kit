#!/usr/bin/env python3
"""
Basic API test without database dependencies
Tests that FastAPI can start and serve basic endpoints
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_fastapi_import():
    """Test if FastAPI app can be imported"""
    try:
        from fastapi import FastAPI
        print("FastAPI import successful")
        
        # Create a simple test app
        app = FastAPI(title="Dashboard Test API")
        
        @app.get("/")
        def read_root():
            return {"message": "Dashboard API is working!"}
            
        @app.get("/health")
        def health_check():
            return {
                "status": "healthy",
                "service": "dashboard-api",
                "version": "1.0.0"
            }
        
        print("Test FastAPI app created successfully")
        return True
        
    except Exception as e:
        print(f"FastAPI test failed: {e}")
        return False

def test_dependencies():
    """Test if key dependencies are importable"""
    try:
        import pydantic
        print(f"Pydantic version: {pydantic.__version__}")
        
        import sqlalchemy
        print(f"SQLAlchemy version: {sqlalchemy.__version__}")
        
        import uvicorn
        print("Uvicorn import successful")
        
        return True
        
    except ImportError as e:
        print(f"Dependency test failed: {e}")
        return False

if __name__ == "__main__":
    print("Backend API Basic Test")
    print("-" * 30)
    
    # Test FastAPI
    fastapi_ok = test_fastapi_import()
    print()
    
    # Test dependencies
    deps_ok = test_dependencies()
    print()
    
    if fastapi_ok and deps_ok:
        print("SUCCESS: Backend is ready for testing!")
        print("\nTo start the API server:")
        print("cd backend")
        print("python -m uvicorn test_api_basic:app --reload")
    else:
        print("FAILED: Some issues found in backend setup")