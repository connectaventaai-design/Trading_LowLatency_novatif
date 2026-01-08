# Deployment Guide

## Production Deployment

This guide covers deploying the HFT GOLD Trading System to a production environment.

## Server Requirements

### Minimum Specifications
- **CPU**: 4 cores, 3.0+ GHz
- **RAM**: 16GB
- **Storage**: 100GB SSD
- **Network**: <20ms latency to broker
- **OS**: Ubuntu 22.04 LTS or Windows Server 2019+

### Recommended Specifications
- **CPU**: 8+ cores, 4.0+ GHz (Intel Xeon or AMD EPYC)
- **RAM**: 32GB+
- **Storage**: 500GB NVMe SSD
- **Network**: <10ms latency to broker, dedicated connection
- **OS**: Ubuntu 22.04 LTS with real-time kernel

## VPS Provider Recommendations

### For Low-Latency Trading
1. **Equinix** - Colocation near broker datacenters
2. **AWS EC2** - c6i.2xlarge instances in broker-adjacent regions
3. **Vultr** - High-frequency instances
4. **OVH** - Bare metal servers

### Selection Criteria
- Physical proximity to MT5 broker (< 10ms ping)
- Stable network with redundancy
- 99.9%+ uptime SLA
- Good CPU performance (single-thread)

## Installation on Production Server

### 1. System Preparation (Ubuntu)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y build-essential python3.10 python3.10-venv python3-pip git wget curl

# Install TA-Lib
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
cd ..

# Optimize system for low latency
sudo sysctl -w net.core.rmem_max=134217728
sudo sysctl -w net.core.wmem_max=134217728
sudo sysctl -w net.ipv4.tcp_rmem='4096 87380 134217728'
sudo sysctl -w net.ipv4.tcp_wmem='4096 65536 134217728'
```

### 2. Application Deployment

```bash
# Clone repository
git clone https://github.com/connectaventaai-design/Trading_LowLatency_novatif.git
cd Trading_LowLatency_novatif

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Edit with production settings
```

### 3. Security Hardening

```bash
# Create dedicated user
sudo useradd -m -s /bin/bash hft_trader
sudo usermod -aG sudo hft_trader

# Set file permissions
sudo chown -R hft_trader:hft_trader /path/to/Trading_LowLatency_novatif
chmod 600 .env

# Firewall configuration
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 8000/tcp  # API (if exposing externally)
sudo ufw enable
```

### 4. Systemd Service Setup

Create service file: `/etc/systemd/system/hft-trading.service`

```ini
[Unit]
Description=HFT GOLD Trading System
After=network.target

[Service]
Type=simple
User=hft_trader
WorkingDirectory=/home/hft_trader/Trading_LowLatency_novatif
Environment="PATH=/home/hft_trader/Trading_LowLatency_novatif/venv/bin"
ExecStart=/home/hft_trader/Trading_LowLatency_novatif/venv/bin/python main.py
Restart=on-failure
RestartSec=10
StandardOutput=append:/var/log/hft-trading.log
StandardError=append:/var/log/hft-trading-error.log

[Install]
WantedBy=multi-user.target
```

Enable and start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable hft-trading
sudo systemctl start hft-trading
sudo systemctl status hft-trading
```

## Monitoring and Maintenance

### Log Monitoring

```bash
# View live logs
tail -f logs/trading.log

# System logs
sudo journalctl -u hft-trading -f

# Error logs
tail -f logs/trading-error.log
```

### Performance Monitoring

Create monitoring script: `monitor.sh`

```bash
#!/bin/bash
while true; do
  echo "=== $(date) ==="
  echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')"
  echo "Memory: $(free -h | awk '/Mem:/ {print $3 "/" $2}')"
  echo "Disk: $(df -h / | awk 'NR==2 {print $3 "/" $2}')"
  curl -s http://localhost:8000/metrics | jq '.daily_pnl'
  echo ""
  sleep 60
done
```

### Health Checks

```bash
# System health check
curl http://localhost:8000/health

# Trading status
curl http://localhost:8000/status
```

### Automated Alerts

Install email alerts:

```bash
sudo apt install -y mailutils

# Add to crontab
*/5 * * * * /path/to/check_trading_system.sh
```

Alert script: `check_trading_system.sh`

```bash
#!/bin/bash
STATUS=$(curl -s http://localhost:8000/status | jq -r '.status')
if [ "$STATUS" != "running" ]; then
  echo "HFT System is DOWN!" | mail -s "ALERT: Trading System" admin@example.com
fi
```

