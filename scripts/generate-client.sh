#! /usr/bin/env bash
# Copy openapi schema from backend and paste inside frontend dir, then generate client using openapi-ts

set -e
set -x

cd ..
cd backend
source venv/bin/activate

cd app
python3 -c "import main; import json; print(json.dumps(main.app.openapi()))" > ../openapi.json
cd ..
mv openapi.json ../frontend/
cd ../frontend
npm run generate-client
#npx biome format --write ./src/client

