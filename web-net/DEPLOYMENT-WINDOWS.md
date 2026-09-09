# Windows Deployment Guide: File Organizer (.NET 8 Web Server)

This guide covers production and on-premise deployment of the native ASP.NET Core 8.0 `FileOrganizer.Web` application on Windows Server and Windows 10/11 environments.

The published artifact in `dist/win-x64/` is completely **self-contained** and packaged as a **single-file executable** (`FileOrganizer.Web.exe`). It requires **zero pre-installed .NET runtimes**, **zero Python installations**, and **zero external package dependencies**.

---

## 1. Prerequisites & Package Contents

### Published Distribution Files (`dist/win-x64/`)
```text
dist/win-x64/
├── FileOrganizer.Web.exe         # Self-contained single-file executable (~96 MB, includes .NET 8 runtime)
├── appsettings.json             # Core runtime configuration (paths, logging, connection strings)
├── appsettings.Development.json # Development environment overrides
├── web.config                   # IIS In-Process hosting configuration
├── e_sqlite3.dll                # Bundled SQLite engine
├── aspnetcorev2_inprocess.dll   # IIS In-Process hosting module helper
└── wwwroot/                     # Static frontend web dashboard
    ├── index.html               # Main dashboard UI
    ├── css/styles.css           # Styling and responsive design
    └── js/                      # Modular JavaScript application
```

### System Requirements
- **OS**: Windows Server 2016+, Windows 10 (1809+), or Windows 11 (x64 architecture).
- **RAM**: Minimum 512 MB available RAM (recommended 2 GB).
- **Disk**: 500 MB free disk space for application + adequate storage for document vault.

---

## 2. Configuration (`appsettings.json` and Environment Variables)

`FileOrganizer.Web` binds to `organizer.db` and the document root path. Configuration can be managed via `appsettings.json` or system environment variables.

### `appsettings.json` Example:
```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  },
  "AllowedHosts": "*",
  "ORGANIZER_DB_PATH": "C:\\FileOrganizer\\data\\organizer.db",
  "AREAS_ROOT_PATH": "C:\\FileOrganizer\\areas"
}
```

### Environment Variables:
- `ORGANIZER_DB_PATH`: Absolute path to the SQLite WAL database (defaults to `organizer.db` in the working directory).
- `AREAS_ROOT_PATH`: Absolute path to the root containing Area/House folders (defaults to current directory).
- `ASPNETCORE_URLS`: Binding URLs and ports (e.g., `http://0.0.0.0:5000` or `http://*:80`).

---

## 3. Deployment Mode 1: Standalone Execution (Double-Click / CLI)

Ideal for developer workstations, local administrative review, and portable flash drive execution.

