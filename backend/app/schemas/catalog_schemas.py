from marshmallow import Schema, fields, validate, pre_load


class TaxSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    rate = fields.Decimal(required=True, as_string=True)
    is_active = fields.Boolean(load_default=True)


class DiscountSchema(Schema):
    code = fields.String(required=True, validate=validate.Length(min=1, max=100))
    description = fields.String(load_default=None)
    discount_type = fields.String(
        required=True, validate=validate.OneOf(["percentage", "percent", "fixed"])
    )
    value = fields.Decimal(required=True, as_string=True)
    min_quantity = fields.Integer(load_default=0)
    min_purchase = fields.Decimal(load_default=0.0, as_string=True)
    start_date = fields.Date(load_default=None)
    end_date = fields.Date(load_default=None)
    usage_limit = fields.Integer(load_default=None)
    applies_to = fields.String(
        load_default="all", validate=validate.OneOf(["product", "subscription", "all"])
    )
    is_active = fields.Boolean(load_default=True)

    @pre_load
    def normalize_discount_type(self, data, **kwargs):
        if isinstance(data, dict) and "type" in data and "discount_type" not in data:
            data["discount_type"] = data["type"]
        return data


class ProductSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    description = fields.String(load_default=None)
    sales_price = fields.Decimal(required=True, as_string=True)
    cost_price = fields.Decimal(load_default=0.0, as_string=True)
    is_active = fields.Boolean(load_default=True)


class VariantSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    extra_price = fields.Decimal(required=True, as_string=True)
    is_active = fields.Boolean(load_default=True)


class PlanSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    description = fields.String(load_default=None)
    billing_period = fields.String(
        required=True, validate=validate.OneOf(["daily", "weekly", "monthly", "yearly"])
    )
    min_quantity = fields.Integer(load_default=1)
    start_date = fields.Date(required=True)
    end_date = fields.Date(load_default=None)
    allow_pause = fields.Boolean(load_default=True)
    allow_close = fields.Boolean(load_default=True)
    allow_renew = fields.Boolean(load_default=True)
    allow_early_close = fields.Boolean(load_default=None)
    allow_renewal = fields.Boolean(load_default=None)
    price = fields.Decimal(load_default=0.0, as_string=True)
    auto_close = fields.Boolean(load_default=False)
    is_active = fields.Boolean(load_default=True)

    @pre_load
    def map_aliases(self, data, **kwargs):
        if isinstance(data, dict):
            if "allow_early_close" in data and "allow_close" not in data:
                data["allow_close"] = data["allow_early_close"]
            if "allow_renewal" in data and "allow_renew" not in data:
                data["allow_renew"] = data["allow_renewal"]
        return data
