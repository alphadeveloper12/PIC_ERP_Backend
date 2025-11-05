import json
import traceback
import os
import requests
from datetime import datetime
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from openai import OpenAI
from json_repair import repair_json
from django.http import JsonResponse
from .amadeus_client import search_flights
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import JSONParser
from amadeus import Client, ResponseError, Location
from .flight import Flight
from .booking import Booking
import base64

from rest_framework.exceptions import ValidationError


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = (
    "You are a travel expert. Create a detailed travel itinerary for a user based on their preferences. "
    "The response must be STRICTLY valid JSON only. "
    "The JSON must include: "
    "- destination (city, country), "
    "- duration_days, "
    "- budget_aed, "
    "- total_estimated_cost_aed, "
    "- flight (from, to, airline, price_aed, booking_link), "
    "- visa (type, price_aed, booking_link), "
    "- hotel (name, stars, nights, price_per_night, total_price_aed, booking_link), "
    "- transport (method, total_cost_aed), "
    "- food (estimated_total_cost_aed, restaurants: list of {name, cuisine, price_range, link}), "
    "- itinerary: list of days with {date, activities: list of {time_block, name, price_aed, booking_link}}, "
    "- total_cost_breakdown (flights, visa, hotel, transport, food, activities, misc, grand_total), "
    "- full_trip_booking_link (affiliate link that covers the entire trip). "
    "Each day’s itinerary must be divided into 3-hour activity blocks (09:00–21:00). "
    "Each activity, hotel, restaurant, and transport must include a valid booking/affiliate link."
)

def _parse_date(date_str):
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
    except ValueError:
        return None

def _safe_json_loads(raw_text):
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        try:
            fixed = repair_json(raw_text)
            return json.loads(fixed)
        except Exception:
            return None

@csrf_exempt
def create_trip_plan(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Only POST requests are allowed")

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON body")

    required_fields = ["from", "to", "departDate", "returnDate", "travelers", "budget"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        return HttpResponseBadRequest(f"Missing fields: {', '.join(missing)}")

    depart_date = _parse_date(data["departDate"])
    return_date = _parse_date(data["returnDate"])
    if not depart_date or not return_date:
        return HttpResponseBadRequest("Invalid date format.")

    user_prompt = (
        f"Plan a trip from {data['from']} to {data['to']}, departing {depart_date} and returning {return_date}. "
        f"Number of travelers: {data['travelers']}. Budget: {data['budget']} AED. "
        f"Preferences: {data.get('preferences', 'No specific preferences')}. "
        "Return JSON with all fields, including affiliate booking links. "
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )

        generated_json = response.choices[0].message.content
        trip_plan_json = _safe_json_loads(generated_json)
        if trip_plan_json is None:
            return JsonResponse({"error": "Failed to parse JSON", "raw_text": generated_json}, status=500)

        return JsonResponse(trip_plan_json, safe=False, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e), "trace": traceback.format_exc()}, status=500)

amadeus = Client(
    client_id="bGXPHa9RbA8eu8xpGzadp1J3Rrxisc2o",  # Replace with your actual Amadeus client ID
    client_secret="wPCkbnoZvJ9y5aAm"  # Replace with your actual Amadeus client secret
)


class FlightDetailsAPIView(APIView):
    
    def post(self, request):
        """
        Endpoint to search for flight details based on user input.
        """
        # Retrieve data from the request
        origin = request.data.get("Origin")
        destination = request.data.get("Destination")
        departure_date = request.data.get("Departuredate")
        return_date = request.data.get("Returndate")
        
        if not origin or not destination or not departure_date:
            return Response({"error": "Origin, Destination, and Departure Date are required."}, status=status.HTTP_400_BAD_REQUEST)

        kwargs = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": 1,
        }

        # For a round trip, we use AI Trip Purpose Prediction to predict if it is a leisure or business trip
        trip_purpose = ""
        if return_date:
            kwargs["returnDate"] = return_date
            kwargs_trip_purpose = {
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDate": departure_date,
                "returnDate": return_date,
            }
            try:
                # Calls Trip Purpose Prediction API
                trip_purpose_response = amadeus.travel.predictions.trip_purpose.get(**kwargs_trip_purpose).data
                trip_purpose = trip_purpose_response["result"]
            except ResponseError as error:
                return Response({"error": error.response.result["errors"][0]["detail"]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Perform flight search based on previous inputs
        try:
            search_flights = amadeus.shopping.flight_offers_search.get(**kwargs)
        except ResponseError as error:
            return Response({"error": error.response.result["errors"][0]["detail"]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        search_flights_returned = []
        for flight in search_flights.data:
            offer = Flight(flight).construct_flights()
            search_flights_returned.append(offer)

        response_data = {
            "flights": search_flights_returned,
            "tripPurpose": trip_purpose,
            "origin": origin,
            "destination": destination,
            "departureDate": departure_date,
            "returnDate": return_date
        }

        return Response(response_data, status=status.HTTP_200_OK)


class BookFlightAPIView(APIView):

    def post(self, request, flight):
        """
        Endpoint to book a flight.
        """
        # Create a fake traveler profile for booking
        traveler = {
            "id": "1",
            "dateOfBirth": "1982-01-16",
            "name": {"firstName": "JORGE", "lastName": "GONZALES"},
            "gender": "MALE",
            "contact": {
                "emailAddress": "jorge.gonzales833@telefonica.es",
                "phones": [
                    {
                        "deviceType": "MOBILE",
                        "countryCallingCode": "34",
                        "number": "480080076",
                    }
                ],
            },
            "documents": [
                {
                    "documentType": "PASSPORT",
                    "birthPlace": "Madrid",
                    "issuanceLocation": "Madrid",
                    "issuanceDate": "2015-12-14",
                    "number": "00000000",
                    "expiryDate": "2025-12-14",
                    "issuanceCountry": "ES",
                    "validityCountry": "ES",
                    "nationality": "ES",
                    "holder": True,
                }
            ],
        }

        # Use Flight Offers Price to confirm price and availability
        try:
            flight_price_confirmed = amadeus.shopping.flight_offers.pricing.post(
                ast.literal_eval(flight)
            ).data["flightOffers"]
        except (ResponseError, KeyError, AttributeError) as error:
            return Response({"error": error.response.body}, status=status.HTTP_400_BAD_REQUEST)

        # Use Flight Create Orders to perform the booking
        try:
            order = amadeus.booking.flight_orders.post(flight_price_confirmed, traveler).data
        except (ResponseError, KeyError, AttributeError) as error:
            return Response({"error": error.response.result["errors"][0]["detail"]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        booking = Booking(order).construct_booking()

        return Response({"booking": booking}, status=status.HTTP_201_CREATED)


class AirportSearchAPIView(APIView):

    def get(self, request):
        """
        Endpoint for searching origin and destination airports.
        """
        term = request.GET.get("term", None)
        if not term:
            return Response({"error": "Search term is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = amadeus.reference_data.locations.get(keyword=term, subType=Location.ANY).data
        except (ResponseError, KeyError, AttributeError) as error:
            return Response({"error": error.response.result["errors"][0]["detail"]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        result = [f"{item['iataCode']}, {item['name']}" for item in data]
        result = list(dict.fromkeys(result))  # Remove duplicates
        return Response(result, status=status.HTTP_200_OK)