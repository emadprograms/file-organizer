#!/bin/bash
export PATH="$HOME/.dotnet:$PATH"

# Remote paths (SMB network share)
REMOTE_DB="/Volumes/arshad-pc/areas_v11/organizer.db"
AREAS_ROOT="/Volumes/arshad-pc/areas_v11"

# Local DB cache — SQLite random-reads over SMB are ~250x slower than local disk.
# Copy the DB locally at startup; AREAS_ROOT stays on SMB for PDF file serving.
LOCAL_DB="/tmp/file_organizer_local.db"

if [ -f "$REMOTE_DB" ]; then
    echo "📋 Copying database locally for performance (SMB → local)..."
    cp "$REMOTE_DB" "$LOCAL_DB"
    DB_PATH="$LOCAL_DB"
    echo "✅ Local copy ready: $LOCAL_DB ($(du -h "$LOCAL_DB" | cut -f1))"
elif [ -f "$LOCAL_DB" ]; then
    DB_PATH="$LOCAL_DB"
    echo "⚠️  Remote DB not available, using existing local copy"
else
    DB_PATH="$(pwd)/organizer.db"
    AREAS_ROOT="$(pwd)/areas"
fi

echo "🚀 Starting File Organizer .NET Web Server on Mac..."
echo "📁 Database: $DB_PATH"
echo "📂 Areas Root: $AREAS_ROOT"
echo "🌐 Open browser at: http://localhost:5000"

~/.dotnet/dotnet run --project web-net/FileOrganizer.Web.csproj --urls "http://localhost:5000" --ORGANIZER_DB_PATH "$DB_PATH" --AREAS_ROOT_PATH "$AREAS_ROOT"