1. Copy `dist/win-x64/` to your target directory (e.g., `C:\FileOrganizer\app\`).
2. Double-click `FileOrganizer.Web.exe` or execute from PowerShell / Command Prompt:
   ```cmd
   cd C:\FileOrganizer\app
   FileOrganizer.Web.exe --urls "http://0.0.0.0:5000"
   ```
3. Open a browser and navigate to:
   ```
   http://localhost:5000
   ```
4. Press `Ctrl+C` in the console window to gracefully stop the application.

---

## 4. Deployment Mode 2: Native Windows Service (`sc.exe`)

Ideal for dedicated on-premise Windows servers requiring automatic restart on system reboot, background execution without active user login, and service monitoring.

### Step 1: Create Windows Service
Open an administrative PowerShell or Command Prompt and run:
```cmd
sc.exe create "FileOrganizerWeb" binPath= "\"C:\FileOrganizer\app\FileOrganizer.Web.exe\"" start= auto DisplayName= "File Organizer Web Dashboard"
```

### Step 2: Configure Service Description & Recovery Options
```cmd
sc.exe description "FileOrganizerWeb" "Provides high-performance web dashboard for multi-tenant house document archives."
sc.exe failure "FileOrganizerWeb" reset= 86400 actions= restart/60000/restart/60000/none/60000
```

### Step 3: Configure Service Environment Variables (PowerShell)
To specify database and vault paths for the service account:
```powershell
[System.Environment]::SetEnvironmentVariable("ORGANIZER_DB_PATH", "C:\FileOrganizer\data\organizer.db", [System.EnvironmentVariableTarget]::Machine)
[System.Environment]::SetEnvironmentVariable("AREAS_ROOT_PATH", "C:\FileOrganizer\areas", [System.EnvironmentVariableTarget]::Machine)
[System.Environment]::SetEnvironmentVariable("ASPNETCORE_URLS", "http://0.0.0.0:5000", [System.EnvironmentVariableTarget]::Machine)
```

### Step 4: Start the Service
```cmd
sc.exe start "FileOrganizerWeb"
```

To check service status:
```cmd
sc.exe query "FileOrganizerWeb"
```

To stop or delete the service:
```cmd
sc.exe stop "FileOrganizerWeb"
sc.exe delete "FileOrganizerWeb"
```

---

## 5. Deployment Mode 3: IIS In-Process Hosting (Port 80 / 443)

Ideal for enterprise environments integrated with Active Directory, corporate SSL certificates, and standard HTTP/HTTPS ports.

### Step 1: Install IIS & ASP.NET Core Hosting Bundle
1. Enable IIS role via Server Manager or PowerShell:
   ```powershell
   Install-WindowsFeature -name Web-Server -IncludeManagementTools
   ```
2. Download and install the **.NET 8.0 Hosting Bundle** (for `AspNetCoreModuleV2`).
   *(Even though `FileOrganizer.Web.exe` is self-contained, IIS requires `AspNetCoreModuleV2` to proxy requests in-process).*

### Step 2: Prepare Application Directory
Place the files into `C:\inetpub\wwwroot\FileOrganizer\`:
```text
C:\inetpub\wwwroot\FileOrganizer\
├── FileOrganizer.Web.exe
├── appsettings.json
├── web.config
└── wwwroot\
```

### Step 3: Verify `web.config`
Ensure `web.config` is present with `hostingModel="inprocess"`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <location path="." inheritInChildApplications="false">
    <system.webServer>
      <handlers>
        <add name="aspNetCore" path="*" verb="*" modules="AspNetCoreModuleV2" resourceType="Unspecified" />
      </handlers>
      <aspNetCore processPath=".\FileOrganizer.Web.exe"
                  stdoutLogEnabled="true"
                  stdoutLogFile=".\logs\stdout"
                  hostingModel="inprocess">
        <environmentVariables>
          <environmentVariable name="ASPNETCORE_ENVIRONMENT" value="Production" />
          <environmentVariable name="ORGANIZER_DB_PATH" value="C:\FileOrganizer\data\organizer.db" />
          <environmentVariable name="AREAS_ROOT_PATH" value="C:\FileOrganizer\areas" />
        </environmentVariables>
      </aspNetCore>
    </system.webServer>
  </location>
</configuration>
```

### Step 4: Create IIS Site or Application
In IIS Manager:
1. Create a new Application Pool:
   - Name: `FileOrganizerAppPool`
   - .NET CLR Version: `No Managed Code`
   - Managed Pipeline Mode: `Integrated`
2. Add Site:
   - Site name: `FileOrganizer`
   - Physical path: `C:\inetpub\wwwroot\FileOrganizer`
   - Binding: Port 80 (HTTP) and/or 443 (HTTPS with SSL Certificate).

---

## 6. Permissions, SQLite WAL & Network Share Configuration

### SQLite WAL Mode Concurrency Considerations
SQLite uses Write-Ahead Logging (`WAL`). When active, SQLite creates two auxiliary files alongside `organizer.db`:
- `organizer.db-wal` (Write-Ahead Log)
- `organizer.db-shm` (Shared Memory Index)

### File & Folder Permissions (ACLs)
The user account running the application (`IIS_IUSRS`, `NETWORK SERVICE`, or a dedicated service account) MUST have **Full Modify / Write** permissions to:
1. **The Database Directory**: Not just `organizer.db`, but the parent folder containing it, so SQLite can create/delete `-wal` and `-shm` files.
   ```cmd
   icacls "C:\FileOrganizer\data" /grant "IIS_IUSRS":(OI)(CI)M
   ```
2. **The Areas & Vault Root**: To save ingested PDFs into `{area}/{house}/vault/` and `{area}/{house}/batches/`.
   ```cmd
   icacls "C:\FileOrganizer\areas" /grant "IIS_IUSRS":(OI)(CI)M
   ```

### SMB / Network Share Hosting
If `AREAS_ROOT_PATH` or `ORGANIZER_DB_PATH` points to a UNC path (e.g. `\\fileserver\share\areas`):
1. **Database Placement**: It is strongly recommended that `organizer.db` reside on a **local fast SSD** drive on the web server to ensure SQLite file locking and WAL shared memory behave properly.
2. **Vault PDFs on SMB Share**: Document vaults and batches can safely reside on SMB network shares. Ensure the computer account (`DOMAIN\WEBSERVER$`) or service account has `Read/Write` share and NTFS permissions.
3. Configure UNC path in `appsettings.json`:
   ```json
   {
     "AREAS_ROOT_PATH": "\\\\fileserver\\archives\\areas"
   }
   ```

---

## 7. Windows Firewall Configuration

If running standalone or as a Windows Service on a custom port (e.g., `5000`):
```cmd
netsh advfirewall firewall add rule name="File Organizer Web Dashboard (Port 5000)" dir=in action=allow protocol=TCP localport=5000
```

For standard HTTP / HTTPS (Ports 80 / 443 with IIS):
```cmd
netsh advfirewall firewall add rule name="File Organizer HTTP (Port 80)" dir=in action=allow protocol=TCP localport=80
netsh advfirewall firewall add rule name="File Organizer HTTPS (Port 443)" dir=in action=allow protocol=TCP localport=443
```

---

## 8. Troubleshooting & Maintenance

### Diagnostic Endpoints
- Health Check: `GET /api/health` (Returns `{"status": "healthy", "timestamp": "..."}`)
- Database Status: `GET /api/db/info` (Returns connection status, table row counts, and schema verification)

### Logs
- For Standalone/Service: Logs stream to console and Windows Event Log (`Application` source).
- For IIS In-Process: Check `C:\inetpub\wwwroot\FileOrganizer\logs\stdout_*.log` (enable `stdoutLogEnabled="true"` in `web.config`).
