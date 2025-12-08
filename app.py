from Project import creat_app
from datetime import timedelta

if __name__ == "__main__":
    app = creat_app()
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)
    app.run(debug=True, port='5500')