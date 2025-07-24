#!/bin/bash
export NODE_OPTIONS="--max-old-space-size=4096"
export NEXT_TELEMETRY_DISABLED=1
npx next dev -p 3020
