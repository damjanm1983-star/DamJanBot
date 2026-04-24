#!/bin/bash
# Wrapper script for vibe-trading-mcp with virtual environment

source /home/dame/.openclaw/workspace/trading_bot/venv/bin/activate
exec vibe-trading-mcp "$@"
