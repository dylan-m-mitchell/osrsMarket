# osrsMarket
Fully functional market tool for Old School RuneScape. 
Ability to search any item in the game and return Grand Exchange data on that item.

## Features
- Search for any OSRS item by name
- View latest market data (buy/sell prices, margin, last sale time)
- View 24-hour historical price data with interactive charts
- Dark theme UI

## Running the Application

### Local Development
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the Flask application:
   ```bash
   python app.py
   ```

3. Open your browser and navigate to `http://localhost:5000`

#### Accessing from Other Devices on the Network
The application is configured to accept connections from any device on your network. To access from another device:

1. Find your computer's IP address:
   - **Windows**: Run `ipconfig` in Command Prompt (look for IPv4 Address)
   - **Mac/Linux**: Run `ifconfig` or `ip addr` in Terminal (look for inet address)

2. On the other device, open a browser and navigate to `http://YOUR_IP_ADDRESS:5000`
   - Example: `http://192.168.1.100:5000`

3. Ensure your firewall allows incoming connections on port 5000

### Using DevContainer
The repository includes a DevContainer configuration that automatically sets up and runs the application.
