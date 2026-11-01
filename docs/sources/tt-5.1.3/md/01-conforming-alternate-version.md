# 1. Conforming Alternate Version (CAV) and Non-Interference

<!-- TT 5.1.3, printed pp. 7-13. Converted from the PDF by convert.py; the PDF is the authority. -->

Section 508/WCAG 2.0 allows the use of conforming alternate version to meet conformance requirements. When there are multiple versions of the content, only one version is required to be fully conforming as described in this section.

WCAG defines a conforming alternate version (CAV) as a version that:

1. conforms at the designated level, and

2. provides all of the same information and functionality in the same human language, and

3. is as up to date as the non-conforming content, and

4. for which at least one of the following is true:

1. the conforming version can be reached from the non-conforming page via an accessibility-supported mechanism, or

2. the non-conforming version can only be reached from the conforming version, or

3. the non-conforming version can only be reached from a conforming page that also provides a mechanism to reach the conforming version

This test process covers the four parts of the definition of conforming alternate up to 4.1. In this test process, it is not practical for the tester to find all of the paths to reach the non-conforming version; therefore, it is not possible to accurately validate that the non-conforming version can only be reached as described by 4.2 or 4.3. There may also be unknown paths to the non-conforming version that may be outside of the scope of testing. For these reasons, this test process assumes access from the non-conforming version (4.1 in the CAV definition) and does not cover 4.2 or 4.3.

This Conforming Alternate Version section deviates from the other tests in this process in the following ways:

- This section instructs the tester to perform tests in other sections. (See 1.A.)
- Conformance test results should be tracked and recorded under the respective Test IDs contained in the remainder of this document. At the end of this section, the tester will indicate if conforming alternate version(s) exists, using the results from this section combined with the test results from the remaining Test IDs.
- If found, a conforming alternate version essentially replaces the non-conforming versions of that content when determining the scope of conformance and reporting conformance results.
- Non-conforming content that has a conforming alternate version is only tested for the non-interference standards.

Reference this section whenever alternate versions of content are found.

Section 508 Conformance Tests
1. Conforming Alternate Version (CAV) and Non-Interference

The process for determining whether a conforming alternate version exists can be summarized as follows:

1. Find the version identified as the conforming alternate version.
2. For that version:
    - a. Check if the identified version passes all tests in this test process (sections 2-20)
    - b. Check for equivalence of the identified version
    - c. Check for a conforming access mechanism
3. Based on these test results:
    - a. If all tests pass, it is a conforming alternate version.
        - i. Test the non-conforming versions for non-interference
    - b. If any tests fail, it is not a conforming alternate version.

Although the identified version must pass all tests in Step 2 to be considered a Conforming Alternate Version, testers should continue testing even if a failure is found in Step 2.a so that any failures of 2.b or 2.c can be reported in the same report for remediation.

A test report should indicate that in cases when the identified version fails any of the tests required to be considered the conforming alternate version, the nonconforming version is still limited to only the non-interference tests. While this deviates from WCAG’s Understanding Conformance, this process assumes that the identified version will be remediated to pass all the conforming alternate version requirements.

### Accessible Alternate Version

#### Identify Content

Per WCAG 2.1, accessible versions should be identified, e.g., through a label on the page, as a link, in documentation, user preferences, controls to modify text appearance, etc. It may be helpful to review product documentation for information about accessible versions or enabling accessibility.

Alternate versions may be provided for a part of the page, entire pages, or an entire site. A web page or site may have more than one version of content or features. It is also possible that a site has more than one instance of conforming alternate version. The following are some indications that content is provided in more than one way.

- Content is identified as the accessible version
- Instructions are provided that describe how to enable accessibility
- Multiple methods are provided to complete a task (e.g., a calendar widget and a text field are provided for a user to enter a date)
- A link’s destination is an accessible alternate version or a version for assistive technology (e.g., screen reader version)
- User preferences or settings are provided to enable accessibility
- User controls exist to modify colors and text appearance

