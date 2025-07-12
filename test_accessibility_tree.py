#!/usr/bin/env python3
"""
Test script for the accessibility tree endpoint in the observer service.
"""

import asyncio
import httpx
import json
from typing import Dict, Any

async def test_accessibility_tree():
    """Test the accessibility tree endpoint"""
    
    # First, navigate to a test page
    navigate_url = "http://localhost:8002/navigate"
    navigate_data = {"url": "https://example.com"}
    
    async with httpx.AsyncClient() as client:
        try:
            # Navigate to the test page
            print("Navigating to example.com...")
            response = await client.post(navigate_url, json=navigate_data)
            response.raise_for_status()
            print(f"Navigation response: {response.json()}")
            
            # Wait a moment for the page to load
            await asyncio.sleep(2)
            
            # Test 1: Get default accessibility tree (filtered)
            print("\n=== Test 1: Default accessibility tree (filtered) ===")
            accessibility_url = "http://localhost:8002/accessibility-tree"
            response = await client.get(accessibility_url)
            response.raise_for_status()
            
            result = response.json()
            print(f"Success: {result.get('success')}")
            print(f"Message: {result.get('message')}")
            
            if result.get('success') and result.get('accessibility_tree'):
                tree = result['accessibility_tree']
                print(f"Root node name: {tree.get('name', 'N/A')}")
                print(f"Root node role: {tree.get('role', 'N/A')}")
                print(f"Number of children: {len(tree.get('children', []))}")
                
                # Save the filtered tree
                with open("accessibility_tree_filtered.json", "w", encoding="utf-8") as f:
                    json.dump(tree, f, indent=2, ensure_ascii=False)
                print(f"Filtered tree saved to accessibility_tree_filtered.json")
            
            # Test 2: Get accessibility tree with ignored elements
            print("\n=== Test 2: Accessibility tree with ignored elements ===")
            response = await client.get(accessibility_url, params={"include_ignored": "true"})
            response.raise_for_status()
            
            result = response.json()
            if result.get('success') and result.get('accessibility_tree'):
                tree = result['accessibility_tree']
                print(f"Root node name: {tree.get('name', 'N/A')}")
                print(f"Root node role: {tree.get('role', 'N/A')}")
                print(f"Number of children: {len(tree.get('children', []))}")
                
                # Save the tree with ignored elements
                with open("accessibility_tree_with_ignored.json", "w", encoding="utf-8") as f:
                    json.dump(tree, f, indent=2, ensure_ascii=False)
                print(f"Tree with ignored elements saved to accessibility_tree_with_ignored.json")
            
            # Test 3: Get accessibility tree with hidden elements
            print("\n=== Test 3: Accessibility tree with hidden elements ===")
            response = await client.get(accessibility_url, params={"include_hidden": "true"})
            response.raise_for_status()
            
            result = response.json()
            if result.get('success') and result.get('accessibility_tree'):
                tree = result['accessibility_tree']
                print(f"Root node name: {tree.get('name', 'N/A')}")
                print(f"Root node role: {tree.get('role', 'N/A')}")
                print(f"Number of children: {len(tree.get('children', []))}")
                
                # Save the tree with hidden elements
                with open("accessibility_tree_with_hidden.json", "w", encoding="utf-8") as f:
                    json.dump(tree, f, indent=2, ensure_ascii=False)
                print(f"Tree with hidden elements saved to accessibility_tree_with_hidden.json")
            
            # Test 4: Get accessibility tree with both ignored and hidden elements
            print("\n=== Test 4: Accessibility tree with both ignored and hidden elements ===")
            response = await client.get(accessibility_url, params={
                "include_ignored": "true", 
                "include_hidden": "true"
            })
            response.raise_for_status()
            
            result = response.json()
            if result.get('success') and result.get('accessibility_tree'):
                tree = result['accessibility_tree']
                print(f"Root node name: {tree.get('name', 'N/A')}")
                print(f"Root node role: {tree.get('role', 'N/A')}")
                print(f"Number of children: {len(tree.get('children', []))}")
                
                # Save the complete tree
                with open("accessibility_tree_complete.json", "w", encoding="utf-8") as f:
                    json.dump(tree, f, indent=2, ensure_ascii=False)
                print(f"Complete tree saved to accessibility_tree_complete.json")
                
        except httpx.RequestError as e:
            print(f"Request error: {e}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_accessibility_tree()) 