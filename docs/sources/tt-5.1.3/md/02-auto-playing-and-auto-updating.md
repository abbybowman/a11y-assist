# 2. Auto-Playing and Auto-Updating Content

<!-- TT 5.1.3, printed pp. 13-18. Converted from the PDF by convert.py; the PDF is the authority. -->

### Auto-Playing Audio

#### Identify Content

Before loading the page, make sure the browser is not set to block auto-playing content. Identify audio content that automatically plays (without user activation) for more than 3 seconds.

- Content of this type includes alerts, sounds, and music.

If there is no such content, the result for the following test ID(s) is DOES NOT APPLY: 2.A.

### Check 1.4.2-audio-control

| Test Name | Test ID | Test Condition |
| --- | --- | --- |
| 1.4.2-audio-control | 2.A | The user can pause, stop, or control the volume of audio content that plays automatically. |

**Applicability:**

This Test Condition DOES NOT APPLY (DNA) if there is no audio content that plays automatically for more than 3 seconds.

**How to Test:**

1. Determine if there is a mechanism within the first three elements encountered for the user to pause or stop the audio or to control the volume of only the auto-playing audio.
    - a. The browser should already have been configured to allow auto-play. (See the Test Tool Installation and Configuration Guide for instructions.)
2. Activate the mechanism.
3. Following this test process, test the mechanism for all applicable Test Conditions.

**Evaluate Results:**

If ALL of the following are TRUE, then the content PASSES:

1. There is a mechanism that can pause or stop the audio or control the volume of only the auto-playing audio, AND
2. The mechanism is within the first three elements encountered by the user, AND
3. The mechanism passes all applicable Test Conditions in this test process.

**Notes:**

- The Trusted Tester process requires the mechanism within three elements for clear measurability. This requirement is not specified in WCAG. To meet the non-interference requirement, the mechanism can be a focusable element or text instructions at the top of the page prior to repetitive content.
- A browser’s ability to disable auto-playing media and/or mute a specific tab are acceptable mechanisms to stop or control the volume of auto-playing audio content. However, not all browsers have the capability to disable auto-playing media or mute specific windows or tabs.

Moving, Blinking, and Scrolling Content Identify Content: Before loading the page, make sure the browser is not set to block auto-playing content. Identify visual content that:

- Starts moving, blinking, or scrolling without user activation (including videos, synchronized media, and scrolling text), AND
- Moves, blinks, or scrolls continuously for more than 5 seconds, AND
- Is not the only content on the page.

EXCLUDE content where the movement, blinking, or scrolling of the content is essential.

If there is no such content, the result for the following test ID(s) is DOES NOT APPLY: 2.B.

**Notes:**

- When displayed content moves, blinks or scrolls, but the content itself does not change, only Test 2.B, 2.2.2-blinking-moving-scrolling applies.
- When there is auto-updating content where the content itself changes (e.g., in a carousel, stock tickers, updating sports scores), Test 2.C, 2.2.2-auto-updating applies.
- If the content moves, blinks, or scrolls AND auto-updates, both test conditions (2.B and 2.C) apply.

### Check 2.2.2-blinking-moving-scrolling

| Test Name | Test ID | Test Condition |
| --- | --- | --- |
| 2.2.2-blinking-moving-scrolling | 2.B | The user can pause, stop, or hide moving, blinking, or scrolling content. |

**Applicability:**

This Test Condition DOES NOT APPLY (DNA) if there is no moving, blinking, or scrolling content that plays automatically for more than 5 seconds OR if the moving, blinking, or scrolling content is the ONLY content on the web page.

**How to Test:**

1. Determine if there is an evident mechanism for the user to pause, stop, or hide the content within the first three elements that the user would encounter OR within three elements before/after the moving/blinking/scrolling content.
2. Activate the mechanism.
3. Following this test process, test the mechanism for all applicable Test Conditions.

**Evaluate Results:**

If ALL of the following are TRUE, then the content PASSES:

1. There is an evident mechanism that can pause, stop, or hide the content, AND
2. The mechanism is either within:
    - the first three elements encountered by the user, OR
    - three elements before/after the moving/blinking/scrolling content,

AND

3. The mechanism PASSES all applicable Test Conditions in this test process.

### Auto-Updating Information

#### Identify Content

Identify content that:

- Automatically updates (the content changes without user activation) AND
- Is not the only content on the page

Content of this type includes timers, stock tickers, news carousels, and counters.

**Note:**

- WCAG SC 2.2.2 does not apply to auto-updating of information where the auto-updating is essential. However, the auto-updating of a stock ticker that conveys real-time information would not be considered essential (per WCAG) so it would be included in this test. It is likely that most instances of auto-update would not be essential. To avoid incorrect omission(s) of content from this test, the tester is not tasked with determining whether auto-updating is essential and should include all content that meets the Identify Content description. A Section 508 exception may be applied for essential auto-updating content; however, this is outside the scope of the testing process. An exception for SC 2.2.2 should be considered carefully as Conformance Requirement 5: Non-Interference requires its conformance.
- When displayed content moves, blinks or scrolls, but the content itself does not change, only Test 2.B, 2.2.2-blinking-moving-scrolling applies.
- When there is auto-updating content where the content itself changes (e.g., in a carousel, stock tickers, updating sports scores), Test 2.C, 2.2.2-auto-updating applies.
- If the content moves, blinks, or scrolls AND auto-updates, both test conditions (2.B and 2.C) apply.

