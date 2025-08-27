#!/usr/bin/env python3
"""
Simple SSE client to test the graph streaming API and display all events.
"""

import requests
import json
import sys

def test_streaming_api(base_url="http://localhost:8000", message="Test streaming message"):
    """Test the streaming API and display all SSE events."""
    
    url = f"{base_url}/stream-graph"
    payload = {"message": message}
    
    print(f"🚀 Testing streaming API at: {url}")
    print(f"📤 Sending payload: {json.dumps(payload, indent=2)}")
    print("=" * 60)
    
    try:
        # Make the request with stream=True to handle SSE
        response = requests.post(
            url,
            json=payload,
            headers={"Accept": "text/event-stream"},
            stream=True,
            timeout=30  # 30 second timeout
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        print("📡 Connected! Receiving SSE events:")
        print("-" * 40)
        
        event_count = 0
        
        # Process the streaming response
        for line in response.iter_lines(decode_unicode=True):
            if line:
                print(f"📨 Raw line: {repr(line)}")
                
                # SSE events start with "data: "
                if line.startswith("data: "):
                    event_count += 1
                    # Extract and parse the JSON data
                    json_data = line[6:]  # Remove "data: " prefix
                    try:
                        event_data = json.loads(json_data)
                        
                        print(f"✅ Event #{event_count}:")
                        print(f"   📋 Data: {json.dumps(event_data, indent=6)}")
                        
                        # Check if this is a completion event
                        if event_data.get("type") == "completion":
                            print("🏁 Stream completed!")
                            break
                            
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to parse JSON: {e}")
                        print(f"   📄 Raw data: {json_data}")
                
                print("-" * 40)
        
        print(f"\n🎉 Successfully received {event_count} events!")
        print("✅ Stream terminated properly")
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to {url}")
        print("💡 Make sure the server is running: uv run src/now/stream_api.py")
        sys.exit(1)
        
    except requests.exceptions.Timeout:
        print("⏰ Request timed out")
        sys.exit(1)
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(0)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the Graph Streaming API")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="Base URL of the API (default: http://localhost:8000)")
    parser.add_argument("--message", default="Test streaming message",
                       help="Message to send to the graph")
    
    args = parser.parse_args()
    
    test_streaming_api(args.url, args.message)