#!/bin/bash
# Security Setup Script for Central Server
# This script creates a restricted SSH user for tunnel connections only
# Run this on the Central Server

set -e  # Exit on error

# Configuration
TUNNEL_USER="tunnel_agent"
TUNNEL_HOME="/home/${TUNNEL_USER}"
SSH_DIR="${TUNNEL_HOME}/.ssh"
AUTH_KEYS="${SSH_DIR}/authorized_keys"

echo "========================================"
echo "SSH Security Hardening Setup"
echo "========================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# 1. Create restricted user
echo "[1/6] Creating restricted user: ${TUNNEL_USER}"
if id "$TUNNEL_USER" &>/dev/null; then
    echo "  User already exists, skipping..."
else
    # Create user with no login shell
    useradd -m -s /usr/sbin/nologin "$TUNNEL_USER"
    echo "  ✓ User created"
fi

# 2. Create SSH directory
echo "[2/6] Setting up SSH directory"
mkdir -p "$SSH_DIR"
touch "$AUTH_KEYS"

# 3. Set proper permissions
echo "[3/6] Setting permissions"
chmod 700 "$SSH_DIR"
chmod 600 "$AUTH_KEYS"
chown -R "${TUNNEL_USER}:${TUNNEL_USER}" "$SSH_DIR"
echo "  ✓ Permissions set"

# 4. Display authorized_keys location
echo "[4/6] Authorized keys file location:"
echo "  $AUTH_KEYS"
echo ""
echo "Add public keys with restrictions like:"
echo "  from=\"SITE_IP\",restrict,port-forwarding,no-pty,no-agent-forwarding,no-X11-forwarding ssh-rsa AAAA..."

# 5. Configure SSH server (optional)
echo "[5/6] SSH server configuration"
SSHD_CONFIG="/etc/ssh/sshd_config"

# Check if Match block exists
if grep -q "Match User ${TUNNEL_USER}" "$SSHD_CONFIG"; then
    echo "  SSH config already has Match block for ${TUNNEL_USER}"
else
    echo "  Adding restriction to ${SSHD_CONFIG}..."
    cat >> "$SSHD_CONFIG" <<EOF

# Restriction for tunnel agent (added by security setup script)
Match User ${TUNNEL_USER}
    AllowTcpForwarding yes
    X11Forwarding no
    AllowAgentForwarding no
    PermitTTY no
    ForceCommand /bin/false
EOF
    echo "  ✓ SSH config updated"
    echo "  Note: SSH service restart required"
fi

# 6. Summary
echo "[6/6] Setup complete!"
echo ""
echo "========================================"
echo "Next Steps:"
echo "========================================"
echo "1. Add site VM public keys to: $AUTH_KEYS"
echo "   Format: from=\"SITE_IP\",restrict,port-forwarding,no-pty ssh-rsa ..."
echo ""
echo "2. Restart SSH service:"
echo "   sudo systemctl restart sshd"
echo ""
echo "3. Test from site VM:"
echo "   ssh ${TUNNEL_USER}@$(hostname -I | awk '{print $1}') \"ls\"  # Should FAIL"
echo "   ssh -fN -L 5100:localhost:5100 ${TUNNEL_USER}@$(hostname -I | awk '{print $1}')  # Should SUCCEED"
echo ""
echo "4. Update agent script to use user: ${TUNNEL_USER}"
echo "========================================"
