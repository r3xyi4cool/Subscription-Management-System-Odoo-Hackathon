from marshmallow import Schema, fields, validate


class QuotationLineInputSchema(Schema):
    product_id = fields.Integer(required=True)
    variant_id = fields.Integer(load_default=None)
    quantity = fields.Integer(load_default=1, validate=validate.Range(min=1))
    tax_id = fields.Integer(load_default=None)
    discount_id = fields.Integer(load_default=None)


class QuotationCreateSchema(Schema):
    customer_id = fields.Integer(required=True)
    plan_id = fields.Integer(required=True)
    validity_days = fields.Integer(load_default=30, validate=validate.Range(min=1))
    template_id = fields.Integer(load_default=None)
    lines = fields.List(
        fields.Nested(QuotationLineInputSchema), required=True, validate=validate.Length(min=1)
    )

