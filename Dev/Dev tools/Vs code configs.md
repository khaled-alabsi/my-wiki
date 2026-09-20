VS Code macOS — Local Network Access Fix

Newer VS Code versions on macOS may fail to access devices on the local network from the integrated terminal, while the same commands work with sudo.

For a local network such as 192.168.178.0/24:

Wi-Fi

sudo defaults write com.apple.network.local-network \

  AllowedWiFiLocalNetworkAddresses \

  -array "192.168.178.0/24"

Ethernet

sudo defaults write com.apple.network.local-network \

  AllowedEthernetLocalNetworkAddresses \

  -array "192.168.178.0/24"

Restart macOS afterward.

This allows applications such as VS Code to access the specified local subnet without running VS Code or its terminal commands with sudo.