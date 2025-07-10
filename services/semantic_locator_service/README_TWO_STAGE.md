# Two-Stage Locator Resolution System

## Overview

The Two-Stage Locator Resolution system solves the classic "semantic vs. actionability" problem in UI automation. It combines semantic search with heuristic re-ranking to accurately identify the most actionable element for a given user command.

## The Problem

Traditional semantic search approaches often struggle with ambiguity. For example, when the query is "Click Sign In", both a `<h2>` heading and a `<div>` inside a button might contain the same "Sign In" text. The semantic model might even rank the heading higher because it's an exact text match, but the user clearly wants to click the button, not read the heading.

## The Solution: Two-Stage Approach

### Stage 1: Semantic Search (Candidate Generation)
- **Purpose**: Find semantically relevant candidates
- **Process**: 
  1. Embed the user command into a vector
  2. Use cosine similarity to find top-K most similar elements
  3. Return a manageable list of candidates (typically 5-10 elements)

### Stage 2: Heuristic Re-ranking (Actionability Scoring)
- **Purpose**: Re-rank candidates based on actionability and user intent
- **Process**:
  1. Detect action type from user command (click, input, select, verify)
  2. Apply heuristic rules to score each candidate
  3. Combine semantic and heuristic scores for final ranking

## Implementation

### Core Classes

#### `TwoStageLocatorResolver`
The main orchestrator class that implements the two-stage pipeline.

**Key Methods:**
- `resolve_locator(user_step, top_k=10)`: Main entry point
- `_stage1_semantic_search()`: Performs vector similarity search
- `_stage2_heuristic_rerank()`: Applies heuristic re-ranking
- `_detect_action_type()`: Identifies user intent
- `_calculate_heuristic_bonus()`: Scores element actionability

#### Action Keywords Configuration
```python
ACTION_KEYWORDS = {
    'click': {
        'keywords': ['click', 'press', 'tap', 'submit', 'button'],
        'priority_elements': ['button', 'a', 'input[type="submit"]'],
        'priority_roles': ['button', 'link', 'menuitem'],
        'bonus_score': 0.5
    },
    'input': {
        'keywords': ['enter', 'type', 'fill', 'input', 'write'],
        'priority_elements': ['input', 'textarea'],
        'priority_roles': ['textbox', 'searchbox'],
        'bonus_score': 0.5
    },
    # ... more action types
}
```

### Scoring Algorithm

**Final Score = Semantic Score + Heuristic Bonus**

#### Semantic Score
- Cosine similarity between user command and element signature
- Range: 0.0 to 1.0 (higher is better)

#### Heuristic Bonus
- **Element Type Bonus**: +0.5 for matching priority elements/roles
- **Context Bonus**: +0.1-0.2 for word overlap between command and signature
- **Explicit Mention Bonus**: +0.75 for explicit element type mentions (e.g., "button" in command)
- **Cap**: Maximum bonus is 1.0

## Usage

### API Endpoints

#### Original Single-Stage Approach
```http
POST /resolve
{
    "dom": [...],
    "user_step": "Click Sign In"
}
```

#### New Two-Stage Approach
```http
POST /resolve-two-stage
{
    "dom": [...],
    "user_step": "Click Sign In",
    "debug": true
}
```

### Response Format
```json
{
    "locator": "page.get_by_role('button', { name: 'Sign In' })",
    "signature": "div: Sign In, class: button-text",
    "score": 0.85,
    "semantic_score": 0.75,
    "heuristic_bonus": 0.10,
    "all_candidates": [
        {
            "signature": "div: Sign In, class: button-text",
            "final_score": 0.85,
            "semantic_score": 0.75,
            "heuristic_bonus": 0.10,
            "locators": [...]
        },
        // ... more candidates
    ]
}
```

## Example Scenarios

### Scenario 1: "Click Sign In"
**DOM Elements:**
1. `<h2>Sign In</h2>` (heading)
2. `<button><div>Sign In</div></button>` (button)

**Stage 1 Results:**
- Both elements have high semantic similarity
- Heading might score slightly higher due to exact text match

**Stage 2 Results:**
- Button gets +0.5 bonus for being clickable
- Button gets +0.75 bonus for explicit "button" mention
- **Final Winner**: Button element

### Scenario 2: "Enter email in the email field"
**DOM Elements:**
1. `<h3>Email</h3>` (heading)
2. `<input type="email" placeholder="Enter your email">` (input field)

**Stage 1 Results:**
- Both elements have high semantic similarity
- Heading might score higher due to "email" text match

**Stage 2 Results:**
- Input field gets +0.5 bonus for being input element
- Input field gets +0.6 bonus for "input" keyword in command
- **Final Winner**: Input field

## Testing

Run the test script to see the system in action:

```bash
cd services/semantic_locator_service
python test_two_stage.py
```

This will demonstrate how the system handles ambiguous scenarios and correctly identifies the most actionable elements.

## Benefits

1. **Accuracy**: Solves semantic vs. actionability conflicts
2. **Robustness**: Handles ambiguous scenarios gracefully
3. **Performance**: Efficient two-stage pipeline
4. **Transparency**: Debug output shows reasoning process
5. **Extensibility**: Easy to add new action types and rules

## Future Enhancements

1. **Machine Learning**: Train models to learn optimal scoring weights
2. **Context Awareness**: Consider page context and element relationships
3. **Multi-modal**: Incorporate visual information from screenshots
4. **User Feedback**: Learn from user corrections to improve ranking
5. **Dynamic Rules**: Adapt scoring based on application type

## Integration

The two-stage resolver is designed to be a drop-in replacement for the original single-stage approach. Both endpoints are available, allowing for gradual migration and comparison of results. 