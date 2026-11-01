# 4. Keyboard Access and Focus

<!-- TT 5.1.3, printed pp. 19-25. Converted from the PDF by convert.py; the PDF is the authority. -->

### Keyboard Access

#### Identify Content

1. Use the mouse or other pointing device to determine available functions provided by interactive elements (including drop-down menus, form fields, revealing/hiding content, tooltips, AND all interactive interface components).
2. Use the mouse to identify instances where interactive elements provide information that is essential to understanding or operating the page content.

**Note:**

- WCAG SC 2.1.1 requirement does not apply to functions that require input that depends on the path of the user’s movement and not just the endpoints. For this test process, the tester is not tasked with identifying and omitting these types of functions. The tester should include all functions that meet the Identify Content description. A Section 508 exception may be applied for certain functions; however, this is outside the scope the testing process.

If there is no such content, the result for the following test ID(s) is DOES NOT APPLY: 4.A to 4.H.

### Check 2.1.1-keyboard-access

| Test Name | Test ID | Test Condition |
| --- | --- | --- |
| 2.1.1-keyboard-access | 4.A | All functionality can be accessed and executed using only the keyboard. |

**Applicability:**

This Test Condition DOES NOT APPLY (DNA) if the page has no user activated functionality.

**How to Test:**

1. Identify the functionality and essential information provided by interactive elements.
    - a. Possible ways to identify functionality include: mouse, touch screen, voice commands, and documentation of functionality (e.g., of shortcut keys).
    - b. The “title attributes” feature in ANDI: focusable elements can help identify any essential information contained in title attributes.
2. Use the keyboard to operate identified functionality and/or access the essential information: access (e.g., tab to) the element and execute (e.g., press Enter with focus on the element).
    - a. For interactive elements with title attributes, place keyboard focus on the element. If the tooltip does not appear within two seconds, keyboard focus will not reveal the title information.
    - b. If an interactive element does not have keyboard access, determine if there is another keyboard accessible method available on the page which provides the same functionality, e.g., one of two print methods provided is keyboard accessible, etc. [See Conforming Alternate Version for further details.]
    - c. If an interactive element does not provide access to essential information via keyboard interaction, determine whether the information is available elsewhere on the page (e.g., as text).

**Note:**

- Not all browsers visually display the title attribute as a tooltip when an element has keyboard focus.
- Shortcut keys are typically documented on the page or in the Help documentation so that they are discoverable by a user.

**Evaluate Results:**

If BOTH of the following are TRUE, the content PASSES:

1. All functionality can be accessed and executed using the keyboard, AND
2. All essential information can be accessed via keyboard interaction OR the information is available elsewhere on the page.

**Note:**

- Any changes to functionality that occur automatically or as a result of interaction with the page should be included in this test.
- Information is considered essential or required when the information is necessary to execute an action or understand information and relationships.
- Title/tooltip information that is not essential does not require keyboard access.

### Check 2.1.1-no-keystroke-timing

| Test Name | Test ID | Test Condition |
| --- | --- | --- |
| 2.1.1-no-keystroke-timing | 4.B | Individual keystrokes do not require specific timings for activation of functionality. |

**Applicability:**

This Test Condition DOES NOT APPLY (DNA) if the page has no user activated functionality.

**How to Test:**

1. Continue from Test 4.A.
2. Determine whether there are any instances where the timing of the keystrokes is required to activate the element, e.g., the speed at which a password keystrokes are typed is part of the password authentication.
3. If there is a timing dependent functionality, determine if there is another keyboard accessible method available on the page, which does not require specific timing.

**Evaluate Results:**

If the following is TRUE, the content PASSES:

1. A keyboard method is provided for functionality to be activated without requiring users to perform specific timings for activation.

### Check 2.1.2-no-keyboard-trap

| Test Name | Test ID | Test Condition |
| --- | --- | --- |
| 2.1.2-no-keyboard-trap | 4.C | There is no keyboard trap. |

**Applicability:**

This Test Condition DOES NOT APPLY (DNA) if the page has no components that can receive keyboard focus.

**How to Test:**

1. Use standard navigation keys (e.g., TAB, SHIFT + TAB, arrow keys, CTRL + TAB, etc.) to navigate through all keyboard focusable elements on the page.
2. Determine whether there are any instances where keyboard navigation becomes trapped:
    - a. Keyboard users are unable to move away from an element, e.g., using a TAB or arrow key
    - b. Keyboard access is restricted to a small section of the page with no way to navigate out of the “loop” to the rest of the page. Note:
        - Keyboard focus should remain within a modal dialog box until it is closed (per Test ID 4.F Step 3). However, check for keyboard traps in the dialog.
        - If a section of a page requires input or interaction before allowing focus to progress to the rest of the page, this is not a failure.
3. If a keyboard trap is found:
    - a. Inspect any help (contextual help, or application help) and documentation for notification of available alternate keyboard commands (e.g., non-standard keyboard controls, access keys, hotkeys) to escape/avoid the keyboard trap.
    - b. Determine whether the alternate command(s) work.

**Evaluate Results:**

If ALL of the following are TRUE, the content PASSES:

1. Keyboard focus can be moved away from an element using either:
    - a. Standard navigation keys
    - b. Custom keystrokes (which are documented and available to users in the application).

AND

