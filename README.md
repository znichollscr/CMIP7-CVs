Working branch for demonstrating CMIP7 CVs access via esgvoc.
Not meant for widespread consumption.
This README will be re-written if/when this branch is merged back into main.

## CMOR CVs file

When using [cmor](https://github.com/PCMDI/cmor) for re-writing raw model output,
a JSON file of controlled vocabulary (CV) information is required.
A JSON file in the required format, based on the CVs information contained in this repository
is included here, see `cmor-cvs.json`.

### Keeping the file up to date

To ensure that this file is always consistent with the CV content,
we check it as part of each pull request.
Pull requests are only merged into the `esgvoc` branch once the CMOR CVs file is up to date.

The process for updating the CMOR CVs file can be a bit fiddly,
as it requires carefully installing and using `esgvoc`.
To make updating the file simpler, we have introduced some extra functionality.
In a pull request, you can simply comment
`\update-cmor-cvs-table` and the CMOR CVs file will be updated.

In most cases, simply commenting `\update-cmor-cvs-table` will be enough.
In such a case, the content of the `cmor-cvs-creation.env` file
is used to determine which fork and branch/commit of the CMIP7 CVs,
the universe CVs and esgvoc to use when updating the CVs file.
In some cases, you will want to update these settings.
This can be done by parsing arguments to the `\update-cmor-cvs-table` command,
e.g. `\update-cmor-cvs-table universe-cvs-fork="my-fork" esgvoc-commit="abc123"`.
At the time of writing, the available arguments are
(check the github workflow file for the full list of available arguments):

- `universe-cvs-fork`: The fork to use when retrieving the universe CVs
- `universe-cvs-brach`: The branch to use when retrieving the universe CVs
- `esgvoc-fork`: The fork to use when installing esgvoc
- `esgvoc-commit`: The commit (ID) to use when installing esgvoc
- `cmip7-cvs-fork`: The fork to use when retrieving the CMIP7 CVs
- `cmip7-cvs-branch`: 'The branch to use when retrieving the CMIP7 CVs

For users who prefer to run things locally, simply update `cmor-cvs-creation.env` as required,
then (likely within a virtual environment)
run `source cmor-cvs-creation.env && bash install-environment-for-cmor-cvs-creation.sh -v`
then `esgvoc cmor-export-cvs-table --out-path cmor-cvs.json`
then finally commit and push the result.

#### Developer notes

The set of actions which makes this possible is relatively straightforward.
In short, there is one workflow that listens for comments
(`slash-command-dispatch.yaml` at the time of writing)
and one that updates the file
(`update-cmor-cvs-table-command.yaml` at the time of writing).
If a comment of the right form is made, then the workflow that updates the file is run.
The actions that are used for this are all clearly specified in the relevant workflow files.

The other key component is authentication.
In order for the action to be able to commit and push,
there is a secret `PERSONAL_ACCESS_TOKEN`, which contains an access token
that gives the required permissions.
