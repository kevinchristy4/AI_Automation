#!/usr/bin/env python3
"""
Test script for the accessibility locator generation functionality.
Demonstrates how to generate locators from accessibility tree data.
"""

import asyncio
import httpx
import json
from typing import Dict, Any

async def test_accessibility_locators():
    """Test the accessibility locators endpoint"""
    
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
            
            # Test 1: Get accessibility locators (default filtering)
            print("\n=== Test 1: Accessibility Locators (filtered) ===")
            locators_url = "http://localhost:8002/accessibility-locators"
            response = await client.get(locators_url)
            response.raise_for_status()
            
            result = response.json()
            print(f"Success: {result.get('success')}")
            print(f"Message: {result.get('message')}")
            
            if result.get('success') and result.get('elements'):
                elements = result['elements']
                print(f"Generated {len(elements)} elements with locators")
                
                # Display first few elements
                print(f"\nFirst 5 elements:")
                for i, element in enumerate(elements[:5]):
                    print(f"\n  {i+1}. Signature: {element['signature']}")
                    print(f"     Locators ({len(element['locators'])}):")
                    for j, locator in enumerate(element['locators'][:3]):  # Show top 3 locators
                        print(f"       {j+1}. {locator['type']}: {locator['locator']} (score: {locator['score']})")
                
                # Save the results
                with open("accessibility_locators_filtered.json", "w", encoding="utf-8") as f:
                    json.dump(elements, f, indent=2, ensure_ascii=False)
                print(f"\nFiltered locators saved to accessibility_locators_filtered.json")
            
            # Test 2: Get accessibility locators with ignored elements
            print("\n=== Test 2: Accessibility Locators (with ignored elements) ===")
            response = await client.get(locators_url, params={"include_ignored": "true"})
            response.raise_for_status()
            
            result = response.json()
            if result.get('success') and result.get('elements'):
                elements = result['elements']
                print(f"Generated {len(elements)} elements with locators (including ignored)")
                
                # Save the results
                with open("accessibility_locators_with_ignored.json", "w", encoding="utf-8") as f:
                    json.dump(elements, f, indent=2, ensure_ascii=False)
                print(f"Locators with ignored elements saved to accessibility_locators_with_ignored.json")
            
            # Test 3: Analyze locator types
            print("\n=== Test 3: Locator Type Analysis ===")
            response = await client.get(locators_url)
            response.raise_for_status()
            result = response.json()
            
            if result.get('success') and result.get('elements'):
                elements = result['elements']
                
                # Count locator types
                locator_types = {}
                total_locators = 0
                
                for element in elements:
                    for locator in element['locators']:
                        loc_type = locator['type']
                        locator_types[loc_type] = locator_types.get(loc_type, 0) + 1
                        total_locators += 1
                
                print(f"Total elements: {len(elements)}")
                print(f"Total locators: {total_locators}")
                print(f"Locator type distribution:")
                for loc_type, count in sorted(locator_types.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / total_locators) * 100
                    print(f"  {loc_type}: {count} ({percentage:.1f}%)")
                
                # Show examples of each locator type
                print(f"\nExamples of each locator type:")
                examples = {}
                for element in elements:
                    for locator in element['locators']:
                        loc_type = locator['type']
                        if loc_type not in examples:
                            examples[loc_type] = {
                                'locator': locator['locator'],
                                'signature': element['signature'],
                                'score': locator['score']
                            }
                
                for loc_type, example in examples.items():
                    print(f"  {loc_type}:")
                    print(f"    Locator: {example['locator']}")
                    print(f"    Signature: {example['signature']}")
                    print(f"    Score: {example['score']}")
                    print()
                
        except httpx.RequestError as e:
            print(f"Request error: {e}")
        except Exception as e:
            print(f"Error: {e}")

def demonstrate_accessibility_xpath_generation():
    """
    Demonstrate how accessibility-based XPath generation works.
    """
    print("\n=== Accessibility XPath Generation Examples ===")
    
    # Example accessibility tree nodes
    example_nodes = [
        {
            "role": "button",
            "name": "Sign In",
            "disabled": False
        },
        {
            "role": "heading",
            "name": "Welcome",
            "level": 1
        },
        {
            "role": "textbox",
            "name": "Email",
            "value": "",
            "required": True
        },
        {
            "role": "link",
            "name": "Forgot Password?",
            "disabled": False
        }
    ]
    
    from services.observer_service.accessibility_locator_generator import AccessibilityLocatorGenerator
    
    for i, node in enumerate(example_nodes):
        print(f"\nExample {i+1}: {node['role']} - {node['name']}")
        
        # Generate accessibility XPath
        axpath = AccessibilityLocatorGenerator._generate_accessibility_xpath(node, "")
        print(f"  Accessibility XPath: {axpath}")
        
        # Generate all locators
        locators = AccessibilityLocatorGenerator._generate_node_locators(node, "")
        print(f"  Generated {len(locators)} locators:")
        for j, locator in enumerate(locators):
            print(f"    {j+1}. {locator['type']}: {locator['locator']} (score: {locator['score']})")

if __name__ == "__main__":
    # Run the main test
    asyncio.run(test_accessibility_locators())
    
    # Demonstrate XPath generation
    demonstrate_accessibility_xpath_generation() 