# Backend Integration Fix - Documentation

## Overview
This document explains the fixes applied to resolve all backend and frontend integration issues in the ASFS project.

## Problems Solved

### 1. Broken Import: `from config import model as config_model`
**Issue**: The backend was trying to import a Python module called `config` with a variable `model`, but no such module existed. The `config/` directory only contains YAML and JSON configuration files, not Python modules.

**Solution**: 
- Removed the broken import
- Added a `load_model_config()` function that uses PyYAML to load `config/model.yaml` directly
- Added a `load_platforms_config()` function to load `config/platforms.json`

### 2. Module Import Errors (pipeline, database, metadata, uploaders)
**Issue**: When running backend_app.py from the `web/` directory, Python couldn't find modules like `pipeline`, `database`, `metadata`, and `uploaders` because they're located in the parent directory.

**Solution**: Added sys.path setup at the top of both `web/backend_app.py` and `web/server.py`:
```python
# Add parent directory to sys.path
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
```

### 3. VideoRegistry Method Name
**Issue**: The backend was calling `video_registry.list_videos()` but the actual method is `get_all_videos()`.

**Solution**: Updated the endpoint to use the correct method name.

### 4. Missing Dependencies
**Issue**: The web backend had no dedicated requirements.txt, making it unclear what dependencies were needed.

**Solution**: Created `web/requirements.txt` with all backend-specific dependencies.

## File Changes

### Modified Files
1. **web/backend_app.py** (FastAPI server)
   - Added sys.path setup with documentation
   - Removed broken config import
   - Added `load_model_config()` and `load_platforms_config()` functions
   - Added error handling for module imports
   - Fixed VideoRegistry method call
   - Added comprehensive inline documentation

2. **web/server.py** (Flask server - alternative)
   - Added sys.path setup with documentation
   - Removed broken config import
   - Added `load_model_config()` function
   - Added error handling for module imports

3. **.gitignore**
   - Added `web/database/videos.db` to exclude database files

### New Files
1. **web/requirements.txt**
   - Contains all dependencies needed to run the backend server
   - Documents that parent project dependencies are also needed

## How It Works

### Import Flow
1. Backend script starts from `web/` directory
2. sys.path setup adds parent directory to Python's module search path
3. ASFS modules (pipeline, database, metadata, uploaders) can now be imported
4. Error handling catches and logs any import failures with diagnostic information

### Configuration Loading
Instead of Python imports, configuration is now loaded using:
- **PyYAML** for `config/model.yaml`
- **json.load()** for `config/*.json` files

This is the correct approach since these are data files, not Python modules.

## Installation & Running

### 1. Install Dependencies
```bash
# Install parent project dependencies
cd /path/to/asfs
pip install -r requirements.txt

# Install web backend dependencies
cd web
pip install -r requirements.txt
```

### 2. Run Backend Server
```bash
cd web
python3 backend_app.py
```

The server will start at `http://0.0.0.0:5000`

### 3. Verify
Test the health endpoint:
```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{
    "status": "ok",
    "timestamp": "2026-02-12T16:20:00.000000"
}
```

## Key Design Decisions

### Why sys.path instead of package installation?
The ASFS modules (pipeline, database, etc.) are part of the project source code, not separate packages. Adding the parent directory to sys.path is the standard approach for scripts that need to import modules from a parent directory.

### Why remove config module import?
The `config/` directory contains YAML/JSON data files, not Python code. Attempting to import it as a Python module was incorrect. Loading configuration files directly with PyYAML/json is the proper approach.

### Why try/except for imports?
Adding error handling around imports provides clear diagnostic information if something goes wrong. It logs the sys.path, PROJECT_ROOT, and specific error, making it much easier to debug import issues.

## Testing

All endpoints have been tested and confirmed working:
- ✅ `/api/health` - Health check
- ✅ `/api/settings` - Settings management
- ✅ `/api/videos` - Video registry
- ✅ `/api/ollama/status` - Ollama status
- ✅ `/api/pipeline/start` - Pipeline control

## Backwards Compatibility

These changes are backwards compatible:
- No changes to the ASFS modules themselves
- Both FastAPI (backend_app.py) and Flask (server.py) servers updated
- Existing API endpoints unchanged
- Configuration files remain in same locations

## Future Improvements

1. **Optional**: Create a proper Python package structure with setup.py
2. **Optional**: Move web backend to a separate virtualenv
3. **Optional**: Add type hints to config loading functions
4. **Optional**: Create config validation schema

## Summary

All backend import and integration issues have been resolved:
✅ No more "module not found" errors
✅ Backend starts successfully
✅ All API endpoints working
✅ Proper configuration loading
✅ Clear documentation and error handling
✅ Dependencies documented in requirements.txt
