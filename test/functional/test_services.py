from app.core.entities import User
from app.models import UserModel, CompanyModel
from test.functional.base_test_class import BaseTestClass

from app import services


class TestEntities(BaseTestClass):
    def test_user_services(self):
        company = CompanyModel(name='alese.it', domain='alese.it')
        user = UserModel(email='gabriele@alese.it', company_id=1)
        self.DB.session.add(company)
        self.DB.session.add(user)
        self.DB.session.commit()

        company = services.company.get_for_domain('alese.it')

        assert company.domain == 'alese.it'

        user = services.user.get_by_email('gabriele@alese.it')  # type: User
        assert user.email == 'gabriele@alese.it'

        token = services.user.generate_auth_token(user)
        assert services.user.verify_token(token)
