from flask import request, jsonify


def get_pagination_params(default_page=1, default_per_page=20, max_per_page=100):
    try:
        page = int(request.args.get("page", default_page))
        if page < 1:
            page = default_page
    except (ValueError, TypeError):
        page = default_page

    try:
        per_page = int(request.args.get("per_page", default_per_page))
        if per_page < 1:
            per_page = default_per_page
        elif per_page > max_per_page:
            per_page = max_per_page
    except (ValueError, TypeError):
        per_page = default_per_page

    return page, per_page


def paginated_response(items, total, page, per_page):
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    return (
        jsonify({
            "items": items,
            "data": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
        }),
        200,
    )

