def test_catalog_crud_and_validation(client, admin_token):
    # 1. Tax
    tax_res = client.post(
        "/api/v1/taxes",
        json={"name": "VAT 15%", "rate": 15.0},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert tax_res.status_code == 201
    tax_id = tax_res.get_json().get("id") or tax_res.get_json()["data"]["id"]

    taxes_list = client.get(
        "/api/v1/taxes",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert taxes_list.status_code == 200
    assert len(taxes_list.get_json().get("items", [])) >= 1

    # 2. Discount
    disc_res = client.post(
        "/api/v1/discounts",
        json={
            "code": "PROMO10",
            "discount_type": "percentage",
            "value": 10.0,
            "min_quantity": 2,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert disc_res.status_code == 201

    # 3. Product & Variant
    prod_res = client.post(
        "/api/v1/products",
        json={"name": "Database Server", "sales_price": 500.0, "cost_price": 100.0},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert prod_res.status_code == 201
    prod_id = prod_res.get_json().get("id") or prod_res.get_json()["data"]["id"]

    var_res = client.post(
        f"/api/v1/products/{prod_id}/variants",
        json={"name": "High RAM (64GB)", "extra_price": 120.0},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert var_res.status_code == 201

    # 4. Plan
    plan_res = client.post(
        "/api/v1/plans",
        json={
            "name": "Standard Monthly",
            "billing_period": "monthly",
            "min_quantity": 1,
            "start_date": "2026-01-01",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert plan_res.status_code == 201

