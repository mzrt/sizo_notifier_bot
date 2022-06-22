import os
from dotenv import dotenv_values

devMode = 'app' in os.environ and os.environ['app']=="dev"

config = {
    **dotenv_values(".env.shared"),
    **dotenv_values(".env.secret"),
    **dotenv_values(".env.shared.local"),
    **dotenv_values(".env.secret.local"),
    **(dotenv_values(".env.development.local") if devMode else {}),
    **os.environ,  # override loaded values with environment variables
}
