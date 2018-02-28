from app.core.models import DataSource
from app.entities import DataSourceEntity


def get_by_upload_code(datasource_id):
    model = DataSourceEntity.get_by_upload_code(datasource_id)
    return DataSource.from_model(model)


def generate_filename(upload_code, filename):
    return DataSourceEntity.generate_filename(upload_code, filename)


def insert(upload):
    model = upload.to_model()
    model.save()
    return DataSource.from_model(model)
