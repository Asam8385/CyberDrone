from __future__ import annotations # reduce the errors

import argparse
import hashlib
import json
import math
import re
from collections import defaultdict
from datetime import datetime , timezone
from pathlib import Path
from typing import Any

import pymupdf
import yaml

SCHEMA_VERSION = "1.0"