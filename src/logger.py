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

import datetime
import sys
from typing import Optional


class Logger:
    verbose: Optional[bool]
    quiet: Optional[bool]

    def __init__(self, verbose: Optional[bool] = False, quiet: Optional[bool] = False,
                 beautify: Optional[bool] = True, debug_mode: Optional[bool] = False):
        self.verbose = verbose
        self.quiet = quiet
        self.beautify = beautify
        self.debug_mode = debug_mode

    @staticmethod
    def time_header():
        return datetime.datetime.now().strftime("%H:%M:%S")

    def custom_print(self, message, color, fo=sys.stdout):
        if self.beautify:
            if sys.platform == "win32":
                fo.write(f"{message}\033[0m\n")
            else:
                fo.write(f"\033[{color}m{message}\033[0m\n")
        else:
            fo.write(f"{message}\n")

    def log(self, message):
        if not self.quiet:
            self.custom_print(f"[{self.time_header()}] {message}", 32)

    def error(self, message):
        self.custom_print(f"[{self.time_header()}] {message}", 31, sys.stderr)

    def warn(self, message):
        self.custom_print(f"[{self.time_header()}] {message}", 33)

    def info(self, message):
        if self.verbose:
            self.custom_print(f"[{self.time_header()}] {message}", 36)

    def debug(self, message):
        if self.verbose:
            self.custom_print(f"[{self.time_header()}] {message}", 35)
