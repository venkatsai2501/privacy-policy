import requests
from django.http import JsonResponse
from django.shortcuts import render

def search_company(request):
    if request.method == "GET":
        query = request.GET.get('q', '')
        if query:
            url = f"https://autocomplete.clearbit.com/v1/companies/suggest?query={query}"
            response = requests.get(url)
            if response.status_code == 200:
                print(response.json())
                return JsonResponse(response.json(), safe=False)
                
        return JsonResponse([], safe=False)

def test_page(request):
    return render(request, 'test_search.html')
