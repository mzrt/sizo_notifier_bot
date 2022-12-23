import os, json
import sys
from dotenv import dotenv_values

devMode = 'app' in os.environ and os.environ['app']=="dev"

config = {
    **dotenv_values(".env.shared"),
    **dotenv_values(".env.secret"),
    **dotenv_values(".env.shared.local"),
    **dotenv_values(".env.secret.local"),
    **os.environ,  # override loaded values with environment variables
    **(dotenv_values(".env.development.local") if devMode else {}),
}
sys.stdout.write('config' + json.dumps(config, indent=4)+'\n' )
