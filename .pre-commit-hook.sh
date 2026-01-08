#!/bin/bash
# Pre-commit hook to prevent regression
# Install: ln -s ../../.pre-commit-hook.sh .git/hooks/pre-commit

echo "🔍 Running Cthulu Health Check..."

# Check critical files exist
critical_files=(
    "cognition/entry_confluence.py"
    "risk/dynamic_sltp.py"
    "position/trade_manager.py"
    "config.json"
)

for file in "${critical_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ CRITICAL FILE MISSING: $file"
        echo "Commit BLOCKED - restore file before committing"
        exit 1
    fi
done

# Run health check if available
if [ -f "scripts/health_check.py" ]; then
    python scripts/health_check.py
    if [ $? -ne 0 ]; then
        echo "❌ Health check FAILED"
        echo "Fix issues before committing or use 'git commit --no-verify' to bypass"
        exit 1
    fi
fi

echo "✅ Pre-commit checks passed"
exit 0
