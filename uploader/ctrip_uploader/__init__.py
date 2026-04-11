# -*- coding: utf-8 -*-
"""携程内容中心 Cookie 目录初始化。"""

from pathlib import Path
from conf import BASE_DIR

Path(BASE_DIR / "cookies" / "ctrip_uploader").mkdir(exist_ok=True)
