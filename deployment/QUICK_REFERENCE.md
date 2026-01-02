# Cthulu Node Infrastructure Reference

## Quick Access

| Service | URL/Command |
|---------|-------------|
| **Windows Desktop** | http://34.171.231.16:8006 |
| **SSH (Linux Host)** | `gcloud compute ssh cthulu-reign-node --zone=us-central1-a` |
| **VM Console** | https://console.cloud.google.com/compute/instances |

## Credentials & Access

### GCP Project
- **Project ID**: artifact-virtual
- **Service Account**: 937668381187-compute@developer.gserviceaccount.com

### VM Details
- **Name**: cthulu-reign-node
- **Zone**: us-central1-a
- **External IP**: 34.171.231.16
- **Internal IP**: 10.128.0.4
- **User**: ali_shakil_backup_gmail_com

### Network Tags
- `cthulu-rdp` - Allows port 8006

## Common Operations

### Daily Operations
```bash
# Check VM status
gcloud compute instances list --filter="name:cthulu"

# Start VM
gcloud compute instances start cthulu-reign-node --zone=us-central1-a

# Stop VM (cost savings)
gcloud compute instances stop cthulu-reign-node --zone=us-central1-a
```

### Emergency Recovery
```bash
# Force restart
gcloud compute instances reset cthulu-reign-node --zone=us-central1-a

# Access serial console
gcloud compute connect-to-serial-port cthulu-reign-node --zone=us-central1-a

# Restart Windows container (SSH into host first)
sudo docker restart cthulu-windows
```

### Backup
```bash
# Create disk snapshot
gcloud compute disks snapshot cthulu-reign-node \
    --zone=us-central1-a \
    --snapshot-names=cthulu-backup-$(date +%Y%m%d)

# List snapshots
gcloud compute snapshots list --filter="name:cthulu"
```

## Directory Structure on VM

```
C:\workspace\
├── cthulu\              # Main trading system
│   ├── __main__.py      # Entry point
│   ├── config.json      # Active configuration
│   └── ...
├── sentinel\            # Crash recovery system
└── logs\                # Application logs
```

## Cthulu Launch Commands

```powershell
# Navigate to Cthulu
cd C:\workspace\cthulu

# Activate environment
.\venv\Scripts\Activate.ps1

# Launch with wizard
python __main__.py --wizard

# Launch headless
python __main__.py --config config.json

# Launch Sentinel
python C:\workspace\sentinel\sentinel_gui.py
```

## Monitoring URLs (when running)

| Service | Port | URL |
|---------|------|-----|
| Prometheus | 9090 | http://34.171.231.16:9090 |
| Grafana | 3000 | http://34.171.231.16:3000 |
| Dashboard | 8080 | http://34.171.231.16:8080 |

*Note: Requires firewall rules to be configured*

## Cost Summary

| Resource | Est. Monthly |
|----------|--------------|
| Spot VM (n2-standard-2) | $15-20 |
| 50GB pd-balanced disk | $5 |
| Network | $1-5 |
| **Total** | **$21-30** |

## Important Notes

1. **Spot VM**: May be preempted - data safe on persistent disk
2. **Windows License**: Using dockurr/windows (evaluation/personal use)
3. **MT5**: Must enable Algo Trading in settings
4. **Sentinel**: Should be running for crash recovery

---

**Last Updated**: 2026-01-02