If there is no such content, the result for the following test ID(s) is DOES NOT APPLY: 2.C and 2.D.

### Check 2.2.2-auto-updating

| Test Name | Test ID | Test Condition |
| --- | --- | --- |
| 2.2.2-auto-updating | 2.C | The user can pause, stop, hide, or control the frequency of automatically updating content. |

**Applicability:**

This Test Condition DOES NOT APPLY (DNA) if there is no auto-updating content or the auto-updating content is the only content on the page.

**How to Test:**

1. Determine if there is an evident mechanism for the user to pause, stop, or hide the content or to control the frequency of the update within the first three elements that the user would encounter OR within three elements before/after the auto-updating content.
2. Activate the mechanism.
3. Following this test process, test the mechanism for all applicable Test Conditions.

**Evaluate Results:**

If ALL of the following are TRUE, then the content PASSES:

1. There is an evident mechanism that can pause, stop, or hide the content or control the frequency of the update, AND
2. The mechanism is either within:
    - the first three elements encountered by the user, OR
    - three elements before/after the auto-updating content,

AND

3. The mechanism passes all applicable Test Conditions in this test process.

### Notification of Automatic Content Changes

#### Identify Content

Identify content that changes automatically on the page as part of auto-update.

If there is no such content, the result for the following test ID(s) is DOES NOT APPLY: 2.D.

### Check 4.1.2-change-notify-auto

| Test Name | Test ID | Test Condition |
| --- | --- | --- |
| 4.1.2-change-notify-auto | 2.D | The page provides notification of each automatic update/change in content. |

**Applicability:**

This Test Condition DOES NOT APPLY (DNA) if the page content does not update or change automatically.

**How to Test:**

1. Identify how the user is notified of the change in content.
    - a. Identify any dialogs that alert the user to changes in content.
        - i. Determine whether the dialogs provide sufficient programmatic notification of content changes.
    - b. Identify content changes that result in focus moving to the content that has changed.
        - i. Determine whether moving the focus to the content that has changed is sufficient to notify the user of the change event (e.g., by describing the change directly in the content to which the focus moved).
    - c. Identify content changes occurring in an ARIA Live Region:
        - i. Launch ANDI: structures
        - ii. Click the “live regions” link, then use the mouse to hover over any identified live region (alternatively, use ANDI’s previous/next element buttons to navigate to identified Live Regions).
        - iii. Determine whether the changing content is contained within the Live Region.

**Evaluate Results:**

If any of the following is TRUE, the content PASSES:

1. The page notifies the user about a change via a keyboard-accessible dialog, OR

2. The page moves focus to the content that has changed, AND the content that has changed provides sufficient description about the change, OR
3. The content that has changed is contained in an ARIA Live Region.

**Note:**

- This is a test for notification of automatic changes to content. The testing of the content before and after the change are to be performed in other tests. Testing of changes due to user interaction are also tested elsewhere. For example, form elements that change in response to user selections are to be tested per Test ID 5.B.

**Applicable Standards**

```text
Section 508/WCAG Success Criteria                                                    Baseline Requirements
WCAG SC 2.2.2 Pause, Stop, Hide: For moving, blinking, scrolling, or auto-updating 21. Timed Events
information, all of the following are true:
• Moving, blinking, scrolling: For any moving, blinking or scrolling information
     that (1) starts automatically, (2) lasts more than five seconds, and (3) is
     presented in parallel with other content, there is a mechanism for the user to
     pause, stop, or hide it unless the movement, blinking, or scrolling is part of an
     activity where it is essential.
• Auto-updating: For any auto-updating information that (1) starts
     automatically and (2) is presented in parallel with other content, there is a
     mechanism for the user to pause, stop, or hide it or to control the frequency
     of the update unless the auto-updating is part of an activity where it is
     essential.
• Note 2: Since any content that does not meet this success criterion can
     interfere with a user's ability to use the whole page [or software application],
     all content [in the software or] on the Web page (whether it is used to meet
     other success criteria or not) must meet this success criterion. See
     Conformance Requirement 5: Non-Interference.
WCAG SC 1.4.2 Audio Control: If any audio on a Web page plays automatically for
more than 3 seconds, either a mechanism is available to pause or stop the audio,
or a mechanism is available to control audio volume independently from the
overall system volume level.
•   Note: Since any content that does not meet this success criterion can
    interfere with a user's ability to use the whole page, all content on the Web
    page (whether it is used to meet other success criteria or not) must meet this
    success criterion. See Conformance Requirement 5: Non-Interference. Until
    such time that this test process includes a test for flashing content, no
    definitive statement can be made regarding Conformance Requirement 5 if
    any flashing content is present.
WCAG SC 4.1.2 Name, Role, Value: For all user interface components (including         5. Changing Content
but not limited to: form elements, links and components generated by scripts),
the name and role can be programmatically determined; states, properties, and
values that can be set by the user can be programmatically set; and notification of
changes to these items is available to user agents, including assistive technologies.
```
