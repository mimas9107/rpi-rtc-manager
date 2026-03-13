import os

# Default config
DEFAULT_CONFIG = {
    'CLK': 17,
    'DAT': 27,
    'RST': 22,
    'LOG_FILE': '/opt/rpi-rtc-manager/logs/rpi-rtc-manager.log'
}

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'rtc.conf')
    config = DEFAULT_CONFIG.copy()
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if key in ['CLK', 'DAT', 'RST']:
                            config[key] = int(value)
                        else:
                            config[key] = value
        except Exception as e:
            print(f"Warning: Failed to load config from {config_path}: {e}")
    
    return config

# Load on import
config = load_config()
