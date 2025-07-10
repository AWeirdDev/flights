# Flight Parser Analysis Results

## Key Discovery

The visual validation tool revealed that the discrepancy between JS (108 flights) and HTML (218 flights) parsers is due to **duplicate display of flights** in the HTML structure.

## HTML Structure

The HTML contains 4 containers with pattern `[3, 106, 3, 106]`:
- **Container 0**: 3 "best" flights for outbound
- **Container 1**: 106 "other" flights for outbound  
- **Container 2**: 3 "best" flights for return (DUPLICATES of container 0)
- **Container 3**: 106 "other" flights for return (DUPLICATES of container 1)

Total visible items: 3 + 106 + 3 + 106 = 218 (but only 109 unique)

## Visual Evidence

The visual validator confirmed:
- 218 total flight items visible on page
- 648 visible prices (3 price classes × 218 items)
- HTML parser correctly finds all 218 items
- JS parser correctly identifies 108 unique flights

## Current Problems

1. **HTML parser counts duplicates**: Reports 218 flights instead of 109 unique
2. **Enrichment extraction duplicates**: Extracts 218 enrichments for 109 flights
3. **Hybrid matching fails**: Tries to match 108 JS flights to 218 enrichments
4. **arrival_time_ahead coverage drops**: Only 53/108 (49%) instead of 116/218 (53%)

## Root Cause

The HTML shows round-trip search results with both outbound and return flights, but displays them identically. The JS parser correctly consolidates these into unique flights, while the HTML parser treats each display instance as a separate flight.

## Solution Approach

1. **Fix HTML parser**: Detect and skip duplicate containers
2. **Fix enrichment extraction**: Only extract from unique containers
3. **Improve matching**: Account for the actual structure
4. **Preserve all enrichment data**: Ensure arrival_time_ahead is properly extracted

## Visual Validator Benefits

The Playwright-based visual validator was crucial in:
- Confirming the actual page structure
- Validating parser accuracy
- Identifying the duplicate pattern
- Providing concrete evidence for the fix