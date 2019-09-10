# ulauncher-locate extension

Locate files using `locate` linux tool (`findutils` package).

The `locate` tool is lightening fast compared to `find`, as it relies on a database pre-initialized.

1. Search: 
- files
  - 'fl scala olympus' will match '/home/mjost/workspace/scala/olympus-photosync'
  - 'fl .bashrc' will match '/home/mjost/.bashrc'
  - 'fl fstab' will match '/etc/fstab'
- directories
  - 'dl mjost scala' will match '/home/mjost/workspace/scala/'

2. Open: 
- the file using a configurable script/tool (on enter)
  - on a file, pressing enter will open it
- the directory containing the file using your favorite shell
  - on a file, pressing alt+enter will open a console in the parent directory

