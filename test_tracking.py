#!/usr/bin/env python3
"""
Test script for the E-commerce Tracking API
This script demonstrates the complete tracking workflow
"""

import requests
import json
import uuid
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"

def print_response(response, title):
    """Print formatted API response"""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print(f"{'='*50}")

def test_tracking_api():
    """Test the complete tracking API workflow"""
    
    print("🚀 Starting E-commerce Tracking API Test")
    print(f"API Base URL: {BASE_URL}")
    
    # Step 1: Create a product first
    print("\n📦 Step 1: Creating a test product...")
    product_data = {
        "name": "Test Smartphone",
        "description": "A test smartphone for tracking demo",
        "price": 599.99,
        "quantity": 10,
        "rating": 4.5,
        "img_url": "https://example.com/smartphone.jpg"
    }
    
    response = requests.post(f"{BASE_URL}/products/", json=product_data)
    if response.status_code != 200:
        print("❌ Failed to create product")
        return
    
    product = response.json()
    product_id = product["id"]
    print(f"✅ Product created with ID: {product_id}")
    
    # Step 2: Create an order
    print("\n🛒 Step 2: Creating an order...")
    order_data = {
        "product_id": product_id,
        "user_id": str(uuid.uuid4())  # Generate a random user ID
    }
    
    response = requests.post(f"{BASE_URL}/orders/", json=order_data)
    if response.status_code != 201:
        print("❌ Failed to create order")
        return
    
    order = response.json()
    order_id = order["id"]
    print(f"✅ Order created with ID: {order_id}")
    
    # Step 3: Create tracking for the order
    print("\n📋 Step 3: Creating tracking record...")
    tracking_data = {
        "order_id": order_id,
        "current_location": "Manmad"
    }
    
    response = requests.post(f"{BASE_URL}/track/create", json=tracking_data)
    if response.status_code != 201:
        print("❌ Failed to create tracking")
        return
    
    tracking = response.json()
    tracking_id = tracking["tracking_id"]
    print(f"✅ Tracking created with ID: {tracking_id}")
    print(f"   Current Location: {tracking['current_location']}")
    print(f"   Status: {tracking['status']}")
    print(f"   Progress: {tracking['progress_percentage']:.1f}%")
    
    # Step 4: Get initial tracking info
    print("\n📍 Step 4: Getting initial tracking information...")
    response = requests.get(f"{BASE_URL}/track/{tracking_id}")
    if response.status_code == 200:
        tracking_info = response.json()
        print(f"✅ Tracking Info Retrieved")
        print(f"   Current Location: {tracking_info['current_location']}")
        print(f"   Status: {tracking_info['status']}")
        print(f"   Progress: {tracking_info['progress_percentage']:.1f}%")
        print(f"   Next Location: {tracking_info['next_location']}")
        if tracking_info.get('estimated_delivery'):
            print(f"   Estimated Delivery: {tracking_info['estimated_delivery']}")
    
    # Step 5: Update location through the shipping route
    shipping_route = ["Yeola", "Kopargaon", "Talegaon Dighe", "Sangamner"]
    
    for i, location in enumerate(shipping_route, 1):
        print(f"\n🚚 Step {4+i}: Updating location to {location}...")
        
        update_data = {
            "current_location": location
        }
        
        response = requests.put(f"{BASE_URL}/track/update/{tracking_id}", json=update_data)
        if response.status_code == 200:
            updated_tracking = response.json()
            print(f"✅ Location updated successfully")
            print(f"   Current Location: {updated_tracking['current_location']}")
            print(f"   Status: {updated_tracking['status']}")
            print(f"   Progress: {updated_tracking['progress_percentage']:.1f}%")
            print(f"   Next Location: {updated_tracking['next_location']}")
        else:
            print(f"❌ Failed to update location: {response.text}")
            break
    
    # Step 6: Mark as delivered
    print("\n🎉 Step 9: Marking order as delivered...")
    response = requests.put(f"{BASE_URL}/track/deliver/{tracking_id}")
    if response.status_code == 200:
        final_tracking = response.json()
        print(f"✅ Order marked as delivered!")
        print(f"   Final Location: {final_tracking['current_location']}")
        print(f"   Final Status: {final_tracking['status']}")
        print(f"   Final Progress: {final_tracking['progress_percentage']:.1f}%")
    else:
        print(f"❌ Failed to mark as delivered: {response.text}")
    
    # Step 7: Get final tracking info
    print("\n📊 Step 10: Getting final tracking information...")
    response = requests.get(f"{BASE_URL}/track/{tracking_id}")
    if response.status_code == 200:
        final_info = response.json()
        print(f"✅ Final Tracking Info")
        print(f"   Current Location: {final_info['current_location']}")
        print(f"   Status: {final_info['status']}")
        print(f"   Progress: {final_info['progress_percentage']:.1f}%")
        print(f"   Next Location: {final_info['next_location']}")
    
    # Step 8: Get shipping routes
    print("\n🗺️ Step 11: Getting shipping routes...")
    response = requests.get(f"{BASE_URL}/track/routes/list")
    if response.status_code == 200:
        routes = response.json()
        print(f"✅ Shipping Routes Retrieved")
        print(f"   Total Stops: {routes['total_stops']}")
        print(f"   Routes: {' → '.join(routes['routes'])}")
    
    print("\n🎯 Tracking API Test Completed Successfully!")
    print(f"📋 Tracking ID for reference: {tracking_id}")

def test_error_handling():
    """Test error handling scenarios"""
    print("\n🔍 Testing Error Handling...")
    
    # Test 1: Invalid tracking ID
    print("\n❌ Test 1: Invalid tracking ID")
    response = requests.get(f"{BASE_URL}/track/INVALID123")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 2: Invalid location
    print("\n❌ Test 2: Invalid location update")
    response = requests.put(f"{BASE_URL}/track/update/TRK12345678", 
                          json={"current_location": "InvalidLocation"})
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    try:
        # Test the main tracking workflow
        test_tracking_api()
        
        # Test error handling
        test_error_handling()
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the API server is running on http://localhost:8000")
        print("💡 Start the server with: python -m app.main")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
