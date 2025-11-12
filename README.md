# osrsMarket
Fully functional market tool for Old School RuneScape. 
Ability to search any item in the game and return Grand Exchange data on that item.

## Features
- Search for any OSRS item by name
- View latest market data (buy/sell prices, margin, last sale time)
- View 24-hour historical price data with interactive charts
- Dark theme UI
- **User Account Management**
  - Secure account registration with password hashing
  - Login/logout functionality
  - Account settings page
  - CSRF protection on all forms

## Security Features
- Password hashing using Werkzeug's secure password hashing
- CSRF protection using Flask-WTF
- Session management with Flask-Login
- Input validation (username, email, password requirements)
- Secure session cookies

## Running the Application

### Local Development
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. (Optional) Set environment variables:
   ```bash
   export SECRET_KEY="your-secure-secret-key"
   export FLASK_DEBUG=false
   ```

3. Run the Flask application:
   ```bash
   python app.py
   ```

4. Open your browser and navigate to `http://localhost:8080`

### Using DevContainer
The repository includes a DevContainer configuration that automatically sets up and runs the application.
