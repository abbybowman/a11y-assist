# Appendix C: Test Process Quick Reference

<!-- TT 5.1.3, printed pp. 89-94. Converted from the PDF by convert.py; the PDF is the authority. -->

## Quick Reference with Test Conditions

```text
Test ID   Test Name                   Test Condition
1.A       alt-version-conformant      The identified version passes all applicable Test Conditions in
                                      this test process.
1.B       alt-version-equivalent      The accessible version is up to date with the same information
                                      and functionality.
1.C       alt-version-access          The mechanism to reach the identified version is accessible.
```

```text
1.D       non-interference            Content in the non-conforming version(s) meets Conformance
                                      Requirement 5.
2.A       1.4.2-audio-control         The user can pause, stop, or control the volume of audio
                                      content that plays automatically.
2.B       2.2.2-blinking-moving-      The user can pause, stop, or hide moving, blinking, or scrolling
          scrolling                   content.
2.C       2.2.2-auto-updating         The user can pause, stop, hide, or control the frequency of
                                      automatically updating content.
2.D       4.1.2-change-notify-auto    The page provides notification of each automatic
                                      update/change in content.
3.A       2.3.1-flashing              If NO flashing content is found, then this Test Condition DOES
                                      NOT APPLY (DNA). If flashing content IS found, then this test
                                      should be recorded as NOT TESTED.
4.A       2.1.1-keyboard-access       All functionality can be accessed and executed using only the
                                      keyboard.
4.B       2.1.1-no-keystroke-timing   Individual keystrokes do not require specific timings for
                                      activation of functionality.
4.C       2.1.2-no-keyboard-trap      There is no keyboard trap.
4.D       2.4.7-focus-visible         A visible indication of focus is provided when focus is on the
                                      interface component.
4.E       3.2.1-on-focus              When an interface component receives focus, it does not
                                      initiate an unexpected change of context.
4.F       2.4.3-focus-order-meaning   The focus order preserves the meaning and operability of the
                                      web page.
5.A       3.3.2-label-provided        Visual labels or instructions are provided for form elements.
```

```text
5.B       2.4.6-label-descriptive     Each visual form label is sufficiently descriptive.
```

```text
5.C       1.3.1-programmatic-label    The combination of the accessible name, accessible
                                      description, and other programmatic associations (e.g., table
                                      column and/or row associations) describes each input field and
                                      includes all relevant instructions and cues (textual and
                                      graphical).
5.D       3.2.2-on-input              Changing field values/selections (e.g., entering data in a text
                                      field, changing a radio button selection) does NOT initiate an
                                      unexpected change of context.
Test ID Test Name                     Test Condition
5.E      4.1.2-change-notify-form     The page provides notification of each form-related change in
                                      content.
5.F      3.3.1-error-identification   The item in error is identified and the error is described to the
                                      user in text.
5.G      3.3.3-error-suggestion       Guidance (e.g., suggestion for corrected input) is provided
                                      about how to correct errors for form fields.
5.H      3.3.4-error-prevention       The web page allows the user to check, reverse, and/or
                                      confirm submission.
6.A      2.4.4-link-purpose           The purpose of each link can be determined from any
                                      combination of the link text, accessible name, accessible
                                      description, and/or programmatically determined link context.
6.B      4.1.2-change-notify-links    The page provides notification of each change in content that
                                      is the result of interaction with a link.
7.A      1.1.1-meaningful-image-      The accessible name and accessible description for a
         name                         meaningful image provides an equivalent description of the
                                      image.
7.B      1.1.1-decorative-image       There is no accessible name and accessible description for a
                                      decorative image.
7.C      1.1.1- decorative-           The background image is not the only means used to convey
         background-image             important information.
7.D      1.1.1-captcha-alternative    Alternative forms of CAPTCHA are provided.
7.E      1.4.5-image-of-text          The image of text cannot be replaced by text or is
                                      customizable.
8.A      2.2.1-timing-adjustable      The user can turn off, adjust, or extend the time limit.
9.A      2.4.1-bypass-function        A keyboard-accessible method is provided to bypass repetitive
                                      content.
9.B      3.2.3-consistent-            Each navigational element occurs in the same relative order
         navigation                   with regard to other repeated components on each web page
                                      where it appears.
9.C      3.2.4-consistent-            The accessible name and description is consistent for
         identification               components that perform the same function.
10.A     2.4.6-heading-purpose        Each heading describes the topic or purpose of its content.
10.B     1.3.1-heading-               Each programmatically determinable heading is a visual
         determinable                 heading and each visual heading is programmatically
                                      determinable.
10.C     1.3.1-heading-level          Programmatic heading levels logically match the visual heading
                                      presentation within the heading structure.
10.D     1.3.1-list-type              All visually apparent lists are programmatically identified
                                      according to their type.
11.A     3.1.1-page-language-         The default human language of each web page can be
         defined                      programmatically determined.
11.B     3.1.2-part-language-         The human language for any content segment that differs from
         defined                      the default human language of the page can be
                                      programmatically determined.
12.A     2.4.2-page-title-defined     A <title> element is defined for the web page.
Test ID Test Name                      Test Condition
12.B     2.4.2-page-title-purpose      The <title> element identifies the contents or purpose of the
                                       web page.
12.C     4.1.2-frame-title             Each <frame> has a title attribute that describes its content.
12.D     4.1.2-iframe-name             The combination of accessible name and description for each
                                       <iframe> describes its content.
13.A     1.4.1-color-meaning          Color is not used as the only visual means of conveying
                                      information, indicating an action, prompting a response, or
                                      distinguishing a visual element.
13.B     1.3.3-sensory-info           Instructions provided for understanding and operating content
                                      do not rely solely on sensory characteristics of components,
                                      such as shape, color, size, visual location, orientation, or
                                      sound.
13.C     1.4.3-contrast               The visual presentation of text and images of text have
                                      sufficient contrast.
14.A     1.3.1-table-identification   Each data table has programmatic markup to identify it as a
                                      table.
14.B     1.3.1-cell-header-           All data cells are programmatically associated with relevant
         association                  headers.
14.C     1.3.1-layout-table-structure The layout table DOES NOT designate the layout table using
                                      ARIA role="table" AND DOES NOT include table header
                                      structure and relationship elements and/or associated
                                      attributes.
15.A     1.3.2-content-order-         The reading order of the content (in context) is correct and the
         meaning-CSS-position         meaning of the content (in context) is preserved without CSS
                                      positioning.
16.A     1.2.1-audio-transcript-text A text-based alternative is provided for audio-only content
                                      that provides an accurate and complete representation of the
                                      audio-only content.
16.B     1.2.1-video- alternative-    The video-only content information is also available through
         equivalent                   an equivalent text or audio alternative.
17.A     1.2.2-captions-equivalent     The synchronized media provides accurate captions for the
                                       audio content.
17.B     1.2.5-audio-description-      The synchronized media provides an equivalent soundtrack
         equivalent                    (combination of narration and audio descriptions) for the
                                       video content.
17.C     1.2.4-captions-live-          The live synchronized media provides accurate captions for the
         equivalent                    audio content.
17.D     503.4-caption-controls        The media player provides user controls for closed captions.
17.E     503.4-description-controls    The media player provides user controls for audio descriptions.
```

