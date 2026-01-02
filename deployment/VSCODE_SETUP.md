# VS Code Server Setup for Cthulu GCP Node

## Overview

This guide covers setting up VS Code for remote development on the Cthulu GCP VM.

---

## Option 1: VS Code Remote-SSH (Recommended)

Connect VS Code on your local machine to the Linux host.

### Prerequisites
- VS Code installed locally
- Remote-SSH extension installed
- gcloud CLI authenticated

### Setup

1. **Generate SSH key** (if not done):
   ```bash
   gcloud compute config-ssh
   ```

2. **Add to SSH config** (`~/.ssh/config` or `C:\Users\<you>\.ssh\config`):
   ```
   Host cthulu-gcp
       HostName 34.171.231.16
       User ali_shakil_backup_gmail_com
       IdentityFile ~/.ssh/google_compute_engine
   ```

3. **Connect in VS Code**:
   - Press `Ctrl+Shift+P`
   - Type: `Remote-SSH: Connect to Host`
   - Select `cthulu-gcp`

4. **Open Workspace**:
   - Navigate to `/home/ali_shakil_backup_gmail_com/workspace/cthulu`

---

## Option 2: code-server (Browser-based)

Run VS Code in browser, accessible from anywhere.

### Install on Linux Host

```bash
# SSH into host
gcloud compute ssh cthulu-reign-node --zone=us-central1-a

# Install code-server
curl -fsSL https://code-server.dev/install.sh | sh

# Configure
mkdir -p ~/.config/code-server
cat > ~/.config/code-server/config.yaml << EOF
bind-addr: 0.0.0.0:8443
auth: password
password: YOUR_SECURE_PASSWORD
cert: false
EOF

# Start as service
sudo systemctl enable --now code-server@$USER
```

### Add Firewall Rule

```bash
gcloud compute firewall-rules create allow-code-server \
    --allow tcp:8443 \
    --target-tags=cthulu-rdp \
    --description="Allow VS Code Server"
```

### Access

```
http://34.171.231.16:8443
```

---

## Option 3: VS Code Inside Windows Container

For developing directly in the Windows environment with MT5.

### Install

1. Access Windows desktop: `http://34.171.231.16:8006`
2. Download VS Code: `https://code.visualstudio.com`
3. Install normally
4. Configure Python extension

### Recommended Extensions

- Python
- Pylance
- Git Lens
- Remote Development pack (for nested scenarios)

---

## Recommended Configuration

### VS Code Settings (`.vscode/settings.json`)

```json
{
  "python.defaultInterpreterPath": "venv/Scripts/python.exe",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "files.autoSave": "afterDelay",
  "files.autoSaveDelay": 1000,
  "git.autofetch": true
}
```

### Launch Configurations (`.vscode/launch.json`)

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Cthulu Wizard",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/__main__.py",
      "args": ["--wizard"],
      "console": "integratedTerminal"
    },
    {
      "name": "Cthulu Live",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/__main__.py",
      "args": ["--config", "config.json"],
      "console": "integratedTerminal"
    },
    {
      "name": "Cthulu Dry Run",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/__main__.py",
      "args": ["--config", "config.json", "--dry-run"],
      "console": "integratedTerminal"
    },
    {
      "name": "Sentinel GUI",
      "type": "python",
      "request": "launch",
      "program": "C:/workspace/sentinel/sentinel_gui.py",
      "console": "integratedTerminal"
    }
  ]
}
```

### Tasks (`.vscode/tasks.json`)

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Run Tests",
      "type": "shell",
      "command": "pytest tests/ -v",
      "group": "test"
    },
    {
      "label": "Lint",
      "type": "shell",
      "command": "pylint cthulu/ --rcfile=.pylintrc",
      "group": "build"
    },
    {
      "label": "Start Cthulu",
      "type": "shell",
      "command": "python __main__.py --config config.json",
      "group": "none"
    }
  ]
}
```

---

## Sync Local <-> Remote

### Using Git (Recommended)

```bash
# On local machine
git add .
git commit -m "Update"
git push

# On remote VM
cd /path/to/cthulu
git pull
```

### Using rsync (Linux/Mac)

```bash
# Push local changes
rsync -avz --exclude 'venv' --exclude '__pycache__' \
    ./cthulu/ cthulu-gcp:/home/ali_shakil_backup_gmail_com/workspace/cthulu/

# Pull remote changes
rsync -avz cthulu-gcp:/home/ali_shakil_backup_gmail_com/workspace/cthulu/ ./cthulu-backup/
```

---

## Troubleshooting

### SSH Connection Refused
```bash
# Check VM is running
gcloud compute instances list

# Check SSH key
gcloud compute config-ssh --remove
gcloud compute config-ssh
```

### code-server Not Loading
```bash
# Check status
sudo systemctl status code-server@$USER

# Check port
sudo netstat -tlnp | grep 8443

# Restart
sudo systemctl restart code-server@$USER
```

### Extension Issues
- Ensure Python extension is installed on remote
- Check Python interpreter path
- Reload VS Code window

---

**Last Updated**: 2026-01-02
