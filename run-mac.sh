#!/bin/bash
export PATH="$HOME/.dotnet:$PATH"

# Resolve DB path
DB_PATH="/Volumes/arshad-pc/areas_20260908_v11test/organizer.db"
AREAS_ROOT="/Volumes/arshad-pc/areas_20260908_v11test"

if [ ! -f "$DB_PATH" ]; then
    DB_PATH="$(pwd)/organizer.db"
    AREAS_ROOT="$(pwd)/areas"
fi

echo "🚀 Starting File Organizer .NET Web Server on Mac..."
echo "📁 Database: $DB_PATH"
echo "🌐 Open browser at: http://localhost:5000"

~/.dotnet/dotnet run --project web-net/FileOrganizer.Web.csproj --urls "http://localhost:5000" --ORGANIZER_DB_PATH "$DB_PATH" --AREAS_ROOT_PATH "$AREAS_ROOT"
