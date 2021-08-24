import time
import httpx
import asyncio

from django.http import JsonResponse


def api(request):
    time.sleep(1)
    payload = {
        "message": "Hello ERM!"
    }
    if "task_id" in request.GET:
        payload["task_id"] = request.GET["task_id"]

    return JsonResponse(payload)


def get_api_urls(task_num):
    base_url = "http://localhost:8000/api/"
    return [f"{base_url}?task_id={task_id}" for task_id in range(task_num)]


async def api_aggregated_async(request):
    s = time.perf_counter()

    urls = get_api_urls(task_num=10)
    async with httpx.AsyncClient() as client:
        responses = await asyncio.gather(*[client.get(url) for url in urls])
        responses = [r.json() for r in responses]

    elapsed = time.perf_counter() - s
    result = {
        "message": "Hello Async World!",
        "responses": responses,
        "debug_message": f"fetch executed in {elapsed:0.2f} seconds.",
    }
    return JsonResponse(result)


def api_aggregated_sync(request):
    s = time.perf_counter()

    responses = []
    urls = get_api_urls(task_num=10)
    for url in urls:
        r = httpx.get(url)
        responses.append(r.json())

    elapsed = time.perf_counter() - s
    result = {
        "message": "Hello Sync World!",
        "aggregated_responses": responses,
        "debug_message": f"fetch executed in {elapsed:0.2f} seconds.",
    }
    return JsonResponse(result)