2. Keyboard focus can be moved away from each section of the page containing elements (and are not trapped in a “loop”, preventing access to other elements on the page) by using either:
    - a. Standard navigation keys
    - b. Custom keystrokes (which are documented and available to users in the application)

**Note:**

- In case of a keyboard trap, continue to test interactive elements after the trap by using the mouse to bypass the trap or refreshing the page and using the keyboard to navigate backwards through the page.

### Focus

#### Identify Content

Use the keyboard to navigate to keyboard-accessible interface components (including drop-down menus, form fields, revealing/hiding content, tooltips, AND all interactive interface components).

If there is no such content, the result for the following test ID(s) is DOES NOT APPLY: 4.A to 4.H.

### Check 2.4.7-focus-visible

| Test Name | Test ID | Test Condition |
| --- | --- | --- |
| 2.4.7-focus-visible | 4.D | A visible indication of focus is provided when focus is on the interface component. |

**Applicability:**

This Test Condition DOES NOT APPLY (DNA) if the page has no elements that can receive keyboard focus.

**How to Test:**

1. Continue from Test 4.C.
2. Determine whether there is a visible indication of focus on the element that has keyboard focus.
    - a. When the keyboard focus is on a frame, some browsers will display a visible focus and some may not. Where a visible focus is not available on a frame, do NOT consider this a failure of the web content.

**Evaluate Results:**

If the following is TRUE, then the content PASSES:

1. When each interface element receives focus, there is a visible indication of focus.

**Note:**

- To confirm keyboard focus is on a frame when there is not visible focus: use the TAB and SHIFT + TAB combination to deduce that the keyboard focus is on the frame. When on the frame, a tab forward should move focus to the first keyboard focusable element within the frame. From there, SHIFT + TAB once to move back to the frame and another SHIFT + TAB should move focus to a keyboard focusable element before the frame. Only the frame is permitted to not have a visible focus. Be certain it is the frame that does not have a visible focus and not another element.

### Check 3.2.1-on-focus

| Test Name | Test ID | Test Condition |
| --- | --- | --- |
| 3.2.1-on-focus | 4.E | When an interface component receives focus, it does not initiate an unexpected change of context. |

**Applicability:**

This Test Condition DOES NOT APPLY (DNA) if the page has no elements that can receive keyboard focus.

**How to Test:**

1. Continue from Test 4.D.
2. When the interface component receives focus, evaluate whether an unexpected change of context occurs, e.g., a new window is launched, or focus is moved to another interface component.

**Evaluate Results:**

If the following is TRUE, then the content PASSES:

1. An unexpected change of context is not initiated when an interface component receives focus.

### Check 2.4.3-focus-order-meaning

| Test Name | Test ID | Test Condition |
| --- | --- | --- |
| 2.4.3-focus-order-meaning | 4.F | The focus order preserves the meaning and operability of the web page. |

**Applicability:**

This Test Condition DOES NOT APPLY (DNA) if the page has no elements that can receive keyboard focus.

**How to Test:**

1. Use the tab key to move focus through the page.
2. Determine if the focus order impacts the page meaning (e.g., form fields for a mailing address are presented in the expected sequence).
    - a. This is most often noticeable when focus order does not follow the logical order of operation (normally top to bottom, left to right).
    - b. It may be necessary to use the keyboard to activate trigger controls that reveal hidden content with focusable elements (e.g., menus, dialogs, modal dialog boxes, expandable tree list) to check the focus order to, from, and within the revealed content.
    - c. It may be helpful to launch ANDI: focusable elements and select tab order.
    - d. Backward focus order does not have to mirror the forward focus order. However, it must preserve the meaning and operability of the page.
3. For modal dialog boxes, keyboard focus navigating both forward and backward should remain within the modal dialog box until it is closed.

**Evaluate Results:**

If ALL of the following are TRUE, then the content PASSES:

1. The focus order preserves the meaning of the page, AND
2. The focus order preserves the operability of the page.

**Note:**

- Focus order does not necessarily need to be top to bottom, left to right.
- When the focus order does not affect meaning or operability, this test Does Not Apply. Example: A row of icons linking to social media may not need to be navigated in a particular order.
- ANDI tab order markup may be slightly different from actual keyboard tab order in certain browsers. Always use the results from keyboard tab order.

**Applicable Standards**

```text
Section 508/WCAG Success Criteria                                                     Baseline Requirements
WCAG SC 2.1.1 Keyboard: All functionality of the content is operable through a 1. Keyboard Access
keyboard interface without requiring specific timings for individual keystrokes,
except where the underlying function requires input that depends on the path of the
user's movement and not just the endpoints.
WCAG SC 2.1.2 No Keyboard Trap: If keyboard focus can be moved to a component
of the [content] using a keyboard interface, then focus can be moved away from that
component using only a keyboard interface, and, if it requires more than unmodified
arrow or tab keys or other standard exit methods, the user is advised of the method
for moving focus away.
WCAG SC 2.4.7 Focus Visible: Any keyboard operable user interface has a mode of 2. Focus
operation where the keyboard focus indicator is visible.
WCAG SC 2.4.3 Focus Order: If a Web page can be navigated sequentially and the
navigation sequences affect meaning or operation, focusable components receive
focus in an order that preserves meaning and operability.
WCAG 3.2.1 - On Focus: When any component receives focus, it does not initiate a
change of context.
```
