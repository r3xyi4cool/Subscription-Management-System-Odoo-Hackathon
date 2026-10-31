from marshmallow import Schema, fields, validate


class TaxSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    rate = fields.Decimal(required=True, as_string=True)
    is_active = fields.Boolean(load_default=True)


class DiscountSchema(Schema):
    code = fields.String(required=True, validate=validate.Length(min=1, max=100))
    description = fields.String(load_default=None)
    discount_type = fields.String(
        required=True, validate=validate.OneOf(["percentage", "fixed"])
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
    is_active = fields.Boolean(load_default=True)

