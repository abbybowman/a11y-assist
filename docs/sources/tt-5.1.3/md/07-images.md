# 7. Images

<!-- TT 5.1.3, printed pp. 34-40. Converted from the PDF by convert.py; the PDF is the authority. -->

### Meaningful Images

#### Identify Content

1. Use ANDI: graphics/images to find all images on the page with non-empty accessible names.
2. Use ANDI: Focusable Elements (and/or ANDI: links/buttons if applicable) to check the ANDI Output of keyboard-focusable images, as they may be components of focusable elements. Use these results if they are different from the output of ANDI: Graphics/Images.
3. Identify images that have non-empty accessible names.

**Note:**

- ANDI may skip over background images and images with role=”presentation” or role=”none”. These will be tested in 7.B.

### For Meaningful Images – Check 1.1.1-meaningful-image-name

| Test Name | Test ID | Test Condition |
| --- | --- | --- |
| 1.1.1-meaningful-image-name | 7.A | The accessible name and accessible description for a meaningful image provides an equivalent description of the image. |

**Applicability:**

This Test Condition only applies to images with non-empty accessible names. This test DOES NOT APPLY (DNA) to images with empty or missing accessible names, or if there are no images on the page.

**How to Test:**

1. For each image with a non-empty accessible name:
    - a. Determine if the image is pure decoration.
    - b. The ANDI Output (of ANDI: graphics/images, ANDI: Focusable Elements or ANDI: links/buttons as applicable) must provide an equivalent description of the image.
        - i. This does not have to be a literal description of the image. An equivalent description could also describe the meaning or purpose of the image.
        - ii. This could also be a brief description of the image with instructions on where to find equivalent information elsewhere on the page.
    - c. If the image is used as a CAPTCHA, ANDI Output must describe the purpose of the CAPTCHA.
    - d. If the image is of meaningful text, ANDI Output must contain the same text.

**Evaluate Results:**

If ALL of the following are TRUE, then the content PASSES:

1. The image is not pure decoration.
2. The ANDI Output contains an equivalent description for the image or refers to a description in the page content.

**Note:**

- WCAG defines “pure decoration” as “serving only an aesthetic purpose, providing no information, and having no functionality,” used only for visual formatting, or not presented to users. Examples of this are:  a swirl in the corner that conveys no information but just fills up a blank space to create an aesthetic effect  images used as generic bullet points  an abstract graphic used to separate sections of a page  an invisible image that is used to track usage statistics  part of a link to improve appearance or to increase the clickable area
- Any image that is on the page but not detected by ANDI should not be tested in 7.A.
- Step 1.d applies to images where the text is the main content. If you have already tested an image under 1.b, there is no need to retest it under 1.d.
- Step 1.d does not apply to text that is part of a picture that contains significant other visual content. Examples of such pictures include graphs, screenshots, and diagrams which visually convey important information through more than just text. Another example would be a person’s name on a nametag in a photograph, where showing the name is not the main purpose of the photo.
- Any changes to meaningful images that occur automatically or as a result of interaction with the page should be included in this test.  Notification of automatic changes is tested in Test 2.D.  Notification of changes as a result of interaction with other content is tested either in Test 5.E or 6.B.

### Decorative Images

#### Identify Content

1. If available, select the “find background” button in ANDI: graphics/images to highlight all background images. (This button is not available if no background images are detected.) Exclude them from this test and test them under 7.C.
2. Use ANDI: graphics/images to find all images on the page with empty accessible names (blank ANDI Output).
    - a. Use ANDI: Focusable Elements (and/or ANDI: Links/Buttons if applicable) to check the ANDI Output of keyboard-focusable images, as they may be components of focusable elements. Use these results if they are different from the output of ANDI: Graphics/Images.
3. Use ANDI: graphics/images to find all images on the page with no accessible names (“The image has no accessible name, [alt], or [title]”).
4. Use visual inspection along with ANDI to determine if there are images skipped (not navigated to) by ANDI.

**Note:**

- ANDI may skip over background images and images with role=”presentation”, role=”none”, or aria-hidden=”true”.

### For Decorative Images – Check 1.1.1-decorative-image

| Test Name | Test ID | Test Condition |
| --- | --- | --- |
| 1.1.1-decorative-image | 7.B | There is no accessible name and accessible description for a decorative image. |

**Applicability:**

This test DOES NOT APPLY (DNA) to background images, images with non-empty accessible names, or if there are no images on the page.

**How to Test:**

1. For each image identified:
    - a. Determine if the image is the only means of conveying important information on the page.
    - b. Determine if the image is in the tab order.
    - c. Determine if the image has no accessible name markup (ANDI Output: “The image has no accessible name, [alt], or [title]”).

