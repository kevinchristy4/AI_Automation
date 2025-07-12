# Accessibility Locators API

The Observer Service now includes functionality to generate Playwright locators directly from the browser's accessibility tree. This provides a more semantic and robust approach to locator generation compared to traditional DOM parsing.

## Overview

The accessibility tree contains rich semantic information about web elements, including:
- **ARIA roles** (button, link, heading, textbox, etc.)
- **Accessible names** (what screen readers announce)
- **Form properties** (required, disabled, value, etc.)
- **Hierarchical relationships** between elements
- **State information** (expanded, selected, focused, etc.)

This information is used to generate high-quality, semantic locators that are more resilient to UI changes.

## Endpoints

### GET `/accessibility-locators`

Generates Playwright locators for all elements in the accessibility tree.

#### Query Parameters

- `include_ignored` (boolean, optional): Whether to include ignored elements. Default: `false`
- `include_hidden` (boolean, optional): Whether to include hidden elements. Default: `false`

#### Response

```json
{
  "success": true,
  "elements": [
    {
      "signature": "button, name: Sign In",
      "locators": [
        {
          "type": "get_by_role",
          "locator": "page.get_by_role('button', { name: 'Sign In' })",
          "score": 0.95
        },
        {
          "type": "get_by_text",
          "locator": "page.get_by_text('Sign In')",
          "score": 0.80
        },
        {
          "type": "xpath",
          "locator": "page.locator('//*[@role=\"button\"][contains(@aria-label, \"Sign In\") or contains(text(), \"Sign In\")]')",
          "score": 0.60
        }
      ]
    }
  ],
  "message": "Generated 15 elements with locators"
}
```

## Generated Locator Types

### 1. `get_by_role` (Highest Priority - Score: 0.95)
Uses ARIA roles and accessible names for semantic element identification.

**Examples:**
```javascript
// Button with name
page.get_by_role('button', { name: 'Sign In' })

// Heading with level
page.get_by_role('heading', { level: 2, name: 'Welcome' })

// Textbox with value
page.get_by_role('textbox', { name: 'Email', value: 'user@example.com' })

// Checkbox with state
page.get_by_role('checkbox', { name: 'Remember me', checked: true })
```

### 2. `get_by_label` (Score: 0.90)
Uses accessible names for form elements.

**Examples:**
```javascript
page.get_by_label('Email')
page.get_by_label('Password')
page.get_by_label('Remember me')
```

### 3. `get_by_placeholder` (Score: 0.85)
Uses placeholder text for text inputs.

**Examples:**
```javascript
page.get_by_placeholder('Enter your email')
page.get_by_placeholder('Enter your password')
```

### 4. `get_by_text` (Score: 0.80)
Uses the accessible name as text content.

**Examples:**
```javascript
page.get_by_text('Sign In')
page.get_by_text('Welcome to our application')
```

### 5. `test_id` (Score: 0.88)
Uses test IDs when available (common in modern applications).

**Examples:**
```javascript
page.get_by_test_id('login-button')
page.get_by_test_id('email-input')
```

### 6. `xpath` (Score: 0.60)
Accessibility-based XPath using ARIA attributes.

**Examples:**
```xpath
//*[@role="button"][contains(@aria-label, "Sign In")]
//*[@role="heading"][@aria-level="2"][contains(text(), "Welcome")]
//*[@role="textbox"][@aria-required="true"][contains(@aria-label, "Email")]
```

## Accessibility-Based XPath Generation

The system generates XPaths that use accessibility properties rather than DOM structure:

### XPath Patterns

1. **Role-based selection:**
   ```xpath
   //*[@role="button"]
   //*[@role="textbox"]
   //*[@role="heading"]
   ```

2. **Role with name:**
   ```xpath
   //*[@role="button"][contains(@aria-label, "Sign In") or contains(text(), "Sign In")]
   ```

3. **Role with level (for headings):**
   ```xpath
   //*[@role="heading"][@aria-level="2"]
   ```

