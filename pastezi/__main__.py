import sys


def main() -> None:
    print("""\
Please run with Sanic CLI, not as a module!

# Using Sanic stand-alone server (with your certificates)
sanic --host 0.0.0.0 --port 443 --tls /etc/letsencrypt/live/paste.zi.fi

# Locally/proxied (set SANIC_SERVER_NAME to public URL with no trailing slash)
SANIC_SERVER_NAME="https://paste.zi.fi" sanic --port 8000 pastezi:app
""")
    sys.exit(1)


if __name__ == "__main__":
    main()
