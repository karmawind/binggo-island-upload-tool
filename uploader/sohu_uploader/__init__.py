# -*- coding: utf-8 -*-
"""搜狐号 Cookie 目录初始化。"""

from pathlib import Path
from conf import BASE_DIR

Path(BASE_DIR / "cookies" / "sohu_uploader").mkdir(exist_ok=True)
