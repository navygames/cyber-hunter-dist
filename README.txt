Cyber Hunter Reawakening - Navy Games
=====================================

A fan revival of Cyber Hunter. This folder is the player client: launcher,
connection scripts and the in-game mod. The game files themselves (game\)
are supplied separately.

WHAT YOU NEED
  1. Windows 10/11, 64-bit.
  2. Python 3.10+ (64-bit) - tick "Add python.exe to PATH" when installing.
     Then, in this folder:   pip install -r requirements.txt
     (Not needed if you installed with CyberHunterInstaller.exe.)
  3. Node.js 18+ (LTS) - for in-game stats and friends.
  4. The game files. The launcher downloads and installs them for you
     (press DOWNLOAD GAME after signing in); they end up in
        game\bin\client.exe   next to the launcher.

HOW TO PLAY
  1. Double-click CyberHunter.bat  (it asks for Administrator - needed to
     redirect the game's old servers).
  2. Sign in or create an account in the Navy Games Launcher.
  3. Press PLAY.

  That's the only way to start the game. Don't run client.exe directly.

THE SERVER
  The server is set in revival_config.env (created from
  revival_config.env.example on first run). Leave it as it is unless the
  Navy Games team tells you otherwise.

UNINSTALL / UNDO NETWORK CHANGES
  Run these from an Administrator PowerShell in tools\private_server\:
     .\remove_hosts.ps1
     .\remove_loopback_ips.ps1
     .\untrust_ca.ps1

FOLDERS
  CyberHunter.bat   start here
  Launcher\         the Navy Games launcher
  client\           connection scripts + the compiled in-game mod (client\runtime\ = logs)
  tools\            game-file checks and the local connection helpers
  game-server\src\  account bridge (talks to the server over HTTPS only)
  game\             the game itself (installed by the launcher)

UPDATES
  The launcher updates itself and these scripts automatically (UPDATE button).
  It only downloads player files, checked against a SHA-256 manifest.
