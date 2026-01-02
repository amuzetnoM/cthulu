# Cthulu GCP Deployment Guide

<div align="center">
<img src="https://img.shields.io/badge/APEX-v5.1.0-4B0082?style=for-the-badge" />
<img src="https://img.shields.io/badge/GCP-Compute_Engine-4285F4?style=for-the-badge&logo=google-cloud" />
<img src="https://img.shields.io/badge/Status-DEPLOYED-brightgreen?style=for-the-badge" />
</div>

---

## Infrastructure Overview

### Current Deployment

| Attribute | Value |
|-----------|-------|
| **VM Name** | `cthulu-reign-node` |
| **Zone** | `us-central1-a` |
| **Machine Type** | `n2-standard-2` (2 vCPU, 8GB RAM) |
| **Provisioning** | Spot (Preemptible) |
| **External IP** | `34.171.231.16` |
| **Internal IP** | `10.128.0.4` |
| **Boot Disk** | 50GB pd-balanced |
| **OS** | Ubuntu 22.04 LTS (Host) + Windows 11 (Container) |
| **Nested Virtualization** | Enabled |

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GCP Compute Engine                        │
│                    cthulu-reign-node                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Ubuntu 22.04 LTS (Host)                 │   │
│  │                                                      │   │
│  │  ┌────────────────────────────────────────────────┐ │   │
│  │  │           Docker Container                      │ │   │
│  │  │           dockurr/windows                       │ │   │
│  │  │  ┌──────────────────────────────────────────┐  │ │   │
│  │  │  │         Windows 11 (KVM)                 │  │ │   │
│  │  │  │                                          │  │ │   │
│  │  │  │  ┌──────────┐  ┌──────────┐            │  │ │   │
│  │  │  │  │ MT5      │  │ Cthulu   │            │  │ │   │
│  │  │  │  │ Terminal │  │ Trading  │            │  │ │   │
│  │  │  │  └──────────┘  └──────────┘            │  │ │   │
│  │  │  │                                          │  │ │   │
│  │  │  │  ┌──────────┐  ┌──────────┐            │  │ │   │
│  │  │  │  │ Sentinel │  │ VS Code  │            │  │ │   │
│  │  │  │  │ Monitor  │  │ Server   │            │  │ │   │
│  │  │  │  └──────────┘  └──────────┘            │  │ │   │
│  │  │  └──────────────────────────────────────────┘  │ │   │
│  │  └────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Exposed Ports:                                             │
│  • 8006 - Windows Web Desktop (noVNC)                      │
│  • 3389 - RDP (if configured)                              │
│  • 22   - SSH (Linux host)                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Access Methods

### 1. Web Desktop (Primary)

Access the Windows 11 environment directly in your browser:

```
http://34.171.231.16:8006
```

**First Boot:**
- Wait 5-10 minutes for Windows image to download and initialize
- No password required on first boot
- Complete Windows regional setup if prompted

### 2. SSH to Linux Host

```bash
gcloud compute ssh cthulu-reign-node --zone=us-central1-a
```

Or directly:
```bash
ssh ali_shakil_backup_gmail_com@34.171.231.16
```

### 3. VS Code Remote Development

**Option A: Remote-SSH Extension**
1. Install VS Code Remote-SSH extension
2. Add to SSH config (`~/.ssh/config`):
```
Host cthulu-gcp
    HostName 34.171.231.16
    User ali_shakil_backup_gmail_com
    IdentityFile ~/.ssh/google_compute_engine
```
3. Connect via VS Code command palette: `Remote-SSH: Connect to Host`

**Option B: VS Code Server (Inside Windows Container)**
1. Access web desktop at `http://34.171.231.16:8006`
2. Download VS Code from `https://code.visualstudio.com`
3. Install and configure for local development

---

## Installation on GCP VM

### Step 1: Access Windows Desktop
```
http://34.171.231.16:8006
```

### Step 2: Install Prerequisites

Inside Windows 11:

1. **Install Python 3.10+**
   - Download from `https://www.python.org/downloads/`
   - Check "Add to PATH" during installation

2. **Install Git**
   - Download from `https://git-scm.com/download/win`

3. **Install MetaTrader 5**
   - Download from your broker or `https://www.metatrader5.com`
   - Login to your trading account
   - Enable Algo Trading

### Step 3: Clone and Setup Cthulu

Open PowerShell:

```powershell
# Clone repository
git clone https://github.com/amuzetnoM/cthulu.git C:\workspace\cthulu
cd C:\workspace\cthulu

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Copy example config
Copy-Item config.example.json config.json

# Edit config with your settings
notepad config.json
```

