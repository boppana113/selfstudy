#!/bin/bash
# Store your Anthropic API key in the macOS Keychain, once.
# You type it at a hidden prompt: it never lands in a file, an env var,
# your shell history, or the process list. server.py reads it from the Keychain.
#
# Tip: create a dedicated key for this (console.anthropic.com → API keys) and
# set a monthly spend limit, so a leak is capped and one click to revoke.
#
# Replace the key: run this again.   Remove it:
#   security delete-generic-password -s dsa-call-anthropic
echo "Paste your Anthropic API key at the prompt (input is hidden)."
security add-generic-password -U -s dsa-call-anthropic -a "$USER" -l "dsa-call Anthropic API key" -w
echo "Saved to the Keychain as 'dsa-call-anthropic'."
