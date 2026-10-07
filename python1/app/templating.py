import os
from typing import Optional, Dict, Any
from fastapi.templating import Jinja2Templates
from fastapi import Request
from starlette.responses import Response

templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

def render_template(
    request: Request,
    name: str,
    context: Optional[Dict[str, Any]] = None,
    status_code: int = 200
) -> Response:
    ctx = context.copy() if context else {}
    if "request" not in ctx:
        ctx["request"] = request

    # In modern Starlette (0.36+), signature is TemplateResponse(request=request, name=name, context=ctx, status_code=status_code)
    try:
        return templates.TemplateResponse(
            request=request,
            name=name,
            context=ctx,
            status_code=status_code
        )
    except TypeError:
        # Fallback for older versions
        return templates.TemplateResponse(
            name,
            ctx,
            status_code=status_code
        )
