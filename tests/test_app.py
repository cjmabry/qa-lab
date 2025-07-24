import pytest
from app import app as flask_app, db, TestCase, TestStep, Environment, EnvironmentVariable


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with flask_app.app_context():
        db.create_all()
        yield flask_app.test_client()
        db.session.remove()
        db.drop_all()


def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Test Cases" in response.data


def test_add_test_case(client):
    with flask_app.app_context():
        env = Environment(title="Test Env", url="https://example.com", description="desc")
        db.session.add(env)
        db.session.commit()
    response = client.post("/", data={"title": "Sample Case", "description": "A test case"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Sample Case" in response.data


def test_add_environment(client):
    with flask_app.app_context():
        env = Environment(title="Test Env", url="https://example.com", description="desc")
        db.session.add(env)
        db.session.commit()
        assert Environment.query.count() == 1


def test_add_step(client):
    with flask_app.app_context():
        env = Environment(title="Test Env", url="https://example.com", description="desc")
        db.session.add(env)
        case = TestCase(title="Case", description="desc")
        db.session.add(case)
        db.session.commit()
        case_id = case.id  # Get the id while still in the session
    response = client.post(f"/add_step/{case_id}", data={
        "step_text": "Step 1",
        "slug": "/foo",
        "expected_result": "Bar"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Step 1" in response.data