```text
17.F     503.4.1-caption-control-      User controls for captions are provided at the same menu level
         level                         as the user controls for volume or program selection.
17.G     503.4.2-description-          User controls for audio descriptions are provided at the same
         control-level                 menu level as the user controls for volume or program
                                       selection.
Test ID Test Name                     Test Condition
18.A     1.4.4-resize-text            There is a mechanism to resize, scale, or zoom in on the text to
                                      at least 200% of its original size without loss of content or
                                      functionality.
19.A     2.4.5-multiple-ways          There are two or more ways to locate a web page within a set
                                      of web pages.
20.A     4.1.1-parsing                This test should be recorded as NOT TESTED.
```

## One-Page Quick Reference – Test Names Only

```text
Test ID   Test Name                       Test ID   Test Name                    Test ID   Test Name
1.A       alt-version-conformant          5.H       3.3.4-error-prevention       13.A      1.4.1-color-meaning
1.B       alt-version-equivalent          6.A       2.4.4-link-purpose           13.B      1.3.3-sensory-info
1.C       alt-version-access              6.B       4.1.2-change-notify-         13.C      1.4.3-contrast
                                                    links
1.D       non-interference                7.A       1.1.1-meaningful-            14.A      1.3.1-table-
2.A       1.4.2-audio-control                       image-name                             identification
                                          7.B       1.1.1-decorative-image       14.B      1.3.1-cell-header-
2.B       2.2.2-blinking-moving-                                                           association
          scrolling                       7.C       1.1.1- decorative-           14.C      1.3.1-layout-table-
2.C       2.2.2-auto-updating                       background-image                       structure
2.D       4.1.2-change-notify-            7.D       1.1.1-captcha-               15.A      1.3.2-content-order-
          auto                                      alternative                            meaning-CSS-position
                                          7.E       1.4.5-image-of-text          16.A      1.2.1-audio-transcript-
3.A       2.3.1-flashing
                                          8.A       2.2.1-timing-adjustable                text
4.A       2.1.1-keyboard-access                                                  16.B      1.2.1-video-
                                          9.A       2.4.1-bypass-function
                                                                                           alternative-equivalent
4.B       2.1.1-no-keystroke-             9.B       3.2.3-consistent-
                                                    navigation                   17.A      1.2.2-captions-
          timing                                                                           equivalent
4.C       2.1.2-no-keyboard-trap          9.C       3.2.4-consistent-
                                                    identification               17.B      1.2.5-audio-
4.D       2.4.7-focus-visible
                                          10.A      2.4.6-heading-purpose                  description-equivalent
4.E       3.2.1-on-focus                                                         17.C      1.2.4-captions-live-
                                          10.B      1.3.1-heading-
4.F       2.4.3-focus-order-                                                               equivalent
                                                    determinable
          meaning
                                          10.C      1.3.1-heading-level          17.D      503.4-caption-controls
5.A       3.3.2-label-provided
5.B       2.4.6-label-descriptive                                                17.E      503.4-description-
                                          10.D      1.3.1-list-type
5.C       1.3.1-programmatic-                                                              controls
          label                           11.A      3.1.1-page-language-
                                                    defined                      17.F      503.4.1-caption-
5.D       3.2.2-on-input                                                                   control-level
                                          11.B      3.1.2-part-language-
                                                    defined                      17.G      503.4.2-description-
5.E       4.1.2-change-notify-                                                             control-level
          form                            12.A      2.4.2-page-title-defined     18.A      1.4.4-resize-text
5.F       3.3.1-error-                    12.B      2.4.2-page-title-            19.A      2.4.5-multiple-ways
          identification                            purpose
                                          12.C      4.1.2-frame-title
                                                                                 20.A      4.1.1-parsing
5.G       3.3.3-error-suggestion
                                          12.D      4.1.2-iframe-name
```
