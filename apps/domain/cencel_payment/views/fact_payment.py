# views.py
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from pydantic import ValidationError

from apps.core.services import log_run
from apps.integrations.bx24.lib.services.webhook import parse_bitrix_payload, extract_trailing_id

from ..application.cencel_payment import CencelPaymentApplication

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def cencel_payment(request):
    try:
        payload = parse_bitrix_payload(
            dict(request.POST.lists())
        )

        result = extract_trailing_id(payload["document_id"]["2"])
        if result is None:
            raise ValueError("document_id does not contain payment id")

        with log_run("cencel_payment", fact_payment_id=result):
            CencelPaymentApplication().execute(fact_payment_id=result)

        return JsonResponse({
            "status": "success",
        })

    except (KeyError, TypeError, ValueError) as e:
        return JsonResponse(
            {
                "status": "error",
                "errors": str(e),
            },
            status=400,
        )

    except ValidationError as e:
        logger.warning("Некорректный вебхук от Bitrix: %s", e)

        return JsonResponse(
            {
                "status": "error",
                "errors": e.errors(),
            },
            status=400,
        )
