#!/bin/sh
set -eu

ollama serve &
server_pid=$!

until ollama list >/dev/null 2>&1; do
  sleep 2
done

ollama pull "${OLLAMA_VISION_MODEL:-qwen2.5vl:3b}"
wait "$server_pid"
