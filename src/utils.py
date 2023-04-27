#   Copyright (c) 2023, TriForMine. (https://triformine.dev) and samsoucoupe All rights reserved.
#  #
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#  #
#        http://www.apache.org/licenses/LICENSE-2.0
#  #
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
from typing import Tuple, Optional


def parse_path(path: str) -> Tuple[str, Optional[str], Optional[str], str]:
    """
    Parse a path to get the type of path, the user, the host and the path
    :param path: The path to parse
    :return: A tuple with the type of path, the user, the host and the path
    """
    # Check if it's ssh (user@host:/path/to/dir or host:/path/to/dir) or daemon (host::/path/to/dir) or local (/path/to/dir)
    if "::" in path:
        return "daemon", None, path.split("::")[0], path.split("::")[1]
    elif ":" in path:
        if "@" in path.split(":")[0]:
            return (
                "ssh",
                path.split(":")[0].split("@")[0],
                path.split(":")[0].split("@")[1],
                path.split(":")[1],
            )
        else:
            return "ssh", None, path.split(":")[0], path.split(":")[1]
    else:
        return "local", None, None, path
