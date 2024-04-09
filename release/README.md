# PyRTL release process documentation

See [Packaging Python
Projects](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
for an overview of Python packaging. PyRTL's `pyproject.toml` configuration is
based on this tutorial.

See [Publishing package distribution releases using GitHub
Actions](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
for an overview of distributing Python packages with GitHub Actions. PyRTL's
`python-release.yml` configuration is based on this tutorial.

## PyRTL versioning

PyRTL uses [semantic versioning](https://semver.org/). All version numbers are
of the form `MAJOR.MINOR.PATCH`, with an optional `rcN` suffix for release
candidates, starting from `rc0`. Valid examples include `0.11.1` and
`0.11.0rc0`.

Use `rc` release candidates for pre-releases, and to test the release process.
`pip` will not install release candidates by default. Use `pip install --pre
pyrtl` to install the latest release candidate.

The rest of this document assumes that the new PyRTL version number is
`$NEW_VERSION`.

See [PEP 440](https://peps.python.org/pep-0440/) for more details on version
numbers.

## Update version numbers

1. Clone the PyRTL repository: `git clone git@github.com:UCSBarchlab/PyRTL.git`
1. Edit `pyproject.toml` by updating the `version =` line to `version =
   "$NEW_VERSION"`
2. Commit this change: `git commit pyproject.toml`
3. Tag the new version with `git tag $NEW_VERSION`
4. Push this change to GitHub. Tags are not pushed by default, so use: `git push
   origin $NEW_VERSION`

The `python-release.yml` GitHub workflow should detect the new tag, build a new
release, and upload the new release to TestPyPI.

The following manual steps should be automated by
`.github/workflows/python-release.yml`. Manual release instructions are
provided below in case a release needs to be built without GitHub workflow
automation.

## Building and publishing a new release manually

These manual steps should be automated by
`.github/workflows/python-release.yml`. If the automation is working, you
shouldn't need to run these commands.

### Manual build

1. Update build tools: `pip install  --upgrade -r release/requirements.txt`
2. Build distribution archive: `python3 -m build`. This produces two files in
   `dist/`: a `.whl` file and a `.tar.gz` file.

### Manual publish on TestPyPI

1. If necessary, create a TestPyPI API token: Go to
   https://test.pypi.org/manage/account/ and click 'Add API token'.
2. Upload distribution archive to TestPyPI: `twine upload --repository testpypi
   dist/*` and enter your API token when prompted.
3. Check the new release's status at https://test.pypi.org/project/pyrtl/#history
4. Create a new virtual environment, then install and test the new release from
   TestPyPI: `pip install --index-url https://test.pypi.org/simple/ --no-deps
   pyrtl` . If you created a `rc` release candidate, add the `--pre` flag.

### Manual publish on PyPI

> :warning: The next steps update the official PyRTL release on PyPI, which
> affects anyone running `pip install pyrtl`. Proceed with caution!

1. Upload distribution archive to PyPI: `twine upload dist/*`
2. Check the new release's status at https://pypi.org/project/pyrtl/
3. Install and test the new release from PyPI: `pip install pyrtl`

## Fixing Mistakes

First assess the magnitude of the problem. If the new release is unusable or is
unsafe to use, yank the bad release, then publish a fixed release. If the new
release has a smaller problem, and is mostly usable, just publish a fixed
release.

### Yanking A Bad Release

If the new release is unusable, [yank the
release](https://pypi.org/help/#yanked). This can be done by a project owner on
PyPI, by clicking on 'Manage project' then 'Options', then Yank'. When a
release is yanked, it remains available to anyone requesting exactly the yanked
version, so a project with a pinned requirement on PyRTL won't break. A yanked
version will not be installed in any other case, so a user running `pip install
pyrtl` will not receive a yanked version.

### Publishing A Fixed Release

Fix the problem in the code, then publish a new release with a new version
number by following the instructions above. Do not attempt to reuse an old
version number.
