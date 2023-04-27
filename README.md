# Mrsync
This is an rsync clone implemented as a school project. It's written in Python 3 and supports nearly all the options from the real rsync tool. It also supports incremental transfers, compression, and SSH.

[![action status](https://github.com/triformine/mrsync/actions/workflows/unittest.yml/badge.svg?event=push)]

## What is rsync?
Rsync is a popular file synchronization tool used to copy and synchronize files between two locations. It is known for its ability to transfer only the differences between the source and destination files, which makes it highly efficient for large file transfers over slow or unreliable networks.

## Dependencies
This rsync clone requires Python 3.6 or higher. It also requires the following Python libraries:
- [cbor2](https://pypi.org/project/cbor2/) (for encoding messages)
- [argparse](https://pypi.org/project/argparse/) (for parsing command line arguments)
- [python-daemon](https://pypi.org/project/python-daemon/) (for running as a daemon)

## Installation
To install this rsync clone, first clone this repository to your local machine. Then, run the following command to install the dependencies:
```sh
pip3 install -r requirements.txt
```

## Usage
To run this rsync clone, use the following command:

```sh
python3 mrsync.py /path/to/source/dir/ /path/to/destination/dir/
```
or
```sh
mrsync.py /path/to/source/dir/ /path/to/destination/dir/
```

## Logs
When running the script with the `--verbose` option:

- When using SSH, the script will print the SSH logs to log.txt and error.txt in the home directory on the remote server.
- When using Daemon, the script will print the Daemon logs to log.txt and error.txt in the directory the daemon is running in.
- When using the default mode, the script will print the logs to stdout and stderr.

## Unit Test
To run the unit test, use the following command:
```sh
python3 -m unittest discover
```

## List Only
By default, if you run the script with only a source it will list all the files in the source directory. To list all the files in the source directory, use the following command:
```sh
python3 mrsync.py /path/to/source/dir/
```

## Incremental Transfers
Incremental transfers are supported by default. This means that only the parts of the file that have changed will be transferred. To disable incremental transfers, use the `--whole-file` option.
It's implemented by using a modified version of the rolling hash adler32. The hash is calculated for each block of the file and compared to the hash of the same block in the destination file. If the hashes are different, the block is transferred.

## SSH
This rsync clone supports transferring files over SSH. To use SSH, you first need to add all those project files to your remote server. Then, you can use the following command to transfer files over SSH:
```sh
python3 mrsync.py /path/to/source/dir/ user@remotehost:/path/to/destination/dir/
```

## Daemon
This rsync clone also supports running as a daemon. To run as a daemon, use the following command:
```sh
python3 mrsync.py --daemon
```

Then, you can connect to the daemon using the following command:
```sh
python3 mrsync.py host::/path/to/source/dir/ /path/to/destination/dir/
```
## Compression
This rsync clone supports compressing files during transfer. To compress files during transfer, use the `--compress` option. By default, the compression level is set to 6. To change the compression level, use the `--compress-level` option.
It uses the zlib library to compress files.

## Message Encoding
We are using cbor to encode messages. It's a binary encoding format that is more efficient than json. It's also more secure because it doesn't allow for arbitrary code execution.
More information about cbor can be found [here](https://cbor.io/).

## Options
The following options from the real rsync tool are implemented in our clone:

| Option                          | Description                                      |
|---------------------------------|--------------------------------------------------|
| -h, --help                      | show this help message and exit                  |
| -v, --verbose                   | increase verbosity                               |
| -q, --quiet                     | suppress non-error messages                      |
| -a, --archive                   | archive mode; same as -rpt (no -H)               |
| -r, --recursive                 | recurse into directories                         |
| -u, --update                    | skip files that are newer on the receiver        |
| -d, --dirs                      | transfer directories without recursing           |
| -H, --hard-links                | preserve hard links                              |
| -p, --perms                     | preserve permissions                             |
| -t, --times                     | preserve times                                   |
| -z, --compress                  | compress file data                               |
| --compress-level COMPRESS_LEVEL | specify level of compression                     |
| --existing                      | skip creating new files on receiver              |
| --ignore-existing               | skip updating files that exist on receiver       |
| --delete                        | delete extraneous files from dest dirs           |
| --force                         | force deletion of dirs even if not empty         |
| --timeout TIMEOUT               | set I/O timeout in seconds                       |
| --blocking-io                   | use blocking I/O for the remote shell            |
| -I, --ignore-times              | don't skip files that match size and time        |
| --size-only                     | skip files that match in size                    |
| --address ADDRESS               | bind address for outgoing socket to daemon       |
| --port PORT                     | specify double-colon alternate port number       |
| --list-only                     | list the files instead of copying them           |
| --whole-file                    | copy files whole (w/o dividing them into blocks) |
| --checksum                      | skip based on checksum, not mod-time & size      |
| --server                        | run as the server on remote machine              |
| --daemon                        | run as a daemon                                  |
| --no-detach                     | don't detach from the controlling terminal       |
| --version                       | print version number                             |

To get more information about these options, run the following command:
```sh
python3 mrsync.py --help
```

## Bugs
This rsync clone is not perfect. There are a few known bugs that we were not able to fix before the deadline. Here are some of the known bugs:
- Sometimes packet will get broken with ssh transfer which will cause the transfer to fail. Running the transfer again will fix the issue.
- Huge file (over 100MB) will sometimes cause the transfer to fail, but it mostly works. Using compression will help with this issue.
- Daemon create zombie process while it's running. We tried to fix this issue but we were not able to find the cause of the issue. They all get cleaned up when the daemon is stopped.

## Contributions
We welcome contributions from the community! If you find a bug or have an idea for a new feature, please open an issue or submit a pull request.

## License
This rsync clone is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for more information.
