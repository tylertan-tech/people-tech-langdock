#!/usr/bin/env python3
"""
Quick Google Maps API key validation script.

Usage:
  # Create a .env file in this folder:
  # GOOGLE_MAPS_API_KEY=your_key_here
  python3 validate_google_maps_key.py
"""

import json
import os
import sys
import urllib.parse
import urllib.request


def load_dotenv(path: str = ".env") -> None:
    try:
        with open(path, "r", encoding="utf-8") as file:
            for raw_line in file:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key:
                    os.environ.setdefault(key, value)
    except FileNotFoundError:
        pass


def main() -> int:
    load_dotenv()
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("GOOGLE_MAPS_API_KEY is not set.")
        print("Add it to a local .env file, for example:")
        print("  GOOGLE_MAPS_API_KEY=your_key_here")
        return 1

    params = urllib.parse.urlencode(
        {
            "address": "Berlin",
            "key": api_key,
        }
    )
    url = f"https://maps.googleapis.com/maps/api/geocode/json?{params}"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body)
    except Exception as exc:
        print(f"Network/request error: {exc}")
        return 1

    status = data.get("status")
    error_message = data.get("error_message", "")

    if status == "OK":
        results = data.get("results", [])
        first = results[0] if results else {}
        formatted_address = first.get("formatted_address", "n/a")
        print("Key looks valid.")
        print(f"API status: {status}")
        print(f"Sample result: {formatted_address}")
        return 0

    print("Key check failed.")
    print(f"API status: {status}")
    if error_message:
        print(f"Google message: {error_message}")
    print("This can mean the key is invalid, the Geocoding API is disabled, or billing is not enabled.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
