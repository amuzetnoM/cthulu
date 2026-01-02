# Cthulu GCP Deployment Guide

![APEX](https://img.shields.io/badge/APEX-v5.1.0-4B0082?style=flat-square)
![GCP](https://img.shields.io/badge/GCP-Compute_Engine-4285F4?style=flat-square)
![Status](https://img.shields.io/badge/Status-ACTIVE-brightgreen?style=flat-square)

## Overview

This guide covers deploying Cthulu on Google Cloud Platform using a cost-optimized architecture:
- **Linux Host** (Ubuntu 22.04) running Docker
- **Windows 11 Container** (dockur/windows) with KVM virtualization
- **Spot VM** pricing for 60-90% cost reduction

## Current Deployment

| Property | Value |
|----------|-------|
| **VM Name** | `cthulu-reign-node` |
| **Zone** | `us-central1-a` |
| **Machine Type** | `n2-standard-2` (Spot) |
| **External IP** | `34.171.231.16` |
| **Windows Access** | `http://34.171.231.16:8006` |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    GCP Compute Engine                    │
│                    (n2-standard-2 Spot)                  │
├─────────────────────────────────────────────────────────┤
│  Ubuntu 22.04 LTS (Host)                                │
│  ├── Docker Engine                                       │
│  └── dockur/windows Container                           │
│      ├── Windows 11 (KVM Virtualized)                   │
│      ├── MetaTrader 5                                   │
│      ├── Python 3.10+                                   │
│      └── Cthulu Trading System                          │
└─────────────────────────────────────────────────────────┘
```

## Access Methods

### 1. Browser-Based Desktop (Primary)
Navigate to: **http://34.171.231.16:8006**

This provides a full Windows 11 desktop in your browser via noVNC.

### 2. SSH to Linux Host
```bash
gcloud compute ssh cthulu-reign-node --zone=us-central1-a
```

### 3. Docker Container Access
```bash
# SSH into host first, then:
sudo docker exec -it cthulu-windows bash
```

## Initial Setup Checklist

### Step 1: Access Windows Desktop
1. Open browser: `http://34.171.231.16:8006`
2. Wait for Windows to fully boot (first boot takes 5-10 minutes)
3. Complete Windows regional setup if prompted

### Step 2: Install MetaTrader 5
1. Open Microsoft Edge in the VM
2. Download MT5: https://www.metatrader5.com/en/download
3. Run installer with default settings
4. Login to your broker account

### Step 3: Install Python
1. Download Python 3.10+: https://www.python.org/downloads/
2. **Important**: Check "Add Python to PATH" during installation
3. Verify: Open CMD, run `python --version`

### Step 4: Install Git
1. Download Git: https://git-scm.com/download/win
2. Install with default settings
3. Verify: `git --version`

### Step 5: Clone Cthulu
```cmd
cd C:\
git clone https://github.com/amuzetnoM/cthulu.git
cd cthulu
pip install -r requirements.txt
```

### Step 6: Configure Cthulu
1. Copy example config: `copy config.example.json config.json`
2. Edit config.json with your settings
3. Ensure MT5 terminal is running and logged in

### Step 7: Launch Cthulu
```cmd
cd C:\cthulu
python __main__.py --config config.json
```

## Operations

### Starting the VM
```bash
gcloud compute instances start cthulu-reign-node --zone=us-central1-a
```

### Stopping the VM
```bash
gcloud compute instances stop cthulu-reign-node --zone=us-central1-a
```

### Checking Status
```bash
gcloud compute instances describe cthulu-reign-node --zone=us-central1-a --format="value(status)"
```

### Viewing Logs (Linux Host)
```bash
gcloud compute ssh cthulu-reign-node --zone=us-central1-a --command="sudo docker logs cthulu-windows --tail 100"
```

## Spot VM Considerations

### Preemption Handling
- Spot VMs can be preempted with 30 seconds notice
- The VM is configured with `--instance-termination-action=STOP`
- Persistent disk ensures data survives preemption
- Simply restart the VM after preemption

### Auto-Recovery Script
Create a Cloud Function or use Cloud Scheduler to auto-restart:
```bash
# Check every 5 minutes and restart if stopped
gcloud compute instances start cthulu-reign-node --zone=us-central1-a 2>/dev/null || true
```

## Security Notes

1. **Firewall**: Only port 8006 is exposed (Windows container web access)
2. **Secrets**: Never commit credentials to Git
3. **MT5 Credentials**: Store in MT5's built-in credential manager
4. **Config Files**: Keep config.json in .gitignore

## Cost Optimization

| Resource | Monthly Cost (Spot) |
|----------|---------------------|
| n2-standard-2 | ~$15-25 |
| 50GB Balanced Disk | ~$5 |
| Network Egress | ~$1-5 |
| **Total** | **~$21-35/month** |

*Standard pricing would be $80-100/month*

## Troubleshooting

### Windows Container Not Starting
```bash
# SSH to host
gcloud compute ssh cthulu-reign-node --zone=us-central1-a

# Check container status
sudo docker ps -a

# View container logs
sudo docker logs cthulu-windows

# Restart container
sudo docker restart cthulu-windows
```

### MT5 Connection Issues
1. Ensure MT5 terminal is fully logged in
2. Check "Allow Algo Trading" is enabled
3. Verify DLLs are enabled in MT5 settings
4. Test with: `python -c "import MetaTrader5; print(MetaTrader5.initialize())"`

### Cthulu Won't Start
1. Check Python dependencies: `pip install -r requirements.txt`
2. Verify config.json is valid JSON
3. Check logs in `C:\cthulu\logs\`
4. Ensure MT5 is running before starting Cthulu

## Maintenance Schedule

| Task | Frequency |
|------|-----------|
| Check VM status | Daily |
| Review trade logs | Daily |
| Update Cthulu | Weekly |
| Backup config | Weekly |
| Check GCP billing | Weekly |

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-02  
**Maintainer**: Cthulu Development Team