## Backup Strategy

### Database Backup

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/trading"
mkdir -p $BACKUP_DIR
cp trading_system/data/trading.db $BACKUP_DIR/trading_${DATE}.db
# Keep last 30 days
find $BACKUP_DIR -name "trading_*.db" -mtime +30 -delete
```

### Configuration Backup

```bash
# Backup configs
tar -czf configs_backup.tar.gz .env trading_system/config/
```

### Model Backup

```bash
# Backup trained models
tar -czf models_backup.tar.gz trading_system/models_trained/
```

## Disaster Recovery

### Automatic Restart on Crash

The systemd service automatically restarts on failure. Configure in service file:

```ini
Restart=on-failure
RestartSec=10
```

### Connection Loss Recovery

The system has built-in reconnection logic with exponential backoff. No manual intervention needed.

### Emergency Procedures

1. **System Crash**: Systemd auto-restarts
2. **MT5 Disconnect**: Auto-reconnection kicks in
3. **Excessive Losses**: Auto-stop triggers at drawdown limit
4. **Manual Emergency**: `curl -X POST http://localhost:8000/trading/emergency_close`

## Updates and Maintenance

### Updating the System

```bash
# Stop trading
curl -X POST http://localhost:8000/trading/stop

# Stop service
sudo systemctl stop hft-trading

# Backup current version
cp -r Trading_LowLatency_novatif Trading_LowLatency_novatif.backup

# Pull updates
cd Trading_LowLatency_novatif
git pull

# Update dependencies
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Test in paper trading
PAPER_TRADING=true python main.py

# If successful, restart service
sudo systemctl start hft-trading
```

### Model Retraining

Schedule weekly retraining:

```bash
# Add to crontab
0 2 * * 0 /home/hft_trader/Trading_LowLatency_novatif/retrain.sh
```

Retraining script:

```bash
#!/bin/bash
cd /home/hft_trader/Trading_LowLatency_novatif
source venv/bin/activate
python train_models.py
sudo systemctl restart hft-trading
```

## Security Best Practices

1. **Credentials**: Store in `.env`, never commit to git
2. **SSH Keys**: Use key-based authentication, disable password login
3. **Firewall**: Only open necessary ports
4. **API Access**: Use authentication tokens if exposing API
5. **Logs**: Rotate and archive logs regularly
6. **Updates**: Keep system and dependencies updated
7. **Access**: Limit SSH access to specific IPs
8. **Monitoring**: Set up intrusion detection

## Performance Optimization

### CPU Affinity

Pin process to specific cores:

```bash
# In systemd service file
[Service]
CPUAffinity=0 1 2 3
```

Or use taskset:

```bash
taskset -c 0-3 python main.py
```

### Network Tuning

```bash
# TCP optimizations
sudo sysctl -w net.ipv4.tcp_fin_timeout=15
sudo sysctl -w net.ipv4.tcp_tw_reuse=1
sudo sysctl -w net.core.netdev_max_backlog=5000

# Make permanent
echo "net.ipv4.tcp_fin_timeout=15" | sudo tee -a /etc/sysctl.conf
```

### Disk I/O

Use SSD/NVMe and mount with optimizations:

```bash
# In /etc/fstab
/dev/sda1 / ext4 defaults,noatime,nodiratime 0 1
```

## Compliance and Regulations

### Trading Regulations

- Ensure compliance with local financial regulations
- Maintain audit logs (system does this automatically)
- Implement kill switches (emergency stop provided)
- Monitor for market manipulation patterns

### Data Privacy

- Secure storage of trading data
- Regular backups
- Encryption at rest (optional)

## Checklist Before Going Live

- [ ] Paper trading tested for minimum 2 weeks
- [ ] All risk limits configured appropriately
- [ ] Emergency procedures documented and tested
- [ ] Monitoring and alerts active
- [ ] Backups configured and tested
- [ ] System performance validated (<10ms execution)
- [ ] Broker connectivity stable (<20ms ping)
- [ ] All team members trained on emergency procedures
- [ ] Disaster recovery plan in place
- [ ] Legal and compliance requirements met

## Support Contacts

- **Broker Support**: [Your broker's support]
- **System Administrator**: [Your admin contact]
- **Emergency Contact**: [24/7 contact]

---

**Critical**: Never deploy to production without thorough testing in paper trading mode for at least 2 weeks!
