# 18. Resize Text

<!-- TT 5.1.3, printed pp. 74-75. Converted from the PDF by convert.py; the PDF is the authority. -->

### Textual Content

#### Identify Content

All text on a page.

EXCLUDE captions for synchronized media and images of text.

If there is no such content, the result for the following test ID(s) is DOES NOT APPLY: 18.A.

### Check 1.4.4-resize-text

| Test Name | Test ID | Test Condition |
| --- | --- | --- |
| 1.4.4-resize-text | 18.A | There is a mechanism to resize, scale, or zoom in on the text to at least 200% of its original size without loss of content or functionality. |

**Applicability**

This Test Condition DOES NOT APPLY (DNA) if there is no text on the page.

**How to Test:**

1. Use built-in browser zoom functions to resize the text to at least 200%.

2. If any of the content did not zoom using the built-in browser functions, determine whether there is a non-AT mechanism to resize page content to 200% of its original size, e.g., Operating System, platform, or other mechanism provided directly by the web page/application.

**Evaluate Results:**

If ALL of the following are TRUE, then the content PASSES:

1. There is a non-AT-reliant mechanism that allows the user to resize text to at least 200% of its original size, AND
2. Text is not clipped, truncated or obscured, AND
3. All functionality is available, AND
4. All content is available.

**Applicable Standards**

```text
Section 508/WCAG Success Criteria                                                      Baseline Requirements
WCAG SC 1.4.4 Resize Text: Except for captions and images of text, text can be         22. Resize Text
resized without assistive technology up to 200 percent without loss of content or
functionality.
```
