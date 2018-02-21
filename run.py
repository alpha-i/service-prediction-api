from app import create_app
import logging

app = create_app('config')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True, host=app.config['HOST'], port=app.config['PORT'])
