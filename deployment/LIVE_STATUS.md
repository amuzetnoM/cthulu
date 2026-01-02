# Cthulu GCP Node - Live Status

## Current Status: ✅ OPERATIONAL

**Last Updated**: 2026-01-02 13:55 UTC

---

## Access Points

| Service | URL | Status |
|---------|-----|--------|
| **Windows Desktop** | http://34.171.231.16:8006 | ✅ Running |
| **VS Code Server** | http://34.171.231.16:8443 | ✅ Running |
| **Cthulu Repo** | ~/workspace/cthulu | ✅ Cloned |

### VS Code Server Credentials
- **URL**: http://34.171.231.16:8443
- **Password**: `cthulu2026apex`

---

## VM Specifications

```yaml
Name: cthulu-reign-node
Zone: us-central1-a
Type: n2-standard-2 (Spot)
External IP: 34.171.231.16
Internal IP: 10.128.0.4
OS: Ubuntu 22.04 LTS
Container: dockurr/windows (Windows 11)
```

---

## Services Running

### Linux Host
- **Docker**: Running Windows 11 container
- **code-server**: VS Code in browser (port 8443)

### Windows Container
- **Status**: Booting/Running
- **Access**: Web-based noVNC on port 8006
- **RAM**: 6GB allocated
- **CPU**: 2 cores

---

## Quick Commands

### Check Status
```bash
gcloud compute instances list --filter="name:cthulu"
```

### SSH Access
```bash
gcloud compute ssh cthulu-reign-node --zone=us-central1-a
```

### Container Management
```bash
# Check Windows container
gcloud compute ssh cthulu-reign-node --zone=us-central1-a --command="sudo docker ps"

# View logs
gcloud compute ssh cthulu-reign-node --zone=us-central1-a --command="sudo docker logs cthulu-windows -f"

# Restart Windows
gcloud compute ssh cthulu-reign-node --zone=us-central1-a --command="sudo docker restart cthulu-windows"
```

---

## Next Steps

1. **Access Windows Desktop**: http://34.171.231.16:8006
2. **Complete Windows Setup** (if first boot)
3. **Install MT5** inside Windows
4. **Configure MT5** with trading account
5. **Run Cthulu** via wizard or config

---

## Cost Estimate

~$21-30/month with Spot pricing

---

## Notes

- Spot VM may be preempted - restart with `gcloud compute instances start`
- Cthulu repo already cloned on Linux host at `~/workspace/cthulu`
- For Windows development, use web desktop or install VS Code inside container