### Step 4: Configure Trading Account

Edit `config.json`:
```json
{
  "mt5": {
    "login": YOUR_ACCOUNT_NUMBER,
    "password": "YOUR_PASSWORD",
    "server": "YOUR_BROKER_SERVER"
  },
  "trading": {
    "symbol": "BTCUSD#",
    "mindset": "ultra_aggressive",
    "timeframe": "M5"
  }
}
```

### Step 5: Launch Cthulu

```powershell
# Start with wizard
python __main__.py --wizard

# Or direct launch
python __main__.py --config config.json
```

---

## Operations & Management

### Start/Stop VM

```bash
# Start
gcloud compute instances start cthulu-reign-node --zone=us-central1-a

# Stop
gcloud compute instances stop cthulu-reign-node --zone=us-central1-a

# Check status
gcloud compute instances list
```

### Monitor Container (from Linux host)

```bash
# SSH into host
gcloud compute ssh cthulu-reign-node --zone=us-central1-a

# Check Windows container
sudo docker ps
sudo docker logs cthulu-windows -f

# Restart Windows container
sudo docker restart cthulu-windows
```

### Spot VM Preemption Recovery

Spot VMs can be preempted. Data is safe on persistent disk.

```bash
# Check if VM was preempted
gcloud compute operations list --filter="targetLink:cthulu-reign-node"

# Restart after preemption
gcloud compute instances start cthulu-reign-node --zone=us-central1-a
```

### Firewall Rules

Current rules:
```bash
# List rules
gcloud compute firewall-rules list --filter="name:cthulu"

# Allow additional port (example: Prometheus)
gcloud compute firewall-rules create allow-cthulu-prometheus \
    --allow tcp:9090 \
    --target-tags=cthulu-rdp \
    --description="Allow Prometheus access"
```

---

## Cost Optimization

### Current Configuration
- **Spot VM**: ~70% cheaper than on-demand
- **Machine Type**: n2-standard-2 (minimum for nested virtualization)
- **Disk**: pd-balanced (good performance/cost ratio)

### Estimated Costs
| Resource | Monthly Cost (Spot) |
|----------|---------------------|
| n2-standard-2 | ~$15-20 |
| 50GB pd-balanced | ~$5 |
| Network egress | ~$1-5 |
| **Total** | **~$21-30/month** |

### Cost Reduction Options

1. **Schedule VM**: Stop when not trading
   ```bash
   # Create scheduled stop (Friday 22:00 UTC)
   gcloud compute resource-policies create instance-schedule cthulu-weekend-stop \
       --region=us-central1 \
       --vm-stop-schedule="0 22 * * 5"
   ```

2. **Use e2-standard-2**: If nested virtualization not needed
   - Note: Requires different Windows deployment approach

---

## Troubleshooting

### Windows Container Not Starting

```bash
# Check container logs
sudo docker logs cthulu-windows

# Check KVM support
ls -la /dev/kvm

# Restart container
sudo docker rm -f cthulu-windows
sudo docker run -d \
    --name cthulu-windows \
    --restart always \
    -p 8006:8006 \
    --device=/dev/kvm \
    --cap-add NET_ADMIN \
    -e RAM_SIZE=6G \
    -e CPU_CORES=2 \
    dockurr/windows
```

### Web Desktop Not Loading

1. Check firewall: `gcloud compute firewall-rules list`
2. Check container: `sudo docker ps`
3. Check port: `sudo netstat -tlnp | grep 8006`

### MT5 Connection Issues

Inside Windows:
1. Check internet connectivity
2. Verify broker server is correct
3. Check login credentials
4. Ensure Algo Trading is enabled in MT5 settings

---

## Security Considerations

1. **Change default passwords** after Windows setup
2. **Configure Windows Firewall** inside the container
3. **Use SSH keys** for host access (gcloud manages this)
4. **Restrict firewall rules** to specific IPs if possible
5. **Enable 2FA** on trading accounts

---

## Reference Commands

```bash
# Quick status check
gcloud compute instances describe cthulu-reign-node --zone=us-central1-a --format="table(name,status,networkInterfaces[0].accessConfigs[0].natIP)"

# Serial console (if web desktop fails)
gcloud compute connect-to-serial-port cthulu-reign-node --zone=us-central1-a

# Create snapshot (backup)
gcloud compute disks snapshot cthulu-reign-node --zone=us-central1-a --snapshot-names=cthulu-backup-$(date +%Y%m%d)

# Resize disk
gcloud compute disks resize cthulu-reign-node --zone=us-central1-a --size=100GB
```

---

**Last Updated**: 2026-01-02
**Maintained By**: Cthulu Development Team