Per WCAG's definition, the identified version “does not need to reside within the scope of conformance, or even on the same web site, as long as it is as freely available as the non-conforming version.” However, the scope of testing with this process is limited to web-based alternatives that are available

Section 508 Conformance Tests
1. Conforming Alternate Version (CAV) and Non-Interference

on a desktop computer. Alternate versions do not include mobile applications that can only be accessed on a mobile device.

If there is more than one version and none are identified as the conforming alternate version/accessible version, assume there is no conforming alternate version and that these Conforming Alternate Version tests DO NOT APPLY. Perform tests 2 through 20 on all versions.

### Check alt-version-conformant

| Test Name | Test ID | Test Condition |
| --- | --- | --- |
| alt-version-conformant | 1.A | The identified version passes all applicable Test Conditions in this test process. |

**Applicability:**

This Test Condition DOES NOT APPLY (DNA) if

- there is only one version of content or
- if no versions are identified as the conforming alternate version/accessible version.

**How to Test:**

1. Enable accessibility settings (if necessary), select, and/or navigate to the version of content identified as the accessible alternate version.
2. Following this test process, test the identified version of the content for all applicable Test Conditions. Record the result for the appropriate Test ID.
    - a. If no failures are found, this may be a conforming alternate version.
    - b. If a failure is found, the identified version is not a conforming alternate version.

**Evaluate Results:**

If the following is TRUE, then the content PASSES; if the following is FALSE, then this Test Condition FAILS:

1. The identified version of content passes all applicable Test Conditions in this test process.

**Note:**

- Alternate versions may be provided to accommodate different technology environments or user groups. At least one version would need to pass all Test Conditions.

Equivalent Alternative

### Check alt-version-equivalent

| Test Name | Test ID | Test Condition |
| --- | --- | --- |
| alt-version-equivalent | 1.B | The identified version is up to date with the same information and functionality. |

**Applicability:**

This Test Condition DOES NOT APPLY if Test ID 1.A was evaluated as DOES NOT APPLY (DNA).

**How to Test:**

1. Continue from Test 1.A.
2. Review the content of the non-conforming version.
3. Verify that the identified version has the same information, functionality, and language as the non-conforming version. Section 508 Conformance Tests
1. Conforming Alternate Version (CAV) and Non-Interference

**Evaluate Results:**

If the following is TRUE, then the content PASSES; if the following is FALSE, then this Test Condition FAILS:

1. The identified version provides all of the same information and functionality in the same human language as the non-conforming content.

**Note:**

- Per WCAG, the identified version “does not need to be matched page for page with the original (e.g., the identified version may consist of more or fewer pages).”

### Conforming Mechanism

#### Identify Content

Identify the mechanism used to access the identified version. Various mechanisms may be used to reach the identified version, such as:

- A link to the identified version or a version for assistive technology (e.g., screen reader version)
- User preferences or settings to enable accessibility for a page or the entire site
- User controls to modify colors and text appearance of the page or entire site
- Navigating to the identified accessible version of content on a page

### Check alt-version-access

| Test Name | Test ID | Test Condition |
| --- | --- | --- |
| alt-version-access | 1.C | The mechanism to reach the identified version is accessible. |

**Applicability:**

This Test Condition DOES NOT APPLY if Test ID 1.A was evaluated as DOES NOT APPLY (DNA).

**How to Test:**

1. Perform Tests 2 through 20 for the mechanism used to reach the identified version.

**Evaluate Results:**

If the following is TRUE, then the content PASSES; if the following is FALSE, then this Test Condition FAILS:

1. The mechanism used to reach the accessible equivalent version passes all applicable Test Conditions.

**Notes:**

