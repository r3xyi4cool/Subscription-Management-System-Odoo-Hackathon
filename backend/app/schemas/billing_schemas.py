from marshmallow import Schema, fields, validate


class PaymentCreateSchema(Schema):
    invoice_id = fields.Integer(required=True)
    amount = fields.Decimal(required=True, as_string=True)
    method = fields.String(
        required=True,
        validate=validate.OneOf(
            [
                "credit_card",
                "bank_transfer",
                "cash",
                "check",
                "cheque",
                "upi",
                "card",
                "paypal",
                "stripe",
                "other",
            ]
        ),
    )
    date = fields.Date(load_default=None)
    note = fields.String(load_default=None)


class RefundCreateSchema(Schema):
    amount = fields.Decimal(required=True, as_string=True)
    reason = fields.String(load_default=None)
    payment_id = fields.Integer(load_default=None)
    date = fields.Date(load_default=None)

