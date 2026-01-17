- make sure the text color contrast is correct so that users can read it without any issues
- make sure the buttons are horizontal and not vertical
- make sure that the streamlit app demo covering use case scenarios are rich and contextual, with clear explanation of what, where, when, how and why provided in a narrative fashion and ensure the stories all align with rich and large supporting data
- buttons need to be horizontal
- Make sure the color contrast for the UI for dark and light modes are done correctly so that the text and components are all clearly visible/legible to the users

## CRITICAL: Test Directory Policy

**NEVER DELETE THE test/ DIRECTORY OR ITS CONTENTS**

The test/ directory is a local testing infrastructure that:
- Contains scripts for running end-to-end tests against local and hybrid deployments
- Captures detailed test results in JSON format
- Tracks query execution metrics (success/failure, timing, row counts)
- Is intentionally in .gitignore to keep it local only
- Should remain on the local filesystem even though it's not committed to git

If asked to clean up the repository:
- DO NOT delete the test/ directory
- The directory is correctly ignored by git via .gitignore
- It contains valuable test infrastructure for validation
- Deletion would require recreating the entire test framework

This note was added after an incident where the test/ directory was mistakenly deleted when it should have only been added to .gitignore.