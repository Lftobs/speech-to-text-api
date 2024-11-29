import requests
import time
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('api_health_check.log'),
        logging.StreamHandler()
    ]
)

class APIHealthMonitor:
    def __init__(
        self, 
        api_url, 
        check_interval=300,  # Default 5 minutes
        max_retries=3,
        retry_delay=30
    ):
        self.api_url = api_url
        self.check_interval = check_interval
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def ping_health_endpoint(self):
        """
        Ping the health endpoint of the API
        """
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            return response.status_code == 200
        except requests.RequestException as e:
            logging.error(f"Health check failed: {e}")
            return False

    def perform_keep_alive(self):
        """
        Perform keep-alive checks with retry mechanism
        """
        retries = 0
        while retries < self.max_retries:
            try:
                # Simulate a simple request to keep the API warm
                requests.get(self.api_url, timeout=10)
                logging.info(f"Successfully pinged API at {datetime.now()}")
                return True
            except requests.RequestException as e:
                retries += 1
                logging.warning(f"Keep-alive attempt {retries} failed: {e}")
                time.sleep(self.retry_delay)
        
        logging.error("Failed to keep API alive after maximum retries")
        return False

    def run(self):
        """
        Continuous monitoring loop
        """
        logging.info(f"Starting API Health Monitor for {self.api_url}")
        
        while True:
            try:
                # Check health
                if not self.ping_health_endpoint():
                    logging.warning("API health check failed")
                
                # Perform keep-alive
                self.perform_keep_alive()
                
                # Wait before next check
                time.sleep(self.check_interval)
            
            except Exception as e:
                logging.error(f"Unexpected error in monitor: {e}")
                time.sleep(self.check_interval)

def main():
    # Read API URL from environment variable or use default
    api_url = os.getenv('API_URL', 'https://speech-to-text-api-production.up.railway.app/')
    
    monitor = APIHealthMonitor(
        api_url=api_url,
        check_interval=int(os.getenv('CHECK_INTERVAL', 80)),
        max_retries=int(os.getenv('MAX_RETRIES', 3))
    )
    
    monitor.run()

if __name__ == "__main__":
    main()

# requirements.txt
# requests
# python-dotenv