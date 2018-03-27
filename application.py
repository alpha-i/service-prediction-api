from app import create_app
import logging

app = create_app('config')


@app.cli.command('create_superuser')
def create_superuser():
    from app.services.superuser import create_admin
    create_admin('admin@alpha-i.co', 'LondonRulez')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True, host=app.config['HOST'], port=app.config['PORT'])
