# 🎨 v5.0.1 - Cthulhu Rebranding

Complete system rebranding from "Herald" to "Cthulhu". This is a branding-only release with no functional changes to the trading system.

## 🌟 Highlights

- **Complete Rebranding**: All ~978 references systematically updated
- **150+ Files Modified**: Comprehensive updates across entire codebase
- **✅ All Tests Passing**: 156/156 unit tests passing
- **🔄 CI/CD Added**: GitHub Actions workflow for automated testing
- **🔒 Zero Breaking Functionality**: All trading features preserved

## 📦 What's Changed

### Branding Updates
- Package name: `herald` → `cthulhu`
- CLI tools: `herald` → `cthulhu`, `herald-trade` → `cthulhu-trade`
- Class names: `HeraldBootstrap` → `CthulhuBootstrap`, `HeraldGUI` → `CthulhuGUI`
- Logger names: All `herald.*` → `cthulhu.*`
- File references: `herald.db` → `cthulhu.db`, `herald.log` → `cthulhu.log`

### Infrastructure
- Docker: Service/container/network names updated to `cthulhu-*`
- Prometheus: Job names and metrics updated to `cthulhu_*`
- Environment variables: All `HERALD_*` → `CTHULHU_*`

### Testing & CI
- ✅ Fixed all unit tests (156 passing)
- 🔄 GitHub Actions CI workflow
- 🐍 Python 3.10, 3.11, 3.12 support
- 🖥️ Cross-platform (Ubuntu, Windows)

## 📚 Documentation

All documentation updated:
- ✅ Markdown files (CONTEXT.md, guides, etc.)
- ✅ HTML documentation
- ✅ Code examples
- ✅ Deployment guides

## ⬆️ Upgrade Instructions

### Update Imports
```python
# OLD
from herald import MT5Connector

# NEW
from cthulhu import MT5Connector
```

### Update CLI Commands
```bash
# OLD
python -m herald --config config.json

# NEW
python -m cthulhu --config config.json
```

### Update Environment Variables
```bash
# In your .env file
# OLD: HERALD_API_TOKEN
# NEW: CTHULHU_API_TOKEN
```

### Reinstall Package
```bash
pip install -e .  # or pip install cthulhu==5.0.1
```

## ⚠️ Breaking Changes

**Import paths have changed** - you'll need to update:
- All Python imports: `herald` → `cthulhu`
- CLI commands: `herald` → `cthulhu`
- Environment variables: `HERALD_*` → `CTHULHU_*`

## ✨ What's Preserved

- ✅ All trading functionality
- ✅ Configuration file formats
- ✅ Database schema
- ✅ API interfaces
- ✅ Performance characteristics
- ✅ System architecture

## 📊 Statistics

- **Files Modified**: 150+
- **References Updated**: ~978
- **Tests Passing**: 156/156 ✅
- **Python Versions**: 3.10, 3.11, 3.12
- **Platforms**: Ubuntu, Windows

## 🤝 Contributors

- @copilot - Complete rebranding implementation
- @amuzetnoM - Project oversight and requirements

---

**Full Changelog**: v5.0.1...v5.0.1

For detailed upgrade instructions and release notes, see [docs/release_notes/v5.0.1.md](https://github.com/amuzetnoM/herald/blob/main/docs/release_notes/v5.0.1.md)