**Evaluate Results:**

If ALL of the following are TRUE, then the content PASSES:

1. The image is NOT the only means of conveying important information on the page.
2. The image is NOT in the tab order.
3. The image has an empty (NOT missing) accessible name.

**Note:**

- Any changes to decorative images that occur automatically or from user interaction with the page should be included in this test.

CSS Background Images Identify content
1. Use the ANDI: graphics/images module to find CSS background images. If the “find background” and “hide background” buttons are available, background images are on the page.

If there is no such content, the result for the following test ID(s) is DOES NOT APPLY: 7.C.

Check 1.1.1- decorative-background-image

| Test Name | Test ID | Test Condition |
| --- | --- | --- |
| 1.1.1-decorative-background-image | 7.C | The background image is not the only means used to convey important information. |

**Applicability:**

This Test Condition DOES NOT APPLY (DNA) if there are no background images on the page.

**How to Test:**

1. Select the “find background” button in ANDI: graphics/images to highlight all background images.
2. For each background image, determine whether important information provided by the background image is available without the background image.

- a. Select the “hide background” function in ANDI: graphics/images to hide background images and help determine if the image’s information is also available on the page without the background image.
- b. Review the sequence or positioning of the image to determine whether equivalent information is presented in the same logical order.

**Evaluate Results:**

If any of the following is TRUE, then the content PASSES:

1. The background image is decorative, OR
2. The meaning of the background image is also available without the background image.

**Note:**

- Any changes to meaningful background images that occur automatically or as a result of user interaction with the page should be included in this test.

CAPTCHA Images Identify content Identify all CAPTCHA images.

If there is no such content, the result for the following test ID(s) is DOES NOT APPLY: 7.D.

### Check 1.1.1-captcha-alternative

| Test Name | Test ID | Test Condition |
| --- | --- | --- |
| 1.1.1-captcha-alternative | 7.D | Alternative forms of CAPTCHA are provided. |

**Applicability:**

This Test Condition DOES NOT APPLY (DNA) if there are no CAPTCHA images on the page.

**How to Test:**

1. Determine whether alternative forms of CAPTCHA with output modes for different types of sensory perception are provided.

**Evaluate Results:**

If ALL of the following are TRUE, then the content PASSES:

1. The CAPTCHA has a format for users without vision, AND
2. The CAPTCHA has a format for users without hearing.

Images of Text Identify content Identify all images of text

EXCLUDE text that is part of a picture that contains significant other visual content such as CAPTCHA, graphs, screenshots, and diagrams, which visually convey important information more than just text.

If there is no such content, the result for the following test ID(s) is DOES NOT APPLY: 7.E.

### Check 1.4.5-image-of-text

| Test Name | Test ID | Test Condition |
| --- | --- | --- |
| 1.4.5-image-of-text | 7.E | The image of text cannot be replaced by text or is customizable. |

**Applicability:**

This Test Condition DOES NOT APPLY (DNA) if there are no images of text on the page.

**How to Test:**

1. Determine if text can be used instead of the image of text to present the same effect and information.
    - a. Logotypes (text that is part of a logo or brand name) cannot be replaced by text.
    - b. Type samples, branding, images of specific fonts that are not widely supported are additional examples of images of text that cannot be replaced by text.
2. Determine if the image of text can be visually customized: adjust the font, size, color and background with controls provided by the web page.
    - a. Customizing font size for an image of text also implies the ability to adjust the size without pixelation (which is typically evident when simply using the browser resize functionality to resize images).

**Evaluate Results:**

If ANY of the following is TRUE, then the content PASSES:

1. The image of text cannot be replaced with text, OR
2. The image of text can be visually customized.

**Applicable Standards**

```text
Section 508/WCAG Success Criteria                                                       Baseline Requirements
WCAG SC: 1.1.1. Non-Text: All non-text content that is presented to the user has a      6. Images
text alternative that serves the equivalent purpose, except for [specific] situations
listed.
WCAG SC: 1.4.5 Images of Text: If the technologies being used can achieve the visual
presentation, text is used to convey information rather than images of text except
for [specific situation listed].
WCAG SC: 1.1.1. Non-Text: All non-text content that is presented to the user has a      18. CSS Content and
text alternative that serves the equivalent purpose, except for [specific] situations   Positioning
listed.
WCAG SC 4.1.2 Name, Role, Value: For all user interface components (including but       5. Changing Content
not limited to: form elements, links and components generated by scripts), the
name and role can be programmatically determined; states, properties, and values
that can be set by the user can be programmatically set; and notification of changes
to these items is available to user agents, including assistive technologies.
```
