from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from Resturant.models import Table_Reservation, Table
from RestFrameWork.serializers import Table_Reservation_Serializer, TableSerializer
from rest_framework.decorators import permission_classes,api_view

# ✅ View all reservations (admin/general)
class ViewReservationView(APIView):
    def get(self, request):
        reservations = Table_Reservation.objects.all()
        serializer = Table_Reservation_Serializer(reservations, many=True)
        return Response(serializer.data, status=200)


# ✅ Create reservation and fetch current user's reservations
class CreateAPIReservationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reservations = Table_Reservation.objects.filter(user=request.user)
        serializer = Table_Reservation_Serializer(reservations, many=True)
        return Response(serializer.data, status=200)

    def post(self, request):
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = Table_Reservation_Serializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


# ✅ Update a reservation only if the user owns it
class UpdateReservationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            reservation = Table_Reservation.objects.get(pk=pk, user=request.user)
        except Table_Reservation.DoesNotExist:
            return Response({"error": "Reservation not found"}, status=404)

        serializer = Table_Reservation_Serializer(reservation)
        return Response(serializer.data, status=200)

    def put(self, request, pk):
        try:
            reservation = Table_Reservation.objects.get(pk=pk, user=request.user)
        except Table_Reservation.DoesNotExist:
            return Response({"error": "Reservation not found"}, status=404)

        serializer = Table_Reservation_Serializer(reservation, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_table_availability(request):
    table_id = request.GET.get('table_id')
    date_str = request.GET.get('date')  # format: 'YYYY-MM-DD'
    time_str = request.GET.get('time')  # format: 'HH:MM'
    
    if not (table_id and date_str and time_str):
        return Response({"error": "Missing required parameters"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        reservation_datetime = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
    except ValueError:
        return Response({"error": "Invalid date or time format"}, status=status.HTTP_400_BAD_REQUEST)
    
    reservation_end = reservation_datetime + timedelta(hours=2)  # Duration assumed 2 hours
    
    conflicts = Table_Reservation.objects.filter(
        table_id=table_id,
        reservation_time__lt=reservation_end,
        reservation_time__gte=reservation_datetime
    ).exists()
    
    return Response({"available": not conflicts}, status=status.HTTP_200_OK)

# ✅ Autocomplete API for table names
def autocomplete_table_name(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        query = request.GET.get('term', '')
        matches = Table.objects.filter(name__icontains=query).values_list('name', flat=True).distinct()
        return JsonResponse(list(matches), safe=False)
    return JsonResponse([], safe=False)

