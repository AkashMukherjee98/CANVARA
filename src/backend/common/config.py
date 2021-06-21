import os
import yaml

# Root directory containing configs for all the environments
canvara_configs_root_dir = os.environ['CANVARA_CONFIGS_DIR']

# Current Canvara environment ('dev', 'prod' etc.)
canvara_env = os.environ['CANVARA_ENV']

# Directory containing all config files for the current environment
canvara_config_dir = os.path.join(canvara_configs_root_dir, canvara_env)

def get_canvara_config():
    path = os.path.join(canvara_config_dir, 'canvara_config.yaml')
    with open(path) as config_file:
        return yaml.load(config_file, Loader=yaml.SafeLoader)
