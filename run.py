# Used template:
# https://www.creative-tim.com/product/argon-dashboard-flask
from flaskapp import create_app

app = create_app()

if __name__ == "__main__":    
    # Esto solo se ejecuta al lanzar 'python run.py' manualmente
    app.run(host="0.0.0.0", port=5000, debug=True)