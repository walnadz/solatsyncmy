#!/usr/bin/env python3
"""
Test script to check if services are properly registered in Home Assistant.
Run this script to see if the services are available with their UI schemas.
"""

import requests
import json
import sys

# Home Assistant configuration
HA_URL = "http://192.168.0.114:8123"  # Your Home Assistant URL
HA_TOKEN = None  # You'll need to get this from Home Assistant

def get_services():
    """Get all services from Home Assistant."""
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    } if HA_TOKEN else {}
    
    try:
        response = requests.get(f"{HA_URL}/api/services", headers=headers)
        if response.status_code == 200:
            services = response.json()
            return services
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Connection error: {e}")
        return None

def check_solatsyncmy_services():
    """Check if solatsyncmy services are registered."""
    print("🔍 Checking solatsyncmy services...")
    
    services = get_services()
    if not services:
        print("❌ Could not retrieve services from Home Assistant")
        return
    
    # Look for solatsyncmy domain
    solat_services = None
    for domain_data in services:
        if domain_data.get("domain") == "solatsyncmy":
            solat_services = domain_data.get("services", {})
            break
    
    if not solat_services:
        print("❌ No solatsyncmy services found!")
        print("📝 Available domains:", [d.get("domain") for d in services[:10]])
        return
    
    print("✅ Found solatsyncmy services!")
    
    expected_services = ["refresh_prayer_times", "play_azan", "test_audio"]
    
    for service_name in expected_services:
        if service_name in solat_services:
            service_data = solat_services[service_name]
            print(f"\n📋 Service: {service_name}")
            print(f"   Name: {service_data.get('name', 'N/A')}")
            print(f"   Description: {service_data.get('description', 'N/A')}")
            
            fields = service_data.get("fields", {})
            if fields:
                print(f"   Fields: {len(fields)} field(s)")
                for field_name, field_data in fields.items():
                    print(f"     - {field_name}: {field_data.get('description', 'N/A')}")
            else:
                print("   ⚠️  No fields found (UI won't show options)")
        else:
            print(f"❌ Service '{service_name}' not found!")

def main():
    """Main function."""
    print("🏠 Home Assistant Service Checker")
    print("=" * 50)
    
    if not HA_TOKEN:
        print("⚠️  No HA_TOKEN provided - trying without authentication")
        print("   If this fails, get a Long-Lived Access Token from Home Assistant:")
        print("   Profile → Security → Long-Lived Access Tokens")
        print()
    
    check_solatsyncmy_services()
    
    print("\n" + "=" * 50)
    print("💡 If services show but have no fields:")
    print("   1. Restart Home Assistant completely")
    print("   2. Check that services.yaml is in the integration folder")
    print("   3. Check Home Assistant logs for any errors")

if __name__ == "__main__":
    main() 