#   Copyright (c) 2023, TriForMine. (https://triformine.dev) All rights reserved.
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
    debug: Optional[bool]

    def __init__(self, verbose: Optional[bool] = False, quiet: Optional[bool] = False, debug: Optional[bool] = False,
                 beautify: Optional[bool] = False):
        self.verbose = verbose
        self.quiet = quiet
        self.beautify = beautify
        self.debug = debug

    @staticmethod
    def time_header():
        return datetime.datetime.now().strftime("%H:%M:%S")

    def custom_print(self, message, color):
        if self.beautify:
            if sys.platform == "win32":
                sys.stdout.write(f"{message}\033[0m")
            else:
                sys.stdout.write(f"\033[{color}m{message}\033[0m")
        else:
            sys.stdout.write(f"{message}")

    def log(self, message):
        if not self.quiet:
            self.custom_print(f"[{self.time_header()}] {message}", 32)

    def error(self, message):
        self.custom_print(f"[{self.time_header()}] {message}", 31)

    def warn(self, message):
        self.custom_print(f"[{self.time_header()}] {message}", 33)
    
    def info(self, message):
        if self.verbose:
            self.custom_print(f"[{self.time_header()}] {message}", 36)

    def debug(self, message):
        if self.debug:
            self.custom_print(f"[{self.time_header()}] {message}", 35)