- Applicable mechanism tests may include Links and Buttons, Headings, Forms, and/or other tests.
- The mechanism to access the conforming version should directly or indirectly indicate that it leads to the accessible version. For example, text preceding a link to the accessible version might directly state that the link leads to the accessible version. It may also be possible to “hide” non-conforming content from AT and/or exclude it from keyboard focus, thereby limiting access only to the accessible version for users with disabilities. Such an approach, however, may not be possible, depending on the content.
- The mechanism may be explicitly provided in the content or may be relied upon to be provided by either the platform or by user agents, including assistive technologies. Section 508 Conformance Tests
1. Conforming Alternate Version (CAV) and Non-Interference

### Non-Interference

#### Identify Content

The non-conforming version(s) of the content. Exclude the version identified as the accessible version.

### Check non-interference

| Test Name | Test ID | Test Condition |
| --- | --- | --- |
| non-interference | 1.D | Content in the non-conforming version(s) meets Conformance Requirement 5. |

**Applicability:**

This Test Condition DOES NOT APPLY if Test ID 1.A was evaluated as DOES NOT APPLY (DNA).

**How to Test:**

1. If necessary and/or applicable, disable accessibility features within site settings or preferences.
2. Perform ONLY the following tests on the non-conforming version(s) of the content:
    - a. Test ID 2.A (1.4.2-audio-control)
    - b. Test ID 2.B (2.2.2-blinking-moving-scrolling)
    - c. Test ID 2.C (2.2.2-auto-updating)
    - d. Test ID 3.A (2.3.1-flashing)
    - e. Test ID 4.C (2.1.2-no-keyboard-trap)
3. Enter test results for the appropriate Test IDs listed above.
4. Do not perform any further testing on the non-conforming version(s) of the content.

**Evaluate Results:**

If the following is TRUE, then the content PASSES. If the following is FALSE, then this Test Condition FAILS:

1. The results for each of the following tests are PASS or DOES NOT APPLY for all non-conforming version(s) of the content.
    - a. Test ID 2.A (1.4.2-audio-control)
    - b. Test ID 2.B (2.2.2-blinking-moving-scrolling)
    - c. Test ID 2.C (2.2.2-auto-updating)
    - d. Test ID 3.A (2.3.1-flashing)
    - e. Test ID 4.C (2.1.2-no-keyboard-trap)

**Note:**

- Enter a single result for all non-conforming versions of content. (FAIL if any of the versions fail; PASS if at least one result is Pass and the others are Pass or Does not apply; DOES NOT APPLY if all results are Does Not Apply.)
- 3.A (2.3.1 flashing) must have a test result of DOES NOT APPLY in order to meet the 1.D, Non-Interference Test Condition. A test result of NOT TESTED does not meet the 1.D Test Condition. See Test ID 3.A for further details.
- After performing this test on the non-conforming version of content that has a conforming alternate version for the content, omit testing of the non-conforming content from the rest of testing.

Section 508 Conformance Tests
1. Conforming Alternate Version (CAV) and Non-Interference

- While a conforming alternate version of content might have been confirmed under Tests 1.A through 1.C, a content owner CANNOT make a claim of conformance to the Section 508 standards if any version of content fails Test ID 1.D non-interference, including content that is not otherwise relied upon to meet conformance.

**Applicable Standards**

```text
Section 508/WCAG Success Criteria                                                      Baseline Requirements
Conforming alternate version is not a requirement. Conformance requirement #1          20. Conforming Alternate
allows non-conforming pages to be included within the scope of conformance as          Versions
long as they have a "conforming alternate version". This ensures that all of the
information and all of the functionality that is on the pages inside of the scope of
conformance is available on conforming Web pages.
WCAG Conformance Requirement 3. Non-Interference: The following success                3. Non-Interference
criteria apply to all content on the page, including content that is not otherwise
relied upon to meet conformance, because failure to meet them could interfere
with any use of the page:
• 1.4.2 - Audio Control,
• 2.1.2 - No Keyboard Trap,
• 2.3.1 - Three Flashes or Below Threshold, and
• 2.2.2 - Pause, Stop, Hide.

Section 508 Conformance Tests
1. Conforming Alternate Version (CAV) and Non-Interference
```
