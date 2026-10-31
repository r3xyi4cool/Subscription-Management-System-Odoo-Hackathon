import os
import sys

# Ensure root and backend directories are in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in [root_dir, backend_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

import pytest
from backend.app import create_app
from backend.app.extensions import db
from backend.app.models.auth import Auth
from backend.app.models.customer import Customer
from backend.app.models.staff import Staff
from flask_jwt_extended import create_access_token


class UserHolder:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.fixture(scope="session")
def app():
    os.environ["FLASK_ENV"] = "testing"
    _app = create_app("testing")
    return _app


@pytest.fixture(autouse=True)
def init_db(app):
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_user(app):
    with app.app_context():
        auth = Auth(email="admin_test@example.com", role="admin", is_active=True)
        auth.set_password("AdminTest@123")
        db.session.add(auth)
        db.session.commit()
        return UserHolder(id=auth.id, email=auth.email, role=auth.role)


@pytest.fixture
def admin_token(app, admin_user):
    with app.app_context():
        return create_access_token(
            identity=str(admin_user.id),
            additional_claims={"role": admin_user.role, "email": admin_user.email},
        )


@pytest.fixture
def staff_user(app):
    with app.app_context():
        auth = Auth(email="staff_test@example.com", role="staff", is_active=True)
        auth.set_password("StaffTest@123")
        db.session.add(auth)
        db.session.flush()

        staff = Staff(
            auth_id=auth.id,
            name="Test Staff",
            email=auth.email,
            department="Support",
            is_active=True,
        )
        db.session.add(staff)
        db.session.commit()
        return UserHolder(
            id=auth.id,
            auth_id=auth.id,
            staff_id=staff.id,
            email=auth.email,
            role=auth.role,
        )


@pytest.fixture
def staff_token(app, staff_user):
    with app.app_context():
        return create_access_token(
            identity=str(staff_user.id),
            additional_claims={"role": staff_user.role, "email": staff_user.email},
        )


@pytest.fixture
def customer_user(app):
    with app.app_context():
        auth = Auth(email="cust1_test@example.com", role="customer", is_active=True)
        auth.set_password("CustTest@123")
        db.session.add(auth)
        db.session.flush()

        cust = Customer(
            auth_id=auth.id,
            name="Customer One",
            email=auth.email,
            company="One Co",
            billing_address="1st Ave",
        )
        db.session.add(cust)
        db.session.commit()
        return UserHolder(
            id=cust.id,
            customer_id=cust.id,
            auth_id=auth.id,
            name=cust.name,
            email=cust.email,
            role="customer",
        )


@pytest.fixture
def customer_token(app, customer_user):
    with app.app_context():
        return create_access_token(
            identity=str(customer_user.auth_id),
            additional_claims={
                "role": "customer",
                "email": customer_user.email,
                "customer_id": customer_user.id,
            },
        )


@pytest.fixture
def customer2_user(app):
    with app.app_context():
        auth = Auth(email="cust2_test@example.com", role="customer", is_active=True)
        auth.set_password("CustTest@123")
        db.session.add(auth)
        db.session.flush()

        cust = Customer(
            auth_id=auth.id,
            name="Customer Two",
            email=auth.email,
            company="Two Co",
            billing_address="2nd Ave",
        )
        db.session.add(cust)
        db.session.commit()
        return UserHolder(
            id=cust.id,
            customer_id=cust.id,
            auth_id=auth.id,
            name=cust.name,
            email=cust.email,
            role="customer",
        )


@pytest.fixture
def customer2_token(app, customer2_user):
    with app.app_context():
        return create_access_token(
            identity=str(customer2_user.auth_id),
            additional_claims={
                "role": "customer",
                "email": customer2_user.email,
                "customer_id": customer2_user.id,
            },
        )
