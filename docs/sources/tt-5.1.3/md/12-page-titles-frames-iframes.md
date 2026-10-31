# 12. Page Titles, Frames, and iFrames

<!-- TT 5.1.3, printed pp. 53-56. Converted from the PDF by convert.py; the PDF is the authority. -->

### Page Titles

#### Identify Content

All web pages.

Test Conditions 12.A and 12.B always apply.

### Check 2.4.2-page-title-defined

| Test Name | Test ID | Test Condition |
| --- | --- | --- |
| 2.4.2-page-title-defined | 12.A | A <title> element is defined for the web page. |

**Applicability:**

This Test Condition always applies – you may NOT evaluate the condition as DOES NOT APPLY (DNA).

**How to Test:**

1. Launch ANDI: structures. Review the alerts in ANDI’s “Accessibility Alerts” section to determine whether ANDI displays any of the following Invalid HTML Alerts:
    - a. “Page has no <title>”
    - b. “Page <title> cannot be empty”

**Evaluate Results:**

If the following is TRUE, then the Test Condition is TRUE and the content PASSES:
1. A Page Title is defined for the web page.

### Check 2.4.2-page-title-purpose

| Test Name | Test ID | Test Condition |
| --- | --- | --- |
| 2.4.2-page-title-purpose | 12.B | The <title> element identifies the contents or purpose of the web page. |

**Applicability:**

This Test Condition always applies – you may NOT evaluate the condition as DOES NOT APPLY (DNA).

**How to Test:**

1. Launch ANDI: structures, then select “more details”, then "page title."
    - a. A modal dialog box will appear with the identified page title listed.
2. Evaluate the purpose and content of the web page.
3. Determine whether the Page Title is a meaningful representation or indication of page content.
    - a. If the web page is part of a set of web pages, determine whether the Page Title is sufficient to distinguish the web page from other pages.
    - b. For documents or web applications, the name of the document or web application would be sufficient to describe the purpose of the page.

**Evaluate Results:**

If ALL of the following are TRUE, then the Test Condition is TRUE and the content PASSES:

1. The Page Title accurately identifies the contents or purpose of the web page, AND
2. If the web page is part of a set of web pages, the Page Title accurately distinguishes the web page from other pages in the web site.

**Note:**

- A web application is an application that runs in a web browser (such as webmail) and may not have a URL that changes as content on the web page changes.

### Frames

#### Identify Content

Use ANDI to identify all Frames.
1. Launch ANDI. If a Frame is used, ANDI will provide a notification that frames have been detected.
    - a. If there are no Frames, ANDI will provide no notification.

If there is no such content, the result for the following test ID(s) is DOES NOT APPLY: 12.C.

### Check 4.1.2-frame-title

| Test Name | Test ID | Test Condition |
| --- | --- | --- |
| 4.1.2-frame-title | 12.C | Each <frame> has a title attribute that describes its content. |

**Applicability:**

This Test Condition DOES NOT APPLY (DNA) if no Frames are identified.

**How to Test:**

1. Launch ANDI. If a Frame is used, ANDI will provide a notification that Frames have been detected. Select “Cancel” to test an individual Frame.
2. ANDI will list each Frame, and, if available, the associated title attribute.
    - a. If there is no title attribute, ANDI will reveal an “alert”.
3. Select each link to access each frame. Review the Frame to understand its content. Navigate back to the page being tested and launch ANDI again.
4. In ANDI, review each frame’s corresponding title attribute for a meaningful description of content.

**Evaluate Results:**

If the following is TRUE, then the Test Condition is TRUE and the content PASSES:

1. All frames have a title attribute that describes its content.

**Note:**

- In HTML5 the <frame> element is marked as obsolete. While the <frame> element has been deprecated in HTML5, testers may still encounter web pages and/or web applications with code that, while outdated, can and should still be accessible.
- Frame content must be tested for conformance with all other applicable tests (12.A and 12.B do not apply to frame content).
    - To open each Frame to test: Launch ANDI and select “Cancel”. A list of Frames will show; select the link to test an individual frame.

### iFrames

#### Identify Content

Use ANDI to identify all iframes in the tab order.
1. Launch ANDI: iframes to navigate to and highlight iframes on the page. If there is not an option for the iframes module, there are no iframes on the web page.

2. Use the “Next Element” button to find all iframes that have the following listed in the Accessibility Component:
    - a tabindex value that is not negative (e.g., 0, 1) meaning the iframe is in the tab order

OR

    - no tabindex shown. Test only these <iframes>.

Note: A negative tabindex such as -1 means that the iframe is explicitly excluded from the tab order. Do not test iframes explicitly excluded from the tab order.

If there is no such content, the result for the following test ID(s) is DOES NOT APPLY: 12.D.

### Check 4.1.2-iframe-name

| Test Name | Test ID | Test Condition |
| --- | --- | --- |
| 4.1.2-iframe-name | 12.D | The combination of accessible name and description for each <iframe> describes its content. |

**Applicability:**

This Test Condition DOES NOT APPLY (DNA) if no iframes are identified or if the iframes are explicitly excluded from the tab order (i.e., the tabindex is a negative number).

**How to Test:**

1. Launch ANDI: iframes
2. Review the ANDI Output for each iframe that has a non-negative tabindex value or where the tabindex is not defined to determine whether the accessible name and description accurately describe the content of each <iframe>.

**Evaluate Results:**

If the following is TRUE, then the content PASSES:

1. The ANDI Output for each <iframe> in the tab order sufficiently describes its content.

**Note:**

- All iframe content must be tested for conformance with all other applicable tests (12.A and 12.B do not apply to iframe content). To open each iframe to test: Within ANDI: iframe, select the button to “test in new tab.”
- If ANDI fails to run in an iframe, see Appendix D for possible workarounds.

**Applicable Standards**

```text
Section 508/WCAG Success Criteria                                                      Baseline Requirements
WCAG SC 2.4.2 Page Titled: Web pages have titles that describe topic or purpose.       11. Page Titles
WCAG SC 4.1.2 Name, Role, Value: For all user interface components (including but      19. Frames and iFrames
not limited to: form elements, links and components generated by scripts), the
name and role can be programmatically determined; states, properties, and values
that can be set by the user can be programmatically set; and notification of changes
to these items is available to user agents, including assistive technologies.
```
