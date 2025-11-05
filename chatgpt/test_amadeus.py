import os
import json
from amadeus import Client, ResponseError
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Initialize Amadeus client
amadeus = Client(
    client_id=os.getenv("AMADEUS_CLIENT_ID"),
    client_secret=os.getenv("AMADEUS_CLIENT_SECRET")
)

def test_flights():
    origin = "DXB"       # Dubai
    destination = "LHR"  # London
    departure_date = "2025-12-05"
    adults = 1

    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            adults=adults,
            currencyCode="AED",
            max=5
        )
        
        # Save full JSON response to file
        with open("flights.json", "w", encoding="utf-8") as f:
            json.dump(response.data, f, indent=4, ensure_ascii=False)
        
        print("Flight data saved to flights.json")

    except ResponseError as error:
        print("Amadeus API Error:", error)

if __name__ == "__main__":
    test_flights()
