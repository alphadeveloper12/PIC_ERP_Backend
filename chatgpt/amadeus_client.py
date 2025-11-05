import os
from amadeus import Client, ResponseError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

amadeus = Client(
    client_id=os.getenv("AMADEUS_CLIENT_ID"),
    client_secret=os.getenv("AMADEUS_CLIENT_SECRET")
)

def search_flights(origin, destination, departure_date, return_date=None, adults=1):
    """
    Search for flights using Amadeus API.
    """
    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            returnDate=return_date,
            adults=adults,
            currencyCode="AED",
            max=5
        )
        flights = []
        for offer in response.data:
            flights.append({
                "from": origin,
                "to": destination,
                "airline": offer.get("validatingAirlineCodes", ["Unknown"])[0],
                "price_aed": offer["price"]["total"],
                "booking_link": f"https://sandbox.amadeus.com/flights/{offer['id']}"
            })
        return flights
    except ResponseError as error:
        return {"error": str(error)}


def search_hotels(city_code, checkin_date, checkout_date, adults=1):
    """
    Search for hotels using Amadeus API.
    """
    try:
        response = amadeus.shopping.hotel_offers_search.get(
            cityCode=city_code,
            checkInDate=str(checkin_date),
            checkOutDate=str(checkout_date),
            adults=adults,
            currency="AED"
        )
        hotels = []
        for hotel_offer in response.data[:5]:
            hotel = hotel_offer["hotel"]
            offer = hotel_offer["offers"][0]
            nights = (checkout_date - checkin_date).days
            hotels.append({
                "name": hotel.get("name", "Unknown"),
                "stars": hotel.get("rating", "N/A"),
                "nights": nights,
                "price_per_night": offer["price"]["total"],
                "total_price_aed": str(float(offer["price"]["total"]) * nights),
                "booking_link": f"https://sandbox.amadeus.com/hotels/{hotel['hotelId']}"
            })
        return hotels
    except ResponseError as error:
        return {"error": str(error)}
