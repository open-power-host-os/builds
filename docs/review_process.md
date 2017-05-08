# Review Process Guidelines

Refer to https://help.github.com/articles/about-pull-request-reviews/ for details on Pull Request review process at GitHub.

For Host OS project, also consider the following guidelines:

## Avoid stacked Pull Requests

* Pull Requests (PR) should be independent of each other.
* If any, identify dependencies in the very first line of the PR description.
  * GitHub does not allow approving only a subset of commits from a PR. When commits are updated but the reviewing commit is not, there is no way to distinguish this in the GitHub interface.

## Avoid non-related commits in the Pull Request

* Non-related changes make reviewing difficult and deviate from the original purpose of the PR.
* Maintainers will close PR with unrelated changes and ask submitter to submit a new PR without the noise commits.

## Do not approve a Pull Request which does not pass tests (only for reviwers)

* The maintainer approval will be one of the last steps on the review process. 
* If maintainer gave his/her approval, it means the PR can be merged at any time, unless PR dependencies are still under review.
