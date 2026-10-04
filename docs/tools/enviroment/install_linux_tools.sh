#!/usr/bin/env bash
set -euo pipefail

# Install the small set of Linux utilities used by benchmark Agents for
# inspecting files, preparing data and recording reproducible runs.
# Supported systems: Ubuntu and Debian.

if [[ "${EUID}" -ne 0 ]]; then
    echo "Run this script as root, for example: sudo bash $0" >&2
    exit 1
fi

if ! command -v apt-get >/dev/null 2>&1; then
    echo "This installer requires apt-get (Ubuntu/Debian)." >&2
    exit 1
fi

export DEBIAN_FRONTEND=noninteractive

packages=(
    # File and text inspection
    file
    coreutils
    findutils
    grep
    sed
    gawk
    util-linux
    tree
    jq
    # Archives and checksums
    tar
    gzip
    bzip2
    xz-utils
    unzip
    # Network and data transfer
    ca-certificates
    curl
    wget
    rsync
    # Process and resource inspection
    procps
    lsof
    # Source and lightweight build support
    git
    build-essential
    pkg-config
    which
)

echo "Updating apt package indexes..."
apt-get update

echo "Installing benchmark host utilities..."
apt-get install -y --no-install-recommends "${packages[@]}"

echo "Installed Linux benchmark utilities:"
for command_name in file find stat du readlink realpath tree grep sed awk jq \
    sha256sum curl wget rsync tar gzip bzip2 xz unzip git ps top free lsof; do
    if command -v "${command_name}" >/dev/null 2>&1; then
        printf '  OK   %s -> %s\n' "${command_name}" "$(command -v "${command_name}")"
    else
        printf '  MISS %s\n' "${command_name}" >&2
    fi
done
