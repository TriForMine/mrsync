# Rsync Clone
This is an rsync clone implemented as a school project.

## What is rsync?
Rsync is a popular file synchronization tool used to copy and synchronize files between two locations. It is known for its ability to transfer only the differences between the source and destination files, which makes it highly efficient for large file transfers over slow or unreliable networks.

## How does this clone work?
Our rsync clone uses a similar algorithm to the original rsync tool to transfer files efficiently. It compares the source and destination files to determine which parts of the file have changed, and only transfers those parts.

## Usage
To use this rsync clone, first clone this repository to your local machine. Then, run the rsync.py script with the appropriate command line arguments to specify the source and destination files, as well as any additional options.

Here's an example command to synchronize files between two directories:
```sh
python3 mrsync.py /path/to/source/dir/ /path/to/destination/dir/
```

## Contributions
We welcome contributions from the community! If you find a bug or have an idea for a new feature, please open an issue or submit a pull request.

## License
This rsync clone is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for more information.
