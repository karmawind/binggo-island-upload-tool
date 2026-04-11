# -*- coding: utf-8 -*-
"""头条号图文文章发布器。"""

from pathlib import Path
from conf import BASE_DIR

Path(BASE_DIR / "cookies" / "toutiao_uploader").mkdir(exist_ok=True)
