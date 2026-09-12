#!/bin/bash
export PATH="$HOME/.dotnet:$PATH"

# Remote paths (SMB network share)
REMOTE_DB="/Volumes/arshad-pc/areas_v11/organizer.db"
AREAS_ROOT="/Volumes/arshad-pc/areas_v11"

# Local DB cache — SQLite random-reads over SMB are ~250x slower than local disk.
# Copy the DB locally at startup; AREAS_ROOT stays on SMB for PDF file serving.
LOCAL_DB="/tmp/file_organizer_local.db"

if [ -f "$REMOTE_DB" ]; then
    NEED_COPY=0
    if [ ! -f "$LOCAL_DB" ]; then
        NEED_COPY=1
    elif [ "$(sqlite3 "$LOCAL_DB" "PRAGMA quick_check;" 2>/dev/null)" != "ok" ]; then
        echo "⚠️  Local copy failed integrity check, re-copying..."
        NEED_COPY=1
    fi

    if [ "$NEED_COPY" -eq 1 ]; then
        echo "📋 Copying database locally for performance (SMB → local)..."
        TEMP_COPY="/tmp/file_organizer_copy.db"
        if cp "$REMOTE_DB" "$TEMP_COPY" && [ "$(sqlite3 "$TEMP_COPY" "PRAGMA quick_check;" 2>/dev/null)" = "ok" ]; then
            mv "$TEMP_COPY" "$LOCAL_DB"
            echo "✅ Local copy ready and verified: $LOCAL_DB ($(du -h "$LOCAL_DB" | cut -f1))"
        else
            echo "⚠️  Copy failed or corrupted, keeping existing local copy if available"
            rm -f "$TEMP_COPY"
        fi
    else
        echo "✅ Existing local copy is valid: $LOCAL_DB ($(du -h "$LOCAL_DB" | cut -f1))"
    fi
    DB_PATH="$LOCAL_DB"
elif [ -f "$LOCAL_DB" ]; then
    DB_PATH="$LOCAL_DB"
    echo "⚠️  Remote DB not available, using existing local copy"
else
    DB_PATH="$(pwd)/organizer.db"
    AREAS_ROOT="$(pwd)/areas"
fi

PORT=5000
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || ifconfig | grep "inet " | grep -v 127.0.0.1 | head -n1 | awk '{print $2}')

echo "🚀 Starting File Organizer .NET Web Server on Mac..."
echo "📁 Database: $DB_PATH"
echo "📂 Areas Root: $AREAS_ROOT"
echo "🌐 Local:   http://localhost:$PORT"
if [ -n "$LOCAL_IP" ]; then
    echo "📱 Network: http://$LOCAL_IP:$PORT  (Accessible to other devices on the same Wi-Fi / network)"
fi

~/.dotnet/dotnet run --project web-net/FileOrganizer.Web.csproj --urls "http://0.0.0.0:$PORT" --ORGANIZER_DB_PATH "$DB_PATH" --AREAS_ROOT_PATH "$AREAS_ROOT"
