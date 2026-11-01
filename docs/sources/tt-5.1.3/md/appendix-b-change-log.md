# Appendix B: Document Change Log

<!-- TT 5.1.3, printed pp. 82-88. Converted from the PDF by convert.py; the PDF is the authority. -->

**Note:** Minor punctuation, formatting and spelling changes not included.

Version 5.1.3, April 2024
- Testing Tools: added content regarding use of alternate tools; updated OS and browser information
- 2: Auto-playing Audio - Identify Content: updated to require that browser is not set to block autoplay
- 2.B: Evaluate Results: clarified that mechanism must be “evident”
- 4.C: How to Test: Added 2.b to clarify allowed loops
- 5.B: Note: Clarified that label can also be graphical
- 5.C: Changed “button” to “form element”
- 5.E has been removed
- 5.H Note: Added explanation of “user-controlled data”
- 5.H Note: Added clarification that this does not apply to one-page forms
- 6.B has been removed
- 7: Images: Rewritten to start with detection of empty/non-empty accessible name
- 7.E: Added CAPTCHA to exclusion list
- 10.C How to Test: added 2.a regarding aria heading levels taking precedence, removed check for heading level conflict
- 10.D Identify Content: Clarification that lists should be identified visually, not by using ANDI; inclusion of items with visual bullets
- 13: Identify Content: added tip about using grayscale to identify use of color to convey information
- 13.C How to Test, Evaluate Results: added notes about large-scale text

Version 5.1.2, December 2022
- Updated reference tables

Version 5.1.1, August 2022 Version 5.1.1 makes some clarifications to the test process and supporting content from Version 5.1. There are a few significant changes to the test process:

- Added Appendix D for possible ANDI workarounds.
- 1.A to 1.C: Conforming alternate versions should be identified as such. Failure of a test in this section results in FAIL rather than DNA so that testing continues. Test for “one path” to conforming version removed as this may be impossible to verify.
- 1.C removes reference to access from non-conforming version.
- 5.A and 5.B: Clarification that these tests are for visual labels.
- 6.A: Sentences and list items are acceptable link context.
- 7.A: Meaningful images, including images that suggest mood or tone, should be identified even if they are described in nearby text. This allows AT users to be aware of their presence and location. [OBE per 5.1.3]
- 10.D: Exclude menus and navigational framework.
- 13.A: Clarification to check if color is only visual method used.
- 13.B: Color added as a type of sensory information and therefore cannot be used in combination with another type of sensory information to pass this test.
- 15.A: Not testing for overlapping or other illegibility issues.

```text
Location in 5.1        Change
Testing Tools          Added reference to App. D for ANDI workarounds
```

