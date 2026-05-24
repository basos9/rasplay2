# Configuration for rasplay2
from types import SimpleNamespace
import os
import yaml

# Try to load YAML configuration; fall back to defaults if missing
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")


def _load_yaml(path):
	try:
		with open(path, "r") as f:
			return yaml.safe_load(f)
	except Exception:
		raise FileNotFoundError(f"Could not load configuration from {path}. Please create a config.yaml fbased on config.yaml.dist.")


_cfg = _load_yaml(CONFIG_PATH)

# Grouped MPD settings
mpd_cfg = _cfg.get("mpd", {})
MPD = SimpleNamespace(
	host=mpd_cfg.get("host", "localhost"),
	port=mpd_cfg.get("port", 6600),
	password=mpd_cfg.get("password", ""),
)


# Grouped Transmission settings
tr_cfg = _cfg.get("transmission", {})
TRANS = SimpleNamespace(
	host=tr_cfg.get("host", "localhost"),
	port=tr_cfg.get("port", 9091),
	user=tr_cfg.get("user", "transmission"),
	password=tr_cfg.get("password", "transmission"),
)


# Grouped BUTTON settings (physical pin names for gpiozero)
btn_cfg = _cfg.get("buttons", {})
BUTTONS = SimpleNamespace(
	up=btn_cfg.get("up", "BOARD36"),
	down=btn_cfg.get("down", "BOARD31"),
	left=btn_cfg.get("left", "BOARD32"),
	right=btn_cfg.get("right", "BOARD33"),
	mid=btn_cfg.get("mid", "BOARD37"),
	btn_set=btn_cfg.get("set", "BOARD38"),
	rst=btn_cfg.get("rst", "BOARD40"),
)


# Mounts regex for SysInfo
sys_cfg = _cfg.get("sys", {})
SYS = SimpleNamespace(
    mntreg=sys_cfg.get("mntreg", "^/|xoros|data|aux")
)
