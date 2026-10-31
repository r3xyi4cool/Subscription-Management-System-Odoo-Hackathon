import os
from flask import Blueprint, send_file, render_template_string

from backend.app.routes.health import health_bp
from backend.app.routes.auth import auth_bp
from backend.app.routes.staff import staff_bp
from backend.app.routes.catalog import catalog_bp
from backend.app.routes.quotations import quotations_bp
from backend.app.routes.subscriptions import subscriptions_bp
from backend.app.routes.billing_trigger import billing_trigger_bp
from backend.app.routes.invoices import invoices_bp
from backend.app.routes.payments import payments_bp
from backend.app.routes.dashboard import dashboard_bp
from backend.app.routes.customers import customers_bp
from backend.app.routes.refunds import refunds_bp
from backend.app.routes.portal import portal_bp
from backend.app.routes.audit import audit_bp

api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")

# Register nested blueprints
api_v1.register_blueprint(health_bp)
api_v1.register_blueprint(auth_bp)
api_v1.register_blueprint(staff_bp)
api_v1.register_blueprint(catalog_bp)
api_v1.register_blueprint(quotations_bp)
api_v1.register_blueprint(subscriptions_bp)
api_v1.register_blueprint(billing_trigger_bp)
api_v1.register_blueprint(invoices_bp)
api_v1.register_blueprint(payments_bp)
api_v1.register_blueprint(dashboard_bp)
api_v1.register_blueprint(customers_bp)
api_v1.register_blueprint(refunds_bp)
api_v1.register_blueprint(portal_bp)
api_v1.register_blueprint(audit_bp)

# Documentation endpoints
docs_bp = Blueprint("docs", __name__)

SWAGGER_UI_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>Subscription Management System API Docs</title>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    window.onload = function() {
      SwaggerUIBundle({
        url: "/api/v1/openapi.yaml",
        dom_id: '#swagger-ui',
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIBundle.SwaggerUIStandalonePreset
        ],
        layout: "BaseLayout"
      });
    };
  </script>
</body>
</html>
"""


@docs_bp.route("/docs", methods=["GET"])
def swagger_ui():
    return render_template_string(SWAGGER_UI_TEMPLATE)


@docs_bp.route("/api/v1/openapi.yaml", methods=["GET"])
def openapi_spec():
    root_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    spec_path = os.path.join(root_dir, "openapi.yaml")
    return send_file(spec_path, mimetype="text/yaml")