```text
Conforming Alternate   General
Version and Non-       • Introduction revised; some headings renamed
Interference           Changes to testing process
                       • Failures of 1.A through 1.C now marked as FAIL instead of DNA to allow
                            for continued testing of version identified as the alternate version.
                       • “Alternate” version changed to “identified” version
                       • 1.C removes reference to access from non-conforming version
                       • Removed test 1.D. Simplified the mechanism test to no longer check for
                            path taken (whether from conforming or non-conforming version, etc.)
                       • Conforming alternate versions must be identified, e.g., through a label
                            on the page, as a link, in documentation, user preferences, controls to
                            modify text appearance, etc.
4.C                    How to Test, Step 1: Changed “Tab through…” to “Use standard navigation
                       keys…”
5.A                    Clarified that this test addresses presence of visual labels, and that accuracy
                       of visual labels is not evaluated in this test
5.B                    General
                            • Clarified that this test is for visual labels only
                       Evaluate Results
                            • Added “OR” after condition #3
5.C                    5.C now references SC 1.1.1 instead of 1.3.1
5.E                    Removed Note item about testing revealed content per 4.G
5                      Applicable standards: added SC 1.1.1 to replace SC 1.3.1
6.A                    How to Test, Step 2: added “sentence” and clarified “list item” as acceptable
                       link context
7                      This test has been updated so that most images that convey information
                       should be considered meaningful. This allows AT users to be aware of their
                       presence and location.
                       Identify Content
                            • First bullet: Added “All”, removed “important” before “meaningful
                                 images” – now “All images which convey information should be
                                 considered meaningful images”
                            • Last bullet added: “Images are not pure decoration if they serve to
                                 illustrate text content, suggest mood or tone, or create specific
                                 sensory experiences, such as a section dividers or bullet icons that
                                 use imagery or designs that convey specific moods or tones. If they
                                 convey any information, AT users should receive the same benefit of
                                 that information.” [OBE per 5.1.3]
                            • Added to Notes:
                                      o “WCAG defines “pure decoration” as “serving only an
                                          aesthetic purpose, providing no information, and having no
                                          functionality.”
                                      o WCAG defines “specific sensory experiences” as “a sensory
                                          experience that is not purely decorative and does not
                                          primarily convey important information or perform a
                                          function.”
Location in 5.1        Change
7.A                    Note: changed “These cannot be set” to “These should not be set”
10.D                   Identify Content
                            • Replaced note to clarify that navigation framework elements such as
                                 menus should be excluded: “Exclude menus or other elements that
                                 are part of the page’s navigational framework from this test.
                                 Developers might use list elements to create grouped navigational
                                 items, such as menus, submenus, lists of navigation links,
                                 breadcrumbs, etc. while styling them to remove bullets or
                                 numbering and orienting the lists horizontally instead of vertically. If
                                 these navigational elements are part of the page’s navigational
                                 framework, separate from the main content, they should not be
                                 considered visually apparent lists for this test and should be
                                 excluded. However, any lists which are part of the main content
                                 should be included.”
                       How to Test
                            • Step 3: Added “Exclude menus and navigational framework
                                 elements from this test, unless they are part of the main content.”
12.D                   Note: added note “If ANDI fails to run in an iframe, see Appendix D for
                       possible workarounds.”
13.A                   How to Test: Added “visual” to “Determine whether color is the only visual
                       method used to convey information”
13.B                   Identify Content, Test Condition, How to Test, Evaluate Results
                            • Added color as a type of sensory information
                       Removed note “The use of color can be used in combination with … to meet
                       this requirement”, etc.
14.A                   How to Test
                            • Step 1.a: added “ANDI will identify any non-hidden tables coded
                                 using <table>, role=”table”, or role=”grid”.”
15.A                   How to Test
                            • Step 2: added “If content becomes illegible due to overlapping, etc.,
                                 this is not a failure of this test, which is to verify if the programmatic
                                 reading order is understandable.”
17.C                   Identify Content: “If there is no such content, the result for the following test
                       ID(s) is DOES NOT APPLY: 17.D to 17.G” instead of “to 17.F”
17.E                   Identify Content: “If there is no such content, the result for the following test
                       ID(s) is DOES NOT APPLY: 17.F” instead of 17.E
17.F                   Test Name is now “503.4.1-caption-control-level”
17.G                        • Identify Content: “If there is no such content, the result for the
                                 following test ID(s) is DOES NOT APPLY: 17.G” instead of 17.F
                            • Test name is now “503.4.2-description-control-level”
```

Version 5.1, January 2021 This section is included as a reference for testers who were using Version 5.0. Version 5.1 introduced some significant changes from Version 5.0:

- Buttons testing moved from 6: Links/Buttons to Forms. Topic 6 now only tests links.
- 5.C checks for other programmatic associations.
- 5.E test includes button names.
- 6.A does not apply to anchors or hidden links.
- Images not automatically required to be decorative due to nearby text description.
- 10.B compares ANDI output and visual heading.
- 12.D provides more information on handling negative tabindex.
- 13.B allows use of “above” and “below” to reference sequence.
- 15.A test for ::before and ::after removed.
- Reorganization and clarification of audio description and caption control tests.

