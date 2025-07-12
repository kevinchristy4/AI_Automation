#!/usr/bin/env python3
"""
Example demonstrating how accessibility locator generation works with sample data.
This shows how the system would process the accessibility tree nodes you provided.
"""

import sys
import os

# Add the project root to the path to allow for absolute imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from services.observer_service.accessibility_locator_generator import AccessibilityLocatorGenerator

def demonstrate_sample_data():
    """
    Demonstrate how the accessibility locator generator would process your sample data.
    """
    print("=== Accessibility Locator Generation Example ===\n")
    
    # Your sample accessibility tree nodes
    sample_nodes = [
        {
            "role": "text",
            "name": "Broadcast your skills to managers at your company",
            "children": []
        },
        {
            "role": "text", 
            "name": "Earn credentials that translate to college credit",
            "children": []
        },
        {
            "role": "text",
            "name": "Discover new professional opportunities", 
            "children": []
        },
        {
            "role": "heading",
            "name": "Sign In",
            "level": 2,
            "children": []
        },
        {
            "role": "text",
            "name": "Email",
            "children": []
        }
    ]
    
    print("Processing your sample accessibility tree nodes:\n")
    
    for i, node in enumerate(sample_nodes):
        print(f"Node {i+1}: {node['role']} - '{node['name']}'")
        
        # Generate locators for this node
        locators = AccessibilityLocatorGenerator._generate_node_locators(node, f"node[{i+1}]")
        
        if locators:
            print(f"  Generated {len(locators)} locators:")
            for j, locator in enumerate(locators):
                print(f"    {j+1}. {locator['type']}: {locator['locator']} (score: {locator['score']})")
        else:
            print("  No locators generated (likely disabled or generic element)")
        
        # Generate signature
        signature = AccessibilityLocatorGenerator._generate_signature(node)
        print(f"  Signature: {signature}")
        
        # Generate accessibility XPath
        axpath = AccessibilityLocatorGenerator._generate_accessibility_xpath(node, f"node[{i+1}]")
        print(f"  Accessibility XPath: {axpath}")
        print()

def demonstrate_complete_tree():
    """
    Demonstrate processing a complete accessibility tree structure.
    """
    print("=== Complete Accessibility Tree Processing ===\n")
    
    # Simulate a complete accessibility tree with your sample data
    complete_tree = {
        "role": "WebArea",
        "name": "Example Page",
        "children": [
            {
                "role": "text",
                "name": "Broadcast your skills to managers at your company",
                "children": []
            },
            {
                "role": "text", 
                "name": "Earn credentials that translate to college credit",
                "children": []
            },
            {
                "role": "text",
                "name": "Discover new professional opportunities", 
                "children": []
            },
            {
                "role": "heading",
                "name": "Sign In",
                "level": 2,
                "children": []
            },
            {
                "role": "text",
                "name": "Email",
                "children": []
            }
        ]
    }
    
    print("Processing complete accessibility tree...")
    
    # Generate locators for all elements
    elements = AccessibilityLocatorGenerator.generate_locators_from_accessibility_tree(complete_tree)
    
    print(f"\nGenerated {len(elements)} elements with locators:\n")
    
    for i, element in enumerate(elements):
        print(f"Element {i+1}:")
        print(f"  Signature: {element['signature']}")
        print(f"  Locators ({len(element['locators'])}):")
        for j, locator in enumerate(element['locators']):
            print(f"    {j+1}. {locator['type']}: {locator['locator']} (score: {locator['score']})")
        print()

def demonstrate_xpath_generation():
    """
    Demonstrate accessibility-based XPath generation.
    """
    print("=== Accessibility XPath Generation Examples ===\n")
    
    # Example nodes with different properties
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
            "role": "checkbox",
            "name": "Remember me",
            "selected": False
        },
        {
            "role": "link",
            "name": "Forgot Password?",
            "disabled": False
        }
    ]
    
    for i, node in enumerate(example_nodes):
        print(f"Example {i+1}: {node['role']} - '{node['name']}'")
        
        # Generate accessibility XPath
        axpath = AccessibilityLocatorGenerator._generate_accessibility_xpath(node, "")
        print(f"  Accessibility XPath: {axpath}")
        
        # Show what this XPath would match
        print(f"  Matches: Elements with role='{node['role']}' and name containing '{node['name']}'")
        
        # Add additional conditions if present
        if node.get('level'):
            print(f"  Additional: aria-level='{node['level']}'")
        if node.get('required'):
            print(f"  Additional: aria-required='true'")
        if node.get('selected') is not None:
            print(f"  Additional: aria-checked='{str(node['selected']).lower()}'")
        if node.get('disabled'):
            print(f"  Additional: aria-disabled='true'")
        
        print()

def show_advantages():
    """
    Show the advantages of accessibility-based locators.
    """
    print("=== Advantages of Accessibility-Based Locators ===\n")
    
    advantages = [
        {
            "aspect": "Semantic Accuracy",
            "description": "Uses ARIA roles and accessible names instead of HTML structure",
            "example": "page.get_by_role('button', { name: 'Sign In' }) vs page.locator('button.btn-primary')"
        },
        {
            "aspect": "Resilience to Changes", 
            "description": "Survives CSS changes, layout modifications, and HTML restructuring",
            "example": "Still works if button class changes from 'btn-primary' to 'btn-login'"
        },
        {
            "aspect": "Accessibility Compliance",
            "description": "Uses the same information screen readers use",
            "example": "Ensures elements are properly labeled and accessible"
        },
        {
            "aspect": "User Intent Matching",
            "description": "Matches how users think about elements",
            "example": "'Click the Sign In button' matches 'button with name Sign In'"
        },
        {
            "aspect": "State Awareness",
            "description": "Understands element states (disabled, required, checked, etc.)",
            "example": "page.get_by_role('checkbox', { name: 'Remember me', checked: true })"
        }
    ]
    
    for i, advantage in enumerate(advantages):
        print(f"{i+1}. {advantage['aspect']}")
        print(f"   {advantage['description']}")
        print(f"   Example: {advantage['example']}")
        print()

if __name__ == "__main__":
    # Run all demonstrations
    demonstrate_sample_data()
    demonstrate_complete_tree() 
    demonstrate_xpath_generation()
    show_advantages()
    
    print("\n=== Summary ===")
    print("The accessibility locator generator provides:")
    print("✅ Semantic, resilient locators based on ARIA roles and names")
    print("✅ Accessibility-compliant element identification")
    print("✅ Better user intent matching")
    print("✅ State-aware locator generation")
    print("✅ XPath generation using accessibility properties")
    print("\nThis approach is more robust and maintainable than traditional DOM-based locators!") 