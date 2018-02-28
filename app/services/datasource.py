from app.core.entities import DataSource
from app.models.datasource import DataSourceModel


def get_by_upload_code(datasource_id):
    model = DataSourceModel.get_by_upload_code(datasource_id)
    return DataSource.from_model(model)


def generate_filename(upload_code, filename):
    return DataSourceModel.generate_filename(upload_code, filename)


def insert(upload):
    model = upload.to_model()
    model.save()
    return DataSource.from_model(model)
