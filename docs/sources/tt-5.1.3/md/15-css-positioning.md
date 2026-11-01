# 15. CSS Positioning

<!-- TT 5.1.3, printed pp. 64-65. Converted from the PDF by convert.py; the PDF is the authority. -->

### CSS Positioning

#### Identify Content

Use ANDI to identify all content positioned with CSS and inline styles.

1. Launch ANDI, then select the Advanced Settings button; then select “linearize page” to remove CSS positioning from elements on the page.
2. If content is positioned with CSS, the information will be displayed with blue highlighting around the elements and those elements will be placed in the page in the same order in which they appear in the page code. If there is no such content, the result for the following test ID(s) is DOES NOT APPLY: 15.A.

### Check 1.3.2-content-order-meaning-css-position

| Test Name | Test ID | Test Condition |
| --- | --- | --- |
| 1.3.2-content-order-meaning-css-position | 15.A | The reading order of the content (in context) is correct and the meaning of the content (in context) is preserved without CSS positioning. |

**Applicability:**

This Test Condition DOES NOT APPLY (DNA) if there is no content positioned using CSS.

**How to Test:**

1. Review all highlighted, linearized content.

2. Determine whether the reading order of content is still understandable after linearization. If necessary, toggle the linearization button to view the original position of the content. If content becomes illegible due to overlapping, etc., this is not a failure of this test, which is to verify if the programmatic reading order is understandable.

**Evaluate Results:**

If the following is TRUE, then the Test Condition is TRUE and the content PASSES:

1. The sequence and meaning of the content (in context) is understandable without CSS positioning.

**Note:**

- ANDI: structures, and the “reading order” link can also be used to reveal the reading order prior to linearizing the content, but it will not identify which content has been positioned with CSS.

**Applicable Standards**

```text
Section 508/WCAG Success Criteria                                           Baseline Requirements
WCAG SC 1.3.2 Meaningful Sequence: When the sequence in which               18. CSS Content and
content is presented affects its meaning, a correct reading sequence can be Positioning
programmatically determined.
```
