# Historical recovery artifacts

- `recovered-output/` contains the three tracked PDF editions and validation
  reports recovered from the PSPMAN worktree before relocation.
- `original-path-control-output/` contains a controlled external-output build
  made with the unchanged generator at its original absolute path. It reproduced
  all three recovered PDF hashes exactly and proved the ReportLab path-sensitive
  cover-resource boundary.

These files are evidence, not current build destinations. Ordinary relocated
outputs are generated under the ignored `manuals/pspman/output` directory.