```text
Location in 5.0         Change
various                 Update Baseline Test Numbering:
                             • The name of 2. Focus Visible changed to 2. Focus.
                             • The new 2. Focus now also includes what was formerly in 3. Focus
                                 Order.
                             • The numbering for 25. Non-Interference changed to 3. Non-
                                 Interference.
Page 5                  Added to Conformance Reporting Requirements: If a tester cannot complete
                        a test, a note should be added to the test report indicating “This test could
                        not be performed”, with a detailed explanation of the issue.
Page 12                 1.E, non-interference added note to clarify Flashing result of Not Tested
                        does not pass the evaluation result requirements.
Page 15                 2.A, 1.4.2-audio-control
                             • added bullet to “Notes”: The Trusted Tester process requires the
                                 mechanism within three elements for clear measurability. This
                                 requirement is not specified in WCAG. To meet the non-interference
                                 requirement, the mechanism can be a focusable element or text
                                 instructions at the top of the page prior to repetitive content.
Page 16                 2.B, 2.2.2-blinking-moving-scrolling
                             • Added “Note” to the Identify Content section to clarify when 2.B,
                                 2.C, or both apply
                             • Moved text (including scrolling text, videos, and synchronized
                                 media) to beneath first bullet and changed order of items in the list
                                 for clarity; “scrolling text’ is now the last item in the list
Page 17                 2.C, 2.2.2-auto-updating
                             • Added “Note” to the Identify Content section to clarify when 2.B,
                                 2.C, or both apply
                             • Changed “moving/blinking/scrolling” to “auto-updating” to now read
                                 “three elements before/after the auto-updating content” in Evaluate
                                 Results section.
Page 21                 4.A, 2.1.1-keyboard-access How to Test instructions broadened to include
                        additional methods of identifying functionality.
Page 22                 4.A, 2.1.1-keyboard-access Note added to identify common methods of
                        documenting shortcut keys.
Location in 5.0        Change
Page 25                4.F, 2.4.3-focus-order-meaning
                            • Added directions to incorporate revealed content into the test steps
                                for focus-order-meaning. (This eliminates a separate test result for
                                4.G.)
                                “It may be necessary to use the keyboard to activate trigger controls
                                that reveal hidden content with focusable elements (e.g., menus,
                                dialogs, modal dialog boxes, expandable tree list) to check the focus
                                order to, from, and within the revealed content.”
                            • Clarified that focus must also remain in modal dialog boxes when
                                navigating backwards.
                            • Added bulleted content to the “Notes”:
                                     o Focus order does not necessarily need to be top to bottom,
                                         left to right.
                                     o When the focus order does not affect meaning or
                                         operability, this test Does Not Apply. Example: A row of
                                         icons linking to social media may not need to be navigated in
                                         a particular order.
Page 25                4.G, 2.4.3-focus-order-reveal as a separate test condition and ID was
                       removed for redundancy. A test step was added to 4.F
Page 26                4.H, 2.4.3-focus-order-return as a separate test condition and ID was
                       removed for redundancy. This condition is already covered in 4.F steps to
                       check backward focus for meaning and operability.
Page 27                Topic 5: In the Identified Content section, added “focusable element” to
                       clarify the ANDI module used to identify form elements.
```

Buttons testing was uncoupled from Topic 6 (Links/Buttons) and included as part of Forms testing.
- “Identifying Form Components” added “buttons” as an example of a form element to be tested in this topic.
- Terminology changed from “form field” to “form elements” or “form components/controls”.

