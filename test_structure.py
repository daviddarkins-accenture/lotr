#!/usr/bin/env python3
"""
Test script to validate project structure and basic imports
This doesn't require .env or API credentials
"""

import sys
import os
from pathlib import Path

def test_file_structure():
    """Test that all required files exist"""
    print("🔍 Testing project structure...")
    
    required_files = [
        'app.py',
        'auth.py',
        'config.py',
        'deletion.py',
        'ingestion.py',
        'lotr_client.py',
        'setup.py',
        'requirements.txt',
        'README.md',
        '.gitignore',
        'templates/index.html',
        'static/style.css',
        'static/app.js',
        'static/bg.png'
    ]
    
    missing = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing.append(file_path)
        else:
            print(f"  ✅ {file_path}")
    
    if missing:
        print(f"\n❌ Missing files: {missing}")
        return False
    
    print("\n✅ All required files present!")
    return True


def test_imports():
    """Test that Python modules can be imported (without executing)"""
    print("\n🔍 Testing Python module structure...")
    
    try:
        # Test config (will fail validation, but import should work)
        import config
        print("  ✅ config.py structure valid")
        
        # Test that Config class exists
        assert hasattr(config, 'Config')
        assert hasattr(config.Config, 'validate')
        print("  ✅ Config class has validate method")
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except Exception as e:
        # Expected - config validation will fail without .env
        if "Configuration Incomplete" in str(e):
            print("  ✅ Config validation works (expected to fail without .env)")
        else:
            print(f"  ⚠️  Unexpected error (may be OK): {e}")
    
    try:
        # Test auth module structure
        import auth
        assert hasattr(auth, 'DataCloudAuth')
        assert hasattr(auth, 'get_auth')
        print("  ✅ auth.py structure valid")
        
        # Test lotr_client structure
        import lotr_client
        assert hasattr(lotr_client, 'LOTRClient')
        assert hasattr(lotr_client, 'fetch_characters')
        print("  ✅ lotr_client.py structure valid")
        
        # Test ingestion structure
        import ingestion
        assert hasattr(ingestion, 'ingest_lotr_data')
        print("  ✅ ingestion.py structure valid")
        
        # Test deletion structure
        import deletion
        assert hasattr(deletion, 'delete_lotr_data')
        print("  ✅ deletion.py structure valid")
        
        print("\n✅ All Python modules have correct structure!")
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except AssertionError as e:
        print(f"  ❌ Missing required function or class: {e}")
        return False


def test_requirements():
    """Test that requirements.txt is valid"""
    print("\n🔍 Testing requirements.txt...")
    
    try:
        with open('requirements.txt', 'r') as f:
            lines = f.readlines()
        
        required_packages = ['Flask', 'requests', 'python-dotenv']
        found_packages = [line.split('==')[0].strip() for line in lines if '==' in line]
        
        for pkg in required_packages:
            if pkg in found_packages:
                print(f"  ✅ {pkg} specified")
            else:
                print(f"  ❌ {pkg} missing")
                return False
        
        print("\n✅ Requirements file valid!")
        return True
        
    except Exception as e:
        print(f"  ❌ Error reading requirements.txt: {e}")
        return False


def main():
    """Run all tests"""
    print("""
╔════════════════════════════════════════════════════════════╗
║  🧙‍♂️  LOTR POC Structure Validation                        ║
║  "One does not simply skip validation..."                 ║
╚════════════════════════════════════════════════════════════╝
""")
    
    results = []
    
    results.append(test_file_structure())
    results.append(test_imports())
    results.append(test_requirements())
    
    print("\n" + "="*60)
    
    if all(results):
        print("""
✅ All validation checks passed!

The structure is ready for Gandalf's configuration wizard.

Next steps:
  1. Run: python setup.py
  2. Configure your environment variables
  3. Run: python app.py
  4. Open: http://localhost:5000

May the light of Eärendil guide your journey! 🌟
""")
        return 0
    else:
        print("""
❌ Some validation checks failed.

Please review the errors above and fix them before proceeding.

"Even the wisest cannot see all ends." - Gandalf
""")
        return 1


if __name__ == '__main__':
    sys.exit(main())