4. **Role with state:**
   ```xpath
   //*[@role="checkbox"][@aria-checked="true"]
   //*[@role="textbox"][@aria-required="true"]
   //*[@role="button"][@aria-disabled="true"]
   ```

## Scoring System

Locators are scored based on:

### Base Scores
- `get_by_role`: 0.95 (highest - most semantic)
- `get_by_label`: 0.90
- `get_by_placeholder`: 0.85
- `test_id`: 0.88
- `get_by_text`: 0.80
- `xpath`: 0.60 (lowest - most fragile)

### Bonuses
- **Interactive roles**: +0.05 (button, link, textbox, etc.)
- **Good name length**: +0.05 (1-5 words)
- **Meaningful names**: +0.03 (not generic text)
- **Form values**: +0.02 (for form controls)
- **Required elements**: +0.02
- **Specific roles**: +0.02 (button, link, heading)

### Penalties
- **Disabled elements**: -0.10
- **Generic roles**: -0.15 (generic, text without name)
- **Verbose names**: -0.05 (>10 words)
- **Complex locators**: -0.05 (>200 characters)

## Advantages Over DOM-Based Locators

### 1. **Semantic Accuracy**
- Uses ARIA roles instead of HTML tags
- Leverages accessible names (what users actually see/hear)
- Understands element purpose, not just structure

### 2. **Resilience to Changes**
- Less dependent on HTML structure
- Focuses on semantic meaning
- Survives CSS and layout changes

### 3. **Accessibility Compliance**
- Ensures elements are properly labeled
- Uses the same information screen readers use
- Promotes accessible web development

### 4. **Better User Intent Matching**
- Matches how users think about elements
- Uses human-readable names
- Understands element functionality

## Example Usage

### Basic Usage
```bash
# Get locators for all accessible elements
curl "http://localhost:8002/accessibility-locators"

# Include ignored elements
curl "http://localhost:8002/accessibility-locators?include_ignored=true"

# Include hidden elements
curl "http://localhost:8002/accessibility-locators?include_hidden=true"
```

### Integration with Semantic Locator Service
```python
import httpx

async def get_semantic_locators():
    async with httpx.AsyncClient() as client:
        # Get accessibility locators
        response = await client.get("http://localhost:8002/accessibility-locators")
        result = response.json()
        
        if result['success']:
            elements = result['elements']
            
            # Use with semantic locator service
            semantic_request = {
                "dom": elements,  # Pass accessibility-based elements
                "user_step": "Click the Sign In button"
            }
            
            semantic_response = await client.post(
                "http://localhost:8006/resolve-two-stage",
                json=semantic_request
            )
            
            return semantic_response.json()
```

## Testing

Run the test script to see the functionality in action:

```bash
python test_accessibility_locators.py
```

This will:
1. Navigate to example.com
2. Generate locators from the accessibility tree
3. Show examples of each locator type
4. Analyze locator distribution
5. Demonstrate XPath generation

## Comparison with DOM-Based Approach

| Aspect | DOM-Based | Accessibility-Based |
|--------|-----------|-------------------|
| **Data Source** | HTML structure | ARIA tree |
| **Element Identification** | Tags + attributes | Roles + names |
| **Resilience** | Low (structure-dependent) | High (semantic) |
| **Accessibility** | Not considered | Built-in compliance |
| **User Intent** | Structure-focused | Meaning-focused |
| **Maintenance** | High (fragile) | Low (robust) |

## Best Practices

1. **Use `get_by_role` when possible** - It's the most semantic and resilient
2. **Prefer accessible names over text content** - They're more reliable
3. **Include state information** - Use checked, required, disabled properties
4. **Avoid XPath for critical elements** - Use semantic locators instead
5. **Test with screen readers** - Ensure accessibility compliance

## Future Enhancements

1. **Learning from user corrections** - Improve scoring based on success/failure
2. **Domain-specific optimization** - Adapt to different application types
3. **Multi-modal context** - Combine with visual and structural information
4. **Dynamic vocabulary** - Learn new element types and patterns
5. **Feedback integration** - Use user feedback to improve locator quality 