#!/bin/bash
# PROPOSAL ONLY: replace the image /start.sh tail in the controller's STAGE0.
# Preserve the existing bounded-lifetime/prefetch prefix. Root owns deployment.
set -eu
printf 'ideas-startup: explicit SSH bootstrap reached\n' >&2
test -n "${PUBLIC_KEY:-}" || { printf 'ideas-startup: PUBLIC_KEY missing\n' >&2; exit 70; }
test -x /usr/sbin/sshd || { printf 'ideas-startup: openssh-server absent\n' >&2; exit 70; }
install -d -m 0700 /root/.ssh
printf '%s\n' "$PUBLIC_KEY" | tr -d '\r' > /root/.ssh/authorized_keys
chmod 0600 /root/.ssh/authorized_keys
chown 0:0 /root/.ssh /root/.ssh/authorized_keys
install -d -m 0755 /run/sshd
ssh-keygen -A
# A dedicated config avoids nginx, Jupyter, legacy DSA generation and unknown
# image sshd_config fragments. PAM keeps public-key access compatible with a
# locked root password; password and keyboard-interactive auth stay disabled.
opts=(-f /dev/null -p 22 -h /etc/ssh/ssh_host_ed25519_key
      -o ListenAddress=0.0.0.0 -o AuthorizedKeysFile=/root/.ssh/authorized_keys
      -o PubkeyAuthentication=yes -o PasswordAuthentication=no
      -o KbdInteractiveAuthentication=no -o PermitEmptyPasswords=no
      -o PermitRootLogin=prohibit-password -o UsePAM=yes -o LogLevel=VERBOSE)
/usr/sbin/sshd -t "${opts[@]}"
printf 'ideas-startup: SSH configuration valid; listening on 22\n' >&2
exec /usr/sbin/sshd -D -e "${opts[@]}"