```text
Page 28                 Test 5.B, 2.4.6-label-descriptive added Evaluation result: 2. Each button label
                        is sufficiently clear and descriptive, so users know its function.
                        Modified test step #4 to 5.C, 1.3.1-programmatic-label to clarify other
                        programmatic associations are reviewed “If the ANDI Output does not
                        adequately define the form element,” and added sub-step a. This language
                        was previous part of the test language in Topic 6 for buttons.
                           a. In cases where the purpose of the button is intentionally vague or
                               ambiguous (e.g., the content to be revealed after selecting a link to
                               “Door 1,” “Door 2,” or “Door 3” is intended to be a surprise), it may
                               be sufficient for the combination of button text, accessible name,
                               accessible description, and/or button context to refer to the button
                               purpose vaguely or ambiguously.
                        Evaluation result # 4 was added to 5.C, 1.3.1-programmatic-label. “The
                        combination of the programmatically determined button context and the
                        ANDI Output provide adequate description of each buttons’ purpose.”
Location in 5.0        Change
Page 29                Test 5.E, 4.1.2-change-notify-form now specifically includes “button names”
                       as a possible form element to be tested for interactions that trigger changes.
Page 31                Test 5.F, 3.3.1-error-identification clarifies the test does not apply if the
                       “form element” (rather than the page) does not have automatic error
                       detection.
Page 34 & 35           Topic 6 tests links alone. Buttons are now tested as part of Forms (Topic 5).
                       The test condition for 6.A, 2.4.4-link-purpose and 6.B, 4.1.2-change-notify-
                       links no longer include references to buttons.
                        Changes to “Notes” for 6.A, 2.4.4-link-purpose
                             • Added: This test does not apply to links that function as an anchor or
                                 target and are not perceivable or selectable by users.
                             • Removed: This test also covers the requirement for WCAG SC 4.1.2
                                 Name, Role, Value.
Page 36                 A change to our understanding of Decorative Images removes the ability to
                        label an image “decorative” when text provides the same information.
                             • 7.A, 1.1.1-meaningful-image-name no longer states: “If the ANDI
                                 Output points to page content for the image’s description,
                                 determine whether the description is provided.”
                             • Instead, the Test Step 1.a instructs: “The ANDI Output must provide
                                 an equivalent description of the image. This description can be
                                 provided by a brief description of the image in the ANDI Output and
                                 instructions about where to obtain the full description.”
Page 42                 The order of test steps was modified for 9.A, 2.4.1-bypass-function to first
                        check for keyboard-accessible methods to bypass repetitive content before
                        launching ANDI: focusable elements.
Page 47                 10.B, 1.3.1-heading-determinable added in How to Test, step 3 “Review the
                        ANDI Output for each heading to determine if it matches the visual heading.
                        If they do not match, then the heading is not properly defined
                        programmatically.”
Page 55                 Instructions for How to Test, step 3 of 12.C, 4.1.2-frame-title changed to
                        “Navigate back to the page being tested and launch ANDI again” (from “Use
                        the browser’s Back button to return to the page being tested and launch
                        ANDI again”). Change was made due to different navigation behaviors of
                        various browsers.
Page 56                 Changes to 12.D, 4.1.2-iframe-name to clarify how to address iframes with a
                        negative tabindex.
                             • Created a note in the Identify Content which moved some content
                                 and added further explanation regarding excluding iframes when
                                 they have a negative tabindex.
                             • Clarified test applicability to account for browser inconsistency’s in
                                 handling the tab order of iframes. New wording states: “This Test
                                 Condition DOES NOT APPLY (DNA) if no iframes are identified or if
                                 the iframes are explicitly excluded from the tab order.”
                             • Added text “or where the tabindex is not defined” to test step 2 to
                                 now read, “Review the ANDI Output for each iframe that has a non-
                                 negative tabindex value or where the tabindex is not defined to
                                 determine whether the accessible name and description accurately
                                 describe the content of each <iframe>.”
Location in 5.0        Change
Page 59                Addition to 13.B, 1.3.3-sensory-info
                       Note: The use of “above” or “below” is allowable when it references the
                       sequential order of content.
Page 66                    1. Removed CSS Content subsection which had Test ID 15.A, 1.3.1-
                                meaningful-content-css-before-after --“For the meaningful content
                                provided via CSS pseudo-elements ::before and ::after, equivalent
                                information is available in another way.”
                                Newer Assistive Technology accounts for content using CSS pseudo-
                                elements ::before and ::after. The ANDI computation has already
                                been updated
                           2. Removed WCAG SC 1.3.1 Info and Relationships from applicable
                                Standards for this section.
                           3. Renumbered 15.B. It is now:
                                15.A, 1.3.2-content-order-meaning-css-position
Page 73                Removed audio-description control mechanism from Test ID 17.D.
                           • The Test Name changed to 503.4-caption-controls (from 503.4-
                                caption-description-controls)
                           • Text “and audio descriptions” was removed from the Test Condition,
                                Test Steps, and Evaluate Results.
                           • The Test Condition is now: The media player provides user controls
                                for closed captions.
                       Note: This change was made to provide better clarity in tests for the menu
                       level of the mechanism
Page 74                Added a separate test for audio-description control mechanism to create
                       new Test ID 17.E, 503.4-audio-controls.
                       Note: This change was made to provide better clarity in tests for the menu
                       level of the mechanism.
Page 74                Renumbered Test ID 17.E to 17.F, 503.4.1-caption-control.
                           • Added “and caption controls” to Identify Content to now read,
                                “Identify any media player with volume adjustment and caption
                                controls.”
                           • Added “no caption control” to Applicability: This Test Condition
                                DOES NOT APPLY (DNA) if there is no media player, no caption
                                control, or the media player does not have a volume adjustment
                                control.
Page 75                Renumbered Test ID 17.F to 17.G, 503.4.2-description-control
                           • Added “and audio description controls” to Identify Content: Identify
                                any media player with program selection and audio description
                                controls.
                           • Added “and audio description” to Applicability: This Test Condition
                                DOES NOT APPLY (DNA) if there is no media player, or the media
                                player does not have a program selection and audio description
                                control.
```
