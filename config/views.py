from django.http import JsonResponse


def handler404(request, exception):
    return JsonResponse({"error": "Resource not found"}, status=404)


def handler500(request):
    return JsonResponse({"error": "Internal server error"}, status=500)


def handler403(request, exception):
    return JsonResponse({"error": "Permission denied"}, status=403)


def handler400(request, exception):
    return JsonResponse({"error": "Bad request"}, status=400)
