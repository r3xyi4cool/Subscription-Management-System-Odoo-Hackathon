def test_signup_success(client):
    res = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "new_user@example.com",
            "password": "Password123!",
            "name": "New User",
            "company": "User Org",
        },
    )
    assert res.status_code == 201
    data = res.get_json()
    assert "id" in data or ("data" in data and "id" in data["data"])


def test_signup_duplicate_email(client):
    payload = {
        "email": "dup@example.com",
        "password": "Password123!",
        "name": "Dup User",
    }
    res1 = client.post("/api/v1/auth/signup", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/auth/signup", json=payload)
    assert res2.status_code in (400, 409)
    err = res2.get_json()
    assert "error" in err


def test_signup_weak_passwords(client):
    weak_passwords = [
        "short1!",  # too short (<8)
        "nocaps123!",  # no uppercase
        "NOLOWER123!",  # no lowercase
        "NoDigits!@",  # no digits
        "NoSpecialChar123",  # no special chars
    ]
    for idx, pwd in enumerate(weak_passwords):
        res = client.post(
            "/api/v1/auth/signup",
            json={
                "email": f"weak{idx}@example.com",
                "password": pwd,
                "name": "Weak User",
            },
        )
        assert res.status_code in (400, 422)
        err = res.get_json()
        assert "error" in err


def test_login_and_logout(client):
    # Create user
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "logintest@example.com",
            "password": "Password123!",
            "name": "Login Tester",
        },
    )

    # Login bad credentials
    bad_res = client.post(
        "/api/v1/auth/login",
        json={"email": "logintest@example.com", "password": "WrongPassword1!"},
    )
    assert bad_res.status_code == 401

    # Login good credentials
    good_res = client.post(
        "/api/v1/auth/login",
        json={"email": "logintest@example.com", "password": "Password123!"},
    )
    assert good_res.status_code == 200
    token = good_res.get_json().get("access_token") or good_res.get_json()["data"]["access_token"]
    assert token is not None

    # Test logout
    logout_res = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_res.status_code == 200

    # Using revoked token
    after_res = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert after_res.status_code == 401

