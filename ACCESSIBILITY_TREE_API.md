# Accessibility Tree API

The Observer Service now includes an endpoint to retrieve the browser accessibility tree for the current webpage. This provides semantic information about the page structure including ARIA attributes, roles, labels, and accessibility properties.

## Endpoint

### GET `/accessibility-tree`

Retrieves the accessibility tree for the current webpage.

#### Query Parameters

- `include_ignored` (boolean, optional): Whether to include ignored elements in the tree. Default: `false`
- `include_hidden` (boolean, optional): Whether to include hidden elements in the tree. Default: `false`

#### Response

```json
{
  "success": true,
  "accessibility_tree": {
    "name": "Example Domain",
    "role": "WebArea",
    "children": [
      {
        "name": "Example Domain",
        "role": "heading",
        "level": 1
      },
      {
        "name": "This domain is for use in illustrative examples in documents.",
        "role": "text"
      }
    ]
  },
  "message": "Accessibility tree retrieved successfully"
}
```

#### Example Usage

```bash
# Get default accessibility tree (filtered)
curl "http://localhost:8002/accessibility-tree"

# Get accessibility tree with ignored elements
curl "http://localhost:8002/accessibility-tree?include_ignored=true"

# Get accessibility tree with hidden elements
curl "http://localhost:8002/accessibility-tree?include_hidden=true"

# Get complete accessibility tree (both ignored and hidden elements)
curl "http://localhost:8002/accessibility-tree?include_ignored=true&include_hidden=true"
```

## Accessibility Tree Structure

Each node in the accessibility tree contains the following properties:

- `name`: The accessible name of the element
- `role`: The ARIA role or semantic role of the element
- `children`: Array of child accessibility nodes
- `ignored`: Whether the element is ignored by accessibility tools
- `level`: Heading level (for heading elements)
- `value`: Current value (for form controls)
- `description`: Additional description text
- `keyshortcuts`: Keyboard shortcuts
- `roledescription`: Custom role description
- `valuetext`: Human-readable value text
- `disabled`: Whether the element is disabled
- `expanded`: Whether the element is expanded
- `focused`: Whether the element is focused
- `modal`: Whether the element is modal
- `multiline`: Whether the element supports multiple lines
- `multiselectable`: Whether the element supports multiple selection
- `readonly`: Whether the element is read-only
- `required`: Whether the element is required
- `selected`: Whether the element is selected

## Use Cases

1. **Semantic Locator Resolution**: Use accessibility information to improve locator resolution accuracy
2. **Accessibility Testing**: Verify that web pages meet accessibility standards
3. **Screen Reader Simulation**: Understand how screen readers would interpret the page
4. **UI Automation**: Find elements based on their semantic meaning rather than just visual properties

## Integration with Semantic Locator Service

The accessibility tree can be integrated with the semantic locator service to improve locator resolution by:

1. Using ARIA labels and roles for better element identification
2. Leveraging semantic relationships between elements
3. Understanding the hierarchical structure of the page
4. Identifying interactive elements more accurately

## Testing

Run the test script to verify the functionality:

```bash
python test_accessibility_tree.py
```

This will:
1. Navigate to example.com
2. Test all filtering options
3. Save the results to JSON files for inspection 