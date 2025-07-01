#! /usr/bin/env bash

set -e
set -x

cd ..
cd backend
cd app
python -c "import main; import json; print(json.dumps(main.app.openapi()))" > ../openapi.json
cd ..
mv openapi.json ../frontend/
cd ../frontend
npm run generate-client
npx biome format --write ./src/client
